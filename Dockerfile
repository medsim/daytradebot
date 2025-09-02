# syntax=docker/dockerfile:1
FROM python:3.11-slim AS builder
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"
WORKDIR /tmp
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt &&         python -c "import sys; import uvicorn, fastapi; print('OK: uvicorn', uvicorn.__version__); print('OK: fastapi', fastapi.__version__)"

FROM python:3.11-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY --from=builder /opt/venv /opt/venv
WORKDIR /app
COPY . /app
EXPOSE 8000
# Use a tiny launcher that execs the ABSOLUTE uvicorn path
ENTRYPOINT ["/app/start.sh"]
