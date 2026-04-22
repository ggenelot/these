"""Prototype minimal pour générer un bloc-diagramme 3D depuis un MNT GeoTIFF.

Ce module fournit une première brique analytique reproductible :
- chargement d'un MNT raster ;
- gestion des NoData ;
- recadrage optionnel de l'emprise ;
- exagération verticale paramétrable ;
- rendu oblique 3D simple et export image.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import rasterio
from matplotlib.figure import Figure
from rasterio.crs import CRS
from rasterio.transform import array_bounds
from rasterio.warp import Resampling, calculate_default_transform, reproject
from rasterio.windows import from_bounds


Bounds = Tuple[float, float, float, float]
USE_TEXTURE = False
TEXTURE_PATH: Optional[str] = None


def _utm_crs_from_lonlat(lon: float, lat: float) -> CRS:
    """Retourner un CRS UTM (mètres) adapté à une longitude/latitude donnée."""
    zone = int(np.floor((lon + 180.0) / 6.0) + 1)
    zone = min(max(zone, 1), 60)
    epsg = 32600 + zone if lat >= 0 else 32700 + zone
    return CRS.from_epsg(epsg)


def _load_texture_on_dem_grid(
    texture_path: str | Path,
    *,
    target_shape: Tuple[int, int],
    target_transform,
    target_crs: Optional[CRS],
) -> Optional[np.ndarray]:
    """Charger/reprojeter une texture raster sur la grille du MNT."""
    if target_crs is None:
        return None

    texture_path = Path(texture_path)
    if not texture_path.exists():
        return None

    dst_h, dst_w = target_shape
    texture_rgb = np.zeros((dst_h, dst_w, 3), dtype=np.float32)
    nodata_mask = np.zeros((dst_h, dst_w), dtype=bool)

    with rasterio.open(texture_path) as tex:
        src_crs = tex.crs
        if src_crs is None:
            return None

        bands_to_use = [1, 2, 3] if tex.count >= 3 else [1, 1, 1]
        tex_nodata = tex.nodata

        for i, bidx in enumerate(bands_to_use):
            src_band = tex.read(bidx).astype("float32")
            dst_band = np.zeros((dst_h, dst_w), dtype=np.float32)
            reproject(
                source=src_band,
                destination=dst_band,
                src_transform=tex.transform,
                src_crs=src_crs,
                src_nodata=tex_nodata,
                dst_transform=target_transform,
                dst_crs=target_crs,
                dst_nodata=np.nan,
                resampling=Resampling.bilinear,
            )
            texture_rgb[:, :, i] = dst_band

        # Masque des pixels invalides (hors couverture ou NoData)
        nodata_mask = ~np.isfinite(texture_rgb).all(axis=2)

        # Normalisation 0..1 pour matplotlib facecolors.
        tex_min = np.nanpercentile(texture_rgb, 2)
        tex_max = np.nanpercentile(texture_rgb, 98)
        if np.isfinite(tex_min) and np.isfinite(tex_max) and tex_max > tex_min:
            texture_rgb = (texture_rgb - tex_min) / (tex_max - tex_min)
        texture_rgb = np.clip(texture_rgb, 0.0, 1.0)
        texture_rgb[nodata_mask] = 0.0

    return texture_rgb


def _load_dem_core(
    dem_path: str | Path,
    *,
    bounds: Optional[Bounds] = None,
):
    """Lecture DEM avec métadonnées nécessaires au rendu/alignement texture."""
    dem_path = Path(dem_path)

    with rasterio.open(dem_path) as src:
        if bounds is not None:
            window = from_bounds(*bounds, transform=src.transform)
            window = window.round_offsets().round_lengths()
            z = src.read(1, window=window, masked=True).astype("float64")
            transform = src.window_transform(window)
        else:
            z = src.read(1, masked=True).astype("float64")
            transform = src.transform

        nodata = src.nodata
        src_crs = src.crs

    # Si le raster est en coordonnées géographiques (degrés),
    # on le reprojette en UTM local (mètres) pour homogénéiser X/Y/Z.
    work_crs = src_crs
    if src_crs is not None and src_crs.is_geographic:
        ny_src, nx_src = z.shape
        xmin, ymin, xmax, ymax = array_bounds(ny_src, nx_src, transform)
        lon_center = (xmin + xmax) / 2.0
        lat_center = (ymin + ymax) / 2.0
        dst_crs = _utm_crs_from_lonlat(lon_center, lat_center)
        dst_transform, dst_width, dst_height = calculate_default_transform(
            src_crs,
            dst_crs,
            nx_src,
            ny_src,
            xmin,
            ymin,
            xmax,
            ymax,
        )

        src_nodata = nodata if nodata is not None else -9999.0
        src_data = np.asarray(z.filled(src_nodata), dtype="float64")
        dst_data = np.full((dst_height, dst_width), src_nodata, dtype="float64")

        reproject(
            source=src_data,
            destination=dst_data,
            src_transform=transform,
            src_crs=src_crs,
            src_nodata=src_nodata,
            dst_transform=dst_transform,
            dst_crs=dst_crs,
            dst_nodata=src_nodata,
            resampling=Resampling.bilinear,
        )

        z = np.ma.array(dst_data, mask=np.isclose(dst_data, src_nodata))
        transform = dst_transform
        nodata = src_nodata
        work_crs = dst_crs

    # Convertit le masque rasterio en NaN explicites pour matplotlib.
    z = np.where(np.ma.getmaskarray(z), np.nan, np.asarray(z))

    ny, nx = z.shape
    cols = np.arange(nx)
    rows = np.arange(ny)

    # Coordonnées des centres de pixels.
    x = transform.c + (cols + 0.5) * transform.a
    y = transform.f + (rows + 0.5) * transform.e

    return z, x, y, nodata, transform, work_crs


def load_dem(
    dem_path: str | Path,
    *,
    bounds: Optional[Bounds] = None,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, Optional[float]]:
    """Charger un MNT GeoTIFF en appliquant un recadrage optionnel.

    Parameters
    ----------
    dem_path : str | pathlib.Path
        Chemin vers le MNT GeoTIFF.
    bounds : tuple(float, float, float, float), optional
        Emprise de recadrage ``(xmin, ymin, xmax, ymax)`` dans le CRS du raster.

    Returns
    -------
    z : numpy.ndarray
        Matrice 2D des élévations (float) avec NoData converti en ``nan``.
    x : numpy.ndarray
        Coordonnées X des centres de pixels.
    y : numpy.ndarray
        Coordonnées Y des centres de pixels.
    nodata : float or None
        Valeur NoData déclarée dans la source.
    """
    z, x, y, nodata, _, _ = _load_dem_core(dem_path, bounds=bounds)
    return z, x, y, nodata


def create_block_diagram(
    dem_path: str | Path,
    output_path: str | Path,
    *,
    bounds: Optional[Bounds] = None,
    vertical_exaggeration: float = 1.5,
    azimuth: float = -60,
    elevation: float = 30,
    cmap: str = "terrain",
    figure_size: Tuple[float, float] = (12, 7),
    dpi: int = 200,
    base_level: Optional[float] = None,
    use_texture: Optional[bool] = None,
    texture_path: Optional[str | Path] = None,
) -> Figure:
    """Créer une vue oblique 3D simple à partir d'un MNT et exporter l'image.

    Parameters
    ----------
    dem_path : str | pathlib.Path
        Chemin vers le MNT GeoTIFF.
    output_path : str | pathlib.Path
        Chemin de sortie (PNG/JPG/SVG...) pour l'export de la figure.
    bounds : tuple(float, float, float, float), optional
        Recadrage d'emprise ``(xmin, ymin, xmax, ymax)``.
    vertical_exaggeration : float
        Facteur d'exagération verticale appliqué au relief.
    azimuth : float
        Angle d'azimut de la caméra (``ax.view_init``).
    elevation : float
        Angle d'élévation de la caméra (``ax.view_init``).
    cmap : str
        Colormap matplotlib.
    figure_size : tuple(float, float)
        Taille de la figure en pouces.
    dpi : int
        Résolution d'export.
    base_level : float, optional
        Altitude de base du bloc. Si None, prend le minimum du relief exagéré.
    use_texture : bool, optional
        Active l'application d'une texture raster sur la surface supérieure.
        Si None, utilise la constante globale ``USE_TEXTURE``.
    texture_path : str | pathlib.Path, optional
        Chemin vers la texture géoréférencée (GeoTIFF recommandé).
        Si None, utilise ``TEXTURE_PATH``.

    Returns
    -------
    matplotlib.figure.Figure
        Figure générée (utile pour ajustements en aval).
    """
    if vertical_exaggeration <= 0:
        raise ValueError("vertical_exaggeration doit être strictement positif.")

    z, x, y, _, dem_transform, dem_crs = _load_dem_core(dem_path, bounds=bounds)

    xx, yy = np.meshgrid(x, y)
    zz = z * vertical_exaggeration
    z_min = float(np.nanmin(zz))
    z_base = z_min if base_level is None else float(base_level)
    zz_top = np.where(np.isnan(zz), z_base, zz)

    fig = plt.figure(figsize=figure_size)
    ax = fig.add_subplot(111, projection="3d")

    use_texture_resolved = USE_TEXTURE if use_texture is None else use_texture
    texture_path_resolved = TEXTURE_PATH if texture_path is None else texture_path
    texture_rgb = None
    if use_texture_resolved and texture_path_resolved:
        texture_rgb = _load_texture_on_dem_grid(
            texture_path_resolved,
            target_shape=zz_top.shape,
            target_transform=dem_transform,
            target_crs=dem_crs,
        )

    top_surface_kwargs = dict(
        linewidth=0,
        antialiased=False,
        rcount=min(zz.shape[0], 300),
        ccount=min(zz.shape[1], 300),
    )
    if texture_rgb is not None:
        top_surface_kwargs["facecolors"] = texture_rgb
        top_surface_kwargs["shade"] = False
    else:
        top_surface_kwargs["cmap"] = cmap

    ax.plot_surface(
        xx,
        yy,
        zz_top,
        **top_surface_kwargs,
    )

    # Base horizontale
    ax.plot_surface(
        xx,
        yy,
        np.full_like(zz_top, z_base),
        color="#d7cfbe",
        linewidth=0,
        antialiased=False,
    )

    # Faces latérales verticales pour fermer le volume.
    x0 = np.array([x[0], x[0]])
    x1 = np.array([x[-1], x[-1]])
    y0 = np.array([y[0], y[0]])
    y1 = np.array([y[-1], y[-1]])

    top_left = zz_top[:, 0]
    top_right = zz_top[:, -1]
    top_front = zz_top[0, :]
    top_back = zz_top[-1, :]

    y_col = y[:, None]
    x_col = x[:, None]
    z_left = np.column_stack((np.full_like(top_left, z_base), top_left))
    z_right = np.column_stack((np.full_like(top_right, z_base), top_right))
    z_front = np.column_stack((np.full_like(top_front, z_base), top_front))
    z_back = np.column_stack((np.full_like(top_back, z_base), top_back))

    ax.plot_surface(
        np.tile(x0, (len(y), 1)),
        np.tile(y_col, (1, 2)),
        z_left,
        color="#b8ad97",
        linewidth=0,
        antialiased=False,
    )
    ax.plot_surface(
        np.tile(x1, (len(y), 1)),
        np.tile(y_col, (1, 2)),
        z_right,
        color="#b8ad97",
        linewidth=0,
        antialiased=False,
    )
    ax.plot_surface(
        np.tile(x_col, (1, 2)),
        np.tile(y0, (len(x), 1)),
        z_front,
        color="#a89d86",
        linewidth=0,
        antialiased=False,
    )
    ax.plot_surface(
        np.tile(x_col, (1, 2)),
        np.tile(y1, (len(x), 1)),
        z_back,
        color="#a89d86",
        linewidth=0,
        antialiased=False,
    )

    ax.view_init(elev=elevation, azim=azimuth)
    ax.set_axis_off()

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight")

    return fig


__all__ = ["load_dem", "create_block_diagram"]
