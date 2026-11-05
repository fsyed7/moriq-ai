# MORIQ AI local app

The first connected version: the Studio interface, MORIQ Brain prompt, governed retrieval and a local model, working together on one computer. It is a single-user prototype, not a production service.

## Run it

Double-click `start-moriq.bat` in the repository root, or run this from the root:

```shell
py -3.12 -m moriq.app
```

Then open http://127.0.0.1:5180. It needs Python 3.12 and Ollama running with the model named in `provider.py`. It installs nothing, and chats are saved in `.moriq` in your home folder.

Test it with `py -3.12 -B -m unittest moriq.app.test_app`.

## How a question is handled

|Question|What happens|Model used?|
|---|---|---|
|General architecture|Answered and labelled as general explanation, or as source-supported if a source matches|Yes|
|MORIQ practice, policy or standard|Blocked as an evidence gap, because no approved MORIQ document is loaded|No|
|Building code, without jurisdiction and edition|Asks for both|No|
|Building code, with no approved source|Blocked as an evidence gap|No|
|Building code, with an approved source|Answered from that source and marked as not a compliance decision|Yes|
|Who MORIQ is|Shows public listing facts with links, marked as not approved by MORIQ|No|

Routing uses keyword rules, so a question can be sorted wrongly. Every answer stays `claim_status=not_assessed` and `release_allowed=false`. Answers also get automatic warnings for citation numbers that do not exist, and for code or section names that no retrieved source contains. These checks catch some invented references. They cannot show that the rest of an answer is true.

## Public company facts

`profile.py` holds facts from public listings, checked on 2026-11-04. They are shown to users with links but are not knowledge sources: they stay out of the registry and out of model prompts. The firm should confirm them. The site listed by ArchDaily, moriq.co.in, could not be reached when checked.

## Known limits

- **Knowledge:** only two clearly synthetic sample sources are loaded. Real MORIQ documents need rights and an independent reviewer before they go in.
- **Model:** a small local model on a CPU. Answers took about 50 to 75 seconds in testing, and it invented a code reference during testing despite its instructions. Quality has not been evaluated.
- **Stop:** closing the connection asks Ollama to stop, but nothing proves the model has gone idle.
- **Access:** there is no login or audit trail, and the app listens on this computer only. Do not expose it to a network or enter confidential client information.
- **Offline facade:** the Task 6.1B facade refuses generation by design, so this app does not route through it. It reuses the same registry, retrieval, citation checks and public status fields.
- **Image:** `courtyard-villa.jpg` is approved for local preview only and is left out of Git. A clone without it shows the labelled placeholder.
