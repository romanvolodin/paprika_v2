RED := `printf '\033[31m'`
PURPLE := `printf '\033[35m'`
RESET-COLOR := `printf '\033[0m'`

default:
  @just --list

init-dev:
  @echo "{{ PURPLE }}Initializing dev environment...{{ RESET-COLOR }}"
  @if [ ! -f backend/.env ]; then \
    echo "{{ PURPLE }}Creating backend/.env from template...{{ RESET-COLOR }}"; \
    cp backend/.env.template backend/.env; \
  else \
    echo "{{ RED }}backend/.env already exists, it will not be overwritten.{{ RESET-COLOR }}"; \
  fi
  docker compose -f compose.dev.yaml up --build --detach
  docker compose -f compose.dev.yaml exec backend ./manage.py migrate
  docker compose -f compose.dev.yaml down
  @echo "{{ PURPLE }}Initializing done.{{ RESET-COLOR }}"

dev init='skip':
  {{ if init == "init" { "just init-dev" } else { "" } }}
  @echo "{{ PURPLE }}Running dev environment... Ctrl+C to stop.{{ RESET-COLOR }}"
  docker compose -f compose.dev.yaml up --build

migrate:
  docker compose -f compose.dev.yaml exec backend uv run manage.py migrate

superuser:
  docker compose -f compose.dev.yaml exec backend uv run manage.py createsuperuser
