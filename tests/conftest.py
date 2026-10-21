from pathlib import Path

import pytest

from hof import data

FIXTURE = Path(__file__).parent / "fixtures" / "data"


@pytest.fixture(scope="session")
def ds() -> data.Dataset:
    """A small synthetic dataset (80 players, 1990-2024). Regenerate with the
    command in scripts/make_synthetic_data.py."""
    return data.load(FIXTURE)
