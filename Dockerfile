FROM  northamerica-northeast1-docker.pkg.dev/cuenca-challenge/base-python/python-base-image:1.0.0
ENV PYTHONPATH "/app"
COPY pyproject.toml .
COPY uv.lock .
RUN uv sync
COPY app/ /app/app/
WORKDIR /app
RUN adduser -m userapp && chown -R userapp:userapp /app
USER userapp

CMD ["uv", "run", "/app/app/main.py" ]