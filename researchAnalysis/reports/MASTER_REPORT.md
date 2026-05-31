# Comprehensive Research Analysis Report
## Spec-Guided Automated Program Repair — Experiments E17 & E34

**Date:** 2026-03-29
**Bug Pool:** 98 Defects4J bugs (Time, Math, Lang, Compress, Collections, Codec, Csv)
**Methodology:** Each plausible patch verified against the developer fixed version (checked out from D4J) and the D4J patch file. All fixed versions checked out to `researchAnalysis/checkouts/{Bug}_fixed/`.

---

# Part 1: Plausible Patch Verification

## 1.1 Final Reconciled Results

### E17 (Baseline Experiment — 16 plausible patches)

| # | Bug | Verdict | Match Type | Evidence |
|---|-----|---------|------------|----------|
| 1 | Time-15 | **CORRECT** | Exact match | Agent inserts identical `Long.MIN_VALUE` overflow check |
| 2 | Time-16 | **INCORRECT** | Wrong variable | Agent uses `instantMillis` instead of `instantLocal` |
| 3 | Math-3 | **CORRECT** | Exact match | Agent restores identical `len == 1` shortcut |
| 4 | Math-38 | **CORRECT** | Sem. equivalent | Agent deletes throw statements; developer comments them out — same effect |
| 5 | Math-53 | **CORRECT** | Sem. equivalent | Agent uses `isNaN()` method + `createComplex(NaN,NaN)` vs field access + constant |
| 6 | Math-98 | **CORRECT** | Exact match | Agent changes `v.length` to `nRows` in both matrix classes |
| 7 | Math-99 | **INCORRECT** | Wrong target | Agent checks lcm INPUTS instead of RESULT for `MIN_VALUE` |
| 8 | Math-103 | **INCORRECT** | Different structure | Agent adds pre-check guard; developer uses try-catch with fallback |
| 9 | Lang-6 | **INCORRECT** | Wrong variable | Agent keeps buggy `pos` in `codePointAt`; developer uses `pt` |
| 10 | Lang-13 | **INCORRECT** | Different structure | Agent adds if-else chain; developer uses HashMap + nested try-catch |
| 11 | Lang-39 | **INCORRECT** | Incomplete | Agent only guards `replacementList` null, not `searchList` |
| 12 | Lang-45 | **CORRECT** | Sem. equivalent | Agent adds correct `lower` bounds check (+ redundant `upper` check) |
| 13 | Lang-61 | **CORRECT** | Exact match | Agent restores `size - strLen + 1` loop bound |
| 14 | Compress-18 | **INCORRECT** | Wrong method | Agent patches `write()` instead of `writePaxHeaders()` |
| 15 | Compress-26 | **INCORRECT** | Different impl | Same idea (fallback read) but different structure and API calls |
| 16 | Compress-28 | **INCORRECT** | Opposite direction | Agent adds EOF exception; developer removes it |

**E17 Totals: 7 correct / 16 plausible (43.8%)**

### E34 (Improved Pipeline — 24 plausible patches)

