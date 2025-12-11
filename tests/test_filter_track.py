import pandas as pd
from src.hurricanes import filter_track

def test_filter_track_basic():
    df = pd.DataFrame({
        "TC number": [1,1,2,2],
        "Year": [2020,2020,2020,2020],
        "Category": [3,5,2,2]
    })

    out = filter_track(df, "Category", lambda x: x > 4, return_filtered=True)

    # Hurricane 1 should remain; Hurricane 2 should be filtered out
    assert out["TC number"].unique().tolist() == [1]
    assert len(out) == 2
