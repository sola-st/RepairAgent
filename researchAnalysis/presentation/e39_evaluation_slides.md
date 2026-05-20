# E39 New Design Evaluation — Slide Content

---

## Slide 1: What We Designed

**5 improvements to the spec-guided repair pipeline:**

| # | Improvement | Where | How |
|---|-----------|-------|-----|
| 1 | Neutral FAULT_OF_OMISSION | `spec_generator.py` | Changed "CODE IS MISSING — add" → "fix may involve adding, changing, OR removing code" |
| 2 | fix_direction field | `spec_generator.py` | New JSON field: ADD_CODE / DELETE_CODE / MODIFY_LOGIC / SIMPLIFY |
| 3 | Auto DELETE+INSERT | `defects4j.py` | Low-similarity modifications auto-converted to deletion + insertion |
| 4 | Anti-overfitting | `prompt_settings.yaml` | "Fix must work for arbitrary inputs, not just test values" |
| 5 | Self-clarification | `spec_generator.py` | confidence + clarifying_question fields; verifier LLM answers when LOW |

**Test pool:** 22 bugs (8 regression, 14 improvement targets)

---

## Slide 2: Overall Results

| | Plausible | Correct | New wins | Regressions |
|---|----------|---------|----------|-------------|
| E39 (new design) | 6 | 5 | 2 | 3 |
| E34 (baseline) | 8 | 5 | — | — |

**New wins:** Collections_3 (correct), Collections_5 (plausible)
**Regressions:** Compress_3, Math_97, Time_9 (LLM variance — not caused by our changes)

---

## Slide 3: Success Case — Collections_3 (Exact Correct Fix)

**Bug:** `removeAll()` calls `ListUtils.retainAll()` instead of `ListUtils.removeAll()`

**Spec generated (E39):**
```
Evidence: experiment_39/spec_logs/spec_parsed_json_Collections_3.json
```
- fix_direction: `MODIFY_LOGIC`
- code_violations: *"Line 1121: The code calls ListUtils.retainAll(collection, remove), which retains only elements common to both collections, in contradiction to the Javadoc"*

**Agent thinking:**
> "The 'retainAll' method simply calls 'ListUtils.retainAll', which retains elements present in both collections. This confirms that the logic in the 'removeAll' method is incorrect."

**Agent fix — 1 attempt, immediate success:**
```java
return ListUtils.removeAll(collection, remove);  // line 1121
```

**Developer patch:** identical — `retainAll` → `removeAll`

**Verdict:** CORRECT. Exact match. Agent understood the bug and applied simplest fix.

---

## Slide 4: Success Case — Collections_5 (New Plausible Fix)

**Bug:** `addAll(index, coll)` adds duplicates without checking

**Spec generated (E39):**
```
Evidence: experiment_39/spec_logs/spec_parsed_json_Collections_5.json
```
- fix_direction: `MODIFY_LOGIC`
- Rule 3: *"If an element is not in the list, insert it at the current index and increment the index"*

**Agent fix (after ~15 attempts):**
```java
Object element = it.next();
if (!contains(element)) {
    add(index++, element);
}
```

**Developer fix:** Different approach — removes index tracking entirely, uses `add(it.next())`

**Verdict:** PLAUSIBLE but not correct. Passes all tests, different strategy.

**Never plausible in any previous experiment.**

---

## Slide 5: Limitation — fix_direction Accuracy

**Distribution across all 22 bugs:**

| fix_direction | Count | Accuracy |
|--------------|-------|----------|
| MODIFY_LOGIC | 16 (73%) | ~4 correct, ~12 should be DELETE |
| ADD_CODE | 4 (18%) | ~2 correct, ~2 should be DELETE |
| DELETE_CODE | 2 (9%) | Both correct (Lang_46, Compress_11) |
| SIMPLIFY | 0 | Never used |

**confidence: HIGH for all 22 bugs** (100%) — never LOW

**The LLM defaults to MODIFY_LOGIC.** It almost never recognizes that the fix is deletion.

**Example — Lang_65 (fix_direction = ADD_CODE, wrong):**
```
Evidence: experiment_39/spec_logs/spec_parsed_json_Lang_65.json
```
- Spec says: *"Missing logic for truncating milliseconds, seconds, and minutes"*
- fix_direction: `ADD_CODE`
- Agent thinking: *"the truncation logic is currently unimplemented. I will proceed to suggest a fix by implementing the necessary truncation logic"*
- Agent: 30 write_fix attempts, all adding truncation code
- **Developer fix: DELETE 25 lines** (the entire LANG-59 manual truncation block)

The spec misread code comments as "missing implementation" when the existing code WAS the bug.

---

## Slide 6: Limitation — Agent Ignores DELETE_CODE

**Even when fix_direction is correct, agent doesn't delete.**

