"""Digital Society Casebook - application entry point.

Run with:  streamlit run app.py

This file sets up the page, the theme, the database and the navigation.
Each screen lives in the ``screens`` folder (not ``pages``, so Streamlit's
folder-based routing stays off and only st.navigation is used).
"""

from __future__ import annotations

import logging

import streamlit as st

import config
import database
import ui
from components import navigation

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

st.set_page_config(
    page_title=config.APP_NAME,
    page_icon=config.APP_ICON,
    layout="wide",
    initial_sidebar_state="auto",
    menu_items={
        "About": f"**{config.APP_NAME}**\n\n{config.APP_SUBTITLE}\n\nBuilt for IB Digital Society.",
        "Report a bug": None,
        "Get help": None,
    },
)

logo = config.BASE_DIR / "assets" / "logo.svg"
st.logo(str(logo), icon_image=str(config.BASE_DIR / "assets" / "icon.svg"), size="large")

ui.inject_styles()

# Make sure the table exists before any page runs. A failure here is
# remembered so pages can show a friendly message instead of crashing.
try:
    database.initialize_database()
    st.session_state["db_ready"] = True
except database.DatabaseError as exc:
    logging.getLogger(__name__).error("Database initialisation failed: %s", exc)
    st.session_state["db_ready"] = False

pages = {
    "Explore": [
        st.Page(navigation.PAGE_HOME, title="Home", icon=":material/home:", default=True),
        st.Page(navigation.PAGE_BROWSE, title="Browse examples", icon=":material/search:", url_path="browse"),
    ],
    "Contribute": [
        st.Page(navigation.PAGE_SUBMIT, title="Submit an example", icon=":material/add_circle:", url_path="submit"),
    ],
    "Insights": [
        st.Page(navigation.PAGE_ANALYTICS, title="Analytics", icon=":material/insights:", url_path="analytics"),
    ],
    "Moderation": [
        st.Page(navigation.PAGE_ADMIN, title="Admin / Review", icon=":material/admin_panel_settings:", url_path="admin"),
    ],
}

current = st.navigation(pages, position="sidebar")

pending_count = None
if navigation.is_admin() and st.session_state.get("db_ready"):
    try:
        pending_count = database.count_examples("pending")
    except database.DatabaseError:
        pending_count = None
navigation.sidebar_footer(pending_count)

current.run()
