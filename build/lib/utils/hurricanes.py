import math

import xarray as xr
import numpy as np
import geopandas as gpd
from shapely.geometry import Point, Polygon

def filter_track_in_geometry(df, geometry, tc_col='TC number', year_col='Year',
                            lat_col='Latitude', lon_col='Longitude', new_col='in_geometry', return_filtered=True):
    """
    Adds a boolean column indicating if any point of each hurricane track (identified by TC_number and Year)
    is inside the given geometry.
    
    Parameters:
    - df: pandas.DataFrame with hurricane tracks.
    - geometry: shapely.geometry object (Polygon, MultiPolygon, etc.).
    - tc_col: column for tropical cyclone number.
    - year_col: column for year of the hurricane.
    - lat_col, lon_col: names of latitude and longitude columns.
    - new_col: name of the boolean column to add.
    
    Returns:
    - df with new boolean column added.
    """
    # Create a temporary hurricane ID by combining TC_number and Year
    df['_hurricane_id'] = df[tc_col].astype(str) + "_" + df[year_col].astype(str)
    
    # Function to check for a single hurricane
    def check_hurricane(group):
        points = gpd.GeoSeries([Point(lon, lat) for lon, lat in zip(group[lon_col], group[lat_col])])
        group[new_col] = points.within(geometry).any()
        return group
    
    # Apply to each hurricane track
    df = df.groupby('_hurricane_id', group_keys=False).apply(check_hurricane)
    
    # Drop the temporary ID column
    df = df.drop(columns=['_hurricane_id'])
    
    if return_filtered:
        df=df[df[new_col]==True]
        df = df.drop(columns=new_col)

    return df

def filter_track(df, column, condition, tc_col = 'TC number', year_col='Year', return_filtered = True):

    # Create a temporary hurricane ID by combining TC_number and Year
    df['_hurricane_id'] = df[tc_col].astype(str) + "_" + df[year_col].astype(str)

    # Function to check for a single hurricane track
    def check_hurricane(group):
        # Compute boolean mask within the group
        condition_mask = condition(group[column])
        
        # Flag = True if ANY row satisfies the condition
        flag = condition_mask.any()
        
        # Assign result as a new column for all rows in the group
        group[f'{column}_condition_met'] = flag
        return group
    
    # Apply to each hurricane track
    df = df.groupby('_hurricane_id', group_keys=False).apply(check_hurricane)
    
    # Drop the temporary ID column
    df = df.drop(columns=['_hurricane_id'])

    # Return only the filtered values
    if return_filtered: 
        df=df[df[f'{column}_condition_met'] == True]
        df=df.drop(columns=f'{column}_condition_met')
    
    return df






def blank_raster_from_track(track, resolution=0.01, pad=1.0):
    """
    Create a zero-filled raster (xarray.DataArray) that spans the spatial
    extent of a cyclone track.

    Parameters
    ----------
    track : pandas.DataFrame
        A DataFrame containing at least the columns ``"Latitude"`` and
        ``"Longitude"``. Each row represents a track point.
    resolution : float, optional
        Grid resolution in degrees for both latitude and longitude.
        Default is 0.01.
    pad : float, optional
        Padding (in degrees) added to all sides of the track’s bounding box.
        Default is 1.0.

    Returns
    -------
    xarray.DataArray
        A DataArray named ``"blank"`` with dimensions ``("lat", "lon")``.
        All values are zeros. Coordinates correspond to regularly spaced
        latitude and longitude arrays covering the track’s extent + padding.
    """


    # Extract lats/lons
    #lats = np.array([p["lat"] for p in track])
    #lons = np.array([p["lon"] for p in track])
    
    # Determine bounding box with padding
    lat_min = track["Latitude"].min() - pad
    lat_max = track["Latitude"].max() + pad
    lon_min = track["Longitude"].min() - pad
    lon_max = track["Longitude"].max() + pad
    
    # Create coordinate grid
    lat_grid = np.arange(lat_min, lat_max + resolution, resolution)
    lon_grid = np.arange(lon_min, lon_max + resolution, resolution)
    
    # Create raster of zeros
    data = np.zeros((len(lat_grid), len(lon_grid)))
    
    # Return as DataArray
    da = xr.DataArray(
        data,
        dims=("lat", "lon"),
        coords={"lat": lat_grid, "lon": lon_grid},
        name="blank"
    )
    
    return da


def haversine_distance(lat_center, lon_center, lat, lon):
    """
    Compute great-circle distances using the haversine formula.

    Parameters
    ----------
    lat_center : float
        Latitude of the center point in degrees.
    lon_center : float
        Longitude of the center point in degrees.
    lat : array-like
        Array of latitudes of the target points in degrees.
    lon : array-like
        Array of longitudes of the target points in degrees.

    Returns
    -------
    numpy.ndarray
        Array of distances (in kilometers) from the center point to each
        (lat, lon) location. Output shape matches the broadcasted shapes
        of ``lat`` and ``lon``.
    """

    R = 6371.0  # Earth radius in km
    
    lat1 = np.radians(lat_center)
    lon1 = np.radians(lon_center)
    lat2 = np.radians(lat)
    lon2 = np.radians(lon)
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = (np.sin(dlat/2)**2 +
         np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2)
    
    return 2 * R * np.arcsin(np.sqrt(a))

