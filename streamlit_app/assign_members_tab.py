import streamlit as st
import requests

def assign_members_tab(st, AUTH_API_BASE_URL, BACKEND_API_BASE_URL, batch_options, batch_id_map):
    st.header("Assign Members")
    # Fetch active users from auth gateway with short cache (per session)
    import time
    active_user_options = []
    active_user_id_map = {}
    cache_key = "active_users_cache"
    cache_time_key = "active_users_cache_time"
    cache_ttl = 300  # 5 minutes
    now = time.time()
    if st.session_state.token:
        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        refresh_users = st.button("\U0001F504 Refresh Active Users", key="refresh_active_users", help="Reload active users from backend")
        # Use cache if not expired and not forced refresh
        if (
            cache_key in st.session_state
            and cache_time_key in st.session_state
            and now - st.session_state[cache_time_key] < cache_ttl
            and not refresh_users
        ):
            users = st.session_state[cache_key]
        else:
            try:
                users_resp = requests.get(f"{AUTH_API_BASE_URL}/auth/active-users/", headers=headers)
                if users_resp.status_code == 200:
                    users = users_resp.json()
                    st.session_state[cache_key] = users
                    st.session_state[cache_time_key] = now
                else:
                    users = []
            except Exception as e:
                st.warning(f"Could not fetch active users: {e}")
                users = []
        if isinstance(users, list):
            for user in users:
                label = f"{user.get('first_name', 'User')} {user.get('last_name', '')} - ID: {user.get('id')}"
                active_user_options.append(label)
                active_user_id_map[label] = user.get('id')

    with st.form("assign_members_form"):
        batch_label = st.selectbox("Select Batch", batch_options) if batch_options else st.text_input("Batch ID")
        batch_id = batch_id_map.get(batch_label, batch_label)
        selected_users = st.multiselect("Select Active Users to Assign", active_user_options)
        user_role = st.selectbox("User Role", ["Annotator", "Reviewer"])
        submitted = st.form_submit_button("Assign Members")
        if submitted:
            if not st.session_state.token:
                st.error("You must be logged in.")
            else:
                headers = {"Authorization": f"Bearer {st.session_state.token}"}
                # Batch assign if multiple users selected
                if len(selected_users) > 1:
                    profiles = [active_user_id_map.get(user_label, user_label) for user_label in selected_users]
                    payload = {"profile": profiles, "user_role": user_role}
                    with st.spinner(f"Assigning {len(profiles)} members to batch..."):
                        resp = requests.post(f"{BACKEND_API_BASE_URL}/project-management/batches/{batch_id}/members/", headers=headers, json=payload)
                    if resp.status_code in (200, 201):
                        st.success(f"Assigned {len(profiles)} members as {user_role}.")
                    else:
                        st.error(f"Failed to assign members: {resp.text}")
                elif selected_users:
                    user_label = selected_users[0]
                    profile = active_user_id_map.get(user_label, user_label)
                    payload = {"profile": profile, "user_role": user_role}
                    with st.spinner(f"Assigning {user_label} to batch..."):
                        resp = requests.post(f"{BACKEND_API_BASE_URL}/project-management/batches/{batch_id}/members/", headers=headers, json=payload)
                    if resp.status_code in (200, 201):
                        st.success(f"Assigned {user_label} as {user_role}.")
                    else:
                        st.error(f"Failed to assign {user_label}: {resp.text}")
                else:
                    st.warning("No users selected.")
