# Trading Bot API (Render-ready, absolute uvicorn path)

This build calls uvicorn via its absolute path to avoid PATH issues on Render.

## Local (Docker)
```bash
docker build -t trading-bot-api .
docker run --rm -p 8000:8000 -e PORT=8000 trading-bot-api
```

## Notes
- ENTRYPOINT runs `/app/start.sh`, which execs `/opt/venv/bin/uvicorn`.
- No Render start command needed. If you previously set one, **clear it** so the image's ENTRYPOINT is used.
