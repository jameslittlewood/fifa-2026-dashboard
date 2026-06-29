from pathlib import Path
from html import escape
import logging
import os
import re
import unicodedata

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
LOGGER = logging.getLogger(__name__)

st.set_page_config(
    page_title="World Cup 2026 Scenario Explorer",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# -----------------------------------------------------------------------------
# Theme setup
# -----------------------------------------------------------------------------
THEMES = {
    "light": {
        # Page and layout
        "app_bg": "#fafafa",
        "app_bg_secondary": "#f1f2f4",
        "sidebar_bg": "#fafafa",

        # Cards, inputs, tables and charts
        "card_bg": "#ffffff",
        "card_bg_soft": "#f5f6f8",
        "input_bg": "#ffffff",
        "table_bg": "#ffffff",
        "table_header": "#f5f1f1",
        "table_hover": "#fff0f2",
        "chart_bg": "#ffffff",

        # Typography
        "text": "#20242b",
        "muted": "#666b73",

        # Borders and chart gridlines
        "border": "#d8dce2",
        "grid": "#e7eaee",

        # Neutral interface palette. Keep chart and table colours unchanged.
        "accent": "#2f343c",
        "comparison_team_a": "#ce1126",
        "comparison_team_b": "#27313d",

        # Player identifiers stay unchanged for chart consistency.
        "comparison_player_1": "#C81E3A",  # crimson
        "comparison_player_2": "#B8622B",  # burnt amber
        "comparison_player_3": "#167C78",  # teal
        "comparison_player_4": "#5167B8",  # indigo-blue
        "accent_soft": "#eef1f4",
        "accent_border": "#d6dbe2",

        # Hero/background effects
        "hero_start": "#f8f9fb",
        "hero_end": "#ffffff",
        "hero_ring": "rgba(80, 88, 100, 0.08)",

        # Map colours
        "map_land": "#f0ebeb",
        "map_ocean": "#fcfbfb",

        # Shadows
        "shadow": "0 10px 28px rgba(32, 36, 43, 0.08)",
    },
}

theme = THEMES["light"]


def inject_theme_css(active_theme: dict[str, str]) -> None:
    """Inject CSS variables and component styling for the active theme."""
    variables = "\n".join(
        f"--{name.replace('_', '-')}: {value};"
        for name, value in active_theme.items()
    )

    st.markdown(
        f"""
        <style>
            :root {{
                {variables}
            }}

            html,
            body,
            [class*="css"] {{
                color: var(--text);
            }}

            .stApp {{
                background:
                    radial-gradient(
                        circle at top right,
                        var(--hero-ring),
                        transparent 42%
                    ),
                    linear-gradient(
                        135deg,
                        var(--app-bg) 0%,
                        var(--app-bg-secondary) 100%
                    );
                color: var(--text);
            }}

            header[data-testid="stHeader"] {{
                background: var(--app-bg) !important;
            }}

            [data-testid="stToolbar"],
            [data-testid="stDecoration"] {{
                background: transparent !important;
            }}

            .block-container {{
                max-width: 1450px;
                padding-top: 1.5rem;
                padding-bottom: 3rem;
            }}

            h1,
            h2,
            h3 {{
                color: var(--text);
                letter-spacing: -0.03em;
            }}

            p,
            label,
            .stCaption {{
                color: var(--muted);
            }}

            [data-testid="stSidebar"] {{
                background: var(--sidebar-bg);
                border-right: 1px solid var(--border);
            }}

            [data-testid="stSidebar"] > div:first-child {{
                background: var(--sidebar-bg);
            }}

            /* Sidebar filter layout: consistent spacing and left alignment. */
            [data-testid="stSidebar"] > div:first-child {{
                padding-top: 1rem;
            }}

            [data-testid="stSidebar"] h3 {{
                margin-bottom: 1.25rem !important;
            }}

            [data-testid="stSidebar"] [role="radiogroup"] {{
                display: flex !important;
                flex-direction: column !important;
                align-items: stretch !important;
                gap: 0.45rem !important;
                padding-top: 0.2rem !important;
            }}

            [data-testid="stSidebar"] [data-baseweb="radio"] {{
                width: 100% !important;
                margin: 0 !important;
                padding: 0 !important;
                min-height: auto !important;
            }}

            [data-testid="stSidebar"] [data-baseweb="radio"] label {{
                width: 100% !important;
                align-items: center !important;
                line-height: 1.25 !important;
            }}

            [data-testid="stSidebar"] [data-testid="stRadio"] > label {{
                margin-bottom: 0.35rem !important;
                color: var(--text) !important;
                font-weight: 700 !important;
            }}

            [data-testid="stSidebar"] [data-testid="stCheckbox"] label,
            [data-testid="stSidebar"] [data-testid="stToggle"] label {{
                align-items: center !important;
                line-height: 1.2 !important;
            }}

            [data-testid="stSidebar"] [data-testid="stCheckbox"] {{
                margin: 0.1rem 0 !important;
            }}

            [data-testid="stSidebar"] [data-testid="stToggle"] {{
                margin: 0.15rem 0 0.35rem !important;
            }}

            [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{
                margin-bottom: 0.35rem !important;
            }}

            /* Keep the desktop sidebar wide enough for filter controls. */
            @media (min-width: 900px) {{
                [data-testid="stSidebar"][aria-expanded="true"],
                [data-testid="stSidebar"][aria-expanded="true"] > div:first-child {{
                    width: 360px !important;
                    min-width: 360px !important;
                    max-width: 360px !important;
                    flex: 0 0 360px !important;
                }}

                [data-testid="stSidebarResizeHandle"],
                [data-testid="stSidebarResizer"] {{
                    display: none !important;
                    pointer-events: none !important;
                }}
            }}

            /* Compact KPI cards keep the shared dashboard header concise on
             * every tab, without changing the underlying values or layout. */
            [data-testid="stMetric"] {{
                background: var(--card-bg);
                border: 1px solid var(--border);
                border-radius: 14px;
                padding: 0.65rem 0.8rem;
                box-shadow: 0 6px 16px rgba(55, 25, 30, 0.05);
            }}

            [data-testid="stMetricLabel"] {{
                color: var(--muted);
                font-size: 0.68rem;
                text-transform: uppercase;
                letter-spacing: 0.075em;
                line-height: 1.2;
            }}

            [data-testid="stMetricValue"] {{
                color: var(--text);
                font-size: 1.45rem;
                line-height: 1.15;
            }}

            /* The dashboard hero appears above every page, so it uses a
             * compact treatment to reduce repeated vertical scrolling. */
            .dashboard-hero {{
                padding: 0.72rem 1.15rem;
                margin-bottom: 0.35rem;
                border: 1px solid var(--accent-border);
                border-radius: 18px;
                background: linear-gradient(
                    135deg,
                    var(--hero-start),
                    var(--hero-end)
                );
                box-shadow: 0 8px 20px rgba(55, 25, 30, 0.06);
            }}

            .dashboard-hero h1 {{
                margin: 0;
                color: var(--text);
                font-size: clamp(1.55rem, 2.7vw, 2.05rem);
                line-height: 1.1;
            }}

            .dashboard-hero p {{
                margin: 0.22rem 0 0;
                color: var(--muted);
                font-size: 0.86rem;
                line-height: 1.35;
            }}

            .england-mode-badge {{
                display: inline-flex;
                align-items: center;
                gap: 0.45rem;
                margin-top: 0.85rem;
                padding: 0.36rem 0.62rem;
                border: 1px solid var(--accent-border);
                border-radius: 999px;
                background: var(--accent-soft);
                color: var(--accent);
                font-size: 0.72rem;
                font-weight: 800;
                letter-spacing: 0.1em;
                text-transform: uppercase;
            }}

            .england-mode-badge::before {{
                content: "";
                width: 0.58rem;
                height: 0.58rem;
                border-radius: 50%;
                background: var(--accent);
                box-shadow: 0 0 0 3px var(--card-bg);
            }}

            .section-label {{
                color: var(--accent);
                font-size: 0.76rem;
                font-weight: 700;
                letter-spacing: 0.12em;
                text-transform: uppercase;
                margin-bottom: 0.35rem;
            }}

            .snapshot-heading {{
                margin: 0.35rem 0 0.3rem;
                font-size: 0.7rem;
            }}

            .soft-note {{
                margin: 0.6rem 0 1.25rem;
                padding: 0.8rem 1rem;
                border: 1px solid var(--accent-border);
                border-radius: 12px;
                background: var(--accent-soft);
                color: var(--muted);
                font-size: 0.92rem;
            }}

            /* Compact pill navigation. This replaces Streamlit's underline
             * tabs with left-aligned clickable controls without adding height. */
            div[data-testid="stTabs"] {{
                margin: 0 !important;
            }}

            div[data-testid="stTabs"] [data-baseweb="tab-list"] {{
                display: flex !important;
                align-items: center !important;
                justify-content: flex-start !important;
                gap: 0.38rem !important;
                min-height: 2.12rem !important;
                margin: 0 !important;
                padding: 0 !important;
                border-bottom: 0 !important;
            }}

            /* Remove Streamlit/BaseWeb's default active-tab indicator. */
            div[data-testid="stTabs"] [data-baseweb="tab-border"],
            div[data-testid="stTabs"] [data-baseweb="tab-highlight"],
            div[data-testid="stTabs"] button[role="tab"]::before,
            div[data-testid="stTabs"] button[role="tab"]::after {{
                display: none !important;
                content: none !important;
            }}

            div[data-testid="stTabs"] button[role="tab"] {{
                min-height: 2.12rem !important;
                margin: 0 !important;
                padding: 0.32rem 0.78rem !important;
                border: 1px solid transparent !important;
                border-bottom: 1px solid transparent !important;
                border-radius: 999px !important;
                background: transparent !important;
                color: var(--muted) !important;
                font-size: 0.88rem !important;
                font-weight: 650 !important;
                line-height: 1 !important;
                white-space: nowrap !important;
                transition: background 120ms ease, border-color 120ms ease,
                    color 120ms ease !important;
            }}

            div[data-testid="stTabs"] button[role="tab"]:hover {{
                background: var(--card-bg-soft) !important;
                border-color: var(--border) !important;
                color: var(--text) !important;
            }}

            div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {{
                background: rgba(32, 36, 43, 0.86) !important;
                border-color: transparent !important;
                border-bottom-color: transparent !important;
                color: #ffffff !important;
                box-shadow: none !important;
            }}

            /* Streamlit nests the visible tab label inside the button, so
             * explicitly set every child to white for the selected pill. */
            div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] *,
            div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] p,
            div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] span {{
                color: #ffffff !important;
                fill: #ffffff !important;
            }}

            @media (max-width: 700px) {{
                div[data-testid="stTabs"] [data-baseweb="tab-list"] {{
                    justify-content: flex-start !important;
                    overflow-x: auto !important;
                    scrollbar-width: none !important;
                }}

                div[data-testid="stTabs"] [data-baseweb="tab-list"]::-webkit-scrollbar {{
                    display: none !important;
                }}
            }}

            /* Closed selectbox and multiselect controls */
            div[data-baseweb="select"] > div,
            [data-testid="stDateInput"] input,
            [data-testid="stTextInput"] input,
            [data-testid="stSelectbox"] input {{
                background: var(--input-bg) !important;
                color: var(--text) !important;
                border-color: var(--border) !important;
            }}

            div[data-baseweb="select"] > div:focus-within {{
                border-color: var(--accent-border) !important;
                box-shadow: 0 0 0 1px var(--accent-border) !important;
                outline: none !important;
            }}

            div[data-baseweb="select"] input,
            div[data-baseweb="select"] span,
            div[data-baseweb="select"] svg {{
                color: var(--text) !important;
                fill: currentColor !important;
            }}

            /* Selected values inside multiselect controls */
            div[data-baseweb="select"] [data-baseweb="tag"] {{
                background: var(--accent-soft) !important;
                border: 1px solid var(--accent-border) !important;
                border-radius: 8px !important;
                box-shadow: none !important;
            }}

            div[data-baseweb="select"] [data-baseweb="tag"] span,
            div[data-baseweb="select"] [data-baseweb="tag"] svg {{
                color: var(--accent) !important;
                fill: var(--accent) !important;
                font-weight: 600 !important;
            }}

            div[data-baseweb="select"] [data-baseweb="tag"]:hover {{
                background: var(--accent-border) !important;
            }}

            /*
             * Open BaseWeb dropdowns.
             *
             * Streamlit places dropdowns in a portal. This rule set removes
             * every browser/BaseWeb focus ring from the portal and then gives
             * only the visible options panel a themed surface. It deliberately
             * uses no visible menu border, so no white outline can appear.
             */
            div[data-baseweb="layer"],
            div[data-baseweb="layer"] > div,
            div[data-baseweb="popover"],
            div[data-baseweb="popover"] > div,
            div[data-baseweb="popover"] > div > div,
            div[data-baseweb="popover"] [data-baseweb="menu"],
            div[data-baseweb="popover"] [role="listbox"],
            div[data-baseweb="popover"] ul,
            div[role="dialog"]:has([role="listbox"]),
            div[role="dialog"]:has([data-baseweb="menu"]) {{
                border: 0 !important;
                outline: 0 !important;
                box-shadow: none !important;
                -webkit-tap-highlight-color: transparent !important;
            }}

            div[data-baseweb="layer"] *,
            div[data-baseweb="layer"] *::before,
            div[data-baseweb="layer"] *::after,
            div[data-baseweb="popover"] *,
            div[data-baseweb="popover"] *::before,
            div[data-baseweb="popover"] *::after,
            div[role="dialog"]:has([role="listbox"]) *,
            div[role="dialog"]:has([data-baseweb="menu"]) * {{
                outline: 0 !important;
            }}

            div[data-baseweb="layer"] *:focus,
            div[data-baseweb="layer"] *:focus-visible,
            div[data-baseweb="layer"] *:focus-within,
            div[data-baseweb="popover"] *:focus,
            div[data-baseweb="popover"] *:focus-visible,
            div[data-baseweb="popover"] *:focus-within,
            div[role="dialog"]:has([role="listbox"]) *:focus,
            div[role="dialog"]:has([role="listbox"]) *:focus-visible,
            div[role="dialog"]:has([role="listbox"]) *:focus-within {{
                outline: 0 !important;
                box-shadow: none !important;
            }}

            div[role="dialog"]:has([role="listbox"]),
            div[role="dialog"]:has([role="listbox"]) > div,
            div[role="dialog"]:has([role="listbox"]) > div > div,
            div[data-baseweb="popover"] > div,
            div[data-baseweb="popover"] > div > div,
            div[data-baseweb="popover"] > div > div > div {{
                background: transparent !important;
                background-color: transparent !important;
                border-color: transparent !important;
                border: 0 !important;
                border-radius: 12px !important;
                box-shadow: none !important;
                overflow: hidden !important;
                clip-path: inset(0 round 12px) !important;
                padding: 0 !important;
            }}

            /* The list itself is the only visible dropdown surface. */
            div[data-baseweb="popover"] [data-baseweb="menu"],
            div[data-baseweb="popover"] [role="listbox"],
            div[data-baseweb="popover"] ul,
            div[role="dialog"] [role="listbox"] {{
                background: var(--card-bg) !important;
                color: var(--text) !important;
                border: 0 !important;
                border-radius: 12px !important;
                box-shadow: var(--shadow) !important;
                overflow: hidden !important;
                scrollbar-width: none !important;
                clip-path: inset(0 round 12px) !important;
                background-clip: padding-box !important;
            }}

            div[data-baseweb="popover"] [data-baseweb="menu"]::-webkit-scrollbar,
            div[data-baseweb="popover"] [role="listbox"]::-webkit-scrollbar,
            div[data-baseweb="popover"] ul::-webkit-scrollbar,
            div[role="dialog"] [role="listbox"]::-webkit-scrollbar,
            div[data-baseweb="popover"] [data-baseweb="calendar"]::-webkit-scrollbar,
            div[data-baseweb="popover"] [data-baseweb="datepicker"]::-webkit-scrollbar,
            div[role="dialog"] [data-baseweb="calendar"]::-webkit-scrollbar,
            div[role="dialog"] [data-baseweb="datepicker"]::-webkit-scrollbar {{
                width: 0 !important;
                height: 0 !important;
                display: none !important;
            }}

            div[data-baseweb="popover"] [role="option"],
            div[role="dialog"] [role="option"] {{
                background: var(--card-bg) !important;
                color: var(--text) !important;
                border: 0 !important;
                box-shadow: none !important;
            }}

            div[data-baseweb="popover"] [role="option"] *,
            div[role="dialog"] [role="option"] * {{
                color: var(--text) !important;
            }}

            div[data-baseweb="popover"] [role="option"]:hover,
            div[data-baseweb="popover"] [role="option"][aria-selected="true"],
            div[role="dialog"] [role="option"]:hover,
            div[role="dialog"] [role="option"][aria-selected="true"] {{
                background: var(--accent-soft) !important;
                color: var(--text) !important;
            }}

            div[data-baseweb="popover"] [role="presentation"],
            div[role="dialog"] [role="presentation"] {{
                background: transparent !important;
                background-color: transparent !important;
                border-radius: 12px !important;
                overflow: hidden !important;
                clip-path: inset(0 round 12px) !important;
                padding: 0 !important;
            }}

            div[data-baseweb="popover"] input,
            div[role="dialog"] input {{
                background: var(--input-bg) !important;
                color: var(--text) !important;
                border: 1px solid var(--border) !important;
                border-radius: 8px !important;
                outline: 0 !important;
                box-shadow: none !important;
            }}

            div[data-baseweb="popover"] svg,
            div[role="dialog"] svg {{
                color: var(--muted) !important;
                fill: currentColor !important;
            }}

            /* Date picker calendar, used by Custom range. */
            div[data-baseweb="popover"] [data-baseweb="calendar"],
            div[data-baseweb="popover"] [data-baseweb="datepicker"],
            div[role="dialog"] [data-baseweb="calendar"],
            div[role="dialog"] [data-baseweb="datepicker"] {{
                background: var(--card-bg) !important;
                color: var(--text) !important;
            }}

            div[data-baseweb="popover"] [data-baseweb="calendar"] button,
            div[data-baseweb="popover"] [data-baseweb="datepicker"] button,
            div[role="dialog"] [data-baseweb="calendar"] button,
            div[role="dialog"] [data-baseweb="datepicker"] button {{
                background: transparent !important;
                color: var(--text) !important;
                border-color: transparent !important;
                box-shadow: none !important;
            }}

            div[data-baseweb="popover"] [aria-selected="true"],
            div[role="dialog"] [aria-selected="true"] {{
                background: var(--accent-soft) !important;
                color: var(--text) !important;
            }}

            /*
             * Native st.dataframe column menus use a different popover path
             * from the regular select/listbox widgets. Give those menus an
             * explicit opaque surface so they do not inherit the transparent
             * wrapper styling above.
             */
            [data-testid="stDataFrameColumnMenu"],
            [data-testid="stDataFrameColumnFormattingMenu"],
            [aria-label="Dataframe column menu"] {{
                background: var(--card-bg) !important;
                background-color: var(--card-bg) !important;
                color: var(--text) !important;
                border: 1px solid var(--border) !important;
                border-radius: 12px !important;
                box-shadow: var(--shadow) !important;
                opacity: 1 !important;
                overflow: hidden !important;
            }}

            [data-testid="stDataFrameColumnMenu"] *,
            [data-testid="stDataFrameColumnFormattingMenu"] *,
            [aria-label="Dataframe column menu"] * {{
                color: var(--text) !important;
            }}

            [data-testid="stDataFrameColumnMenu"] [role="menuitem"],
            [data-testid="stDataFrameColumnFormattingMenu"] [role="menuitem"],
            [aria-label="Dataframe column menu"] [role="menuitem"] {{
                background: var(--card-bg) !important;
                background-color: var(--card-bg) !important;
                color: var(--text) !important;
            }}

            [data-testid="stDataFrameColumnMenu"] [role="menuitem"]:hover,
            [data-testid="stDataFrameColumnFormattingMenu"] [role="menuitem"]:hover,
            [aria-label="Dataframe column menu"] [role="menuitem"]:hover {{
                background: var(--accent-soft) !important;
            }}

            [data-testid="stDataFrameColumnMenu"] [role="separator"],
            [data-testid="stDataFrameColumnFormattingMenu"] [role="separator"],
            [data-testid="stDataFrameColumnMenu"] hr,
            [data-testid="stDataFrameColumnFormattingMenu"] hr {{
                background: var(--border) !important;
                border-color: var(--border) !important;
                opacity: 1 !important;
            }}

            input[type="radio"],
            input[type="checkbox"] {{
                accent-color: var(--accent);
            }}

            /* Date and advanced filters: theme both the summary and the body. */
            [data-testid="stExpander"],
            [data-testid="stExpander"] > details,
            [data-testid="stExpander"] details {{
                background: var(--card-bg) !important;
                border: 1px solid var(--border) !important;
                border-radius: 14px !important;
                box-shadow: var(--shadow) !important;
                overflow: hidden !important;
            }}

            [data-testid="stExpander"] summary,
            [data-testid="stExpander"] summary > div,
            [data-testid="stExpander"] summary > div > div,
            [data-testid="stExpander"] [data-testid="stExpanderHeader"],
            [data-testid="stExpander"] [data-testid="stExpanderHeader"] > div {{
                background: var(--card-bg) !important;
                color: var(--text) !important;
                border: 0 !important;
                box-shadow: none !important;
            }}

            [data-testid="stExpander"] summary *,
            [data-testid="stExpander"] [data-testid="stExpanderHeader"] * {{
                color: var(--text) !important;
            }}

            [data-testid="stExpander"] summary:hover,
            [data-testid="stExpander"] [data-testid="stExpanderHeader"]:hover {{
                background: var(--accent-soft) !important;
            }}

            [data-testid="stExpander"] details > div,
            [data-testid="stExpander"] details > div > div,
            [data-testid="stExpander"] [data-testid="stExpanderDetails"],
            [data-testid="stExpander"] [data-testid="stExpanderDetails"] > div,
            [data-testid="stExpander"] [data-testid="stExpanderDetails"] > div > div {{
                background: var(--card-bg-soft) !important;
                color: var(--text) !important;
                border: 0 !important;
                box-shadow: none !important;
            }}

            [data-testid="stExpander"] [data-testid="stExpanderDetails"] {{
                border-top: 1px solid var(--border) !important;
                padding-top: 0.35rem !important;
            }}

            [data-testid="stExpander"] [data-testid="stExpanderDetails"] label,
            [data-testid="stExpander"] [data-testid="stExpanderDetails"] p,
            [data-testid="stExpander"] [data-testid="stExpanderDetails"] legend,
            [data-testid="stExpander"] [data-testid="stExpanderDetails"] span {{
                color: var(--text) !important;
            }}

            [data-testid="stExpander"] [data-testid="stExpanderDetails"] .stCaption,
            [data-testid="stExpander"] [data-testid="stExpanderDetails"] small {{
                color: var(--muted) !important;
            }}

            [data-testid="stExpander"] [data-testid="stExpanderDetails"] [role="radiogroup"] {{
                gap: 0.4rem !important;
                padding: 0.3rem 0 0.1rem !important;
            }}

            [data-testid="stExpander"] [data-testid="stExpanderDetails"] [data-baseweb="radio"] {{
                padding: 0.2rem 0 !important;
            }}

            [data-testid="stExpander"] [data-testid="stExpanderDetails"] [data-testid="stMarkdownContainer"] strong {{
                color: var(--text) !important;
            }}

            .selector-field-label {{
                margin: 0.2rem 0 0.45rem;
                color: var(--text);
                font-size: 0.98rem;
                font-weight: 600;
            }}

            /* Used by dense control rows such as the four-player selector. */
            .selector-field-label.compact-selector-field-label {{
                margin: 0 0 0.22rem;
                font-size: 0.76rem;
                font-weight: 700;
                letter-spacing: 0.02em;
            }}

            .player-compare-heading {{
                margin: 0.05rem 0 0.4rem;
                color: var(--text);
                font-size: clamp(1.35rem, 2vw, 1.7rem);
                font-weight: 750;
                letter-spacing: -0.025em;
                line-height: 1.15;
            }}


            /* A shorter heading and note keep the international-record panel
             * compact without reducing the chart's reading space. */
            .international-record-heading {{
                margin: 0.02rem 0 0.08rem;
                color: var(--text);
                font-size: clamp(1.18rem, 1.65vw, 1.45rem);
                font-weight: 750;
                letter-spacing: -0.022em;
                line-height: 1.12;
            }}

            .international-record-note {{
                margin: 0 0 0.28rem;
                color: var(--muted);
                font-size: 0.80rem;
                line-height: 1.3;
            }}

            .filter-panel-heading {{
                margin: 0.85rem 0 0.45rem;
                color: var(--text);
                font-size: 0.98rem;
                font-weight: 700;
            }}

            .filter-panel-note {{
                margin: 0.15rem 0 0.7rem;
                color: var(--muted);
                font-size: 0.85rem;
                line-height: 1.45;
            }}

            [data-testid="stDataFrame"] {{
                border: 1px solid var(--border) !important;
                border-radius: 14px !important;
                overflow: hidden !important;
                background: var(--table-bg) !important;
                --gdg-accent-color: var(--accent) !important;
                --gdg-accent-fg: var(--card-bg) !important;
                --gdg-accent-light: var(--accent-soft) !important;
                --gdg-text-dark: var(--text) !important;
                --gdg-text-medium: var(--muted) !important;
                --gdg-text-light: var(--muted) !important;
                --gdg-text-bubble: var(--muted) !important;
                --gdg-text-header: var(--muted) !important;
                --gdg-text-group-header: var(--muted) !important;
                --gdg-text-header-selected: var(--text) !important;
                --gdg-bg-cell: var(--table-bg) !important;
                --gdg-bg-cell-medium: var(--card-bg-soft) !important;
                --gdg-bg-header: var(--table-header) !important;
                --gdg-bg-group-header: var(--table-header) !important;
                --gdg-bg-group-header-hovered: var(--card-bg-soft) !important;
                --gdg-bg-header-has-focus: var(--card-bg-soft) !important;
                --gdg-bg-header-hovered: var(--card-bg-soft) !important;
                --gdg-bg-bubble: var(--card-bg-soft) !important;
                --gdg-bg-bubble-selected: var(--accent-soft) !important;
                --gdg-bg-search-result: var(--accent-soft) !important;
                --gdg-border-color: var(--border) !important;
                --gdg-horizontal-border-color: var(--border) !important;
                --gdg-drilldown-border: var(--border) !important;
                --gdg-link-color: var(--accent) !important;
                --gdg-header-bottom-border-color: var(--border) !important;
            }}

            [data-testid="stDataFrame"] div[style*="--gdg-bg-header"] {{
                --gdg-accent-color: var(--accent) !important;
                --gdg-accent-fg: var(--card-bg) !important;
                --gdg-accent-light: var(--accent-soft) !important;
                --gdg-text-dark: var(--text) !important;
                --gdg-text-medium: var(--muted) !important;
                --gdg-text-light: var(--muted) !important;
                --gdg-text-bubble: var(--muted) !important;
                --gdg-text-header: var(--muted) !important;
                --gdg-text-group-header: var(--muted) !important;
                --gdg-text-header-selected: var(--text) !important;
                --gdg-bg-cell: var(--table-bg) !important;
                --gdg-bg-cell-medium: var(--card-bg-soft) !important;
                --gdg-bg-header: var(--table-header) !important;
                --gdg-bg-group-header: var(--table-header) !important;
                --gdg-bg-group-header-hovered: var(--card-bg-soft) !important;
                --gdg-bg-header-has-focus: var(--card-bg-soft) !important;
                --gdg-bg-header-hovered: var(--card-bg-soft) !important;
                --gdg-bg-bubble: var(--card-bg-soft) !important;
                --gdg-bg-bubble-selected: var(--accent-soft) !important;
                --gdg-bg-search-result: var(--accent-soft) !important;
                --gdg-border-color: var(--border) !important;
                --gdg-horizontal-border-color: var(--border) !important;
                --gdg-drilldown-border: var(--border) !important;
                --gdg-link-color: var(--accent) !important;
                --gdg-header-bottom-border-color: var(--border) !important;
            }}

            [data-testid="stDataFrame"] [role="grid"],
            [data-testid="stDataFrame"] [role="row"],
            [data-testid="stDataFrame"] [role="gridcell"] {{
                background: var(--table-bg) !important;
                color: var(--text) !important;
                border-color: var(--border) !important;
            }}

            [data-testid="stDataFrame"] [role="rowheader"],
            [data-testid="stDataFrame"] input[type="checkbox"] {{
                display: none !important;
            }}

            [data-testid="stDataFrame"] [role="columnheader"],
            [data-testid="stDataFrame"] [role="rowheader"] {{
                background: var(--table-header) !important;
                color: var(--muted) !important;
                border-color: var(--border) !important;
            }}

            [data-testid="stPlotlyChart"] {{
                border: 1px solid var(--border);
                border-radius: 14px;
                background: var(--chart-bg);
                overflow: hidden;
            }}

            .stButton > button,
            .stDownloadButton > button {{
                background: var(--card-bg-soft) !important;
                color: var(--text) !important;
                border: 1px solid var(--accent-border) !important;
                border-radius: 10px;
                box-shadow: none !important;
                font-weight: 600;
            }}

            .stButton > button:hover,
            .stDownloadButton > button:hover {{
                background: var(--accent-soft) !important;
                border-color: var(--accent) !important;
                color: var(--text) !important;
            }}

            /* Fully custom HTML tables. Every visible table surface follows
             * the active dashboard theme.
             */
            .themed-table-wrap {{
                width: 100%;
                max-width: 100%;
                overflow: auto;
                border: 1px solid var(--border);
                border-radius: 14px;
                background: var(--table-bg);
                box-shadow: var(--shadow);
            }}

            .themed-table {{
                width: max-content;
                min-width: 100%;
                border-collapse: separate;
                border-spacing: 0;
                color: var(--text);
                font-size: 0.92rem;
            }}

            .themed-table thead th {{
                position: sticky;
                top: 0;
                z-index: 2;
                padding: 0.78rem 0.85rem;
                background: var(--table-header);
                color: var(--muted);
                border-bottom: 1px solid var(--border);
                border-right: 1px solid var(--border);
                font-weight: 700;
                text-align: left;
                white-space: nowrap;
            }}

            .themed-table thead th:last-child {{
                border-right: 0;
            }}

            .themed-table tbody td {{
                padding: 0.72rem 0.85rem;
                background: var(--table-bg);
                color: var(--text);
                border-bottom: 1px solid var(--border);
                border-right: 1px solid var(--border);
                vertical-align: middle;
            }}

            .themed-table tbody td:last-child {{
                border-right: 0;
            }}

            .themed-table tbody tr:last-child td {{
                border-bottom: 0;
            }}

            .themed-table tbody tr:hover td {{
                background: var(--table-hover);
            }}

            .themed-table .numeric {{
                text-align: right;
                font-variant-numeric: tabular-nums;
                white-space: nowrap;
            }}

            .themed-table .muted-cell {{
                color: var(--muted);
            }}

            .table-empty {{
                padding: 1rem;
                border: 1px solid var(--border);
                border-radius: 14px;
                background: var(--card-bg-soft);
                color: var(--muted);
            }}


            /*
             * The dashboard now has no sidebar controls, so Streamlit's
             * application chrome can be removed completely. This also removes
             * the thin white header strip at the very top of the page.
             */
            header[data-testid="stHeader"],
            [data-testid="stToolbar"],
            [data-testid="stDecoration"],
            [data-testid="stSidebar"],
            [data-testid="stSidebarCollapsedControl"],
            [data-testid="stExpandSidebarButton"],
            #MainMenu,
            footer {{
                display: none !important;
            }}

            /* Keep a small breathing space above the compact dashboard hero. */
            section.main > div.block-container {{
                padding-top: 0.45rem !important;
            }}

            /*
             * Compact summary strip used directly below the hero. It replaces
             * the larger Streamlit metric cards with lightweight tournament
             * totals that do not dominate every page.
             */
            .tournament-snapshot-heading {{
                margin: 0.32rem 0 0.16rem;
                color: var(--accent);
                font-size: 0.68rem;
                font-weight: 750;
                letter-spacing: 0.115em;
                line-height: 1.1;
                text-transform: uppercase;
            }}

            .tournament-snapshot {{
                display: grid;
                grid-template-columns: repeat(4, minmax(0, 1fr));
                gap: 0;
                margin: 0.25rem 0 0.6rem;
                overflow: hidden;
                border: 1px solid var(--border);
                border-radius: 12px;
                background: var(--card-bg);
                box-shadow: 0 4px 12px rgba(55, 25, 30, 0.04);
            }}

            .tournament-snapshot-item {{
                min-width: 0;
                padding: 0.46rem 0.7rem 0.5rem;
                border-right: 1px solid var(--border);
            }}

            .tournament-snapshot-item:last-child {{
                border-right: 0;
            }}

            .tournament-snapshot-label {{
                color: var(--muted);
                font-size: 0.62rem;
                font-weight: 750;
                letter-spacing: 0.075em;
                line-height: 1.15;
                text-transform: uppercase;
                white-space: nowrap;
            }}

            .tournament-snapshot-value {{
                margin-top: 0.14rem;
                color: var(--text);
                font-size: 1.18rem;
                font-weight: 700;
                font-variant-numeric: tabular-nums;
                line-height: 1.05;
            }}

            @media (max-width: 760px) {{
                .tournament-snapshot {{
                    grid-template-columns: repeat(2, minmax(0, 1fr));
                }}

                .tournament-snapshot-item:nth-child(2) {{
                    border-right: 0;
                }}

                .tournament-snapshot-item:nth-child(-n + 2) {{
                    border-bottom: 1px solid var(--border);
                }}
            }}

            /* Compact page rhythm: section labels, headings and controls use
             * less vertical space across Fixtures, Overall table and Teams. */
            [data-testid="stMainBlockContainer"] [data-testid="stElementContainer"] {{
                margin-bottom: 0.28rem !important;
            }}

            [data-testid="stHeading"] {{
                margin: 0.12rem 0 0.28rem !important;
            }}

            [data-testid="stHeading"] h2 {{
                margin: 0 !important;
                font-size: clamp(1.5rem, 2.3vw, 1.9rem) !important;
                line-height: 1.12 !important;
            }}

            [data-testid="stHeading"] h3 {{
                margin: 0 !important;
                font-size: clamp(1.22rem, 1.8vw, 1.55rem) !important;
                line-height: 1.16 !important;
            }}

            .section-label {{
                margin: 0.18rem 0 0.15rem !important;
                font-size: 0.7rem !important;
            }}

            .compact-control-label {{
                margin: 0.12rem 0 0.28rem;
                color: var(--text);
                font-size: 0.78rem;
                font-weight: 700;
            }}

            [data-testid="stRadio"] {{
                margin-top: 0.08rem !important;
            }}

            [data-testid="stRadio"] [role="radiogroup"] {{
                gap: 0.25rem !important;
            }}

            /* Keep team-profile KPI strips dense, but still readable. */
            [data-testid="stMetric"] {{
                min-height: 74px;
                padding: 0.52rem 0.62rem;
            }}

            [data-testid="stMetricLabel"] {{
                font-size: 0.61rem;
                letter-spacing: 0.06em;
            }}

            [data-testid="stMetricValue"] {{
                font-size: 1.22rem;
            }}

            .tournament-snapshot {{
                margin: 0.16rem 0 0.42rem;
            }}

            .tournament-snapshot-item {{
                padding: 0.38rem 0.58rem 0.42rem;
            }}

            .tournament-snapshot-value {{
                font-size: 1.04rem;
            }}


            /* Fixtures tab: compact headings and a smaller weather prompt
             * reduce vertical travel while the table can use the full page width. */
            .fixtures-section-title {{
                margin: 0.02rem 0 0.34rem;
                color: var(--text);
                font-size: clamp(1.35rem, 2vw, 1.7rem);
                font-weight: 750;
                letter-spacing: -0.028em;
                line-height: 1.1;
            }}

            .fixture-weather-prompt {{
                margin: 0.08rem 0 0;
                padding: 0.55rem 0.78rem;
                border: 1px solid #d6e1f3;
                border-radius: 10px;
                background: #edf3ff;
                color: var(--muted);
                font-size: 0.86rem;
                line-height: 1.3;
            }}

            /* The overview fixture grid should use the whole available
             * content container rather than its intrinsic dataframe width. */
            [data-testid="stDataFrame"] {{
                width: 100% !important;
            }}

            /* Overall table: preserve a strong page heading while keeping
             * the search control directly below it and close to the table. */
            .overall-table-title {{
                margin: 0 0 0.16rem;
                color: var(--text);
                font-size: clamp(1.78rem, 2.5vw, 2.25rem);
                font-weight: 750;
                letter-spacing: -0.032em;
                line-height: 1.08;
            }}

            [data-testid="stTextInput"] {{
                margin: 0 !important;
            }}

            [data-testid="stTextInput"] input {{
                min-height: 2.28rem !important;
                padding-block: 0.34rem !important;
                font-size: 0.92rem !important;
            }}

            /* Player comparison: keep advanced-metric controls and the
             * selected lollipop chart concise without making player labels
             * difficult to scan. */
            /* Venues tab: shorten the introductory header so the map and
             * weather controls appear closer to the tab navigation. */
            .venues-section-label {{
                margin: 0.08rem 0 0.04rem !important;
            }}

            .venues-title {{
                margin: 0 0 0.22rem;
                color: var(--text);
                font-size: clamp(1.25rem, 1.85vw, 1.55rem);
                font-weight: 750;
                letter-spacing: -0.024em;
                line-height: 1.08;
            }}

            .advanced-metrics-section-label {{
                margin: 0.2rem 0 0.08rem !important;
            }}

            .advanced-metrics-control-anchor {{
                display: none;
            }}

            [data-testid="stVerticalBlockBorderWrapper"]:has(.advanced-metrics-control-anchor) {{
                margin: 0.04rem 0 0.34rem !important;
                border-color: var(--border) !important;
                border-radius: 12px !important;
                background: rgba(255, 255, 255, 0.70) !important;
                box-shadow: 0 4px 12px rgba(55, 25, 30, 0.04) !important;
            }}

            [data-testid="stVerticalBlockBorderWrapper"]:has(.advanced-metrics-control-anchor) > div {{
                padding: 0.42rem 0.62rem !important;
            }}

            .advanced-metrics-control-title {{
                margin: 0.08rem 0 0.08rem;
                color: var(--text);
                font-size: 0.78rem;
                font-weight: 750;
                letter-spacing: 0.02em;
            }}

            .advanced-metrics-control-note {{
                margin: 0;
                color: var(--muted);
                font-size: 0.76rem;
                line-height: 1.25;
            }}

            .advanced-metric-chart-title {{
                margin: 0.08rem 0 0.18rem;
                color: var(--text);
                font-size: clamp(1.18rem, 1.65vw, 1.42rem);
                font-weight: 750;
                letter-spacing: -0.022em;
                line-height: 1.1;
            }}

            .advanced-metric-note {{
                margin: 0.18rem 0 0 !important;
                color: var(--muted);
                font-size: 0.76rem;
                line-height: 1.25;
            }}

            /* Compact the head-to-head chart without sacrificing the
             * two-team comparison at a glance. */
            .head-to-head-section-label {{
                margin: 0.28rem 0 0.08rem !important;
            }}

            .head-to-head-title {{
                margin: 0 0 0.28rem;
                color: var(--text);
                font-size: clamp(1.28rem, 1.9vw, 1.58rem);
                font-weight: 750;
                letter-spacing: -0.026em;
                line-height: 1.1;
            }}


            /* Teams tab: a compact, grouped selector bar keeps the view and
             * relevant team controls together instead of splitting them
             * across unrelated page columns. */
            .team-analysis-label {{
                margin: 0 0 0.08rem !important;
            }}

            .team-analysis-title {{
                margin: 0 0 0.36rem;
                color: var(--text);
                font-size: clamp(1.45rem, 2.2vw, 1.85rem);
                font-weight: 750;
                letter-spacing: -0.03em;
                line-height: 1.1;
            }}

            .team-control-anchor {{
                display: none;
            }}

            [data-testid="stVerticalBlockBorderWrapper"]:has(.team-control-anchor) {{
                margin: 0.06rem 0 0.42rem !important;
                border-color: var(--border) !important;
                border-radius: 12px !important;
                background: rgba(255, 255, 255, 0.72) !important;
                box-shadow: 0 4px 12px rgba(55, 25, 30, 0.04) !important;
            }}

            [data-testid="stVerticalBlockBorderWrapper"]:has(.team-control-anchor) > div {{
                padding: 0.52rem 0.68rem !important;
            }}

            .team-control-label {{
                margin: 0 0 0.22rem;
                color: var(--text);
                font-size: 0.76rem;
                font-weight: 700;
                letter-spacing: 0.02em;
            }}

            /* Team profile / Compare teams switch: match the compact,
             * neutral pill behaviour used by the page navigation. */
            [data-testid="stSegmentedControl"] {{
                margin: 0 !important;
            }}

            [data-testid="stSegmentedControl"] [data-baseweb="button-group"],
            [data-testid="stSegmentedControl"] [role="radiogroup"] {{
                display: flex !important;
                align-items: center !important;
                gap: 0.38rem !important;
                padding: 0 !important;
                border: 0 !important;
                background: transparent !important;
                box-shadow: none !important;
            }}

            [data-testid="stSegmentedControl"] button {{
                min-height: 2.12rem !important;
                margin: 0 !important;
                padding: 0.32rem 0.78rem !important;
                border: 1px solid transparent !important;
                border-radius: 999px !important;
                background: transparent !important;
                color: var(--muted) !important;
                font-size: 0.84rem !important;
                font-weight: 650 !important;
                line-height: 1 !important;
                box-shadow: none !important;
                transition: background 120ms ease, border-color 120ms ease,
                    color 120ms ease !important;
            }}

            [data-testid="stSegmentedControl"] button:hover {{
                background: var(--card-bg-soft) !important;
                border-color: var(--border) !important;
                color: var(--text) !important;
            }}

            [data-testid="stSegmentedControl"] button[aria-pressed="true"],
            [data-testid="stSegmentedControl"] button[aria-checked="true"],
            [data-testid="stSegmentedControl"] button[data-active="true"],
            [data-testid="stSegmentedControl"] button[data-checked="true"] {{
                background: rgba(32, 36, 43, 0.86) !important;
                border-color: transparent !important;
                color: #ffffff !important;
                box-shadow: none !important;
            }}

            [data-testid="stSegmentedControl"] button[aria-pressed="true"] *,
            [data-testid="stSegmentedControl"] button[aria-checked="true"] *,
            [data-testid="stSegmentedControl"] button[data-active="true"] *,
            [data-testid="stSegmentedControl"] button[data-checked="true"] * {{
                color: #ffffff !important;
                fill: #ffffff !important;
            }}

            .team-snapshot-grid {{
                display: grid;
                grid-template-columns: repeat(6, minmax(0, 1fr));
                gap: 0.42rem;
                margin: 0.06rem 0 0.46rem;
            }}

            .team-snapshot-card {{
                display: flex;
                flex-direction: column;
                justify-content: center;
                min-height: 64px;
                padding: 0.46rem 0.68rem;
                border: 1px solid var(--border);
                border-radius: 12px;
                background: var(--card-bg);
                box-shadow: 0 4px 11px rgba(55, 25, 30, 0.045);
            }}

            .team-snapshot-card-label {{
                color: var(--muted);
                font-size: 0.61rem;
                font-weight: 750;
                letter-spacing: 0.065em;
                line-height: 1.08;
                text-transform: uppercase;
            }}

            .team-snapshot-card-value {{
                margin-top: 0.26rem;
                color: var(--text);
                font-size: 1.13rem;
                font-weight: 700;
                font-variant-numeric: tabular-nums;
                line-height: 1.05;
            }}

            @media (max-width: 1100px) {{
                .team-snapshot-grid {{
                    grid-template-columns: repeat(3, minmax(0, 1fr));
                }}
            }}

            @media (max-width: 640px) {{
                .team-snapshot-grid {{
                    grid-template-columns: repeat(2, minmax(0, 1fr));
                }}
            }}

            /* Squad profile: keep the heading close to the player table and
             * let the table scroll rather than occupying a large page block. */
            .squad-profile-header {{
                margin: 0.12rem 0 0.28rem;
            }}

            .squad-profile-kicker {{
                color: var(--accent);
                font-size: 0.68rem;
                font-weight: 700;
                letter-spacing: 0.12em;
                line-height: 1.1;
                text-transform: uppercase;
            }}

            .squad-profile-title-row {{
                display: flex;
                align-items: baseline;
                gap: 0.5rem;
                margin-top: 0.12rem;
            }}

            .squad-profile-title {{
                color: var(--text);
                font-size: clamp(1.2rem, 1.75vw, 1.45rem);
                font-weight: 750;
                letter-spacing: -0.025em;
                line-height: 1.1;
            }}

            .squad-profile-count {{
                color: var(--muted);
                font-size: 0.78rem;
                line-height: 1.1;
            }}

            /* Team finishing: compact calculation strip and lower-profile chart
             * shared by the single-team profile and comparison views. */
            .team-finishing-title {{
                margin: 0 0 0.24rem;
                color: var(--text);
                font-size: clamp(1.24rem, 1.85vw, 1.52rem);
                font-weight: 750;
                letter-spacing: -0.026em;
                line-height: 1.12;
            }}

            .team-finishing-summary {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                gap: 0.42rem;
                margin: 0.03rem 0 0.26rem;
            }}

            .team-finishing-summary-card {{
                display: grid;
                grid-template-columns: minmax(0, 1fr) auto;
                align-items: center;
                gap: 0.65rem;
                min-height: 58px;
                padding: 0.40rem 0.62rem;
                border: 1px solid var(--border);
                border-left: 3px solid var(--team-accent);
                border-radius: 10px;
                background: var(--card-bg);
                box-shadow: 0 3px 9px rgba(55, 25, 30, 0.04);
            }}

            .team-finishing-card-team {{
                display: flex;
                align-items: center;
                gap: 0.34rem;
                color: var(--text);
                font-size: 0.76rem;
                font-weight: 750;
                line-height: 1.08;
            }}

            .team-finishing-card-dot {{
                width: 0.48rem;
                height: 0.48rem;
                flex: 0 0 0.48rem;
                border-radius: 50%;
                background: var(--team-accent);
            }}

            .team-finishing-card-detail {{
                margin-top: 0.16rem;
                color: var(--muted);
                font-size: 0.72rem;
                line-height: 1.2;
            }}

            .team-finishing-card-value {{
                color: var(--text);
                font-size: 1.18rem;
                font-weight: 750;
                font-variant-numeric: tabular-nums;
                line-height: 1;
                white-space: nowrap;
            }}

            .team-finishing-note,
            .team-finishing-chart-note {{
                color: var(--muted);
                font-size: 0.76rem;
                line-height: 1.28;
            }}

            .team-finishing-note {{
                margin: 0.02rem 0 0.34rem;
            }}

            .team-finishing-chart-note {{
                margin: 0.26rem 0 0.08rem;
            }}

            @media (max-width: 640px) {{
                .team-finishing-summary {{
                    grid-template-columns: 1fr;
                }}
            }}


            /* Goals-minus-xG ranking: the default view is a focused, compact
             * neighbourhood around the active teams; the complete tournament
             * ranking remains available in a collapsed expander. */
            .goals-xg-ranking-title {{
                margin: 0 0 0.2rem;
                color: var(--text);
                font-size: clamp(1.18rem, 1.75vw, 1.45rem);
                font-weight: 750;
                letter-spacing: -0.024em;
                line-height: 1.12;
            }}

            .goals-xg-ranking-note {{
                margin: 0.22rem 0 0.12rem;
                color: var(--muted);
                font-size: 0.75rem;
                line-height: 1.3;
            }}

            [data-testid="stExpander"]:has(.full-goals-xg-ranking-anchor) {{
                margin-top: 0.22rem !important;
                box-shadow: none !important;
            }}

            .full-goals-xg-ranking-anchor {{
                display: none;
            }}


        </style>
        """,
        unsafe_allow_html=True,
    )


inject_theme_css(theme)



# -----------------------------------------------------------------------------
# Data loading and transformation
# -----------------------------------------------------------------------------
DATA_DIR = Path(__file__).parent / "data"

REQUIRED_FILES = [
    "matches_detailed.csv",
    "teams.csv",
    "venues.csv",
    "squads_and_players.csv",
    "match_events.csv",
    "player_tournament_stats.csv",
]

# The two player files use slightly different team naming conventions.
# Convert known variants to one stable join key before merging them.
TEAM_NAME_ALIASES = {
    "bosnia herz": "bosnia and herzegovina",
    "bosnia and herzegovina": "bosnia and herzegovina",
    "congo dr": "democratic republic of the congo",
    "dr congo": "democratic republic of the congo",
    "democratic republic of congo": "democratic republic of the congo",
    "democratic republic of the congo": "democratic republic of the congo",
    "ir iran": "iran",
    "iran": "iran",
    "korea republic": "south korea",
    "south korea": "south korea",
    "republic of korea": "south korea",
    "turkiye": "turkey",
    "turkey": "turkey",
    "united states": "united states",
    "usa": "united states",
    "us": "united states",
    "cote d ivoire": "ivory coast",
    "ivory coast": "ivory coast",
}


def normalise_join_text(value: object) -> str:
    """Return a lower-case, accent-free key containing only word characters."""
    if pd.isna(value):
        return ""

    text = unicodedata.normalize("NFKD", str(value).casefold())
    text = "".join(
        character
        for character in text
        if not unicodedata.combining(character)
    )
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def make_team_join_key(value: object) -> str:
    """Normalise a team name and map known naming variants together."""
    normalised = normalise_join_text(value)
    return TEAM_NAME_ALIASES.get(normalised, normalised)


def make_player_full_key(value: object) -> str:
    """Build a conservative full-name key for player-profile matching."""
    return normalise_join_text(value)


def make_player_short_key(value: object) -> str:
    """
    Build a first-and-last-name fallback key.

    The detailed file often omits middle names used by the scenario profile
    file, so this is used only after a full-name match has been attempted.
    """
    name_parts = normalise_join_text(value).split()

    if len(name_parts) < 2:
        return " ".join(name_parts)

    return f"{name_parts[0]} {name_parts[-1]}"


@st.cache_data
def load_data(
    data_dir: Path,
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
]:
    """Read CSV files and make their data types analysis-ready."""
    matches = pd.read_csv(data_dir / "matches_detailed.csv")
    teams = pd.read_csv(data_dir / "teams.csv")
    venues = pd.read_csv(data_dir / "venues.csv")
    players = pd.read_csv(data_dir / "squads_and_players.csv")
    match_events = pd.read_csv(data_dir / "match_events.csv")
    detailed_player_stats = pd.read_csv(
        data_dir / "player_tournament_stats.csv"
    )

    matches["date"] = pd.to_datetime(matches["date"], errors="coerce")

    for column in ["home_score", "away_score", "home_xg", "away_xg"]:
        matches[column] = pd.to_numeric(matches[column], errors="coerce")

    matches["kickoff_utc"] = pd.to_datetime(
        matches["date"].dt.strftime("%Y-%m-%d")
        + " "
        + matches["kickoff_time_utc"],
        errors="coerce",
        utc=True,
    )

    matches["kickoff_uk"] = matches["kickoff_utc"].dt.tz_convert(
        "Europe/London"
    )

    for column in ["latitude", "longitude", "capacity", "elevation_meters"]:
        venues[column] = pd.to_numeric(venues[column], errors="coerce")

    for column in ["market_value_eur", "caps", "height_cm", "goals"]:
        players[column] = pd.to_numeric(players[column], errors="coerce")

    for column in ["event_id", "match_id", "minute", "team_id", "player_id"]:
        match_events[column] = pd.to_numeric(
            match_events[column],
            errors="coerce",
        )

    # Every detailed-stat column apart from player/team/profile text is numeric.
    detailed_text_columns = {
        "player",
        "team",
        "team_country",
        "position",
        "age",
        "club",
    }

    for column in detailed_player_stats.columns:
        if column not in detailed_text_columns:
            detailed_player_stats[column] = pd.to_numeric(
                detailed_player_stats[column],
                errors="coerce",
            )

    group_lookup = teams[["team_name", "group_letter"]].rename(
        columns={"team_name": "home_team_name"}
    )

    matches = matches.merge(
        group_lookup,
        on="home_team_name",
        how="left",
    )

    return (
        matches,
        teams,
        venues,
        players,
        match_events,
        detailed_player_stats,
    )


def build_team_stats(
    matches: pd.DataFrame,
    teams: pd.DataFrame,
) -> pd.DataFrame:
    """Convert completed fixture rows into one standings row per team."""
    completed = matches.loc[matches["status"].eq("Completed")].copy()

    base = teams[
        ["team_name", "group_letter", "confederation", "elo_rating"]
    ].drop_duplicates()

    numeric_columns = [
        "played",
        "won",
        "drawn",
        "lost",
        "goals_for",
        "goals_against",
        "xg_for",
        "xg_against",
        "points",
        "goal_difference",
        "xg_difference",
    ]

    if completed.empty:
        for column in numeric_columns:
            base[column] = 0

        return base

    home = completed[
        ["home_team_name", "home_score", "away_score", "home_xg", "away_xg"]
    ].rename(
        columns={
            "home_team_name": "team_name",
            "home_score": "goals_for",
            "away_score": "goals_against",
            "home_xg": "xg_for",
            "away_xg": "xg_against",
        }
    )

    away = completed[
        ["away_team_name", "away_score", "home_score", "away_xg", "home_xg"]
    ].rename(
        columns={
            "away_team_name": "team_name",
            "away_score": "goals_for",
            "home_score": "goals_against",
            "away_xg": "xg_for",
            "home_xg": "xg_against",
        }
    )

    team_matches = pd.concat([home, away], ignore_index=True)

    team_matches["played"] = 1

    team_matches["won"] = (
        team_matches["goals_for"] > team_matches["goals_against"]
    ).astype(int)

    team_matches["drawn"] = (
        team_matches["goals_for"] == team_matches["goals_against"]
    ).astype(int)

    team_matches["lost"] = (
        team_matches["goals_for"] < team_matches["goals_against"]
    ).astype(int)

    stats = (
        team_matches.groupby("team_name", as_index=False)
        .agg(
            played=("played", "sum"),
            won=("won", "sum"),
            drawn=("drawn", "sum"),
            lost=("lost", "sum"),
            goals_for=("goals_for", "sum"),
            goals_against=("goals_against", "sum"),
            xg_for=("xg_for", "sum"),
            xg_against=("xg_against", "sum"),
        )
    )

    stats["points"] = stats["won"] * 3 + stats["drawn"]
    stats["goal_difference"] = (
        stats["goals_for"] - stats["goals_against"]
    )
    stats["xg_difference"] = stats["xg_for"] - stats["xg_against"]

    result = base.merge(stats, on="team_name", how="left")
    result[numeric_columns] = result[numeric_columns].fillna(0)

    return result

def build_player_tournament_stats(
    players: pd.DataFrame,
    teams: pd.DataFrame,
    match_events: pd.DataFrame,
    detailed_player_stats: pd.DataFrame,
    active_match_ids: list[int],
) -> pd.DataFrame:
    """
    Build one detailed tournament-statistics row per player.

    `player_tournament_stats.csv` is the primary source for appearances,
    minutes, attacking, defensive, discipline and goalkeeper figures.
    `squads_and_players.csv` is retained for player IDs and career profile
    fields, which are matched by team plus player name.

    The detailed file is an all-tournament snapshot. Only its team selection
    follows the sidebar group filter; its totals are not recalculated from a
    date or match-status subset. Recorded event totals below still respect the
    active fixture filters.
    """
    team_lookup = teams[
        ["team_id", "team_name"]
    ].drop_duplicates().copy()

    team_lookup["team_join_key"] = team_lookup["team_name"].map(
        make_team_join_key
    )

    team_lookup = team_lookup.drop_duplicates(
        subset="team_join_key",
        keep="first",
    )

    # -------------------------------------------------------------------------
    # Detailed tournament-statistics file: this is the base table.
    # -------------------------------------------------------------------------
    player_stats = detailed_player_stats.rename(
        columns={
            "player": "player_name",
            "team": "source_team_name",
            "club": "club_team",
        }
    ).copy()

    player_stats["team_join_key"] = player_stats["source_team_name"].map(
        make_team_join_key
    )

    player_stats = player_stats.merge(
        team_lookup,
        on="team_join_key",
        how="left",
    )

    # Preserve the dashboard's team spelling whenever it is available, so
    # chart labels and group filtering remain consistent across the app.
    player_stats["team_name"] = player_stats["team_name"].fillna(
        player_stats["source_team_name"]
    )

    player_stats["player_full_key"] = player_stats["player_name"].map(
        make_player_full_key
    )
    player_stats["player_short_key"] = player_stats["player_name"].map(
        make_player_short_key
    )
    player_stats["player_key"] = (
        player_stats["team_join_key"]
        + "::"
        + player_stats["player_full_key"]
    )

    # -------------------------------------------------------------------------
    # Scenario player profiles: used only for career/profile information and
    # for the player_id required by match-events records.
    # -------------------------------------------------------------------------
    profile_columns = [
        "player_id",
        "career_caps",
        "career_international_goals",
        "height_cm",
        "market_value_eur",
        "profile_club_team",
        "profile_player_name",
    ]

    player_profiles = players.merge(
        team_lookup[["team_id", "team_name", "team_join_key"]],
        on="team_id",
        how="left",
    ).copy()

    player_profiles = player_profiles.rename(
        columns={
            "player_name": "profile_player_name",
            "goals": "career_international_goals",
            "caps": "career_caps",
            "club_team": "profile_club_team",
        }
    )

    for column in [
        "career_caps",
        "career_international_goals",
        "height_cm",
        "market_value_eur",
    ]:
        player_profiles[column] = pd.to_numeric(
            player_profiles[column],
            errors="coerce",
        )

    player_profiles["player_full_key"] = (
        player_profiles["profile_player_name"].map(make_player_full_key)
    )
    player_profiles["player_short_key"] = (
        player_profiles["profile_player_name"].map(make_player_short_key)
    )

    # First use a strict full-name match. Drop ambiguous keys rather than
    # guessing, which avoids attaching a player ID to the wrong person.
    full_name_profiles = player_profiles[
        [
            "team_join_key",
            "player_full_key",
            *profile_columns,
        ]
    ].drop_duplicates(
        subset=["team_join_key", "player_full_key"],
        keep=False,
    )

    player_stats = player_stats.merge(
        full_name_profiles,
        on=["team_join_key", "player_full_key"],
        how="left",
    )

    # A safe fallback catches full names such as "Harry Edward Kane" in the
    # scenario profile versus "Harry Kane" in the detailed dataset. It is only
    # used where a first-and-last key occurs once within the same team.
    short_name_profiles = player_profiles[
        [
            "team_join_key",
            "player_short_key",
            *profile_columns,
        ]
    ].drop_duplicates(
        subset=["team_join_key", "player_short_key"],
        keep=False,
    )

    fallback_profiles = player_stats[
        ["team_join_key", "player_short_key"]
    ].merge(
        short_name_profiles,
        on=["team_join_key", "player_short_key"],
        how="left",
    )

    for column in profile_columns:
        player_stats[column] = player_stats[column].combine_first(
            fallback_profiles[column]
        )

    player_stats["goals_per_cap"] = (
        player_stats["career_international_goals"]
        / player_stats["career_caps"].replace(0, pd.NA)
    ).fillna(0)

    player_stats["market_value_millions"] = (
        player_stats["market_value_eur"].fillna(0) / 1_000_000
    )

    # -------------------------------------------------------------------------
    # Event data remains useful for the expandable match log. These fields are
    # deliberately named "filtered_*" so they are not confused with detailed
    # all-tournament totals from the new CSV.
    # -------------------------------------------------------------------------
    relevant_events = match_events.loc[
        match_events["match_id"].isin(active_match_ids)
        & match_events["event_type"].isin(
            [
                "Goal",
                "Yellow Card",
                "Red Card",
            ]
        )
    ].copy()

    event_columns = [
        "player_id",
        "filtered_event_goals",
        "filtered_yellow_cards",
        "filtered_red_cards",
    ]

    event_counts = pd.DataFrame(columns=event_columns)

    if not relevant_events.empty:
        event_counts = (
            relevant_events.groupby(
                ["player_id", "event_type"]
            )["event_id"]
            .count()
            .unstack(fill_value=0)
            .reset_index()
            .rename(
                columns={
                    "Goal": "filtered_event_goals",
                    "Yellow Card": "filtered_yellow_cards",
                    "Red Card": "filtered_red_cards",
                }
            )
        )

        for column in event_columns:
            if column not in event_counts.columns:
                event_counts[column] = 0

        event_counts = event_counts[event_columns]

    goal_minutes = pd.DataFrame(
        {
            "player_id": pd.Series(dtype="int64"),
            "goal_minutes": pd.Series(dtype="object"),
        }
    )

    if not relevant_events.empty:
        goal_events = relevant_events.loc[
            relevant_events["event_type"].eq("Goal")
        ].copy()

        if not goal_events.empty:
            goal_minutes = (
                goal_events.groupby("player_id")["minute"]
                .apply(
                    lambda minutes: ", ".join(
                        f"{int(minute)}'"
                        for minute in sorted(minutes)
                        if pd.notna(minute)
                    )
                )
                .reset_index(name="goal_minutes")
            )

    player_stats = player_stats.merge(
        event_counts,
        on="player_id",
        how="left",
    )

    player_stats = player_stats.merge(
        goal_minutes,
        on="player_id",
        how="left",
    )

    for column in [
        "filtered_event_goals",
        "filtered_yellow_cards",
        "filtered_red_cards",
    ]:
        player_stats[column] = (
            pd.to_numeric(player_stats[column], errors="coerce")
            .fillna(0)
            .astype(int)
        )

    player_stats["goal_minutes"] = (
        player_stats["goal_minutes"].fillna("—")
    )

    # Keep numeric chart fields consistent when a player did not record a
    # particular type of action. Career-profile fields remain NaN if no
    # reliable profile match was found, so the interface can show a dash.
    numeric_stat_columns = [
        column
        for column in detailed_player_stats.columns
        if column
        not in {
            "player",
            "team",
            "team_country",
            "position",
            "age",
            "club",
        }
    ]

    for column in numeric_stat_columns:
        if column in player_stats.columns:
            player_stats[column] = pd.to_numeric(
                player_stats[column],
                errors="coerce",
            ).fillna(0)

    player_stats["club_team"] = player_stats["club_team"].fillna(
        player_stats["profile_club_team"]
    ).fillna("—")

    player_stats["player_label"] = (
        player_stats["player_name"].fillna("Unknown player")
        + " — "
        + player_stats["team_name"].fillna("Unknown team")
        + " ("
        + player_stats["position"].fillna("Unknown position")
        + ")"
    )

    return player_stats.sort_values(
        ["team_name", "player_name"]
    ).reset_index(drop=True)


def make_fixture_table(matches: pd.DataFrame) -> pd.DataFrame:
    """Make a compact, chronologically ordered fixture/results table."""
    table = matches.copy()

    table["kickoff (UK)"] = table["kickoff_uk"].dt.strftime(
        "%a %d %b, %H:%M"
    )

    table["fixture"] = (
        table["home_team_name"] + " v " + table["away_team_name"]
    )

    table["score"] = table.apply(
        lambda row: (
            f"{int(row['home_score'])}–{int(row['away_score'])}"
            if pd.notna(row["home_score"])
            and pd.notna(row["away_score"])
            else "–"
        ),
        axis=1,
    )

    table["xG"] = table.apply(
        lambda row: (
            f"{row['home_xg']:.2f}–{row['away_xg']:.2f}"
            if pd.notna(row["home_xg"])
            and pd.notna(row["away_xg"])
            else "–"
        ),
        axis=1,
    )

    table = (
        table[
            [
                "kickoff_uk",
                "kickoff (UK)",
                "fixture",
                "score",
                "xG",
                "status",
                "group_letter",
                "stadium_name",
                "city",
                "referee_name",
            ]
        ]
        .sort_values("kickoff_uk")
        .reset_index(drop=True)
        .drop(columns="kickoff_uk")
    )

    table.index = pd.Index([""] * len(table))

    return table


def style_chart(figure, active_theme: dict[str, str]):
    """Apply a consistent light or dark Plotly chart style."""
    figure.update_layout(
        template="plotly_white",
        paper_bgcolor=active_theme["chart_bg"],
        plot_bgcolor=active_theme["chart_bg"],
        font={
            "color": active_theme["text"],
            "family": "Arial, sans-serif",
        },
        hoverlabel={
            "bgcolor": active_theme["card_bg"],
            "bordercolor": active_theme["border"],
            "font": {"color": active_theme["text"]},
        },
        margin={"l": 24, "r": 24, "t": 24, "b": 24},
        showlegend=False,
    )

    figure.update_xaxes(
        showgrid=False,
        zeroline=False,
        linecolor=active_theme["border"],
        tickfont={"color": active_theme["muted"]},
        title_font={"color": active_theme["muted"]},
    )

    figure.update_yaxes(
        gridcolor=active_theme["grid"],
        zeroline=False,
        linecolor=active_theme["border"],
        tickfont={"color": active_theme["muted"]},
        title_font={"color": active_theme["muted"]},
    )

    return figure

# -----------------------------------------------------------------------------
# Custom selector helper
# -----------------------------------------------------------------------------
def themed_selectbox(
    label: str,
    options,
    *,
    key: str,
    format_func=None,
    help_text: str | None = None,
    search_placeholder: str = "Filter options",
    compact_label: bool = False,
) -> object:
    """Render a compact native selectbox that opens as an overlay menu.

    Unlike the previous expander-and-radio implementation, Streamlit's native
    selectbox opens its options in a floating portal. This means opening a
    menu does not change the page layout or push charts and other content
    downward.
    """
    option_list = list(options)

    if not option_list:
        st.markdown(f"**{label}**")
        st.info("No options are available.")
        return None

    if format_func is None:
        format_func = lambda value: str(value)

    current_value = st.session_state.get(key)
    if current_value not in option_list:
        current_value = option_list[0]
        st.session_state[key] = current_value

    # Remove state created by the legacy expander/radio selector. It is no
    # longer used now that controls open as floating dropdown menus.
    st.session_state.pop(f"{key}__search", None)
    st.session_state.pop(f"{key}__radio", None)

    label_class = "selector-field-label"
    if compact_label:
        label_class += " compact-selector-field-label"

    st.markdown(
        f'<div class="{label_class}">{escape(label)}</div>',
        unsafe_allow_html=True,
    )

    if help_text:
        st.caption(help_text)

    return st.selectbox(
        label,
        option_list,
        index=option_list.index(current_value),
        format_func=format_func,
        key=key,
        label_visibility="collapsed",
    )


def _normalize_label(value: object) -> str:
    """Normalize a label for case-insensitive, accent-insensitive matching."""
    text = str(value).casefold()
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(
        char for char in normalized if not unicodedata.combining(char)
    )


def pick_option_by_label(
    options: list[object],
    desired_label: str,
    label_func,
) -> object | None:
    """Return the first option whose rendered label matches the target."""
    target = _normalize_label(desired_label)

    for option in options:
        if _normalize_label(label_func(option)) == target:
            return option

    return None

def themed_dataframe(
    data: pd.DataFrame,
    *,
    height: int | None = None,
    column_config: dict | None = None,
    width: str | None = None,
    hide_index: bool = False,
    **kwargs: object,
) -> None:
    if data.empty:
        st.markdown(
            '<div class="table-empty">No rows match the current filters.</div>',
            unsafe_allow_html=True,
        )
        return

    display_height = int(height) if height is not None else min(
        680,
        max(180, 54 + min(len(data), 12) * 45),
    )

    use_container_width = width == "stretch"
    return st.dataframe(
        data,
        height=display_height,
        hide_index=hide_index,
        column_config=column_config,
        use_container_width=use_container_width,
        **kwargs,
    )


# -----------------------------------------------------------------------------
# Team comparison helpers
# -----------------------------------------------------------------------------
def summarise_squad(squad: pd.DataFrame) -> dict[str, float]:
    """
    Calculate useful squad-level totals for one national team.

    Input:
        squad: all player rows for one team.

    Output:
        A dictionary containing squad size, average caps, total international
        goals and total dataset market value.
    """
    if squad.empty:
        return {
            "squad_size": 0,
            "average_caps": 0.0,
            "international_goals": 0,
            "market_value": 0.0,
        }

    return {
        "squad_size": int(len(squad)),
        "average_caps": float(squad["caps"].fillna(0).mean()),
        "international_goals": int(squad["goals"].fillna(0).sum()),
        "market_value": float(
            squad["market_value_eur"].fillna(0).sum()
        ),
    }


def format_euro_millions(value: float) -> str:
    """Format a large euro amount into a shorter value such as €425.3m."""
    return f"€{value / 1_000_000:.1f}m"


def get_highlighted_team_colours(
    highlighted_teams: list[str],
    active_theme: dict[str, str],
) -> dict[str, str]:
    """Return the dashboard colour assigned to each selected team."""
    colours = {}

    if len(highlighted_teams) >= 1:
        colours[highlighted_teams[0]] = active_theme["comparison_team_a"]

    if len(highlighted_teams) >= 2:
        colours[highlighted_teams[1]] = active_theme["comparison_team_b"]

    return colours



def render_team_finishing_summary(
    team_rows: list[tuple[str, pd.Series, str]],
) -> None:
    """Render concise goals-minus-xG cards for one or two selected teams."""
    summary_cards = []

    for team_name, team_row, team_colour in team_rows:
        played = int(team_row["played"])

        if played > 0:
            goals_scored = int(team_row["goals_for"])
            expected_goals = float(team_row["xg_for"])
            goal_delta = goals_scored - expected_goals
            value = f"{goal_delta:+.2f}"
            detail = f"{goals_scored} goals from {expected_goals:.2f} xG"
        else:
            value = "—"
            detail = "No completed matches"

        summary_cards.append(
            (
                '<div class="team-finishing-summary-card" '
                f'style="--team-accent: {team_colour};">'
                '<div>'
                '<div class="team-finishing-card-team">'
                '<span class="team-finishing-card-dot"></span>'
                f'{escape(str(team_name))}: goals minus xG'
                '</div>'
                '<div class="team-finishing-card-detail">'
                f'{escape(detail)}'
                '</div>'
                '</div>'
                '<div class="team-finishing-card-value">'
                f'{escape(value)}'
                '</div>'
                '</div>'
            )
        )

    st.markdown(
        '<div class="team-finishing-summary">'
        f'{"".join(summary_cards)}'
        '</div>'
        '<div class="team-finishing-note">'
        'Positive means the team has scored more than expected; negative '
        'means it has scored fewer.'
        '</div>',
        unsafe_allow_html=True,
    )


def create_team_finishing_chart(
    team_stats: pd.DataFrame,
    highlighted_teams: list[str],
    active_theme: dict[str, str],
):
    """
    Create a goals-versus-xG scatter chart.

    Background teams are subtle and fixed in size so the selected teams
    remain the visual focus.
    """
    chart_data = team_stats.loc[
        team_stats["played"].gt(0)
    ].copy()

    if chart_data.empty:
        return None

    chart_data["goal_delta"] = (
        chart_data["goals_for"] - chart_data["xg_for"]
    )

    maximum = max(
        float(chart_data["xg_for"].max()),
        float(chart_data["goals_for"].max()),
    ) + 0.5

    highlighted_colours = get_highlighted_team_colours(
        highlighted_teams,
        active_theme,
    )

    other_teams = chart_data.loc[
        ~chart_data["team_name"].isin(highlighted_teams)
    ].copy()

    figure = go.Figure()

    # Background teams use a fixed, smaller marker size. This keeps crowded
    # areas around low xG and low goals easier to read.
    if not other_teams.empty:
        figure.add_trace(
            go.Scatter(
                x=other_teams["xg_for"],
                y=other_teams["goals_for"],
                mode="markers",
                hovertext=other_teams["team_name"],
                customdata=other_teams[
                    [
                        "played",
                        "goal_delta",
                        "points",
                    ]
                ].to_numpy(),
                marker={
                    "size": 13,
                    "color": active_theme["muted"],
                    "opacity": 0.20,
                    "line": {
                        "color": active_theme["card_bg"],
                        "width": 1,
                    },
                },
                hovertemplate=(
                    "<b>%{hovertext}</b><br>"
                    "xG: %{x:.2f}<br>"
                    "Goals: %{y}<br>"
                    "Matches played: %{customdata[0]}<br>"
                    "Goals minus xG: %{customdata[1]:+.2f}<br>"
                    "Points: %{customdata[2]}"
                    "<extra></extra>"
                ),
                name="Other teams",
            )
        )

    # Selected teams remain large, clearly outlined and labelled.
    for team_name, team_colour in highlighted_colours.items():
        selected_team_data = chart_data.loc[
            chart_data["team_name"].eq(team_name)
        ].copy()

        if selected_team_data.empty:
            continue

        goals_scored = float(
            selected_team_data["goals_for"].iloc[0]
        )

        # Keep labels above points except when a point is very close to the
        # top boundary, where the label is placed below instead.
        label_position = (
            "bottom center"
            if goals_scored >= maximum - 0.8
            else "top center"
        )

        figure.add_trace(
            go.Scatter(
                x=selected_team_data["xg_for"],
                y=selected_team_data["goals_for"],
                mode="markers+text",
                text=selected_team_data["team_name"],
                textposition=label_position,
                textfont={
                    "color": active_theme["text"],
                    "size": 13,
                },
                hovertext=selected_team_data["team_name"],
                customdata=selected_team_data[
                    [
                        "played",
                        "goal_delta",
                        "points",
                    ]
                ].to_numpy(),
                marker={
                    "size": 40,
                    "color": team_colour,
                    "opacity": 1,
                    "line": {
                        "color": active_theme["text"],
                        "width": 2,
                    },
                },
                cliponaxis=False,
                hovertemplate=(
                    "<b>%{hovertext}</b><br>"
                    "xG: %{x:.2f}<br>"
                    "Goals: %{y}<br>"
                    "Matches played: %{customdata[0]}<br>"
                    "Goals minus xG: %{customdata[1]:+.2f}<br>"
                    "Points: %{customdata[2]}"
                    "<extra></extra>"
                ),
                name=team_name,
            )
        )

    # This line represents a team scoring exactly in line with its xG.
    figure.add_shape(
        type="line",
        x0=0,
        y0=0,
        x1=maximum,
        y1=maximum,
        layer="below",
        line={
            "dash": "dash",
            "color": active_theme["muted"],
            "width": 1.5,
        },
    )

    figure = style_chart(figure, active_theme)

    figure.update_layout(
        height=305,
        hovermode="closest",
        margin={"l": 18, "r": 18, "t": 12, "b": 18},
    )

    # Matching numerical ranges make the equality line easy to interpret,
    # while preserving the dashboard's full-width layout.
    figure.update_xaxes(
        title="Expected goals (xG)",
        range=[0, maximum],
        dtick=1,
    )

    figure.update_yaxes(
        title="Goals scored",
        range=[0, maximum],
        dtick=1,
    )

    return figure


def create_goals_minus_xg_chart(
    team_stats: pd.DataFrame,
    highlighted_teams: list[str],
    active_theme: dict[str, str],
    *,
    compact: bool = False,
):
    """Create a goals-minus-xG ranking with selected teams emphasised.

    In compact mode, only the selected team or teams and their nearby ranking
    neighbours are shown. This preserves context while avoiding a very tall
    full-tournament chart. The full ranking can still be opened on demand.
    """
    ranking_data = team_stats.loc[
        team_stats["played"].gt(0)
    ].copy()

    if ranking_data.empty:
        return None

    ranking_data["goal_delta"] = (
        ranking_data["goals_for"] - ranking_data["xg_for"]
    )

    # Ascending data places underperforming teams at the bottom and teams that
    # have scored above xG at the top of the horizontal ranking.
    ranking_data = (
        ranking_data.sort_values("goal_delta", ascending=True)
        .reset_index(drop=True)
    )

    chart_data = ranking_data.copy()

    if compact and highlighted_teams:
        # Keep a small neighbourhood around each active team. Two selected
        # teams may be far apart, so the union is retained rather than hiding
        # either team's immediate context.
        context_each_side = 4 if len(highlighted_teams) == 1 else 3
        visible_positions: set[int] = set()

        for team_name in highlighted_teams:
            matching_positions = ranking_data.index[
                ranking_data["team_name"].eq(team_name)
            ].tolist()

            for position in matching_positions:
                lower_bound = max(0, position - context_each_side)
                upper_bound = min(
                    len(ranking_data),
                    position + context_each_side + 1,
                )
                visible_positions.update(range(lower_bound, upper_bound))

        if visible_positions:
            chart_data = ranking_data.iloc[
                sorted(visible_positions)
            ].copy()

    highlighted_colours = get_highlighted_team_colours(
        highlighted_teams,
        active_theme,
    )

    other_teams = chart_data.loc[
        ~chart_data["team_name"].isin(highlighted_teams)
    ].copy()

    selected_teams = chart_data.loc[
        chart_data["team_name"].isin(highlighted_teams)
    ].copy()

    muted_hex = active_theme["muted"].lstrip("#")
    muted_bar_colour = (
        f"rgba("
        f"{int(muted_hex[0:2], 16)}, "
        f"{int(muted_hex[2:4], 16)}, "
        f"{int(muted_hex[4:6], 16)}, 0.23)"
    )

    figure = go.Figure()

    # Context bars deliberately stay slim and muted. This creates room for the
    # chosen team bars to become visibly taller and more prominent.
    if not other_teams.empty:
        figure.add_trace(
            go.Bar(
                x=other_teams["goal_delta"],
                y=other_teams["team_name"],
                orientation="h",
                width=0.48,
                customdata=other_teams[
                    ["goals_for", "xg_for", "played"]
                ].to_numpy(),
                marker={
                    "color": muted_bar_colour,
                    "line": {
                        "color": active_theme["card_bg"],
                        "width": 0,
                    },
                },
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Goals minus xG: %{x:+.2f}<br>"
                    "Goals scored: %{customdata[0]}<br>"
                    "Expected goals: %{customdata[1]:.2f}<br>"
                    "Matches played: %{customdata[2]}"
                    "<extra></extra>"
                ),
                name="Other teams",
            )
        )

    # Draw each selected team separately so it can use its own colour, a thick
    # outline and a substantially taller bar. The value label makes teams that
    # sit close to zero, such as England in the screenshot, easy to spot.
    for team_name, team_colour in highlighted_colours.items():
        selected_team = selected_teams.loc[
            selected_teams["team_name"].eq(team_name)
        ]

        if selected_team.empty:
            continue

        figure.add_trace(
            go.Bar(
                x=selected_team["goal_delta"],
                y=selected_team["team_name"],
                orientation="h",
                width=0.88,
                customdata=selected_team[
                    ["goals_for", "xg_for", "played"]
                ].to_numpy(),
                marker={
                    "color": team_colour,
                    "line": {
                        "color": active_theme["text"],
                        "width": 1.35,
                    },
                },
                text=[
                    f"{float(value):+.2f}"
                    for value in selected_team["goal_delta"]
                ],
                textposition="outside",
                textfont={
                    "color": active_theme["text"],
                    "size": 12,
                },
                cliponaxis=False,
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Goals minus xG: %{x:+.2f}<br>"
                    "Goals scored: %{customdata[0]}<br>"
                    "Expected goals: %{customdata[1]:.2f}<br>"
                    "Matches played: %{customdata[2]}"
                    "<extra></extra>"
                ),
                name=team_name,
            )
        )

    # The vertical zero line separates overperformance from underperformance.
    figure.add_shape(
        type="line",
        x0=0,
        x1=0,
        y0=0,
        y1=1,
        xref="x",
        yref="paper",
        layer="below",
        line={
            "color": active_theme["text"],
            "width": 1.2,
        },
    )

    figure = style_chart(figure, active_theme)

    if compact:
        chart_height = max(
            260,
            min(400, len(chart_data) * 22 + 88),
        )
        top_margin = 12
        bottom_margin = 34
    else:
        chart_height = max(
            360,
            min(720, len(chart_data) * 22 + 100),
        )
        top_margin = 18
        bottom_margin = 45

    tick_text = [
        (
            f'<b>{escape(str(team_name))}</b>'
            if team_name in highlighted_teams
            else escape(str(team_name))
        )
        for team_name in chart_data["team_name"]
    ]

    figure.update_layout(
        height=chart_height,
        margin={
            "l": 170,
            "r": 44,
            "t": top_margin,
            "b": bottom_margin,
        },
        bargap=0.24,
    )

    figure.update_xaxes(
        title=(
            "Goals scored minus expected goals (xG)"
            if not compact
            else None
        ),
        showgrid=True,
        gridcolor=active_theme["grid"],
        zeroline=False,
    )

    figure.update_yaxes(
        title=None,
        categoryorder="array",
        categoryarray=chart_data["team_name"].tolist(),
        tickmode="array",
        tickvals=chart_data["team_name"].tolist(),
        ticktext=tick_text,
        tickfont={
            "color": active_theme["text"],
            "size": 11,
        },
    )

    return figure

