FROM python:3.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH" \
    HOME=/home/goofish \
    DISPLAY=:99 \
    GOOFISH_NO_CHROME_BOOTSTRAP=1
WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends nodejs xvfb xauth ca-certificates \
    && pip install uv==0.11.3 \
    && rm -rf /var/lib/apt/lists/*
# Keep the browser layer independent of source and README changes.
RUN printf 'APT::Install-Recommends "false";\n' > /etc/apt/apt.conf.d/99goofish-no-recommends \
    && uvx --from playwright==1.58.0 playwright install --with-deps chrome \
    && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml uv.lock README.md LICENSE ./
COPY src ./src
COPY skills ./skills
RUN uv sync --frozen --no-dev --no-editable \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 goofish \
    && mkdir -p /home/goofish/.goofish-cli \
    && chown -R goofish:goofish /home/goofish
# Upstream uv.lock omits filelock declared in pyproject.toml.
RUN uv pip install --python /app/.venv/bin/python filelock==3.16.1 \
    && uv pip check --python /app/.venv/bin/python
COPY --chmod=755 docker/entrypoint.sh /usr/local/bin/goofish-entrypoint
COPY docker/verify_runtime.py /usr/local/lib/goofish/verify_runtime.py
USER goofish
ENTRYPOINT ["goofish-entrypoint"]
CMD ["sleep", "infinity"]
