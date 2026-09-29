"""Admin / Review: moderation queue, record management, editing and export."""

from __future__ import annotations

import streamlit as st

import config
import database
import ui
import validation
from components import cache, forms, messages, navigation
from components.detail import render_example_detail

ui.page_header("Admin / Review", kicker="Moderation")

if not st.session_state.get("db_ready", True):
    messages.database_error()
    st.stop()

# ---------------------------------------------------------------- sign in

if not navigation.is_admin():
    if config.get_admin_password() is None:
        with st.container(border=True, key="section-admin-setup"):
            ui.kicker("Setup required")
            st.markdown(
                "No admin password is configured, so the review area is locked.\n\n"
                "Create the file `.streamlit/secrets.toml` next to `app.py` (copy `secrets.toml.example`) and add:\n"
            )
            st.code('ADMIN_PASSWORD = "a-long-random-password"', language="toml")
            st.markdown(
                "On Streamlit Community Cloud, add the same line under **Settings -> Secrets**. "
                "Alternatively set an `ADMIN_PASSWORD` environment variable. Then restart the app."
            )
        st.stop()

    with st.container(border=True, key="section-admin-login"):
        ui.kicker("Moderators only")
        with st.form("admin-login", border=False):
            password = st.text_input("Admin password", type="password", autocomplete="current-password")
            if st.form_submit_button("Sign in", type="primary", icon=":material/login:"):
                if navigation.try_login(password):
                    st.rerun()
                messages.error("That password is not correct.")
    st.stop()

# ---------------------------------------------------------------- flash messages from the previous action

flash = st.session_state.pop("admin_flash", None)
if flash:
    kind, text = flash
    getattr(messages, kind, messages.info)(text)


def _flash(kind: str, text: str) -> None:
    st.session_state["admin_flash"] = (kind, text)


# ---------------------------------------------------------------- dialogs

@st.dialog("Delete this example?")
def confirm_delete(example: dict) -> None:
    st.markdown(f'**"{example["title"]}"** (record #{example["id"]}) will be permanently deleted. This cannot be undone.')
    st.markdown("If you only want to hide it from visitors, archive it instead.")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Delete permanently", type="primary", icon=":material/delete_forever:", width="stretch"):
            try:
                database.delete_example(example["id"])
                cache.invalidate()
                _flash("success", f'Deleted "{example["title"]}".')
            except database.DatabaseError as exc:
                _flash("error", f"Could not delete the record: {exc}")
            st.rerun()
    with c2:
        if st.button("Cancel", width="stretch"):
            st.rerun()


# ---------------------------------------------------------------- actions

def _approve(example: dict, notes: str) -> None:
    allowed, reason = validation.can_be_approved(example)
    if not allowed:
        _flash("error", reason)
        return
    database.approve_example(example["id"], notes if notes.strip() else None)
    cache.invalidate()
    _flash("success", f'Approved "{example["title"]}". It is now visible to everyone.')


def _reject(example: dict, notes: str) -> None:
    database.reject_example(example["id"], notes if notes.strip() else None)
    cache.invalidate()
    _flash("success", f'Rejected "{example["title"]}".')


def _archive(example: dict, notes: str) -> None:
    database.archive_example(example["id"], notes if notes.strip() else None)
    cache.invalidate()
    _flash("success", f'Archived "{example["title"]}". Visitors can no longer see it.')


def _restore(example: dict) -> None:
    database.restore_example(example["id"])
    cache.invalidate()
    _flash("success", f'"{example["title"]}" was sent back to the review queue.')


def _save_notes(example: dict, notes: str) -> None:
    database.set_reviewer_notes(example["id"], notes)
    cache.invalidate()
    _flash("success", "Reviewer notes saved.")