def create_team_comparison_bar_chart(
    team_a_name: str,
    team_b_name: str,
    team_a_row: pd.Series,
    team_b_row: pd.Series,
    active_theme: dict[str, str],
):
    """Create a grouped bar chart for the two selected teams."""
    chart_metrics = [
        "Points",
        "Goals scored",
        "Goals conceded",
        "Expected goals",
    ]

    team_a_values = [
        float(team_a_row["points"]),
        float(team_a_row["goals_for"]),
        float(team_a_row["goals_against"]),
        float(team_a_row["xg_for"]),
    ]

    team_b_values = [
        float(team_b_row["points"]),
        float(team_b_row["goals_for"]),
        float(team_b_row["goals_against"]),
        float(team_b_row["xg_for"]),
    ]

    figure = go.Figure()

    figure.add_trace(
        go.Bar(
            name=team_a_name,
            x=chart_metrics,
            y=team_a_values,
            marker_color=active_theme["comparison_team_a"],
            texttemplate="%{y:.3g}",
            textposition="outside",
            cliponaxis=False,
            hovertemplate=(
                f"<b>{team_a_name}</b><br>"
                "%{x}: %{y:.2f}"
                "<extra></extra>"
            ),
        )
    )

    figure.add_trace(
        go.Bar(
            name=team_b_name,
            x=chart_metrics,
            y=team_b_values,
            marker_color=active_theme["comparison_team_b"],
            texttemplate="%{y:.3g}",
            textposition="outside",
            cliponaxis=False,
            hovertemplate=(
                f"<b>{team_b_name}</b><br>"
                "%{x}: %{y:.2f}"
                "<extra></extra>"
            ),
        )
    )

    figure = style_chart(figure, active_theme)

    figure.update_layout(
        barmode="group",
        bargap=0.34,
        bargroupgap=0.06,
        height=235,
        showlegend=True,
        margin={"l": 18, "r": 18, "t": 38, "b": 28},
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.03,
            "xanchor": "right",
            "x": 1,
            "font": {"size": 12},
        },
    )

    figure.update_xaxes(
        tickfont={"size": 12},
    )

    figure.update_yaxes(
        title=None,
        rangemode="tozero",
        tickfont={"size": 11},
    )

    return figure

