# Dependency and runtime inventory
The inherited application uses npm/package-lock.json, pyproject.toml/uv.lock and backend/requirements.txt. Source declares FastAPI, Uvicorn, Pydantic and other server dependencies; frontend uses Svelte, TypeScript, Vite and Tailwind configuration. Versions must come from these preserved manifests, not this narrative.

Historical bootstrap: Node 22.20.0, npm 10.9.3, Python 3.12.14, Ruff 0.16.10. Plain host python currently selects 3.10; migration validation uses an explicit 3.12 runtime where available. Studio package is private, type=module, with dev/test scripts and no third-party package dependencies. Its build/lint scripts are not configured.

Docker Desktop/WSL2 and Ollama belong to historical local deployment, not prerequisites for offline registry/contract tests. Model-weight downloads, Docker images, virtual environments, node_modules and uv caches are not duplicated in the recovery archive. Recreate dependencies only from reviewed locks and approved model/service settings; do not launch provider evaluation automatically. Live Docker volume data was not copied and remains a separate backup requirement.
