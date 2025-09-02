# Trading Bot API (Absolute CMD)

This image runs uvicorn via an absolute path in `CMD` (no shell scripts, no PATH reliance).

## Deploy notes
- Service **must be** type **Web** with **Environment: Docker** on Render.
- Leave **Start Command** blank so Render uses the image's CMD.
- The container listens on `$PORT` (Render injects this). Locally, it defaults to 8000.

## Local
```bash
docker build -t trading-bot-api .
docker run --rm -p 8000:8000 -e PORT=8000 trading-bot-api
```
