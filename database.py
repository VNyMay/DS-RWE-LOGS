"""Data access layer for the casebook.

Every SQL statement in the project lives in this module. Pages call the
functions below and receive plain dictionaries, so the interface never
depends on SQLite itself.

Two backends are understood:

* SQLite (default) - a file in ``data/examples.db``. Used for local work.
* PostgreSQL / Supabase - selected automatically when ``DATABASE_URL`` is
  set in Streamlit secrets or the environment. Needs ``psycopg`` installed.
  The SQL is written in the small dialect both databases share; the few
  differences (placeholders, auto-increment ids) are handled in one place.

All queries are parameterised. Never build SQL from user text.
"""

from __future__ import annotations

import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Iterator

import pandas as pd

import config
from validation import clean_choice, clean_text, normalize_title, parse_source_list, parse_year

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------- schema

# Column order matters: it is the order used for inserts and exports.
COLUMNS: list[str] = [
    "id",
    "title",
    "summary",
    "technology",
    "category",
    "subcategory",
    "level",
    "country",
    "city",
    "year",
    "organizations",
    "stakeholders",
    "affected_groups",
    "description",
    "positive_impacts",
    "negative_impacts",
    "ethical_concerns",
    "ethical_issues",
    "privacy_issues",
    "security_issues",
    "environmental_impact",
    "legal_issues",
    "conclusion",
    "source_url",
    "additional_sources",
    "tags",
    "submitted_by",
    "submission_date",
    "updated_date",
    "status",
    "reviewer_notes",
    "is_demo",
]

# Fields the user may edit. Everything else is managed by the application.
EDITABLE_FIELDS: list[str] = [
    "title", "summary", "technology", "category", "subcategory", "level", "country", "city", "year",
    "organizations", "stakeholders", "affected_groups", "description",
    "positive_impacts", "negative_impacts", "ethical_concerns", "ethical_issues",
    "privacy_issues", "security_issues", "environmental_impact", "legal_issues", "conclusion",
    "source_url", "additional_sources", "tags", "submitted_by",
]

REQUIRED_TEXT_FIELDS = ["title", "summary", "technology", "category", "level", "description", "source_url", "submitted_by"]

# Only these columns are private: they never leave the admin page.
PRIVATE_FIELDS = ["reviewer_notes"]

# Columns inspected by keyword search, with their weight for relevance sorting.
SEARCH_FIELDS: list[tuple[str, int]] = [
    ("title", 6),
    ("summary", 4),
    ("technology", 3),
    ("category", 3),
    ("tags", 3),
    ("country", 2),
    ("city", 1),
    ("organizations", 2),
    ("stakeholders", 1),
    ("affected_groups", 1),
    ("description", 1),
    ("ethical_concerns", 1),
    ("ethical_issues", 2),
    ("privacy_issues", 1),
    ("security_issues", 1),
]

_SCHEMA = """
CREATE TABLE IF NOT EXISTS examples (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    title                TEXT    NOT NULL,
    summary              TEXT    NOT NULL,
    technology           TEXT    NOT NULL,
    category             TEXT    NOT NULL,
    subcategory          TEXT,
    level                TEXT    NOT NULL DEFAULT 'SL',
    country              TEXT,
    city                 TEXT,
    year                 INTEGER,
    organizations        TEXT,
    stakeholders         TEXT,
    affected_groups      TEXT,
    description          TEXT    NOT NULL,
    positive_impacts     TEXT,
    negative_impacts     TEXT,
    ethical_concerns     TEXT,
    ethical_issues       TEXT,
    privacy_issues       TEXT,
    security_issues      TEXT,
    environmental_impact TEXT,
    legal_issues         TEXT,
    conclusion           TEXT,
    source_url           TEXT    NOT NULL,
    additional_sources   TEXT,
    tags                 TEXT,
    submitted_by         TEXT    NOT NULL,
    submission_date      TEXT    NOT NULL,
    updated_date         TEXT    NOT NULL,
    status               TEXT    NOT NULL DEFAULT 'pending',
    reviewer_notes       TEXT,
    is_demo              INTEGER NOT NULL DEFAULT 0
)
"""

_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_examples_status ON examples (status)",
    "CREATE INDEX IF NOT EXISTS idx_examples_category ON examples (category)",
    "CREATE INDEX IF NOT EXISTS idx_examples_country ON examples (country)",
    "CREATE INDEX IF NOT EXISTS idx_examples_year ON examples (year)",
    "CREATE INDEX IF NOT EXISTS idx_examples_level ON examples (level)",
]

