# SYNTHETIC SINGLE-INSTANCE STAGING ONLY. No clinical production deployment mode.
FROM python:3.13-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /srv/radar
COPY requirements-staging.txt .
RUN pip install --no-cache-dir -r requirements-staging.txt
COPY . .
RUN groupadd --gid 10001 radar && useradd --uid 10001 --gid 10001 --create-home radar \
    && mkdir -p /data && chown -R radar:radar /data /srv/radar
USER radar
EXPOSE 8080
CMD ["sh","-c","exec python -m uvicorn server:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1 --no-access-log"]
