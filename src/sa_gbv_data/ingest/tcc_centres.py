"""Ingest Thuthuzela Care Centre locations from the official Google My Maps KML."""

import argparse
from html import unescape
from pathlib import Path
from xml.etree import ElementTree

import geopandas as gpd
import requests
from shapely.geometry import Point

from .common import validate_with_geoengine, write_geodataframe, write_pmtiles

DEFAULT_KML_URL = (
    "https://www.google.com/maps/d/u/0/kml?mid="
    "1J5vQRQD2NXR36hwuig8OhV8uO2B5JX0i&forcekml=1"
)
KML_NAMESPACE = "{http://www.opengis.net/kml/2.2}"


def ingest(source: str, output: Path, pmtiles_output: Path | None = None) -> gpd.GeoDataFrame:
    response = requests.get(source, timeout=120)
    response.raise_for_status()
    root = ElementTree.fromstring(response.content)
    rows = []
    for folder in root.findall(f".//{KML_NAMESPACE}Folder"):
        province = (folder.findtext(f"{KML_NAMESPACE}name") or "").strip()
        for placemark in folder.findall(f"{KML_NAMESPACE}Placemark"):
            name = (placemark.findtext(f"{KML_NAMESPACE}name") or "").strip()
            coordinates = placemark.findtext(f"{KML_NAMESPACE}Point/{KML_NAMESPACE}coordinates")
            if not name or not coordinates:
                continue
            longitude, latitude, *_ = coordinates.strip().split(",")
            description = unescape(placemark.findtext(f"{KML_NAMESPACE}description") or "")
            rows.append(
                {
                    "tcc_name": name,
                    "province": province,
                    "description": description,
                    "geometry": Point(float(longitude), float(latitude)),
                }
            )
    frame = gpd.GeoDataFrame(rows, geometry="geometry", crs="EPSG:4326")
    if frame.empty:
        raise ValueError("The TCC KML contained no point placemarks")
    validate_with_geoengine(frame, "tcc_centres")
    write_geodataframe(frame, output)
    write_pmtiles(output, pmtiles_output or output.with_suffix(".pmtiles"), layer_name="tcc_centres")
    return frame


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--url", default=DEFAULT_KML_URL)
    parser.add_argument("--pmtiles-output", type=Path)
    args = parser.parse_args()
    ingest(args.url, args.output, args.pmtiles_output)


if __name__ == "__main__":
    main()