| # | Bug | Verdict | Match Type | Evidence |
|---|-----|---------|------------|----------|
| 1 | Time-15 | **CORRECT** | Exact match | Identical `Long.MIN_VALUE` overflow check |
| 2 | Time-7 | **CORRECT** | Sem. equivalent | Agent computes `defaultYear` from original chrono + millis before `selectChronology`, matching FIXED version |
| 3 | Time-9 | **INCORRECT** | Partial fix | Agent only restores hours range check; misses `MAX_MILLIS`, plain arithmetic, `forOffsetMillis` check |
| 4 | Math-3 | **CORRECT** | Exact match | Identical `len == 1` shortcut |
| 5 | Math-25 | **INCORRECT** | Overly restrictive | Agent adds `c1<=0 || c2<=0 || c3<=0` guard; developer only checks `c2==0` |
| 6 | Math-53 | **CORRECT** | Sem. equivalent | Equivalent NaN check with method calls instead of field access |
| 7 | Math-69 | **INCORRECT** | Overfitting | Hardcodes `1e-10` instead of using `cumulativeProbability(-t)` |
| 8 | Math-90 | **INCORRECT** | Wrong approach | Adds type guards instead of merging method overloads |
| 9 | Math-97 | **INCORRECT** | Different structure | Missing `setResult()` calls; no explicit `sign==0` handling |
| 10 | Math-98 | **CORRECT** | Exact match | Identical `nRows` array sizing |
| 11 | Math-99 | **INCORRECT** | Wrong target | Same issue as E17: checks lcm inputs instead of result |
| 12 | Math-100 | **CORRECT** | Exact match | Identical `getUnboundParameters()` replacement |
| 13 | Math-102 | **INCORRECT** | Side effects | Mutates input `expected[]` array; developer uses ratio during computation |
| 14 | Lang-11 | **CORRECT** | Sem. equivalent | Unconditional `start >= end` check equivalent because auto-computed values always satisfy `end > start` |
| 15 | Lang-27 | **INCORRECT** | Different strategy | Changes `expPos` calculation; developer restores bounds checks |
| 16 | Lang-35 | **CORRECT** | Sem. equivalent | Guard clause throws `IllegalArgumentException` on both-null; same behavior |
| 17 | Lang-37 | **INCORRECT** | Different semantics | Pre-validation with `isAssignableFrom` vs developer removing try-catch entirely |
| 18 | Lang-39 | **INCORRECT** | Incomplete | Same issue as E17: only guards `replacementList` null |
| 19 | Lang-45 | **CORRECT** | Sem. equivalent | Correct `lower` bounds check |
| 20 | Compress-3 | **CORRECT** | Sem. equivalent | Identical boolean tracking logic for unclosed entries |
| 21 | Compress-12 | **CORRECT** | Sem. equivalent | Identical `IllegalArgumentException` → `IOException` wrapping |
| 22 | Compress-14 | **CORRECT** | Exact match | Agent restores `buffer[start] == 0` first-byte check matching FIXED version |
| 23 | Compress-28 | **INCORRECT** | Opposite direction | Agent adds EOF exception; developer removes it (same as E17) |
| 24 | Csv-5 | **CORRECT** | Exact match | Identical null-guard on `recordSeparator` |

**E34 Totals: 13 correct / 24 plausible (54.2%)**

### Combined Summary

| Metric | E17 | E34 | Union |
|--------|-----|-----|-------|
| Plausible patches | 16 | 24 | 32 unique |
| Correct patches | 7 | 13 | 15 unique |
| Precision (correct/plausible) | 43.8% | 54.2% | 46.9% |
| Recall (correct/attempted) | 7.1% | 14.3% | 15.3% |

### Union of Correct Patches (15 unique)

| Bug | In E17 | In E34 | Match Type |
|-----|--------|--------|------------|
| Time-15 | Yes | Yes | Exact match |
| Time-7 | — | Yes | Sem. equivalent |
| Math-3 | Yes | Yes | Exact match |
| Math-38 | Yes | — | Sem. equivalent |
| Math-53 | Yes | Yes | Sem. equivalent |
| Math-98 | Yes | Yes | Exact match |
| Math-100 | — | Yes | Exact match |
| Lang-11 | — | Yes | Sem. equivalent |
| Lang-35 | — | Yes | Sem. equivalent |
| Lang-45 | Yes | Yes | Sem. equivalent |
| Lang-61 | Yes | — | Exact match |
| Compress-3 | — | Yes | Sem. equivalent |
| Compress-12 | — | Yes | Sem. equivalent |
| Compress-14 | — | Yes | Exact match |
| Csv-5 | — | Yes | Exact match |

**Match type distribution:** 7 Exact match (46.7%), 8 Sem. equivalent (53.3%)

---

## 1.2 Evidence File Paths

For each plausible patch, the following evidence is available:

