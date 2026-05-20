# Unfixed Bugs — Root Cause Analysis (66 bugs)

The original categories (STUCK_LOOP, COMPILE_ERROR, TEST_FAILURE) describe **symptoms**. This document reclassifies all 66 bugs by the actual **reason** the fix failed.

---

## New Taxonomy

| Category | Count | % | Meaning |
|----------|-------|---|---------|
| **A. SPEC_MISLED_AGENT** | 24 | 36.4% | Spec was wrong about fix direction — agent followed spec into dead end |
| **B1. Agent lacks domain knowledge** | 4 | 6.1% | Spec correct, agent understands area, but lacks IEEE 754 / numerical algorithm / etc. knowledge |
| **B2a. Agent's own add/fix bias** | 11 | 16.7% | Spec correct/neutral (NOT misleading), but agent defaults to adding code instead of deleting/simplifying |
| **B2b. Can't compose multi-step logic** | 5 | 7.6% | Agent understands each piece but can't coordinate two interacting changes |
| **B2c. Understanding-to-code gap** | 3 | 4.5% | Agent can articulate the problem but can't produce the exact code edit |
| **C. FIX_BEYOND_TOOL_SCOPE** | 12 | 18.2% | Fix requires multi-file/multi-method/structural refactoring beyond single-point edit |
| **D. AGENT_OVERFITS_TO_TESTS** | 3 | 4.5% | Agent reads test values, hardcodes them instead of fixing root cause |
| **E. CORRECT_FIX_TOOL_BLOCKED** | 2 | 3.0% | Agent had correct fix, tool's similarity constraint rejected it |
| **F. AGENT_NEVER_ATTEMPTED** | 2 | 3.0% | Agent spent all turns reading code, never tried a fix |

---

## A. SPEC_MISLED_AGENT (24 bugs — 36.4%)

The spec pointed the agent in the wrong direction. Most common pattern: spec says "CODE IS MISSING" or "add check" when developer fix is to DELETE code. Agent follows spec, adds code, fails.

**Could better specs fix these?** YES — this is the highest-impact improvement target.

| Bug | Spec Said | Developer Actually Did | Agent Did |
|-----|-----------|----------------------|-----------|
| Time_4 | Constructor param ordering issue | Reorder constructor call to use validated public constructor | Followed spec's wrong param direction |
| Time_10 | Constant usage is the issue | Remove unsafe constant, use 0L for invalid date edge case | Kept constant, missed Feb 29 edge case |
| Math_55 | isZero flag is reliable for checking | Replace cached isZero with direct component comparison | Trusted spec's isZero pointer, patches wrong |
| Math_81 | Vague about OR vs AND relationship | Change OR→AND and fix loop range 4*n0-16→4*n0-11 | Couldn't determine correct logic from vague spec |
| Math_88 | Multiple approaches without clarifying | Remove HashSet, use tableau column inspection | Confused by spec's ambiguity, couldn't commit |
| Math_93 | Rounding errors (but not algorithmic fix) | Remove overflow check entirely, delegate to Math.round() | Stuck trying to fix precision, not simplify |
| Math_9 | Suggested wrong type of transformation | Revert to direct initialization with zero-subtracted direction | Tried setter approaches per spec |
| Lang_1 | Overspecified hex digit checks | Change `> 16` to compound condition (count + leading digit) | 35 simple threshold variants, never compound |
| Lang_3 | "Code is missing" | Remove numDecimal guard conditions (deletion) | Added code per spec |
| Lang_5 | "Missing locale parsing" | Remove entire underscore-prefix block (30 lines) | Tried adding parsing per spec |
| Lang_12 | Flagged empty array check as violation | Remove the flagged check entirely | Tried to fix flagged code, not delete it |
| Lang_32 | "Registry not cleared post-use" | Refactor ThreadLocal to anonymous class with initialValue() | Focused on registry clearing per spec |
| Lang_36 | Array notation handling violation | Remove all array encoding logic entirely | Tried to fix array notation per spec |
| Lang_46 | "/" should not be escaped | Remove both escape cases (deletion) | Added alternative handling instead of deleting |
| Lang_50 | !Character.isDigit(lastChar) is the issue | Remove '.' from lastChar condition (subtle change) | Focused on digit checking per spec |
| Lang_64 | Add null/type checks | Remove complex cross-classloader comparison (simplification) | Added checks per spec instead of removing |
| Lang_65 | 8 locations: "CODE IS MISSING" | Delete entire 25-line LANG-59 section | 21 attempts adding code at all 8 locations |
| Compress_11 | "Exception handling missing" | Remove guard `if (signatureLength >= 512)` | Added exception code instead of removing guard |
| Compress_35 | "Code is missing" | Replace parseOctal() with manual parsing loop | Added exception handling instead of refactoring |
| Compress_33 | Deflate detection wrong approach | Delete matches() method entirely | 36 detection reimplementations |
| Codec_15 | Loop logic issues (wrong direction) | Invert from backward to forward peek-ahead | Variant loops in same backward direction |
| Collections_3 | Initialization/instance variable logic | Remove instance variable, revert to static field | Trapped in init fixes per spec |
| Collections_5 | Indexed insertion necessary | Remove index-tracking, use unindexed add() | Over-engineered indexing per spec |
| Collections_15 | Condition inversion needed (but vague) | Invert set() condition + specific deletion order | Got deletion order wrong following spec hints |

