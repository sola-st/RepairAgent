# Status Report for Mentor Discussion

---

## 1. What We Have Done

### 1.1 Experimental Timeline

| Experiment | Bugs | Plausible | Correct | Specs? | Key change |
|-----------|------|-----------|---------|--------|------------|
| E1-E10 | small tests | few | — | E1-E10: NO | Early development, no specs |
| E11-E16 | 1-3 bugs each | 0-2 | — | YES | First spec prototypes, iterating prompt design |
| **E17** | **98** | **16** | **7** | YES + FIX SHAPE | Full run with FIX SHAPE guidance (INSERT_BEFORE_LINE / MODIFY_LINE) |
| E29 | 8 | 3 | — | YES | Intermediate spec iteration |
| **E34** | **98** | **24** | **13** | YES, no FIX SHAPE | Full run, refined spec (removed FIX SHAPE, added spec verifier) |
| **E39** | **22** | **6** | **5** | YES + new fields | Test run with 5 improvements (fix_direction, anti-overfitting, etc.) |

### 1.2 Key Results

| Metric | E17 (baseline with specs) | E34 (refined specs) | Delta |
|--------|--------------------------|--------------------|----|
| Plausible patches | 16 / 98 | 24 / 98 | +8 |
| Correct patches | 7 / 98 | 13 / 98 | +6 |
| Union (unique correct) | — | 15 / 98 | — |
| Spec avg length | 1,930 chars | 2,350 chars | +22% |

### 1.3 Spec Design Evolution

**E17 spec (shorter, more prescriptive):**
- Purpose + Javadoc Rules + Code Violations + Test Expectation
- **"Likely fix direction"** — told agent what to do
- **"FIX SHAPE: INSERT_BEFORE_LINE"** or **"MODIFY_LINE"** — told agent which tool mechanism to use
- **"Fix target:"** — gave the actual fixed line of code
- Average: ~1,930 chars

**E34 spec (longer, diagnostic only):**
- Purpose + Javadoc Rules + Code Violations + Test Expectation + Behavioral Rules + Fix Targets
- Removed FIX SHAPE (no tool mechanism guidance)
- Removed "Likely fix direction" and "Fix target" code
- Added spec verifier (LLM checks spec quality before injection)
- Added behavioral rules (up to 8 rules)
- Average: ~2,350 chars

**E39 spec (longest, with new fields):**
- Everything from E34 + fix_direction + confidence + clarifying_question + anti-overfitting
- Average: ~2,468 chars

### 1.4 Analysis Work Completed

- **Per-bug analysis of all 24 E34 plausible patches** — correct/incorrect verdict, match type, evidence paths
- **Root cause taxonomy of all 66 unfixed bugs** — reclassified from symptoms (STUCK_LOOP, COMPILE_ERROR) to causes (SPEC_MISLED, ADD_VS_DELETE_BIAS, DOMAIN_KNOWLEDGE, etc.)
- **6 charts** — e17_vs_e34 comparison, failure categories, project breakdown, etc.
- **Presentation slide content** — for both fixed and unfixed bugs with evidence
- **E39 detailed evaluation** — per-bug analysis comparing spec content, agent behavior, and outcomes

---

## 2. What is Working

### 2.1 Spec-guided repair improves over baseline RepairAgent
- E34 (spec-guided): 24 plausible, 13 correct vs original RepairAgent: 16 plausible, 7 correct
- Specs consistently help the agent localize the bug and understand the fix direction
- The spec generator + verifier pipeline is stable and produces valid specs for 98/98 bugs

### 2.2 Root cause analysis is complete and actionable
- 36% of failures caused by misleading specs (FAULT_OF_OMISSION says "add" when fix is "delete")
- 53% of all failures involve agent adding code when it should delete — this is the single most important finding
- Clear taxonomy: A (spec misled), B1-B2c (agent limitations), C (tool scope), D (overfitting), E (tool blocked), F (never attempted)

### 2.3 E39 improvements — partial success
- 2 new plausible patches (Collections_3 correct, Collections_5 plausible) that E34 never had
- 16 unique correct fixes total across all experiments (E17 + E34 + E39)
- FAULT_OF_OMISSION neutralization works conceptually

---

## 3. What is NOT Working

### 3.1 fix_direction accuracy is poor
- LLM defaults to MODIFY_LOGIC (73% of bugs), DELETE_CODE only 9%
- 8 of 10 deletion-type bugs got wrong fix_direction
- **Tweak applied:** Added Step 6 with examples and "common mistake" warning — not yet tested

### 3.2 Agent ignores fix_direction even when correct
- Lang_46: spec said DELETE_CODE, agent made 32 write_fix attempts, all using `modifications`, zero using `deletions`
- **Tweak applied:** Added ACTION instruction ("Use the `deletions` field in write_fix") — not yet tested