### Developer Fixed Source (Ground Truth)
All checked out to: `researchAnalysis/checkouts/{Project}_{id}_fixed/`
```
researchAnalysis/checkouts/Time_15_fixed/     researchAnalysis/checkouts/Math_3_fixed/
researchAnalysis/checkouts/Time_16_fixed/     researchAnalysis/checkouts/Math_38_fixed/
researchAnalysis/checkouts/Time_7_fixed/      researchAnalysis/checkouts/Math_53_fixed/
researchAnalysis/checkouts/Time_9_fixed/      researchAnalysis/checkouts/Math_69_fixed/
researchAnalysis/checkouts/Math_90_fixed/     researchAnalysis/checkouts/Math_97_fixed/
researchAnalysis/checkouts/Math_98_fixed/     researchAnalysis/checkouts/Math_99_fixed/
researchAnalysis/checkouts/Math_100_fixed/    researchAnalysis/checkouts/Math_102_fixed/
researchAnalysis/checkouts/Math_103_fixed/    researchAnalysis/checkouts/Math_25_fixed/
researchAnalysis/checkouts/Lang_6_fixed/      researchAnalysis/checkouts/Lang_11_fixed/
researchAnalysis/checkouts/Lang_13_fixed/     researchAnalysis/checkouts/Lang_27_fixed/
researchAnalysis/checkouts/Lang_35_fixed/     researchAnalysis/checkouts/Lang_37_fixed/
researchAnalysis/checkouts/Lang_39_fixed/     researchAnalysis/checkouts/Lang_45_fixed/
researchAnalysis/checkouts/Lang_61_fixed/     researchAnalysis/checkouts/Compress_3_fixed/
researchAnalysis/checkouts/Compress_12_fixed/ researchAnalysis/checkouts/Compress_14_fixed/
researchAnalysis/checkouts/Compress_18_fixed/ researchAnalysis/checkouts/Compress_26_fixed/
researchAnalysis/checkouts/Compress_28_fixed/ researchAnalysis/checkouts/Csv_5_fixed/
```

### Developer Patches
`repair_agent/defects4j/framework/projects/{Project}/patches/{id}.src.patch`

### Agent Plausible Patches
- E17: `repair_agent/experimental_setups/experiment_17/plausible_patches/plausible_patches_{Project}_{id}.json`
- E34: `repair_agent/experimental_setups/experiment_34/plausible_patches/plausible_patches_{Project}_{id}.json`

### Agent Conversation Logs
- E17: `repair_agent/experimental_setups/experiment_17/logs/prompt_history_{Project}_{id}/`
- E34: `repair_agent/experimental_setups/experiment_34/logs/prompt_history_{Project}_{id}/`

### Spec Logs
- E17: `repair_agent/experimental_setups/experiment_17/spec_logs/spec_raw_response_{Project}_{id}.txt`
- E34: `repair_agent/experimental_setups/experiment_34/spec_logs/spec_raw_response_{Project}_{id}.txt`

---

## 1.3 Incorrect Patch Classification

### E34 Incorrect Patches (11)

| Category | Count | Bugs | Description |
|----------|-------|------|-------------|
| WRONG_APPROACH | 4 | Math-90, Lang-27, Lang-37, Compress-28 | Agent uses fundamentally different fix strategy |
| OVERFITTING | 2 | Math-69, Math-25 | Agent patches symptom with workaround/overly broad guard |
| INCOMPLETE_FIX | 2 | Time-9, Lang-39 | Agent addresses part of the bug but misses components |
| DIFFERENT_STRUCTURE | 2 | Math-97, Math-102 | Similar intent but different code structure/side-effects |
| WRONG_TARGET | 1 | Math-99 | Checks wrong variable (inputs vs result) |

### E17 Incorrect Patches (9)

| Category | Count | Bugs | Description |
|----------|-------|------|-------------|
| WRONG_VARIABLE | 2 | Time-16, Lang-6 | Uses wrong variable (`instantMillis` vs `instantLocal`, `pos` vs `pt`) |
| DIFFERENT_STRUCTURE | 2 | Math-103, Lang-13 | Same intent but different implementation structure |
| WRONG_APPROACH | 2 | Compress-18, Compress-28 | Patches wrong method or opposite direction |
| WRONG_TARGET | 1 | Math-99 | Checks inputs instead of result |
| INCOMPLETE_FIX | 1 | Lang-39 | Guards only one of two null cases |
| DIFFERENT_IMPL | 1 | Compress-26 | Same idea but different API calls and structure |

### Cross-Experiment Pattern: "Add Validation" Bias

In both experiments, the agent shows a strong bias toward ADDING code (guards, checks, validation) as a repair strategy. This fails when the developer fix requires REMOVING code:

| Pattern | E17 | E34 | Total |
|---------|-----|-----|-------|
| Developer removes, agent adds | 2 | 5 | 7 |
| Agent uses wrong variable/target | 3 | 1 | 4 |
| Different structure/implementation | 3 | 2 | 5 |
| Partial/incomplete fix | 1 | 2 | 3 |
| Overfitting | 0 | 2 | 2 |