**Pattern:** 20 of 24 (83%) involve the spec saying "add/fix code" when the developer fix was "delete/simplify." The FAULT_OF_OMISSION annotation is the #1 source of misleading specs.

---

## B. SPEC_CORRECT_AGENT_NOT_CAPABLE (23 bugs — 34.8%)

Spec correctly identified the buggy area. Agent understood the bug location. But agent couldn't produce the correct fix — either lacking domain knowledge or unable to synthesize the right logic.

### B1. Lacks Domain Knowledge (4 bugs)

Agent understood WHERE the bug is but not HOW to fix it — requires specialized technical knowledge.

| Bug | What Agent Needed to Know | What Agent Used Instead |
|-----|--------------------------|------------------------|
| Math_10 | `Double.doubleToLongBits()` distinguishes +0.0/-0.0 | `y == 0.0` (matches both in Java) |
| Math_31 | Lentz modification for continued fraction scaling | Simple overflow checks (insufficient) |
| Math_47 | Cross-product preconditioning formula for v3 | Understood concept, couldn't derive formula |
| Math_92 | Log-space evaluation: `binomialCoefficientLog` + `Math.floor` | Identified precision issue, couldn't reformulate |

**Could better specs fix these?** YES — a single sentence of domain knowledge would unlock each fix.

### B2. Understands Bug, Produces Wrong Fix (19 bugs)

Agent correctly localized the bug. Spec was correct or neutral (NOT misleading). Agent attempted fixes in the right area but couldn't find the correct logic. There are **3 distinct sub-patterns**:

#### B2a. Agent's Own "Add/Fix" Bias — spec didn't mislead, but agent defaults to adding code (11 bugs)

Unlike Category A (where spec actively said "add code"), here the spec was correct or neutral. The agent's **own inherent tendency** is to add/fix code rather than delete/simplify. This is a core LLM weakness: "fixing" feels more natural than "removing."

| Bug | Spec Said | Developer Fix | Agent's Bias |
|-----|-----------|--------------|-------------|
| Time_3 | HELPFUL — identified guard removal | Remove null-check guards (2 deletions per method) | Added DST complexity instead of simply deleting |
| Time_12 | HELPFUL — missing era handling | Remove broken BC arithmetic + add era extraction | Added era handling but didn't remove the broken code |
| Lang_30 | NEUTRAL | Remove surrogate pair handling entirely | Tried to fix the surrogate code instead of removing |
| Lang_31 | HELPFUL — "removal needed" | Delete nested conditional | Added supplementary char logic on top |
| Math_13 | NEUTRAL | Delete DiagonalMatrix optimization branch | Kept trying to fix the branch instead of deleting |
| Compress_17 | NEUTRAL | Simplify while→if (reduce complexity) | Tried fixing loop conditions, never simplified |
| Compress_36 | HELPFUL — overflow is problematic | Delete overflow handling (simplify) | Over-engineered more overflow logic |
| Compress_40 | NEUTRAL | Remove else block, call unconditionally | Added code instead of removing else |
| Compress_29 | HELPFUL — encoding issues | Remove encoding branches entirely | Added MORE encoding support |
| Codec_6 | NEUTRAL | Remove while-loop wrapper, return directly | Confused — added control flow instead of simplifying |
| Collections_2 | HELPFUL — retainAll→removeAll | Change one method name | Over-complicated with conditional logic |

**Key insight:** The agent has a systematic "add code" bias **independent of the spec**. Even when the spec doesn't say "add," the agent defaults to adding rather than deleting. This is a deeper problem than misleading specs — it's an inherent LLM behavior pattern.

