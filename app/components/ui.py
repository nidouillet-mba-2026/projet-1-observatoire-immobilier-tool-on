import streamlit as st

from app.config import DEFAULT_PERIOD, DEFAULT_SETTINGS, PERIOD_OPTIONS
from app.services.export import dataframe_to_csv_bytes


def initialize_session_state() -> None:
    if "periode" not in st.session_state:
        st.session_state["periode"] = DEFAULT_PERIOD
    if "theme" not in st.session_state:
        st.session_state["theme"] = DEFAULT_SETTINGS["theme"]
    if "min_opportunity_score" not in st.session_state:
        st.session_state["min_opportunity_score"] = DEFAULT_SETTINGS["min_opportunity_score"]
    if "rows_per_page" not in st.session_state:
        st.session_state["rows_per_page"] = DEFAULT_SETTINGS["rows_per_page"]


def apply_custom_css() -> None:
    st.markdown(
        """
    <style>
    .stApp {
        background: radial-gradient(circle at top left, #eef2ff 0%, #f8fafc 35%, #f8fafc 100%);
    }

    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }

    .sidebar-logo {
        font-size: 1.5rem;
        font-weight: 700;
        color: #0f172a;
        padding: 1rem 0;
        margin-bottom: 1.5rem;
        border-bottom: 1px solid #e2e8f0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .sidebar-logo span {
        color: #0ea5e9;
    }

    .kpi-card {
        background-color: #ffffff;
        border-radius: 14px;
        padding: 1.2rem;
        box-shadow: 0 6px 16px -10px rgba(15, 23, 42, 0.35);
        border: 1px solid #e2e8f0;
        display: flex;
        flex-direction: column;
        gap: 0.35rem;
    }

    .kpi-title {
        font-size: 0.74rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-weight: 700;
    }

    .kpi-value {
        font-size: 1.7rem;
        color: #0f172a;
        font-weight: 700;
        line-height: 1.2;
    }

    .kpi-trend {
        font-size: 0.88rem;
        display: flex;
        align-items: center;
        gap: 0.35rem;
        margin-top: 0.1rem;
    }

    .trend-up { color: #16a34a; font-weight: 600; }
    .trend-down { color: #dc2626; font-weight: 600; }
    .trend-neutral { color: #64748b; font-weight: 600; }

    .header-title {
        font-size: 1.9rem;
        color: #0f172a;
        font-weight: 700;
        margin: 0;
    }

    .section-title {
        font-size: 1.05rem;
        color: #0f172a;
        font-weight: 600;
        margin: 0.25rem 0 0.75rem 0;
    }

    .badge {
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
    }

    .badge-excellent { background-color: #dcfce7; color: #166534; }
    .badge-good { background-color: #fef9c3; color: #854d0e; }
    .badge-neutral { background-color: #f1f5f9; color: #64748b; }

    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    </style>
    """,
        unsafe_allow_html=True,
    )


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


def page_header(title: str, export_df=None, export_filename: str = "export.csv", show_period: bool = True) -> None:
    col_title, col_period, col_export = st.columns([2.2, 1.2, 1.1])

    with col_title:
        st.markdown(f'<h1 class="header-title">{title}</h1>', unsafe_allow_html=True)

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
            f"<span style='color: #94a3b8; font-weight: 500;'>{trend_text}</span></div>"
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
