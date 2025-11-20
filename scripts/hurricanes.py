import xarray as xr
import numpy as np



def blank_raster_from_track(track, resolution=0.01, pad=1.0):
    """
    Create a DataArray of zeros covering the extent of a cyclone track.
    
    Parameters
    ----------
    track : iterable of dict or objects with attributes
        Must contain 'lat' and 'lon' entries.
    resolution : float
        Grid cell size in degrees.
    pad : float
        Extra degrees added around the bounding box.
    
    Returns
    -------
    xarray.DataArray
        DataArray with dims (lat, lon) filled with zeros.
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
    Computes the haversine distance (km) between a center point
    and arrays of points (lat, lon).
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
    Returns a boolean DataArray mask where each cell indicates
    whether the grid point is within max_distance_km of (lat_center, lon_center).
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

