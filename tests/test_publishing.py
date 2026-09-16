import sys
import types
from pathlib import Path

import geopandas as gpd
import pytest
from shapely.geometry import Point

from sa_gbv_data.ingest import common


def test_validate_with_geoengine_rejects_failed_readiness(monkeypatch):
    class FailedReport:
        passed = False

        def format_report(self):
            return "invalid geometry"

    fake_geoengine = types.ModuleType("geoengine_utils")
    fake_geoengine.assess_readiness = lambda _: FailedReport()
    monkeypatch.setitem(sys.modules, "geoengine_utils", fake_geoengine)

    frame = gpd.GeoDataFrame({"geometry": [Point(18.4, -33.9)]}, crs="EPSG:4326")
    with pytest.raises(ValueError, match="invalid geometry"):
        common.validate_with_geoengine(frame, "sample")


def test_write_pmtiles_delegates_with_expected_options(monkeypatch, tmp_path):
    calls = {}

    def fake_convert(source, output, **options):
        calls.update(source=source, output=output, options=options)
        Path(output).write_bytes(b"pmtiles")

    fake_cloud = types.ModuleType("geoengine_utils.cloud")
    fake_cloud.convert_vector_to_pmtiles = fake_convert
    fake_geoengine = types.ModuleType("geoengine_utils")
    monkeypatch.setitem(sys.modules, "geoengine_utils", fake_geoengine)
    monkeypatch.setitem(sys.modules, "geoengine_utils.cloud", fake_cloud)

    source = tmp_path / "sample.parquet"
    output = tmp_path / "sample.pmtiles"
    source.write_bytes(b"parquet")
    common.write_pmtiles(source, output, layer_name="sample", min_zoom=2, max_zoom=6)

    assert calls["source"] == source
    assert calls["output"] == output
    assert calls["options"] == {"layer_name": "sample", "min_zoom": 2, "max_zoom": 6}


def test_repository_size_guard_rejects_large_artifacts(monkeypatch, tmp_path):
    artifact = tmp_path / "large.pmtiles"
    artifact.write_bytes(b"x" * 10)
    monkeypatch.setattr(common, "MAX_GITHUB_FILE_BYTES", 9)

    with pytest.raises(common.RepositorySizeError, match="move it to R2"):
        common.enforce_repository_size(artifact)