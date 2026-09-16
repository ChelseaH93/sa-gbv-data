from pathlib import Path

import pandas as pd

from sa_gbv_data.ingest import saps_crime


def test_current_saps_raw_workbook_layout_is_normalized(monkeypatch):
    summary = pd.DataFrame({"Description": ["summary"]})
    raw = pd.DataFrame(
        {
            "Station": ["Acornhoek", None, ""],
            "District": ["Ehlanzeni", None, "Ehlanzeni"],
            "Province": ["Mpumalanga", None, ""],
            "Crime_Category": ["Murder", None, "Murder"],
            "April 2026 to June 2026": [3, None, None],
        }
    )

    def fake_read_excel(_, **options):
        return raw if options.get("sheet_name") == "RAW Data" else summary

    monkeypatch.setattr(saps_crime.pd, "read_excel", fake_read_excel)
    frame = saps_crime._read_saps_workbook(
        Path("2026-2027_-_1st_Quarter_WEB.xlsm")
    )

    assert frame.to_dict("records") == [
        {
            "station_name": "Acornhoek",
            "province": "Mpumalanga",
            "crime_category": "Murder",
            "count": 3,
            "financial_year": "2026/27",
            "quarter": "Q1",
        }
    ]