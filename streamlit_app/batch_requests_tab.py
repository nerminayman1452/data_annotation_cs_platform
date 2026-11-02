import streamlit as st
import requests
import pandas as pd

def batch_requests_tab(st, BACKEND_API_BASE_URL):

    st.markdown("### 📨 Batch Access Requests")

    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    url = f"{BACKEND_API_BASE_URL}/dashboard/join-requests/"
    resp = requests.get(url, headers=headers)

    if resp.status_code != 200:
        st.error("Failed to load requests.")
        return

    requests_data = resp.json()

    if not requests_data:
        st.info("No batch access requests at the moment.")
        return

    # Convert to DataFrame for filtering
    df = pd.DataFrame(requests_data)

    # Status filter (simple)
    status_filter = st.selectbox("Filter by Status", ["All", "pending", "approved", "rejected"])

    filtered_df = df.copy()
    if status_filter != "All":
        filtered_df = filtered_df[filtered_df["status"] == status_filter]

    st.write("---")

    for _, req in filtered_df.iterrows():

        full_name = f"{req['first_name'].capitalize()} {req['last_name'].capitalize()}"
        request_time = req["created_at"].split("T")[0]

        # CARD UI
        st.markdown(
            f"""
            <div style="
                padding: 1rem;
                margin-bottom: 1rem;
                border-radius: 1rem;
                background: rgba(255,255,255,0.04);
                border: 1px solid rgba(255,255,255,0.08);
            ">
                <h4>👤 {full_name}</h4>
                <p>
                    <b>Email:</b> {req['email']}<br>
                    <b>Batch:</b> {req['batch_name']}<br>
                    <b>Requested At:</b> {request_time}<br>
                    <b>Status:</b> 
                    <span style="color:#ffd16b;font-weight:700">{req['status'].capitalize()}</span>
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        # BUTTONS
        col1, col2, col3 = st.columns([1,1,1])

        # APPROVE
        with col1:
            if st.button("✔ Approve", key=f"approve_{req['id']}"):
                approve_url = f"{BACKEND_API_BASE_URL}/dashboard/join-requests/{req['request_id']}/approve/"
                r = requests.post(approve_url, headers=headers,)
                if r.status_code in (200, 201):
                    st.success("Request approved.")
                    st.experimental_rerun()

        # REJECT
        with col2:
            if st.button("✖ Reject", key=f"reject_{req['id']}"):
                reject_url = f"{BACKEND_API_BASE_URL}/projects/batch-requests/{req['request_id']}/reject/"
                r = requests.post(reject_url, headers=headers)
                if r.status_code in (200, 201):
                    st.warning("Request rejected.")
                    st.experimental_rerun()

        # PROFILE (later)
        with col3:
            st.info("Profile (soon)")

        st.write("---")
