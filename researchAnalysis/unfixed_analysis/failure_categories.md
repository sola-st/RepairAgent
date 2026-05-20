# Unfixed Bug Failure Categories — E34 Experiment

**Total unfixed bugs:** 66 out of 98 in pool (67.3%)

---

## Category Definitions

| Category | Description |
|----------|-------------|
| STUCK_LOOP | Agent retries minor variations of the same fix repeatedly without changing strategy |
| TEST_FAILURE | Patches compile but tests keep failing — agent is close but can't find correct logic |
| COMPILE_ERROR | Agent produces patches that don't compile (syntax errors, missing APIs, brace mismatch) |
| INFRASTRUCTURE | Tool constraints (70% similarity threshold) block valid fixes |
| WRONG_DIRECTION | Agent pursues fundamentally wrong fix strategy |
| TIMEOUT | Agent spends all turns on information gathering, never attempts fixes |

---

## Aggregated Results

### Primary Category Distribution

| Primary Category | Count | Percentage | Bugs |
|-----------------|-------|------------|------|
| STUCK_LOOP | 43 | 65.2% | Time_2, Time_4, Time_8, Time_10, Time_12, Math_10, Math_31, Math_44, Math_47, Math_55, Math_78, Math_81, Math_88, Math_92, Math_93, Lang_1, Lang_3, Lang_5, Lang_12, Lang_30, Lang_32, Lang_36, Lang_41, Lang_46, Lang_50, Lang_52, Lang_53, Lang_54, Lang_64, Compress_11, Compress_17, Compress_24, Compress_35, Compress_36, Compress_40, Compress_45, Csv_16, Codec_11, Codec_13, Collections_2, Collections_3, Collections_7 |
| COMPILE_ERROR | 10 | 15.2% | Time_3, Time_5, Math_106, Lang_17, Lang_31, Codec_6, Codec_15, Collections_17, Collections_25, Compress_29 |
| TEST_FAILURE | 7 | 10.6% | Math_9, Lang_65, Collections_5, Collections_8, Collections_15, Compress_4 |
| WRONG_DIRECTION | 5 | 7.6% | Math_13, Math_36, Math_66, Lang_7, Compress_33 |
| TIMEOUT | 2 | 3.0% | Lang_23, Compress_43 |

### Contributing Factor: INFRASTRUCTURE (Similarity Constraint)

The write_fix tool's 70% similarity threshold was a significant contributing blocker in **12 bugs** (18.2%):
- Lang_52, Lang_53, Lang_54, Lang_12
- Math_92, Math_93
- Compress_11, Compress_17, Compress_24
- Collections_2, Collections_3, Collections_7

In these cases, the agent correctly diagnosed the bug and proposed a valid fix direction, but the tool rejected the modification because the new code was less than 70% similar to the original line.

### Spec Effectiveness for Unfixed Bugs

| Spec Quality | Count | Percentage |
|-------------|-------|------------|
| Generated and helpful (correct file/method) | 48 | 72.7% |
| Generated but insufficient | 12 | 18.2% |
| Generated but misleading | 6 | 9.1% |

**Key finding:** Specs correctly located the buggy code in ~73% of unfixed bugs. The bottleneck is NOT diagnosis — it's the fix generation and application phase.

---

## Case Studies by Category

### Case Study Selection Criteria
For each failure category, we select 3 representative bugs that best illustrate the root cause, choosing bugs where the agent's behavior is most clearly documented and the failure is most instructive.

### STUCK_LOOP Case Studies

#### Case 1: Collections_3 — Perfect diagnosis, tool blocks fix
- **Bug:** `CollectionUtils.removeAll()` calls `ListUtils.retainAll()` (wrong method)
- **Developer fix:** Change `retainAll` to `removeAll` on line 1121
- **Agent behavior:** Correctly identified the wrong method call. Attempted to replace line 1121 but ALL modifications rejected (38% similarity — `retainAll` vs `removeAll` changes too many characters). Cycled 33 times between the same two fix variants.
- **Log path:** `experiment_34/logs/prompt_history_Collections_3/`
- **Why spec couldn't help more:** Spec correctly diagnosed the issue. The failure is purely in the tool's similarity constraint — this is an infrastructure limitation, not a spec quality issue.

#### Case 2: Math_10 — Misses edge case despite correct area
- **Bug:** `DSCompiler.atan2()` doesn't handle signed-zero (`-0.0` vs `+0.0`)
- **Developer fix:** Add special cases for `y=+0/-0` combined with `x=+0/-0` and `x>0/x<0`
- **Agent behavior:** Correctly targeted `atan2` and inserted if-checks, but every variant used `y == 0.0` (which matches both +0.0 and -0.0 in Java) instead of `Double.doubleToLongBits(y)` for signed-zero detection. 27 fixes attempted, all producing wrong results for `-0.0` inputs.
- **Log path:** `experiment_34/logs/prompt_history_Math_10/`
- **Why spec couldn't help more:** Spec identified `atan2` but didn't mention the IEEE 754 signed-zero distinction. A spec enriched with "Java's `==` operator treats +0.0 and -0.0 as equal; use `Double.doubleToLongBits()` for signed-zero comparison" would have helped.