def record_row(example: dict, key_prefix: str) -> None:
    """One record in the queue or the full list, with its moderation controls."""
    example_id = example["id"]
    status = example["status"]
    with st.container(border=True, key=f"card-{key_prefix}-{example_id}"):
        pills = [
            ui.status_badge_html(status),
            ui.level_badge_html(example.get("level") or "SL"),
            ui.badge_html(example.get("category") or "", "category"),
        ]
        if example.get("technology"):
            pills.append(ui.badge_html(example["technology"], "tech"))
        if example.get("is_demo"):
            pills.append(ui.badge_html("Demo record", "demo"))
        meta = [
            f"<span>✍️ <strong>{ui.esc(example.get('submitted_by') or 'Anonymous')}</strong></span>",
            f"<span>🗓️ {ui.esc(ui.format_date(example.get('submission_date'), with_time=True))}</span>",
            f"<span>#{example_id}</span>",
        ]
        if not validation.is_valid_url(example.get("source_url")):
            meta.append("<span>No source – add one before approving</span>")
        st.html(
            f'<div>{"".join(pills)}</div>'
            f'<h3 class="dsc-card-title">{ui.esc(example.get("title"))}</h3>'
            f'<p class="dsc-card-summary">{ui.esc(example.get("summary"))}</p>'
            f'<p class="dsc-meta">{"".join(meta)}</p>'
        )

        with st.expander("Full details"):
            render_example_detail(example, is_admin=True, key_prefix=key_prefix)

        notes = st.text_input(
            "Reviewer notes (private)",
            value=example.get("reviewer_notes") or "",
            key=f"notes-{key_prefix}-{example_id}",
            placeholder="Why it was approved or rejected, what to fix, source quality...",
        )

        buttons = st.columns(6)
        actions: list[tuple[str, str, str, str]] = []  # label, icon, type, action name
        if status == "pending":
            actions += [("Approve", ":material/check_circle:", "primary", "approve"), ("Reject", ":material/cancel:", "secondary", "reject")]
        if status == "approved":
            actions += [("Archive", ":material/inventory_2:", "secondary", "archive")]
        if status in ("rejected", "archived"):
            actions += [("Send back to review", ":material/undo:", "secondary", "restore")]
        if status in ("rejected", "archived"):
            actions += [("Approve", ":material/check_circle:", "primary", "approve")]
        actions += [("Edit", ":material/edit:", "secondary", "edit"), ("Save notes", ":material/save:", "secondary", "save_notes"), ("Delete", ":material/delete:", "secondary", "delete")]

        for column, (label, icon, kind, action) in zip(buttons, actions):
            with column:
                if st.button(label, key=f"{action}-{key_prefix}-{example_id}", icon=icon, type=kind, width="stretch"):
                    try:
                        if action == "approve":
                            _approve(example, notes)
                        elif action == "reject":
                            _reject(example, notes)
                        elif action == "archive":
                            _archive(example, notes)
                        elif action == "restore":
                            _restore(example)
                        elif action == "save_notes":
                            _save_notes(example, notes)
                        elif action == "edit":
                            st.session_state["admin_edit_id"] = example_id
                        elif action == "delete":
                            confirm_delete(example)
                            return
                    except database.DatabaseError as exc:
                        _flash("error", f"The action failed: {exc}")
                    st.rerun()


# ---------------------------------------------------------------- editor (shown above the tabs when active)

edit_id = st.session_state.get("admin_edit_id")
if edit_id is not None:
    try:
        editing = database.get_example_by_id(edit_id, include_unapproved=True)
    except database.DatabaseError as exc:
        messages.database_error(exc)
        editing = None
    if editing is None:
        st.session_state.pop("admin_edit_id", None)
        messages.warning("That record no longer exists.")
    else:
        with st.container(border=True, key="section-admin-editor"):
            ui.kicker("Editing")
            st.html(
                f'<h2 class="dsc-section-title" style="font-size:22px">{ui.esc(editing["title"])}</h2>'
                f'<p class="dsc-note">Record #{editing["id"]} · {ui.esc(config.STATUS_LABELS[editing["status"]])} · '
                f'contributed by {ui.esc(editing.get("submitted_by"))}. Changes are saved without altering the status.</p>'
            )
            if st.button("Cancel editing", icon=":material/close:", type="tertiary"):
                st.session_state.pop("admin_edit_id", None)
                st.rerun()
        data = forms.example_form(initial=editing, key=f"edit-{edit_id}", submit_label="Save changes", wizard=False)
        if data is not None:
            try:
                similar = database.find_similar_titles(data.get("title") or "", exclude_id=edit_id)
            except database.DatabaseError:
                similar = []
            result = validation.validate_example(data, similar_titles=similar)
            if not result.ok:
                messages.validation_errors(result)
            else:
                for text in result.warnings:
                    messages.warning(text)
                try:
                    database.update_example(edit_id, data)
                    cache.invalidate()
                    st.session_state.pop("admin_edit_id", None)
                    _flash("success", f'Saved changes to "{validation.clean_text(data["title"])}".')
                    st.rerun()
                except (database.DatabaseError, ValueError) as exc:
                    messages.database_error(exc)
        st.markdown("---")

# ---------------------------------------------------------------- tabs

try:
    stats = cache.statistics()
    pending = database.get_pending_examples()
except database.DatabaseError as exc:
    messages.database_error(exc)
    st.stop()

ui.metric_row([
    ("Pending", stats["by_status"]["pending"], "Awaiting review"),
    ("Approved", stats["by_status"]["approved"], "Published"),
    ("Rejected", stats["by_status"]["rejected"], "Not published"),
    ("Archived", stats["by_status"]["archived"], "Hidden from visitors"),
])
st.markdown("")

VIEWS = ["pending", "all", "export"]
VIEW_LABELS = {"pending": f"Pending review ({len(pending)})", "all": "All records", "export": "Export"}
active_view = st.segmented_control(
    "View", VIEWS, key="admin_active_view", default="pending",
    format_func=lambda v: VIEW_LABELS[v], label_visibility="collapsed",
)
if active_view is None:  # a widget-level rerun can briefly clear the selection
    active_view = "pending"
