# RepairAgent

This is the main source directory for RepairAgent. See the [root README](../README.md) for full documentation on setup, usage, configuration, and result analysis.

## Quick Start

```bash
# Works on a fresh clone — bootstraps itself, installs deps, guides you through everything
python3 repairagent.py

# Direct mode (for scripting/CI)
python3 repairagent.py run --bugs "Chart 1, Math 5" --model gpt-4o-mini

# Install all dependencies non-interactively
python3 repairagent.py setup --install-deps

# Analyze results
cd experimental_setups && python3 experiment_overview.py
```

## Fix Your Own Project (generic mode)

Beyond the Defects4J benchmark, RepairAgent can attempt to repair an **arbitrary
Maven or Gradle Java project** that has a failing test. This is an additive path
selected by the `fix-project` command — the Defects4J evaluation flow is
untouched.

```bash
python3 repairagent.py fix-project \
    --path /abs/path/to/your/project \      # must be a git repo; or use --git <url> [--ref <sha>]
    --test "com.foo.BarTest#testThing" \    # failing test (repeatable); auto-detected if omitted
    --build auto \                          # maven | gradle | auto (default: auto-detect)
    --model gpt-4o-mini \
    --max-cycles 40
```

What it does:

1. Copies your project into the workspace (your repo is left untouched) and runs
   the test suite once to establish a baseline of already-failing tests.
2. Localizes the fault from the failing test's **stack trace** (no ground-truth
   buggy lines are needed). You can add hints with `--suspect src/.../Foo.java:120`
   and narrow stack-frame filtering with `--package com.foo`.
3. Runs the normal agent loop. After each candidate fix it validates the targeted
   test first, then the full suite to check for regressions.
4. On success (the failing test passes and nothing previously-passing regressed)
   it writes the unified diff to `plausible_patch.diff` for **human review**.
   Correctness is not auto-decided — there is no reference patch to compare to.

Requirements & notes:

- The target **must be a git repository** (the agent reverts its edits via git
  between attempts). Run `git init && git add -A && git commit -m base` first if
  needed.
- Generic mode **builds and runs the target project's code on this host**. For
  untrusted projects, prefer Docker (`--docker`).
- Multi-module builds: pass `--module <subdir>` (single-module is the default).
- The first build may download dependencies (network required).

## Directory Structure

```
repair_agent/
  repairagent.py              # Guided CLI — recommended entry point
  autogpt/                    # Core agent framework (based on AutoGPT)
    agents/                   # Agent classes (base agent, repair agent)
    app/                      # CLI, configurator, main entry point
    commands/                 # Agent commands (defects4j operations, fix writing)
    config/                   # Configuration (Config class, env vars)
    llm/                      # LLM providers (OpenAI, Anthropic) and utilities
    logs/                     # Logging infrastructure (Rich console output)
    memory/                   # Conversation memory and vector storage
    prompts/                  # Prompt templates
  experimental_setups/        # Experiment folders, analysis scripts, batch configs
  requirements-core.txt       # Minimal Python dependencies (for the core agent)
  requirements.txt            # Full dependencies (includes dev tools, analysis)
  Dockerfile                  # Self-contained image (Java, Perl, Defects4J included)
  hyperparams.json            # Agent hyperparameters
  set_api_key.py              # Configure API keys (OpenAI and/or Anthropic)
```

## What the CLI Handles

The `repairagent.py` wizard automates the full setup and run pipeline:

1. **Bootstrap** — if `click`/`rich` aren't installed, offers to `pip install` them automatically
2. **Environment check** — detects Python, Java, Perl, cpanminus, Subversion, Defects4J, Python packages, API keys
3. **Dependency installation** — offers to install missing system packages (`apt-get`), Python packages (`pip`), and Defects4J (clone + init)
4. **API key setup** — interactive configuration for OpenAI and/or Anthropic
5. **Model selection** — pick from available models based on configured providers
6. **Bug selection** — manual entry, project picker, or load from file
7. **Execution** — runs the agent locally or in Docker, shows progress and results summary
