"""Ingest Census Small Area Layer data from Shapefile or Parquet."""

import argparse
from pathlib import Path

import geopandas as gpd
import pandas as pd

from ..contracts import CENSUS_SAL_CONTRACT
from .common import validate_with_geoengine, write_geodataframe, write_pmtiles


def ingest(source: Path, output: Path, pmtiles_output: Path | None = None) -> pd.DataFrame:
    frame = gpd.read_file(source) if source.suffix.lower() == ".shp" else pd.read_parquet(source)
    CENSUS_SAL_CONTRACT.validate(frame)
    if isinstance(frame, gpd.GeoDataFrame):
        validate_with_geoengine(frame, "census_sal")
        write_geodataframe(frame, output)
        write_pmtiles(
            output,
            pmtiles_output or output.with_suffix(".pmtiles"),
            layer_name="census_sal",
        )
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        frame.to_parquet(output, index=False)
    return frame


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--pmtiles-output", type=Path)
    args = parser.parse_args()
    ingest(args.source, args.output, args.pmtiles_output)


if __name__ == "__main__":
    main()