# Streamlit Crowdsourcing Prototype

This Streamlit app will demonstrate the main features of your crowdsourcing platform using backend data:

## Main Features/Pages

- **User Login**: Authenticate users via backend API.
- **Annotation Tasks**: Display available annotation tasks (audio, image, text) and allow users to submit annotations.
- **Admin Dashboard**: Show project/task statistics, user management, and batch uploads.
- **Analytics**: Visualize annotation progress, quality metrics, and user activity.

## Data Integration
- The app will connect to your Django backend via REST API endpoints for authentication, task retrieval, submission, and analytics.
- API endpoints will be configurable in the Streamlit app.

## UI Navigation
- Sidebar navigation for switching between pages.
- Responsive layout for usability.

---

Next: Set up the Streamlit app structure and basic navigation.

## Run Streamlit
- poetry run streamlit run .\streamlit_app\app.py