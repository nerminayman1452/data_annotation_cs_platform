import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# ========================================================
# Helpers
# ========================================================

def _auth_headers():
    token = st.session_state.get("token")
    return {"Authorization": f"Bearer {token}"} if token else {}

def _format_date(dt_str):
    if not dt_str:
        return "-"
    try:
        # Handle ISO format with Z
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00")).strftime("%Y-%m-%d")
    except Exception:
        return dt_str

# ========================================================
# UI: Gamification + Stats
# ========================================================

def _render_gamification_header(stats):
    """
    Renders the top stats bar using custom HTML cards for a dashboard look.
    """
    xp = stats.get("xp_points", 0)
    coins = stats.get("datcoins", 0)
    level = stats.get("level", 1)
    accuracy = stats.get("accuracy", 0.0)
    level_progress = stats.get("level_progress", 0)

    # Ensure ratio is between 0.0 and 1.0
    ratio = max(0.0, min(level_progress / 100, 1.0))

    st.markdown("""
        <style>
        .stat-card {
            border-radius: 10px;
            padding: 15px;
            background-color: #262730; /* Streamlit dark theme friendly */
            border: 1px solid rgba(250, 250, 250, 0.1);
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        .stat-value {
            font-size: 1.2rem;
            font-weight: bold;
            color: #ffffff;
            margin-top: 5px;
        }
        .stat-label {
            font-size: 0.85rem;
            color: #b0b0b0;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        </style>
    """, unsafe_allow_html=True)

    st.subheader("🎮 Your Progress")

    col1, col2, col3, col4 = st.columns([1, 1, 1, 2])

    with col1:
        st.markdown(f"""
            <div class='stat-card'>
                <div class='stat-label'>Level</div>
                <div class='stat-value'>{level}</div>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
            <div class='stat-card'>
                <div class='stat-label'>⭐ XP</div>
                <div class='stat-value'>{xp}</div>
            </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
            <div class='stat-card'>
                <div class='stat-label'>🪙 Coins</div>
                <div class='stat-value'>{coins}</div>
            </div>
        """, unsafe_allow_html=True)
    with col4:
        # Using a container to vertically align with cards
        with st.container():
            st.markdown(f"**🚀 Next Level** ({level_progress}%)")
            st.progress(ratio)
            st.caption(f"🎯 Average Accuracy: **{accuracy:.1f}%**")

# ========================================================
# UI: Batch Cards
# ========================================================

def _render_batch_card(batch):
    """
    Renders a single batch as a distinct visual block.
    """
    plans = batch.get("plans", [])
    total_tasks = sum(p.get("tasks_count", 0) for p in plans)
    total_done = sum(p.get("my_completed_count", 0) for p in plans)

    ratio = total_done / total_tasks if total_tasks else 0
    status = batch.get("status", "Unknown").capitalize()
    
    # Determine emoji based on access
    access_status = batch.get('access_status', 'open')
    access_icon = "🔒" if access_status == "locked" else "🔓"

    # Create a visual container (card)
    with st.container():
        # Header Row
        c1, c2 = st.columns([3, 1])
        with c1:
            st.markdown(f"### 🗂 {batch.get('batch_name')}")
        with c2:
            st.markdown(f"**{status}**")
        
        # Meta Data
        st.markdown(
            f"**Members:** `{batch.get('members_count',0)}` | "
            f"**Access:** {access_icon} `{access_status.capitalize()}`"
        )

        # Progress
        st.progress(ratio)
        st.caption(f"Batch Completion: {int(ratio*100)}%")

        # Plans Preview (Expandable to save space)
        if plans:
            with st.expander("Show Plans Preview", expanded=False):
                for p in plans[:5]: # Limit to 5 previews
                    p_done = p.get('my_completed_count', 0)
                    p_total = p.get('tasks_count', 0)
                    st.markdown(f"- **{p.get('plan_name')}**: {p_done}/{p_total}")
                
        st.divider()

# ========================================================
# UI: Plans Overview Table
# ========================================================

def _render_progress_table(batches):
    st.subheader("📋 Your Plans Overview")

    table_data = []

    # Flatten the hierarchical JSON into a flat list for the table
    for batch in batches:
        batch_name = batch.get("batch_name", "Unknown")
        access = "🔒 Locked" if batch.get("access_status") == "locked" else "🔓 Open"
        
        for plan in batch.get("plans", []):
            current = plan.get("my_completed_count", 0)
            total = plan.get("tasks_count", 0)
            
            # FIX: Calculate percentage on 0-100 scale
            percentage = (current / total) * 100 if total > 0 else 0.0
            
            table_data.append({
                "Batch": f"📦 {batch_name}",
                "Plan": plan.get("plan_name"),
                "Progress": percentage,
                "Stats": f"{current} / {total}", # Text representation
                "Created": _format_date(plan.get("created_at")),
                "Access": access
            })

    if not table_data:
        st.info("You have no active plans.")
        return

    # Convert to DataFrame
    df = pd.DataFrame(table_data)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_order=["Batch", "Plan", "Stats", "Progress", "Created", "Access"],
        column_config={
            "Batch": st.column_config.TextColumn("Batch Name", width="medium"),
            "Plan": st.column_config.TextColumn("Plan Name", width="large"),
            "Stats": st.column_config.TextColumn("Tasks", help="Completed / Total Tasks", width="small"),
            "Progress": st.column_config.ProgressColumn(
                "Completion", 
                format="%.0f%%", 
                min_value=0, 
                max_value=100, # FIX: Set max value to 100
                width="medium"
            ),
            "Created": st.column_config.TextColumn("Date", width="small"),
            "Access": st.column_config.TextColumn("Status", width="small")
        }
    )

