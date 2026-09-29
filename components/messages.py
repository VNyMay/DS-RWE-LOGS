"""Friendly feedback: success, warnings, validation errors and database problems.

Technical details are logged; people only ever see plain sentences.
"""

from __future__ import annotations

import logging

import streamlit as st

from validation import ValidationResult

logger = logging.getLogger(__name__)

# Human labels for the form fields, used when listing validation errors.
FIELD_LABELS = {
    "title": "Title",
    "summary": "Short summary",
    "technology": "Technology",
    "category": "Main category",
    "description": "What happened?",
    "source_url": "Main source URL",
    "submitted_by": "Your name",
    "year": "Year",
}


def success(text: str) -> None:
    st.success(text, icon="✅")


def info(text: str) -> None:
    st.info(text, icon="ℹ️")


def warning(text: str) -> None:
    st.warning(text, icon="⚠️")


def error(text: str) -> None:
    st.error(text, icon="⛔")


def database_error(exc: Exception | None = None) -> None:
    """Shown wherever the casebook could not be read or written."""
    if exc is not None:
        logger.error("Database problem shown to user: %s", exc)
    st.error(
        "We could not load the casebook right now. Please check the database connection or try again.",
        icon="🗄️",
    )


def validation_errors(result: ValidationResult) -> None:
    """List every problem in one box so the person can fix them all at once."""
    if result.errors:
        lines = "\n".join(
            f"- **{FIELD_LABELS.get(field, field.replace('_', ' ').title())}:** {message}"
            for field, message in result.errors.items()
        )
        st.error("Please correct the highlighted fields before submitting.\n\n" + lines, icon="⛔")
    for text in result.warnings:
        st.warning(text, icon="⚠️")