---

# Part 2: Unfixed Bug Analysis

## 2.1 Overview

**Total unfixed bugs:** 66 out of 98 (67.3%)
- All bugs had specs generated
- 64/66 exhausted the full 39-turn budget
- Specs correctly located the buggy code in ~73% of cases

## 2.2 Failure Category Distribution

| Primary Category | Count | % | Description |
|-----------------|-------|---|-------------|
| STUCK_LOOP | 43 | 65.2% | Agent retries minor variations of the same fix |
| COMPILE_ERROR | 10 | 15.2% | Patches produce syntax/compilation errors |
| TEST_FAILURE | 7 | 10.6% | Patches compile but tests fail; agent is close |
| WRONG_DIRECTION | 5 | 7.6% | Agent pursues fundamentally wrong fix strategy |
| TIMEOUT | 2 | 3.0% | Agent spends all turns on info gathering |

### Contributing Factor: Tool Similarity Constraint

The `write_fix` tool's 70% similarity threshold was a significant blocker in **12 bugs (18.2%)**. In these cases the agent correctly diagnosed the bug and proposed valid fixes, but the tool rejected modifications because the new code differed too much from the original line.

**Affected bugs:** Lang-52, Lang-53, Lang-54, Lang-12, Math-92, Math-93, Compress-11, Compress-17, Compress-24, Collections-2, Collections-3, Collections-7

---

## 2.3 Case Studies by Failure Category

### STUCK_LOOP — 3 Case Studies

#### Case 1: Collections-3 — Perfect diagnosis, tool blocks fix
**Log path:** `experiment_34/logs/prompt_history_Collections_3/`

**Bug:** `CollectionUtils.removeAll()` calls `ListUtils.retainAll()` — wrong method call.
**Developer fix:** Change `retainAll` to `removeAll` on line 1121.
**Agent behavior:** Correctly identified the wrong method call. Attempted to replace line 1121 in 33 consecutive attempts. ALL modifications rejected with <70% similarity because changing `retainAll` to `removeAll` (plus any logic adjustments) falls below the threshold.

**Why unfixed:** The write_fix tool's similarity constraint prevents a one-word method name change. The agent had the CORRECT fix but could not apply it.

**Could spec help?** No — the spec correctly diagnosed the issue. This is purely an infrastructure limitation.

#### Case 2: Math-10 — Misses IEEE 754 signed-zero semantics
**Log path:** `experiment_34/logs/prompt_history_Math_10/`

**Bug:** `DSCompiler.atan2()` doesn't handle `+0.0` vs `-0.0` correctly.
**Developer fix:** Add special cases using `Double.doubleToLongBits()` for signed-zero detection.
**Agent behavior:** Correctly targeted `atan2` and inserted if-checks for `y == 0.0` and `x == 0.0`, but Java's `==` operator treats `+0.0` and `-0.0` as equal. 27 fix attempts, all producing wrong results for `-0.0` inputs. Agent never discovered `Double.doubleToLongBits()`.

**Why unfixed:** Missing domain knowledge about IEEE 754 signed-zero representation in Java.

**Could spec help?** YES — A spec noting "Java's `==` treats +0.0 and -0.0 as equal; use `Double.doubleToLongBits()` for signed-zero comparison" would have directly enabled the fix.

#### Case 3: Lang-1 — Exhaustive threshold search fails
**Log path:** `experiment_34/logs/prompt_history_Lang_1/`

**Bug:** `NumberUtils.createNumber()` hex digit boundary for Long vs BigInteger routing.
**Developer fix:** Compound condition: `hexDigits > 16 || (hexDigits == 16 && ...)`
**Agent behavior:** 35 fix variants cycling through `hexDigits >= 16`, `> 16`, `== 16` — never found the correct compound condition checking the leading hex digit value.

**Why unfixed:** The fix requires a two-part condition (count threshold AND leading digit check) that the agent never synthesized from individual threshold experiments.

**Could spec help?** YES — A spec stating "0x7FFFFFFFFFFFFFFF (16 hex digits) fits in Long, but 0x8000000000000000 (16 hex digits) overflows — check leading digit for 16-digit hex" would have guided the correct compound condition.

---

### COMPILE_ERROR — 3 Case Studies

#### Case 1: Math-47 — Syntax errors from code formatting
**Log path:** `experiment_34/logs/prompt_history_Math_47/`

