# Base image: Python 3.14 on Alpine with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.14-alpine

# Use copy mode for the cache mount (cache and venv live on different filesystems)
ENV UV_LINK_MODE=copy

# git is required by uv to fetch the git-backed msoffcrypto-tool/olefile forks
RUN apk add --no-cache git ca-certificates

# Change the working directory to the `app` directory
WORKDIR /app

# Install dependencies (no project, no dev group; include the `http` extra for FastAPI/uvicorn)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-dev --no-install-project --extra http

# Copy only the files needed to build and run the project
COPY pyproject.toml uv.lock README.md LICENSE /app/
COPY src /app/src

# Sync the project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --extra http

# Expose the HTTP port
EXPOSE 8080

# Run the HTTP server
CMD ["/app/.venv/bin/uvicorn", "--log-level=info", "--proxy-headers", "--forwarded-allow-ips=*", "--host", "0.0.0.0", "--port", "8080", "doc_unlock.interface.http:app"]
