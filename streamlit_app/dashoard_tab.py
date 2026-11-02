"""
batches_tab.py
Streamlit UI for the "Batches" tab (user dashboard / batches-group).
Expecting BACKEND_API_BASE_URL like "http://localhost:8003" and
st.session_state.token available after login.
"""

import math
from datetime import datetime

import streamlit as st
import requests


st.markdown("""
<style>

.batch-card {
    border-radius: 1.1rem;
    padding: 1rem 1.3rem;
    margin-bottom: 1rem;
    border: 1px solid rgba(255,255,255,0.08);
    background: rgba(255,255,255,0.025);
    transition: 0.25s ease;
}
.batch-card:hover {
    background: rgba(255,255,255,0.05);
    transform: translateY(-3px);
    box-shadow: 0 8px 20px rgba(0,0,0,0.25);
}

.batch-title {
    font-size: 1.25rem;
    font-weight: 700;
    margin-bottom: 0.3rem;
}

.batch-meta {
    font-size: 0.85rem;
    opacity: 0.8;
    margin-bottom: 0.4rem;
}

.status-pill {
    display: inline-block;
    padding: 0.22rem 0.65rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-right: 0.3rem;
}

.status-active {
    background: rgba(40,167,69,0.2);
    color: #c8f7d4;
}

.status-pending {
    background: rgba(255,193,7,0.2);
    color: #ffe9a3;
}

.status-locked {
    background: rgba(220,53,69,0.25);
    color: #ffb8c5;
}

.plan-item {
    font-size: 0.85rem;
    margin-bottom: 0.2rem;
}

</style>
""", unsafe_allow_html=True)


# ------------ Helpers ------------

def _auth_headers():
    token = st.session_state.get("token")
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}


def fetch_dashboard(base_url: str):
    """
    Calls the AnnotatorDashboardAPIView:
        GET {base_url}/dashboard/batches-group/

    Expected payload:
    {
      "xp_points": int,
      "datcoins": int,
      "level": int,
      "accuracy": float,
      "level_progress": float|int,  # progress to next level
      "active_batches": [...],
      "recent_plans": [...]
    }
    """
    try:
        url = f"{base_url}/dashboard/batches-group/"
        headers = _auth_headers()
        resp = requests.get(url, headers=headers, timeout=10)

        if resp.status_code == 401:
            return {"error": "unauthorized", "status_code": 401}
        if resp.status_code != 200:
            return {
                "error": "failed",
                "status_code": resp.status_code,
                "body": resp.text,
            }

        return {"data": resp.json()}
    except requests.exceptions.RequestException as e:
        return {"error": "network", "message": str(e)}
    except Exception as e:
        return {"error": "exception", "message": str(e)}


def request_batch_access(base_url: str, batch_id: int):
    """
    POST to request batch access.

    NOTE: this uses your dashboard URLs:
      path("batches-group/<int:batch_id>/request-access/", ...)
    """
    try:
        url = f"{base_url}/dashboard/batches-group/{batch_id}/request-access/"
        headers = _auth_headers()
        return requests.post(url, headers=headers, timeout=8)
    except requests.exceptions.RequestException:
        return None


# ------------ UI Components ------------

def _render_top_navigation(orgs, projects):
    st.markdown(
        """
        <style>
        .top-nav {
            padding: 0.8rem 1rem;
            background: rgba(255,255,255,0.04);
            border-radius: 0.9rem;
            margin-bottom: 1.2rem;
            border: 1px solid rgba(255,255,255,0.08);
        }
        .nav-title {
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 0.6rem;
        }
        .filter-pill {
            padding: 0.35rem 0.9rem;
            border-radius: 999px;
            border: 1px solid rgba(255,255,255,0.18);
            background: rgba(255,255,255,0.05);
            cursor: pointer;
            font-size: 0.85rem;
            margin-right: 0.4rem;
        }
        .filter-pill-active {
            background: linear-gradient(135deg, #4c6fff, #7b5cff);
            border-color: transparent;
            color: white;
            box-shadow: 0 0.3rem 1rem rgba(124,92,255,0.4);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.container():
        st.markdown('<div class="top-nav">', unsafe_allow_html=True)

        # --- First Row: Org + Project ---
        c1, c2 = st.columns([1, 1])
        with c1:
            st.selectbox(
                "🏢 Organization",
                orgs,
                key="selected_org",
            )
        with c2:
            st.selectbox(
                "📁 Project",
                projects,
                key="selected_project",
            )

        # --- Second Row: Search ---
        st.text_input(
            "🔍 Search (Batch or Plan name)",
            placeholder="Search...",
            key="dashboard_search",
        )

        # --- Third Row: Filters ---
        st.markdown("#### Filters")

        filter_options = ["All", "Joined", "Available", "Completed"]
        active_filter = st.session_state.get("dashboard_filter", "All")

        fcols = st.columns(len(filter_options))
        for idx, f in enumerate(filter_options):
            style_class = "filter-pill-active" if f == active_filter else "filter-pill"
            with fcols[idx]:
                if st.button(f"{f}", key=f"filter_{f}"):
                    st.session_state.dashboard_filter = f
                    st.experimental_rerun()

            st.markdown(
                f"""
                <style>
                div.stButton > button#{f.replace(" ", "_")} {{
                    display:none;
                }}
                </style>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)



