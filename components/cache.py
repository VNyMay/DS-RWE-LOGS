"""Cached reads for the pages.

Streamlit re-runs a page on every click, so the same small queries would
otherwise hit SQLite dozens of times per visit. Results are kept for a few
seconds and thrown away after any write, so pages never show stale data
for longer than a moment.
"""

from __future__ import annotations

import streamlit as st

import database

TTL_SECONDS = 20


@st.cache_data(ttl=TTL_SECONDS, show_spinner=False)
def statistics() -> dict:
    return database.get_statistics()


@st.cache_data(ttl=TTL_SECONDS, show_spinner=False)
def filter_options(status: str | None) -> dict:
    return database.get_filter_options(status=status)


@st.cache_data(ttl=TTL_SECONDS, show_spinner=False)
def find(**kwargs) -> tuple[list[dict], int]:
    return database.find_examples(**kwargs)


@st.cache_data(ttl=TTL_SECONDS, show_spinner=False)
def recent(limit: int) -> list[dict]:
    return database.get_recent_examples(limit=limit)


@st.cache_data(ttl=TTL_SECONDS, show_spinner=False)
def pending_count() -> int:
    return database.count_examples("pending")


def invalidate() -> None:
    """Forget every cached read. Call after any insert, update or delete."""
    for cached in (statistics, filter_options, find, recent, pending_count):
        cached.clear()
