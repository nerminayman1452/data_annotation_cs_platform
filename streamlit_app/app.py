import streamlit as st
import pandas as pd
import requests
import os
import time

# Import your existing tabs
from organizations_tab import organizations_tab
from assign_members_tab import assign_members_tab
from manage_members_tab import manage_members_tab
from plans_configurations_tab import plans_configurations_tab
from dashoard_tab import dashboard_tab
from batch_requests_tab import batch_requests_tab
from estimation_tab import estimation_tab
from tasks_managment_tab import tasks_management
from upload_batch_data_tab import upload_batch_data_tab
from projects_tab import render_create_project_form, render_projects_list
from batches_tab import render_create_batch_form, render_batches_list
from batch_details_page import batch_details_page

# --- Page Config ---
st.set_page_config(
    page_title="Crowdsourcing Platform", 
    page_icon="🧩",
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- Custom CSS for "Dark Platform" Look ---
st.markdown("""
<style>
    /* 1. Global Background (Deep Dark Blue/Gray) */
    .stApp { background-color: #0e1117; color: #fafafa; }
    
    /* 2. Card Styling */
    div[data-testid="stVerticalBlock"] > div[style*="background-color"] {
        background-color: #262730; padding: 2rem; border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3); border: 1px solid #3d3d3d;
    }

    /* 3. Primary Buttons (Green) */
    div.stButton > button[kind="primary"] {
        background-color: #28a745; border-color: #28a745; color: white;
        border-radius: 6px; font-weight: 600;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #34ce57; border-color: #34ce57;
    }

    /* 4. Secondary Buttons */
    div.stButton > button[kind="secondary"] {
        background-color: #3d3d3d; color: #ffffff; border: 1px solid #555;
    }
    div.stButton > button[kind="secondary"]:hover {
        background-color: #4e4e4e; border-color: #666;
    }

    /* 5. Sidebar */
    section[data-testid="stSidebar"] { background-color: #161a20; border-right: 1px solid #333; }
    
    /* 6. Text */
    h1, h2, h3, h4, h5, h6, p, span, div { color: #e0e0e0; font-family: 'Segoe UI', sans-serif; }
    
    /* 7. Inputs */
    .stTextInput > div > div > input, .stSelectbox > div > div {
        color: white; background-color: #262730; border: 1px solid #555;
    }
    
    /* 8. Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: transparent; color: #e0e0e0; }
    .stTabs [aria-selected="true"] { background-color: #262730; color: #ffffff; }
    
    /* 9. Expanders */
    .streamlit-expanderHeader { background-color: #262730; color: white; }
</style>
""", unsafe_allow_html=True)

# --- Session State Initialization ---
if "token" not in st.session_state:
    st.session_state.token = None
if "username" not in st.session_state:
    st.session_state.username = None
if "active_project_id" not in st.session_state:
    st.session_state.active_project_id = None
if "active_project_name" not in st.session_state:
    st.session_state.active_project_name = None
if "active_org_name" not in st.session_state:
    st.session_state.active_org_name = "MCIT" 
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "default" 

# --- Config ---
AUTH_API_BASE_URL = "http://127.0.0.1:8000"
# AUTH_API_BASE_URL = os.getenv("AUTH_API_BASE_URL", "http://auth-gateway-nginx:80")
BACKEND_API_BASE_URL = os.getenv("BACKEND_API_BASE_URL", "http://localhost:8003")

# ==========================================
#               HELPER FUNCTIONS
# ==========================================
def get_projects_list():
    try:
        headers = {
            "Authorization": f"Bearer {st.session_state.token}"
        } if st.session_state.token else {}

        resp = requests.get(
            f"{BACKEND_API_BASE_URL}/project-management/organization-projects-list/",
            headers=headers,
            timeout=10
        )

        if resp.status_code == 200:
            return resp.json()  # ✅ THIS WAS MISSING
        else:
            st.error(f"Failed to load projects ({resp.status_code})")
            return []

    except Exception as e:
        st.error(f"Project fetch error: {e}")
        return []


def fetch_all_batches():
    """Fetches ALL batches in the system (not filtered by project)."""
    try:
        headers = {"Authorization": f"Bearer {st.session_state.token}"} if st.session_state.token else {}
        # Removing the ?project_id= filter to get everything
        url = f"{BACKEND_API_BASE_URL}/project-management/batches/"
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            return resp.json()
        return []
    except Exception:
        return []    

# ==========================================
#               UI FUNCTIONS
# ==========================================

def login_form():
    """Centered, clean login card."""
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("<h2 style='text-align: center; color: white;'>🔐 Sign In</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #a0a0a0;'>Access the Crowdsourcing Control Center</p>", unsafe_allow_html=True)
            
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                submitted = st.form_submit_button("Sign In", type="primary", use_container_width=True)
                
                if submitted:
                    try:
                        resp = requests.post(f"{AUTH_API_BASE_URL}/auth/login/", json={"username": username, "password": password})
                        if resp.status_code == 200:
                            data = resp.json()
                            token = data.get("access") or data.get("access_token") or data.get("token")
                            if token:
                                st.session_state.token = token
                                st.session_state.username = username
                                st.success("Login successful!")
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                st.error("No access token received.")
                        else:
                            st.error("Invalid credentials.")
                    except Exception as e:
                        st.error(f"Connection Error: {e}")

# ==========================================
#            PLANNING UI 
# ==========================================
def planning_ui():
    """Project Planning UI"""
    
    # 1. CREATE PROJECT
    if st.session_state.view_mode == "create_project":
        col_back, _ = st.columns([1, 5])
        with col_back:
            if st.button("← Back"):
                st.session_state.view_mode = "default"
                st.rerun()
        render_create_project_form(st, BACKEND_API_BASE_URL)
        return

    # 2. CREATE BATCH
    if st.session_state.view_mode == "create_batch":
        col_back, _ = st.columns([1, 5])
        with col_back:
            if st.button("← Back"):
                st.session_state.view_mode = "default"
                st.rerun()
        render_create_batch_form(st, BACKEND_API_BASE_URL)
        return

    # 3. CREATE TASK
    if st.session_state.view_mode == "create_task":
        if st.button("← Back"):
            st.session_state.view_mode = "default"
            st.rerun()
        plans_configurations_tab(st, BACKEND_API_BASE_URL)
        return
    
    # 4. MANAGE ORG
    if st.session_state.view_mode == "manage_org":
        if st.button("← Back"):
            st.session_state.view_mode = "default"
            st.rerun()
        organizations_tab(st, BACKEND_API_BASE_URL)
        return

    # --- DEFAULT PLANNING DASHBOARD ---
    col_header, col_org = st.columns([3, 1])
    with col_header:
        st.title("Project Planning")
    with col_org:
        if st.button("🏢 New Organization", use_container_width=True, type="primary"):
            st.session_state.view_mode = "manage_org"
            st.rerun()

    # Control Bar
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
        
        projects = get_projects_list()

        if not isinstance(projects, list):
            st.error("Invalid project data format received.")
            projects = []

        project_names = [
            p.get("project_name")
            for p in projects
            if isinstance(p, dict) and "project_name" in p
        ]
        
        with c1:
            current_idx = 0
            if st.session_state.active_project_name in project_names:
                current_idx = project_names.index(st.session_state.active_project_name) + 1
            
            selected_proj_name = st.selectbox(
                "Select Project", 
                options=["Select a project..."] + project_names,
                label_visibility="collapsed",
                index=current_idx
            )
            
            if selected_proj_name != "Select a project...":
                st.session_state.active_project_name = selected_proj_name
                for p in projects:
                    if p["project_name"] == selected_proj_name:
                        st.session_state.active_project_id = p["id"]
            else:
                st.session_state.active_project_name = None
                st.session_state.active_project_id = None

        with c2:
            if st.button("➕ Create Project", use_container_width=True):
                st.session_state.view_mode = "create_project"
                st.rerun()

        with c3:
            btn_disabled = not st.session_state.active_project_id
            if st.button("📦 New Batch", use_container_width=True, disabled=btn_disabled):
                st.session_state.view_mode = "create_batch"
                st.rerun()
                
        with c4:
            btn_disabled = not st.session_state.active_project_id
            if st.button("📋 New Task", use_container_width=True, disabled=btn_disabled):
                st.session_state.view_mode = "create_task"
                st.rerun()

    st.markdown("---")

    if st.session_state.active_project_id:
        st.caption(f"Settings for: **{st.session_state.active_project_name}**")
        estimation_tab(st, BACKEND_API_BASE_URL)
    else:
        st.info("👆 Please select a project to configure details.")


# ==========================================
#        IMPLEMENTATION UI (UPDATED)
# ==========================================
def implementation_ui():
    """Monitoring & Implementation View with Side-by-Side Control Panel"""
    
    if "batch_nav" not in st.session_state:
        st.session_state.batch_nav = "list" 

    st.title("Implementation & Monitoring")
    
    # 1. PREPARE BATCH DATA (Global List, not just project specific)
    batch_options = []
    batch_id_map = {}
    
    # Call the new function to fetch ALL batches
    all_batches_data = fetch_all_batches()
    
    for b in all_batches_data:
        b_id = b.get('id')
        b_name = b.get('batch_name', 'Unnamed Batch')
        # Optional: Add project ID to label for clarity since we are showing all
        project_ref = f" (Proj: {b.get('project', '?')})"
        label = f"{b_name} - ID: {b_id}"
        batch_options.append(label)
        batch_id_map[label] = b_id
    
    # Main Tabs
    tab_projects, tab_batches, tab_tasks = st.tabs([
        "🗂️ Projects List", 
        "📦 Batches & Operations", 
        "✅ Tasks & Monitoring"
    ])

    # --- TAB 1: PROJECTS ---
    with tab_projects:
        render_projects_list(st, BACKEND_API_BASE_URL)

    # --- TAB 2: BATCHES & OPERATIONS ---
    with tab_batches:
        col_display, col_controls = st.columns([0.75, 0.25], gap="large")

        # --- RIGHT COLUMN: ACTIONS ---
        with col_controls:
            with st.container(border=True):
                st.markdown("### 🛠️ Actions")
                
                def set_view(view_name):
                    st.session_state.batch_nav = view_name
                
                if st.button("📋 Active Batches List", use_container_width=True, type="primary" if st.session_state.batch_nav == "list" else "secondary"):
                    set_view("list")
                st.markdown("---")
                if st.button("📤 Upload Data", use_container_width=True, type="primary" if st.session_state.batch_nav == "upload" else "secondary"):
                    set_view("upload")
                if st.button("👥 Assign Members", use_container_width=True, type="primary" if st.session_state.batch_nav == "assign" else "secondary"):
                    set_view("assign")
                if st.button("🔐 Access Requests", use_container_width=True, type="primary" if st.session_state.batch_nav == "access" else "secondary"):
                    set_view("access")
                if st.button("👥 Invite Members", use_container_width=True, disabled=True):
                    pass
                if st.button("📇 Manage Members", use_container_width=True, type="primary" if st.session_state.batch_nav == "members" else "secondary"):
                    set_view("members")
                st.markdown("---")

                if st.button("📋 Question Bank ", use_container_width=True, disabled=True):
                    pass  # Placeholder for future feature


        # --- LEFT COLUMN: DISPLAYS ---
        with col_display:
            
            if st.session_state.batch_nav == "list":
                st.markdown("### 📋 Active Batches")
                # You might want to update render_batches_list to accept all batches too, 
                # but assuming it fetches its own data or relies on backend filtering:
                render_batches_list(st, BACKEND_API_BASE_URL)
            
            elif st.session_state.batch_nav == "upload":
                st.markdown("### 📤 Upload Batch Data")
                if st.button("← Back to List"):
                    set_view("list")
                    st.rerun()
                st.divider()
                upload_batch_data_tab(st, BACKEND_API_BASE_URL)

            # --- ASSIGN MEMBERS (Global Access) ---
            elif st.session_state.batch_nav == "assign":
                st.markdown("### 👥 Assign Workforce")
                if st.button("← Back to List"):
                    set_view("list")
                    st.rerun()
                st.divider()
                
                # Removed the "if st.session_state.active_project_id" check
                # Now we pass the global batch list
                assign_members_tab(st, AUTH_API_BASE_URL, BACKEND_API_BASE_URL, batch_options, batch_id_map)

            elif st.session_state.batch_nav == "access":
                st.markdown("### 🔐 Access Requests")
                if st.button("← Back to List"):
                    set_view("list")
                    st.rerun()
                st.divider()
                # Access requests might still be best filtered by project context, 
                # but if you want all, you'd update batch_requests_tab similarly.
                # Keeping project check here for safety unless you want that global too.
                batch_requests_tab(st, BACKEND_API_BASE_URL)

            # --- MANAGE MEMBERS (Global Access) ---
            elif st.session_state.batch_nav == "members":
                st.markdown("### 📇 Manage Members")
                if st.button("← Back to List"):
                    set_view("list")
                    st.rerun()
                st.divider()
                # Removed the "if st.session_state.active_project_id" check
                manage_members_tab(st, BACKEND_API_BASE_URL, batch_options, batch_id_map)

    # --- TAB 3: TASKS ---
    with tab_tasks:
        tasks_management(st, BACKEND_API_BASE_URL)


# ==========================================
#        WORKER WORKSPACE LOGIC (FIXED)
# ==========================================
def worker_workspace_logic():
    """Worker View Controller"""
    # 1. Get Query Params
    query_params = st.query_params
    params = {k: v for k, v in query_params.items()}
    
    batch_id = params.get("batch_id")
    plan_id = params.get("plan_id")

    # --- STATE C: Task View (Batch + Plan selected) ---
    if batch_id and plan_id:
        # Button to go back up one level to Batch Details
        if st.sidebar.button("⬅ Back to Batch Details"):
            st.query_params["plan_id"] = None # Remove only plan_id
            st.rerun() # Reloads app, will fall into State B
            
        from annotation_tasks_page import annotation_tasks_page 
        annotation_tasks_page(st, BACKEND_API_BASE_URL, params)

    # --- STATE B: Details View (Batch selected, No Plan) ---
    elif batch_id:
        # Button to go back up one level to List
        if st.sidebar.button("⬅ Back to All Batches"):
            st.query_params.clear() # Remove all params
            st.rerun() # Reloads app, will fall into State A
            
        # Call the batch details page
        batch_details_page(st, BACKEND_API_BASE_URL, batch_id)

    # --- STATE A: List View (Nothing selected) ---
    else:
        st.title("My Workspace")
        st.markdown("Welcome! Here are the batches assigned to you.")
        from annotation_tasks_tab import annotation_tasks_tab
        annotation_tasks_tab(st, BACKEND_API_BASE_URL)


# ==========================================
#           MAIN NAVIGATION CONTROLLER
# ==========================================

st.sidebar.title("🧩 Crowdsourcing Platform")
if st.session_state.username:
    st.sidebar.markdown(f"👤 **{st.session_state.username}**")
st.sidebar.markdown("---")

if not st.session_state.token:
    current_selection = "Login"
else:
    current_selection = st.sidebar.radio(
        "Main Menu", 
        ["📊 Dashboard", "🛠️ Project Management", "🏗️ Worker Workspace", "⚙️ Profile"],
        key="main_nav"
    )

selected_sub_page = None
if current_selection == "🛠️ Project Management":
    st.sidebar.markdown("### Phase")
    selected_sub_page = st.sidebar.radio(
        "Select Phase:", 
        ["1. Planning", "2. Implementation", "3. Reports"],
        label_visibility="collapsed"
    )

st.sidebar.markdown("---")
if st.session_state.token:
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state.token = None
        st.session_state.username = None
        st.session_state.active_project_id = None
        st.session_state.view_mode = "default"
        st.rerun()

# ==========================================
#               PAGE ROUTING
# ==========================================

if not st.session_state.token:
    login_form()

elif current_selection == "📊 Dashboard":
    dashboard_tab(st, BACKEND_API_BASE_URL)

elif current_selection == "🛠️ Project Management":
    if "Planning" in selected_sub_page:
        planning_ui()
    elif "Implementation" in selected_sub_page:
        implementation_ui()
    else:
        st.title("Reports & Analytics")
        st.info("Export CSVs and view project health charts here.")

elif current_selection == "🏗️ Worker Workspace":
    worker_workspace_logic()

elif current_selection == "⚙️ Profile":
    st.title("User Profile")
    from profile_tab import profile_tab
    profile_tab(st, BACKEND_API_BASE_URL, AUTH_API_BASE_URL)