"""Entry point that binds uvicorn from :class:`~app.core.config.Settings`.

``BACKEND_HOST`` / ``BACKEND_PORT`` are read through the same settings object the
application uses, so one source governs both local runs (``python -m app.run``)
and the container command.
"""

import uvicorn

from app.core.config import get_settings


def main() -> None:
    """Serve the API on the configured host and port."""
    settings = get_settings()
    uvicorn.run("app.main:app", host=settings.backend_host, port=settings.backend_port)


if __name__ == "__main__":
    main()
