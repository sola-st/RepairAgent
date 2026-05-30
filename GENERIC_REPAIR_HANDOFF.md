# Handoff: "Fix any failing Java project" mode

A working design + implementation plan for letting RepairAgent repair an
**arbitrary Java project with a failing test**, instead of only Defects4J bugs.
This is the single biggest adoption lever: it turns the tool from a benchmark
reproduction harness into something a developer can point at their own repo.

> **Hard constraint:** the existing Defects4J evaluation path must keep working
> **byte-for-byte**. The published results depend on it. The generic mode is an
> additive, parallel path selected by a flag, not a rewrite of the D4J path.

---

## 1. Goal & non-goals

**Goal.** Given a Java project (Maven or Gradle) and a failing test, run the
existing agent loop to produce a patch that makes the failing test pass without
breaking the rest of the suite, and emit the diff for human review.

**In scope**
- A new entry point (CLI command) that does not touch the D4J flow.
- An adapter that replaces the four Defects4J-specific operations (checkout,
  run-tests oracle, restore, localization) with build-tool / VCS equivalents.
- Stack-trace-based fault localization (no ground-truth buggy lines exist).

**Non-goals (for the first version)**
- Judging "correctness" automatically (there is no developer patch to compare
  to). Output is a *plausible* patch + diff; a human decides.
- Multi-language support, multi-file refactors beyond what the agent already does.
- SBFL/GZoltar localization (note it as an optional later enhancement).

---

## 2. How the Defects4J path works today (the seams to replace)

The agent loop, prompt construction, and most commands are **project-agnostic**.
Only a handful of operations are Defects4J-specific. Verified locations:

| Seam | Where | What it does (D4J) | Generic equivalent |
|------|-------|--------------------|--------------------|
| **A. Init localization** | `autogpt/agents/base.py:98` → `defects4j_static.get_info` → reads `defects4j/buggy-lines/{P}-{N}.buggy.lines` | Ground-truth buggy lines/methods | Derive candidate locations from the failing test's **stack trace** (no ground truth) |
| **B. Init test results** | `autogpt/agents/base.py:99` → `defects4j_static.run_tests` | Initial failing-test output | Run `mvn test` / `gradle test` once, parse failures |
| **C. Test oracle (runtime)** | `autogpt/commands/defects4j.py:199 run_defects4j_tests` (called from the `write_fix` path) → `defects4j compile && defects4j test` → `extract_fail_report` | Compile + run suite, return fail report; **0 failing = plausible patch** | `mvn -q test` / `gradle test`, parse surefire/gradle XML for failures |
| **D. Restore** | `autogpt/commands/defects4j.py:158 undo_changes` → `run_checkout` (re-checkout) | Revert agent edits between attempts | `git restore`/`git checkout --` of touched files (or snapshot+restore) |
| **E. Checkout / prepare** | `repairagent.py:792 checkout_bug` → `defects4j checkout -p P -v Nb -w <dir>` | Materialize buggy revision into `auto_gpt_workspace/<proj>_<idx>_buggy/` | Copy the user's project into the workspace (or `git clone` + checkout ref) |

**Reusable as-is (do NOT duplicate):**
- Agent loop, 3-state machine, prompt construction — `autogpt/agents/{base,agent}.py`.
- Navigation commands — `read_range`, `search_code_base`, `get_classes_and_methods`,
  `extract_method_code`, `extract_similar_functions_calls` (operate on workspace
  files via `preprocess_paths` + `files_index.txt`; work for any Java project).
- `write_fix` / `execute_write_range` — applies edits + Java syntax validation
  via `javalang` (generic). Only the *test run after writing* is D4J-coupled (seam C).
- `commands_interface.json`, the `states` command group, `create_files_index.list_java_files`.

**Workspace layout assumption.** Everything lives under
`auto_gpt_workspace/<project>_<index>_buggy/`. The generic path can reuse the
same shape, e.g. `auto_gpt_workspace/<name>_<runid>_buggy/`, so the navigation
commands and `preprocess_paths` keep working unchanged.

---

## 3. Proposed design

### 3.1 A `RepairBackend` abstraction

Introduce a small strategy interface; the agent talks to it instead of calling
Defects4J functions directly:

