#!/usr/bin/env python3
"""RepairAgent — Guided CLI for autonomous LLM-powered bug repair.

Usage:
    python3 repairagent.py                                     # Interactive guided mode
    python3 repairagent.py run --bugs "Chart 1,Math 5" --model gpt-4o-mini
    python3 repairagent.py setup                               # Check environment & configure API keys
    python3 repairagent.py run --docker --bugs "Chart 1"       # Run inside Docker
"""
import json
import locale
import os
import shutil
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Bootstrap: ensure click and rich are available before anything else.
# If missing, offer to install with pip using only stdlib I/O, then re-exec.
# ---------------------------------------------------------------------------
_BOOTSTRAP_PACKAGES = ["click", "rich"]


def _check_bootstrap_deps() -> list:
    """Return list of missing bootstrap packages."""
    missing = []
    for pkg in _BOOTSTRAP_PACKAGES:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    return missing


def _bootstrap_install(missing: list) -> None:
    """Install missing bootstrap packages using stdlib-only I/O, then re-exec."""
    print()
    print("=" * 60)
    print("  RepairAgent requires these Python packages to start:")
    for pkg in missing:
        print(f"    - {pkg}")
    print()
    answer = input("  Install them now with pip? [Y/n] ").strip().lower()
    if answer in ("", "y", "yes"):
        cmd = [sys.executable, "-m", "pip", "install", "--quiet"] + missing
        print(f"  Running: {' '.join(cmd)}")
        result = subprocess.run(cmd)
        if result.returncode != 0:
            print("  ERROR: pip install failed. Install manually:")
            print(f"    pip install {' '.join(missing)}")
            sys.exit(1)
        # Re-exec so the real imports succeed
        print("  Restarting...")
        os.execv(sys.executable, [sys.executable] + sys.argv)
    else:
        print(f"  Install manually: pip install {' '.join(missing)}")
        sys.exit(1)


_missing_bootstrap = _check_bootstrap_deps()
if _missing_bootstrap:
    _bootstrap_install(_missing_bootstrap)

# Now safe to import click and rich
import click  # noqa: E402
from rich.console import Console  # noqa: E402
from rich.panel import Panel  # noqa: E402
from rich.prompt import Confirm, IntPrompt, Prompt  # noqa: E402
from rich.rule import Rule  # noqa: E402
from rich.table import Table  # noqa: E402

console = Console()

SCRIPT_DIR = Path(__file__).parent.resolve()

AGENT_VERSION = "0.6.5"

AI_SETTINGS_TEMPLATE = """\
ai_goals:
- 'Locate the Bug: Execute test cases and get info to systematically identify and isolate the bug within the project "{name}" and bug index "{bug_index}".'
- 'Perform code Analysis: Analyze the lines of code associated with the bug to discern and comprehend the potentially faulty sections.'
- 'Try simple Fixes: Attempt straightforward remedies, such as altering operators, changing identifiers, modifying numerical or boolean literals, adjusting function arguments, or refining conditional statements. Explore all plausible and elementary fixes relevant to the problematic code.'
- 'Try complex Fixes: In instances where simple fixes prove ineffective, utilize the information gathered to propose more intricate solutions aimed at resolving the bug.'
- 'Iterative Testing: Repeat the debugging process iteratively, incorporating the insights gained from each iteration, until all test cases pass successfully.'
ai_name: RepairAgentV{version}
ai_role: |
  You are an AI assistant specialized in fixing bugs in Java code.
  You will be given a buggy project, and your objective is to autonomously understand and fix the bug.
  You have three states, which each offer a unique set of commands,
   * 'collect information to understand the bug', where you gather information to understand a bug;
   * 'collect information to fix the bug', where you gather information to fix the bug;
   * 'trying out candidate fixes', where you suggest bug fixes that will be validated by a test suite.
api_budget: 0.0
"""

OPENAI_MODELS = [
    ("gpt-4o", "Most capable OpenAI model"),
    ("gpt-4o-mini", "Fast and affordable"),
    ("gpt-4.1", "Latest GPT-4.1"),
    ("gpt-4.1-mini", "GPT-4.1 mini"),
    ("gpt-4-turbo", "GPT-4 Turbo"),
    ("gpt-3.5-turbo", "Legacy, cheapest"),
]

ANTHROPIC_MODELS = [
    ("claude-sonnet-4-20250514", "Recommended — balanced speed/quality"),
    ("claude-haiku-4-20250414", "Fastest, lowest cost"),
    ("claude-opus-4-20250514", "Most capable"),
]


# ---------------------------------------------------------------------------
# Environment checks
# ---------------------------------------------------------------------------

def is_in_container() -> bool:
    """Detect if running inside a Docker container or Codespace."""
    if os.path.exists("/.dockerenv"):
        return True
    if os.environ.get("CODESPACES"):
        return True
    if os.path.exists("/run/.containerenv"):
        return True
    return False


