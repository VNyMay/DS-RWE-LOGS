"""Analytics: how the approved cases are distributed.

Chart rules (from the data-visualisation guidelines): one measure per chart,
a single hue for single-series bars, sorted bars with rounded ends, whole
number axes, a tooltip on every bar, a table view for every chart, and no
chart at all when there is nothing to show.
"""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

import config
import database
import ui
from components import messages, navigation

DARK = ui.theme_type() == "dark"
BAR_COLOR = "#00946e" if DARK else "#027554"
INK = "#8fa69b" if DARK else "#56695f"
GRID = "rgba(190,255,230,0.10)" if DARK else "rgba(0,82,63,0.12)"

ui.page_header(
    "Analytics",
    "How the approved cases are spread across categories, technologies, places, years, ethical issues and course levels.",
    kicker="Insights",
)

if not st.session_state.get("db_ready", True):
    messages.database_error()
    st.stop()

try:
    stats = database.get_statistics()
except database.DatabaseError as exc:
    messages.database_error(exc)
    st.stop()

# ---------------------------------------------------------------- headline numbers

ui.metric_row([
    ("Approved", stats["approved"], "Published cases"),
    ("Categories", stats["category_count"], "Distinct topics"),
    ("Technologies", stats["technology_count"], "Distinct systems"),
    ("Countries", stats["country_count"], "Distinct locations"),
])
st.markdown("")

if navigation.is_admin():
    ui.section_heading("Review pipeline", "Visible to administrators only.")
    ui.metric_row([
        ("Pending", stats["by_status"]["pending"], "Awaiting review"),
        ("Approved", stats["by_status"]["approved"], "Published"),
        ("Rejected", stats["by_status"]["rejected"], "Not published"),
        ("Archived", stats["by_status"]["archived"], "Hidden from visitors"),
    ])
    st.markdown("")

if stats["approved"] == 0:
    ui.empty_state(
        "Nothing to chart yet",
        "Charts appear once at least one example has been approved. Submit a case or approve a pending one.",
        icon="📊",
    )
    st.stop()


# ---------------------------------------------------------------- charts

def _bar_chart(frame: pd.DataFrame, label: str, horizontal: bool) -> alt.Chart:
    """A single-series bar chart styled to the casebook theme."""
    axis_common = dict(labelColor=INK, titleColor=INK, tickColor=GRID, domainColor=GRID, gridColor=GRID, labelFontSize=12, titleFontSize=12)
    count_axis = alt.Axis(tickMinStep=1, format="d", title="Examples", **axis_common)
    label_axis = alt.Axis(title=None, labelLimit=220, **axis_common)
    mark = alt.Chart(frame).mark_bar(color=BAR_COLOR, cornerRadiusEnd=4, size=18 if horizontal else 26)
    if horizontal:
        chart = mark.encode(
            y=alt.Y(f"{label}:N", sort=None, axis=label_axis),
            x=alt.X("Examples:Q", axis=count_axis),
            tooltip=[alt.Tooltip(f"{label}:N"), alt.Tooltip("Examples:Q", format="d")],
        )
    else:
        chart = mark.encode(
            x=alt.X(f"{label}:N", sort=None, axis=alt.Axis(title=None, labelAngle=0, **axis_common)),
            y=alt.Y("Examples:Q", axis=count_axis),
            tooltip=[alt.Tooltip(f"{label}:N"), alt.Tooltip("Examples:Q", format="d")],
        )
    return chart.configure_view(strokeWidth=0).configure(background="transparent")


def bar_block(title: str, subtitle: str, pairs: list[tuple], label: str, key: str, horizontal: bool = True, top: int | None = None) -> None:
    """One sorted single-series bar chart with an accompanying table view."""
    with st.container(border=True, key=f"section-analytics-{key}"):
        ui.section_heading(title, subtitle)
        if not pairs:
            ui.note("No data for this chart yet.")
            return
        shown = pairs[:top] if top else pairs
        frame = pd.DataFrame(shown, columns=[label, "Examples"])
        frame[label] = frame[label].astype(str)
        height = max(200, 30 * len(shown) + 50) if horizontal else 260
        st.altair_chart(_bar_chart(frame, label, horizontal).properties(height=height), width="stretch")
        if top and len(pairs) > top:
            ui.note(f"Top {top} of {len(pairs)} shown. The table below lists everything.")
        with st.expander("View as table"):
            st.dataframe(pd.DataFrame(pairs, columns=[label, "Examples"]), hide_index=True, width="stretch")


left, right = st.columns(2, gap="large")
with left:
    with st.container(border=True, key="section-analytics-level"):
        ui.section_heading("Course level", "Standard Level versus Higher Level cases.")
        sl, hl = stats["by_level"]["SL"], stats["by_level"]["HL"]
        c1, c2 = st.columns(2)
        with c1:
            st.html(ui.level_badge_html("SL") + f'<p class="dsc-metric-value">{sl}</p><p class="dsc-metric-hint">{config.LEVEL_LABELS["SL"]}</p>')
        with c2:
            st.html(ui.level_badge_html("HL") + f'<p class="dsc-metric-value">{hl}</p><p class="dsc-metric-hint">{config.LEVEL_LABELS["HL"]}</p>')
        total = sl + hl
        if total:
            st.html(
                '<div style="display:flex;height:10px;border-radius:999px;overflow:hidden;margin-top:6px;gap:2px">'
                f'<div style="flex:{sl};background:{BAR_COLOR}" title="SL"></div>'
                f'<div style="flex:{hl};background:#f1a001" title="HL"></div></div>'
                f'<p class="dsc-note" style="margin-top:8px">SL {round(100 * sl / total)}% · HL {round(100 * hl / total)}%</p>'
            )
with right:
    bar_block("Examples by year", "When the cases happened or became public.", stats["by_year"], "Year", "year", horizontal=False)

bar_block("Examples by category", "Which Digital Society topics the casebook covers.", stats["by_category"], "Category", "category")
bar_block("Examples by ethical issue", "Each case can raise several issues, so totals exceed the number of cases.", stats["by_ethical_issue"], "Ethical issue", "issue")

left, right = st.columns(2, gap="large")
with left:
    bar_block("Examples by technology", "The systems at the centre of each case.", stats["by_technology"], "Technology", "technology", top=10)
with right:
    bar_block("Examples by country", "Where the cases took place.", stats["by_country"], "Country", "country", top=10)