# -----------------------------------------------------------------------------
# Weather helpers
# -----------------------------------------------------------------------------
WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Heavy drizzle",
    61: "Light rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Light snow",
    73: "Moderate snow",
    75: "Heavy snow",
    80: "Light rain showers",
    81: "Moderate rain showers",
    82: "Heavy rain showers",
    95: "Thunderstorm",
    96: "Thunderstorm with hail",
    99: "Thunderstorm with heavy hail",
}


def get_weather_description(weather_code: int) -> str:
    """Convert the Open-Meteo numerical weather code into readable text."""
    return WEATHER_CODES.get(weather_code, "Weather unavailable")


@st.cache_data(ttl=3600, show_spinner=False)
def get_current_venue_weather_batch(
    venue_locations: tuple[tuple[str, float, float], ...],
) -> dict[str, object]:
    """
    Retrieve current weather for visible venues using WeatherAPI.

    WeatherAPI standard plans use one request per location, so the result is
    cached for one hour to keep API usage low for the public dashboard.
    """
    api_key = os.environ.get("WEATHER_API_KEY", "").strip()

    if not api_key:
        LOGGER.error("WEATHER_API_KEY is not configured.")

        return {
            "ok": False,
            "records": [],
            "error": (
                "Live weather is not configured on the dashboard server."
            ),
        }

    if not venue_locations:
        return {
            "ok": True,
            "records": [],
            "error": None,
        }

    api_url = "https://api.weatherapi.com/v1/current.json"

    weather_records = []
    failed_venues = []

    with requests.Session() as session:
        for stadium_name, latitude, longitude in venue_locations:
            parameters = {
                "key": api_key,
                "q": f"{latitude:.6f},{longitude:.6f}",
                "aqi": "no",
            }

            try:
                response = session.get(
                    api_url,
                    params=parameters,
                    timeout=8,
                )
                response.raise_for_status()
                weather_payload = response.json()

                if "error" in weather_payload:
                    LOGGER.warning(
                        "WeatherAPI returned an API error for %s: %s",
                        stadium_name,
                        weather_payload["error"],
                    )
                    failed_venues.append(stadium_name)
                    continue

            except requests.Timeout:
                LOGGER.warning(
                    "WeatherAPI request timed out for %s.",
                    stadium_name,
                )
                failed_venues.append(stadium_name)
                continue

            except requests.HTTPError as error:
                status_code = (
                    error.response.status_code
                    if error.response is not None
                    else "unknown"
                )

                response_body = (
                    error.response.text[:500]
                    if error.response is not None
                    else ""
                )

                LOGGER.warning(
                    "WeatherAPI request failed for %s. status=%s body=%s",
                    stadium_name,
                    status_code,
                    response_body,
                )
                failed_venues.append(stadium_name)
                continue

            except requests.RequestException as error:
                LOGGER.warning(
                    "WeatherAPI connection failed for %s: %s",
                    stadium_name,
                    error,
                )
                failed_venues.append(stadium_name)
                continue

            except ValueError:
                LOGGER.warning(
                    "WeatherAPI returned invalid JSON for %s.",
                    stadium_name,
                )
                failed_venues.append(stadium_name)
                continue

            current_weather = weather_payload.get("current", {})

            if not current_weather:
                LOGGER.warning(
                    "WeatherAPI returned no current data for %s.",
                    stadium_name,
                )
                failed_venues.append(stadium_name)
                continue

            condition = current_weather.get("condition", {})

            weather_records.append(
                {
                    "stadium_name": stadium_name,
                    "weather_available": True,
                    "observation_time": current_weather.get(
                        "last_updated"
                    ),
                    "temperature": current_weather.get("temp_c"),
                    "feels_like": current_weather.get("feelslike_c"),
                    "humidity": current_weather.get("humidity"),
                    "precipitation": current_weather.get("precip_mm"),
                    "wind_speed": current_weather.get("wind_kph"),
                    "condition": condition.get(
                        "text",
                        "Weather unavailable",
                    ),
                }
            )

    if not weather_records:
        return {
            "ok": False,
            "records": [],
            "error": (
                "The weather provider did not return usable weather data "
                "for the active venues."
            ),
        }

    if failed_venues:
        LOGGER.warning(
            "WeatherAPI did not return weather for: %s",
            ", ".join(failed_venues),
        )

    return {
        "ok": True,
        "records": weather_records,
        "error": None,
    }

