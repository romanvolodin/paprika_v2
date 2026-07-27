# syntax = docker/dockerfile:1

FROM node:22-alpine AS frontend-build
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json frontend/.npmrc ./
RUN npm ci
COPY frontend/ .
ARG VITE_API_BASE_URL=/api/v1
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build

FROM python:3.14-slim AS docs-build
COPY --from=ghcr.io/astral-sh/uv:0.11.22 /uv /usr/local/bin/uv
WORKDIR /docs
COPY docs/ .
RUN uv sync --locked && uv run zensical build

FROM caddy:2-alpine
COPY caddy/Caddyfile /etc/caddy/Caddyfile
COPY --from=frontend-build /app/dist /srv/frontend
COPY --from=docs-build /docs/site /srv/docs
