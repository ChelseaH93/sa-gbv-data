"""Shared download and output helpers for ingestion commands."""

from pathlib import Path
from zipfile import ZipFile

import geopandas as gpd
import requests

MAX_GITHUB_FILE_BYTES = 90_000_000
TARGET_CRS = "EPSG:9221"


class RepositorySizeError(ValueError):
    """Raised when an output is too large for a normal GitHub repository."""


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
    if frame.crs is None:
        raise ValueError(f"GeoDataFrame must have a CRS before writing {destination}")
    frame = frame.to_crs(TARGET_CRS)
    frame.to_parquet(destination, index=False)
    enforce_repository_size(destination)


def validate_with_geoengine(frame: gpd.GeoDataFrame, dataset_name: str) -> None:
    """Run geoengine-utils readiness checks before publishing spatial data."""
    try:
        from geoengine_utils import assess_readiness
    except ImportError as error:
        raise ImportError(
            "geoengine-utils readiness import failed; install the project dependencies "
            f"(missing dependency: {error.name or error})"
        ) from error

    report = assess_readiness(frame)
    if not report.passed:
        raise ValueError(f"{dataset_name} readiness check failed:\n{report.format_report()}")


def write_pmtiles(
    parquet: Path,
    destination: Path,
    *,
    layer_name: str,
    min_zoom: int = 0,
    max_zoom: int = 8,
) -> None:
    """Convert a validated GeoParquet file to PMTiles."""
    try:
        from geoengine_utils.cloud import convert_vector_to_pmtiles
    except ImportError as error:
        raise ImportError(
            "Install PMTiles support with `pip install -e .`"
        ) from error

    destination.parent.mkdir(parents=True, exist_ok=True)
    convert_vector_to_pmtiles(
        parquet,
        destination,
        layer_name=layer_name,
        min_zoom=min_zoom,
        max_zoom=max_zoom,
    )
    enforce_repository_size(destination)


def enforce_repository_size(path: Path) -> None:
    """Keep checked-in artifacts below GitHub's 100 MB file limit."""
    size = path.stat().st_size
    if size > MAX_GITHUB_FILE_BYTES:
        raise RepositorySizeError(
            f"{path} is {size:,} bytes; move it to R2 before committing "
            f"(repository guard: {MAX_GITHUB_FILE_BYTES:,} bytes)."
        )