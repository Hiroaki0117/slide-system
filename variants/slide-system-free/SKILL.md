---
name: slide-system-free
description: Creates and revises consistent Japanese slide decks within resource-limited Claude sessions. Use when a free-plan or short-session user asks for slides, presentations, HTML/PDF decks, proposals, reports, roadmaps, training material, or teaching material and needs a downloadable artifact before the session limit. Delivers a compact HTML draft first, stops, then produces the PDF and final QA only after the user's next reply.
---

# Slide System Free

Create usable Japanese slides from ordinary, incomplete requests while guaranteeing an early downloadable checkpoint. Preserve the same factual, safety, typography, and layout standards as the full skill; reduce scope and split delivery instead of lowering correctness.

## Core behavior

- Treat short, non-expert input as normal. Infer safe defaults and ask only questions that materially change safety, rights, factual accuracy, scope, or deliverables.
- Separate a blocking question, production approval, HTML delivery, and PDF delivery into distinct turns.
- Never treat an answer to a question, a correction, or `続けてください` before the production summary as approval.
- Do not expose internal labels or narrate routine tool activity.
- Do not paste source code or detailed QA logs into chat.
- Keep the newest `deck.json`, `work-state.json`, HTML, PDF, renders, and QA reports in a user-accessible task directory.
- Treat an existing artifact as a revision source, not automatically as a request for a new deck. Follow `references/html-pdf.md` for HTML/PDF recovery.
- Set `delivery_profile: "staged"` in `work-state.json` from preflight through completion.

## Mandatory turn gate — highest priority

Before every tool call, classify the conversation from the immediately preceding assistant action. This gate overrides every later workflow or reference instruction.

If the preceding assistant message asked a blocking question and the user's newest message answers it:

1. Do not call any tool. Do not search the web, open files, run code, create files, reload this skill, or read a reference.
2. Do not research, calculate recommendations, build the content model, or design the training plan internally.
3. Using only the request, already inspected material, and the new answer, present the compact production conditions from step 3 and end the turn.
4. If the answer itself reveals one new blocking uncertainty, ask only that one follow-up question and end the turn, still without tools.

The next visible assistant response after a blocking answer must therefore be either another single blocking question or the production conditions. Any intervening tool call is a workflow failure.

If the preceding assistant message presented production conditions, accept only an explicit choice approving or revising those conditions. Do not treat a question answer, `続けてください`, or a general acknowledgement from an earlier turn as approval.

Do not explicitly reopen or reload `SKILL.md` during the same task. Do not read bundled references before production approval; route to the minimum required references once during Stage A.

## Free-plan defaults

- Use self-contained slides, `warm_clean`, Japanese, and 16:9 unless the user explicitly supplies another template or format.
- Create 6–8 slides. Use up to 10 only when the user's required content cannot be represented safely in 8.
- Use the bundled layouts, font, template, and scripts. Do not create a new framework or custom theme.
- Prefer diagrams, tables, charts, and restrained shapes. Do not search for or generate decorative images unless the user explicitly requests them or supplies them.
- Research only claims needed for the deck. Normally use 2–4 authoritative sources, prioritizing supplied material, official sources, recognized clinical guidance, and primary research. Add more only when safety or factual coverage requires it.
- Deliver HTML first and PDF in the next turn even when both were requested initially. State this staged delivery in the production confirmation.

After explicit production approval, read each needed reference at most once and store decisions in `work-state.json`.

For a dated, high-stakes exercise roadmap, use the compact roadmap builder in Stage A. This specialized path is self-contained and overrides the reference-reading list below: do not open bundled references, scripts, the HTML template, or the font before the first HTML is saved. The adapter expands the compact brief into the same full validation model and runs the unchanged strict validator.

- Read `references/content.md`, `references/layouts.md`, and `references/warm-clean.md` once for a new default-theme deck.
- Read `references/source-safety.md` once for research, health, legal, financial, safety, or rights-sensitive claims.
- Read `references/html-pdf.md` once before building. The staged workflow below overrides its instruction to continue immediately from HTML to rendering.
- Read `references/visuals.md` only when a supplied or necessary visual is used.
- Read `references/pptx.md` only when PowerPoint is explicitly requested; explain that PPTX may require more turns.

