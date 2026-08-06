---
name: slide-system-free
description: Creates and revises consistent Japanese slide decks in resource-limited Claude sessions. Use for HTML/PDF presentations, proposals, reports, roadmaps, training material, and teaching material. Asks only blocking questions, requires explicit production approval, delivers a reviewable HTML draft first, and creates PDF only after the user's next request.
---

# Slide System Free

Create usable Japanese slides from ordinary, incomplete requests. Preserve correctness, readability, evidence, and the warm_clean design system. Save capacity by narrowing scope and splitting delivery, not by lowering quality.

## Non-negotiable turn gate

Before any tool call, classify the newest user message.

- If the previous assistant message asked a blocking question and the user has answered it, use no tools. Present the production conditions from step 3 and stop.
- If the user is discussing options, asking for an opinion, or suggesting a possible structure without explicitly approving production, use no tools. Give a recommendation and revised outline, then ask for approval.
- If production conditions were presented, begin production only after an explicit approval of those conditions.
- An answer to a question, a correction, a general acknowledgement, or “continue” before the production summary is not approval.
- After HTML delivery, treat changes to story order, page count, section grouping, timeline structure, or several repeated items as a material revision. Present the revised outline and wait for approval. A bounded wording, color, or single-element correction may proceed directly.

Do not reload this file during the same task. Before approval, do not open bundled references, inspect scripts, draft the content model, or perform broad research.

## Defaults

Apply explicit user instructions first. Otherwise:

- Japanese, self-contained slides, 16:9, warm_clean.
- HTML is the first deliverable. PDF is created in a later turn.
- Start with 6–8 slides. Increase the count whenever required content would otherwise become dense. Page count is an outcome, not a target.
- Use the bundled font, template, layouts, and scripts. Do not invent another framework or theme.
- Prefer diagrams, comparisons, tables, charts, and restrained shapes. Do not search for decorative images.
- Research only material claims. Prefer supplied material and authoritative primary sources.
- Set `delivery_profile: "staged"` in `work-state.json`.

## Workflow

### 1. Inspect and preflight

Open only the supplied files needed to understand the request. Infer audience, purpose, likely title, output, and important constraints.

Before approval, allow at most one official-fact lookup when a current date, organization, rule, product, or event fact is necessary to ask an accurate blocking question. Do not research the deck's substantive recommendations yet.

If existing HTML or PDF is supplied:

- Use current slide-system HTML as the editable source. Use PDF only as a visual reference.
- For a bounded correction, record `phase: "revision_approved"`, source artifact, requested scope, and the exact user request.
- For a material revision, present the revised outline and stop for approval.
- For older HTML without embedded data or PDF only, reconstruct a compact content model, present the intended reconstruction, and wait for approval.
- Never edit PDF independently. Revise HTML first.

### 2. Ask one blocking question and stop

Ask only when the missing answer changes safety, rights, factual accuracy, scope, or deliverables. Ask one concise question and stop. Set `phase: "questions_pending"`.

After the answer, follow the non-negotiable gate: no tools, present production conditions, and stop.

### 3. Present production conditions and stop

Present one compact confirmation containing:

- audience and intended use;
- title and date;
- proposed story and approximate page count;
- deliverables: HTML draft first, PDF after the user's next request;
- important assumptions, corrections, and safety or rights conditions;
- for repeated user-supplied items, the current state and the proposed decision: maintain, change, or stop.

End with explicit choices equivalent to “Create with this content” and “Revise the content”. Set `phase: "confirmation_pending"` and `approval.status: "pending"`, then stop.

After explicit approval, record `phase: "approved"`, `approval.status: "approved"`, and the exact reply in `approval.user_reply`.

### 4. Stage A: create and deliver HTML

In the approval turn:

1. Create `work-state.json` from approved conditions.
2. Read only the references needed for this deck:
   - `references/content.md`
   - `references/layouts.md`
   - `references/warm-clean.md`
   - `references/html-pdf.md`
   - `references/source-safety.md` only for researched, high-stakes, or rights-sensitive content
   - `references/visuals.md` only when a supplied or necessary visual is used
