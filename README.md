# Fénix

**Plataforma AIOps agéntica de resolución de incidencias.** Un sistema multi-agente recibe una
incidencia de infraestructura, la triajea, investiga en una base de conocimiento (RAG híbrido),
diagnostica una infraestructura real mediante herramientas MCP y propone remediación con
aprobación humana — todo trazado, evaluado en CI y desplegado en Kubernetes.

<!-- TODO(F0): ajustar OWNER/REPO al publicar -->
<!-- ![ci](https://github.com/OWNER/fenix/actions/workflows/ci.yml/badge.svg) -->

> **Estado:** F0 · cimientos del repo. Roadmap completo en [`fenix-planning.md`](fenix-planning.md).

## Por qué existe

Trabajo como sysadmin resolviendo incidencias; Fénix es la plataforma de IA que automatiza mi
propio trabajo, construida con el rigor de producción que usaría un equipo real: cada decisión
tiene su [ADR](docs/adr/), cada cambio pasa evals en CI, y todo corre 100% local y gratis.

## Arquitectura

```mermaid
flowchart TB
    subgraph cliente["Cliente"]
        UI["CLI / mini-UI web<br/>(SSE)"]
    end

    subgraph plataforma["Plataforma Fénix (→ Kubernetes en F7)"]
        API["FastAPI Gateway<br/>SSE · auth simple · rate limit"]
        subgraph graph["LangGraph (proceso del API o worker)"]
            SUP["Supervisor<br/>(solo enruta/termina, máx. 25 iter.)"]
            TRI["Triage"]
            INV["Investigador<br/>(RAG)"]
            DIA["Diagnosticador<br/>(tools MCP read-only)"]
            REM["Remediador<br/>(acciones + aprobación humana)"]
        end
        RET["Servicio Retrieval<br/>híbrido RRF + reranker"]
        ING["Pipeline Ingesta<br/>(Job: parse→chunk→embed)"]
        PG[("PostgreSQL<br/>pgvector + FTS + checkpoints")]
        MCP["MCP Server 'fenix-diagnostics'<br/>FastMCP · streamable HTTP"]
    end

    subgraph demo["Demo-env 'rompible' (Compose, fuera de K8s)"]
        NGX["nginx"]
        APP["webapp dummy"]
        DBD[("postgres-demo")]
        RED[("redis-demo")]
        CHAOS["scripts de caos"]
    end

    subgraph obs["Observabilidad"]
        LF["Langfuse v3<br/>trazas · costes · prompts"]
        PROM["Prometheus"]
        GRAF["Grafana"]
    end

    subgraph llm["Modelos"]
        GEM["Gemini Flash<br/>(free tier)"]
        OLL["Ollama Qwen3<br/>(local)"]
        EMB["bge-m3 + bge-reranker<br/>(local, CPU)"]
    end

    UI -->|POST /incidents| API --> SUP
    SUP --> TRI & INV & DIA & REM
    INV --> RET --> PG
    ING --> PG
    DIA & REM --> MCP --> NGX & APP & DBD & RED
    CHAOS -.rompe.-> NGX & APP & DBD & RED
    graph -.trazas.-> LF
    API & MCP & demo -.métricas.-> PROM --> GRAF
    TRI & INV & DIA & REM --> GEM & OLL
    RET --> EMB
```

## Quickstart

Requisitos: Docker + compose v2, [`uv`](https://docs.astral.sh/uv/), `make`. 32 GB RAM para el
perfil `full` (hay perfiles `lite` y `cloud-llm` para máquinas justas — §1 del planning).

```bash
git clone <repo> fenix && cd fenix
cp .env.example .env        # ajusta valores; .env nunca se commitea
make up                     # Postgres+pgvector y Ollama (PROFILE=lite|cloud-llm, GPU=1 con NVIDIA)
make test                   # unit tests (LLMs mockeados: rápidos y gratis)
make lint                   # ruff + mypy --strict
```

## Estructura

```
apps/        api (gateway) · agents (LangGraph) · ingestion · mcp_server
packages/    retrieval · llm · guardrails (libs compartidas)
corpus/      KB sintética: runbooks, postmortems, tickets (F1)
evals/       golden sets + suites L1/L2/L3 como gate de CI (F1+)
demo-env/    infraestructura "rompible" que Fénix diagnostica (F3)
deploy/      compose (perfiles) · helm + k3d (F7)
ops/         Prometheus + Grafana (F2/F7)
docs/        ADRs · arquitectura · evals · seguridad
```

## Roadmap (fases shippables)

- [x] **F0** Cimientos: monorepo uv, tooling, compose base, CI
- [ ] **F1** Corpus + ingesta + retrieval híbrido + evals L1
- [ ] **F2** RAG conversacional + API + Langfuse
- [ ] **F3** Demo-env rompible + servidor MCP
- [ ] **F4** Multi-agente LangGraph + human-in-the-loop
- [ ] **F5** Evals E2E como quality gate
- [ ] **F6** Guardrails + seguridad (OWASP LLM Top 10)
- [ ] **F7** Kubernetes + dashboards
- [ ] **F8** Storytelling y cierre

Regla inquebrantable: no se empieza la fase N+1 sin el DoD de la fase N
([ADR-000](docs/adr/000-alcance-y-principios.md)).

## Licencia

[MIT](LICENSE)
