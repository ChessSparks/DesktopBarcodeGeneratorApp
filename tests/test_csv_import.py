from pathlib import Path

from app.csv_import import import_payers_csv
from app.db import get_connection, list_payers


def test_import_valid_csv(tmp_path: Path):
    csv_path = tmp_path / "payers.csv"
    csv_path.write_text(
        "name,address,place,amount,model,reference,purpose_code,description\n"
        "Ivan Ivic,Ilica 10,10000 Zagreb,25.00,HR01,00-001,COST,Clanarina srpanj\n"
        "Ana Anic,Vlaska 5,10000 Zagreb,40.5,,00-002,,\n"
    )
    conn = get_connection(tmp_path / "test.db")

    result = import_payers_csv(conn, csv_path)

    assert result.imported == 2
    assert result.errors == []
    rows = list_payers(conn)
    assert len(rows) == 2
    assert rows[1]["model"] == "HR00"


def test_import_reports_row_errors(tmp_path: Path):
    csv_path = tmp_path / "payers.csv"
    csv_path.write_text(
        "name,address,place,amount,model,reference,purpose_code,description\n"
        ",Ilica 10,10000 Zagreb,25.00,,,, \n"
        "Ana Anic,Vlaska 5,10000 Zagreb,not-a-number,,,,\n"
    )
    conn = get_connection(tmp_path / "test.db")

    result = import_payers_csv(conn, csv_path)

    assert result.imported == 0
    assert len(result.errors) == 2


def test_import_missing_required_column(tmp_path: Path):
    csv_path = tmp_path / "payers.csv"
    csv_path.write_text("address,place,amount\nIlica 10,10000 Zagreb,25.00\n")
    conn = get_connection(tmp_path / "test.db")

    result = import_payers_csv(conn, csv_path)

    assert result.imported == 0
    assert "name" in result.errors[0]
