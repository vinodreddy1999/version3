FROM python:3.12-slim AS base

WORKDIR /app

RUN groupadd --system app && useradd --system --gid app --home-dir /app app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini .
COPY docker-entrypoint.sh .
RUN chmod +x docker-entrypoint.sh

RUN chown -R app:app /app
USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/ready', timeout=3)" || exit 1

# Runs `alembic upgrade head` before serving. Fine for a single-instance
# deployment (docker-compose); with multiple replicas run migrations as a
# separate one-off step/Job instead so they don't race on container start.
#
# --proxy-headers/--forwarded-allow-ips trust X-Forwarded-* from any peer:
# safe here because this container is never published to the host (see
# docker-compose.yml) — only nginx, on the same private compose network, can
# reach it. Without this, request.client.host (and slowapi's rate-limit key)
# would resolve to nginx's container IP for every request instead of the
# real client, collapsing every visitor into one shared rate-limit bucket.
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=*"]
