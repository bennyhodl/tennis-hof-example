"""Developer environment: set it up, diagnose it, and run the same checks CI runs."""

import shutil
import subprocess
import sys
from collections.abc import Callable

from hof import data, paper


def _out(*cmd: str) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, cwd=data.ROOT).stdout.strip()
    except FileNotFoundError:
        return ""


def _ok(*cmd: str) -> bool:
    try:
        return subprocess.run(cmd, capture_output=True, cwd=data.ROOT).returncode == 0
    except FileNotFoundError:
        return False


def _snapshot_ok() -> bool:
    snap = data.pinned()
    marker = snap.path / ".sha256"
    return marker.exists() and marker.read_text(encoding="utf-8") == snap.sha256


# (what we check, how to check it, how to fix it)
CHECKS: list[tuple[str, Callable[[], bool], str]] = [
    (
        "git is installed",
        lambda: shutil.which("git") is not None,
        "Install Git: winget install --id Git.Git -e   (then open a new terminal)",
    ),
    (
        "git knows your name",
        lambda: bool(_out("git", "config", "user.name")),
        'git config --global user.name "Your Name"',
    ),
    (
        "git knows your email",
        lambda: bool(_out("git", "config", "user.email")),
        'git config --global user.email "you@example.com"   (the email on your GitHub account)',
    ),
    (
        "GitHub CLI is installed",
        lambda: shutil.which("gh") is not None,
        "Install it: winget install --id GitHub.cli -e   (then open a new terminal)",
    ),
    ("GitHub CLI is logged in", lambda: _ok("gh", "auth", "status"), "gh auth login"),
    (
        "pre-commit hook is installed",
        lambda: (data.ROOT / _out("git", "rev-parse", "--git-path", "hooks/pre-commit")).is_file(),
        "uv run hof setup",
    ),
    ("data snapshot is downloaded and verified", _snapshot_ok, "uv run hof setup"),
    (
        "Tectonic (LaTeX) is available",
        lambda: paper.tectonic(install=False) is not None,
        "uv run hof setup",
    ),
]


def doctor() -> int:
    failed = 0
    for name, check, fix in CHECKS:
        if check():
            print(f"[ok] {name}")
        else:
            failed += 1
            print(f"[!!] {name}\n     fix: {fix}")
    branch = _out("git", "branch", "--show-current")
    if branch == "main":
        print("\nYou are on main. Start new work on a branch: git switch -c my-change")
    print(
        "\nAll good."
        if not failed
        else f"\n{failed} problem(s). Run each fix, then run this again."
    )
    return 1 if failed else 0


def setup() -> int:
    print("Installing the pre-commit hook...", flush=True)
    subprocess.run([sys.executable, "-m", "pre_commit", "install"], check=True, cwd=data.ROOT)
    snap = data.pinned()
    print(f"Downloading data snapshot {snap.name}...", flush=True)
    data.fetch(snap)
    print("Downloading Tectonic (LaTeX)...", flush=True)
    paper.tectonic()
    print()
    return doctor()


def check(fix: bool = False) -> int:
    """Lint, format and test: exactly what CI runs."""
    steps = [
        ["ruff", "check", *(["--fix"] if fix else [])],
        ["ruff", "format", *([] if fix else ["--check"])],
        ["pytest"],
    ]
    failed = []
    for step in steps:
        print(f"\n$ {' '.join(step)}", flush=True)
        if subprocess.run([sys.executable, "-m", *step], cwd=data.ROOT).returncode:
            failed.append(step[0])
    if failed:
        print(f"\nFailed: {', '.join(failed)}. Try `uv run hof check --fix` for lint and format.")
    return 1 if failed else 0
