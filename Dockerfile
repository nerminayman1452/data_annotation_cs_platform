# FIX: Use 'bookworm' (Debian 12) instead of 'bullseye' for better support and repositories
FROM python:3.12-slim-bookworm as builder

LABEL name="DROP" \
    description="Base Project" \
    version="1.0.0"

ENV APP_HOME=/opt/application/webapp
WORKDIR $APP_HOME

# Install required system packages
# FIX: Added '-o Acquire::Retries=3' to handle network timeouts automatically
# FIX: Combined commands to reduce layers and potential failures
RUN apt-get update && apt-get install --yes --no-install-recommends -o Acquire::Retries=3 \
    gcc \
    netcat-openbsd \
    libmariadb-dev-compat \
    libmariadb-dev \
    pkg-config \
    curl \
    libstdc++6 \
    apt-transport-https \
    ca-certificates \
    openssl \
    && update-ca-certificates \
    && openssl rehash /etc/ssl/certs

ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt

# Install Poetry
RUN pip install --no-color --no-warn-script-location --no-cache-dir poetry
COPY ./pyproject.toml $APP_HOME
RUN poetry config virtualenvs.create true
RUN poetry config virtualenvs.in-project true

# Add dependencies
RUN poetry add gunicorn
RUN poetry install --no-root --extras mysql

COPY . $APP_HOME

RUN chmod +x $APP_HOME/docker-entrypoint.sh

# Clean up
RUN find .venv -regex '.*\(/tests.*/\|/test.*/\|/*.pyc\|/*.dist-info\|/__pycache__\|/slapdtest\)$' -exec rm -rf "{}" + \
    && apt-get autoremove --yes --allow-remove-essential --purge gcc \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/log/* /var/cache/* \
    && rm -rf /root/* /root/.cache /root/.local

EXPOSE 8003
ENTRYPOINT ["/bin/sh", "/opt/application/webapp/docker-entrypoint.sh"]