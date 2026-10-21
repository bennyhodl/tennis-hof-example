"""Generate a synthetic ATP-style dataset.

Stands in for real data until the team picks a source. The output has the same
shape as Jeff Sackmann's tennis_atp files (matches, players, weekly rankings)
plus a simulated Hall of Fame vote, so the pipeline does not care which it gets.

    uv run python scripts/make_synthetic_data.py --out data/raw/synthetic-v1
    uv run python scripts/make_synthetic_data.py --out tests/fixtures/data \
        --players 80 --first-year 1990 --majors-only --seed 7
"""

import argparse
import heapq
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

FIRST = "Andre Bjorn Boris Carlos Diego Evan Felix Goran Hugo Ivan Jonas Karl Luca Marat Nikos Omar Pete Rafa Stan Tomas Uli Viktor Yannick Zeke".split()  # noqa: E501
LAST = "Arden Basso Castell Dreyer Ekberg Faure Gallo Holt Ilic Jansen Kovac Lund Moreau Novak Ortiz Pavel Quist Rosen Sato Toft Ueda Varga Wolfe Yates Zorin".split()  # noqa: E501

ROUNDS = {128: "R128", 64: "R64", 32: "R32", 16: "R16", 8: "QF", 4: "SF", 2: "F"}
# Ranking points for the round a player lost in ("W" = won the event).
POINTS = {
    "G": {"W": 2000, "F": 1200, "SF": 720, "QF": 360, "R16": 180, "R32": 90, "R64": 45, "R128": 10},
    "M": {"W": 1000, "F": 600, "SF": 360, "QF": 180, "R16": 90, "R32": 45, "R64": 10},
    "F": {"W": 1500, "F": 1000, "SF": 400, "QF": 200},
    "A": {"W": 250, "F": 150, "SF": 90, "QF": 45, "R16": 20, "R32": 0},
}


def calendar(year: int, majors_only: bool) -> list[tuple[int, str, str, int]]:
    """(week, name, level, max draw) for every event in a season."""
    events = [
        (3, "Australian Open", "G", 128),
        (22, "Roland Garros", "G", 128),
        (27, "Wimbledon", "G", 128),
        (35, "US Open", "G", 128),
        (46, "Tour Finals", "F", 8),
    ]
    masters_weeks = [10, 12, 15, 18, 19, 31, 32, 41, 44]
    level = "M" if year >= 1990 else "A"
    events += [
        (w, f"Masters {i + 1}", level, 64 if level == "M" else 32)
        for i, w in enumerate(masters_weeks)
    ]
    if majors_only:
        return sorted(events)
    events += [
        (w, f"Open {w}", "A", 32)
        for w in (1, 5, 7, 9, 14, 24, 26, 29, 33, 37, 39, 40, 42, 43, 45, 48)
    ]
    return sorted(events)


