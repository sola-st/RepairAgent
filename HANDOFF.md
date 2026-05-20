# Spec-Guided RepairAgent — Project Handoff

This document is a complete handoff for the spec-guided extension of RepairAgent. It covers what was built, what works, what's broken, how to set everything up, and what experiments still need to run.

---

## 1. Project Overview

**Goal:** Improve automated program repair on Defects4J by injecting Javadoc-derived behavioral specifications into the agent's prompt before it tries to fix bugs.

**Base system:** RepairAgent (ICSE 2025) — an LLM-driven repair agent with a 3-state machine (understand bug → collect fix info → try fix) and 40-command budget.

**Our addition:** A spec generation + verification pipeline that runs once at agent init. It produces a structured behavioral spec (purpose, code violations, fix targets, fix_direction, etc.) and injects it into every prompt cycle.

**Key result on 98 bugs the original RepairAgent could NOT fix:**
- 24 plausible patches, 13 correct (E34 — refined spec design)
- 15 unique correct fixes across all experiments (E17 + E34)
- 16 unique correct including E39 (Collections_3)

---

## 2. What Was Built

### 2.1 New Files

| File | Purpose |
|------|---------|
| `repair_agent/autogpt/commands/spec_generator.py` | Main spec generation pipeline. Reads Javadoc + buggy code + tests, produces structured JSON spec via GPT-4o. |
| `repair_agent/autogpt/commands/spec_verifier.py` | Second LLM call that checks spec quality (grounding, violation accuracy, rule consistency). Triggers regeneration if rejected. |

### 2.2 Modified Files

| File | What changed |
|------|-------------|
| `repair_agent/autogpt/agents/base.py` | Lines 99-117: Calls `generate_spec()` at agent init. Injects spec into `prompt_dictionary["spec_section"]`. |
| `repair_agent/autogpt/commands/defects4j.py` | Lines 634-665: Auto DELETE+INSERT — when modifications fail the 70% similarity check, automatically converts to deletion + insertion instead of rejecting. |
| `repair_agent/prompt_settings.yaml` | Added anti-overfitting guideline: "fix must work for arbitrary inputs, not just test values." |

### 2.3 Spec JSON Schema

The spec generator outputs:
```json
{
  "purpose": "One-sentence summary",
  "javadoc_key_rules": ["..."],
  "code_violations": ["Line N: specific discrepancy"],
  "test_expectation": "Input → expected output",
  "rules": ["Behavioral rules the fix must satisfy"],
  "fix_target_line": "primary line",
  "fix_targets": [{"line": "N", "description": "..."}],
  "fix_direction": "ADD_CODE | DELETE_CODE | MODIFY_LOGIC | SIMPLIFY",
  "confidence": "HIGH | LOW",
  "clarifying_question": "yes/no question if confidence is LOW"
}
```

### 2.4 Pipeline Flow

```
Bug selected
    ↓
Gather info (Javadoc, buggy code, tests, sibling/peer methods)
    ↓
LLM (GPT-4o) generates spec JSON
    ↓
Verifier LLM checks spec → accept or regenerate with feedback
    ↓
If confidence LOW → Self-clarify (verifier answers from test context)
    ↓
Format as text → inject as `spec_section` in agent prompt
    ↓
RepairAgent runs unchanged 3-state loop with spec in every prompt
```

---

## 3. Experimental Results So Far

### 3.1 Experiment Summary

| Experiment | Bugs | Plausible | Correct | Notes |
|-----------|------|-----------|---------|-------|
| E17 | 98 | 16 | 7 | First full spec design (with FIX SHAPE guidance) |
| E34 | 98 | 24 | 13 | Refined spec, no FIX SHAPE, added verifier |
| E39 | 22 (subset) | 6 | 5 | Improved spec with fix_direction + self-clarification |

**Union of all experiments: 16 unique correct fixes** on 98 bugs that the original RepairAgent could not fix.

### 3.2 Failure Analysis (66 unfixed bugs in E34)

| Root Cause | Count | % |
|-----------|-------|---|
| Spec misled agent (said "add" when fix is deletion) | 24 | 36% |
| Agent's own add-code bias | 11 | 17% |
| Fix beyond tool scope (multi-file refactoring) | 12 | 18% |
| Agent lacks domain knowledge | 4 | 6% |
| Can't compose multi-step logic | 5 | 8% |
| Other (overfitting, timeout, tool blocked) | 10 | 15% |

**Key insight:** 53% of failures involve the agent adding code when it should delete. Half from misleading specs, half from agent bias.

### 3.3 E39 New Design Evaluation

