"""Unit tests for the generic (non-Defects4J) project repair backend.

All tests are hermetic: no real Maven/Gradle/Java/git is invoked. The pure
helpers (build-tool detection, command construction, JUnit XML parsing,
stack-trace parsing/localization) are exercised directly; the seam functions are
exercised with ``subprocess`` mocked.
"""

import os
import shutil
import subprocess
import textwrap
from types import SimpleNamespace
from unittest import mock

import pytest

from autogpt.commands import project_repair as pr

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


# ---------------------------------------------------------------------------
# Build-tool detection
# ---------------------------------------------------------------------------
def test_detect_build_tool_maven(tmp_path):
    (tmp_path / "pom.xml").write_text("<project/>")
    assert pr.detect_build_tool(str(tmp_path)) == "maven"


def test_detect_build_tool_gradle(tmp_path):
    (tmp_path / "build.gradle").write_text("")
    assert pr.detect_build_tool(str(tmp_path)) == "gradle"


def test_detect_build_tool_gradle_kts(tmp_path):
    (tmp_path / "build.gradle.kts").write_text("")
    assert pr.detect_build_tool(str(tmp_path)) == "gradle"


def test_detect_build_tool_none(tmp_path):
    assert pr.detect_build_tool(str(tmp_path)) is None


# ---------------------------------------------------------------------------
# Command construction
# ---------------------------------------------------------------------------
def test_compile_cmd():
    assert pr.build_compile_cmd("maven") == "mvn -q -DskipTests compile"
    assert pr.build_compile_cmd("gradle") == "gradle compileJava"


def test_build_test_cmd_maven_targeted():
    assert pr.build_test_cmd("maven", "com.foo.BarTest#testThing") == (
        "mvn -q -Dtest=com.foo.BarTest#testThing test"
    )


def test_build_test_cmd_maven_suite():
    assert pr.build_test_cmd("maven", None) == "mvn -q test"


def test_build_test_cmd_gradle_targeted_uses_dotted_form():
    assert pr.build_test_cmd("gradle", "com.foo.BarTest#testThing") == (
        "gradle test --tests com.foo.BarTest.testThing"
    )


def test_build_test_cmd_gradle_suite():
    assert pr.build_test_cmd("gradle", None) == "gradle test"


def test_unknown_build_tool_raises():
    with pytest.raises(ValueError):
        pr.build_test_cmd("ant", None)
    with pytest.raises(ValueError):
        pr.build_compile_cmd("ant")
    with pytest.raises(ValueError):
        pr.reports_dir("ant", "/x")


def test_reports_dir():
    assert pr.reports_dir("maven", "/p").endswith(
        os.path.join("target", "surefire-reports")
    )
    assert pr.reports_dir("gradle", "/p").endswith(
        os.path.join("build", "test-results", "test")
    )


# ---------------------------------------------------------------------------
# JUnit XML parsing
# ---------------------------------------------------------------------------
_PASS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="com.foo.BarTest" tests="2" failures="0" errors="0">
  <testcase classname="com.foo.BarTest" name="testA"/>
  <testcase classname="com.foo.BarTest" name="testB"/>
</testsuite>
"""

_FAIL_XML = """<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="com.foo.BarTest" tests="2" failures="1" errors="0">
  <testcase classname="com.foo.BarTest" name="testA"/>
  <testcase classname="com.foo.BarTest" name="testB">
    <failure message="expected:&lt;1&gt; but was:&lt;2&gt;">java.lang.AssertionError
\tat com.foo.Bar.add(Bar.java:42)</failure>
  </testcase>
</testsuite>
"""

_ERROR_XML = """<?xml version="1.0" encoding="UTF-8"?>
<testsuites>
  <testsuite name="com.foo.BazTest" tests="1" failures="0" errors="1">
    <testcase classname="com.foo.BazTest" name="testBoom">
      <error message="NPE">java.lang.NullPointerException
\tat com.foo.Baz.go(Baz.java:7)</error>
    </testcase>
  </testsuite>
