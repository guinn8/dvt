# ── base: 7 MB compressed, ~23 MB unpacked ─────────────────────────────
FROM python:3.12-alpine

# tiniest (musl-based) image with python & pip pre-installed
# python:<ver>-alpine already has pip and setuptools, so no build-system drama.

# ── install runtime deps ───────────────────────────────────────────────
RUN apk add --no-cache git

# ── copy project & install in editable mode ────────────────────────────
WORKDIR /src
COPY . /src
RUN pip install --no-cache-dir --editable . \
    && pip install --no-cache-dir pytest

# ── copy integration script & run it by default ────────────────────────
WORKDIR /suite
COPY docker/suite.sh /suite/
RUN chmod +x /suite/suite.sh
CMD ["/suite/suite.sh"]