**Bug:** `Complex.divide()` missing NaN/Infinity handling.
**Developer fix:** Add `isNaN`/`isInfinite` checks with proper returns.
**Agent behavior:** Understood the fix conceptually but produced 101 syntax errors across 34 attempts. The agent put multiple Java statements on single lines using literal `\n` strings, which the tool treated as text rather than newlines.

**Why unfixed:** The write_fix tool's insertion format clashes with multi-line Java code. The agent cannot express multi-statement insertions cleanly.

**Could spec help?** No — spec was correct. The failure is in code formatting.

#### Case 2: Collections-25 — Wrong Java version API
**Log path:** `experiment_34/logs/prompt_history_Collections_25/`

**Bug:** `IteratorUtils.collatedIterator()` null comparator handling.
**Developer fix:** Add null check with natural ordering fallback.
**Agent behavior:** Used `Comparator.naturalOrder()` (Java 8+) in a project targeting Java 6. Compilation failed because the API doesn't exist.

**Why unfixed:** Agent doesn't know the project's target Java version.

**Could spec help?** YES — Adding "target Java version: 1.6" to the spec would have prevented this API mismatch.

#### Case 3: Lang-17 — Surrogate pair code in wrong format
**Log path:** `experiment_34/logs/prompt_history_Lang_17/`

**Bug:** `CharSequenceTranslator.translate()` doesn't handle surrogate pairs.
**Developer fix:** Use `Character.codePointAt()` and advance by `Character.charCount()`.
**Agent behavior:** Correct conceptual understanding, but 62 of 33 fix attempts had syntax errors from embedded newline characters in insertion strings.

**Why unfixed:** Multi-line insertions produce invalid syntax in the tool's format.

**Could spec help?** No — spec correctly identified the surrogate pair issue.

---

### TEST_FAILURE — 3 Case Studies

#### Case 1: Collections-8 — Within 1 test of success
**Log path:** `experiment_34/logs/prompt_history_Collections_8/`

**Bug:** `UnboundedFifoBuffer` serialization (writeObject/readObject).
**Developer fix:** Fix buffer size initialization during deserialization.
**Agent behavior:** One variant produced only 1 failing test (expected buffer size 1, got 0). The agent correctly targeted serialization methods but couldn't find the exact buffer size initialization formula.

**Why unfixed:** Very specific implementation detail: the relationship between buffer capacity and element count during deserialization. The agent was extremely close.

**Could spec help?** Partially — spec could note "buffer capacity must be initialized to `size + 1` for circular buffer implementation."

#### Case 2: Lang-65 — Calendar field rounding arithmetic
**Log path:** `experiment_34/logs/prompt_history_Lang_65/`

**Bug:** `DateUtils.truncate/round()` field rounding.
**Developer fix:** Fix truncation offset calculation for specific calendar fields.
**Agent behavior:** 21 fixes all compiled and ran but produced wrong rounding results. The agent tried various offset values without finding the correct formula.

**Why unfixed:** The fix requires deep knowledge of Java's Calendar field ordinal values and their offset relationships — domain knowledge not captured in code or documentation.

**Could spec help?** Partially — spec could include the specific offset relationships between calendar fields.

#### Case 3: Collections-15 — Index adjustment after removal
**Log path:** `experiment_34/logs/prompt_history_Collections_15/`

**Bug:** `SetUniqueList.set()` index handling after removing duplicate.
**Developer fix:** Adjust index when removed position precedes target.
**Agent behavior:** Correctly targeted the `set()` method but missed that `remove(pos)` shifts elements, invalidating `index` when `pos < index`.

**Why unfixed:** The index shift semantics of `remove()` on a list are non-obvious — the agent didn't account for the element shift.

**Could spec help?** YES — "After `remove(pos)`, all indices > pos shift down by 1. If `pos < index`, decrement `index`."

---

### WRONG_DIRECTION — 3 Case Studies

#### Case 1: Math-36 — Overfits to test values
**Log path:** `experiment_34/logs/prompt_history_Math_36/`

**Bug:** `BigFraction.doubleValue()` overflow handling for large numerator/denominator.
**Developer fix:** Use proper double arithmetic with BigInteger conversion.
**Agent behavior:** Inserted checks returning hardcoded `5.0` and `5.0f` for specific conditions — reading the expected test output value directly.

