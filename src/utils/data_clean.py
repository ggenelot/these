import argparse
import logging
import shutil
import zipfile
from pathlib import Path
import sys
import subprocess
import py7zr

#!/usr/bin/env python3
"""
Copy contents of the 'raw' folder into 'processed' (same project root),
preserving folder structure, and unzip any .zip files found inside 'processed'.
"""


def copy_raw_to_processed(src: Path, dst: Path) -> None:
    """
    Copy everything under ``src`` into ``dst`` preserving the folder structure.

    Parameters
    ----------
    src : Path
        Source directory (e.g., ``data/raw``).
    dst : Path
        Destination directory (e.g., ``data/processed``). Created if missing.

    Raises
    ------
    FileNotFoundError
        If ``src`` does not exist or is not a directory.
    """
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
    """
    Recursively unzip all ``*.zip`` files under ``root``.

    Parameters
    ----------
    root : Path
        Base directory to search for zips.
    remove_zip : bool, default True
        If True, delete each archive after successful extraction.
    """
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
    """CLI entry point to copy raw data to processed and unzip archives."""
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

    # Ensure this specific geopackage zip from data/raw is extracted into data/processed
    def extract_filosofi_zip():
        p = Path(__file__).resolve()
        project_root = p.parents[1]
        raw = project_root / "data" / "raw"
        processed = project_root / "data" / "processed" /"Filosofi2017"
        z = raw / "Filosofi2017_carreaux_200m_gpkg.zip"

        if not z.exists():
            logging.INFO("Specified zip not found, skipping: %s", z)
            return

        processed.mkdir(parents=True, exist_ok=True)
        try:
            logging.info("Extracting %s -> %s", z, processed)
            with zipfile.ZipFile(z, "r") as zf:
                zf.extractall(processed)
            logging.info("Zip extraction complete: %s", z)

            # After extracting the zip, look for any .7z archives and extract them in place
            for sev in processed.rglob("*.7z"):
                try:
                    logging.info("Found 7z archive, extracting: %s", sev)
                    with py7zr.SevenZipFile(sev, mode="r") as sz:
                        sz.extractall(path=sev.parent)
                    logging.info("7z extraction complete: %s -> %s", sev, sev.parent)
                    # Remove the .7z after successful extraction
                    try:
                        sev.unlink()
                        logging.info("Removed 7z archive: %s", sev)
                    except Exception as e:
                        logging.error("Failed to remove 7z %s: %s", sev, e)
                except Exception as e:
                    logging.error("Failed to extract 7z %s: %s", sev, e)

        except zipfile.BadZipFile:
            logging.error("Bad zip file: %s", z)
        except Exception as e:
            logging.error("Failed to extract %s: %s", z, e)

    if __name__ == "__main__":
        # main() already runs above; run the specific extraction to ensure the geopackage is in processed
        extract_filosofi_zip()

        def extract_bdtopo_7z():
            p = Path(__file__).resolve()
            project_root = p.parents[1]
            raw = project_root / "data" / "raw"
            processed = project_root / "data" / "processed"
            src = raw / "BDTOPO_3-5_TOUSTHEMES_GPKG_RGAF09UTM20_R02_2025-09-15.7z"

            if not src.exists():
                logging.info("7z not found, skipping: %s", src)
                return

            processed.mkdir(parents=True, exist_ok=True)
            try:
                logging.info("Extracting 7z: %s -> %s", src, processed)
                with py7zr.SevenZipFile(src, mode="r") as archive:
                    archive.extractall(path=processed)
                logging.info("Extraction complete: %s", src)
            except Exception as e:
                logging.error("Failed to extract %s: %s", src, e)


        if __name__ == "__main__":
            extract_bdtopo_7z()

            # remove specific leftover .7z files (and any other top-level .7z in processed) to keep workspace clean
            p = Path(__file__).resolve()
            project_root = p.parents[1]
            processed = project_root / "data" / "processed"

            leftovers = [
                "Filosofi2017_carreaux_200m_gpkg.7z",
                "BDTOPO_3-5_TOUSTHEMES_GPKG_RGAF09UTM20_R02_2025-09-15.7z",
            ]

            for name in leftovers:
                f = processed / name
                if f.exists():
                    try:
                        f.unlink()
                        logging.info("Removed leftover archive: %s", f)
                    except Exception as e:
                        logging.error("Failed to remove %s: %s", f, e)

            # also remove any other top-level .7z files in data/processed
            for z in processed.glob("*.7z"):
                try:
                    z.unlink()
                    logging.info("Removed additional .7z: %s", z)
                except Exception as e:
                    logging.error("Failed to remove %s: %s", z, e)