def generate(
    players: int, first_year: int, last_year: int, seed: int, majors_only: bool = False
) -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    birth = rng.integers(first_year - 30, last_year - 17, players)
    skill = rng.normal(0, 1, players)
    debut = rng.integers(17, 22, players)
    retire = np.clip(rng.normal(31, 3, players), 23, 38).astype(int)
    combos = len(FIRST) * len(LAST)
    names = [
        f"{FIRST[i % len(FIRST)]} {chr(65 + i // combos)}. {LAST[i // len(FIRST) % len(LAST)]}"
        for i in range(players)
    ]

    matches: list[tuple] = []
    point_events: dict[int, list[tuple[int, int]]] = defaultdict(
        list
    )  # week index -> (player, pts)
    for year in range(first_year, last_year + 1):
        age = year - birth
        active = np.flatnonzero((age >= debut) & (age <= retire))
        strength = skill - 0.012 * (age - 26) ** 2
        for week, name, level, max_draw in calendar(year, majors_only):
            draw = min(max_draw, 1 << (len(active).bit_length() - 1))
            noisy = strength[active] + rng.normal(0, 0.4, len(active))
            alive = list(active[np.argsort(-noisy)[:draw]])
            rng.shuffle(alive)
            start = date(year, 1, 1) + timedelta(weeks=week)
            tourney_id = f"{year}-{week:02d}"
            while len(alive) > 1:
                rnd = ROUNDS[len(alive)]
                winners = []
                for a, b in zip(alive[::2], alive[1::2], strict=True):
                    p = 1 / (1 + np.exp(-1.6 * (strength[a] - strength[b])))
                    w, lose = (a, b) if rng.random() < p else (b, a)
                    winners.append(w)
                    matches.append(
                        (
                            tourney_id,
                            name,
                            level,
                            int(start.strftime("%Y%m%d")),
                            rnd,
                            int(w),
                            int(lose),
                        )
                    )
                    point_events[(year - first_year) * 52 + week].append(
                        (int(lose), POINTS[level][rnd])
                    )
                alive = winners
            point_events[(year - first_year) * 52 + week].append(
                (int(alive[0]), POINTS[level]["W"])
            )

    rankings = []
    rolling: dict[int, int] = defaultdict(int)
    for w in range((last_year - first_year + 1) * 52):
        for p, pts in point_events.get(w, []):
            rolling[p] += pts
        for p, pts in point_events.get(w - 52, []):
            rolling[p] -= pts
        day = date(first_year + w // 52, 1, 1) + timedelta(weeks=w % 52)
        top = heapq.nlargest(10, rolling.items(), key=lambda kv: (kv[1], -kv[0]))
        rankings += [
            (int(day.strftime("%Y%m%d")), r + 1, p, pts)
            for r, (p, pts) in enumerate(top)
            if pts > 0
        ]

    m = pd.DataFrame(
        matches,
        columns=[
            "tourney_id",
            "tourney_name",
            "tourney_level",
            "tourney_date",
            "round",
            "winner_id",
            "loser_id",
        ],
    )
    r = pd.DataFrame(rankings, columns=["ranking_date", "rank", "player_id", "points"])
    p = pd.DataFrame({"player_id": range(players), "name": names, "birth_year": birth})
    return {
        "matches": m,
        "players": p,
        "rankings": r,
        "inductees": simulate_vote(m, r, players, last_year, rng),
    }


def simulate_vote(
    m: pd.DataFrame, r: pd.DataFrame, players: int, last_year: int, rng: np.random.Generator
) -> pd.DataFrame:
    """Voters weigh careers a little differently from any model, plus noise."""
    final = m[m["round"] == "F"]
    titles = final.groupby(["winner_id", "tourney_level"]).size().unstack(fill_value=0)
    titles = titles.reindex(range(players), fill_value=0)
    weeks_no1 = r[r["rank"] == 1].groupby("player_id").size().reindex(range(players), fill_value=0)
    played = pd.concat(
        [
            m[["winner_id", "tourney_date"]].set_axis(["p", "d"], axis=1),
            m[["loser_id", "tourney_date"]].set_axis(["p", "d"], axis=1),
        ]
    )
    last = (played.groupby("p")["d"].max() // 10000).reindex(range(players))
    score = (
        titles.get("G", 0) * 1.0
        + titles.get("M", 0) * 0.25
        + titles.get("F", 0) * 0.4
        + titles.get("A", 0) * 0.04
        + weeks_no1 * 0.015
        + rng.normal(0, 1.2, players)
    )  # reputation, era, and everything not in the data
    year = last + 5 + rng.geometric(0.6, players) - 1
    voted = (score >= 4.5) & (year <= last_year + 1)
    out = pd.DataFrame({"player_id": range(players), "induction_year": year})[voted.to_numpy()]
    return out.astype(int).reset_index(drop=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--players", type=int, default=1500)
    ap.add_argument("--first-year", type=int, default=1968)
    ap.add_argument("--last-year", type=int, default=2024)
    ap.add_argument("--seed", type=int, default=1968)
    ap.add_argument("--majors-only", action="store_true", help="skip small events (for fixtures)")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    for name, df in generate(
        args.players, args.first_year, args.last_year, args.seed, args.majors_only
    ).items():
        df.to_csv(args.out / f"{name}.csv", index=False, lineterminator="\n")
        print(f"{name}: {len(df):,} rows")


if __name__ == "__main__":
    main()
