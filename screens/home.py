"""Home: what the casebook is, headline numbers, recent cases, how it works."""

from __future__ import annotations

import streamlit as st

import config
import database
import ui
from components import cache, cards, messages, navigation

# ---------------------------------------------------------------- hero

st.html(
    '<div class="dsc-hero">'
    '<p class="dsc-kicker">IB Digital Society</p>'
    f'<h1 class="dsc-title">{ui.esc(config.APP_NAME)}</h1>'
    f'<p class="dsc-subtitle">{ui.esc(config.APP_SUBTITLE)}</p>'
    "</div>"
)
left, right, _ = st.columns([2, 2, 5])
with left:
    if st.button("Browse examples", type="primary", icon=":material/search:", width="stretch"):
        navigation.go(navigation.PAGE_BROWSE)
with right:
    if st.button("Submit an example", icon=":material/add_circle:", width="stretch"):
        navigation.go(navigation.PAGE_SUBMIT)

# ---------------------------------------------------------------- data

if not st.session_state.get("db_ready", True):
    messages.database_error()
    st.stop()

try:
    stats = cache.statistics()
    recent = cache.recent(6)
    latest_sl, _ = cache.find(level="SL", sort="updated", limit=3)
    latest_hl, _ = cache.find(level="HL", sort="updated", limit=3)
except database.DatabaseError as exc:
    messages.database_error(exc)
    st.stop()

st.markdown("")
metrics = [
    ("Approved examples", stats["approved"], "Visible to everyone"),
    ("Categories covered", stats["category_count"], f"of {len(config.CATEGORIES)} Digital Society topics"),
    ("Countries and locations", stats["country_count"], "Where the cases took place"),
    ("SL / HL cases", f'{stats["by_level"]["SL"]} / {stats["by_level"]["HL"]}', "Standard Level / Higher Level"),
]
if navigation.is_admin():
    metrics.append(("Pending review", stats["pending"], "Waiting for a moderator"))
ui.metric_row(metrics)

st.markdown("")

# ---------------------------------------------------------------- recent + categories

main, side = st.columns([8, 4], gap="large")

with main:
    ui.section_heading("Recently added")
    if recent:
        cards.example_grid(recent, columns=2, key_prefix="home", compact=True)
    else:
        ui.empty_state(
            "Your casebook is empty",
            "Submit the first sourced Digital Society example and it will appear here once approved.",
            icon="📚",
        )

with side:
    ui.section_heading("Categories")
    if stats["by_category"]:
        for category, count in stats["by_category"][:8]:
            if st.button(f"{category}  ·  {count}", key=f"home-cat-{category}", width="stretch"):
                st.session_state["browse_prefill"] = {"category": category}
                navigation.go(navigation.PAGE_BROWSE)
    else:
        ui.note("No categories yet.")

st.markdown("")

# ---------------------------------------------------------------- SL / HL sections

ui.section_heading("SL and HL")
sl_col, hl_col = st.columns(2, gap="large")

for column, level, examples in ((sl_col, "SL", latest_sl), (hl_col, "HL", latest_hl)):
    with column:
        with st.container(border=True, key=f"section-home-{level.lower()}"):
            st.html(
                ui.level_badge_html(level)
                + f'<p class="dsc-metric-value" style="font-size:26px;margin-top:10px">{stats["by_level"][level]} '
                f'<span class="dsc-note">approved case{"s" if stats["by_level"][level] != 1 else ""}</span></p>'
            )
            if examples:
                for example in examples:
                    st.html(
                        f'<p style="margin:6px 0 0;font-weight:600">{ui.esc(example["title"])}</p>'
                        f'<p class="dsc-note" style="margin:0 0 6px">{ui.esc(example.get("category"))}'
                        f'{" · " + ui.esc(example["country"]) if example.get("country") else ""}'
                        f'{" · " + ui.esc(example["year"]) if example.get("year") else ""}</p>'
                    )
            else:
                ui.note(f"No {level} cases yet.")
            if st.button(f"Browse {level} examples", key=f"home-level-{level}", icon=":material/arrow_forward:"):
                st.session_state["browse_prefill"] = {"level": level}
                navigation.go(navigation.PAGE_BROWSE)

st.markdown("")

# ---------------------------------------------------------------- how it works

ui.section_heading("How it works")
with st.container(border=True, key="section-home-how"):
    ui.steps([
        ("Find a real case", "News, reports, rulings, research."),
        ("Describe it", "What happened, impacts, issues."),
        ("Add a source and your name", "One source URL is required."),
        ("Review, then publish", "Approved cases become public."),
    ])
