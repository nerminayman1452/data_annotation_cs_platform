import streamlit as st
import requests
import pandas as pd

def organizations_tab(st, BACKEND_API_BASE_URL):
    st.subheader("Organizations")
    if st.session_state.token:
        headers = {"Authorization": f"Bearer {st.session_state.token}"}

        @st.cache_data(show_spinner=False)
        def get_organizations(token):
            headers = {"Authorization": f"Bearer {token}"}
            resp = requests.get(f"{BACKEND_API_BASE_URL}/project-management/organization-details/", headers=headers)
            if resp.status_code == 200:
                return resp.json()
            return []

        # Search/filter UI
        search_org = st.text_input("🔍 Search organizations by name or email", "")
        with st.spinner("Loading organizations..."):
            orgs = get_organizations(st.session_state.token)

        # Filter organizations
        if search_org:
            orgs = [o for o in orgs if search_org.lower() in (o.get('name','')+o.get('contact_email','')).lower()]

        if orgs:
            org_df = pd.DataFrame(orgs)[["id","name","contact_email"]]
            org_df.columns = ["ID","Name","Contact Email"]
            st.dataframe(org_df, width='stretch', hide_index=True)
        else:
            st.info("No organization found. Please create one.")

    st.write("---")
    st.header("Create Organization")
    with st.form("create_org_form"):
        org_name = st.text_input("Organization Name")
        org_email = st.text_input("Contact Email")
        submitted = st.form_submit_button("Create Organization")
        if submitted:
            if not st.session_state.token:
                st.error("You must be logged in.")
            elif not org_name or not org_email:
                st.error("Name and email are required.")
            else:
                headers = {"Authorization": f"Bearer {st.session_state.token}"}
                payload = {"name": org_name, "contact_email": org_email}
                with st.spinner("Creating organization..."):
                    resp = requests.post(f"{BACKEND_API_BASE_URL}/project-management/create-organization/", headers=headers, json=payload)
                if resp.status_code in (200, 201):
                    st.success("Organization created successfully!")
                else:
                    st.error(f"Failed to create organization: {resp.text}")
