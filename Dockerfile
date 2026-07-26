FROM registry.access.redhat.com/ubi9/python-314 AS builder
USER root
COPY --from=ghcr.io/astral-sh/uv:python3.14-alpine /uv /uvx /bin/

USER 1001
WORKDIR /opt/app-root/src

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_DEV=1 \
    UV_PYTHON_DOWNLOADS=0

RUN --mount=type=cache,target=/opt/app-root/src/.cache/uv,uid=1001,gid=0 \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-editable

COPY . /opt/app-root/src/
RUN --mount=type=cache,target=/opt/app-root/src/.cache/uv,uid=1001,gid=0 \
    uv sync --locked --no-editable

FROM registry.access.redhat.com/ubi9/python-314-minimal

LABEL org.opencontainers.image.title="Clankair Shakur" \
      org.opencontainers.image.description="Discord bot for Umamusume-related statistics" \
      org.opencontainers.image.source="https://github.com/wiesmak/clankair-shakur" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.vendor="Umamusume Polska" \
      org.opencontainers.image.licenses="MIT"

USER root
WORKDIR /opt/app-root/src

COPY --from=builder /opt/app-root/src /opt/app-root/src

RUN chgrp -R 0 /opt/app-root/src && \
    chmod -R g=u /opt/app-root/src

ENV PATH="/opt/app-root/src/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

USER 1001

CMD ["clankair-shakur"]