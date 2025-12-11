import xarray as xr
import rioxarray
import geopandas as gpd
from rasterio import features
import numpy as np

def binary_vector_to_raster(input_vector, layer_name, reference):
    """
    Rasterize a binary vector layer to match a reference raster grid.

    Parameters
    ----------
    input_vector : geopandas.GeoDataFrame
        Vector geometries to burn into the raster (1 where geometry exists).
    layer_name : str
        Name for the output DataArray.
    reference : xarray.DataArray
        Raster providing grid shape, transform, and coords.
    """

    shape = (reference.sizes["y"], reference.sizes["x"])
    transform = reference.rio.transform()

    geom = [shapes for shapes in input_vector.geometry]

    # Rasterize vector using the shape and coordinate system of the raster
    rasterized = features.rasterize(geom,
                                out_shape = shape,
                                fill = 0,
                                out = None,
                                transform = transform,
                                all_touched = True,
                                default_value = 1,
                                dtype = None)
    
    # Turning it into a DataArray
    xarray = xr.DataArray(
    rasterized,
    dims=("y", "x"),
    coords={"x": reference.x, "y": reference.y},
    name=layer_name
    )

    return xarray

def class_vector_to_raster(input_vector, layer_name, column_name,  reference):
    """
    Rasterize a categorical vector layer using values from a column.

    Parameters
    ----------
    input_vector : geopandas.GeoDataFrame
        Vector geometries with class values.
    layer_name : str
        Name for the output DataArray.
    column_name : str
        Column containing class values to burn into the raster.
    reference : xarray.DataArray
        Raster providing grid shape, transform, and coords.
    """

    shape = (reference.sizes["y"], reference.sizes["x"])
    transform = reference.rio.transform()

    geom = [shapes for shapes in input_vector.geometry]

    # Rasterize vector using the shape and coordinate system of the raster
    rasterized = features.rasterize(
                                ((geom, value) for geom, value in zip(input_vector.geometry, input_vector[column_name])),
                                out_shape = shape,
                                fill = 0,
                                out = None,
                                transform = transform,
                                all_touched = True,
                                default_value = 1,
                                dtype = None)
    
    # Turning it into a DataArray
    xarray = xr.DataArray(
    rasterized,
    dims=("y", "x"),
    coords={"x": reference.x, "y": reference.y},
    name=layer_name
    )

    return xarray

def road_distance(input_vector, layer_name, reference): 
    """
    Compute distance (in map units) from each raster cell to the nearest road.

    Parameters
    ----------
    input_vector : geopandas.GeoDataFrame
        Road geometries.
    layer_name : str
        Name for the output DataArray.
    reference : xarray.DataArray
        Raster providing grid shape, transform, and coords.

    Returns
    -------
    xarray.DataArray
        Distance raster with same shape/coords as ``reference``.
    """

    # Rasterize road geometries to a binary mask (1 = road, 0 = background)
    shape = (reference.sizes["y"], reference.sizes["x"])
    transform = reference.rio.transform()
    roads_raster = features.rasterize(
        ((geom, 1) for geom in input_vector.geometry),
        out_shape=shape,
        fill=0,
        transform=transform,
        all_touched=True,
        dtype="uint8",
    )

    # Build coordinate grid of pixel centers from the reference
    xs = reference.x.values
    ys = reference.y.values
    X, Y = np.meshgrid(xs, ys, indexing="xy")  # shapes = (ny, nx)

    road_mask = roads_raster == 1
    if not road_mask.any():
        # No roads: return array of NaNs
        distances = np.full(shape, np.nan, dtype=np.float32)
    else:
        # Coordinates of road pixels and all pixels
        road_pts = np.column_stack((X[road_mask], Y[road_mask]))
        all_pts = np.column_stack((X.ravel(), Y.ravel()))

        # Use scipy cKDTree to compute nearest-neighbour distances
        try:
            from scipy.spatial import cKDTree
        except Exception as e:
            raise ImportError("scipy is required for distance computation (install scipy).") from e

        tree = cKDTree(road_pts)
        dists, _ = tree.query(all_pts, k=1)
        distances = dists.reshape(shape).astype(np.float32)

    # Return as an xarray DataArray with the same coords as the reference
    return xr.DataArray(distances, dims=("y", "x"), coords={"x": reference.x, "y": reference.y}, name=layer_name)
