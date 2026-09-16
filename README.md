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
python -m sa_gbv_data.enrich data/processed/saps_crime.parquet data/processed/precincts.parquet data/processed/saps_crime_enriched.parquet
```

The commands validate the required source fields, run `geoengine-utils` spatial readiness checks, and write columnar Parquet outputs. Spatial commands also write a PMTiles archive beside the Parquet file by default; use `--pmtiles-output` to choose another path. SAPS crime is tabular and remains GeoParquet-only until it is joined to a spatial dataset. Replace the example SAPS and MDB URLs/paths with the current official downloads when running them.

Outputs are kept under `data/` while they are small enough for GitHub. A repository-size guard stops artifacts at 90 MB, leaving room below GitHub's hard per-file limit; move larger outputs to R2 when that happens.

The enrichment command joins normalized station names from SAPS crime to precinct `STATION` values, keeps unmatched stations in a `.unmatched.csv` report, and produces a map-ready crime GeoParquet plus PMTiles layer.

## Data contracts and tests

Normalized schemas are defined in `src/sa_gbv_data/contracts.py`. Each contract checks required fields, nullability, scalar types, geometry validity, and SAL code uniqueness before an output is written. Run the regression suite with:

```text
python -m pytest -q
```
