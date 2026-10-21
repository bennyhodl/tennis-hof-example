"""The ranking on a frozen dataset. If this fails, the method changed.

If you meant to change it, regenerate the expected files and commit them with
your PR so reviewers see exactly what moved:

    uv run pytest tests/test_pipeline.py --force-regen
"""

from hypothesis import given, settings
from hypothesis import strategies as st

from hof import data, pipeline


def test_rankings_match_golden_file(ds, dataframe_regression, data_regression):
    rankings, metrics = pipeline.rank(ds)
    dataframe_regression.check(rankings)
    data_regression.check(metrics)


@settings(max_examples=5, deadline=None)
@given(seed=st.integers(0, 2**32 - 1))
def test_row_order_does_not_change_rankings(ds, seed):
    shuffled = data.Dataset(
        matches=ds.matches.sample(frac=1, random_state=seed),
        players=ds.players.sample(frac=1, random_state=seed),
        rankings=ds.rankings.sample(frac=1, random_state=seed),
        inductees=ds.inductees,
    )
    expected, _ = pipeline.rank(ds)
    got, _ = pipeline.rank(shuffled)
    assert got.equals(expected)
