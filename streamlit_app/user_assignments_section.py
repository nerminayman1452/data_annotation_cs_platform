import streamlit as st


def render_user_card(user):
    name = user["name"]
    role = user["role"]
    completed = user["total_completed"]
    assigned = user["total_assigned"]
    percent = user["progress_percent"]

    # Card UI
    card = st.container(border=True)
    with card:
        st.markdown(f"### {name} 🎯")
        st.caption(f"**Role:** {role}")

        # Progress bar + percent
        col1, col2 = st.columns([5, 1])
        with col1:
            st.progress(percent / 100)
        with col2:
            st.markdown(f"**{percent:.0f}%**")

        st.markdown(f"📌 **{completed} / {assigned} tasks completed**")


def render_assigned_users_section(annotators, reviewers):
    st.markdown("## 👥 Assignment Overview")
    st.markdown("---")

    # =========================
    # Annotators Section
    # =========================
    st.subheader(f"🧑‍💻 Annotators Assigned ({len(annotators)})")

    if not annotators:
        st.info("No annotators assigned yet.")
    else:
        for ann in annotators:
            render_user_card(ann)

    st.markdown("---")

    # =========================
    # Reviewers Section
    # =========================
    st.subheader(f"📝 Reviewers Assigned ({len(reviewers)})")

    if not reviewers:
        st.info("No reviewers assigned yet.")
    else:
        for rev in reviewers:
            render_user_card(rev)

    st.markdown("---")
