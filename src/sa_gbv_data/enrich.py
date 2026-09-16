"""Join SAPS crime records to precinct geometries for map delivery."""

import argparse
import re
from pathlib import Path

import geopandas as gpd
import pandas as pd

from .contracts import SAPS_CRIME_CONTRACT, SAPS_PRECINCT_CONTRACT
from .ingest.common import (
    TARGET_CRS,
    normalize_polygon_geometry,
    validate_with_geoengine,
    write_geodataframe,
    write_pmtiles,
)


def normalize_station_name(value: str) -> str:
    """Create a stable join key for station names from different source systems."""
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def join_crime_to_precincts(
    crime_source: Path,
    precinct_source: Path,
    output: Path,
    *,
    pmtiles_output: Path | None = None,
    unmatched_output: Path | None = None,
    simplify_tolerance_meters: float = 25.0,
) -> gpd.GeoDataFrame:
    """Publish crime records with matching precinct geometry."""
    crime = pd.read_parquet(crime_source)
    precincts = gpd.read_parquet(precinct_source)
    SAPS_CRIME_CONTRACT.validate(crime)
    SAPS_PRECINCT_CONTRACT.validate(precincts)

    crime = crime.copy()
    precincts = precincts.copy()
    if simplify_tolerance_meters < 0:
        raise ValueError("simplify_tolerance_meters must be non-negative")
    # Keep the source precinct artifact authoritative; the enriched map layer
    # only needs a compact geometry because it repeats it per crime record.
    precincts = normalize_polygon_geometry(precincts).to_crs(TARGET_CRS)
    if simplify_tolerance_meters:
        precincts["geometry"] = precincts.geometry.simplify(
            simplify_tolerance_meters,
            preserve_topology=True,
        )
    crime["_station_key"] = crime["station_name"].map(normalize_station_name)
    precincts["_station_key"] = precincts["STATION"].map(normalize_station_name)

    precinct_keys = set(precincts["_station_key"])
    unmatched = crime.loc[
        ~crime["_station_key"].isin(precinct_keys), ["station_name", "province"]
    ].drop_duplicates().sort_values(["province", "station_name"])
    if unmatched_output is None:
        unmatched_output = output.with_suffix(".unmatched.csv")
    unmatched_output.parent.mkdir(parents=True, exist_ok=True)
    unmatched.to_csv(unmatched_output, index=False)

    joined = precincts.merge(
        crime,
        on="_station_key",
        how="inner",
        suffixes=("", "_crime"),
    ).drop(columns=["_station_key"])
    if joined.empty:
        raise ValueError(
            "No SAPS crime station names matched the precinct layer. "
            f"Review {unmatched_output}."
        )

    joined = gpd.GeoDataFrame(joined, geometry="geometry", crs=precincts.crs)
    validate_with_geoengine(joined, "saps_crime_enriched")
    write_geodataframe(joined, output)
    write_pmtiles(
        output,
        pmtiles_output or output.with_suffix(".pmtiles"),
        layer_name="saps_crime",
    )
    return joined


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("crime", type=Path, help="Normalized SAPS crime GeoParquet")
    parser.add_argument("precincts", type=Path, help="Normalized SAPS precinct GeoParquet")
    parser.add_argument("output", type=Path, help="Enriched GeoParquet output")
    parser.add_argument("--pmtiles-output", type=Path)
    parser.add_argument("--unmatched-output", type=Path)
    parser.add_argument("--simplify-tolerance-meters", type=float, default=25.0)
    args = parser.parse_args()
    join_crime_to_precincts(
        args.crime,
        args.precincts,
        args.output,
        pmtiles_output=args.pmtiles_output,
        unmatched_output=args.unmatched_output,
        simplify_tolerance_meters=args.simplify_tolerance_meters,
    )


if __name__ == "__main__":
    main()