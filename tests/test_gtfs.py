from zipfile import ZipFile

from sa_gbv_data.ingest import gtfs


def test_gtfs_feed_is_consolidated(monkeypatch, tmp_path):
    archive_path = tmp_path / "feed.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr("stops.txt", "stop_id,stop_name,stop_lat,stop_lon\nS1,Central,-33.9,18.4\n")
        archive.writestr("shapes.txt", "shape_id,shape_pt_lat,shape_pt_lon,shape_pt_sequence\nR1,-33.9,18.4,1\nR1,-33.91,18.41,2\n")

    class Response:
        def __enter__(self): return self
        def __exit__(self, *_): pass
        def raise_for_status(self): pass
        def iter_content(self, _size): yield archive_path.read_bytes()

    monkeypatch.setattr(gtfs.requests, "get", lambda *_args, **_kwargs: Response())
    monkeypatch.setattr(gtfs, "validate_with_geoengine", lambda *_: None)
    monkeypatch.setattr(gtfs, "write_pmtiles", lambda *_args, **_kwargs: None)

    stops, shapes = gtfs.ingest(["https://example.test/feed.zip"], tmp_path / "stops.parquet", tmp_path / "shapes.parquet")

    assert len(stops) == 1
    assert len(shapes) == 1
    assert stops.loc[0, "stop_id"] == "S1"
    assert shapes.loc[0, "shape_id"] == "R1"