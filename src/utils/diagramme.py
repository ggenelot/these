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
from typing import Any, Mapping, Optional, Sequence, Tuple

import matplotlib.pyplot as plt
import numpy as np
import rasterio
from matplotlib.colors import (
    LightSource,
    LinearSegmentedColormap,
    TwoSlopeNorm,
    to_rgba,
)
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import proj3d
from rasterio.crs import CRS
from rasterio.transform import array_bounds
from rasterio.warp import Resampling, calculate_default_transform, reproject, transform
from rasterio.windows import from_bounds


Bounds = Tuple[float, float, float, float]
LabelSpec = Mapping[str, Any]
USE_TEXTURE = False
TEXTURE_PATH: Optional[str] = None


def _utm_crs_from_lonlat(lon: float, lat: float) -> CRS:
    """Retourner un CRS UTM (mètres) adapté à une longitude/latitude donnée."""
    zone = int(np.floor((lon + 180.0) / 6.0) + 1)
    zone = min(max(zone, 1), 60)
    epsg = 32600 + zone if lat >= 0 else 32700 + zone
    return CRS.from_epsg(epsg)


def _load_texture_on_grid(
    texture_path: str | Path,
    *,
    target_shape: Tuple[int, int],
    target_transform,
    target_crs: Optional[CRS],
) -> Optional[np.ndarray]:
    """Charger/reprojeter une texture raster sur une grille cible."""
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


def _load_texture_on_dem_grid(
    texture_path: str | Path,
    *,
    target_shape: Tuple[int, int],
    target_transform,
    target_crs: Optional[CRS],
) -> Optional[np.ndarray]:
    """Charger/reprojeter une texture raster sur la grille du MNT."""
    return _load_texture_on_grid(
        texture_path,
        target_shape=target_shape,
        target_transform=target_transform,
        target_crs=target_crs,
    )


def _load_single_band_on_grid(
    raster_path: str | Path,
    *,
    target_shape: Tuple[int, int],
    target_transform,
    target_crs: Optional[CRS],
    source_crs: Optional[str | CRS] = None,
) -> Optional[np.ndarray]:
    """Charger/reprojeter un raster monobande sur une grille cible."""
    if target_crs is None:
        return None

    raster_path = Path(raster_path)
    if not raster_path.exists():
        return None

    dst_h, dst_w = target_shape
    dst = np.full((dst_h, dst_w), np.nan, dtype=np.float64)

    with rasterio.open(raster_path) as src:
        src_crs = src.crs
        if src_crs is None and source_crs is not None:
            src_crs = CRS.from_user_input(source_crs)
            print(f"[bathymetry] Using fallback CRS for {raster_path}: {src_crs}")
        if src_crs is None:
            print(f"[bathymetry] Ignoring {raster_path}: missing CRS")
            return None

        src_band = src.read(1).astype("float64")
        src_nodata = src.nodata
        if src_nodata is not None:
            src_band = np.where(np.isclose(src_band, src_nodata), np.nan, src_band)

        reproject(
            source=src_band,
            destination=dst,
            src_transform=src.transform,
            src_crs=src_crs,
            src_nodata=np.nan,
            dst_transform=target_transform,
            dst_crs=target_crs,
            dst_nodata=np.nan,
            resampling=Resampling.bilinear,
        )

    return dst


def _load_dem_core(
    dem_path: str | Path,
    *,
    bounds: Optional[Bounds] = None,
):
    """Lecture DEM avec métadonnées nécessaires au rendu/alignement texture."""
    dem_path = Path(dem_path)

    with rasterio.open(dem_path) as src:
        if bounds is not None:
            left = max(bounds[0], src.bounds.left)
            bottom = max(bounds[1], src.bounds.bottom)
            right = min(bounds[2], src.bounds.right)
            top = min(bounds[3], src.bounds.top)
            if left >= right or bottom >= top:
                raise ValueError(
                    "L'emprise demandée ne recoupe pas l'emprise du MNT."
                )

            window = from_bounds(left, bottom, right, top, transform=src.transform)
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