def _render_gamification_header(stats: dict):
    """
    Top hero section: level badge, XP, coins, accuracy, and progress bar.
    """
    xp = stats.get("xp_points", 0)
    coins = stats.get("datcoins", 0)
    level = stats.get("level", 1)
    accuracy = stats.get("accuracy", 0)
    level_progress = stats.get("level_progress", 0)  # backend metric

    # normalize progress to [0, 1] safely
    try:
        if level_progress > 1:
            progress_ratio = min(level_progress / 100.0, 1.0)
        else:
            progress_ratio = max(min(float(level_progress), 1.0), 0.0)
    except Exception:
        progress_ratio = 0.0

    with st.container():
        st.markdown(
            """
            <style>
            .level-badge {
                display:inline-block;
                padding: 0.4rem 0.9rem;
                border-radius: 999px;
                background: linear-gradient(135deg, #4c6fff, #7b5cff);
                color: white;
                font-weight: 700;
                letter-spacing: 0.03em;
                font-size: 0.9rem;
                box-shadow: 0 0.5rem 1.5rem rgba(124, 92, 255, 0.4);
            }
            .stat-card {
                border-radius: 0.9rem;
                padding: 0.9rem 1rem;
                background: rgba(255,255,255,0.03);
                border: 1px solid rgba(255,255,255,0.08);
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("### 🎮 Your Progress")

        top_cols = st.columns([1, 2])
        with top_cols[0]:
            st.markdown(f'<span class="level-badge">LEVEL {level}</span>', unsafe_allow_html=True)
            st.write("")
            st.markdown(f"**⭐ XP:** `{xp}`")
            st.markdown(f"**🪙 DatCoins:** `{coins}`")

        with top_cols[1]:
            st.markdown("**🚀 Progress to Next Level**")
            st.progress(progress_ratio)
            st.markdown(f"**🎯 Accuracy:** `{accuracy:.1f}%`")


def _compute_batch_completion(batch: dict):
    """
    Compute completion ratio for a batch based on its plans.
    Uses my_completed_count / tasks_count summed across plans.
    """
    plans = batch.get("plans") or []
    total_tasks = sum(p.get("tasks_count", 0) or 0 for p in plans)
    my_completed = sum(p.get("my_completed_count", 0) or 0 for p in plans)

    if total_tasks <= 0:
        return 0.0, 0, 0

    ratio = my_completed / total_tasks
    return min(max(ratio, 0.0), 1.0), my_completed, total_tasks

def _handle_continue_click(batch_id):
    """
    Callback to handle navigation safely.
    This runs BEFORE the app reruns, avoiding the 'modified after instantiated' error.
    """
    # Switch the sidebar tab
    st.session_state["main_nav"] = "🏗️ Worker Workspace"
    # Set the URL parameter
    st.query_params["batch_id"] = str(batch_id)


def _render_batch_card(batch: dict, base_url: str):
    completion_ratio, my_completed, total_tasks = _compute_batch_completion(batch)
    days_remaining = 0
    plans = batch.get("plans", [])
    first_plan = plans[0] if plans else None

    if first_plan and first_plan.get("days_remaining") is not None:
        days_remaining = first_plan.get("days_remaining")

    access_status = (batch.get("access_status") or "locked").lower()
    status = batch.get("status", "unknown").capitalize()

    # ... [Keep your existing CSS Styles here] ...
    st.markdown("""
    <style>
        /* ... keep your existing css ... */
    </style>
    """, unsafe_allow_html=True)

    # --- Render Card ---
    st.markdown("<div class='batch-card'>", unsafe_allow_html=True)

    top = st.columns([5, 2])
    with top[0]:
        st.markdown(
            f"<div class='batch-title'>📦 {batch.get('batch_name')}</div>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<div class='batch-meta'>Status: <b>{status}</b> • Members: <b>{batch.get('members_count', 0)}</b></div>",
            unsafe_allow_html=True
        )

    with top[1]:
        if days_remaining is not None:
            st.markdown(
                f"<span class='badge badge-days'>⏳ {days_remaining} days left</span>",
                unsafe_allow_html=True
            )

        if access_status in ("accessible", "approved", "granted"):
            # === FIXED BUTTON LOGIC ===
            # We use on_click to change state safely
            st.button(
                "▶ Continue", 
                key=f"continue_{batch['id']}",
                on_click=_handle_continue_click,  # Calls the function defined above
                args=(batch["id"],)               # Passes the ID to that function
            )
            # No need for st.rerun() here manually, on_click triggers it automatically

        elif access_status == "pending":
            st.button("⏱ Pending", disabled=True, key=f"pending_{batch['id']}")
        else:
            if st.button("🔓 Request Access", key=f"req_{batch['id']}"):
                with st.spinner("Requesting access..."):
                    resp = request_batch_access(base_url, batch["id"])
                    if resp and resp.status_code in (200, 201):
                        st.success("Request sent.")
                        st.rerun() # This one is fine as is

    # --- Progress section ---
    st.write(f"**Progress:** {my_completed}/{total_tasks} tasks")
    st.progress(completion_ratio)

    # --- Plans preview ---
    if plans:
        st.caption("Plans:")
        for p in plans[:3]:
            st.markdown(
                f"- <b>{p.get('plan_name')}</b> — {p.get('my_completed_count')}/{p.get('tasks_count')}",
                unsafe_allow_html=True
            )

    st.markdown("</div>", unsafe_allow_html=True)

def _render_active_batches(active_batches: list, base_url: str):
    st.subheader("🧩 Active Batches")

    if not active_batches:
        st.info("You have no active batches right now. Ask your project manager to assign you to a batch.")
        return

    for batch in active_batches:
        _render_batch_card(batch, base_url)


def _format_date(dt_str):
    if not dt_str:
        return "-"
    try:
        # handle ...Z or timezone-aware
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00")).strftime("%Y-%m-%d")
    except Exception:
        return str(dt_str)


def _render_recent_plans(recent_plans: list):
    st.subheader("🕒 Recent Plans")

    st.markdown(
        """
        <style>
        .plan-card {
            border-radius: 0.9rem;
            padding: 0.75rem 0.95rem;
            margin-bottom: 0.5rem;
            border: 1px dashed rgba(255,255,255,0.18);
            background: rgba(255,255,255,0.02);
        }
        .plan-chip {
            display:inline-block;
            padding: 0.15rem 0.6rem;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 600;
            background: rgba(76, 111, 255, 0.12);
            color: #cdd5ff;
            margin-left: 0.25rem;
        }
        .plan-meta {
            font-size: 0.8rem;
            opacity: 0.8;
        }
        .plan-status-pill {
            display:inline-block;
            padding: 0.15rem 0.55rem;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 500;
            margin-top: 0.2rem;
        }
        .plan-status-good {
            background: rgba(40, 167, 69, 0.15);
            color: #b6f6c4;
        }
        .plan-status-warn {
            background: rgba(255, 193, 7, 0.15);
            color: #ffe9a8;
        }
        .plan-status-bad {
            background: rgba(220, 53, 69, 0.15);
            color: #ffb7c0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if not recent_plans:
        st.info("No recent plans yet. Start annotating to see your activity here.")
        return

    # Show up to 5 recent plans in full cards
    for idx, p in enumerate(recent_plans[:5]):
        plan_name = p.get("plan_name") or "Unnamed plan"
        plan_type = p.get("type") or "Unknown"
        batch_id = p.get("batch_id")
        created = _format_date(p.get("created_at"))
        deadline = _format_date(p.get("deadline"))

        tasks_count = p.get("tasks_count", 0) or 0
        my_done = p.get("my_completed_count", 0) or 0
        ratio = 0.0
        if tasks_count > 0:
            ratio = min(max(my_done / tasks_count, 0.0), 1.0)

        days_remaining = p.get("days_remaining", None)
        status_text = ""
        status_class = ""

        if days_remaining is not None:
            if days_remaining < 0:
                status_text = "Overdue"
                status_class = "plan-status-bad"
            elif days_remaining == 0:
                status_text = "Due today"
                status_class = "plan-status-warn"
            elif days_remaining <= 3:
                status_text = f"Due in {days_remaining} days"
                status_class = "plan-status-warn"
            else:
                status_text = f"Due in {days_remaining} days"
                status_class = "plan-status-good"

        with st.container():
            st.markdown('<div class="plan-card">', unsafe_allow_html=True)

            # Header row
            hcols = st.columns([3, 1])
            with hcols[0]:
                st.markdown(
                    f"**{plan_name}**"
                    f"<span class='plan-chip'>{plan_type}</span>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f"<div class='plan-meta'>Batch ID: <code>{batch_id}</code></div>",
                    unsafe_allow_html=True,
                )
            with hcols[1]:
                st.markdown(
                    f"<div class='plan-meta'>📅 Created: {created}<br/>⏳ Deadline: {deadline}</div>",
                    unsafe_allow_html=True,
                )

            # Status pill
            if status_text and status_class:
                st.markdown(
                    f"<span class='plan-status-pill {status_class}'>{status_text}</span>",
                    unsafe_allow_html=True,
                )

            # Progress
            if tasks_count > 0:
                st.markdown(
                    f"<div class='plan-meta' style='margin-top:0.4rem;'>"
                    f"Progress: <strong>{my_done}/{tasks_count}</strong> tasks"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                st.progress(ratio)
            else:
                st.caption("No tasks yet in this plan.")

            st.markdown("</div>", unsafe_allow_html=True)

    # If there are more, show a compact list inside an expander
    if len(recent_plans) > 5:
        with st.expander("Show more recent plans"):
            for p in recent_plans[5:]:
                plan_name = p.get("plan_name") or "Unnamed plan"
                created = _format_date(p.get("created_at"))
                st.markdown(f"- **{plan_name}** · Created: `{created}`")



# ------------ Main entry point for the Dashboard tab ------------

def dashboard_tab(st, BACKEND_API_BASE_URL: str, *_args, **_kwargs):
    """
    UI for the "Dashboard" tab:
    - Gamification header
    - Active batches
    - Recent plans
    """
    if not st.session_state.get("token"):
        st.warning("Please log in from the Login tab to view your dashboard.")
        return

    # Fetch dashboard data
    result = fetch_dashboard(BACKEND_API_BASE_URL)
    if result.get("error"):
        if result.get("status_code") == 401 or result.get("error") == "unauthorized":
            st.error("Unauthorized — please log in again.")
        elif result.get("error") == "network":
            st.error(f"Network error: {result.get('message')}")
        else:
            st.error(f"Failed to fetch dashboard: {result.get('message', result.get('body', 'unknown error'))}")
        return

    data = result.get("data", {})
    stats = {
        "xp_points": data.get("xp_points", 0),
        "datcoins": data.get("datcoins", 0),
        "level": data.get("level", 1),
        "accuracy": data.get("accuracy", 0),
        "level_progress": data.get("level_progress", 0),
    }
    active_batches = data.get("active_batches", [])
    recent_plans = data.get("recent_plans", [])

    # --- Layout ---
    _render_gamification_header(stats)

    st.markdown("---")

    # # Two-column main body: left = batches, right = recent plans
    # left_col, right_col = st.columns([2, 1])

    # with left_col:
    #     _render_active_batches(active_batches, BACKEND_API_BASE_URL)

    # with right_col:
    #     _render_recent_plans(recent_plans)

    # First: Active Batches
    _render_active_batches(active_batches, BACKEND_API_BASE_URL)

    # Then: Recent Plans (under it)
    st.markdown("")
    _render_recent_plans(recent_plans)

    st.markdown("---")
    st.info("Tip: keep your accuracy high and finish tasks to gain more XP and DatCoins 🎯")
