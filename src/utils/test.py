from diagramme import *
from download_data import *

bbox_precheur = (-61.25, 14.78, -61.18, 14.86)
dem_path = "data/raw/elevation/precheur.tif"

#download_elevation(bbox=bbox_precheur, output_tif=dem_path)

create_block_diagram(dem_path, "output.png", azimuth=120, vertical_exaggeration=1)
