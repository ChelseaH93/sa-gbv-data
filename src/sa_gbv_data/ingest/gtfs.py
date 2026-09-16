"""Ingest static GTFS feeds into consolidated mobility GeoParquet layers."""

import argparse
import re
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import geopandas as gpd
import pandas as pd
import requests
from shapely.geometry import LineString, Point

from .common import validate_with_geoengine, write_geodataframe, write_pmtiles


def _feed_id(url: str, index: int) -> str:
    value = re.sub(r"[^a-z0-9]+", "_", url.casefold()).strip("_")
    return (value[-60:] or f"feed_{index}")


def _read_csv(archive: ZipFile, name: str) -> pd.DataFrame:
    member = next((item for item in archive.namelist() if item.casefold() == name.casefold()), None)
    if member is None:
        return pd.DataFrame()
    with archive.open(member) as stream:
        return pd.read_csv(stream)


def ingest(urls: list[str], stops_output: Path, shapes_output: Path) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """Download and consolidate GTFS stops and shapes from one or more feeds."""
    stops_frames = []
    shapes_frames = []
    with TemporaryDirectory() as temporary_directory:
        for index, url in enumerate(urls):
            archive_path = Path(temporary_directory) / f"feed_{index}.zip"
            with requests.get(url, stream=True, timeout=180) as response:
                response.raise_for_status()
                with archive_path.open("wb") as output:
                    for chunk in response.iter_content(1024 * 1024):
                        if chunk:
                            output.write(chunk)
            feed_id = _feed_id(url, index)
            with ZipFile(archive_path) as archive:
                stops = _read_csv(archive, "stops.txt")
                if not stops.empty:
                    required = {"stop_id", "stop_name", "stop_lat", "stop_lon"}
                    missing = required - set(stops.columns)
                    if missing:
                        raise ValueError(f"GTFS feed is missing stops fields: {sorted(missing)}")
                    stops_frames.append(
                        gpd.GeoDataFrame(
                            stops.assign(feed_id=feed_id),
                            geometry=[Point(lon, lat) for lon, lat in zip(stops.stop_lon, stops.stop_lat)],
                            crs="EPSG:4326",
                        )
                    )

                shapes = _read_csv(archive, "shapes.txt")
                if not shapes.empty:
                    required = {"shape_id", "shape_pt_lat", "shape_pt_lon", "shape_pt_sequence"}
                    missing = required - set(shapes.columns)
                    if missing:
                        raise ValueError(f"GTFS feed is missing shapes fields: {sorted(missing)}")
                    rows = []
                    for shape_id, group in shapes.sort_values("shape_pt_sequence").groupby("shape_id"):
                        points = [Point(lon, lat) for lon, lat in zip(group.shape_pt_lon, group.shape_pt_lat)]
                        if len(points) >= 2:
                            rows.append({"feed_id": feed_id, "shape_id": shape_id, "geometry": LineString(points)})
                    if rows:
                        shapes_frames.append(gpd.GeoDataFrame(rows, geometry="geometry", crs="EPSG:4326"))

    stops_frame = gpd.GeoDataFrame(pd.concat(stops_frames, ignore_index=True), geometry="geometry", crs="EPSG:4326") if stops_frames else gpd.GeoDataFrame(columns=["feed_id", "geometry"], geometry="geometry", crs="EPSG:4326")
    shapes_frame = gpd.GeoDataFrame(pd.concat(shapes_frames, ignore_index=True), geometry="geometry", crs="EPSG:4326") if shapes_frames else gpd.GeoDataFrame(columns=["feed_id", "shape_id", "geometry"], geometry="geometry", crs="EPSG:4326")
    if stops_frame.empty and shapes_frame.empty:
        raise ValueError("GTFS feeds contained no stops.txt or shapes.txt records")
    if not stops_frame.empty:
        validate_with_geoengine(stops_frame, "mobility_stops")
        write_geodataframe(stops_frame, stops_output)
        write_pmtiles(stops_output, stops_output.with_suffix(".pmtiles"), layer_name="mobility_stops")
    if not shapes_frame.empty:
        validate_with_geoengine(shapes_frame, "mobility_shapes")
        write_geodataframe(shapes_frame, shapes_output)
        write_pmtiles(shapes_output, shapes_output.with_suffix(".pmtiles"), layer_name="mobility_shapes")
    return stops_frame, shapes_frame


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("urls", help="Comma-separated static GTFS ZIP URLs")
    parser.add_argument("stops_output", type=Path)
    parser.add_argument("shapes_output", type=Path)
    args = parser.parse_args()
    ingest([url.strip() for url in args.urls.split(",") if url.strip()], args.stops_output, args.shapes_output)


if __name__ == "__main__":
    main()