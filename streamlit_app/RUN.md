# Running the Streamlit Crowdsourcing Prototype

This guide explains how to launch and use the Streamlit UI for your crowdsourcing platform, including integration with your backend and authentication gateway.

## Prerequisites
- Python 3.8+
- Poetry (for dependency management)
- Your Django backend and auth gateway service running and accessible
- Streamlit and requests installed (already handled by Poetry)

## 1. Backend & Auth Gateway Setup
- Ensure your Django backend is running (e.g., `python manage.py runserver` or via Docker).
- Ensure the authentication gateway service is running and accessible. Note its API base URL (e.g., `http://localhost:8001`).
- Update the Streamlit app's `API_BASE_URL` in `streamlit_app/app.py` to point to the correct backend or gateway endpoint if needed.

## 2. Launch the Streamlit App
From the project root or `streamlit_app/` directory, run:

```
poetry run streamlit run streamlit_app/app.py
```

Or, if not using Poetry:
```
cd streamlit_app
streamlit run app.py
```

## 3. Using the UI
- **Login**: Enter your username and password. The app will authenticate via the auth gateway and store your token in session.
- **Annotation Tasks**: After login, view and annotate tasks fetched from the backend. Submissions are sent with your auth token.
- **Admin Dashboard**: (To be implemented) Will show project stats, user management, and batch uploads.
- **Analytics**: (To be implemented) Will visualize annotation progress and quality.

## 4. Configuration
- Edit `API_BASE_URL` in `app.py` to match your backend or gateway URL.
- If your auth gateway uses a different login endpoint or token scheme, update the login logic in `app.py` accordingly.

## 5. Troubleshooting
- If you see connection errors, check that both backend and auth gateway are running and accessible from your machine.
- Ensure CORS is enabled on your backend/gateway for requests from Streamlit (localhost).
- Check the terminal for error messages from Streamlit or the backend.

---

For further customization, extend the UI pages in `app.py` and connect to additional backend endpoints as needed.
