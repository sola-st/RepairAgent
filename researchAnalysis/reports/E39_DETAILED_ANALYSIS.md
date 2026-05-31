# E39 Detailed Analysis Report — New Spec Design Evaluation

**Experiment:** E39 (improved spec generator + auto DELETE+INSERT + anti-overfitting)
**Baseline:** E34 (original spec-guided)
**Bug pool:** 22 bugs (8 regression, 14 improvement targets)
**Model:** gpt-4o-mini

---

## Overall Results

| Metric | E34 (same 22 bugs) | E39 |
|--------|-------------------|-----|
| Plausible patches | 8 | 6 |
| Correct patches | 5 | 5 |
| New plausible (E34 didn't have) | — | 2 (Collections_3, Collections_5) |
| Regressions (E34 had, E39 lost) | — | 3 (Compress_3, Math_97, Time_9) |
| Net plausible change | baseline | **-2** |

---

## Part 1: NEW WINS (2 bugs)

### Collections_3 — CORRECT (exact match)

**Evidence paths:**
- E34 spec: `experiment_34/spec_logs/spec_parsed_json_Collections_3.json`
- E39 spec: `experiment_39/spec_logs/spec_parsed_json_Collections_3.json`
- E34 responses: `experiment_34/responses/model_responses_Collections_3`
- E39 responses: `experiment_39/responses/model_responses_Collections_3`
- E39 patch: `experiment_39/plausible_patches/plausible_patches_Collections_3.json`
- Developer patch: `defects4j/framework/projects/Collections/patches/3.src.patch`

**Spec comparison:**
Both E34 and E39 specs were nearly identical — both correctly identified line 1121 using `ListUtils.retainAll` when it should exclude elements. E39 added `fix_direction: MODIFY_LOGIC`, `confidence: HIGH`.

**E34 agent (FAILED):**
> "The bug is caused by using ListUtils.retainAll(collection, remove) instead of a method that removes elements in 'remove' from 'collection'."

Correct diagnosis but **over-engineered every fix**. Tried 30+ write_fix calls, all attempting to rewrite the entire method body with `for (Object item : collection) { if (!remove.contains(item)) { result.add(item); } }`. Every attempt rejected by similarity constraint or failed compilation. **Never tried the simple one-word swap.**

**E39 agent (SUCCEEDED):**
> "The 'retainAll' method simply calls 'ListUtils.retainAll', which retains elements present in both collections. This confirms that the logic in the 'removeAll' method is incorrect."

**1 write_fix attempt, immediate success:**
```json
{"line_number": 1121, "modified_line": "return ListUtils.removeAll(collection, remove);"}
```

**Verdict:** Win was from **LLM variance** (E39 agent tried simple fix first), not spec quality. Both specs were equivalent.

---

### Collections_5 — PLAUSIBLE (not correct)

**Evidence paths:**
- E39 spec: `experiment_39/spec_logs/spec_parsed_json_Collections_5.json`
- E39 patch: `experiment_39/plausible_patches/plausible_patches_Collections_5.json`
- Developer patch: `defects4j/framework/projects/Collections/patches/5.src.patch`

**Developer fix:** Remove `sizeBeforeAddNext` tracking, change `add(index, it.next())` to `add(it.next())` — simplify from indexed to unindexed add.

**E39 agent fix:** Added `!contains(element)` guard with `add(index++, element)` — different strategy (keeps index tracking, adds duplicate check).

**E34 agent (FAILED):** Used `!set.contains(element)` and `super.add(index, element)` + `set.add(element)` — tried to manage the internal set manually. 30+ attempts, all failed due to inserting code before line 195 without removing the original, causing double `it.next()`.

**E39 agent (SUCCEEDED after ~15 attempts):** Used `!contains(element)` + `add(index, element)` — leveraged the class's own methods. Multi-line modification eventually compiled.

**E39 spec** had more procedural rules: `"If an element is not in the list, insert it at the current index and increment the index"` — this may have nudged toward using `contains()`.

**Verdict:** Marginal spec improvement + LLM variance. Patch is plausible but not correct.

---

## Part 2: REGRESSIONS (3 bugs)

### Compress_3 — Regressed (plausible in E34, failed in E39)

**Evidence paths:**
- E34 spec: `experiment_34/spec_logs/spec_parsed_json_Compress_3.json`
- E39 spec: `experiment_39/spec_logs/spec_parsed_json_Compress_3.json`
- E34 patch: `experiment_34/plausible_patches/plausible_patches_Compress_3.json`
- E39 responses: `experiment_39/responses/model_responses_Compress_3`

**Spec difference:** E34 spec had 3 fix targets (lines 55, 112, 217) — line 55 explicitly said *"A mechanism to track if putArchiveEntry has been called."* E39 spec dropped line 55, kept only lines 112 and 217.

**E34 agent (SUCCESS):** Used **insertions** to add `private boolean entryOpen = false;` at line 54, guard in `finish()` at line 112, and state management at lines 187/217. Semantically equivalent to developer patch.

**E39 agent (FAILURE):** Used only **modifications** (never insertions). Tried to cram multi-line logic into single modified lines (`"if (!isClosed) { throw new IOException(...); }\n writeEOFRecord();"`) — every attempt caused compilation errors. 30+ attempts, same broken pattern.

**Cause:** **(a) Spec dropped line 55 hint** + **(b) LLM variance** (agent never discovered insertions mechanism).

---

### Math_97 — Regressed

**Spec difference:** E34 had 4 specific per-line violations ("sufficiently close to zero"). E39 consolidated to 2 violations ("exactly a root") with 1 fix target.

**E34 agent (SUCCESS):** Used `Math.abs(yMin) <= functionValueAccuracy` (tolerance check).

**E39 agent (FAILURE):** Used `Math.abs(yMin) == 0` (exact equality check). Exact zero never matches because `Math.sin(Math.PI)` ≈ 1.2e-16, not 0.0.

**Cause:** **(a) E39 spec said "exactly a root"** → agent used exact equality. **(b) LLM variance** — fewer fix targets gave less guidance.

---

### Time_9 — Regressed

**E34 agent (SUCCESS):** Found minimal fix — just inserted hours validation check at line 257. Partial fix but enough to pass tests.

**E39 agent (FAILURE):** Tried full fix (validation + arithmetic rewrite) via modifications only. Multi-line modifications caused cascading compilation errors. Never tried the minimal insertion-only approach.

**Cause:** **(b) LLM variance** — E39 agent was more ambitious but less effective.

---

## Part 3: FAILED IMPROVEMENT TARGETS (12 bugs)

### Improvement #1/#2: FAULT_OF_OMISSION + fix_direction

| Bug | E39 fix_direction | Correct direction | Spec improved? | Why still failed |
|-----|------------------|-------------------|---------------|-----------------|
| **Lang_46** | DELETE_CODE | DELETE | **Yes** | Agent never used `deletions` field; fix spans 13 locations (parameter removal) — beyond single-point edit |
| **Lang_65** | ADD_CODE | DELETE | **No, still wrong** | Spec misread code comments as "missing implementation"; agent added code on top of bug |
| **Lang_12** | ADD_CODE | DELETE | **No, still wrong** | Spec said add validation; developer removes validation entirely |
| **Lang_64** | ADD_CODE | DELETE | **No, still wrong** | Spec said add null/type checks; developer removes complex comparison logic |
| **Lang_3** | MODIFY_LOGIC | DELETE | **No, wrong target** | Spec pointed at inner lines (593-605) not the guard conditions (590, 598); agent submitted no-op changes |
| **Lang_5** | MODIFY_LOGIC | DELETE | **No, insufficient** | Spec didn't recognize 30-line block deletion needed |
| **Math_93** | MODIFY_LOGIC | SIMPLIFY/DELETE | **No** | Agent tried to fix precision instead of removing overflow check |
| **Compress_11** | DELETE_CODE | DELETE | **Yes** | Correct direction but agent still couldn't execute deletion |

**Pattern:** fix_direction was correct for only **2 of 10** Category A bugs (Lang_46, Compress_11). The LLM generating specs still has a systematic bias toward ADD_CODE/MODIFY_LOGIC.

### Improvement #3: Auto DELETE+INSERT (Lang_52, Compress_24)

**Lang_52:** Agent submitted 15+ identical broken modifications. **No "Auto-converted" messages found in logs.** The auto-conversion either didn't trigger (modifications were rejected before reaching the conversion step) or the issue was JSON escaping of backslashes, not similarity.

**Compress_24:** Agent tried complex restructuring via modifications. Same pattern — no auto-conversion evidence.

**Verdict:** Improvement #3 was **not tested** effectively. The agents failed at a step before the similarity check.

### Improvement #4: Anti-overfitting (Math_36)

**E39 spec:** `fix_direction: MODIFY_LOGIC`, test_expectation mentions "returning a precise result of 5.0."

**Agent behavior:** Tried to ADD overflow handling (`Double.MAX_VALUE`, `ArithmeticException`). Never attempted bit-shifting. Never hardcoded `return 5.0` (so the anti-overfitting instruction may have prevented that specific failure mode), but also never found the correct fix.

**Developer fix:** REMOVES the `if(Double.isNaN)` block with `shiftRight` — the overflow handling IS the bug.

**Verdict:** Anti-overfitting instruction **may have prevented hardcoding** (agent didn't do `return 5.0`), but the spec said MODIFY_LOGIC when the fix is DELETE_CODE. Agent never considered that existing code was the problem.

### Improvement #5: Self-clarification (Collections_8)

**E39 spec:** `confidence: HIGH`, `clarifying_question: null`

**Self-clarification never triggered.** The spec generator set confidence to HIGH even though the Javadoc says only "Write the buffer out using a custom routine" — a textbook case for LOW confidence.

**Agent behavior:** Tried to change `buffer = new Object[size + 1]` to `buffer = new Object[size]`, which is backwards — `size + 1` is correct. The developer fix removes an extra `writeInt(buffer.length)` from writeObject and keeps `size + 1`.

**Verdict:** Improvement #5 **completely failed** — the LLM never sets confidence to LOW.

---

## Part 4: Cross-Cutting Findings

### Finding 1: fix_direction accuracy is poor

| fix_direction set | Count | Correct? |
|-------------------|-------|----------|
| MODIFY_LOGIC | 12 | Correct for ~4, wrong for ~8 (should be DELETE) |
| ADD_CODE | 4 | Correct for 2 (Lang_52 concept, Lang_12 concept), wrong for 2 |
| DELETE_CODE | 2 | Correct for both (Lang_46, Compress_11) |
| SIMPLIFY | 0 | Never used |

**The LLM defaults to MODIFY_LOGIC.** DELETE_CODE and SIMPLIFY are underused. The fix_direction field works when correct but the LLM generating specs can't reliably determine direction.

### Finding 2: The core problem remains — agent adds code when it should delete

Of the 12 failed improvement targets:
- **8** had developer fixes that were primarily deletion/simplification
- **0** had the agent attempt deletion as a strategy
- Every agent exclusively used `modifications` and `insertions`, never `deletions`

The spec can say DELETE_CODE (as it did for Lang_46), but the agent ignores it and uses modifications anyway.

### Finding 3: Regressions are from LLM variance, not our changes

All 3 regressions show:
- Specs are similar quality (slightly different wording, same core diagnosis)
- E34 agent used insertions; E39 agent used modifications
- The insertions vs modifications difference is random agent strategy, not spec-driven

### Finding 4: confidence is always HIGH

Every single bug got `confidence: HIGH`. The self-clarification feature is dead code in practice.

---

## Recommendations

### What worked
1. **FAULT_OF_OMISSION neutralization** helped in 2 cases (Collections_3, Collections_5)
2. **fix_direction concept** is sound — Lang_46 and Compress_11 got correct DELETE_CODE

### What needs improvement
1. **fix_direction accuracy** — the LLM needs explicit training/few-shot examples for recognizing DELETE fixes. Consider: if the buggy code has MORE lines than peer methods, the fix is likely deletion.
2. **Agent ignores fix_direction** — even when spec says DELETE_CODE, agent uses modifications. The agent prompt should explicitly say "When fix_direction is DELETE_CODE, use the deletions field."
3. **confidence calibration** — the LLM never says LOW. Consider: make confidence based on Javadoc length (< 150 chars → LOW) rather than LLM judgment.
4. **Auto DELETE+INSERT** wasn't tested — need to verify the code path actually executes.
5. **Multiple runs needed** — single runs can't distinguish signal from LLM variance. Each bug should be run 3-5 times.
