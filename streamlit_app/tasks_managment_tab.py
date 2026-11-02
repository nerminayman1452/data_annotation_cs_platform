from datetime import datetime
import pandas as pd
from PIL import Image
from io import BytesIO
import streamlit as st
import requests

from user_assignments_section import render_assigned_users_section

# ==========================================
#           HELPER FUNCTIONS
# ==========================================

def fetch_batches_for_dropdown(backend_url, headers, project_id=None):
    """Fetches batches, optionally filtering by project."""
    try:
        url = f"{backend_url}/project-management/batches/"
        if project_id:
            url += f"?project={project_id}"
        
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, dict) and "results" in data:
                return data["results"]
            return data
        return []
    except Exception:
        return []

def fetch_plans_for_batch(backend_url, headers, batch_id):
    """Fetches classification plans for a specific batch."""
    try:
        url = f"{backend_url}/image-annotations/image-classification-plans/{batch_id}/"
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            return resp.json()
        return []
    except Exception:
        return []

def badge(text, color="#4CAF50"):
    """Returns an HTML badge for labels."""
    return f"<span style='background-color:{color}; color:white; padding: 4px 10px; border-radius: 15px; font-size: 12px; font-weight: 500; margin-right: 5px;'>{text}</span>"

# ==========================================
#           UI COMPONENTS
# ==========================================

def render_plan_dashboard(plan):
    """Renders a beautiful dashboard summary of the selected plan."""
    config = plan.get("plan_config", {})
    label_types = plan.get("label_types", [])
    
    # --- Header Section ---
    st.markdown(f"#### 📑 Plan: {plan.get('plan_name')}")
    
    # --- Metrics Row ---
    # We use st.container with border to group these nicely
    with st.container(border=True):
        c1, c2, c3, c4, c5 = st.columns(5)
        
        with c1:
            st.metric("💰 Reward", f"${config.get('reward_per_task', 0)}")
        with c2:
            st.metric("👥 Annotators", f"{config.get('annotators_per_task', 1)}")
        with c3:
            st.metric("🤝 Consensus", f"{config.get('acceptance_agreement', 0)}%")
        with c4:
            st.metric("⏱ Time Limit", f"{config.get('time_allotted_per_annotator', 0)}s")
        with c5:
            dist_mode = config.get('task_distribution_mode', 'auto')
            st.metric("⚙️ Mode", dist_mode.title())

    # --- Details & Instructions ---
    c_desc, c_labels = st.columns([2, 1])
    
    with c_desc:
        with st.expander("📝 Description & Questions", expanded=False):
            st.markdown(f"**Description:**")
            st.caption(config.get('description', 'No description provided.'))
            st.markdown("---")
            st.markdown(f"**Question presented to user:**")
            st.info(config.get('question', 'No question configured.'))

    with c_labels:
        with st.container(border=True):
            st.caption("🏷️ Label Taxonomy")
            if label_types:
                # Render badges
                html_badges = "".join([badge(l.get('label_type', 'Unknown'), "#262730") for l in label_types])
                st.markdown(html_badges, unsafe_allow_html=True)
            else:
                st.warning("No labels defined.")


# ==========================================
#           MAIN TAB LOGIC
# ==========================================

