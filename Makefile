# Fénix — todos los flujos pasan por aquí (nunca comandos crudos).
COMPOSE_FILE := deploy/compose/docker-compose.yml
PROFILE ?= full
GPU ?= 0

COMPOSE := docker compose --env-file .env -f $(COMPOSE_FILE)
ifeq ($(GPU),1)
COMPOSE += -f deploy/compose/gpu.override.yml
endif

.DEFAULT_GOAL := help
.PHONY: help install up down logs test lint fmt ingest eval-retrieval eval-chunking

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

ingest: .env ## Ingesta corpus/ → pgvector + FTS (idempotente por hash)
	uv run --env-file .env python -m fenix_ingestion

# OMP/torch a pocos hilos: con bge-m3 y el reranker (modelos pequeños en CPU) usar
# todos los núcleos genera contención y va más lento que con 4 hilos.
eval-retrieval: .env ## Evals L1: denso vs híbrido vs híbrido+rerank → docs/evals.md
	OMP_NUM_THREADS=4 uv run --env-file .env python evals/run_retrieval.py

eval-chunking: .env ## Experimento L1: target=500 vs 250 tokens (tabla temporal) → docs/evals.md
	OMP_NUM_THREADS=4 uv run --env-file .env python evals/run_chunking_experiment.py

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
