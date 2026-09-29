"""The full detail view of one example."""

from __future__ import annotations

import streamlit as st

import database
import ui


def render_example_detail(example: dict, is_admin: bool = False, key_prefix: str = "detail") -> None:
    """Show every part of an example. Empty optional sections are hidden."""
    k = f"-{key_prefix}-{example['id']}"  # keeps container keys unique when several details share a page
    pills = [ui.level_badge_html(example.get("level") or "SL"), ui.badge_html(example.get("category") or "", "category")]
    if example.get("subcategory"):
        pills.append(ui.badge_html(example["subcategory"], "muted"))
    pills.append(ui.badge_html(example.get("technology") or "", "tech"))
    if is_admin and example.get("status"):
        pills.append(ui.status_badge_html(example["status"]))
    if example.get("is_demo"):
        pills.append(ui.badge_html("Demo record", "demo"))

    st.html(
        f'<div>{"".join(pills)}</div>'
        f'<h1 class="dsc-title" style="margin-top:6px">{ui.esc(example.get("title"))}</h1>'
        f'<p class="dsc-subtitle" style="font-size:16px">{ui.esc(example.get("summary"))}</p>'
    )

    main, side = st.columns([7, 4], gap="large")

    with side:
        with st.container(border=True, key=f"section-detail-facts{k}"):
            ui.kicker("At a glance")
            location = ", ".join(part for part in [example.get("city"), example.get("country")] if part)
            ui.info_list([
                ("Location", location or None),
                ("Year", str(example["year"]) if example.get("year") else None),
                ("Organizations", example.get("organizations")),
                ("Stakeholders", example.get("stakeholders")),
                ("Affected groups", example.get("affected_groups")),
            ])
            issues = database.split_list(example.get("ethical_issues"))
            if issues:
                st.html(
                    '<p class="dsc-kicker" style="margin-top:14px">Ethical issues</p>'
                    + "".join(ui.badge_html(issue, "issue") for issue in issues)
                )
            tags = database.split_list(example.get("tags"))
            if tags:
                st.html(
                    '<p class="dsc-kicker" style="margin-top:10px">Tags</p>'
                    + "".join(ui.badge_html(tag, "muted") for tag in tags)
                )

        with st.container(border=True, key=f"section-detail-sources{k}"):
            ui.kicker("Sources")
            ui.source_list(example.get("source_url"), database.split_list(example.get("additional_sources")))
            ui.note("Sources open in a new tab. The casebook records them as submitted; check them yourself before citing.")

        with st.container(border=True, key=f"section-detail-submission{k}"):
            ui.kicker("Submission")
            ui.info_list([
                ("Contributed by", example.get("submitted_by")),
                ("Submitted", ui.format_date(example.get("submission_date"))),
                ("Last updated", ui.format_date(example.get("updated_date"))),
                ("Record id", f"#{example.get('id')}"),
            ])
            if is_admin and example.get("reviewer_notes"):
                st.html(
                    '<p class="dsc-kicker" style="margin-top:14px">Reviewer notes (private)</p>'
                    f'<p class="dsc-note" style="white-space:pre-wrap">{ui.esc(example["reviewer_notes"])}</p>'
                )

    with main:
        with st.container(border=True, key=f"section-detail-story{k}"):
            ui.detail_section("What happened?", example.get("description"), show_when_empty=True)

        impacts = [
            ("Positive impacts", example.get("positive_impacts")),
            ("Negative impacts", example.get("negative_impacts")),
        ]
        if any(body for _, body in impacts):
            with st.container(border=True, key=f"section-detail-impacts{k}"):
                ui.kicker("Impacts")
                for title, body in impacts:
                    ui.detail_section(title, body)

        issues = [
            ("Ethical concerns", example.get("ethical_concerns")),
            ("Privacy issues", example.get("privacy_issues")),
            ("Security issues", example.get("security_issues")),
            ("Environmental impact", example.get("environmental_impact")),
            ("Legal or regulatory issues", example.get("legal_issues")),
        ]
        if any(body for _, body in issues):
            with st.container(border=True, key=f"section-detail-issues{k}"):
                ui.kicker("Issues and implications")
                for title, body in issues:
                    ui.detail_section(title, body)

        if example.get("conclusion"):
            with st.container(border=True, key=f"section-detail-conclusion{k}"):
                ui.kicker("Digital Society analysis")
                ui.detail_section("Conclusion", example.get("conclusion"))

        missing = [title for title, body in impacts + issues if not body]
        if missing and not example.get("conclusion"):
            missing.append("Conclusion")
        if missing:
            ui.note("Not specified for this case: " + ", ".join(missing).lower() + ".")
