"""Bulk payer import from CSV files."""
import csv
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from app.db import insert_payer

REQUIRED_COLUMNS = ["name", "address", "place", "amount"]
OPTIONAL_COLUMNS = ["model", "reference", "purpose_code", "description"]


@dataclass
class ImportResult:
    imported: int
    errors: list[str]


def import_payers_csv(conn: sqlite3.Connection, path: Path) -> ImportResult:
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        missing = [col for col in REQUIRED_COLUMNS if col not in (reader.fieldnames or [])]
        if missing:
            return ImportResult(0, [f"Missing required column(s): {', '.join(missing)}"])

        imported = 0
        errors = []
        for line_number, row in enumerate(reader, start=2):
            name = (row.get("name") or "").strip()
            if not name:
                errors.append(f"Row {line_number}: name is required")
                continue

            amount_text = (row.get("amount") or "").strip().replace(",", ".")
            try:
                amount = float(amount_text)
            except ValueError:
                errors.append(f"Row {line_number}: invalid amount {amount_text!r}")
                continue
            if amount <= 0:
                errors.append(f"Row {line_number}: amount must be greater than 0")
                continue

            insert_payer(
                conn,
                name=name,
                address=(row.get("address") or "").strip(),
                place=(row.get("place") or "").strip(),
                amount=amount,
                model=(row.get("model") or "").strip() or "HR00",
                reference=(row.get("reference") or "").strip(),
                purpose_code=(row.get("purpose_code") or "").strip(),
                description=(row.get("description") or "").strip(),
            )
            imported += 1

        return ImportResult(imported, errors)
