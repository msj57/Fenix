# ADR-000 · Alcance y principios del proyecto

- **Estado:** aceptado
- **Fecha:** 2026-06-12
- **Decisores:** Marcos

## Contexto y problema

Fénix es un proyecto de portfolio: una plataforma AIOps agéntica que triajea, investiga
(RAG híbrido), diagnostica (tools MCP sobre una infraestructura demo) y propone remediación
con aprobación humana. Debe cubrir la checklist de contratación 2026 (LangGraph, MCP, RAG
híbrido, evals como gate, observabilidad LLM, guardrails, K8s, CI/CD) con coste recurrente €0
y un esfuerzo acotado (74–98 h). El riesgo principal no es técnico: es el scope creep y el
abandono a medias.

## Opciones consideradas

1. Construir "a demanda", sin plan cerrado, añadiendo piezas según apetezca.
2. Plan exhaustivo con fases shippables, Definition of Done por fase y stack congelado.

## Decisión

Opción 2. El proyecto se rige por `fenix-planning.md` v1.0:

- **9 fases (F0–F8), cada una mergeable a `main` y válida como portfolio desde F2.**
- **Regla inquebrantable:** no se empieza la fase N+1 sin cumplir el DoD de la fase N.
- **Stack congelado** (§2 del planning): cambiarlo exige un ADR nuevo.
- **Una decisión mayor = un ADR** (plantilla en `docs/adr/template.md`).
- **Modo 100% local/gratuito:** Gemini free tier + Ollama + OSS self-hosted.
- **Principio rector:** el proyecto no compite por tamaño, compite por criterio demostrable —
  cada decisión documentada y respaldada por una métrica.

## Consecuencias

### Positivas

- Progreso visible y celebrable (releases v0.1…v0.8); abandono a mitad sigue dejando un
  artefacto útil.
- Las decisiones quedan defendibles en entrevista (ADRs + métricas).

### Negativas (tradeoffs honestos)

- Menos libertad para perseguir ideas brillantes a mitad de camino: van a "extensiones
  opcionales", nunca antes de F8.
- Mantener ADRs y DoD tiene un coste fijo de tiempo por fase.