### 3.3 Self-clarification never triggers
- confidence = HIGH for all 22 bugs (100%), including Collections_8 where Javadoc is 13 words
- The LLM doesn't know when to admit uncertainty
- Possible fix: heuristic confidence based on Javadoc length instead of LLM judgment

### 3.4 Auto DELETE+INSERT not verified
- No "Auto-converted" messages in E39 logs
- Agents may have failed at JSON escaping or compilation before reaching the similarity check
- Need targeted test with a bug where we know similarity blocking occurs

### 3.5 LLM variance masks signal
- 3 regressions (Compress_3, Math_97, Time_9) are from different agent execution paths, not worse specs
- Single runs cannot distinguish improvement signal from gpt-4o-mini randomness
- Need 3-5 runs per bug for statistical validity

---

## 4. The Prompt Length Question

### 4.1 Current spec sizes

| Version | Avg chars | Avg tokens (~) | Key components |
|---------|-----------|---------------|----------------|
| E17 | 1,930 | ~480 | Purpose + Rules + Violations + FIX SHAPE + Fix target code |
| E34 | 2,350 | ~590 | Purpose + Rules + Violations + Behavioral rules + Fix targets |
| E39 | 2,468 | ~620 | E34 + fix_direction + confidence + anti-overfitting |

### 4.2 What a reviewer would ask

> "Your spec adds ~600 tokens to every agent prompt. How do you know all of it is necessary? Would a simpler spec work just as well?"

### 4.3 What we already know about short vs long specs

**E17 (shorter spec, 1,930 chars) vs E34 (longer spec, 2,350 chars):**
- E17: 16 plausible, 7 correct
- E34: 24 plausible, 13 correct
- The longer spec performed **better**, not worse

But E17 had **FIX SHAPE** guidance (INSERT_BEFORE_LINE/MODIFY_LINE in 92/98 specs) that E34 removed. This complicates the comparison — E17 was shorter but more prescriptive. E34 was longer but more diagnostic.

The interesting finding: E17's FIX SHAPE told agents **how to use the tool** (use insertions, not modifications). This helped Compress_3 succeed in E17. When E34 removed FIX SHAPE, Compress_3 still succeeded — but when E39 ran, Compress_3 regressed because the agent used modifications instead of insertions. This suggests **FIX SHAPE was valuable for tool guidance**, even though E34 got more total fixes without it (because E34 improved other spec components).

### 4.4 Ablation study design

To satisfy reviewers, we need to test these variants on the same 98 bugs:

| Variant | Spec content | Tokens | Tests |
|---------|-------------|--------|-------|
| **A0: No spec** | Nothing injected | 0 | Need new run (or use RepairAgent baseline numbers) |
| **A1: Minimal spec** | Purpose + test_expectation only | ~100 | Need to run |
| **A2: Core spec** | Purpose + code_violations + test_expectation | ~250 | Need to run |
| **A3: Full spec (E34)** | All fields | ~590 | Already have: 24 plausible, 13 correct |
| **A4: Full + new (E39)** | All fields + fix_direction + tweaks | ~620 | Need full 98-bug run |

Implementation: Modify `format_spec_for_prompt()` to accept a `level` parameter that controls which fields are rendered. All spec JSONs stay the same — we just control what the agent sees.

### 4.5 Minimal viable ablation (if time is tight)

If running 98 bugs 4 times is too expensive, test on a **20-bug representative subset** (same as E39 test list minus the 2 non-regression bugs). This gives directional signal in 1/5 the cost.

---

## 5. What is Ready for the Paper

| Section | Status | Notes |
|---------|--------|-------|
| **Approach/Method** | Ready | Spec generator + verifier pipeline is implemented and stable |
| **RQ1: Does spec guidance help?** | Ready | E17 vs E34 comparison: +8 plausible, +6 correct |
| **RQ2: What types of bugs benefit?** | Ready | Per-bug analysis of 24 plausible + 66 unfixed |
| **RQ3: Root cause of failures** | Ready | Full taxonomy with evidence |
| **RQ4: Ablation study** | **NOT ready** | Need A0/A1/A2 runs to justify prompt length |
| **Threats to validity** | Partially ready | LLM variance is identified but not quantified (need multi-run) |

---

## 6. Recommended Next Steps (Priority Order)

1. **Ablation study** (addresses mentor's concern directly)
   - Implement level parameter in `format_spec_for_prompt`
   - Run A1 and A2 on 98 bugs (A0 and A3 already exist)
   - This is the #1 blocker for the paper

2. **Full E39 run with tweaks** (98 bugs, not just 22)
   - Tests the latest fix_direction improvements on the full pool
   - Provides A4 data point for ablation

3. **Multi-run for statistical validity** (3 runs of E34 on 98 bugs)
   - Quantifies LLM variance
   - Shows which improvements are real vs noise

4. **Paper writing**
   - Can start Introduction, Related Work, Approach sections now
   - Results section needs ablation data