# ========================================================
# UI: HITS Status Table (NEW)
# ========================================================

def _render_hits_status_table(stats):
    st.subheader("✅ HITS Status")
    
    # Construct data from the stats object
    data = [{
        "Total Assigned": stats.get("all_tasks", 0),
        "Submitted": stats.get("all_submitted", 0),
        "Approved": stats.get("all_approved", 0),
        "Rejected": stats.get("all_rejected", 0),
        "Earnings": stats.get("datcoins", 0.0)
    }]

    df = pd.DataFrame(data)

    # Render as a clean, wide table
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Total Assigned": st.column_config.NumberColumn(format="%d"),
            "Submitted": st.column_config.NumberColumn(format="%d"),
            "Approved": st.column_config.NumberColumn(format="%d"),
            "Rejected": st.column_config.NumberColumn(format="%d"),
            "Earnings": st.column_config.NumberColumn(format="$%.2f")
        }
    )

# ========================================================
# MAIN PROFILE TAB
# ========================================================

def profile_tab(st, base_url, auth_url):
    st.title("👤 User Profile")

    if not st.session_state.get("token"):
        st.warning("Please login to view your profile.")
        return

    headers = _auth_headers()

    # ----------------------------------------------------
    # 1. Fetch User Info
    # ----------------------------------------------------
    try:
        resp = requests.get(f"{auth_url}/auth/profile/", headers=headers)
        if resp.status_code == 200:
            user = resp.json()
            st.subheader("Personal Information")
            with st.container(border=True):
                col1, col2 = st.columns(2)
                with col1:
                    st.text_input("Full Name", value=f"{user.get('first_name','')} {user.get('last_name','')}", disabled=True)
                    st.text_input("Phone", value=user.get("phone_number") or "-", disabled=True)
                    st.text_input("Gender", value=user.get("gender") or "-", disabled=True)
                    st.text_input("Country", value=user.get("country") or "-", disabled=True)
                with col2:
                    st.text_input("Region", value=user.get("region") or "-", disabled=True)
                    st.text_input("Age", value=str(user.get("age") or "-"), disabled=True)
                    st.text_input("Weight", value=str(user.get("weight") or "-"), disabled=True)
                    role_str = ", ".join(user.get("roles", []))
                    st.text_input("Roles", value=role_str or "-", disabled=True)
        else:
            st.error(f"Failed to load profile. Status: {resp.status_code}")
    except Exception as e:
        st.error(f"Error connecting to server: {e}")

    st.divider()

    # ----------------------------------------------------
    # 2. Fetch Stats
    # ----------------------------------------------------
    stats = {}
    try:
        resp_stats = requests.get(f"{base_url}/dashboard/user-stats/", headers=headers)
        stats = resp_stats.json() if resp_stats.status_code == 200 else {}
        _render_gamification_header(stats)
    except Exception:
        st.warning("Could not load gamification stats.")

    st.divider()

    # ----------------------------------------------------
    # 3. Fetch My Active Batches & Plans
    # ----------------------------------------------------
    batches = []
    try:
        resp_batches = requests.get(f"{base_url}/dashboard/my-active-batches-plans-group/", headers=headers)
        if resp_batches.status_code == 200:
            batches = resp_batches.json().get("batches", [])
    except Exception:
        st.error("Error loading active batches.")

    # 4. Render Active Batches List
    if batches:
        st.subheader("🧩 Active Batches")
        for batch in batches:
            _render_batch_card(batch)
    else:
        st.info("No active batches found.")

    # 5. Render Plans Table
    if batches:
        _render_progress_table(batches)

    # 6. Render HITS Status Table (NEW)
    if stats:
        st.divider()
        _render_hits_status_table(stats)

    # ----------------------------------------------------
    # 7. Optional Chart
    # ----------------------------------------------------
    if batches:
        chart_rows = []
        for batch in batches:
            for plan in batch.get("plans", []):
                chart_rows.append({
                    "Plan": plan["plan_name"],
                    "Completed": plan["my_completed_count"],
                })

        if chart_rows:
            st.divider()
            df_chart = pd.DataFrame(chart_rows)
            st.subheader("📊 Plan Progress Chart")
            st.bar_chart(df_chart.set_index("Plan"))