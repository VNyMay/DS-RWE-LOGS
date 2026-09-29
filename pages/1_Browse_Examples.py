"""Browse: keyword search, independent filters, sorting, pagination and the detail view."""

from __future__ import annotations

import math

import streamlit as st

import config
import database
import ui
from components import cards, messages, navigation
from components.detail import render_example_detail

ANY = "All"
SORT_OPTIONS = {
    "Newest first": "newest",
    "Oldest first": "oldest",
    "Title A to Z": "title",
    "Most relevant": "relevance",
    "Year, latest first": "year",
}

if not st.session_state.get("db_ready", True):
    ui.page_header("Browse examples", kicker="Explore")
    messages.database_error()
    st.stop()

is_admin = navigation.is_admin()

# ---------------------------------------------------------------- detail view

example_id = navigation.selected_example_id()
if example_id is not None:
    try:
        example = database.get_example_by_id(example_id, include_unapproved=is_admin)
    except database.DatabaseError as exc:
        messages.database_error(exc)
        st.stop()

    if st.button("Back to all examples", icon=":material/arrow_back:", type="tertiary"):
        navigation.clear_selected_example()
        st.rerun()

    if example is None:
        ui.empty_state(
            "Example not available",
            "It may still be under review or was removed.",
            icon="🔎",
        )
        st.stop()

    render_example_detail(example, is_admin=is_admin)

    if is_admin:
        st.markdown("")
        if st.button("Open in Admin / Review", icon=":material/admin_panel_settings:"):
            st.session_state["admin_focus_id"] = example["id"]
            navigation.go(navigation.PAGE_ADMIN)
    st.stop()

# ---------------------------------------------------------------- list view

ui.page_header("Browse examples", kicker="Explore")

# Filters arriving from other pages (Home category buttons, SL/HL buttons).
prefill = st.session_state.pop("browse_prefill", None)
if prefill:
    st.session_state["browse_category"] = prefill.get("category", ANY)
    st.session_state["browse_level"] = prefill.get("level", ANY)
    st.session_state["browse_page"] = 1

try:
    options = database.get_filter_options(status=None if is_admin else "approved")
except database.DatabaseError as exc:
    messages.database_error(exc)
    st.stop()

with st.container(border=True, key="section-browse-filters"):
    top_left, top_right = st.columns([5, 2])
    with top_left:
        query = st.text_input(
            "Search",
            key="browse_query",
            placeholder="Search titles, summaries, technologies, countries, issues, tags...",
            label_visibility="collapsed",
        )
    with top_right:
        level_choice = st.segmented_control(
            "Course level",
            options=[ANY] + config.LEVELS,
            key="browse_level",
            default=ANY,
            label_visibility="collapsed",
            width="stretch",
        )

    f1, f2, f3, f4 = st.columns(4)
    with f1:
        category = st.selectbox("Category", [ANY] + config.CATEGORIES, key="browse_category")
    with f2:
        technology = st.selectbox("Technology", [ANY] + options["technology"], key="browse_technology")
    with f3:
        country = st.selectbox("Country or location", [ANY] + options["country"], key="browse_country")
    with f4:
        ethical_issue = st.selectbox("Ethical issue", [ANY] + config.ETHICAL_ISSUES, key="browse_issue")

    g1, g2, g3 = st.columns([3, 2, 2])
    lo, hi = options["year_range"]
    year_from = year_to = None
    with g1:
        if lo is not None and hi is not None:
            if lo == hi:
                lo, hi = lo - 1, hi
            year_span = st.slider("Year", min_value=int(lo), max_value=int(hi), value=(int(lo), int(hi)), key="browse_years")
            if year_span != (int(lo), int(hi)):
                year_from, year_to = year_span
        else:
            st.slider("Year", min_value=config.YEAR_MIN, max_value=config.YEAR_MAX, value=(config.YEAR_MIN, config.YEAR_MAX), disabled=True, help="Available once examples with a year exist.")
    with g2:
        sort_label = st.selectbox("Sort by", list(SORT_OPTIONS), key="browse_sort")
    with g3:
        if is_admin:
            status_choice = st.selectbox("Status (admin)", [ANY] + config.STATUSES, key="browse_status", format_func=lambda s: s if s == ANY else config.STATUS_LABELS[s])
        else:
            status_choice = "approved"
            st.selectbox("Status", ["Approved"], disabled=True)

    active = [
        label for label, value in (
            ("search", query.strip()), ("level", level_choice != ANY and level_choice), ("category", category != ANY),
            ("technology", technology != ANY), ("country", country != ANY), ("ethical issue", ethical_issue != ANY),
            ("year", year_from is not None),
        ) if value
    ]
    c1, c2 = st.columns([6, 1])
    with c1:
        ui.note("Filters: " + ", ".join(active) if active else "Showing all examples.")
    with c2:
        if st.button("Clear", key="browse_clear", disabled=not active, width="stretch"):
            for key in ("browse_query", "browse_level", "browse_category", "browse_technology", "browse_country", "browse_issue", "browse_years", "browse_sort", "browse_status"):
                st.session_state.pop(key, None)
            st.session_state["browse_page"] = 1
            st.rerun()

