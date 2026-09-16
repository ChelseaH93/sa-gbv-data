"""Executable data contracts for normalized ingestion outputs."""

from dataclasses import dataclass, field
from typing import Literal

import pandas as pd

ColumnType = Literal["string", "numeric", "integer", "geometry"]


class ContractViolation(ValueError):
    """Raised when an input does not satisfy a dataset contract."""


@dataclass(frozen=True)
class DataContract:
    name: str
    columns: dict[str, ColumnType]
    non_null: frozenset[str] = field(default_factory=frozenset)
    unique: tuple[str, ...] = ()

    def validate(self, frame: pd.DataFrame) -> pd.DataFrame:
        """Validate and return ``frame`` without changing its contents."""
        missing = set(self.columns) - set(frame.columns)
        if missing:
            raise ContractViolation(f"{self.name} is missing columns: {sorted(missing)}")

        null_fields = [
            column for column in self.non_null if frame[column].isna().any()
        ]
        if null_fields:
            raise ContractViolation(f"{self.name} has null values in: {sorted(null_fields)}")

        for column, column_type in self.columns.items():
            values = frame[column]
            if column_type == "string" and not values.map(lambda value: isinstance(value, str)).all():
                raise ContractViolation(f"{self.name}.{column} must contain strings")
            if column_type == "numeric" and not pd.api.types.is_numeric_dtype(values):
                raise ContractViolation(f"{self.name}.{column} must be numeric")
            if column_type == "integer":
                if not pd.api.types.is_integer_dtype(values):
                    raise ContractViolation(f"{self.name}.{column} must contain integers")
            if column_type == "geometry":
                if values.isna().any() or values.map(lambda value: value.is_empty).any():
                    raise ContractViolation(f"{self.name}.{column} contains empty geometry")

        if self.unique and frame.duplicated(list(self.unique)).any():
            raise ContractViolation(f"{self.name} has duplicate values for: {self.unique}")
        return frame


SAPS_CRIME_CONTRACT = DataContract(
    name="saps_crime",
    columns={
        "station_name": "string",
        "province": "string",
        "crime_category": "string",
        "count": "numeric",
        "financial_year": "string",
        "quarter": "string",
    },
    non_null=frozenset({"station_name", "province", "crime_category", "count", "financial_year", "quarter"}),
)

SAPS_PRECINCT_CONTRACT = DataContract(
    name="saps_precincts",
    columns={"COMPONENT": "string", "STATION": "string", "geometry": "geometry"},
    non_null=frozenset({"COMPONENT", "STATION", "geometry"}),
)

MUNICIPAL_WARD_CONTRACT = DataContract(
    name="municipal_wards",
    columns={
        "MUNICNAME": "string",
        "CAT_B": "string",
        "WARD_NO": "string",
        "PROVINCE": "string",
        "geometry": "geometry",
    },
    non_null=frozenset({"MUNICNAME", "CAT_B", "WARD_NO", "PROVINCE", "geometry"}),
)

CENSUS_SAL_CONTRACT = DataContract(
    name="census_sal",
    columns={"SAL_CODE": "string", "POPULATION": "numeric", "HOUSEHOLDS": "numeric"},
    non_null=frozenset({"SAL_CODE", "POPULATION", "HOUSEHOLDS"}),
    unique=("SAL_CODE",),
)

OSM_RISK_CONTRACT = DataContract(
    name="osm_risk",
    columns={"osm_id": "integer", "osm_type": "string", "geometry": "geometry"},
    non_null=frozenset({"osm_id", "osm_type", "geometry"}),
)

DATA_CONTRACTS = {
    contract.name: contract
    for contract in (
        SAPS_CRIME_CONTRACT,
        SAPS_PRECINCT_CONTRACT,
        MUNICIPAL_WARD_CONTRACT,
        CENSUS_SAL_CONTRACT,
        OSM_RISK_CONTRACT,
    )
}