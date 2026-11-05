# MORIQ AI

**An AI assistant for architects and engineers at MORIQ.** It answers questions on design, climate, materials, structure, services, drawings and site coordination, and it declines everything else. Every answer says what it rests on.

> **Version 1, working prototype.** It runs for one person on one computer. Answers are unreviewed drafts to check, not professional advice. It has no login and is not ready for a shared deployment.

## What it does

- **Stays in its field:** questions outside architecture and building engineering are declined.
- **Doesn't invent company practice:** MORIQ questions are answered only from documents you load. Otherwise it says the evidence is missing.
- **Careful with building codes:** it explains code concepts, but won't state a limit without an approved source for that jurisdiction and edition.
- **Labels every answer:** each one shows whether it used general knowledge, the built-in guide or a loaded document, with an evidence panel to inspect.
- **Warns about likely inventions:** it flags made-up citations, code sections and measurements that no source contains.
- **Teaches juniors:** a "Guide me" setting adds definitions and checklists.

## Run it

You need Python 3.12 and one model: either [Ollama](https://ollama.com) with the local model, or a Claude API key.

```shell
git clone https://github.com/fsyed7/moriq-ai.git
cd moriq-ai
py -3.12 -m moriq.app
```

Then open http://127.0.0.1:5180. On Windows you can double-click `start-moriq.bat` instead.

See the [app guide](moriq/app/README.md) for choosing a model and adding MORIQ documents.

## Test results

Run on 4 November 2026 with the local model on a laptop CPU:

|Check|Result|
|---|---|
|App tests, with a simulated model|22 of 22 pass|
|Browser click-through, including live answers and phone sizes|20 of 20 pass|
|Live spot check of routing, scope and references|10 of 10 pass, with answers taking about 20 to 25 seconds|
|Backend, contract and knowledge suites|57, 66 and 116 pass|

The spot check is a small set that was adjusted against during development. It does not grade whether answers are architecturally correct, and no architect or engineer has reviewed them. The Claude connection has only been tested against a simulated model.

## Before wider use

- Add MORIQ's own documents, which it does not have yet.
- Have an architect or engineer review answer quality and the AI-written starter guide.
- Run the live evaluation on a stronger model.
- Add logins and access control before anyone else uses it.
- Confirm the rights to use company images and documents.

## What's where

|Folder|Contents|
|---|---|
|[`moriq/app`](moriq/app)|**The MORIQ AI app:** server, question routing, model connection, starter guide and interface|
|[`moriq/brain`](moriq/brain)|The assistant's instructions and earlier reliability experiments|
|[`moriq/knowledge`](moriq/knowledge)|Source registry, retrieval and citation checks|
|[`studio-preview`](studio-preview)|Studio design and styles used by the app|
|[`offline_integration`](offline_integration), [`offline_evaluation`](offline_evaluation), [`synthetic_pilot`](synthetic_pilot)|Earlier offline contracts and test suites|
|[`docs/moriq-project`](docs/moriq-project/DOCUMENTATION-INDEX.md)|Project history, architecture, status and limitations|
|`backend`, `src`, `static` and root config files|Inherited Open WebUI code, which the app doesn't run on|

Earlier branches are kept as `archive/*` tags.

## Licence

This repository grew from [Open WebUI](https://github.com/open-webui/open-webui). Its [licence](LICENSE), [notice](LICENSE_NOTICE), [history](LICENSE_HISTORY) and [original README](README-OPEN-WEBUI.md) are preserved. The Courtyard Villa photograph is approved for local preview only, so it's left out of this repository and a clone shows a labelled placeholder instead.