def mask_points_within_distance(da, lat_center, lon_center, max_distance_km):
    """
    Create a boolean mask indicating which grid cells fall within
    a given great-circle distance from a central point.

    Parameters
    ----------
    da : xarray.DataArray
        A DataArray with ``lat`` and ``lon`` coordinates. Typically the
        output of ``blank_raster_from_track``.
    lat_center : float
        Latitude of the center point in degrees.
    lon_center : float
        Longitude of the center point in degrees.
    max_distance_km : float
        Maximum distance (in kilometers) defining the mask radius.

    Returns
    -------
    xarray.DataArray
        Boolean mask DataArray of shape ``(lat, lon)`` where ``True``
        indicates that the grid point is within ``max_distance_km``.
        Coordinates from ``da`` are preserved.
    """

    # Get broadcasting coordinate grids
    Lon, Lat = np.meshgrid(da.lon.values, da.lat.values)
    
    # Compute distances for the whole grid
    distance = haversine_distance(lat_center, lon_center, Lat, Lon)
    
    # Create boolean mask
    mask = distance <= max_distance_km
    
    # Return as DataArray
    return xr.DataArray(
        mask,
        dims=("lat", "lon"),
        coords={"lat": da.lat, "lon": da.lon},
        name="mask_within_distance"
    )


def _destination_point(lat, lon, bearing_deg, distance_km, radius_km=6371.0):
    """
    Compute destination point from a start point, bearing, and distance on a sphere.

    Returns (lat, lon) in degrees.
    """
    lat1 = math.radians(lat)
    lon1 = math.radians(lon)
    bearing = math.radians(bearing_deg)
    angular_distance = distance_km / radius_km

    lat2 = math.asin(
        math.sin(lat1) * math.cos(angular_distance)
        + math.cos(lat1) * math.sin(angular_distance) * math.cos(bearing)
    )

    lon2 = lon1 + math.atan2(
        math.sin(bearing) * math.sin(angular_distance) * math.cos(lat1),
        math.cos(angular_distance) - math.sin(lat1) * math.sin(lat2),
    )

    return math.degrees(lat2), math.degrees((lon2 + math.pi) % (2 * math.pi) - math.pi)


def polygon_from_point_radius(lat_center, lon_center, radius_km, n_points=64):
    """
    Build an approximate circular polygon around a point with a geodesic radius.

    Parameters
    ----------
    lat_center, lon_center : float
        Center coordinates in degrees.
    radius_km : float
        Radius of the circle in kilometers.
    n_points : int
        Number of points to sample along the circle.
    """
    if radius_km <= 0:
        raise ValueError("radius_km must be positive")
    bearings = np.linspace(0, 360, num=n_points, endpoint=False)
    coords_latlon = [_destination_point(lat_center, lon_center, b, radius_km) for b in bearings]
    # shapely expects (x, y) -> (lon, lat)
    coords = [(lon, lat) for lat, lon in coords_latlon]
    return Polygon(coords)

def track_to_ds(track, resolution=0.05):
    """
    Convert a cyclone track DataFrame into a gridded Dataset of wind speeds.

    For each track point, the function:
    1. Creates a spatial mask corresponding to the radius of maximum winds.
    2. Multiplies the mask by the maximum wind speed.
    3. Stacks all time steps into a new ``time_step`` dimension.

    Parameters
    ----------
    track : pandas.DataFrame
        Must contain the following columns:
        - ``"Latitude"``
        - ``"Longitude"``
        - ``"Maximum wind speed"``
        - ``"Radius to maximum winds"``
        - ``"Time step"``
    resolution : float, optional
        Spatial resolution of the output grid in degrees. Default is 0.05.

    Returns
    -------
    xarray.Dataset
        Dataset with a single variable ``"wind_speed"`` and dimensions
        ``("time_step", "lat", "lon")``. Each time step contains the wind
        speed field computed from the distance mask multiplied by the
        maximum wind speed.
    """

    # Create an empty da that has the shape of the track
    da = blank_raster_from_track(track, resolution=resolution)

    # Populate the wind speed
    masked_list = []
    for i, step in track.iterrows():


        wind_speed = step["Maximum wind speed"] * mask_points_within_distance(da, step["Latitude"], step["Longitude"], step["Radius to maximum winds"])
        
        wind_speed = wind_speed.expand_dims({"time_step": [step["Time step"]]})

        masked_list.append(wind_speed)

    # Combine all the DataArrays along the new time_step dimension
    combined_da = xr.concat(masked_list, dim="time_step")

    # If you want it as a Dataset instead
    return combined_da.to_dataset(name="wind_speed")

