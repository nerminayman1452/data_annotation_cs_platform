import math
import streamlit as st
import requests
import os

def get_batches_list(backend_url, headers, project_id=None):
    """Helper to fetch batches from the backend"""
    try:
        # Construct URL - Assuming standard endpoint, filtering by project if ID exists
        url = f"{backend_url}/project-management/batches/"
        if project_id:
            url += f"?project={project_id}"
            
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            # Handle pagination if API returns {results: [...]}
            if isinstance(data, dict) and "results" in data:
                return data["results"]
            elif isinstance(data, list):
                return data
        return []
    except Exception:
        return []

def upload_batch_data_tab(st, BACKEND_API_BASE_URL):
    st.header("Upload Batch Data")
    st.markdown("""
        <style>
        .upload-card {
            background: linear-gradient(90deg, #232526 0%, #414345 100%);
            border-radius: 12px;
            padding: 1.2em 1.1em 1.1em 1.1em;
            margin-bottom: 1.2em;
            color: #fff;
        }
        </style>
    """, unsafe_allow_html=True)

    if not st.session_state.token:
        st.warning("You must be logged in to upload batch data.")
        return

    headers = {"Authorization": f"Bearer {st.session_state.token}"}

    # --- 1. FETCH & SELECT BATCH (Global for this page) ---
    
    # Check if a project is active in session state
    active_project = st.session_state.get("active_project_id")
    
    with st.spinner("Loading your batches..."):
        batches = get_batches_list(BACKEND_API_BASE_URL, headers, active_project)

    if not batches:
        if active_project:
            st.warning(f"No batches found for the active project. Please create a batch first in the 'Planning' phase.")
        else:
            st.warning("No batches found. Please create a batch first.")
        return

    # Create a mapping for the dropdown: "Batch Name (ID)" -> ID
    batch_options = {f"{b.get('batch_name', 'Unnamed')} (ID: {b['id']})": b['id'] for b in batches}
    
    # The Dropdown
    st.markdown("##### 1. Select Target Batch")
    selected_option = st.selectbox(
        "Choose a batch to upload data into:", 
        options=list(batch_options.keys()),
        label_visibility="collapsed"
    )
    
    # Get the actual ID from the selection
    selected_batch_id = batch_options[selected_option]

    st.info(f"📂 Uploading data to: **{selected_option}**")
    st.divider()

    # --- 2. TABS FOR DATA TYPES ---
    tab1, tab2, tab3 = st.tabs(["🖼️ Image Files", "🔊 Audio Files", "📄 Text Files"])

    # ensure proper full URL for file
    def get_file_url(file_url):
        if not file_url:
            return None
        if file_url.startswith("/"):
            return f"{BACKEND_API_BASE_URL}/{file_url}"
        return file_url

    def show_uploaded_files(batch_id, file_type, BACKEND_API_BASE_URL, headers):
        # API endpoint selection
        if file_type == 'image':
            url = f"{BACKEND_API_BASE_URL}/project-management/batch-imagedata-upload/?batch_id={batch_id}"
        elif file_type == 'audio':
            url = f"{BACKEND_API_BASE_URL}/project-batch/batch-audiodata-upload/?batch_id={batch_id}"
        else:
            url = f"{BACKEND_API_BASE_URL}/project-batch/batch-textdata-upload/?batch_id={batch_id}"

        try:
            resp = requests.get(url, headers=headers)
            if resp.status_code != 200:
                # Silent fail or small warning to avoid clutter if empty
                return

            data = resp.json()
            files = data["results"] if isinstance(data, dict) and "results" in data else data

            if not files:
                st.info("No files uploaded to this batch yet.")
                return

            st.subheader("📂 Uploaded Files in this Batch")

            # ====== IMAGE GALLERY ======
            if file_type == 'image':
                cols_per_row = 5
                rows = math.ceil(len(files) / cols_per_row)

                for row in range(rows):
                    cols = st.columns(cols_per_row)
                    for col_idx, col in enumerate(cols):
                        idx = row * cols_per_row + col_idx
                        if idx < len(files):
                            f = files[idx]
                            fname = f.get('file_name') or f.get('file')
                            file_url = get_file_url(f.get('file'))
                            if file_url:
                                col.image(file_url, caption=fname, use_container_width=True)

            # ====== TABLE VIEW ======
            st.markdown("### 📑 File Metadata")
            file_table = [
                {
                    "Name": f.get("file_name") or f.get("file"),
                    "Size (KB)": round(f.get("file_size", 0)/1024, 2) if f.get("file_size") else 0,
                    "Type": f.get("file_type", "-"),
                    "Uploaded At": f.get("uploaded_at", "-"),
                    "Download": get_file_url(f.get("file")),
                }
                for f in files
            ]
            st.dataframe(file_table, use_container_width=True)

        except Exception as e:
            st.error(f"❌ Error fetching files: {e}")

    # --- Image Upload ---
    with tab1:
        st.markdown("""
            <div class='upload-card'>
                <b>Upload Images</b><br>
                <span style='font-size:0.95em;color:#bbb;'>Supported: jpg, jpeg, png, webp, zip</span>
            </div>
        """, unsafe_allow_html=True)

        plans_class, plans_obj, plans_poly = [], [], []
        selected_class, selected_obj, selected_poly = [], [], []

        if selected_batch_id:
            try:
                # Fetch available plans from backend using the selected batch ID
                resp_class = requests.get(f"{BACKEND_API_BASE_URL}/image-annotations/image-classification-plans/{selected_batch_id}/", headers=headers)
                resp_obj = requests.get(f"{BACKEND_API_BASE_URL}/image-annotations/image-object-detection-plans/{selected_batch_id}/", headers=headers)
                resp_poly = requests.get(f"{BACKEND_API_BASE_URL}/image-annotations/image-polygon-plans/{selected_batch_id}/", headers=headers)

                if resp_class.status_code == 200:
                    plans_class = resp_class.json()
                    selected_class = st.multiselect(
                        "Select Classification Plans",
                        options=[(p["id"], p["plan_name"]) for p in plans_class],
                        format_func=lambda x: x[1],
                        key="class_plan_select"
                    )
                if resp_obj.status_code == 200:
                    plans_obj = resp_obj.json()
                    selected_obj = st.multiselect(
                        "Select Object Detection Plans",
                        options=[(p["id"], p["plan_name"]) for p in plans_obj],
                        format_func=lambda x: x[1],
                        key="obj_plan_select"
                    )
                if resp_poly.status_code == 200:
                    plans_poly = resp_poly.json()
                    selected_poly = st.multiselect(
                        "Select Polygon Plans",
                        options=[(p["id"], p["plan_name"]) for p in plans_poly],
                        format_func=lambda x: x[1],
                        key="poly_plan_select"
                    )
            except Exception as e:
                st.error(f"❌ Could not fetch plans: {e}")

        uploaded_images = st.file_uploader(
            "Select image files",
            type=["jpg", "jpeg", "png", "webp", "zip"],
            accept_multiple_files=True,
            key="img_upload"
        )

        if st.button("Upload Images", key="upload_img_btn"):
            if not selected_batch_id or not uploaded_images:
                st.error("Please select a batch and at least one image file.")
            else:
                # Extract only IDs from selections
                plan_class_ids = [pid for pid, _ in selected_class]
                plan_obj_ids = [pid for pid, _ in selected_obj]
                plan_poly_ids = [pid for pid, _ in selected_poly]

                for img_file in uploaded_images:
                    files = {"file": (img_file.name, img_file, img_file.type)}
                    data = {
                        "batch": selected_batch_id,
                        "plan_classification": plan_class_ids,
                        "plan_object_detection": plan_obj_ids,
                        "plan_polygon": plan_poly_ids,
                    }

                    upload_url = f"{BACKEND_API_BASE_URL}/project-management/batch-imagedata-upload/"
                    with st.spinner(f"Uploading {img_file.name}..."):
                        resp = requests.post(upload_url, headers=headers, files=files, data=data)

                    if resp.status_code in (200, 201):
                        st.success(f"Uploaded: {img_file.name}")
                    else:
                        st.error(f"Failed to upload {img_file.name}: {resp.text}")
        
        # Show gallery below
        st.divider()
        show_uploaded_files(selected_batch_id, 'image', BACKEND_API_BASE_URL, headers)


    # --- Audio Upload ---
    with tab2:
        st.markdown("""
            <div class='upload-card'>
                <b>Upload Audio Files</b><br>
                <span style='font-size:0.95em;color:#bbb;'>Supported: mp3, wav, ogg, flac, zip</span>
            </div>
        """, unsafe_allow_html=True)
        
        uploaded_audios = st.file_uploader("Select audio files", type=["mp3", "wav", "ogg", "flac", "zip"], accept_multiple_files=True, key="audio_upload")
        
        if st.button("Upload Audio Files", key="upload_audio_btn"):
            if not selected_batch_id or not uploaded_audios:
                st.error("Please select a batch and at least one audio file.")
            else:
                for audio_file in uploaded_audios:
                    files = {"file": (audio_file.name, audio_file, audio_file.type)}
                    data = {"batch": selected_batch_id}
                    upload_url = f"{BACKEND_API_BASE_URL}/project-batch/batch-audiodata-upload/"
                    with st.spinner(f"Uploading {audio_file.name}..."):
                        resp = requests.post(upload_url, headers=headers, files=files, data=data)
                    if resp.status_code in (200, 201):
                        st.success(f"Uploaded: {audio_file.name}")
                    else:
                        st.error(f"Failed to upload {audio_file.name}: {resp.text}")
        
        st.divider()
        show_uploaded_files(selected_batch_id, 'audio', BACKEND_API_BASE_URL, headers)


    # --- Text Upload ---
    with tab3:
        st.markdown("""
            <div class='upload-card'>
                <b>Upload Text Files</b><br>
                <span style='font-size:0.95em;color:#bbb;'>Supported: txt, csv, tsv, xlsx, zip</span>
            </div>
        """, unsafe_allow_html=True)
        
        uploaded_texts = st.file_uploader("Select text files", type=["txt", "csv", "tsv", "xlsx", "zip"], accept_multiple_files=True, key="text_upload")
        
        if st.button("Upload Text Files", key="upload_text_btn"):
            if not selected_batch_id or not uploaded_texts:
                st.error("Please select a batch and at least one text file.")
            else:
                for text_file in uploaded_texts:
                    files = {"file": (text_file.name, text_file, text_file.type)}
                    data = {"batch": selected_batch_id}
                    upload_url = f"{BACKEND_API_BASE_URL}/project-batch/batch-textdata-upload/"
                    with st.spinner(f"Uploading {text_file.name}..."):
                        resp = requests.post(upload_url, headers=headers, files=files, data=data)
                    if resp.status_code in (200, 201):
                        st.success(f"Uploaded: {text_file.name}")
                    else:
                        st.error(f"Failed to upload {text_file.name}: {resp.text}")
        
        st.divider()
        show_uploaded_files(selected_batch_id, 'text', BACKEND_API_BASE_URL, headers)