# Roadmap to V1 — planned, no release dates
|Phase|Deliverable and dependency|Acceptance and key risk|
|---|---|---|
|A: offline integration|Assess recovered 6.1B against 6.1A; agree bounded scope and frozen criteria before edits|Reproduce existing errors, preserve all contract/public-boundary tests, negative revocation/expiry/authority cases; no live calls|
|B: backend|Reviewed service boundary after A|Fixed DTO validation, denial/error/cancel behavior, scoped identities and durable audit; no implicit release authority|
|C: Studio connection|Backend contract plus preserved Studio design|Synthetic end-to-end chat/status/error/cancel flows; no private draft leakage; storage migration and keyboard regression evidence|
|D: controlled inference|Separate authorization and security/source prerequisites|Fixed endpoint/model/settings, semantic review, resource bounds, provider-idle/cancellation tests; no automatic promotion|
|E: persistence/lifecycle|Identity, durable audit and transactional state|Restart recovery, revocation races, replay, ownership and cross-process tests|
|F: end-to-end verification|Integrated approved components|Reproducible setup, real acceptance workflows, error/recovery tests and accessibility disposition|
|G: readiness|Security, rights, operational and performance review|All blocking risks resolved or explicitly accepted within an agreed scope; independent review where required|
|H: V1 release|Explicit owner approval after G|Reviewed commit/tag, deployment plan, rollback and post-release verification; no release created by migration|

Each phase requires bounded requirements, frozen acceptance, relevant tests, security review, documentation and separately approved Git checkpoint/release actions. Existing 6.1B work is not a greenfield task and must not be overwritten. Standalone apps and CAD/BIM features remain outside V1.
