import streamlit as st
import requests

# --- Helper: Fetch Batches ---
@st.cache_data(show_spinner=False)
def get_batches(token, api_url):
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.get(f"{api_url}/project-management/batches/", headers=headers)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        st.error(f"Connection error: {e}")
    return []

# ==========================================
# VIEW 1: BATCHES LIST (Monitoring View)
# ==========================================
def render_batches_list(st, BACKEND_API_BASE_URL):
    # CSS for the Cards (Scoped to this view)
    st.markdown("""
        <style>
        .batch-card {
            background-color: #262730;
            border-radius: 10px;
            padding: 1rem;
            margin-bottom: 1rem;
            border: 1px solid #3d3d3d;
            border-left: 5px solid #1976d2;
            transition: transform 0.2s;
        }
        .batch-card:hover {
            border-color: #555;
            transform: translateX(5px);
        }
        .batch-header {
            font-size: 1.1em; 
            font-weight: 600; 
            color: #e0e0e0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .batch-status {
            padding: 2px 10px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: bold;
        }
        .status-active { background-color: rgba(40, 167, 69, 0.2); color: #28a745; }
        .status-inactive { background-color: rgba(220, 53, 69, 0.2); color: #dc3545; }
        .batch-meta { font-size: 0.9em; color: #a0a0a0; margin-top: 5px; }
        .batch-desc { margin-top: 8px; font-size: 0.95em; color: #cccccc; }
        </style>
    """, unsafe_allow_html=True)

    # 1. Search Bar
    col_search, _ = st.columns([1, 2])
    with col_search:
        search_batch = st.text_input("🔍 Search Batches", placeholder="Name, description, or project...", key="search_batch_impl")

    # 2. Fetch Data
    with st.spinner("Loading batches..."):
        batches = get_batches(st.session_state.token, BACKEND_API_BASE_URL)

    # 3. Filter
    if search_batch:
        batches = [b for b in batches if search_batch.lower() in (str(b.get('batch_name',''))+str(b.get('batch_description',''))+str(b.get('project',''))).lower()]

    # 4. Render Cards
    if batches:
        for batch in batches:
            status = batch.get('is_active', True)
            status_html = f"<span class='batch-status status-active'>Active</span>" if status else f"<span class='batch-status status-inactive'>Inactive</span>"
            
            with st.container():
                st.markdown(f"""
                <div class="batch-card">
                    <div class="batch-header">
                        <span>📦 {batch.get('batch_name', 'Unnamed Batch')}</span>
                        {status_html}
                    </div>
                    <div class="batch-meta">
                        ID: {batch.get('id')} &nbsp;•&nbsp; Project ID: {batch.get('project', 'N/A')}
                    </div>
                    <div class="batch-desc">
                        {batch.get('batch_description', 'No description provided.')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Logic to show tasks inside the list (Optional expander)
                with st.expander("🔻 View Details", expanded=False):
                    c1, c2 = st.columns(2)
                    c1.info(f"Created At: {batch.get('created_at', 'N/A')}")
                    c2.info(f"Updated At: {batch.get('updated_at', 'N/A')}")
                    
    else:
        st.info("No batches found.")


# ==========================================
# VIEW 2: CREATE BATCH FORM (Form Only)
# ==========================================
def render_create_batch_form(st, BACKEND_API_BASE_URL):
    # Determine Context (Active Project)
    active_project_id = st.session_state.get('active_project_id')
    active_project_name = st.session_state.get('active_project_name', 'Unknown Project')

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container(border=True):
            st.markdown(f"### 📦 Create New Batch")
            st.caption(f"Adding data container for Project: **{active_project_name}**")
            st.markdown("---")

            if not active_project_id:
                st.error("❌ No project selected. Please go back and select a project first.")
                return

            with st.form("create_batch_form_isolated"):
                batch_name = st.text_input("Batch Name", placeholder="e.g., Dataset A - High Quality")
                batch_desc = st.text_area("Description", placeholder="Describe the source or nature of this data...", height=120)
                
                # Hidden info for user context
                st.markdown(f"<small style='color:#666'>Linked to Project ID: {active_project_id}</small>", unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                submitted = st.form_submit_button("Create Batch", type="primary", use_container_width=True)

            if submitted:
                if not batch_name:
                    st.error("Batch Name is required.")
                else:
                    headers = {"Authorization": f"Bearer {st.session_state.token}"}
                    payload = {
                        "project": active_project_id, 
                        "batch_name": batch_name, 
                        "batch_description": batch_desc
                    }
                    
                    with st.spinner("Creating batch..."):
                        try:
                            resp = requests.post(f"{BACKEND_API_BASE_URL}/project-management/batches/", headers=headers, json=payload)
                            if resp.status_code in (200, 201):
                                st.success("✅ Batch created successfully!")
                                # Clear cache so the list updates
                                get_batches.clear()
                                time.sleep(1)
                                # Redirect back to main plan
                                st.session_state.view_mode = "default"
                                st.rerun()
                            else:
                                st.error(f"Failed: {resp.text}")
                        except Exception as e:
                            st.error(f"Connection error: {e}")