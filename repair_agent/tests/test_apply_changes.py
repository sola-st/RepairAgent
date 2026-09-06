"""Unit tests for ``apply_changes`` — the function that turns an LLM-proposed
patch dict into edits on disk.

Every fix the agent proposes passes through here, so a defect in this module is
invisible in the logs but fatal to results: the agent is told its patch was
applied, the build then fails (or silently keeps the old behavior), and the bug
is recorded as unfixable.

The ordering tests below cover a defect where each line of a multi-line
insertion was inserted at the same index, writing the block out in reverse and
turning a valid fix into uncompilable code.
"""

import pytest

import tests.conftest  # noqa: F401  (sys.path / chdir / langchain stubs)
from apply_changes import apply_changes


@pytest.fixture
def java_file(tmp_path):
    """A small file plus a helper returning its lines after a patch."""

    def _make(text):
        path = tmp_path / "Sample.java"
        path.write_text(text)
        return path

    return _make


def test_multiline_insertion_preserves_line_order(java_file):
    """A block of inserted lines must land in the order the patch lists them."""
    path = java_file("line1\nline2\nline3\nline4\n")

    apply_changes(
        {
            "file_name": str(path),
            "insertions": [{"line_number": 3, "new_lines": ["A\n", "B\n", "C\n"]}],
            "deletions": [],
            "modifications": [],
        }
    )

    assert path.read_text() == "line1\nline2\nA\nB\nC\nline3\nline4\n"


def test_multiline_insertion_produces_compilable_java(java_file):
    """The realistic shape of the defect: a method body inserted as a block.

    Reversal keeps every line but scrambles the order, so the result still
    "applies" while being syntactically invalid — the reason it went unnoticed.
    """
    path = java_file("class C {\n    void a() {}\n}\n")
    body = [
        "    public String path() {\n",
        "        if (pkg.isEmpty()) {\n",
        "            return name;\n",
        "        }\n",
        "        return pkg + name;\n",
        "    }\n",
    ]

    apply_changes(
        {
            "file_name": str(path),
            "insertions": [{"line_number": 3, "new_lines": body}],
            "deletions": [],
            "modifications": [],
        }
    )

    result = path.read_text()
    assert "".join(body) in result
    # A brace-balance check is enough to catch the reversed form.
    assert result.count("{") == result.count("}")
    assert result.index("public String path()") < result.index("return pkg + name;")


def test_multiple_insertion_blocks_land_at_their_own_targets(java_file):
    """Earlier insertions shift later ones; each block must still land correctly."""
    path = java_file("a\nb\nc\nd\ne\n")

    apply_changes(
        {
            "file_name": str(path),
            "insertions": [
                {"line_number": 2, "new_lines": ["X1\n", "X2\n"]},
                {"line_number": 4, "new_lines": ["Y1\n", "Y2\n"]},
            ],
            "deletions": [],
            "modifications": [],
        }
    )

    assert path.read_text() == "a\nX1\nX2\nb\nc\nY1\nY2\nd\ne\n"


def test_insertion_blocks_are_ordered_even_when_listed_out_of_order(java_file):
    """The patch dict may list blocks in any order; targets are by line number."""
    path = java_file("a\nb\nc\nd\ne\n")

    apply_changes(
        {
            "file_name": str(path),
            "insertions": [
                {"line_number": 4, "new_lines": ["Y1\n", "Y2\n"]},
                {"line_number": 2, "new_lines": ["X1\n", "X2\n"]},
            ],
            "deletions": [],
            "modifications": [],
        }
    )

    assert path.read_text() == "a\nX1\nX2\nb\nc\nY1\nY2\nd\ne\n"


def test_single_line_insertion_still_works(java_file):
    """The common case must be unaffected by the ordering fix."""
    path = java_file("a\nb\n")

    apply_changes(
        {
            "file_name": str(path),
            "insertions": [{"line_number": 2, "new_lines": ["mid\n"]}],
            "deletions": [],
            "modifications": [],
        }
    )

    assert path.read_text() == "a\nmid\nb\n"


def test_deletions_blank_lines_and_insertions_keep_their_order(java_file):
    """Deletions blank a line in place, so insertion targets stay stable."""
    path = java_file("keep1\ndrop\nkeep2\n")

    apply_changes(
        {
            "file_name": str(path),
            "insertions": [{"line_number": 3, "new_lines": ["new1\n", "new2\n"]}],
            "deletions": [2],
            "modifications": [],
        }
    )

    lines = path.read_text().splitlines()
    assert "drop" not in lines
    assert lines.index("new1") < lines.index("new2")


def test_modification_replaces_a_similar_line(java_file):
    path = java_file("int x = 1;\n")

    apply_changes(
        {
            "file_name": str(path),
            "insertions": [],
            "deletions": [],
            "modifications": [{"line_number": 1, "modified_line": "int x = 2;"}],
        }
    )

    assert path.read_text() == "int x = 2;\n"


def test_dissimilar_modification_is_dropped_without_any_signal(java_file):
    """KNOWN DEFECT (not fixed): a rewrite too unlike the original is skipped.

    ``apply_changes`` compares the proposed line to the original with
    ``fuzz.ratio`` and silently ``continue``s below 70. A legitimate rewrite is
    therefore discarded while the caller is still told the patch was applied,
    and the agent reasons about a fix that never reached the file. This test
    documents the behavior so the fix can be tracked; it asserts the drop AND
    the absence of any error being surfaced.
    """
    path = java_file("int x = 1;\n")
    original = path.read_text()

    result = apply_changes(
        {
            "file_name": str(path),
            "insertions": [],
            "deletions": [],
            "modifications": [
                {
                    "line_number": 1,
                    "modified_line": "return Collections.unmodifiableList(entries);",
                }
            ],
        }
    )

    assert path.read_text() == original, "behavior changed — update the issue"
    assert not result, "the skip is reported through no channel at all"


@pytest.mark.parametrize("line_number", [0, -3])
def test_malformed_line_number_keeps_the_block_together(java_file, line_number):
    """``line_number`` defaults to 0 when the model omits it, and a naive
    ``line_number - 1`` then indexes at -1: ``list.insert(-1, x)`` places a line
    before the LAST line, splitting the block across the file. The index is
    clamped so a malformed target degrades to "insert at the top", intact.
    """
    path = java_file("a\nb\nc\n")

    apply_changes(
        {
            "file_name": str(path),
            "insertions": [{"line_number": line_number, "new_lines": ["X\n", "Y\n"]}],
            "deletions": [],
            "modifications": [],
        }
    )

    assert path.read_text() == "X\nY\na\nb\nc\n"


def test_insertion_past_end_of_file_appends_in_order(java_file):
    path = java_file("a\nb\n")

    apply_changes(
        {
            "file_name": str(path),
            "insertions": [{"line_number": 99, "new_lines": ["X\n", "Y\n"]}],
            "deletions": [],
            "modifications": [],
        }
    )

    assert path.read_text() == "a\nb\nX\nY\n"


def test_empty_new_lines_is_a_noop(java_file):
    path = java_file("a\nb\n")

    apply_changes(
        {
            "file_name": str(path),
            "insertions": [{"line_number": 2, "new_lines": []}],
            "deletions": [],
            "modifications": [],
        }
    )

    assert path.read_text() == "a\nb\n"
