"""The example form, in two layouts that share the same fields.

* ``wizard=True`` (Submit page): three short steps with a progress bar, so
  adding a case never feels like a long questionnaire. Values are kept in
  session state while moving between steps.
* ``wizard=False`` (admin editor): every step on one page with one save button.

Required text boxes accept a single dash as "skip" (see validation.py).
"""

from __future__ import annotations

import streamlit as st

import config
import database
import ui

STEP_LABELS = ["The case", "Analysis", "Source and name"]


def _req(text: str) -> str:
    return f"{text} *"


def _list(values: dict, field: str, allowed: list[str]) -> list[str]:
    return [item for item in database.split_list(values.get(field)) if item in allowed]


def _index(options: list[str], value: object) -> int | None:
    return options.index(value) if value in options else None


# ---------------------------------------------------------------- step 1: the case

def _step_case(v: dict) -> dict:
    out: dict = {}
    out["title"] = st.text_input(_req("Title"), value=v.get("title") or "", placeholder="Facial recognition at international airports", max_chars=config.MAX_TITLE_LENGTH)
    out["summary"] = st.text_area(_req("Short summary"), value=v.get("summary") or "", placeholder="One or two sentences: the technology, the situation, why it matters.", height=80)

    left, right = st.columns(2)
    with left:
        out["level"] = st.segmented_control(
            _req("Course level"), options=config.LEVELS,
            default=v.get("level") if v.get("level") in config.LEVELS else None,
            format_func=lambda x: f"{x} · {config.LEVEL_LABELS[x]}", width="stretch",
        )
        out["category"] = st.selectbox(_req("Category"), options=config.CATEGORIES, index=_index(config.CATEGORIES, v.get("category")), placeholder="Choose a category")
        out["technology"] = st.text_input(_req("Technology"), value=v.get("technology") or "", placeholder="Facial recognition")
    with right:
        out["country"] = st.text_input("Country or location", value=v.get("country") or "", placeholder="United Kingdom")
        out["year"] = st.number_input("Year", min_value=config.YEAR_MIN, max_value=config.YEAR_MAX, value=int(v["year"]) if v.get("year") else None, step=1, format="%d", placeholder="2023")
        out["organizations"] = st.text_input("Organizations involved", value=v.get("organizations") or "", placeholder="Airport authority, technology vendor")
    return out


# ---------------------------------------------------------------- step 2: analysis

def _step_analysis(v: dict) -> dict:
    out: dict = {}
    out["description"] = st.text_area(_req("What happened?"), value=v.get("description") or "", placeholder="Who used the technology, where, how, and what followed.", height=150)

    ui.kicker("3Cs")
    c1, c2, c3 = st.columns(3)
    with c1:
        out["concepts"] = st.multiselect("Concepts", options=config.CONCEPTS, default=_list(v, "concepts", config.CONCEPTS), placeholder="Choose")
    with c2:
        out["content_strands"] = st.multiselect("Content", options=config.CONTENT_STRANDS, default=_list(v, "content_strands", config.CONTENT_STRANDS), placeholder="Choose")
    with c3:
        out["contexts"] = st.multiselect("Contexts", options=config.CONTEXTS, default=_list(v, "contexts", config.CONTEXTS), placeholder="Choose")

    left, right = st.columns(2)
    with left:
        out["ethical_issues"] = st.multiselect("Ethical issues", options=config.ETHICAL_ISSUES, default=_list(v, "ethical_issues", config.ETHICAL_ISSUES), placeholder="Choose")
    with right:
        out["affected_groups"] = st.text_input("Affected groups", value=v.get("affected_groups") or "", placeholder="Travellers, minority communities")

    if v.get("level") == "HL":
        ui.kicker("HL extension")
        h1, h2 = st.columns([1, 2])
        with h1:
            out["hl_challenge"] = st.selectbox("Challenge", options=config.HL_CHALLENGES, index=_index(config.HL_CHALLENGES, v.get("hl_challenge")), placeholder="Choose a challenge")
        with h2:
            out["intervention"] = st.text_area("Intervention", value=v.get("intervention") or "", placeholder="What was done about it, and did it work?", height=80)
    else:
        out["hl_challenge"] = None
        out["intervention"] = v.get("intervention") or ""

    with st.expander("More detail (optional)", expanded=bool(v.get("_expand_more"))):
        a, b = st.columns(2)
        with a:
            out["positive_impacts"] = st.text_area("Positive impacts", value=v.get("positive_impacts") or "", height=90)
            out["ethical_concerns"] = st.text_area("Ethical concerns", value=v.get("ethical_concerns") or "", placeholder="Privacy, fairness, autonomy, surveillance, bias, responsibility...", height=90)
            out["security_issues"] = st.text_area("Security issues", value=v.get("security_issues") or "", height=80)
            out["legal_issues"] = st.text_area("Legal or regulatory issues", value=v.get("legal_issues") or "", height=80)
            out["stakeholders"] = st.text_input("Stakeholders", value=v.get("stakeholders") or "", placeholder="Passengers, border officers, regulators")
            out["subcategory"] = st.text_input("Subcategory", value=v.get("subcategory") or "", placeholder="Biometric identification")
        with b:
            out["negative_impacts"] = st.text_area("Negative impacts", value=v.get("negative_impacts") or "", height=90)
            out["privacy_issues"] = st.text_area("Privacy issues", value=v.get("privacy_issues") or "", height=90)
            out["environmental_impact"] = st.text_area("Environmental impact", value=v.get("environmental_impact") or "", height=80)
            out["conclusion"] = st.text_area("Conclusion", value=v.get("conclusion") or "", placeholder="Weigh benefits against harms.", height=80)
            out["city"] = st.text_input("City or region", value=v.get("city") or "", placeholder="London")
            out["tags"] = st.text_input("Tags", value=v.get("tags") or "", placeholder="biometrics, travel")
    return out


