import pytest

import database


def test_empty_database_statistics():
    stats = database.get_statistics()
    assert stats["total"] == 0
    assert stats["by_status"] == {"pending": 0, "approved": 0, "rejected": 0, "archived": 0}
    assert stats["by_category"] == []
    assert database.export_examples().empty


def test_initialize_is_idempotent():
    database.initialize_database()
    database.initialize_database()
    assert database.count_examples() == 0


def test_create_stores_pending_and_hides_from_visitors(example):
    new_id = database.create_example(example)
    assert database.get_example_by_id(new_id) is None  # visitors see approved only
    record = database.get_example_by_id(new_id, include_unapproved=True)
    assert record["status"] == "pending"
    assert record["submitted_by"] == "Radwan"
    assert record["ethical_issues"] == "Consent, Privacy"
    assert record["submission_date"] == record["updated_date"]


def test_optional_placeholders_are_stored_as_null(example):
    new_id = database.create_example({**example, "subcategory": "-", "organizations": "N/A", "conclusion": "   "})
    record = database.get_example_by_id(new_id, include_unapproved=True)
    assert record["subcategory"] is None
    assert record["organizations"] is None
    assert record["conclusion"] is None


def test_missing_required_field_raises(example):
    with pytest.raises(ValueError):
        database.create_example({**example, "title": ""})


def test_search_and_combined_filters(example):
    first = database.create_example(example, status="approved")
    database.create_example(
        {**example, "title": "Smart city sensors in Singapore", "country": "Singapore", "year": 2019,
         "category": "Surveillance", "level": "SL", "technology": "IoT sensors", "ethical_issues": ["Surveillance"]},
        status="approved",
    )
    database.create_example({**example, "title": "Pending drone case"})  # pending: never shown

    rows, total = database.find_examples()
    assert total == 2

    rows, total = database.find_examples(query="AIRPORTS")
    assert total == 1 and rows[0]["id"] == first

    rows, total = database.find_examples(category="Surveillance", country="lebanon", year_from=2020, year_to=2026, ethical_issue="Privacy", level="HL")
    assert total == 1 and rows[0]["id"] == first

    rows, total = database.find_examples(ethical_issue="Consent and more")
    assert total == 0

    rows, total = database.find_examples(query="singapore", sort="relevance")
    assert total == 1 and rows[0]["country"] == "Singapore"

    rows, total = database.find_examples(status=None)
    assert total == 3

    rows, total = database.find_examples(limit=1, offset=1)
    assert total == 2 and len(rows) == 1


def test_status_workflow_and_notes(example):
    new_id = database.create_example(example)
    database.approve_example(new_id, "Checked the source")
    assert database.get_example_by_id(new_id)["reviewer_notes"] == "Checked the source"
    database.archive_example(new_id)
    assert database.get_example_by_id(new_id) is None
    assert database.count_examples("archived") == 1
    database.restore_example(new_id)
    assert database.count_examples("pending") == 1
    database.reject_example(new_id, "Not a Digital Society case")
    assert database.count_examples("rejected") == 1
    with pytest.raises(ValueError):
        database.update_status(new_id, "published")


def test_update_and_delete(example):
    new_id = database.create_example(example, status="approved")
    database.update_example(new_id, {**example, "title": "Updated title", "year": None})
    record = database.get_example_by_id(new_id)
    assert record["title"] == "Updated title"
    assert record["year"] is None
    assert record["updated_date"] >= record["submission_date"]
    database.delete_example(new_id)
    assert database.get_example_by_id(new_id, include_unapproved=True) is None


def test_similar_titles(example):
    database.create_example(example, status="approved")
    assert database.find_similar_titles("facial recognition at international airports") == [example["title"]]
    assert database.find_similar_titles("Something else entirely") == []


def test_export_excludes_private_notes_unless_asked(example):
    new_id = database.create_example(example)
    database.approve_example(new_id, "private note")
    public = database.export_examples(status="approved")
    assert "reviewer_notes" not in public.columns
    assert len(public) == 1
    full = database.export_examples(status=None, include_private=True)
    assert full.loc[0, "reviewer_notes"] == "private note"


def test_demo_records_can_be_removed(example):
    database.create_example(example, status="approved", is_demo=True)
    database.create_example({**example, "title": "Real student case"}, status="approved")
    assert database.get_statistics()["demo_count"] == 1
    assert database.delete_demo_examples() == 1
    assert database.count_examples() == 1


def test_filter_options_only_use_approved(example):
    database.create_example(example, status="approved")
    database.create_example({**example, "country": "Hidden", "title": "Pending"})
    options = database.get_filter_options()
    assert options["country"] == ["Lebanon"]
    assert options["year_range"] == [2023, 2023]
