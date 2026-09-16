"""Ingest SAPS precinct boundary shapefiles from a static ZIP download."""

import argparse
from pathlib import Path
from zipfile import ZipFile

import geopandas as gpd

from ..contracts import SAPS_PRECINCT_CONTRACT
from .common import (
    download,
    extract_zip,
    normalize_polygon_geometry,
    validate_with_geoengine,
    write_geodataframe,
    write_pmtiles,
)


def _prepare_archive(source: str | Path, workdir: Path) -> Path:
    source_path = Path(source)
    archive = source_path if source_path.exists() else download(str(source), workdir / "saps_precincts.zip")
    extract_dir = extract_zip(archive, workdir / "saps_precincts")
    nested_archive = next(extract_dir.rglob("station_boundaries.zip"), None)
    if nested_archive:
        extract_dir = extract_zip(nested_archive, workdir / "saps_boundaries")
    return extract_dir


def ingest(source: str | Path, output: Path, workdir: Path, pmtiles_output: Path | None = None) -> gpd.GeoDataFrame:
    extract_dir = _prepare_archive(source, workdir)
    shapefile = next(extract_dir.rglob("Police_bounds.shp"), None)
    shapefile = shapefile or next(extract_dir.rglob("*.shp"), None)
    if shapefile is None:
        raise FileNotFoundError("The SAPS precinct archive contains no .shp file")
    frame = gpd.read_file(shapefile)
    if "COMPNT_NM" in frame.columns:
        selected = frame.rename(columns={"COMPNT_NM": "STATION"})
        selected["COMPONENT"] = selected["STATION"]
        selected = selected[["COMPONENT", "STATION", "geometry"]]
    else:
        selected = frame[["COMPONENT", "STATION", "geometry"]]
    selected = normalize_polygon_geometry(selected)
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