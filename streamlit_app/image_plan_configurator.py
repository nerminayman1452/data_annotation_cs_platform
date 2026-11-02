import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Image Annotation Plan Configurator", layout="wide")

BACKEND_API_BASE_URL = "http://localhost:8003"

st.title("🖼️ Image Annotation Plan Configurator")

# --- Auth (assume token in session) ---
if "token" not in st.session_state:
    st.warning("Please login from the main app first.")
    st.stop()
headers = {"Authorization": f"Bearer {st.session_state.token}"}

# --- Helper: Fetch batches for dropdown ---
@st.cache_data(show_spinner=False)
def get_batches(token):
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{BACKEND_API_BASE_URL}/project-management/batches/", headers=headers)
    if resp.status_code == 200:
        return resp.json()
    return []

batches = get_batches(st.session_state.token)
batch_options = [f"{b.get('batch_name','Batch')} - ID: {b.get('id')}" for b in batches]
batch_id_map = {f"{b.get('batch_name','Batch')} - ID: {b.get('id')}": b.get('id') for b in batches}

batch_label = st.selectbox("Select Batch", batch_options) if batch_options else st.text_input("Batch ID")
batch_id = batch_id_map.get(batch_label, batch_label)

# --- Helper: Fetch plans for batch ---
@st.cache_data(show_spinner=False)
def get_plans(token, batch_id):
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{BACKEND_API_BASE_URL}/image-annotation/image-classification-plans/{batch_id}/"
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        return resp.json()
    return []

# --- Helper: Fetch label types ---
@st.cache_data(show_spinner=False)
def get_label_types(token):
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{BACKEND_API_BASE_URL}/image-annotation/create/image-label-type/"
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        return resp.json()
    return []

# --- Show existing plans ---
if batch_id:
    st.subheader("Existing Image Classification Plans")
    plans = get_plans(st.session_state.token, batch_id)
    if plans:
        for plan in plans:
            with st.expander(f"Plan: {plan.get('plan_name','(no name)')}"):
                plan_table = pd.DataFrame([
                    ["Plan Name", plan.get("plan_name")],
                    ["Plan ID", plan.get("id")],
                    ["Config", str(plan.get("plan_config"))],
                    ["Labels", ', '.join([l.get('label_type','') for l in plan.get('label_types',[])])],
                    ["Created At", plan.get("created_at")],
                    ["Updated At", plan.get("updated_at")],
                ], columns=["Field", "Value"])
                st.table(plan_table)
    else:
        st.info("No plans found for this batch.")

# --- Create new plan ---
st.write("---")
st.header("Create New Image Classification Plan")

with st.form("create_plan_form"):
    plan_name = st.text_input("Plan Name")
    # Config fields (example: can be extended)
    config_col1, config_col2 = st.columns(2)
    with config_col1:
        allow_multi = st.checkbox("Allow Multiple Labels", value=False)
    with config_col2:
        time_limit = st.number_input("Time Limit (seconds)", min_value=0, value=60)
    # Label types
    label_types = get_label_types(st.session_state.token)
    label_options = [l.get('label_type','') for l in label_types]
    selected_labels = st.multiselect("Select Existing Label Types", label_options)
    new_labels = st.text_input("Add New Label Types (comma separated)")
    submitted = st.form_submit_button("Create Plan")
    if submitted:
        if not plan_name:
            st.error("Plan name is required.")
        else:
            # Prepare payload
            label_types_input = []
            for l in selected_labels:
                for obj in label_types:
                    if obj.get('label_type') == l:
                        label_types_input.append(obj.get('id'))
            if new_labels:
                label_types_input.extend([s.strip() for s in new_labels.split(',') if s.strip()])
            payload = {
                "plan_name": plan_name,
                "plan_config": {"allow_multi": allow_multi, "time_limit": time_limit},
                "label_types_input": label_types_input
            }
            url = f"{BACKEND_API_BASE_URL}/image-annotation/create/image-classification-plan/{batch_id}/"
            with st.spinner("Creating plan..."):
                resp = requests.post(url, json=payload, headers=headers)
            if resp.status_code in (200, 201):
                st.success(f"Plan '{plan_name}' created!")
                st.cache_data.clear()
            else:
                st.error(f"Failed: {resp.text}")
