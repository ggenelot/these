import json
import logging
import os
import shutil
import math
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse


import rasterio
import requests
from rasterio.plot import show
from rasterio.warp import transform_bounds
from rasterio.windows import from_bounds

try:
    from terracatalogueclient import Catalogue
except ImportError:
    Catalogue = None


def download_elevation(bbox = (-61.25, 14.35, -60.75, 14.95), 
                       dataset = "COP30",
                       output_tif = "data/raw/elevation/cop30_dem.tif"):
    """
    Download a Digital Elevation Model (DEM) from OpenTopography and inspect it.

    The function:
    1. Loads the OpenTopography API key from env var ``OPENTOPO_API_KEY``.
    2. Defines a bounding box (or optionally reads from a shapefile).
    3. Downloads the COP30 DEM to ``data/raw/elevation/cop30_dem.tif``.
    4. Prints metadata (CRS, resolution, bounds).
    5. Displays the DEM with ``rasterio.plot.show``.

    Raises
    ------
    ValueError
        If the API key is not found in the environment.
    SystemExit
        If the API request fails.
    """
    API_KEY = os.getenv("OPENTOPO_API_KEY")

    if not API_KEY:
        raise ValueError(
            "No API key found! Please set OPENTOPO_API_KEY as an environment variable."
        )

    os.makedirs("data/raw/elevation", exist_ok=True)




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


def _stac_datetime_to_timestamp(value: str) -> float:
    """Convert STAC datetime string to a sortable UNIX timestamp."""
    if not value:
        return 0.0
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return 0.0


def _date_range(start_date=None, end_date=None, days_back=30) -> tuple[str, str]:
    """Resolve a date range as ISO dates."""
    if end_date is None:
        end_date = date.today().isoformat()
    if start_date is None:
        start_date = (date.fromisoformat(end_date) - timedelta(days=days_back)).isoformat()
    return start_date, end_date


def _print_raster_metadata(path: str | Path, title: str, preview: bool = False) -> None:
    """Print common raster metadata and optionally preview it."""
    with rasterio.open(path) as src:
        print(f"\n--- {title} Metadata ---")
        print("Projection:", src.crs)
        print("Resolution:", src.res)
        print("Bounds:", src.bounds)
        if preview:
            show(src, title=title)