# ---------------------------------------------------------------- results

sort = SORT_OPTIONS[sort_label]
if sort == "relevance" and not query.strip():
    sort = "newest"

page = int(st.session_state.get("browse_page", 1))
filter_signature = (query, level_choice, category, technology, country, ethical_issue, year_from, year_to, sort_label, status_choice)
if st.session_state.get("browse_signature") != filter_signature:
    st.session_state["browse_signature"] = filter_signature
    page = 1
    st.session_state["browse_page"] = 1

try:
    results, total = database.find_examples(
        query=query,
        category=None if category == ANY else category,
        technology=None if technology == ANY else technology,
        country=None if country == ANY else country,
        year_from=year_from,
        year_to=year_to,
        ethical_issue=None if ethical_issue == ANY else ethical_issue,
        level=None if level_choice in (ANY, None) else level_choice,
        status=None if status_choice == ANY else status_choice,
        sort=sort,
        limit=config.PAGE_SIZE,
        offset=(page - 1) * config.PAGE_SIZE,
    )
except database.DatabaseError as exc:
    messages.database_error(exc)
    st.stop()

pages_total = max(1, math.ceil(total / config.PAGE_SIZE))
if page > pages_total:
    page = pages_total
    st.session_state["browse_page"] = page

st.markdown("")
if total == 0:
    if active:
        ui.empty_state(
            "No examples match these filters",
            "Try removing a filter or searching for a broader keyword.",
            icon="🔍",
        )
    else:
        ui.empty_state(
            "No examples yet",
            "Submit the first sourced example.",
            icon="📚",
        )
        if st.button("Submit an example", type="primary", icon=":material/add_circle:"):
            navigation.go(navigation.PAGE_SUBMIT)
else:
    first = (page - 1) * config.PAGE_SIZE + 1
    last = min(total, page * config.PAGE_SIZE)
    ui.section_heading(f"{total} example{'s' if total != 1 else ''}", f"{first}-{last} of {total}" if pages_total > 1 else None)
    cards.example_grid(results, columns=2, key_prefix="browse", show_status=is_admin)

    if pages_total > 1:
        st.markdown("")
        p1, p2, p3 = st.columns([1, 2, 1])
        with p1:
            if st.button("Previous", disabled=page <= 1, icon=":material/chevron_left:", width="stretch"):
                st.session_state["browse_page"] = page - 1
                st.rerun()
        with p2:
            st.html(f'<p class="dsc-note" style="text-align:center;margin-top:10px">Page {page} of {pages_total}</p>')
        with p3:
            if st.button("Next", disabled=page >= pages_total, icon=":material/chevron_right:", icon_position="right", width="stretch"):
                st.session_state["browse_page"] = page + 1
                st.rerun()
