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
from rasterio.windows import from_bounds


Bounds = Tuple[float, float, float, float]


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

    # Convertit le masque rasterio en NaN explicites pour matplotlib.
    z = np.where(np.ma.getmaskarray(z), np.nan, np.asarray(z))

    ny, nx = z.shape
    cols = np.arange(nx)
    rows = np.arange(ny)

    # Coordonnées des centres de pixels.
    x = transform.c + (cols + 0.5) * transform.a
    y = transform.f + (rows + 0.5) * transform.e

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

    Returns
    -------
    matplotlib.figure.Figure
        Figure générée (utile pour ajustements en aval).
    """
    if vertical_exaggeration <= 0:
        raise ValueError("vertical_exaggeration doit être strictement positif.")

    z, x, y, _ = load_dem(dem_path, bounds=bounds)

    xx, yy = np.meshgrid(x, y)
    zz = z * vertical_exaggeration

    fig = plt.figure(figsize=figure_size)
    ax = fig.add_subplot(111, projection="3d")

    surf = ax.plot_surface(
        xx,
        yy,
        zz,
        cmap=cmap,
        linewidth=0,
        antialiased=False,
        rcount=min(zz.shape[0], 300),
        ccount=min(zz.shape[1], 300),
    )

    ax.view_init(elev=elevation, azim=azimuth)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Altitude (exagérée)")
    ax.set_title("Bloc-diagramme (prototype)")

    cbar = fig.colorbar(surf, ax=ax, shrink=0.6, pad=0.08)
    cbar.set_label("Élévation")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight")

    return fig


__all__ = ["load_dem", "create_block_diagram"]
