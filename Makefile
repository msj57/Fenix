# Fénix — todos los flujos pasan por aquí (nunca comandos crudos).
COMPOSE_FILE := deploy/compose/docker-compose.yml
PROFILE ?= full
GPU ?= 0

COMPOSE := docker compose --env-file .env -f $(COMPOSE_FILE)
ifeq ($(GPU),1)
COMPOSE += -f deploy/compose/gpu.override.yml
endif

.DEFAULT_GOAL := help
.PHONY: help install up down logs test lint fmt

help: ## Lista los targets disponibles
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

install: ## Sincroniza el entorno (uv sync: workspace completo + dev)
	uv sync

up: .env ## Levanta el stack (PROFILE=full|lite|cloud-llm, GPU=1 para Ollama con NVIDIA)
	$(COMPOSE) --profile $(PROFILE) up -d --wait

down: .env ## Para el stack
	$(COMPOSE) --profile $(PROFILE) down

logs: .env ## Sigue los logs del stack
	$(COMPOSE) logs -f

test: ## Tests unitarios (LLMs mockeados; rápidos y gratis)
	uv run pytest

lint: ## ruff + formato + mypy --strict
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy .

fmt: ## Autoformatea y aplica fixes seguros
	uv run ruff format .
	uv run ruff check --fix .

.env:
	@echo "Falta .env — copia .env.example a .env y ajusta los valores." && exit 1