5 improvements tested on 22-bug subset:
1. **Neutral FAULT_OF_OMISSION** — contributed to 2 new wins
2. **fix_direction field** — correct for only 2/10 deletion bugs (LLM defaults to MODIFY_LOGIC 73%)
3. **Auto DELETE+INSERT** — implemented but never observed firing in logs
4. **Anti-overfitting** — may have prevented Math_36 from hardcoding test values
5. **Self-clarification** — never triggered (confidence always HIGH)

---

## 4. Environment Setup

### 4.1 Prerequisites

- Ubuntu 22.04+ (devcontainer or native)
- Python 3.10+
- Java 11
- Perl with modules: `String::Interpolate`, `DBI`
- OpenAI API key

### 4.2 Quick Setup

```bash
# Clone repo
git clone <repo-url>
cd RepairAgent

# Install Java + Perl deps (system-wide, critical for subprocesses)
sudo apt-get update
sudo apt-get install -y openjdk-11-jdk subversion dos2unix cpanminus libdbi-perl
sudo cpanm String::Interpolate DBI

# Setup defects4j
cd repair_agent/defects4j
./init.sh
cd ..

# Install Python deps
pip install -r requirements.txt

# Set API key
export OPENAI_API_KEY="sk-..."
```

### 4.3 Known Issue: Perl Modules in Devcontainers

**Problem:** Devcontainers are ephemeral. When the container rebuilds, locally-installed Perl modules (`~/perl5/`) are lost.

**Symptom:** `Can't locate String/Interpolate.pm in @INC` or `Can't locate DBI.pm in @INC` during checkout.

**Fix:** Install Perl modules **system-wide** with `sudo cpanm`, not just via `cpanm --local-lib`. The Python subprocess that runs `defects4j checkout` doesn't inherit the local::lib environment.

To make this persistent, add to `.devcontainer/devcontainer.json`:
```json
"postCreateCommand": "sudo apt-get update && sudo apt-get install -y openjdk-11-jdk subversion dos2unix cpanminus libdbi-perl && sudo cpanm String::Interpolate && cd repair_agent/defects4j && ./init.sh"
```

---

## 5. Running Experiments

### 5.1 Run a Single Bug

```bash
cd repair_agent
export PATH=$PATH:$(pwd)/defects4j/framework/bin
python3 checkout_py.py Math 98
./run.sh --ai-settings ai_settings.yaml --model gpt-4o-mini -c -l 40
```

### 5.2 Run a Batch of Bugs

```bash
cd repair_agent
./run_on_defects4j.sh experimental_setups/test_e35_bugs_list hyperparams.json gpt-4o-mini
```

The bug list file format is: `Project BugNumber` per line with blank lines between.

### 5.3 Output Locations

After running, results are in `experimental_setups/experiment_N/`:
- `logs/prompt_history_{Bug}/` — full conversation transcripts
- `responses/model_responses_{Bug}` — raw model responses
- `plausible_patches/plausible_patches_{Bug}.json` — successful patches
- `spec_logs/` — generated specs (parsed JSON + injected prompt text)
- `saved_contexts/` — agent state snapshots
- `mutations_history/` — fix attempt history

---

## 6. What's NOT Done

These are the gaps that need to be filled before the main experiment can run.

### 6.1 Ablation Infrastructure

Need to add `spec_level` parameter to `format_spec_for_prompt()` to control which spec sections are rendered:
- **short:** purpose + test_expectation only (~100 tokens)
- **core:** + code_violations + fix_targets (~250 tokens)
- **full:** everything (current behavior, ~600 tokens)
- **none:** disable spec injection entirely (baseline)

Implementation: read `spec_level` from `hyperparams.json` and pipe it through `generate_spec()` → `format_spec_for_prompt()`.

### 6.2 Multi-LLM Support

Currently hardcoded to:
- Spec generator: `gpt-4o` (in `base.py:102`)
- Agent: passed via `--model` flag, only tested with OpenAI

Need to abstract LLM provider to support:
- OpenAI (gpt-4o, gpt-4o-mini, gpt-4)
- Anthropic (Claude Sonnet/Opus)
- DeepSeek (DeepSeek-V3, DeepSeek-Coder)
- Qwen (Qwen2.5-Coder)

LangChain already supports most of these — need wrapper logic in `spec_generator.py` and `base.py` to select provider based on model name prefix.

### 6.3 Parallel Execution

Current runner `run_on_defects4j.sh` runs bugs sequentially (~7 min/bug). For 835 bugs × 4 conditions × 3 runs = 10,020 runs, sequential is infeasible.

Need either:
- AWS-based parallel orchestration (run N instances)
- GNU parallel locally if hardware allows

### 6.4 Multi-Run / Statistical Validity

Each bug currently runs once. LLM variance is significant (we saw 3 regressions in E39 from non-determinism). For paper-ready results, need 3+ runs per bug with different seeds.

