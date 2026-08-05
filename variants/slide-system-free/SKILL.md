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

## Free-plan defaults

- Use self-contained slides, `warm_clean`, Japanese, and 16:9 unless the user explicitly supplies another template or format.
- Create 6–8 slides. Use up to 10 only when the user's required content cannot be represented safely in 8.
- Use the bundled layouts, font, template, and scripts. Do not create a new framework or custom theme.
- Prefer diagrams, tables, charts, and restrained shapes. Do not search for or generate decorative images unless the user explicitly requests them or supplies them.
- Research only claims needed for the deck. Normally use 2–4 authoritative sources, prioritizing supplied material, official sources, recognized clinical guidance, and primary research. Add more only when safety or factual coverage requires it.
- Deliver HTML first and PDF in the next turn even when both were requested initially. State this staged delivery in the production confirmation.

Read each needed reference once and store decisions in `work-state.json`.
Read `references/content.md` for narrative, audience, density, cover, and ending.
Read `references/layouts.md` before assigning layouts.
Read `references/warm-clean.md` when using the default theme.
Read `references/source-safety.md` for research, health, legal, financial, safety, or rights-sensitive claims.
Read `references/visuals.md` only when a supplied or necessary visual is used.
Read `references/html-pdf.md` before building. The staged workflow below overrides its instruction to continue immediately from HTML to rendering.
Read `references/pptx.md` only when PowerPoint is explicitly requested; explain that PPTX may require more turns.

## Workflow

### 1. Inspect and preflight

Open supplied files, infer audience and purpose, choose the smallest sufficient story, and check output capability. Before approval, allow only the minimum lookup needed to identify material, verify an event or date, or form accurate production conditions.

If existing HTML or PDF is supplied, classify it before the new-deck workflow:

- Recover `deck.json` from a current slide-system HTML. If PDF is also present, use HTML as the editing source and PDF as the visual reference.
- For a specific, bounded correction, the user's correction request authorizes only that correction. Set `phase: "revision_approved"` and record `revision.source_artifact`, `revision.scope`, and the exact request in `revision.user_reply`; do not repeat the full production confirmation or research unrelated claims.
- For an older HTML without embedded data or PDF only, inspect and reconstruct first, present a compact reconstruction plus requested changes, and stop for confirmation before production.
- Never edit the PDF independently. Revise HTML first and offer PDF in the next turn.

### 2. Ask a blocking question and stop

If a missing answer changes safety, rights, factual accuracy, scope, or deliverables, ask only that question and stop. Set `phase: "questions_pending"`. For an injury history, ask whether pain is currently present before proposing an individualized plan.

After the answer, do not start research or production and do not infer approval.

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

1. Verify the minimum necessary unstable and high-stakes facts.
2. Create a compact 6–8 slide content model with one job and one primary claim per slide. Before compressing, list the mandatory coverage and confirm that none is lost; use 9–10 slides when safety, source traceability, phase-specific load guidance, or the user's decision criteria do not fit legibly in 8. Do not rely on a later correction turn to add essential content.
3. Run the bundled static builder with `--work-state`. Resolve every static `FAIL` in one batch.
4. Save `deck-draft.html`, `deck.json`, static QA, and `work-state.json` in the user-accessible output directory.
5. Set `phase: "html_delivered"`, store the HTML path, and set the next action to `PDF化と最終QA`.
6. Return the HTML draft to the user and stop the turn.

Do not run `render_deck.mjs`, create screenshots, export PDF, or start visual correction in Stage A. Do not use remaining capacity to continue automatically.

The Stage A response must clearly say that the HTML is a usable draft, visual/PDF QA remains, and the user can reply naturally with `PDFもお願いします` or `続けてください`.

### 5. Stage B: render, correct, and deliver PDF

Start only after Stage A has delivered the HTML and the user asks to continue or create the PDF. Record `phase: "pdf_requested"` and the exact reply in `pdf_request.user_reply`.

