"""SQLite storage for the recipient profile and the list of payers."""
import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "payments.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS recipient_profile (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    name TEXT NOT NULL DEFAULT '',
    address TEXT NOT NULL DEFAULT '',
    place TEXT NOT NULL DEFAULT '',
    iban TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS payers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    name TEXT NOT NULL,
    address TEXT NOT NULL,
    place TEXT NOT NULL,
    amount REAL NOT NULL,
    model TEXT NOT NULL DEFAULT 'HR00',
    reference TEXT NOT NULL DEFAULT '',
    purpose_code TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT ''
);
"""


def get_connection(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


# --- Recipient profile (single row) -----------------------------------------

def get_recipient_profile(conn: sqlite3.Connection) -> sqlite3.Row:
    conn.execute("INSERT OR IGNORE INTO recipient_profile (id) VALUES (1)")
    conn.commit()
    return conn.execute("SELECT * FROM recipient_profile WHERE id = 1").fetchone()


def save_recipient_profile(
    conn: sqlite3.Connection,
    name: str,
    address: str,
    place: str,
    iban: str,
) -> None:
    conn.execute(
        """
        INSERT INTO recipient_profile (id, name, address, place, iban)
        VALUES (1, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            name = excluded.name,
            address = excluded.address,
            place = excluded.place,
            iban = excluded.iban
        """,
        (name, address, place, iban),
    )
    conn.commit()


# --- Payers ------------------------------------------------------------------

def list_payers(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM payers ORDER BY id").fetchall()


def get_payer(conn: sqlite3.Connection, payer_id: int) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM payers WHERE id = ?", (payer_id,)).fetchone()


def insert_payer(
    conn: sqlite3.Connection,
    name: str,
    address: str,
    place: str,
    amount: float,
    model: str,
    reference: str,
    purpose_code: str,
    description: str,
) -> int:
    cursor = conn.execute(
        """
        INSERT INTO payers (name, address, place, amount, model, reference, purpose_code, description)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (name, address, place, amount, model, reference, purpose_code, description),
    )
    conn.commit()
    return cursor.lastrowid


def update_payer(
    conn: sqlite3.Connection,
    payer_id: int,
    name: str,
    address: str,
    place: str,
    amount: float,
    model: str,
    reference: str,
    purpose_code: str,
    description: str,
) -> None:
    conn.execute(
        """
        UPDATE payers
        SET name = ?, address = ?, place = ?, amount = ?, model = ?, reference = ?,
            purpose_code = ?, description = ?
        WHERE id = ?
        """,
        (name, address, place, amount, model, reference, purpose_code, description, payer_id),
    )
    conn.commit()


def delete_payer(conn: sqlite3.Connection, payer_id: int) -> None:
    conn.execute("DELETE FROM payers WHERE id = ?", (payer_id,))
    conn.commit()
