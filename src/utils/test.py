from diagramme import *
from download_data import *

bbox_precheur = (-61.25, 14.78, -61.18, 14.86)
dem_path = "data/raw/elevation/precheur.tif"
sat_path = "data/raw/satellite/precheur_s2.tif"

#download_elevation(bbox=bbox_precheur, output_tif=dem_path)
#download_satellite_image(bbox=(-61.25, 14.78, -61.18, 14.86), output_tif=sat_path)


create_block_diagram(dem_path, 
                     use_texture=True, 
                     texture_path=sat_path, 
                     output_path="output.png", 
                     azimuth=270, 
                     vertical_exaggeration=1
                     )