def _resample_dem_to_match_texture(
    z: np.ndarray,
    *,
    src_transform,
    src_crs: Optional[CRS],
    texture_path: str | Path,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, Any, Optional[CRS]]:
    """Reprojeter/rééchantillonner le MNT sur la grille de la texture."""
    if src_crs is None:
        return z, * _xy_from_transform(src_transform, z.shape), src_transform, src_crs

    texture_path = Path(texture_path)
    if not texture_path.exists():
        return z, * _xy_from_transform(src_transform, z.shape), src_transform, src_crs

    with rasterio.open(texture_path) as tex:
        if tex.crs is None:
            return z, * _xy_from_transform(src_transform, z.shape), src_transform, src_crs

        dst = np.full((tex.height, tex.width), np.nan, dtype="float64")
        reproject(
            source=np.asarray(z, dtype="float64"),
            destination=dst,
            src_transform=src_transform,
            src_crs=src_crs,
            src_nodata=np.nan,
            dst_transform=tex.transform,
            dst_crs=tex.crs,
            dst_nodata=np.nan,
            resampling=Resampling.bilinear,
        )
        x, y = _xy_from_transform(tex.transform, dst.shape)
        return dst, x, y, tex.transform, tex.crs


def _xy_from_transform(transform, shape: Tuple[int, int]) -> Tuple[np.ndarray, np.ndarray]:
    """Coordonnées X/Y des centres de pixels pour une transform affine."""
    ny, nx = shape
    cols = np.arange(nx)
    rows = np.arange(ny)
    x = transform.c + (cols + 0.5) * transform.a
    y = transform.f + (rows + 0.5) * transform.e
    return x, y


def _normalise_rgb(rgb: np.ndarray) -> np.ndarray:
    """Normaliser un raster RGB en 0..1 de manière robuste."""
    rgb = rgb.astype("float32", copy=False)
    if np.nanmax(rgb) > 1.0:
        rgb = rgb / 255.0
    return np.clip(rgb, 0.0, 1.0)


def _topobathy_colormap() -> LinearSegmentedColormap:
    """Palette continue pour relief terrestre et bathymetrie."""
    return LinearSegmentedColormap.from_list(
        "modele_sig_topobathy",
        [
            (0.00, "#07192f"),
            (0.18, "#0a3f7f"),
            (0.34, "#1677a6"),
            (0.48, "#72c9c8"),
            (0.50, "#0f6f8e"),
            (0.515, "#e0c88c"),
            (0.58, "#a5bf63"),
            (0.70, "#5d9a50"),
            (0.82, "#386f37"),
            (0.92, "#806846"),
            (1.00, "#d2c9b8"),
        ],
    )


def _resolve_cmap(cmap: str):
    """Retourner une palette matplotlib, avec alias locaux."""
    if cmap == "topobathy":
        return _topobathy_colormap()
    return plt.get_cmap(cmap)


def _solid_facecolors(shape: Tuple[int, int], color: str) -> np.ndarray:
    """Construire un tableau RGBA uniforme pour une surface matplotlib 3D."""
    rgba = np.asarray(to_rgba(color), dtype=float)
    facecolors = np.empty((*shape, 4), dtype=float)
    facecolors[...] = rgba
    return facecolors


def _shade_rgb(
    rgb: np.ndarray,
    elevation: np.ndarray,
    *,
    azimuth: float,
    altitude: float,
    fraction: float,
    brightness: float,
    gamma: float,
) -> np.ndarray:
    """Appliquer un hillshade léger à une texture RGB."""
    light = LightSource(azdeg=azimuth, altdeg=altitude)
    shade = light.hillshade(np.nan_to_num(elevation, nan=np.nanmin(elevation)))
    corrected = _normalise_rgb(rgb)
    corrected = np.power(corrected, gamma) * brightness
    corrected = np.clip(corrected, 0.0, 1.0)
    shaded = corrected * (0.45 + 0.55 * shade[:, :, None] * fraction)
    return np.clip(shaded, 0.0, 1.0)


