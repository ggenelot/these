from pathlib import Path
import sys

SRC_DIR = Path(__file__).resolve().parents[2]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from utils.diagramme import create_block_diagram
from utils.download_data import (
    download_elevation,
    download_gebco_bathymetry,
    download_satellite_image,
)


# Grande echelle: emprise resserree autour de la baie de Fort-de-France.
# Ordre: ouest, sud, est, nord en EPSG:4326.
BBOX_BAIE_FORT_DE_FRANCE = (-61.08295, 14.57162, -60.97086, 14.63408)

DEM_PATH = "data/raw/elevation/cop30_dem.tif"
BATHYMETRY_PATH = "data/raw/elevation/gebco_baie_fort_de_france.tif"
TEXTURE_PATH = "data/raw/satellite/baie_fort_de_france_copernicus_s2_30m.tif"
OUTPUT_PATH = "figures/cartes/output_bloc_baie_fort_de_france.png"


download_elevation(
    bbox=BBOX_BAIE_FORT_DE_FRANCE,
    dataset="COP30",
    output_tif=DEM_PATH,
    force_download=False,
)

download_satellite_image(
    bbox=BBOX_BAIE_FORT_DE_FRANCE,
    output_tif=TEXTURE_PATH,
    provider="copernicus",
    # 30 m garde la requete Copernicus sous la limite 2500 x 2500 pixels
    # pour cette emprise. A 20 m ou 10 m, la grille demandee est trop grande.
    resolution=10,
    max_cloud_cover=30,
    days_back=365,
    force_download=False,
)

download_gebco_bathymetry(
    bbox=BBOX_BAIE_FORT_DE_FRANCE,
    output_tif=BATHYMETRY_PATH,
    force_download=False,
)

create_block_diagram(
    DEM_PATH,
    OUTPUT_PATH,
    bounds=BBOX_BAIE_FORT_DE_FRANCE,
    use_texture=True,
    texture_path=TEXTURE_PATH,
    align_dem_to_texture=True,
    use_bathymetry=True,
    bathymetry_path=BATHYMETRY_PATH,
    azimuth=230,
    elevation=33,
    vertical_exaggeration=2.6,
    block_base_depth=1800,
    figure_size=(13, 8.5),
    dpi=600,
    tight_layout=True,
    tight_pad_inches=0.35,
    box_zoom=1.05,
    surface_max_samples=1600,
    texture_brightness=1.35,
    texture_gamma=0.82,
    flatten_below_sea_level=False,
    show_base=True,
    show_block_edges=True,
    block_edge_color="#202020",
    block_edge_width=0.75,
    show_sea=False,
    shade_azimuth=315,
    shade_altitude=45,
    shade_fraction=0.9,
    labels=[
        {
            "text": "Pitons du Carbet",
            "xy_fraction": (0.25, 0.86),
            "fontsize": 11,
        },
        {
            "text": "Fort-de-France",
            "xy_fraction": (0.38, 0.61),
            "fontsize": 11,
        },
        {
            "text": "Baie de\nFort-de-France",
            "xy_fraction": (0.51, 0.45),
            "fontsize": 11,
        },
        {
            "text": "Le Lamentin",
            "xy_fraction": (0.72, 0.58),
            "fontsize": 10,
        },
        {
            "text": "Trois-Ilets",
            "xy_fraction": (0.48, 0.28),
            "fontsize": 10,
        },
        {
            "text": "Anses-d'Arlet",
            "xy_fraction": (0.28, 0.17),
            "fontsize": 10,
        },
        {
            "text": "Ducos",
            "xy_fraction": (0.77, 0.28),
            "fontsize": 10,
        },
    ],
    label_height_ratio=0.36,
    title="Bloc diagramme de la baie de Fort-de-France",
    credit="Modele SIG - Copernicus Sentinel-2 L2A / COP30 DEM / GEBCO bathymetry",
)

print(f"Bloc diagramme exported to: {OUTPUT_PATH}")
