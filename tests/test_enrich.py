import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Polygon

from sa_gbv_data import enrich


def test_normalize_station_name_is_stable():
    assert enrich.normalize_station_name("Cape Town - Central") == "capetowncentral"
    assert enrich.normalize_station_name("  CAPE TOWN CENTRAL ") == "capetowncentral"


def test_join_crime_to_precincts_writes_enriched_outputs(tmp_path, monkeypatch):
    crime_path = tmp_path / "crime.parquet"
    precinct_path = tmp_path / "precincts.parquet"
    output = tmp_path / "enriched.parquet"
    unmatched = tmp_path / "unmatched.csv"
    pd.DataFrame(
        {
            "station_name": ["Cape Town - Central", "Unknown"],
            "province": ["Western Cape", "Gauteng"],
            "crime_category": ["Robbery", "Murder"],
            "count": [4, 2],
            "financial_year": ["2024/25", "2024/25"],
            "quarter": ["Q1", "Q1"],
        }
    ).to_parquet(crime_path, index=False)
    gpd.GeoDataFrame(
        {
            "COMPONENT": ["Western Cape"],
            "STATION": ["Cape Town Central"],
            "geometry": [Polygon([(18, -34), (19, -34), (19, -33), (18, -33)])],
        },
        geometry="geometry",
        crs="EPSG:4326",
    ).to_parquet(precinct_path, index=False)

    monkeypatch.setattr(enrich, "validate_with_geoengine", lambda *_: None)
    monkeypatch.setattr(enrich, "write_pmtiles", lambda *_args, **_kwargs: None)

    joined = enrich.join_crime_to_precincts(
        crime_path,
        precinct_path,
        output,
        unmatched_output=unmatched,
    )

    assert len(joined) == 1
    assert joined.loc[0, "count"] == 4
    assert joined.loc[0, "STATION"] == "Cape Town Central"
    assert pd.read_csv(unmatched)["station_name"].tolist() == ["Unknown"]
    assert output.exists()


def test_join_crime_to_precincts_fails_when_nothing_matches(tmp_path, monkeypatch):
    crime_path = tmp_path / "crime.parquet"
    precinct_path = tmp_path / "precincts.parquet"
    pd.DataFrame(
        {
            "station_name": ["Unknown"], "province": ["Gauteng"],
            "crime_category": ["Murder"], "count": [2],
            "financial_year": ["2024/25"], "quarter": ["Q1"],
        }
    ).to_parquet(crime_path, index=False)
    gpd.GeoDataFrame(
        {
            "COMPONENT": ["C"],
            "STATION": ["Other"],
            "geometry": [Polygon([(18, -34), (19, -34), (19, -33), (18, -33)])],
        },
        geometry="geometry",
        crs="EPSG:4326",
    ).to_parquet(precinct_path, index=False)
    monkeypatch.setattr(enrich, "validate_with_geoengine", lambda *_: None)

    with pytest.raises(ValueError, match="No SAPS crime station names matched"):
        enrich.join_crime_to_precincts(crime_path, precinct_path, tmp_path / "out.parquet")