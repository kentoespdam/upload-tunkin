FROM ghcr.io/astral-sh/uv:debian-slim
WORKDIR /app
COPY . .

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
