from pathlib import Path
import sys

SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from utils.download_data import download_satellite_image
from utils.diagramme import create_block_diagram

bbox_precheur = (-61.25, 14.78, -61.18, 14.86)

download_satellite_image(
    bbox=bbox_precheur,
    output_tif="data/raw/satellite/precheur_copernicus_s2_10m.tif",
    provider="copernicus",
    resolution=10,
    max_cloud_cover=20,
    days_back=180,
)

create_block_diagram(
    "data/raw/elevation/precheur.tif",
    "output_bloc_copernicus.png",
    use_texture=True,
    texture_path="data/raw/satellite/precheur_copernicus_s2_10m.tif",
    azimuth=230,
    elevation=28,
    vertical_exaggeration=1.2,
    flatten_below_sea_level=True,
    show_base=True,
)
