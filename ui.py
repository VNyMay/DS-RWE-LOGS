"""Visual layer: theme tokens, global CSS and small reusable building blocks.

The look follows the Secure_Lan / EXVIN design language (deep greens, a gold
accent, lifted cards, uppercase kicker labels). Streamlit's own theme is
configured in ``.streamlit/config.toml``; this module adds the custom
pieces Streamlit cannot express on its own.

All HTML produced here escapes user text with ``esc`` first. Never pass raw
user input into a markup string without it.
"""

from __future__ import annotations

import html
from datetime import datetime

import streamlit as st

import config

# ---------------------------------------------------------------- tokens

# Same values as Secure_Lan's tokens.css, one set per theme.
_TOKENS = {
    "dark": {
        "base": "#06110d", "panel": "#0a1914", "raised": "#11261e", "hover": "#173228",
        "line": "rgba(190, 255, 230, 0.09)", "line-strong": "rgba(190, 255, 230, 0.18)",
        "text": "#eef5f1", "muted": "#8fa69b", "link": "#4fd8b0",
        "glow": "rgba(0, 148, 110, 0.22)",
        "shadow-sm": "0 1px 2px rgba(0,0,0,.4), 0 2px 8px rgba(0,0,0,.25)",
        "shadow-md": "0 14px 32px -14px rgba(0,0,0,.7), 0 4px 10px -4px rgba(0,0,0,.4)",
        "shadow-lg": "0 34px 70px -24px rgba(0,0,0,.85), 0 14px 28px -14px rgba(0,0,0,.5)",
        "amber-bg": "rgba(241, 160, 1, 0.16)", "amber-fg": "#ffd27a",
        "green-bg": "rgba(0, 148, 110, 0.18)", "green-fg": "#4fd8b0",
        "red-bg": "rgba(229, 72, 77, 0.16)", "red-fg": "#ff8a8e",
        "gray-bg": "rgba(143, 166, 155, 0.16)", "gray-fg": "#b7c6be",
        "gold-on": "#1a1200",
    },
    "light": {
        "base": "#ffffff", "panel": "#ffffff", "raised": "#f1f6f3", "hover": "#e4eee8",
        "line": "#e1eae5", "line-strong": "#c9d9d1",
        "text": "#0c1f18", "muted": "#5b6d64", "link": "#027554",
        "glow": "rgba(2, 117, 84, 0.08)",
        "shadow-sm": "0 1px 2px rgba(0,40,30,.05), 0 2px 8px rgba(0,40,30,.04)",
        "shadow-md": "0 14px 32px -14px rgba(0,50,38,.22), 0 4px 10px -4px rgba(0,50,38,.06)",
        "shadow-lg": "0 34px 70px -24px rgba(0,50,38,.28), 0 14px 28px -14px rgba(0,50,38,.10)",
        "amber-bg": "#fff1d6", "amber-fg": "#7a5200",
        "green-bg": "#e3f2ec", "green-fg": "#00523f",
        "red-bg": "#fde4e5", "red-fg": "#a3191e",
        "gray-bg": "#eceff0", "gray-fg": "#3f4f47",
        "gold-on": "#1a1200",
    },
}

_COMMON = {
    "green": "#027554", "green-bright": "#00946e", "green-deep": "#00523f",
    "gold": "#f1a001", "gold-soft": "#ffd27a", "danger": "#e5484d",
    "radius-large": "20px", "radius": "16px", "radius-small": "12px",
    "ease": "cubic-bezier(0.22, 1, 0.36, 1)",
}


def theme_type() -> str:
    """'light' or 'dark', following the active Streamlit theme (the app ships light only)."""
    try:
        return "dark" if st.context.theme.type == "dark" else "light"
    except Exception:  # noqa: BLE001 - bare mode
        return "light"


def _css_variables() -> str:
    tokens = {**_COMMON, **_TOKENS[theme_type()]}
    return ":root{" + "".join(f"--dsc-{name}:{value};" for name, value in tokens.items()) + "}"


