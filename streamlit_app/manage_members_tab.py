import streamlit as st
import requests
from typing import Any, Dict

def manage_members_tab(st, BACKEND_API_BASE_URL, batch_options=None, batch_id_map=None):
    st.subheader("\U0001F465 View & Manage Batch Members")
    
    # ... (Keep your existing CSS style block here) ...
    st.markdown("""
        <style>
        .member-card {
            border-radius: 10px;
            padding: 1.1em 0.9em 0.9em 0.9em;
            margin-bottom: 1.1em;
            border: 1.5px solid #1976d2;
            box-shadow: 0 1px 4px #e0e0e0;
            background: transparent;
            transition: box-shadow 0.2s;
        }
        /* ... rest of your CSS ... */
        </style>
    """, unsafe_allow_html=True)

    if st.session_state.token:
        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        
        # --- NEW LOGIC: Use Selectbox if options exist, otherwise text input ---
        batch_id = None
        
        col_sel, col_btn = st.columns([4, 1])
        with col_sel:
            if batch_options and batch_id_map:
                selected_batch_label = st.selectbox(
                    "Select Batch", 
                    options=batch_options,
                    help="Select a batch from the active project."
                )
                batch_id = batch_id_map.get(selected_batch_label)
            else:
                batch_id = st.text_input("\U0001F50E Enter Batch ID", help="Type a batch ID to see its members.")

        with col_btn:
             # Add spacing to align button with input/select
             st.write("") 
             st.write("")
             load_members = st.button("\U0001F50E Load", key="load_members_btn")

        # --- Initialize Session States ---
        if "open_update_member_id" not in st.session_state:
            st.session_state.open_update_member_id = None
        if "batch_members_cache" not in st.session_state:
            st.session_state.batch_members_cache = {}
        if "batch_members_cache_time" not in st.session_state:
            st.session_state.batch_members_cache_time = {}
        if "batch_members_last_id" not in st.session_state:
            st.session_state.batch_members_last_id = None
            
        import time
        cache_ttl = 300  # 5 minutes

        def fetch_batch_members(b_id: str, h: Dict[str, str]) -> Any:
            resp = requests.get(f"{BACKEND_API_BASE_URL}/project-management/batches/{b_id}/members/", headers=h)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("batch_members", []) if isinstance(data, dict) else data
            else:
                return f"Failed to fetch members: {resp.text}"

        members = []
        error_msg = None
        now = time.time()
        
        # Determine if we should fetch
        cache_key = f"{batch_id}"
        cache_time = st.session_state.batch_members_cache_time.get(cache_key, 0)
        should_fetch = False
        
        if batch_id:
            # Auto-fetch if switching to a new batch via dropdown, or if button clicked
            is_new_selection = (st.session_state.batch_members_last_id != batch_id)
            
            if load_members or is_new_selection:
                should_fetch = True
            elif (
                cache_key in st.session_state.batch_members_cache
                and now - cache_time < cache_ttl
            ):
                members = st.session_state.batch_members_cache[cache_key]
            
            if should_fetch:
                result = fetch_batch_members(batch_id, headers)
                if isinstance(result, str):
                    error_msg = result
                else:
                    members = result
                    st.session_state.batch_members_cache[cache_key] = members
                    st.session_state.batch_members_cache_time[cache_key] = now
                    st.session_state.batch_members_last_id = batch_id

        # --- Render Results ---
        if batch_id and error_msg:
            st.error(error_msg)
        elif batch_id:
            if members:
                # ... (Keep your existing member rendering loop exactly as is) ...
                for idx, member in enumerate(members):
                    # ... (rest of your existing logic for rendering cards) ...
                    user_info = member.get('user_info') or member.get('user') or {}
                    # ... [Insert your existing rendering code here] ...
                    
                    # (Simplified for brevity, paste your original rendering logic here)
                    # I will assume you keep the logic from your original file 
                    # starting from: if isinstance(user_info, dict): ...
                    pass 
                    
                    # Render the Expander and Forms (Pasted from your original file)
                    username = user_info.get('user', {}).get('username') or user_info.get('username') or 'User'
                    # ... (Rest of logic) ...
                    role = member.get('user_role') or member.get('role') or '-'
                    full_name = username # Simplification for example
                    expander_label = f"👤  {full_name} - {role}"
                    
                    with st.expander(label=expander_label, expanded=False):
                         # ... (Your card HTML and Forms) ...
                         st.write("Member details...") # Placeholder
            else:
                st.info(f"No members found for Batch ID: {batch_id}")
    else:
        st.warning("Please login to view members.")