# MORIQ AI app

An AI assistant for architects and engineers at MORIQ. It connects the Studio interface, the MORIQ Brain prompt, a built-in knowledge guide and a language model, and it only answers questions in that field.

## Run it

Run `install-moriq.ps1` once for a Desktop and Start menu icon, use `start-moriq.bat` to see startup errors, or run this from the root:

```shell
py -3.12 -m moriq.app
```

Then open http://127.0.0.1:5180. It needs Python 3.12, with nothing else to install for the local model.

## Choose a model

|Model|How to use it|Trade-off|
|---|---|---|
|Claude Opus 5.5 (recommended)|`pip install anthropic`, then set `ANTHROPIC_API_KEY` before starting|Much stronger and faster, but questions go to Anthropic and usage is billed|
|Local Ollama model (default)|Run Ollama with the model named in `provider.py`|Private and free, but slow on a CPU and weaker|

The app picks Claude automatically when a key and the SDK are present, and the top bar shows which model is running. Claude calls use server-side fallback, so a declined request is retried on another model.

## Add MORIQ documents

Put `.md` or `.txt` files in the `documents` folder inside `.moriq` in your home folder, then restart the app. The app prints the exact folder when it starts. It can then answer MORIQ questions from those files, and it labels those answers as loaded MORIQ documents that have not been independently reviewed. Only add documents you have the right to use.

## How a question is handled

|Question|What happens|Model used?|
|---|---|---|
|Outside architecture and engineering|Declined|No, or the model declines when the wording is unclear|
|General architecture or engineering|Answered from the starter guide where it matches, otherwise as general explanation|Yes|
|MORIQ practice, policy or standard|Answered from loaded documents, otherwise reported as an evidence gap|Only with a matching document|
|MORIQ projects and public facts|Answered from the public record, marked as not confirmed by MORIQ|Yes|
|Permit process or a code concept|Explained from the guide with no limits, labelled as not a code requirement|Yes|
|Specific code limit|Asks for jurisdiction and edition, then needs an approved source|Only with an approved source|
|Who MORIQ is|Shows public listing facts with links, marked as not approved by MORIQ|No|

Every answer stays `claim_status=not_assessed` and `release_allowed=false`. Answers get automatic warnings for citation numbers that do not exist, for code or section names that no retrieved source contains, and for numeric limits stated with no code source. These checks catch some invented content. They cannot show that an answer is true.

## What it is, and is not

This is not a model trained on MORIQ's work. It is a general language model restricted by rules to this field, and grounded in the guide and any documents you load. Its knowledge of MORIQ is only as good as those documents.

- **Starter guide:** most of the `guide` folder is general guidance written by AI. No architect or engineer has reviewed it, and every answer using it says so. Its regulation pointers rely partly on secondary sources, so confirm them with the authority.
- **Public record:** `guide/moriq-public.md` summarises public listings in our own words, with links and no photographs. MORIQ has not confirmed it. It cannot establish internal practice, so practice questions need loaded documents.
- **Scope lock:** keyword rules plus the model's own judgement, so unusual wording can slip through in either direction.
- **Access:** there is no login or audit trail, and the app listens on this computer only. Do not expose it to a network or enter confidential client information.
- **Stop:** closing the connection asks the model to stop, but nothing proves it has gone idle.
- **Offline facade:** the Task 6.1B facade refuses generation by design, so this app does not route through it. It reuses the same registry, retrieval, citation checks and public status fields.
- **Design:** the interface follows Apple's Human Interface Guidelines as principles, in a web app. It uses no Apple artwork or SF Symbols, and it is not a native iOS app. The icon and name styling are provisional, not MORIQ's logo.
- **Image:** `courtyard-villa.jpg` is approved for local preview only and is left out of Git. A clone without it shows the labelled placeholder.
- **Firm website:** the site listed by ArchDaily, moriq.co.in, could not be reached on 2026-11-04, so nothing comes from it.

## Test it

```shell
py -3.12 -B -m unittest moriq.app.test_app moriq.app.test_security
py -3.12 -B -m moriq.app.evaluate results.json
```

The first uses a fake model. The second runs live questions through the configured model and checks routing, scope and references. A person still needs to read the answers to judge whether they are architecturally correct.
