"""Ingest municipal and ward boundary data from MDB Spatial Hub exports."""

import argparse
from pathlib import Path

import geopandas as gpd

from ..contracts import MUNICIPAL_WARD_CONTRACT
from .common import write_geodataframe


def ingest(source: Path, output: Path) -> gpd.GeoDataFrame:
    frame = gpd.read_file(source)
    selected = frame[["MUNICNAME", "CAT_B", "WARD_NO", "PROVINCE", "geometry"]]
    MUNICIPAL_WARD_CONTRACT.validate(selected)
    write_geodataframe(selected, output)
    return selected


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="GeoJSON, Shapefile, or MDB export")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    ingest(args.source, args.output)


if __name__ == "__main__":
    main()