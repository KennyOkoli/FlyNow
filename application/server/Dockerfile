FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /server
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project
COPY . .
RUN uv sync --frozen
CMD [ "uv", "run", "python", "./src/server/main.py"]