_CSS = """
/* ---------- layout ---------- */
[data-testid="stMainBlockContainer"] { padding-top: 3.6rem; padding-bottom: 5rem; max-width: 1180px; }
@media (max-width: 720px) { [data-testid="stMainBlockContainer"] { padding-left: 16px; padding-right: 16px; } }
[data-testid="stAppViewContainer"] { background: var(--dsc-base); }
[data-testid="stSidebar"] { background: var(--dsc-panel); }
[data-testid="stSidebar"] [data-testid="stSidebarNav"] a { border-radius: var(--dsc-radius-small); }
[data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover { transform: translateX(3px); transition: transform .45s var(--dsc-ease); }
[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] { box-shadow: inset 3px 0 0 var(--dsc-green); }
[data-testid="stSidebar"] [data-testid="stSidebarNavSeparator"] { display: none; }
[data-testid="stSidebar"] [data-testid="stNavSectionHeader"] {
    color: var(--dsc-muted); font-size: 11px; font-weight: 700; letter-spacing: .1em; text-transform: uppercase;
}
h1, h2, h3 { letter-spacing: -0.01em; }
a { text-decoration: none; }
a:hover { text-decoration: underline; }
/* No focus rings: the app relies on colour changes instead of outlines. */
*:focus, *:focus-visible { outline: none !important; }
button:focus-visible, a:focus-visible, [role="button"]:focus-visible, [tabindex]:focus-visible { box-shadow: none !important; }

/* ---------- buttons ---------- */
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button, [data-testid="stLinkButton"] a { font-weight: 600; }
.stButton > button:hover:not(:disabled), .stDownloadButton > button:hover:not(:disabled), .stFormSubmitButton > button:hover:not(:disabled) { transform: translateY(-2px); box-shadow: var(--dsc-shadow-md); transition: transform .45s var(--dsc-ease), box-shadow .45s var(--dsc-ease); }
.stButton > button:active:not(:disabled), .stFormSubmitButton > button:active:not(:disabled) { transform: translateY(0) scale(.97); transition-duration: .2s; }
.stButton > button[kind="primary"]:hover:not(:disabled), .stFormSubmitButton > button[kind="primary"]:hover:not(:disabled) { box-shadow: var(--dsc-shadow-md), 0 8px 24px -8px rgba(0,148,110,.6); }

/* ---------- widgets ---------- */
[data-baseweb="input"], [data-baseweb="textarea"], [data-baseweb="select"] > div, .stNumberInput [data-baseweb="input"] {
    background: #ffffff !important;
}
[data-baseweb="input"]:hover, [data-baseweb="textarea"]:hover, [data-baseweb="select"] > div:hover { border-color: var(--dsc-green-bright) !important; }
[data-baseweb="input"]:focus-within, [data-baseweb="textarea"]:focus-within, [data-baseweb="select"] > div:focus-within {
    border-color: var(--dsc-green) !important; box-shadow: none !important;
}
[data-baseweb="input"] input:focus, [data-baseweb="textarea"] textarea:focus, [data-baseweb="select"] input:focus { outline: none !important; box-shadow: none !important; }
[data-testid="stWidgetLabel"] p { font-weight: 600; font-size: 13.5px; }
[data-testid="stExpander"] details { border-radius: var(--dsc-radius-small); }
.stTabs [data-baseweb="tab-list"] { gap: 6px; }
.stTabs [data-baseweb="tab"] { font-weight: 600; }
[data-testid="stSegmentedControl"] button, [data-testid="stPills"] button { font-weight: 600; }
[data-testid="stSidebar"] .stButton > button { background: #ffffff; }
.stButton > button[kind="secondary"], .stDownloadButton > button, .stFormSubmitButton > button[kind="secondary"] { background: #ffffff; }

/* ---------- bordered containers become cards ---------- */
[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: var(--dsc-radius) !important; background: var(--dsc-panel);
}
[class*="st-key-card-"] > [data-testid="stVerticalBlockBorderWrapper"],
[class*="st-key-card-"][data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--dsc-panel);
}
[class*="st-key-card-"]:hover > [data-testid="stVerticalBlockBorderWrapper"],
[class*="st-key-card-"][data-testid="stVerticalBlockBorderWrapper"]:hover {
    transform: translateY(-3px); box-shadow: var(--dsc-shadow-md); border-color: var(--dsc-green-bright) !important;
    transition: transform .45s var(--dsc-ease), box-shadow .45s var(--dsc-ease), border-color .45s var(--dsc-ease);
}
[class*="st-key-section-"] > [data-testid="stVerticalBlockBorderWrapper"],
[class*="st-key-section-"][data-testid="stVerticalBlockBorderWrapper"] { background: var(--dsc-panel); }

/* ---------- custom blocks ---------- */
.dsc-kicker { margin: 0 0 4px; color: var(--dsc-link); font-size: 11px; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; }
.dsc-title { margin: 0; font-size: 30px; font-weight: 700; line-height: 1.15; letter-spacing: -0.02em; color: var(--dsc-text); }
.dsc-subtitle { margin: 8px 0 0; max-width: 720px; color: var(--dsc-muted); font-size: 15px; line-height: 1.5; }
.dsc-header { padding-bottom: 18px; margin-bottom: 6px; border-bottom: 1px solid var(--dsc-line); }
.dsc-section-title { margin: 0 0 2px; font-size: 19px; font-weight: 700; letter-spacing: -0.01em; color: var(--dsc-text); }
.dsc-section-sub { margin: 0 0 10px; color: var(--dsc-muted); font-size: 13.5px; }

.dsc-hero {
    position: relative; overflow: hidden; margin-bottom: 8px; padding: 40px 40px 36px;
    border: 1px solid var(--dsc-line-strong); border-radius: var(--dsc-radius-large);
    background: var(--dsc-panel);
    box-shadow: var(--dsc-shadow-sm);
}
.dsc-hero::before { content: ""; position: absolute; inset: 0 0 auto 0; height: 4px; background: linear-gradient(90deg, var(--dsc-green-deep), var(--dsc-green-bright)); }
.dsc-hero .dsc-title { font-size: 40px; }
@media (max-width: 720px) { .dsc-hero { padding: 28px 22px; } .dsc-hero .dsc-title { font-size: 30px; } }

.dsc-metric {
    padding: 18px 20px; border: 1px solid var(--dsc-line); border-radius: var(--dsc-radius);
    background: var(--dsc-panel);
}
.dsc-metric:hover { transform: translateY(-2px); box-shadow: var(--dsc-shadow-md); border-color: var(--dsc-green-bright); transition: transform .45s var(--dsc-ease), box-shadow .45s var(--dsc-ease), border-color .45s var(--dsc-ease); }
.dsc-metric-label { margin: 0; color: var(--dsc-muted); font-size: 12px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }
.dsc-metric-value { margin: 6px 0 0; font-size: 32px; font-weight: 700; line-height: 1.1; letter-spacing: -0.02em; color: var(--dsc-text); }
.dsc-metric-hint { margin: 6px 0 0; color: var(--dsc-muted); font-size: 13px; }

.dsc-badge {
    display: inline-block; margin: 0 6px 6px 0; padding: 4px 11px; border-radius: 999px;
    font-size: 12px; font-weight: 700; line-height: 1.4; white-space: nowrap;
    background: var(--dsc-raised); color: var(--dsc-link); border: 1px solid transparent;
}
.dsc-badge-tech { background: transparent; border-color: var(--dsc-line-strong); color: var(--dsc-text); }
.dsc-badge-muted { background: var(--dsc-gray-bg); color: var(--dsc-gray-fg); }
.dsc-badge-demo { background: var(--dsc-gray-bg); color: var(--dsc-gray-fg); }
.dsc-badge-pending { background: var(--dsc-amber-bg); color: var(--dsc-amber-fg); }
.dsc-badge-approved { background: var(--dsc-green-bg); color: var(--dsc-green-fg); }
.dsc-badge-rejected { background: var(--dsc-red-bg); color: var(--dsc-red-fg); }
.dsc-badge-archived { background: var(--dsc-gray-bg); color: var(--dsc-gray-fg); }
.dsc-badge-level { background: var(--dsc-green-bg); color: var(--dsc-green-fg); border-color: var(--dsc-green); letter-spacing: .04em; }
.dsc-badge-level-hl { background: linear-gradient(135deg, var(--dsc-green-deep), var(--dsc-green)); color: #ffffff; border-color: transparent; }
.dsc-badge-issue { background: var(--dsc-raised); color: var(--dsc-muted); font-weight: 600; }

.dsc-card-title { margin: 4px 0 6px; font-size: 17px; font-weight: 700; line-height: 1.3; letter-spacing: -0.01em; color: var(--dsc-text); }
.dsc-card-summary { margin: 0 0 10px; color: var(--dsc-muted); font-size: 14px; line-height: 1.5;
    display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
.dsc-meta { display: flex; flex-wrap: wrap; gap: 6px 14px; margin: 0; color: var(--dsc-muted); font-size: 13px; }
.dsc-meta span { white-space: nowrap; }
.dsc-meta strong { color: var(--dsc-text); font-weight: 600; }

.dsc-empty {
    display: flex; flex-direction: column; align-items: center; gap: 8px; margin: 12px 0; padding: 44px 24px;
    border: 1px dashed var(--dsc-line-strong); border-radius: var(--dsc-radius); text-align: center;
}
.dsc-empty-icon { font-size: 34px; line-height: 1; margin-bottom: 4px; filter: drop-shadow(0 8px 18px var(--dsc-glow)); }
.dsc-empty h3 { margin: 0; font-size: 20px; letter-spacing: -0.01em; color: var(--dsc-text); }
.dsc-empty p { margin: 0; max-width: 460px; color: var(--dsc-muted); font-size: 14.5px; }

.dsc-detail-section { margin: 0 0 22px; }
.dsc-detail-section h3 { margin: 0 0 6px; font-size: 16px; font-weight: 700; color: var(--dsc-text); }
.dsc-detail-section p { margin: 0; white-space: pre-wrap; line-height: 1.6; color: var(--dsc-text); }
.dsc-detail-section .dsc-none { color: var(--dsc-muted); font-style: italic; }

.dsc-source { display: flex; align-items: flex-start; gap: 10px; margin: 0 0 8px; padding: 10px 14px;
    border: 1px solid var(--dsc-line); border-radius: var(--dsc-radius-small); background: var(--dsc-raised); font-size: 13.5px; word-break: break-all; }
.dsc-source .dsc-source-kind { flex: none; color: var(--dsc-muted); font-size: 11px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; padding-top: 3px; }
.dsc-source a { color: var(--dsc-link); }
.dsc-source .dsc-source-text { color: var(--dsc-text); }

.dsc-info-list { margin: 0; padding: 0; list-style: none; }
.dsc-info-list li { display: flex; flex-wrap: wrap; gap: 4px 12px; padding: 9px 0; border-bottom: 1px solid var(--dsc-line); font-size: 14px; }
.dsc-info-list li:last-child { border-bottom: 0; }
.dsc-info-list .k { flex: none; width: 100%; color: var(--dsc-muted); font-size: 11.5px; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; }
.dsc-info-list .v { flex: 1; min-width: 0; color: var(--dsc-text); line-height: 1.45; }

.dsc-step { display: flex; gap: 14px; align-items: flex-start; padding: 6px 0; }
.dsc-step-num { flex: none; display: grid; place-items: center; width: 30px; height: 30px; border-radius: 50%;
    background: linear-gradient(135deg, var(--dsc-green-deep), var(--dsc-green-bright)); color: #fff; font-weight: 700; font-size: 13px; }
.dsc-step h4 { margin: 3px 0 2px; font-size: 15px; color: var(--dsc-text); }
.dsc-step p { margin: 0; color: var(--dsc-muted); font-size: 13.5px; line-height: 1.5; }

.dsc-callout { padding: 14px 16px; border: 1px solid rgba(241,160,1,.45); border-radius: var(--dsc-radius-small);
    background: rgba(241,160,1,.10); color: var(--dsc-text); font-size: 14px; line-height: 1.5; }
.dsc-note { color: var(--dsc-muted); font-size: 13px; }
.dsc-required { color: var(--dsc-danger); font-weight: 700; }

.dsc-stepper { display: flex; gap: 8px; margin: 4px 0 18px; }
.dsc-step-pill { flex: 1; display: flex; align-items: center; gap: 10px; padding: 10px 14px; border: 1px solid var(--dsc-line); border-radius: 999px; background: var(--dsc-panel); color: var(--dsc-muted); font-size: 13px; font-weight: 600; }
.dsc-step-pill .n { display: grid; place-items: center; width: 24px; height: 24px; border-radius: 50%; border: 1px solid var(--dsc-line-strong); font-size: 12px; }
.dsc-step-pill.is-current { border-color: var(--dsc-green); color: var(--dsc-text); box-shadow: 0 0 0 4px rgba(2,117,84,.10); }
.dsc-step-pill.is-current .n { background: var(--dsc-green); border-color: var(--dsc-green); color: #fff; }
.dsc-step-pill.is-done { color: var(--dsc-green-fg); background: var(--dsc-green-bg); border-color: transparent; }
.dsc-step-pill.is-done .n { background: var(--dsc-green); border-color: var(--dsc-green); color: #fff; }
@media (max-width: 720px) { .dsc-step-pill span.t { display: none; } .dsc-step-pill { justify-content: center; } }

@keyframes dsc-rise { from { opacity: 0; transform: translateY(16px); } }
@media (prefers-reduced-motion: reduce) { * { animation-duration: 1ms !important; transition-duration: 1ms !important; } }
"""


