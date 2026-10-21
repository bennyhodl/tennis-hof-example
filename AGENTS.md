# Notes for coding agents

This repo ranks ATP players for the International Tennis Hall of Fame. The
people working in it are mathematics students who are new to Git and Python
tooling. Explain what you do in plain words, and teach the workflow rather
than hide it.

## Commands

- `uv run hof check` runs lint, format and tests. Run it before every push; it is what CI runs.
- `uv run hof check --fix` fixes lint and formatting.
- `uv run hof run --out results/x` runs the method.
- `uv run hof diff results/a results/b` compares two runs.
- `uv run hof doctor` diagnoses the environment. Run it first when something fails to run.

Always use `uv run`. Never `pip install`; add dependencies with `uv add <pkg>`
(or `uv add --dev <pkg>`), which updates `pyproject.toml` and `uv.lock`.

## Workflow

- Never commit to `main`. Branch, push, `gh pr create`. Fill in the PR template,
  including the prediction of what the rankings will do.
- One idea per PR. A refactor and a method change are two PRs, so the report
  comment shows the effect of each.
- If the golden test fails because the method changed on purpose, regenerate it
  with `uv run pytest --force-regen` and commit the new files. If you did not
  mean to change the method, the failure is a bug: fix the code.
- Never skip, weaken or delete a test to make CI pass. Stop and explain instead.

## Code

- The method lives in `src/hof/`. Notebooks only import from it.
- Every number in the paper comes from `paper.py`; never hard-code results in `.tex`.
- The team uses macOS and Windows: use `pathlib`, pass `encoding="utf-8"` to every
  `open`/`read_text`/`write_text`, and write CSVs with `lineterminator="\n"`.
- Keep it plain: pandas, functions, a dataclass when needed. No frameworks.
