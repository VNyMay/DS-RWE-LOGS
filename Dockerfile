# Digital Society Casebook - container image.
#
# Build:  docker build -t digital-society-casebook .
# Run:    docker run -p 8501:8501 -e ADMIN_PASSWORD=change-me -v casebook-data:/app/data digital-society-casebook
#
# ADMIN_PASSWORD is required (there is no secrets.toml baked into the
# image). The volume keeps data/examples.db across container restarts;
# without it, every restart starts with an empty database.

FROM python:3.12-slim

# Streamlit writes bytecode caches and a config folder; keep the image
# deterministic and skip .pyc files.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

WORKDIR /app

# Install dependencies first so this layer is cached unless requirements change.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code.
COPY . .

# The database lives here; mount a volume on it to persist data.
RUN mkdir -p /app/data

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')" || exit 1

CMD ["streamlit", "run", "app.py"]
