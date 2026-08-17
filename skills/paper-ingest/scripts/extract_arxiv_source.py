#!/usr/bin/env python3
"""Unpack an arXiv e-print bundle into a directory.

arXiv serves either a gzipped tarball or a single gzipped .tex file. The shell
version of this step used `tar`, which git-bash on Windows refuses to run on a
path like C:\\Users\\... because it reads the drive letter as a remote host.
tarfile and gzip from the standard library behave identically everywhere.
"""

from __future__ import annotations

import argparse
import gzip
import shutil
import tarfile
from pathlib import Path


def unpack(archive: Path, dest: Path) -> str:
    dest.mkdir(parents=True, exist_ok=True)

    if tarfile.is_tarfile(archive):
        with tarfile.open(archive) as tf:
            try:
                # filter="data" refuses absolute paths and traversal outside
                # dest; arXiv bundles are arbitrary user uploads.
                tf.extractall(dest, filter="data")
            except TypeError:
                # Python older than 3.11.4 has no extraction filters.
                tf.extractall(dest)
        return f"tar -> {dest}"

    main_tex = dest / "main.tex"
    with gzip.open(archive, "rb") as src, open(main_tex, "wb") as dst:
        shutil.copyfileobj(src, dst)
    return f"gz -> {main_tex}"


def main():
    parser = argparse.ArgumentParser(description="Unpack an arXiv e-print bundle")
    parser.add_argument("archive", help="Downloaded e-print file (.tar.gz)")
    parser.add_argument("dest", help="Directory to unpack into")
    args = parser.parse_args()

    archive = Path(args.archive)
    if not archive.is_file():
        raise SystemExit(f"ERROR: archive not found: {archive}")

    print("OK " + unpack(archive, Path(args.dest)))


if __name__ == "__main__":
    main()
