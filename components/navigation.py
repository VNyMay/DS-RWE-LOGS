"""Moving between pages and remembering who is logged in as administrator."""

from __future__ import annotations

import hmac

import streamlit as st

import config

# File paths of the pages, used with st.switch_page.
PAGE_HOME = "pages/0_Home.py"
PAGE_BROWSE = "pages/1_Browse_Examples.py"
PAGE_SUBMIT = "pages/2_Submit_Example.py"
PAGE_ANALYTICS = "pages/3_Analytics.py"
PAGE_ADMIN = "pages/4_Admin.py"

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
    """Jump to the detail view of one example on the Browse page."""
    st.query_params[QUERY_EXAMPLE] = str(example_id)
    st.switch_page(PAGE_BROWSE)


def go(page: str) -> None:
    """Switch page, dropping any example selection."""
    if QUERY_EXAMPLE in st.query_params:
        del st.query_params[QUERY_EXAMPLE]
    st.switch_page(page)


def selected_example_id() -> int | None:
    """The example id in the URL, if any and if it is a number."""
    raw = st.query_params.get(QUERY_EXAMPLE)
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def clear_selected_example() -> None:
    if QUERY_EXAMPLE in st.query_params:
        del st.query_params[QUERY_EXAMPLE]


def sidebar_footer(pending_count: int | None = None) -> None:
    """Small block under the navigation: admin state and a one-line description."""
    with st.sidebar:
        st.markdown("")
        if is_admin():
            label = "Signed in as administrator"
            if pending_count:
                label += f" · {pending_count} pending"
            st.caption(label)
            if st.button("Sign out", key="sidebar-logout", width="stretch"):
                logout()
                st.rerun()
        else:
            st.caption("Browsing as a visitor. Moderators sign in on the Admin page.")
        st.caption(config.APP_SUBTITLE)
