default:
  @just --list

dev:
  docker compose -f compose.dev.yaml up --build

migrate:
  docker compose -f compose.dev.yaml exec backend uv run manage.py migrate

superuser:
  docker compose -f compose.dev.yaml exec backend uv run manage.py createsuperuser
