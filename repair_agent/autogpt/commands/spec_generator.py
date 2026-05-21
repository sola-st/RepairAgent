
import os
import re
import json
import logging

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────
# 0. Logging helpers
# ─────────────────────────────────────────────────────────────────────

def _get_spec_log_dir():
    """Get the spec_logs directory under the current experiment folder."""
    try:
        with open("experimental_setups/experiments_list.txt") as f:
            exps = f.read().splitlines()
        if exps:
            log_dir = os.path.join("experimental_setups", exps[-1], "spec_logs")
            os.makedirs(log_dir, exist_ok=True)
            return log_dir
    except Exception as e:
        logger.info("SPEC-LOG: Could not find experiment dir: {}".format(e))
    os.makedirs("spec_logs", exist_ok=True)
    return "spec_logs"


def _save_spec_log(project_name, bug_index, suffix, content):
    """Save a spec log file."""
    try:
        log_dir = _get_spec_log_dir()
        ext = "json" if suffix.endswith("json") else "txt"
        filename = "spec_{}_{}_{}.{}".format(suffix, project_name, bug_index, ext)
        filepath = os.path.join(log_dir, filename)
        with open(filepath, "w") as f:
            if isinstance(content, (dict, list)):
                json.dump(content, f, indent=2)
            else:
                f.write(str(content))
        logger.info("SPEC-LOG: Saved {} ({} chars)".format(filepath, len(str(content))))
    except Exception as e:
        logger.info("SPEC-LOG: Failed to save {}: {}".format(suffix, e))


# ─────────────────────────────────────────────────────────────────────
# 1. Information Gathering (no LLM — pure disk reads)
# ─────────────────────────────────────────────────────────────────────

