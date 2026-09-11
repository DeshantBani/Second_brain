FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY api/pyproject.toml ./
# Install dependencies only first (no source yet) so rebuilds are fast when app code changes.
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir fastapi "uvicorn[standard]" sqlalchemy "psycopg[binary]" \
       pgvector pydantic pydantic-settings pyjwt bcrypt google-genai langgraph beautifulsoup4 \
       pypdf python-docx \
       celery redis minio python-multipart httpx python-dotenv pytest pytest-asyncio

# Build context is the repo root (not ./api) specifically so this can also copy in db/ -
# the mock CaseLawProvider's fixtures live there and, on a plain Docker host with no bind
# mount (e.g. Render), this COPY is the only way they end up in the image. Locally,
# docker-compose's `./db:/app/db` volume mount takes precedence at runtime anyway.
COPY api/ ./
COPY db/ ./db

RUN chmod +x entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
