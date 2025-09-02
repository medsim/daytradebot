# syntax=docker/dockerfile:1
FROM python:3.11-slim AS builder
ENV PYTHONDONTWRITEBYTECODE=1         PYTHONUNBUFFERED=1
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"
WORKDIR /tmp
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

FROM python:3.11-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1         PYTHONUNBUFFERED=1         PATH="/opt/venv/bin:${PATH}"
COPY --from=builder /opt/venv /opt/venv
WORKDIR /app
COPY . /app
EXPOSE 8000
# Render sets $PORT; default to 8000 locally
CMD ["/bin/sh","-lc","uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}"]
