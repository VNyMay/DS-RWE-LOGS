"""Submit: the structured form, validation, duplicate warnings and the confirmation screen."""

from __future__ import annotations

import streamlit as st

import config
import database
import ui
import validation
from components import forms, messages, navigation

ui.page_header(
    "Submit an example",
    "Add a real-world case about technology and society. Submissions are reviewed before they are published.",
    kicker="Contribute",
)

if not st.session_state.get("db_ready", True):
    messages.database_error()
    st.stop()

# A counter in the form key gives a fresh, empty form after a successful submission.
st.session_state.setdefault("submit_form_version", 0)
form_key = f"submit-{st.session_state['submit_form_version']}"


def _save(data: dict) -> None:
    """Store the submission as pending and switch to the confirmation screen."""
    try:
        new_id = database.create_example(data, status=config.DEFAULT_STATUS)
    except (database.DatabaseError, ValueError) as exc:
        messages.database_error(exc)
        return
    st.session_state["last_submission"] = {
        "id": new_id,
        "title": validation.clean_text(data.get("title")),
        "submitted_by": validation.clean_text(data.get("submitted_by")),
        "level": validation.clean_choice(data.get("level")),
    }
    st.session_state.pop("submit_pending_data", None)
    st.session_state["submit_form_version"] += 1
    st.rerun()


# ---------------------------------------------------------------- confirmation

last = st.session_state.get("last_submission")
if last:
    with st.container(border=True, key="section-submit-done"):
        ui.kicker("Submitted")
        st.html(
            f'<h2 class="dsc-section-title" style="font-size:24px">Thank you, {ui.esc(last["submitted_by"])}. Your example was submitted.</h2>'
            f'<p class="dsc-subtitle">"{ui.esc(last["title"])}" is now <strong>pending review</strong> '
            f'(record #{last["id"]}, {ui.esc(last.get("level") or "SL")}).</p>'
        )
        st.html(
            "<div>" + ui.status_badge_html("pending") + "</div>"
            '<ul class="dsc-info-list" style="margin-top:10px">'
            '<li><span class="k">Next step</span><span class="v">A moderator will check the case and its sources.</span></li>'
            '<li><span class="k">Visibility</span><span class="v">It will not appear publicly until it is approved.</span></li>'
            '<li><span class="k">Sources</span><span class="v">Keep your source information accurate. Cases without a working source cannot be approved.</span></li>'
            "</ul>"
        )
        st.markdown("")
        b1, b2, _ = st.columns([2, 2, 4])
        with b1:
            if st.button("Submit another example", type="primary", icon=":material/add_circle:", width="stretch"):
                st.session_state.pop("last_submission", None)
                st.rerun()
        with b2:
            if st.button("Browse examples", icon=":material/search:", width="stretch"):
                st.session_state.pop("last_submission", None)
                navigation.go(navigation.PAGE_BROWSE)
    st.stop()

# ---------------------------------------------------------------- guidance

with st.expander("What makes a strong Digital Society case?", expanded=False):
    st.markdown(
        """
- **Be specific.** Name the technology, the organisation using it, the place and the year.
- **Show both sides.** Record positive impacts as well as harms; balanced entries are more useful for analysis.
- **Separate facts from analysis.** Describe what happened first, then discuss ethics, privacy, security, environment and law.
- **Cite credible sources.** News organisations, official reports, court documents and peer-reviewed research. Wikipedia is a starting point, not a final source.
- **Leave unknowns empty.** If a detail is genuinely unavailable, leave the box blank rather than typing "-".
        """
    )

# ---------------------------------------------------------------- form

data = forms.example_form(initial=None, key=form_key, submit_label="Submit for review")

# A submission with only warnings (for example a possible duplicate) waits
# here for an explicit "submit anyway".
pending = st.session_state.get("submit_pending_data")

if data is not None:
    try:
        similar = database.find_similar_titles(data.get("title") or "")
    except database.DatabaseError:
        similar = []
    result = validation.validate_example(data, similar_titles=similar)

    if not result.ok:
        st.session_state.pop("submit_pending_data", None)
        messages.validation_errors(result)
    elif result.warnings:
        st.session_state["submit_pending_data"] = data
        st.session_state["submit_pending_warnings"] = result.warnings
        st.rerun()
    else:
        _save(data)

elif pending:
    for text in st.session_state.get("submit_pending_warnings", []):
        messages.warning(text)
    ui.note("Please check the warnings above. You can still submit if you are confident the example is new and the sources are correct.")
    w1, w2, _ = st.columns([2, 2, 4])
    with w1:
        if st.button("Submit anyway", type="primary", icon=":material/send:", width="stretch"):
            _save(pending)
    with w2:
        if st.button("Go back and edit", width="stretch"):
            st.session_state.pop("submit_pending_data", None)
            st.session_state.pop("submit_pending_warnings", None)
            st.rerun()
