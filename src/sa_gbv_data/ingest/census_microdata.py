"""Normalize the Stats SA Census 2022 sample CSV bundle to Parquet."""

import argparse
from pathlib import Path
from zipfile import ZipFile

import pandas as pd


def ingest(source: Path, output_dir: Path) -> dict[str, Path]:
    """Extract the Census sample tables and write one Parquet file per table."""
    output_dir.mkdir(parents=True, exist_ok=True)
    with ZipFile(source) as archive:
        names = {Path(name).name: name for name in archive.namelist()}
        expected = {
            "geography": "Census2022sample_F18.csv",
            "households": "Census2022sample_F19.csv",
            "persons": "Census2022sample_F21.csv",
        }
        missing = set(expected.values()) - set(names)
        if missing:
            raise ValueError(f"Census sample archive is missing: {sorted(missing)}")

        outputs = {}
        for key, filename in expected.items():
            with archive.open(names[filename]) as stream:
                frame = pd.read_csv(stream)
            destination = output_dir / f"census2022_{key}.parquet"
            frame.to_parquet(destination, index=False)
            outputs[key] = destination
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    ingest(args.source, args.output_dir)


if __name__ == "__main__":
    main()