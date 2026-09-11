#!/usr/bin/env bash
set -e

echo "[entrypoint] waiting for postgres..."
python - <<'PYEOF'
import os
import time
import psycopg

owner_url = os.environ.get("DATABASE_URL_OWNER", "")
# psycopg wants a plain postgresql:// url, strip the sqlalchemy driver suffix
conn_str = owner_url.replace("postgresql+psycopg://", "postgresql://")

for attempt in range(60):
    try:
        with psycopg.connect(conn_str, connect_timeout=3) as conn:
            pass
        print("[entrypoint] postgres is up")
        break
    except Exception as exc:
        print(f"[entrypoint] postgres not ready yet ({exc}); retrying...")
        time.sleep(2)
else:
    raise SystemExit("[entrypoint] postgres never became ready")
PYEOF

if [ "$#" -gt 0 ]; then
  echo "[entrypoint] running: $*"
  exec "$@"
fi

echo "[entrypoint] starting uvicorn"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
