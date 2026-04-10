import json
import logging
import os
import shutil
import sys
from pathlib import Path
from urllib.parse import urlparse


def _bootstrap_gdal_proj_env() -> None:
    """
    Populate GDAL/PROJ env vars early to avoid import-time warnings on Windows.
    """
    env_prefix = Path(os.environ.get("CONDA_PREFIX", sys.prefix))
    proj_candidates = [
        env_prefix / "Library/share/proj",
        env_prefix / "share/proj",
    ]
    gdal_candidates = [
        env_prefix / "Library/share/gdal",
        env_prefix / "share/gdal",
    ]

    if not os.getenv("PROJ_LIB"):
        for candidate in proj_candidates:
            if candidate.exists():
                os.environ["PROJ_LIB"] = str(candidate)
                break

    if not os.getenv("PROJ_DATA"):
        for candidate in proj_candidates:
            if candidate.exists():
                os.environ["PROJ_DATA"] = str(candidate)
                break

    if not os.getenv("GDAL_DATA"):
        for candidate in gdal_candidates:
            if candidate.exists():
                os.environ["GDAL_DATA"] = str(candidate)
                break


_bootstrap_gdal_proj_env()

import rasterio
import requests
from rasterio.plot import show
from terracatalogueclient import Catalogue


def download_elevation():
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
#download_ESA()
#download_figshare()
#download_filosofi()

