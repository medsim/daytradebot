# syntax=docker/dockerfile:1
FROM python:3.11-slim AS builder
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
WORKDIR /tmp
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt &&     python - <<'PY'
import uvicorn, fastapi; print('OK uvicorn', uvicorn.__version__); print('OK fastapi', fastapi.__version__)
PY

FROM python:3.11-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
WORKDIR /app
COPY --from=builder $VIRTUAL_ENV $VIRTUAL_ENV
COPY . /app
EXPOSE 8000
# Use absolute path for uvicorn; shell expands ${PORT:-8000}
CMD ["/bin/sh","-lc","exec /opt/venv/bin/uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}"]