def _check_command(cmd: list[str]) -> str | None:
    """Run a command and return its stdout, or None on failure."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.stdout.strip() if result.returncode == 0 else None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def check_environment() -> dict[str, tuple[bool, str]]:
    """Check all required dependencies and return status dict."""
    checks = {}

    # Python
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    checks["Python 3.10+"] = (sys.version_info >= (3, 10), py_ver)

    # Java (java -version writes to stderr)
    java_ver = None
    try:
        result = subprocess.run(
            ["java", "-version"], capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            output = result.stderr.strip() or result.stdout.strip()
            java_ver = output.split("\n")[0] if output else None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    checks["Java (JDK)"] = (java_ver is not None, java_ver or "not found")

    # Perl
    perl_out = _check_command(["perl", "-v"])
    checks["Perl"] = (perl_out is not None, "available" if perl_out else "not found")

    # cpanminus (needed for Defects4J init)
    cpanm_out = _check_command(["cpanm", "--version"])
    checks["cpanminus"] = (cpanm_out is not None, "available" if cpanm_out else "not found")

    # Subversion (needed by some Defects4J projects)
    svn_out = _check_command(["svn", "--version", "--quiet"])
    checks["Subversion"] = (svn_out is not None, svn_out or "not found")

    # Defects4J
    d4j_path = SCRIPT_DIR / "defects4j" / "framework" / "bin" / "defects4j"
    d4j_on_path = shutil.which("defects4j") is not None
    checks["Defects4J"] = (d4j_path.exists() or d4j_on_path, str(d4j_path) if d4j_path.exists() else "not found")

    # Python packages
    py_pkgs_ok = _check_python_packages()
    checks["Python packages"] = (py_pkgs_ok, "installed" if py_pkgs_ok else "some missing")

    # API keys
    has_openai = _has_api_key("OPENAI_API_KEY")
    has_anthropic = _has_api_key("ANTHROPIC_API_KEY")
    if has_openai and has_anthropic:
        key_status = "OpenAI + Anthropic"
    elif has_openai:
        key_status = "OpenAI"
    elif has_anthropic:
        key_status = "Anthropic"
    else:
        key_status = "not configured"
    checks["API key"] = (has_openai or has_anthropic, key_status)

    return checks


def _check_python_packages() -> bool:
    """Quick check if critical Python packages are installed."""
    for mod in ["colorama", "openai", "yaml", "tiktoken", "dotenv", "pydantic"]:
        try:
            __import__(mod)
        except ImportError:
            return False
    return True


def _has_api_key(key_name: str) -> bool:
    """Check if an API key is set in environment or .env files."""
    val = os.environ.get(key_name)
    if val and val != "GLOBAL-API-KEY-PLACEHOLDER":
        return True
    # Check .env files
    for env_file in [SCRIPT_DIR / ".env", SCRIPT_DIR / "autogpt" / ".env"]:
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.strip().startswith(f"{key_name}="):
                    v = line.split("=", 1)[1].strip()
                    if v and v != "GLOBAL-API-KEY-PLACEHOLDER":
                        return True
    return False


def display_environment(checks: dict) -> None:
    """Display environment check results."""
    console.print()
    console.print(Rule("Environment Check", style="bold blue"))
    console.print()
    for name, (ok, detail) in checks.items():
        mark = "[green]OK[/green]" if ok else "[red]MISSING[/red]"
        console.print(f"  {mark}  {name}: {detail}")
    console.print()


# ---------------------------------------------------------------------------
# Dependency installation
# ---------------------------------------------------------------------------

REQUIRED_SYSTEM_PACKAGES = {
    "openjdk-11-jdk": {
        "check_cmd": ["java", "-version"],
        "check_stderr": True,
        "desc": "Java 11 JDK (required for Defects4J)",
    },
    "perl": {
        "check_cmd": ["perl", "-v"],
        "desc": "Perl interpreter (required for Defects4J)",
    },
    "cpanminus": {
        "check_cmd": ["cpanm", "--version"],
        "desc": "Perl module installer (required for Defects4J init)",
    },
    "subversion": {
        "check_cmd": ["svn", "--version", "--quiet"],
        "desc": "SVN client (required by some Defects4J projects)",
    },
    "libdbi-perl": {
        "check_cmd": ["perl", "-MDBI", "-e", "1"],
        "desc": "Perl DBI library (required by Defects4J)",
    },
}

D4J_REPO_URL = "https://github.com/rjust/defects4j.git"
DATA_DIR = SCRIPT_DIR.parent / "data"


def detect_missing_system_packages() -> list[tuple[str, str]]:
    """Return list of (package_name, description) for missing system packages."""
    missing = []
    for pkg, info in REQUIRED_SYSTEM_PACKAGES.items():
        try:
            result = subprocess.run(
                info["check_cmd"],
                capture_output=True, text=True, timeout=10,
            )
            if info.get("check_stderr"):
                output = result.stderr.strip() or result.stdout.strip()
                ok = result.returncode == 0 or bool(output)
            else:
                ok = result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            ok = False
        if not ok:
            missing.append((pkg, info["desc"]))
    return missing


def install_system_packages(packages: list[str]) -> bool:
    """Install system packages using apt-get. Returns True on success."""
    if not shutil.which("apt-get"):
        console.print("  [yellow]apt-get not found. Install these packages manually:[/yellow]")
        console.print(f"    {' '.join(packages)}")
        return False

    console.print()
    console.print("  The following system packages will be installed:")
    for pkg in packages:
        console.print(f"    - {pkg}")
    console.print()
    console.print("  [dim]This requires sudo (administrator) access.[/dim]")
    if not Confirm.ask("  Install now?", default=True):
        return False

    cmd = ["sudo", "apt-get", "update", "-qq"]
    console.print(f"  Running: sudo apt-get update")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        console.print("  [red]apt-get update failed.[/red]")
        return False

    cmd = ["sudo", "apt-get", "install", "-y"] + packages
    console.print(f"  Running: sudo apt-get install -y {' '.join(packages)}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        console.print("  [red]Package installation failed.[/red]")
        return False

    console.print("  [green]System packages installed successfully.[/green]")
    return True


def install_python_requirements() -> bool:
    """Install Python requirements. Tries core first, falls back to full."""
    core_req = SCRIPT_DIR / "requirements-core.txt"
    full_req = SCRIPT_DIR / "requirements.txt"
    req_file = core_req if core_req.exists() else full_req

    console.print(f"  Installing Python packages from {req_file.name}...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
        cwd=str(SCRIPT_DIR),
    )
    if result.returncode != 0:
        console.print("  [red]pip install failed. Check errors above.[/red]")
        return False
    console.print("  [green]Python packages installed.[/green]")
    return True


def is_defects4j_initialized() -> bool:
    """Check if Defects4J is fully initialized (not just cloned)."""
    d4j_bin = SCRIPT_DIR / "defects4j" / "framework" / "bin" / "defects4j"
    return d4j_bin.exists()


def install_defects4j() -> bool:
    """Clone, copy bug data, install Perl deps, and initialize Defects4J."""
    d4j_dir = SCRIPT_DIR / "defects4j"

    # Step 1: Clone if needed
    if not (d4j_dir / ".git").exists():
        console.print("  [bold]Step 1/4:[/bold] Cloning Defects4J...")
        if d4j_dir.exists():
            shutil.rmtree(d4j_dir)
        result = subprocess.run(
            ["git", "clone", D4J_REPO_URL, str(d4j_dir)],
            cwd=str(SCRIPT_DIR),
        )
        if result.returncode != 0:
            console.print("  [red]Git clone failed.[/red]")
            return False
        console.print("  [green]Cloned successfully.[/green]")
    else:
        console.print("  [bold]Step 1/4:[/bold] Defects4J already cloned. [green]OK[/green]")

    # Step 2: Copy buggy-lines and buggy-methods data
    console.print("  [bold]Step 2/4:[/bold] Copying bug data...")
    for data_subdir in ["buggy-lines", "buggy-methods"]:
        src = DATA_DIR / data_subdir
        dst = d4j_dir / data_subdir
        if src.exists():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(str(src), str(dst))
            console.print(f"    Copied {data_subdir}/")
        else:
            console.print(f"    [yellow]Warning: {src} not found, skipping.[/yellow]")

    # Step 3: Install Perl dependencies
    console.print("  [bold]Step 3/4:[/bold] Installing Perl dependencies (cpanm)...")
    if shutil.which("cpanm"):
        subprocess.run(
            ["cpanm", "--installdeps", "."],
            cwd=str(d4j_dir),
        )
        # String::Interpolate is required by Defects4J but not always declared
        subprocess.run(["cpanm", "String::Interpolate"], cwd=str(d4j_dir))
        console.print("  [green]Perl dependencies installed.[/green]")
    else:
        console.print("  [yellow]cpanm not found — skipping Perl deps (install cpanminus first).[/yellow]")

    # Step 4: Run init.sh
    console.print("  [bold]Step 4/4:[/bold] Running Defects4J init.sh (this takes several minutes)...")
    init_script = d4j_dir / "init.sh"
    if init_script.exists():
        result = subprocess.run(
            ["bash", str(init_script)],
            cwd=str(d4j_dir),
        )
        if result.returncode != 0:
            console.print("  [red]init.sh failed.[/red]")
            return False
    else:
        console.print("  [red]init.sh not found in Defects4J directory.[/red]")
        return False

    if is_defects4j_initialized():
        console.print("  [green]Defects4J initialized successfully.[/green]")
        return True
    else:
        console.print("  [red]Defects4J initialization did not produce expected binaries.[/red]")
        return False


def install_all_dependencies() -> bool:
    """Interactive dependency installation orchestrator.

    Detects all missing deps, installs in order:
    system packages → Python packages → Defects4J.
    Returns True if environment is ready.
    """
    console.print(Rule("Dependency Installation", style="bold blue"))
    console.print()

    all_ok = True

    # 1. System packages
    missing_sys = detect_missing_system_packages()
    if missing_sys:
        console.print("  [yellow]Missing system packages:[/yellow]")
        for pkg, desc in missing_sys:
            console.print(f"    - {pkg}: {desc}")
        pkg_names = [pkg for pkg, _ in missing_sys]
        if not install_system_packages(pkg_names):
            console.print("  [yellow]Skipping system packages. Some features may not work.[/yellow]")
            all_ok = False
    else:
        console.print("  System packages: [green]all present[/green]")

    # 2. Python packages
    if not _check_python_packages():
        console.print()
        console.print("  [yellow]Some Python packages are missing.[/yellow]")
        if Confirm.ask("  Install Python requirements now?", default=True):
            if not install_python_requirements():
                all_ok = False
        else:
            all_ok = False
    else:
        console.print("  Python packages: [green]all present[/green]")

    # 3. Defects4J
    if not is_defects4j_initialized():
        console.print()
        console.print("  [yellow]Defects4J is not initialized.[/yellow]")
        console.print("  This involves: git clone, copy bug data, cpanm, init.sh")
        console.print("  [dim]It takes approximately 5-10 minutes.[/dim]")
        if Confirm.ask("  Install Defects4J now?", default=True):
            if not install_defects4j():
                all_ok = False
        else:
            all_ok = False
    else:
        console.print("  Defects4J: [green]initialized[/green]")

    console.print()
    return all_ok


# ---------------------------------------------------------------------------
# API key setup
# ---------------------------------------------------------------------------

def setup_api_keys() -> str | None:
    """Interactive API key configuration. Returns provider name."""
    from set_api_key import replace_placeholder, set_env_var

    console.print(Rule("API Key Setup", style="bold blue"))
    console.print()
    console.print("  [1] OpenAI (GPT models)")
    console.print("  [2] Anthropic (Claude models)")
    console.print("  [3] Both")
    choice = Prompt.ask("  Provider", choices=["1", "2", "3"], default="1")

    env_files = [
        str(SCRIPT_DIR / ".env"),
        str(SCRIPT_DIR / "autogpt" / ".env"),
    ]
    provider = None

    if choice in ("1", "3"):
        key = Prompt.ask("  OpenAI API key", password=True)
        if key:
            for ef in env_files:
                set_env_var(ef, "OPENAI_API_KEY", key)
            replace_placeholder(str(SCRIPT_DIR / "run.sh"), "GLOBAL-API-KEY-PLACEHOLDER", key)
            token_path = SCRIPT_DIR / "token.txt"
            token_path.write_text(key)
            os.environ["OPENAI_API_KEY"] = key
            console.print("  [green]OpenAI key saved[/green]")
            provider = "openai"

    if choice in ("2", "3"):
        key = Prompt.ask("  Anthropic API key", password=True)
        if key:
            for ef in env_files:
                set_env_var(ef, "ANTHROPIC_API_KEY", key)
            os.environ["ANTHROPIC_API_KEY"] = key
            console.print("  [green]Anthropic key saved[/green]")
            provider = "anthropic" if provider is None else "both"

    console.print()
    return provider


# ---------------------------------------------------------------------------
# Model selection
# ---------------------------------------------------------------------------

def select_model() -> tuple[str, float]:
    """Interactive model picker. Returns (model_id, temperature)."""
    console.print(Rule("Model Selection", style="bold blue"))
    console.print()

    has_openai = _has_api_key("OPENAI_API_KEY")
    has_anthropic = _has_api_key("ANTHROPIC_API_KEY")

    models = []
    if has_openai:
        for name, desc in OPENAI_MODELS:
            models.append((name, desc))
    if has_anthropic:
        for name, desc in ANTHROPIC_MODELS:
            models.append((name, desc))

    if not models:
        console.print("  [red]No API keys configured. Run setup first.[/red]")
        sys.exit(1)

    for i, (name, desc) in enumerate(models, 1):
        console.print(f"  [{i}] {name} — {desc}")
    custom_idx = len(models) + 1
    console.print(f"  [{custom_idx}] Custom model — enter any model name manually")

    idx = IntPrompt.ask("  Select model", default=1)
    idx = max(1, min(idx, custom_idx))

    if idx == custom_idx:
        selected = Prompt.ask("  Model name").strip()
        if not selected:
            console.print("  [red]No model name entered. Aborting.[/red]")
            sys.exit(1)
    else:
        selected = models[idx - 1][0]

    console.print(f"  Selected: [bold]{selected}[/bold]")
    console.print()

    # Temperature prompt
    console.print("  Temperature controls randomness (0.0 = deterministic, 1.0 = creative).")
    console.print("  [dim]Note: some models require a specific value (e.g. o3 requires 1.0).[/dim]")
    temp_str = Prompt.ask("  Temperature", default="0.0")
    try:
        temperature = float(temp_str)
    except ValueError:
        console.print("  [yellow]Invalid value, defaulting to 0.0[/yellow]")
        temperature = 0.0
    console.print(f"  Temperature: [bold]{temperature}[/bold]")
    console.print()

    return selected, temperature


# ---------------------------------------------------------------------------
# Bug selection
# ---------------------------------------------------------------------------

def get_available_projects() -> list[str]:
    """List available Defects4J projects."""
    projects_dir = SCRIPT_DIR / "defects4j" / "framework" / "projects"
    if not projects_dir.exists():
        return []
    return sorted(
        d.name for d in projects_dir.iterdir()
        if d.is_dir() and d.name != "lib"
    )


def get_bug_count(project: str) -> int:
    """Get number of bugs available for a project."""
    patches_dir = SCRIPT_DIR / "defects4j" / "framework" / "projects" / project / "patches"
    if not patches_dir.exists():
        return 0
    return len([p for p in patches_dir.iterdir() if p.suffix == ".src"])


def parse_bugs_string(bugs_str: str) -> list[tuple[str, str]]:
    """Parse comma-separated bugs like 'Chart 1, Math 5'."""
    # Strip surrounding quotes from the whole string (interactive input artifacts)
    bugs_str = bugs_str.strip().strip("\"'")
    bugs = []
    for part in bugs_str.split(","):
        part = part.strip().strip("\"'")
        if not part:
            continue
        tokens = part.split()
        if len(tokens) == 2:
            bugs.append((tokens[0], tokens[1]))
        else:
            console.print(f"  [yellow]Skipping invalid entry: '{part}' (expected 'Project Index')[/yellow]")
    return bugs


def load_bugs_file(path: str) -> list[tuple[str, str]]:
    """Load bugs from a file (one per line: 'Project Index')."""
    bugs = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            tokens = line.split()
            if len(tokens) >= 2:
                bugs.append((tokens[0], tokens[1]))
    return bugs


def select_bugs() -> list[tuple[str, str]]:
    """Interactive bug selection. Returns list of (project, index) tuples."""
    console.print(Rule("Bug Selection", style="bold blue"))
    console.print()
    console.print("  [1] Enter bugs manually (e.g. Chart 1, Math 5)")
    console.print("  [2] Choose a Defects4J project and bug range")
    console.print("  [3] Load from a file")
    choice = Prompt.ask("  Method", choices=["1", "2", "3"], default="1")

    if choice == "1":
        bugs_str = Prompt.ask('  Enter bugs (comma-separated, e.g. "Chart 1, Math 5")')
        bugs = parse_bugs_string(bugs_str)

    elif choice == "2":
        projects = get_available_projects()
        if not projects:
            console.print("  [red]No Defects4J projects found. Is Defects4J initialized?[/red]")
            sys.exit(1)

        console.print()
        # Show projects in columns
        table = Table(show_header=False, box=None, padding=(0, 3))
        table.add_column("col1")
        table.add_column("col2")
        table.add_column("col3")
        rows = []
        for i, p in enumerate(projects, 1):
            count = get_bug_count(p)
            rows.append(f"[{i}] {p} ({count} bugs)")
        # Pad to multiple of 3
        while len(rows) % 3 != 0:
            rows.append("")
        for i in range(0, len(rows), 3):
            table.add_row(rows[i], rows[i + 1] if i + 1 < len(rows) else "", rows[i + 2] if i + 2 < len(rows) else "")
        console.print(table)

        idx = IntPrompt.ask("  Select project", default=1)
        idx = max(1, min(idx, len(projects)))
        project = projects[idx - 1]
        max_bugs = get_bug_count(project)
        console.print(f"  Selected: {project} ({max_bugs} bugs)")

        range_str = Prompt.ask(
            f"  Bug range (e.g. '1-10' or '1,3,5' or 'all')",
            default="1",
        )

        bugs = []
        if range_str.lower() == "all":
            bugs = [(project, str(i)) for i in range(1, max_bugs + 1)]
        elif "-" in range_str:
            parts = range_str.split("-")
            start, end = int(parts[0]), int(parts[1])
            bugs = [(project, str(i)) for i in range(start, end + 1)]
        else:
            for idx_str in range_str.split(","):
                idx_str = idx_str.strip()
                if idx_str:
                    bugs.append((project, idx_str))

    else:  # choice == "3"
        path = Prompt.ask("  Path to bugs file")
        bugs = load_bugs_file(path)

    if not bugs:
        console.print("  [red]No bugs selected.[/red]")
        sys.exit(1)

    console.print(f"  [green]{len(bugs)} bug(s) selected[/green]")
    console.print()
    return bugs


# ---------------------------------------------------------------------------
# Run preparation (replaces shell scripts)
# ---------------------------------------------------------------------------

def setup_defects4j_env():
    """Set up Defects4J PATH and Perl environment."""
    d4j_bin = str(SCRIPT_DIR / "defects4j" / "framework" / "bin")
    if d4j_bin not in os.environ.get("PATH", ""):
        os.environ["PATH"] = d4j_bin + os.pathsep + os.environ.get("PATH", "")

    # Add local cpanm/perl5 lib to PERL5LIB so Defects4J can find modules
    # installed via 'cpanm' as a non-root user (e.g. String::Interpolate).
    home_perl5 = str(Path.home() / "perl5" / "lib" / "perl5")
    current_perl5lib = os.environ.get("PERL5LIB", "")
    if home_perl5 not in current_perl5lib:
        os.environ["PERL5LIB"] = (
            home_perl5 + os.pathsep + current_perl5lib
            if current_perl5lib
            else home_perl5
        )

    # Perl locale setup (replaces bash locale detection loop)
    for lang in ["en_AU.UTF-8", "en_GB.UTF-8", "C.UTF-8", "C"]:
        try:
            locale.setlocale(locale.LC_ALL, lang)
            os.environ["LANG"] = lang
            break
        except locale.Error:
            continue
    os.environ["LC_COLLATE"] = "C"


def generate_commands_descriptions():
    """Generate commands_by_state.json (replaces construct_commands_descriptions.py)."""
    # Run the script as a subprocess to keep it simple and avoid import issues
    subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "construct_commands_descriptions.py")],
        cwd=str(SCRIPT_DIR),
        check=True,
    )


def increment_experiment() -> str:
    """Create new experiment folder and return its path."""
    exp_list_path = SCRIPT_DIR / "experimental_setups" / "experiments_list.txt"
    exp_list_path.parent.mkdir(parents=True, exist_ok=True)

    if exp_list_path.exists():
        exps = exp_list_path.read_text().strip().splitlines()
        last_exp = int(exps[-1].split("_")[1]) if exps else 0
    else:
        exp_list_path.write_text("")
        last_exp = 0

    new_exp = last_exp + 1
    exp_name = f"experiment_{new_exp}"
    exp_dir = SCRIPT_DIR / "experimental_setups" / exp_name

    with open(exp_list_path, "a") as f:
        f.write(f"{exp_name}\n")

    for subdir in ["logs", "responses", "external_fixes", "saved_contexts", "mutations_history", "plausible_patches"]:
        (exp_dir / subdir).mkdir(parents=True, exist_ok=True)

    return str(exp_dir)


def prepare_ai_settings(project: str, bug_index: str):
    """Generate ai_settings.yaml for a specific bug."""
    settings = AI_SETTINGS_TEMPLATE.format(
        name=project, bug_index=bug_index, version=AGENT_VERSION
    )
    (SCRIPT_DIR / "ai_settings.yaml").write_text(settings)


def checkout_bug(project: str, bug_index: str):
    """Check out a buggy project version from Defects4J."""
    write_to = SCRIPT_DIR / "auto_gpt_workspace" / f"{project.lower()}_{bug_index}_buggy"
    cmd = f"defects4j checkout -p {project} -v {bug_index}b -w {write_to}"
    try:
        subprocess.run(cmd, shell=True, check=True, cwd=str(SCRIPT_DIR))
    except subprocess.CalledProcessError as e:
        console.print(f"  [red]Checkout failed: {e}[/red]")
        raise


def run_single_bug(project: str, bug_index: str, model: str, hyperparams_file: str, max_cycles: int, temperature: float = 0.0):
    """Run RepairAgent on a single bug."""
    prepare_ai_settings(project, bug_index)
    checkout_bug(project, bug_index)

    os.environ["TEMPERATURE"] = str(temperature)

    from autogpt.app.main import run_auto_gpt

    run_auto_gpt(
        continuous=True,
        continuous_limit=max_cycles,
        ai_settings="ai_settings.yaml",
        prompt_settings=None,
        skip_reprompt=True,
        speak=False,
        debug=False,
        gpt3only=False,
        gpt4only=False,
        memory_type="json_file",
        browser_name=None,
        allow_downloads=False,
        skip_news=True,
        working_directory=SCRIPT_DIR,
        workspace_directory=None,
        install_plugin_deps=False,
        experiment_file=hyperparams_file,
        model=model,
    )


# ---------------------------------------------------------------------------
# Docker support
# ---------------------------------------------------------------------------

def build_docker_image():
    """Build the RepairAgent Docker image."""
    console.print("  Building Docker image...")
    subprocess.run(
        ["docker", "build", "-t", "repairagent", "."],
        cwd=str(SCRIPT_DIR),
        check=True,
    )
    console.print("  [green]Docker image built successfully[/green]")


def run_in_docker(bugs: list[tuple[str, str]], model: str, hyperparams: str, max_cycles: int, temperature: float = 0.0):
    """Run RepairAgent inside a Docker container."""
    if not shutil.which("docker"):
        console.print("  [red]Docker not found. Please install Docker first.[/red]")
        sys.exit(1)

    # Check if image exists
    result = subprocess.run(
        ["docker", "images", "-q", "repairagent"],
        capture_output=True, text=True,
    )
    if not result.stdout.strip():
        if Confirm.ask("  Docker image not found. Build it now?", default=True):
            build_docker_image()
        else:
            sys.exit(1)

    # Write temporary bugs file
    tmp_bugs = SCRIPT_DIR / ".tmp_bugs_list"
    tmp_bugs.write_text("\n".join(f"{p} {i}" for p, i in bugs))

    bugs_str = ",".join(f"{p} {i}" for p, i in bugs)

    # Load API keys from .env files if not already in environment
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not openai_key or not anthropic_key:
        for env_file in [SCRIPT_DIR / ".env", SCRIPT_DIR / "autogpt" / ".env"]:
            if env_file.exists():
                for line in env_file.read_text().splitlines():
                    line = line.strip()
                    if "=" not in line or line.startswith("#"):
                        continue
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip()
                    if k == "OPENAI_API_KEY" and not openai_key and v != "GLOBAL-API-KEY-PLACEHOLDER":
                        openai_key = v
                    elif k == "ANTHROPIC_API_KEY" and not anthropic_key and v != "GLOBAL-API-KEY-PLACEHOLDER":
                        anthropic_key = v

    cmd = [
        "docker", "run", "--rm",
        "-e", f"OPENAI_API_KEY={openai_key}",
        "-e", f"ANTHROPIC_API_KEY={anthropic_key}",
        "-e", f"TEMPERATURE={temperature}",
        "-v", f"{SCRIPT_DIR}:/app",
        "-w", "/app",
        "repairagent",
        "run",
        "--bugs", bugs_str,
        "--model", model,
        "--temperature", str(temperature),
        "--hyperparams", hyperparams,
        "--max-cycles", str(max_cycles),
    ]

    try:
        subprocess.run(cmd, check=True)
    finally:
        tmp_bugs.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Main execution flow
# ---------------------------------------------------------------------------

def execute_run(bugs: list[tuple[str, str]], model: str, hyperparams: str, max_cycles: int, temperature: float = 0.0):
    """Prepare environment and run on all bugs sequentially."""
    setup_defects4j_env()

    # Pre-flight: verify Defects4J is available
    if not shutil.which("defects4j"):
        console.print("  [red]Defects4J is not available on PATH.[/red]")
        console.print("  Install it first, or use Docker mode (--docker).")
        console.print("  See: https://github.com/rjust/defects4j#steps-to-set-up-defects4j")
        sys.exit(1)

    generate_commands_descriptions()
    exp_dir = increment_experiment()

    console.print(Rule("Running RepairAgent", style="bold green"))
    console.print(f"  Experiment dir: {exp_dir}")
    console.print()

    results = []
    for i, (project, bug_index) in enumerate(bugs, 1):
        console.print(Rule(f"[{i}/{len(bugs)}] {project} {bug_index}", style="bold cyan"))
        try:
            run_single_bug(project, bug_index, model, hyperparams, max_cycles, temperature)
            results.append((project, bug_index, "OK"))
            console.print(f"  [green]{project} {bug_index} completed[/green]")
        except SystemExit as e:
            # task_complete() calls quit() → SystemExit(0): normal agent finish.
            # sys.exit(1) means a fatal setup error — re-raise to abort the run.
            if e.code == 0 or e.code is None:
                results.append((project, bug_index, "OK"))
                console.print(f"  [green]{project} {bug_index} completed[/green]")
            else:
                raise
        except Exception as e:
            results.append((project, bug_index, f"FAILED: {e}"))
            console.print(f"  [red]{project} {bug_index} failed: {e}[/red]")

    # Summary
    console.print()
    console.print(Rule("Results Summary", style="bold blue"))
    summary_table = Table(show_header=True, box=None, padding=(0, 2))
    summary_table.add_column("Bug", style="bold")
    summary_table.add_column("Status")
    for project, bug_index, status in results:
        style = "green" if status == "OK" else "red"
        summary_table.add_row(f"{project} {bug_index}", f"[{style}]{status}[/{style}]")
    console.print(summary_table)
    console.print()

    ok_count = sum(1 for _, _, s in results if s == "OK")
    console.print(f"  {ok_count}/{len(results)} bugs completed successfully.")
    console.print(f"  Results saved to: {exp_dir}")


# ---------------------------------------------------------------------------
# Interactive wizard
# ---------------------------------------------------------------------------

def interactive_run():
    """Full guided interactive experience."""
    console.print()
    console.print(Panel(
        f"[bold]RepairAgent v{AGENT_VERSION}[/bold]\n"
        "Autonomous LLM-powered bug repair for Java projects",
        border_style="blue",
        expand=False,
    ))

    # 1. Environment check
    checks = check_environment()
    display_environment(checks)

    # 1b. Offer to install missing dependencies (excluding API key — handled separately)
    missing = [name for name, (ok, _) in checks.items() if not ok and name != "API key"]
    if missing:
        console.print(f"  [yellow]Missing: {', '.join(missing)}[/yellow]")
        if Confirm.ask("  Would you like to install missing dependencies?", default=True):
            install_all_dependencies()
            # Re-check after installation
            checks = check_environment()
            display_environment(checks)

    # 2. API key setup if needed
    if not checks["API key"][0]:
        setup_api_keys()

    # 3. Container choice (skip if already in container)
    use_docker = False
    if not is_in_container() and shutil.which("docker"):
        console.print(Rule("Execution Mode", style="bold blue"))
        console.print()
        console.print("  [1] Run locally (recommended if dependencies are installed)")
        console.print("  [2] Run in Docker container")
        mode = Prompt.ask("  Mode", choices=["1", "2"], default="1")
        use_docker = mode == "2"
        console.print()

    # 4. Model selection
    model, temperature = select_model()

    # 5. Bug selection
    bugs = select_bugs()

    # 6. Configuration
    console.print(Rule("Configuration", style="bold blue"))
    console.print()
    max_cycles = IntPrompt.ask("  Max cycles per bug", default=40)
    hyperparams = str(SCRIPT_DIR / "hyperparams.json")
    console.print(f"  Hyperparameters: {hyperparams}")
    console.print()

    # 7. Summary and confirmation
    console.print(Rule("Ready", style="bold green"))
    console.print()
    console.print(f"  Model: [bold]{model}[/bold]")
    console.print(f"  Temperature: [bold]{temperature}[/bold]")
    console.print(f"  Bugs:  [bold]{len(bugs)}[/bold]")
    for project, bug_index in bugs:
        console.print(f"    - {project} {bug_index}")
    console.print(f"  Max cycles: [bold]{max_cycles}[/bold]")
    console.print(f"  Docker: [bold]{'yes' if use_docker else 'no'}[/bold]")
    console.print()

    if not Confirm.ask("  Start?", default=True):
        console.print("  Aborted.")
        return

    # 8. Execute
    if use_docker:
        run_in_docker(bugs, model, hyperparams, max_cycles, temperature)
    else:
        execute_run(bugs, model, hyperparams, max_cycles, temperature)


# ---------------------------------------------------------------------------
# CLI definition
# ---------------------------------------------------------------------------

@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """RepairAgent -- Autonomous LLM-powered bug repair for Java projects."""
    if ctx.invoked_subcommand is None:
        interactive_run()


@cli.command()
@click.option("--bugs", default=None, help='Comma-separated bugs, e.g. "Chart 1,Math 5"')
@click.option("--bugs-file", type=click.Path(exists=True), default=None, help="Path to bugs list file")
@click.option("--model", default="gpt-4o-mini", help="LLM model name")
@click.option("--temperature", default=0.0, type=float, help="LLM temperature (0.0–2.0)")
@click.option("--hyperparams", default=None, help="Hyperparams JSON file path")
@click.option("--max-cycles", default=40, type=int, help="Max agent cycles per bug")
@click.option("--docker", is_flag=True, help="Run inside Docker container")
def run(bugs, bugs_file, model, temperature, hyperparams, max_cycles, docker):
    """Run RepairAgent on one or more bugs."""
    if hyperparams is None:
        hyperparams = str(SCRIPT_DIR / "hyperparams.json")

    # Parse bugs
    if bugs:
        bug_list = parse_bugs_string(bugs)
    elif bugs_file:
        bug_list = load_bugs_file(bugs_file)
    else:
        # Fall back to interactive bug selection
        bug_list = select_bugs()

    if not bug_list:
        console.print("[red]No bugs specified. Use --bugs or --bugs-file.[/red]")
        sys.exit(1)

    console.print(f"  Model: [bold]{model}[/bold]")
    console.print(f"  Temperature: [bold]{temperature}[/bold]")
    console.print(f"  Bugs: [bold]{len(bug_list)}[/bold]")
    console.print(f"  Max cycles: [bold]{max_cycles}[/bold]")
    console.print()

    if docker:
        run_in_docker(bug_list, model, hyperparams, max_cycles, temperature)
    else:
        execute_run(bug_list, model, hyperparams, max_cycles, temperature)


@cli.command()
@click.option("--docker", is_flag=True, help="Build Docker image for RepairAgent")
@click.option("--install-deps", is_flag=True, help="Install all missing dependencies")
def setup(docker, install_deps):
    """Check environment, install dependencies, and configure API keys."""
    checks = check_environment()
    display_environment(checks)

    if docker:
        build_docker_image()
        return

    # Determine what is missing (excluding API key, handled separately)
    missing = [name for name, (ok, _) in checks.items() if not ok and name != "API key"]

    if missing or install_deps:
        if missing:
            console.print(f"  [yellow]Missing: {', '.join(missing)}[/yellow]")
        if install_deps or Confirm.ask("  Install missing dependencies?", default=True):
            install_all_dependencies()
            # Re-check after installation
            checks = check_environment()
            display_environment(checks)

    # API key setup
    if not checks["API key"][0]:
        if Confirm.ask("  Configure API keys now?", default=True):
            setup_api_keys()
    else:
        console.print("  [green]API keys already configured.[/green]")
        if Confirm.ask("  Reconfigure?", default=False):
            setup_api_keys()

    # Final status
    checks = check_environment()
    missing = [name for name, (ok, _) in checks.items() if not ok]
    if missing:
        console.print()
        console.print(f"  [yellow]Still missing: {', '.join(missing)}[/yellow]")
    else:
        console.print()
        console.print("  [green]All checks passed! You can now run:[/green]")
        console.print("    python3 repairagent.py run --bugs 'Chart 1' --model gpt-4o-mini")


if __name__ == "__main__":
    cli()