def inject_styles() -> None:
    """Add the theme variables and CSS to the page. Call once per script run."""
    st.html(f"<style>{_css_variables()}{_CSS}</style>")


# ---------------------------------------------------------------- helpers

def esc(value: object) -> str:
    """HTML-escape any value for safe inclusion in markup."""
    return html.escape("" if value is None else str(value), quote=True)


def format_date(value: str | None, with_time: bool = False) -> str:
    """Turn a stored ISO timestamp into '12 Mar 2026' (or with a time)."""
    if not value:
        return ""
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", ""))
    except ValueError:
        return str(value)
    return parsed.strftime("%d %b %Y, %H:%M UTC" if with_time else "%d %b %Y")


# ---------------------------------------------------------------- blocks

def page_header(title: str, subtitle: str | None = None, kicker: str | None = None) -> None:
    parts = ['<div class="dsc-header">']
    if kicker:
        parts.append(f'<p class="dsc-kicker">{esc(kicker)}</p>')
    parts.append(f'<h1 class="dsc-title">{esc(title)}</h1>')
    if subtitle:
        parts.append(f'<p class="dsc-subtitle">{esc(subtitle)}</p>')
    parts.append("</div>")
    st.html("".join(parts))


def section_heading(title: str, subtitle: str | None = None) -> None:
    sub = f'<p class="dsc-section-sub">{esc(subtitle)}</p>' if subtitle else '<div style="height:8px"></div>'
    st.html(f'<h2 class="dsc-section-title">{esc(title)}</h2>{sub}')


