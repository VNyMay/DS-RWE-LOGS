"""Example cards for lists and grids."""

from __future__ import annotations

import streamlit as st

import database
import ui
from components import navigation


def _location(example: dict) -> str:
    parts = [example.get("city"), example.get("country")]
    return ", ".join(part for part in parts if part)


def example_card(
    example: dict,
    key_prefix: str = "browse",
    show_status: bool = False,
    compact: bool = False,
) -> None:
    """One example as a card with badges, summary, metadata and a details button."""
    example_id = example["id"]
    with st.container(border=True, key=f"card-{key_prefix}-{example_id}"):
        pills = [(example.get("category") or "", "category"), (example.get("technology") or "", "tech")]
        parts = [ui.badge_html(text, kind) for text, kind in pills if text]
        if example.get("level"):
            parts.insert(0, ui.level_badge_html(example["level"]))
        if show_status and example.get("status"):
            parts.append(ui.status_badge_html(example["status"]))
        if example.get("is_demo"):
            parts.append(ui.badge_html("Demo record", "demo"))

        summary = example.get("summary") or ""
        meta: list[str] = []
        location = _location(example)
        if location:
            meta.append(f"<span>📍 <strong>{ui.esc(location)}</strong></span>")
        if example.get("year"):
            meta.append(f"<span>📅 <strong>{ui.esc(example['year'])}</strong></span>")
        source_count = 1 + len(database.split_list(example.get("additional_sources")))
        meta.append(f"<span>🔗 {source_count} source{'s' if source_count != 1 else ''}</span>")
        if example.get("submitted_by"):
            meta.append(f"<span>✍️ {ui.esc(example['submitted_by'])}</span>")

        st.html(
            f'<div>{"".join(parts)}</div>'
            f'<h3 class="dsc-card-title">{ui.esc(example.get("title"))}</h3>'
            f'<p class="dsc-card-summary">{ui.esc(summary)}</p>'
            f'<p class="dsc-meta">{"".join(meta)}</p>'
        )
        if not compact:
            if st.button("View details", key=f"open-{key_prefix}-{example_id}", type="secondary", icon=":material/arrow_forward:"):
                navigation.open_example(example_id)
        else:
            if st.button("Open", key=f"open-{key_prefix}-{example_id}", type="tertiary", icon=":material/arrow_forward:"):
                navigation.open_example(example_id)


def example_grid(examples: list[dict], columns: int = 2, key_prefix: str = "grid", show_status: bool = False, compact: bool = False) -> None:
    """Lay cards out in ``columns`` columns; Streamlit stacks them on small screens."""
    cols = st.columns(columns, gap="medium")
    for index, example in enumerate(examples):
        with cols[index % columns]:
            example_card(example, key_prefix=key_prefix, show_status=show_status, compact=compact)
