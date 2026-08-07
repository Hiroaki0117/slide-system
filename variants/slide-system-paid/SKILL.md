---
name: slide-system-paid
description: Creates and revises production-quality Japanese slide decks by faithfully applying the bundled 00-60 slide specifications. Use for HTML/PDF or PPTX/PDF proposals, reports, explainers, roadmaps, training material, and teaching material when full research, complete visual QA, iterative correction, and resumable work are required.
---

# Slide System Paid

Create finished slide deliverables from ordinary, incomplete requests. Treat the bundled 00-60 specifications as the canonical contract. Optimize repeated work, not quality or required QA.

## Canonical contract

Use these files as the source of truth:

1. `references/00_MASTER.md`: priority, inputs, approval, workflow, and completion
2. `references/10_CONTENT.md`: audience, story, density, sources, and endings
3. `references/20_DESIGN.md`: theme, typography, color, spacing, and accessibility
4. `references/30_LAYOUTS.md`: layout selection, capacity, and overflow handling
5. `references/40_VISUALS.md`: photos, illustrations, diagrams, charts, tables, and rights
6. `references/50_OUTPUTS.md`: HTML, PPTX, PDF, naming, conversion, and format checks
7. `references/60_QA.md`: gates 0-5, full-page inspection, correction loop, and completion

Apply the priority order in `00_MASTER.md`. An explicit user instruction wins when it is a clear intentional exception. Never silently relax a `MUST` rule, change the requested output, or substitute a required asset.

Read each canonical file completely at most once per task. Before approval, read only the files required for preflight and confirmation. After approval, read every remaining file relevant to the selected output profile. Record loaded specifications and decisions in `work-state.json`; do not reread unchanged files.

The shorter helper references remain implementation aids. When they differ from a canonical 00-60 file, follow the canonical file.

## Non-negotiable approval gate

Before any production tool call, classify the newest user message.

- Inspect supplied inputs and run Gate 0 only far enough to identify blocking problems and available output capabilities.
- Ask only questions whose answers materially change safety, rights, factual accuracy, scope, or deliverables. Ask the necessary question and stop.
- Do not mix a missing-information question with production approval.
- After questions are resolved, present one compact production confirmation and stop.
- Include audience, purpose, title, date, story direction, approximate page count, output profile, assumptions, supplied-asset treatment, and material safety or rights conditions.
- Begin production only after explicit approval of those conditions. An answer, correction, acknowledgement, or request to continue research is not approval.
- Record the exact approval reply in `work-state.json`. Pass that file to every production script.

Before approval, do not perform broad research, create the content model, build HTML or PPTX, render pages, or export PDF.

## Production workflow

### 1. Establish resumable state

Create a task-local working directory and a user-accessible output directory. Save:

- `work-state.json` with approval, confirmed conditions, loaded specs, paths, completed steps, remaining steps, and failures;
- `deck.json` or the editable PPTX source model;
- source records and unresolved assumptions;
- static, render, and final QA reports.

If a later session receives existing artifacts, read `work-state.json` first. Recover the editable model from current slide-system HTML when necessary. Use PDF as a visual reference, never as the independent editing source. Preserve unaffected content and do not repeat completed research.

### 2. Research and content design

After approval, verify unstable and material claims. Prefer user-supplied material and first-party authoritative sources. Apply claim-level evidence requirements even when the whole deck is low-risk.

Define the deck type, content mode, audience profile, one deck-level communication goal, and one job and primary message per slide. Split before shrinking type. Let page count follow the content. Keep assumptions and execution conditions visible on the affected slide.

Create the complete content model before rendering. Check story order, claim strength, exact dates and calculations, source coverage, title length, density, repeated-item structure, and the ending.

### 3. Design and visual planning

Apply the confirmed template or brand first; otherwise use `warm_clean`. Select layouts from the slide job and primary material. Use meaningful photos, maps, diagrams, charts, tables, screenshots, or illustrations when they improve evidence, explanation, context, comparison, or action.

Do not add decorative images to fill space. Do not use gradients in `warm_clean`. Treat repeated layout warnings as design work: vary the visual grammar unless an exact shared frame improves comparison, and record the reason.

### 4. Build the requested primary format

For `html_pdf` or `html_only`:

1. Use `assets/deck-schema-example.json`, the bundled font, and `assets/deck-template.html`.
2. Run `scripts/build_deck.py` with approved `work-state.json`.
3. Resolve every static `FAIL` and review every `WARN`.
4. Save a draft HTML checkpoint before expensive visual work.

For `pptx_pdf` or `pptx_only`, follow the canonical output specification and `references/pptx.md`. Keep text, tables, charts, and simple shapes editable when possible. If the environment cannot generate, convert, or inspect the requested format, stop at Gate 0 with a recommended option and alternatives.

### 5. Run full visual QA

Do not use the staged `export_pdf.mjs` path for a normal paid production run. For HTML/PDF, set the approved non-staged workflow to `phase: "qa"` and run `scripts/render_deck.mjs` to render every HTML slide, create a contact sheet, and generate PDF.

Inspect, rather than merely generate:

1. the contact sheet for story, rhythm, and consistency;
2. every HTML slide at readable size for text, hierarchy, overlap, crop, source, page number, and visual accuracy;
3. every PDF page after conversion for the same items and HTML/PDF parity;
4. navigation, font loading, 16:9 dimensions, page count, print backgrounds, and hidden control UI;
5. every table, chart, number, unit, label, image crop, and source marker on its relevant page.

Use the available PDF renderer or inspection capability for all PDF pages. If no such capability exists, Gate 0 cannot pass for a PDF deliverable; propose HTML-only or a user-approved alternative rather than claiming completion.

### 6. Correct until PASS

Collect findings into one correction batch. Fix the editable source, rebuild, and rerender affected and related pages. Regenerate derivative formats from the corrected primary source. Then rerun whole-deck and all-format QA.

Repeat without a fixed iteration limit until every required item is `PASS` or has a justified `N/A`. Do not convert `NOT_VERIFIED` into `PASS`. Resolve safe `WARN` items; document only deliberate tradeoffs.

### 7. Deliver

Rename draft artifacts to final names only after Gate 5 passes. Return the requested files, slide count, output profile, final QA result, and any deliberate warning or constraint. Do not paste code, internal logs, or the full checklist unless requested.

If interrupted, preserve the newest draft, QA state, exact failure, and next action. State that the work is incomplete and allow a later session to continue naturally.

## Completion rule

Complete only when the requested artifacts exist, open correctly, match the approved conditions, every page of every delivered format has been inspected, every applicable canonical `MUST` is `PASS` or justified `N/A`, and no known failure remains.