# Columns added after the first release, with the SQL used to add them to an
# existing database. Order matters if one depends on another.
_MIGRATIONS: list[tuple[str, str]] = [
    ("level", "ALTER TABLE examples ADD COLUMN level TEXT NOT NULL DEFAULT 'SL'"),
]


class DatabaseError(Exception):
    """Raised when the casebook cannot be read or written."""


# ---------------------------------------------------------------- connections

def _backend() -> str:
    url = config.get_database_url()
    return "postgres" if url and url.startswith(("postgres://", "postgresql://")) else "sqlite"


def _sql(statement: str) -> str:
    """Translate the '?' placeholders used in this file for the active backend."""
    if _backend() == "postgres":
        return statement.replace("?", "%s")
    return statement


def get_connection():
    """Open a new connection. Callers should use the ``cursor()`` helper instead."""
    if _backend() == "postgres":
        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError as exc:  # pragma: no cover - only when misconfigured
            raise DatabaseError("DATABASE_URL is set but the 'psycopg' package is not installed.") from exc
        return psycopg.connect(config.get_database_url(), row_factory=dict_row)

    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(config.DATABASE_PATH), timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


@contextmanager
def cursor(commit: bool = False) -> Iterator[Any]:
    """Yield a cursor, commit on success, and always close the connection."""
    try:
        connection = get_connection()
    except Exception as exc:  # noqa: BLE001 - surface every connection problem the same way
        logger.exception("Could not open the database")
        raise DatabaseError(str(exc)) from exc
    try:
        cur = connection.cursor()
        yield cur
        if commit:
            connection.commit()
    except DatabaseError:
        connection.rollback()
        raise
    except ValueError:
        connection.rollback()
        raise
    except Exception as exc:  # noqa: BLE001 - sqlite3.Error, psycopg errors, ...
        connection.rollback()
        logger.exception("Database operation failed")
        raise DatabaseError(str(exc)) from exc
    finally:
        connection.close()


def _row_to_dict(row: Any) -> dict:
    if row is None:
        return {}
    if isinstance(row, dict):
        return dict(row)
    return {key: row[key] for key in row.keys()}


def now_iso() -> str:
    """Current UTC time as 'YYYY-MM-DDTHH:MM:SS' (no microseconds)."""
    return datetime.now(timezone.utc).replace(microsecond=0, tzinfo=None).isoformat()


# ---------------------------------------------------------------- setup

def initialize_database() -> None:
    """Create the table and indexes if they do not exist. Safe to call repeatedly."""
    schema = _SCHEMA
    if _backend() == "postgres":
        schema = schema.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
    with cursor(commit=True) as cur:
        cur.execute(schema)
        existing = _existing_columns(cur)
        for column, statement in _MIGRATIONS:
            if column not in existing:
                cur.execute(statement)
        for statement in _INDEXES:
            cur.execute(statement)


def _existing_columns(cur: Any) -> set[str]:
    """Column names of the examples table, on either backend."""
    if _backend() == "postgres":
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'examples'")
        return {_row_to_dict(row)["column_name"] for row in cur.fetchall()}
    cur.execute("PRAGMA table_info(examples)")
    return {_row_to_dict(row)["name"] for row in cur.fetchall()}


# ---------------------------------------------------------------- cleaning

def _prepare(data: dict) -> dict:
    """Normalise a submission dictionary before it touches the database.

    Optional text becomes NULL when empty or a placeholder such as '-'.
    Lists (ethical issues, tags) are stored as comma-separated text.
    """
    prepared: dict[str, Any] = {}
    for field in EDITABLE_FIELDS:
        value = data.get(field)
        if field == "year":
            prepared[field] = parse_year(value)
        elif field in ("ethical_issues", "tags"):
            if isinstance(value, (list, tuple, set)):
                items = [clean_text(item) for item in value]
            else:
                items = [clean_text(item) for item in parse_source_list(value)]
            prepared[field] = ", ".join(sorted({item for item in items if item})) or None
        elif field in ("category", "subcategory", "level"):
            prepared[field] = clean_choice(value)
        elif field == "additional_sources":
            prepared[field] = "\n".join(parse_source_list(value)) or None
        else:
            prepared[field] = clean_text(value)
    return prepared


def split_list(value: str | None) -> list[str]:
    """Turn a stored comma/newline separated string back into a list."""
    return parse_source_list(value)


# ---------------------------------------------------------------- create

