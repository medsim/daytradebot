
# Python slim base
FROM python:3.11-slim

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends     ca-certificates     && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# The service binds to $PORT (Render/Heroku)
ENV PORT=8000

# Expose port (optional for some PaaS)
EXPOSE 8000

# Default command
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
