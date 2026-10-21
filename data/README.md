# Data

The data is not in git. `data/snapshot.toml` pins one snapshot by URL and
`revision` (the zip's SHA-256); `uv run hof setup` downloads it to
`data/raw/<name>/` and refuses it if the hash does not match. Each run records
which snapshot it used. Only `src/hof/data.py` knows how snapshots are stored.

## Changing the snapshot

1. Build the new files: `matches.csv`, `players.csv`, `rankings.csv`, `inductees.csv`
   (see the schemas in `src/hof/data.py`).
2. Zip them and attach the zip to a new GitHub release named `data-<name>`.
3. Update `snapshot.toml` with the new name, URL and the zip's SHA-256 as `revision`.
4. Open a PR that changes only the snapshot. The report will warn that the data changed.

## Current snapshot

`synthetic-v1`: 1,500 made-up players, 1968–2024, from
`uv run python scripts/make_synthetic_data.py --out data/raw/synthetic-v1`.
Not real players. A stand-in until the team chooses a real source.
