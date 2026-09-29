"""The structured example form, shared by the Submit page and the admin editor.

The form keeps its values across reruns, so a validation error never wipes
what the person typed.
"""

from __future__ import annotations

import streamlit as st

import config
import database
import ui

REQUIRED = ' <span class="dsc-required">*</span>'


def _label(text: str, required: bool = False) -> str:
    # Streamlit labels accept limited markdown; the asterisk is added as text.
    return f"{text} *" if required else text


def _section(title: str, subtitle: str, key: str):
    container = st.container(border=True, key=f"section-form-{key}")
    with container:
        ui.section_heading(title, subtitle)
    return container


def example_form(initial: dict | None = None, key: str = "submit", submit_label: str = "Submit example") -> dict | None:
    """Render the form. Returns the entered values when the submit button is pressed, else None."""
    values = dict(initial or {})
    issues_initial = database.split_list(values.get("ethical_issues"))
    issues_initial = [issue for issue in issues_initial if issue in config.ETHICAL_ISSUES]

    level_options = [config.NOT_SPECIFIED] + config.LEVELS
    level_index = level_options.index(values["level"]) if values.get("level") in config.LEVELS else 0
    category_options = [config.NOT_SPECIFIED] + config.CATEGORIES
    category_index = category_options.index(values["category"]) if values.get("category") in config.CATEGORIES else 0

    with st.form(key=f"form-{key}", border=False, clear_on_submit=False):
        # ---------------------------------------------------- 1. basics
        with _section("1. Basic information", "Identify the case so other people can find it.", f"{key}-basics"):
            title = st.text_input(
                _label("Title", True),
                value=values.get("title") or "",
                placeholder="Facial recognition at international airports",
                help="A specific, descriptive title. Name the technology and the setting.",
                max_chars=config.MAX_TITLE_LENGTH,
            )
            summary = st.text_area(
                _label("Short summary", True),
                value=values.get("summary") or "",
                placeholder="Briefly explain the technology, situation, and why this example matters.",
                help="One or two sentences. This appears on the example card.",
                height=90,
            )
            left, right = st.columns(2)
            with left:
                technology = st.text_input(
                    _label("Technology or digital system", True),
                    value=values.get("technology") or "",
                    placeholder="Facial recognition",
                    help="The system at the centre of the case: an app, an algorithm, a device, a platform.",
                )
                category = st.selectbox(
                    _label("Main category", True),
                    options=category_options,
                    index=category_index,
                    help="Choose the Digital Society topic that fits best. Use tags for extra themes.",
                )
                level = st.selectbox(
                    _label("Course level", True),
                    options=level_options,
                    index=level_index,
                    format_func=lambda option: option if option == config.NOT_SPECIFIED else f"{option} - {config.LEVEL_LABELS[option]}",
                    help="SL: " + config.LEVEL_HELP["SL"] + " HL: " + config.LEVEL_HELP["HL"],
                )
                subcategory = st.text_input(
                    "Subcategory",
                    value=values.get("subcategory") or "",
                    placeholder="Biometric identification",
                    help="Optional. A more specific theme inside the main category.",
                )
            with right:
                country = st.text_input(
                    "Country or location",
                    value=values.get("country") or "",
                    placeholder="Lebanon",
                    help="Where the case took place. Use 'Global' for worldwide cases.",
                )
                city = st.text_input(
                    "City or region",
                    value=values.get("city") or "",
                    placeholder="Beirut",
                    help="Optional.",
                )
                year = st.number_input(
                    "Year",
                    min_value=config.YEAR_MIN,
                    max_value=config.YEAR_MAX,
                    value=int(values["year"]) if values.get("year") else None,
                    step=1,
                    format="%d",
                    placeholder="2023",
                    help="Optional. The year the case happened or became public.",
                )

        # ---------------------------------------------------- 2. description
        with _section("2. Case description", "Tell the story: who used the technology, where, and what followed.", f"{key}-story"):
            description = st.text_area(
                _label("What happened?", True),
                value=values.get("description") or "",
                placeholder="Describe what happened, who was involved, where it happened, and how the digital system was used.",
                help=f"At least {config.MIN_DESCRIPTION_LENGTH} characters. Facts first, analysis later.",
                height=190,
            )
            left, right = st.columns(2)
            with left:
                organizations = st.text_input(
                    "Organizations involved",
                    value=values.get("organizations") or "",
                    placeholder="Airport authority, technology vendor, national police",
                    help="Companies, governments, schools or institutions.",
                )
                stakeholders = st.text_input(
                    "Stakeholders",
                    value=values.get("stakeholders") or "",
                    placeholder="Passengers, border officers, regulators, civil-liberties groups",
                    help="Everyone with an interest in the outcome.",
                )
            with right:
                affected_groups = st.text_input(
                    "Affected groups",
                    value=values.get("affected_groups") or "",
                    placeholder="Travellers, minority communities",
                    help="Who felt the effects most directly.",
                )
                ethical_issues = st.multiselect(
                    "Ethical issues (select all that apply)",
                    options=config.ETHICAL_ISSUES,
                    default=issues_initial,
                    help="Used for filtering and analytics. Explain them in the 'Ethical concerns' box below.",
                )

        # ---------------------------------------------------- 3. analysis
        with _section("3. Impacts and analysis", "Balanced entries score best: include benefits as well as harms. Leave a box empty if the information is genuinely unavailable.", f"{key}-analysis"):
            left, right = st.columns(2)
            with left:
                positive_impacts = st.text_area(
                    "Positive impacts",
                    value=values.get("positive_impacts") or "",
                    placeholder="Faster boarding, fewer identity errors, lower staffing costs...",
                    height=120,
                )
                ethical_concerns = st.text_area(
                    "Ethical concerns",
                    value=values.get("ethical_concerns") or "",
                    placeholder="Explain concerns related to privacy, fairness, autonomy, surveillance, bias, or responsibility.",
                    height=140,
                )
                security_issues = st.text_area(
                    "Security issues",
                    value=values.get("security_issues") or "",
                    placeholder="Data breaches, spoofing, misuse of stored templates...",
                    height=110,
                )
                legal_issues = st.text_area(
                    "Legal or regulatory issues",
                    value=values.get("legal_issues") or "",
                    placeholder="Data-protection law, court cases, government guidance...",
                    height=110,
                )
            with right:
                negative_impacts = st.text_area(
                    "Negative impacts",
                    value=values.get("negative_impacts") or "",
                    placeholder="False matches, discrimination, chilling effects on travel...",
                    height=120,
                )
                privacy_issues = st.text_area(
                    "Privacy issues",
                    value=values.get("privacy_issues") or "",
                    placeholder="What data was collected, who could see it, how long it was kept...",
                    height=140,
                )
                environmental_impact = st.text_area(
                    "Environmental impact",
                    value=values.get("environmental_impact") or "",
                    placeholder="Energy use, hardware waste, or 'no notable impact'...",
                    height=110,
                )
                conclusion = st.text_area(
                    "Conclusion or overall Digital Society analysis",
                    value=values.get("conclusion") or "",
                    placeholder="Weigh the benefits against the harms and say what this case shows about technology and society.",
                    height=110,
                )

        # ---------------------------------------------------- 4. sources
        with _section("4. Sources and contributor", "Every case needs evidence. Your name is shown publicly next to the example.", f"{key}-sources"):
            source_url = st.text_input(
                _label("Main source URL", True),
                value=values.get("source_url") or "",
                placeholder="https://example.com/article",
                help="A news article, report, court document or official page. Must start with https:// or http://.",
            )
            additional_sources = st.text_area(
                "Additional sources",
                value=values.get("additional_sources") or "",
                placeholder="One source per line: https://...\nhttps://...",
                help="Optional. One per line. Books or reports without a link are accepted too.",
                height=90,
            )
            left, right = st.columns(2)
            with left:
                submitted_by = st.text_input(
                    _label("Your name or nickname", True),
                    value=values.get("submitted_by") or "",
                    placeholder="Radwan",
                    help="Shown publicly as the contributor of this example.",
                )
            with right:
                tags = st.text_input(
                    "Tags",
                    value=values.get("tags") or "",
                    placeholder="biometrics, travel, border control",
                    help="Optional. Comma-separated keywords that help searching.",
                )

        st.html('<p class="dsc-note">Fields marked <span class="dsc-required">*</span> are required. Everything else is optional; leave it empty rather than typing "-".</p>')
        submitted = st.form_submit_button(submit_label, type="primary", icon=":material/send:", width="stretch")

    if not submitted:
        return None

    return {
        "title": title,
        "summary": summary,
        "technology": technology,
        "category": category,
        "subcategory": subcategory,
        "level": level,
        "country": country,
        "city": city,
        "year": year,
        "organizations": organizations,
        "stakeholders": stakeholders,
        "affected_groups": affected_groups,
        "ethical_issues": ethical_issues,
        "description": description,
        "positive_impacts": positive_impacts,
        "negative_impacts": negative_impacts,
        "ethical_concerns": ethical_concerns,
        "privacy_issues": privacy_issues,
        "security_issues": security_issues,
        "environmental_impact": environmental_impact,
        "legal_issues": legal_issues,
        "conclusion": conclusion,
        "source_url": source_url,
        "additional_sources": additional_sources,
        "submitted_by": submitted_by,
        "tags": tags,
    }
