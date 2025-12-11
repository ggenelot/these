"""
Helpers to visualise hurricane tracks as GeoPandas objects and Matplotlib plots.

Typical use:
    lines = tracks_to_lines_gdf(df)
    ax = plot_tracks(lines)
    plot_track_points(df, ax=ax)
"""

from typing import Iterable, Optional, Sequence, Union

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
from shapely.geometry import LineString, Point


def _default_sort_keys(df) -> Optional[Sequence[str]]:
    """Pick a sensible default sort order if time columns exist."""
    for key in ("Time step", "time", "datetime"):
        if key in df.columns:
            return [key]
    return None


def tracks_to_points_gdf(
    df,
    *,
    lat_col: str = "Latitude",
    lon_col: str = "Longitude",
    track_id_col: str = "track_id",
    tc_col: str = "TC number",
    year_col: str = "Year",
    crs: str = "EPSG:4326",
    sort_by: Optional[Sequence[str]] = None,
) -> gpd.GeoDataFrame:
    """
    Convert a hurricane track table into a GeoDataFrame of points.

    Parameters
    ----------
    df : pandas.DataFrame or GeoDataFrame
        Input table containing latitude/longitude columns. If ``track_id_col``
        is missing, it is built from ``tc_col`` and ``year_col`` when present.
    lat_col, lon_col : str
        Column names storing coordinates in decimal degrees.
    track_id_col : str
        Name of the column that uniquely identifies each storm track.
    tc_col, year_col : str
        Column names used to build ``track_id_col`` when it does not already
        exist in ``df``.
    crs : str
        Coordinate reference system for the output GeoDataFrame.
    sort_by : list[str] or None
        Optional columns to sort by; if None, tries to infer a time column.
    """
    gdf = df.copy()

    if (
        track_id_col not in gdf.columns
        and tc_col in gdf.columns
        and year_col in gdf.columns
    ):
        gdf[track_id_col] = gdf[tc_col].astype(str) + "_" + gdf[year_col].astype(str)

    if sort_by is None:
        sort_by = _default_sort_keys(gdf)
    if sort_by:
        gdf = gdf.sort_values(list(sort_by))

    gdf = gpd.GeoDataFrame(
        gdf,
        geometry=gpd.points_from_xy(gdf[lon_col], gdf[lat_col]),
        crs=crs,
    )
    return gdf


def tracks_to_lines_gdf(
    df,
    *,
    lat_col: str = "Latitude",
    lon_col: str = "Longitude",
    track_id_col: str = "track_id",
    tc_col: str = "TC number",
    year_col: str = "Year",
    crs: str = "EPSG:4326",
    sort_by: Optional[Sequence[str]] = None,
) -> gpd.GeoDataFrame:
    """
    Aggregate track points into LineStrings, one feature per storm.

    Parameters mirror ``tracks_to_points_gdf``.
    """
    points = tracks_to_points_gdf(
        df,
        lat_col=lat_col,
        lon_col=lon_col,
        track_id_col=track_id_col,
        tc_col=tc_col,
        year_col=year_col,
        crs=crs,
        sort_by=sort_by,
    )

    records = []
    for track_id, group in points.groupby(track_id_col, dropna=False):
        coords: Iterable[Point] = group.geometry
        coords = list(coords)
        geom = LineString(coords) if len(coords) > 1 else coords[0]
        row = group.iloc[0].copy()
        row.geometry = geom
        records.append(row)

    return gpd.GeoDataFrame(records, crs=crs)


def plot_tracks(
    data: Union[gpd.GeoDataFrame, "pd.DataFrame"],
    *,
    background: Optional[gpd.GeoDataFrame] = None,
    ax=None,
    color_by: Optional[str] = None,
    cmap: str = "viridis",
    linewidth: float = 1.5,
    alpha: float = 0.8,
    legend: bool = True,
    **plot_kwargs,
):
    """
    Plot hurricane tracks as lines.

    Parameters
    ----------
    data : DataFrame or GeoDataFrame
        Either a line GeoDataFrame or a point table convertible with
        ``tracks_to_lines_gdf``.
    background : GeoDataFrame, optional
        Features (e.g., coastlines) to draw beneath tracks.
    ax : matplotlib axis, optional
        Existing axis to draw on; created if missing.
    color_by : str, optional
        Column to color lines by; solid color if None.
    """
    lines = (
        data
        if isinstance(data, gpd.GeoDataFrame)
        and data.geom_type.isin(["LineString", "MultiLineString"]).all()
        else tracks_to_lines_gdf(data)
    )

    if ax is None:
        _, ax = plt.subplots(figsize=(8, 6))

    if background is not None:
        background.plot(ax=ax, color="lightgrey", edgecolor="white", linewidth=0.5)

    if color_by and color_by in lines.columns:
        lines.plot(
            ax=ax,
            column=color_by,
            cmap=cmap,
            linewidth=linewidth,
            alpha=alpha,
            legend=legend,
            **plot_kwargs,
        )
    else:
        lines.plot(ax=ax, color="C0", linewidth=linewidth, alpha=alpha, **plot_kwargs)

    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("Hurricane tracks")
    return ax


def plot_track_points(
    data: Union[gpd.GeoDataFrame, "pd.DataFrame"],
    *,
    background: Optional[gpd.GeoDataFrame] = None,
    ax=None,
    color_by: Optional[str] = None,
    cmap: str = "viridis",
    markersize: float = 25,
    alpha: float = 0.9,
    **plot_kwargs,
):
    """
    Plot hurricane track points (e.g., by intensity).
    """
    points = (
        data
        if isinstance(data, gpd.GeoDataFrame) and data.geom_type.isin(["Point"]).all()
        else tracks_to_points_gdf(data)
    )

    if ax is None:
        _, ax = plt.subplots(figsize=(8, 6))

    if background is not None:
        background.plot(ax=ax, color="lightgrey", edgecolor="white", linewidth=0.5)

    if color_by and color_by in points.columns:
        points.plot(
            ax=ax,
            column=color_by,
            cmap=cmap,
            markersize=markersize,
            alpha=alpha,
            legend=False,
            **plot_kwargs,
        )
    else:
        points.plot(
            ax=ax, color="C1", markersize=markersize, alpha=alpha, **plot_kwargs
        )

    ax.set_axis_off()
    ax.set_title("Hurricane track points")
    return ax


__all__ = [
    "tracks_to_points_gdf",
    "tracks_to_lines_gdf",
    "plot_tracks",
    "plot_track_points",
]