## Workflow

### 1. Inspect and preflight

Open supplied files once, infer audience and purpose, and check output capability. Before approval, do not design the detailed story or research content topics. Allow at most one official-fact lookup only when an event, date, organization, or current rule must be verified to ask the blocking question or state accurate production conditions. Do not search medical treatment, training methods, tapering, nutrition, formulas, or other slide content before approval.

If existing HTML or PDF is supplied, classify it before the new-deck workflow:

- Recover `deck.json` from a current slide-system HTML. If PDF is also present, use HTML as the editing source and PDF as the visual reference.
- For a specific, bounded correction, the user's correction request authorizes only that correction. Set `phase: "revision_approved"` and record `revision.source_artifact`, `revision.scope`, and the exact request in `revision.user_reply`; do not repeat the full production confirmation or research unrelated claims.
- For an older HTML without embedded data or PDF only, inspect and reconstruct first, present a compact reconstruction plus requested changes, and stop for confirmation before production.
- Never edit the PDF independently. Revise HTML first and offer PDF in the next turn.

### 2. Ask a blocking question and stop

If a missing answer changes safety, rights, factual accuracy, scope, or deliverables, ask only that question and stop. Set `phase: "questions_pending"`. For an injury history, ask whether pain is currently present before proposing an individualized plan.

After the answer, apply the mandatory turn gate: use no tools, present production conditions, and stop. Keep the phase conversational until approval; do not spend a tool call merely to write `work-state.json`.

### 3. Present production conditions and stop

Present one compact confirmation containing:

- audience and intended use;
- proposed title, date, 6–8 slide story, and important assumptions;
- `まずHTML下書きを納品し、次の返信でPDF化と最終確認を行う`;
- safety or rights conditions already resolved;
- the choices `この内容で制作する` and `内容を修正する`.

Set `phase: "confirmation_pending"` and `approval.status: "pending"`, then stop. Only explicit approval of these conditions counts.

After approval, record `phase: "approved"`, `approval.status: "approved"`, and the user's exact reply in `approval.user_reply`. An explicit waiver may use `approval.status: "waived"` with the exact waiver reply.

### 4. Stage A: build and deliver HTML, then stop

In this turn only:

1. Create `work-state.json` from the approved conditions and exact user replies. Then verify only the minimum necessary unstable and high-stakes facts.
2. For a dated high-stakes exercise roadmap, copy `assets/free-roadmap-brief-example.json`, replace its example values with the approved facts and minimum verified sources, and run `scripts/build_free_roadmap.py` once. Treat the script as an opaque executable: never open or inspect any `.py`, `.mjs`, template HTML, bundled font, or generated full `deck.json` before returning the first HTML.
3. For other deck types, start from a compact 6–8 slide content model and run the standard static builder. Use 9–10 slides when required content cannot fit legibly, and exceed 10 when splitting is still necessary at the minimum type size. Slide count is the result of fitting one primary message per slide, never a fixed target. Do not rely on a later correction turn to add essential content.
4. Save `deck-draft.html`, `deck.json`, static QA, and `work-state.json` in the user-accessible output directory. The compact builder must create HTML whether its report says `PASS` or `DRAFT`.
5. Confirm that the HTML navigation includes `PDF保存`. Set `phase: "html_delivered"`, store the HTML path, and set the next action to `PDF化`.
6. Return the HTML draft, then copy the compact builder's `user_review_points` into the response as three short confirmation points. Ask the user to check the proposed distances, recurring-session intensity, and start/stop conditions; do not automatically rewrite those content decisions. Then stop the turn.

If the compact builder reports `DRAFT`, return that HTML immediately and say it is a visible, non-executable validation draft. Its PDF button is disabled. Ask only for the correction needed by the report; do not offer or create PDF. Do not inspect source code, rebuild, research again, or retry in the same turn. A `DRAFT` is not completion; its banner and QA report preserve the unresolved issue for the next chat or turn.

Do not run `render_deck.mjs`, create screenshots, export PDF, or start visual correction in Stage A. Do not use remaining capacity to continue automatically.

