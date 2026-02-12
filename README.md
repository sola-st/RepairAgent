<p align="center">
  <h1 align="center">RepairAgent</h1>
  <p align="center">
    <strong>Autonomous LLM-powered bug repair for Java projects — no human intervention needed.</strong>
  </p>
</p>

<p align="center">
  <a href="https://github.com/codespaces/new?hide_repo_select=true&repo=sola-st/RepairAgent&ref=main"><img src="https://img.shields.io/badge/Open%20in-Codespaces-blue?logo=github" alt="Open in GitHub Codespaces"></a>
  <a href="https://arxiv.org/abs/2403.17134"><img src="https://img.shields.io/badge/arXiv-2403.17134-b31b1b.svg" alt="arXiv"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python 3.10+"></a>
</p>

---

RepairAgent is an autonomous agent that fixes bugs in Java projects using LLMs.
It operates in a loop: **localize the bug -> analyze the code -> generate a fix -> test it -> iterate** — all without human guidance.

On the [Defects4J](https://github.com/rjust/defects4j) benchmark, RepairAgent correctly fixed **164 bugs**, outperforming prior state-of-the-art tools:

| Tool | Correct Fixes | Year |
|------|:---:|:---:|
| **RepairAgent** | **164** | 2024 |
| ChatRepair | 162 | 2024 |
| SelfAPR | 110 | 2023 |
| ITER | 107 | 2023 |
| AlphaRepair | 100 | 2022 |
| Recoder | 68 | 2021 |

> Published at [ICSE 2025](https://arxiv.org/abs/2403.17134). RepairAgent is the first autonomous agent-based approach to automated program repair.

## How It Works

```
                     RepairAgent Workflow
                     ====================

  +---------------------------------------------------------------+
  |                      LLM-Powered Agent                        |
  |                                                               |
  |   +-----------------+    +------------------+    +----------+ |
  |   |  1. Understand  | -> |   2. Collect Info | -> | 3. Fix   | |
  |   |     the Bug     |    |    to Fix the Bug |    | the Bug  | |
  |   +-----------------+    +------------------+    +----------+ |
  |   | - Extract test  |    | - Search codebase |    | - Write  | |
  |   | - Form          |    | - Extract methods |    |   patch   | |
  |   |   hypothesis    |    | - Find similar    |    | - Run    | |
  |   |                 |    |   patterns        |    |   tests  | |
  |   +-----------------+    +------------------+    +----+-----+ |
  |         ^                                              |      |
  |         |           iterate if tests fail              |      |
  |         +----------------------------------------------+      |
  +---------------------------------------------------------------+

  Input: Buggy Java project + failing test
  Output: Correct patch that passes all tests
```

The agent has three states, each with specialized commands:
- **Understand the bug**: reads failing tests, forms hypotheses about root causes
- **Collect information**: searches the codebase, extracts method signatures and similar code patterns
- **Try fixes**: generates patches, applies them, runs the test suite, and iterates

## Supported Models

RepairAgent supports both **OpenAI** and **Anthropic (Claude)** models:

| Provider | Models | Environment Variable |
|----------|--------|---------------------|
| OpenAI | `gpt-4o`, `gpt-4o-mini`, `gpt-4.1`, `gpt-4.1-mini`, `gpt-4.1-nano`, `gpt-4-turbo`, `gpt-3.5-turbo` | `OPENAI_API_KEY` |
| Anthropic | `claude-sonnet-4-20250514`, `claude-haiku-4-20250414`, `claude-opus-4-20250514` | `ANTHROPIC_API_KEY` |

---

## Quick Start

### Option A: Open in Codespaces (zero install)

Click the badge above or go to **Code > Codespaces > New codespace**. Once the container is ready:

```bash
cd repair_agent
python3 set_api_key.py                    # enter your OpenAI or Anthropic API key
./run_on_defects4j.sh experimental_setups/bugs_list hyperparams.json gpt-4o-mini
```

### Option B: VS Code Dev Container

1. **Clone and prepare:**

   ```bash
   git clone https://github.com/sola-st/RepairAgent.git
   cd RepairAgent/repair_agent
   rm -rf defects4j
   git clone https://github.com/rjust/defects4j.git
   cp -r ../data/buggy-lines defects4j
   cp -r ../data/buggy-methods defects4j
   cd ..
   ```

2. **Open in VS Code**, then click "Reopen in Container" when prompted (or use the Command Palette: `Dev Containers: Reopen in Container`).

3. **Set your API key and run:**

   ```bash
   cd repair_agent
   python3 set_api_key.py
   ./run_on_defects4j.sh experimental_setups/bugs_list hyperparams.json gpt-4o-mini
   ```

---

## Table of Contents

1. [Requirements](#requirements)
2. [Running RepairAgent](#running-repairagent)
3. [Configuration](#configuration)
4. [Analyzing Results](#analyzing-results)
5. [Replicating Experiments](#replicating-experiments)
6. [Our Data](#our-data)
7. [Contributing](#contributing)
8. [Citation](#citation)

---

## Requirements

- **Docker** >= 20.04 ([install](https://docs.docker.com/get-docker))
- **VS Code** with the **Dev Containers** extension (recommended, not required)
- **API key** for either [OpenAI](https://platform.openai.com/account/api-keys) or [Anthropic](https://console.anthropic.com/)
- **Disk space**: ~40 GB (dependencies ~8 GB; experiment artifacts grow over time)
- **Internet access** for LLM API calls during execution

---

## Running RepairAgent

### Basic usage

```bash
./run_on_defects4j.sh <bugs_file> <hyperparams_file> [model]
```

**Arguments:**

| Argument | Description | Example |
|----------|-------------|---------|
| `bugs_file` | Text file with one `Project BugIndex` per line | `experimental_setups/bugs_list` |
| `hyperparams_file` | JSON file with agent hyperparameters | `hyperparams.json` |
| `model` | Model name (optional, default: `gpt-4o-mini`) | `gpt-4o`, `claude-sonnet-4-20250514` |

**Examples:**

```bash
# OpenAI
./run_on_defects4j.sh experimental_setups/bugs_list hyperparams.json gpt-4o-mini

# Anthropic Claude
./run_on_defects4j.sh experimental_setups/bugs_list hyperparams.json claude-sonnet-4-20250514
```

The bugs file format is one bug per line:

```
Chart 1
Math 5
Closure 10
Lang 22
```

### What happens during a run

1. RepairAgent checks out the buggy project version from Defects4J.
2. The agent autonomously analyzes the bug, explores the code, and generates fix candidates.
3. Each candidate is applied and tested against the project's test suite.
4. Logs and results are saved to `experimental_setups/experiment_N/` (auto-incremented).

### Choosing the LLM model

The `model` argument (third argument to `run_on_defects4j.sh`) sets **all** LLM models used by RepairAgent:

- **Main agent** (`fast_llm` / `smart_llm`): drives the agent's reasoning loop
- **Static/auxiliary** (`static_llm`): used for mutation generation, fix queries, and auto-completion

For finer control, use environment variables:

```bash
export FAST_LLM=gpt-4o-mini       # main agent fast model
export SMART_LLM=gpt-4o           # main agent smart model
export STATIC_LLM=gpt-4o-mini     # auxiliary LLM calls
```

---

## Configuration

### `hyperparams.json`

| Parameter | Description | Default |
|-----------|-------------|---------|
| `budget_control.name` | Budget visibility: `FULL-TRACK` (show remaining cycles) or `NO-TRACK` (suppress) | `FULL-TRACK` |
| `budget_control.params.#fixes` | Minimum patches the agent should suggest within the budget | `4` |
| `repetition_handling` | `RESTRICT` prevents the agent from repeating the same actions | `RESTRICT` |
| `commands_limit` | Maximum number of agent cycles (iterations) | `40` |
| `external_fix_strategy` | How often to query an external LLM for fix suggestions (0 = disabled) | `0` |

Example:

```json
{
  "budget_control": {
    "name": "FULL-TRACK",
    "params": { "#fixes": 4 }
  },
  "repetition_handling": "RESTRICT",
  "commands_limit": 40,
  "external_fix_strategy": 0
}
```

---

## Analyzing Results

### Output structure

Each run creates an experiment folder under `experimental_setups/`:

```
experimental_setups/experiment_N/
  logs/                  # Full chat history and command outputs (one file per bug)
  plausible_patches/     # Patches that pass all tests (one JSON file per bug)
  mutations_history/     # Mutant patches generated from prior suggestions
  responses/             # Raw LLM responses at each cycle
  saved_contexts/        # Saved agent contexts
  external_fixes/        # Fixes from external LLM queries (if enabled)
```

### Unified overview

The `experiment_overview.py` script provides a single consolidated report across all experiments:

```bash
cd experimental_setups

# Analyze all experiments
python3 experiment_overview.py

# Analyze a specific range
python3 experiment_overview.py --start 1 --end 10

# JSON output for scripting
python3 experiment_overview.py --json
```

This produces:
- Grand totals (bugs tested, fixed, plausible patches, queries)
- Per-experiment summary table
- Per-project breakdown
- Per-bug detail with fix status, plausible status, iteration count
- Lists of fixed and plausible-only bugs

### Individual analysis scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `analyze_experiment_results.py` | Generate per-experiment text reports | `python3 analyze_experiment_results.py` |
| `collect_plausible_patches_files.py` | Consolidate plausible patches from multiple experiments | `python3 collect_plausible_patches_files.py 1 10` |
| `get_list_of_fully_executed.py` | Find bugs that ran to completion (38+ cycles) | `python3 get_list_of_fully_executed.py` |
| `calculate_tokens.py` | Token usage statistics and cost analysis | `python3 calculate_tokens.py` |

---

## Replicating Experiments

### Defects4J

1. **Generate execution batches:**

   ```bash
   python3 get_defects4j_list.py
   ```

   This creates bug lists under `experimental_setups/batches/`.

2. **Run on each batch:**

   ```bash
   ./run_on_defects4j.sh experimental_setups/batches/0 hyperparams.json gpt-4o-mini
   ```

   Replace `0` with the desired batch number. Batches can run in parallel.

3. **Analyze results** using `experiment_overview.py` or the individual scripts above.

4. **Generate comparison tables** (Table III in the paper):

   ```bash
   cd experimental_setups
   python3 generate_main_table.py
   ```

5. **Draw Venn diagrams** (Figure 6 in the paper):

   ```bash
   python3 draw_venn_chatrepair_clean.py
   ```

### GitBug-Java

1. Prepare the GitBug-Java VM (~140 GB disk). See: https://github.com/gitbugactions/gitbug-java
2. Copy RepairAgent into the VM.
3. Run with `experimental_setups/gitbuglist` as the bugs file.
4. Analyze results using the same scripts.

---

## Our Data

In our experiments, RepairAgent fixed **164 bugs** on the Defects4J dataset.

| Resource | Location |
|----------|----------|
| List of fixed bugs | [`data/final_list_of_fixed_bugs`](./data/final_list_of_fixed_bugs) |
| Patch implementation details | [`data/fixes_implementation`](./data/fixes_implementation) |
| Root patches (main phase) | [`data/root_patches/`](./data/root_patches) |
| Derived patches (mutations) | [`data/derivated_pathces/`](./data/derivated_pathces) |
| Defects4J 1.2 baseline comparison | [`repair_agent/experimental_setups/d4j12.csv`](./repair_agent/experimental_setups/d4j12.csv) |

Note: RepairAgent encountered middleware exceptions on 29 bugs, which were not re-run.

---

## Contributing

If you find issues, bugs, or documentation gaps, please [open an issue](https://github.com/sola-st/RepairAgent/issues) or [email the author](mailto:fi_bouzenia@esi.dz).

---

## Citation

If you use RepairAgent in your research, please cite:

```bibtex
@inproceedings{bouzenia2024repairagent,
  title={RepairAgent: An Autonomous, LLM-Based Agent for Program Repair},
  author={Bouzenia, Islem and Pradel, Michael},
  booktitle={Proceedings of the 47th International Conference on Software Engineering (ICSE)},
  year={2025},
  url={https://arxiv.org/abs/2403.17134}
}
```