# ---------------------------------------------------------------- step 3: source and name

def _step_sources(v: dict) -> dict:
    out: dict = {}
    out["source_url"] = st.text_input(_req("Main source URL"), value=v.get("source_url") or "", placeholder="https://example.com/article", help="Type - to skip. A moderator adds a source before approval.")
    out["additional_sources"] = st.text_area("More sources", value=v.get("additional_sources") or "", placeholder="One per line", height=70)
    out["submitted_by"] = st.text_input(_req("Your name or nickname"), value=v.get("submitted_by") or "", placeholder="Name or nickname", help="Shown next to the case. Type - to stay anonymous.")
    return out


STEPS = [_step_case, _step_analysis, _step_sources]


def _footnote() -> None:
    st.html('<p class="dsc-note"><span class="dsc-required">*</span> required. Type <strong>-</strong> in a required text box to skip it.</p>')


def _step_problems(step: int, values: dict) -> list[str]:
    """Light checks before moving on, so mistakes surface on the step they belong to."""
    problems: list[str] = []
    if step == 0:
        title = (values.get("title") or "").strip()
        if not title or title == config.SKIP_MARK:
            problems.append("Please enter a title.")
        if not values.get("level"):
            problems.append("Please choose SL or HL.")
        if not values.get("category"):
            problems.append("Please choose a category.")
    return problems


# ---------------------------------------------------------------- public entry point

def example_form(initial: dict | None = None, key: str = "submit", submit_label: str = "Submit example", wizard: bool = True) -> dict | None:
    """Render the form. Returns every field when the final button is pressed, else None."""
    if not wizard:
        return _full_form(initial or {}, key, submit_label)

    state_key = f"wiz-{key}"
    state = st.session_state.setdefault(state_key, {"step": 0, "draft": dict(initial or {})})
    step, draft = state["step"], state["draft"]
    last = len(STEPS) - 1

    ui.stepper(STEP_LABELS, step)
    problems = state.pop("problems", None)
    if problems:
        st.error("\n".join(f"- {text}" for text in problems), icon="⛔")

    with st.form(key=f"form-{key}-{step}", border=True):
        values = STEPS[step](draft)
        _footnote()
        back_col, next_col = st.columns([1, 3])
        with back_col:
            back = st.form_submit_button("Back", disabled=step == 0, width="stretch", icon=":material/arrow_back:")
        with next_col:
            forward = st.form_submit_button(
                submit_label if step == last else "Next",
                type="primary", width="stretch",
                icon=":material/send:" if step == last else ":material/arrow_forward:",
            )

    if back:
        draft.update(values)
        state["step"] = step - 1
        st.rerun()

    if forward:
        draft.update(values)
        if step < last:
            found = _step_problems(step, draft)
            if found:
                state["problems"] = found
            else:
                state["step"] = step + 1
            st.rerun()
        return dict(draft)
    return None


def _full_form(values: dict, key: str, submit_label: str) -> dict | None:
    merged: dict = dict(values)
    merged["_expand_more"] = True
    with st.form(key=f"form-{key}", border=False):
        for label, render in zip(STEP_LABELS, STEPS):
            with st.container(border=True, key=f"section-form-{key}-{label.replace(' ', '-')}"):
                ui.section_heading(label)
                merged.update(render(merged))
        _footnote()
        submitted = st.form_submit_button(submit_label, type="primary", icon=":material/save:", width="stretch")
    merged.pop("_expand_more", None)
    return merged if submitted else None


def reset_wizard(key: str) -> None:
    """Forget a wizard's draft (used after a successful submission)."""
    st.session_state.pop(f"wiz-{key}", None)
