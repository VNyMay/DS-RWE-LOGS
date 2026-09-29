"""Submit: the structured form, validation, duplicate warnings and the confirmation screen."""

from __future__ import annotations

import streamlit as st

import config
import database
import ui
import validation
from components import cache, forms, messages, navigation

ui.page_header("Submit an example", "Reviewed before publishing. Type - to skip a required field.", kicker="Contribute")

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
    saved = database.get_example_by_id(new_id, include_unapproved=True) or {}
    st.session_state["last_submission"] = {
        "id": new_id,
        "title": validation.clean_text(data.get("title")),
        "submitted_by": validation.clean_text(data.get("submitted_by")),
        "level": validation.clean_choice(data.get("level")),
        "edit_code": saved.get("edit_code"),
    }
    cache.invalidate()
    st.session_state.pop("submit_pending_data", None)
    forms.reset_wizard(form_key)
    st.session_state["submit_form_version"] += 1
    st.rerun()


# ---------------------------------------------------------------- confirmation

last = st.session_state.get("last_submission")
if last:
    with st.container(border=True, key="section-submit-done"):
        ui.kicker("Submitted")
        st.html(
            f'<h2 class="dsc-section-title" style="font-size:24px">Thanks{", " + ui.esc(last["submitted_by"]) if last.get("submitted_by") else ""}.</h2>'
            f'<p class="dsc-subtitle">"{ui.esc(last["title"])}" is pending review and will appear once approved.</p>'
            f'<div style="margin-top:12px">{ui.status_badge_html("pending")}{ui.level_badge_html(last.get("level") or "SL")}</div>'
        )
        if last.get("edit_code"):
            st.html('<p class="dsc-kicker" style="margin-top:16px">Your edit code</p>')
            st.code(last["edit_code"], language=None)
            ui.note("Keep it. Enter it on this page to change the case while it is pending.")
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

# ---------------------------------------------------------------- edit a pending submission

flash = st.session_state.pop("submit_flash", None)
if flash:
    messages.success(flash)

edit_id = st.session_state.get("student_edit_id")
if edit_id is None:
    with st.expander("Already submitted? Edit it with your code"):
        c1, c2 = st.columns([3, 1])
        with c1:
            typed_code = st.text_input("Edit code", key="student_edit_code", placeholder="K7PQ-3XMZ", label_visibility="collapsed")
        with c2:
            load = st.button("Load", key="student_edit_load", width="stretch")
        if load:
            try:
                record = database.get_example_by_edit_code(typed_code)
            except database.DatabaseError as exc:
                messages.database_error(exc)
                record = None
            if record is None:
                messages.error("No submission matches that code.")
            elif record["status"] != "pending":
                messages.info("This case has already been reviewed. Ask the admin for changes.")
            else:
                st.session_state["student_edit_id"] = record["id"]
                st.rerun()
else:
    try:
        editing = database.get_example_by_id(edit_id, include_unapproved=True)
    except database.DatabaseError as exc:
        messages.database_error(exc)
        editing = None
    if editing is None or editing["status"] != "pending":
        st.session_state.pop("student_edit_id", None)
        messages.info("This case can no longer be edited.")
        st.stop()
    with st.container(border=True, key="section-student-edit"):
        ui.kicker("Editing")
        st.html(f'<h2 class="dsc-section-title" style="font-size:22px">{ui.esc(editing["title"])}</h2>')
        if st.button("Cancel", icon=":material/close:", type="tertiary", key="student_edit_cancel"):
            st.session_state.pop("student_edit_id", None)
            st.rerun()
    changes = forms.example_form(initial=editing, key=f"student-edit-{edit_id}", submit_label="Save changes", wizard=False)
    if changes is not None:
        try:
            similar = database.find_similar_titles(changes.get("title") or "", exclude_id=edit_id)
        except database.DatabaseError:
            similar = []
        result = validation.validate_example(changes, similar_titles=similar)
        if not result.ok:
            messages.validation_errors(result)
        else:
            try:
                database.update_example(edit_id, changes)
                cache.invalidate()
                st.session_state.pop("student_edit_id", None)
                st.session_state["submit_flash"] = f'Saved "{validation.clean_text(changes["title"])}". It stays pending until a moderator approves it.'
                st.rerun()
            except (database.DatabaseError, ValueError) as exc:
                messages.database_error(exc)
    st.stop()

# ---------------------------------------------------------------- form

data = forms.example_form(initial=None, key=form_key, submit_label="Submit for review", wizard=True)

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
    w1, w2, _ = st.columns([2, 2, 4])
    with w1:
        if st.button("Submit anyway", type="primary", icon=":material/send:", width="stretch"):
            _save(pending)
    with w2:
        if st.button("Go back and edit", width="stretch"):
            st.session_state.pop("submit_pending_data", None)
            st.session_state.pop("submit_pending_warnings", None)
            st.rerun()
