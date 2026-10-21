"""Career statistics for every player, one row per player."""

import pandas as pd

from hof.data import Dataset

ROUND_ORDER = {"R128": 0, "R64": 1, "R32": 2, "R16": 3, "QF": 4, "SF": 5, "F": 6}
ELO_K = 32

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
    "peak_elo",
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
    df["peak_elo"] = peak_elo(m).reindex(ids, fill_value=0.0).round(1)
    df["first_year"] = span["min"]
    df["last_year"] = span["max"]
    return df[COLUMNS]


def peak_elo(matches: pd.DataFrame) -> pd.Series:
    """Highest Elo rating each player reached, relative to a debutant (who starts at 0).

    Elo rewards beating strong opponents, which title counts miss: a final lost
    to the best player of the era is worth more than a title won against nobody.
    """
    order = matches.assign(r=matches["round"].map(ROUND_ORDER)).sort_values(
        ["tourney_date", "r", "tourney_id"], kind="stable"
    )
    rating: dict[int, float] = {}
    peak: dict[int, float] = {}
    for w, lo in zip(order["winner_id"], order["loser_id"], strict=True):
        rw, rl = rating.get(w, 0.0), rating.get(lo, 0.0)
        gain = ELO_K * (1 - 1 / (1 + 10 ** ((rl - rw) / 400)))
        rating[w], rating[lo] = rw + gain, rl - gain
        peak[w] = max(peak.get(w, 0.0), rating[w])
    return pd.Series(peak, dtype=float)
