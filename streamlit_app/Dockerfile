# Use the same stable base image as your other services
FROM python:3.12-slim-bookworm

WORKDIR /app

# Install system dependencies (curl/netcat are useful for debugging connection issues)
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
# If you have a requirements.txt, COPY it and run pip install -r requirements.txt
# For now, we install directly based on your imports:
RUN pip install streamlit pandas requests

# Copy the rest of the application code
COPY . /app

# Expose Streamlit's default port
EXPOSE 8501

# Run Streamlit
# --server.address=0.0.0.0 is REQUIRED for Docker to expose the port externally
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]