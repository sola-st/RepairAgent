# Unfixed Bug Slides — Detailed Content for PowerPoint (Revised)

---

## Slide: Corrected Failure Category Overview

**66 of 98 bugs unfixed (67.3%)**

### Corrected Breakdown

Previously, we reported 12 bugs as "blocked by infrastructure (similarity constraint)." After verifying each agent's rejected fix against the developer patch, **only 2 had genuinely correct fixes blocked.** The other 10 had wrong fixes — the similarity rejection masked deeper agent logic errors.

| Category | Count | % | Root Cause | Slide |
|----------|-------|---|------------|-------|
| STUCK_LOOP | 41 | 62.1% | Agent retries minor variations of the same wrong fix | Slides 2 & 6 |
| COMPILE_ERROR | 10 | 15.2% | Patches have syntax/formatting errors | *(no dedicated slide — tool formatting issue, partially addressed by FIX SHAPE guidance in E17)* |
| TEST_FAILURE | 6 | 9.1% | Patches compile but produce wrong output | Slide 3 |
| WRONG_DIRECTION | 5 | 7.6% | Agent pursues fundamentally wrong fix strategy | Slide 4 |
| TIMEOUT | 2 | 3.0% | Agent spends all turns reading, never attempts fix | Slide 5 |
| INFRA_BLOCKED (correct fix rejected) | 2 | 3.0% | Tool's similarity constraint rejected a correct fix | Slide 1 |

**COMPILE_ERROR (10 bugs):** Time_3, Time_5, Math_106, Lang_17, Lang_31, Codec_6, Codec_15, Collections_17, Collections_25, Compress_29. These fail because the agent can't express multi-line Java in the tool's format. E17 partially addressed this with FIX SHAPE guidance (telling agents to use insertions). Not given a dedicated slide because it's a tool formatting issue rather than an agent reasoning limitation.

*(Previously STUCK_LOOP was 43, but 2 are reclassified as INFRA_BLOCKED)*

### Key Correction

| Original Claim | Verified Reality |
|----------------|-----------------|
| 12 bugs blocked by 70% similarity constraint | Only **2** had correct fixes blocked (Lang_52, Compress_24) |
| Infrastructure is the #1 improvement target | Agent reasoning is the #1 bottleneck — 64 of 66 unfixed bugs failed due to agent limitations, not tool limitations |
| Specs correctly located bug in 73% of cases | True — but correct localization doesn't lead to correct fixes |

*(Use chart: `researchAnalysis/charts/failure_categories_pie.png` — update to reflect corrected numbers)*

---

---

## Slide 1: INFRA_BLOCKED — Lang_52 & Compress_24

### Title: "2 Correct Fixes the Tool Wouldn't Accept"

**Pattern size: 2 of 66 unfixed bugs (3.0%)**
**Bugs:** Lang_52, Compress_24

These are the only 2 bugs where the agent produced the correct fix and the tool rejected it.

---

### Lang_52 — Forward Slash Escape (EXACT MATCH with developer)

**The Bug:**
- `StringEscapeUtils.escapeJavaScript()` doesn't escape forward slashes (`/`)
- Buggy source: `auto_gpt_workspace/lang_52_buggy/src/java/org/apache/commons/lang/StringEscapeUtils.java:236`
- Line 236 is the `default :` case — missing a `case '/'` handler before it

**Developer Fix:**
- D4J patch: `defects4j/framework/projects/Lang/patches/52.src.patch`
- Adds `case '/': out.write('\\'); out.write('/'); break;` before the `default :` case

**Agent's Rejected Fix:**
- Agent logs: `experiment_34/logs/prompt_history_Lang_52/`
- Tried to modify line 236 to: `case '/': out.write('\\'); out.write('/'); break;`
- **Identical code to developer fix**
- Rejected: **45% similarity** (threshold: 70%)
- Why: original line was `default :` (3 tokens) → new line has 11 tokens

**Spec:**
- Parsed spec: `experiment_34/spec_logs/spec_parsed_json_Lang_52.json`
- Correctly identified: "Line 236: code does not handle forward slash '/'"
- Test expectation: "`</script>` should be escaped as `<\\/script>`"

