"""Ingest SAPS precinct boundary shapefiles from a static ZIP download."""

import argparse
from pathlib import Path

import geopandas as gpd

from ..contracts import SAPS_PRECINCT_CONTRACT
from .common import (
    download,
    extract_zip,
    validate_with_geoengine,
    write_geodataframe,
    write_pmtiles,
)


def ingest(source: str, output: Path, workdir: Path, pmtiles_output: Path | None = None) -> gpd.GeoDataFrame:
    archive = workdir / "saps_precincts.zip"
    extract_dir = extract_zip(download(source, archive), workdir / "saps_precincts")
    shapefile = next(extract_dir.rglob("*.shp"), None)
    if shapefile is None:
        raise FileNotFoundError("The SAPS precinct archive contains no .shp file")
    frame = gpd.read_file(shapefile)
    selected = frame[["COMPONENT", "STATION", "geometry"]]
    SAPS_PRECINCT_CONTRACT.validate(selected)
    validate_with_geoengine(selected, "saps_precincts")
    write_geodataframe(selected, output)
    write_pmtiles(
        output,
        pmtiles_output or output.with_suffix(".pmtiles"),
        layer_name="saps_precincts",
    )
    return frame


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    parser.add_argument("output", type=Path)
    parser.add_argument("--workdir", type=Path, default=Path("data/raw"))
    parser.add_argument("--pmtiles-output", type=Path)
    args = parser.parse_args()
    ingest(args.url, args.output, args.workdir, args.pmtiles_output)


if __name__ == "__main__":
    main()