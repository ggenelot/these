from pathlib import Path
import sys

SRC_DIR = Path(__file__).resolve().parents[2]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from utils.diagramme import create_block_diagram
from utils.download_data import download_elevation


# Rendu type atlas de la Martinique, sans image satellite.
# Ordre: ouest, sud, est, nord en EPSG:4326.
BBOX_MARTINIQUE = (-61.30, 14.35, -60.75, 14.95)

DEM_PATH = "data/raw/elevation/cop30_dem_martinique.tif"
OUTPUT_PATH = "figures/cartes/output_bloc_martinique_atlas.png"


download_elevation(
    bbox=BBOX_MARTINIQUE,
    dataset="COP30",
    output_tif=DEM_PATH,
    force_download=False,
)

create_block_diagram(
    DEM_PATH,
    OUTPUT_PATH,
    bounds=BBOX_MARTINIQUE,
    use_texture=False,
    align_dem_to_texture=False,
    cmap="topobathy",
    cmap_center=0.0,
    azimuth=238,
    elevation=34,
    vertical_exaggeration=2.1,
    block_base_depth=900,
    figure_size=(13, 8.5),
    dpi=300,
    tight_layout=True,
    tight_pad_inches=0.45,
    box_zoom=1.02,
    surface_max_samples=1700,
    flatten_below_sea_level=True,
    show_base=False,
    show_block_edges=False,
    color_surface_boundary=False,
    show_coastline=True,
    coastline_color="#155b4f",
    coastline_width=1.0,
    show_sea=True,
    sea_position="full",
    sea_margin=0.18,
    sea_color="#8bd6d6",
    shade_azimuth=315,
    shade_altitude=45,
    shade_fraction=0.72,
    shade_blend_mode="soft",
    labels=[
        {
            "text": "Montagne Pelee\n(1395 m)",
            "lon": -61.1656,
            "lat": 14.8096,
            "fontsize": 11,
            "z": 4300,
        },
        {
            "text": "Pitons du Carbet\n(1117 m)",
            "lon": -61.1250,
            "lat": 14.7005,
            "fontsize": 11,
            "z": 3800,
        },
        {
            "text": "Morne Jacob\n(884 m)",
            "lon": -61.0675,
            "lat": 14.7160,
            "fontsize": 10,
            "z": 3400,
        },
        {
            "text": "Morne Balata (337 m)\nMorne Pavillon (337 m)",
            "lon": -61.0600,
            "lat": 14.6450,
            "fontsize": 10,
            "z": 3600,
        },
        {
            "text": "Montagne du\nVauclin\n(504 m)",
            "lon": -60.8655,
            "lat": 14.5450,
            "fontsize": 10,
            "z": 3000,
        },
        {
            "text": "Morne Bigot (395 m)\nMorne le Plaine (395 m)\nMorne Genty (397 m)\nMorne Larcher (478 m)",
            "lon": -61.0600,
            "lat": 14.4900,
            "fontsize": 9,
            "z": 1450,
        },
        {
            "text": "Morne Gardier\n(400 m)",
            "lon": -61.0050,
            "lat": 14.5000,
            "fontsize": 10,
            "z": 1150,
        },
        {
            "text": "Presqu'ile\ndu Diamant",
            "lon": -61.0800,
            "lat": 14.4700,
            "fontsize": 10,
            "z": 1600,
        },
        {
            "text": "Morne\ndu Sud",
            "lon": -60.8250,
            "lat": 14.4650,
            "fontsize": 10,
            "z": 1700,
        },
        {
            "text": "Presqu'ile\nde Sainte-Anne",
            "lon": -60.8400,
            "lat": 14.4300,
            "fontsize": 10,
            "z": 1150,
        },
    ],
    labels_in_front=True,
    label_height_ratio=0.34,
    title=None,
    credit="Modele SIG - COP30 DEM",
)

print(f"Bloc diagramme exported to: {OUTPUT_PATH}")
