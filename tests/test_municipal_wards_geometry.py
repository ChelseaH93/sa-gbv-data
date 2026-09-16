import geopandas as gpd
from shapely.geometry import MultiPolygon, Polygon

from sa_gbv_data.ingest.common import normalize_polygon_geometry


def test_polygon_layers_use_multipolygon_geometry_type():
    frame = gpd.GeoDataFrame(
        {"geometry": [Polygon([(0, 0), (1, 0), (1, 1), (0, 0)]), MultiPolygon()]},
        geometry="geometry",
        crs="EPSG:4326",
    )

    normalized = normalize_polygon_geometry(frame)

    assert all(geometry.geom_type == "MultiPolygon" for geometry in normalized.geometry)