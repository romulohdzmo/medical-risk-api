# syntax=docker/dockerfile:1

FROM python:3.12-slim-bookworm

# Copy official uv binary from Astral image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PYTHON_PREFERENCE=only-system

WORKDIR /app

# Create unprivileged user for security compliance
RUN useradd -m -u 1000 appuser

# Copy dependency configuration and lockfile
COPY pyproject.toml uv.lock README.md ./

# Install dependencies into /app/.venv using system Python
RUN uv sync --frozen --no-dev --no-install-project

# Copy source code and install project
COPY src/ /app/src/
RUN uv sync --frozen --no-dev

# Place virtualenv binaries directly on PATH
ENV PATH="/app/.venv/bin:$PATH"

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "medical_risk_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
