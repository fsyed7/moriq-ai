# MORIQ AI — Architecture

Status: agreed V1 product direction recorded from the [PR #9 review](https://github.com/fsyed7/moriq-ai/pull/9#issuecomment-6026177279), October 6, 2026. These are requirements, not claims of implemented functionality.

## Inherited foundation

- `src/`: SvelteKit/Svelte and TypeScript frontend, built with Vite.
- `backend/open_webui/`: Python FastAPI application, API routers, models, retrieval, and provider integrations.
- `backend/open_webui/migrations/`: database migrations using upstream SQLAlchemy/Alembic persistence.
- `static/`: frontend assets, including browser Python assets prepared by `scripts/prepare-pyodide.js`.
- Upstream supports Ollama and OpenAI-compatible services. MORIQ's agreed strategy is provider-agnostic; the initial provider/model remains unselected.

Development runs the frontend and backend separately; the backend can serve the built frontend. Keep development data isolated and credentials outside Git.

## V1 responsibilities

MORIQ Knowledge supplies curated, traceable references. Architectural Intelligence uses that evidence with explicit jurisdiction/edition context. MORIQ Guide/Freshie presents explanations and practical next steps without inventing company procedures. These are product responsibilities, not three newly implemented services.

The intended answer flow is: establish the question and relevant context, retrieve appropriate source material, generate an answer through a replaceable provider/model, and return citations with uncertainty or missing evidence made clear. Start with curated architectural material and legitimate public MORIQ sources; add private/internal data only after approval and access controls are defined.

## Implementation decisions

Prefer existing upstream configuration and extension interfaces before proposing core changes. Provider adapters, retrieval/chunking configuration, embedding/vector-store choices, jurisdiction metadata, deployment topology, and private-data authorization require later implementation decisions. No code or runtime settings change in this review correction.

See [knowledge strategy](KNOWLEDGE_STRATEGY.md) and [upstream workflow](UPSTREAM_AND_LICENSE.md).