def tasks_management(st, BACKEND_API_BASE_URL):
    st.title("📋 Tasks Management (Admin / Linguist Lead)")

    if not st.session_state.token:
        st.warning("🔒 Please login as Admin/Linguist Lead to manage tasks.")
        return

    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    active_project_id = st.session_state.get("active_project_id")

    # Tabs
    tab1, tab2, tab3 = st.tabs(["🛠 Generate Tasks", "📊 Monitor Tasks", "👥 Assign Tasks"])

    # ------------------------------------
    # TAB 1: GENERATE TASKS
    # ------------------------------------
    with tab1:
        st.markdown("### 🛠 Generate Tasks")
        st.caption("Select a batch and a configuration plan to generate labeling tasks.")
        
        col1, col2 = st.columns(2)
        
        # 1. Select Batch
        with col1:
            batches_gen = fetch_batches_for_dropdown(BACKEND_API_BASE_URL, headers, active_project_id)
            if not batches_gen:
                st.warning("No batches found. Create a batch first.")
                batch_id_gen = None
            else:
                batch_opts_gen = {f"{b['batch_name']} (ID: {b['id']})": b['id'] for b in batches_gen}
                selected_batch_name_gen = st.selectbox("Select Batch", options=list(batch_opts_gen.keys()), key="gen_batch_select")
                batch_id_gen = batch_opts_gen[selected_batch_name_gen]

        # 2. Select Plan (Dependent on Batch)
        with col2:
            if batch_id_gen:
                plans_gen = fetch_plans_for_batch(BACKEND_API_BASE_URL, headers, batch_id_gen)
                if not plans_gen:
                    st.info("No plans found for this batch.")
                    plan_id_gen = None
                else:
                    plan_opts_gen = {f"{p['plan_name']} (ID: {p['id']})": p['id'] for p in plans_gen}
                    selected_plan_name_gen = st.selectbox("Select Plan", options=list(plan_opts_gen.keys()), key="gen_plan_select")
                    plan_id_gen = plan_opts_gen[selected_plan_name_gen]
            else:
                plan_id_gen = None

        st.divider()

        if st.button("🚀 Generate Tasks", use_container_width=True, disabled=not (batch_id_gen and plan_id_gen)):
            with st.spinner("Generating tasks..."):
                resp = requests.post(
                    f"{BACKEND_API_BASE_URL}/image-annotations/generate/image-classification-task/",
                    json={"batch": batch_id_gen, "plan": plan_id_gen},
                    headers=headers,
                )
            if resp.status_code == 201:
                st.success("✅ Tasks generated successfully!")
            else:
                st.error(f"❌ Failed to generate tasks: {resp.text}")

    # ------------------------------------
    # TAB 2: MONITOR TASKS (UPDATED UI)
    # ------------------------------------
    with tab2:
        st.markdown("### 📊 Monitor Tasks")
        st.caption("View configuration, progress, assigned users, and task details.")

        m_col1, m_col2 = st.columns(2)

        # 1. Select Batch (Monitor)
        with m_col1:
            batches_mon = fetch_batches_for_dropdown(BACKEND_API_BASE_URL, headers, active_project_id)
            if not batches_mon:
                st.warning("No batches found.")
                batch_id_mon = None
            else:
                batch_opts_mon = {f"{b['batch_name']} (ID: {b['id']})": b['id'] for b in batches_mon}
                selected_batch_name_mon = st.selectbox("Select Batch", options=list(batch_opts_mon.keys()), key="mon_batch_select")
                batch_id_mon = batch_opts_mon[selected_batch_name_mon]

        # 2. Select Plan (Monitor)
        selected_plan_obj = None
        with m_col2:
            if batch_id_mon:
                plans_mon = fetch_plans_for_batch(BACKEND_API_BASE_URL, headers, batch_id_mon)
                if not plans_mon:
                    st.info("No plans found.")
                    plan_id_mon = None
                else:
                    plan_opts_mon = {f"{p['plan_name']} (ID: {p['id']})": p['id'] for p in plans_mon}
                    selected_plan_name_mon = st.selectbox("Select Plan", options=list(plan_opts_mon.keys()), key="mon_plan_select")
                    plan_id_mon = plan_opts_mon[selected_plan_name_mon]
                    
                    # RETRIEVE FULL PLAN OBJECT FOR DASHBOARD
                    selected_plan_obj = next((p for p in plans_mon if p["id"] == plan_id_mon), None)
            else:
                plan_id_mon = None

        st.divider()

        # --- NEW: DISPLAY PLAN DETAILS DASHBOARD ---
        if selected_plan_obj:
            render_plan_dashboard(selected_plan_obj)
            st.divider()

        # --- FETCH TASKS BUTTON ---
        if st.button("📥 Fetch Task Data", use_container_width=True, disabled=not (batch_id_mon and plan_id_mon)):
            with st.spinner("Fetching tasks..."):
                resp = requests.get(
                    f"{BACKEND_API_BASE_URL}/image-annotations/image-classification-tasks/{batch_id_mon}/{plan_id_mon}/",
                    headers=headers,
                )

            if resp.status_code != 200:
                st.error(f"❌ Error fetching tasks: {resp.text}")
                return

            tasks = resp.json()

            if not tasks:
                st.info("📭 No tasks found for this configuration.")
                return

            # 1. Render Users Stats
            # Extract users from the first task if available, or fetch separately if your API supports it
            annotators_list = tasks[0].get("annotators", [])
            reviewers_list = tasks[0].get("reviewers", [])
            
            st.markdown("### 👷 Workforce Status")
            render_assigned_users_section(annotators=annotators_list, reviewers=reviewers_list)

            st.divider()

            # 2. Render Task List
            st.markdown(f"### 🖼 Tasks List ({len(tasks)})")
            
            # Simple pagination for better UI performance
            page_size = 10
            if len(tasks) > page_size:
                page_num = st.number_input("Page", min_value=1, max_value=(len(tasks)//page_size)+1, value=1)
                start_idx = (page_num - 1) * page_size
                current_tasks = tasks[start_idx : start_idx + page_size]
            else:
                current_tasks = tasks

            for task in current_tasks:
                with st.expander(f"Task {task['id']} - Status: {task.get('status', 'Pending')}"):
                    t_col1, t_col2 = st.columns([1, 2])
                    with t_col1:
                        img_url = task.get("image_url")
                        if img_url:
                            st.image(img_url, width=200)
                        else:
                            st.markdown("🚫 *No Image*")
                            
                    with t_col2:
                        st.markdown(f"**Status:** `{task.get('status', 'Pending')}`")
                        st.markdown(f"**Created:** {task.get('created_at')}")
                        
                        # Show labels visually
                        lbls = [l["label_type"] for l in task.get("label_choices", [])]
                        if lbls:
                            st.markdown(f"**Labels:** {', '.join(lbls)}")
                        else:
                            st.caption("No labels defined.")

    # ------------------------------------
    # TAB 3: ASSIGN TASKS
    # ------------------------------------
    with tab3:
        st.markdown("### 👥 Assign Tasks")
        st.caption("Distribute generated tasks among annotators.")

        a_col1, a_col2 = st.columns(2)

        # 1. Select Batch (Assign)
        with a_col1:
            batches_asn = fetch_batches_for_dropdown(BACKEND_API_BASE_URL, headers, active_project_id)
            if not batches_asn:
                st.warning("No batches found.")
                batch_id_asn = None
            else:
                batch_opts_asn = {f"{b['batch_name']} (ID: {b['id']})": b['id'] for b in batches_asn}
                selected_batch_name_asn = st.selectbox("Select Batch", options=list(batch_opts_asn.keys()), key="asn_batch_select")
                batch_id_asn = batch_opts_asn[selected_batch_name_asn]

        # 2. Select Plan (Assign)
        with a_col2:
            if batch_id_asn:
                plans_asn = fetch_plans_for_batch(BACKEND_API_BASE_URL, headers, batch_id_asn)
                if not plans_asn:
                    st.info("No plans found.")
                    plan_id_asn = None
                else:
                    plan_opts_asn = {f"{p['plan_name']} (ID: {p['id']})": p['id'] for p in plans_asn}
                    selected_plan_name_asn = st.selectbox("Select Plan", options=list(plan_opts_asn.keys()), key="asn_plan_select")
                    plan_id_asn = plan_opts_asn[selected_plan_name_asn]
            else:
                plan_id_asn = None

        st.divider()

        if st.button("🔄 Auto-assign Tasks", use_container_width=True, disabled=not (batch_id_asn and plan_id_asn)):
            with st.spinner("Assigning tasks..."):
                resp = requests.post(
                    f"{BACKEND_API_BASE_URL}/image-annotations/assign/image-classification-tasks/{plan_id_asn}/",
                    headers=headers,
                )
            if resp.status_code == 200:
                st.success("✅ Tasks assigned successfully!")
            else:
                st.error(f"❌ Failed to assign tasks: {resp.text}")