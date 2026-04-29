from pathlib import Path
import sys

SRC_DIR = Path(__file__).resolve().parents[2]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from utils.diagramme import create_block_diagram
from utils.download_data import (
    download_elevation,
    download_gebco_bathymetry,
    download_shom_homonim_bathymetry,
)


# Test sans image satellite : relief terrestre COP30 + bathymetrie SHOM prioritaire.
# Ordre: ouest, sud, est, nord en EPSG:4326.
BBOX_PRECHEUR = (-61.2501, 14.7889, -61.1802, 14.8313)

DEM_PATH = "data/raw/elevation/precheur.tif"
SHOM_BATHYMETRY_DIR = "data/raw/elevation/shom_ants100m"
GEBCO_BATHYMETRY_PATH = "data/raw/elevation/gebco_precheur.tif"
OUTPUT_PATH = "figures/cartes/output_bloc_precheur_mnt_bathymetrie.png"


download_elevation(
    bbox=BBOX_PRECHEUR,
    dataset="COP30",
    output_tif=DEM_PATH,
    force_download=False,
)

bathymetry_source = "SHOM HOMONIM NM"
try:
    bathymetry_path = download_shom_homonim_bathymetry(
        output_dir=SHOM_BATHYMETRY_DIR,
        vertical_reference="NM",
        force_download=False,
    )
except Exception as exc:
    print(f"[bathymetry] SHOM automatic download failed: {exc}")
    download_gebco_bathymetry(
        bbox=BBOX_PRECHEUR,
        output_tif=GEBCO_BATHYMETRY_PATH,
        force_download=False,
    )
    bathymetry_path = Path(GEBCO_BATHYMETRY_PATH)
    bathymetry_source = "GEBCO fallback"
    print(f"[bathymetry] Falling back to GEBCO: {bathymetry_path}")

create_block_diagram(
    DEM_PATH,
    OUTPUT_PATH,
    bounds=BBOX_PRECHEUR,
    use_texture=False,
    align_dem_to_texture=False,
    use_bathymetry=True,
    bathymetry_path=bathymetry_path,
    bathymetry_crs="EPSG:4326",
    bathymetry_water_margin=2.0,
    cmap="topobathy",
    cmap_center=0.0,
    azimuth=230,
    elevation=34,
    vertical_exaggeration=1.25,
    block_base_depth=350,
    figure_size=(13, 8.5),
    dpi=300,
    tight_layout=True,
    tight_pad_inches=0.35,
    box_zoom=1.05,
    surface_max_samples=1600,
    flatten_below_sea_level=False,
    show_base=True,
    base_color="#2f312d",
    side_color="#353831",
    front_side_color="#30332e",
    show_block_edges=True,
    block_edge_color="#101010",
    block_edge_width=0.75,
    color_surface_boundary=False,
    show_coastline=True,
    coastline_color="#171717",
    coastline_width=1.4,
    show_sea=False,
    shade_azimuth=315,
    shade_altitude=45,
    shade_fraction=0.75,
    shade_blend_mode="soft",
    labels=[
        {
            "text": "Le Precheur",
            "lon": -61.2249,
            "lat": 14.8015,
            "fontsize": 11,
        },
        {
            "text": "Anse Ceron",
            "lon": -61.2307,
            "lat": 14.8157,
            "fontsize": 10,
        },
        {
            "text": "Habitation Ceron",
            "lon": -61.2238,
            "lat": 14.8172,
            "fontsize": 10,
        },
        {
            "text": "Riviere du Precheur",
            "lon": -61.2170,
            "lat": 14.8058,
            "fontsize": 10,
        },
        {
            "text": "Grande Savane",
            "lon": -61.1888,
            "lat": 14.8118,
            "fontsize": 10,
        },
        {
            "text": "Flanc ouest\nde la Montagne Pelee",
            "lon": -61.1815,
            "lat": 14.8096,
            "fontsize": 11,
        },
    ],
    label_height_ratio=0.32,
    title="Bloc diagramme MNT et bathymetrie du Precheur",
    credit=f"Modele SIG - COP30 DEM / bathymetrie {bathymetry_source}",
)

print(f"Bloc diagramme exported to: {OUTPUT_PATH}")
