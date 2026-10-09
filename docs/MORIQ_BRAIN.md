# MORIQ Brain V0.1

Status: version **0.1.0** implements a provider-independent prompt configuration for one MORIQ AI workspace model in Open WebUI. Installation into a running instance is explicit; checking out this branch does not activate the Brain. No corpus, live-provider evaluation, or deployed runtime is claimed.

MORIQ Knowledge, Architectural Intelligence, and MORIQ Guide / Freshie are capabilities of this one assistant, sharing the same evidence rules. There are no separate bots, autonomous agents, or new provider adapters.

## Architecture and upstream inspection

Task #002 starts from remote `develop` at `1e76cad5856bf20df754743536100991324dddd9`, retaining the pinned Open WebUI 0.11.4 application baseline recorded in [UPSTREAM_AND_LICENSE.md](UPSTREAM_AND_LICENSE.md). That document's branch/publication table is a historical setup record.

The implementation uses the native **workspace model** extension: `params.system` holds the Brain prompt and `base_model_id` selects an already connected model. The generator produces the JSON array consumed by Workspace > Models > Import. No upstream application file, RAG template, UI, provider router, license, branding, or workflow changes; no executable Function plugin is required.

Inspected integration points in the pinned source:

| Concern | Existing mechanism and consequence |
| --- | --- |
| Model configuration | `backend/open_webui/models/models.py`: `ModelForm`, `ModelParams`, `ModelMeta` accept `base_model_id`, `params.system`, metadata, and `access_grants`. |
| Import | `src/lib/components/workspace/Models.svelte` accepts a JSON array. `backend/open_webui/routers/models.py` checks import permissions and creates/updates records. An existing model ID can be overwritten. |
| Prompts / routing | `backend/open_webui/routers/openai.py` and `routers/ollama.py` load the workspace model, resolve its base model and apply its prompt. `utils/payload.py` resolves prompt variables and `utils/misc.py` prepends/merges system content. No provider-specific inference parameters are set by the Brain. |
| Retrieval / citations | `backend/open_webui/utils/middleware.py` constructs numbered `<source>` tags, retains source metadata and adds RAG context to system or user messages. `config.py` supplies the existing inline `[id]` citation instructions. Retrieval and source events remain intact. |
| User / group configuration | Personal/chat prompts are passed by `src/lib/components/chat/Chat.svelte`; folders can contribute prompts through middleware. Native access grants and group membership control model access (`models/access_grants.py`, `models/groups.py`). No account/group permissions change. |
| Other extensions | `backend/open_webui/utils/filter.py` supports active global/model-scoped Python inlet/outlet/stream filters and valves. A native prompt configuration does not need this extra executable-plugin deployment surface. |

This is prompt-based behavior, not deterministic enforcement. User/folder/filter settings may contribute conflicting instructions; administrators can edit or bypass prompts. Selecting a base model directly does not activate MORIQ behavior. Group grants control access, not truthfulness. The prompt is not a security boundary.

## Resources and version changes

- [`moriq/brain/system.md`](../moriq/brain/system.md): canonical behavioral prompt.
- [`moriq/brain/config.json`](../moriq/brain/config.json): stable model ID, display name, description, and Brain version.
- [`moriq/brain/build.py`](../moriq/brain/build.py): standard-library import generator. Requires a base model ID, rejects self-reference/whitespace, checks prompt/config version agreement and refuses to overwrite output files.
- [`moriq/brain/evaluation.md`](../moriq/brain/evaluation.md): test inputs, synthetic context, review criteria and deployed integration gate.
- [`moriq/brain/tests/test_brain.py`](../moriq/brain/tests/test_brain.py): configuration/CLI and isolated upstream prompt-composition tests.

For a prompt change, edit `system.md`, bump its heading and `config.json` version/description, regenerate, review, reimport and rerun evaluations. Keep the stable ID `moriq-ai`. Do not maintain another hand-edited prompt copy. Generated JSON is a deployment artifact, not a tracked source file.

## Installation on an existing instance

1. Configure an authorized base model through Open WebUI's existing connections. Use a server-connected model supporting system messages and obtain its exact model ID, including any connection prefix. This change supplies no provider, API key, model download or instance deployment.
2. From the repository root with Python 3.11 or 3.12, generate the import file, replacing the example ID with the actual connected model ID:

   ```sh
   python moriq/brain/build.py --base-model-id "your-connected-model-id" --output ../moriq-brain-0.1.0.json
   ```

