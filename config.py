"""Application settings and controlled vocabularies.

Everything that is "a fixed choice" lives here so that the pages, the
validation and the database all agree. To add a category or an ethical
issue, edit the lists below; nothing else needs to change.
"""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path

# ---------------------------------------------------------------- branding

APP_NAME = "Digital Society Casebook"
APP_SUBTITLE = "A searchable repository of real-world technology cases, impacts, and ethical issues."
APP_ICON = "📚"

# ---------------------------------------------------------------- paths

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATABASE_PATH = DATA_DIR / "examples.db"
LOGO_PATH = BASE_DIR / "assets" / "logo.svg"

# ---------------------------------------------------------------- vocabularies

CATEGORIES: list[str] = [
    "Artificial intelligence",
    "Cybersecurity",
    "Privacy",
    "Surveillance",
    "Social media",
    "Automation",
    "Digital divide",
    "Digital identity",
    "Data ownership",
    "Intellectual property",
    "Misinformation",
    "Online safety",
    "Environmental impact",
    "E-commerce",
    "Education technology",
    "Healthcare technology",
    "Financial technology",
    "Other",
]

# Controlled list used by the "ethical issue" filter and the analytics page.
# The free-text "Ethical concerns" field is still where the explanation goes.
ETHICAL_ISSUES: list[str] = [
    "Privacy",
    "Surveillance",
    "Bias and discrimination",
    "Autonomy and manipulation",
    "Consent",
    "Transparency and accountability",
    "Security and safety",
    "Misinformation",
    "Digital inequality",
    "Wellbeing",
    "Freedom of expression",
    "Labour and employment",
    "Intellectual property",
    "Environmental harm",
    "Responsibility and liability",
]

# The IB Digital Society "3Cs": concepts, content and contexts.
CONCEPTS: list[str] = ["Change", "Expression", "Identity", "Power", "Space", "Systems", "Values and ethics"]
CONTENT_STRANDS: list[str] = ["Data", "Algorithms", "Computers", "Networks and the internet", "Media", "Artificial intelligence", "Robots and autonomous technologies"]

# HL extension: challenge topics. HL cases can also record an intervention.
HL_CHALLENGES: list[str] = ["Global well-being", "Governance and human rights", "Sustainable development"]
CONTEXTS: list[str] = ["Cultural", "Economic", "Environmental", "Health", "Human knowledge", "Political", "Social"]

# Typing this alone in a required text box skips it (title excepted).
SKIP_MARK = "-"

# IB Digital Society course level a case is intended for.
LEVELS: list[str] = ["SL", "HL"]
LEVEL_LABELS: dict[str, str] = {
    "SL": "Standard Level",
    "HL": "Higher Level",
}
LEVEL_HELP: dict[str, str] = {
    "SL": "Core Digital Society content shared by every student: concepts, content and contexts.",
    "HL": "Cases suited to the HL extension: global well-being challenges and interventions, studied in more depth.",
}

STATUSES: list[str] = ["pending", "approved", "rejected", "archived"]
DEFAULT_STATUS = "pending"

STATUS_LABELS: dict[str, str] = {
    "pending": "Pending review",
    "approved": "Approved",
    "rejected": "Rejected",
    "archived": "Archived",
}

# Shown in select boxes for optional choices.
NOT_SPECIFIED = "Not specified"

# ---------------------------------------------------------------- limits

YEAR_MIN = 1950
YEAR_MAX = date.today().year + 1

MIN_TITLE_LENGTH = 5
MIN_SUMMARY_LENGTH = 20
MIN_DESCRIPTION_LENGTH = 50
MAX_TITLE_LENGTH = 200

PAGE_SIZE = 12  # results per page on the Browse page


# ---------------------------------------------------------------- secrets

def _read_secret(name: str) -> str | None:
    """Return a setting from Streamlit secrets, then the environment, else None.

    Streamlit is imported lazily so this module also works in plain scripts
    (tests, seed_data.py) where Streamlit is not running.
    """
    try:
        import streamlit as st

        if name in st.secrets:
            value = st.secrets[name]
            if value:
                return str(value)
    except Exception:  # noqa: BLE001 - secrets file missing or Streamlit not running
        pass

    value = os.environ.get(name)
    return value if value else None


def get_admin_password() -> str | None:
    """The admin password, or None when nobody has configured one."""
    return _read_secret("ADMIN_PASSWORD")


def get_contributor_code() -> str | None:
    """The shared class code that unlocks editing, or None when not configured."""
    return _read_secret("CONTRIBUTOR_CODE")


def get_database_url() -> str | None:
    """A PostgreSQL connection string, or None to use the local SQLite file."""
    return _read_secret("DATABASE_URL")
