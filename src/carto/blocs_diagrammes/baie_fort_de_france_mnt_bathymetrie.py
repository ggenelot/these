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
#BBOX_BAIE_FORT_DE_FRANCE = (-61.08295, 14.57162, -60.97086, 14.63408)
BBOX_PRECHEUR = (-61.2714, 14.7889,-61.1589,14.8313)
BBOX_BAIE_FORT_DE_FRANCE = BBOX_PRECHEUR

DEM_PATH = "data/raw/elevation/cop30_dem.tif"
SHOM_BATHYMETRY_DIR = "data/raw/elevation/shom_ants100m"
GEBCO_BATHYMETRY_PATH = "data/raw/elevation/gebco_baie_fort_de_france.tif"
OUTPUT_PATH = "figures/cartes/output_bloc_baie_fort_de_france_mnt_bathymetrie.png"


download_elevation(
    bbox=BBOX_BAIE_FORT_DE_FRANCE,
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
        bbox=BBOX_BAIE_FORT_DE_FRANCE,
        output_tif=GEBCO_BATHYMETRY_PATH,
        force_download=False,
    )
    bathymetry_path = Path(GEBCO_BATHYMETRY_PATH)
    bathymetry_source = "GEBCO fallback"
    print(f"[bathymetry] Falling back to GEBCO: {bathymetry_path}")

create_block_diagram(
    DEM_PATH,
    OUTPUT_PATH,
    bounds=BBOX_BAIE_FORT_DE_FRANCE,
    use_texture=False,
    align_dem_to_texture=False,
    use_bathymetry=True,
    bathymetry_path=bathymetry_path,
    bathymetry_crs="EPSG:4326",
    bathymetry_water_margin=2.0,
    cmap="topobathy",
    cmap_center=0.0,
    azimuth=230,
    elevation=33,
    vertical_exaggeration=1.0,
    block_base_depth=300,
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
            "text": "Trois-Ilets",
            "xy_fraction": (0.48, 0.28),
            "fontsize": 10,
        },
        {
            "text": "Ducos",
            "xy_fraction": (0.77, 0.28),
            "fontsize": 10,
        },
    ],
    label_height_ratio=0.36,
    title="Bloc diagramme MNT et bathymetrie de la baie de Fort-de-France",
    credit=f"Modele SIG - COP30 DEM / bathymetrie {bathymetry_source}",
)

print(f"Bloc diagramme exported to: {OUTPUT_PATH}")
