"""The data snapshot: which one we use, how to fetch it, and how to load it.

`data/snapshot.toml` pins one snapshot by URL and SHA-256. Every run says which
snapshot it used, so a ranking change is always a code change, never a silent
change upstream.
"""

import hashlib
import io
import tomllib
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import pandera.pandas as pa

ROOT = Path(__file__).resolve().parents[2]
PIN = ROOT / "data" / "snapshot.toml"
RAW = ROOT / "data" / "raw"


@dataclass(frozen=True)
class Snapshot:
    name: str
    url: str
    sha256: str

    @property
    def path(self) -> Path:
        return RAW / self.name


def pinned() -> Snapshot:
    with PIN.open("rb") as f:
        return Snapshot(**tomllib.load(f))


def sha256(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def fetch(snap: Snapshot) -> Path:
    """Download and unpack the snapshot once; refuse it if the hash is wrong."""
    marker = snap.path / ".sha256"
    if marker.exists() and marker.read_text(encoding="utf-8") == snap.sha256:
        return snap.path
    with urllib.request.urlopen(snap.url) as resp:
        blob = resp.read()
    if (got := sha256(blob)) != snap.sha256:
        raise RuntimeError(f"{snap.name}: expected sha256 {snap.sha256}, downloaded {got}")
    zipfile.ZipFile(io.BytesIO(blob)).extractall(snap.path)
    marker.write_text(snap.sha256, encoding="utf-8")
    return snap.path


@dataclass(frozen=True)
class Dataset:
    matches: pd.DataFrame
    players: pd.DataFrame
    rankings: pd.DataFrame
    inductees: pd.DataFrame


_id = pa.Column(int, pa.Check.ge(0))
_date = pa.Column(int, pa.Check.in_range(19680101, 20991231))
SCHEMAS = {
    "matches": pa.DataFrameSchema(
        {
            "tourney_id": pa.Column(str),
            "tourney_name": pa.Column(str),
            "tourney_level": pa.Column(str, pa.Check.isin(["G", "M", "F", "A"])),
            "tourney_date": _date,
            "round": pa.Column(str, pa.Check.isin(["R128", "R64", "R32", "R16", "QF", "SF", "F"])),
            "winner_id": _id,
            "loser_id": _id,
        },
        checks=pa.Check(lambda df: df["winner_id"] != df["loser_id"], error="self-match"),
    ),
    "players": pa.DataFrameSchema(
        {
            "player_id": pa.Column(int, unique=True),
            "name": pa.Column(str),
            "birth_year": pa.Column(int, pa.Check.in_range(1900, 2020)),
        }
    ),
    "rankings": pa.DataFrameSchema(
        {
            "ranking_date": _date,
            "rank": pa.Column(int, pa.Check.ge(1)),
            "player_id": _id,
            "points": pa.Column(int, pa.Check.ge(0)),
        },
        unique=["ranking_date", "rank"],
    ),
    "inductees": pa.DataFrameSchema(
        {
            "player_id": pa.Column(int, unique=True),
            "induction_year": pa.Column(int, pa.Check.in_range(1955, 2099)),
        }
    ),
}


def load(path: Path) -> Dataset:
    """Read every table and validate it, so bad data fails here and not in a model."""
    return Dataset(
        **{
            name: schema.validate(pd.read_csv(path / f"{name}.csv"))
            for name, schema in SCHEMAS.items()
        }
    )
