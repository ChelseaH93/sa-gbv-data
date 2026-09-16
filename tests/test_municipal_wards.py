import geopandas as gpd
from shapely.geometry import Polygon

from sa_gbv_data.ingest.municipal_wards import normalize_source


def test_hdx_admin4_fields_normalize_to_ward_contract():
    frame = gpd.GeoDataFrame(
        {
            "adm4_name": ["001"],
            "adm3_name": ["Makhado"],
            "adm2_name": ["Vhembe"],
            "adm1_name": ["Limpopo"],
            "geometry": [Polygon([(28, -23), (29, -23), (29, -22), (28, -22)])],
        },
        geometry="geometry",
        crs="EPSG:4326",
    )

    normalized = normalize_source(frame)

    assert normalized[["MUNICNAME", "CAT_B", "WARD_NO", "PROVINCE"]].iloc[0].to_dict() == {
        "MUNICNAME": "Makhado",
        "CAT_B": "Vhembe",
        "WARD_NO": "001",
        "PROVINCE": "Limpopo",
    }