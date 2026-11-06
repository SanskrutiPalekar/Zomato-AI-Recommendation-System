"""
Streamlit Deployment Entrypoint (streamlit_app.py)
Integrates Phases 1-6 of the Zomato AI Restaurant Recommendation Service
for one-click deployment on Streamlit Community Cloud.
"""

import importlib
import inspect
import os
import socket
import sys
import threading
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

load_dotenv()

# Sync Streamlit Cloud secrets into environment variables if present
try:
    if "GROQ_API_KEY" in st.secrets and not os.getenv("GROQ_API_KEY"):
        os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
    if "DATASET_FILE" in st.secrets and not os.getenv("DATASET_FILE"):
        os.environ["DATASET_FILE"] = st.secrets["DATASET_FILE"]
except Exception:
    pass

import phase4.config
import phase4.reranker
import phase5.service
import phase6.dependencies

importlib.reload(phase4.config)
importlib.reload(phase4.reranker)
importlib.reload(phase5.service)
importlib.reload(phase6.dependencies)

from phase6.dependencies import get_service, get_store, initialize_store, reset_singletons


def _is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.3)
        return s.connect_ex((host, port)) == 0


@st.cache_resource(show_spinner="Initializing Zomato AI Knowledge Base & FastAPI Backend...")
def init_backend(_version: int = 2):
    """
    Initializes the singleton MetadataStore & ZomatoAIService once per container,
    and starts the FastAPI backend on port 8000 in a background daemon thread
    if not already running.
    """
    reset_singletons()
    store = initialize_store(force_reinit=True)
    service = get_service()

    # Start FastAPI server in background thread so /api/recommend, /api/cities, /health
    # are also live inside the deployment environment
    if not _is_port_in_use(8000):
        def _run_api():
            import uvicorn
            from phase6.api import app
            uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")

        api_thread = threading.Thread(target=_run_api, daemon=True)
        api_thread.start()

    cities = store.get_distinct_cities()
    locations = store.get_distinct_locations()
    all_localities = list(dict.fromkeys(cities + locations))
    return store, service, all_localities


