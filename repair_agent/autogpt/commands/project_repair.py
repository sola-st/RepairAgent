"""Generic (non-Defects4J) project repair backend.

This module lets RepairAgent repair an *arbitrary* Maven or Gradle Java project
that has a failing test, instead of only Defects4J bugs. It is an additive,
parallel path: the Defects4J flow is never touched. It is activated when
``config.repair_mode == "generic"`` (default is ``"defects4j"``).

Design
------
The agent loop, prompt construction, and navigation commands are
project-agnostic and reused as-is. Only a handful of operations are
Defects4J-specific (see GENERIC_REPAIR_HANDOFF.md):

* **A. localize**          -> :func:`generic_localize`         (stack-trace based)
* **B. initial test run**  -> :func:`generic_initial_test_report`
* **C. test oracle**       -> :func:`generic_run_tests`        (mvn/gradle + JUnit XML)
* **D. restore**           -> :func:`generic_restore`          (git checkout --)

These four functions are dispatched to from the existing seams in
``defects4j.py`` / ``base.py`` when ``repair_mode == "generic"``.

A small JSON *sidecar* file (``.repair_generic.json``) is written into the
workspace project directory by the ``fix-project`` CLI command. It records the
build tool, the optional module subdir, and the targeted failing test(s). The
backend reads it so the seam functions keep the same ``(project_name, bug_index,
workspace)`` signatures as their Defects4J counterparts.

Everything in this module is import-light and the pure helpers (command
construction, JUnit XML parsing, stack-trace parsing) take no external
dependencies, so they are unit-testable without a real Maven/Gradle/Java
toolchain.
"""

from __future__ import annotations

import glob
import json
import os
import re
import subprocess
import xml.etree.ElementTree as ET
from typing import Optional

from autogpt.logs import logger

# Name of the per-project sidecar config the CLI writes into the workspace dir.
SIDECAR_NAME = ".repair_generic.json"

# Test-run timeout (seconds). Real suites can be slow; this guards against hangs.
DEFAULT_TEST_TIMEOUT = 1800

# Frame prefixes that never point at the project's own code.
_FRAMEWORK_PREFIXES = (
    "org.junit", "junit.", "org.testng", "org.mockito", "org.hamcrest",
    "org.assertj", "org.apache.maven", "org.gradle", "worker.org.gradle",
    "jdk.", "java.", "javax.", "sun.", "com.sun.", "org.openjdk",
)


# ---------------------------------------------------------------------------
# Workspace / sidecar helpers
# ---------------------------------------------------------------------------
def project_dir(project_name: str, bug_index, workspace) -> str:
    """Path to the buggy project copy in the workspace.

    Uses the same ``<name>_<index>_buggy`` shape as the Defects4J path so the
    navigation commands and ``preprocess_paths`` keep working unchanged.
    """
    folder = "{}_{}_buggy".format(str(project_name).lower(), bug_index)
    return os.path.join(workspace, folder)


def read_sidecar(proj_dir: str) -> dict:
    """Read the generic-mode sidecar config from a project directory.

    Returns an empty dict (with sensible auto-detected defaults applied by the
    caller) if the sidecar is missing or unreadable.
    """
    path = os.path.join(proj_dir, SIDECAR_NAME)
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError) as e:
        logger.warn(f"generic repair: could not read sidecar {path}: {e}")
        return {}


def write_sidecar(proj_dir: str, data: dict) -> None:
    """Persist the generic-mode sidecar config into a project directory."""
    with open(os.path.join(proj_dir, SIDECAR_NAME), "w") as f:
        json.dump(data, f, indent=2)


def module_dir(proj_dir: str, sidecar: dict) -> str:
    """Resolve the build module directory (single-module: the project root)."""
    sub = (sidecar or {}).get("module") or ""
    return os.path.join(proj_dir, sub) if sub else proj_dir


# ---------------------------------------------------------------------------
# Build-tool detection + command construction (pure, unit-testable)
# ---------------------------------------------------------------------------
def detect_build_tool(directory: str) -> Optional[str]:
    """Auto-detect the build tool: 'maven', 'gradle', or None."""
    if os.path.exists(os.path.join(directory, "pom.xml")):
        return "maven"
    if os.path.exists(os.path.join(directory, "build.gradle")) or os.path.exists(
        os.path.join(directory, "build.gradle.kts")
    ):
        return "gradle"
    return None


