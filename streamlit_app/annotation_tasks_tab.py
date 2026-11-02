import streamlit as st
import requests

def annotation_tasks_tab(st, base_url):
    # Only show title if not already shown by app.py (optional check)
    if "batch_id" not in st.query_params:
        st.title("📝 Your Annotation Dashboard")

    if not st.session_state.get("token"):
        st.warning("Please login to view tasks.")
        return

    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    resp = requests.get(f"{base_url}/dashboard/my-active-batches-plans-group/", headers=headers)

    if resp.status_code != 200:
        st.error("Failed to fetch your annotation plans.")
        return

    data = resp.json()
    batches = data.get("batches", [])

    if not batches:
        st.info("You have no active batches or annotation plans assigned.")
        return

    # Check if we are filtering by a specific batch (from Case B in app.py)
    current_batch_filter = st.query_params.get("batch_id")

    for batch in batches:
        # If we are in "Single Batch View", skip other batches
        if current_batch_filter and str(batch.get("id")) != str(current_batch_filter):
            continue

        batch_name = batch.get("batch_name")
        status = batch.get("status", "unknown").capitalize()
        members_count = batch.get("members_count", 0)
        access_status = batch.get("access_status", "unknown").capitalize()
        
        # Only show the Big Batch Header if we are NOT filtering (or you can keep it)
        if not current_batch_filter:
            st.markdown(
                f"""
                <div style="
                    background: linear-gradient(135deg, #4e54c8, #8f94fb);
                    padding: 20px;
                    border-radius: 15px;
                    box-shadow: 2px 2px 15px rgba(0,0,0,0.2);
                    color: #fff;
                    margin-bottom: 20px;
                ">
                    <h2 style="margin-bottom:5px;">🗂 {batch_name} | <span style='color:#ffe066'>{status}</span></h2>
                    <p style="margin:0;">👥 Members: {members_count} | Access: {access_status}</p>
                </div>
                """, unsafe_allow_html=True
            )

        plans = batch.get("plans", [])
        if not plans:
            st.info(f"No plans in {batch_name} yet.")
            continue

        for plan in plans:
            plan_name = plan.get("plan_name")
            plan_type = plan.get("type")
            completed = plan.get("my_completed_count", 0)
            total = plan.get("tasks_count", 1)
            percent = int((completed / total) * 100) if total else 0
            
            bar_color = "#2ECC71" if percent >= 70 else "#F7B731" if percent >= 30 else "#FF4B4B"
            xp = completed * 10
            streak = completed % 10

            st.markdown(
                f"""
                <div style="
                    border-radius: 15px;
                    padding: 20px;
                    margin-bottom: 20px;
                    background: linear-gradient(135deg, #1f1c2c, #928dab);
                    color: #fff;
                    box-shadow: 2px 2px 10px rgba(0,0,0,0.3);
                ">
                    <h3 style="margin-bottom:10px;">📌 {plan_name} ({plan_type})</h3>
                    <div style='width: 100%; background-color: #333; border-radius: 10px; height: 20px; margin-bottom: 10px;'>
                        <div style='width: {percent}%; height: 20px; background-color: {bar_color}; border-radius: 10px; text-align: right; padding-right:5px; color:#fff; font-weight:bold;'>
                            {percent}%
                        </div>
                    </div>
                    <p style="margin:0;">Progress: {completed}/{total}</p>
                    <p style="margin:0;">🎯 XP: +{xp} | 🔥 Streak: {streak} tasks</p>
                </div>
                """, unsafe_allow_html=True
            )

            button_label = "Start Tasks" if completed == 0 else "Continue"
            
            # --- FIX: BUTTON SETS PLAN_ID ---
            if st.button(button_label, key=f"plan_{plan.get('id')}"):
                # We need BOTH batch_id and plan_id to render the page
                st.query_params["batch_id"] = str(batch.get("id"))
                st.query_params["plan_id"] = str(plan.get("id"))
                st.rerun()