# -----------------------------------------------------------------------------
# Fixture weather helper
# -----------------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def get_fixture_weather(
    latitude: float,
    longitude: float,
    kickoff_utc_iso: str,
) -> dict[str, object]:
    """
    Retrieve weather nearest to a fixture's kick-off time.

    Past fixtures use Open-Meteo historical data.
    Upcoming fixtures use WeatherAPI forecasts.
    """
    kickoff_utc = pd.to_datetime(kickoff_utc_iso, utc=True)
    current_time_utc = pd.Timestamp.now(tz="UTC")

    def optional_number(value: object) -> float | None:
        """Return a float where possible, otherwise None."""
        try:
            return None if pd.isna(value) else float(value)
        except (TypeError, ValueError):
            return None

    # -------------------------------------------------------------------------
    # Past fixtures: retain Open-Meteo historical weather.
    # -------------------------------------------------------------------------
    if kickoff_utc <= current_time_utc:
        historical_url = "https://archive-api.open-meteo.com/v1/archive"

        historical_parameters = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": kickoff_utc.strftime("%Y-%m-%d"),
            "end_date": kickoff_utc.strftime("%Y-%m-%d"),
            "hourly": (
                "temperature_2m,"
                "apparent_temperature,"
                "precipitation,"
                "weather_code,"
                "wind_speed_10m,"
                "relative_humidity_2m"
            ),
            "timezone": "UTC",
        }

        try:
            response = requests.get(
                historical_url,
                params=historical_parameters,
                timeout=15,
            )
            response.raise_for_status()

            response_data = response.json()
            hourly_data = response_data.get("hourly")

            if not hourly_data:
                return {
                    "status": "error",
                    "message": "No historical hourly weather data was returned.",
                }

            hourly_weather = pd.DataFrame(hourly_data)

            if hourly_weather.empty:
                return {
                    "status": "error",
                    "message": "No historical hourly weather data was returned.",
                }

            hourly_weather["time"] = pd.to_datetime(
                hourly_weather["time"],
                utc=True,
                errors="coerce",
            )

            hourly_weather = hourly_weather.dropna(subset=["time"])

            if hourly_weather.empty:
                return {
                    "status": "error",
                    "message": "No usable historical weather data was returned.",
                }

            nearest_row_index = (
                hourly_weather["time"] - kickoff_utc
            ).abs().idxmin()

            weather_row = hourly_weather.loc[nearest_row_index]

            nearest_time_uk = weather_row["time"].tz_convert(
                "Europe/London"
            )

            return {
                "status": "available",
                "weather_type": "historical",
                "weather_time_uk": nearest_time_uk.strftime(
                    "%a %d %b, %H:%M %Z"
                ),
                "temperature": optional_number(
                    weather_row.get("temperature_2m")
                ),
                "feels_like": optional_number(
                    weather_row.get("apparent_temperature")
                ),
                "precipitation": optional_number(
                    weather_row.get("precipitation")
                ),
                "wind_speed": optional_number(
                    weather_row.get("wind_speed_10m")
                ),
                "humidity": optional_number(
                    weather_row.get("relative_humidity_2m")
                ),
                "rain_probability": None,
                "weather_code": int(weather_row["weather_code"]),
                "condition": None,
            }

        except requests.RequestException as error:
            LOGGER.warning(
                "Historical fixture weather request failed: %s",
                error,
            )

            return {
                "status": "error",
                "message": (
                    "Historical weather data could not be retrieved. "
                    "Please try again later."
                ),
            }

        except (ValueError, KeyError, TypeError) as error:
            LOGGER.warning(
                "Historical fixture weather response could not be read: %s",
                error,
            )

            return {
                "status": "error",
                "message": (
                    "Historical weather data could not be read."
                ),
            }

    # -------------------------------------------------------------------------
    # Upcoming fixtures: use WeatherAPI instead of Open-Meteo.
    # -------------------------------------------------------------------------
    api_key = os.environ.get("WEATHER_API_KEY", "").strip()

    if not api_key:
        return {
            "status": "error",
            "message": (
                "Fixture forecasts are not configured on the dashboard server."
            ),
        }

    forecast_limit = current_time_utc + pd.Timedelta(days=3)

    if kickoff_utc > forecast_limit:
        return {
            "status": "unavailable",
            "message": (
                "Fixture forecasts are available once a match is within "
                "3 days of kick-off."
            ),
        }

    forecast_url = "https://api.weatherapi.com/v1/forecast.json"

    forecast_parameters = {
        "key": api_key,
        "q": f"{latitude:.6f},{longitude:.6f}",
        "days": 3,
        "dt": kickoff_utc.strftime("%Y-%m-%d"),
        "aqi": "no",
        "alerts": "no",
    }

    try:
        response = requests.get(
            forecast_url,
            params=forecast_parameters,
            timeout=12,
        )
        response.raise_for_status()

        response_data = response.json()

        if "error" in response_data:
            LOGGER.warning(
                "WeatherAPI fixture forecast error: %s",
                response_data["error"],
            )

            return {
                "status": "error",
                "message": (
                    "The weather provider could not return a fixture forecast."
                ),
            }

        forecast_days = (
            response_data.get("forecast", {})
            .get("forecastday", [])
        )

        if not forecast_days:
            return {
                "status": "error",
                "message": "No forecast weather data was returned.",
            }

        hourly_data = forecast_days[0].get("hour", [])

        if not hourly_data:
            return {
                "status": "error",
                "message": "No hourly forecast weather data was returned.",
            }

        hourly_weather = pd.DataFrame(hourly_data)

        if hourly_weather.empty or "time_epoch" not in hourly_weather.columns:
            return {
                "status": "error",
                "message": "No usable hourly forecast weather data was returned.",
            }

        hourly_weather["time"] = pd.to_datetime(
            hourly_weather["time_epoch"],
            unit="s",
            utc=True,
            errors="coerce",
        )

        hourly_weather = hourly_weather.dropna(subset=["time"])

        if hourly_weather.empty:
            return {
                "status": "error",
                "message": "No usable hourly forecast weather data was returned.",
            }

        nearest_row_index = (
            hourly_weather["time"] - kickoff_utc
        ).abs().idxmin()

        weather_row = hourly_weather.loc[nearest_row_index]

        condition_data = weather_row.get("condition", {})

        condition_text = (
            condition_data.get("text", "Weather unavailable")
            if isinstance(condition_data, dict)
            else "Weather unavailable"
        )

        nearest_time_uk = weather_row["time"].tz_convert(
            "Europe/London"
        )

        return {
            "status": "available",
            "weather_type": "forecast",
            "weather_time_uk": nearest_time_uk.strftime(
                "%a %d %b, %H:%M %Z"
            ),
            "temperature": optional_number(weather_row.get("temp_c")),
            "feels_like": optional_number(weather_row.get("feelslike_c")),
            "precipitation": optional_number(weather_row.get("precip_mm")),
            "wind_speed": optional_number(weather_row.get("wind_kph")),
            "humidity": optional_number(weather_row.get("humidity")),
            "rain_probability": optional_number(
                weather_row.get("chance_of_rain")
            ),
            "weather_code": None,
            "condition": condition_text,
        }

    except requests.HTTPError as error:
        status_code = (
            error.response.status_code
            if error.response is not None
            else "unknown"
        )

        LOGGER.warning(
            "WeatherAPI fixture forecast failed. status=%s body=%s",
            status_code,
            error.response.text[:300]
            if error.response is not None
            else "",
        )

        return {
            "status": "error",
            "message": (
                "The weather provider could not return a fixture forecast "
                f"(HTTP {status_code})."
            ),
        }

    except requests.RequestException as error:
        LOGGER.warning(
            "WeatherAPI fixture forecast connection failed: %s",
            error,
        )

        return {
            "status": "error",
            "message": (
                "Fixture forecast data could not be retrieved. "
                "Please try again later."
            ),
        }

    except (ValueError, KeyError, TypeError) as error:
        LOGGER.warning(
            "WeatherAPI fixture forecast response could not be read: %s",
            error,
        )

        return {
            "status": "error",
            "message": (
                "Fixture forecast data could not be read."
            ),
        }
    