3. Verify the minimum necessary unstable or high-stakes facts.
4. Copy `assets/deck-schema-example.json` to the task directory and replace example content with the approved content.
5. Run `scripts/build_deck.py` with the approved `work-state.json`.
6. Save `deck.json`, `deck-draft.html`, static QA, and `work-state.json` in a user-accessible directory.
7. Deliver the HTML and stop.

Do not render screenshots, create a contact sheet, export PDF, or start a second correction cycle in Stage A.

Ask the user to review only three things:

1. story order and key conclusions;
2. wording, figures, tables, and sources;
3. assumptions, conditions, and next action.

### 5. Stage B: create PDF

Start only when the HTML has been delivered and the user requests PDF or continuation.

- Record `phase: "pdf_requested"` and the exact reply.
- Read only `work-state.json` and the existing HTML.
- Do not repeat research or rebuild content.
- Run `scripts/export_pdf.mjs`.
- Verify font loading, hidden navigation, 16:9 page size, and HTML/PDF page-count parity.
- Return the existing HTML and new PDF, then set `phase: "complete"`.

If conversion cannot finish, tell the user to open the HTML and use its PDF-save button or the browser's print-to-PDF function. Do not restart the deck.

## Resource budget

Preserve capacity for the HTML checkpoint.

- Use one grouped search with up to four precise queries and one grouped opening of up to four authoritative pages.
- Do not search separately for every slide or repeated item.
- If evidence is insufficient, omit the claim, use qualified wording, or mark it unresolved.
- Do not inspect builder source code in order to interpret a validation report.
- Do not narrate routine progress or paste source code and QA logs into chat.
- Save HTML before optional work.

## General content controls

These rules apply across topics. Do not embed rules for a single sample domain.

- Give each slide one communication job and one primary message.
- Use takeaway titles, not topic labels.
- Split a slide before shrinking type. A dense slide is a structure failure, not a font-size problem.
- For a multi-stage roadmap, show period, purpose, checkpoint, advance condition, hold condition, regression condition, and stop or review condition.
- Name a table or diagram for its actual scope. Do not present a subset as if it covers the whole plan.
- For repeated items, first use one overview matrix when readers need cross-item comparison. Add detail slides only where the proposal changes by period or needs explanation.
- Separate user-supplied current state from the recommendation. Show maintain/change/stop, proposal, rationale, and adjustment condition.
- If several items share the same time axis, combine them into a readable cross-axis table before creating repetitive one-item-per-period slides.
- Derived numbers must show their basis and limitation nearby.
- Match claim strength to evidence. Observational evidence supports association or inference wording, not causal wording.
- A dated roadmap must use exact ISO dates internally, show the exact remaining duration consistently, and avoid misleading rounding.
- Important assumptions or execution conditions must be visible on the slide they constrain, not only in hidden data or an appendix.
- If required content does not fit legibly, increase the page count. Never force a fixed slide count.

## High-stakes controls

For medical, legal, financial, safety, or other high-impact content:

- Record current condition or context, limitations, stop or review conditions, and unresolved assumptions.
- Create `claim_evidence` records before building. Each record needs visible claim text, slide, basis type, source IDs, support, evidence design, and claim strength.
- Put page-level source markers on every material claim or instruction.
- If execution depends on an unresolved condition, mark the plan provisional and show the clearance condition on the relevant slide.
- State practical limits and recommend a qualified professional when required.
- Do not hardcode domain prescriptions into the skill. Research and justify them for the current request.

## Layout and visual controls

- Use at least two layout families in decks of six or more slides.
- Do not allow four consecutive text-only or decoration-only content slides.
- Use meaningful visuals for evidence, explanation, comparison, sequence, hierarchy, or decisions.
- Do not fill empty space with unrelated decoration.
- Use solid warm_clean colors. Do not use gradients.
- Keep text within safe margins and retain minimum type sizes.
- Make source appendices compact but readable.

## Completion

The HTML stage is complete only when the downloadable HTML exists and static validation has no failures. The PDF stage is complete only when PDF exists and the required parity checks pass. If unfinished, preserve the latest artifacts and exact next action in `work-state.json`; never claim completion.
