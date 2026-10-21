"""Bad data must fail at load time, not three steps later inside the model."""

import pandas as pd
import pandera.errors
import pytest

from hof import data


def test_fixture_passes_schema(ds):
    assert len(ds.matches) > 0


def test_player_cannot_play_themselves(ds):
    bad = ds.matches.copy()
    bad.loc[bad.index[0], "loser_id"] = bad.loc[bad.index[0], "winner_id"]
    with pytest.raises(pandera.errors.SchemaError):
        data.SCHEMAS["matches"].validate(bad)


def test_unknown_round_is_rejected(ds):
    bad = ds.matches.copy()
    bad.loc[bad.index[0], "round"] = "Final"
    with pytest.raises(pandera.errors.SchemaError):
        data.SCHEMAS["matches"].validate(pd.DataFrame(bad))