# -----------------------------------------------------------------------------
# Validate data files and load the dataset
# -----------------------------------------------------------------------------
missing = [
    file
    for file in REQUIRED_FILES
    if not (DATA_DIR / file).exists()
]

if missing:
    st.error("Some dataset files are missing.")

    st.code(
        "fifa-2026-dashboard/\n"
        "├── app.py\n"
        "└── data/\n"
        "    ├── matches_detailed.csv\n"
        "    ├── teams.csv\n"
        "    ├── venues.csv\n"
        "    └── squads_and_players.csv"
    )

    st.write("Missing:", ", ".join(missing))
    st.stop()

(
    matches,
    teams,
    venues,
    players,
    match_events,
    detailed_player_stats,
) = load_data(DATA_DIR)


# -----------------------------------------------------------------------------
# Dashboard data scope
# -----------------------------------------------------------------------------
# This dashboard now shows the full World Cup dataset by default. Removing the
# sidebar keeps every page wider, more compact and easier to navigate.
statuses = sorted(matches["status"].dropna().unique())
groups = sorted(matches["group_letter"].dropna().unique())
countries = sorted(matches["country"].dropna().unique())

selected_statuses = statuses
selected_groups = groups
selected_countries = countries

start_date = matches["date"].min()
end_date = matches["date"].max()

filtered_matches = matches.copy()

completed = filtered_matches.loc[
    filtered_matches["status"].eq("Completed")
].copy()

scheduled = filtered_matches.loc[
    filtered_matches["status"].eq("Scheduled")
].copy()

filtered_team_stats = build_team_stats(filtered_matches, teams)

active_match_ids = (
    filtered_matches["match_id"]
    .dropna()
    .astype(int)
    .tolist()
)

player_tournament_stats = build_player_tournament_stats(
    players,
    teams,
    match_events,
    detailed_player_stats,
    active_match_ids,
)

# The detailed player file contains full-tournament totals. Group selection can
# safely limit the available teams; date and status filters continue to apply
# to fixture- and venue-based parts of the dashboard.
active_team_keys = {
    make_team_join_key(team_name)
    for team_name in teams.loc[
        teams["group_letter"].isin(selected_groups),
        "team_name",
    ].dropna()
}

player_tournament_stats = player_tournament_stats.loc[
    player_tournament_stats["team_join_key"].isin(active_team_keys)
].copy()

# -----------------------------------------------------------------------------
# Header and KPIs
# -----------------------------------------------------------------------------

