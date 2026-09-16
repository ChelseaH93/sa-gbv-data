from zipfile import ZipFile

import pandas as pd

from sa_gbv_data.ingest.census_microdata import ingest


def test_census_sample_bundle_is_split_to_parquet(tmp_path):
    source = tmp_path / "census.zip"
    for name, frame in {
        "Census2022sample_F18.csv": pd.DataFrame({"QID": [1], "Province": [1]}),
        "Census2022sample_F19.csv": pd.DataFrame({"QID": [1], "DERH_HSIZE": [2]}),
        "Census2022sample_F21.csv": pd.DataFrame({"QID": [1], "PID": [11]}),
    }.items():
        csv_path = tmp_path / name
        frame.to_csv(csv_path, index=False)
    with ZipFile(source, "w") as archive:
        for name in ["Census2022sample_F18.csv", "Census2022sample_F19.csv", "Census2022sample_F21.csv"]:
            archive.write(tmp_path / name, name)

    outputs = ingest(source, tmp_path / "processed")

    assert set(outputs) == {"geography", "households", "persons"}
    assert pd.read_parquet(outputs["persons"])["PID"].tolist() == [11]