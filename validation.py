"""Validation rules for example submissions.

The functions here never talk to Streamlit or the database directly, so
they can be unit-tested and reused by the submission form and the admin
editor alike.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import urlparse

import config

# Values people type when they mean "nothing". These are stored as NULL.
PLACEHOLDER_VALUES = {
    "", "-", "--", "n/a", "na", "n.a.", "none", "null", "nil", "?",
    "not specified", "not applicable", "unknown", "tbd",
}


@dataclass
class ValidationResult:
    """Errors block saving; warnings are shown but do not block."""

    errors: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


# ---------------------------------------------------------------- helpers

def clean_text(value: object) -> str | None:
    """Trim a free-text value and turn placeholders like '-' or 'N/A' into None."""
    if value is None:
        return None
    text = str(value).strip()
    if text.lower() in PLACEHOLDER_VALUES:
        return None
    return text


def clean_choice(value: object) -> str | None:
    """Turn the 'Not specified' select-box option into None."""
    text = clean_text(value)
    if text is None or text == config.NOT_SPECIFIED:
        return None
    return text


def is_valid_url(url: str | None) -> bool:
    """True for an http(s) URL with a host that contains a dot."""
    if not url:
        return False
    try:
        parsed = urlparse(url.strip())
    except ValueError:
        return False
    if parsed.scheme not in ("http", "https"):
        return False
    host = parsed.netloc.split("@")[-1].split(":")[0]
    return "." in host and not host.startswith(".") and not host.endswith(".")


def parse_source_list(text: str | None) -> list[str]:
    """Split the 'additional sources' box into individual entries.

    Entries may be separated by new lines, commas or semicolons. Blank
    entries are dropped; the order is kept.
    """
    if not text:
        return []
    parts = re.split(r"[\n,;]+", str(text))
    return [part.strip() for part in parts if part.strip()]


def normalize_title(title: str) -> str:
    """Lower-case, strip punctuation and collapse spaces, for duplicate checks."""
    lowered = re.sub(r"[^a-z0-9 ]+", " ", (title or "").lower())
    return re.sub(r"\s+", " ", lowered).strip()


def parse_year(value: object) -> int | None:
    """Accept an int, a numeric string, or nothing."""
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------- main rule set

def validate_example(data: dict, similar_titles: list[str] | None = None) -> ValidationResult:
    """Check a submission dictionary and report problems.

    ``similar_titles`` lets the caller pass titles that already exist in the
    database; a close match becomes a warning, not an error.
    """
    result = ValidationResult()

    title = clean_text(data.get("title"))
    if not title:
        result.errors["title"] = "Please enter a title."
    elif len(title) < config.MIN_TITLE_LENGTH:
        result.errors["title"] = (
            f"Please enter a more descriptive title (at least {config.MIN_TITLE_LENGTH} characters)."
        )
    elif len(title) > config.MAX_TITLE_LENGTH:
        result.errors["title"] = f"Please shorten the title to {config.MAX_TITLE_LENGTH} characters or fewer."

    summary = clean_text(data.get("summary"))
    if not summary:
        result.errors["summary"] = "Please enter a short summary."
    elif len(summary) < config.MIN_SUMMARY_LENGTH:
        result.errors["summary"] = (
            "Please write a fuller summary: one or two sentences explaining what the case is about."
        )

    if not clean_text(data.get("technology")):
        result.errors["technology"] = "Please name the technology or digital system involved."

    category = clean_choice(data.get("category"))
    if not category:
        result.errors["category"] = "Please select a main category."
    elif category not in config.CATEGORIES:
        result.errors["category"] = "Please choose a category from the list."

    level = clean_choice(data.get("level"))
    if not level:
        result.errors["level"] = "Please choose whether this case is for SL or HL Digital Society."
    elif level not in config.LEVELS:
        result.errors["level"] = "Please choose SL or HL."

    description = clean_text(data.get("description"))
    if not description:
        result.errors["description"] = "Please describe what happened."
    elif len(description) < config.MIN_DESCRIPTION_LENGTH:
        result.errors["description"] = (
            f"Please provide a more detailed description (at least {config.MIN_DESCRIPTION_LENGTH} characters)."
        )

    source_url = clean_text(data.get("source_url"))
    if not source_url:
        result.errors["source_url"] = "Please provide a main source URL. Every case needs evidence."
    elif not is_valid_url(source_url):
        result.errors["source_url"] = "Please enter a valid URL beginning with https:// or http://."

    if not clean_text(data.get("submitted_by")):
        result.errors["submitted_by"] = "Please enter your name or nickname."

    year = data.get("year")
    if year not in (None, ""):
        parsed = parse_year(year)
        if parsed is None or not (config.YEAR_MIN <= parsed <= config.YEAR_MAX):
            result.errors["year"] = (
                f"Please enter a year between {config.YEAR_MIN} and {config.YEAR_MAX}, or leave it empty."
            )

    # Additional sources: every entry should look like a URL. Anything else is
    # a warning rather than an error so that a book or report citation can
    # still be recorded.
    extra_sources = parse_source_list(data.get("additional_sources"))
    non_urls = [source for source in extra_sources if not is_valid_url(source)]
    if non_urls:
        shown = "; ".join(non_urls[:3])
        result.warnings.append(
            f"Some additional sources are not web links ({shown}). "
            "That is fine for books or reports, but please double-check them."
        )

    if title and similar_titles:
        wanted = normalize_title(title)
        for existing in similar_titles:
            other = normalize_title(existing)
            if other == wanted or wanted in other or other in wanted:
                result.warnings.append(
                    f'This looks similar to an existing example ("{existing}"). '
                    "Please check whether it is a duplicate."
                )
                break

    return result


def can_be_approved(record: dict) -> tuple[bool, str]:
    """A record must have a valid main source before it can be approved."""
    if not is_valid_url(record.get("source_url")):
        return False, (
            "This record cannot be approved because its main source URL is missing or invalid. Edit it first."
        )
    return True, ""
