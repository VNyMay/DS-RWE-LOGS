"""Moving between pages and remembering who is logged in as administrator."""

from __future__ import annotations

import hmac

import streamlit as st

import config

# File paths of the pages, used with st.switch_page.
PAGE_HOME = "screens/home.py"
PAGE_BROWSE = "screens/browse.py"
PAGE_SUBMIT = "screens/submit.py"
PAGE_ANALYTICS = "screens/analytics.py"
PAGE_ADMIN = "screens/admin.py"

QUERY_EXAMPLE = "example"  # ?example=<id> opens a detail page


# ---------------------------------------------------------------- admin session

def is_admin() -> bool:
    return bool(st.session_state.get("is_admin", False))


def try_login(password: str) -> bool:
    """Compare against the configured password without leaking timing information."""
    expected = config.get_admin_password()
    if not expected or not password:
        return False
    if hmac.compare_digest(password.encode("utf-8"), expected.encode("utf-8")):
        st.session_state["is_admin"] = True
        return True
    return False


def logout() -> None:
    st.session_state["is_admin"] = False


# ---------------------------------------------------------------- navigation helpers

def open_example(example_id: int) -> None:
    """Jump to the detail view of one example on the Browse page.

    The id travels through session state because switching pages clears the
    URL query; the Browse page then copies it into the URL so the link can
    be shared.
    """
    st.session_state["selected_example_id"] = int(example_id)
    st.switch_page(PAGE_BROWSE)


def go(page: str) -> None:
    """Switch page, dropping any example selection."""
    clear_selected_example()
    st.switch_page(page)


def selected_example_id() -> int | None:
    """The example to show: handed over by a button, or given in the URL."""
    pending = st.session_state.pop("selected_example_id", None)
    if pending is not None:
        st.query_params[QUERY_EXAMPLE] = str(pending)
        return int(pending)
    raw = st.query_params.get(QUERY_EXAMPLE)
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def clear_selected_example() -> None:
    st.session_state.pop("selected_example_id", None)
    if QUERY_EXAMPLE in st.query_params:
        del st.query_params[QUERY_EXAMPLE]


def sidebar_footer(pending_count: int | None = None) -> None:
    """Small block under the navigation: admin state and a one-line description."""
    with st.sidebar:
        st.markdown("")
        if is_admin():
            label = "Administrator"
            if pending_count:
                label += f" \u00b7 {pending_count} pending"
            st.caption(label)
            if st.button("Sign out", key="sidebar-logout", width="stretch"):
                logout()
                st.rerun()
        else:
            st.caption("Visitor")
