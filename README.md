# Tennis Hall of Fame ranking (example repo)

An example of how to set up a research project as a team: rank ATP players for
the International Tennis Hall of Fame, test the method against real inductions,
and write the paper. Every change goes through a pull request, and every pull
request gets a report showing what it did to the rankings.

> [!IMPORTANT]
> The data here is **synthetic**: made-up players from
> `scripts/make_synthetic_data.py`. The structure is real; the numbers are not.

**Latest paper:** [paper.pdf](https://github.com/bennyhodl/tennis-hof-example/releases/download/latest/paper.pdf) ·
**Latest rankings:** [rankings.csv](https://github.com/bennyhodl/tennis-hof-example/releases/download/latest/rankings.csv)

## First-time setup

### Windows

1. Open **PowerShell** and install Git and the GitHub CLI:
   ```powershell
   winget install --id Git.Git -e
   winget install --id GitHub.cli -e
   ```
2. Close PowerShell, open a new one, and log in to GitHub:
   ```powershell
   gh auth login
   ```
3. Clone the repo and run the setup script:
   ```powershell
   gh repo clone bennyhodl/tennis-hof-example
   cd tennis-hof-example
   powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
   ```

The script installs [uv](https://docs.astral.sh/uv/), which installs the right
Python and every package. You never install Python yourself. At the end it runs
`hof doctor`, which lists anything still missing and the exact command to fix it.

### macOS or Linux

```bash
gh repo clone bennyhodl/tennis-hof-example && cd tennis-hof-example
bash scripts/setup.sh
```

### Nothing works on my machine

Open the repo on GitHub → **Code** → **Codespaces** → **Create codespace on main**.
You get VS Code in the browser with everything already installed.

## Daily loop

```bash
git switch main && git pull          # 1. start from the latest main
git switch -c better-slam-weights    # 2. a branch for one idea
# ... edit code ...
uv run hof check                     # 3. lint, format and tests: what CI runs
git add -A && git commit -m "Weight Slam finals by round reached"
git push -u origin HEAD              # 4. push your branch
gh pr create --fill                  # 5. open a pull request
```

Then wait a few minutes. CI runs the checks, and a bot comment appears on your
PR with the **Hall of Fame report**: who crossed the line, who moved, how the
method now scores against real inductions, and how long it took. A teammate
reviews, and you **squash and merge**.

You can't push to `main` or merge without a passing CI run and one approval.
That is on purpose.

## Commands

Everything goes through one command, `hof`. Run `uv run hof --help`.

| Command | What it does |
|---|---|
| `uv run hof setup` | First-time setup: git hook, data snapshot, LaTeX |
| `uv run hof doctor` | Checks your machine and tells you how to fix what is wrong |
| `uv run hof check` | Lint, format and tests. Same as CI. Add `--fix` to auto-fix style |
| `uv run hof run` | Runs the method; writes `results/rankings.csv` and `results/metrics.json` |
| `uv run hof diff A B` | Compares two runs. This is the PR report, locally |
| `uv run hof paper` | Builds `paper/build/main.pdf` from the latest run |

To see what your branch does before you push (commit first):

```bash
git switch main && uv run hof run --out results/main
git switch -    && uv run hof run --out results/mine
uv run hof diff results/main results/mine
```

## What CI does

| Workflow | When | Blocks merge? |
|---|---|---|
| **CI / check** | Every PR, on Linux and Windows | Yes |
| **CI / setup script** | Every PR: runs the setup script from scratch | No |
| **Report** | Every PR: runs main and the PR, posts the comparison | No |
| **Publish** | Every merge to main: rebuilds the paper and rankings | — |

## Layout

```
src/hof/            the method, as a Python package
  data.py             the pinned data snapshot: fetch, validate, load
  features.py         career statistics per player
  model.py            the score, the Hall of Fame threshold, the ITHF baseline rule
  evaluate.py         precision, recall, F1, AUC against real inductions
  pipeline.py         runs it all, times each stage, writes results/
  report.py           compares two runs (the PR comment)
  paper.py            writes paper/generated/ and builds the PDF
tests/              what must stay true; see the docstring in each file
  fixtures/data/      a small frozen dataset the tests run on
  test_pipeline/      golden files: the expected rankings on the fixture
data/snapshot.toml  which data snapshot we use (URL + SHA-256)
paper/main.tex      the paper; numbers come from paper/generated/results.tex
scripts/            setup scripts and the synthetic data generator
```

## Rules of thumb

- **Logic lives in `src/hof/`.** Notebooks are for looking at results; they
  import from `hof` and hold no logic. Outputs are stripped on commit.
- **Never type a number into the paper.** Add it to `paper.py` and `\input` it.
- **A method change changes the golden files.** If `test_rankings_match_golden_file`
  fails and you meant it, run `uv run pytest --force-regen` and commit the
  result. Reviewers read that diff.
- **Write your prediction in the PR before reading the report.** The interesting
  PRs are the ones where you were wrong.
- **A PR that makes the method worse is still a result.** Close it with a note
  saying what you learned; it may go in the paper.

## License

Code: MIT. Synthetic data: public domain.
