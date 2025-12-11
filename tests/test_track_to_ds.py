import pandas as pd
from src.hurricanes import track_to_ds

def test_track_to_ds_dimensions():
    df = pd.DataFrame({
        "Latitude": [0, 0.5],
        "Longitude": [0, 0.5],
        "Maximum wind speed": [100, 80],
        "Radius to maximum winds": [200, 200],
        "Time step": [0, 1],
    })

    ds = track_to_ds(df, resolution=1.0)

    assert "wind_speed" in ds
    assert len(ds.time_step) == 2
    assert ds.wind_speed.shape[0] == 2
