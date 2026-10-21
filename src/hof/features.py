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
    m, r = ds.matches, ds.rankings
    ids = pd.Index(ds.players["player_id"], name="player_id")

    def count(s: pd.Series) -> pd.Series:
        return s.value_counts().reindex(ids, fill_value=0)

    year = m["tourney_date"] // 10000
    played = pd.DataFrame(
        {"player_id": pd.concat([m["winner_id"], m["loser_id"]]), "year": pd.concat([year, year])}
    )
    span = played.groupby("player_id")["year"].agg(["min", "max"]).reindex(ids, fill_value=0)
    finals = m[m["round"] == "F"]
    slam_finals = finals[finals["tourney_level"] == "G"]

    df = pd.DataFrame(index=ids)
    df["slams"] = count(slam_finals["winner_id"])
    df["slam_finals"] = count(pd.concat([slam_finals["winner_id"], slam_finals["loser_id"]]))
    df["masters"] = count(finals.loc[finals["tourney_level"] == "M", "winner_id"])
    df["tour_finals"] = count(finals.loc[finals["tourney_level"] == "F", "winner_id"])
    df["titles"] = count(finals["winner_id"])
    df["wins"] = count(m["winner_id"])
    df["losses"] = count(m["loser_id"])
    played_any = (df["wins"] + df["losses"]).where(lambda n: n > 0)
    df["win_pct"] = (df["wins"] / played_any).fillna(0.0)
    df["weeks_no1"] = count(r.loc[r["rank"] == 1, "player_id"])
    df["weeks_top10"] = count(r["player_id"])
    df["first_year"] = span["min"]
    df["last_year"] = span["max"]
    return df[COLUMNS]
