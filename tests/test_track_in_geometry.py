import pandas as pd
from shapely.geometry import Polygon
from scripts.hurricanes import track_in_geometry

def test_track_in_geometry():
    df = pd.DataFrame({
        "TC number": [1,1],
        "Year": [2020,2020],
        "Latitude": [10, 12],
        "Longitude": [50, 55],
    })

    poly = Polygon([(0,0),(0,20),(60,20),(60,0)])

    out = track_in_geometry(df, poly, new_col="inside")

    assert out["inside"].all() is True