def create_example(data: dict, status: str = config.DEFAULT_STATUS, is_demo: bool = False) -> int:
    """Insert a new example and return its id."""
    if status not in config.STATUSES:
        raise ValueError(f"Unknown status: {status}")
    record = _prepare(data)
    for field in REQUIRED_TEXT_FIELDS:
        if not record.get(field):
            raise ValueError(f"Missing required field: {field}")

    stamp = now_iso()
    record.update({
        "submission_date": stamp,
        "updated_date": stamp,
        "status": status,
        "reviewer_notes": None,
        "is_demo": 1 if is_demo else 0,
    })
    columns = [column for column in COLUMNS if column != "id"]
    placeholders = ", ".join("?" for _ in columns)
    statement = f"INSERT INTO examples ({', '.join(columns)}) VALUES ({placeholders})"
    values = [record.get(column) for column in columns]

    with cursor(commit=True) as cur:
        if _backend() == "postgres":
            cur.execute(_sql(statement + " RETURNING id"), values)
            return int(_row_to_dict(cur.fetchone())["id"])
        cur.execute(statement, values)
        return int(cur.lastrowid)


add_example = create_example  # alias, same function


# ---------------------------------------------------------------- read

def get_example_by_id(example_id: int, include_unapproved: bool = False) -> dict | None:
    """Fetch one record. Visitors only ever see approved records."""
    statement = "SELECT * FROM examples WHERE id = ?"
    params: list[Any] = [example_id]
    if not include_unapproved:
        statement += " AND status = ?"
        params.append("approved")
    with cursor() as cur:
        cur.execute(_sql(statement), params)
        row = cur.fetchone()
    return _row_to_dict(row) or None


_ORDER_BY = {
    "newest": "submission_date DESC, id DESC",
    "oldest": "submission_date ASC, id ASC",
    "title": "LOWER(title) ASC",
    "updated": "updated_date DESC, id DESC",
    "year": "year DESC, submission_date DESC",
}


def list_examples(status: str | None = "approved", sort: str = "newest", limit: int | None = None) -> list[dict]:
    """Simple listing, optionally restricted to one status (None = every status)."""
    statement = "SELECT * FROM examples"
    params: list[Any] = []
    if status:
        statement += " WHERE status = ?"
        params.append(status)
    statement += " ORDER BY " + _ORDER_BY.get(sort, _ORDER_BY["newest"])
    if limit:
        statement += " LIMIT ?"
        params.append(int(limit))
    with cursor() as cur:
        cur.execute(_sql(statement), params)
        return [_row_to_dict(row) for row in cur.fetchall()]


get_examples = list_examples


def get_approved_examples(limit: int | None = None) -> list[dict]:
    return list_examples(status="approved", limit=limit)


def get_pending_examples() -> list[dict]:
    return list_examples(status="pending", sort="oldest")


def get_recent_examples(limit: int = 6) -> list[dict]:
    return list_examples(status="approved", sort="updated", limit=limit)


def find_examples(
    query: str = "",
    category: str | None = None,
    technology: str | None = None,
    country: str | None = None,
    year_from: int | None = None,
    year_to: int | None = None,
    ethical_issue: str | None = None,
    level: str | None = None,
    status: str | None = "approved",
    sort: str = "newest",
    limit: int | None = None,
    offset: int = 0,
) -> tuple[list[dict], int]:
    """Keyword search plus independent filters.

    Returns ``(rows, total)`` where ``total`` is the number of matches before
    ``limit``/``offset`` are applied, for pagination. ``status=None`` means
    every status (admin use only).
    """
    where: list[str] = []
    params: list[Any] = []

    if status:
        where.append("status = ?")
        params.append(status)
    if category:
        where.append("category = ?")
        params.append(category)
    if level:
        where.append("level = ?")
        params.append(level)
    if technology:
        where.append("LOWER(technology) = LOWER(?)")
        params.append(technology)
    if country:
        where.append("LOWER(country) = LOWER(?)")
        params.append(country)
    if year_from is not None:
        where.append("year >= ?")
        params.append(int(year_from))
    if year_to is not None:
        where.append("year <= ?")
        params.append(int(year_to))
    if ethical_issue:
        # ethical_issues is stored as "A, B, C"; wrap in commas so "Privacy"
        # cannot match "Privacy and consent".
        where.append("(',' || REPLACE(COALESCE(ethical_issues, ''), ', ', ',') || ',') LIKE ?")
        params.append(f"%,{ethical_issue},%")

    query = (query or "").strip()
    if query:
        like = f"%{query.lower()}%"
        clauses = [f"LOWER(COALESCE({column}, '')) LIKE ?" for column, _ in SEARCH_FIELDS]
        where.append("(" + " OR ".join(clauses) + ")")
        params.extend([like] * len(clauses))

    where_sql = (" WHERE " + " AND ".join(where)) if where else ""

    with cursor() as cur:
        cur.execute(_sql("SELECT COUNT(*) AS n FROM examples" + where_sql), params)
        total = int(_row_to_dict(cur.fetchone())["n"])

        if sort == "relevance" and query:
            # Relevance is computed in Python on the full match set: the
            # casebook is small and this keeps the SQL portable.
            cur.execute(_sql("SELECT * FROM examples" + where_sql), params)
            rows = [_row_to_dict(row) for row in cur.fetchall()]
            rows.sort(key=lambda row: (-_relevance(row, query), row.get("submission_date") or ""))
            if limit:
                rows = rows[offset: offset + limit]
            return rows, total

        order = _ORDER_BY.get("newest" if sort == "relevance" else sort, _ORDER_BY["newest"])
        statement = "SELECT * FROM examples" + where_sql + " ORDER BY " + order
        page_params = list(params)
        if limit:
            statement += " LIMIT ? OFFSET ?"
            page_params.extend([int(limit), int(offset)])
        cur.execute(_sql(statement), page_params)
        return [_row_to_dict(row) for row in cur.fetchall()], total


