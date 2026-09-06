"""Robustness tests for ``autogpt.commands.defects4j`` command handlers.

These cover failure modes that do not crash the agent but quietly waste its
budget: a command that raises instead of returning guidance, a search that
aborts on one unparseable file, a workspace that never recovers after a failed
restore, and a fix that is refused before it is ever tested.

Nothing here runs Java, git, defects4j or the network; the external calls are
monkeypatched inside the module namespace.
"""

import os
from types import SimpleNamespace

import pytest

import tests.conftest  # noqa: F401  (sys.path / chdir / langchain stubs)
from autogpt.commands import defects4j as d


# --------------------------------------------------------------------------
# search_code_base: one unparseable file must not abort the whole search
# --------------------------------------------------------------------------

MODERN_JAVA = """package demo;

public class Modern {
    record Point(int x, int y) {}

    public String describe(Object o) {
        return switch (o) {
            case Integer i -> "int";
            default -> "other";
        };
    }
}
"""

LEGACY_JAVA = """package demo;

public class Legacy {
    public String getAliasFullPath() {
        return "x";
    }
}
"""


def test_search_code_base_skips_files_javalang_cannot_parse(buggy_project_dir):
    """A single modern-Java file used to abort the entire search.

    ``javalang`` raises ``JavaSyntaxError`` on newer syntax such as switch
    expressions (plain records happen to parse). The error propagated out of
    ``search_code_base``, so the agent received a bare "Error:" and lost the
    command — on a codebase where most files were perfectly searchable.
    """
    import javalang

    fixture = buggy_project_dir
    fixture.write("src/demo/Modern.java", MODERN_JAVA)
    fixture.write("src/demo/Legacy.java", LEGACY_JAVA)

    # Guard: the test is only meaningful while javalang really rejects this.
    with pytest.raises(Exception):
        javalang.parse.parse(MODERN_JAVA)

    result = d.search_code_base(
        fixture.project_name, fixture.bug_index, ["getAliasFullPath"], fixture.agent
    )

    assert "getAliasFullPath" in result
    assert "Legacy" in result


# --------------------------------------------------------------------------
# path resolution failures must be reported, not raised or written to disk
# --------------------------------------------------------------------------

UNRESOLVABLE = "The filepath Foo.java does not exist."


def test_read_range_returns_guidance_when_the_path_cannot_be_resolved(
    buggy_project_dir, monkeypatch
):
    """``preprocess_paths`` returns an explanatory message on failure.

    Joining that message onto the project directory and opening it surfaced a
    raw ``FileNotFoundError`` (``Errno 2 ... files_index.txt``) to the agent
    instead of the guidance the message was written to give.
    """
    fixture = buggy_project_dir
    monkeypatch.setattr(d, "preprocess_paths", lambda *a, **k: UNRESOLVABLE)

    result = d.execute_read_range(
        fixture.project_name, fixture.bug_index, "Foo.java", 1, 10, fixture.agent
    )

    assert result == UNRESOLVABLE


def test_write_range_does_not_create_a_file_named_after_the_error(
    buggy_project_dir, monkeypatch
):
    """The write path had the same defect, with a worse consequence: it would
    have written the patch into a file whose name was the error message."""
    fixture = buggy_project_dir
    monkeypatch.setattr(d, "preprocess_paths", lambda *a, **k: UNRESOLVABLE)
    applied = []
    monkeypatch.setattr(d, "apply_changes", lambda resolved: applied.append(resolved))

    result = d.execute_write_range(
        fixture.project_name,
        fixture.bug_index,
        [{"file_name": "Foo.java", "insertions": [], "deletions": [], "modifications": []}],
        fixture.agent,
    )

    assert result == UNRESOLVABLE
    assert applied == [], "no edit may be attempted against an unresolved path"
    assert not (fixture.project_dir / UNRESOLVABLE).exists()


# --------------------------------------------------------------------------
# workspace recovery
# --------------------------------------------------------------------------


def test_ensure_project_checkout_restores_a_missing_working_copy(tmp_path, monkeypatch):
    """``undo_changes`` deletes the checkout before recreating it. When the
    recreate step failed, every later file command errored for the rest of the
    run; recovery is now attempted at the point of use."""
    workspace = tmp_path / "auto_gpt_workspace"
    workspace.mkdir()
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        (workspace / "lang_1_buggy").mkdir()
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(d.subprocess, "run", fake_run)

    project_dir = d.ensure_project_checkout("Lang", 1, str(workspace))

    assert os.path.isdir(project_dir)
    assert len(calls) == 1 and "checkout" in calls[0]


def test_ensure_project_checkout_is_a_noop_when_the_copy_exists(tmp_path, monkeypatch):
    """A present working copy must never be re-checked-out: that would discard
    the candidate edits the agent has just written."""
    workspace = tmp_path / "auto_gpt_workspace"
    (workspace / "lang_1_buggy").mkdir(parents=True)

    def fail(*a, **k):  # pragma: no cover - must not run
        raise AssertionError("checkout attempted while the working copy existed")

    monkeypatch.setattr(d.subprocess, "run", fail)

    assert os.path.isdir(d.ensure_project_checkout("Lang", 1, str(workspace)))
