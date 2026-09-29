import validation


def test_required_fields_reported_with_friendly_messages():
    result = validation.validate_example({})
    assert not result.ok
    for field in ("title", "summary", "technology", "category", "level", "description", "source_url", "submitted_by"):
        assert field in result.errors
    assert result.errors["title"] == "Please enter a title."


def test_valid_example_passes(example):
    assert validation.validate_example(example).ok


def test_url_must_be_http_or_https(example):
    for bad in ("example.com", "ftp://example.com/x", "https://nodots", "htp://x.com"):
        result = validation.validate_example({**example, "source_url": bad})
        assert "source_url" in result.errors, bad
    assert validation.is_valid_url("http://example.org/page?x=1")


def test_year_range(example):
    assert "year" in validation.validate_example({**example, "year": 1800}).errors
    assert validation.validate_example({**example, "year": None}).ok
    assert validation.validate_example({**example, "year": ""}).ok


def test_short_description_rejected(example):
    result = validation.validate_example({**example, "description": "Too short."})
    assert "description" in result.errors


def test_level_must_be_sl_or_hl(example):
    assert "level" in validation.validate_example({**example, "level": "Not specified"}).errors
    assert "level" in validation.validate_example({**example, "level": "XL"}).errors


def test_duplicate_title_is_a_warning_not_an_error(example):
    result = validation.validate_example(example, similar_titles=["Facial Recognition at International Airports!"])
    assert result.ok
    assert any("similar to an existing example" in text for text in result.warnings)


def test_placeholders_become_none():
    for value in ("", "-", "N/A", "none", "  ", "Not specified"):
        assert validation.clean_text(value) is None, value
    assert validation.clean_text("  real value ") == "real value"


def test_source_list_parsing():
    assert validation.parse_source_list("https://a.com/1\nhttps://b.com/2, https://c.com/3;") == [
        "https://a.com/1", "https://b.com/2", "https://c.com/3",
    ]
    assert validation.parse_source_list(None) == []