st.markdown("")

if active_view == "pending":
    if not pending:
        ui.empty_state("Queue is empty", "No submissions waiting for review.", icon="✅")
    else:
        q = st.text_input("Search pending submissions", key="admin_queue_search", placeholder="Title, contributor, technology...", label_visibility="collapsed")
        shown = pending
        if q.strip():
            needle = q.strip().lower()
            shown = [
                item for item in pending
                if any(needle in str(item.get(field) or "").lower() for field in ("title", "summary", "technology", "category", "country", "submitted_by", "tags"))
            ]
        focus = st.session_state.pop("admin_focus_id", None)
        if focus is not None:
            shown = sorted(shown, key=lambda item: 0 if item["id"] == focus else 1)
        if not shown:
            ui.empty_state("No matches", "No pending submission matches that search.", icon="🔍")
        for item in shown:
            record_row(item, key_prefix="queue")

elif active_view == "all":
    f1, f2, f3 = st.columns([3, 2, 2])
    with f1:
        q_all = st.text_input("Search all records", key="admin_all_search", placeholder="Search every record...", label_visibility="collapsed")
    with f2:
        status_filter = st.selectbox("Status", ["All"] + config.STATUSES, key="admin_all_status", format_func=lambda s: s if s == "All" else config.STATUS_LABELS[s])
    with f3:
        sort_all = st.selectbox("Sort", ["Recently updated", "Newest", "Oldest", "Title"], key="admin_all_sort")
    sort_map = {"Recently updated": "updated", "Newest": "newest", "Oldest": "oldest", "Title": "title"}
    try:
        rows, total = database.find_examples(query=q_all, status=None if status_filter == "All" else status_filter, sort=sort_map[sort_all], limit=None)
    except database.DatabaseError as exc:
        messages.database_error(exc)
        rows, total = [], 0

    if not rows:
        ui.empty_state("No records", "Nothing matches this search and status.", icon="🗂️")
    else:
        ui.note(f"{total} record{'s' if total != 1 else ''}")
        with st.expander("Overview table"):
            import pandas as pd

            table = pd.DataFrame(rows)[["id", "status", "level", "title", "category", "technology", "country", "year", "submitted_by", "submission_date", "updated_date", "is_demo"]]
            st.dataframe(table, hide_index=True, width="stretch")
        for item in rows[:60]:
            record_row(item, key_prefix="all")
        if len(rows) > 60:
            ui.note("Showing the first 60 cards. Narrow the search to see the rest.")

elif active_view == "export":
    ui.section_heading("Export CSV")
    e1, e2 = st.columns(2, gap="large")
    with e1:
        with st.container(border=True, key="section-export-public"):
            ui.kicker("Public")
            st.markdown("Approved examples, no private fields.")
            try:
                public = database.export_examples(status="approved", include_private=False)
                st.download_button(
                    f"Download approved examples ({len(public)})",
                    data=public.to_csv(index=False).encode("utf-8-sig"),
                    file_name="digital-society-casebook-approved.csv",
                    mime="text/csv",
                    icon=":material/download:",
                    type="primary",
                    disabled=public.empty,
                )
            except database.DatabaseError as exc:
                messages.database_error(exc)
    with e2:
        with st.container(border=True, key="section-export-all"):
            ui.kicker("Full backup")
            st.markdown("Every record, every status.")
            include_private = st.checkbox("Include private reviewer notes", value=False)
            try:
                everything = database.export_examples(status=None, include_private=include_private)
                st.download_button(
                    f"Download all records ({len(everything)})",
                    data=everything.to_csv(index=False).encode("utf-8-sig"),
                    file_name="digital-society-casebook-all.csv",
                    mime="text/csv",
                    icon=":material/download:",
                    disabled=everything.empty,
                )
            except database.DatabaseError as exc:
                messages.database_error(exc)

    st.markdown("")
    with st.container(border=True, key="section-export-demo"):
        ui.kicker("Demonstration data")
        demo_total = sum(1 for _ in database.list_examples(status=None) if _.get("is_demo"))
        st.markdown(f"**{demo_total}** demo record{'s' if demo_total != 1 else ''} in the database.")
        if demo_total:
            confirm = st.checkbox("Permanently delete all demo records", key="confirm_demo_delete")
            if st.button("Delete demonstration records", icon=":material/delete_sweep:", disabled=not confirm):
                try:
                    removed = database.delete_demo_examples()
                    cache.invalidate()
                    _flash("success", f"Removed {removed} demonstration record{'s' if removed != 1 else ''}.")
                except database.DatabaseError as exc:
                    _flash("error", f"Could not delete the demonstration records: {exc}")
                st.rerun()
