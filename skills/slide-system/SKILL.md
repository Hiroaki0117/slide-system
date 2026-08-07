---
name: slide-system
description: Creates and revises consistent Japanese slide decks from short, non-expert requests. Use when a user asks for slides, a presentation, PowerPoint, HTML/PDF deck, proposal, report, explainer, roadmap, training material, or teaching material. Infers sensible defaults, applies the warm_clean theme, produces HTML and PDF by default, performs checkpointed resource-efficient QA, and avoids exposing internal production chatter.
---

# Slide System

Create a usable slide deck from ordinary language without requiring the user to know prompting, design, file formats, or this skill's internal labels.

## Core behavior

- Treat incomplete, informal input as normal. Do not ask the user to rewrite it as a specification.
- Infer safe defaults and ask only questions that materially change the result or are necessary for safety, rights, or factual accuracy.
- Separate blocking questions from production approval. Never treat an answer to a question as approval.
- Keep each user-facing checkpoint compact. Use an interactive question UI when available.
- Do not expose labels such as `standalone`, `how_to`, `warm_clean`, or `html_pdf` unless the user asks about the system.
- Do not narrate routine production steps. Suppress messages such as “Good, continuing,” static-validation success, render starts, per-page inspection updates, code changes, and raw QA logs. Tool activity may still appear in the interface; do not duplicate it in prose.
- Do not paste generated HTML, CSS, scripts, or detailed QA records into chat.
- Show the user only a necessary question, a decision request, a material blocker, or the final deliverables and concise QA result.

## Defaults and routing

Apply explicit user instructions first. Otherwise use these defaults.

- Audience: infer one primary audience. Use beginner-friendly language when expertise is unknown.
- Content mode: use self-contained slides unless a live presentation is explicit.
- Deck type: choose `explain`, `proposal`, `report`, `how_to`, or `training` from the requested outcome.
- Theme: use `warm_clean` unless a template, brand, or other theme is explicitly supplied.
- Output: create HTML as the primary artifact and PDF as its derivative unless the user requests PowerPoint or a single format.
- Aspect ratio: 16:9.
- Length: normally 8–12 slides; use 5–7 for a short overview and 13–20 only when the content genuinely requires detail.
- Cover: title and date are required. Add a subtitle only when useful. Never invent an author or organization.

Read each needed reference once per task, record its decisions in `work-state.json`, and do not repeatedly reopen the same reference unless the file changed or a validation failure points back to it.
Read `references/content.md` when selecting the narrative, audience level, deck type, density, cover, or ending.
Read `references/layouts.md` before assigning layouts.
Read `references/warm-clean.md` whenever the default theme is used or adapted.
Read `references/source-safety.md` when facts require research or any claim is current, medical, legal, financial, safety-related, or rights-sensitive, even if the deck as a whole is low-risk.
Read `references/visuals.md` for every deck with six or more content slides, or when using supplied or external photos, illustrations, icons, charts, tables, diagrams, or screenshots.
Read `references/pptx.md` only for PowerPoint output.
Read `references/html-pdf.md` before building the default HTML/PDF output.

## Workflow

### 1. Inspect and preflight

1. Open every supplied file that is needed for the task.
2. Identify audience, purpose, central takeaway, content mode, deck type, output format, and source constraints.
3. Check that the required output, conversion, and inspection tools are available without beginning content production.
4. Identify missing information that materially changes safety, rights, scope, or factual accuracy.
5. If a required input, right, or capability is missing, recommend the safest practical option and at most two alternatives before production.

### 2. Resolve blocking questions and stop

If a missing answer materially changes safety, rights, factual accuracy, scope, or the proposed deliverables, ask only the necessary question and stop the turn. Do not include the production approval choice in the same message.

Set `work-state.json` to `phase: "questions_pending"`. After the user answers, update the conditions, but do not infer approval from that answer. If another blocking answer is still required, ask it and stop again.

When health or safety changes the recommendation, ask one concise question about the missing current condition before proposing individualized guidance.

### 3. Present production conditions and stop

Present one plain-language production confirmation containing:

- who the slides are for and how they will be used;
- the proposed title, date, approximate length, and story direction;
- the deliverable formats;
- important assumptions, corrections, and safety conditions already resolved.

For a new deck or full restructuring, this confirmation is a hard gate. End with an explicit choice such as `この内容で制作する` or `内容を修正する`, then stop the turn and wait. Set `work-state.json` to `phase: "confirmation_pending"` and `approval.status: "pending"`.

