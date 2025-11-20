import os
import requests
import json
from pathlib import Path
from terracatalogueclient import Catalogue 
import rasterio
from rasterio.plot import show
import geopandas as gpd

def download_elevation():
    # -----------------------------------------------------------
    # 1. Load API key (from environment or .env file)
    # -----------------------------------------------------------
    API_KEY = os.getenv("OPENTOPO_API_KEY")

    if not API_KEY:
        raise ValueError("No API key found! Please set OPENTOPO_API_KEY as an environment variable.")

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


def download_figshare():
    #---INSERT CODE TO COLLECT ITEM IDS HERE----

    # Or use this test set of ids that have small files (To use, delete the '#' in the next line)
    item_ids = [12706085]
    #item_ids = [17714843,153788] #test items
    folder_path = "data/raw/"


    #Set the base URL
    BASE_URL = 'https://api.figshare.com/v2'
    api_call_headers = {'Authorization': 'token $env:FIGSHARE_TOKEN'}

    file_info = [] #a blank list to hold all the file metadata

    print('Retrieving metadata')
    for i in item_ids:
        r = requests.get(BASE_URL + '/articles/' + str(i) + '/files')
        file_metadata = json.loads(r.text)
        for j in file_metadata: #add the item id to each file record- this is used later to name a folder to save the file to
            j['item_id'] = i
            file_info.append(j) #Add the file metadata to the list
    print('Files available' + str(file_info))

    #Download each file to a subfolder named for the article id and save with the file name
    for k in file_info:
        print('Downloading '+k['name'])
        print("Download URL : "+BASE_URL + '/file/download/' + str(k['id']))
        response = requests.get(BASE_URL + '/file/download/' + str(k['id']), headers=api_call_headers)
        dir_path = Path(folder_path) / str(k['item_id'])
        dir_path.mkdir(parents=True, exist_ok=True)
        file_path = dir_path / k['name']
        file_path.write_bytes(response.content)
        print(k['name']+ ' downloaded')
        
    print('All files have been downloaded in '+ str(folder_path))






def download_ESA():
    # create catalogue object and authenticate 
    catalogue = Catalogue().authenticate() 

    # search for products in the WorldCover collection 
    products = catalogue.get_products("urn:eop:VITO:ESA_WorldCover_10m_2020_V1") 

    # download the products to the given directory 
    catalogue.download_products(products, "downloads") 

    from shapely.geometry import Polygon 
    from terracatalogueclient import Catalogue 

    ### Authenticate to the Terrascope platform (registration required) 
    # create catalogue object and authenticate interactively with a browser 
    catalogue = Catalogue().authenticate()  

    # or authenticate with username and password 
    # catalogue = catalogue.authenticate_non_interactive(username, password) 

    ### Filter catalogue 
    # search for all products in the WorldCover collection 
    # products = catalogue.get_products("urn:eop:VITO:ESA_WorldCover_10m_2020_V1") 

    # or filter to a desired geometry, by providing it as an argument to get_products 

    bounds = (-61.3, 14.2, -60.75, 15.0)
    geometry = Polygon.from_bounds(*bounds)
    products = catalogue.get_products("urn:eop:VITO:ESA_WorldCover_10m_2020_V1", geometry=geometry) 

    ### Download 
    # download the products to the given directory 
    catalogue.download_products(products, "data/raw/ESA_worldcover")

from pathlib import Path
import sys
import logging
from urllib.parse import urlparse
import shutil

def download_filosofi(url: str = None) -> None:
    """
    Download a file and save it to data/raw relative to the repository root.
    If `requests` is available, uses it with a progress bar; otherwise falls back to urllib.
    """

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    # Default URL if none provided
    default_url = "https://www.insee.fr/fr/statistiques/fichier/6215138/Filosofi2017_carreaux_200m_gpkg.zip"
    url = url or default_url

    # Determine target directory (assumes script is in <repo>/scripts/)
    repo_root = Path(__file__).resolve().parent.parent
    out_dir = repo_root / "data" / "raw"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Determine filename
    fname = Path(urlparse(url).path).name or "downloaded.file"
    dest = out_dir / fname

    if dest.exists():
        logging.info("File already exists: %s", dest)
        return

    # Try using requests first
    try:
        import requests
        from tqdm import tqdm

        logging.info("Using requests to download %s -> %s", url, dest)
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            total = int(r.headers.get("content-length") or 0)
            chunk_size = 8192
            with dest.open("wb") as f, tqdm(
                total=(total if total else None),
                unit="B",
                unit_scale=True,
                desc=dest.name,
            ) as pbar:
                for chunk in r.iter_content(chunk_size=chunk_size):
                    if not chunk:
                        continue
                    f.write(chunk)
                    pbar.update(len(chunk))
        logging.info("Saved to %s", dest)

    except Exception:
        # fallback to urllib
        import urllib.request
        logging.info("Falling back to urllib to download %s -> %s", url, dest)
        with urllib.request.urlopen(url, timeout=30) as r, dest.open("wb") as f:
            shutil.copyfileobj(r, f)
        logging.info("Saved to %s", dest)


if __name__ == "__main__":
    # Optionally pass URL as the first argument
    download_file(sys.argv[1] if len(sys.argv) > 1 else None)


#download_figshare()
