import streamlit as st

from app.config import DEFAULT_PERIOD, DEFAULT_SETTINGS, PERIOD_OPTIONS
from app.services.export import dataframe_to_csv_bytes


def initialize_session_state() -> None:
    if "periode" not in st.session_state:
        st.session_state["periode"] = DEFAULT_PERIOD

    # Theme global: light/dark only (default light for readability safety)
    current_theme = st.session_state.get("theme")
    if current_theme in {"light", "dark"}:
        pass
    elif isinstance(current_theme, str) and "sombre" in current_theme.lower():
        st.session_state["theme"] = "dark"
    else:
        st.session_state["theme"] = "light"

    if "min_opportunity_score" not in st.session_state:
        st.session_state["min_opportunity_score"] = DEFAULT_SETTINGS["min_opportunity_score"]
    if "rows_per_page" not in st.session_state:
        st.session_state["rows_per_page"] = DEFAULT_SETTINGS["rows_per_page"]


def get_plotly_template() -> str:
    return "plotly_dark" if st.session_state.get("theme", "light") == "dark" else "plotly_white"


def apply_theme_css(theme: str) -> None:
    if theme == "dark":
        css = """
        <style>
        :root {
            --bg: #0b1220;
            --card-bg: #111827;
            --text-color: #e5e7eb;
            --muted: #94a3b8;
            --border-color: #1f2937;
            --accent: #38bdf8;
        }
        .stApp { background: radial-gradient(circle at top left, #111827 0%, #0b1220 45%, #0b1220 100%); color: var(--text-color); }
        [data-testid="stSidebar"] { background-color: #0f172a; border-right: 1px solid var(--border-color); }
        [data-testid="stSidebar"] * { color: var(--text-color) !important; }
        .sidebar-logo { color: var(--text-color); border-bottom: 1px solid var(--border-color); }
        .sidebar-logo span { color: var(--accent); }

        .kpi-card { background-color: var(--card-bg); border: 1px solid var(--border-color); box-shadow: 0 8px 20px -14px rgba(0, 0, 0, 0.8); }
        .kpi-title { color: var(--muted); }
        .kpi-value, .section-title, .header-title { color: var(--text-color); }
        .trend-up { color: #22c55e; }
        .trend-down { color: #f87171; }
        .trend-neutral { color: var(--muted); }

        [data-testid="stMarkdownContainer"], [data-testid="stText"], .stCaption, .stMarkdown, .st-emotion-cache-10trblm { color: var(--text-color); }
        [data-testid="stDataFrame"], [data-testid="stTable"] { background-color: var(--card-bg); border: 1px solid var(--border-color); border-radius: 12px; }
        [data-testid="stDataFrame"] * { color: var(--text-color) !important; }

        .stButton button, .stDownloadButton button {
            background-color: #1e293b;
            color: var(--text-color);
            border: 1px solid #334155;
        }
        .stButton button:hover, .stDownloadButton button:hover { border-color: var(--accent); color: #ffffff; }

        .badge-excellent { background-color: #14532d; color: #dcfce7; }
        .badge-good { background-color: #78350f; color: #fef3c7; }
        .badge-neutral { background-color: #334155; color: #cbd5e1; }

        #MainMenu { visibility: hidden; }
        footer { visibility: hidden; }
        </style>
        """
    else:
        css = """
        <style>
        :root {
            --bg: #f8fafc;
            --card-bg: #ffffff;
            --text-color: #0f172a;
            --muted: #64748b;
            --border-color: #e2e8f0;
            --accent: #0ea5e9;
        }
        .stApp { background: radial-gradient(circle at top left, #eef2ff 0%, #f8fafc 35%, #f8fafc 100%); color: var(--text-color); }
        [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid var(--border-color); }
        .sidebar-logo { color: var(--text-color); border-bottom: 1px solid var(--border-color); }
        .sidebar-logo span { color: var(--accent); }

        .kpi-card { background-color: var(--card-bg); border: 1px solid var(--border-color); box-shadow: 0 6px 16px -10px rgba(15, 23, 42, 0.35); }
        .kpi-title { color: var(--muted); }
        .kpi-value, .section-title, .header-title { color: var(--text-color); }
        .trend-up { color: #16a34a; }
        .trend-down { color: #dc2626; }
        .trend-neutral { color: var(--muted); }

        [data-testid="stDataFrame"], [data-testid="stTable"] { background-color: var(--card-bg); border: 1px solid var(--border-color); border-radius: 12px; }
        .stButton button, .stDownloadButton button { border: 1px solid #cbd5e1; }

        .badge-excellent { background-color: #dcfce7; color: #166534; }
        .badge-good { background-color: #fef9c3; color: #854d0e; }
        .badge-neutral { background-color: #f1f5f9; color: #64748b; }

        #MainMenu { visibility: hidden; }
        footer { visibility: hidden; }
        </style>
        """

    st.markdown(css, unsafe_allow_html=True)