```python
class RepairBackend:
    def prepare(self) -> str: ...                 # seam E: materialize project into workspace
    def initial_test_report(self) -> str: ...      # seam B: run suite once, return failing-test text
    def localize(self) -> str: ...                 # seam A: candidate fault locations (prompt text)
    def run_tests(self) -> str: ...                # seam C: oracle; return fail report ("0 failing" => plausible)
    def restore(self) -> None: ...                 # seam D: revert agent edits
    @property
    def is_fixed(self, report: str) -> bool: ...   # parse report -> all targeted tests pass, no regressions
```

- `Defects4JBackend` — thin wrapper over the existing functions. Behavior must be
  identical to today so the eval path is unchanged.
- `GenericProjectBackend` — new (Maven/Gradle + git + stack-trace localization).

### 3.2 Minimally-invasive integration (keep eval byte-for-byte)

The agent currently hardcodes the D4J calls at three seams (base.py:98-99 and the
`write_fix` oracle). Recommended approach:

1. Add `repair_mode: str = "defects4j"` to config / `hyperparams.json` (default
   keeps D4J behavior).
2. At each of the ~5 seam call sites, branch on `repair_mode`: `"defects4j"` →
   existing code unchanged; `"generic"` → call the new backend. (A full backend
   object threaded through `Agent` is cleaner long-term, but the flag-branch keeps
   the diff to the shared D4J code tiny and obviously safe for the eval.)
3. New CLI command `fix-project` (in `repairagent.py`) sets `repair_mode=generic`
   and wires the `GenericProjectBackend`.

> Do **not** refactor `base.py`/`defects4j.py` broadly. Add branches at the seams.
> The eval path should produce an identical diff to `git show` on the D4J flow.

### 3.3 New CLI surface

```
python3 repairagent.py fix-project \
    --path /abs/path/to/project \         # or --git <url> [--ref <sha>]
    --test "com.foo.BarTest#testThing" \   # failing test (FQN#method); repeatable / optional (auto-detect)
    --build maven|gradle|auto \            # default: auto-detect (pom.xml / build.gradle)
    --model gpt-4o-mini \
    --max-cycles 40
```

Output: the unified `git diff` of the proposed patch + a short report (tests
before/after), saved under `experimental_setups/<run>/` like normal runs.

---

## 4. The hard part: localization without ground truth

Defects4J hands the agent the buggy lines. A real project does not. Options, in
recommended order:

1. **Stack-trace localization (ship this first).** Run the failing test, capture
   the exception stack trace, and extract frames that point into the **project's
   own classes** (skip test classes, JUnit, JDK, libraries). Map class → source
   file (+ line). Format this into the same kind of text `get_info` returns today
   (file path + line + surrounding code window). This is usually enough to seed
   the agent and reuses the existing code-window machinery in
   `read_buggy_source`-style helpers.
2. **Assertion-based hint.** For assertion failures with no app frame, fall back
   to the test method body (the assertion + the methods it calls) as the seed.
3. **User hint flag.** `--suspect src/.../Foo.java:120` to override/augment.
4. **(Later) SBFL via GZoltar.** Higher quality, much heavier setup; keep optional.

Localization quality is the main driver of success in generic mode; budget the
most implementation effort here and make it pluggable.

---

## 5. Build-system adapter

Auto-detect: `pom.xml` → Maven, `build.gradle[.kts]` → Gradle.

| Operation | Maven | Gradle |
|-----------|-------|--------|
| Compile | `mvn -q -DskipTests compile` | `gradle compileJava` |
| Run one test | `mvn -q -Dtest=Class#method test` | `gradle test --tests Class.method` |
| Run suite (regression) | `mvn -q test` | `gradle test` |
| Results to parse | `target/surefire-reports/*.xml` | `build/test-results/test/*.xml` |

- Parse the JUnit XML (`testsuite`/`testcase`/`failure`) for pass/fail counts and
  which tests failed — this is the oracle (`is_fixed` = targeted test(s) now pass
  AND no previously-passing test regressed).
- **Regression strategy:** running the *whole* suite every attempt can be slow.
  Suggested: validate the targeted test first (fast), then run the full suite only
  when the targeted test passes, to confirm no regressions before declaring a
  plausible patch.
- **Restore:** require the project be a git repo (simplest) → `git stash`/`git
  checkout -- <files>` between attempts; otherwise snapshot touched files before
  the first edit and copy them back.

---

## 6. Success criteria

- **Plausible patch:** the originally-failing test(s) pass and no
  previously-passing test fails.