def render_restaurant_card(rank: int, rec, max_budget: float):
    """Renders a styled HTML card for a recommended restaurant."""
    rating_bg = "#16a34a" if rec.rating >= 4.0 else ("#eab308" if rec.rating >= 3.5 else "#dc2626")
    saving = int(max_budget - rec.cost_for_two) if max_budget > 0 else 0
    saving_badge = (
        f'<span style="background:#ecfdf5;color:#047857;border:1px solid #a7f3d0;'
        f'padding:3px 10px;border-radius:999px;font-size:12px;font-weight:600;">'
        f'₹{saving} below budget</span>'
        if saving > 0
        else f'<span style="background:#f3f4f6;color:#374151;padding:3px 10px;'
             f'border-radius:999px;font-size:12px;">{rec.budget_verdict or "Within budget"}</span>'
    )

    dishes_html = ""
    if rec.must_try_dishes:
        chips = "".join(
            f'<span style="background:#fef2f2;color:#b91c1c;border:1px solid #fecaca;'
            f'padding:3px 8px;border-radius:6px;font-size:12px;margin-right:6px;display:inline-block;margin-bottom:4px;">'
            f'🍽 {d}</span>'
            for d in rec.must_try_dishes
        )
        dishes_html = f'<div style="margin-top:10px;"><div style="font-size:11px;font-weight:700;color:#6b7280;text-transform:uppercase;margin-bottom:4px;">Must-Try Dishes</div>{chips}</div>'

    delivery_badge = (
        '<span style="background:#ecfdf5;color:#047857;padding:2px 8px;border-radius:4px;font-size:12px;margin-right:8px;">✓ Online Delivery</span>'
        if rec.online_order == "Yes"
        else '<span style="background:#f3f4f6;color:#6b7280;padding:2px 8px;border-radius:4px;font-size:12px;margin-right:8px;">✗ No Delivery</span>'
    )
    booking_badge = (
        '<span style="background:#eff6ff;color:#1d4ed8;padding:2px 8px;border-radius:4px;font-size:12px;">✓ Table Booking</span>'
        if rec.book_table == "Yes"
        else '<span style="background:#f3f4f6;color:#6b7280;padding:2px 8px;border-radius:4px;font-size:12px;">✗ No Table Booking</span>'
    )

    st.markdown(
        f"""
        <div style="background:white;border:1px solid #e5e7eb;border-radius:16px;padding:20px;margin-bottom:16px;box-shadow:0 1px 3px rgba(0,0,0,0.05);">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:6px;">
                <div style="display:flex;align-items:center;gap:8px;">
                    <span style="background:#E23744;color:white;border-radius:50%;width:26px;height:26px;display:inline-flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;">#{rank}</span>
                    <span style="font-size:18px;font-weight:700;color:#111827;">{rec.restaurant_name}</span>
                </div>
                <span style="background:{rating_bg};color:white;padding:4px 10px;border-radius:8px;font-size:12px;font-weight:700;">
                    ★ {rec.rating:.1f} / 5.0
                </span>
            </div>
            <div style="font-size:13px;color:#6b7280;margin-bottom:10px;">
                📍 <strong style="color:#374151;">{rec.location}</strong>
                {f" • {rec.cuisines}" if rec.cuisines else ""}
            </div>
            <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:12px;">
                <span style="background:#f3f4f6;color:#1f2937;padding:3px 10px;border-radius:999px;font-size:12px;font-weight:600;">
                    ₹{rec.cost_for_two} for two
                </span>
                {saving_badge}
            </div>
            <div style="background:#fffbeb;border:1px solid #fde68a;border-radius:10px;padding:12px;margin-bottom:8px;">
                <div style="font-size:11px;font-weight:700;color:#92400e;text-transform:uppercase;margin-bottom:4px;">
                    AI Concierge Rationale
                </div>
                <div style="font-size:13.5px;color:#374151;line-height:1.5;">
                    {rec.ai_rationale}
                </div>
            </div>
            {dishes_html}
            <div style="border-top:1px solid #f3f4f6;margin-top:12px;padding-top:10px;">
                {delivery_badge} {booking_badge}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main():
    st.set_page_config(
        page_title="Zomato AI Restaurant Concierge",
        page_icon="🍽️",
        layout="wide",
    )

    # Header Banner
    st.markdown(
        """
        <div style="background:#E23744;color:white;padding:22px 28px;border-radius:16px;margin-bottom:24px;">
            <h1 style="margin:0;font-size:28px;font-weight:800;color:white;">🍽️ Zomato AI Restaurant Concierge</h1>
            <p style="margin:4px 0 0 0;font-size:14px;color:#ffe4e6;">
                Personalized dining recommendations powered by RAG & Groq LLM
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    store, service, localities = init_backend()

    # Search Form
    with st.form("recommendation_search_form"):
        col1, col2, col3, col4 = st.columns([3, 3, 3, 2])

        with col1:
            city_choice = st.selectbox(
                "City / Locality *",
                options=localities if localities else ["Koramangala", "Indiranagar", "BTM"],
                index=0,
                help="Select or type a city/locality from the dataset",
            )

        with col2:
            price_input = st.text_input(
                "Budget for Two (INR) *",
                value="under 800",
                placeholder="e.g. under 800, 600, 500 to 1000, budget",
            )

        with col3:
            preferences_input = st.text_input(
                "Food / Vibe Preferences (Optional)",
                value="",
                placeholder="e.g. Pizza, Biryani, Cafe, Romantic",
            )

        with col4:
            top_k = st.slider(
                "AI Picks to Show",
                min_value=3,
                max_value=15,
                value=6,
                step=1,
                help="Number of AI-curated restaurant cards to generate",
            )

        submitted = st.form_submit_button("🔍 Find Restaurants", use_container_width=True)

    # Sidebar status info
    with st.sidebar:
        st.subheader("📊 Knowledge Base Status")
        st.write(f"**Indexed Restaurants:** {store.count()}")
        st.write(f"**Available Localities:** {len(localities)}")
        st.caption("FastAPI Backend (`/api/recommend`, `/api/cities`, `/health`) is integrated.")

    if submitted:
        if not city_choice.strip() or not price_input.strip():
            st.error("Please provide both a City/Locality and a Budget.")
            return

        with st.spinner("Consulting Zomato AI Concierge (Groq LLM)..."):
            try:
                sig = inspect.signature(service.search)
                search_kwargs = {
                    "city": city_choice.strip(),
                    "price": price_input.strip(),
                    "preferences": preferences_input.strip() or None,
                    "force_mock": False,
                    "render_output": False,
                }
                if "top_k" in sig.parameters:
                    search_kwargs["top_k"] = top_k
                response = service.search(**search_kwargs)
            except ValueError as err:
                st.error(f"Input Validation Error: {err}")
                return
            except Exception as err:
                st.error(f"Service Error: {err}")
                return

        if not response.recommendations:
            st.warning(f"No restaurants found in '{city_choice}' within budget '{price_input}'.")
            return

        max_budget = (
            response.query_summary.get("max_budget", 0)
            or response.query_summary.get("budget_for_two", 0)
            or response.query_summary.get("budget", 0)
        )
        engine_label = "Offline Mock Engine" if response.is_mock else f"Groq ({response.model_name})"
        latency_ms = int(response.latency_seconds * 1000)

        # AI Concierge Overview Box
        st.markdown(
            f"""
            <div style="background:white;border:1px solid #fecaca;border-radius:14px;padding:18px;margin:16px 0;">
                <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;margin-bottom:6px;">
                    <strong style="font-size:16px;color:#111827;">
                        🤖 AI Concierge Overview — <span style="color:#E23744;">{response.query_summary.get("city", city_choice)}</span> (Up to ₹{int(max_budget)})
                    </strong>
                    <span style="font-size:12px;color:#6b7280;background:#f3f4f6;padding:3px 10px;border-radius:6px;">
                        {engine_label} • ⚡ {latency_ms} ms
                    </span>
                </div>
                <div style="font-size:14px;color:#374151;line-height:1.5;">
                    {response.overall_ai_summary}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Render Recommendation Cards in Columns
        cols = st.columns(min(3, len(response.recommendations)))
        for idx, rec in enumerate(response.recommendations):
            with cols[idx % len(cols)]:
                render_restaurant_card(idx + 1, rec, max_budget)

        # Also show all matching restaurants from the database in an expandable table
        all_db_matches = store.query_by_city_and_price(
            city=city_choice.strip(),
            max_price=max_budget,
            limit=200,
        )
        if all_db_matches:
            with st.expander(f"📋 View All {len(all_db_matches)} Matching Restaurants in '{city_choice}' (Up to ₹{int(max_budget)})"):
                import pandas as pd
                df_matches = pd.DataFrame(all_db_matches)[
                    ["restaurant_name", "location", "rating", "votes", "cost_for_two", "cuisines", "rest_type"]
                ]
                df_matches.columns = ["Restaurant", "Locality", "Rating", "Votes", "Cost for Two (₹)", "Cuisines", "Dining Type"]
                st.dataframe(df_matches, use_container_width=True, hide_index=True)
    else:
        st.info("👆 Select a locality, enter your budget for two, and click **Find Restaurants** to get started!")


if __name__ == "__main__":
    main()

