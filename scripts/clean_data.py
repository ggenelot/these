import argparse
import logging
import shutil
import zipfile
from pathlib import Path
import sys

#!/usr/bin/env python3
"""
Copy contents of the 'raw' folder into 'processed' (same project root),
preserving folder structure, and unzip any .zip files found inside 'processed'.
"""


logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def copy_raw_to_processed(src: Path, dst: Path) -> None:
    if not src.exists() or not src.is_dir():
        raise FileNotFoundError(f"Source raw directory not found: {src}")
    dst.mkdir(parents=True, exist_ok=True)

    for item in src.iterdir():
        target = dst / item.name
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True)
            logging.info("Copied directory: %s -> %s", item, target)
        else:
            shutil.copy2(item, target)
            logging.info("Copied file: %s -> %s", item, target)


def unzip_in_place(root: Path, remove_zip: bool = True) -> None:
    for z in root.rglob("*.zip"):
        try:
            logging.info("Unzipping: %s", z)
            with zipfile.ZipFile(z, "r") as zf:
                zf.extractall(z.parent)
            if remove_zip:
                z.unlink()
                logging.info("Removed zip: %s", z)
        except zipfile.BadZipFile:
            logging.error("Bad zip file, skipping: %s", z)
        except Exception as e:
            logging.error("Failed to unzip %s: %s", z, e)


def main():
    p = Path(__file__).resolve()
    project_root = p.parents[1]  # script is expected in <project>/scripts/
    default_src = project_root / "data/raw"
    default_dst = project_root / "data/processed"

    parser = argparse.ArgumentParser(description="Copy raw -> processed and unzip files")
    parser.add_argument("--src", type=Path, default=default_src, help="Source raw folder")
    parser.add_argument("--dst", type=Path, default=default_dst, help="Destination processed folder")
    parser.add_argument("--keep-zips", action="store_true", help="Keep .zip files after extraction")
    args = parser.parse_args()

    try:
        copy_raw_to_processed(args.src, args.dst)
        unzip_in_place(args.dst, remove_zip=not args.keep_zips)
        logging.info("Done.")
    except Exception as exc:
        logging.error("Error: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()