The Stage A response must clearly say that the HTML is a usable draft, identify the three user review points, and explain that PDF確認 remains. The user can reply naturally with a correction or `PDFもお願いします`, or use the HTML's `PDF保存` button if the session limit is near.

### Stage A tool budget

Preserve capacity for the downloadable HTML.

- Reuse supplied facts and any official event fact already verified during preflight.
- Use at most one grouped web-search operation with up to four precise queries, followed by at most one grouped source-opening operation with up to four authoritative pages.
- Prefer an official event page, a recognized clinical guideline, a primary or peer-reviewed taper source, and a recognized endurance-nutrition consensus when those topics are material.
- Do not open commercial clinic, product, coaching-blog, calculator, or search-summary pages when an official, clinical, or primary source is available.
- Do not research race-prediction formulas unless the user explicitly requests a prediction. A current-versus-target pace comparison can be calculated directly and labelled with its limitation.
- Do not run separate searches for every slide or every weekly distance. Treat an individualized weekly schedule as a conditional proposal based on confirmed baseline and recovery, not as a sourced universal rule.
- Do not inspect builder or validator source code to understand a report. Use the report code and return the generated HTML checkpoint first.
- If the budget cannot support a claim, omit the claim, use non-numeric conditional wording, or mark it unresolved. Do not continue searching and risk losing the HTML checkpoint.
- Do not emit routine progress narration. Save the HTML before any optional work.

### 5. Stage B: fast PDF export and delivery

Start only after Stage A has delivered the HTML and the user asks to continue or create the PDF. Record `phase: "pdf_requested"` and the exact reply in `pdf_request.user_reply`.

1. Read only the existing `work-state.json` and HTML path needed for conversion. Do not reread source material, research, recover the model, rebuild content, or re-evaluate the story.
2. Pass `work-state.json` to `scripts/export_pdf.mjs`. It must reject `html_delivered` or a missing `pdf_request.user_reply`.
3. Export the full PDF before screenshots or contact-sheet work. Verify bundled-font loading, hidden navigation controls, 16:9 page size, and HTML/PDF page-count parity.
4. Return the existing HTML and newly created PDF immediately after these checks. Set `phase: "complete"` and give only a concise conversion result.

Do not run `render_deck.mjs`, create per-page screenshots, make a contact sheet, repeat research, or alter slide content before the downloadable PDF exists. Full visual QA is an optional later `仕上げQA` turn, not a prerequisite for free-plan PDF delivery.

If code execution cannot finish, do not restart production. Tell the user to open the delivered HTML and choose `PDF保存`, or use Chrome/Edge `Ctrl+P` and select `PDFに保存`. A new chat may also receive the HTML with `内容は変えずPDF化のみ`.

Never export a PDF from HTML that contains the `検証未完了ドラフト` banner. `export_pdf.mjs` must reject it with `DRAFT_NOT_APPROVED`; manual PDF fallback applies only to a validated HTML whose `PDF保存` button is enabled.

Never claim PDF conversion completion if PDF generation, page-count parity, font loading, hidden controls, or 16:9 page size remain unresolved. Content, sources, overflow, title wrapping, and layout-specific text density must already have passed Stage A static/HTML checks; do not spend the PDF-only turn redoing them.

## Content and safety controls