**Could better specs fix these?** PARTIALLY — explicit "DELETE lines X-Y" or "SIMPLIFY by removing" direction would override the agent's default bias. But unlike Category A, the spec wasn't the cause here.

#### B2b. Can't Compose Multi-Step Logic (5 bugs)

Agent understands each individual piece but can't combine two or more changes into a coherent fix. The fix requires coordinating changes that interact — e.g., adjusting a calculation AND a validation check simultaneously.

| Bug | What Agent Understood | What It Couldn't Compose |
|-----|----------------------|--------------------------|
| Time_2 | Field ordering is wrong | Checking isSupported() flag AND adjusting range duration comparison together |
| Time_8 | Sign validation is missing | Integrating the exception check WITH the minute offset calculation for negative hours |
| Math_44 | resetOccurred flag is premature | Removing flag reset AND selectively keeping/deleting stepAccepted calls in different contexts |
| Math_78 | Bracketing needs sign-change detection | Epsilon-based adjustment loop WITH bounded iteration count (got infinite loops) |
| Collections_8 | Serialization write/read mismatch | Changing write protocol (size only) AND read protocol (allocate size+1) in tandem |

**Key insight:** Agent can fix single-variable problems but struggles when the fix requires coordinating two interacting changes. Each change in isolation makes sense, but they must be applied together to produce correct behavior.

**Could better specs fix these?** YES — if the spec explicitly described both changes and their interaction: "Change X at line A AND correspondingly change Y at line B because they form a protocol pair."

#### B2c. Understanding-to-Code Translation Gap (3 bugs)

Agent can articulate what's wrong (in its hypothesis) but cannot translate that understanding into the specific code edit. The conceptual understanding exists but the code synthesis fails.

| Bug | Agent's Correct Understanding | What It Couldn't Produce |
|-----|-------------------------------|--------------------------|
| Lang_53 | "variant without country should be allowed (fr__POSIX)" | The specific character-check removal (`!= '3'`) that implements this rule |
| Lang_54 | "underscore variant parsing is wrong" | The exact structural simplification of the parsing logic |
| Collections_17 | "EqualPredicate needs a non-null equator" | `new DefaultEquator()` instantiation instead of null-check guard |

**Key insight:** These are cases where the agent "knows the answer" conceptually but can't bridge from understanding to the exact Java code edit. The gap is in code generation precision, not comprehension.

**Could better specs fix these?** YES — if the spec included the specific code pattern: "Replace null with `new DefaultEquator()`" rather than just describing the problem.

---

## C. FIX_BEYOND_TOOL_SCOPE (12 bugs — 18.2%)

These fixes require multi-file refactoring, class deletion, 15+ line structural changes, or cross-method coordination that is beyond the write_fix tool's single-point edit model.

| Bug | Fix Scope | Developer Fix Description |
|-----|-----------|-------------------------|
| Lang_41 | Remove parameter across 3+ method signatures | Remove escapeForwardSlash parameter from method chain |
| Lang_17 | 15+ interdependent line changes | Refactor translate() with codePointCount + restructure branching |
| Time_5 | Multi-point simplification | Remove field-support checks, replace with modular arithmetic |
| Math_106 | Delete 4 duplicate validation blocks | Remove minus-sign checks from numerator + denominator parsers |
| Math_66 | 33 interrelated changes across methods | Major BrentOptimizer refactor: constructor, optimize, loop counter |
| Compress_4 | Multi-class method redistribution | Add finish() to 3 subclass close() methods + remove from performer |
| Compress_45 | Field→anonymous class refactoring | Remove field, create anonymous class inside iterator() |
| Compress_43 | Multi-site parameter removal | Remove phased param from method + update all call sites |
| Csv_16 | Same pattern as Compress_45 | Remove field + convert to anonymous inner class |
| Codec_11 | Delete 6 methods + change return types + rewrite loops | Massive multi-method quoted-printable encoding refactor |
| Codec_13 | Delete entire utility class | Delete CharSequenceUtils.java, change all callers |
| Collections_7 | Delete overrides + change super→this across class | Remove put()/remove() overrides, fix inheritance pattern |

**Could better specs fix these?** NO — this is a fundamental tool/agent capability limitation. The agent can only make single-point edits. These bugs need a more capable repair infrastructure (multi-hunk patches, file deletion).

---

## D. AGENT_OVERFITS_TO_TESTS (3 bugs — 4.5%)

