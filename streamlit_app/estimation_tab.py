import streamlit as st
import pandas as pd
import requests

def estimation_tab(st, BASE_URL):
    st.title("📊 Phase Planning & Estimation")

    # -----------------------------------------
    # 1. Select Batch
    # -----------------------------------------
    try:
        resp = requests.get(
            f"{BASE_URL}/project-management/batches/",
            headers={"Authorization": f"Bearer {st.session_state.token}"}
        )
        if resp.status_code != 200:
            st.error("Failed to fetch batches.")
            return
        batches = resp.json()
    except Exception as e:
        st.error(f"Error fetching batches: {e}")
        return

    # Create a map for the selectbox
    batch_map = {f"{b['id']} – {b['batch_name']}": b for b in batches}
    selected_batch_label = st.selectbox("Select Batch:", list(batch_map.keys()))

    if not selected_batch_label:
        st.info("Please select a batch to view estimation.")
        return

    selected_batch = batch_map[selected_batch_label]
    batch_id = selected_batch['id']

    # -----------------------------------------
    # 2. Fetch Estimation Data
    # -----------------------------------------
    if st.button("🔄 Refresh / Calculate Estimation", use_container_width=True):
        st.session_state.get(f"est_data_{batch_id}", None)

    try:
        resp = requests.get(
            f"{BASE_URL}/planning/batches/{batch_id}/",
            headers={"Authorization": f"Bearer {st.session_state.token}"}
        )
        if resp.status_code == 200:
            est_data = resp.json()
        else:
            st.error(f"Failed to load estimation. Status: {resp.status_code}")
            return
    except Exception as e:
        st.error(f"API Error: {e}")
        return

    # -----------------------------------------
    # 3. Process Data for Table
    # -----------------------------------------
    plans = est_data.get("plans", [])
    summary = est_data.get("summary", {})

    if not plans:
        st.warning("No plans found for this batch. Create a plan configuration first.")
        return

    # -- A. Construct Main DataFrame --
    table_rows = []
    for p in plans:
        cost_per_unit = 0
        if p.get('quantity', 0) > 0:
            cost_per_unit = p.get('total_cost', 0) / p['quantity']
        
        wp_percent = (p.get('weight', 0) * p.get('progress', 0)) / 100

        row = {
            "ID": p.get('plan_id'),
            "Task": p.get('plan_name'),
            "Start Date": p.get('start_date'),
            "End Date": p.get('end_date'),
            "Measure Units": p.get('measure_unit'),
            "Total Amount": p.get('quantity'),
            "Standard": p.get('standard'),
            "Man Days": p.get('efforts_man_days'),
            "Man Days/Worker": p.get('efforts_man_days_per_worker'),
            "Worker #": p.get('total_workforce'),
            "Duration": p.get('duration_days'),
            "Cost Per Unit": cost_per_unit, 
            "Task Cost": p.get('total_cost'),
            "Progress": p.get('progress', 0) / 100,
            "Weight": p.get('weight', 0),
            "Rates": p.get('rate'),
            "W.P%": wp_percent,
        }
        table_rows.append(row)

    df = pd.DataFrame(table_rows)

    # Convert Date Strings to Actual Datetime Objects
    df["Start Date"] = pd.to_datetime(df["Start Date"], errors='coerce')
    df["End Date"] = pd.to_datetime(df["End Date"], errors='coerce')

    # -- B. Calculate Averages for Summary --
    total_plans = len(plans) if len(plans) > 0 else 1
    
    # Calculate averages based on table data
    avg_man_days = summary.get('total_efforts_man_days', 0) / total_plans
    avg_workers = summary.get('total_workers', 0) / total_plans
    avg_duration = summary.get('total_duration_days', 0) / total_plans
    avg_cost = summary.get('total_cost', 0) / total_plans
    
    # -- C. Construct Footer Rows (Total & Average) --
    total_row = {
        "ID": "TOTAL",
        "Task": "Total",
        "Start Date": df["Start Date"].min() if not df["Start Date"].isna().all() else None,
        "End Date": df["End Date"].max() if not df["End Date"].isna().all() else None,
        "Measure Units": None,
        "Total Amount": df["Total Amount"].sum(),
        "Standard": None,
        "Man Days": summary.get('total_efforts_man_days', 0),
        "Worker #": summary.get('total_workers', 0),
        "Duration": None, # Summing duration usually doesn't mean much, max or range is better
        "Cost Per Unit": df["Cost Per Unit"].sum(),
        "Task Cost": summary.get('total_cost', 0),
        "Progress": df["Progress"].mean(), # Average progress
        "Weight": df["Weight"].sum(), 
        "Rates": df["Rates"].sum(),
        "W.P%": df["W.P%"].sum(),
    }

    average_row = {
        "ID": "AVG",
        "Task": "Average",
        "Start Date": summary.get('avg_start_date', None),
        "End Date": summary.get('avg_end_date', None),
        "Measure Units": None,
        "Total Amount": df["Total Amount"].mean(),
        "Standard": df["Standard"].mean(),
        "Man Days": avg_man_days,
        "Worker #": avg_workers,
        "Duration": avg_duration,
        "Cost Per Unit": df["Cost Per Unit"].mean(),
        "Task Cost": avg_cost,
        "Progress": df["Progress"].mean(),
        "Weight": df["Weight"].mean(),
        "Rates": df["Rates"].mean(),
        "W.P%": df["W.P%"].mean(),
    }
    
    # Append rows: DataFrame + Total + Average
    df_final = pd.concat([
        df, 
        pd.DataFrame([total_row]), 
        pd.DataFrame([average_row])
    ], ignore_index=True)

    # -----------------------------------------
    # 4. Display Enhanced Data Table
    # -----------------------------------------
    st.markdown("### 📋 Estimation Breakdown")
    
    st.data_editor(
        df_final,
        use_container_width=True,
        hide_index=True,
        disabled=True, 
        column_config={
            "Task": st.column_config.TextColumn("Task", width="medium"),
            "Start Date": st.column_config.DateColumn("Start Date", format="YYYY-MM-DD"),
            "End Date": st.column_config.DateColumn("End Date", format="YYYY-MM-DD"),
            "Total Amount": st.column_config.NumberColumn("Total Amount"),
            "Standard": st.column_config.NumberColumn("Standard"),
            "Man Days": st.column_config.NumberColumn("Man Days", format="%.2f"),
            "Worker #": st.column_config.NumberColumn("Worker #"),
            "Duration": st.column_config.NumberColumn("Duration (Days)"),
            "Cost Per Unit": st.column_config.NumberColumn("Cost / Unit", format="$%.4f"),
            "Task Cost": st.column_config.NumberColumn("Task Cost", format="$%.2f"),
            "Progress": st.column_config.ProgressColumn(
                "Progress", 
                format="%.0f%%", 
                min_value=0, 
                max_value=1
            ),
            "Weight": st.column_config.NumberColumn("Weight", format="%.2f"),
            "Rates": st.column_config.NumberColumn("Rates (Daily)", format="%.2f"),
            "W.P%": st.column_config.NumberColumn("W.P%", format="%.2f%%"),
        }
    )

    # -----------------------------------------
    # 5. Approval & Status Flow
    # -----------------------------------------
    st.divider()
    
    col_status, col_actions = st.columns([2, 1])

    is_approved = est_data.get("is_approved", False)

    with col_status:
        st.subheader("Status")
        if is_approved:
            st.success("✅ **APPROVED**: This plan is frozen and ready for production.")
        # elif is_estimated:
        #     st.info("⚠️ **ESTIMATED**: Review the costs above before approving.")
        else:
            st.warning("📝 **DRAFT**: Plan is currently in draft mode.")

    with col_actions:
        st.subheader("Actions")
        if not is_approved:
            if st.button("✅ Approve & Pay", type="primary", use_container_width=True):
                try:
                    approve_resp = requests.post(
                        f"{BASE_URL}/project-management/batches/{batch_id}/approve_plan/",
                        headers={"Authorization": f"Bearer {st.session_state.token}"}
                    )
                    if approve_resp.status_code == 200:
                        st.success("Plan approved successfully!")
                        st.rerun()
                    else:
                        st.error(f"Approval failed: {approve_resp.text}")
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
             st.button("🔒 Plan Locked", disabled=True, use_container_width=True)