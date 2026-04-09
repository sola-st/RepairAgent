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
