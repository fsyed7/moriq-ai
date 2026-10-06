# MORIQ Brain — V1 answer behavior

Status: agreed V1 product direction recorded from the [PR #9 review](https://github.com/fsyed7/moriq-ai/pull/9#issuecomment-6026177279), October 6, 2026. These are requirements, not claims of implemented functionality.

This document records the intended answer behavior shared by MORIQ Knowledge, Architectural Intelligence, and MORIQ Guide/Freshie. It does not claim a deployed prompt, agent, memory system, or approved internal policy library.

## Required behavior

- Understand whether the user needs project/knowledge retrieval, architectural reasoning, or a teaching explanation.
- Use curated architectural references and legitimate public MORIQ evidence first; approved internal/private knowledge is a later phase.
- Ground answers in retrieved evidence and cite the material supporting factual claims. Identify source gaps or contradictions instead of filling them with invented content.
- Do not fabricate MORIQ facts, policies, project specifics, or internal workflows. Label general advice and suggestions as such.
- For code-related questions, establish jurisdiction and edition/date. Ask for missing context and distinguish authoritative local requirements from general guidance; do not infer compliance from an unrelated source.
- In Freshie responses, explain terminology and workflows, coordination/checklists, common mistakes, and useful next steps.
- Maintain these behaviors across model providers. Provider/model selection is a technical choice, not a change to the product's evidence requirements.

Prompt design, retrieval configuration, confidence handling, optional memory, and associated consent/retention controls remain implementation decisions. Assess proposed behavior using [EVALUATION.md](EVALUATION.md).
