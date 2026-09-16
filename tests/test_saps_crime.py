from pathlib import Path

import pandas as pd

from sa_gbv_data.ingest import saps_crime


def test_saps_crime_ingest_writes_contract_compliant_parquet(tmp_path, monkeypatch):
    source = Path("crime.xlsx")
    output = tmp_path / "crime.parquet"
    source_frame = pd.DataFrame(
        {
            "Station Name": ["Central"], "Province": ["Gauteng"],
            "Crime Category": ["Robbery"], "Count": ["7"],
            "Financial Year": ["2024/25"], "Quarter": ["Q1"],
        }
    )
    monkeypatch.setattr(saps_crime.pd, "read_excel", lambda _, **__: source_frame)

    first = saps_crime.ingest(source, output)
    first_bytes = output.read_bytes()
    second = saps_crime.ingest(source, output)

    assert first["count"].tolist() == [7]
    assert second.equals(first)
    assert output.read_bytes() == first_bytes
    assert pd.read_parquet(output)["station_name"].tolist() == ["Central"]