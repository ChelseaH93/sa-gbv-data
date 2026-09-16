import geopandas as gpd
from shapely.geometry import Point

from sa_gbv_data.ingest import tcc_centres


def test_tcc_kml_ingest_extracts_points(monkeypatch, tmp_path):
    kml = b'''<kml xmlns="http://www.opengis.net/kml/2.2"><Document><Folder><name>Gauteng</name><Placemark><name>Example TCC</name><description><![CDATA[Hospital<br>Tel: 010 123 4567]]></description><Point><coordinates>28.1,-26.2,0</coordinates></Point></Placemark></Folder></Document></kml>'''

    class Response:
        content = kml

        def raise_for_status(self):
            pass

    monkeypatch.setattr(tcc_centres.requests, "get", lambda *_args, **_kwargs: Response())
    monkeypatch.setattr(tcc_centres, "validate_with_geoengine", lambda *_: None)
    monkeypatch.setattr(tcc_centres, "write_geodataframe", lambda frame, destination: frame.to_parquet(destination, index=False))
    monkeypatch.setattr(tcc_centres, "write_pmtiles", lambda *_args, **_kwargs: None)

    frame = tcc_centres.ingest("https://example.test/tcc.kml", tmp_path / "tcc.parquet")

    assert len(frame) == 1
    assert frame.loc[0, "tcc_name"] == "Example TCC"
    assert frame.loc[0, "province"] == "Gauteng"
    assert isinstance(frame.loc[0, "geometry"], Point)