- **Correctness:** not auto-decidable (no reference patch). Emit the diff and the
  before/after test summary for a human. Do not claim "correct".

---

## 7. Phased implementation plan (each phase testable, TDD)

1. **Backend seam + flag.** Add `repair_mode` and the `RepairBackend` interface;
   wrap the existing D4J calls in `Defects4JBackend`; branch the 5 seams. Verify
   the D4J eval path is unchanged (run an existing bug, diff behavior).
2. **Build adapter (Maven first).** Detect, compile, run-one-test, run-suite,
   parse surefire XML. Unit-test the XML parsing + command construction with
   fixtures (no real Maven needed); one integration test against a tiny sample
   Maven project committed under `tests/fixtures/`.
3. **Restore via git.** Implement + test on the sample project.
4. **Stack-trace localization.** Parse a captured trace → project frames → file/line
   → code window. Unit-test with canned traces.
5. **`GenericProjectBackend`** wiring all of the above; the `fix-project` CLI.
6. **End-to-end** on a tiny seeded-bug sample project (one-line bug + failing test).
7. **Gradle adapter** (mirror of Maven).
8. Docs: README "Fix your own project" section + CONTRIBUTING note.

---

## 8. Testing strategy

- Keep all new logic behind the same unit-test discipline already in `tests/`
  (mock `subprocess`, parse fixture XML/traces; no real Maven/Gradle/Java needed
  for unit tests).
- Commit a **minimal sample Maven project** with one seeded bug + failing test
  under `repair_agent/tests/fixtures/sample_maven/` for one slow, opt-in
  integration test (mark it `@pytest.mark.slow` / skip if `mvn` absent).
- **Do not** modify the existing Defects4J tests; add a regression test asserting
  the D4J seam still delegates to the original functions when `repair_mode` is
  default.

---

## 9. Risks & decisions for the implementer

- **Arbitrary code execution.** Building/testing an unknown project runs its code.
  Strongly prefer running generic mode **inside the Docker container** (the repo
  already supports `--docker`); document this.
- **Slow / flaky suites.** Real suites can take minutes and be nondeterministic.
  Mitigate with the targeted-test-first strategy and a per-test timeout.
- **Multi-module Maven / monorepos.** First version: support single-module or a
  `--module` flag; detect and error clearly otherwise.
- **No localization signal** (e.g. failure with no app frame in the trace): fall
  back to the test body; surface a clear message if even that is empty.
- **Dependency resolution / offline builds:** first build may download
  dependencies; note network requirement.

---

## 10. Concrete inventory

**New files**
- `repair_agent/autogpt/commands/project_repair.py` — `GenericProjectBackend`,
  build-tool adapter, stack-trace localizer.
- `repair_agent/tests/test_project_repair.py` — unit tests (mocked).
- `repair_agent/tests/fixtures/sample_maven/` — tiny seeded-bug project.

**Files to touch (small, flag-guarded branches only)**
- `repair_agent/repairagent.py` — new `fix-project` command; wire backend.
- `repair_agent/autogpt/agents/base.py:98-99` — seam A/B branch on `repair_mode`.
- `repair_agent/autogpt/commands/defects4j.py` — seam C (`run_defects4j_tests`
  call site in the `write_fix` path) and seam D (`undo_changes`) branch on mode,
  or route through the backend.
- `repair_agent/hyperparams.json` / config — add `repair_mode` (default
  `"defects4j"`).

**Reference reading before starting**
- `autogpt/agents/base.py` `__init__` (the localization/test-results seam).
- `autogpt/commands/defects4j.py`: `run_defects4j_tests`, `extract_fail_report`,
  `run_checkout`/`undo_changes`, `write_fix`/`execute_write_range`.
- `autogpt/commands/defects4j_static.py`: `get_info`, `run_tests`.
- `repairagent.py`: `checkout_bug`, `prepare_ai_settings`, `run_single_bug`,
  `execute_run` (mirror this structure for `fix-project`).

---

## 11. Open questions for the next session

1. Single-module only, or handle multi-module Maven from the start?
2. Require the target be a git repo (simplifies restore), or support non-git dirs?
3. Default to running generic mode in Docker for safety, or leave it to the user?
4. Failing test: require `--test`, or auto-detect by running the suite first?
5. How aggressive on regression checking (full suite each attempt vs targeted-first)?