**Why unfixed:** Agent overfitted to specific test assertions rather than understanding the mathematical operation.

**Could spec help?** YES — "The method must work for arbitrary BigInteger values; do not hardcode specific return values."

#### Case 2: Math-66 — Overwhelmed by scope
**Log path:** `experiment_34/logs/prompt_history_Math_66/`

**Bug:** `BrentOptimizer` logic error across 15+ lines.
**Developer fix:** Multiple coordinated changes to the optimization algorithm.
**Agent behavior:** Spec identified 15+ buggy lines. Agent attempted massive insertions touching many lines simultaneously — all fundamentally wrong.

**Why unfixed:** The fix scope (15+ lines with complex interdependencies) exceeds the agent's ability to reason about coordinated changes.

**Could spec help?** A spec that **prioritized** the 2-3 most critical lines would have been more effective than listing all 15.

#### Case 3: Compress-33 — Placeholder logic never completed
**Log path:** `experiment_34/logs/prompt_history_Compress_33/`

**Bug:** `CompressorStreamFactory` missing deflate stream detection.
**Developer fix:** Add proper deflate signature matching.
**Agent behavior:** Created `matches()` method returning `return true` as a "placeholder" — causing all streams to match as deflate. Repeated this pattern 17+ times.

**Why unfixed:** Agent used a placeholder that breaks other functionality and never replaced it with actual detection logic.

**Could spec help?** YES — providing the actual deflate signature bytes (`0x78` followed by specific check bytes) would have enabled proper detection.

---

### TIMEOUT — 2 Case Studies (both included)

#### Case 1: Lang-23 — Analysis paralysis
**Log path:** `experiment_34/logs/prompt_history_Lang_23/`
**Bug:** `ExtendedMessageFormat.hashCode()` missing override.
**Agent behavior:** Spent all 39 turns searching for equals/hashCode methods across the codebase. Never submitted a single fix attempt.

#### Case 2: Compress-43 — Insufficient fix density
**Log path:** `experiment_34/logs/prompt_history_Compress_43/`
**Bug:** `ZipArchiveOutputStream.usesDataDescriptor()` logic error.
**Agent behavior:** Only 4 fix attempts in 39 turns. Spent most time reading code.

---

## 2.4 Spec Effectiveness for Unfixed Bugs

| Assessment | Count | % | Examples |
|-----------|-------|---|---------|
| Spec correctly located bug, agent couldn't fix | 36 | 54.5% | Collections-3, Math-47, Lang-52 |
| Spec helped but missed key domain knowledge | 16 | 24.2% | Math-10, Lang-1, Lang-65 |
| Spec was too broad (too many buggy lines) | 6 | 9.1% | Math-66, Codec-11, Collections-7 |
| Spec was insufficient/misleading | 6 | 9.1% | Math-36, Compress-33, Lang-7 |
| No effective spec interaction | 2 | 3.0% | Lang-23, Compress-43 |

**Key insight:** In 54.5% of unfixed bugs, the spec was correct but the agent couldn't translate the diagnosis into a working fix. The bottleneck is fix generation and application, not bug localization.

---

# Part 3: Key Findings and Recommendations

## 3.1 Findings

1. **Combined correct patch count: 15 unique bugs** (15.3% of 98-bug pool) across both experiments, with 7 exact matches and 8 semantically equivalent fixes.

2. **E34 pipeline improvements increased both plausible patches (+50%) and correct patches (+86%)** compared to E17 (7→13 correct), demonstrating that the improved spec generation, verification, and agent loop controls are effective.

3. **The dominant failure mode is STUCK_LOOP (65.2%)** — the agent retries minor variations without fundamentally changing strategy. This is exacerbated by the 70% similarity constraint.

4. **The tool similarity constraint blocks 18.2% of unfixed bugs** where the agent has the correct diagnosis. This is the highest-ROI infrastructure improvement.

5. **Specs are effective for localization but insufficient for fix generation.** 73% of specs correctly identify the buggy code, but translating this to a correct fix requires domain knowledge, structural understanding, and code formatting skills the current pipeline lacks.

6. **The "add validation" bias** causes incorrect patches in both experiments — the agent defaults to adding guards/checks when the developer fix requires removing code.

## 3.2 Recommendations

