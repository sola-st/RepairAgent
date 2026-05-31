
import json
import re
import logging

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────
# Spec Verifier — validates generated specs before they reach the agent
# ─────────────────────────────────────────────────────────────────────

VERIFIER_SYSTEM_PROMPT = """You are a specification quality reviewer for Java bug repair.

You will receive a generated behavioral specification (JSON) along with the source code context it was derived from. The spec is a DIAGNOSTIC document — it describes what the method should do and what is wrong, NOT how to fix it. Your job is to verify whether the diagnosis is accurate, code-grounded, and useful.

## Verification Checklist

### 1. Code Grounding
- Do variable names, method names, and class names referenced in code_violations actually appear in the code?
- Do line numbers referenced in code_violations exist within the buggy method?
- Does the spec reference APIs or methods NOT visible in the provided code context?

### 2. Violation Accuracy
- Does each code_violation describe a REAL discrepancy between the Javadoc/expected behavior and the actual code?
- Are the violations specific enough to locate the exact problem? (e.g., "Line 95 increments by codepoint count instead of char count" NOT "there may be an issue with the loop")
- Do the violations match what the test_expectation says the test expects?

### 3. Scenario Coverage
- For each code_violation: is there a clear condition under which the violation triggers and what the correct behavior should be?
- Does the spec address ALL buggy lines, or does it only discuss one location while ignoring others?
- Are the rules concrete enough that a developer could write a test for each one?

### 4. Language Quality
- Any hedging language? ("possibly", "might", "consider", "review", "may need to")
- Are code_violations specific and concrete, not vague?
- Does the spec accidentally prescribe HOW to fix instead of describing WHAT is wrong? (It should NOT contain fix instructions)

## Output
Return ONLY valid JSON (no markdown fences, no extra text):
{
  "verdict": "ACCEPT" or "REJECT",
  "issues": [
    {
      "check": "which check failed (code_grounding | violation_accuracy | scenario_coverage | language_quality)",
      "severity": "CRITICAL or WARNING",
      "description": "specific description of the problem",
      "suggestion": "how to fix this in the spec"
    }
  ],
  "summary": "One sentence overall assessment"
}

CRITICAL rules for your review:
- ACCEPT specs that are good enough to guide repair, even if imperfect. Minor issues → WARNING, not REJECT.
- REJECT only when the spec contains WRONG diagnosis — code_violations that describe non-existent problems, references to fabricated APIs/methods, or violations that contradict the test expectations.
- Be STRICT about code grounding: references to non-existent methods/variables/line numbers are CRITICAL.
- Be STRICT about violation accuracy: a code_violation that describes the wrong problem will mislead the repair agent.
- Hedging language is a WARNING, not CRITICAL — vague specs are less useful but not actively harmful."""


