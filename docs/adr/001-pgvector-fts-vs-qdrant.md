# ADR-001 · PostgreSQL (pgvector + FTS) como almacén único del RAG

- **Estado:** aceptado
- **Fecha:** 2026-06-12
- **Decisores:** Marcos

## Contexto y problema

El RAG híbrido necesita búsqueda densa (embeddings) y léxica (texto completo) sobre un
corpus ES/EN. Hay que elegir almacén(es) sabiendo que el equipo (de una persona) ya
opera PostgreSQL a diario y que el stack debe ser 100% self-hosted.

## Opciones consideradas

1. PostgreSQL 16 + pgvector (HNSW) + FTS nativo (`tsvector`).
2. Qdrant (vectores) + su léxico/payload filtering.
3. Elasticsearch/OpenSearch (BM25 real) + almacén vectorial aparte.

## Decisión

Opción 1. Un solo almacén para datos, vectores y léxico: menos piezas, backups y
operación triviales, y coherente con la experiencia previa del equipo. La fusión se
hace con **RRF** (k=60) sobre tres rankings: denso (coseno sobre HNSW) + FTS con
diccionario `spanish` + FTS con diccionario `english` (no se detecta el idioma de la
query; RRF absorbe el ranking que no aplique). El top-20 fusionado pasa por
**bge-reranker-v2-m3** y se sirve el top-5.

Detalles de implementación que fijan contrato:

- Embeddings `bge-m3` (1024 dims) normalizados → `vector_cosine_ops`.
- HNSW `m=16, ef_construction=64` (defaults razonables; se recalibran si los evals L1
  lo piden).
- `tsv` es columna generada por idioma del documento → indexable con GIN y sin lógica
  de ingesta extra.
- Vectores serializados como literal textual + `::vector` (sin adaptador
  `pgvector-python`: una dependencia menos).

## Consecuencias

### Positivas

- Híbrido real en una sola query path; el experimento L1 (denso vs híbrido vs
  híbrido+rerank) se reduce a SQL + una función de fusión pura y testeable.
- Checkpoints de LangGraph (F4) podrán vivir en el mismo Postgres.

### Negativas (tradeoffs honestos)

- `ts_rank` no es BM25 (sin saturación de término ni normalización por longitud
  equivalentes). Si los evals L1 mostraran al léxico lastrando al híbrido, las
  alternativas documentadas son ParadeDB `pg_search` o Qdrant.
- HNSW añade coste de escritura en ingesta; irrelevante a este tamaño de corpus.