| Priority | Recommendation | Expected Impact |
|----------|---------------|-----------------|
| HIGH | Lower or remove the 70% similarity threshold | Unblocks 12 currently-stuck bugs |
| HIGH | Add fix-direction hints to specs (ADD/REMOVE/MODIFY) | Prevents opposite-direction fixes |
| MEDIUM | Support multi-line insertions in write_fix tool | Reduces syntax errors (~15% of failures) |
| MEDIUM | Add target Java version to spec context | Prevents API version mismatches |
| MEDIUM | Limit spec buggy lines to top-3 most critical | Prevents agent scope overwhelm |
| LOW | Add domain knowledge prompts (IEEE 754, chi-square, etc.) | Helps with mathematical/domain bugs |
| LOW | Add anti-overfitting guidance to agent prompt | Prevents hardcoded-value patches |

---

# Part 4: Visualizations

All charts are in `researchAnalysis/charts/`.

| Chart | File | Description |
|-------|------|-------------|
| E17 vs E34 Comparison | `charts/e17_vs_e34_comparison.png` | Bar chart comparing plausible/correct counts, precision, and recall |
| Failure Categories | `charts/failure_categories_pie.png` | Pie chart of 66 unfixed bugs by failure category |
| Project Breakdown | `charts/project_breakdown.png` | Stacked bar: correct/incorrect/unfixed per D4J project |
| Spec Effectiveness | `charts/spec_effectiveness.png` | Horizontal bar: spec quality for unfixed bugs |
| Correct Patches Overlap | `charts/correct_patches_overlap.png` | E17-only vs shared vs E34-only correct patches |
| Match Type Distribution | `charts/match_type_distribution.png` | Donut chart: exact match vs semantically equivalent |

---

# Part 5: Detailed Per-Bug Analysis Files

| File | Description |
|------|-------------|
| `researchAnalysis/e17_plausible_patch_analysis.md` | E17: All 16 plausible patches with evidence |
| `researchAnalysis/plausible_analysis/E34/*.md` | E34: Individual per-bug analysis (24 files) |
| `researchAnalysis/unfixed_analysis/failure_categories.md` | All 66 unfixed bugs categorized with case studies |
| `researchAnalysis/unfixed_analysis/unfixed_bugs_evidence.md` | Per-bug evidence for all 66 unfixed bugs: sub-reasons, spec helpfulness, evidence paths |
| `researchAnalysis/unfixed_analysis/failure_root_causes.md` | Root cause reclassification: WHY bugs failed (not symptoms like stuck_loop) |
| `researchAnalysis/presentation/unfixed_bugs_slides.md` | Detailed slide content for unfixed bug failure patterns |
| `researchAnalysis/checkouts/` | 32 developer fixed version checkouts |
| `researchAnalysis/charts/` | 6 visualization charts |
| `researchAnalysis/reports/MASTER_REPORT.md` | This file |

---

# Appendix A: Correct Patch Evidence Summary

For each correct patch, the key evidence comparison:

### Time-15 (Exact Match)
```
Developer: if (val1 == Long.MIN_VALUE) { throw new ArithmeticException("Multiplication overflows a long: " + val1 + " * " + val2); }
Agent:     if (val1 == Long.MIN_VALUE) { throw new ArithmeticException("Multiplication overflows a long: " + val1 + " * " + val2); }
Fixed source: researchAnalysis/checkouts/Time_15_fixed/src/main/java/org/joda/time/field/FieldUtils.java:138
```

### Time-7 (Sem. Equivalent)
```
Developer: int defaultYear = DateTimeUtils.getChronology(chrono).year().get(instantMillis);  // before selectChronology
Agent:     int yearFromInstant = instant.getChronology().year().get(instant.getMillis());     // before selectChronology
Fixed source: researchAnalysis/checkouts/Time_7_fixed/src/main/java/org/joda/time/format/DateTimeFormatter.java:708
```

### Math-3 (Exact Match)
```
Developer: if (len == 1) { return a[0] * b[0]; }
Agent:     if (len == 1) { return a[0] * b[0]; }
Fixed source: researchAnalysis/checkouts/Math_3_fixed/src/main/java/org/apache/commons/math3/util/MathArrays.java:821
```

### Math-38 (Sem. Equivalent)
```
Developer: //  throw new PathIsExploredException(); // XXX  (comments out the throw)
Agent:     (deletes the throw line entirely — same effect, the throw is removed)
Fixed source: researchAnalysis/checkouts/Math_38_fixed/ (PathIsExploredException throws commented out)
```