def apply_custom_css() -> None:
    apply_theme_css(st.session_state.get("theme", "light"))


def sidebar_logo() -> None:
    st.sidebar.markdown(
        """
        <div class="sidebar-logo">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#0ea5e9" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
                <polyline points="9 22 9 12 15 12 15 22"></polyline>
            </svg>
            Nid<span>Douillet</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.sidebar.caption("Observatoire Immobilier - Toulon")


def topbar(title: str) -> None:
    col_left, col_right = st.columns([6, 1])
    with col_left:
        st.markdown(f'<h1 class="header-title">{title}</h1>', unsafe_allow_html=True)

    with col_right:
        theme = st.session_state.get("theme", "light")
        label = "🌙" if theme == "light" else "☀️"
        help_text = "Basculer en mode sombre" if theme == "light" else "Basculer en mode clair"
        if st.button(label, key="theme_toggle_btn", help=help_text, use_container_width=True):
            st.session_state["theme"] = "dark" if theme == "light" else "light"
            st.rerun()


def page_header(export_df=None, export_filename: str = "export.csv", show_period: bool = True) -> None:
    col_period, col_export = st.columns([1.2, 1.1])

    with col_period:
        if show_period:
            current_period = st.session_state.get("periode", DEFAULT_PERIOD)
            index = PERIOD_OPTIONS.index(current_period) if current_period in PERIOD_OPTIONS else PERIOD_OPTIONS.index(DEFAULT_PERIOD)
            period = st.selectbox(
                "Période",
                PERIOD_OPTIONS,
                index=index,
                key="global_period_selector",
                label_visibility="collapsed",
            )
            st.session_state["periode"] = period

    with col_export:
        if export_df is None:
            st.button("Export CSV", use_container_width=True, disabled=True)
        else:
            st.download_button(
                label="Export CSV",
                data=dataframe_to_csv_bytes(export_df),
                file_name=export_filename,
                mime="text/csv",
                use_container_width=True,
                type="primary",
            )

    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)


def section_title(text: str) -> None:
    st.markdown(f"<div class='section-title'>{text}</div>", unsafe_allow_html=True)


def kpi_card(title: str, value, trend=None, trend_text: str = "vs période précédente") -> None:
    trend_html = ""
    if trend is not None:
        if trend > 0:
            trend_class, icon, trend_str = "trend-up", "↑", f"+{trend}%"
        elif trend < 0:
            trend_class, icon, trend_str = "trend-down", "↓", f"{trend}%"
        else:
            trend_class, icon, trend_str = "trend-neutral", "→", "0%"

        trend_html = (
            f"<div class='kpi-trend {trend_class}'><span>{icon} {trend_str}</span>"
            f"<span style='color: var(--muted); font-weight: 500;'>{trend_text}</span></div>"
        )

    st.markdown(
        f"""
    <div class="kpi-card">
        <div class="kpi-title">{title}</div>
        <div class="kpi-value">{value}</div>
        {trend_html}
    </div>
    """,
        unsafe_allow_html=True,
    )
