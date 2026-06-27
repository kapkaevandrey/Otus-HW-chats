## ---------------------------------------------------------------
## Local environment commands:
## ---------------------------------------------------------------

.DEFAULT_GOAL := help

PROJECT_NAME ?= otus-chats

## run:       start chat service in docker
run:
	docker compose -p $(PROJECT_NAME) up --build

## down:      stop containers
down:
	docker compose -p $(PROJECT_NAME) down --remove-orphans

## pytest:    run pytest in docker
pytest: down
	docker compose -p $(PROJECT_NAME) run --rm app pytest

## coverage:  check coverage in docker
coverage:
	docker compose -p $(PROJECT_NAME) run --rm app coverage

## check_code: run linter and mypy
check_code:
	docker compose -p $(PROJECT_NAME) run --rm app check_code

## format_code: apply formatters
format_code:
	docker compose -p $(PROJECT_NAME) run --rm app format_code

## upgrade:   apply alembic migrations
upgrade:
	docker compose -p $(PROJECT_NAME) run --rm app alembic upgrade head

## downgrade: rollback alembic migrations
downgrade:
	docker compose -p $(PROJECT_NAME) run --rm app alembic downgrade base

## install:   install dependencies locally via uv
install:
	uv sync --group dev

## update:    update dependencies via uv
update:
	uv sync --upgrade --group dev

help:
	@sed -ne '/@sed/!s/## //p' $(MAKEFILE_LIST)
