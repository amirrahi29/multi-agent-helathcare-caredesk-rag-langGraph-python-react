"""Patient lookup by email (Postgres). Used by API auth gate."""

from __future__ import annotations

import os
from typing import Any

import psycopg2
from dotenv import load_dotenv

load_dotenv()

_DB = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("USER_NAME"),
    "password": os.getenv("PASSWORD"),
    "host": os.getenv("HOST_NAME"),
    "port": os.getenv("PORT", "5432"),
}


def normalize_email(email: str | None) -> str:
    return (email or "").strip().lower()


def fetch_patient_by_email(email: str) -> dict[str, Any] | None:
    """Return patient row dict or None if not found / invalid email."""
    norm = normalize_email(email)
    if not norm or "@" not in norm:
        return None
    conn = psycopg2.connect(**_DB)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT patient_id, name, email, city
            FROM patients
            WHERE lower(trim(email)) = %s
            LIMIT 1
            """,
            (norm,),
        )
        row = cur.fetchone()
        cur.close()
        if not row:
            return None
        return {
            "patient_id": row[0],
            "name": row[1],
            "email": row[2],
            "city": row[3],
        }
    finally:
        conn.close()
