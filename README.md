# sa-gbv-data
An open-source, automated data pipeline transforming public South African SAPS crime statistics and police precinct boundaries into cloud-native geospatial formats (GeoParquet &amp; PMTiles).

## Ingestion commands

The Python package lives in `src/sa_gbv_data/ingest`. Install it with:

```text
pip install -e .
```

Each source has a standalone module:

- `saps_crime`: SAPS quarterly Excel or PDF tables
- `saps_precincts`: SAPS precinct boundary ZIP downloads
- `municipal_wards`: MDB Spatial Hub GeoJSON or Shapefile exports
- `census_sal`: Stats SA Census Small Area Layer Shapefile or Parquet
- `osm_risk`: Overpass API infrastructure features

Examples:

```text
python -m sa_gbv_data.ingest.saps_crime data/raw/saps.xlsx data/processed/saps_crime.parquet
python -m sa_gbv_data.ingest.saps_precincts https://example.org/precincts.zip data/processed/precincts.parquet
python -m sa_gbv_data.ingest.municipal_wards data/raw/wards.geojson data/processed/wards.parquet
python -m sa_gbv_data.ingest.census_sal data/raw/sal.shp data/processed/sal.parquet
python -m sa_gbv_data.ingest.osm_risk -35.0 18.0 -33.5 19.0 data/processed/osm_risk.parquet
```

The commands validate the required source fields and write columnar Parquet outputs. Replace the example SAPS and MDB URLs/paths with the current official downloads when running them.

## Data contracts and tests

Normalized schemas are defined in `src/sa_gbv_data/contracts.py`. Each contract checks required fields, nullability, scalar types, geometry validity, and SAL code uniqueness before an output is written. Run the regression suite with:

```text
python -m pytest -q
```