Agent reads test assertions and hardcodes expected values or over-applies defensive patterns from test structure.

| Bug | Test Value Agent Saw | What Agent Did | Developer Fix |
|-----|---------------------|---------------|--------------|
| Math_36 | `assertEquals(5, large.doubleValue())` | `if (isNaN) return 5.0;` | Bit-shift scaling algorithm preserving ratio |
| Lang_7 | BigDecimal exception for "--" prefix | Over-fit to exception pattern | Simple null-return for "--" prefix |
| Collections_25 | Null comparator test cases | Over-fit to defensive null-handling | Remove null-check, pass comparator directly |

**Could better specs fix these?** YES — anti-overfitting instruction: "The fix must work for arbitrary inputs, not just test values."

---

## E. CORRECT_FIX_TOOL_BLOCKED (2 bugs — 3.0%)

Agent produced the correct fix. The tool's 70% similarity constraint rejected it.

| Bug | Fix Match | Similarity Score | Why Blocked |
|-----|-----------|-----------------|-------------|
| Lang_52 | EXACT — identical to developer | 45% | `case '/':` line too different from `default:` |
| Compress_24 | SEM. EQUIVALENT — same restructure | 20-47% | 7 modified lines all below threshold |

**Could better specs fix these?** N/A — this is a tool infrastructure issue, not a spec issue. Fix: use DELETE+INSERT instead of MODIFY.

---

## F. AGENT_NEVER_ATTEMPTED (2 bugs — 3.0%)

Agent spent entire turn budget reading/analyzing code and never attempted a fix.

| Bug | Turns | Fix Attempts | What Agent Did Instead |
|-----|-------|-------------|----------------------|
| Lang_23 | 39 | 0 | 28 calls to extract_method_code on OTHER classes; never opened buggy file |
| Compress_43 | ~39 | 4 | Mostly reading; timeout from cross-site coordination complexity |

**Could better specs fix these?** PARTIALLY — clearer spec language ("the equals/hashCode methods EXIST but are wrong") would prevent the "go search for code" misinterpretation.

---

## Summary: What Is Fixable?

| Root Cause | Count | Can Spec v2 Fix? | Expected Impact |
|-----------|-------|-------------------|-----------------|
| **A. Spec misled agent** | 24 | **YES** — fix FAULT_OF_OMISSION, add fix-direction hints | Could recover 10-15 bugs |
| **B1. Knowledge gap** | 4 | **YES** — add domain knowledge hints to spec | Could recover 2-3 bugs |
| **B2a. Agent's add/fix bias** | 11 | **PARTIALLY** — explicit "DELETE" direction helps | Could recover 3-5 bugs |
| **B2b. Can't compose logic** | 5 | **YES** — describe both changes + their interaction | Could recover 2-3 bugs |
| **B2c. Understanding→code gap** | 3 | **YES** — include specific code pattern in spec | Could recover 1-2 bugs |
| **C. Fix beyond scope** | 12 | **NO** — requires multi-hunk tool support | 0 (infra limitation) |
| **D. Overfits to tests** | 3 | **YES** — anti-overfitting prompt | Could recover 1-2 bugs |
| **E. Tool blocked** | 2 | **NO** — infra fix (DELETE+INSERT) | 2 with tool fix |
| **F. Never attempted** | 2 | **PARTIALLY** — clearer spec language | Could recover 1 bug |
| **TOTAL** | 66 | | **Estimated 19-30 recoverable** |

### The Contribution Story

From 98 bugs:
- **E34 fixed 24 plausible (13 correct)** — spec guidance nearly doubled correct patches vs baseline (7→13)
- **36% of failures (24 bugs) are directly caused by misleading specs** — the FAULT_OF_OMISSION annotation says "add code" when developer fix is deletion. This is our biggest finding and most actionable improvement.
- **17% (11 bugs) the spec was correct, but the agent has an inherent "add code" bias** — even without misleading guidance, the agent defaults to adding rather than deleting/simplifying. Combined with Category A, this means **53% of all failures (35 bugs) involve the agent adding code when it should delete.** This is the single most important insight.
- **8% (5 bugs) require composing two interacting changes** — agent understands each piece but can't coordinate them. Better specs that describe change interactions could help.
- **18% (12 bugs) are beyond single-point edit capability** — multi-file refactoring that no current single-point APR tool can handle.
- **Better specs could recover 19-30 more bugs** — potentially doubling the plausible patch count from 24 to ~45-54.
