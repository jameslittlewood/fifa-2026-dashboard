from pathlib import Path
from html import escape
import logging
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
    initial_sidebar_state="expanded",
)


# -----------------------------------------------------------------------------
# Theme setup
# -----------------------------------------------------------------------------
THEMES = {
    "light": {
        # Page and layout
        "app_bg": "#fcfbfb",
        "app_bg_secondary": "#f4f1f1",
        "sidebar_bg": "#fcfbfb",

        # Cards, inputs, tables and charts
        "card_bg": "#ffffff",
        "card_bg_soft": "#f7f4f4",
        "input_bg": "#ffffff",
        "table_bg": "#ffffff",
        "table_header": "#f5f1f1",
        "table_hover": "#fff0f2",
        "chart_bg": "#ffffff",

        # Typography
        "text": "#20242b",
        "muted": "#666b73",

        # Borders and chart gridlines
        "border": "#dfd9d9",
        "grid": "#ebe5e5",

        # St George palette and readable comparison variants
        "accent": "#ce1126",
        "comparison_team_a": "#ce1126",
        "comparison_team_b": "#27313d",
        "comparison_player_3": "#9f1020",
        "comparison_player_4": "#72777f",
        "accent_soft": "#ffe7ea",
        "accent_border": "#edb9c0",

        # Hero/background effects
        "hero_start": "#fff7f8",
        "hero_end": "#ffffff",
        "hero_ring": "rgba(206, 17, 38, 0.11)",

        # Map colours
        "map_land": "#f0ebeb",
        "map_ocean": "#fcfbfb",

        # Shadows
        "shadow": "0 10px 28px rgba(55, 25, 30, 0.08)",
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

            [data-testid="stMetric"] {{
                background: var(--card-bg);
                border: 1px solid var(--border);
                border-radius: 18px;
                padding: 1rem 1.1rem;
                box-shadow: var(--shadow);
            }}

            [data-testid="stMetricLabel"] {{
                color: var(--muted);
                font-size: 0.78rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
            }}

            [data-testid="stMetricValue"] {{
                color: var(--text);
                font-size: 1.8rem;
            }}

            .dashboard-hero {{
                padding: 1.8rem 2rem;
                margin-bottom: 1.2rem;
                border: 1px solid var(--accent-border);
                border-radius: 22px;
                background: linear-gradient(
                    135deg,
                    var(--hero-start),
                    var(--hero-end)
                );
                box-shadow: var(--shadow);
            }}

            .dashboard-hero h1 {{
                margin: 0;
                color: var(--text);
                font-size: clamp(2rem, 4vw, 2.65rem);
            }}

            .dashboard-hero p {{
                margin: 0.55rem 0 0;
                color: var(--muted);
                font-size: 1rem;
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

            .soft-note {{
                margin: 0.6rem 0 1.25rem;
                padding: 0.8rem 1rem;
                border: 1px solid var(--accent-border);
                border-radius: 12px;
                background: var(--accent-soft);
                color: var(--muted);
                font-size: 0.92rem;
            }}

            div[data-testid="stTabs"] button {{
                color: var(--muted);
                font-weight: 600;
            }}

            div[data-testid="stTabs"] button[aria-selected="true"] {{
                color: var(--accent);
                border-bottom-color: var(--accent);
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


            /* Hide the Streamlit header, toolbar, menu, and footer. */
            header[data-testid="stHeader"] {{
                display: none !important;
            }}

            div[data-testid="stToolbar"] {{
                display: none !important;
            }}

            div[data-testid="stDecoration"] {{
                display: none !important;
            }}

            #MainMenu,
            footer {{
                display: none !important;
            }}

            /* Remove the blank space left above the dashboard. */
            section.main > div.block-container {{
                padding-top: 1rem !important;
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
]


@st.cache_data
def load_data(
    data_dir: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Read CSV files and make their data types analysis-ready."""
    matches = pd.read_csv(data_dir / "matches_detailed.csv")
    teams = pd.read_csv(data_dir / "teams.csv")
    venues = pd.read_csv(data_dir / "venues.csv")
    players = pd.read_csv(data_dir / "squads_and_players.csv")
    match_events = pd.read_csv(data_dir / "match_events.csv")

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

    group_lookup = teams[["team_name", "group_letter"]].rename(
        columns={"team_name": "home_team_name"}
    )

    matches = matches.merge(
        group_lookup,
        on="home_team_name",
        how="left",
    )

    return matches, teams, venues, players, match_events


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
    active_match_ids: list[int],
) -> pd.DataFrame:
    """
    Combine player profile data with tournament goal and card totals.

    Tournament event totals only include matches currently selected through
    the sidebar filters.
    """
    team_lookup = teams[
        ["team_id", "team_name"]
    ].drop_duplicates()

    player_stats = players.merge(
        team_lookup,
        on="team_id",
        how="left",
    ).copy()

    # Career international profile measures.
    for column in ["caps", "goals", "height_cm", "market_value_eur"]:
        player_stats[column] = pd.to_numeric(
            player_stats[column],
            errors="coerce",
        )

    player_stats["goals_per_cap"] = (
        player_stats["goals"]
        / player_stats["caps"].replace(0, pd.NA)
    ).fillna(0)

    player_stats["market_value_millions"] = (
        player_stats["market_value_eur"].fillna(0) / 1_000_000
    )

    # Keep only goal and card events from the currently filtered fixtures.
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
        "tournament_goals",
        "yellow_cards",
        "red_cards",
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
                    "Goal": "tournament_goals",
                    "Yellow Card": "yellow_cards",
                    "Red Card": "red_cards",
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
        "tournament_goals",
        "yellow_cards",
        "red_cards",
    ]:
        player_stats[column] = (
            player_stats[column].fillna(0).astype(int)
        )

    player_stats["goal_minutes"] = (
        player_stats["goal_minutes"].fillna("—")
    )

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
) -> object:
    """
    Render a themed single-select control without Streamlit's popup selectbox.

    The selector uses an expander and radio list inside the normal page DOM,
    which avoids the unthemeable BaseWeb portal corners from Streamlit popups.
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

    summary_label = format_func(current_value)
    search_key = f"{key}__search"
    radio_key = f"{key}__radio"

    st.markdown(
        f'<div class="selector-field-label">{escape(label)}</div>',
        unsafe_allow_html=True,
    )

    if help_text:
        st.caption(help_text)

    with st.expander(summary_label, expanded=False):
        filtered_options = option_list

        if len(option_list) > 8:
            search_value = st.text_input(
                f"Search {label}",
                key=search_key,
                placeholder=search_placeholder,
                label_visibility="collapsed",
            ).strip()

            if search_value:
                needle = search_value.casefold()
                filtered_options = [
                    option
                    for option in option_list
                    if needle in format_func(option).casefold()
                ]

        if not filtered_options:
            st.caption("No options match the current search.")
            return current_value

        default_value = (
            current_value
            if current_value in filtered_options
            else filtered_options[0]
        )

        if st.session_state.get(radio_key) not in filtered_options:
            st.session_state[radio_key] = default_value

        selected_value = st.radio(
            f"{label} options",
            filtered_options,
            index=filtered_options.index(default_value),
            format_func=format_func,
            key=radio_key,
            label_visibility="collapsed",
        )

        if selected_value != current_value:
            st.session_state[key] = selected_value
            st.rerun()

    return current_value


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
        height=560,
        hovermode="closest",
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
):
    """
    Create a ranked horizontal bar chart showing goals scored minus xG.

    Positive values mean a team has scored more goals than its xG.
    Negative values mean a team has scored fewer goals than its xG.
    """
    chart_data = team_stats.loc[
        team_stats["played"].gt(0)
    ].copy()

    if chart_data.empty:
        return None

    chart_data["goal_delta"] = (
        chart_data["goals_for"] - chart_data["xg_for"]
    )

    chart_data = chart_data.sort_values(
        "goal_delta",
        ascending=True,
    )

    highlighted_colours = get_highlighted_team_colours(
        highlighted_teams,
        active_theme,
    )

    # Keep selected teams fully vivid, while fading all other teams into
    # the background so the active selection is immediately clearer.
    unselected_bar_opacity = 0.24

    muted_hex = active_theme["muted"].lstrip("#")

    muted_bar_colour = (
        f"rgba("
        f"{int(muted_hex[0:2], 16)}, "
        f"{int(muted_hex[2:4], 16)}, "
        f"{int(muted_hex[4:6], 16)}, "
        f"{unselected_bar_opacity}"
        f")"
    )

    chart_data["bar_colour"] = (
        chart_data["team_name"]
        .map(highlighted_colours)
        .fillna(muted_bar_colour)
    )

    figure = go.Figure()

    figure.add_trace(
        go.Bar(
            x=chart_data["goal_delta"],
            y=chart_data["team_name"],
            orientation="h",
            customdata=chart_data[
                [
                    "goals_for",
                    "xg_for",
                    "played",
                ]
            ].to_numpy(),
            marker={
                "color": chart_data["bar_colour"].tolist(),
                "line": {
                    "color": active_theme["card_bg"],
                    "width": 0.7,
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
            "width": 1.3,
        },
    )

    figure = style_chart(figure, active_theme)

    chart_height = max(
        520,
        min(1100, len(chart_data) * 28 + 120),
    )

    figure.update_layout(
        height=chart_height,
        margin={
            "l": 170,
            "r": 30,
            "t": 24,
            "b": 45,
        },
    )

    figure.update_xaxes(
        title="Goals scored minus expected goals (xG)",
        showgrid=True,
        gridcolor=active_theme["grid"],
        zeroline=False,
    )

    figure.update_yaxes(
        title=None,
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
        height=370,
        showlegend=True,
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
        },
    )

    figure.update_yaxes(
        title="Value",
        rangemode="tozero",
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


@st.cache_data(ttl=900, show_spinner=False)
def get_current_venue_weather_batch(
    venue_locations: tuple[tuple[str, float, float], ...],
) -> dict[str, object]:
    """
    Retrieve live weather for all visible venues in one Open-Meteo request.

    The result is cached for 15 minutes. Using one request prevents a slow
    venue from holding up every other stadium's weather details.
    """
    if not venue_locations:
        return {
            "ok": True,
            "records": [],
            "error": None,
        }

    api_url = "https://api.open-meteo.com/v1/forecast"

    parameters = {
        "latitude": ",".join(
            f"{latitude:.6f}"
            for _, latitude, _ in venue_locations
        ),
        "longitude": ",".join(
            f"{longitude:.6f}"
            for _, _, longitude in venue_locations
        ),
        "current": (
            "temperature_2m,"
            "apparent_temperature,"
            "relative_humidity_2m,"
            "precipitation,"
            "weather_code,"
            "wind_speed_10m"
        ),
        "temperature_unit": "celsius",
        "wind_speed_unit": "kmh",
    }

    try:
        response = requests.get(
            api_url,
            params=parameters,
            timeout=6,
        )
        response.raise_for_status()
        response_payload = response.json()

    except requests.Timeout:
        LOGGER.warning("Open-Meteo venue-weather request timed out.")

        return {
            "ok": False,
            "records": [],
            "error": (
                "The weather service took too long to respond. "
                "Please try Refresh live weather."
            ),
        }

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
            "Open-Meteo venue weather failed. "
            "status=%s url=%s body=%s",
            status_code,
            error.response.url if error.response is not None else api_url,
            response_body,
        )

        return {
            "ok": False,
            "records": [],
            "error": (
                "The weather provider rejected this request "
                f"(HTTP {status_code})."
            ),
        }

    except requests.RequestException as error:
        LOGGER.warning(
            "Open-Meteo venue weather connection failed: %s",
            error,
        )

        return {
            "ok": False,
            "records": [],
            "error": (
                "The weather service could not be reached "
                f"({type(error).__name__})."
            ),
        }

    except ValueError:
        LOGGER.warning(
            "Open-Meteo venue-weather response could not be read."
        )

        return {
            "ok": False,
            "records": [],
            "error": (
                "The weather service returned an unreadable response."
            ),
        }

    weather_payloads = (
        response_payload
        if isinstance(response_payload, list)
        else [response_payload]
    )

    if len(weather_payloads) != len(venue_locations):
        LOGGER.warning(
            "Open-Meteo returned %s venue results for %s requests.",
            len(weather_payloads),
            len(venue_locations),
        )

        return {
            "ok": False,
            "records": [],
            "error": (
                "The weather service returned an incomplete venue response."
            ),
        }

    weather_records = []

    for (
        stadium_name,
        _,
        _,
    ), venue_payload in zip(
        venue_locations,
        weather_payloads,
    ):
        current_weather = (
            venue_payload.get("current", {})
            if isinstance(venue_payload, dict)
            else {}
        )

        weather_code = current_weather.get("weather_code")

        weather_records.append(
            {
                "stadium_name": stadium_name,
                "weather_available": bool(current_weather),
                "observation_time": current_weather.get("time"),
                "temperature": current_weather.get("temperature_2m"),
                "feels_like": current_weather.get(
                    "apparent_temperature"
                ),
                "humidity": current_weather.get(
                    "relative_humidity_2m"
                ),
                "precipitation": current_weather.get(
                    "precipitation"
                ),
                "wind_speed": current_weather.get("wind_speed_10m"),
                "condition": (
                    get_weather_description(int(weather_code))
                    if weather_code is not None
                    and pd.notna(weather_code)
                    else "Weather unavailable"
                ),
            }
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
    Retrieve hourly weather nearest to a fixture's kick-off time.

    Past fixtures use Open-Meteo's historical endpoint.
    Upcoming fixtures use Open-Meteo's forecast endpoint.
    """

    kickoff_utc = pd.to_datetime(kickoff_utc_iso, utc=True)
    current_time_utc = pd.Timestamp.now(tz="UTC")

    weather_fields = [
        "temperature_2m",
        "apparent_temperature",
        "precipitation",
        "weather_code",
        "wind_speed_10m",
    ]

    # A completed or past fixture uses historical modelled weather data.
    if kickoff_utc <= current_time_utc:
        api_url = "https://archive-api.open-meteo.com/v1/archive"

        weather_type = "historical"

        parameters = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": kickoff_utc.strftime("%Y-%m-%d"),
            "end_date": kickoff_utc.strftime("%Y-%m-%d"),
            "hourly": ",".join(
                weather_fields + ["relative_humidity_2m"]
            ),
            "timezone": "UTC",
        }

    # A future fixture uses forecast data, provided it is close enough.
    else:
        forecast_limit = current_time_utc + pd.Timedelta(days=16)

        if kickoff_utc > forecast_limit:
            return {
                "status": "unavailable",
                "message": (
                    "Forecasts are available once a fixture is within "
                    "16 days of kick-off."
                ),
            }

        api_url = "https://api.open-meteo.com/v1/forecast"

        weather_type = "forecast"

        parameters = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": kickoff_utc.strftime("%Y-%m-%d"),
            "end_date": kickoff_utc.strftime("%Y-%m-%d"),
            "hourly": ",".join(
                weather_fields + ["precipitation_probability"]
            ),
            "timezone": "UTC",
        }

    try:
        response = requests.get(
            api_url,
            params=parameters,
            timeout=15,
        )

        response.raise_for_status()

        response_data = response.json()
        hourly_data = response_data.get("hourly")

        if not hourly_data:
            return {
                "status": "error",
                "message": "No hourly weather data was returned.",
            }

        hourly_weather = pd.DataFrame(hourly_data)

        if hourly_weather.empty:
            return {
                "status": "error",
                "message": "No hourly weather data was returned.",
            }

        hourly_weather["time"] = pd.to_datetime(
            hourly_weather["time"],
            utc=True,
            errors="coerce",
        )

        hourly_weather = hourly_weather.dropna(subset=["time"])

        nearest_row_index = (
            hourly_weather["time"] - kickoff_utc
        ).abs().idxmin()

        weather_row = hourly_weather.loc[nearest_row_index]

        def optional_number(value):
            """Return a float where possible, otherwise None."""
            return None if pd.isna(value) else float(value)

        nearest_time_uk = weather_row["time"].tz_convert(
            "Europe/London"
        )

        return {
            "status": "available",
            "weather_type": weather_type,
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
            "rain_probability": optional_number(
                weather_row.get("precipitation_probability")
            ),
            "weather_code": int(weather_row["weather_code"]),
        }

    except (
        requests.RequestException,
        ValueError,
        KeyError,
        TypeError,
    ):
        return {
            "status": "error",
            "message": (
                "Weather data could not be retrieved. "
                "Check your internet connection and try again."
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

matches, teams, venues, players, match_events = load_data(DATA_DIR)


# -----------------------------------------------------------------------------
# Sidebar filters
# -----------------------------------------------------------------------------
statuses = sorted(matches["status"].dropna().unique())
groups = sorted(matches["group_letter"].dropna().unique())
countries = sorted(matches["country"].dropna().unique())

min_date = matches["date"].min().date()
max_date = matches["date"].max().date()

# Default values are stored once so filters keep their selections while the
# dashboard reruns after a user changes a control.
filter_defaults = {
    "filter_status_mode": "All",
    "filter_all_groups": True,
    "filter_specific_groups": groups,
    "filter_all_countries": True,
    "filter_date_preset": "All tournament",
    "filter_custom_date_range": (min_date, max_date),
}

for filter_key, default_value in filter_defaults.items():
    if filter_key not in st.session_state:
        st.session_state[filter_key] = default_value

for country in countries:
    country_key = f"filter_country_{country}"

    if country_key not in st.session_state:
        st.session_state[country_key] = True


with st.sidebar:
    st.markdown("### Filters")

    reset_clicked = st.button(
        "Reset filters",
        key="reset_dashboard_filters",
        use_container_width=True,
    )

    # Reset must happen before the filter widgets are created below.
    if reset_clicked:
        st.session_state["filter_status_mode"] = "All"
        st.session_state["filter_all_groups"] = True
        st.session_state["filter_specific_groups"] = groups
        st.session_state["filter_all_countries"] = True
        st.session_state["filter_date_preset"] = "All tournament"
        st.session_state["filter_custom_date_range"] = (
            min_date,
            max_date,
        )

        for country in countries:
            st.session_state[f"filter_country_{country}"] = True

        st.rerun()

    # -------------------------------------------------------------------------
    # Match status
    # -------------------------------------------------------------------------
    status_mode = st.radio(
    "Match status",
    ["All", *statuses],
    key="filter_status_mode",
)

    selected_statuses = (
        statuses
        if status_mode == "All"
        else [status_mode]
    )

    # -------------------------------------------------------------------------
    # Group filter
    # -------------------------------------------------------------------------
    st.markdown("**Group**")

    all_groups_selected = st.toggle(
        "All groups",
        key="filter_all_groups",
    )

    if all_groups_selected:
        selected_groups = groups

    else:
        selected_groups = st.multiselect(
            "Choose groups",
            groups,
            key="filter_specific_groups",
            placeholder="Select one or more groups",
        )

        if not selected_groups:
            st.warning(
                "Choose at least one group, or turn All groups back on."
            )

    # -------------------------------------------------------------------------
    # Host-country filter
    # -------------------------------------------------------------------------
    st.markdown("**Host country**")

    all_countries_selected = st.toggle(
        "All host countries",
        key="filter_all_countries",
    )

    if all_countries_selected:
        selected_countries = countries

    else:
        country_columns = st.columns(len(countries))
        selected_countries = []

        for country, country_column in zip(
            countries,
            country_columns,
        ):
            with country_column:
                is_selected = st.checkbox(
                    country,
                    key=f"filter_country_{country}",
                )

                if is_selected:
                    selected_countries.append(country)

        if not selected_countries:
            st.warning(
                "Choose at least one host country, or turn All host "
                "countries back on."
            )

    # -------------------------------------------------------------------------
    # Date controls
    # -------------------------------------------------------------------------
    completed_dates = matches.loc[
        matches["status"].eq("Completed"),
        "date",
    ].dropna()

    st.markdown(
        '<div class="filter-panel-heading">Date and advanced filters</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="filter-panel-note">Focus the dashboard on a specific '
        'phase of the tournament or a custom date window.</div>',
        unsafe_allow_html=True,
    )

    date_preset = st.radio(
    "Quick range",
    [
        "All tournament",
        "Completed matches",
        "Next 7 days",
        "Custom range",
    ],
    key="filter_date_preset",
)

    if date_preset == "All tournament":
        start_date = pd.Timestamp(min_date)
        end_date = pd.Timestamp(max_date)

    elif date_preset == "Completed matches":
        if completed_dates.empty:
            start_date = pd.Timestamp(min_date)
            end_date = pd.Timestamp(max_date)

            st.caption(
                "No completed fixtures are available, so the full "
                "tournament date range is shown."
            )

        else:
            start_date = completed_dates.min()
            end_date = completed_dates.max()

    elif date_preset == "Next 7 days":
        today = pd.Timestamp.now(
            tz="Europe/London"
        ).tz_localize(None).normalize()

        start_date = max(
            pd.Timestamp(min_date),
            min(today, pd.Timestamp(max_date)),
        )

        end_date = min(
            pd.Timestamp(max_date),
            start_date + pd.Timedelta(days=7),
        )

        st.caption(
            f"Showing fixtures from {start_date.strftime('%d %b %Y')} "
            f"to {end_date.strftime('%d %b %Y')}."
        )

    else:
        selected_dates = st.date_input(
            "Date range",
            min_value=min_date,
            max_value=max_date,
            key="filter_custom_date_range",
        )

        if (
            isinstance(selected_dates, (tuple, list))
            and len(selected_dates) == 2
        ):
            start_date, end_date = map(
                pd.Timestamp,
                selected_dates,
            )

        else:
            start_date = pd.Timestamp(selected_dates)
            end_date = pd.Timestamp(selected_dates)

    # -------------------------------------------------------------------------
    # Active filter summary
    # -------------------------------------------------------------------------
    preview_count = len(
        matches.loc[
            matches["status"].isin(selected_statuses)
            & matches["group_letter"].isin(selected_groups)
            & matches["country"].isin(selected_countries)
            & matches["date"].between(start_date, end_date)
        ]
    )

    status_summary = (
        "All matches"
        if status_mode == "All"
        else status_mode
    )

    group_summary = (
        "All groups"
        if all_groups_selected
        else ", ".join(selected_groups)
    )

    country_summary = (
        "All host countries"
        if all_countries_selected
        else ", ".join(selected_countries)
    )

    st.divider()

    st.caption(f"**Showing {preview_count} fixtures**")

    st.caption(
        f"{status_summary} · {group_summary} · {country_summary}"
    )

    st.caption(
        f"{start_date.strftime('%d %b %Y')} – "
        f"{end_date.strftime('%d %b %Y')}"
    )

filtered_matches = matches.loc[
    matches["status"].isin(selected_statuses)
    & matches["group_letter"].isin(selected_groups)
    & matches["country"].isin(selected_countries)
    & matches["date"].between(start_date, end_date)
].copy()

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
    active_match_ids,
)

active_team_ids = teams.loc[
    teams["group_letter"].isin(selected_groups),
    "team_id",
].tolist()

player_tournament_stats = player_tournament_stats.loc[
    player_tournament_stats["team_id"].isin(active_team_ids)
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

st.markdown(
    """
    <div class="soft-note">
        Dataset explorer: some results, expected-goals values and event records
        may be generated rather than official.
    </div>
    """,
    unsafe_allow_html=True,
)

goals = completed["home_score"].sum() + completed["away_score"].sum()
xg = completed["home_xg"].sum() + completed["away_xg"].sum()

st.markdown(
    '<div class="section-label">Tournament snapshot</div>',
    unsafe_allow_html=True,
)

metric_1, metric_2, metric_3, metric_4 = st.columns(4)

metric_1.metric("Fixtures shown", len(filtered_matches))
metric_2.metric("Completed matches", len(completed))
metric_3.metric("Scheduled matches", len(scheduled))

metric_4.metric(
    "Goals vs xG",
    f"{int(goals)} / {xg:.1f}"
    if not completed.empty
    else "No results",
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

    st.subheader("Fixtures and results")

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

    fixture_table = make_fixture_table(fixture_weather_rows)

    fixture_table_event = themed_dataframe(
        fixture_table,
        height=320,
        hide_index=True,
        column_config={
            "kickoff (UK)": {"label": "Kick-off"},
            "fixture": {"label": "Fixture"},
            "score": {"label": "Score"},
            "xG": {"label": "xG"},
            "status": {"label": "Status"},
            "group_letter": {"label": "Group"},
            "stadium_name": {"label": "Venue"},
            "city": {"label": "City"},
            "referee_name": {"label": "Referee"},
        },
        on_select="rerun",
        selection_mode="single-row",
        key="fixture_table_selector",
    )

    st.markdown(
        '<div class="section-label">Fixture weather</div>',
        unsafe_allow_html=True,
    )

    st.subheader("Weather at kick-off")

    if fixture_weather_rows.empty:
        st.info("No fixtures match the current sidebar filters.")
    else:
        selected_rows = fixture_table_event.selection.rows

        if not selected_rows:
            st.info(
                "Select a fixture row in the table above to view weather at kick-off."
            )

        else:
            selected_fixture = fixture_weather_rows.iloc[selected_rows[0]]

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
                    weather_description = get_weather_description(
                        fixture_weather["weather_code"]
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

    st.subheader("Overall team table")

    st.caption(
        "Teams are ranked using the active sidebar filters. "
        "The table uses points, goal difference and goals scored. "
        "It is a comparison view rather than an official FIFA tournament table."
    )

    # Keep only teams from the groups currently selected in the sidebar.
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
        column_config={
            "rank": st.column_config.NumberColumn(
                "Rank",
                format="%d",
                width="small",
            ),
            "team_name": st.column_config.TextColumn(
                "Team",
                width="large",
            ),
            "group_letter": st.column_config.TextColumn(
                "Group",
                width="small",
            ),
            "played": st.column_config.NumberColumn(
                "P",
                format="%d",
                width="small",
            ),
            "won": st.column_config.NumberColumn(
                "W",
                format="%d",
                width="small",
            ),
            "drawn": st.column_config.NumberColumn(
                "D",
                format="%d",
                width="small",
            ),
            "lost": st.column_config.NumberColumn(
                "L",
                format="%d",
                width="small",
            ),
            "goals_for": st.column_config.NumberColumn(
                "GF",
                format="%d",
                width="small",
            ),
            "goals_against": st.column_config.NumberColumn(
                "GA",
                format="%d",
                width="small",
            ),
            "goal_difference": st.column_config.NumberColumn(
                "GD",
                format="%+d",
                width="small",
            ),
            "xg_difference": st.column_config.NumberColumn(
                "xG diff",
                format="%+.2f",
                width="small",
            ),
            "points": st.column_config.NumberColumn(
                "Pts",
                format="%d",
                width="small",
            ),
            "points_per_game": st.column_config.NumberColumn(
                "PPG",
                format="%.2f",
                width="small",
            ),
        },
    )


# -----------------------------------------------------------------------------
# Teams tab
# -----------------------------------------------------------------------------
with teams_tab:
    st.markdown(
        '<div class="section-label">Team analysis</div>',
        unsafe_allow_html=True,
    )

    st.subheader("Explore or compare national teams")

    def reset_compare_team_defaults() -> None:
        """Restore the default matchup whenever Compare teams is selected."""
        if st.session_state.get("teams_view_mode") != "Compare teams":
            return

        for selector_key, team_name in {
            "compare_team_a": "England",
            "compare_team_b": "Argentina",
        }.items():
            st.session_state[selector_key] = team_name
            # themed_selectbox stores the expanded radio choice separately.
            # Keep it in sync with the closed selector summary.
            st.session_state[f"{selector_key}__radio"] = team_name
            st.session_state.pop(f"{selector_key}__search", None)

    team_view = st.radio(
        "Choose a Teams view",
        [
            "Team profile",
            "Compare teams",
        ],
        horizontal=True,
        key="teams_view_mode",
        on_change=reset_compare_team_defaults,
    )

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

    # -------------------------------------------------------------------------
    # Single-team profile mode
    # -------------------------------------------------------------------------
    if team_view == "Team profile":
        selected_team = themed_selectbox(
            "Choose a team",
            team_options,
            key="profile_team_selector",
            search_placeholder="Filter teams",
        )

        team_row = filtered_team_stats.loc[
            filtered_team_stats["team_name"].eq(selected_team)
        ].iloc[0]

        team_id = teams.loc[
            teams["team_name"].eq(selected_team),
            "team_id",
        ].iloc[0]

        team_matches = filtered_matches.loc[
            filtered_matches["home_team_name"].eq(selected_team)
            | filtered_matches["away_team_name"].eq(selected_team)
        ].copy()

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
            '<div class="section-label">Tournament record</div>',
            unsafe_allow_html=True,
        )

        profile_metric_1, profile_metric_2, profile_metric_3, profile_metric_4 = (
            st.columns(4)
        )

        profile_metric_1.metric(
            "Played",
            int(team_row["played"]),
        )

        profile_metric_2.metric(
            "Points",
            int(team_row["points"]),
        )

        profile_metric_3.metric(
            "Goals scored",
            int(team_row["goals_for"]),
        )

        profile_metric_4.metric(
            "Goals conceded",
            int(team_row["goals_against"]),
        )

        st.markdown(
            '<div class="section-label">Performance detail</div>',
            unsafe_allow_html=True,
        )

        detail_metric_1, detail_metric_2, detail_metric_3, detail_metric_4 = (
            st.columns(4)
        )

        detail_metric_1.metric(
            "Goal difference",
            f"{int(team_row['goal_difference']):+d}",
        )

        detail_metric_2.metric(
            "xG difference",
            f"{float(team_row['xg_difference']):+.2f}",
        )

        detail_metric_3.metric(
            "Points per game",
            f"{points_per_game:.2f}",
        )

        detail_metric_4.metric(
            "Elo rating",
            int(team_row["elo_rating"]),
        )

        st.markdown(
            '<div class="section-label">Squad context</div>',
            unsafe_allow_html=True,
        )

        squad_metric_1, squad_metric_2, squad_metric_3, squad_metric_4 = (
            st.columns(4)
        )

        squad_metric_1.metric(
            "Squad size",
            squad_summary["squad_size"],
        )

        squad_metric_2.metric(
            "Average caps",
            f"{squad_summary['average_caps']:.1f}",
        )

        squad_metric_3.metric(
            "International goals",
            squad_summary["international_goals"],
        )

        squad_metric_4.metric(
            "Dataset squad value",
            format_euro_millions(
                squad_summary["market_value"]
            ),
        )

        st.markdown(
            '<div class="section-label">Team finishing</div>',
            unsafe_allow_html=True,
        )

        st.subheader(
            f"{selected_team}: goals scored versus expected goals"
        )

        if int(team_row["played"]) == 0:
            st.info(
                f"{selected_team} has no completed matches within the "
                "current sidebar filters."
            )

        else:
            selected_team_goal_delta = (
                float(team_row["goals_for"])
                - float(team_row["xg_for"])
            )

            finishing_metric, finishing_explanation = st.columns(
                [1, 2]
            )

            finishing_metric.metric(
                "Goals minus xG",
                f"{selected_team_goal_delta:+.2f}",
                delta=(
                    f"{int(team_row['goals_for'])} goals from "
                    f"{float(team_row['xg_for']):.2f} xG"
                ),
                delta_color="off",
            )

            with finishing_explanation:
                st.caption(
                    "A positive value means the team has scored more than "
                    "its expected-goals total. A negative value means it "
                    "has scored fewer."
                )

            finishing_figure = create_team_finishing_chart(
                filtered_team_stats,
                [selected_team],
                theme,
            )

            st.plotly_chart(
                finishing_figure,
                width="stretch",
            )

            st.caption(
                "The dashed line represents a team scoring exactly in line "
                "with expected goals. Teams above the line have scored more "
                "than their xG; teams below it have scored fewer."
            )

            st.markdown(
                '<div class="section-label">Goals minus xG ranking</div>',
                unsafe_allow_html=True,
            )

            st.subheader("Where teams are finishing above or below xG")

            goal_delta_figure = create_goals_minus_xg_chart(
                filtered_team_stats,
                [selected_team],
                theme,
            )

            st.plotly_chart(
                goal_delta_figure,
                width="stretch",
            )

            st.caption(
                "Red marks the selected team. Teams to the right of zero "
                "have scored more goals than expected; teams to the left "
                "have scored fewer."
            )

        # ---------------------------------------------------------------------
        # Team fixtures: full-width table
        # ---------------------------------------------------------------------
        st.markdown(
            '<div class="section-label">Match centre</div>',
            unsafe_allow_html=True,
        )

        st.subheader("Fixtures and results")

        themed_dataframe(
            make_fixture_table(team_matches),
            width="stretch",
            hide_index=True,
            height=260,
            column_config={
                "kickoff (UK)": st.column_config.TextColumn(
                    "Kick-off",
                    width="medium",
                ),
                "fixture": st.column_config.TextColumn(
                    "Fixture",
                    width="large",
                ),
                "score": st.column_config.TextColumn(
                    "Score",
                    width="small",
                ),
                "xG": st.column_config.TextColumn(
                    "xG",
                    width="small",
                ),
                "status": st.column_config.TextColumn(
                    "Status",
                    width="small",
                ),
                "group_letter": st.column_config.TextColumn(
                    "Group",
                    width="small",
                ),
                "stadium_name": st.column_config.TextColumn(
                    "Venue",
                    width="large",
                ),
                "city": st.column_config.TextColumn(
                    "City",
                    width="medium",
                ),
                "referee_name": st.column_config.TextColumn(
                    "Referee",
                    width="medium",
                ),
            },
        )

        # ---------------------------------------------------------------------
        # Team squad: full-width table
        # ---------------------------------------------------------------------
        st.markdown(
            '<div class="section-label">Squad profile</div>',
            unsafe_allow_html=True,
        )

        st.subheader("Players")

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
            height=420,
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
        st.caption(
            "Team A is shown in Red. Team B is shown in Black."
        )

        # Set a valid first-time fallback before either themed selector renders.
        # Previously this ran after Team A had already defaulted to the first
        # alphabetical option (Algeria), so England could never be applied.
        default_team_a = pick_option_by_label(
            team_options,
            "England",
            lambda option: option,
        )
        if default_team_a is None:
            default_team_a = team_options[0]

        if st.session_state.get("compare_team_a") not in team_options:
            st.session_state["compare_team_a"] = default_team_a
            st.session_state["compare_team_a__radio"] = default_team_a

        team_b_options = [
            team_name
            for team_name in team_options
            if team_name != st.session_state["compare_team_a"]
        ]

        default_team_b = pick_option_by_label(
            team_b_options,
            "Argentina",
            lambda option: option,
        )
        if default_team_b is None:
            default_team_b = team_b_options[0]

        if st.session_state.get("compare_team_b") not in team_b_options:
            st.session_state["compare_team_b"] = default_team_b
            st.session_state["compare_team_b__radio"] = default_team_b

        team_a_column, team_b_column = st.columns(2)

        with team_a_column:
            selected_team_a = themed_selectbox(
                "Choose Team A",
                team_options,
                key="compare_team_a",
                search_placeholder="Filter teams",
            )

        # Build Team B's choices after Team A is resolved, so the same team
        # cannot be selected on both sides.
        team_b_options = [
            team_name
            for team_name in team_options
            if team_name != selected_team_a
        ]

        if st.session_state.get("compare_team_b") not in team_b_options:
            st.session_state["compare_team_b"] = default_team_b
            st.session_state["compare_team_b__radio"] = default_team_b

        with team_b_column:
            selected_team_b = themed_selectbox(
                "Choose Team B",
                team_b_options,
                key="compare_team_b",
                search_placeholder="Filter teams",
            )

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
            '<div class="section-label">Head-to-head performance</div>',
            unsafe_allow_html=True,
        )

        st.subheader("Tournament performance comparison")

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
        )

        st.markdown(
            '<div class="section-label">Team finishing</div>',
            unsafe_allow_html=True,
        )

        st.subheader("Goals scored versus expected goals")

        highlighted_teams = []

        if int(team_a_row["played"]) > 0:
            highlighted_teams.append(selected_team_a)

        if int(team_b_row["played"]) > 0:
            highlighted_teams.append(selected_team_b)

        if not highlighted_teams:
            st.info(
                "Neither selected team has completed matches within the "
                "current sidebar filters."
            )

        else:
            finishing_metric_a, finishing_metric_b = st.columns(2)

            if int(team_a_row["played"]) > 0:
                team_a_goal_delta = (
                    float(team_a_row["goals_for"])
                    - float(team_a_row["xg_for"])
                )

                finishing_metric_a.metric(
                    f"{selected_team_a} goals minus xG",
                    f"{team_a_goal_delta:+.2f}",
                    delta=(
                        f"{int(team_a_row['goals_for'])} goals from "
                        f"{float(team_a_row['xg_for']):.2f} xG"
                    ),
                    delta_color="off",
                )

            else:
                finishing_metric_a.metric(
                    f"{selected_team_a} goals minus xG",
                    "No completed matches",
                )

            if int(team_b_row["played"]) > 0:
                team_b_goal_delta = (
                    float(team_b_row["goals_for"])
                    - float(team_b_row["xg_for"])
                )

                finishing_metric_b.metric(
                    f"{selected_team_b} goals minus xG",
                    f"{team_b_goal_delta:+.2f}",
                    delta=(
                        f"{int(team_b_row['goals_for'])} goals from "
                        f"{float(team_b_row['xg_for']):.2f} xG"
                    ),
                    delta_color="off",
                )

            else:
                finishing_metric_b.metric(
                    f"{selected_team_b} goals minus xG",
                    "No completed matches",
                )

            finishing_figure = create_team_finishing_chart(
                filtered_team_stats,
                highlighted_teams,
                theme,
            )

            st.plotly_chart(
                finishing_figure,
                width="stretch",
            )

            st.caption(
                "Red marks Team A and Black marks Team B. The dashed line "
                "represents a team scoring exactly in line with expected "
                "goals. Teams above it have scored more than their xG; "
                "teams below it have scored fewer."
            )

            st.markdown(
                '<div class="section-label">Goals minus xG ranking</div>',
                unsafe_allow_html=True,
            )

            st.subheader("Where teams are finishing above or below xG")

            goal_delta_figure = create_goals_minus_xg_chart(
                filtered_team_stats,
                highlighted_teams,
                theme,
            )

            st.plotly_chart(
                goal_delta_figure,
                width="stretch",
            )

            st.caption(
                "Red marks Team A and Black marks Team B. Teams to the "
                "right of zero have scored more goals than expected; teams "
                "to the left have scored fewer."
            )

        st.markdown(
            '<div class="section-label">Fixtures and results</div>',
            unsafe_allow_html=True,
        )

        team_a_matches = filtered_matches.loc[
            filtered_matches["home_team_name"].eq(selected_team_a)
            | filtered_matches["away_team_name"].eq(selected_team_a)
        ].copy()

        team_b_matches = filtered_matches.loc[
            filtered_matches["home_team_name"].eq(selected_team_b)
            | filtered_matches["away_team_name"].eq(selected_team_b)
        ].copy()

        team_a_fixture_column, team_b_fixture_column = st.columns(
            2,
            gap="large",
        )

        with team_a_fixture_column:
            st.subheader(selected_team_a)

            themed_dataframe(
                make_fixture_table(team_a_matches),
                width="stretch",
                hide_index=True,
                height=330,
            )

        with team_b_fixture_column:
            st.subheader(selected_team_b)

            themed_dataframe(
                make_fixture_table(team_b_matches),
                width="stretch",
                hide_index=True,
                height=330,
            )

# -----------------------------------------------------------------------------
# Players tab
# -----------------------------------------------------------------------------
with players_tab:
    st.markdown(
        '<div class="section-label">Player comparison</div>',
        unsafe_allow_html=True,
    )

    st.subheader("Compare up to four players")

    st.caption(
        "Tournament goals and cards follow the current fixture filters. "
        "Caps, career international goals, club, height and market value "
        "come from player-profile data in the scenario dataset."
    )

    # -------------------------------------------------------------------------
    # Position filter
    # -------------------------------------------------------------------------
    position_options = ["All positions"] + sorted(
        player_tournament_stats["position"].dropna().unique()
    )

    selected_position = themed_selectbox(
        "Filter available players by position",
        position_options,
        key="player_position_filter",
        search_placeholder="Filter positions",
    )

    available_players = player_tournament_stats.copy()

    if selected_position != "All positions":
        available_players = available_players.loc[
            available_players["position"].eq(selected_position)
        ].copy()

    if available_players.empty:
        st.info(
            "No players match the selected position and current sidebar filters."
        )

    else:
        # ---------------------------------------------------------------------
        # Player dropdown setup
        # ---------------------------------------------------------------------
        player_label_lookup = (
            available_players.set_index("player_id")["player_label"].to_dict()
        )

        # None is the "No player selected" option.
        player_selector_options = [
            None,
            *available_players["player_id"].tolist(),
        ]

        def format_player_option(player_id):
            """Turn a player ID into a readable dropdown label."""
            if player_id is None:
                return "No player selected"

            return player_label_lookup[player_id]

        player_name_lookup = (
            available_players.set_index("player_id")["player_name"].to_dict()
        )

        # On first load, use the intended four-player comparison. If a position
        # filter later removes a chosen player, replace only that invalid value.
        default_player_labels = {
            "player_1_selector": "Harry Edward Kane",
            "player_2_selector": "Michael Akpovie Olise",
            "player_3_selector": "Lionel Andrés Messi",
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
                    available_players["player_id"].tolist(),
                    desired_label,
                    lambda player_id: player_name_lookup[player_id],
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

        st.markdown(
            '<div class="section-label">Choose players</div>',
            unsafe_allow_html=True,
        )

        player_1_column, player_2_column = st.columns(2)

        with player_1_column:
            selected_player_1 = themed_selectbox(
                "Player 1",
                player_selector_options,
                format_func=format_player_option,
                key="player_1_selector",
                search_placeholder="Filter players",
            )

        with player_2_column:
            selected_player_2 = themed_selectbox(
                "Player 2",
                player_selector_options,
                format_func=format_player_option,
                key="player_2_selector",
                search_placeholder="Filter players",
            )

        player_3_column, player_4_column = st.columns(2)

        with player_3_column:
            selected_player_3 = themed_selectbox(
                "Player 3",
                player_selector_options,
                format_func=format_player_option,
                key="player_3_selector",
                search_placeholder="Filter players",
            )

        with player_4_column:
            selected_player_4 = themed_selectbox(
                "Player 4",
                player_selector_options,
                format_func=format_player_option,
                key="player_4_selector",
                search_placeholder="Filter players",
            )

        selected_player_ids = [
            player_id
            for player_id in [
                selected_player_1,
                selected_player_2,
                selected_player_3,
                selected_player_4,
            ]
            if player_id is not None
        ]

        # Keep dropdown order, but prevent the same player appearing twice.
        unique_player_ids = []
        duplicate_found = False

        for player_id in selected_player_ids:
            if player_id not in unique_player_ids:
                unique_player_ids.append(player_id)
            else:
                duplicate_found = True

        selected_player_ids = unique_player_ids

        if duplicate_found:
            st.warning(
                "Each player should only be selected once. "
                "Duplicate selections have been ignored."
            )

        if not selected_player_ids:
            st.info(
                "Choose one to four players to compare their profile and "
                "tournament event data."
            )

        else:
            # reindex keeps the players in Player 1 → Player 4 order.
            selected_players = (
                available_players.set_index("player_id")
                .reindex(selected_player_ids)
                .reset_index()
                .copy()
            )

            # Use concise two-line labels inside charts so four selected
            # players remain readable in a two-column dashboard layout.
            # Full names remain available in hover tooltips and the tables.
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

            player_colours = [
                theme["comparison_team_a"],
                theme["comparison_team_b"],
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

            # -----------------------------------------------------------------
            # Compact comparison table
            # -----------------------------------------------------------------
            st.markdown(
                '<div class="section-label">Profile and event comparison</div>',
                unsafe_allow_html=True,
            )

            comparison_table = selected_players[
                [
                    "player_name",
                    "team_name",
                    "position",
                    "club_team",
                    "caps",
                    "goals",
                    "goals_per_cap",
                    "tournament_goals",
                    "yellow_cards",
                    "red_cards",
                ]
            ].rename(
                columns={
                    "player_name": "Player",
                    "team_name": "Team",
                    "position": "Position",
                    "club_team": "Club",
                    "caps": "International caps",
                    "goals": "Career international goals",
                    "goals_per_cap": "Goals per cap",
                    "tournament_goals": "Tournament goals",
                    "yellow_cards": "YC",
                    "red_cards": "RC",
                }
            )

            themed_dataframe(
                comparison_table,
                width="stretch",
                hide_index=True,
                height=180,
                column_config={
                    "Player": st.column_config.TextColumn(
                        "Player",
                        width="medium",
                    ),
                    "Team": st.column_config.TextColumn(
                        "Team",
                        width="medium",
                    ),
                    "Position": st.column_config.TextColumn(
                        "Position",
                        width="small",
                    ),
                    "Club": st.column_config.TextColumn(
                        "Club",
                        width="medium",
                    ),
                    "International caps": st.column_config.NumberColumn(
                        "Caps",
                        format="%d",
                    ),
                    "Career international goals": st.column_config.NumberColumn(
                        "Career goals",
                        format="%d",
                    ),
                    "Goals per cap": st.column_config.NumberColumn(
                        "G/Cap",
                        format="%.2f",
                    ),
                    "Tournament goals": st.column_config.NumberColumn(
                        "Tournament goals",
                        format="%d",
                    ),
                    "YC": st.column_config.NumberColumn(
                        "YC",
                        format="%d",
                    ),
                    "RC": st.column_config.NumberColumn(
                        "RC",
                        format="%d",
                    ),
                },
            )

            # Secondary information is useful, but does not need to dominate
            # the main comparison view.
            with st.expander("View secondary player details"):
                secondary_details = selected_players[
                    [
                        "player_name",
                        "height_cm",
                        "market_value_millions",
                        "goal_minutes",
                    ]
                ].rename(
                    columns={
                        "player_name": "Player",
                        "height_cm": "Height (cm)",
                        "market_value_millions": "Market value (€m)",
                        "goal_minutes": "Tournament goal minutes",
                    }
                )

                themed_dataframe(
                    secondary_details,
                    width="stretch",
                    hide_index=True,
                    height=180,
                    column_config={
                        "Height (cm)": st.column_config.NumberColumn(
                            "Height (cm)",
                            format="%d",
                        ),
                        "Market value (€m)": st.column_config.NumberColumn(
                            "Market value (€m)",
                            format="€%.1f m",
                        ),
                    },
                )

            # -----------------------------------------------------------------
            # Player comparison charts
            #
            # Horizontal bars are intentional: player names and teams remain
            # legible at any dashboard width, rather than colliding on a
            # crowded x-axis. All four figures use the same height and axis
            # treatment so their chart cards align cleanly.
            # -----------------------------------------------------------------
            st.markdown(
                '<div class="section-label">Tournament event record</div>',
                unsafe_allow_html=True,
            )

            goals_chart_column, discipline_chart_column = st.columns(
                2,
                gap="large",
            )

            with goals_chart_column:
                st.subheader("Tournament goals")

                tournament_goals_figure = px.bar(
                    selected_players,
                    x="tournament_goals",
                    y="chart_label",
                    orientation="h",
                    color="chart_label",
                    color_discrete_map=colour_map,
                    custom_data=["player_name", "team_name"],
                    labels={
                        "chart_label": "Player",
                        "tournament_goals": "Goals",
                    },
                )

                tournament_goals_figure = style_chart(
                    tournament_goals_figure,
                    theme,
                )

                tournament_goals_figure.update_traces(
                    hovertemplate=(
                        "<b>%{customdata[0]}</b> — %{customdata[1]}<br>"
                        "Tournament goals: %{x}"
                        "<extra></extra>"
                    ),
                )

                tournament_goals_figure.update_layout(
                    height=420,
                    showlegend=False,
                    margin={"l": 18, "r": 46, "t": 24, "b": 24},
                )

                tournament_goals_figure.update_xaxes(
                    title="Goals",
                    rangemode="tozero",
                    dtick=1,
                    automargin=True,
                )

                tournament_goals_figure.update_yaxes(
                    title=None,
                    autorange="reversed",
                    tickfont={"size": 12, "color": theme["text"]},
                    automargin=True,
                )

                st.plotly_chart(
                    tournament_goals_figure,
                    width="stretch",
                    config={"displayModeBar": False},
                )

            with discipline_chart_column:
                st.subheader("Tournament discipline")

                discipline_data = selected_players.melt(
                    id_vars=["chart_label", "player_name", "team_name"],
                    value_vars=[
                        "yellow_cards",
                        "red_cards",
                    ],
                    var_name="Card type",
                    value_name="Cards",
                )

                discipline_data["Card type"] = discipline_data[
                    "Card type"
                ].replace(
                    {
                        "yellow_cards": "Yellow cards",
                        "red_cards": "Red cards",
                    }
                )

                discipline_figure = px.bar(
                    discipline_data,
                    x="Cards",
                    y="chart_label",
                    orientation="h",
                    color="Card type",
                    barmode="group",
                    custom_data=["player_name", "team_name"],
                    color_discrete_map={
                        "Yellow cards": "#d7a600",
                        "Red cards": "#c93c3c",
                    },
                    labels={
                        "chart_label": "Player",
                    },
                )

                discipline_figure = style_chart(
                    discipline_figure,
                    theme,
                )

                discipline_figure.update_traces(
                    hovertemplate=(
                        "<b>%{customdata[0]}</b> — %{customdata[1]}<br>"
                        "%{fullData.name}: %{x}"
                        "<extra></extra>"
                    ),
                )

                discipline_figure.update_layout(
                    height=420,
                    showlegend=True,
                    legend={
                        "orientation": "h",
                        "yanchor": "bottom",
                        "y": 1.02,
                        "xanchor": "right",
                        "x": 1,
                    },
                    margin={"l": 18, "r": 46, "t": 48, "b": 24},
                )

                discipline_figure.update_xaxes(
                    title="Cards",
                    rangemode="tozero",
                    dtick=1,
                    automargin=True,
                )

                discipline_figure.update_yaxes(
                    title=None,
                    autorange="reversed",
                    tickfont={"size": 12, "color": theme["text"]},
                    automargin=True,
                )

                st.plotly_chart(
                    discipline_figure,
                    width="stretch",
                    config={"displayModeBar": False},
                )

            # -----------------------------------------------------------------
            # International record charts
            # -----------------------------------------------------------------
            st.markdown(
                '<div class="section-label">International record</div>',
                unsafe_allow_html=True,
            )

            caps_chart_column, career_goals_chart_column = st.columns(
                2,
                gap="large",
            )

            with caps_chart_column:
                # Kept compact so this heading remains a single line and the
                # chart starts level with the chart beside it.
                st.subheader("Caps & goals/cap")

                caps_figure = go.Figure()

                caps_figure.add_trace(
                    go.Bar(
                        x=selected_players["caps"],
                        y=selected_players["chart_label"],
                        orientation="h",
                        name="International caps",
                        marker_color=selected_player_colours,
                        customdata=selected_players[
                            [
                                "player_name",
                                "team_name",
                                "goals_per_cap",
                            ]
                        ].to_numpy(),
                        hovertemplate=(
                            "<b>%{customdata[0]}</b> — %{customdata[1]}<br>"
                            "International caps: %{x}<br>"
                            "Goals per cap: %{customdata[2]:.2f}"
                            "<extra></extra>"
                        ),
                    )
                )

                caps_figure.add_trace(
                    go.Scatter(
                        x=selected_players["goals_per_cap"],
                        y=selected_players["chart_label"],
                        name="Goals per cap",
                        xaxis="x2",
                        mode="markers+text",
                        text=[
                            f"{value:.2f}"
                            for value in selected_players["goals_per_cap"]
                        ],
                        textposition="middle right",
                        marker={
                            "size": 11,
                            "color": selected_player_colours,
                            "line": {
                                "color": theme["text"],
                                "width": 1,
                            },
                        },
                        hovertemplate=(
                            "<b>%{y}</b><br>"
                            "Goals per cap: %{x:.2f}"
                            "<extra></extra>"
                        ),
                    )
                )

                caps_figure = style_chart(
                    caps_figure,
                    theme,
                )

                max_goals_per_cap = max(
                    float(selected_players["goals_per_cap"].max()),
                    0.1,
                )

                caps_figure.update_layout(
                    height=420,
                    showlegend=True,
                    legend={
                        "orientation": "h",
                        "yanchor": "bottom",
                        "y": 1.02,
                        "xanchor": "right",
                        "x": 1,
                    },
                    margin={"l": 18, "r": 52, "t": 48, "b": 24},
                    xaxis={
                        "title": "International caps",
                        "rangemode": "tozero",
                        "automargin": True,
                    },
                    xaxis2={
                        "title": "Goals per cap",
                        "overlaying": "x",
                        "side": "top",
                        "range": [0, max_goals_per_cap * 1.22],
                        "showgrid": False,
                        "tickformat": ".1f",
                        "tickfont": {"color": theme["muted"]},
                        "title_font": {"color": theme["muted"]},
                    },
                    yaxis={
                        "title": None,
                        "autorange": "reversed",
                        "tickfont": {
                            "size": 12,
                            "color": theme["text"],
                        },
                        "automargin": True,
                    },
                )

                st.plotly_chart(
                    caps_figure,
                    width="stretch",
                    config={"displayModeBar": False},
                )

            with career_goals_chart_column:
                st.subheader("Career international goals")

                career_goals_figure = px.bar(
                    selected_players,
                    x="goals",
                    y="chart_label",
                    orientation="h",
                    color="chart_label",
                    color_discrete_map=colour_map,
                    custom_data=["player_name", "team_name"],
                    labels={
                        "chart_label": "Player",
                        "goals": "Career international goals",
                    },
                )

                career_goals_figure = style_chart(
                    career_goals_figure,
                    theme,
                )

                career_goals_figure.update_traces(
                    hovertemplate=(
                        "<b>%{customdata[0]}</b> — %{customdata[1]}<br>"
                        "Career international goals: %{x}"
                        "<extra></extra>"
                    ),
                )

                career_goals_figure.update_layout(
                    height=420,
                    showlegend=False,
                    margin={"l": 18, "r": 46, "t": 24, "b": 24},
                )

                career_goals_figure.update_xaxes(
                    title="Goals",
                    rangemode="tozero",
                    nticks=8,
                    automargin=True,
                )

                career_goals_figure.update_yaxes(
                    title=None,
                    autorange="reversed",
                    tickfont={"size": 12, "color": theme["text"]},
                    automargin=True,
                )

                st.plotly_chart(
                    career_goals_figure,
                    width="stretch",
                    config={"displayModeBar": False},
                )

            # -----------------------------------------------------------------
            # Expandable event log
            # -----------------------------------------------------------------
            with st.expander("View recorded tournament events"):
                selected_event_log = match_events.loc[
                    match_events["match_id"].isin(active_match_ids)
                    & match_events["player_id"].isin(selected_player_ids)
                    & match_events["event_type"].isin(
                        [
                            "Goal",
                            "Yellow Card",
                            "Red Card",
                        ]
                    )
                ].copy()

                selected_event_log = selected_event_log.merge(
                    selected_players[
                        [
                            "player_id",
                            "player_name",
                        ]
                    ],
                    on="player_id",
                    how="left",
                )

                selected_event_log = selected_event_log.merge(
                    filtered_matches[
                        [
                            "match_id",
                            "kickoff_uk",
                            "home_team_name",
                            "away_team_name",
                        ]
                    ],
                    on="match_id",
                    how="left",
                )

                if selected_event_log.empty:
                    st.info(
                        "No goal or card events were recorded for the selected "
                        "players within the current fixture filters. This does "
                        "not mean that they did not play."
                    )

                else:
                    selected_event_log["fixture"] = (
                        selected_event_log["home_team_name"]
                        + " v "
                        + selected_event_log["away_team_name"]
                    )

                    selected_event_log = selected_event_log.sort_values(
                        [
                            "kickoff_uk",
                            "minute",
                        ]
                    )

                    selected_event_log["date"] = (
                        selected_event_log["kickoff_uk"].dt.strftime(
                            "%a %d %b"
                        )
                    )

                    selected_event_log["minute"] = (
                        selected_event_log["minute"]
                        .astype(int)
                        .astype(str)
                        + "'"
                    )

                    themed_dataframe(
                        selected_event_log[
                            [
                                "player_name",
                                "event_type",
                                "minute",
                                "date",
                                "fixture",
                            ]
                        ].rename(
                            columns={
                                "player_name": "Player",
                                "event_type": "Event",
                                "minute": "Minute",
                                "date": "Date",
                                "fixture": "Fixture",
                            }
                        ),
                        width="stretch",
                        hide_index=True,
                        height=280,
                    )

# -----------------------------------------------------------------------------
# Venues tab
# -----------------------------------------------------------------------------
with venues_tab:
    st.markdown(
        '<div class="section-label">Host cities</div>',
        unsafe_allow_html=True,
    )

    st.subheader("Venues used by the selected fixtures")

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