st.markdown(
    f"""
    <div class="dashboard-hero">
        <div class="section-label">Tournament analytics</div>
        <h1>FIFA World Cup 2026</h1>
        <p>
            Explore fixtures, group standings, team performance and host venues
            across the tournament.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

goals = completed["home_score"].sum() + completed["away_score"].sum()
xg = completed["home_xg"].sum() + completed["away_xg"].sum()

st.markdown(
    '<div class="tournament-snapshot-heading">Tournament overview</div>',
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="tournament-snapshot" aria-label="Tournament overview snapshot">
        <div class="tournament-snapshot-item">
            <div class="tournament-snapshot-label">Fixtures</div>
            <div class="tournament-snapshot-value">{len(filtered_matches)}</div>
        </div>
        <div class="tournament-snapshot-item">
            <div class="tournament-snapshot-label">Completed</div>
            <div class="tournament-snapshot-value">{len(completed)}</div>
        </div>
        <div class="tournament-snapshot-item">
            <div class="tournament-snapshot-label">Scheduled</div>
            <div class="tournament-snapshot-value">{len(scheduled)}</div>
        </div>
        <div class="tournament-snapshot-item">
            <div class="tournament-snapshot-label">Goals / xG</div>
            <div class="tournament-snapshot-value">
                {f"{int(goals)} / {xg:.1f}" if not completed.empty else "—"}
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

overview_tab, standings_tab, teams_tab, players_tab, venues_tab = st.tabs(
    [
        "Fixtures",
        "Overall table",
        "Teams",
        "Players",
        "Venues",
    ]
)


# -----------------------------------------------------------------------------
# Dashboard tab
# -----------------------------------------------------------------------------
with overview_tab:
    st.markdown(
        '<div class="section-label">Match centre</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="fixtures-section-title">Fixtures and results</div>',
        unsafe_allow_html=True,
    )

    # Add venue coordinates to every fixture so the weather section can
    # request data for the correct stadium.
    fixture_weather_rows = (
        filtered_matches.merge(
            venues[
                [
                    "stadium_name",
                    "latitude",
                    "longitude",
                ]
            ],
            on="stadium_name",
            how="left",
        )
        .sort_values("kickoff_uk")
        .reset_index(drop=True)
    )

    # The search reruns the page as the user types, so fixture results update
    # immediately without an Apply button. Keep it directly beneath the title
    # to make it the natural first step when locating a match.
    fixture_search = st.text_input(
        "Search fixtures",
        key="fixture_table_search",
        placeholder=(
            "Search team, venue, city, group, status or referee"
        ),
        label_visibility="collapsed",
    )

    searchable_fixture_columns = [
        "home_team_name",
        "away_team_name",
        "stadium_name",
        "city",
        "country",
        "referee_name",
        "status",
        "group_letter",
    ]

    filtered_fixture_weather_rows = fixture_weather_rows.copy()

    if fixture_search.strip():
        fixture_search_text = (
            fixture_weather_rows[searchable_fixture_columns]
            .fillna("")
            .astype(str)
            .agg(" ".join, axis=1)
        )

        filtered_fixture_weather_rows = fixture_weather_rows.loc[
            fixture_search_text.str.contains(
                re.escape(fixture_search.strip()),
                case=False,
                na=False,
            )
        ].reset_index(drop=True)

    fixture_table = make_fixture_table(filtered_fixture_weather_rows)

    fixture_table_event = themed_dataframe(
        fixture_table,
        width="stretch",
        height=224,
        hide_index=True,
        column_config={
            # Explicit pixel widths make the table fit far more comfortably
            # on desktop screens, while still allowing a small amount of
            # horizontal scrolling on narrow mobile displays.
            "kickoff (UK)": st.column_config.TextColumn(
                "Kick-off",
                width=165,
            ),
            "fixture": st.column_config.TextColumn(
                "Fixture",
                width=300,
            ),
            "score": st.column_config.TextColumn(
                "Score",
                width=70,
            ),
            "xG": st.column_config.TextColumn(
                "xG",
                width=88,
            ),
            "status": st.column_config.TextColumn(
                "Status",
                width=96,
            ),
            "group_letter": st.column_config.TextColumn(
                "Group",
                width=64,
            ),
            "stadium_name": st.column_config.TextColumn(
                "Venue",
                width=290,
            ),
            "city": st.column_config.TextColumn(
                "City",
                width=140,
            ),
            "referee_name": st.column_config.TextColumn(
                "Referee",
                width=170,
            ),
        },
        on_select="rerun",
        selection_mode="single-row",
        key="fixture_table_selector",
    )

    st.markdown(
        '<div class="section-label">Fixture weather</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="fixtures-section-title">Weather at kick-off</div>',
        unsafe_allow_html=True,
    )

    if fixture_weather_rows.empty:
        st.info("No fixtures are available in the tournament dataset.")
    else:
        selected_rows = fixture_table_event.selection.rows

        if not selected_rows:
            st.markdown(
                '<div class="fixture-weather-prompt">'
                'Select a fixture row above to view weather at kick-off.'
                '</div>',
                unsafe_allow_html=True,
            )

        else:
            # The table may be search-filtered, so use the same filtered rows
            # to ensure the selected position always maps to the right match.
            selected_fixture = filtered_fixture_weather_rows.iloc[
                selected_rows[0]
            ]

            st.caption(
                f"{selected_fixture['stadium_name']} · "
                f"{selected_fixture['city']}, "
                f"{selected_fixture['country']} · "
                f"Kick-off: "
                f"{selected_fixture['kickoff_uk'].strftime('%a %d %b %Y, %H:%M UK time')}"
            )

            if (
                pd.isna(selected_fixture["latitude"])
                or pd.isna(selected_fixture["longitude"])
            ):
                st.info(
                    "Venue coordinates are not available for this fixture."
                )

            else:
                fixture_weather = get_fixture_weather(
                    latitude=float(selected_fixture["latitude"]),
                    longitude=float(selected_fixture["longitude"]),
                    kickoff_utc_iso=selected_fixture[
                        "kickoff_utc"
                    ].isoformat(),
                )

                if fixture_weather["status"] == "unavailable":
                    st.info(fixture_weather["message"])

                elif fixture_weather["status"] == "error":
                    st.warning(fixture_weather["message"])

                else:
                    weather_description = (
                        fixture_weather.get("condition")
                        or get_weather_description(fixture_weather["weather_code"])
)

                    if fixture_weather["weather_type"] == "forecast":
                        weather_heading = "Forecast at kick-off"
                        final_metric_label = "Rain chance"
                        final_metric_value = (
                            f"{fixture_weather['rain_probability']:.0f}%"
                            if fixture_weather["rain_probability"] is not None
                            else "—"
                        )
                    else:
                        weather_heading = (
                            "Historical conditions at kick-off"
                        )
                        final_metric_label = "Precipitation"
                        final_metric_value = (
                            f"{fixture_weather['precipitation']:.1f} mm"
                            if fixture_weather["precipitation"] is not None
                            else "—"
                        )

                    st.markdown(f"**{weather_heading}**")

                    weather_1, weather_2, weather_3, weather_4, weather_5 = (
                        st.columns(5)
                    )

                    weather_1.metric(
                        "Temperature",
                        f"{fixture_weather['temperature']:.1f} °C",
                    )

                    weather_2.metric(
                        "Feels like",
                        f"{fixture_weather['feels_like']:.1f} °C",
                    )

                    weather_3.metric(
                        "Condition",
                        weather_description,
                    )

                    weather_4.metric(
                        "Wind",
                        f"{fixture_weather['wind_speed']:.0f} km/h",
                    )

                    weather_5.metric(
                        final_metric_label,
                        final_metric_value,
                    )

                    st.caption(
                        "Nearest hourly weather point: "
                        f"{fixture_weather['weather_time_uk']}"
                    )


# -----------------------------------------------------------------------------
# Standings tab
# -----------------------------------------------------------------------------
with standings_tab:
    st.markdown(
        '<div class="section-label">Tournament comparison</div>',
        unsafe_allow_html=True,
    )

    # Keep the hierarchy prominent, then place a generous search field directly
    # beneath the heading. The text input is not inside a form, so its current
    # value immediately drives the table filter whenever Streamlit receives
    # input; there is no separate Apply action.
    st.markdown(
        '<div class="overall-table-title">Overall team table</div>',
        unsafe_allow_html=True,
    )

    # Keep the search field aligned with the full-width standings table.
    standings_search = st.text_input(
        "Search standings",
        key="overall_team_table_search",
        placeholder="Search a team or group",
        label_visibility="collapsed",
    ).strip()

    # Include all tournament teams in the overall comparison.
    overall_table = filtered_team_stats.loc[
        filtered_team_stats["group_letter"].isin(selected_groups)
    ].copy()

    # Avoid dividing by zero for teams with no completed matches.
    overall_table["points_per_game"] = (
        overall_table["points"]
        / overall_table["played"].replace(0, pd.NA)
    ).fillna(0)

    # Sort the strongest-performing teams to the top of the table.
    overall_table = (
        overall_table.sort_values(
            [
                "points",
                "goal_difference",
                "goals_for",
                "xg_difference",
            ],
            ascending=[False, False, False, False],
        )
        .reset_index(drop=True)
    )

    # Create a clear visible rank instead of relying on the dataframe row number.
    overall_table.insert(
        0,
        "rank",
        range(1, len(overall_table) + 1),
    )

    # Search keeps the original tournament rank visible, while allowing users
    # to find a team quickly without extra filters or horizontal controls.
    if standings_search:
        normalised_query = normalise_join_text(standings_search)
        team_matches_search = overall_table["team_name"].map(
            normalise_join_text
        ).str.contains(normalised_query, regex=False)
        group_matches_search = (
            overall_table["group_letter"]
            .astype(str)
            .str.casefold()
            .eq(standings_search.casefold())
        )
        overall_table = overall_table.loc[
            team_matches_search | group_matches_search
        ].copy()

    themed_dataframe(
        overall_table[
            [
                "rank",
                "team_name",
                "group_letter",
                "played",
                "won",
                "drawn",
                "lost",
                "goals_for",
                "goals_against",
                "goal_difference",
                "xg_difference",
                "points",
                "points_per_game",
            ]
        ],
        width="stretch",
        hide_index=True,
        height=288,
        column_config={
            "rank": st.column_config.NumberColumn(
                "Rank",
                format="%d",
                width=52,
            ),
            "team_name": st.column_config.TextColumn(
                "Team",
                width=170,
            ),
            "group_letter": st.column_config.TextColumn(
                "Grp",
                width=48,
            ),
            "played": st.column_config.NumberColumn(
                "P",
                format="%d",
                width=42,
            ),
            "won": st.column_config.NumberColumn(
                "W",
                format="%d",
                width=42,
            ),
            "drawn": st.column_config.NumberColumn(
                "D",
                format="%d",
                width=42,
            ),
            "lost": st.column_config.NumberColumn(
                "L",
                format="%d",
                width=42,
            ),
            "goals_for": st.column_config.NumberColumn(
                "GF",
                format="%d",
                width=44,
            ),
            "goals_against": st.column_config.NumberColumn(
                "GA",
                format="%d",
                width=44,
            ),
            "goal_difference": st.column_config.NumberColumn(
                "GD",
                format="%+d",
                width=48,
            ),
            "xg_difference": st.column_config.NumberColumn(
                "xGΔ",
                format="%+.2f",
                width=64,
            ),
            "points": st.column_config.NumberColumn(
                "Pts",
                format="%d",
                width=46,
            ),
            "points_per_game": st.column_config.NumberColumn(
                "PPG",
                format="%.2f",
                width=58,
            ),
        },
    )



# -----------------------------------------------------------------------------
# Teams tab
# -----------------------------------------------------------------------------
with teams_tab:
    st.markdown(
        """
        <div class="section-label team-analysis-label">Team analysis</div>
        <div class="team-analysis-title">
            Explore or compare national teams
        </div>
        """,
        unsafe_allow_html=True,
    )

    def reset_compare_team_defaults() -> None:
        """Restore the default matchup whenever Compare teams is selected."""
        if st.session_state.get("teams_view_mode") != "Compare teams":
            return

        st.session_state["compare_team_a"] = "England"
        st.session_state["compare_team_b"] = "Argentina"

    team_options = sorted(
        teams["team_name"].dropna().unique()
    )

    default_team_profile = pick_option_by_label(
        team_options,
        "England",
        lambda option: option,
    )
    if default_team_profile is not None and st.session_state.get(
        "profile_team_selector"
    ) not in team_options:
        st.session_state["profile_team_selector"] = default_team_profile

    view_options = ["Team profile", "Compare teams"]
    if st.session_state.get("teams_view_mode") not in view_options:
        st.session_state["teams_view_mode"] = "Team profile"

    # Keep the mode switch and its related selector(s) in one compact panel.
    # In comparison mode, both team choices appear alongside the View control.
    with st.container(border=True):
        st.markdown(
            '<span class="team-control-anchor"></span>',
            unsafe_allow_html=True,
        )

        team_mode_column, team_selector_column = st.columns(
            [1.15, 2.85],
            gap="small",
        )

        with team_mode_column:
            st.markdown(
                '<div class="team-control-label">View</div>',
                unsafe_allow_html=True,
            )
            team_view = st.segmented_control(
                "Choose a Teams view",
                view_options,
                selection_mode="single",
                key="teams_view_mode",
                on_change=reset_compare_team_defaults,
                label_visibility="collapsed",
            )

        # A selected value is always expected because the session-state key is
        # initialised above. The fallback also keeps the interface robust on
        # a first render if Streamlit returns None for the control.
        team_view = team_view or st.session_state["teams_view_mode"]

        with team_selector_column:
            if team_view == "Team profile":
                selected_team = themed_selectbox(
                    "Team",
                    team_options,
                    key="profile_team_selector",
                    search_placeholder="Filter teams",
                    compact_label=True,
                )

            else:
                default_team_a = pick_option_by_label(
                    team_options,
                    "England",
                    lambda option: option,
                ) or team_options[0]

                if st.session_state.get("compare_team_a") not in team_options:
                    st.session_state["compare_team_a"] = default_team_a

                team_a_column, team_b_column = st.columns(2, gap="small")

                with team_a_column:
                    selected_team_a = themed_selectbox(
                        "Team A (Red)",
                        team_options,
                        key="compare_team_a",
                        search_placeholder="Filter teams",
                        compact_label=True,
                    )

                # Build Team B's options only after Team A is resolved, so the
                # same national team cannot appear on both sides.
                team_b_options = [
                    team_name
                    for team_name in team_options
                    if team_name != selected_team_a
                ]

                if st.session_state.get("compare_team_b") not in team_b_options:
                    default_team_b = pick_option_by_label(
                        team_b_options,
                        "Argentina",
                        lambda option: option,
                    ) or team_b_options[0]
                    st.session_state["compare_team_b"] = default_team_b

                with team_b_column:
                    selected_team_b = themed_selectbox(
                        "Team B (Black)",
                        team_b_options,
                        key="compare_team_b",
                        search_placeholder="Filter teams",
                        compact_label=True,
                    )

    # -------------------------------------------------------------------------
    # Single-team profile mode
    # -------------------------------------------------------------------------
    if team_view == "Team profile":
        team_row = filtered_team_stats.loc[
            filtered_team_stats["team_name"].eq(selected_team)
        ].iloc[0]

        team_id = teams.loc[
            teams["team_name"].eq(selected_team),
            "team_id",
        ].iloc[0]

        team_squad = players.loc[
            players["team_id"].eq(team_id)
        ].sort_values(
            "market_value_eur",
            ascending=False,
        )

        squad_summary = summarise_squad(team_squad)

        points_per_game = (
            float(team_row["points"]) / float(team_row["played"])
            if team_row["played"] > 0
            else 0
        )

        st.markdown(
            '<div class="section-label">Team snapshot</div>',
            unsafe_allow_html=True,
        )

        team_snapshot_metrics = [
            ("Played", int(team_row["played"])),
            ("Points", int(team_row["points"])),
            ("Goals scored", int(team_row["goals_for"])),
            ("Goals conceded", int(team_row["goals_against"])),
            ("Goal difference", f"{int(team_row['goal_difference']):+d}"),
            ("xG difference", f"{float(team_row['xg_difference']):+.2f}"),
            ("Points per game", f"{points_per_game:.2f}"),
            ("Elo rating", int(team_row["elo_rating"])),
            ("Squad size", squad_summary["squad_size"]),
            ("Average caps", f"{squad_summary['average_caps']:.1f}"),
            ("Intl. goals", squad_summary["international_goals"]),
            ("Squad value", format_euro_millions(squad_summary["market_value"])),
        ]

        # Build each card as a compact, unindented HTML fragment. Leading
        # spaces in a multi-line Markdown string are treated as a code block,
        # which is why the previous version displayed the HTML tags as text.
        snapshot_cards = "".join(
            (
                '<div class="team-snapshot-card">'
                '<div class="team-snapshot-card-label">'
                f'{escape(str(metric_label))}'
                '</div>'
                '<div class="team-snapshot-card-value">'
                f'{escape(str(metric_value))}'
                '</div>'
                '</div>'
            )
            for metric_label, metric_value in team_snapshot_metrics
        )

        st.markdown(
            '<div class="team-snapshot-grid">'
            f'{snapshot_cards}'
            '</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="section-label">Team finishing</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            f'<div class="team-finishing-title">'
            f'{escape(selected_team)}: goals scored versus expected goals'
            '</div>',
            unsafe_allow_html=True,
        )

        if int(team_row["played"]) == 0:
            st.info(
                f"{selected_team} has no completed matches in the "
                "tournament dataset."
            )

        else:
            render_team_finishing_summary(
                [
                    (
                        selected_team,
                        team_row,
                        theme["comparison_team_a"],
                    )
                ]
            )

            finishing_figure = create_team_finishing_chart(
                filtered_team_stats,
                [selected_team],
                theme,
            )

            st.plotly_chart(
                finishing_figure,
                width="stretch",
                config={"displayModeBar": False, "responsive": True},
            )

            st.markdown(
                '<div class="team-finishing-chart-note">'
                'The dashed line marks teams performing exactly in line with '
                'expected goals. Teams above it have scored more than their '
                'xG; teams below it have scored fewer.'
                '</div>',
                unsafe_allow_html=True,
            )

            st.markdown(
                '<div class="section-label">Goals minus xG ranking</div>',
                unsafe_allow_html=True,
            )

            st.markdown(
                f'<div class="goals-xg-ranking-title">'
                f'{escape(selected_team)}: local position in the '
                'goals-minus-xG ranking'
                '</div>',
                unsafe_allow_html=True,
            )

            focused_goal_delta_figure = create_goals_minus_xg_chart(
                filtered_team_stats,
                [selected_team],
                theme,
                compact=True,
            )

            st.plotly_chart(
                focused_goal_delta_figure,
                width="stretch",
                config={"displayModeBar": False, "responsive": True},
            )

            st.markdown(
                '<div class="goals-xg-ranking-note">'
                'The selected team is enlarged and labelled; the surrounding '
                'teams show its immediate ranking context.'
                '</div>',
                unsafe_allow_html=True,
            )

            with st.expander("Expand to view the full tournament ranking"):
                st.markdown(
                    '<span class="full-goals-xg-ranking-anchor"></span>',
                    unsafe_allow_html=True,
                )

                full_goal_delta_figure = create_goals_minus_xg_chart(
                    filtered_team_stats,
                    [selected_team],
                    theme,
                    compact=False,
                )

                st.plotly_chart(
                    full_goal_delta_figure,
                    width="stretch",
                    config={"displayModeBar": False, "responsive": True},
                )

        # ---------------------------------------------------------------------
        # Team squad: compact, scrollable player table
        # ---------------------------------------------------------------------
        st.markdown(
            '<div class="squad-profile-header">'
            '<div class="squad-profile-kicker">Squad profile</div>'
            '<div class="squad-profile-title-row">'
            '<div class="squad-profile-title">Players</div>'
            f'<div class="squad-profile-count">{len(team_squad)} players</div>'
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        themed_dataframe(
            team_squad[
                [
                    "player_name",
                    "position",
                    "club_team",
                    "caps",
                    "goals",
                    "market_value_eur",
                ]
            ],
            width="stretch",
            hide_index=True,
            height=min(270, 56 + min(len(team_squad), 6) * 36),
            column_config={
                "player_name": st.column_config.TextColumn(
                    "Player",
                    width="large",
                ),
                "position": st.column_config.TextColumn(
                    "Position",
                    width="small",
                ),
                "club_team": st.column_config.TextColumn(
                    "Club",
                    width="large",
                ),
                "caps": st.column_config.NumberColumn(
                    "Caps",
                    format="%d",
                ),
                "goals": st.column_config.NumberColumn(
                    "Goals",
                    format="%d",
                ),
                "market_value_eur": st.column_config.NumberColumn(
                    "Market value",
                    format="€%d",
                ),
            },
        )

    # -------------------------------------------------------------------------
    # Two-team comparison mode
    # -------------------------------------------------------------------------
    else:
        team_a_row = filtered_team_stats.loc[
            filtered_team_stats["team_name"].eq(selected_team_a)
        ].iloc[0]

        team_b_row = filtered_team_stats.loc[
            filtered_team_stats["team_name"].eq(selected_team_b)
        ].iloc[0]

        team_a_id = teams.loc[
            teams["team_name"].eq(selected_team_a),
            "team_id",
        ].iloc[0]

        team_b_id = teams.loc[
            teams["team_name"].eq(selected_team_b),
            "team_id",
        ].iloc[0]

        team_a_squad = players.loc[
            players["team_id"].eq(team_a_id)
        ].copy()

        team_b_squad = players.loc[
            players["team_id"].eq(team_b_id)
        ].copy()

        team_a_summary = summarise_squad(team_a_squad)
        team_b_summary = summarise_squad(team_b_squad)

        team_a_ppg = (
            float(team_a_row["points"]) / float(team_a_row["played"])
            if team_a_row["played"] > 0
            else 0
        )

        team_b_ppg = (
            float(team_b_row["points"]) / float(team_b_row["played"])
            if team_b_row["played"] > 0
            else 0
        )

        st.markdown(
            '<div class="section-label">Side-by-side comparison</div>',
            unsafe_allow_html=True,
        )

        comparison_table = pd.DataFrame(
            {
                "Metric": [
                    "Played",
                    "Points",
                    "Points per game",
                    "Goals scored",
                    "Goals conceded",
                    "Goal difference",
                    "xG for",
                    "xG against",
                    "xG difference",
                    "Elo rating",
                    "Squad size",
                    "Average caps",
                    "International goals",
                    "Dataset squad value",
                ],
                selected_team_a: [
                    int(team_a_row["played"]),
                    int(team_a_row["points"]),
                    f"{team_a_ppg:.2f}",
                    int(team_a_row["goals_for"]),
                    int(team_a_row["goals_against"]),
                    f"{int(team_a_row['goal_difference']):+d}",
                    f"{float(team_a_row['xg_for']):.2f}",
                    f"{float(team_a_row['xg_against']):.2f}",
                    f"{float(team_a_row['xg_difference']):+.2f}",
                    int(team_a_row["elo_rating"]),
                    team_a_summary["squad_size"],
                    f"{team_a_summary['average_caps']:.1f}",
                    team_a_summary["international_goals"],
                    format_euro_millions(
                        team_a_summary["market_value"]
                    ),
                ],
                selected_team_b: [
                    int(team_b_row["played"]),
                    int(team_b_row["points"]),
                    f"{team_b_ppg:.2f}",
                    int(team_b_row["goals_for"]),
                    int(team_b_row["goals_against"]),
                    f"{int(team_b_row['goal_difference']):+d}",
                    f"{float(team_b_row['xg_for']):.2f}",
                    f"{float(team_b_row['xg_against']):.2f}",
                    f"{float(team_b_row['xg_difference']):+.2f}",
                    int(team_b_row["elo_rating"]),
                    team_b_summary["squad_size"],
                    f"{team_b_summary['average_caps']:.1f}",
                    team_b_summary["international_goals"],
                    format_euro_millions(
                        team_b_summary["market_value"]
                    ),
                ],
            }
        )

        themed_dataframe(
            comparison_table,
            width="stretch",
            hide_index=True,
            height=300,
        )

        st.markdown(
            '<div class="section-label head-to-head-section-label">'
            'Head-to-head performance</div>'
            '<div class="head-to-head-title">'
            'Tournament performance comparison</div>',
            unsafe_allow_html=True,
        )

        comparison_bar_chart = create_team_comparison_bar_chart(
            selected_team_a,
            selected_team_b,
            team_a_row,
            team_b_row,
            theme,
        )

        st.plotly_chart(
            comparison_bar_chart,
            width="stretch",
            config={"displayModeBar": False},
        )

        st.markdown(
            '<div class="section-label">Team finishing</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="team-finishing-title">'
            'Goals scored versus expected goals'
            '</div>',
            unsafe_allow_html=True,
        )

        highlighted_teams = []

        if int(team_a_row["played"]) > 0:
            highlighted_teams.append(selected_team_a)

        if int(team_b_row["played"]) > 0:
            highlighted_teams.append(selected_team_b)

        if not highlighted_teams:
            st.info(
                "Neither selected team has completed matches in the "
                "tournament dataset."
            )

        else:
            render_team_finishing_summary(
                [
                    (
                        selected_team_a,
                        team_a_row,
                        theme["comparison_team_a"],
                    ),
                    (
                        selected_team_b,
                        team_b_row,
                        theme["comparison_team_b"],
                    ),
                ]
            )

            finishing_figure = create_team_finishing_chart(
                filtered_team_stats,
                highlighted_teams,
                theme,
            )

            st.plotly_chart(
                finishing_figure,
                width="stretch",
                config={"displayModeBar": False, "responsive": True},
            )

            st.markdown(
                '<div class="team-finishing-chart-note">'
                'Red marks Team A and Black marks Team B. The dashed line '
                'marks teams performing exactly in line with expected goals.'
                '</div>',
                unsafe_allow_html=True,
            )

            st.markdown(
                '<div class="section-label">Goals minus xG ranking</div>',
                unsafe_allow_html=True,
            )

            st.markdown(
                '<div class="goals-xg-ranking-title">'
                'Selected teams and their nearby ranking positions'
                '</div>',
                unsafe_allow_html=True,
            )

            focused_goal_delta_figure = create_goals_minus_xg_chart(
                filtered_team_stats,
                highlighted_teams,
                theme,
                compact=True,
            )

            st.plotly_chart(
                focused_goal_delta_figure,
                width="stretch",
                config={"displayModeBar": False, "responsive": True},
            )

            st.markdown(
                '<div class="goals-xg-ranking-note">'
                'Team A is enlarged in red and Team B is enlarged in black. '
                'The other bars show nearby teams only.'
                '</div>',
                unsafe_allow_html=True,
            )

            with st.expander("Expand to view the full tournament ranking"):
                st.markdown(
                    '<span class="full-goals-xg-ranking-anchor"></span>',
                    unsafe_allow_html=True,
                )

                full_goal_delta_figure = create_goals_minus_xg_chart(
                    filtered_team_stats,
                    highlighted_teams,
                    theme,
                    compact=False,
                )

                st.plotly_chart(
                    full_goal_delta_figure,
                    width="stretch",
                    config={"displayModeBar": False, "responsive": True},
                )

# -----------------------------------------------------------------------------
# Players tab
# -----------------------------------------------------------------------------
with players_tab:
    st.markdown(
        '<div class="section-label">Detailed player analysis</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="player-compare-heading">Compare players</div>',
        unsafe_allow_html=True,
    )

    # Keep the position filter and four player controls together on one compact
    # desktop row. This removes the separate filter and “Choose players” rows.
    (
        position_column,
        player_1_column,
        player_2_column,
        player_3_column,
        player_4_column,
    ) = st.columns([0.9, 1.25, 1.25, 1.25, 1.25], gap="small")

    position_options = ["All positions"] + sorted(
        player_tournament_stats["position"].dropna().unique()
    )

    with position_column:
        selected_position = themed_selectbox(
            "Position",
            position_options,
            key="player_position_filter",
            search_placeholder="Filter positions",
            compact_label=True,
        )

    available_players = player_tournament_stats.copy()

    if selected_position != "All positions":
        available_players = available_players.loc[
            available_players["position"].eq(selected_position)
        ].copy()

    if available_players.empty:
        st.info(
            "No players match the selected position and current group filter."
        )

    else:
        # ---------------------------------------------------------------------
        # Player dropdown setup
        # ---------------------------------------------------------------------
        player_label_lookup = (
            available_players.set_index("player_key")["player_label"].to_dict()
        )

        # None is the "No player selected" option.
        player_selector_options = [
            None,
            *available_players["player_key"].tolist(),
        ]

        def format_player_option(player_key):
            """Turn a stable player key into a readable selector label."""
            if player_key is None:
                return "No player selected"

            return player_label_lookup[player_key]

        player_name_lookup = (
            available_players.set_index("player_key")["player_name"].to_dict()
        )

        # These are the names used by the detailed statistics file.
        default_player_labels = {
            "player_1_selector": "Harry Kane",
            "player_2_selector": "Michael Olise",
            "player_3_selector": "Lionel Messi",
            "player_4_selector": "Kylian Mbappé",
        }

        player_selector_keys = [
            "player_1_selector",
            "player_2_selector",
            "player_3_selector",
            "player_4_selector",
        ]

        for selector_key in player_selector_keys:
            saved_value = st.session_state.get(selector_key)

            if (
                selector_key not in st.session_state
                or saved_value not in player_selector_options
            ):
                desired_label = default_player_labels[selector_key]

                default_player = pick_option_by_label(
                    available_players["player_key"].tolist(),
                    desired_label,
                    lambda player_key: player_name_lookup[player_key],
                )

                if default_player is None:
                    default_player = pick_option_by_label(
                        player_selector_options,
                        desired_label,
                        format_player_option,
                    )

                st.session_state[selector_key] = (
                    default_player if default_player is not None else None
                )

        with player_1_column:
            selected_player_1 = themed_selectbox(
                "Player 1",
                player_selector_options,
                format_func=format_player_option,
                key="player_1_selector",
                search_placeholder="Filter players",
                compact_label=True,
            )

        with player_2_column:
            selected_player_2 = themed_selectbox(
                "Player 2",
                player_selector_options,
                format_func=format_player_option,
                key="player_2_selector",
                search_placeholder="Filter players",
                compact_label=True,
            )

        with player_3_column:
            selected_player_3 = themed_selectbox(
                "Player 3",
                player_selector_options,
                format_func=format_player_option,
                key="player_3_selector",
                search_placeholder="Filter players",
                compact_label=True,
            )

        with player_4_column:
            selected_player_4 = themed_selectbox(
                "Player 4",
                player_selector_options,
                format_func=format_player_option,
                key="player_4_selector",
                search_placeholder="Filter players",
                compact_label=True,
            )

        selected_player_keys = [
            player_key
            for player_key in [
                selected_player_1,
                selected_player_2,
                selected_player_3,
                selected_player_4,
            ]
            if player_key is not None
        ]

        # Keep dropdown order, but prevent the same player appearing twice.
        unique_player_keys = []
        duplicate_found = False

        for player_key in selected_player_keys:
            if player_key not in unique_player_keys:
                unique_player_keys.append(player_key)
            else:
                duplicate_found = True

        selected_player_keys = unique_player_keys

        if duplicate_found:
            st.warning(
                "Each player should only be selected once. "
                "Duplicate selections have been ignored."
            )

        if not selected_player_keys:
            st.info(
                "Choose one to four players to compare detailed tournament "
                "statistics and career international records."
            )

        else:
            # Reindex keeps Player 1 → Player 4 order.
            selected_players = (
                available_players.set_index("player_key")
                .reindex(selected_player_keys)
                .reset_index()
                .copy()
            )

            # Use concise two-line labels inside charts so four selected
            # players remain readable in a two-column dashboard layout.
            # Full names remain available in hover tooltips and tables.
            name_particles = {
                "al",
                "bin",
                "da",
                "das",
                "de",
                "del",
                "den",
                "der",
                "di",
                "dos",
                "du",
                "la",
                "le",
                "van",
                "von",
            }

            def compact_chart_name(full_name: object) -> str:
                """Return a short, readable player name for chart axes."""
                name_parts = str(full_name).split()

                if len(name_parts) <= 2:
                    return " ".join(name_parts)

                surname_parts = [name_parts[-1]]

                if name_parts[-2].casefold() in name_particles:
                    surname_parts.insert(0, name_parts[-2])

                return f"{name_parts[0]} {' '.join(surname_parts)}"

            selected_players["chart_label"] = (
                selected_players["player_name"].map(compact_chart_name)
                + "<br>"
                + selected_players["team_name"]
            )

            # Keep the selected-player identity consistent across every
            # visual. These four colours are intentionally high contrast on
            # the light dashboard and do not reuse the red/black team palette.
            player_colours = [
                theme["comparison_player_1"],
                theme["comparison_player_2"],
                theme["comparison_player_3"],
                theme["comparison_player_4"],
            ]

            colour_map = {
                chart_label: player_colours[index]
                for index, chart_label in enumerate(
                    selected_players["chart_label"]
                )
            }

            selected_player_colours = [
                colour_map[chart_label]
                for chart_label in selected_players["chart_label"]
            ]

            def safe_player_number(value: object) -> float:
                """Return a numeric player value, treating missing values as 0."""
                number = pd.to_numeric(value, errors="coerce")
                return 0.0 if pd.isna(number) else float(number)

            player_performance_tab, player_advanced_tab, player_international_tab = st.tabs(
                [
                    "Tournament performance",
                    "Advanced metrics",
                    "International record",
                ]
            )

            with player_performance_tab:
                # -----------------------------------------------------------------
                # Tournament comparison matrix
                # -----------------------------------------------------------------
                st.markdown(
                    (
                        '<div style="margin: 0.35rem 0 0.28rem;">'
                        '<div class="section-label" style="margin-bottom: 0.12rem;">'
                        'Tournament comparison</div>'
                        '<div style="color: var(--text); font-size: 1.45rem; '
                        'font-weight: 750; letter-spacing: -0.025em; line-height: 1.15;">'
                        'Player comparison matrix</div>'
                        '</div>'
                    ),
                    unsafe_allow_html=True,
                )
                st.markdown(
                    '<div style="margin: 0 0 0.45rem; color: var(--muted); '
                    'font-size: 0.80rem; line-height: 1.35;">'
                    'World Cup 2026 performance from player_tournament_stats.csv. '
                    'Each coloured cell compares the selected players within that statistic.'
                    '</div>',
                    unsafe_allow_html=True,
                )

                # The detailed player dataset already provides shots_on_target_pct.
                # Normalise it here so the matrix remains reliable if a source row
                # contains a missing value.
                selected_players["shots_on_target_pct"] = pd.to_numeric(
                    selected_players["shots_on_target_pct"],
                    errors="coerce",
                ).fillna(0)

                # All heatmap values below come directly from
                # player_tournament_stats.csv. The mix deliberately covers
                # availability, attacking output and efficiency, defensive work,
                # creativity and ball-carrying/foul-winning contribution.
                matrix_metrics = [
                    ("Minutes", "minutes"),
                    ("Starts", "games_starts"),
                    ("Goals", "goals"),
                    ("Assists", "assists"),
                    ("Goal<br>contribs /90", "goals_assists_per90"),
                    ("Shots", "shots"),
                    ("Shots<br>on target", "shots_on_target"),
                    ("Shot<br>accuracy", "shots_on_target_pct"),
                    ("Tackles<br>won", "tackles_won"),
                    ("Interceptions", "interceptions"),
                    ("Crosses", "crosses"),
                    ("Fouls<br>won", "fouled"),
                ]

                # Purple-blue sequential matrix palette sampled from the
                # attached reference. Values are ordered from lowest to
                # highest here. The legend below now reads from lower totals
                # on the left to higher totals on the right, while keeping
                # the same colour meaning across the scale.
                matrix_heat_stops = [
                    (241, 241, 241),  # lowest positive total: soft neutral
                    (205, 225, 234),  # pale blue
                    (173, 197, 219),  # powder blue
                    (145, 162, 199),  # muted blue
                    (124, 123, 174),  # blue-violet
                    (109, 79, 145),   # muted purple
                    (97, 15, 115),    # highest total: deep purple
                ]
                # Keep the sampled palette intact. The matrix uses dark text,
                # so no global opacity/white blend is applied to the colours.
                matrix_heat_white_mix = 0.00
                matrix_zero_background = theme["card_bg_soft"]

                def blend_matrix_heat_colour(proportion: float) -> str:
                    """Return an interpolated purple-blue matrix colour."""
                    clamped_proportion = min(max(proportion, 0.0), 1.0)
                    scaled_position = clamped_proportion * (
                        len(matrix_heat_stops) - 1
                    )
                    lower_index = int(scaled_position)
                    upper_index = min(
                        lower_index + 1,
                        len(matrix_heat_stops) - 1,
                    )
                    local_position = scaled_position - lower_index

                    start_colour = matrix_heat_stops[lower_index]
                    end_colour = matrix_heat_stops[upper_index]

                    red = round(
                        start_colour[0]
                        + (end_colour[0] - start_colour[0])
                        * local_position
                    )
                    green = round(
                        start_colour[1]
                        + (end_colour[1] - start_colour[1])
                        * local_position
                    )
                    blue = round(
                        start_colour[2]
                        + (end_colour[2] - start_colour[2])
                        * local_position
                    )
                    return f"rgb({red}, {green}, {blue})"

                # Keep the actual maximum for each metric so values can be
                # scaled consistently within their own column.
                metric_actual_maxima = {
                    column: safe_player_number(selected_players[column].max())
                    for _, column in matrix_metrics
                }

                metric_maxima = {
                    column: max(metric_actual_maxima[column], 1.0)
                    for _, column in matrix_metrics
                }

                # Min/max scaling alone can make close totals look nearly equal.
                # Add a rank-aware component so every distinct positive value is
                # clearly separated, while preserving the fact that larger totals
                # always receive a darker colour.
                metric_rank_positions: dict[str, dict[float, float]] = {}

                for _, column in matrix_metrics:
                    positive_values = sorted(
                        {
                            safe_player_number(value)
                            for value in selected_players[column]
                            if safe_player_number(value) > 0
                        }
                    )

                    if len(positive_values) == 1:
                        metric_rank_positions[column] = {
                            positive_values[0]: 1.0
                        }
                    elif positive_values:
                        metric_rank_positions[column] = {
                            value: index / (len(positive_values) - 1)
                            for index, value in enumerate(positive_values)
                        }
                    else:
                        metric_rank_positions[column] = {}

                def hex_to_rgb(colour: str) -> tuple[int, int, int]:
                    """Convert a six-character hex colour into an RGB tuple."""
                    value = colour.lstrip("#")
                    return (
                        int(value[0:2], 16),
                        int(value[2:4], 16),
                        int(value[4:6], 16),
                    )

                def rgb_to_css(colour: tuple[int, int, int]) -> str:
                    """Return a CSS rgb() value from an RGB tuple."""
                    return f"rgb({colour[0]}, {colour[1]}, {colour[2]})"

                def soften_matrix_heat_rgb(
                    colour: tuple[int, int, int],
                ) -> tuple[int, int, int]:
                    """Optionally blend a matrix palette colour towards white."""
                    return tuple(
                        round(
                            channel * (1 - matrix_heat_white_mix)
                            + 255 * matrix_heat_white_mix
                        )
                        for channel in colour
                    )

                def matrix_heat_rgb(proportion: float) -> tuple[int, int, int]:
                    """Return a display RGB colour from the purple-blue scale."""
                    css_colour = blend_matrix_heat_colour(proportion)
                    rgb_values = re.findall(r"\d+", css_colour)
                    raw_rgb = tuple(int(value) for value in rgb_values[:3])
                    return soften_matrix_heat_rgb(raw_rgb)

                def blend_rgb(
                    first: tuple[int, int, int],
                    second: tuple[int, int, int],
                    fraction: float,
                ) -> tuple[int, int, int]:
                    """Blend two RGB colours by the given fraction."""
                    clamped_fraction = min(max(fraction, 0.0), 1.0)
                    return tuple(
                        round(
                            first[index]
                            + (second[index] - first[index]) * clamped_fraction
                        )
                        for index in range(3)
                    )

                def midpoint_colour(
                    first: tuple[int, int, int],
                    second: tuple[int, int, int],
                ) -> tuple[int, int, int]:
                    """Return the visual midpoint between two adjacent cells."""
                    return blend_rgb(first, second, 0.5)

                def relative_luminance(colour: tuple[int, int, int]) -> float:
                    """Return WCAG relative luminance for an RGB colour."""
                    channels = []

                    for channel in colour:
                        scaled = channel / 255
                        channels.append(
                            scaled / 12.92
                            if scaled <= 0.04045
                            else ((scaled + 0.055) / 1.055) ** 2.4
                        )

                    return (
                        0.2126 * channels[0]
                        + 0.7152 * channels[1]
                        + 0.0722 * channels[2]
                    )

                def matrix_text_style(
                    background: tuple[int, int, int],
                ) -> tuple[str, str]:
                    """Choose the most readable label colour for a heat cell."""
                    dark_text = hex_to_rgb(theme["text"])
                    white_text = (255, 255, 255)
                    background_luminance = relative_luminance(background)

                    dark_contrast = (
                        max(relative_luminance(dark_text), background_luminance)
                        + 0.05
                    ) / (
                        min(relative_luminance(dark_text), background_luminance)
                        + 0.05
                    )
                    white_contrast = (
                        max(relative_luminance(white_text), background_luminance)
                        + 0.05
                    ) / (
                        min(relative_luminance(white_text), background_luminance)
                        + 0.05
                    )

                    if white_contrast > dark_contrast:
                        return (
                            "#ffffff",
                            "text-shadow: 0 1px 2px rgba(0, 0, 0, 0.22);",
                        )

                    return (
                        theme["text"],
                        "text-shadow: 0 1px 1px rgba(255, 255, 255, 0.20);",
                    )

                zero_rgb = hex_to_rgb(matrix_zero_background)

                # Build each cell before rendering the table. Each numerical column
                # then uses a continuous top-to-bottom gradient: the colour at a row
                # boundary is shared by the cell above and below it, eliminating the
                # white horizontal dividers while preserving each row's own value at
                # the centre of its cell.
                matrix_cell_styles: dict[str, list[dict[str, object]]] = {}

                for _, column in matrix_metrics:
                    column_cells: list[dict[str, object]] = []

                    for _, player in selected_players.iterrows():
                        value = safe_player_number(player[column])

                        if value <= 0:
                            heat_proportion = None
                            base_rgb = zero_rgb
                        else:
                            relative_value = min(
                                value / metric_maxima[column],
                                1.0,
                            )
                            rank_position = metric_rank_positions[column][value]

                            heat_proportion = min(
                                1.0,
                                0.66 * rank_position + 0.34 * relative_value,
                            )
                            base_rgb = matrix_heat_rgb(heat_proportion)

                        # Choose black or white dynamically from the actual
                        # heat colour. This keeps labels readable on the deep
                        # purple end of the scale without weakening legibility
                        # on pale blue or neutral cells.
                        value_colour, value_text_shadow = matrix_text_style(
                            base_rgb
                        )

                        display_value = (
                            f"{value:.1f}%"
                            if column == "shots_on_target_pct"
                            else f"{value:.0f}"
                        )

                        column_cells.append(
                            {
                                "value": value,
                                "display_value": display_value,
                                "base_rgb": base_rgb,
                                "heat_proportion": heat_proportion,
                                "value_colour": value_colour,
                                "value_text_shadow": value_text_shadow,
                            }
                        )

                    for row_index, cell in enumerate(column_cells):
                        current_rgb = cell["base_rgb"]
                        previous_rgb = (
                            column_cells[row_index - 1]["base_rgb"]
                            if row_index > 0
                            else current_rgb
                        )
                        next_rgb = (
                            column_cells[row_index + 1]["base_rgb"]
                            if row_index < len(column_cells) - 1
                            else current_rgb
                        )

                        top_rgb = midpoint_colour(previous_rgb, current_rgb)
                        bottom_rgb = midpoint_colour(current_rgb, next_rgb)

                        cell["background"] = (
                            "linear-gradient(to bottom, "
                            f"{rgb_to_css(top_rgb)} 0%, "
                            f"{rgb_to_css(current_rgb)} 50%, "
                            f"{rgb_to_css(bottom_rgb)} 100%)"
                        )

                    matrix_cell_styles[column] = column_cells

                # Render the matrix as a CSS grid rather than a table. Each metric
                # is one uninterrupted thermal surface: no horizontal seams split
                # the four player rows, but the actual value remains centred in
                # its own row. The name column remains row-based for identity.
                def build_continuous_column_gradient(
                    cells: list[dict[str, object]],
                ) -> str:
                    """Build one uninterrupted thermal, contour-style metric gradient."""
                    base_colours = [cell["base_rgb"] for cell in cells]

                    if len(base_colours) == 1:
                        colour = rgb_to_css(base_colours[0])
                        return f"linear-gradient(to bottom, {colour}, {colour})"

                    row_count = len(base_colours)
                    gradient_stops: list[str] = []
                    warm_highlight = soften_matrix_heat_rgb(
                        matrix_heat_stops[-1]
                    )

                    for row_index, colour in enumerate(base_colours):
                        current_cell = cells[row_index]
                        previous_colour = (
                            base_colours[row_index - 1]
                            if row_index > 0
                            else colour
                        )
                        next_colour = (
                            base_colours[row_index + 1]
                            if row_index < row_count - 1
                            else colour
                        )

                        row_start = (row_index / row_count) * 100
                        row_end = ((row_index + 1) / row_count) * 100
                        row_span = row_end - row_start
                        core_start = row_start + row_span * 0.30
                        core_end = row_start + row_span * 0.70

                        edge_top = midpoint_colour(previous_colour, colour)
                        edge_bottom = midpoint_colour(colour, next_colour)
                        shoulder_top = blend_rgb(edge_top, colour, 0.62)
                        shoulder_bottom = blend_rgb(edge_bottom, colour, 0.62)

                        # The centred highlight creates the subtle contour band.
                        # It scales with the positive value, so low values retain
                        # their burgundy tone and zeros stay neutral grey.
                        heat_proportion = current_cell["heat_proportion"]
                        if current_cell["value"] > 0 and heat_proportion is not None:
                            highlight_strength = 0.07 + 0.17 * float(
                                heat_proportion
                            )
                            highlight_rgb = blend_rgb(
                                colour,
                                warm_highlight,
                                highlight_strength,
                            )
                        else:
                            highlight_rgb = colour

                        if row_index == 0:
                            gradient_stops.append(
                                f"{rgb_to_css(edge_top)} {row_start:.3f}%"
                            )

                        gradient_stops.extend(
                            [
                                f"{rgb_to_css(shoulder_top)} {core_start:.3f}%",
                                f"{rgb_to_css(highlight_rgb)} "
                                f"{((core_start + core_end) / 2):.3f}%",
                                f"{rgb_to_css(shoulder_bottom)} {core_end:.3f}%",
                            ]
                        )

                        if row_index < row_count - 1:
                            gradient_stops.append(
                                f"{rgb_to_css(edge_bottom)} {row_end:.3f}%"
                            )
                        else:
                            gradient_stops.append(
                                f"{rgb_to_css(edge_bottom)} 100%"
                            )

                    return (
                        "linear-gradient(to bottom, "
                        + ", ".join(gradient_stops)
                        + ")"
                    )

                # Keep the expanded 12-metric matrix on one desktop canvas. The
                # player column is compact but still comfortable for names, while
                # every metric column shares the remaining available width. There
                # is intentionally no minimum table width or horizontal scroller.
                # A compact row height keeps the matrix scannable without making
                # the player identity or 12 metric columns feel cramped.
                matrix_row_height_px = 70
                matrix_player_column_width_px = 195
                matrix_column_template = (
                    f"{matrix_player_column_width_px}px "
                    + " ".join(
                        "minmax(0, 1fr)"
                        for _ in matrix_metrics
                    )
                )

                matrix_parts = [
                    (
                        '<div class="player-comparison-matrix" style="width: 100%; '
                        'max-width: 100%; overflow: hidden; border: 1px solid var(--border); '
                        'border-radius: 14px; background: var(--chart-bg);">'
                        '<div style="width: 100%; min-width: 0;">'
                        f'<div style="display: grid; width: 100%; min-width: 0; grid-template-columns: {matrix_column_template}; '
                        'background: var(--table-header); border-bottom: 1px solid var(--border);">'
                        '<div style="padding: 0.55rem 0.78rem; color: var(--muted); '
                        'font-size: 0.78rem; font-weight: 750; border-right: 1px solid var(--border); '
                        'display: flex; align-items: center;">Player</div>'
                    )
                ]

                for metric_index, (metric_label, _) in enumerate(matrix_metrics):
                    header_border = (
                        'border-right: 1px solid var(--border); '
                        if metric_index < len(matrix_metrics) - 1
                        else ''
                    )
                    matrix_parts.append(
                        (
                            '<div style="padding: 0.44rem 0.18rem; min-width: 0; text-align: center; '
                            'color: var(--muted); line-height: 1.12; overflow-wrap: anywhere; '
                            'font-size: clamp(0.54rem, 0.60vw, 0.66rem); font-weight: 750; '
                            'text-transform: uppercase; letter-spacing: 0.02em; display: flex; '
                            'align-items: center; '
                            f'justify-content: center; {header_border}">'
                            f'{metric_label}</div>'
                        )
                    )

                # Close the header grid before starting the body grid. Keeping the
                # two grids as siblings means the shared width and column template
                # align every data column exactly beneath its header.
                matrix_parts.append('</div>')

                matrix_parts.append(
                    (
                        f'<div style="display: grid; width: 100%; min-width: 0; grid-template-columns: {matrix_column_template}; '
                        'align-items: stretch;">'
                        '<div style="min-width: 0; background: var(--card-bg); border-right: 1px solid var(--border);">'
                    )
                )

                for row_index, (_, player) in enumerate(selected_players.iterrows()):
                    player_colour = player_colours[row_index]
                    player_name = escape(str(player["player_name"]))
                    team_name = escape(str(player["team_name"]))
                    position = escape(str(player.get("position", "—")))
                    name_row_border = (
                        'border-bottom: 1px solid var(--border); '
                        if row_index < len(selected_players) - 1
                        else ''
                    )

                    matrix_parts.append(
                        (
                            f'<div style="height: {matrix_row_height_px}px; min-width: 0; padding: 0.42rem 0.62rem; '
                            f'border-left: 4px solid {player_colour}; {name_row_border}'
                            'box-sizing: border-box; display: flex; flex-direction: column; '
                            'justify-content: center;">'
                            f'<div style="font-size: 0.86rem; font-weight: 750; color: {player_colour}; line-height: 1.15; '
                            'overflow-wrap: anywhere;">'
                            f'{player_name}</div>'
                            '<div style="margin-top: 0.10rem; color: var(--muted); font-size: 0.68rem; '
                            'line-height: 1.15;">'
                            f'{team_name} · {position}</div>'
                            '</div>'
                        )
                    )

                matrix_parts.append('</div>')

                for metric_index, (_, column) in enumerate(matrix_metrics):
                    column_cells = matrix_cell_styles[column]
                    column_background = build_continuous_column_gradient(
                        column_cells
                    )
                    column_border = (
                        # A thin, translucent charcoal divider separates metrics
                        # without competing with the thermal heat treatment.
                        'border-right: 1px solid rgba(32, 36, 43, 0.18); '
                        if metric_index < len(matrix_metrics) - 1
                        else ''
                    )

                    matrix_parts.append(
                        (
                            f'<div class="player-matrix-gradient-column" style="height: '
                            f'{matrix_row_height_px * len(selected_players)}px; '
                            f'background: {column_background}; {column_border}'
                            'box-sizing: border-box; display: grid; '
                            f'grid-template-rows: repeat({len(selected_players)}, {matrix_row_height_px}px); '
                            'position: relative;">'
                        )
                    )

                    for cell in column_cells:
                        matrix_parts.append(
                            (
                                '<div style="position: relative; display: flex; align-items: center; '
                                'justify-content: center; min-width: 0; background: transparent; '
                                'border: 0 !important; outline: 0 !important; box-shadow: none !important; '
                                'font-variant-numeric: tabular-nums;">'
                                f'<strong style="position: relative; z-index: 1; color: {cell["value_colour"]}; '
                                f'{cell["value_text_shadow"]} '
                                'font-size: clamp(0.80rem, 1.00vw, 0.98rem); font-weight: 800; white-space: nowrap;">'
                                f'{cell["display_value"]}</strong>'
                                '</div>'
                            )
                        )

                    matrix_parts.append('</div>')

                matrix_parts.append('</div></div></div>')

                st.markdown(
                    "".join(matrix_parts),
                    unsafe_allow_html=True,
                )
                legend_gradient = ", ".join(
                    rgb_to_css(soften_matrix_heat_rgb(colour))
                    for colour in matrix_heat_stops
                )
                st.markdown(
                    (
                        '<div style="display: flex; align-items: center; gap: 0.55rem; '
                        'margin: 0.35rem 0 0.80rem; color: var(--muted); '
                        'font-size: 0.72rem; font-weight: 650;">'
                        '<span style="white-space: nowrap;">Lower positive total</span>'
                        f'<div aria-label="Purple-blue heatmap legend: pale blue represents a lower positive total and purple represents a higher total" '
                        f'style="height: 10px; flex: 1; min-width: 160px; '
                        f'background: linear-gradient(to right, {legend_gradient}); '
                        'border: 1px solid rgba(32, 36, 43, 0.16); border-radius: 999px;"></div>'
                        '<span style="white-space: nowrap;">Higher total</span>'
                        '<span style="display: inline-flex; align-items: center; gap: 0.28rem; white-space: nowrap;">'
                        f'<span aria-hidden="true" style="width: 0.68rem; height: 0.68rem; background: {matrix_zero_background}; '
                        'border: 1px solid rgba(32, 36, 43, 0.14); border-radius: 2px;"></span>'
                        '0 / no total</span>'
                        '</div>'
                    ),
                    unsafe_allow_html=True,
                )

                # -----------------------------------------------------------------
                # Finishing and shot volume
                # -----------------------------------------------------------------
                st.markdown(
                    (
                        '<div style="margin: 0.35rem 0 0.28rem;">'
                        '<div class="section-label" style="margin-bottom: 0.12rem;">'
                        'Finishing and shot volume</div>'
                        '<div style="color: var(--text); font-size: 1.35rem; '
                        'font-weight: 750; letter-spacing: -0.025em; line-height: 1.15;">'
                        'Goals compared with shots on target</div>'
                        '</div>'
                    ),
                    unsafe_allow_html=True,
                )

                maximum_minutes = max(
                    safe_player_number(selected_players["minutes"].max()),
                    1.0,
                )
                bubble_sizes = [
                    18 + safe_player_number(value) / maximum_minutes * 30
                    for value in selected_players["minutes"]
                ]

                shot_on_target_values = [
                    safe_player_number(value)
                    for value in selected_players["shots_on_target"]
                ]
                goal_values = [
                    safe_player_number(value)
                    for value in selected_players["goals"]
                ]

                maximum_goals = max(max(goal_values, default=0.0), 1.0)
                maximum_shots_on_target = max(
                    max(shot_on_target_values, default=0.0),
                    1.0,
                )

                # Reserve enough room beneath y=0 for the full radius of a
                # zero-goal bubble. The estimate uses the compact chart's
                # drawable height, so it continues to work when player minutes
                # change the bubble sizes.
                largest_bubble_radius = max(bubble_sizes, default=18) / 2
                estimated_plot_height = 250
                estimated_y_span = maximum_goals + 1.0
                zero_goal_padding = max(
                    0.8,
                    (
                        largest_bubble_radius
                        * estimated_y_span
                        / estimated_plot_height
                    )
                    + 0.22,
                )

                # Use Plotly's compact colour legend instead of labels next to
                # the bubbles. This prevents overlapping or clipped names when
                # selected players occupy similar areas of the scatter plot.
                attacking_scatter = go.Figure()

                for index, (_, player_row) in enumerate(selected_players.iterrows()):
                    attacking_scatter.add_trace(
                        go.Scatter(
                            x=[shot_on_target_values[index]],
                            y=[goal_values[index]],
                            mode="markers",
                            name=(
                                f"{compact_chart_name(player_row['player_name'])} "
                                f"— {player_row['team_name']}"
                            ),
                            customdata=[[
                                player_row["player_name"],
                                player_row["team_name"],
                                safe_player_number(player_row["shots"]),
                                safe_player_number(player_row["assists"]),
                                safe_player_number(player_row["minutes"]),
                            ]],
                            marker={
                                "size": bubble_sizes[index],
                                "color": selected_player_colours[index],
                                "line": {
                                    "color": theme["card_bg"],
                                    "width": 2,
                                },
                                "opacity": 0.92,
                            },
                            hovertemplate=(
                                "<b>%{customdata[0]}</b> — %{customdata[1]}<br>"
                                "Goals: %{y:.0f}<br>"
                                "Shots on target: %{x:.0f}<br>"
                                "Total shots: %{customdata[2]:.0f}<br>"
                                "Assists: %{customdata[3]:.0f}<br>"
                                "Minutes: %{customdata[4]:.0f}"
                                "<extra></extra>"
                            ),
                        )
                    )

                attacking_scatter = style_chart(attacking_scatter, theme)
                attacking_scatter.update_layout(
                    # Prioritise the scatter plot itself: the legend now sits
                    # close beneath the axis label instead of using a large
                    # empty band below the chart.
                    height=460,
                    margin={"l": 50, "r": 34, "t": 18, "b": 70},
                    showlegend=True,
                    legend={
                        "orientation": "h",
                        "yanchor": "top",
                        "y": -0.30,
                        "xanchor": "center",
                        "x": 0.5,
                        "font": {"size": 10, "color": theme["text"]},
                        "bgcolor": "rgba(0, 0, 0, 0)",
                        "borderwidth": 0,
                        "tracegroupgap": 8,
                    },
                )
                attacking_scatter.update_xaxes(
                    title="Shots on target",
                    range=[
                        -0.20,
                        maximum_shots_on_target + 0.75,
                    ],
                    dtick=1,
                    layer="below traces",
                )
                attacking_scatter.update_yaxes(
                    title="Tournament goals",
                    range=[
                        -zero_goal_padding,
                        maximum_goals + 0.95,
                    ],
                    dtick=1,
                    tick0=0,
                    layer="below traces",
                )

                st.plotly_chart(
                    attacking_scatter,
                    width="stretch",
                    config={"displayModeBar": False},
                )
                st.markdown(
                    '<div style="margin: 0.12rem 0 0.65rem; color: var(--muted); '
                    'font-size: 0.72rem; line-height: 1.25;">'
                    'Bubble size represents minutes played.'                    '</div>',
                    unsafe_allow_html=True,
                )

                # -----------------------------------------------------------------
                # Discipline summary
                # -----------------------------------------------------------------
                st.markdown(
                    (
                        '<div style="margin: 0.25rem 0 0.28rem;">'
                        '<div class="section-label" style="margin-bottom: 0.12rem;">Discipline</div>'
                        '<div style="color: var(--text); font-size: 1.35rem; '
                        'font-weight: 750; letter-spacing: -0.025em; line-height: 1.15;">'
                        'Discipline summary</div>'
                        '</div>'
                    ),
                    unsafe_allow_html=True,
                )

                discipline_table = selected_players[
                    [
                        "player_name",
                        "team_name",
                        "cards_yellow",
                        "cards_red",
                        "fouls",
                    ]
                ].copy()
                discipline_table["cards_yellow"] = pd.to_numeric(
                    discipline_table["cards_yellow"],
                    errors="coerce",
                ).fillna(0).astype(int)
                discipline_table["cards_red"] = pd.to_numeric(
                    discipline_table["cards_red"],
                    errors="coerce",
                ).fillna(0).astype(int)
                discipline_table["fouls"] = pd.to_numeric(
                    discipline_table["fouls"],
                    errors="coerce",
                ).fillna(0).astype(int)
                discipline_table = discipline_table.rename(
                    columns={
                        "player_name": "Player",
                        "team_name": "Team",
                        "cards_yellow": "Yellow cards",
                        "cards_red": "Red cards",
                        "fouls": "Fouls committed",
                    }
                )

                themed_dataframe(
                    discipline_table,
                    height=180,
                    width="stretch",
                    hide_index=True,
                    column_config={
                        "Player": st.column_config.TextColumn(
                            "Player",
                            width="large",
                        ),
                        "Team": st.column_config.TextColumn(
                            "Team",
                            width="medium",
                        ),
                        "Yellow cards": st.column_config.NumberColumn(
                            "🟨 Yellow",
                            format="%d",
                        ),
                        "Red cards": st.column_config.NumberColumn(
                            "🟥 Red",
                            format="%d",
                        ),
                        "Fouls committed": st.column_config.NumberColumn(
                            "Fouls",
                            format="%d",
                        ),
                    },
                )

            with player_advanced_tab:
                # -----------------------------------------------------------------
                # Advanced metrics
                # -----------------------------------------------------------------
                st.markdown(
                    '<div class="section-label advanced-metrics-section-label">'
                    'Advanced metrics</div>',
                    unsafe_allow_html=True,
                )

                # Keep this selector deliberately small. The heatmap already covers
                # minutes, starts, goal output, shots, accuracy, defensive actions,
                # crossing and fouls won. These are the useful non-duplicated
                # tournament fields from player_tournament_stats.csv.
                metric_options = {
                    "Non-penalty goals": {
                        "column": "goals_pens",
                        "axis_title": "Non-penalty goals",
                        "hover_value": "%{x:.0f}",
                        "tickformat": ".0f",
                        "is_rate": False,
                    },
                    "Shots per 90": {
                        "column": "shots_per90",
                        "axis_title": "Shots per 90",
                        "hover_value": "%{x:.2f}",
                        "tickformat": ".1f",
                        "is_rate": True,
                    },
                    "Minutes %": {
                        "column": "minutes_pct",
                        "axis_title": "Minutes played (%)",
                        "hover_value": "%{x:.1f}%",
                        "tickformat": ".0f",
                        "is_rate": False,
                    },
                    "Offsides": {
                        "column": "offsides",
                        "axis_title": "Offsides",
                        "hover_value": "%{x:.0f}",
                        "tickformat": ".0f",
                        "is_rate": False,
                    },
                    "On-pitch goal difference per 90": {
                        "column": "plus_minus_per90",
                        "axis_title": "On-pitch goal difference per 90",
                        "hover_value": "%{x:+.2f}",
                        "tickformat": "+.1f",
                        "is_rate": True,
                    },
                }

                with st.container(border=True):
                    st.markdown(
                        '<span class="advanced-metrics-control-anchor"></span>',
                        unsafe_allow_html=True,
                    )

                    metric_copy_column, metric_selector_column = st.columns(
                        [1.2, 2.8],
                        gap="medium",
                    )

                    with metric_copy_column:
                        st.markdown(
                            '<div class="advanced-metrics-control-title">'
                            'Comparison metric</div>'
                            '<p class="advanced-metrics-control-note">'
                            'Choose a deeper metric to complement the core '
                            'comparison above.</p>',
                            unsafe_allow_html=True,
                        )

                    with metric_selector_column:
                        selected_metric_label = themed_selectbox(
                            "Metric",
                            list(metric_options),
                            key="player_detail_metric",
                            search_placeholder="Filter metrics",
                            compact_label=True,
                        )

                selected_metric_definition = metric_options[
                    selected_metric_label
                ]
                selected_metric = selected_metric_definition["column"]

                st.markdown(
                    f'<div class="advanced-metric-chart-title">'
                    f'{escape(selected_metric_label)}</div>',
                    unsafe_allow_html=True,
                )

                # Use horizontal bar charts here because they are easier
                # for most users to scan than lollipop charts. Missing
                # values fall back to zero so the selected player order
                # remains stable across metric changes.
                raw_detail_values = pd.to_numeric(
                    selected_players[selected_metric],
                    errors="coerce",
                )

                detail_data = selected_players.copy()
                detail_data["metric_value"] = raw_detail_values.fillna(0)
                detail_values = detail_data["metric_value"].tolist()

                detail_figure = go.Figure()
                detail_figure.add_trace(
                    go.Bar(
                        x=detail_data["metric_value"],
                        y=detail_data["chart_label"],
                        orientation="h",
                        marker={
                            "color": selected_player_colours,
                            "line": {
                                "color": theme["card_bg"],
                                "width": 1.5,
                            },
                        },
                        width=0.58,
                        customdata=detail_data[
                            ["player_name", "team_name"]
                        ].to_numpy(),
                        hovertemplate=(
                            "<b>%{customdata[0]}</b> — %{customdata[1]}<br>"
                            f"{selected_metric_definition['axis_title']}: "
                            f"{selected_metric_definition['hover_value']}"
                            "<extra></extra>"
                        ),
                    )
                )

                detail_minimum = min(detail_values, default=0.0)
                detail_maximum = max(detail_values, default=0.0)

                if selected_metric == "plus_minus_per90":
                    if detail_minimum >= 0:
                        detail_right_padding = max(
                            max(detail_maximum, 1.0) * 0.10,
                            0.25,
                        )
                        detail_x_range = [
                            0,
                            detail_maximum + detail_right_padding,
                        ]
                    elif detail_maximum <= 0:
                        detail_left_padding = max(
                            abs(min(detail_minimum, -1.0)) * 0.10,
                            0.25,
                        )
                        detail_x_range = [
                            detail_minimum - detail_left_padding,
                            0,
                        ]
                    else:
                        detail_span = max(detail_maximum - detail_minimum, 1.0)
                        detail_x_range = [
                            detail_minimum - detail_span * 0.08,
                            detail_maximum + detail_span * 0.12,
                        ]
                else:
                    detail_axis_maximum = max(detail_maximum, 1.0)
                    detail_right_padding = max(
                        detail_axis_maximum * 0.10,
                        0.25,
                    )
                    detail_x_range = [
                        0,
                        detail_axis_maximum + detail_right_padding,
                    ]

                detail_figure = style_chart(detail_figure, theme)
                compact_chart_height = max(
                    235,
                    56 * len(selected_players) + 40,
                )

                detail_figure.update_layout(
                    height=compact_chart_height,
                    margin={"l": 138, "r": 24, "t": 8, "b": 40},
                    bargap=0.34,
                )
                detail_figure.update_xaxes(
                    title=selected_metric_definition["axis_title"],
                    range=detail_x_range,
                    tickformat=selected_metric_definition["tickformat"],
                )
                detail_figure.update_yaxes(
                    title=None,
                    autorange="reversed",
                    categoryorder="array",
                    categoryarray=selected_players["chart_label"].tolist(),
                    tickfont={"size": 12, "color": theme["text"]},
                    automargin=True,
                )

                if selected_metric == "plus_minus_per90":
                    detail_figure.add_vline(
                        x=0,
                        line_color=theme["muted"],
                        line_width=1,
                    )

                st.plotly_chart(
                    detail_figure,
                    width="stretch",
                    config={"displayModeBar": False},
                )

                if selected_metric_definition["is_rate"]:
                    st.markdown(
                        '<p class="advanced-metric-note">Per-90 metrics should '
                        'be interpreted alongside minutes played, as short '
                        'appearances can produce extreme values.</p>',
                        unsafe_allow_html=True,
                    )

                # -----------------------------------------------------------------
                # Goalkeeping is shown only when the selection contains a keeper
                # with recorded goalkeeper minutes.
                # -----------------------------------------------------------------
                if selected_players["gk_minutes"].gt(0).any():
                    st.markdown(
                        '<div class="section-label">Goalkeeping</div>',
                        unsafe_allow_html=True,
                    )

                    goalkeeper_scatter_column, goalkeeper_rate_column = st.columns(
                        2,
                        gap="large",
                    )

                    with goalkeeper_scatter_column:
                        st.subheader("Saves and clean sheets")

                        maximum_gk_minutes = max(
                            safe_player_number(selected_players["gk_minutes"].max()),
                            1.0,
                        )
                        goalkeeper_sizes = [
                            18
                            + safe_player_number(value) / maximum_gk_minutes * 30
                            for value in selected_players["gk_minutes"]
                        ]

                        goalkeeper_figure = go.Figure(
                            go.Scatter(
                                x=selected_players["gk_saves"],
                                y=selected_players["gk_clean_sheets"],
                                mode="markers+text",
                                text=selected_players["player_name"].map(
                                    compact_chart_name
                                ),
                                textposition="top center",
                                marker={
                                    "size": goalkeeper_sizes,
                                    "color": selected_player_colours,
                                    "line": {
                                        "color": theme["card_bg"],
                                        "width": 2,
                                    },
                                },
                                customdata=selected_players[
                                    [
                                        "player_name",
                                        "team_name",
                                        "gk_minutes",
                                        "gk_goals_against",
                                    ]
                                ].to_numpy(),
                                hovertemplate=(
                                    "<b>%{customdata[0]}</b> — %{customdata[1]}<br>"
                                    "Saves: %{x:.0f}<br>"
                                    "Clean sheets: %{y:.0f}<br>"
                                    "Goalkeeper minutes: %{customdata[2]:.0f}<br>"
                                    "Goals conceded: %{customdata[3]:.0f}"
                                    "<extra></extra>"
                                ),
                            )
                        )
                        goalkeeper_figure = style_chart(goalkeeper_figure, theme)
                        goalkeeper_figure.update_layout(
                            height=330,
                            margin={"l": 54, "r": 24, "t": 28, "b": 52},
                        )
                        goalkeeper_figure.update_xaxes(
                            title="Saves",
                            rangemode="tozero",
                            dtick=1,
                        )
                        goalkeeper_figure.update_yaxes(
                            title="Clean sheets",
                            rangemode="tozero",
                            dtick=1,
                        )

                        st.plotly_chart(
                            goalkeeper_figure,
                            width="stretch",
                            config={"displayModeBar": False},
                        )

                    with goalkeeper_rate_column:
                        st.subheader("Save percentage")

                        save_percentage_figure = go.Figure()
                        for index, value in enumerate(
                            selected_players["gk_save_pct"].fillna(0)
                        ):
                            save_percentage_figure.add_shape(
                                type="line",
                                x0=0,
                                x1=safe_player_number(value),
                                y0=selected_players["chart_label"].iloc[index],
                                y1=selected_players["chart_label"].iloc[index],
                                xref="x",
                                yref="y",
                                line={
                                    "color": selected_player_colours[index],
                                    "width": 4,
                                },
                            )

                        save_percentage_figure.add_trace(
                            go.Scatter(
                                x=selected_players["gk_save_pct"].fillna(0),
                                y=selected_players["chart_label"],
                                mode="markers",
                                marker={
                                    "size": 17,
                                    "color": selected_player_colours,
                                    "line": {
                                        "color": theme["card_bg"],
                                        "width": 2,
                                    },
                                },
                                customdata=selected_players[
                                    [
                                        "player_name",
                                        "team_name",
                                        "gk_minutes",
                                        "gk_goals_against",
                                    ]
                                ].to_numpy(),
                                hovertemplate=(
                                    "<b>%{customdata[0]}</b> — %{customdata[1]}<br>"
                                    "Save percentage: %{x:.1f}%<br>"
                                    "Goalkeeper minutes: %{customdata[2]:.0f}<br>"
                                    "Goals conceded: %{customdata[3]:.0f}"
                                    "<extra></extra>"
                                ),
                            )
                        )
                        save_percentage_figure = style_chart(
                            save_percentage_figure,
                            theme,
                        )
                        save_percentage_figure.update_layout(
                            height=330,
                            margin={"l": 18, "r": 28, "t": 24, "b": 48},
                        )
                        save_percentage_figure.update_xaxes(
                            title="Save percentage",
                            range=[0, 100],
                            ticksuffix="%",
                        )
                        save_percentage_figure.update_yaxes(
                            title=None,
                            autorange="reversed",
                            tickfont={"size": 12, "color": theme["text"]},
                            automargin=True,
                        )

                        st.plotly_chart(
                            save_percentage_figure,
                            width="stretch",
                            config={"displayModeBar": False},
                        )

            with player_international_tab:
                # -----------------------------------------------------------------
                # International record
                # -----------------------------------------------------------------
                st.markdown(
                    '<div class="section-label">International record</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    '<div class="international-record-heading">Career record</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    (
                        '<div class="international-record-note">'
                        'Grey bars show caps; colour bars show goals. '
                        'The aligned summary gives the scoring rate.'
                        '</div>'
                    ),
                    unsafe_allow_html=True,
                )

                career_chart_data = selected_players.copy()
                career_chart_data["career_caps"] = pd.to_numeric(
                    career_chart_data["career_caps"],
                    errors="coerce",
                ).fillna(0)
                career_chart_data["career_international_goals"] = pd.to_numeric(
                    career_chart_data["career_international_goals"],
                    errors="coerce",
                ).fillna(0)
                career_chart_data["goals_per_cap"] = pd.to_numeric(
                    career_chart_data["goals_per_cap"],
                    errors="coerce",
                ).fillna(0)

                # Ranking by goals produces an immediately useful scoring
                # comparison, while the pale background bar retains the caps
                # context on the same simple count scale.
                career_chart_data = career_chart_data.sort_values(
                    ["career_international_goals", "career_caps"],
                    ascending=[True, True],
                ).reset_index(drop=True)

                career_chart_data["career_label"] = career_chart_data.apply(
                    lambda row: (
                        f"{compact_chart_name(row['player_name'])} — "
                        f"{row['team_name']}"
                    ),
                    axis=1,
                )

                player_colour_lookup = {
                    row["player_label"]: colour
                    for (_, row), colour in zip(
                        selected_players.iterrows(),
                        selected_player_colours,
                    )
                }
                career_chart_data["chart_colour"] = career_chart_data[
                    "player_label"
                ].map(player_colour_lookup).fillna(theme["accent"])

                maximum_caps = max(
                    safe_player_number(career_chart_data["career_caps"].max()),
                    1,
                )
                summary_x = maximum_caps * 1.08
                x_axis_maximum = maximum_caps * 1.46 + 8
                chart_height = max(246, 86 + len(career_chart_data) * 54)

                # One chart, two unambiguous layers: caps are the wider muted
                # context bars and goals are the narrower coloured foreground
                # bars. Text is deliberately placed in a shared right-hand
                # summary column, avoiding the collisions caused by value
                # labels attached to short bars.
                career_record_figure = go.Figure()
                career_record_figure.add_trace(
                    go.Bar(
                        x=career_chart_data["career_caps"],
                        y=career_chart_data["career_label"],
                        orientation="h",
                        name="International caps",
                        marker={
                            "color": "rgba(102, 107, 115, 0.18)",
                            "line": {"color": "rgba(102, 107, 115, 0.13)", "width": 1},
                        },
                        width=0.56,
                        customdata=career_chart_data[
                            [
                                "player_name",
                                "team_name",
                                "career_international_goals",
                                "goals_per_cap",
                            ]
                        ].to_numpy(),
                        hovertemplate=(
                            "<b>%{customdata[0]}</b> — %{customdata[1]}<br>"
                            "International caps: %{x:.0f}<br>"
                            "Career goals: %{customdata[2]:.0f}<br>"
                            "Goals per cap: %{customdata[3]:.2f}"
                            "<extra></extra>"
                        ),
                    )
                )
                career_record_figure.add_trace(
                    go.Bar(
                        x=career_chart_data["career_international_goals"],
                        y=career_chart_data["career_label"],
                        orientation="h",
                        name="Career goals",
                        marker={
                            "color": career_chart_data["chart_colour"].tolist(),
                            "line": {"color": theme["card_bg"], "width": 1},
                        },
                        width=0.34,
                        customdata=career_chart_data[
                            [
                                "player_name",
                                "team_name",
                                "career_caps",
                                "goals_per_cap",
                            ]
                        ].to_numpy(),
                        hovertemplate=(
                            "<b>%{customdata[0]}</b> — %{customdata[1]}<br>"
                            "Career goals: %{x:.0f}<br>"
                            "International caps: %{customdata[2]:.0f}<br>"
                            "Goals per cap: %{customdata[3]:.2f}"
                            "<extra></extra>"
                        ),
                    )
                )

                # The statistics column always starts in the same place, so
                # values remain readable even for players with short bars.
                for row in career_chart_data.itertuples(index=False):
                    career_record_figure.add_annotation(
                        x=summary_x,
                        y=row.career_label,
                        xref="x",
                        yref="y",
                        text=(
                            f"<b>{row.career_caps:.0f}</b> caps  ·  "
                            f"<b>{row.career_international_goals:.0f}</b> goals  ·  "
                            f"{row.goals_per_cap:.2f}/cap"
                        ),
                        showarrow=False,
                        xanchor="left",
                        yanchor="middle",
                        align="left",
                        font={"size": 12, "color": theme["text"]},
                    )

                career_record_figure.add_annotation(
                    x=summary_x,
                    y=1.06,
                    xref="x",
                    yref="paper",
                    text="<b>CAPS  ·  GOALS  ·  GOALS/CAP</b>",
                    showarrow=False,
                    xanchor="left",
                    yanchor="bottom",
                    font={"size": 10, "color": theme["muted"]},
                )

                career_record_figure = style_chart(career_record_figure, theme)
                career_record_figure.update_layout(
                    height=chart_height,
                    margin={"l": 226, "r": 24, "t": 34, "b": 30},
                    barmode="overlay",
                    bargap=0.34,
                    showlegend=False,
                )
                career_record_figure.update_xaxes(
                    title="Career international appearances and goals",
                    range=[0, x_axis_maximum],
                    showgrid=True,
                    gridcolor=theme["grid"],
                    zeroline=False,
                    nticks=6,
                )
                career_record_figure.update_yaxes(
                    title=None,
                    categoryorder="array",
                    categoryarray=career_chart_data["career_label"].tolist(),
                    showgrid=False,
                    tickfont={"size": 12, "color": theme["text"]},
                    automargin=True,
                )

                st.plotly_chart(
                    career_record_figure,
                    width="stretch",
                    config={"displayModeBar": False},
                )


# -----------------------------------------------------------------------------
# Venues tab
# -----------------------------------------------------------------------------
with venues_tab:
    st.markdown(
        """
        <div class="section-label venues-section-label">Host cities</div>
        <div class="venues-title">Selected fixture venues</div>
        """,
        unsafe_allow_html=True,
    )

    matches_per_venue = (
        filtered_matches.groupby("stadium_name", as_index=False)
        .agg(matches=("match_id", "count"))
    )

    venue_map = venues.merge(
        matches_per_venue,
        on="stadium_name",
        how="inner",
    )

    if venue_map.empty:
        st.info("No host venues match the active filters.")

    else:
                # Build a stable, duplicate-free list of venues for one batch request.
        weather_request_venues = (
            venue_map[
                [
                    "stadium_name",
                    "latitude",
                    "longitude",
                ]
            ]
            .dropna(
                subset=[
                    "latitude",
                    "longitude",
                ]
            )
            .drop_duplicates(
                subset="stadium_name"
            )
            .sort_values("stadium_name")
        )

        venue_locations = tuple(
            (
                str(venue.stadium_name),
                float(venue.latitude),
                float(venue.longitude),
            )
            for venue in weather_request_venues.itertuples(
                index=False
            )
        )

        if not venue_locations:
            st.warning(
                "Weather cannot be loaded because the active venues do not "
                "have valid latitude and longitude values."
            )

        else:
            if st.button(
                "Refresh live weather",
                key="refresh_venue_weather",
            ):
                get_current_venue_weather_batch.clear()

            with st.spinner("Loading current weather for host venues..."):
                weather_result = get_current_venue_weather_batch(
                    venue_locations
                )

            if not weather_result["ok"]:
                st.warning(
                    "Current weather could not be retrieved for the active "
                    "host venues."
                )
                st.caption(weather_result["error"])
                st.stop()

            else:
                weather_map = venue_map.merge(
                    pd.DataFrame(weather_result["records"]),
                    on="stadium_name",
                    how="left",
                )

                weather_map = weather_map.loc[
                    weather_map["weather_available"].eq(True)
                ].copy()

                if weather_map.empty:
                    st.warning(
                        "The weather service responded, but no usable live "
                        "weather readings were available for these venues."
                    )

                else:
                    st.markdown(
                        '<div class="section-label">Live venue weather</div>',
                        unsafe_allow_html=True,
                    )

            weather_metric_options = {
                "Temperature (°C)": (
                    "temperature",
                    "Temperature",
                    "°C",
                ),
                "Precipitation (mm)": (
                    "precipitation",
                    "Precipitation",
                    "mm",
                ),
                "Wind speed (km/h)": (
                    "wind_speed",
                    "Wind speed",
                    "km/h",
                ),
                "Humidity (%)": (
                    "humidity",
                    "Humidity",
                    "%",
                ),
            }

            map_control_column, map_note_column = st.columns([1, 2])

            with map_control_column:
                selected_weather_metric = themed_selectbox(
                    "Colour the map by",
                    list(weather_metric_options),
                    key="venue_weather_map_metric",
                    search_placeholder="Filter weather measures",
                )

            with map_note_column:
                
                metric_column, metric_label, metric_unit = (
                weather_metric_options[selected_weather_metric]
            )

            weather_map["metric_value"] = pd.to_numeric(
                weather_map[metric_column],
                errors="coerce",
            )

            weather_map = weather_map.dropna(
                subset=["metric_value"]
            ).copy()

            if weather_map.empty:
                st.info(
                    "The selected weather measure is not available for the "
                    "active venues."
                )

            else:
                metric_values = weather_map["metric_value"]

                def format_weather_metric(value: float) -> str:
                    """Format the selected measure for the summary cards."""
                    if metric_unit == "%":
                        return f"{value:.0f}%"

                    if metric_unit == "km/h":
                        return f"{value:.0f} km/h"

                    return f"{value:.1f} {metric_unit}"

                highest_venue = weather_map.loc[
                    weather_map["metric_value"].idxmax()
                ]

                summary_1, summary_2, summary_3, summary_4 = st.columns(4)

                summary_1.metric(
                    "Reporting venues",
                    f"{len(weather_map)} / {len(venue_map)}",
                )

                summary_2.metric(
                    f"Average {metric_label.lower()}",
                    format_weather_metric(metric_values.mean()),
                )

                summary_3.metric(
                    f"Highest {metric_label.lower()}",
                    format_weather_metric(metric_values.max()),
                )

                summary_4.metric(
                    "Highest at",
                    highest_venue["city"],
                )

                st.caption(
                    f"{highest_venue['stadium_name']} · "
                    f"{highest_venue['city']}, "
                    f"{highest_venue['country']} · "
                    "Weather data is cached for up to 15 minutes."
                )

                metric_minimum = float(metric_values.min())
                metric_maximum = float(metric_values.max())

                # Padding prevents a single shared value, such as 0.0 mm at
                # every venue, from creating an unhelpful colour scale.
                if metric_label == "Precipitation":
                    colour_range = [0, max(metric_maximum, 1.0)]

                elif metric_minimum == metric_maximum:
                    padding = max(abs(metric_minimum) * 0.10, 1.0)
                    colour_range = [
                        metric_minimum - padding,
                        metric_maximum + padding,
                    ]

                else:
                    colour_range = [metric_minimum, metric_maximum]

                # Stronger colour scales make differences easier to see against the
                # pale map and lavender dashboard background.
                if metric_column == "temperature":
                    map_colour_scale = [
                        [0.00, "#7ea0e8"],
                        [0.25, "#5f73c9"],
                        [0.50, "#5b51a9"],
                        [0.75, "#9b4d8b"],
                        [1.00, "#df6548"],
                    ]

                elif metric_column == "precipitation":
                    map_colour_scale = [
                        [0.00, "#b8ccf4"],
                        [0.25, "#779bd8"],
                        [0.50, "#416db8"],
                        [0.75, "#234b8d"],
                        [1.00, "#122d63"],
                    ]

                elif metric_column == "wind_speed":
                    map_colour_scale = [
                        [0.00, "#c7b8e8"],
                        [0.25, "#9678ca"],
                        [0.50, "#6652ad"],
                        [0.75, "#287b95"],
                        [1.00, "#07566c"],
                    ]

                else:
                    # Humidity
                    map_colour_scale = [
                        [0.00, "#e5b7dc"],
                        [0.25, "#c875b6"],
                        [0.50, "#9a468f"],
                        [0.75, "#682b70"],
                        [1.00, "#3c164c"],
                    ]

                figure = px.scatter_geo(
                    weather_map,
                    lat="latitude",
                    lon="longitude",
                    color="metric_value",
                    range_color=colour_range,
                    color_continuous_scale=map_colour_scale,
                    hover_name="stadium_name",
                    custom_data=[
                        "city",
                        "country",
                        "capacity",
                        "elevation_meters",
                        "matches",
                        "temperature",
                        "feels_like",
                        "precipitation",
                        "wind_speed",
                        "humidity",
                        "condition",
                        "observation_time",
                    ],
                    projection="natural earth",
                )

                figure = style_chart(figure, theme)

                figure.update_geos(
                    fitbounds="locations",
                    visible=False,
                    showland=True,
                    landcolor=theme["map_land"],
                    showocean=True,
                    oceancolor=theme["map_ocean"],
                    showcountries=True,
                    countrycolor=theme["border"],
                )

                figure.update_traces(
                    marker={
                        "size": 18,
                        "opacity": 0.98,
                        "line": {
                            "color": "#ffffff",
                            "width": 2,
                        },
                    },
                    hovertemplate=(
                        "<b>%{hovertext}</b><br>"
                        "City: %{customdata[0]}<br>"
                        "Country: %{customdata[1]}<br>"
                        "Capacity: %{customdata[2]:,}<br>"
                        "Elevation: %{customdata[3]:,.0f} m<br>"
                        "Selected fixtures: %{customdata[4]}<br>"
                        "<br>"
                        "Temperature: %{customdata[5]:.1f} °C<br>"
                        "Feels like: %{customdata[6]:.1f} °C<br>"
                        "Precipitation: %{customdata[7]:.1f} mm<br>"
                        "Wind: %{customdata[8]:.0f} km/h<br>"
                        "Humidity: %{customdata[9]:.0f}%<br>"
                        "Condition: %{customdata[10]}<br>"
                        "Observed: %{customdata[11]}"
                        "<extra></extra>"
                    ),
                )

                figure.update_layout(
                    height=580,
                    margin={"l": 0, "r": 24, "t": 24, "b": 0},
                )

                figure.update_coloraxes(
                    colorbar={
                        "title": {
                            "text": f"{metric_label}<br>({metric_unit})",
                            "font": {
                                "color": theme["muted"],
                            },
                        },
                        "tickfont": {
                            "color": theme["muted"],
                        },
                    }
                )

                st.plotly_chart(
                    figure,
                    width="stretch",
                )

                st.markdown(
                    '<div class="section-label">Venue weather details</div>',
                    unsafe_allow_html=True,
                )

                st.caption(
                    f"Ranked from highest to lowest {metric_label.lower()}."
                )

                weather_table = weather_map.sort_values(
                    "metric_value",
                    ascending=False,
                )[
                    [
                        "stadium_name",
                        "city",
                        "country",
                        "condition",
                        "temperature",
                        "feels_like",
                        "precipitation",
                        "wind_speed",
                        "humidity",
                        "matches",
                    ]
                ]

                themed_dataframe(
                    weather_table,
                    width="stretch",
                    hide_index=True,
                    column_config={
                        "stadium_name": st.column_config.TextColumn(
                            "Venue",
                            width="large",
                        ),
                        "city": st.column_config.TextColumn(
                            "City",
                            width="medium",
                        ),
                        "country": st.column_config.TextColumn(
                            "Country",
                            width="medium",
                        ),
                        "condition": st.column_config.TextColumn(
                            "Condition",
                            width="medium",
                        ),
                        "temperature": st.column_config.NumberColumn(
                            "Temperature",
                            format="%.1f °C",
                        ),
                        "feels_like": st.column_config.NumberColumn(
                            "Feels like",
                            format="%.1f °C",
                        ),
                        "precipitation": st.column_config.NumberColumn(
                            "Precipitation",
                            format="%.1f mm",
                        ),
                        "wind_speed": st.column_config.NumberColumn(
                            "Wind",
                            format="%.0f km/h",
                        ),
                        "humidity": st.column_config.NumberColumn(
                            "Humidity",
                            format="%.0f%%",
                        ),
                        "matches": st.column_config.NumberColumn(
                            "Selected fixtures",
                            format="%d",
                        ),
                    },
                )