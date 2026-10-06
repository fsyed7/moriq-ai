# MORIQ AI — Knowledge strategy

Status: agreed V1 product direction recorded from the [PR #9 review](https://github.com/fsyed7/moriq-ai/pull/9#issuecomment-6026177279), October 6, 2026. These are requirements, not claims of implemented functionality.

## Agreed sequence

1. Start with curated architectural knowledge and legitimate public MORIQ sources.
2. Use that material for source-grounded, cited answers across the three V1 pillars.
3. Introduce private/internal MORIQ material only later, after explicit approval and definition of access and data-handling controls.

The source categories and order are agreed. Individual sources are not approved merely by belonging to a category; no corpus has been ingested by this documentation change.

## Source review and answer requirements

Record each source's publisher/owner, provenance, permission or usage terms, date/version, intended audience, and review status. For codes and jurisdiction-dependent material, record location, authority, edition/effective date, and applicability. Ask for missing jurisdiction context rather than treating one region's rules as universal.

Retain enough provenance for answers to cite and identify the supporting source. Surface conflicts, outdated references, and missing evidence. Do not transform general architectural guidance or a public project description into an invented MORIQ policy or internal procedure.

Use the [public source register](PUBLIC_MORIQ_SOURCES.md) to record verified MORIQ sources. Public accessibility alone does not establish authenticity, reuse rights, or suitability. Keep public references distinguishable from any later approved internal knowledge.

## Open implementation decisions

Specific source selections, reviewers, ingestion cadence, chunking, embeddings, vector store, retention, authorization, and evaluation thresholds remain open. The model strategy is provider-agnostic. See [evaluation](EVALUATION.md) and [security](SECURITY.md).