Only an unambiguous approval of the presented conditions counts. A reply that merely answers a preceding question, supplies a correction, says to continue gathering information, or is otherwise ambiguous is not approval. Incorporate the new information, present the revised production conditions, and stop again.

After explicit approval, record `phase: "approved"`, `approval.status: "approved"`, and the user's exact approval reply in `approval.user_reply`. If the user explicitly waives confirmation, record `approval.status: "waived"` and the exact waiver reply. Never create or set these values before the user provides that reply.

While the phase is `questions_pending` or `confirmation_pending`, allow only the minimum read-only lookup needed to identify supplied material, verify an event or date, or form accurate production conditions. Do not perform broader content research, draft the content model, build HTML, render, or export. Skip this gate only for a minor edit, conversion, evaluation, or explicit waiver.

### 4. Plan internally

After confirmation, verify unstable and high-stakes facts before writing them.
Define one communication job for the deck. Give every slide one narrative job and one primary claim. Choose a cumulative story rather than an agenda-shaped list. End with the conclusion, action, application, or understanding appropriate to the deck type.

Create a compact internal content model before implementation. Validate factual claims, title lengths, text density, minimum type sizes, citations, and source coverage before rendering or exporting PDF.

### 5. Checkpoint before expensive work

Use a task-local working directory. Maintain `work-state.json` with:

- current phase: `questions_pending`, `confirmation_pending`, `approved`, `building`, `qa`, or `complete`;
- approval status and the exact user reply that granted or waived approval;
- confirmed conditions;
- source list and unresolved assumptions;
- slide count and slide jobs;
- paths of the current source artifact, HTML, PDF, renders, and QA report;
- completed and remaining steps;
- last known failures.

Save the content model and `work-state.json` before rendering. Save a clearly named draft HTML to the user-accessible output directory immediately after the first successful build. Do not present it as final.

If resuming a prior task, read `work-state.json` and existing artifacts first. Do not repeat research, rebuild from scratch, or ask the same questions unless the files are missing or assumptions changed.

Before calling a production script, pass `work-state.json` to its approval gate. A missing, pending, or unauditable approval is a hard failure, not a warning.

### 6. Build efficiently

For HTML/PDF, use the bundled template and scripts described in `references/html-pdf.md`. Generate deck data, not a new site framework. Reuse the existing CSS, bundled Japanese font, navigation, print rules, page numbering, and layout classes. Assign every content slide both `job` and `visual_role`; use `visual_reason` when the role is `none`.

For PowerPoint, follow `references/pptx.md` and use the available presentation-generation capability. Do not convert the HTML into a flattened PowerPoint unless the user explicitly accepts a non-editable result.

### 7. Validate in the correct order

1. Run static validation before screenshots or PDF generation.
2. Fix all static failures together.
3. Render every HTML slide and a contact sheet in one batch.
4. Inspect the contact sheet for story and consistency, then inspect every rendered slide at readable size. Open multiple renders in one tool call when supported. Do not report each page inspection to the user.
5. Collect all detected issues, fix them as one batch, and rerender affected and related slides together.
6. Generate PDF only after the final HTML passes.
7. Verify PDF page count, dimensions, backgrounds, text, sources, page numbers, and lack of navigation UI. Inspect all PDF pages in batches.
8. If PDF differs, fix the HTML source and regenerate PDF. Never edit the PDF independently.

Do not reduce quality to meet a turn limit. Reduce repeated work, tool calls, and narration instead.

### 8. Handle resource limits safely

Checkpoint after every build, render, correction batch, and export. Before starting another correction cycle, ensure current artifacts and remaining QA are saved.

If the environment stops before completion:

- keep the newest artifacts in the user-accessible output directory with `draft` in their names;
- update `work-state.json` with the exact next action;
- state that the work is incomplete and list only the remaining checks;
- allow the user to resume with a natural message such as “続けてください”.

Never claim completion when a required artifact or final QA is missing.

### 9. Deliver concisely

The final response should normally contain only:

- the generated files;
- the slide count and output formats;
- the final QA result;
- any remaining warning or constraint.

Do not display internal labels, source code, per-page narration, or the full QA checklist.

## Completion rule

Call the task complete only when requested artifacts exist, open correctly, all required pages were inspected, all mandatory checks pass or have an explicit not-applicable reason, and no known failure remains. Keep warnings visible but concise.
