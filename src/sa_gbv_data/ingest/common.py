"""Shared download and output helpers for ingestion commands."""

from pathlib import Path
from zipfile import ZipFile

import geopandas as gpd
import requests


def download(url: str, destination: Path) -> Path:
    """Download a URL to disk, creating parent directories as needed."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=120) as response:
        response.raise_for_status()
        with destination.open("wb") as output:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    output.write(chunk)
    return destination


def extract_zip(archive: Path, destination: Path) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    with ZipFile(archive) as zipped:
        zipped.extractall(destination)
    return destination


def write_geodataframe(frame: gpd.GeoDataFrame, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(destination, index=False)