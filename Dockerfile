# syntax=docker/dockerfile:1
FROM ghcr.io/astral-sh/uv:python3.13-trixie-slim

# Create a non-root user for security
RUN groupadd --system --gid 999 appuser \
    && useradd --system --gid 999 --uid 999 --create-home appuser

WORKDIR /app

# --- Performance optimizations ---
# Compile .pyc bytecode for faster startup
ENV UV_COMPILE_BYTECODE=1
# Use copy instead of symlink (cache mount on separate filesystem)
ENV UV_LINK_MODE=copy
# Omit dev dependencies from production image
ENV UV_NO_DEV=1

# Layer 1: Install project dependencies only (cached until lock changes)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

# Layer 2: Add source code and install project itself
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

# Add entry points to PATH
ENV PATH="/app/.venv/bin:$PATH"

ENV TIMEZONE='Asia/Jakarta'

# Ensure logs directory exists and is writable by non-root user
RUN mkdir -p /app/logs && chown -R appuser:appuser /app/logs

# Reset default uv entrypoint
ENTRYPOINT []

# Drop root privileges
USER appuser

EXPOSE 80

# Use the CLI entry point defined in pyproject.toml -> app.cli:start
CMD ["start"]
