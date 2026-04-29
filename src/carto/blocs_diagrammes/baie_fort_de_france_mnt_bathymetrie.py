from pathlib import Path
import sys

SRC_DIR = Path(__file__).resolve().parents[2]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from utils.diagramme import create_block_diagram
from utils.download_data import (
    download_elevation,
    download_gebco_bathymetry,
    download_litto3d_martinique,
    download_shom_homonim_bathymetry,
)


# Ordre: ouest, sud, est, nord en EPSG:4326.
# BBOX_BAIE_FORT_DE_FRANCE = (-61.08295, 14.57162, -60.97086, 14.63408)
BBOX_PRECHEUR = (-61.2714, 14.7889, -61.1589, 14.8313)
BBOX_BAIE_FORT_DE_FRANCE = BBOX_PRECHEUR

COP30_DEM_PATH = "data/raw/elevation/cop30_dem.tif"
LITTO3D_DEM_PATH = "data/raw/elevation/litto3d_baie_fort_de_france.tif"
SHOM_BATHYMETRY_DIR = "data/raw/elevation/shom_ants100m"
GEBCO_BATHYMETRY_PATH = "data/raw/elevation/gebco_baie_fort_de_france.tif"
LITTO3D_BATHYMETRY_PATH = LITTO3D_DEM_PATH
OUTPUT_PATH = "figures/cartes/output_bloc_baie_fort_de_france_mnt_bathymetrie.png"


def prepare_terrain(
    *,
    bbox=BBOX_BAIE_FORT_DE_FRANCE,
    terrain_source="cop30",
    litto3d_source_url=None,
    litto3d_source_path=None,
    litto3d_source_crs="EPSG:32620",
    force_download=False,
):
    """Return a DEM path and display label for the requested terrain source."""
    terrain_source = terrain_source.lower()
    if terrain_source == "cop30":
        dem_path = download_elevation(
            bbox=bbox,
            dataset="COP30",
            output_tif=COP30_DEM_PATH,
            force_download=force_download,
        )
        return dem_path, "COP30 DEM"

    if terrain_source == "litto3d":
        dem_path = download_litto3d_martinique(
            bbox=bbox,
            output_tif=LITTO3D_DEM_PATH,
            source_url=litto3d_source_url,
            source_path=litto3d_source_path,
            source_crs=litto3d_source_crs,
            force_download=force_download,
        )
        return dem_path, "Litto3D Martinique"

    raise ValueError("terrain_source must be 'cop30' or 'litto3d'.")


def prepare_bathymetry(
    *,
    bbox=BBOX_BAIE_FORT_DE_FRANCE,
    bathymetry_source="shom",
    litto3d_source_url=None,
    litto3d_source_path=None,
    litto3d_source_crs="EPSG:32620",
    force_download=False,
):
    """Return bathymetry options for create_block_diagram."""
    bathymetry_source = bathymetry_source.lower()
    if bathymetry_source in {"none", "off", "false"}:
        return {
            "use_bathymetry": False,
            "bathymetry_path": None,
            "bathymetry_crs": None,
            "label": "sans bathymetrie",
        }

    if bathymetry_source == "gebco":
        bathymetry_path = download_gebco_bathymetry(
            bbox=bbox,
            output_tif=GEBCO_BATHYMETRY_PATH,
            force_download=force_download,
        )
        return {
            "use_bathymetry": True,
            "bathymetry_path": bathymetry_path,
            "bathymetry_crs": None,
            "label": "GEBCO",
        }

    if bathymetry_source == "litto3d":
        bathymetry_path = download_litto3d_martinique(
            bbox=bbox,
            output_tif=LITTO3D_BATHYMETRY_PATH,
            source_url=litto3d_source_url,
            source_path=litto3d_source_path,
            source_crs=litto3d_source_crs,
            force_download=force_download,
        )
        return {
            "use_bathymetry": True,
            "bathymetry_path": bathymetry_path,
            "bathymetry_crs": None,
            "label": "Litto3D Martinique",
        }

    if bathymetry_source == "shom":
        bathymetry_label = "SHOM HOMONIM NM"
        try:
            bathymetry_path = download_shom_homonim_bathymetry(
                output_dir=SHOM_BATHYMETRY_DIR,
                vertical_reference="NM",
                force_download=force_download,
            )
        except Exception as exc:
            print(f"[bathymetry] SHOM automatic download failed: {exc}")
            bathymetry_path = download_gebco_bathymetry(
                bbox=bbox,
                output_tif=GEBCO_BATHYMETRY_PATH,
                force_download=force_download,
            )
            bathymetry_label = "GEBCO fallback"
            print(f"[bathymetry] Falling back to GEBCO: {bathymetry_path}")

        return {
            "use_bathymetry": True,
            "bathymetry_path": bathymetry_path,
            "bathymetry_crs": "EPSG:4326",
            "label": bathymetry_label,
        }

    raise ValueError("bathymetry_source must be 'shom', 'gebco', 'litto3d' or 'none'.")


def create_image(
    *,
    bbox=BBOX_BAIE_FORT_DE_FRANCE,
    output_path=OUTPUT_PATH,
    terrain_source="cop30",
    bathymetry_source="shom",
    litto3d_source_url=None,
    litto3d_source_path=None,
    litto3d_source_crs="EPSG:32620",
    force_download=False,
):
    """Create the block diagram using selectable terrain/bathymetry sources."""
    dem_path, terrain_label = prepare_terrain(
        bbox=bbox,
        terrain_source=terrain_source,
        litto3d_source_url=litto3d_source_url,
        litto3d_source_path=litto3d_source_path,
        litto3d_source_crs=litto3d_source_crs,
        force_download=force_download,
    )
    bathymetry = prepare_bathymetry(
        bbox=bbox,
        bathymetry_source=bathymetry_source,
        litto3d_source_url=litto3d_source_url,
        litto3d_source_path=litto3d_source_path,
        litto3d_source_crs=litto3d_source_crs,
        force_download=force_download,
    )
    render_bounds = None if terrain_source.lower() == "litto3d" else bbox

    figure = create_block_diagram(
        dem_path,
        output_path,
        bounds=render_bounds,
        use_texture=False,
        align_dem_to_texture=False,
        use_bathymetry=bathymetry["use_bathymetry"],
        bathymetry_path=bathymetry["bathymetry_path"],
        bathymetry_crs=bathymetry["bathymetry_crs"],
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
        credit=(
            "Modele SIG - "
            f"{terrain_label} / bathymetrie {bathymetry['label']}"
        ),
    )
    print(f"Bloc diagramme exported to: {output_path}")
    return figure


if __name__ == "__main__":
    create_image()
