# evals/ — Golden sets y suites L1/L2/L3 como gate de CI. Arranca en F1 (§5.2, §6).

## L1 · Retrieval (ya disponible)

- `golden/retrieval/cases.yaml` — casos `question → relevant` (documentos por `source_path`).
- `run_retrieval.py` — corre denso/híbrido/híbrido+rerank, calcula hit@k y MRR, y escribe
  la tabla en `docs/evals.md`. Métricas en `fenix_retrieval.metrics` (testeadas sin DB ni LLM).
- Ejecutar: `make eval-retrieval` (necesita `make up` + `make ingest` antes).

Las métricas son deterministas y no llaman a ningún LLM. L2 (RAGAS) y L3 (trayectorias)
llegan en F2 y F5.
