"""Moving between pages and remembering who is signed in.

Besides visitors there are two roles:

* Administrator: signed in with ADMIN_PASSWORD on the Admin page.
* Contributor: unlocked with the shared class code (CONTRIBUTOR_CODE) in the
  sidebar. Contributors see pending cases and can edit any case; editing a
  published case sends it back to the review queue.

Both roles survive a browser refresh through a token in the URL that is
derived from the secret, never the secret itself.
"""

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
QUERY_SESSION = "session"  # ?session=<token> keeps an admin signed in across a refresh
QUERY_CLASS = "class"      # ?class=<token> keeps a contributor unlocked across a refresh


# ---------------------------------------------------------------- tokens

def _token(secret: str | None, purpose: bytes) -> str | None:
    if not secret:
        return None
    return hmac.new(secret.encode("utf-8"), purpose, "sha256").hexdigest()[:32]


def _admin_token() -> str | None:
    return _token(config.get_admin_password(), b"digital-society-casebook-admin")


def _class_token() -> str | None:
    return _token(_normalize_code(config.get_contributor_code()), b"digital-society-casebook-class")


def _normalize_code(code: str | None) -> str:
    """Class codes are compared without spaces and regardless of case."""
    return "".join((code or "").split()).upper()


def _restore(flag: str, param: str, token: str | None) -> bool:
    """True when the role is active in this session or proven by the URL token.

    Switching pages drops the URL query, so an active role re-stamps its
    token on every run; a refresh on any page then keeps the role.
    """
    if st.session_state.get(flag):
        if token:
            st.query_params[param] = token  # every run, so the URL never loses it
        return True
    supplied = st.query_params.get(param)
    if token and supplied and hmac.compare_digest(supplied, token):
        st.session_state[flag] = True
        return True
    return False


# ---------------------------------------------------------------- admin

def is_admin() -> bool:
    return _restore("is_admin", QUERY_SESSION, _admin_token())


def try_login(password: str) -> bool:
    """Compare against the configured password without leaking timing information."""
    expected = config.get_admin_password()
    if not expected or not password:
        return False
    if hmac.compare_digest(password.encode("utf-8"), expected.encode("utf-8")):
        st.session_state["is_admin"] = True
        token = _admin_token()
        if token:
            st.query_params[QUERY_SESSION] = token
        return True
    return False


def logout() -> None:
    st.session_state["is_admin"] = False
    if QUERY_SESSION in st.query_params:
        del st.query_params[QUERY_SESSION]


# ---------------------------------------------------------------- contributor (class code)

def is_contributor() -> bool:
    """Unlocked with the class code. Administrators use is_admin instead."""
    return _restore("is_contributor", QUERY_CLASS, _class_token())


def can_edit() -> bool:
    return is_admin() or is_contributor()


def try_unlock(code: str) -> bool:
    expected = _normalize_code(config.get_contributor_code())
    given = _normalize_code(code)
    if not expected or not given:
        return False
    if hmac.compare_digest(given.encode("utf-8"), expected.encode("utf-8")):
        st.session_state["is_contributor"] = True
        token = _class_token()
        if token:
            st.query_params[QUERY_CLASS] = token
        return True
    return False


def lock() -> None:
    st.session_state["is_contributor"] = False
    if QUERY_CLASS in st.query_params:
        del st.query_params[QUERY_CLASS]


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


def _unlock_clicked() -> None:
    if not try_unlock(st.session_state.get("sidebar-class-code", "")):
        st.toast("That class code is not right.", icon="⛔")


def sidebar_footer(pending_count: int | None = None) -> None:
    """Small block under the navigation: who you are, and the class-code unlock.

    The buttons use callbacks, which run before the page is drawn, so the
    sidebar and the page both show the new role in the same run and URL
    token changes reach the browser.
    """
    with st.sidebar:
        st.markdown("")
        if is_admin():
            label = "Administrator"
            if pending_count:
                label += f" · {pending_count} pending"
            st.caption(label)
            st.button("Sign out", key="sidebar-logout", width="stretch", on_click=logout)
        elif is_contributor():
            st.caption("Contributor · editing unlocked")
            st.button("Lock", key="sidebar-lock", width="stretch", on_click=lock)
        else:
            st.caption("Visitor")
            if config.get_contributor_code():
                st.text_input("Class code", key="sidebar-class-code", placeholder="Class code", label_visibility="collapsed", on_change=_unlock_clicked)
                st.button("Unlock editing", key="sidebar-unlock", width="stretch", on_click=_unlock_clicked)