**Why It Failed:**
The agent used `modifications` (which has the 70% check) instead of `deletions` + `insertions` (which don't). Had the agent inserted the `case '/'` block as a new line BEFORE line 236, no similarity check would apply.

| Verdict | EXACT_MATCH — agent had the identical fix, tool rejected it |
|---------|-------------------------------------------------------------|

---

### Compress_24 — Octal Parsing Restructure (SEMANTICALLY EQUIVALENT)

**The Bug:**
- `TarUtils.parseOctal()` throws `IllegalArgumentException` on valid tar headers with trailing characters
- Buggy source: `auto_gpt_workspace/compress_24_buggy/src/main/java/org/apache/commons/compress/archivers/tar/TarUtils.java:129-139`
- The `while` loop over-strips trailing bytes, hitting `start == end` prematurely

**Developer Fix:**
- D4J patch: `defects4j/framework/projects/Compress/patches/24.src.patch`
- Restructures: `while` loop → `if/else` check (single decrement) + new `while` loop with `start < end - 1`
- Changes error parameter from `start` to `end-1`

**Agent's Rejected Fix:**
- Agent logs: `experiment_34/logs/prompt_history_Compress_24/`
- Attempted same restructure: `if (trailer == 0 || trailer == ' ') { end--; } else { throw ... }` then `while (start < end - 1 && ...)`
- Rejected: **20-47% similarity** across 7 modified lines (threshold: 70%)
- Agent added an extra `else if` for octal digits (slight over-engineering) but core logic matches

**Spec:**
- Parsed spec: `experiment_34/spec_logs/spec_parsed_json_Compress_24.json`
- Correctly identified: "throws IllegalArgumentException prematurely when valid extra digits exist"

**Why It Failed:**
Multi-line structural changes (while→if/else) cause massive similarity drops on every affected line. The tool can't accept structural refactoring even when the result is correct.

| Verdict | SEM. EQUIVALENT — same logic, slightly different style, tool rejected all 7 lines |
|---------|-----------------------------------------------------------------------------------|

---

### Slide Key Takeaway
> Only 2 of the 12 originally-claimed "infrastructure-blocked" bugs actually had correct fixes. The tool's similarity constraint is a real limitation but a minor one (3% of unfixed bugs). The bigger problem: in the other 10 cases, the similarity rejection **masked** the fact that the agent's fix was also wrong.

---

---

## Slide 2: STUCK_LOOP — Math_10

### Title: "Missing Domain Knowledge: IEEE 754 Signed Zero"

**Pattern size: 41 of 66 unfixed bugs (62.1%) — the dominant failure mode**
**All bugs in this pattern:** Time_2, Time_4, Time_8, Time_10, Time_12, Math_10, Math_31, Math_44, Math_47, Math_55, Math_78, Math_81, Math_88, Math_92, Math_93, Lang_1, Lang_3, Lang_5, Lang_12, Lang_30, Lang_32, Lang_36, Lang_41, Lang_46, Lang_50, Lang_53, Lang_54, Lang_64, Compress_11, Compress_17, Compress_35, Compress_36, Compress_40, Compress_45, Csv_16, Codec_11, Codec_13, Collections_2, Collections_3, Collections_7, Compress_24
*(Note: Lang_52 and Compress_24 moved to INFRA_BLOCKED; Math_47 was originally here but is COMPILE_ERROR-adjacent)*

### The Bug
- `DSCompiler.atan2()` doesn't handle `+0.0` vs `-0.0` correctly
- In IEEE 754, `+0.0 == -0.0` is `true` in Java, but `atan2(+0.0, x)` and `atan2(-0.0, x)` must return different values
- File: `auto_gpt_workspace/math_10_buggy/src/main/java/org/apache/commons/math3/analysis/differentiation/DSCompiler.java`

### What the Spec Said
- Spec: `experiment_34/spec_logs/spec_parsed_json_Math_10.json`
- Identified `atan2` as the buggy method
- Test expectation: `atan2(-0.0, 0.0)` should return `-PI`, `atan2(+0.0, 0.0)` should return `+0.0`
- **Spec did NOT mention that Java's `==` treats +0.0 and -0.0 as equal**

### Developer Fix
- D4J patch: `defects4j/framework/projects/Math/patches/10.src.patch`
- Uses `Double.doubleToLongBits(y[yOffset])` to distinguish `+0.0` from `-0.0`
- Adds special-case handling for 8 combinations of signed zero inputs

### What the Agent Did
- Logs: `experiment_34/logs/prompt_history_Math_10/`
- **27 fix attempts**, all using `y == 0.0` checks:
  ```java
  if (y[yOffset] == 0.0) {  // BUG: matches BOTH +0.0 and -0.0
      if (x[xOffset] >= 0.0) { ... }
  }
  ```
- Never discovered `Double.doubleToLongBits()` — the only way to distinguish signed zeros in Java
- Each attempt produced wrong results for `-0.0` inputs, agent tweaked conditions but never changed the comparison method

### The Limitation: Domain Knowledge Gap

| What Agent Used | What Was Needed |
|----------------|-----------------|
| `y == 0.0` | `Double.doubleToLongBits(y) == Double.doubleToLongBits(+0.0)` |
| Java equality (`==`) | IEEE 754 bit-level comparison |
| "Zero is zero" mental model | "+0.0 and -0.0 are distinct bit patterns" |

### Could Spec Help?
**YES** — Adding one sentence to the spec would fix this:
> "Java's `==` operator treats +0.0 and -0.0 as equal. Use `Double.doubleToLongBits()` for signed-zero comparison."

### Slide Key Takeaway
> The agent tried 27 variations of `y == 0.0` without ever questioning whether Java's equality operator was the right tool. This is a domain knowledge gap that specs CAN address — a single sentence about IEEE 754 signed-zero semantics would have unlocked the correct fix.

### Evidence
| Item | Path |
|------|------|
| Buggy source | `auto_gpt_workspace/math_10_buggy/.../DSCompiler.java` |
| D4J patch | `defects4j/framework/projects/Math/patches/10.src.patch` |
| Spec | `experiment_34/spec_logs/spec_parsed_json_Math_10.json` |
| Agent logs | `experiment_34/logs/prompt_history_Math_10/` |

---

---

## Slide 3: TEST_FAILURE — Lang_65

### Title: "Spec Says 'Add Code' — Developer Says 'Delete Code'"

**Pattern size: 6 of 66 unfixed bugs (9.1%)**
**All bugs in this pattern:** Math_9, Lang_65, Collections_5, Collections_8, Collections_15, Compress_4

In these bugs, the agent's patches compile and run but produce wrong output — the agent is close but can't find the correct logic.

### The Bug
- `DateUtils.modify()` breaks during daylight saving time transitions (Oct 31, 2004: MDT→MST)
- A previous "fix" (LANG-59) added raw millisecond arithmetic that bypasses Calendar's timezone awareness
- File: `auto_gpt_workspace/lang_65_buggy/src/java/org/apache/commons/lang/time/DateUtils.java:619-640`

### What the Spec Said
- Spec: `experiment_34/spec_logs/spec_parsed_json_Lang_65.json`
- 8 code violations at lines 624, 631, 633, 635, 637, 639, 709, 710
- All marked: **"FAULT_OF_OMISSION — CODE IS MISSING HERE"**
- Test: `expected: Oct 31 01:02:03 MDT, actual: Oct 31 01:02:03 MST`
- **Spec told the agent code needs to be ADDED at 8 locations**

### Developer Fix — The Counter-Intuitive Solution
- D4J patch: `defects4j/framework/projects/Lang/patches/65.src.patch`
- **DELETES the entire 25-line LANG-59 section:**
  ```java
  // DELETED: raw millisecond arithmetic that breaks DST
  Date date = val.getTime();
  long time = date.getTime();
  time = time - millisecs;      // loses TimeZone!
  date.setTime(time);           // wrong TZ applied
  val.setTime(date);
  ```
- By removing this, Calendar's native `set()`/`add()` operations handle DST correctly

### What the Agent Did
- Logs: `experiment_34/logs/prompt_history_Lang_65/`
- **21 fix attempts**, all trying to ADD truncation code at the empty comment lines:
  ```java
  val.set(Calendar.MILLISECOND, 0);
  val.set(Calendar.SECOND, 0);
  val.set(Calendar.MINUTE, 0);
  ```
- All compiled but produced wrong DST results
- Never considered DELETING the surrounding LANG-59 code
- Interpreted "CODE IS MISSING" as "fill in the blanks" instead of "the whole section is wrong"

### The Limitation: "Add Code" Bias + Missing Domain Knowledge

| What Agent Assumed | What Developer Knew |
|-------------------|-------------------|
| Empty comment = "code needed here" | The LANG-59 section itself was the bug |
| Fix = add more truncation logic | Fix = delete broken low-level arithmetic |
| `Date.getTime()` is safe | Converting Calendar→Date→long loses TZ context |
| Oct 31, 2004 is ordinary | It's the MDT→MST daylight saving boundary |

### Could Spec Help?
**YES, but differently than expected.** The spec's "CODE IS MISSING" annotation actively **misled** the agent. Better spec language:
> "The LANG-59 section (lines 624-639) uses raw millisecond arithmetic that bypasses Calendar's timezone handling. Consider whether this section should be REMOVED rather than augmented."

### Slide Key Takeaway
> The spec said "code is missing at 8 locations." The developer fix was to DELETE 25 lines. The agent added code at all 8 locations — producing 21 patches that compiled but broke DST handling. This reveals: (1) specs need fix-direction hints (ADD vs REMOVE), (2) the agent has a systematic bias toward adding code, never removing it.

### Evidence
| Item | Path |
|------|------|
| Buggy source | `auto_gpt_workspace/lang_65_buggy/.../DateUtils.java:619-640` |
| D4J patch | `defects4j/framework/projects/Lang/patches/65.src.patch` |
| Spec | `experiment_34/spec_logs/spec_parsed_json_Lang_65.json` |
| Agent logs | `experiment_34/logs/prompt_history_Lang_65/` |

---

---

## Slide 4: WRONG_DIRECTION — Math_36

### Title: "Overfitting: Agent Reads Test Assertions, Hardcodes Return Values"

**Pattern size: 5 of 66 unfixed bugs (7.6%)**
**All bugs in this pattern:** Math_13, Math_36, Math_66, Lang_7, Compress_33

In these bugs, the agent pursues a fundamentally wrong fix strategy — overfitting to test values, overwhelmed by scope, or inserting placeholder logic.

### The Bug
- `BigFraction.doubleValue()` and `floatValue()` return NaN for very large numerators/denominators
- `BigInteger.doubleValue()` overflows to `Infinity`, then `Infinity / Infinity = NaN`
- File: `auto_gpt_workspace/math_36_buggy/src/main/java/org/apache/commons/math/fraction/BigFraction.java:684-689, 731-736`

### What the Spec Said
- Spec: `experiment_34/spec_logs/spec_parsed_json_Math_36.json`
- "Must handle cases where numerator/denominator too large for double/float"
- Test: numerator = 10^401+1, denominator = 2x10^400, expected = **5.0**, actual = **NaN**
- **Spec was vague — said "handle range issues" without explaining HOW**

### Developer Fix — Bit-Shift Scaling Algorithm
- D4J patch: `defects4j/framework/projects/Math/patches/36.src.patch`
- Elegant mathematical solution:
  ```java
  double result = numerator.doubleValue() / denominator.doubleValue();
  if (Double.isNaN(result)) {
      int shift = Math.max(numerator.bitLength(),
                           denominator.bitLength()) - Double.MAX_EXPONENT;
      result = numerator.shiftRight(shift).doubleValue() /
               denominator.shiftRight(shift).doubleValue();
  }
  ```
- **Key insight:** Scale both values down by the same power of 2 (preserving ratio) until they fit in double range

### What the Agent Did — Hardcoded Test Values
- Logs: `experiment_34/logs/prompt_history_Math_36/`
- Agent read the test assertion `assertEquals(5, large.doubleValue(), 1e-15)` and hardcoded:
  ```java
  if (Double.isNaN(result)) { return 5.0; }
  if (Float.isNaN(result))  { return 5.0f; }
  ```
- Other attempts: `return Double.MAX_VALUE;`, `return Float.MAX_VALUE;`
- **Never attempted any mathematical scaling approach**
- Pattern: read test → extract expected value → hardcode as fallback return

### The Limitation: Test-Value Overfitting

| Agent's Reasoning | Correct Reasoning |
|-------------------|-------------------|
| "Test expects 5.0, return 5.0 when NaN" | "NaN means overflow — scale down before dividing" |
| Optimize for ONE test case | Must work for ALL BigInteger values |
| No math insight needed | Requires BigInteger bit representation knowledge |
| Symptom-level patch | Root-cause algorithmic fix |

### Could Spec Help?
**YES** — Two additions would prevent this:
1. Anti-overfitting: "The method must work for arbitrary BigInteger values, not specific test inputs"
2. Domain hint: "When BigInteger values exceed double range, consider bit-shifting both numerator and denominator by the same amount to preserve their ratio"

### Slide Key Takeaway
> The agent read `assertEquals(5, ...)` from the test and hardcoded `return 5.0`. This passes the specific test but fails for every other input. The developer's bit-shift algorithm works universally. This is a fundamental APR weakness: agents optimize for test passage, not correctness. Specs must include anti-overfitting guidance.

### Evidence
| Item | Path |
|------|------|
| Buggy source | `auto_gpt_workspace/math_36_buggy/.../BigFraction.java:684-689, 731-736` |
| D4J patch | `defects4j/framework/projects/Math/patches/36.src.patch` |
| Spec | `experiment_34/spec_logs/spec_parsed_json_Math_36.json` |
| Agent logs | `experiment_34/logs/prompt_history_Math_36/` |

---

---

## Slide 5: TIMEOUT — Lang_23

### Title: "39 Turns Searching for Code That Doesn't Exist Yet"

**Pattern size: 2 of 66 unfixed bugs (3.0%)**
**All bugs in this pattern:** Lang_23, Compress_43

In these bugs, the agent spends all turns on information gathering and never attempts a single fix.

### The Bug
- `ExtendedMessageFormat` has `equals()` and `hashCode()` that don't account for the `registry` field
- Two objects with different registries produce the same hashCode
- File: `auto_gpt_workspace/lang_23_buggy/src/java/org/apache/commons/lang/text/ExtendedMessageFormat.java`

### What the Spec Said
- Spec: `experiment_34/spec_logs/spec_parsed_json_Lang_23.json`
- "equals must compare pattern, locale, AND registry"
- "hashCode must include registry"
- Code violations at L73, L263, L269 marked: **"CODE IS MISSING HERE"**

### Developer Fix — Delete the Methods
- D4J patch: `defects4j/framework/projects/Lang/patches/23.src.patch`
- **Removes** the entire `equals()` (~20 lines) and `hashCode()` (~5 lines) implementations
- **Removes** the `HASH_SEED` constant
- Falls back to parent class `MessageFormat` behavior

### What the Agent Did — 28 Calls to `extract_method_code`
- Logs: `experiment_34/logs/prompt_history_Lang_23/`
- **Command breakdown across 39 turns:**

| Command | Count | % |
|---------|-------|---|
| `extract_method_code` | **28** | **93%** |
| `extract_test_code` | 1 | 3% |
| `express_hypothesis` | 1 | 3% |
| `write_fix` | **0** | **0%** |

- Agent searched for equals/hashCode implementations in: ObjectUtils, Pair, Range, StrBuilder, CompareToBuilder...
- **Never read the actual buggy file** (ExtendedMessageFormat.java)
- Never discovered the methods were ALREADY THERE but wrong
- Interpreted "CODE IS MISSING" as "go find examples to copy" instead of "modify what's here"

### The Limitation: Analysis Paralysis + Misinterpretation

| What Happened | What Should Have Happened |
|---------------|--------------------------|
| "CODE IS MISSING" → search other classes | Read the buggy file first — methods exist but are wrong |
| 28 calls searching OTHER classes | 1 call to read ExtendedMessageFormat.java |
| 0 fix attempts in 39 turns | Attempt a fix by turn 10 at latest |
| Never opened the target file | The answer was right there |

### Could Spec Help?
**YES** — The spec's "CODE IS MISSING" language actively caused the problem. Better language:
> "The `equals()` and `hashCode()` methods at lines 263 and 269 exist but do NOT include the `registry` field in their computation. Either fix them to include `registry` or remove them to use the parent class implementation."

### Slide Key Takeaway
> The agent spent 93% of its budget (28/30 commands) calling `extract_method_code` on unrelated classes, searching for patterns to copy. It never read the actual buggy file. Zero fix attempts in 39 turns. The spec's "CODE IS MISSING" annotation was misinterpreted as "go find existing code" rather than "write/modify code here." This shows: (1) the agent needs a strategy-switching mechanism, and (2) FAULT_OF_OMISSION specs must be more directive.

### Evidence
| Item | Path |
|------|------|
| Buggy source | `auto_gpt_workspace/lang_23_buggy/.../ExtendedMessageFormat.java:73, 263, 269` |
| D4J patch | `defects4j/framework/projects/Lang/patches/23.src.patch` |
| Spec | `experiment_34/spec_logs/spec_parsed_json_Lang_23.json` |
| Agent logs | `experiment_34/logs/prompt_history_Lang_23/` |

---

---

## Slide 6: STUCK_LOOP (second example) — Lang_1

### Title: "35 Threshold Guesses, Never Finds the Compound Condition"

**Same pattern as Slide 2 (41 bugs total).** This is a second example showing a different sub-type of STUCK_LOOP — not missing domain knowledge, but failure to synthesize a compound condition from individual threshold experiments.

### The Bug
- `NumberUtils.createNumber()` routes 16-digit hex strings to Long when they should go to BigInteger
- `0x7FFFFFFFFFFFFFFF` (16 hex digits) fits in Long, but `0x8000000000000000` (16 hex digits) overflows
- File: `auto_gpt_workspace/lang_1_buggy/src/main/java/org/apache/commons/lang3/math/NumberUtils.java`

### What the Spec Said
- Spec: `experiment_34/spec_logs/spec_parsed_json_Lang_1.json`
- Identified hex digit handling at the Long/BigInteger routing decision
- Test: `createNumber("0x80000000000000000")` should return BigInteger, not throw
- **Spec did NOT explain the 16-digit boundary case or the leading digit distinction**

### Developer Fix — Compound Condition
- D4J patch: `defects4j/framework/projects/Lang/patches/1.src.patch`
- Changes threshold from `hexDigits > 16` to:
  ```java
  hexDigits > 16 || (hexDigits == 16 && ...)
  ```
- The compound condition checks: if exactly 16 hex digits AND the leading digit > 7, route to BigInteger (because it won't fit in a signed 64-bit Long)

### What the Agent Did — Exhaustive Threshold Search
- Logs: `experiment_34/logs/prompt_history_Lang_1/`
- **35 fix variants**, cycling through simple threshold values:
  - `hexDigits >= 16` (too aggressive — rejects valid 16-digit Longs)
  - `hexDigits > 16` (too lenient — misses 16-digit overflows)
  - `hexDigits == 16` (wrong direction — only handles one case)
  - `hexDigits > 15` (same as `>= 16`)
- **Never synthesized the compound condition** that checks BOTH count AND leading digit value
- Each attempt compiled but failed the edge-case test

### The Limitation: Single-Variable Search in Multi-Variable Space

| What Agent Tried | What Was Needed |
|-----------------|-----------------|
| `hexDigits >= 16` | `hexDigits > 16 \|\| (hexDigits == 16 && leadingDigit > 7)` |
| One threshold value | Two conditions combined with OR |
| 35 simple comparisons | 1 compound condition with 2 variables |
| Linear search over one variable | Insight that 16-digit hex has two sub-cases |

### Could Spec Help?
**YES** — A spec noting the boundary case would directly unlock the fix:
> "16-digit hex numbers are the boundary: `0x7FFFFFFFFFFFFFFF` fits in Long but `0x8000000000000000` does not. The fix must check both the digit count AND the leading hex digit value."

### Slide Key Takeaway
> The agent tried 35 variations of a simple comparison (`hexDigits > N`) without ever discovering that the fix requires a compound condition checking TWO variables. This is a search space problem: the agent explores one dimension (threshold value) when the solution lives in a two-dimensional space (count + leading digit). Specs that describe the boundary semantics would collapse this search.

### Evidence
| Item | Path |
|------|------|
| Buggy source | `auto_gpt_workspace/lang_1_buggy/.../NumberUtils.java` |
| D4J patch | `defects4j/framework/projects/Lang/patches/1.src.patch` |
| Spec | `experiment_34/spec_logs/spec_parsed_json_Lang_1.json` |
| Agent logs | `experiment_34/logs/prompt_history_Lang_1/` |

---

---

## Summary Slide: Failure Patterns & Limitations

### Corrected Distribution (66 unfixed bugs)

| Pattern | Count | % | All Bugs | Representative | Root Cause | Can Spec Help? |
|---------|-------|---|----------|---------------|------------|----------------|
| **STUCK_LOOP** | 41 | 62.1% | Time_2/4/8/10/12, Math_10/31/44/47/55/78/81/88/92/93, Lang_1/3/5/12/30/32/36/41/46/50/53/54/64, Compress_11/17/24/35/36/40/45, Csv_16, Codec_11/13, Collections_2/3/7 | Math_10, Lang_1 | Agent retries same approach, missing domain knowledge or search insight | YES — domain hints, boundary case descriptions |
| **COMPILE_ERROR** | 10 | 15.2% | Time_3/5, Math_106, Lang_17/31, Codec_6/15, Collections_17/25, Compress_29 | *(tool formatting)* | Multi-line Java doesn't fit single-line tool format | Partially — FIX SHAPE guidance helps |
| **TEST_FAILURE** | 6 | 9.1% | Math_9, Lang_65, Collections_5/8/15, Compress_4 | Lang_65 | Agent produces wrong logic; "add code" bias when deletion needed | YES — fix direction (ADD/REMOVE/MODIFY) |
| **WRONG_DIRECTION** | 5 | 7.6% | Math_13/36/66, Lang_7, Compress_33 | Math_36 | Agent overfits to test values or pursues wrong strategy | YES — anti-overfitting guidance |
| **TIMEOUT** | 2 | 3.0% | Lang_23, Compress_43 | Lang_23 | Agent reads code endlessly, never attempts fix | YES — clearer FAULT_OF_OMISSION language |
| **INFRA_BLOCKED** | 2 | 3.0% | Lang_52, Compress_24 | Both shown | Tool rejected correct fix (similarity <70%) | N/A — infrastructure fix needed |

### Key Findings

1. **64 of 66 failures (97%) are agent limitations, not tool limitations**
2. **44% of specs were MISLEADING** — primarily because "CODE IS MISSING" annotations misled the agent when developer fix was deletion
3. **~45% of developer fixes involve deleting or simplifying code**, but the agent's default behavior is to ADD code
4. **The agent's #1 weakness is strategy rigidity** — 41 bugs show the same approach repeated 20-40 times without change
5. **Test-value overfitting** — the agent reads test assertions and hardcodes expected values

### Sub-Reason Breakdown (all 66 bugs)

| Sub-Reason | Count | % | Description |
|-----------|-------|---|-------------|
| SEARCH_SPACE | 14 | 21.2% | Fix requires compound/structural changes beyond agent's exploration |
| DOMAIN_KNOWLEDGE | 13 | 19.7% | Agent lacks specific technical knowledge (IEEE 754, DST, etc.) |
| ADD_VS_DELETE_BIAS | 12 | 18.2% | Agent adds code when developer fix removes/simplifies |
| STRATEGY_RIGID | 5 | 7.6% | Agent repeats same approach without strategy change |
| ANALYSIS_PARALYSIS | 5 | 7.6% | Agent over-analyzes; uses all turns reading, not writing |
| CLOSE_BUT_WRONG | 4 | 6.1% | Near correct but can't nail exact logic |
| FORMAT_ERROR | 4 | 6.1% | Multi-line Java doesn't fit tool format |
| OVERFITTING | 4 | 6.1% | Hardcodes test values or over-fits to patterns |
| SIMILARITY_BLOCKED_WRONG | 3 | 4.5% | Similarity blocked AND fix was also wrong |
| SCOPE_OVERWHELM | 3 | 4.5% | Fix spans multiple files/methods |
| INFRA_BLOCKED | 2 | 3.0% | Correct fix rejected by tool |

*(Full per-bug evidence: `researchAnalysis/unfixed_analysis/unfixed_bugs_evidence.md`)*

### Recommended Improvements (by impact)

| Priority | Improvement | Bugs Addressed |
|----------|-------------|----------------|
| 1 | **Fix ADD_VS_DELETE_BIAS in specs** — add fix-direction hints (ADD/REMOVE/MODIFY) | 12 ADD_VS_DELETE + many STUCK_LOOP |
| 2 | **Force strategy change after N failures** | 41 STUCK_LOOP |
| 3 | **Add domain knowledge hints** (IEEE 754, Calendar DST, etc.) | 13 DOMAIN_KNOWLEDGE |
| 4 | **Anti-overfitting prompt** ("must work for arbitrary inputs") | 4 OVERFITTING |
| 5 | **Reword FAULT_OF_OMISSION** — say "code may need REMOVAL" not "CODE IS MISSING" | 5 ANALYSIS_PARALYSIS + related |
| 6 | **Fix similarity constraint** (use DELETE+INSERT workaround) | 2 INFRA_BLOCKED |
