# Resultados de evaluación

Metodología y resultados versionados de las evals de Fénix. Las tablas marcadas como
_autogenerado_ las reescribe el runner correspondiente; el texto alrededor se cura a mano.

## L1 · Retrieval (determinista, sin LLM)

Mide la calidad del recuperador antes de meter ningún LLM por medio. Para cada caso del
golden set (`evals/golden/retrieval/cases.yaml`) se lanza la misma pregunta por los tres
modos y se comprueba si los documentos relevantes aparecen en el top-k.

- **hit@k**: fracción de casos en los que al menos un documento relevante está en el top-k.
- **MRR**: media del inverso del rango del primer documento relevante (documentos
  deduplicados; varios chunks del mismo doc no mejoran el rango).

La relevancia se ancla al **documento** (`source_path`), no al `chunk_id` (que Postgres
reasigna en cada reingesta) ni al `heading_path` (que depende de la estrategia de
chunking). Así el golden set sobrevive a reingestas y a recalibrar el chunking.

**Modos comparados:**

- `denso` — solo similitud coseno sobre embeddings bge-m3 (HNSW).
- `híbrido` — denso + FTS (es/en) fusionados con RRF.
- `híbrido+rerank` — lo anterior, reordenado por el cross-encoder bge-reranker-v2-m3.

**DoD de F1:** `hit@5` de _híbrido+rerank_ debe ser ≥ que el de _denso_ solo. Si no se
cumple, no se baja el umbral: se investiga (ver regla en CLAUDE.md).

Reproducir con `make eval-retrieval` (requiere el stack arriba y el corpus ingestado).

<!-- BEGIN eval-retrieval (autogenerado) -->
_Generado el 2026-06-13 14:20 UTC · 45 casos · top_k=5_

| Modo | hit@5 | MRR |
|---|---|---|
| denso | 1.000 | 0.896 |
| híbrido | 1.000 | 0.911 |
| híbrido+rerank | 1.000 | 0.944 |
<!-- END eval-retrieval -->

> Corpus: 50 documentos (22 runbooks, 9 postmortems, 19 tickets; ES/EN ~58/42), 45 casos
> en el golden set, incluidos casos "difíciles" donde varios documentos comparten
> vocabulario (502, timeout, sesión, HTTPS) y el retrieval debe discriminar el correcto.

## L1 · Experimento de chunking (determinista)

¿Importa el tamaño de chunk para el retrieval en este corpus? Se compara la estrategia
actual (`target=500` tokens) contra chunks más pequeños (`target=250`), reingestando el
corpus en una tabla temporal aislada (no toca la tabla de producción). Se mide denso e
híbrido; el reranker se omite porque actúa igual sobre cualquier chunking y solo añadiría
coste sin cambiar la conclusión sobre el troceado.

Reproducir con `make eval-chunking`.

<!-- BEGIN eval-chunking (autogenerado) -->
_Generado el 2026-06-13 14:40 UTC · top_k=5 · sin reranker_

| Estrategia | nº chunks | hit@5 denso | MRR denso | hit@5 híbrido | MRR híbrido |
|---|---|---|---|---|---|
| target=500 (actual) | 59 | 1.000 | 0.896 | 1.000 | 0.911 |
| target=250 | 99 | 1.000 | 0.904 | 1.000 | 0.919 |
<!-- END eval-chunking -->

> **Conclusión:** chunks de 250 tokens mejoran el MRR de forma marginal (+0.008) pero
> casi duplican el número de chunks (99 vs 59), con su coste proporcional en embeddings,
> almacenamiento y latencia por query. La ganancia no justifica el coste en este corpus,
> así que se **mantiene `target=500`**. hit@5 satura a 1.0 en ambas: el reto del dominio
> es ordenar (MRR), no encontrar.