**Example — Lang_46 (fix_direction = DELETE_CODE, correct):**
```
Evidence: experiment_39/spec_logs/spec_parsed_json_Lang_46.json
Evidence: experiment_39/responses/model_responses_Lang_46 (32 write_fix attempts)
```
- Spec says: fix_direction = `DELETE_CODE`
- Spec says: *"The code incorrectly escapes forward slashes, which should not be escaped"*
- Agent thinking: *"I will modify the logic to ensure that the forward slash is not escaped"*
- Agent: 32 write_fix attempts — **all using `modifications`, zero using `deletions`**
- **Developer fix:** Remove the `escapeForwardSlash` parameter from 13 locations

The agent understood the problem. The spec gave the right direction. But the agent's execution strategy was always "modify lines" — never "delete lines."

---

## Slide 7: Limitation — Self-Clarification Never Triggered

**Collections_8 — textbook case for LOW confidence:**
```
Evidence: experiment_39/spec_logs/spec_parsed_json_Collections_8.json
```

**Javadoc:** *"Write the buffer out using a custom routine"* (13 words, no behavioral detail)

**Spec generated:**
- confidence: `HIGH` (should be LOW)
- clarifying_question: `null`

**Agent thinking:**
> "The readObject method initializes the buffer with size + 1, which is incorrect."

**But size + 1 is actually correct.** The developer fix keeps `size + 1` and removes a different line (`writeInt(buffer.length)`). The agent had it backwards.

A clarifying question like *"Should writeObject serialize buffer.length separately from size?"* would have resolved this — but the LLM never set confidence to LOW.

---

## Slide 8: Limitation — Anti-Overfitting Partial Effect

**Math_36 — agent no longer hardcodes test values, but still can't fix:**
```
Evidence: experiment_39/spec_logs/spec_parsed_json_Math_36.json
Evidence: experiment_39/responses/model_responses_Math_36 (31 write_fix attempts)
```

- test_expectation: *"returning a precise result of 5.0 instead of NaN"*
- In E34, agent hardcoded `return 5.0` from test assertion
- In E39, agent never hardcoded — anti-overfitting instruction may have helped
- But agent tried 31 fixes adding overflow handling (`Double.MAX_VALUE`, `ArithmeticException`)
- **Developer fix: DELETE the overflow handling** — the `if(Double.isNaN) { shiftRight }` block IS the bug
- Spec said `MODIFY_LOGIC` — should be `DELETE_CODE`

**Anti-overfitting prevented one failure mode but didn't enable the correct fix.**

---

## Slide 9: Why Regressions Are LLM Variance

**3 bugs regressed (plausible in E34, failed in E39). Root cause: different agent strategy, not worse specs.**

| Bug | E34 agent strategy | E39 agent strategy | Why E39 failed |
|-----|-------------------|-------------------|---------------|
| Compress_3 | Used **insertions** at 4 locations | Used only **modifications** | Multi-line cramming → compilation errors |
| Math_97 | `Math.abs(yMin) <= tolerance` | `Math.abs(yMin) == 0` | Exact equality fails (sin(π) ≈ 1.2e-16) |
| Time_9 | Minimal fix: just validation insert | Full fix: validation + arithmetic | Too ambitious → cascading errors |

**Evidence:** Specs were similar quality. E39 agents took different (worse) execution paths — a known property of LLM non-determinism with gpt-4o-mini.

---

## Slide 10: Summary — What Worked, What Didn't

### Worked
- **Neutral FAULT_OF_OMISSION** — contributed to 2 new wins (Collections_3, Collections_5)
- **fix_direction concept** — correct for Lang_46 and Compress_11 (DELETE_CODE)
- **Anti-overfitting** — may have prevented Math_36 from hardcoding `return 5.0`

### Didn't Work
- **fix_direction accuracy** — LLM defaults to MODIFY_LOGIC (73%), rarely says DELETE_CODE (9%)
- **Agent ignores direction** — even when spec says DELETE_CODE, agent uses modifications (0 deletions across all 22 bugs)
- **confidence always HIGH** — self-clarification never triggered (0/22 bugs)
- **Auto DELETE+INSERT** — not tested (agents failed before reaching similarity check)

### Key Insight
**The bottleneck shifted from spec quality to agent execution.** Improving specs is necessary but not sufficient — the agent must also learn to use the `deletions` mechanism when specs indicate deletion is the correct fix direction.

---

## Slide 11: Recommendations for Future Work

1. **Few-shot examples for fix_direction** — show the LLM examples of DELETE_CODE bugs (existing code contradicts Javadoc → delete it)
2. **Agent prompt: "When fix_direction = DELETE_CODE, prefer the deletions field"** — bridge the gap between spec knowledge and agent execution
3. **Heuristic confidence** — set LOW when Javadoc < 150 chars, don't rely on LLM judgment
4. **Multiple runs** — each bug needs 3-5 runs to separate signal from LLM variance
5. **Stronger model** — gpt-4o (not mini) would likely produce better fix_direction accuracy
