"""Fetch infrastructure risk features from OpenStreetMap Overpass API."""

import argparse
from pathlib import Path

import geopandas as gpd
import requests
from shapely.geometry import Point

from ..contracts import OSM_RISK_CONTRACT
from .common import enforce_repository_size, validate_with_geoengine, write_pmtiles

DEFAULT_ENDPOINT = "https://overpass-api.de/api/interpreter"


def build_query(south: float, west: float, north: float, east: float) -> str:
    bbox = f"{south},{west},{north},{east}"
    return f"""[out:json][timeout:120];(nwr[highway=street_lamp]({bbox});nwr[amenity=police]({bbox});nwr[building=informal]({bbox}););out center tags;"""


def ingest(
    south: float,
    west: float,
    north: float,
    east: float,
    output: Path,
    endpoint: str = DEFAULT_ENDPOINT,
    pmtiles_output: Path | None = None,
) -> gpd.GeoDataFrame:
    response = requests.post(endpoint, data=build_query(south, west, north, east), timeout=180)
    response.raise_for_status()
    rows = []
    for element in response.json().get("elements", []):
        location = element.get("center", element)
        if "lat" not in location or "lon" not in location:
            continue
        rows.append({"osm_id": element["id"], "osm_type": element["type"], **element.get("tags", {}), "geometry": Point(location["lon"], location["lat"])})
    frame = gpd.GeoDataFrame(rows, geometry="geometry", crs="EPSG:4326")
    OSM_RISK_CONTRACT.validate(frame)
    validate_with_geoengine(frame, "osm_risk")
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(output, index=False)
    enforce_repository_size(output)
    write_pmtiles(
        output,
        pmtiles_output or output.with_suffix(".pmtiles"),
        layer_name="osm_risk",
    )
    return frame


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("south", type=float)
    parser.add_argument("west", type=float)
    parser.add_argument("north", type=float)
    parser.add_argument("east", type=float)
    parser.add_argument("output", type=Path)
    parser.add_argument("--pmtiles-output", type=Path)
    args = parser.parse_args()
    ingest(args.south, args.west, args.north, args.east, args.output, pmtiles_output=args.pmtiles_output)


if __name__ == "__main__":
    main()