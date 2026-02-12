# RepairAgent

RepairAgent is an autonomous LLM-based agent for automated program repair. It targets the [Defects4J](https://github.com/rjust/defects4j) benchmark and uses an LLM-driven loop to localize, analyze, and fix Java bugs.

For details on the approach and evaluation, see the [research paper](https://arxiv.org/abs/2403.17134).

---

## Table of Contents

1. [Requirements](#i-requirements)
2. [Getting Started](#ii-getting-started)
   - [VS Code Dev Container](#option-a-vs-code-dev-container)
3. [Running RepairAgent](#iii-running-repairagent)
4. [Configuration](#iv-configuration)
5. [Analyzing Results](#v-analyzing-results)
6. [Replicating Experiments](#vi-replicating-experiments)
7. [Our Data](#vii-our-data)
8. [Contributing](#viii-contributing)

---

## I. Requirements

- **Docker** >= 20.04 ([install](https://docs.docker.com/get-docker))
- **VS Code** with the **Dev Containers** extension (recommended, not required)
- **OpenAI API key** with credits ([get one here](https://platform.openai.com/account/api-keys))
- **Disk space**: ~40 GB (dependencies ~8 GB; experiment artifacts grow over time)
- **Internet access** for OpenAI API calls during execution

---

## II. Getting Started

### VS Code Dev Container

This is the easiest method. It builds a lightweight container locally and avoids pulling the full Docker image (~22 GB).

1. **Clone and prepare the repository:**

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

3. **In the VS Code terminal:**

   ```bash
   cd repair_agent
   ```

4. **Mark generated files as assume-unchanged** to keep your git status clean:

   ```bash
   git update-index --assume-unchanged .env autogpt/.env run.sh
   git update-index --assume-unchanged ai_settings.yaml
   git update-index --assume-unchanged experimental_setups/experiments_list.txt
   git update-index --assume-unchanged experimental_setups/fixed_so_far
   ```

5. **Set the OpenAI API key:**

   ```bash
   python3 set_api_key.py
   ```

   This writes your key into the `.env` files and `run.sh`. Alternatively, export it directly:

   ```bash
   export OPENAI_API_KEY=sk-...
   ```

You are now ready to run RepairAgent (see [Running RepairAgent](#iii-running-repairagent)).
---

## III. Running RepairAgent

### Quick start

```bash
./run_on_defects4j.sh <bugs_file> <hyperparams_file> [model]
```

**Arguments:**

| Argument | Description | Example |
|----------|-------------|---------|
| `bugs_file` | Text file with one `Project BugIndex` per line | `experimental_setups/bugs_list` |
| `hyperparams_file` | JSON file with agent hyperparameters | `hyperparams.json` |
| `model` | OpenAI model name (optional, default: `gpt-4o-mini`) | `gpt-4o`, `gpt-4.1` |

**Example:**

```bash
./run_on_defects4j.sh experimental_setups/bugs_list hyperparams.json gpt-4o-mini
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

The `--model` flag (or third argument to `run_on_defects4j.sh`) sets **all** LLM models used by RepairAgent:

- **Main agent** (`fast_llm` / `smart_llm`): drives the agent's reasoning loop
- **Static/auxiliary** (`static_llm`): used for mutation generation, fix queries, and auto-completion

For finer control, use environment variables:

```bash
export FAST_LLM=gpt-4o-mini       # main agent fast model
export SMART_LLM=gpt-4o           # main agent smart model
export STATIC_LLM=gpt-4o-mini     # auxiliary LLM calls
```

---

## IV. Configuration

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

## V. Analyzing Results

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

These older scripts are still available for specific tasks:

| Script | Purpose | Usage |
|--------|---------|-------|
| `analyze_experiment_results.py` | Generate per-experiment text reports | `python3 analyze_experiment_results.py` |
| `collect_plausible_patches_files.py` | Consolidate plausible patches from multiple experiments | `python3 collect_plausible_patches_files.py 1 10` |
| `get_list_of_fully_executed.py` | Find bugs that ran to completion (38+ cycles) | `python3 get_list_of_fully_executed.py` |
| `calculate_tokens.py` | Token usage statistics and cost analysis | `python3 calculate_tokens.py` |

---

## VI. Replicating Experiments

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

## VII. Our Data

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

## VIII. Contributing

If you find issues, bugs, or documentation gaps, please [open an issue](https://github.com/sola-st/RepairAgent/issues) or [email the author](mailto:fi_bouzenia@esi.dz).
