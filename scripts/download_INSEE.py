from pathlib import Path
import sys
import logging
from urllib.parse import urlparse
import requests
import shutil

#!/usr/bin/env python3
"""
download_INSEE.py

Download a file and save it to data/raw relative to the repository root
(assumes this script lives in <repo>/scripts/).
"""

# URL to download (can be overridden by first CLI arg)
URL = "https://www.insee.fr/fr/statistiques/fichier/6215138/Filosofi2017_carreaux_200m_gpkg.zip"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def target_dir() -> Path:
    # script is expected at <repo>/scripts/, so repo root is parent of this file's parent
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent
    return repo_root / "data" / "raw"


def filename_from_url(url: str) -> str:
    return Path(urlparse(url).path).name or "downloaded.file"


def download_with_requests(url: str, dest: Path) -> None:

    with requests.get(url, stream=True, timeout=30) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        chunk_size = 8192
        downloaded = 0
        with dest.open("wb") as f:
            for chunk in r.iter_content(chunk_size=chunk_size):
                if not chunk:
                    continue
                f.write(chunk)
                downloaded += len(chunk)
                if total:
                    pct = downloaded * 100 // total
                    logging.info("Downloading %s: %d%% (%d/%d bytes)", dest.name, pct, downloaded, total)
    logging.info("Saved to %s", dest)


def download_with_urllib(url: str, dest: Path) -> None:
    import urllib.request

    with urllib.request.urlopen(url, timeout=30) as r, dest.open("wb") as f:
        shutil.copyfileobj(r, f)
    logging.info("Saved to %s", dest)


def main(argv):
    url = argv[1] if len(argv) > 1 else URL
    out_dir = target_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    fname = filename_from_url(url)
    dest = out_dir / fname

    if dest.exists():
        logging.info("File already exists: %s", dest)
        return 0

    # prefer requests if available (better streaming support)
    try:
        import requests  # type: ignore
        logging.info("Using requests to download %s -> %s", url, dest)
        download_with_requests(url, dest)
    except Exception:
        logging.info("Falling back to urllib to download %s -> %s", url, dest)
        download_with_urllib(url, dest)

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))