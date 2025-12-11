"""Helpers to download OpenStreetMap features with osmnx."""

import osmnx as ox
import geopandas as gpd


def download_osm_features(place_name: str = "martinique", tags: dict | None = None) -> gpd.GeoDataFrame:
    """
    Fetch OpenStreetMap features for a given place.

    Parameters
    ----------
    place_name : str, default "martinique"
        Nominatim place string to query.
    tags : dict, optional
        OSM tags to filter (e.g., ``{"building": True}``). If None, buildings are fetched.

    Returns
    -------
    geopandas.GeoDataFrame
        Features returned by osmnx.
    """
    if tags is None:
        tags = {"building": True}
    return ox.features_from_place(place_name, tags)


__all__ = ["download_osm_features"]
