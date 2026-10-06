# MORIQ AI V1 — Product specification

Status: agreed V1 product direction recorded from the [PR #9 review](https://github.com/fsyed7/moriq-ai/pull/9#issuecomment-6026177279), October 6, 2026. These are requirements, not claims of implemented functionality.

## Purpose and pillars

MORIQ AI is an internal architecture/project knowledge assistant. V1 has three pillars:

| Pillar | Intended role |
| --- | --- |
| MORIQ Knowledge | Retrieve and explain source-backed architectural and MORIQ project knowledge |
| Architectural Intelligence | Support architectural reasoning and jurisdiction-aware interpretation of relevant codes and references |
| MORIQ Guide/Freshie | Teach terminology, workflows, coordination/checklists, common mistakes, and next steps |

## Agreed requirements

- Begin with curated architectural knowledge and legitimate public MORIQ sources. Approved private/internal material comes later; internal use does not imply permission to ingest private data now.
- Ground substantive answers in sources and provide citations. Make missing evidence, uncertainty, and conflicting sources explicit.
- Keep the model strategy provider-agnostic; do not couple product behavior to a single vendor or model.
- Never fabricate MORIQ facts, policies, project details, or internal practices. Distinguish general architectural guidance from verified MORIQ-specific information.
- Handle building-code questions in context: establish jurisdiction and applicable edition/date, cite relevant authority, and avoid presenting another jurisdiction's requirements as locally applicable.
- Deliver the V0.1 demo target on **October 20, 2026**, following the [two-week roadmap](ROADMAP.md). V0.1 is a limited demonstration of the V1 direction, not a claim that V1 is complete.

## Scope of this change

Repository: `fsyed7/moriq-ai`, based on the pinned official Open WebUI baseline. This setup and review correction are documentation-only: preserve application behavior, UI, Open WebUI branding, attribution, notices, and licenses. No feature implementation or merge is included.

## Decisions still open

Specific source URLs and usage rights, the initial model/provider configuration, supported jurisdictions/code editions, deployment details, access/retention controls, evaluation thresholds, and the precise demo script remain to be selected. The product purpose, pillars, knowledge sequence, and Freshie behavior above are agreed, not TBD.

See [architecture](ARCHITECTURE.md), [evaluation](EVALUATION.md), and [provenance and validation](UPSTREAM_AND_LICENSE.md). Branch publication is complete; full baseline runtime validation remains outstanding.
