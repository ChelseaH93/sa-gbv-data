"""Ingest SAPS quarterly crime statistics from Excel or PDF exports."""

import argparse
import re
from pathlib import Path

import pandas as pd

from ..contracts import SAPS_CRIME_CONTRACT


def _normalize_columns(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    frame.columns = [str(column).strip().lower().replace(" ", "_") for column in frame.columns]
    return frame


def _read_saps_workbook(source: Path) -> pd.DataFrame:
    frame = _normalize_columns(pd.read_excel(source))
    if "count" in frame.columns:
        return frame

    # Current SAPS workbooks keep station-level records on a hidden RAW Data
    # sheet and store the latest quarter total in the final AC column.
    raw = pd.read_excel(source, sheet_name="RAW Data", header=2, usecols="E:H,AC")
    raw = raw.iloc[:, [0, 2, 3, 4]].copy()
    raw.columns = ["station_name", "province", "crime_category", "count"]
    year_match = re.search(r"(20\d{2})-(20\d{2})", source.stem)
    quarter_match = re.search(r"(\d)(?:st|nd|rd|th)[ _-]+quarter", source.stem, re.IGNORECASE)
    raw["financial_year"] = (
        f"{year_match.group(1)}/{year_match.group(2)[-2:]}" if year_match else "unknown"
    )
    raw["quarter"] = f"Q{quarter_match.group(1)}" if quarter_match else "unknown"
    return raw


def ingest(source: Path, output: Path) -> pd.DataFrame:
    """Read a SAPS export, normalize its column names, and write Parquet."""
    if source.suffix.lower() in {".xlsx", ".xls", ".xlsm"}:
        frame = _read_saps_workbook(source)
    elif source.suffix.lower() == ".pdf":
        try:
            import pdfplumber
        except ImportError as error:
            raise ImportError("Install the PDF extra with `pip install pdfplumber` to ingest PDF files") from error
        tables = []
        with pdfplumber.open(source) as document:
            for page in document.pages:
                tables.extend(table for table in page.extract_tables() if table)
        if not tables:
            raise ValueError("No tables found in SAPS crime PDF")
        header, *rows = tables[0]
        frame = pd.DataFrame(rows, columns=header)
        for table in tables[1:]:
            frame = pd.concat([frame, pd.DataFrame(table[1:], columns=table[0])], ignore_index=True)
    else:
        raise ValueError(f"Unsupported SAPS crime source: {source.suffix}")

    frame = _normalize_columns(frame)
    frame["count"] = pd.to_numeric(frame["count"], errors="coerce")
    SAPS_CRIME_CONTRACT.validate(frame)
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(output, index=False)
    return frame


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    ingest(args.source, args.output)


if __name__ == "__main__":
    main()