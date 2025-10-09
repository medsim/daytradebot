
# Minimal Dockerfile for Render Worker (Python 3.11)
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1     PYTHONUNBUFFERED=1

WORKDIR /app

# System deps (optional: ca-certificates for https APIs)
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy code last to leverage Docker layer cache
COPY . .

# Ensure packages import cleanly
RUN python - <<'PY'
import os
for pkg in ['utils','brokers','bot_daytrade']:
    os.makedirs(pkg, exist_ok=True)
    init_path = os.path.join(pkg,'__init__.py')
    open(init_path,'a').close()
print('Package init files ensured')
PY

# Default command (can be overridden by Render)
CMD [ "python", "app_fast.py" ]
