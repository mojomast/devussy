FROM python:3.12-slim
WORKDIR /app

# Install required system packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project code
COPY ./ /app/

# Install Python deps
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "streaming_server.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
