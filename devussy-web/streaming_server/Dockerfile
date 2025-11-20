FROM python:3.12-slim
WORKDIR /app

# Install required system packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy only what's needed from the repo to keep the image lean and predictable.
# We ensure the repo's 'src' and the streaming_server code are available at
# /app/src and /app/streaming_server respectively, and copy supporting files.
COPY pyproject.toml requirements.txt /app/
COPY src /app/src
COPY devussy-web/streaming_server /app/streaming_server
COPY config /app/config
COPY templates /app/templates

# Use a venv-free build because the image is ephemeral for the service.
RUN pip install --upgrade pip
# Install dependencies used by the streaming server (uses root requirements)
RUN pip install -r requirements.txt
# Install this package so 'src' is available as an installed package (src namespace)
RUN pip install -e .

EXPOSE 8000

CMD ["uvicorn", "streaming_server.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