#### Case 3: Lang_1 — Exhaustive but wrong threshold search
- **Bug:** `NumberUtils.createNumber()` hex digit boundary for Long vs BigInteger
- **Developer fix:** Change threshold from `hexDigits > 16` to `hexDigits > 16 || (hexDigits == 16 && ...)` with additional conditions
- **Agent behavior:** Tried 35 fix variants cycling through `hexDigits >= 16`, `hexDigits > 16`, `hexDigits == 16` — never found the correct compound condition that requires checking the leading hex digit value. All compiled but failed the edge-case test.
- **Log path:** `experiment_34/logs/prompt_history_Lang_1/`
- **Why spec couldn't help more:** Spec identified hex digit handling but didn't specify that `0x7FFFFFFFFFFFFFFF` (16 digits, fits Long) vs `0x8000000000000000` (16 digits, overflows Long) is the key distinction.

### COMPILE_ERROR Case Studies

#### Case 1: Math_47 — Syntax errors in complex code
- **Bug:** `Complex.divide()` missing NaN/Infinity handling
- **Developer fix:** Add `isNaN`/`isInfinite` checks with proper returns
- **Agent behavior:** Understood the fix needed (NaN/Inf checks) but produced 101 syntax errors across 34 attempts. The agent put multiple Java statements on single lines using `\n` literal strings, and the tool treated `\n` as literal text rather than newlines, producing unparseable Java.
- **Log path:** `experiment_34/logs/prompt_history_Math_47/`
- **Why spec couldn't help more:** Spec was correct. The failure is in the agent's code formatting, not in understanding what to fix.

#### Case 2: Collections_25 — Wrong Java version API
- **Bug:** `IteratorUtils.collatedIterator()` null comparator handling
- **Developer fix:** Add null check and use natural ordering
- **Agent behavior:** Correctly identified the fix but used `Comparator.naturalOrder()` (Java 8+) in a project targeting Java 6. Compilation failed because the API doesn't exist in the target runtime.
- **Log path:** `experiment_34/logs/prompt_history_Collections_25/`
- **Why spec couldn't help more:** Spec didn't mention the target Java version. Adding "target Java version: 1.6" to the spec would have prevented this.

#### Case 3: Lang_17 — Surrogate pair formatting issues
- **Bug:** `CharSequenceTranslator.translate()` doesn't handle surrogate pairs correctly
- **Developer fix:** Use `Character.codePointAt()` and advance by `Character.charCount()`
- **Agent behavior:** Understood surrogate pair handling conceptually but 62 of 33 fix attempts had syntax errors from embedded newline characters in insertion strings. The tool's single-line insertion format clashes with multi-line code changes.
- **Log path:** `experiment_34/logs/prompt_history_Lang_17/`
- **Why spec couldn't help more:** Correct diagnosis. Failure is in expressing multi-line Java within the tool's format constraints.

### TEST_FAILURE Case Studies

#### Case 1: Collections_8 — Nearly correct fix
- **Bug:** `UnboundedFifoBuffer` serialization (writeObject/readObject)
- **Developer fix:** Fix buffer size initialization during deserialization
- **Agent behavior:** Got within 1 failing test of success — one variant produced only 1 failure (expected buffer size 1, got 0). The agent correctly targeted the serialization methods but couldn't find the exact right buffer size initialization formula.
- **Log path:** `experiment_34/logs/prompt_history_Collections_8/`
- **Why spec couldn't help more:** Spec pointed to correct area. The fix required understanding the specific relationship between buffer capacity and element count during deserialization — a very specific implementation detail the spec couldn't capture.

#### Case 2: Lang_65 — Correct area, wrong rounding logic
- **Bug:** `DateUtils.truncate/round()` calendar field rounding
- **Developer fix:** Fix the truncation offset calculation for calendar fields
- **Agent behavior:** 21 fixes all compiled and ran but produced wrong results. The agent tried various offset values and rounding conditions but never found the correct formula. The fix involves specific calendar field arithmetic that requires deep understanding of Java's Calendar API.
- **Log path:** `experiment_34/logs/prompt_history_Lang_65/`
- **Why spec couldn't help more:** Spec identified the rounding issue but the fix requires knowing that `Calendar.MILLISECOND` values need specific offset handling — domain knowledge the spec didn't encode.