def _resolve_source_path(workspace, project_dir, rel_path):
    """Resolve a relative source path to an absolute path in the checkout."""
    candidates = [
        os.path.join(workspace, project_dir, rel_path),
        os.path.join(workspace, project_dir, "src", "main", "java", rel_path),
        os.path.join(workspace, project_dir, "src", "java", rel_path),
        os.path.join(workspace, project_dir, "src", rel_path),
        os.path.join(workspace, project_dir, "source", rel_path),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c

    basename = os.path.basename(rel_path)
    root_dir = os.path.join(workspace, project_dir)
    if os.path.exists(root_dir):
        for root, dirs, files in os.walk(root_dir):
            if basename in files:
                cand = os.path.join(root, basename)
                if cand.endswith(rel_path):
                    return cand
    return None


def read_buggy_source(project_name, bug_index, workspace="auto_gpt_workspace"):
    """Read the buggy source file and extract a code window around the buggy lines."""
    result = {"buggy_entries": [], "file_path": "", "lines": [], "window": "", "full_source": ""}

    buggy_lines_path = os.path.join("defects4j", "buggy-lines",
                                    "{}-{}.buggy.lines".format(project_name, bug_index))
    if not os.path.exists(buggy_lines_path):
        logger.info("SPEC-GEN: buggy-lines file not found: {}".format(buggy_lines_path))
        return result

    with open(buggy_lines_path) as f:
        raw_lines = f.read().splitlines()

    for raw in raw_lines:
        raw = raw.strip()
        if not raw:
            continue
        parts = raw.split("#")
        if len(parts) >= 2:
            fp = parts[0]
            try:
                line_num = int(parts[1])
            except ValueError:
                continue
            line_code = parts[2] if len(parts) >= 3 else ""
            result["buggy_entries"].append((fp, line_num, line_code))

    if not result["buggy_entries"]:
        return result

    first_file = result["buggy_entries"][0][0]
    first_line_num = result["buggy_entries"][0][1]
    result["file_path"] = first_file

    project_dir = "{}_{}_buggy".format(project_name.lower(), bug_index)
    full_path = _resolve_source_path(workspace, project_dir, first_file)

    if not full_path or not os.path.exists(full_path):
        logger.info("SPEC-GEN: source file not found for {}".format(first_file))
        return result

    with open(full_path, "r") as f:
        source = f.read()

    result["full_source"] = source
    disk_lines = source.split("\n")
    result["lines"] = [(i + 1, disk_lines[i]) for i in range(len(disk_lines))]

    win_start = max(0, first_line_num - 76)
    win_end = min(len(disk_lines), first_line_num + 75)
    window_lines = []
    for i in range(win_start, win_end):
        marker = ">>> " if (i + 1) == first_line_num else "    "
        window_lines.append("{}{:>5} | {}".format(marker, i + 1, disk_lines[i]))
    result["window"] = "\n".join(window_lines)

    return result


def read_buggy_methods(project_name, bug_index):
    """Read the buggy methods file from defects4j metadata."""
    methods_path = os.path.join("defects4j", "buggy-methods",
                                "{}-{}.buggy.methods".format(project_name, bug_index))
    if os.path.exists(methods_path):
        with open(methods_path) as f:
            return f.read()
    return ""


def read_trigger_tests(project_name, bug_index):
    """Read trigger test info from static D4J metadata (always available).

    Returns (test_classes, trigger_content) where test_classes is a list of
    (class_name, method_name) tuples and trigger_content is the raw file text
    (includes stack traces — useful as fallback test failure info).
    """
    trigger_path = os.path.join(
        "defects4j", "framework", "projects", project_name,
        "trigger_tests", str(bug_index)
    )
    if not os.path.exists(trigger_path):
        return [], ""

    with open(trigger_path) as f:
        content = f.read()

    test_classes = []
    for m in re.finditer(r"---\s+([\w.]+)::([\w]+)", content):
        test_classes.append((m.group(1), m.group(2)))

    return test_classes, content


def read_failing_test_code(project_name, bug_index, workspace="auto_gpt_workspace"):
    """Find and read the failing test method source code."""
    project_dir = "{}_{}_buggy".format(project_name.lower(), bug_index)
    test_class = ""
    test_method = ""

    # Try static D4J trigger_tests metadata first (always exists at spec-gen time)
    trigger_tests, _ = read_trigger_tests(project_name, bug_index)
    if trigger_tests:
        test_class, test_method = trigger_tests[0]

    # Fallback: runtime failing_tests file (only exists after defects4j test)
    if not test_class:
        failing_path = os.path.join(workspace, project_dir, "failing_tests")
        if os.path.exists(failing_path):
            with open(failing_path) as f:
                content = f.read()
            match = re.search(r"---\s+([\w.]+)::([\w]+)", content)
            if match:
                test_class = match.group(1)
                test_method = match.group(2)

    if not test_class:
        return ""

    test_file_rel = test_class.replace(".", "/") + ".java"
    project_path = os.path.join(workspace, project_dir)

    candidates = [
        os.path.join(project_path, "src", "test", "java", test_file_rel),
        os.path.join(project_path, "src", "test", test_file_rel),
        os.path.join(project_path, "test", test_file_rel),
        os.path.join(project_path, "tests", test_file_rel),
        os.path.join(project_path, test_file_rel),
    ]

    test_file = None
    for cand in candidates:
        if os.path.exists(cand):
            test_file = cand
            break

    if not test_file:
        test_basename = os.path.basename(test_file_rel)
        for root, dirs, files in os.walk(project_path):
            if test_basename in files:
                cand = os.path.join(root, test_basename)
                if cand.endswith(test_file_rel):
                    test_file = cand
                    break

    if not test_file:
        return ""

    with open(test_file, "r") as f:
        file_content = f.read()

    if test_method:
        patterns = [
            r"public\s+void\s+{}\s*\(".format(re.escape(test_method)),
            r"void\s+{}\s*\(".format(re.escape(test_method)),
        ]
        start_idx = -1
        for pat in patterns:
            m = re.search(pat, file_content)
            if m:
                start_idx = m.start()
                break

        if start_idx >= 0:
            brace_start = file_content.find("{", start_idx)
            if brace_start >= 0:
                depth = 0
                pos = brace_start
                while pos < len(file_content):
                    if file_content[pos] == "{":
                        depth += 1
                    elif file_content[pos] == "}":
                        depth -= 1
                        if depth == 0:
                            break
                    pos += 1
                return file_content[start_idx:pos + 1][:2500]

    return file_content[:3000]


def extract_javadoc(disk_lines, buggy_line_num):
    """Extract the Javadoc comment for the method containing the buggy line."""
    if not disk_lines or buggy_line_num <= 0:
        return ""

    try:
        # Find method declaration
        decl_idx = -1
        for i in range(buggy_line_num - 1, max(0, buggy_line_num - 100), -1):
            if i >= len(disk_lines):
                continue
            ln = disk_lines[i].strip()
            if re.match(r"(public|protected|private)\s+", ln):
                decl_idx = i
                break

        if decl_idx < 0:
            return ""

        # Find end of Javadoc (looking for */)
        jd_end = -1
        for i in range(decl_idx - 1, max(0, decl_idx - 10), -1):
            if i >= len(disk_lines):
                continue
            stripped = disk_lines[i].strip()
            if stripped.endswith("*/"):
                jd_end = i
                break
            if stripped.startswith("@"):
                continue
            if stripped and not stripped.startswith("@") and not stripped.endswith("*/"):
                break

        if jd_end < 0:
            return disk_lines[decl_idx]

        # Find start of Javadoc (looking for /**)
        jd_start = -1
        for i in range(jd_end, max(0, jd_end - 60), -1):
            if disk_lines[i].strip().startswith("/**"):
                jd_start = i
                break

        if jd_start < 0:
            return disk_lines[decl_idx]

        javadoc = "\n".join(disk_lines[jd_start:jd_end + 1])
        javadoc += "\n" + disk_lines[decl_idx]
        return javadoc

    except Exception as e:
        logger.info("SPEC-GEN: Javadoc extraction failed: {}".format(e))
        return ""


def extract_buggy_method_body(full_source, buggy_line_num):
    """Extract the complete body of the method containing the buggy line."""
    if not full_source or buggy_line_num <= 0:
        return ""

    lines = full_source.split("\n")
    if buggy_line_num > len(lines):
        return ""

    # Find method declaration
    decl_line = -1
    for i in range(buggy_line_num - 1, max(0, buggy_line_num - 100), -1):
        ln = lines[i].strip()
        if re.match(r"(public|protected|private)\s+", ln) and \
                ("(" in ln or (i + 1 < len(lines) and "(" in lines[i + 1])):
            decl_line = i
            break

    if decl_line < 0:
        return ""

    # Find opening brace
    brace_start = -1
    for i in range(decl_line, min(decl_line + 5, len(lines))):
        if "{" in lines[i]:
            brace_start = i
            break

    if brace_start < 0:
        return ""

    # Find matching closing brace
    depth = 0
    end_line = brace_start
    for i in range(brace_start, len(lines)):
        for ch in lines[i]:
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end_line = i
                    break
        if depth == 0:
            break

    method_lines = []
    for i in range(decl_line, end_line + 1):
        marker = ">>> " if (i + 1) == buggy_line_num else "    "
        method_lines.append("{}{:>5} | {}".format(marker, i + 1, lines[i]))

    return "\n".join(method_lines)


def _extract_method_at(lines, method_start):
    """Extract a method body (with Javadoc) given the declaration line index.

    Returns (jd_start, method_end, method_text) or None if parsing fails.
    """
    # Find opening brace
    brace_start = -1
    for j in range(method_start, min(method_start + 5, len(lines))):
        if "{" in lines[j]:
            brace_start = j
            break
    if brace_start < 0:
        return None

    # Find closing brace
    depth = 0
    method_end = brace_start
    for j in range(brace_start, len(lines)):
        for ch in lines[j]:
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    method_end = j
                    break
        if depth == 0:
            break

    # Include Javadoc if present
    jd_start = method_start
    for j in range(method_start - 1, max(0, method_start - 50), -1):
        stripped = lines[j].strip()
        if stripped.startswith("/**"):
            jd_start = j
            break
        elif stripped.startswith("*") or stripped.startswith("@") or stripped == "":
            continue
        else:
            break

    method_text = "\n".join(lines[jd_start:method_end + 1])
    return (jd_start, method_end, method_text)


def extract_sibling_methods(workspace, project_dir, buggy_file,
                            buggy_method_name, buggy_line_num):
    """Find other overloads of the buggy method in the same file."""
    if not buggy_method_name:
        return ""

    full_path = _resolve_source_path(workspace, project_dir, buggy_file)
    if not full_path or not os.path.exists(full_path):
        return ""

    with open(full_path) as f:
        source = f.read()

    lines = source.split("\n")

    pattern = re.compile(
        r"(public|protected|private)\s+(?:static\s+)?[\w<>\[\],\s]+\s+"
        + re.escape(buggy_method_name)
        + r"\s*\("
    )

    methods_found = []
    for i, line in enumerate(lines):
        if pattern.search(line):
            methods_found.append(i)

    if len(methods_found) <= 1:
        return ""

    siblings = []
    for method_start in methods_found:
        result = _extract_method_at(lines, method_start)
        if not result:
            continue
        _, method_end, method_text = result

        # Skip the buggy method itself
        if method_start < buggy_line_num <= method_end + 1:
            continue

        siblings.append(method_text)

    if not siblings:
        return ""

    return "\n\n".join(siblings)[:3000]


def extract_peer_methods(workspace, project_dir, buggy_file,
                         buggy_method_name, buggy_line_num):
    """Find peer methods — other methods in the same class with similar signature/structure.

    For a buggy method like 'add(Complex rhs)', this finds 'subtract', 'multiply',
    'divide' etc. that take the same parameter type and return the same type.
    These show the class's pattern for similar operations, helping the spec generator
    infer whether a fix should ADD code (like a guard) or REMOVE/SIMPLIFY code.
    """
    if not buggy_method_name:
        return ""

    full_path = _resolve_source_path(workspace, project_dir, buggy_file)
    if not full_path or not os.path.exists(full_path):
        return ""

    with open(full_path) as f:
        source = f.read()

    lines = source.split("\n")

    # Extract the buggy method's return type and parameter types from its declaration
    buggy_return_type = ""
    buggy_param_types = []
    method_decl_pattern = re.compile(
        r"(public|protected|private)\s+(?:static\s+)?([\w<>\[\]]+)\s+"
        + re.escape(buggy_method_name)
        + r"\s*\(([^)]*)\)"
    )
    for i in range(max(0, buggy_line_num - 100), buggy_line_num):
        if i >= len(lines):
            continue
        m = method_decl_pattern.search(lines[i])
        if m:
            buggy_return_type = m.group(2)
            params_str = m.group(3).strip()
            if params_str:
                for param in params_str.split(","):
                    parts = param.strip().split()
                    if parts:
                        buggy_param_types.append(parts[0])
            break

    if not buggy_return_type:
        return ""

    # Find all methods in the class with the same return type and parameter signature
    all_methods_pattern = re.compile(
        r"(public|protected|private)\s+(?:static\s+)?([\w<>\[\]]+)\s+(\w+)\s*\(([^)]*)\)"
    )

    peers = []
    for i, line in enumerate(lines):
        m = all_methods_pattern.search(line)
        if not m:
            continue

        ret_type = m.group(2)
        method_name = m.group(3)
        params_str = m.group(4).strip()

        # Skip the buggy method itself
        if method_name == buggy_method_name:
            continue

        # Must have same return type
        if ret_type != buggy_return_type:
            continue

        # Must have same parameter types
        param_types = []
        if params_str:
            for param in params_str.split(","):
                parts = param.strip().split()
                if parts:
                    param_types.append(parts[0])

        if param_types != buggy_param_types:
            continue

        # This method has the same signature shape — extract it
        result = _extract_method_at(lines, i)
        if not result:
            continue
        jd_start, method_end, method_text = result

        # Skip if it contains the buggy line
        if i < buggy_line_num <= method_end + 1:
            continue

        # Keep methods under 60 lines to avoid bloating the prompt
        if method_end - jd_start > 60:
            continue

        peers.append(method_text)

    if not peers:
        return ""

    # Limit to 3 peer methods to keep prompt manageable
    return "\n\n".join(peers[:3])[:3000]


def extract_class_header(workspace, project_dir, buggy_file):
    """Read the class declaration and field/constant definitions."""
    full_path = _resolve_source_path(workspace, project_dir, buggy_file)
    if not full_path or not os.path.exists(full_path):
        return ""

    with open(full_path) as f:
        lines = f.readlines()

    class_start = 0
    for i, line in enumerate(lines):
        if re.match(r"\s*(public|abstract|final)\s+(class|abstract\s+class|final\s+class|enum|interface)\s+",
                    line):
            class_start = i
            break

    # Walk backward from class declaration to find class-level Javadoc
    header_start = class_start
    if class_start > 0:
        # Skip annotations above class (e.g. @SuppressWarnings, @Deprecated)
        j = class_start - 1
        while j >= 0 and lines[j].strip().startswith("@"):
            j -= 1
        # Check for Javadoc comment block ending with */
        if j >= 0 and lines[j].strip().endswith("*/"):
            # Walk backward to find the /** opening
            k = j
            while k >= 0:
                if "/**" in lines[k]:
                    header_start = k
                    break
                k -= 1

    end = min(class_start + 80, len(lines))
    for i in range(class_start + 2, end):
        stripped = lines[i].strip()
        if re.match(r"(public|protected|private)\s+(?:static\s+)?[\w<>\[\],\s]+\s+\w+\s*\(", stripped):
            rest_of_line = stripped[stripped.find("("):]
            if ")" in rest_of_line:
                after_paren = rest_of_line[rest_of_line.find(")") + 1:].strip()
                if after_paren.startswith("{") or after_paren.startswith("throws") or after_paren == "":
                    end = i
                    break

    header = "".join(lines[header_start:end])
    return header[:2000]


def _extract_method_name(buggy_methods_str):
    """Extract method name from the buggy-methods metadata string.

    Prioritizes lines ending with ',1' or higher (the actual buggy method).
    Handles <init> (constructor) by converting to class name.
    Skips <clinit> (static initializer).
    """
    if not buggy_methods_str:
        return ""

    def _name_from_line(line):
        """Extract method name from a single buggy-methods line."""
        paren_idx = line.find("(")
        if paren_idx <= 0:
            return ""
        before_paren = line[:paren_idx]
        dot_idx = before_paren.rfind(".")
        if dot_idx < 0:
            return before_paren
        name = before_paren[dot_idx + 1:]
        if name == "<clinit>":
            return ""
        if name == "<init>":
            class_dot_idx = before_paren.rfind(".", 0, dot_idx)
            if class_dot_idx >= 0:
                return before_paren[class_dot_idx + 1:dot_idx]
            return before_paren[:dot_idx]
        return name

    # First pass: find the actual buggy method (count > 0)
    for line in buggy_methods_str.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        comma_idx = line.rfind(",")
        if comma_idx >= 0:
            try:
                count = int(line[comma_idx + 1:])
            except ValueError:
                continue
            if count > 0:
                name = _name_from_line(line)
                if name:
                    return name

    # Second pass: fallback to first method with a parseable name
    for line in buggy_methods_str.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        name = _name_from_line(line)
        if name:
            return name
    return ""


# ─────────────────────────────────────────────────────────────────────
# 1b. Self-Clarification Helper
# ─────────────────────────────────────────────────────────────────────

def _answer_clarifying_question(question, test_code, test_failure, method_body, model):
    """Use the verifier LLM to answer a clarifying question from available context."""
    prompt = (
        "A spec generator analyzing a Java bug asked this clarifying question:\n"
        "  Q: {}\n\n"
        "Answer it using ONLY the information below. Give a concise factual answer "
        "(1-2 sentences). If the answer cannot be determined, say ONLY 'UNKNOWN'.\n\n"
        "## Test Code\n```java\n{}\n```\n\n"
        "## Test Failure Output\n{}\n\n"
        "## Method Body\n```java\n{}\n```\n\n"
    ).format(
        question,
        test_code[:2000] if test_code else "(none)",
        test_failure[:1000] if test_failure else "(none)",
        method_body[:2000] if method_body else "(none)",
    )

    try:
        from langchain.chat_models import ChatOpenAI
        from langchain.schema.messages import HumanMessage
        chat = ChatOpenAI(model=model)
        response = chat.invoke([HumanMessage(content=prompt)])
        answer = response.content.strip()
        if "UNKNOWN" in answer.upper() and len(answer) < 20:
            return None
        return answer
    except Exception as e:
        logger.warning("SPEC-GEN: Self-clarification failed: {}".format(e))
        return None


# ─────────────────────────────────────────────────────────────────────
# 2. Prompt Construction
# ─────────────────────────────────────────────────────────────────────

SPEC_SYSTEM_PROMPT = """You are a specification expert for Java bug repair.

You will receive information about a buggy Java method. Your task is to produce a precise behavioral specification — what the method SHOULD do and what is WRONG with it. You are an ANALYST, not a fixer. Describe the problem clearly; do NOT prescribe how to fix it.

## How to Analyze

### Step 1: Read the Javadoc carefully
The Javadoc comment above the method is the developer's documented intent. Look for:
- What the method should RETURN in normal and edge cases
- What EXCEPTIONS it should throw and when
- Special case handling (NaN, null, overflow, boundary values etc.)
- References to OTHER methods

### Step 2: Compare Javadoc to code
Find CONTRADICTIONS between what the Javadoc says and what the code does:
- Javadoc says "throws X" but code doesn't check?
- Javadoc says "returns Y" but code returns something else?
- Javadoc says "ignores Z" but code uses Z?

### Step 3: Check the failing test
The test shows correct behavior:
- What input does the test provide?
- What output does it expect?
- Does it expect an exception or edge cases?

### Step 4: Look for patterns in sibling and peer methods
If other overloads (siblings) or methods with the same signature shape (peers) exist, they reveal the class's design pattern:
- Do peer methods (e.g., subtract, multiply, divide for a buggy add) include explicit guards/checks, or do they rely on natural language-level behavior (e.g., IEEE 754 NaN propagation)?
- If NO peer method adds a guard for the edge case, the fix is likely to SIMPLIFY or REMOVE broken code, not to ADD a new check.
- If ALL peer methods include a specific check that the buggy method is missing, the fix is likely to ADD that check.
- State this pattern observation explicitly in your code_violations.

### Step 5: Note FAULT_OF_OMISSION markers
If the buggy lines section contains "FAULT_OF_OMISSION":
- This does NOT necessarily mean code needs to be ADDED. It means the fault is at or near this location.
- The fix could be: (a) adding a missing guard/check, (b) REMOVING or SIMPLIFYING incorrect code nearby, or (c) changing existing logic.
- Use the Javadoc, test expectations, and peer methods to determine WHICH of these applies.
- If peer methods do NOT have a guard for this case, the fix is likely removal/simplification, not addition.
- When the code contains logic that CONTRADICTS the Javadoc (e.g., a special-case branch the Javadoc says should not exist), explicitly state "this code should be DELETED or SIMPLIFIED" in code_violations. Do not default to "add a check" when removal is the correct approach.

### Step 6: Choosing fix_direction
- ADD_CODE: Javadoc specifies behavior that has no code implementing it at all.
- DELETE_CODE: Existing code contradicts the Javadoc or adds unwanted behavior. Example: Javadoc says "returns X" but code has a guard that throws/returns something else — the guard is the bug, delete it.
- MODIFY_LOGIC: Existing code has the right structure but wrong values, operators, or method calls (e.g., retainAll instead of removeAll).
- SIMPLIFY: Code is overly complex; a simpler version would satisfy the Javadoc.

Common mistake: If you see code comments like "// handle case X" with implementation below, do NOT assume the implementation is missing. The implementation might BE the bug. Check if peer methods have similar logic — if they don't, fix_direction is likely DELETE_CODE.

## Output
Return ONLY valid JSON (no markdown fences, no extra text):
{
  "purpose": "One sentence: what this method should do",
  "javadoc_key_rules": ["Each important behavioral rule extracted from the Javadoc"],
  "code_violations": ["Each specific way the current code violates the Javadoc or tests — include line numbers and variable names"],
  "test_expectation": "What the failing test expects (input -> expected output)",
  "rules": ["Rule 1: ...", "Rule 2: ...", "(up to 8 behavioral rules the correct implementation must satisfy)"],
  "fix_target_line": "The line number where the bug is located (from the buggy lines info)",
  "fix_targets": [{"line": "line_number", "description": "what is wrong at this location"}],
  "fix_direction": "One of: ADD_CODE | DELETE_CODE | MODIFY_LOGIC | SIMPLIFY — the strategy that best matches the Javadoc + peer pattern evidence",
  "confidence": "HIGH | LOW — how confident you are in the diagnosis based on Javadoc clarity",
  "clarifying_question": "If confidence is LOW: a single yes/no or A-vs-B question whose answer would resolve the ambiguity. If confidence is HIGH, set to null."
}

CRITICAL:
- You are producing a DIAGNOSIS, not a prescription. Describe WHAT is wrong, not HOW to fix it.
- ONLY reference methods, fields, classes visible in the provided code context.
- NEVER invent API calls or method names not shown in the code.
- Be SPECIFIC about variable names and line numbers in code_violations.
- NEVER use hedging language like "possibly", "might", "review", "consider", "may need to". Every code_violation MUST state a specific discrepancy, not "there may be an issue".
- Each code_violation should be concrete enough that a developer can locate the exact problem in the code.
- Set confidence to LOW only when the Javadoc is genuinely ambiguous or missing critical behavioral details. If you can determine the violation from test + Javadoc + peer methods, confidence should be HIGH.
- The fix must work for ARBITRARY inputs, not just the specific test values. Never suggest hardcoding expected outputs."""


def build_spec_prompt(project_name, bug_index, buggy_lines_info, javadoc,
                      buggy_method_body, code_window, test_failure, test_source,
                      sibling_methods, class_header, extra_methods=None,
                      peer_methods=None):
    """Assemble the user prompt."""
    sections = []

    sections.append("# Bug: {}-{}".format(project_name, bug_index))
    sections.append("")

    if javadoc:
        sections.append("## 1. Javadoc (Developer's Documented Intent)")
        sections.append("```java")
        sections.append(javadoc)
        sections.append("```")
        sections.append("")

    if buggy_lines_info:
        sections.append("## 2. Buggy Lines (Exact Location)")
        sections.append(buggy_lines_info)
        sections.append("")

    if buggy_method_body:
        sections.append("## 3. Buggy Method Code (lines marked >>> are buggy)")
        sections.append("```java")
        sections.append(buggy_method_body[:3500])
        sections.append("```")
        sections.append("")
    elif code_window:
        sections.append("## 3. Code Context (+/-75 lines)")
        sections.append("```java")
        sections.append(code_window[:4000])
        sections.append("```")
        sections.append("")

    if extra_methods:
        sections.append("## 3b. Additional Buggy Method(s) (multi-location bug)")
        for em in extra_methods:
            sections.append("```java")
            sections.append(em[:2500])
            sections.append("```")
        sections.append("")

    if test_failure:
        sections.append("## 4. Test Failure Output")
        sections.append(test_failure[:1500])
        sections.append("")

    if test_source:
        sections.append("## 5. Failing Test Source Code")
        sections.append("```java")
        sections.append(test_source[:2000])
        sections.append("```")
        sections.append("")

    if sibling_methods:
        sections.append("## 6. Sibling Methods (Other Overloads — may show correct pattern)")
        sections.append("```java")
        sections.append(sibling_methods[:2500])
        sections.append("```")
        sections.append("")

    if peer_methods:
        sections.append("## 6b. Peer Methods (Same signature shape — shows how similar operations are implemented)")
        sections.append("These methods have the same return type and parameter types as the buggy method.")
        sections.append("Compare their implementation pattern to the buggy method — do they add guards/checks, or do they keep the logic simple?")
        sections.append("```java")
        sections.append(peer_methods[:2500])
        sections.append("```")
        sections.append("")

    if class_header:
        sections.append("## 7. Class Fields and Constants")
        sections.append("```java")
        sections.append(class_header[:1500])
        sections.append("```")
        sections.append("")

    sections.append("## Task")
    sections.append("Generate a behavioral specification as JSON.")
    sections.append("Focus on what the Javadoc says vs what the code actually does.")
    sections.append("ONLY reference methods and fields visible in the code above.")

    return "\n".join(sections)


# ─────────────────────────────────────────────────────────────────────
# 3. Main Entry Point
# ─────────────────────────────────────────────────────────────────────

def generate_spec(project_name, bug_index, localization_info, test_results,
                  model="gpt-4o-mini", workspace="auto_gpt_workspace"):
    """Generate a behavioral specification for the given bug.

    Called from base.py __init__ at agent startup.
    """
    logger.info("SPEC-GEN: Generating spec for {}-{}".format(project_name, bug_index))

    try:
        # ── Phase 1: Gather all information ──
        source_info = read_buggy_source(project_name, bug_index, workspace)
        buggy_methods_str = read_buggy_methods(project_name, bug_index)
        buggy_method_name = _extract_method_name(buggy_methods_str)
        trigger_classes, trigger_content = read_trigger_tests(project_name, bug_index)
        test_code = read_failing_test_code(project_name, bug_index, workspace)

        # Use trigger_tests stack traces as fallback test failure info
        effective_test_failure = test_results if test_results else trigger_content

        javadoc = ""
        method_body = ""
        extra_methods = []  # Additional method bodies for multi-location bugs
        if source_info["lines"] and source_info["buggy_entries"]:
            disk_lines = [line_text for _, line_text in source_info["lines"]]
            first_line_num = source_info["buggy_entries"][0][1]
            javadoc = extract_javadoc(disk_lines, first_line_num)

            if source_info["full_source"]:
                method_body = extract_buggy_method_body(source_info["full_source"], first_line_num)

                # Extract additional method bodies for multi-location bugs
                seen_methods = {method_body[:80]} if method_body else set()
                for _, ln, _ in source_info["buggy_entries"][1:]:
                    extra_body = extract_buggy_method_body(source_info["full_source"], ln)
                    if extra_body and extra_body[:80] not in seen_methods:
                        seen_methods.add(extra_body[:80])
                        extra_jd = extract_javadoc(disk_lines, ln)
                        if extra_jd:
                            extra_methods.append("// Additional buggy location:\n" + extra_jd + "\n" + extra_body)
                        else:
                            extra_methods.append("// Additional buggy location:\n" + extra_body)

        sibling_methods = ""
        peer_methods = ""
        if buggy_method_name and source_info["file_path"] and source_info["buggy_entries"]:
            project_dir = "{}_{}_buggy".format(project_name.lower(), bug_index)
            first_line_num = source_info["buggy_entries"][0][1]
            sibling_methods = extract_sibling_methods(
                workspace, project_dir, source_info["file_path"],
                buggy_method_name, first_line_num
            )
            peer_methods = extract_peer_methods(
                workspace, project_dir, source_info["file_path"],
                buggy_method_name, first_line_num
            )

        class_header = ""
        if source_info["file_path"]:
            project_dir = "{}_{}_buggy".format(project_name.lower(), bug_index)
            class_header = extract_class_header(workspace, project_dir, source_info["file_path"])

        buggy_lines_info = ""
        if source_info["buggy_entries"]:
            bl_lines = []
            for fp, ln, code in source_info["buggy_entries"]:
                if code == "FAULT_OF_OMISSION":
                    bl_lines.append("  {} # Line {} (FAULT_OF_OMISSION — code at or near this line is implicated; the fix may involve adding, changing, OR removing code)".format(fp, ln))
                elif code:
                    bl_lines.append("  {} # Line {}: {}".format(fp, ln, code))
                else:
                    bl_lines.append("  {} # Line {}".format(fp, ln))
            buggy_lines_info = "\n".join(bl_lines)

        # ── LOG: gathered info ──
        gathered_meta = {
            "project": project_name, "bug_index": str(bug_index), "model": model,
            "buggy_file": source_info["file_path"],
            "buggy_method_name": buggy_method_name,
            "javadoc_found": bool(javadoc), "javadoc_length": len(javadoc),
            "method_body_found": bool(method_body), "method_body_length": len(method_body),
            "extra_methods_count": len(extra_methods),
            "sibling_methods_found": bool(sibling_methods), "sibling_methods_length": len(sibling_methods),
            "peer_methods_found": bool(peer_methods), "peer_methods_length": len(peer_methods),
            "class_header_found": bool(class_header),
            "trigger_tests_found": len(trigger_classes),
            "test_code_found": bool(test_code), "test_code_length": len(test_code),
        }
        _save_spec_log(project_name, bug_index, "gathered_info_json", gathered_meta)

        # ── Phase 2: Build prompt ──
        user_prompt = build_spec_prompt(
            project_name=project_name, bug_index=bug_index,
            buggy_lines_info=buggy_lines_info, javadoc=javadoc,
            buggy_method_body=method_body, code_window=source_info["window"],
            test_failure=effective_test_failure, test_source=test_code,
            sibling_methods=sibling_methods, class_header=class_header,
            extra_methods=extra_methods, peer_methods=peer_methods,
        )

        # ── LOG: full prompt ──
        full_prompt_log = "=== SYSTEM PROMPT ===\n{}\n\n=== USER PROMPT ===\n{}".format(
            SPEC_SYSTEM_PROMPT, user_prompt)
        _save_spec_log(project_name, bug_index, "input_prompt", full_prompt_log)

        # ── Phase 3: Call LLM ──
        from langchain.chat_models import ChatOpenAI
        from langchain.schema.messages import HumanMessage, SystemMessage

        chat = ChatOpenAI(model=model)
        messages = [
            SystemMessage(content=SPEC_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ]
        response = chat.invoke(messages)
        raw_response = response.content

        logger.info("SPEC-GEN: LLM returned {} chars".format(len(raw_response)))
        _save_spec_log(project_name, bug_index, "raw_response", raw_response)

        # ── Phase 4: Parse JSON ──
        spec_json = None
        try:
            json_match = re.search(r"```(?:json)?\s*(.*?)```", raw_response, re.DOTALL)
            if json_match:
                spec_json = json.loads(json_match.group(1).strip())
            else:
                spec_json = json.loads(raw_response.strip())
        except json.JSONDecodeError:
            logger.info("SPEC-GEN: Could not parse JSON, using raw text")

        if spec_json:
            _save_spec_log(project_name, bug_index, "parsed_json", spec_json)
        else:
            _save_spec_log(project_name, bug_index, "parsed_json",
                           {"_parse_failed": True, "_raw_preview": raw_response[:500]})

        # ── Phase 4b: Verify spec ──
        from autogpt.commands.spec_verifier import verify_spec

        verify_context = method_body if method_body else source_info.get("window", "")
        verify_result = verify_spec(
            spec_json=spec_json,
            source_code_context=verify_context,
            buggy_lines_info=buggy_lines_info,
            test_info=effective_test_failure,
            model=model,
        )
        _save_spec_log(project_name, bug_index, "verify_result_json", verify_result)
        logger.info("SPEC-GEN: Verification verdict: {}".format(verify_result["verdict"]))

        if verify_result["verdict"] == "REJECT" and verify_result.get("feedback_prompt"):
            logger.info("SPEC-GEN: Spec REJECTED, regenerating with feedback...")

            # Rebuild prompt with verifier feedback appended
            retry_prompt = user_prompt + "\n" + verify_result["feedback_prompt"]
            _save_spec_log(project_name, bug_index, "retry_prompt", retry_prompt)

            retry_messages = [
                SystemMessage(content=SPEC_SYSTEM_PROMPT),
                HumanMessage(content=retry_prompt),
            ]
            retry_response = chat.invoke(retry_messages)
            raw_response_v2 = retry_response.content

            logger.info("SPEC-GEN: Retry LLM returned {} chars".format(len(raw_response_v2)))
            _save_spec_log(project_name, bug_index, "retry_raw_response", raw_response_v2)

            # Parse the retry response
            spec_json_v2 = None
            try:
                json_match_v2 = re.search(r"```(?:json)?\s*(.*?)```", raw_response_v2, re.DOTALL)
                if json_match_v2:
                    spec_json_v2 = json.loads(json_match_v2.group(1).strip())
                else:
                    spec_json_v2 = json.loads(raw_response_v2.strip())
            except json.JSONDecodeError:
                logger.info("SPEC-GEN: Retry JSON parse failed, keeping original spec")

            if spec_json_v2:
                _save_spec_log(project_name, bug_index, "retry_parsed_json", spec_json_v2)
                spec_json = spec_json_v2
                raw_response = raw_response_v2
                logger.info("SPEC-GEN: Using revised spec after verification feedback")
            else:
                logger.info("SPEC-GEN: Retry parse failed, using original spec")

        # ── Phase 4c: Self-clarification for LOW confidence specs ──
        if spec_json and spec_json.get("confidence") == "LOW" and spec_json.get("clarifying_question"):
            logger.info("SPEC-GEN: Low confidence — self-clarifying: {}".format(
                spec_json["clarifying_question"]))

            answer = _answer_clarifying_question(
                spec_json["clarifying_question"],
                test_code, effective_test_failure, method_body, model,
            )

            if answer:
                logger.info("SPEC-GEN: Self-clarification answer: {}".format(answer[:200]))
                _save_spec_log(project_name, bug_index, "clarification",
                               {"question": spec_json["clarifying_question"],
                                "answer": answer})
                spec_json["developer_clarification"] = "Q: {} A: {}".format(
                    spec_json["clarifying_question"], answer)
            else:
                logger.info("SPEC-GEN: Self-clarification returned UNKNOWN, skipping")

        # ── Phase 5: Format for prompt injection ──
        prompt_section = format_spec_for_prompt(spec_json, raw_response)
        _save_spec_log(project_name, bug_index, "injected_prompt", prompt_section)

        logger.info("SPEC-GEN: Success. Prompt section: {} chars".format(len(prompt_section)))
        return {"success": True, "spec_json": spec_json, "prompt_section": prompt_section, "error": None}

    except Exception as e:
        import traceback
        err_msg = "{}\n{}".format(e, traceback.format_exc())
        logger.info("SPEC-GEN: Failed: {}".format(err_msg))
        _save_spec_log(project_name, bug_index, "error", err_msg)
        return {"success": False, "spec_json": None, "prompt_section": "", "error": str(e)}


def format_spec_for_prompt(spec_json, raw_text):
    """Format the spec into a readable section for the agent's context prompt."""
    header = "## Behavioral Specification of Buggy Method\n\n"

    if spec_json and isinstance(spec_json, dict):
        parts = [header]

        if spec_json.get("purpose"):
            parts.append("**Purpose:** {}\n".format(spec_json["purpose"]))

        if spec_json.get("javadoc_key_rules"):
            parts.append("**Javadoc Rules:**")
            for i, rule in enumerate(spec_json["javadoc_key_rules"], 1):
                parts.append("  {}. {}".format(i, rule))
            parts.append("")

        if spec_json.get("code_violations"):
            parts.append("**Code Violations (what's wrong):**")
            for i, v in enumerate(spec_json["code_violations"], 1):
                parts.append("  {}. {}".format(i, v))
            parts.append("")

        if spec_json.get("test_expectation"):
            parts.append("**What the tests expect:** {}\n".format(spec_json["test_expectation"]))

        if spec_json.get("rules"):
            parts.append("**Behavioral rules the correct implementation must satisfy:**")
            for i, rule in enumerate(spec_json["rules"], 1):
                parts.append("  {}. {}".format(i, rule))
            parts.append("")

        if spec_json.get("fix_target_line"):
            parts.append("**Fix target line:** {}\n".format(spec_json["fix_target_line"]))

        if spec_json.get("fix_targets"):
            parts.append("**Fix targets:**")
            for i, target in enumerate(spec_json["fix_targets"], 1):
                parts.append("  {}. Line {}: {}".format(i, target.get("line", "?"), target.get("description", "")))
            parts.append("")

        if spec_json.get("fix_direction"):
            parts.append("**Fix direction:** {}\n".format(spec_json["fix_direction"]))
            if spec_json["fix_direction"] == "DELETE_CODE":
                parts.append("**ACTION:** The fix requires REMOVING existing code. Use the `deletions` field in write_fix to delete the buggy lines. If replacement code is needed, use `insertions` after deleting.\n")
            elif spec_json["fix_direction"] == "SIMPLIFY":
                parts.append("**ACTION:** The fix requires SIMPLIFYING existing code. Consider deleting unnecessary guards, branches, or logic rather than adding new code.\n")

        if spec_json.get("confidence"):
            parts.append("**Diagnosis confidence:** {}\n".format(spec_json["confidence"]))

        if spec_json.get("developer_clarification"):
            parts.append("**Developer clarification:** {}\n".format(spec_json["developer_clarification"]))

        parts.append("**IMPORTANT:** This specification describes WHAT is wrong, not HOW to fix it. Use the code_violations and fix targets above to understand the problem, then determine the fix approach yourself based on the code.")
        parts.append("**CRITICAL:** Do NOT add trailing comments (// ...) to modified or inserted lines. Write CLEAN code only — comments can cause write_fix to fail.")
        parts.append("**ANTI-OVERFITTING:** The fix must work for arbitrary inputs, not just the specific test values. Never hardcode expected outputs or special-case the exact inputs from the failing test.")

        return "\n".join(parts)

    else:
        return header + str(raw_text)[:2000]