def _surface_facecolors(
    elevation: np.ndarray,
    *,
    cmap: str,
    cmap_center: Optional[float],
    azimuth: float,
    altitude: float,
    texture_rgb: Optional[np.ndarray],
    shade_fraction: float,
    shade_blend_mode: str,
    texture_brightness: float,
    texture_gamma: float,
) -> np.ndarray:
    """Construire les couleurs de surface avec texture ou colormap ombrée."""
    if texture_rgb is not None:
        return _shade_rgb(
            texture_rgb,
            elevation,
            azimuth=azimuth,
            altitude=altitude,
            fraction=shade_fraction,
            brightness=texture_brightness,
            gamma=texture_gamma,
        )

    light = LightSource(azdeg=azimuth, altdeg=altitude)
    safe_elevation = np.nan_to_num(elevation, nan=np.nanmin(elevation))
    norm = None
    if cmap_center is not None:
        vmin = float(np.nanmin(safe_elevation))
        vmax = float(np.nanmax(safe_elevation))
        center = float(cmap_center)
        if vmin < center < vmax:
            norm = TwoSlopeNorm(vmin=vmin, vcenter=center, vmax=vmax)

    return light.shade(
        safe_elevation,
        cmap=_resolve_cmap(cmap),
        norm=norm,
        vert_exag=1.0,
        blend_mode=shade_blend_mode,
        fraction=shade_fraction,
    )