def kicker(text: str) -> None:
    st.html(f'<p class="dsc-kicker">{esc(text)}</p>')


def badge_html(text: str, kind: str = "category") -> str:
    """A pill. ``kind`` is one of category, tech, muted, demo, issue or a status name."""
    return f'<span class="dsc-badge dsc-badge-{esc(kind)}">{esc(text)}</span>'


def level_badge_html(level: str) -> str:
    """SL in green, HL in gold, so the two course levels are told apart at a glance."""
    label = level
    extra = " dsc-badge-level-hl" if level == "HL" else ""
    return f'<span class="dsc-badge dsc-badge-level{extra}">{esc(label)}</span>'


def status_badge_html(status: str) -> str:
    label = config.STATUS_LABELS.get(status, status.title())
    return badge_html(label, status)


def badges(*items: tuple[str, str]) -> None:
    """Render several pills on one line. Each item is (text, kind)."""
    st.html("<div>" + "".join(badge_html(text, kind) for text, kind in items if text) + "</div>")


def metric_card(label: str, value: object, hint: str | None = None) -> None:
    hint_html = f'<p class="dsc-metric-hint">{esc(hint)}</p>' if hint else ""
    st.html(
        f'<div class="dsc-metric"><p class="dsc-metric-label">{esc(label)}</p>'
        f'<p class="dsc-metric-value">{esc(value)}</p>{hint_html}</div>'
    )


