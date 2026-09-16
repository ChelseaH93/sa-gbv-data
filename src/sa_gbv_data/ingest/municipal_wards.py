"""Ingest municipal and ward boundary data from MDB Spatial Hub exports."""

import argparse
from pathlib import Path

import geopandas as gpd

from ..contracts import MUNICIPAL_WARD_CONTRACT
from .common import validate_with_geoengine, write_geodataframe, write_pmtiles


def normalize_source(frame: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Normalize MDB or HDX admin-4 ward fields to the project contract."""
    if {"MUNICNAME", "CAT_B", "WARD_NO", "PROVINCE"}.issubset(frame.columns):
        return frame[["MUNICNAME", "CAT_B", "WARD_NO", "PROVINCE", "geometry"]]
    required = {"adm4_name", "adm3_name", "adm2_name", "adm1_name", "geometry"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Municipal/ward source is missing columns: {sorted(missing)}")
    normalized = frame.rename(
        columns={
            "adm3_name": "MUNICNAME",
            "adm4_name": "WARD_NO",
            "adm1_name": "PROVINCE",
            "adm2_name": "CAT_B",
        }
    )
    return normalized[["MUNICNAME", "CAT_B", "WARD_NO", "PROVINCE", "geometry"]]


def ingest(source: Path, output: Path, pmtiles_output: Path | None = None) -> gpd.GeoDataFrame:
    frame = gpd.read_file(source)
    selected = normalize_source(frame)
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