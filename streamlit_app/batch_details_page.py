import streamlit as st
import requests
from datetime import datetime

def batch_details_page(st, base_url, batch_id):
    st.title("📦 Batch Details")

    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    url = f"{base_url}/dashboard/batches-group/{batch_id}/"
    resp = requests.get(url, headers=headers)

    if resp.status_code != 200:
        st.error("Failed to load batch details.")
        if st.button("⬅ Back to Dashboard"):
            st.query_params.clear()
        return

    data = resp.json()

    # Extract main batch info
    batch_name = data.get("batch_name")
    status = data.get("status")
    members_count = data.get("members_count", 0)
    access_status = data.get("access_status")
    plans = data.get("plans", [])

    # ===============================
    # 🔵 Batch Summary Header
    # ===============================
    st.subheader(f"📦 Batch: **{batch_name}**")
    st.write(f"🔖 **Status:** `{status}`")
    st.write(f"👥 **Members Assigned:** {members_count}")
    st.write(f"🔐 **Access:** {access_status}")

    st.markdown("---")
    st.subheader("🧠 Available Plans")

    if not plans:
        st.info("No plans found for this batch.")
        return

    # ===============================
    # 🔵 Plan Cards UI
    # ===============================
    for p in plans:

        completed = p.get("my_completed_count", 0)
        approved = p.get("my_approved_count", 0)
        rejected = p.get("my_rejected_count", 0)
        submitted = p.get("total_submitted_count", 0)
        total = p.get("tasks_count", 0)

        # Avoid ZeroDivisionError
        if total > 0:
            percent = int((completed / total) * 100)
        else:
            percent = 0

        # Gamified colors based on progress
        if percent < 30:
            bar_color = "#FF4B4B"  # red
        elif percent < 70:
            bar_color = "#F7B731"  # yellow
        else:
            bar_color = "#2ECC71"  # green

        with st.container(border=True):

            # ---------- Header ----------
            st.write(f"### 🎯 {p['plan_name']}")
            st.markdown(f"**📌 Type:** `{p['type']}`")

            # ---------- Progress Bar ----------
            st.write(f"🔥 **Progress: {percent}%**")

            # Custom HTML progress bar (more beautiful)
            st.markdown(
                f"""
                <div style='width: 100%; background-color: #eee; border-radius: 10px; height: 15px;'>
                    <div style='width: {percent}%; height: 15px; background-color: {bar_color}; border-radius: 10px;'></div>
                </div>
                """,
                unsafe_allow_html=True
            )

            st.markdown("")

            # ---------- Stats Chips ----------
            st.write("#### 📊 Your Stats")

            col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 2])

            with col1:
                st.markdown(f"**📋 Total Tasks**")
                st.write(p["tasks_count"])

            with col2:
                st.markdown(f"**🧑‍💻 Completed**")
                st.write(f"{completed}/{total}")

            with col3:
                st.markdown(f"**✅ Approved**")
                st.write(approved)

            with col4:
                st.markdown(f"**❌ Rejected**")
                st.write(rejected)

            with col5:
                st.markdown(f"**📮 Submitted**")
                st.write(submitted)

            # Days Remaining chip
            st.markdown("")
            st.markdown(f"⏳ **Days Remaining:** `{p['days_remaining']}`")

            st.markdown("---")

            # ---------- Gamified Achievements ----------
            achievements = []
            if approved > 0:
                achievements.append("🏅 *Great job! You already have approved tasks.*")

            if percent >= 50:
                achievements.append("💪 *You're halfway there!*")

            if percent == 100:
                achievements.append("🌟 **Amazing! You finished all tasks.**")

            if rejected == 0 and completed > 0:
                achievements.append("✨ *Perfect accuracy so far!*")

            if achievements:
                with st.expander("🏆 Your Achievements"):
                    for a in achievements:
                        st.write(a)

            # ---------- Action Button ----------
            label = "Start Tasks" if completed == 0 else "Continue Annotating"

            if st.button(label, key=f"plan_{p['id']}"):
                st.query_params.clear()
                st.query_params["batch_id"] = batch_id
                st.query_params["plan_id"] = str(p["id"])

            st.markdown("")

    st.markdown("---")

    # Back button
    if st.button("⬅ Back to Dashboard"):
        st.query_params.clear()