def build_compile_cmd(build_tool: str) -> str:
    """Command to compile (without running tests)."""
    if build_tool == "maven":
        return "mvn -q -DskipTests compile"
    if build_tool == "gradle":
        return "gradle compileJava"
    raise ValueError(f"Unknown build tool: {build_tool}")


def build_test_cmd(build_tool: str, test_target: Optional[str] = None) -> str:
    """Command to run a single test (``Class#method`` / ``Class``) or the suite.

    ``test_target`` of ``None`` runs the whole suite (regression check).
    """
    if build_tool == "maven":
        if test_target:
            return f"mvn -q -Dtest={test_target} test"
        return "mvn -q test"
    if build_tool == "gradle":
        if test_target:
            # Gradle uses dotted form: Class.method
            return "gradle test --tests {}".format(test_target.replace("#", "."))
        return "gradle test"
    raise ValueError(f"Unknown build tool: {build_tool}")


def reports_dir(build_tool: str, mod_dir: str) -> str:
    """Directory holding the JUnit XML result files for a build tool."""
    if build_tool == "maven":
        return os.path.join(mod_dir, "target", "surefire-reports")
    if build_tool == "gradle":
        return os.path.join(mod_dir, "build", "test-results", "test")
    raise ValueError(f"Unknown build tool: {build_tool}")


# ---------------------------------------------------------------------------
# JUnit XML parsing (pure, unit-testable)
# ---------------------------------------------------------------------------
def parse_junit_xml_dir(directory: str) -> dict:
    """Parse all JUnit XML reports in ``directory``.

    Returns a dict with keys: ``total``, ``failures``, ``errors``,
    ``failed`` (list of ``Class#method`` names), ``details`` (list of
    human-readable failure blocks).
    """
    out = {"total": 0, "failures": 0, "errors": 0, "failed": [], "details": []}
    if not os.path.isdir(directory):
        return out

    for xml_path in sorted(glob.glob(os.path.join(directory, "*.xml"))):
        try:
            root = ET.parse(xml_path).getroot()
        except (ET.ParseError, OSError) as e:
            logger.warn(f"generic repair: skipping unparsable report {xml_path}: {e}")
            continue
        suites = [root] if root.tag == "testsuite" else root.findall("testsuite")
        for suite in suites:
            for case in suite.findall("testcase"):
                out["total"] += 1
                classname = case.get("classname", "")
                name = case.get("name", "")
                fq = "{}#{}".format(classname, name) if classname else name
                failure = case.find("failure")
                error = case.find("error")
                node = failure if failure is not None else error
                if node is None:
                    continue
                if failure is not None:
                    out["failures"] += 1
                else:
                    out["errors"] += 1
                out["failed"].append(fq)
                msg = (node.get("message") or "").strip()
                body = (node.text or "").strip()
                block = "--- {}".format(fq)
                if msg:
                    block += "\n{}".format(msg)
                if body:
                    block += "\n{}".format(body)
                out["details"].append(block)
    return out


def format_fail_report(parsed: dict) -> str:
    """Format parsed results into the same shape ``extract_fail_report`` returns.

    The agent detects a plausible patch by the substring ``"0 failing test
    cases"`` (see ``write_fix`` / ``try_fixes`` in defects4j.py), so the wording
    of the count line is load-bearing and must match.
    """
    n = len(parsed.get("failed", []))
    header = "There are {} failing test cases, here is the full log of failing cases:\n".format(n)
    return header + "\n\n".join(parsed.get("details", []))


# ---------------------------------------------------------------------------
# Stack-trace localization (pure, unit-testable)
# ---------------------------------------------------------------------------
_FRAME_RE = re.compile(
    r"at\s+([\w.$]+)\.([\w<>$]+)\(([\w$]+\.java):(\d+)\)"
)