#### Case 3: Collections_15 — Index adjustment bug
- **Bug:** `SetUniqueList.set()` index handling after removal
- **Developer fix:** Adjust index position after removing duplicate
- **Agent behavior:** Correctly targeted `set()` method and the remove/add sequence. Patches compiled but produced `IndexOutOfBoundsException` — after removing the old element, the index `pos` becomes invalid if `pos > index`. The agent didn't account for the index shift.
- **Log path:** `experiment_34/logs/prompt_history_Collections_15/`
- **Why spec couldn't help more:** Spec identified the method. The fix requires understanding that `remove(pos)` shifts all subsequent elements down by 1, so `index` needs adjustment when `pos < index`. A spec noting "after removal, adjust target index if removed position was before it" would have helped.

### WRONG_DIRECTION Case Studies

#### Case 1: Math_36 — Hardcoded return values
- **Bug:** `BigFraction.doubleValue()` overflow handling
- **Developer fix:** Use proper double arithmetic for large numerator/denominator
- **Agent behavior:** Inserted checks returning hardcoded `5.0` and `5.0f` for specific conditions — clearly wrong. The agent saw a specific test expecting `5.0` and overfitted to that single test value rather than fixing the general computation.
- **Log path:** `experiment_34/logs/prompt_history_Math_36/`
- **Why spec couldn't help more:** Spec should have stated "the method must work for arbitrary BigInteger values, not specific test cases." Anti-overfitting guidance in the spec could prevent this.

#### Case 2: Math_66 — Overwhelmed by too many buggy lines
- **Bug:** `BrentOptimizer` optimization logic
- **Developer fix:** Multiple changes across the optimization algorithm
- **Agent behavior:** The spec identified 15+ buggy lines. The agent tried to fix all of them simultaneously with massive insertions (setMaxEvaluations, setAbsoluteAccuracy, localMin calls) that were fundamentally wrong. The scope overwhelmed the agent.
- **Log path:** `experiment_34/logs/prompt_history_Math_66/`
- **Why spec couldn't help more:** Too many buggy lines in the spec overwhelmed the agent. A spec that prioritized the 2-3 most critical lines would have been more effective.

#### Case 3: Compress_33 — Placeholder logic left in
- **Bug:** `CompressorStreamFactory` missing deflate detection
- **Developer fix:** Add proper deflate stream signature matching
- **Agent behavior:** Created a `matches()` method returning `return true` as a "placeholder" that was never fixed. This caused all streams to be identified as deflate, breaking other format detection.
- **Log path:** `experiment_34/logs/prompt_history_Compress_33/`
- **Why spec couldn't help more:** Spec correctly identified the missing detection. Agent needed the actual deflate signature bytes (0x78 followed by specific values) which the spec didn't provide.

### TIMEOUT Case Studies (2 bugs — both included)

#### Case 1: Lang_23 — Analysis paralysis
- **Bug:** `ExtendedMessageFormat.hashCode()` missing override
- **Agent behavior:** Spent all 39 turns searching for equals/hashCode methods across the codebase without ever attempting a fix. The agent kept reading more and more code trying to understand the full inheritance hierarchy.
- **Log path:** `experiment_34/logs/prompt_history_Lang_23/`

#### Case 2: Compress_43 — Insufficient fix attempts
- **Bug:** `ZipArchiveOutputStream.usesDataDescriptor()` logic error
- **Agent behavior:** Only 4 fix attempts in 39 turns. Spent most time reading ZipArchiveEntry source code trying to understand the data descriptor flag semantics.
- **Log path:** `experiment_34/logs/prompt_history_Compress_43/`

---

## Cross-Category Observations

### 1. The 70% Similarity Constraint Problem
In 12/66 unfixed bugs (18.2%), the agent correctly diagnosed the bug and knew the fix, but the write_fix tool's similarity threshold prevented applying it. This is the single most impactful infrastructure improvement opportunity.

### 2. Spec Quality vs Fix Generation Gap
Specs correctly located the buggy code in ~73% of unfixed bugs. The primary bottleneck is NOT diagnosis — it's translating the diagnosis into syntactically valid, semantically correct code within the tool's constraints.

### 3. Multi-Line Fix Format Issues
Many compile errors stem from the agent trying to express multi-line Java code within the tool's insertion format. Literal `\n` characters, brace mismatches, and statement-on-one-line issues account for a large portion of syntax errors.

### 4. Turn Budget Exhaustion
All but 2 bugs (Codec_6 with 16 turns, Lang_31 with 19) consumed the full 39-turn budget. The turn limit is not the primary blocker — even with more turns, the STUCK_LOOP pattern suggests the agent would continue cycling without strategy changes.
