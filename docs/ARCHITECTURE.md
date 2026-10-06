# MORIQ AI — Architecture

Status: baseline inventory; no MORIQ implementation has been added.

## Inherited components

- `src/`: SvelteKit/Svelte and TypeScript frontend; Vite builds the static frontend.
- `backend/open_webui/`: Python FastAPI application, API routers, models, retrieval, and provider integrations.
- `backend/open_webui/migrations/`: database migrations; upstream SQLAlchemy/Alembic persistence.
- `static/`: frontend assets, including browser-side Python assets prepared by `scripts/prepare-pyodide.js`.
- Upstream supports Ollama and OpenAI-compatible services. A MORIQ provider/model has not been selected.

During development, Vite and the FastAPI backend run separately. The backend can serve the built frontend. Runtime data and credentials belong outside Git and must use an isolated development environment.

## Change approach

Keep the baseline intact. Evaluate existing upstream configuration and extension interfaces before proposing core edits. Model routing, knowledge ingestion, deployment topology, and access controls require explicit V1 requirements; this document does not select them.

See [upstream workflow and provenance](UPSTREAM_AND_LICENSE.md).