def parse_stack_trace(trace_text: str, project_packages=None) -> list:
    """Extract project-owned frames from a Java stack trace.

    Each returned item is a dict ``{class, method, file, line}``. JUnit/JDK/
    library frames are filtered out. If ``project_packages`` is given, only
    frames whose class starts with one of those package prefixes are kept.
    """
    frames = []
    for m in _FRAME_RE.finditer(trace_text or ""):
        fqcn, method, fname, line = m.group(1), m.group(2), m.group(3), int(m.group(4))
        if any(fqcn.startswith(p) for p in _FRAMEWORK_PREFIXES):
            continue
        if project_packages and not any(fqcn.startswith(p) for p in project_packages):
            continue
        frames.append(
            {"class": fqcn, "method": method, "file": fname, "line": line}
        )
    # De-duplicate while preserving order (a frame can recur in recursion).
    seen = set()
    unique = []
    for fr in frames:
        key = (fr["class"], fr["method"], fr["line"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(fr)
    return unique


def _fqcn_to_relpath(fqcn: str) -> str:
    """com.foo.Bar$Inner -> com/foo/Bar.java (outer class file)."""
    top = fqcn.split("$", 1)[0]
    return top.replace(".", "/") + ".java"


def _find_source_file(proj_dir: str, fqcn: str) -> Optional[str]:
    """Locate the source file for a class within the project copy."""
    rel = _fqcn_to_relpath(fqcn)
    # Fast path: conventional Maven/Gradle source layout.
    for base in ("src/main/java", "src/test/java", "src/java", ""):
        cand = os.path.join(proj_dir, base, rel) if base else os.path.join(proj_dir, rel)
        if os.path.exists(cand):
            return cand
    # Fallback: walk for the bare file name with matching package suffix.
    target = rel.replace("/", os.sep)
    for root, _dirs, files in os.walk(proj_dir):
        for fn in files:
            full = os.path.join(root, fn)
            if full.endswith(os.sep + target) or full.endswith(target):
                return full
    return None


def _code_window(file_path: str, line: int, radius: int = 8) -> str:
    """Return a numbered code window around ``line`` from ``file_path``."""
    try:
        with open(file_path, encoding="utf8", errors="replace") as f:
            lines = f.readlines()
    except OSError:
        return ""
    start = max(1, line - radius)
    end = min(len(lines), line + radius)
    chunk = []
    for i in range(start, end + 1):
        chunk.append("Line {}:{}".format(i, lines[i - 1].rstrip("\n")))
    return "\n".join(chunk)


def localize_from_trace(proj_dir: str, trace_text: str, project_packages=None) -> str:
    """Build localization prompt text from a stack trace.

    Mirrors what the Defects4J ``get_info`` returns: candidate file/line
    locations with a surrounding code window, so the rest of the agent
    machinery is reused unchanged.
    """
    frames = parse_stack_trace(trace_text, project_packages)
    if not frames:
        return ""
    blocks = [
        "Candidate fault locations derived from the failing test's stack trace "
        "(most likely first):"
    ]
    for fr in frames:
        src = _find_source_file(proj_dir, fr["class"])
        rel = os.path.relpath(src, proj_dir) if src else _fqcn_to_relpath(fr["class"])
        blocks.append(
            "\nIn file: {}  (around line {}), method {}:".format(
                rel, fr["line"], fr["method"]
            )
        )
        if src:
            window = _code_window(src, fr["line"])
            if window:
                blocks.append(window)
    return "\n".join(blocks)


# ---------------------------------------------------------------------------
# subprocess wrapper (single place, easy to mock in tests)
# ---------------------------------------------------------------------------
def _run(cmd: str, cwd: str, timeout: int = DEFAULT_TEST_TIMEOUT):
    """Run a shell command, returning the CompletedProcess."""
    logger.info(f"generic repair: running `{cmd}` in {cwd}")
    return subprocess.run(
        cmd,
        shell=True,
        cwd=cwd,
        capture_output=True,
        encoding="utf8",
        errors="replace",
        timeout=timeout,
    )


# ---------------------------------------------------------------------------
# Seam implementations
# ---------------------------------------------------------------------------
def _resolve(project_name, bug_index, workspace):
    """Resolve (proj_dir, sidecar, build_tool, mod_dir) for the seams."""
    proj_dir = project_dir(project_name, bug_index, workspace)
    sidecar = read_sidecar(proj_dir)
    build_tool = sidecar.get("build_tool") or detect_build_tool(proj_dir)
    mod_dir = module_dir(proj_dir, sidecar)
    return proj_dir, sidecar, build_tool, mod_dir


def _run_suite_capture(build_tool, mod_dir, test_target=None):
    """Run tests, returning (parsed_results, combined_output_text)."""
    cmd = build_test_cmd(build_tool, test_target)
    try:
        res = _run(cmd, mod_dir)
    except subprocess.TimeoutExpired:
        return None, "Test run timed out after {}s.".format(DEFAULT_TEST_TIMEOUT)
    combined = (res.stdout or "") + "\n" + (res.stderr or "")
    if "BUILD FAILURE" in combined or "COMPILATION ERROR" in combined or "BUILD FAILED" in combined:
        # Compilation/build error: surface it, no XML to parse.
        return None, combined
    parsed = parse_junit_xml_dir(reports_dir(build_tool, mod_dir))
    return parsed, combined


def generic_initial_test_report(project_name, bug_index, workspace) -> str:
    """Seam B: run the suite once to capture the initial failing-test output."""
    proj_dir, sidecar, build_tool, mod_dir = _resolve(project_name, bug_index, workspace)
    if not build_tool:
        return "Could not detect a Maven or Gradle build in the project."
    targets = sidecar.get("test_targets") or [None]
    # For the initial report, run the targeted test(s) so the trace is captured.
    all_details = []
    total_failed = 0
    for t in targets:
        parsed, combined = _run_suite_capture(build_tool, mod_dir, t)
        if parsed is None:
            return "Build/compile error while running tests:\n" + combined[-4000:]
        total_failed += len(parsed["failed"])
        all_details.extend(parsed["details"])
        # Persist the raw output so localization can mine the stack trace.
        try:
            with open(os.path.join(proj_dir, "_initial_test_output.txt"), "a", encoding="utf8") as f:
                f.write(combined)
        except OSError:
            pass
    header = "There are {} failing test cases, here is the full log of failing cases:\n".format(
        total_failed
    )
    return header + "\n\n".join(all_details)


def generic_localize(project_name, bug_index, workspace) -> str:
    """Seam A: derive candidate fault locations from the failing test's trace."""
    proj_dir, sidecar, build_tool, mod_dir = _resolve(project_name, bug_index, workspace)
    project_packages = sidecar.get("packages") or None

    # User-provided suspect overrides/augments everything else.
    suspects = sidecar.get("suspects") or []
    pieces = []
    if suspects:
        pieces.append("User-provided suspect locations:")
        for s in suspects:
            pieces.append("  " + str(s))

    trace_text = ""
    trace_path = os.path.join(proj_dir, "_initial_test_output.txt")
    if os.path.exists(trace_path):
        try:
            with open(trace_path, encoding="utf8", errors="replace") as f:
                trace_text = f.read()
        except OSError:
            trace_text = ""
    if not trace_text and build_tool:
        # No captured trace yet: run the targeted test(s) now to get one.
        targets = sidecar.get("test_targets") or [None]
        for t in targets:
            _parsed, combined = _run_suite_capture(build_tool, mod_dir, t)
            trace_text += "\n" + combined

    loc = localize_from_trace(proj_dir, trace_text, project_packages)
    if loc:
        pieces.append(loc)
    elif not suspects:
        # Assertion-based fallback: point at the failing test method body.
        targets = sidecar.get("test_targets") or []
        if targets:
            pieces.append(
                "No application frames were found in the stack trace. The failure "
                "appears to be an assertion in the test(s): {}. Inspect the "
                "assertion and the methods it calls to locate the fault.".format(
                    ", ".join(targets)
                )
            )
        else:
            pieces.append(
                "No localization signal could be derived from the stack trace, and "
                "no failing test was specified. Run the test suite to identify a "
                "failing test first."
            )
    return "\n".join(pieces)


def generic_restore(project_name, bug_index, agent) -> str:
    """Seam D: revert agent edits via git (the project copy is a git repo)."""
    workspace = agent.config.workspace_path
    proj_dir = project_dir(project_name, bug_index, workspace)
    if not os.path.isdir(os.path.join(proj_dir, ".git")):
        return (
            "Cannot restore: the project copy is not a git repository. Generic "
            "mode requires a git repo so edits can be reverted between attempts."
        )
    try:
        # Revert tracked files, then remove untracked files the agent created --
        # but preserve generic-mode/RepairAgent bookkeeping that lives untracked
        # in the project copy (the sidecar, the files index, captured test
        # output). Without these excludes, `git clean` deletes the sidecar after
        # the first restore, and every later cycle loses the targeted-test list
        # and baseline, silently degrading the run.
        cmd = (
            "git checkout -- . && "
            "git clean -fdq "
            "-e {} -e files_index.txt -e _initial_test_output.txt -e '*_test.txt'"
        ).format(SIDECAR_NAME)
        res = _run(cmd, proj_dir, timeout=120)
    except subprocess.TimeoutExpired:
        return "Error: git restore timed out."
    if res.returncode == 0:
        return "The changed files were restored to their original content"
    return "Error restoring with git: {}".format(res.stderr)


def _save_generic_patch(proj_dir: str, agent) -> Optional[str]:
    """Capture ``git diff`` of the (currently patched) project copy and save it.

    Called when a plausible patch is found, *before* restoring. Returns the diff
    text, or None if nothing could be captured.
    """
    if not os.path.isdir(os.path.join(proj_dir, ".git")):
        return None
    try:
        res = _run("git diff", proj_dir, timeout=120)
    except subprocess.TimeoutExpired:
        return None
    diff = res.stdout or ""
    if not diff.strip():
        return None
    # Save next to the experiment outputs if we can find them, else in proj_dir.
    out_name = "plausible_patch.diff"
    try:
        exp_dir = getattr(agent, "experiment_file", None)
        target = proj_dir
        if exp_dir:
            cand = os.path.dirname(os.path.abspath(exp_dir))
            if os.path.isdir(cand):
                target = cand
        with open(os.path.join(target, out_name), "w", encoding="utf8") as f:
            f.write(diff)
        logger.info(f"generic repair: saved plausible patch to {target}/{out_name}")
    except OSError as e:
        logger.warn(f"generic repair: could not save patch: {e}")
    return diff


def generic_run_tests(project_name, bug_index, agent) -> str:
    """Seam C: the test oracle.

    Strategy (handoff §5): validate the targeted test(s) first (fast); only when
    they pass, run the full suite to confirm no regressions. A plausible patch is
    one where the targeted test(s) pass AND no previously-passing test fails.

    Returns a fail-report string. ``"0 failing test cases"`` in the result is
    the success signal the agent looks for.
    """
    workspace = agent.config.workspace_path
    proj_dir, sidecar, build_tool, mod_dir = _resolve(project_name, bug_index, workspace)
    if not build_tool:
        generic_restore(project_name, bug_index, agent)
        return "Could not detect a Maven or Gradle build in the project."

    targets = sidecar.get("test_targets") or [None]

    # Phase 1: targeted test(s) first.
    targeted_failed = []
    targeted_details = []
    for t in targets:
        parsed, combined = _run_suite_capture(build_tool, mod_dir, t)
        if parsed is None:
            generic_restore(project_name, bug_index, agent)
            return "Build/compile error:\n" + combined[-4000:]
        targeted_failed.extend(parsed["failed"])
        targeted_details.extend(parsed["details"])

    if targeted_failed:
        generic_restore(project_name, bug_index, agent)
        return format_fail_report(
            {"failed": targeted_failed, "details": targeted_details}
        )

    # Phase 2: targeted test(s) pass -> full suite regression check.
    parsed, combined = _run_suite_capture(build_tool, mod_dir, None)
    if parsed is None:
        generic_restore(project_name, bug_index, agent)
        return "Build/compile error during regression run:\n" + combined[-4000:]

    baseline_failing = set(sidecar.get("baseline_failing") or [])
    # Regressions = currently-failing tests that were NOT failing at baseline.
    regressions = [f for f in parsed["failed"] if f not in baseline_failing]

    if regressions:
        details = [d for d in parsed["details"]]
        generic_restore(project_name, bug_index, agent)
        return format_fail_report({"failed": regressions, "details": details})

    # Plausible patch: capture the diff before restoring.
    _save_generic_patch(proj_dir, agent)
    generic_restore(project_name, bug_index, agent)
    return (
        "There are 0 failing test cases. The targeted test(s) now pass and no "
        "previously-passing test regressed. A plausible patch has been saved as "
        "plausible_patch.diff for human review."
    )
