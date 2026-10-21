"""Career statistics for every player, one row per player."""

import pandas as pd

from hof.data import Dataset

COLUMNS = [
    "slams",
    "slam_finals",
    "masters",
    "tour_finals",
    "titles",
    "wins",
    "losses",
    "win_pct",
    "weeks_no1",
    "weeks_top10",
    "first_year",
    "last_year",
]


def career_stats(ds: Dataset) -> pd.DataFrame:
    stats = {pid: dict.fromkeys(COLUMNS, 0) for pid in ds.players["player_id"]}
    for _, m in ds.matches.iterrows():
        year = m["tourney_date"] // 10000
        for pid, won in ((m["winner_id"], True), (m["loser_id"], False)):
            s = stats[pid]
            s["wins" if won else "losses"] += 1
            s["first_year"] = min(s["first_year"] or year, year)
            s["last_year"] = max(s["last_year"], year)
        if m["round"] == "F":
            w = stats[m["winner_id"]]
            w["titles"] += 1
            if m["tourney_level"] == "G":
                w["slams"] += 1
                w["slam_finals"] += 1
                stats[m["loser_id"]]["slam_finals"] += 1
            elif m["tourney_level"] == "M":
                w["masters"] += 1
            elif m["tourney_level"] == "F":
                w["tour_finals"] += 1
    for _, r in ds.rankings.iterrows():
        s = stats[r["player_id"]]
        s["weeks_top10"] += 1
        if r["rank"] == 1:
            s["weeks_no1"] += 1

    df = pd.DataFrame.from_dict(stats, orient="index")
    df["win_pct"] = df["wins"] / (df["wins"] + df["losses"]).where(lambda n: n > 0)
    df["win_pct"] = df["win_pct"].fillna(0.0)
    df.index.name = "player_id"
    return df[COLUMNS]