def _copernicus_access_token(
    client_id: str | None = None,
    client_secret: str | None = None,
    token_url: str = (
        "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/"
        "protocol/openid-connect/token"
    ),
) -> str:
    """Return an access token for Copernicus Data Space/Sentinel Hub APIs."""
    client_id = (
        client_id
        or os.getenv("COPERNICUS_CLIENT_ID")
        or os.getenv("SENTINELHUB_CLIENT_ID")
    )
    client_secret = (
        client_secret
        or os.getenv("COPERNICUS_CLIENT_SECRET")
        or os.getenv("SENTINELHUB_CLIENT_SECRET")
    )

    if not client_id or not client_secret:
        raise ValueError(
            "Copernicus credentials are missing. Set COPERNICUS_CLIENT_ID and "
            "COPERNICUS_CLIENT_SECRET, or SENTINELHUB_CLIENT_ID and "
            "SENTINELHUB_CLIENT_SECRET, as environment variables."
        )

    response = requests.post(
        token_url,
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def download_copernicus_sentinel2_image(
    bbox=(-61.25, 14.35, -60.75, 14.95),
    output_tif="data/raw/satellite/copernicus_s2_l2a_true_color.tif",
    resolution=10,
    max_cloud_cover=20,
    start_date=None,
    end_date=None,
    days_back=90,
    mosaicking_order="leastCC",
    data_type="sentinel-2-l2a",
    client_id: str | None = None,
    client_secret: str | None = None,
    process_url="https://sh.dataspace.copernicus.eu/api/v1/process",
    preview=False,
):
    """Download a Copernicus Sentinel-2 L2A true-color GeoTIFF for a bbox.

    This uses the Copernicus Data Space Ecosystem / Sentinel Hub Process API.
    It requests a spatial subset directly as a GeoTIFF, which is lighter than
    downloading a full Sentinel-2 SAFE product and extracting JP2 bands locally.

    Parameters
    ----------
    bbox : tuple(float, float, float, float)
        Bounding box in EPSG:4326 as (west, south, east, north).
    output_tif : str
        Output path for the GeoTIFF texture.
    resolution : float
        Output pixel size in metres. Sentinel-2 true color is natively 10 m.
    max_cloud_cover : float
        Maximum scene cloud cover percentage.
    start_date, end_date : str or None
        ISO dates (YYYY-MM-DD). If omitted, uses the last ``days_back`` days.
    days_back : int
        Number of days before ``end_date`` when ``start_date`` is omitted.
    mosaicking_order : str
        Copernicus/Sentinel Hub mosaicking order, e.g. ``leastCC`` or
        ``mostRecent``.
    data_type : str
        Process API data type. Defaults to ``sentinel-2-l2a``.
    client_id, client_secret : str or None
        Optional credentials. If omitted, reads ``COPERNICUS_CLIENT_ID`` and
        ``COPERNICUS_CLIENT_SECRET`` from the environment.
    process_url : str
        Process API endpoint.
    preview : bool
        If True, display the downloaded raster with ``rasterio.plot.show``.
    """
    if len(bbox) != 4:
        raise ValueError("bbox must be a 4-value tuple: (west, south, east, north)")
    if resolution <= 0:
        raise ValueError("resolution must be strictly positive.")

    west, south, east, north = bbox
    if west >= east or south >= north:
        raise ValueError("Invalid bbox order. Expected west < east and south < north.")

    start_date, end_date = _date_range(start_date, end_date, days_back)
    bbox_3857 = transform_bounds(
        "EPSG:4326",
        "EPSG:3857",
        west,
        south,
        east,
        north,
        densify_pts=21,
    )
    width = max(1, math.ceil((bbox_3857[2] - bbox_3857[0]) / resolution))
    height = max(1, math.ceil((bbox_3857[3] - bbox_3857[1]) / resolution))

    output_path = Path(output_tif)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    evalscript = """
//VERSION=3
function setup() {
  return {
    input: ["B04", "B03", "B02", "dataMask"],
    output: { bands: 4, sampleType: "AUTO" }
  };
}

function evaluatePixel(sample) {
  return [2.5 * sample.B04, 2.5 * sample.B03, 2.5 * sample.B02, sample.dataMask];
}
"""

    payload = {
        "input": {
            "bounds": {
                "bbox": list(bbox_3857),
                "properties": {
                    "crs": "http://www.opengis.net/def/crs/EPSG/0/3857",
                },
            },
            "data": [
                {
                    "type": data_type,
                    "dataFilter": {
                        "timeRange": {
                            "from": f"{start_date}T00:00:00Z",
                            "to": f"{end_date}T23:59:59Z",
                        },
                        "maxCloudCoverage": max_cloud_cover,
                        "mosaickingOrder": mosaicking_order,
                    },
                    "processing": {
                        "upsampling": "BILINEAR",
                        "downsampling": "BILINEAR",
                    },
                }
            ],
        },
        "output": {
            "width": width,
            "height": height,
            "responses": [
                {
                    "identifier": "default",
                    "format": {"type": "image/tiff"},
                }
            ],
        },
        "evalscript": evalscript,
    }

    access_token = _copernicus_access_token(client_id, client_secret)
    print(
        "Downloading Copernicus Sentinel-2 L2A true-color image "
        f"for bbox={bbox}, date={start_date}/{end_date}, resolution={resolution} m"
    )
    response = requests.post(
        process_url,
        json=payload,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=120,
    )
    response.raise_for_status()
    output_path.write_bytes(response.content)

    print(f"Download complete! File saved as: {output_path}")
    _print_raster_metadata(output_path, "Copernicus Sentinel-2 L2A true color", preview)
    return output_path


def download_satellite_image(
    bbox=(-61.25, 14.35, -60.75, 14.95),
    output_tif="data/raw/satellite/sentinel2_visual.tif",
    provider="earthsearch",
    resolution=10,
    collection="sentinel-2-l2a",
    asset_key="visual",
    max_cloud_cover=20,
    start_date=None,
    end_date=None,
    days_back=30,
    stac_url="https://earth-search.aws.element84.com/v1/search",
    preview=False,
):
    """
    Download a free/open Sentinel-2 image clipped to a given bbox.

    The function:
    1. Queries the public Earth Search STAC API on the requested bbox/date range.
    2. Selects the best scene (lowest cloud cover, newest timestamp).
    3. Downloads and clips the requested raster asset to the bbox.
    4. Saves the clipped image to ``output_tif`` and prints key metadata.

    Parameters
    ----------
    bbox : tuple(float, float, float, float)
        Bounding box in EPSG:4326 as (west, south, east, north).
    output_tif : str
        Output path for the clipped GeoTIFF.
    provider : {"earthsearch", "copernicus"}
        Imagery provider. ``earthsearch`` uses public STAC COG assets.
        ``copernicus`` uses the Copernicus Data Space / Sentinel Hub Process API.
    resolution : float
        Output pixel size in metres when ``provider="copernicus"``.
    collection : str
        STAC collection ID. Default is Sentinel-2 L2A.
    asset_key : str
        STAC asset key to download (default: ``visual``).
    max_cloud_cover : float
        Maximum cloud cover (%) for the first search pass.
    start_date, end_date : str or None
        ISO dates (YYYY-MM-DD) defining search range.
        If omitted, uses the last ``days_back`` days.
    days_back : int
        Number of days before ``end_date`` when ``start_date`` is omitted.
    stac_url : str
        STAC API search endpoint.
    preview : bool
        If True, display the downloaded raster with ``rasterio.plot.show``.
    """
    if provider == "copernicus":
        return download_copernicus_sentinel2_image(
            bbox=bbox,
            output_tif=output_tif,
            resolution=resolution,
            max_cloud_cover=max_cloud_cover,
            start_date=start_date,
            end_date=end_date,
            days_back=days_back,
            preview=preview,
        )
    if provider != "earthsearch":
        raise ValueError("provider must be 'earthsearch' or 'copernicus'.")

    if len(bbox) != 4:
        raise ValueError("bbox must be a 4-value tuple: (west, south, east, north)")

    west, south, east, north = bbox
    if west >= east or south >= north:
        raise ValueError("Invalid bbox order. Expected west < east and south < north.")

    start_date, end_date = _date_range(start_date, end_date, days_back)

    output_path = Path(output_tif)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    datetime_filter = f"{start_date}T00:00:00Z/{end_date}T23:59:59Z"
    base_payload = {
        "collections": [collection],
        "bbox": [west, south, east, north],
        "datetime": datetime_filter,
        "limit": 100,
    }

    payload = {
        **base_payload,
        "query": {"eo:cloud_cover": {"lte": max_cloud_cover}},
    }

    print(f"Searching free satellite scenes for bbox={bbox} in {datetime_filter}")
    response = requests.post(stac_url, json=payload, timeout=60)
    response.raise_for_status()
    features = response.json().get("features", [])

    if not features:
        print(
            f"No scene found with cloud cover <= {max_cloud_cover}%. "
            "Retrying without cloud filter..."
        )
        response = requests.post(stac_url, json=base_payload, timeout=60)
        response.raise_for_status()
        features = response.json().get("features", [])

    if not features:
        raise RuntimeError(
            "No satellite imagery found for this bbox/date range. "
            "Try widening the date range or changing the bbox."
        )

    def _scene_rank(item):
        props = item.get("properties", {})
        cloud = props.get("eo:cloud_cover")
        cloud = float(cloud) if cloud is not None else 1e6
        ts = _stac_datetime_to_timestamp(props.get("datetime", ""))
        return (cloud, -ts)

    best_item = min(features, key=_scene_rank)
    item_id = best_item.get("id", "<unknown-id>")
    props = best_item.get("properties", {})
    cloud_cover = props.get("eo:cloud_cover", "unknown")
    acquisition_date = props.get("datetime", "unknown")
    assets = best_item.get("assets", {})

    if asset_key not in assets:
        fallback_assets = [k for k in ("visual", "B04", "B03", "B02") if k in assets]
        if not fallback_assets:
            available_assets = ", ".join(sorted(assets.keys()))
            raise RuntimeError(
                f"Requested asset '{asset_key}' not found. "
                f"Available assets: {available_assets}"
            )
        chosen_asset = fallback_assets[0]
        print(
            f"Asset '{asset_key}' unavailable for scene {item_id}. "
            f"Using '{chosen_asset}' instead."
        )
        asset_key = chosen_asset

    asset_href = assets[asset_key].get("href")
    if not asset_href:
        raise RuntimeError(f"Asset '{asset_key}' has no downloadable href.")

    print(
        f"Selected scene {item_id} | date={acquisition_date} "
        f"| cloud_cover={cloud_cover} | asset={asset_key}"
    )

    with rasterio.open(asset_href) as src:
        bbox_src_crs = transform_bounds(
            "EPSG:4326",
            src.crs,
            west,
            south,
            east,
            north,
            densify_pts=21,
        )

        left = max(bbox_src_crs[0], src.bounds.left)
        bottom = max(bbox_src_crs[1], src.bounds.bottom)
        right = min(bbox_src_crs[2], src.bounds.right)
        top = min(bbox_src_crs[3], src.bounds.top)

        if left >= right or bottom >= top:
            raise RuntimeError(
                "The selected image does not overlap the requested bbox after reprojection."
            )

        window = from_bounds(left, bottom, right, top, transform=src.transform)
        window = window.round_offsets().round_lengths()
        if window.width <= 0 or window.height <= 0:
            raise RuntimeError("Computed read window is empty for the requested bbox.")

        data = src.read(window=window)
        profile = src.profile.copy()
        profile.update(
            driver="GTiff",
            height=data.shape[1],
            width=data.shape[2],
            transform=src.window_transform(window),
            compress="LZW",
        )
        profile.pop("blockxsize", None)
        profile.pop("blockysize", None)
        profile.pop("tiled", None)

    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(data)

    print(f"Download complete! File saved as: {output_path}")
    with rasterio.open(output_path) as out:
        print("\n--- Satellite Image Metadata ---")
        print("Projection:", out.crs)
        print("Resolution:", out.res)
        print("Bounds:", out.bounds)
        if preview:
            show(out, title=f"Satellite image ({collection}, {asset_key})")


def download_figshare():
    """
    Download files from Figshare given a list of article/item IDs.

    The function:
    1. Sets up the API base URL and authentication headers.
    2. Collects file metadata for each item ID.
    3. Downloads all files into `data/raw/<item_id>/<filename>` structure.

    Notes
    -----
    - Requires a Figshare personal access token stored in env var
      ``FIGSHARE_TOKEN``.
    - You can modify ``item_ids`` to include your desired Figshare article IDs.

    Raises
    ------
    requests.exceptions.RequestException
        If the API request fails.
    """
    item_ids = [12706085]
    folder_path = "data/raw/"
    BASE_URL = "https://api.figshare.com/v2"
    api_call_headers = {"Authorization": "token $env:FIGSHARE_TOKEN"}
    file_info = []

    print("Retrieving metadata")
    for i in item_ids:
        r = requests.get(BASE_URL + "/articles/" + str(i) + "/files")
        r.raise_for_status()
        file_metadata = json.loads(r.text)
        for j in file_metadata:
            j["item_id"] = i
            file_info.append(j)
    print("Files available" + str(file_info))

    for k in file_info:
        print("Downloading " + k["name"])
        response = requests.get(
            BASE_URL + "/file/download/" + str(k["id"]), headers=api_call_headers
        )
        response.raise_for_status()
        dir_path = Path(folder_path) / str(k["item_id"])
        dir_path.mkdir(parents=True, exist_ok=True)
        file_path = dir_path / k["name"]
        file_path.write_bytes(response.content)
        print(k["name"] + " downloaded")

    print("All files have been downloaded in " + str(folder_path))


def download_ESA():
    """
    Download ESA WorldCover products via Terrascope Catalogue API.

    The function:
    1. Authenticates interactively to the Terrascope platform.
    2. Filters products in the ESA WorldCover 10m 2020 collection,
       optionally within a bounding box.
    3. Downloads all matching products to `data/raw/ESA_worldcover`.

    Notes
    -----
    - Registration and interactive authentication are required.
    - Non-interactive authentication with username/password is also supported.
    - Bounding box for Martinique example: (-61.3, 14.2, -60.75, 15.0).
    """
    from shapely.geometry import Polygon

    if Catalogue is None:
        raise ImportError(
            "terracatalogueclient is required for download_ESA(). "
            "Install the project with the dev dependencies or install "
            "terracatalogueclient."
        )

    catalogue = Catalogue().authenticate()
    bounds = (-61.3, 14.2, -60.75, 15.0)
    geometry = Polygon.from_bounds(*bounds)
    products = catalogue.get_products(
        "urn:eop:VITO:ESA_WorldCover_10m_2020_V1", geometry=geometry
    )
    catalogue.download_products(products, "data/raw/ESA_worldcover")


def download_filosofi(url: str = None) -> None:
    """
    Download the INSEE Filosofi 2017 dataset and save it to ``data/raw``.

    Parameters
    ----------
    url : str, optional
        URL of the dataset to download. If not provided, defaults to the
        official INSEE URL.

    Notes
    -----
    - Uses `requests` with a progress bar if available.
    - Falls back to `urllib` if `requests` fails.
    - Saves the file using the original filename from the URL.
    """
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    default_url = (
        "https://www.insee.fr/fr/statistiques/fichier/"
        "6215138/Filosofi2017_carreaux_200m_gpkg.zip"
    )
    url = url or default_url
    repo_root = Path(__file__).resolve().parent.parent.parent
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
            with (
                dest.open("wb") as f,
                tqdm(
                    total=(total if total else None),
                    unit="B",
                    unit_scale=True,
                    desc=dest.name,
                ) as pbar,
            ):
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

#download_elevation()
#download_satellite_image()
#download_ESA()
#download_figshare()
#download_filosofi()



# def download_osm()
