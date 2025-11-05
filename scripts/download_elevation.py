import os
import requests
import rasterio
from rasterio.plot import show
import geopandas as gpd

# -----------------------------------------------------------
# 1. Load API key (from environment or .env file)
# -----------------------------------------------------------
API_KEY = os.getenv("OPENTOPO_API_KEY")

if not API_KEY:
    raise ValueError("❌ No API key found! Please set OPENTOPO_API_KEY as an environment variable.")

# -----------------------------------------------------------
# 2. Define the area of interest
#    Option A: Bounding box (west, south, east, north)
#    Option B: Shapefile (.shp) - automatically computes bounds
# -----------------------------------------------------------

# Bounding box around Martinique (west, south, east, north)
bbox = (-61.25, 14.35, -60.75, 14.95)

# If you prefer to use a shapefile, uncomment this:
# gdf = gpd.read_file("your_area.shp")
# minx, miny, maxx, maxy = gdf.total_bounds
# bbox = (minx, miny, maxx, maxy)

# -----------------------------------------------------------
# 3. Download COP30 DEM from OpenTopography
# -----------------------------------------------------------
dataset = "COP30"
output_tif = "data/raw/elevation/cop30_dem.tif"

url = (
    f"https://portal.opentopography.org/API/globaldem?"
    f"demtype={dataset}&south={bbox[1]}&north={bbox[3]}"
    f"&west={bbox[0]}&east={bbox[2]}"
    f"&outputFormat=GTiff&API_Key={API_KEY}"
)

print(f"🌍 Downloading {dataset} DEM from OpenTopography...")
print("🔗 URL:", url)

response = requests.get(url)

if response.status_code == 200:
    with open(output_tif, "wb") as f:
        f.write(response.content)
    print(f"✅ Download complete! File saved as: {output_tif}")
else:
    print(f"❌ API error ({response.status_code}): {response.text}")
    exit()

# -----------------------------------------------------------
# 4. Inspect the DEM
# -----------------------------------------------------------
with rasterio.open(output_tif) as src:
    print("\n--- DEM Metadata ---")
    print("Projection:", src.crs)
    print("Resolution:", src.res)
    print("Bounds:", src.bounds)
    show(src, title=f"OpenTopography {dataset} DEM")
