FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /server
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY . .
RUN uv sync --frozen --no-dev
EXPOSE 8000
# Health check for the load balancer / ECS: GET /api/health
CMD ["uv", "run", "--no-sync", "uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
