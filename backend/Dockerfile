# Destiny computation API image.
#
# The backend is a stateless pure-computation service: no volumes, no database,
# no build-time secrets. Build from the repository root:
#   docker build -t destiny-backend ./backend
# pyswisseph publishes no prebuilt wheels for current CPython releases, so the
# C extension is compiled here and only the finished environment is copied on.
FROM python:3.13-slim AS build

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /build
COPY pyproject.toml ./
COPY app ./app
RUN pip install --no-cache-dir .

FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

COPY --from=build /opt/venv /opt/venv

WORKDIR /srv/destiny

# `pip install .` in the build stage resolves the dependency set declared in
# pyproject.toml, keeping that manifest the single source of truth. The source
# tree copied here is what actually runs (`python -m app.run` resolves `app` from
# the working directory before site-packages), because the geocoder reads
# data/cities.json relative to it.
COPY app ./app
COPY data ./data

# Run as an unprivileged user; nothing in the image needs root at runtime.
RUN groupadd --system destiny \
    && useradd --system --gid destiny --home-dir /srv/destiny --no-create-home destiny \
    && mkdir -p /srv/destiny/data/local \
    && chown -R destiny:destiny /srv/destiny /opt/venv
USER destiny

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/api/v1/health' % os.getenv('BACKEND_PORT', '8000'), timeout=4)"

CMD ["python", "-m", "app.run"]