search_examples = find_examples


def _relevance(row: dict, query: str) -> int:
    """Weighted count of keyword hits across the searchable fields."""
    needle = query.lower()
    score = 0
    for column, weight in SEARCH_FIELDS:
        text = str(row.get(column) or "").lower()
        if needle in text:
            score += weight * text.count(needle)
            if column == "title" and text.startswith(needle):
                score += weight
    return score


def get_filter_options(status: str | None = "approved") -> dict[str, list]:
    """Distinct values used to populate the Browse filters."""
    where = " WHERE status = ?" if status else ""
    params = [status] if status else []
    options: dict[str, list] = {}
    with cursor() as cur:
        for column in ("category", "technology", "country"):
            cur.execute(_sql(f"SELECT DISTINCT {column} AS v FROM examples{where} ORDER BY LOWER({column})"), params)
            options[column] = [r["v"] for r in (_row_to_dict(x) for x in cur.fetchall()) if r["v"]]
        cur.execute(_sql(f"SELECT MIN(year) AS lo, MAX(year) AS hi FROM examples{where}"), params)
        span = _row_to_dict(cur.fetchone())
        options["year_range"] = [span.get("lo"), span.get("hi")]
    return options


def find_similar_titles(title: str, exclude_id: int | None = None) -> list[str]:
    """Titles that share the normalised form of ``title`` (for duplicate warnings)."""
    wanted = normalize_title(title or "")
    if len(wanted) < 4:
        return []
    with cursor() as cur:
        cur.execute("SELECT id, title FROM examples WHERE status != 'rejected'")
        rows = [_row_to_dict(row) for row in cur.fetchall()]
    matches = []
    for row in rows:
        if exclude_id is not None and row["id"] == exclude_id:
            continue
        existing = normalize_title(row["title"])
        if existing == wanted or wanted in existing or existing in wanted:
            matches.append(row["title"])
    return matches


# ---------------------------------------------------------------- update

def update_example(example_id: int, data: dict) -> None:
    """Replace the editable fields of a record and bump ``updated_date``."""
    record = _prepare(data)
    for field in REQUIRED_TEXT_FIELDS:
        if not record.get(field):
            raise ValueError(f"Missing required field: {field}")
    assignments = ", ".join(f"{field} = ?" for field in EDITABLE_FIELDS)
    values = [record[field] for field in EDITABLE_FIELDS]
    values.extend([now_iso(), example_id])
    with cursor(commit=True) as cur:
        cur.execute(_sql(f"UPDATE examples SET {assignments}, updated_date = ? WHERE id = ?"), values)


def update_status(example_id: int, status: str, reviewer_notes: str | None = None) -> None:
    """Change a record's status. Reviewer notes are replaced when provided."""
    if status not in config.STATUSES:
        raise ValueError(f"Unknown status: {status}")
    with cursor(commit=True) as cur:
        if reviewer_notes is None:
            cur.execute(
                _sql("UPDATE examples SET status = ?, updated_date = ? WHERE id = ?"),
                [status, now_iso(), example_id],
            )
        else:
            cur.execute(
                _sql("UPDATE examples SET status = ?, reviewer_notes = ?, updated_date = ? WHERE id = ?"),
                [status, clean_text(reviewer_notes), now_iso(), example_id],
            )


def approve_example(example_id: int, reviewer_notes: str | None = None) -> None:
    update_status(example_id, "approved", reviewer_notes)


def reject_example(example_id: int, reviewer_notes: str | None = None) -> None:
    update_status(example_id, "rejected", reviewer_notes)


