"""Ingest SAPS quarterly crime statistics from Excel or PDF exports."""

import argparse
from pathlib import Path

import pandas as pd

from ..contracts import SAPS_CRIME_CONTRACT


def ingest(source: Path, output: Path) -> pd.DataFrame:
    """Read a SAPS export, normalize its column names, and write Parquet."""
    if source.suffix.lower() in {".xlsx", ".xls"}:
        frame = pd.read_excel(source)
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

    frame.columns = [str(column).strip().lower().replace(" ", "_") for column in frame.columns]
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