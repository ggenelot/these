from pathlib import Path
import sys

SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from utils.diagramme import create_block_diagram
from utils.download_data import download_satellite_image


BBOX_MARTINIQUE = (-61.30, 14.35, -60.75, 14.95)
DEM_PATH = "data/raw/elevation/cop30_dem.tif"
TEXTURE_PATH = "data/raw/satellite/martinique_copernicus_s2_30m.tif"
OUTPUT_PATH = "output_bloc_martinique.png"


download_satellite_image(
    bbox=BBOX_MARTINIQUE,
    output_tif=TEXTURE_PATH,
    provider="copernicus",
    resolution=30,
    max_cloud_cover=25,
    days_back=365,
    force_download=False,
)

create_block_diagram(
    DEM_PATH,
    OUTPUT_PATH,
    bounds=BBOX_MARTINIQUE,
    use_texture=True,
    texture_path=TEXTURE_PATH,
    align_dem_to_texture=True,
    azimuth=235,
    elevation=31,
    vertical_exaggeration=2,
    figure_size=(16, 10),
    dpi=600,
    tight_layout=False,
    surface_max_samples=1400,
    texture_brightness=1.4,
    texture_gamma=0.8,
    flatten_below_sea_level=True,
    show_base=True,
    show_sea=False,
    sea_position="front",
    sea_margin=0.12,
    shade_azimuth=315,
    shade_altitude=45,
    shade_fraction=0.9,
    labels=[
        {"text": "Montagne Pelee\n(1395 m)", "xy_fraction": (0.24, 0.86), "fontsize": 11},
        {"text": "Pitons du Carbet\n(1117 m)", "xy_fraction": (0.42, 0.68), "fontsize": 11},
        {"text": "Morne Jacob\n(884 m)", "xy_fraction": (0.49, 0.63), "fontsize": 11},
        {
            "text": "Morne Balata\nMorne Pavillon\n(337 m)",
            "xy_fraction": (0.58, 0.52),
            "fontsize": 10,
        },
        {
            "text": "Montagne du\nVauclin\n(504 m)",
            "xy_fraction": (0.72, 0.36),
            "fontsize": 10,
        },
        {"text": "Morne Larcher\n(478 m)", "xy_fraction": (0.34, 0.29), "fontsize": 10},
        {"text": "Morne Gardier\n(400 m)", "xy_fraction": (0.50, 0.24), "fontsize": 10},
        {"text": "Presqu'ile\ndu Diamant", "xy_fraction": (0.26, 0.22), "fontsize": 10},
        {"text": "Presqu'ile\nde Sainte-Anne", "xy_fraction": (0.82, 0.10), "fontsize": 10},
    ],
    title="Bloc diagramme de la Martinique",
    credit="Modele SIG - Copernicus Sentinel-2 L2A / COP30 DEM",
)

print(f"Bloc diagramme exported to: {OUTPUT_PATH}")