### Math-53 (Sem. Equivalent)
```
Developer: if (isNaN || rhs.isNaN) { return NaN; }
Agent:     if (this.isNaN() || rhs.isNaN()) { return createComplex(Double.NaN, Double.NaN); }
Fixed source: researchAnalysis/checkouts/Math_53_fixed/src/main/java/org/apache/commons/math/complex/Complex.java:153
```

### Math-98 (Exact Match)
```
Developer: final BigDecimal[] out = new BigDecimal[nRows];  /  final double[] out = new double[nRows];
Agent:     final BigDecimal[] out = new BigDecimal[nRows];  /  final double[] out = new double[nRows];
Fixed source: researchAnalysis/checkouts/Math_98_fixed/src/java/org/apache/commons/math/linear/{BigMatrixImpl,RealMatrixImpl}.java
```

### Math-100 (Exact Match)
```
Developer: problem.getUnboundParameters().length  (3 locations)
Agent:     problem.getUnboundParameters().length  (3 locations)
Fixed source: researchAnalysis/checkouts/Math_100_fixed/src/java/org/apache/commons/math/estimation/AbstractEstimator.java:166,202,207
```

### Lang-11 (Sem. Equivalent)
```
Developer: } else { if (end <= start) { throw new IllegalArgumentException(...); } }  (in else branch)
Agent:     if (start >= end) { throw new IllegalArgumentException(...); }              (unconditional — equivalent)
Fixed source: researchAnalysis/checkouts/Lang_11_fixed/src/main/java/org/apache/commons/lang3/RandomStringUtils.java:245
```

### Lang-35 (Sem. Equivalent)
```
Developer: throw new IllegalArgumentException("Arguments cannot both be null");  (replaces buggy code)
Agent:     if (array == null && element == null) { throw new IllegalArgumentException("Both array and element cannot be null"); }  (guard before buggy code)
Fixed source: researchAnalysis/checkouts/Lang_35_fixed/src/main/java/org/apache/commons/lang3/ArrayUtils.java:3295
```

### Lang-45 (Sem. Equivalent)
```
Developer: if (lower > str.length()) { lower = str.length(); }
Agent:     if (lower > str.length()) { lower = str.length(); }  (+ redundant upper check)
Fixed source: researchAnalysis/checkouts/Lang_45_fixed/src/java/org/apache/commons/lang/WordUtils.java:614
```

### Lang-61 (Exact Match)
```
Developer: int len = size - strLen + 1;
Agent:     int len = size - strLen + 1;
Fixed source: researchAnalysis/checkouts/Lang_61_fixed/ (StrBuilder.java)
```

### Compress-3 (Sem. Equivalent)
```
Developer: boolean haveUnclosedEntry = false;  (set true on put, false on close, check on finish)
Agent:     boolean entryOpen = false;           (identical lifecycle, different name)
Fixed source: researchAnalysis/checkouts/Compress_3_fixed/src/main/java/org/apache/commons/compress/archivers/tar/TarArchiveOutputStream.java
```

### Compress-12 (Sem. Equivalent)
```
Developer: catch (IllegalArgumentException e) { IOException ioe = new IOException("Error..."); ioe.initCause(e); throw ioe; }
Agent:     catch (IllegalArgumentException e) { throw new IOException("Invalid tar header", e); }
Fixed source: researchAnalysis/checkouts/Compress_12_fixed/src/main/java/org/apache/commons/compress/archivers/tar/TarArchiveInputStream.java
```

### Compress-14 (Exact Match)
```
Developer: if (buffer[start] == 0) { return 0L; }
Agent:     if (buffer[start] == 0) { return 0; }   (0 auto-widens to 0L)
Fixed source: researchAnalysis/checkouts/Compress_14_fixed/src/main/java/org/apache/commons/compress/archivers/tar/TarUtils.java:65
```

### Csv-5 (Exact Match)
```
Developer: if (recordSeparator != null) { out.append(recordSeparator); }
Agent:     if (recordSeparator != null) { out.append(recordSeparator); }
Fixed source: researchAnalysis/checkouts/Csv_5_fixed/src/main/java/org/apache/commons/csv/CSVPrinter.java:325
```
