import numpy as np
from src.hurricanes import haversine_distance

def test_haversine_zero_distance():
    dist = haversine_distance(10, 20, 10, 20)
    assert np.isclose(dist, 0)

def test_haversine_known_distance():
    # Approx distance 1 degree latitude ≈ 111 km
    dist = haversine_distance(0,0, 1,0)
    assert np.isclose(dist, 111, atol=1)
