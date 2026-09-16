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

## Automated refresh and R2 publishing

The [data pipeline workflow](.github/workflows/data-pipeline.yml) runs unit tests and source checks on pushes and pull requests. It polls the SAPS export daily at 04:17 UTC, can be started manually, reruns the configured ingestion/enrichment steps, validates every generated GeoParquet file with `geoengine-utils`, and overwrites the `latest/` objects in R2.

Configure these GitHub repository variables and secrets:

- Repository variable `SAPS_CRIME_URL`: current SAPS Excel export URL
- Repository variable `SAPS_PRECINCT_URL`: optional precinct boundary ZIP URL
- Repository variable `MDB_BOUNDARIES_URL`: optional MDB GeoJSON/Shapefile/ZIP URL
- Repository variable `CENSUS_SAL_URL`: optional Census SAL Parquet/Shapefile/ZIP URL
- Repository variables `OSM_SOUTH`, `OSM_WEST`, `OSM_NORTH`, `OSM_EAST`: optional Overpass bounding box
- Secret `R2_ACCOUNT_ID`: Cloudflare account ID
- Secret `R2_BUCKET`: R2 bucket name
- Secret `R2_ACCESS_KEY_ID`: R2 API token access key
- Secret `R2_SECRET_ACCESS_KEY`: R2 API token secret key

R2 publishing is implemented in `src/sa_gbv_data/publish_r2.py`. Uploads use stable keys under `latest/`, so a successful refresh replaces the previous dataset versions.

When all source URLs and OSM bounds are configured, the workflow publishes `saps_crime`, `precincts`, `municipal_wards`, `census_sal`, `osm_risk`, and `saps_crime_enriched` GeoParquet files. Spatial outputs also receive matching PMTiles files; raw tabular SAPS crime is intentionally Parquet-only.

## Free web map

The static map in `web/` is ready to deploy with the free Cloudflare Pages plan. Connect the repository in Cloudflare Pages, set the build output directory to `web`, and use no build command. Before deployment, edit `web/config.js` and set `R2_BASE_URL` to the public R2/custom-domain URL containing the `latest/processed` directory.

GeoParquet outputs are written in `EPSG:9221` (Hartebeesthoek94 / ZAF BSU Albers 25E). PMTiles use the Web Mercator tiling convention required by browser vector-tile clients such as MapLibre; the authoritative GeoParquet remains in EPSG:9221.

The current official SAPS first-quarter workbook is `https://www.saps.gov.za/services/downloads/2026/2026-2027_-_1st_Quarter_WEB.xlsm`.

The manually downloaded SAPS boundary archive is stored at `data/raw/saps_station_boundaries_points.zip`. It contains both station points and polygon boundaries; the workflow uses the polygon boundaries for crime enrichment when `SAPS_PRECINCT_URL` is not configured.

## Data contracts and tests

Normalized schemas are defined in `src/sa_gbv_data/contracts.py`. Each contract checks required fields, nullability, scalar types, geometry validity, and SAL code uniqueness before an output is written. Run the regression suite with:

```text
python -m pytest -q
```