def archive_example(example_id: int, reviewer_notes: str | None = None) -> None:
    update_status(example_id, "archived", reviewer_notes)


def restore_example(example_id: int) -> None:
    """Send a rejected or archived record back to the review queue."""
    update_status(example_id, "pending")


def set_reviewer_notes(example_id: int, reviewer_notes: str | None) -> None:
    with cursor(commit=True) as cur:
        cur.execute(
            _sql("UPDATE examples SET reviewer_notes = ?, updated_date = ? WHERE id = ?"),
            [clean_text(reviewer_notes), now_iso(), example_id],
        )


# ---------------------------------------------------------------- delete

def delete_example(example_id: int) -> None:
    with cursor(commit=True) as cur:
        cur.execute(_sql("DELETE FROM examples WHERE id = ?"), [example_id])


def delete_demo_examples() -> int:
    """Remove every demonstration record. Returns how many were deleted."""
    with cursor(commit=True) as cur:
        cur.execute("SELECT COUNT(*) AS n FROM examples WHERE is_demo = 1")
        count = int(_row_to_dict(cur.fetchone())["n"])
        cur.execute("DELETE FROM examples WHERE is_demo = 1")
    return count


# ---------------------------------------------------------------- statistics

def count_examples(status: str | None = None) -> int:
    statement = "SELECT COUNT(*) AS n FROM examples"
    params: list[Any] = []
    if status:
        statement += " WHERE status = ?"
        params.append(status)
    with cursor() as cur:
        cur.execute(_sql(statement), params)
        return int(_row_to_dict(cur.fetchone())["n"])


def _count_by(cur: Any, column: str, status: str = "approved") -> list[tuple[Any, int]]:
    cur.execute(
        _sql(
            f"SELECT {column} AS k, COUNT(*) AS n FROM examples "
            f"WHERE status = ? AND {column} IS NOT NULL AND {column} != '' "
            f"GROUP BY {column} ORDER BY n DESC, LOWER({column}) ASC"
        ),
        [status],
    )
    return [(row["k"], int(row["n"])) for row in (_row_to_dict(x) for x in cur.fetchall())]


def get_statistics() -> dict:
    """Everything the Home and Analytics pages need, in one round trip."""
    stats: dict[str, Any] = {}
    with cursor() as cur:
        cur.execute("SELECT status, COUNT(*) AS n FROM examples GROUP BY status")
        by_status = {row["status"]: int(row["n"]) for row in (_row_to_dict(x) for x in cur.fetchall())}
        stats["by_status"] = {status: by_status.get(status, 0) for status in config.STATUSES}
        stats["total"] = sum(by_status.values())
        stats["approved"] = stats["by_status"]["approved"]
        stats["pending"] = stats["by_status"]["pending"]

        stats["by_level"] = {level: 0 for level in config.LEVELS}
        for level, count in _count_by(cur, "level"):
            stats["by_level"][level] = count
        stats["by_category"] = _count_by(cur, "category")
        stats["by_technology"] = _count_by(cur, "technology")
        stats["by_country"] = _count_by(cur, "country")
        stats["by_year"] = sorted(_count_by(cur, "year"), key=lambda pair: pair[0])

        cur.execute("SELECT ethical_issues FROM examples WHERE status = 'approved'")
        issue_counts: dict[str, int] = {}
        for row in (_row_to_dict(x) for x in cur.fetchall()):
            for issue in split_list(row.get("ethical_issues")):
                issue_counts[issue] = issue_counts.get(issue, 0) + 1
        stats["by_ethical_issue"] = sorted(issue_counts.items(), key=lambda pair: (-pair[1], pair[0]))

        cur.execute("SELECT COUNT(*) AS n FROM examples WHERE status = 'approved' AND is_demo = 1")
        stats["demo_count"] = int(_row_to_dict(cur.fetchone())["n"])

    stats["category_count"] = len(stats["by_category"])
    stats["country_count"] = len(stats["by_country"])
    stats["technology_count"] = len(stats["by_technology"])
    return stats


# ---------------------------------------------------------------- export

def export_examples(status: str | None = "approved", include_private: bool = False) -> pd.DataFrame:
    """Records as a DataFrame ready for CSV download.

    Reviewer notes are dropped unless ``include_private`` is True, so public
    exports never leak moderation comments.
    """
    rows = list_examples(status=status, sort="newest")
    frame = pd.DataFrame(rows, columns=COLUMNS)
    if not include_private:
        frame = frame.drop(columns=[column for column in PRIVATE_FIELDS if column in frame.columns])
    frame["is_demo"] = frame["is_demo"].fillna(0).astype(int).astype(bool)
    return frame
