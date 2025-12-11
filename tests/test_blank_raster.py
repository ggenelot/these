import pandas as pd
from src.hurricanes import blank_raster_from_track

def test_blank_raster_shape():
    df = pd.DataFrame({
        "Latitude": [10, 11],
        "Longitude": [50, 51],
    })

    da = blank_raster_from_track(df, resolution=1.0, pad=0)

    # Lat goes from 10 to 11 inclusive at step 1 → 2 values
    assert len(da.lat) == 2
    assert len(da.lon) == 2
    assert (da.values == 0).all()
