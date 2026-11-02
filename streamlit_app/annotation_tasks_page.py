import streamlit as st
import requests

def annotation_tasks_page(st, base_url, params):
    plan_id = params["plan_id"]
    batch_id = params["batch_id"]

    st.title("📝 Annotation Task")

    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    url = f"{base_url}/image-annotations/image-classification-tasks/{plan_id}/next/"

    resp = requests.get(url, headers=headers)

    # 1. Handle No Content / Errors
    if resp.status_code == 204:
        st.info("🎉 No more tasks available! You have completed your queue.")
        if st.button("⬅ Back to Plan List"):
            st.query_params.clear()
            st.query_params["batch_id"] = batch_id
            st.rerun()
        return

    if resp.status_code != 200:
        st.error("Could not load tasks (or no tasks remaining).")
        if st.button("⬅ Back to Plan List"):
            st.query_params.clear()
            st.query_params["batch_id"] = batch_id
            st.rerun()
        return

    task_data = resp.json()
    annotation_id = task_data["annotation_id"]
    task = task_data["task"]

    all_annotators = task.get("annotators", [])
    current_username = st.session_state.get("username", "")
    print("Current Username:", current_username)

    # Find the annotator dict that matches the current logged-in username
    # We use next() to find the first match, or return a default dict if not found
    annotator_info = next(
        (a for a in all_annotators if a["email"] == current_username), 
        None
    )

    # Fallback if name doesn't match or list is empty
    if not annotator_info:
        # If we can't match by name, and there's only 1 annotator in the list, use that one.
        if len(all_annotators) == 1:
            annotator_info = all_annotators[0]
        else:
            # Default values to prevent crashing
            annotator_info = {
                "total_completed": 0, 
                "total_assigned": 1, 
                "name": "Unknown"
            }
    
    # Calculate percentages safely (in case it's missing from JSON)
    total_assigned = annotator_info.get('total_assigned', 1)
    total_completed = annotator_info.get('total_completed', 0)
    
    # Avoid DivisionByZero
    if total_assigned > 0:
        progress_val = int((total_completed / total_assigned) * 100)
    else:
        progress_val = 0
    # --- FIX END ---

    # -------------------------
    # Header bar with progress & gamification
    # -------------------------
    st.markdown(
        f"""
        **Plan:** {task['plan_name']}  |  **Batch:** {task['batch_name']}  
        **Progress:** {annotator_info['total_completed']} / {annotator_info['total_assigned']}  
        **XP:** +{int(annotator_info['total_completed']*10)}
        """
    )
    # Ensure progress doesn't exceed 100
    # prog_val = min(int(annotator_info['progress_percent']), 100)
    st.progress(min(progress_val, 100))

    st.markdown("---")

    # -------------------------
    # Main Annotation Area
    # -------------------------
    if task.get("image_url"):
        # Centered + Smaller Image Display
        st.markdown("<h4 style='text-align:center;'>Image Preview</h4>", unsafe_allow_html=True)

        st.markdown(
            """
            <div style='display:flex; justify-content:center;'>
            """,
            unsafe_allow_html=True
        )

        st.image(task["image_url"], width=350)  # 👈 adjust size (250–400 recommended)

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("")

    # -------------------------
    # Label selection
    # -------------------------
    st.subheader("Choose a Label for this Task")
    label_options = task.get("label_choices", [])

    col_count = len(label_options) if len(label_options) > 0 else 1
    cols = st.columns(col_count)

    selected_label = st.session_state.get(f"selected_label_{annotation_id}", None)

    for i, label in enumerate(label_options):
        with cols[i]:
            if st.button(label["label_type"], key=f"label_{annotation_id}_{label['id']}"):
                st.session_state[f"selected_label_{annotation_id}"] = label["id"]
                selected_label = label["id"]
                st.success(f"Selected: {label['label_type']}")

    st.markdown("OR")

    # Optional custom label
    custom_label = st.text_input("Or enter a custom label", value="", key=f"custom_label_{annotation_id}")

    # -------------------------
    # Gamification Sidebar
    # -------------------------
    st.sidebar.subheader("🎮 Gamification")
    st.sidebar.write("🎯 +10 XP per completed task")
    st.sidebar.write("🏆 Complete 100 tasks → Earn 50 DatCoins")
    st.sidebar.write("🔥 Task streak bonus!")
    st.sidebar.write(f"Current streak: {annotator_info['total_completed']} tasks")

    # -------------------------
    # Submission
    # -------------------------
    with st.form(f"annotation_form_{annotation_id}"):
        submitted = st.form_submit_button("Submit & Next →")

        if submitted:
            payload = {}
            if selected_label and not custom_label:
                payload["label_type_result"] = selected_label
            elif custom_label and not selected_label:
                payload["custom_label"] = custom_label
            elif selected_label and custom_label:
                st.error("Please select either a predefined label or enter a custom label, not both.")
                st.stop()
            else:
                st.error("You must select a label or enter a custom label.")
                st.stop()

            submit_resp = requests.post(
                f"{base_url}/image-annotations/image-annotations-tasks/submit/{annotation_id}/",
                headers=headers,
                json=payload,
            )
            if submit_resp.status_code == 200:
                st.success("✅ Task submitted!")
                st.balloons()  # celebration
                
                # --- FIX START ---
                st.rerun()  # UPDATED: experimental_rerun() -> rerun()
                # --- FIX END ---
                
            else:
                st.error("❌ Failed to submit task.")

    st.markdown("---")
    if st.button("⬅ Back to Batch"):
        st.query_params.clear()
        st.query_params["batch_id"] = batch_id
        st.rerun() # Added rerun here for smoother navigation