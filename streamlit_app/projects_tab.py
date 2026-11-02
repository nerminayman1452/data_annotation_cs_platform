import streamlit as st
import requests
import pandas as pd

# --- Helper to Fetch Data ---
@st.cache_data(show_spinner=False)
def get_projects(token, api_url):
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.get(f"{api_url}/project-management/organization-projects-list/", headers=headers)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        st.error(f"Error fetching projects: {e}")
    return []

@st.cache_data(show_spinner=False)
def get_my_organizations(token, api_url):
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.get(f"{api_url}/project-management/organization-details/", headers=headers)
        if resp.status_code == 200:
            return resp.json()
    except:
        pass
    return []

# ==========================================
# VIEW 1: PROJECTS LIST (Table View)
# ==========================================
def render_projects_list(st, BACKEND_API_BASE_URL):
    st.markdown("### 🗂️ All Projects")
    
    if not st.session_state.token:
        st.warning("Please log in to view projects.")
        return

    # 1. Search Bar
    col_search, _ = st.columns([1, 2])
    with col_search:
        search_proj = st.text_input("🔍 Search projects", placeholder="Project name...", key="search_proj_impl")

    # 2. Fetch Data
    with st.spinner("Loading projects..."):
        projs = get_projects(st.session_state.token, BACKEND_API_BASE_URL)

    # 3. Filter
    if search_proj and projs:
        projs = [p for p in projs if search_proj.lower() in (p.get('project_name','')+p.get('project_description','')).lower()]

    # 4. Render Table
    if projs and isinstance(projs, list):
        # Formatting for display
        data = []
        for p in projs:
            data.append({
                "ID": p["id"],
                "Project Name": p["project_name"],
                "Description": p["project_description"],
                "Status": "✅ Active" if p.get("is_active") else "❌ Inactive",
                "Org ID": p["organization"]
            })
            
        df = pd.DataFrame(data)
        st.dataframe(
            df, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "Status": st.column_config.TextColumn("Status", width="small"),
                "Description": st.column_config.TextColumn("Description", width="large"),
            }
        )
    else:
        st.info("No projects found. Go to the Planning tab to create one.")


# ==========================================
# VIEW 2: CREATE PROJECT FORM (Form Only)
# ==========================================
def render_create_project_form(st, BACKEND_API_BASE_URL):
    # Centered Layout for better UI
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.container(border=True):
            st.markdown("### 🚀 Create New Project")
            st.markdown("Define the core details of your crowdsourcing effort.")
            st.markdown("---")

            # Load Org Options
            orgs_data = get_my_organizations(st.session_state.token, BACKEND_API_BASE_URL)
            org_options = {}
            if orgs_data:
                org_options = {org.get('name', f"Org {org.get('id')}"): org.get('id') for org in orgs_data}

            with st.form("create_proj_form_isolated"):
                proj_name = st.text_input("Project Name", placeholder="e.g., Arabic Sentiment Analysis")
                
                # Org Selector
                if org_options:
                    selected_org_name = st.selectbox("Organization", list(org_options.keys()))
                    org_id = org_options[selected_org_name]
                else:
                    st.warning("No organizations found. Please create one first.")
                    org_id = None
                
                proj_desc = st.text_area("Description", placeholder="Describe the goal of this project...", height=150)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Buttons Row
                b_col1, b_col2 = st.columns([1, 1])
                with b_col2:
                    submitted = st.form_submit_button("Create Project", type="primary", use_container_width=True)
            
            if submitted:
                if not proj_name:
                    st.error("Project Name is required.")
                elif not org_id:
                    st.error("Organization is required.")
                else:
                    headers = {"Authorization": f"Bearer {st.session_state.token}"}
                    payload = {
                        "organization": org_id, 
                        "project_name": proj_name, 
                        "project_description": proj_desc, 
                        "is_active": True
                    }
                    
                    with st.spinner("Creating project..."):
                        try:
                            resp = requests.post(f"{BACKEND_API_BASE_URL}/project-management/create-project/", headers=headers, json=payload)
                            if resp.status_code in (200, 201):
                                st.success("Project created successfully!")
                                # Clear cache to refresh lists elsewhere
                                get_projects.clear() 
                                # Set a flag to redirect back to plan
                                st.session_state.view_mode = "default"
                                st.rerun()
                            else:
                                st.error(f"Failed: {resp.text}")
                        except Exception as e:
                            st.error(f"Connection error: {e}")