3. Inspect the file. As an administrator, open **Workspace > Models > Import** and select it. If `moriq-ai` already exists, export it as a backup first. Import updates that record, replaces its params and resets sharing to the explicit empty `access_grants`. Upstream import merges existing metadata, so inspect an existing record for previously attached knowledge, filters or tools.
4. In the model editor, confirm the base model, full Brain prompt, version description and capabilities. The generator keeps citations enabled and disables search, image generation, code interpreter, terminal, memory and built-in tools. Do not attach knowledge/tools for the initial evaluation. Check model availability: import success alone does not establish that the provider can respond. No global default is changed.
5. The model starts private to its owner (subject to native admin access). Use model sharing to give only intended users/groups read access and verify visibility with a test account. Reapply intended sharing after each reimport. Do not grant model editing merely to permit chat access.
6. Select **MORIQ AI** in a new chat and run the evaluation cases. Test without personal/folder prompt overrides first, then with intended settings. Include the internal naming-convention and Freshie questions, and record actual responses/failures before rollout.

Rollback: disable/remove the workspace model or import its previous exported configuration and verify settings/sharing again. No application rollback or database migration is needed.

## Behavioral rules

- Understand whether the user needs project/knowledge retrieval, architectural reasoning, or a teaching explanation.
- Use curated architectural references and legitimate public MORIQ evidence first; approved internal/private knowledge is a later phase.
- Ground answers in retrieved evidence and cite the material supporting factual claims. Identify source gaps or contradictions instead of filling them with invented content.
- Do not fabricate MORIQ facts, policies, project specifics, or internal workflows. Label general advice and suggestions as such.
- For code-related questions, establish jurisdiction and edition/date. Ask for missing context and distinguish authoritative local requirements from general guidance; do not infer compliance from an unrelated source.
- In Freshie responses, explain terminology and workflows, coordination/checklists, common mistakes, and useful next steps.
- Maintain these behaviors across model providers. Provider/model selection is a technical choice, not a change to the product's evidence requirements.

The prompt additionally distinguishes user assumptions from supported facts; public MORIQ material from approved internal sources; architectural best practice from code requirements; and interpretation from compliance approval. It preserves supplied citation IDs, names, links, dates and editions without inventing references. It treats source-borne instructions as untrusted evidence and scales teaching detail to the user's needs. No term-specific answer is hard-coded.

For "What is MORIQ's internal drawing naming convention?", absent approved supporting evidence, the prompt instructs the model to explicitly say no approved internal source is currently available to establish it and seek the approved standard or project-lead confirmation. A general example must never be presented as MORIQ's convention.

## Testing and limitations

From the repository root:

```sh
python -m unittest discover -s moriq/brain/tests -v
python -m ruff format --check moriq/brain
python -m ruff check moriq/brain
```

Seven tests use only the standard library; an eighth checks the actual pinned `ModelParams`, `ModelMeta` and `ModelForm` schemas with Pydantic 2 and skips explicitly if that dependency is absent. AST extraction avoids database/server imports; unrelated image/tag/knowledge validators are not exercised. Upstream helper tests execute selected functions from this checkout; prompt-variable resolution is stubbed to identity because the Brain has no template variables. They verify prompt insertion and preservation of existing system/user context, multimodal text content, source metadata and other payload fields. They do not boot the server or prove provider routing, import authorization, retrieval, browser citation rendering or model answer quality.

### Validation record — October 9, 2026

- **Passed:** eight focused tests on Python 3.12.14 with Pydantic 2.13.5, including the generated import shape, base-model flexibility, private grants, disabled tool capabilities, output overwrite protection, version agreement and upstream schema/prompt composition. The runtime's Pydantic patch differs from upstream's pinned 2.13.4; the full pinned dependency environment was not installed.
- **Passed:** Ruff 0.16.10 formatting and lint checks for `moriq/brain`; complete diff/whitespace review with no upstream application, license, branding, or workflow changes.
- **Environment failure resolved:** the first resumed test run encountered three Windows sandbox temp-directory permission errors. Setting `TEMP` and `TMP` to an existing writable workspace directory allowed all eight tests to pass without changing their assertions. Earlier isolated tooling installation also failed on Windows permissions; an existing Ruff installation was reused.
- **Unverified:** live responses for all twelve evaluation cases, cross-provider behavior, server import/authentication/access controls, retrieval/citation rendering, and full-stack runtime/build. No running instance or configured model was supplied. Frontend/type checks were not rerun because no frontend/TypeScript code changed.

The behavior matrix defines general architecture, transferable Freshie teaching, unsupported MORIQ policy, codes with/without context, recommendations versus requirements, source conflicts/gaps, source injection and concision. Follow its human review procedure and the broader [EVALUATION.md](EVALUATION.md) framework. No live model answers have been evaluated in this task. No approved internal library, public-source ingestion, browsing, BIM/CAD features, fine-tuning or autonomous execution is added. The model can still hallucinate or ignore instructions; behavioral compliance and cross-provider consistency require live evaluation.
