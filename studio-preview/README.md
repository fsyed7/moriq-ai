# MORIQ AI — local fixture preview

## Current behavior — Task 5.3

The approved welcome photo is unchanged. Enter Workspace resumes the selected fixture chat; Welcome returns to landing. New Chat, saved-chat selection, rename and confirmed deletion are available. Direct links use `#conversation/fx-…`; legacy project links remain supported.

Only completed scripted scenario codes are saved, never raw typed prompt/answer text. Refresh reconstructs canonical fixture messages. Use fictional names only. Limits: 12 chats, 40 turns/chat, 60-character titles and a 64 KiB versioned local store. Storage is browser/origin-specific, without a backend. See [storage contract](../task-5.3-storage-contract.md), [acceptance report](../task-5.3-acceptance-report.md) and [test results](../task-5.3-test-results.md). Earlier sections below describe historical tasks and their then-current behavior.

Run `npm run dev` (or `node server.mjs`) from this folder. Open http://127.0.0.1:5175. Responsive review: http://127.0.0.1:5175/review.html#mobile (390px), #tablet (768px), or #desktop (1280px). The page itself responds to any browser width. Place the browser in Codex's right pane; alternatively open the address in a browser and use Windows Snap (Win + Left/Right) beside Codex.

CSS saves update the stylesheet in place. HTML, JS and fixture saves automatically reload the page; scripted conversation state resets on reload. Restart the process after changing server.mjs. Stop with Ctrl+C. No install or build is required. Run `npm test` while the server is running.

## Scope and provenance

This isolated prototype uses vanilla HTML/CSS/JS and Node's standard-library HTTP server. The inspected Open WebUI Svelte/Vite config includes API, model, OAuth and WebSocket backend proxies; it is intentionally not reused. No dependency installation, repository edits, commits, pushes or deployment are required. No .env or real document files are read. The server binds only to 127.0.0.1:5175 and serves an explicit file allowlist; it has no proxy or inference endpoints. The only browser network traffic is local static assets and the local save-notification event stream.

Read before implementation: TASK_5_SCOPING_HANDOFF.md and UI01–UI10 in task-4.7-handoff-plan.md from the earlier Task 4 outputs, plus ../task-5.1-moriq-visual-identity.md. No standalone finalized Task 5.1 design-system/IA documents were found. The handoff provides the provisional three-panel IA, and the addendum provides provisional charcoal, warm metal, vegetation tones, material restraint and architectural framing. System fonts only; editorial serif headings are a prototype choice, not an official MORIQ font. The current user request authorizes this isolated prototype beyond the earlier research-only stop condition.

Demo Residence 01, Demo Studio 02 and Demo Pavilion 03 are fictional, not asserted MORIQ projects. Villa 430, Courtyard Villa and Amwaj Villa are genuine portfolio references appearing only as clearly labeled image placeholders. No photography or logo artwork is included or licensed. The MORIQ AI masthead is plain text. Decorative references and fixture content are not ingested or indexed.

## Review interactions

- Select a fictional project; start a new conversation.
- Choose a suggested prompt or type a message (Enter sends; Shift+Enter adds a line). Every reply is explicitly scripted, regardless of the question.
- Open citation 01 to inspect the fictional design note.
- Change among sample passage, no sources, scope gap, identity mismatch, unavailable and simulated access removal. Non-passage states clear both excerpt and inspector text and disable the citation button.
- On mobile, Projects and Evidence open labeled panels; use their close buttons or Escape. Panels are nonmodal and do not claim to provide authentication.

The sample citation has a fixed demo ID and revision. Hash remains “Not computed”; jurisdiction/edition are not applicable; claim status is not assessed; release is never allowed. No Unicode span highlighting, authority DTO parsing, upload, approval or export operation is implemented.

## Validation boundary

check.mjs verifies fixture invariants, the six display states, absence of HTML injection sinks and provider calls, static route allowlisting, same-origin CSP and rejected backend routes. Browser checks cover representative desktop/mobile layouts and the scripted flows. This is not the full historical UI01–UI10 acceptance suite, a screen-reader audit, or production validation. Those frozen cases remain unchanged. Real authentication, RAG, source validation, permissions and model behavior are untested and disconnected by design.

## Completed checks for this preview

- Node syntax checks and `node check.mjs`: passed.
- Save-notification check: saving CSS emitted a stylesheet-update event; CSS is replaced in place without clearing conversation state. Browser reload during development also showed updated markup.
- Browser inspection: desktop 1280px and mobile 390px layouts rendered; responsive review preserves the selected layout width and scales it to the available Codex pane.
- Mobile flow: suggested prompt produced a labeled scripted response; citation opened the inspector; simulated access removal cleared the passage and disabled its citation; Escape closed the inspector and returned focus; project selection changed the fictional workspace and reset the conversation.
- Desktop and mobile screenshots are saved one folder above this preview. Mobile screenshot shows the upper viewport; scroll the live preview to use the composer.

The dev server is intentionally left running for review. Its lifetime depends on the local Codex session; rerun the command above if the address becomes unavailable. No protected source, frozen evidence or existing application file was changed.

## 27 October 2026 — minimal architectural redesign

Updated the same preview in place. Replaced the dashboard-like welcome with a centered chat column, monochrome charcoal/concrete/off-white palette, sharp borders and strong sans-serif headings. Reduced suggestions to two text links and architectural imagery to a small labeled Courtyard Villa placeholder. The wordmark remains plain MORIQ AI text because an official logo master has not been supplied.

The 210px project sidebar collapses at desktop widths and becomes a closed-by-default drawer on mobile. Evidence is closed on initial load at all widths and is revealed through Evidence or a citation. New conversations return to the welcome view with evidence closed. No production connection or Task 3/4 changes.

Validation: syntax and existing isolation checks passed; CSS save notification passed; browser inspection confirmed desktop and mobile welcome layouts, scripted chat, citation opening, Escape dismissal and desktop sidebar collapse. This does not constitute a full accessibility audit. Screenshots: ../moriq-redesign-desktop.png, ../moriq-redesign-mobile.png and ../moriq-redesign-chat.png. Desktop captures show the 1280px layout scaled to the available Codex pane.


## Task 5.2C final continuation

The root now shows the Task 5.1 editorial Courtyard Villa arrival using a labeled CV-01 placeholder (photo rights and official logo still pending). Enter Workspace opens `/#workspace`. Direct fixture links `/#conversation/F-01`, `/#conversation/F-02`, `/#conversation/F-03` select existing fictional workspaces. Reload/navigation starts an empty in-memory conversation; no persistence or backend routes were added. Unknown hashes return to arrival with a status.

Desktop sidebar is now 188px. Native full-size arrival and workspace captures at 1280/768/390/320 are in the parent outputs folder. Actual 200% browser zoom remains blocked; 640px reflow is supplementary only. See the Task 5.2C visual, responsive, interaction and accessibility reports. No build or lint scripts are configured; `npm test` and Node syntax checks pass. The server remains local with save notifications.
