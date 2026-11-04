# Architecture decisions
|Decision|Evidence and rationale|Status|
|---|---|---|
|Reuse Open WebUI|Pinned upstream foundation provides model/workspace/chat/provider infrastructure; initial docs prefer native extensions over core changes|Existing; exact original selection deliberations not fully recovered|
|Brain as native workspace-model prompt|moriq/brain/build.py maps system prompt and selected base model into import JSON|Implemented; prompt is not a security boundary|
|Private drafts and deterministic public projection|Task 3 failures showed unsupported claims and public leakage; source_gate separates review output|Offline implemented; production reviewer identity pending|
|Hash-bound registry and exact applicability|Task 4 binds source bytes, roles, lifecycle and question context|Offline implemented; citation identity is not semantic correctness|
|Preserve exact evaluation bytes|.gitattributes corrections and 4.7 investigations protect frozen H15/runtime pins|Existing; historical restorations retained|
|Owner-led offline acceptance|Dated October 27 owner record adopts V12-OWNER-OFFLINE-v1|Narrow administrative acceptance; original V12 unmet|
|One migration repository, separate Studio folder|Knowledge contains Brain/registry/lifecycle plus unique 6.1 work; UI branch lacks Studio source|Migration decision; no code merge or import restructuring|
|Documentation-first organization|Moving functional src/backend/moriq paths would risk imports and behavior|Adopted for migration|

Future ADRs go under docs/decisions with a unique date/number, status, problem, evidence, considered options, decision, consequences, security/test impact and supersession links. Never rewrite a previous accepted record; add a superseding decision. A proposed ADR is not authorization.