def _resolve_label_xy(label: LabelSpec, x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    """Résoudre une position de label depuis x/y ou des fractions d'emprise."""
    if "xy_fraction" in label:
        fx, fy = label["xy_fraction"]
        return (
            float(x[0] + fx * (x[-1] - x[0])),
            float(y[0] + fy * (y[-1] - y[0])),
        )
    if "x" in label and "y" in label:
        return float(label["x"]), float(label["y"])
    raise ValueError("Chaque label doit définir 'x'/'y' ou 'xy_fraction'.")


def _resolve_label_xy_any(
    label: LabelSpec,
    x: np.ndarray,
    y: np.ndarray,
    target_crs: Optional[CRS],
) -> Tuple[float, float]:
    """Resoudre une position de label depuis lon/lat, x/y ou des fractions."""
    if "lon" in label and "lat" in label:
        if target_crs is None:
            return float(label["lon"]), float(label["lat"])
        xs, ys = transform(
            "EPSG:4326",
            target_crs,
            [float(label["lon"])],
            [float(label["lat"])],
        )
        return float(xs[0]), float(ys[0])
    return _resolve_label_xy(label, x, y)


def _z_at_xy(x0: float, y0: float, x: np.ndarray, y: np.ndarray, z: np.ndarray) -> float:
    """Extraire l'altitude de surface la plus proche d'une coordonnée."""
    col = int(np.nanargmin(np.abs(x - x0)))
    row = int(np.nanargmin(np.abs(y - y0)))
    z0 = z[row, col]
    if np.isfinite(z0):
        return float(z0)
    return float(np.nanmean(z))


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
    cmap_center: Optional[float] = None,
    figure_size: Tuple[float, float] = (12, 7),
    dpi: int = 200,
    tight_layout: bool = True,
    tight_pad_inches: float = 0.15,
    surface_max_samples: int = 600,
    base_level: Optional[float] = None,
    block_base_depth: Optional[float] = None,
    use_texture: Optional[bool] = None,
    texture_path: Optional[str | Path] = None,
    align_dem_to_texture: bool = True,
    bathymetry_path: Optional[str | Path] = None,
    use_bathymetry: bool = False,
    bathymetry_crs: Optional[str | CRS] = None,
    bathymetry_water_margin: float = 0.5,
    shade_azimuth: float = 315,
    shade_altitude: float = 45,
    shade_fraction: float = 1.25,
    shade_blend_mode: str = "soft",
    texture_brightness: float = 1.25,
    texture_gamma: float = 0.85,
    show_sea: bool = True,
    sea_position: str = "front",
    sea_level: float = 0.0,
    clip_below_sea_level: bool = False,
    flatten_below_sea_level: bool = False,
    sea_margin: float = 0.08,
    sea_color: str = "#9ddfe7",
    show_base: bool = True,
    base_color: str = "#6f7b79",
    side_color: str = "#78827f",
    front_side_color: str = "#8f907f",
    show_block_edges: bool = False,
    block_edge_color: str = "#222222",
    block_edge_width: float = 0.8,
    color_surface_boundary: bool = True,
    surface_boundary_cells: int = 2,
    show_coastline: bool = False,
    coastline_color: str = "#111111",
    coastline_width: float = 1.0,
    labels: Optional[Sequence[LabelSpec]] = None,
    label_height_ratio: float = 0.45,
    labels_in_front: bool = True,
    box_zoom: float = 1.0,
    title: Optional[str] = None,
    credit: Optional[str] = None,
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
    tight_layout : bool
        Si True, recadre l'image autour des éléments visibles. Désactiver pour
        conserver la taille pixel attendue ``figure_size * dpi``.
    surface_max_samples : int
        Nombre maximal de lignes/colonnes utilisées par ``plot_surface`` pour
        la surface texturée. Augmenter cette valeur réduit l'effet pixelisé,
        mais ralentit fortement le rendu.
    base_level : float, optional
        Altitude de base du bloc. Si None, prend le minimum du relief exagéré.
    block_base_depth : float, optional
        Épaisseur minimale du bloc sous le niveau de référence, en unités Z
        avant exagération verticale. Utile pour obtenir des faces visibles
        autour des zones en eau.
    use_texture : bool, optional
        Active l'application d'une texture raster sur la surface supérieure.
        Si None, utilise la constante globale ``USE_TEXTURE``.
    texture_path : str | pathlib.Path, optional
        Chemin vers la texture géoréférencée (GeoTIFF recommandé).
        Si None, utilise ``TEXTURE_PATH``.
    align_dem_to_texture : bool
        Si True, rééchantillonne le MNT sur la grille de la texture avant le
        rendu. Cela évite les décalages visibles entre image satellite et relief.
    shade_azimuth, shade_altitude, shade_fraction : float
        Paramètres de l'ombrage appliqué à la surface supérieure.
    texture_brightness : float
        Multiplicateur de luminosité appliqué aux textures raster RGB.
    texture_gamma : float
        Correction gamma appliquée aux textures. Une valeur sous 1 éclaircit
        les tons moyens.
    show_sea : bool
        Ajoute un plan d'eau autour du bloc.
    sea_position : {"front", "full"}
        Position du plan d'eau. ``front`` crée une bande d'avant-plan, ``full``
        couvre toute l'emprise élargie.
    clip_below_sea_level : bool
        Masque la surface topographique sous ``sea_level`` pour laisser le plan
        d'eau visible.
    flatten_below_sea_level : bool
        Ramène les zones sous ``sea_level`` au niveau de la mer tout en gardant
        la texture satellite.
    show_base : bool
        Ajoute une base horizontale pleine sous le bloc.
    show_block_edges : bool
        Dessine les arêtes du cadre du bloc pour renforcer l'effet de tranche.
    block_edge_color, block_edge_width : str, float
        Style des arêtes du bloc.
    labels : sequence of mappings, optional
        Annotations verticales. Chaque entrée doit contenir ``text`` et soit
        ``x``/``y`` en coordonnées du rendu, soit ``xy_fraction`` dans
        l'emprise (0..1, 0..1).
    title, credit : str, optional
        Texte d'habillage ajouté en bas de la figure.

    Returns
    -------
    matplotlib.figure.Figure
        Figure générée (utile pour ajustements en aval).
    """
    if vertical_exaggeration <= 0:
        raise ValueError("vertical_exaggeration doit être strictement positif.")
    if shade_fraction <= 0:
        raise ValueError("shade_fraction doit être strictement positif.")
    if texture_brightness <= 0:
        raise ValueError("texture_brightness doit être strictement positif.")
    if texture_gamma <= 0:
        raise ValueError("texture_gamma doit être strictement positif.")
    if surface_max_samples <= 0:
        raise ValueError("surface_max_samples doit être strictement positif.")
    if tight_pad_inches < 0:
        raise ValueError("tight_pad_inches doit etre positif ou nul.")
    if block_base_depth is not None and block_base_depth <= 0:
        raise ValueError("block_base_depth doit être strictement positif.")
    if block_edge_width <= 0:
        raise ValueError("block_edge_width doit être strictement positif.")
    if surface_boundary_cells < 0:
        raise ValueError("surface_boundary_cells doit etre positif ou nul.")
    if coastline_width <= 0:
        raise ValueError("coastline_width doit etre strictement positif.")
    if sea_margin < 0:
        raise ValueError("sea_margin doit être positif ou nul.")
    if sea_position not in {"front", "full"}:
        raise ValueError("sea_position doit valoir 'front' ou 'full'.")
    if box_zoom <= 0:
        raise ValueError("box_zoom doit etre strictement positif.")
    if bathymetry_water_margin < 0:
        raise ValueError("bathymetry_water_margin doit etre positif ou nul.")

    use_texture_resolved = USE_TEXTURE if use_texture is None else use_texture
    texture_path_resolved = TEXTURE_PATH if texture_path is None else texture_path

    z, x, y, _, dem_transform, dem_crs = _load_dem_core(dem_path, bounds=bounds)
    if use_texture_resolved and texture_path_resolved and align_dem_to_texture:
        z, x, y, dem_transform, dem_crs = _resample_dem_to_match_texture(
            z,
            src_transform=dem_transform,
            src_crs=dem_crs,
            texture_path=texture_path_resolved,
        )

    if use_bathymetry and bathymetry_path is not None:
        bathymetry = _load_single_band_on_grid(
            bathymetry_path,
            target_shape=z.shape,
            target_transform=dem_transform,
            target_crs=dem_crs,
            source_crs=bathymetry_crs,
        )
        if bathymetry is not None:
            water_mask = (
                np.isfinite(bathymetry)
                & (bathymetry <= sea_level)
                & (~np.isfinite(z) | (z <= sea_level + bathymetry_water_margin))
            )
            print(
                "[bathymetry] Replacing DEM water pixels: "
                f"{int(np.count_nonzero(water_mask))} / {water_mask.size} "
                f"(min={float(np.nanmin(bathymetry)):.2f}, "
                f"max={float(np.nanmax(bathymetry)):.2f})"
            )
            z = np.where(water_mask, bathymetry, z)
        else:
            print("[bathymetry] No bathymetry raster loaded; DEM unchanged.")

    xx, yy = np.meshgrid(x, y)
    zz = z * vertical_exaggeration
    z_min = float(np.nanmin(zz))
    z_sea = sea_level * vertical_exaggeration
    if base_level is not None:
        z_base = float(base_level)
    elif block_base_depth is not None:
        z_base = min(z_min, z_sea) - float(block_base_depth) * vertical_exaggeration
    else:
        z_base = z_min
    zz_top = np.where(np.isnan(zz), z_base, zz)

    fig = plt.figure(figsize=figure_size)
    ax = fig.add_subplot(111, projection="3d")
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    texture_rgb = None
    if use_texture_resolved and texture_path_resolved:
        texture_rgb = _load_texture_on_grid(
            texture_path_resolved,
            target_shape=zz_top.shape,
            target_transform=dem_transform,
            target_crs=dem_crs,
        )

    facecolors = _surface_facecolors(
        zz_top,
        cmap=cmap,
        cmap_center=cmap_center,
        azimuth=shade_azimuth,
        altitude=shade_altitude,
        texture_rgb=texture_rgb,
        shade_fraction=shade_fraction,
        shade_blend_mode=shade_blend_mode,
        texture_brightness=texture_brightness,
        texture_gamma=texture_gamma,
    )
    zz_surface = zz_top
    if flatten_below_sea_level:
        sea_mask = ~np.isfinite(z) | (z <= sea_level)
        zz_surface = np.where(sea_mask, z_sea, zz_surface)
    if clip_below_sea_level:
        land_mask = np.isfinite(z) & (z > sea_level)
        zz_surface = np.where(land_mask, zz_top, np.nan)
        facecolors = np.array(facecolors, copy=True)
        if facecolors.shape[-1] == 3:
            alpha = np.where(land_mask, 1.0, 0.0)
            facecolors = np.dstack((facecolors, alpha))
        else:
            facecolors[..., 3] = np.where(land_mask, facecolors[..., 3], 0.0)

    if color_surface_boundary and surface_boundary_cells > 0:
        facecolors = np.array(facecolors, copy=True)
        if facecolors.shape[-1] == 3:
            facecolors = np.dstack((facecolors, np.ones(facecolors.shape[:2])))
        n_rows = min(surface_boundary_cells, facecolors.shape[0])
        n_cols = min(surface_boundary_cells, facecolors.shape[1])
        side_rgba = np.asarray(to_rgba(side_color), dtype=float)
        front_rgba = np.asarray(to_rgba(front_side_color), dtype=float)
        facecolors[:, :n_cols, :] = side_rgba
        facecolors[:, -n_cols:, :] = side_rgba
        facecolors[:n_rows, :, :] = front_rgba
        facecolors[-n_rows:, :, :] = front_rgba

    if show_sea:
        x_span = abs(float(x[-1] - x[0]))
        y_span = abs(float(y[-1] - y[0]))
        sea_x = np.array([x[0] - x_span * sea_margin, x[-1] + x_span * sea_margin])
        if sea_position == "front":
            sea_y = np.array([y[0] - y_span * sea_margin, y[0]])
        else:
            sea_y = np.array([y[0] - y_span * sea_margin, y[-1] + y_span * sea_margin])
        sea_xx, sea_yy = np.meshgrid(sea_x, sea_y)
        sea_zz = np.full_like(sea_xx, z_sea, dtype=float)
        ax.plot_surface(
            sea_xx,
            sea_yy,
            sea_zz,
            color=sea_color,
            linewidth=0,
            antialiased=False,
            alpha=0.72,
            shade=False,
        )

    top_surface_kwargs = dict(
        facecolors=facecolors,
        shade=False,
        linewidth=0,
        edgecolor="none",
        antialiased=False,
        rcount=min(zz.shape[0], surface_max_samples),
        ccount=min(zz.shape[1], surface_max_samples),
    )

    if show_base:
        base_zz = np.full_like(xx, z_base, dtype=float)
        ax.plot_surface(
            xx,
            yy,
            base_zz,
            facecolors=_solid_facecolors(base_zz.shape, base_color),
            linewidth=0,
            edgecolor="none",
            antialiased=False,
            shade=False,
        )

    ax.plot_surface(
        xx,
        yy,
        zz_surface,
        **top_surface_kwargs,
    )

    # Faces latérales verticales pour fermer le volume.
    x0 = np.array([x[0], x[0]])
    x1 = np.array([x[-1], x[-1]])
    y0 = np.array([y[0], y[0]])
    y1 = np.array([y[-1], y[-1]])

    zz_wall_top = np.where(np.isnan(zz_surface), z_base, zz_surface)
    top_left = zz_wall_top[:, 0]
    top_right = zz_wall_top[:, -1]
    top_front = zz_wall_top[0, :]
    top_back = zz_wall_top[-1, :]

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
        facecolors=_solid_facecolors(z_left.shape, side_color),
        linewidth=0,
        edgecolor="none",
        antialiased=False,
        shade=False,
    )
    ax.plot_surface(
        np.tile(x1, (len(y), 1)),
        np.tile(y_col, (1, 2)),
        z_right,
        facecolors=_solid_facecolors(z_right.shape, side_color),
        linewidth=0,
        edgecolor="none",
        antialiased=False,
        shade=False,
    )
    ax.plot_surface(
        np.tile(x_col, (1, 2)),
        np.tile(y0, (len(x), 1)),
        z_front,
        facecolors=_solid_facecolors(z_front.shape, front_side_color),
        linewidth=0,
        edgecolor="none",
        antialiased=False,
        shade=False,
    )
    ax.plot_surface(
        np.tile(x_col, (1, 2)),
        np.tile(y1, (len(x), 1)),
        z_back,
        facecolors=_solid_facecolors(z_back.shape, front_side_color),
        linewidth=0,
        edgecolor="none",
        antialiased=False,
        shade=False,
    )

    if show_block_edges:
        edge_kwargs = {
            "color": block_edge_color,
            "linewidth": block_edge_width,
            "alpha": 0.9,
        }
        ax.plot(x, np.full_like(x, y[0]), top_front, **edge_kwargs)
        ax.plot(x, np.full_like(x, y[-1]), top_back, **edge_kwargs)
        ax.plot(np.full_like(y, x[0]), y, top_left, **edge_kwargs)
        ax.plot(np.full_like(y, x[-1]), y, top_right, **edge_kwargs)

        ax.plot([x[0], x[-1]], [y[0], y[0]], [z_base, z_base], **edge_kwargs)
        ax.plot([x[0], x[-1]], [y[-1], y[-1]], [z_base, z_base], **edge_kwargs)
        ax.plot([x[0], x[0]], [y[0], y[-1]], [z_base, z_base], **edge_kwargs)
        ax.plot([x[-1], x[-1]], [y[0], y[-1]], [z_base, z_base], **edge_kwargs)

        corner_tops = [
            top_front[0],
            top_front[-1],
            top_back[0],
            top_back[-1],
        ]
        corner_xy = [
            (x[0], y[0]),
            (x[-1], y[0]),
            (x[0], y[-1]),
            (x[-1], y[-1]),
        ]
        for (corner_x, corner_y), corner_top in zip(corner_xy, corner_tops):
            ax.plot(
                [corner_x, corner_x],
                [corner_y, corner_y],
                [z_base, corner_top],
                **edge_kwargs,
            )

    if show_coastline:
        ax.contour(
            xx,
            yy,
            zz_top,
            levels=[z_sea],
            colors=[coastline_color],
            linewidths=coastline_width,
            linestyles="solid",
            zorder=10,
        )

    ax.view_init(elev=elevation, azim=azimuth)
    ax.set_box_aspect(
        (
            abs(float(x[-1] - x[0])),
            abs(float(y[-1] - y[0])),
            max(abs(float(np.nanmax(zz_top) - z_base)), 1.0),
        ),
        zoom=box_zoom,
    )
    ax.margins(0)
    fig.canvas.draw()

    if labels:
        z_range = float(np.nanmax(zz_top) - np.nanmin(zz_top))
        default_label_top = float(np.nanmax(zz_top) + z_range * label_height_ratio)
        for label in labels:
            label_x, label_y = _resolve_label_xy_any(label, x, y, dem_crs)
            label_z0 = _z_at_xy(label_x, label_y, x, y, zz_top)
            label_z1 = float(label.get("z", default_label_top))
            ax.plot(
                [label_x, label_x],
                [label_y, label_y],
                [label_z0, label_z1],
                color=label.get("color", "#222222"),
                linewidth=float(label.get("linewidth", 1.1)),
                zorder=1000,
            )
            if labels_in_front:
                x2, y2, _ = proj3d.proj_transform(label_x, label_y, label_z1, ax.get_proj())
                display_xy = ax.transData.transform((x2, y2))
                figure_xy = fig.transFigure.inverted().transform(display_xy)
                fig.text(
                    figure_xy[0],
                    figure_xy[1],
                    str(label["text"]),
                    color=label.get("color", "#111111"),
                    fontsize=float(label.get("fontsize", 16)),
                    ha=label.get("ha", "center"),
                    va=label.get("va", "bottom"),
                    fontfamily=label.get("fontfamily", "serif"),
                    zorder=10000,
                    bbox=label.get(
                        "bbox",
                        {
                            "facecolor": "white",
                            "edgecolor": "none",
                            "alpha": 0.72,
                            "pad": 0.8,
                        },
                    ),
                )
            else:
                ax.text(
                    label_x,
                    label_y,
                    label_z1,
                    str(label["text"]),
                    color=label.get("color", "#111111"),
                    fontsize=float(label.get("fontsize", 16)),
                    ha=label.get("ha", "center"),
                    va=label.get("va", "bottom"),
                    fontfamily=label.get("fontfamily", "serif"),
                    zorder=1000,
                )

    ax.set_axis_off()

    if title:
        fig.text(0.04, 0.045, title, ha="left", va="bottom", fontsize=11)
    if credit:
        fig.text(
            0.012,
            0.075,
            credit,
            ha="left",
            va="bottom",
            rotation=90,
            fontsize=7,
            color="white",
        )

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    savefig_kwargs = {"dpi": dpi}
    if tight_layout:
        savefig_kwargs["bbox_inches"] = "tight"
        savefig_kwargs["pad_inches"] = tight_pad_inches
    fig.savefig(output_path, **savefig_kwargs)

    return fig


__all__ = ["load_dem", "create_block_diagram"]
