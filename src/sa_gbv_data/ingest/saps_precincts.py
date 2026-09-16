"""Ingest SAPS precinct boundary shapefiles from a static ZIP download."""

import argparse
from pathlib import Path

import geopandas as gpd

from ..contracts import SAPS_PRECINCT_CONTRACT
from .common import download, extract_zip, write_geodataframe


def ingest(source: str, output: Path, workdir: Path) -> gpd.GeoDataFrame:
    archive = workdir / "saps_precincts.zip"
    extract_dir = extract_zip(download(source, archive), workdir / "saps_precincts")
    shapefile = next(extract_dir.rglob("*.shp"), None)
    if shapefile is None:
        raise FileNotFoundError("The SAPS precinct archive contains no .shp file")
    frame = gpd.read_file(shapefile)
    selected = frame[["COMPONENT", "STATION", "geometry"]]
    SAPS_PRECINCT_CONTRACT.validate(selected)
    write_geodataframe(selected, output)
    return frame


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    parser.add_argument("output", type=Path)
    parser.add_argument("--workdir", type=Path, default=Path("data/raw"))
    args = parser.parse_args()
    ingest(args.url, args.output, args.workdir)


if __name__ == "__main__":
    main()