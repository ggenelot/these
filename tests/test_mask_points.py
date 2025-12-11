import pandas as pd
from src.hurricanes import blank_raster_from_track, mask_points_within_distance

def test_mask_points():
    df = pd.DataFrame({
        "Latitude": [0],
        "Longitude": [0]
    })

    da = blank_raster_from_track(df, resolution=1.0, pad=1.0)
    mask = mask_points_within_distance(da, 0, 0, max_distance_km=200)

    # Center cell is within 200 km
    center_idx = (mask.lat.values == 0) & (mask.lon.values == 0)
    assert mask.values[center_idx][0][0] == True