def metric_row(items: list[tuple[str, object, str | None]]) -> None:
    """A row of metric cards; ``items`` are (label, value, hint)."""
    columns = st.columns(len(items))
    for column, (label, value, hint) in zip(columns, items):
        with column:
            metric_card(label, value, hint)


def empty_state(title: str, hint: str, icon: str = "📭") -> None:
    st.html(
        f'<div class="dsc-empty"><div class="dsc-empty-icon">{esc(icon)}</div>'
        f"<h3>{esc(title)}</h3><p>{esc(hint)}</p></div>"
    )


def callout(text: str) -> None:
    st.html(f'<div class="dsc-callout">{esc(text)}</div>')


def note(text: str) -> None:
    st.html(f'<p class="dsc-note">{esc(text)}</p>')


def detail_section(title: str, body: str | None, show_when_empty: bool = False) -> None:
    """A titled block of analysis text. Hidden when empty unless asked otherwise."""
    if body:
        st.html(f'<div class="dsc-detail-section"><h3>{esc(title)}</h3><p>{esc(body)}</p></div>')
    elif show_when_empty:
        st.html(f'<div class="dsc-detail-section"><h3>{esc(title)}</h3><p class="dsc-none">Not specified</p></div>')


def info_list(rows: list[tuple[str, str | None]]) -> None:
    """Key/value rows; rows with an empty value are skipped."""
    items = "".join(
        f'<li><span class="k">{esc(key)}</span><span class="v">{esc(value)}</span></li>'
        for key, value in rows if value
    )
    if items:
        st.html(f'<ul class="dsc-info-list">{items}</ul>')


