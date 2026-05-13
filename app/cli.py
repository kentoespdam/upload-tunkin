"""CLI entry points for development and production servers."""

import uvicorn


def dev() -> None:
    """Run development server with auto-reload."""
    uvicorn.run("app.main:app", reload=True, port=8000)


def start() -> None:
    """Run production server."""
    uvicorn.run("app.main:app", host="0.0.0.0", port=80)