</testsuites>
"""


def test_parse_junit_all_passing(tmp_path):
    (tmp_path / "TEST-a.xml").write_text(_PASS_XML)
    res = pr.parse_junit_xml_dir(str(tmp_path))
    assert res["total"] == 2
    assert res["failed"] == []
    assert res["failures"] == 0


def test_parse_junit_with_failure(tmp_path):
    (tmp_path / "TEST-a.xml").write_text(_FAIL_XML)
    res = pr.parse_junit_xml_dir(str(tmp_path))
    assert res["total"] == 2
    assert res["failures"] == 1
    assert res["failed"] == ["com.foo.BarTest#testB"]
    assert "expected:<1> but was:<2>" in res["details"][0]


def test_parse_junit_testsuites_root_and_error(tmp_path):
    (tmp_path / "TEST-b.xml").write_text(_ERROR_XML)
    res = pr.parse_junit_xml_dir(str(tmp_path))
    assert res["total"] == 1
    assert res["errors"] == 1
    assert res["failed"] == ["com.foo.BazTest#testBoom"]


def test_parse_junit_missing_dir():
    res = pr.parse_junit_xml_dir("/no/such/dir")
    assert res == {"total": 0, "failures": 0, "errors": 0, "failed": [], "details": []}


def test_parse_junit_skips_unparsable(tmp_path):
    (tmp_path / "broken.xml").write_text("<<<not xml")
    (tmp_path / "ok.xml").write_text(_PASS_XML)
    res = pr.parse_junit_xml_dir(str(tmp_path))
    assert res["total"] == 2  # only the good file counted


def test_format_fail_report_zero_uses_success_phrase():
    # The agent detects success via "0 failing test cases" - keep it exact.
    out = pr.format_fail_report({"failed": [], "details": []})
    assert "0 failing test cases" in out


def test_format_fail_report_counts():
    out = pr.format_fail_report(
        {"failed": ["A#x", "B#y"], "details": ["--- A#x", "--- B#y"]}
    )
    assert "There are 2 failing test cases" in out


# ---------------------------------------------------------------------------
# Stack-trace parsing + localization
# ---------------------------------------------------------------------------
_TRACE = textwrap.dedent(
    """\
    java.lang.AssertionError: expected:<1> but was:<2>
    \tat org.junit.Assert.fail(Assert.java:88)
    \tat org.junit.Assert.assertEquals(Assert.java:834)
    \tat com.foo.Bar.add(Bar.java:42)
    \tat com.foo.BarTest.testAdd(BarTest.java:15)
    \tat java.base/jdk.internal.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
    """
)


def test_parse_stack_trace_filters_framework_frames():
    frames = pr.parse_stack_trace(_TRACE)
    classes = [f["class"] for f in frames]
    # JUnit + JDK frames removed; project frames kept.
    assert "org.junit.Assert" not in classes
    assert "com.foo.Bar" in classes
    assert "com.foo.BarTest" in classes


def test_parse_stack_trace_package_filter():
    frames = pr.parse_stack_trace(_TRACE, project_packages=["com.foo.Bar"])
    classes = {f["class"] for f in frames}
    assert classes <= {"com.foo.Bar", "com.foo.BarTest"}
    assert "com.foo.Bar" in classes


def test_parse_stack_trace_dedup():
    dup = _TRACE + "\tat com.foo.Bar.add(Bar.java:42)\n"
    frames = pr.parse_stack_trace(dup)
    keys = [(f["class"], f["method"], f["line"]) for f in frames]
    assert keys.count(("com.foo.Bar", "add", 42)) == 1


def test_parse_stack_trace_empty():
    assert pr.parse_stack_trace("") == []
    assert pr.parse_stack_trace(None) == []


def test_localize_from_trace_with_source(tmp_path):
    src = tmp_path / "src" / "main" / "java" / "com" / "foo"
    src.mkdir(parents=True)
    bar = src / "Bar.java"
    bar.write_text("\n".join("line{}".format(i) for i in range(1, 60)))
    out = pr.localize_from_trace(str(tmp_path), _TRACE)
    assert "Candidate fault locations" in out
    assert "Bar.java" in out
    assert "around line 42" in out
    # Code window present (numbered lines around 42).
    assert "Line 42:" in out


def test_localize_from_trace_no_frames():
    assert pr.localize_from_trace("/x", "no frames here") == ""


# ---------------------------------------------------------------------------
# Sidecar helpers
# ---------------------------------------------------------------------------
def test_sidecar_roundtrip(tmp_path):
    data = {"build_tool": "maven", "test_targets": ["A#b"]}
    pr.write_sidecar(str(tmp_path), data)
    assert pr.read_sidecar(str(tmp_path)) == data


def test_read_sidecar_missing(tmp_path):
    assert pr.read_sidecar(str(tmp_path)) == {}


def test_project_dir_shape():
    p = pr.project_dir("MyProj", 3, "ws")
    assert p.endswith(os.path.join("ws", "myproj_3_buggy"))


def test_module_dir_default_and_sub(tmp_path):
    assert pr.module_dir("/p", {}) == "/p"
    assert pr.module_dir("/p", {"module": "sub"}) == os.path.join("/p", "sub")


# ---------------------------------------------------------------------------
# Seam: generic_run_tests oracle (subprocess mocked)
# ---------------------------------------------------------------------------
def _make_agent(workspace):
    return SimpleNamespace(
        config=SimpleNamespace(workspace_path=workspace, repair_mode="generic"),
        experiment_file=None,
    )


def _setup_project(tmp_path, sidecar):
    proj = tmp_path / "proj_1_buggy"
    proj.mkdir()
    (proj / "pom.xml").write_text("<project/>")
    (proj / ".git").mkdir()
    pr.write_sidecar(str(proj), sidecar)
    return proj


def test_generic_run_tests_targeted_failure(tmp_path):
    proj = _setup_project(tmp_path, {"build_tool": "maven", "test_targets": ["com.foo.BarTest#testB"]})
    agent = _make_agent(str(tmp_path))

    def fake_run_suite(build_tool, mod_dir, target=None):
        return {"failed": ["com.foo.BarTest#testB"], "details": ["--- com.foo.BarTest#testB"]}, "log"

    with mock.patch.object(pr, "_run_suite_capture", side_effect=fake_run_suite), mock.patch.object(
        pr, "generic_restore", return_value="restored"
    ) as restore:
        out = pr.generic_run_tests("proj", 1, agent)
    assert "There are 1 failing test cases" in out
    restore.assert_called_once()  # edits reverted after a failing attempt


def test_generic_run_tests_plausible_patch(tmp_path):
    proj = _setup_project(
        tmp_path, {"build_tool": "maven", "test_targets": ["com.foo.BarTest#testB"]}
    )
    agent = _make_agent(str(tmp_path))

    calls = {"n": 0}

    def fake_run_suite(build_tool, mod_dir, target=None):
        # Both the targeted run and the full-suite run pass.
        return {"failed": [], "details": []}, "log"

    with mock.patch.object(pr, "_run_suite_capture", side_effect=fake_run_suite), mock.patch.object(
        pr, "_save_generic_patch", return_value="diff"
    ) as save, mock.patch.object(pr, "generic_restore", return_value="restored"):
        out = pr.generic_run_tests("proj", 1, agent)
    assert "0 failing test cases" in out
    save.assert_called_once()  # diff captured before restore


def test_generic_run_tests_regression_blocks_success(tmp_path):
    proj = _setup_project(
        tmp_path,
        {
            "build_tool": "maven",
            "test_targets": ["com.foo.BarTest#testB"],
            "baseline_failing": [],
        },
    )
    agent = _make_agent(str(tmp_path))

    seq = [
        ({"failed": [], "details": []}, "log"),  # targeted passes
        ({"failed": ["com.foo.OtherTest#x"], "details": ["--- com.foo.OtherTest#x"]}, "log"),  # regression
    ]

    def fake_run_suite(build_tool, mod_dir, target=None):
        return seq.pop(0)

    with mock.patch.object(pr, "_run_suite_capture", side_effect=fake_run_suite), mock.patch.object(
        pr, "generic_restore", return_value="restored"
    ):
        out = pr.generic_run_tests("proj", 1, agent)
    assert "There are 1 failing test cases" in out
    assert "0 failing test cases" not in out


def test_generic_run_tests_no_build_tool(tmp_path):
    proj = tmp_path / "proj_1_buggy"
    proj.mkdir()
    pr.write_sidecar(str(proj), {})  # no build_tool, no pom/gradle
    agent = _make_agent(str(tmp_path))
    with mock.patch.object(pr, "generic_restore", return_value="restored"):
        out = pr.generic_run_tests("proj", 1, agent)
    assert "Could not detect a Maven or Gradle build" in out


def test_generic_restore_requires_git(tmp_path):
    proj = tmp_path / "proj_1_buggy"
    proj.mkdir()  # no .git
    agent = _make_agent(str(tmp_path))
    out = pr.generic_restore("proj", 1, agent)
    assert "not a git repository" in out


# ---------------------------------------------------------------------------
# Opt-in end-to-end oracle test against a real Maven build (no LLM involved).
# Skipped unless Maven + Java are installed. This exercises the genuine
# build->JUnit-XML->oracle path on the committed sample project: the seeded bug
# fails, applying the one-line fix makes generic_run_tests report success, and a
# plausible_patch.diff is produced.
# ---------------------------------------------------------------------------
@pytest.mark.slow
@pytest.mark.skipif(
    shutil.which("mvn") is None or shutil.which("java") is None,
    reason="Maven/Java not installed",
)
def test_end_to_end_sample_maven(tmp_path):
    sample = os.path.join(FIXTURES, "sample_maven")
    proj = tmp_path / "samplemaven_1_buggy"
    shutil.copytree(sample, str(proj))
    subprocess.run(["git", "init", "-q"], cwd=str(proj), check=True)
    subprocess.run(["git", "add", "-A"], cwd=str(proj), check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "base"],
        cwd=str(proj),
        check=True,
    )
    pr.write_sidecar(
        str(proj),
        {
            "build_tool": "maven",
            "test_targets": ["com.example.CalcTest#testAdd"],
            "baseline_failing": [],
        },
    )
    agent = _make_agent(str(tmp_path))

    # Buggy state: the targeted test fails.
    out = pr.generic_run_tests("samplemaven", 1, agent)
    assert "0 failing test cases" not in out

    # Apply the fix in the working copy, then re-run the oracle.
    calc = proj / "src" / "main" / "java" / "com" / "example" / "Calc.java"
    calc.write_text(calc.read_text().replace("return a - b;", "return a + b;", 1))
    out = pr.generic_run_tests("samplemaven", 1, agent)
    assert "0 failing test cases" in out
