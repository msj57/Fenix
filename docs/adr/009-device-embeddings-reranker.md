# ADR-009 · Dispositivo configurable para embeddings y reranker (CPU por defecto, GPU opcional)

- **Estado:** aceptado
- **Fecha:** 2026-06-13
- **Decisores:** Marcos

## Contexto y problema

§1 del planning fija embeddings (bge-m3) y reranker (bge-reranker-v2-m3) en **CPU** para
no competir por los 8 GB de VRAM de la RTX 3070 con Ollama (`qwen3:8b`, ~6 GB). Esa
restricción es correcta en operación normal (F2+), cuando los agentes usan el LLM local.
Pero `make eval-retrieval` (F1) corre **sin Ollama activo**: la VRAM está libre y forzar
CPU hace que el gate tarde minutos (las pasadas forward de los transformers son el cuello
de botella en CPU), cuando en GPU serían segundos.

## Opciones consideradas

1. Mantener todo en CPU siempre (statu quo de §1). Simple y reproducible, pero el gate L1
   es lento y desaprovecha la GPU ociosa durante las evals.
2. Mover embeddings/reranker a GPU siempre. Rápido, pero rompe el motivo de §1: en F2+
   competiría con Ollama por la VRAM.
3. **Dispositivo configurable** (`FENIX_DEVICE` = `cpu` | `cuda` | `auto`), con `cpu` por
   defecto y `auto`/`cuda` cuando convenga.

## Decisión

Opción 3. Se añade el setting `device` a `RetrievalSettings` (prefijo `FENIX_`), con
**`cpu` por defecto** —preserva la intención de §1 para producción— y un helper
`resolve_device()` que mapea `auto` a cuda/cpu según disponibilidad. El runner de evals
pide `FENIX_DEVICE=auto`, de modo que aprovecha la 3070 cuando Ollama no compite; CI sin
GPU funciona igual cayendo a cpu. El dispositivo vive en config, nunca hardcodeado
(coherente con la regla del proyecto).

## Consecuencias

### Positivas

- El gate L1 se acelera drásticamente en una máquina con GPU sin tocar el diseño de F2+.
- Reproducible en cualquier entorno: sin GPU, `auto` cae a cpu; CI puede forzar `cpu`.
- Deja la puerta abierta a decidir, en F2+, si el embedder cabe en VRAM junto a Ollama
  (medible) o se mantiene en CPU.

### Negativas (tradeoffs honestos)

- Los resultados de embeddings pueden diferir en los últimos decimales entre CPU y GPU
  (kernels distintos). No afecta a hit@k/MRR a la resolución que reportamos, pero conviene
  fijar el dispositivo al comparar runs finos.
- Una variable más que documentar y entender; mitigado con el default seguro (`cpu`).
