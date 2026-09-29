"""Point every test at a throw-away SQLite file."""

import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import config  # noqa: E402
import database  # noqa: E402


@pytest.fixture(autouse=True)
def temp_database(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATABASE_PATH", tmp_path / "test.db")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    database.initialize_database()
    yield


@pytest.fixture
def example() -> dict:
    return {
        "title": "Facial recognition at international airports",
        "summary": "Airports use face matching to board passengers, raising consent questions.",
        "technology": "Facial recognition",
        "category": "Surveillance",
        "level": "HL",
        "country": "Norway",
        "city": "Oslo",
        "year": 2023,
        "description": "Airports installed cameras at boarding gates that match passenger faces against passport photos.",
        "source_url": "https://example.com/article",
        "submitted_by": "Test Contributor",
        "ethical_issues": ["Privacy", "Consent"],
        "tags": "airport, biometrics",
    }
