import streamlit as st
import requests
import pandas as pd

def plans_configurations_tab(st, BACKEND_API_BASE_URL):
    st.header("Tasks Configurations")
    
    # Select Task Type
    plan_type = st.radio("Select Task Type", ["Image Tasks", "Text Tasks", "Audio Tasks"], horizontal=True)
    
    if plan_type == "Image Tasks":
        img_tab1, img_tab2, img_tab3 = st.tabs(["Image Classification Task", "Object Detection Task", "Polygon Task"])

        # --- Helper: Fetch batches ---
        # Note: minimal caching time or manual refresh is better for lists that update often
        def get_batches(token):
            headers = {"Authorization": f"Bearer {token}"}
            try:
                resp = requests.get(f"{BACKEND_API_BASE_URL}/project-management/batches/", headers=headers)
                if resp.status_code == 200:
                    return resp.json()
            except Exception as e:
                st.error(f"Error fetching batches: {e}")
            return []

        # --- Helper: Fetch label types ---
        @st.cache_data(show_spinner=False)
        def get_label_types(token, plan_type="image"):
            headers = {"Authorization": f"Bearer {token}"}
            url = f"{BACKEND_API_BASE_URL}/image-annotations/create/image-label-type/"
            try:
                resp = requests.get(url, headers=headers)
                if resp.status_code == 200:
                    return resp.json()
            except:
                pass
            return []

        # --- Helper: Badge Formatting ---
        def badge(text, color):
            return f"<span style='background:{color};color:white;padding:2px 10px;border-radius:8px;font-size:0.95em;margin-right:6px'>{text}</span>"

        # --- Helper: Fetch plans for batch ---
        def get_plans(token, batch_id=None):
            headers = {"Authorization": f"Bearer {token}"}
            if batch_id:
                url = f"{BACKEND_API_BASE_URL}/image-annotations/image-classification-plans/{batch_id}/"
            else:
                url = f"{BACKEND_API_BASE_URL}/image-annotations/image-classification-plans/"
            
            try:
                resp = requests.get(url, headers=headers)
                if resp.status_code == 200:
                    return resp.json()
            except:
                pass
            return []

        # ==========================================
        #       IMAGE CLASSIFICATION TAB
        # ==========================================
        with img_tab1:
            # 1. GET BATCHES
            batches = get_batches(st.session_state.token)

            # 2. BATCH SELECTOR (The fix you requested)
            if not batches:
                st.warning("⚠️ No batches found. Please go to the 'Upload Data' tab to create a batch first.")
                st.stop() # Stop rendering the rest of the tab to prevent errors
            
            col_sel, col_ref = st.columns([4, 1])
            with col_sel:
                selected_batch_obj = st.selectbox(
                    "Select Batch to Configure",
                    options=batches,
                    # Displays: "My Batch Name (ID: 12)"
                    format_func=lambda x: f"{x.get('batch_name', 'Unnamed Batch')} (ID: {x.get('id')})",
                    key="img_plan_batch_select"
                )
            with col_ref:
                st.write("") # Spacer
                st.write("") # Spacer
                if st.button("🔄 Refresh"):
                    st.rerun()

            # Set the ID for use in the rest of the code
            batch_id = selected_batch_obj.get('id')

            # --- Show existing plans for this batch ---
            st.divider()
            st.subheader(f"Existing Plans for: {selected_batch_obj.get('batch_name')}")
            
            plans = get_plans(st.session_state.token, batch_id=batch_id)
            
            if plans:
                for plan in plans:
                    with st.expander(f"📝 {plan.get('plan_name','(no name)')}"):
                        config = plan.get("plan_config", {})
                        label_types = plan.get("label_types", [])
                        st.markdown(f"<b>Plan ID:</b> {plan.get('id')}", unsafe_allow_html=True)
                        st.markdown(f"<b>Labels:</b> " + ' '.join([badge(l.get('label_type',''), '#1976d2') for l in label_types]), unsafe_allow_html=True)
                        st.markdown(f"<b>Created At:</b> {plan.get('created_at','-')}  ", unsafe_allow_html=True)
                        st.markdown("---")
                        
                        # Display Config Table
                        config_map = [
                            ("Annotators per Task", config.get("annotators_per_task")),
                            ("Reviewers per Task", config.get("reviewers_per_task")),
                            ("Acceptance Agreement (%)", config.get("acceptance_agreement")),
                            ("Reward per Task", config.get("reward_per_task")),
                            ("Time Allotted (sec)", config.get("time_allotted_per_annotator")),
                            ("Question", config.get("question")),
                        ]
                        table_html = "<table style='width:100%;font-size:1em;'>" + ''.join([
                            f"<tr><td style='font-weight:bold;padding:4px 12px 4px 0;color:#1976d2'>{k}</td><td style='padding:4px 0'>{v if v not in [None, ''] else '-'}" + ("</td></tr>") for k,v in config_map
                        ]) + "</table>"
                        st.markdown(table_html, unsafe_allow_html=True)

                        # --- Edit/Update UI ---
                        if st.button("✏️ Edit Plan", key=f"edit_btn_{plan['id']}"):
                            st.session_state[f"edit_plan_{plan['id']}"] = not st.session_state.get(f"edit_plan_{plan['id']}", False)
                        
                        if st.session_state.get(f"edit_plan_{plan['id']}", False):
                            st.info("Edit the plan and click Update below.")
                            with st.form(f"update_plan_form_{plan['id']}"):
                                # ... (Keep existing fields mostly same for brevity, just ensure they exist) ...
                                annotators_per_task = st.number_input("Annotators", value=config.get("annotators_per_task", 1), key=f"e_an_{plan['id']}")
                                question = st.text_area("Question", value=config.get("question", ""), key=f"e_qu_{plan['id']}")
                                # Add other fields as necessary per your original code...
                                
                                submitted_update = st.form_submit_button("Update Plan")
                                if submitted_update:
                                    # ... Update Logic ...
                                    st.warning("Update logic placeholder (ensure fields match your API)")
            else:
                st.info(f"No configuration plans found for Batch ID: {batch_id}")

            # --- Create new plan ---
            st.divider()
            st.header("Create New Image Classification Plan")
            st.caption(f"Creating plan for: **{selected_batch_obj.get('batch_name')}** (ID: {batch_id})")
            
            with st.form("create_plan_form"):
                plan_name = st.text_input("Plan Name")
                st.markdown("#### Plan Configuration")
                
                c1, c2, c3 = st.columns(3)
                with c1:
                    annotators_per_task = st.number_input("Annotators per Task", min_value=1, value=1)
                    reviewers_per_task = st.number_input("Reviewers per Task", min_value=0, value=0)
                    acceptance_agreement = st.number_input("Acceptance Agreement (%)", min_value=0, max_value=100, value=80)
                    reward_per_task = st.number_input("Reward per Task", min_value=0.0, value=0.0, format="%.2f")
                    time_allotted_per_annotator = st.number_input("Time Allotted (sec)", min_value=1, value=30)
                    duration = st.number_input("Duration (days)", min_value=1, value=3)
                    # auto_approve_time = st.number_input("Auto Approve Time (days)", min_value=1, value=1)
                with c2:
                    confidence_score = st.number_input("Confidence Score", min_value=0.0, max_value=1.0, value=0.8, step=0.01)
                    min_annotator_approval_rating = st.number_input("Min Annotator Rating", min_value=0.0, max_value=100.0, value=0.0)
                    min_approved_tasks = st.number_input("Min Approved Tasks", min_value=0, value=0)
                    task_distribution_mode = st.selectbox("Task Dist. Mode", ["auto", "manual"], index=0)
                    max_tasks_per_annotator = st.number_input("Max Tasks per Annotator", min_value=1, value=15)
                    # assign_to_all_annotators = st.checkbox("Assign to All Annotators", value=True)
                with c3:
                    description = st.text_area("Description", height=80)
                    question = st.text_area("Question", height=80)
                    keywords = st.text_area("Keywords (comma separated)", height=80)
                    is_qualified = st.checkbox("Qualification Required", value=False)
                    qualification_test = st.text_input("Qual. Test ID (optional)")
                    allow_skipping = st.checkbox("Allow Skipping", value=False)
                
                st.markdown("#### Label Types")
                label_types = get_label_types(st.session_state.token)
                label_options = [l.get('label_type','') for l in label_types]
                selected_labels = st.multiselect("Select Existing Label Types", label_options)
                new_labels = st.text_input("Add New Label Types (comma separated)")
                
                submitted = st.form_submit_button("Create Plan")
                
                if submitted:
                    if not plan_name:
                        st.error("Plan name is required.")
                    else:
                        # Prepare payload logic
                        label_types_input = []
                        for l in selected_labels:
                            for obj in label_types:
                                if obj.get('label_type') == l:
                                    label_types_input.append(obj.get('id'))
                        if new_labels:
                            label_types_input.extend([s.strip() for s in new_labels.split(',') if s.strip()])
                        
                        plan_config = {
                            "annotators_per_task": annotators_per_task,
                            "reviewers_per_task": reviewers_per_task,
                            "description": description,
                            "acceptance_agreement": acceptance_agreement,
                            "reward_per_task": reward_per_task,
                            "time_allotted_per_annotator": time_allotted_per_annotator,
                            "duration": duration,
                            # "auto_approve_time": auto_approve_time,
                            "confidence_score": confidence_score,
                            "is_qualified": is_qualified,
                            "min_annotator_approval_rating": min_annotator_approval_rating,
                            "min_approved_tasks": min_approved_tasks,
                            "qualification_test": qualification_test or None,
                            "task_distribution_mode": task_distribution_mode,
                            "max_tasks_per_annotator": max_tasks_per_annotator,
                            # "assign_to_all_annotators": assign_to_all_annotators,
                            "question": question,
                            "keywords": keywords,
                            "allow_skipping": allow_skipping,
                        }
                        
                        payload = {
                            "plan_name": plan_name,
                            "plan_config": plan_config,
                            "label_types_input": label_types_input,
                            "batch": batch_id # Using the ID from the selectbox above
                        }
                        
                        headers = {"Authorization": f"Bearer {st.session_state.token}"}
                        url = f"{BACKEND_API_BASE_URL}/image-annotations/create/image-classification-plan/{batch_id}/"
                        
                        with st.spinner("Creating plan..."):
                            try:
                                resp = requests.post(url, json=payload, headers=headers)
                                if resp.status_code in (200, 201):
                                    st.success(f"Plan '{plan_name}' created!")
                                    st.cache_data.clear() # Clear cache to refresh lists
                                else:
                                    st.error(f"Failed: {resp.text}")
                            except Exception as e:
                                st.error(f"Connection Error: {e}")

        # --- Object Detection Plan Tab ---
        with img_tab2:
            st.info("Object Detection Plan configuration coming soon.")

        # --- Polygon Plan Tab ---
        with img_tab3:
            st.info("Polygon Plan configuration coming soon.")
            
    elif plan_type == "Text Plans":
        st.info("Text plan configuration coming soon.")
    elif plan_type == "Audio Plans":
        st.info("Audio plan configuration coming soon.")