The current pipeline overwrites results on re-run — need to add run ID to output paths.

### 6.5 Auto DELETE+INSERT Verification

Implemented in `defects4j.py` but never observed in E39 logs. Need to add explicit logging when auto-conversion triggers and verify it works on a known similarity-blocked case.

### 6.6 Two Recent Untested Tweaks

Added but not yet evaluated:
- **Step 6** in spec system prompt — examples for when DELETE_CODE applies
- **ACTION instruction** in `format_spec_for_prompt` — tells agent to use `deletions` field when fix_direction is DELETE_CODE

Need to re-run E39 (or equivalent) to see if these help.

---

## 7. Planned Main Experiment

### 7.1 Scope

- **Bug pool:** All 835 Defects4J bugs (full coverage)
- **Conditions:** 4 spec levels (none / short / core / full)
- **Runs per bug:** 3 (for statistical significance)
- **Models:** TBD — see below

### 7.2 Two-Tier Evaluation

**Tier 1: Main Ablation**
- 835 bugs × 4 conditions × 3 runs = 10,020 runs
- One primary model (e.g., gpt-4o-mini for cost)
- Goal: justify each spec component

**Tier 2: Cross-Model Comparison**
- 100 representative bugs × full spec only × 5 models = 500 runs
- Models: gpt-4o-mini, gpt-4o, Claude Sonnet, DeepSeek-V3, Qwen2.5-Coder
- Goal: show generalization across LLMs

**Total: ~10,520 runs**

### 7.3 Cost & Time Estimate

**Sequential:** ~49 days — infeasible

**AWS parallel (50 instances):**
- Time: ~1-2 days wall-clock
- EC2: ~$200
- LLM API: $200-700 depending on model mix
- **Total: ~$400-1,000**

### 7.4 Research Questions

| RQ | Question | Answered by |
|----|---------|------------|
| RQ1 | Does spec-guided repair fix bugs the original could not? | E17/E34 results on 98 hard bugs (done) |
| RQ2 | Does spec injection break already-fixable bugs? | Tier 1 on 164 originally-fixed bugs |
| RQ3 | Which spec components are necessary? | Tier 1 ablation (none/short/core/full) |
| RQ4 | Does our approach generalize across LLMs? | Tier 2 multi-model |
| RQ5 | Where does our approach still fail? | Already answered (root cause analysis) |

---

## 8. Documentation Map

All analysis and reports are in `researchAnalysis/`:

| File | Contents |
|------|----------|
| `researchAnalysis/reports/MASTER_REPORT.md` | Top-level summary of all experiments |
| `researchAnalysis/reports/MENTOR_STATUS_REPORT.md` | Status report for mentor discussion |
| `researchAnalysis/reports/E39_DETAILED_ANALYSIS.md` | Per-bug evaluation of the 5 improvements |
| `researchAnalysis/unfixed_analysis/failure_root_causes.md` | Root cause taxonomy of 66 unfixed bugs |
| `researchAnalysis/unfixed_analysis/unfixed_bugs_evidence.md` | Per-bug evidence document for all 66 failures |
| `researchAnalysis/plausible_analysis/E34/*.md` | 24 individual analysis files for E34 plausible patches |
| `researchAnalysis/charts/*.png` | Generated charts (6 total) |
| `researchAnalysis/presentation/e39_evaluation_slides.md` | Slide content for E39 results |
| `researchAnalysis/presentation/unfixed_bugs_slides.md` | Slide content for failure patterns |

---

## 9. Open Questions for the Next Researcher

1. **Spec generation model:** Lock to gpt-4o or vary it in the ablation?
2. **Agent model:** gpt-4o-mini (cheap) or stronger model for final paper?
3. **Run count:** 3 runs minimum, or budget allows 5?
4. **Bug filtering:** All 835 Defects4J bugs, or exclude the ones nobody can fix (e.g., multi-file Closure bugs)?
5. **Confidence calibration:** LLM never sets LOW confidence — should we use a heuristic instead (e.g., Javadoc length < 150 chars → LOW)?
6. **Agent prompt:** Should the agent prompt explicitly mention the `deletions` field when fix_direction is DELETE_CODE? (Partially added but untested)

---

## 10. Quick Start for the Next Person

1. **Read** `researchAnalysis/reports/MASTER_REPORT.md` for the big picture
2. **Read** `researchAnalysis/reports/MENTOR_STATUS_REPORT.md` for current state
3. **Set up environment** following Section 4 above
4. **Run a single bug** (Math_98 is easiest) to verify pipeline works
5. **Implement Section 6.1** (ablation infrastructure) — this is the #1 blocker
6. **Run pilot** — 20 bugs × 4 conditions × 1 run locally
7. **If pilot is clean** — scale to AWS with full plan from Section 7

Good luck!