def download_osm_data(
    bbox: tuple[float, float, float, float],
    output_dir: str | Path | None = None,
    file_format: str = "gpkg",
    show_progress: bool = True,
    verbose: bool = True,
) -> dict[str, str | None]:
    """
    Download OSM layers for a hurricane situation map from a bounding box.

    Parameters
    ----------
    bbox : tuple[float, float, float, float]
        Bounding box as ``(west, south, east, north)`` in EPSG:4326.
    output_dir : str | Path, optional
        Output folder. Defaults to ``<repo>/data/raw/osm``.
    file_format : str, default "gpkg"
        Vector output format: ``"gpkg"``, ``"geojson"``, or ``"shp"``.
    show_progress : bool, default True
        Display a progress bar over requested layers when ``tqdm`` is available.
    verbose : bool, default True
        Print detailed runtime information (counts, timings, output paths).

    Returns
    -------
    dict[str, str | None]
        Mapping from layer name (``coastline``, ``roads``, ``mangrove``) to
        file path. Value is ``None`` when no feature is found for that layer.
    """
    try:
        import osmnx as ox
    except ImportError as exc:
        raise ImportError(
            "download_osm_data requires osmnx. Install it with `pip install osmnx`."
        ) from exc

    import pandas as pd
    from shapely.geometry import box
    from time import perf_counter

    def _set_env_if_missing(var_name: str, candidates: list[Path]) -> str | None:
        """Set env var to first existing candidate path if currently missing."""
        if os.getenv(var_name):
            return None
        for candidate in candidates:
            if candidate.exists():
                os.environ[var_name] = str(candidate)
                return str(candidate)
        return None

    if len(bbox) != 4:
        raise ValueError("bbox must have 4 values: (west, south, east, north).")

    west, south, east, north = bbox
    if west >= east or south >= north:
        raise ValueError(
            "Invalid bbox order. Expected (west < east, south < north)."
        )

    valid_formats = {"gpkg": ".gpkg", "geojson": ".geojson", "shp": ".shp"}
    fmt = file_format.lower()
    if fmt not in valid_formats:
        raise ValueError("file_format must be one of: 'gpkg', 'geojson', 'shp'.")

    # Fix common Windows conda setups where GDAL/PROJ data vars are unset.
    env_prefix = Path(os.environ.get("CONDA_PREFIX", sys.prefix))
    proj_candidates = [
        env_prefix / "Library/share/proj",
        env_prefix / "share/proj",
    ]
    gdal_candidates = [
        env_prefix / "Library/share/gdal",
        env_prefix / "share/gdal",
    ]
    gdal_set = _set_env_if_missing("GDAL_DATA", gdal_candidates)
    proj_set = _set_env_if_missing("PROJ_LIB", proj_candidates)
    _set_env_if_missing("PROJ_DATA", proj_candidates)

    repo_root = Path(__file__).resolve().parent.parent.parent
    out_dir = (
        Path(output_dir) if output_dir is not None else repo_root / "data/raw/osm"
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    aoi = box(west, south, east, north)

    layers = {
        "coastline": {"natural": "coastline"},
        "roads": {"highway": True},
        "mangrove": {
            "wetland": "mangrove",
            "landuse": "mangrove",
            "natural": "mangrove",
        },
    }

    saved_files: dict[str, str | None] = {}
    layer_items = list(layers.items())
    start_total = perf_counter()
    n_saved = 0

    fetch_from_polygon = getattr(ox, "features_from_polygon", None)
    if fetch_from_polygon is None and hasattr(ox, "features"):
        fetch_from_polygon = getattr(ox.features, "features_from_polygon", None)
    if fetch_from_polygon is None:
        fetch_from_polygon = getattr(ox, "geometries_from_polygon", None)
    if fetch_from_polygon is None and hasattr(ox, "geometries"):
        fetch_from_polygon = getattr(ox.geometries, "geometries_from_polygon", None)
    if fetch_from_polygon is None:
        raise AttributeError(
            "No compatible polygon query function found in osmnx. "
            "Expected one of: features_from_polygon, geometries_from_polygon."
        )

    if verbose:
        print("Starting OSM download for hurricane situation map")
        print(f"  osmnx version: {getattr(ox, '__version__', 'unknown')}")
        print(f"  query function: {fetch_from_polygon.__name__}")
        print(f"  bbox (west, south, east, north): {bbox}")
        print(f"  output directory: {out_dir.resolve()}")
        print(f"  output format: {fmt}")
        if gdal_set:
            print(f"  GDAL_DATA was unset; using: {gdal_set}")
        if proj_set:
            print(f"  PROJ_LIB was unset; using: {proj_set}")

    iterator = layer_items
    if show_progress:
        try:
            from tqdm.auto import tqdm

            iterator = tqdm(
                layer_items,
                total=len(layer_items),
                desc="Downloading OSM layers",
                unit="layer",
            )
        except Exception:
            if verbose:
                print("tqdm is not available, continuing without progress bar.")

    for idx, (layer_name, tags) in enumerate(iterator, start=1):
        layer_start = perf_counter()
        if verbose:
            print(f"[{idx}/{len(layer_items)}] Requesting layer: {layer_name}")
        try:
            gdf = fetch_from_polygon(aoi, tags)
        except Exception as exc:
            logging.exception("Failed to download '%s': %s", layer_name, exc)
            saved_files[layer_name] = None
            if verbose:
                print(f"  -> failed to query '{layer_name}'.")
            continue

        gdf = gdf.reset_index(drop=True)
        if "geometry" in gdf.columns:
            gdf = gdf[gdf.geometry.notna()].copy()

        if layer_name == "mangrove" and not gdf.empty:
            mask = pd.Series(False, index=gdf.index)
            for col in ("wetland", "landuse", "natural"):
                if col in gdf.columns:
                    values = gdf[col].fillna("").astype(str).str.lower()
                    mask = mask | values.str.contains("mangrove")
            gdf = gdf[mask].copy()

        if gdf.empty:
            logging.warning("No '%s' feature found in bbox %s.", layer_name, bbox)
            saved_files[layer_name] = None
            if verbose:
                elapsed = perf_counter() - layer_start
                print(f"  -> no features found ({elapsed:.1f}s).")
            continue

        out_path = out_dir / f"{layer_name}{valid_formats[fmt]}"
        try:
            if fmt == "gpkg":
                gdf.to_file(out_path, driver="GPKG")
            elif fmt == "geojson":
                gdf.to_file(out_path, driver="GeoJSON")
            else:
                gdf.to_file(out_path)
        except Exception as exc:
            logging.exception(
                "Failed to save '%s' layer to %s: %s", layer_name, out_path, exc
            )
            saved_files[layer_name] = None
            if verbose:
                print(f"  -> failed to write '{layer_name}'.")
            continue

        saved_files[layer_name] = str(out_path)
        n_saved += 1
        if verbose:
            elapsed = perf_counter() - layer_start
            geom_counts = gdf.geometry.geom_type.value_counts().to_dict()
            file_size_mb = out_path.stat().st_size / (1024 * 1024)
            print(
                f"  -> saved {len(gdf)} features to {out_path.name} "
                f"({file_size_mb:.2f} MB, {elapsed:.1f}s)"
            )
            print(f"  -> geometry types: {geom_counts}")

    if verbose:
        total_elapsed = perf_counter() - start_total
        print("OSM download finished")
        print(f"  saved {n_saved}/{len(layer_items)} layer(s) in {total_elapsed:.1f}s")
        for layer_name in layers:
            path = saved_files.get(layer_name)
            status = path if path else "not saved"
            print(f"  - {layer_name}: {status}")

    return saved_files



