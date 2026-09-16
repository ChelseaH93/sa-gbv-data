import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Point, Polygon

from sa_gbv_data.contracts import (
    CENSUS_SAL_CONTRACT,
    MUNICIPAL_WARD_CONTRACT,
    OSM_RISK_CONTRACT,
    SAPS_CRIME_CONTRACT,
    SAPS_PRECINCT_CONTRACT,
    ContractViolation,
)


def test_contract_registry_shapes_are_explicit():
    assert set(SAPS_CRIME_CONTRACT.columns) == {
        "station_name", "province", "crime_category", "count", "financial_year", "quarter"
    }
    assert set(SAPS_PRECINCT_CONTRACT.columns) == {"COMPONENT", "STATION", "geometry"}
    assert set(MUNICIPAL_WARD_CONTRACT.columns) == {
        "MUNICNAME", "CAT_B", "WARD_NO", "PROVINCE", "geometry"
    }
    assert set(CENSUS_SAL_CONTRACT.columns) == {"SAL_CODE", "POPULATION", "HOUSEHOLDS"}
    assert set(OSM_RISK_CONTRACT.columns) == {"osm_id", "osm_type", "geometry"}


def test_crime_contract_rejects_missing_and_null_fields():
    frame = pd.DataFrame({"station_name": ["A"]})
    with pytest.raises(ContractViolation, match="missing columns"):
        SAPS_CRIME_CONTRACT.validate(frame)

    valid = pd.DataFrame(
        {
            "station_name": ["A"], "province": ["Gauteng"], "crime_category": ["Robbery"],
            "count": [1], "financial_year": ["2024/25"], "quarter": ["Q1"],
        }
    )
    valid.loc[0, "count"] = None
    with pytest.raises(ContractViolation, match="null values"):
        SAPS_CRIME_CONTRACT.validate(valid)


def test_contract_rejects_wrong_numeric_type():
    frame = pd.DataFrame(
        {
            "station_name": ["A"], "province": ["Gauteng"], "crime_category": ["Robbery"],
            "count": ["not-a-number"], "financial_year": ["2024/25"], "quarter": ["Q1"],
        }
    )
    with pytest.raises(ContractViolation, match="count must be numeric"):
        SAPS_CRIME_CONTRACT.validate(frame)


def test_geometry_contract_rejects_empty_geometry():
    frame = gpd.GeoDataFrame(
        {"COMPONENT": ["C"], "STATION": ["S"], "geometry": [Polygon()]},
        geometry="geometry",
        crs="EPSG:4326",
    )
    with pytest.raises(ContractViolation, match="empty geometry"):
        SAPS_PRECINCT_CONTRACT.validate(frame)


def test_sal_contract_rejects_duplicate_codes():
    frame = pd.DataFrame(
        {"SAL_CODE": ["SAL-1", "SAL-1"], "POPULATION": [10, 20], "HOUSEHOLDS": [4, 8]}
    )
    with pytest.raises(ContractViolation, match="duplicate"):
        CENSUS_SAL_CONTRACT.validate(frame)


def test_osm_contract_accepts_point_features():
    frame = gpd.GeoDataFrame(
        {"osm_id": [1], "osm_type": ["node"], "geometry": [Point(18.4, -33.9)]},
        geometry="geometry",
        crs="EPSG:4326",
    )
    assert OSM_RISK_CONTRACT.validate(frame).equals(frame)