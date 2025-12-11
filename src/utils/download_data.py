import os
import requests
import json
from pathlib import Path
from terracatalogueclient import Catalogue 
import rasterio
from rasterio.plot import show
from pathlib import Path
import sys
import logging
from urllib.parse import urlparse
import shutil

def download_elevation():
    """
    Download a Digital Elevation Model (DEM) from OpenTopography and inspect it.

    The function:
    1. Loads the OpenTopography API key from the environment variable `OPENTOPO_API_KEY`.
    2. Defines a bounding box (or optionally reads from a shapefile) for the area of interest.
    3. Downloads the COP30 DEM as a GeoTIFF to `data/raw/elevation/cop30_dem.tif`.
    4. Opens the DEM using `rasterio` and prints metadata, including CRS, resolution, and bounds.
    5. Displays the DEM using `rasterio.plot.show`.

    Raises
    ------
    ValueError
        If the API key is not found in the environment.
    SystemExit
        If the API request fails.
    """
    API_KEY = os.getenv("OPENTOPO_API_KEY")

    if not API_KEY:
        raise ValueError("No API key found! Please set OPENTOPO_API_KEY as an environment variable.")

    bbox = (-61.25, 14.35, -60.75, 14.95)
    dataset = "COP30"
    output_tif = "data/raw/elevation/cop30_dem.tif"

    url = (
        f"https://portal.opentopography.org/API/globaldem?"
        f"demtype={dataset}&south={bbox[1]}&north={bbox[3]}"
        f"&west={bbox[0]}&east={bbox[2]}"
        f"&outputFormat=GTiff&API_Key={API_KEY}"
    )

    print(f"Downloading {dataset} DEM from OpenTopography...")
    print("URL:", url)

    response = requests.get(url)
    if response.status_code == 200:
        with open(output_tif, "wb") as f:
            f.write(response.content)
        print(f"Download complete! File saved as: {output_tif}")
    else:
        print(f"API error ({response.status_code}): {response.text}")
        exit()

    with rasterio.open(output_tif) as src:
        print("\n--- DEM Metadata ---")
        print("Projection:", src.crs)
        print("Resolution:", src.res)
        print("Bounds:", src.bounds)
        show(src, title=f"OpenTopography {dataset} DEM")


def download_figshare():
    """
    Download files from Figshare given a list of article/item IDs.

    The function:
    1. Sets up the API base URL and authentication headers.
    2. Collects file metadata for each item ID.
    3. Downloads all files into `data/raw/<item_id>/<filename>` structure.

    Notes
    -----
    - Requires a Figshare personal access token stored in the environment variable `FIGSHARE_TOKEN`.
    - You can modify `item_ids` to include your desired Figshare article IDs.

    Raises
    ------
    requests.exceptions.RequestException
        If the API request fails.
    """
    item_ids = [12706085]
    folder_path = "data/raw/"
    BASE_URL = 'https://api.figshare.com/v2'
    api_call_headers = {'Authorization': 'token $env:FIGSHARE_TOKEN'}
    file_info = []

    print('Retrieving metadata')
    for i in item_ids:
        r = requests.get(BASE_URL + '/articles/' + str(i) + '/files')
        r.raise_for_status()
        file_metadata = json.loads(r.text)
        for j in file_metadata:
            j['item_id'] = i
            file_info.append(j)
    print('Files available' + str(file_info))

    for k in file_info:
        print('Downloading '+k['name'])
        response = requests.get(BASE_URL + '/file/download/' + str(k['id']), headers=api_call_headers)
        response.raise_for_status()
        dir_path = Path(folder_path) / str(k['item_id'])
        dir_path.mkdir(parents=True, exist_ok=True)
        file_path = dir_path / k['name']
        file_path.write_bytes(response.content)
        print(k['name']+ ' downloaded')

    print('All files have been downloaded in '+ str(folder_path))


def download_ESA():
    """
    Download ESA WorldCover products via Terrascope Catalogue API.

    The function:
    1. Authenticates interactively to the Terrascope platform.
    2. Filters products in the ESA WorldCover 10m 2020 collection, optionally within a bounding box.
    3. Downloads all matching products to `data/raw/ESA_worldcover`.

    Notes
    -----
    - Registration and interactive authentication are required.
    - Non-interactive authentication with username/password is also supported.
    - Bounding box for Martinique example: (-61.3, 14.2, -60.75, 15.0).
    """
    from shapely.geometry import Polygon

    catalogue = Catalogue().authenticate()
    bounds = (-61.3, 14.2, -60.75, 15.0)
    geometry = Polygon.from_bounds(*bounds)
    products = catalogue.get_products("urn:eop:VITO:ESA_WorldCover_10m_2020_V1", geometry=geometry)
    catalogue.download_products(products, "data/raw/ESA_worldcover")




def download_filosofi(url: str = None) -> None:
    """
    Download the INSEE Filosofi 2017 dataset and save it to `data/raw` relative to the repository root.

    Parameters
    ----------
    url : str, optional
        URL of the dataset to download. If not provided, defaults to the official INSEE URL.

    Notes
    -----
    - Uses `requests` with a progress bar if available.
    - Falls back to `urllib` if `requests` fails.
    - Saves the file using the original filename from the URL.
    """
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    default_url = "https://www.insee.fr/fr/statistiques/fichier/6215138/Filosofi2017_carreaux_200m_gpkg.zip"
    url = url or default_url
    repo_root = Path(__file__).resolve().parent.parent
    out_dir = repo_root / "data" / "raw"
    out_dir.mkdir(parents=True, exist_ok=True)
    fname = Path(urlparse(url).path).name or "downloaded.file"
    dest = out_dir / fname

    if dest.exists():
        logging.info("File already exists: %s", dest)
        return

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
        import urllib.request
        logging.info("Falling back to urllib to download %s -> %s", url, dest)
        with urllib.request.urlopen(url, timeout=30) as r, dest.open("wb") as f:
            shutil.copyfileobj(r, f)
        logging.info("Saved to %s", dest)


#def download_osm()