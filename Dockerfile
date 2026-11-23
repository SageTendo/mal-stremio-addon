FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

EXPOSE 5000

RUN uv sync --frozen --no-dev

ENTRYPOINT ["uv", "run", "python"]
CMD ["run.py"]