1. Read the existing `work-state.json`, `deck.json`, and HTML first. Do not repeat research or rebuild from scratch.
2. Pass `work-state.json` to the bundled renderer. The renderer must reject `html_delivered` or a missing `pdf_request.user_reply`.
3. Run the bundled renderer once to test navigation and font loading, render all slides and a contact sheet, and export PDF.
4. Inspect the contact sheet and all detected failures. Make one consolidated correction batch, then rerun the affected validation.
5. If another correction batch is necessary, save current artifacts and state, return the newest files as incomplete drafts, and stop. Resume on the next user reply.
6. When all mandatory checks pass, set `phase: "complete"` and return the final HTML and PDF with a concise QA result.

Never claim completion if PDF generation, page-count parity, font loading, overflow, title wrapping, sources, or mandatory safety checks remain unresolved.

## Content and safety controls

- Match claim strength to evidence. Treat formulas, calculators, benchmarks, and single past results as estimates, not guarantees.
- Put assumptions and the main limitation beside a derived number.
- For progressive roadmaps, show starting, progression, recovery, regression, and stop or consultation conditions.
- For high-stakes claims, create `claim_evidence` records before building. Each record must name the visible claim text, slide, basis type, source IDs, and exactly what the source supports. A source title or nearby citation is not evidence that the source supports the recommendation.
- For a date-driven roadmap, set `dated_roadmap: true`, calculate the exact remaining days from ISO dates, and show one consistent natural rounding such as `88日（約13週間）`. Do not shorten 12 weeks and 4 days to `約12週間`.
- For progressive exercise roadmaps, include `safety.phase_guidance`. Every phase needs its period, a numeric long-session distance or time guide, purpose, checkpoint, progression condition, hold or regression condition, and the slide number where the period and load guide are visibly shown.
- A fixed single prescription is prohibited, but omission of load guidance is also prohibited. Use conditional ranges, an explicit current-load ceiling, or time ranges. Do not replace them with only `少しずつ延ばす`.
- For exercise roadmaps, show the pace or effort, purpose, adjustment condition, intensity class, and basis for every recurring session type. Include long-session pace explicitly and distinguish it from goal-pace practice.
- Record each recurring session's `basis_type`, `source_ids`, and slide. If a pace is not user-confirmed or directly supported, use effort or talk-test wording instead of inventing a numeric range.
- For a beginner or return-from-injury plan, set `safety.novice_or_returning: true`, keep at least one recurring session explicitly easy or recovery-oriented, and normally use no more than one quality session per week.
- Do not invent a numeric workout pace from distance and frequency alone. Use a user-confirmed pace, a traceable calculation or authoritative source, or an effort/talk-test range marked provisional.
- When an official result uses gun time, distinguish gross and net goals in the production conditions and final deck. Include official start, cutoff, and timing basis when they affect the requested outcome.
- For event preparation, record official event facts and course implications from official sources, include an explicit recovery phase, and use a 14–21 day taper unless a directly supporting source and confirmed circumstances justify another range.
- When current and target performance are comparable, show both values and the meaning of their difference on the same slide.
- When a current injury symptom is present or unknown, label the plan visibly as provisional and put the clearance condition before the training schedule.
- A race strategy with three or more stages must use a process, comparison, table, chart, or decision visual. A short bullet list with unused space is not sufficient.
- Do not use slide count as a reason to omit current-versus-target comparison, recovery periods, event-specific constraints, or final-use preparation such as pacing, fueling, equipment, and rehearsal when they affect the requested outcome.
- Use source IDs such as `[S1]` on claim and instruction slides and ensure every ID resolves to one complete appendix entry. Do not put a publisher in a page footer unless that exact source appears in the appendix.
- For high-stakes decks, set `high_stakes: true` and provide the required safety model and sources before building.
- Do not reduce source quality, minimum type size, contrast, safe margins, or final factual checks to save resources.

## Completion

Stage A is a deliberate checkpoint, not final completion. The overall task is complete only after the requested final formats exist and the mandatory final checks pass. If a limit interrupts work, return the newest downloadable artifact and the single next action instead of restarting.
