"""Ingest municipal and ward boundary data from MDB Spatial Hub exports."""

import argparse
from pathlib import Path

import geopandas as gpd

from ..contracts import MUNICIPAL_WARD_CONTRACT
from .common import validate_with_geoengine, write_geodataframe, write_pmtiles


def ingest(source: Path, output: Path, pmtiles_output: Path | None = None) -> gpd.GeoDataFrame:
    frame = gpd.read_file(source)
    selected = frame[["MUNICNAME", "CAT_B", "WARD_NO", "PROVINCE", "geometry"]]
    MUNICIPAL_WARD_CONTRACT.validate(selected)
    validate_with_geoengine(selected, "municipal_wards")
    write_geodataframe(selected, output)
    write_pmtiles(
        output,
        pmtiles_output or output.with_suffix(".pmtiles"),
        layer_name="municipal_wards",
    )
    return selected


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="GeoJSON, Shapefile, or MDB export")
    parser.add_argument("output", type=Path)
    parser.add_argument("--pmtiles-output", type=Path)
    args = parser.parse_args()
    ingest(args.source, args.output, args.pmtiles_output)


if __name__ == "__main__":
    main()