def source_link_html(url_or_text: str, kind: str) -> str:
    """One source row. Real URLs open in a new tab; other citations show as text."""
    from validation import is_valid_url  # local import keeps ui.py free of heavy imports

    if is_valid_url(url_or_text):
        safe = esc(url_or_text)
        link = f'<a href="{safe}" target="_blank" rel="noopener noreferrer">{safe}</a>'
    else:
        link = f'<span class="dsc-source-text">{esc(url_or_text)}</span>'
    return f'<div class="dsc-source"><span class="dsc-source-kind">{esc(kind)}</span>{link}</div>'


def source_list(main_url: str | None, additional: list[str]) -> None:
    parts = []
    if main_url:
        parts.append(source_link_html(main_url, "Main"))
    for extra in additional:
        parts.append(source_link_html(extra, "Also"))
    if parts:
        st.html("".join(parts))
    else:
        st.html('<p class="dsc-none dsc-note">No sources recorded.</p>')


def stepper(labels: list[str], current: int) -> None:
    """Progress pills for a multi-step form. ``current`` is zero-based."""
    parts = []
    for index, label in enumerate(labels):
        state = "is-done" if index < current else ("is-current" if index == current else "")
        mark = "&#10003;" if index < current else str(index + 1)
        parts.append(f'<div class="dsc-step-pill {state}"><span class="n">{mark}</span><span class="t">{esc(label)}</span></div>')
    st.html('<div class="dsc-stepper">' + "".join(parts) + "</div>")


def steps(items: list[tuple[str, str]]) -> None:
    """Numbered explanation steps: (heading, text)."""
    parts = []
    for index, (heading, text) in enumerate(items, start=1):
        parts.append(
            f'<div class="dsc-step"><div class="dsc-step-num">{index}</div>'
            f"<div><h4>{esc(heading)}</h4><p>{esc(text)}</p></div></div>"
        )
    st.html("".join(parts))
