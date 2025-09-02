#!/usr/bin/env sh
set -eu
: "${PORT:=8000}"
exec /opt/venv/bin/uvicorn app:app --host 0.0.0.0 --port "$PORT"
