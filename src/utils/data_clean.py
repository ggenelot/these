#!/usr/bin/env python3
"""
Sync data/raw -> data/processed and extract archives (.zip, .7z).

Robustness goals:
- No dependence on script location (auto-detect project root via pyproject.toml / .git)
- Single entrypoint
- Secure ZIP extraction (prevents zip-slip)
- Optional cleaning of destination to avoid stale processed files
"""

from __future__ import annotations

import argparse
import logging
import shutil
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path

import py7zr


# ----------------------------
# Root detection
# ----------------------------

def find_project_root(start: Path) -> Path:
    """
    Walk up from `start` to find a directory containing pyproject.toml or .git.
    Falls back to `start` if nothing is found.
    """
    start = start.resolve()
    for p in [start, *start.parents]:
        if (p / "pyproject.toml").exists() or (p / ".git").exists():
            return p
    return start


# ----------------------------
# Copy / sync
# ----------------------------

def sync_tree(src: Path, dst: Path, clean_dst: bool = False) -> None:
    """
    Copy everything under `src` into `dst`, preserving structure.
    If clean_dst is True, delete dst first (full rebuild to avoid stale files).
    """
    if not src.exists() or not src.is_dir():
        raise FileNotFoundError(f"Source directory not found: {src}")

    if clean_dst and dst.exists():
        logging.info("Cleaning destination: %s", dst)
        shutil.rmtree(dst)

    dst.mkdir(parents=True, exist_ok=True)

    # Copy immediate children (preserve raw top-level structure)
    for item in src.iterdir():
        target = dst / item.name
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True)
            logging.info("Copied dir: %s -> %s", item, target)
        else:
            shutil.copy2(item, target)
            logging.info("Copied file: %s -> %s", item, target)


# ----------------------------
# Secure ZIP extraction
# ----------------------------

def _is_within_directory(base: Path, target: Path) -> bool:
    """
    True if target is within base after resolving.
    """
    base = base.resolve()
    target = target.resolve()
    try:
        target.relative_to(base)
        return True
    except ValueError:
        return False


def safe_extract_zip(zip_path: Path, dest_dir: Path) -> None:
    """
    Extract zip into dest_dir safely (prevents zip-slip).
    """
    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.infolist():
            # Skip directory entries; ZipFile handles them but keep checks consistent
            member_name = member.filename

            # Windows backslashes can appear in zips; normalize to POSIX-like
            member_name = member_name.replace("\\", "/")

            # Disallow absolute paths
            if member_name.startswith("/") or member_name.startswith(".."):
                raise ValueError(f"Unsafe zip entry (absolute or parent traversal): {member.filename}")

            out_path = dest_dir / member_name
            if not _is_within_directory(dest_dir, out_path):
                raise ValueError(f"Unsafe zip entry (path traversal): {member.filename}")

        zf.extractall(dest_dir)


# ----------------------------
# Archive extraction
# ----------------------------

@dataclass(frozen=True)
class ExtractOptions:
    remove_archives: bool = True
    strict: bool = False  # if True, fail hard on extraction errors


def extract_archives(root: Path, patterns: tuple[str, ...], opts: ExtractOptions, max_passes: int = 10) -> None:
    """
    Recursively extract archives matching patterns under root.
    Runs multiple passes so nested archives (zip -> 7z -> ...) are also extracted.
    """
    if not root.exists():
        raise FileNotFoundError(f"Extraction root not found: {root}")

    for _ in range(max_passes):
        archives: list[Path] = []
        for pat in patterns:
            archives.extend(root.rglob(pat))

        # Nothing left to do
        if not archives:
            return

        extracted_any = False

        for a in sorted(set(archives)):
            try:
                logging.info("Extracting: %s", a)
                if a.suffix.lower() == ".zip":
                    safe_extract_zip(a, a.parent)
                elif a.suffix.lower() == ".7z":
                    with py7zr.SevenZipFile(a, mode="r") as sz:
                        sz.extractall(path=a.parent)
                else:
                    continue

                extracted_any = True

                if opts.remove_archives:
                    a.unlink(missing_ok=True)
                    logging.info("Removed archive: %s", a)

            except Exception as e:
                msg = f"Failed to extract {a}: {e}"
                if opts.strict:
                    raise RuntimeError(msg) from e
                logging.error(msg)

        # If we found archives but couldn't extract anything, avoid infinite loops
        if not extracted_any:
            return

    # If still archives after max_passes, decide what you want: warn or fail in strict mode
    remaining = []
    for pat in patterns:
        remaining.extend(root.rglob(pat))
    if remaining:
        msg = f"Archives still present after {max_passes} passes: {len(remaining)}"
        if opts.strict:
            raise RuntimeError(msg)
        logging.warning(msg)


# ----------------------------
# CLI
# ----------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sync raw -> processed and extract archives.")
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Project root (auto-detected via pyproject.toml/.git if omitted).",
    )
    parser.add_argument("--src", type=Path, default=None, help="Source directory (default: <root>/data/raw).")
    parser.add_argument("--dst", type=Path, default=None, help="Destination directory (default: <root>/data/processed).")
    parser.add_argument("--clean", action="store_true", help="Delete destination before copying (avoids stale files).")
    parser.add_argument(
        "--extract",
        action="append",
        default=["*.zip", "*.7z"],
        help="Archive glob to extract under dst (repeatable). Default: *.zip and *.7z",
    )
    parser.add_argument("--keep-archives", action="store_true", help="Keep archives after extraction.")
    parser.add_argument("--strict", action="store_true", help="Fail on first extraction error.")
    parser.add_argument("--log-level", default="INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR).")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, str(args.log_level).upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(message)s",
    )

    # Resolve root reliably
    if args.root is None:
        # Use current working directory as a starting point (works in CI and local)
        root = find_project_root(Path.cwd())
    else:
        root = args.root.resolve()

    src = (args.src or (root / "data" / "raw")).resolve()
    dst = (args.dst or (root / "data" / "processed")).resolve()

    logging.info("Project root: %s", root)
    logging.info("Source: %s", src)
    logging.info("Destination: %s", dst)

    sync_tree(src, dst, clean_dst=args.clean)

    opts = ExtractOptions(remove_archives=not args.keep_archives, strict=args.strict)
    extract_archives(dst, patterns=tuple(args.extract), opts=opts)

    logging.info("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