- Match claim strength to evidence. Treat formulas, calculators, benchmarks, and single past results as estimates, not guarantees.
- Put assumptions and the main limitation beside a derived number.
- For progressive roadmaps, show starting, progression, recovery, regression, and stop or consultation conditions.
- For high-stakes claims, create `claim_evidence` records before building. Each record must name the visible claim text, slide, basis type, source IDs, and exactly what the source supports. A source title or nearby citation is not evidence that the source supports the recommendation.
- Record `evidence_design` and `claim_strength`. Observational evidence may support association or inference wording, not causal improvement wording.
- For a date-driven roadmap, set `dated_roadmap: true`, calculate the exact remaining days from ISO dates, and show one consistent natural rounding such as `88日（約13週間）`. Do not shorten 12 weeks and 4 days to `約12週間`.
- For progressive exercise roadmaps, include `safety.phase_guidance`. Every phase needs its period, a numeric long-session distance or time guide, purpose, checkpoint, progression condition, hold or regression condition, and the slide number where the period and load guide are visibly shown.
- A fixed single prescription is prohibited, but omission of load guidance is also prohibited. Use conditional ranges, an explicit current-load ceiling, or time ranges. Do not replace them with only `少しずつ延ばす`.
- For exercise roadmaps, show the pace or effort, purpose, adjustment condition, intensity class, and basis for every recurring session type. Include long-session pace explicitly and distinguish it from goal-pace practice.
- Record each recurring session's `basis_type`, `source_ids`, and slide. If a pace is not user-confirmed or directly supported, use effort or talk-test wording instead of inventing a numeric range.
- A `user_confirmed` session value needs `confirmation_quote` copied exactly into `work-state.confirmed_conditions`. A calculated target pace may be shown as a comparison, but calculation alone cannot prescribe a recurring workout pace.
- For a beginner or return-from-injury plan, set `safety.novice_or_returning: true`, keep at least one recurring session explicitly easy or recovery-oriented, and normally use no more than one quality session per week.
- Do not invent a numeric workout pace from distance and frequency alone. Use a user-confirmed pace, a traceable calculation or authoritative source, or an effort/talk-test range marked provisional.
- When an official result uses gun time, distinguish gross and net goals in the production conditions and final deck. Include official start, cutoff, and timing basis when they affect the requested outcome.
- For event preparation, record official event facts and course implications from official sources, include an explicit recovery phase, and use a 14–21 day taper unless a directly supporting source and confirmed circumstances justify another range.
- When current and target performance are comparable, show both values in the same unit, the comparison basis, and the meaning of their difference on the same slide.
- In the compact roadmap brief, separate each comparison into `current_label`, `current_metric`, `current_note`, `target_label`, `target_metric`, and `target_note`. Keep a large metric to 18 characters or fewer; never put a label, number, parenthetical explanation, and conclusion in the same large-text field.
- For a dated event roadmap, list every remaining week's long-session distance or time, period, execution condition, and recovery-week flag. Phase endpoints alone are insufficient.
- When a current injury symptom is present or unknown, label the plan visibly as provisional, show sourced pre-clearance actions, and put a visible post-clearance execution condition on every phase and recurring session. Do not place unconditional running instructions elsewhere.
- A race strategy with three or more stages must use a process, comparison, table, chart, or decision visual. A short bullet list with unused space is not sufficient.
- In a `process` slide, keep the lead to 120 characters or fewer and move supporting details into the relevant steps. Do not repeat the same sentence as both a step title and body. For event strategy, keep labels within 30 characters, step titles within 46, and bodies within 72. In a `data_focus` slide, keep the lead, interpretation, and execution condition to 80 characters or fewer each.
- For repeated recurring sessions, keep one shared execution condition instead of repeating it in every row. If any overview row exceeds 90 characters or the three-row cell total exceeds 180, let the compact builder create one short overview and one detail slide per session. Do not force the detail-slide count when the compact table already fits.
- Event preparation needs at least three visible race segments plus fueling, equipment, and rehearsal. An official-facts table alone is not a race strategy. State whether the goal uses gross or net time and note any start-line buffer implication.
- Do not use slide count as a reason to omit current-versus-target comparison, recovery periods, event-specific constraints, or final-use preparation such as pacing, fueling, equipment, and rehearsal when they affect the requested outcome.
- Do not use a slide-count ceiling as a reason to retain dense copy. Remove duplication first, then split overview from detail while preserving all required evidence and safety conditions.
- Use source IDs such as `[S1]` on claim and instruction slides and ensure every ID resolves to one complete appendix entry. Do not put a publisher in a page footer unless that exact source appears in the appendix.
- Every page-level source ID must map to evidence recorded for that same page. A source that merely exists in the appendix cannot support an unrelated training, safety, or taper claim.
- For high-stakes decks, set `high_stakes: true` and provide the required safety model and sources before building.
- Do not reduce source quality, minimum type size, contrast, safe margins, or final factual checks to save resources.

## Completion

Stage A is a deliberate checkpoint, not final completion. The overall task is complete only after the requested final formats exist and the mandatory final checks pass. If a limit interrupts work, return the newest downloadable artifact and the single next action instead of restarting.
