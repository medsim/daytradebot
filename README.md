# Trading Bot API (Render-ready)

Minimal FastAPI service with health checks and stub routes.

## Quick Start (Local)
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
./run_local.sh
# visit http://localhost:8000 and http://localhost:8000/docs
```

## Docker (Local)
```bash
docker build -t trading-bot-api .
docker run --rm -p 8000:8000 -e PORT=8000 trading-bot-api
```

## Deploy on Render
1. Commit this folder to your repo root.
2. Create a **Web Service** on Render, choose **Docker**.
3. Render uses the image's `CMD`, which runs:
   ```
   uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}
   ```
4. Add your env vars in Render dashboard as needed.
