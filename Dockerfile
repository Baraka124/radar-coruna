# SYNTHETIC SINGLE-INSTANCE STAGING ONLY. No clinical production deployment mode.
FROM python:3.13-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /srv/radar

# Verify the Supabase pooler certificate against trusted CAs, including its
# project-specific public root. Do not disable sslmode=verify-full.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*
COPY certs/supabase-root-2021.crt /usr/local/share/ca-certificates/supabase-root-2021.crt
RUN update-ca-certificates

COPY requirements-staging.txt .
RUN pip install --no-cache-dir -r requirements-staging.txt
COPY . .
RUN groupadd --gid 10001 radar && useradd --uid 10001 --gid 10001 --create-home radar \
    && mkdir -p /data && chown -R radar:radar /data /srv/radar
USER radar
EXPOSE 8080
CMD ["sh","-c","exec python -m uvicorn server:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1 --no-access-log"]