def verify_spec(spec_json, source_code_context, buggy_lines_info, test_info,
                model="gpt-4o-mini"):
    """Verify a generated spec against the source code context.

    Args:
        spec_json: The parsed spec JSON from generate_spec()
        source_code_context: The buggy method body or code window
        buggy_lines_info: Formatted buggy lines string
        test_info: Test failure or trigger test content
        model: LLM model to use for verification

    Returns:
        dict with keys: verdict (ACCEPT/REJECT), issues (list), summary (str),
              feedback_prompt (str or None — for regeneration if rejected)
    """
    if not spec_json or not isinstance(spec_json, dict):
        logger.info("SPEC-VERIFY: No valid spec to verify, skipping")
        return {"verdict": "SKIP", "issues": [], "summary": "No spec to verify",
                "feedback_prompt": None}

    if spec_json.get("_parse_failed"):
        logger.info("SPEC-VERIFY: Spec failed to parse, skipping verification")
        return {"verdict": "SKIP", "issues": [], "summary": "Spec parse failed",
                "feedback_prompt": None}

    # Build the verification prompt
    user_prompt = _build_verify_prompt(spec_json, source_code_context,
                                       buggy_lines_info, test_info)

    try:
        from langchain.chat_models import ChatOpenAI
        from langchain.schema.messages import HumanMessage, SystemMessage

        chat = ChatOpenAI(model=model)
        messages = [
            SystemMessage(content=VERIFIER_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ]
        response = chat.invoke(messages)
        raw = response.content

        logger.info("SPEC-VERIFY: Verifier returned {} chars".format(len(raw)))

        # Parse the verifier response
        result = _parse_verifier_response(raw)

        # Build feedback prompt for regeneration if rejected
        if result["verdict"] == "REJECT":
            result["feedback_prompt"] = _build_feedback_prompt(result["issues"])
        else:
            result["feedback_prompt"] = None

        return result

    except Exception as e:
        logger.info("SPEC-VERIFY: Verification failed: {}".format(e))
        # If verification itself fails, accept the spec rather than blocking
        return {"verdict": "ACCEPT", "issues": [],
                "summary": "Verification error: {}".format(e),
                "feedback_prompt": None}


def _build_verify_prompt(spec_json, source_code, buggy_lines_info, test_info):
    """Build the user prompt for the verifier LLM."""
    sections = []

    sections.append("# Spec to Verify")
    sections.append("```json")
    sections.append(json.dumps(spec_json, indent=2))
    sections.append("```")
    sections.append("")

    if source_code:
        sections.append("# Source Code Context")
        sections.append("```java")
        sections.append(str(source_code)[:3500])
        sections.append("```")
        sections.append("")

    if buggy_lines_info:
        sections.append("# Buggy Lines")
        sections.append(buggy_lines_info)
        sections.append("")

    if test_info:
        sections.append("# Test Information")
        sections.append(str(test_info)[:1500])
        sections.append("")

    sections.append("# Task")
    sections.append("Verify this spec against the code context above.")
    sections.append("Check all 4 criteria (code grounding, violation accuracy, "
                    "scenario coverage, language quality).")

    return "\n".join(sections)


def _parse_verifier_response(raw_response):
    """Parse the verifier LLM response into a structured result."""
    try:
        json_match = re.search(r"```(?:json)?\s*(.*?)```", raw_response, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group(1).strip())
        else:
            result = json.loads(raw_response.strip())

        # Normalize verdict
        verdict = result.get("verdict", "ACCEPT").upper().strip()
        if verdict not in ("ACCEPT", "REJECT"):
            verdict = "ACCEPT"

        return {
            "verdict": verdict,
            "issues": result.get("issues", []),
            "summary": result.get("summary", ""),
            "feedback_prompt": None,
        }
    except (json.JSONDecodeError, AttributeError):
        logger.info("SPEC-VERIFY: Could not parse verifier response, defaulting to ACCEPT")
        return {
            "verdict": "ACCEPT",
            "issues": [],
            "summary": "Verifier response unparseable: {}".format(raw_response[:200]),
            "feedback_prompt": None,
        }


def _build_feedback_prompt(issues):
    """Build a feedback section to append to the regeneration prompt."""
    if not issues:
        return None

    lines = []
    lines.append("\n## IMPORTANT: Previous spec was REJECTED by verification. Fix these issues:\n")

    critical_issues = [i for i in issues if i.get("severity") == "CRITICAL"]
    warning_issues = [i for i in issues if i.get("severity") != "CRITICAL"]

    if critical_issues:
        lines.append("### CRITICAL issues (MUST fix):")
        for i, issue in enumerate(critical_issues, 1):
            lines.append("  {}. [{}] {}".format(i, issue.get("check", "?"),
                                                  issue.get("description", "")))
            if issue.get("suggestion"):
                lines.append("     FIX: {}".format(issue["suggestion"]))
        lines.append("")

    if warning_issues:
        lines.append("### Warnings (should fix if possible):")
        for i, issue in enumerate(warning_issues, 1):
            lines.append("  {}. [{}] {}".format(i, issue.get("check", "?"),
                                                  issue.get("description", "")))
        lines.append("")

    lines.append("Generate a REVISED spec that addresses the critical issues above.")
    lines.append("Keep the parts that were correct. Only fix what was flagged.")

    return "\n".join(lines)
