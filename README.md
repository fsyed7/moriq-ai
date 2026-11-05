# MORIQ AI

**An AI assistant for architects and engineers at MORIQ.** It answers questions on design, climate, materials, structure, services, drawings and site coordination, and it declines everything else. Every answer says what it rests on.

> **Version 1, working prototype.** It runs for one person on one computer. Answers are unreviewed drafts to check, not professional advice. It has no login and is not ready for a shared deployment.

## What it does

- **Stays in its field:** questions outside architecture and building engineering are declined.
- **Doesn't invent company practice:** questions on MORIQ's projects use its public record, and questions on its internal practice are answered only from documents you load. Otherwise it says the evidence is missing.
- **Careful with building codes:** it explains code concepts, but won't state a limit without an approved source for that jurisdiction and edition.
- **Labels every answer:** each one shows whether it used general knowledge, the built-in guide or a loaded document, with an evidence panel to inspect.
- **Warns about likely inventions:** it flags made-up citations, code sections and measurements that no source contains.
- **Teaches juniors:** a "Guide me" setting adds definitions and checklists.

## What it knows

|Knowledge|Covers|How it's labelled|
|---|---|---|
|Public MORIQ record|Firm profile, people, services, reported awards and nine published projects, summarised from public listings with links|Not confirmed by MORIQ|
|Regulation pointers|Who governs permits, fire, RERA, energy, insulation and registration in Telangana, India and Bahrain, with reported figures to verify|Depends on the question; not a code source|
|Starter guide|Design and climate, structure and services, materials and interiors, hospitality, sustainability, project stages, fees, contracts, site work and mentoring|AI-written, not reviewed|
|MORIQ documents|Whatever you add to the documents folder|Loaded document, not independently reviewed|

It holds nothing about MORIQ's internal standards, templates, staff or live projects until those documents are added.

## Run it

You need Python 3.12 and one model: either [Ollama](https://ollama.com) with the local model, or a Claude API key.

```shell
git clone https://github.com/fsyed7/moriq-ai.git
cd moriq-ai
py -3.12 -m moriq.app
```

Then open http://127.0.0.1:5180.

**To use it as an app on Windows,** run this once, then open MORIQ AI from the Desktop or Start menu icon:

```shell
powershell -ExecutionPolicy Bypass -File .\install-moriq.ps1
```

Browsers can also install it from the address bar. On a phone it needs hosting first, as explained in [installing, hosting and security testing](docs/moriq-project/DEPLOYMENT-AND-SECURITY.md).

See the [app guide](moriq/app/README.md) for choosing a model and adding MORIQ documents.

## Test results

Run on 4 November 2026 with the local model on a laptop CPU:

|Check|Result|
|---|---|
|App and security tests, with a simulated model|34 of 34 pass|
|Browser click-through, including live answers and phone sizes|20 of 20 pass|
|Live spot check of routing, scope and references|18 of 18 pass, with most answers taking about 25 to 35 seconds|
|Backend, contract and knowledge suites|57, 66 and 116 pass|

The spot check is a small set that was adjusted against during development. It does not grade whether answers are correct, and a passing run still included a wrong answer that missed a published project, which was then fixed in the record. No architect or engineer has reviewed the answers. The Claude connection has only been tested against a simulated model. The Strix penetration test has not been run, since it needs Docker and a paid AI key.

## Before wider use

- Add MORIQ's own documents, which it does not have yet, and have the firm confirm the public record.
- Have an architect or engineer review answer quality and the AI-written starter guide.
- Run the live evaluation on a stronger model.
- Add logins and access control before anyone else uses it, then host it with a domain and HTTPS.
- Run a penetration test such as Strix.
- Confirm the rights to use company images and documents.

## What's where

|Folder|Contents|
|---|---|
|[`moriq/app`](moriq/app)|**The MORIQ AI app:** server, question routing, model connection, knowledge guide and iOS-style interface|
|[`moriq/brain`](moriq/brain)|The assistant's instructions and earlier reliability experiments|
|[`moriq/knowledge`](moriq/knowledge)|Source registry, retrieval and citation checks|
|[`studio-preview`](studio-preview)|The earlier dark Studio prototype, kept for reference|
|[`offline_integration`](offline_integration), [`offline_evaluation`](offline_evaluation), [`synthetic_pilot`](synthetic_pilot)|Earlier offline contracts and test suites|
|[`docs/moriq-project`](docs/moriq-project/DOCUMENTATION-INDEX.md)|Project history, architecture, status and limitations|
|`backend`, `src`, `static` and root config files|Inherited Open WebUI code, which the app doesn't run on|

Earlier branches are kept as `archive/*` tags.

## Licence

This repository grew from [Open WebUI](https://github.com/open-webui/open-webui). Its [licence](LICENSE), [notice](LICENSE_NOTICE), [history](LICENSE_HISTORY) and [original README](README-OPEN-WEBUI.md) are preserved. The Courtyard Villa photograph is approved for local preview only, so it's left out of this repository and a clone shows a labelled placeholder instead.
