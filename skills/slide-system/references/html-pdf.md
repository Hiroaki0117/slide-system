# HTML and PDF output

Use the bundled deterministic path instead of writing a complete HTML/CSS/JavaScript deck from scratch.

## Files

- `assets/deck-template.html`: warm_clean styling, fixed layout classes, navigation, page numbering, responsive scaling, embedded-font marker, and print rules.
- `assets/fonts/NotoSansJP-Variable.ttf`: bundled Japanese font embedded into every final HTML/PDF deck.
- `assets/deck-schema-example.json`: compact content model and supported fields.
- `assets/free-roadmap-brief-example.json`: free-plan compact input for dated high-stakes exercise roadmaps.
- `assets/work-state-example.json`: production phase and approval receipt required by the build gate.
- `scripts/build_deck.py`: validates the content model and creates one self-contained HTML file.
- `scripts/build_free_roadmap.py`: expands the compact roadmap brief, runs the same strict validator, and always saves either a validated HTML or a visibly marked non-executable draft.
- `scripts/recover_deck.py`: restores `deck.json` from HTML created by the current skill.
- `scripts/render_deck.mjs`: opens the HTML, tests navigation, renders every slide, makes a contact sheet, and exports PDF in one run.
- `scripts/export_pdf.mjs`: resource-saving conversion-only path. It writes the PDF first, then checks page count, 16:9 size, font loading, and hidden controls.

Every validated HTML includes a `PDF保存` button. It calls the browser print dialog and is hidden automatically in print/PDF output. A validation draft instead shows a disabled `PDF保存不可` button so an unresolved artifact cannot be mistaken for final output.

Every newly built HTML embeds its editable content model in `slide-deck-data`. This is not displayed in the slides and lets a later chat revise the deck without repeating research or reconstructing every page.

## Existing HTML and PDF

Choose the path from the supplied artifacts before asking questions or rebuilding.

- Existing task folder with `deck.json` and `work-state.json`: use those files as the editing source.
- Current slide-system HTML only: recover the model with `python scripts/recover_deck.py --html EXISTING.html --output WORK_DIR/deck.json`.
- Current HTML and PDF: edit the model recovered from HTML. Use PDF only as the visual reference for the previous delivered state.
- Older HTML without `slide-deck-data`: inspect it, reconstruct a compact model, present the reconstruction and requested changes for confirmation, then build.
- PDF only: render and inspect every page, reconstruct a compact model, and obtain confirmation before building. Never directly edit PDF content.

For a bounded correction to an existing deck, preserve unaffected pages and sources. Update HTML first and stop; create PDF on the next reply in the staged profile. Repeat research only for claims changed by the correction.

## Build

1. Copy `assets/work-state-example.json` to the task working directory as `work-state.json` during preflight.
2. Record blocking questions and production confirmation in the phases defined by `SKILL.md`.
3. Only after explicit approval or waiver, set the approval receipt and change the phase to `approved`.
4. Copy `assets/deck-schema-example.json` to the task working directory as `deck.json`.
5. Replace the example content and delete unused example slides.
6. Use only supported layout names. Prefer a different existing layout or split a slide instead of adding new CSS.
7. Run:

```text
python scripts/build_deck.py --input deck.json --work-state work-state.json --template assets/deck-template.html --output OUTPUT_DIR/deck-draft.html --report WORK_DIR/static-qa.json
```

The build must exit successfully with no `FAIL` item before rendering. `PRODUCTION_NOT_APPROVED` means the conversation must return to the confirmation checkpoint; do not fabricate approval data. Review and resolve every warning; do not ignore a visual-cadence warning merely because the build completed.

## Fast export for the staged free profile

After the user accepts the HTML and requests PDF, use:

```text
node scripts/export_pdf.mjs --html OUTPUT_DIR/deck-draft.html --pdf OUTPUT_DIR/deck-draft.pdf --report WORK_DIR/pdf-export-qa.json --work-state WORK_DIR/work-state.json
```

This is conversion-only. It rejects an HTML containing a visible draft banner with `DRAFT_NOT_APPROVED`. Do not recover or rebuild the deck, repeat research, render screenshots, or create a contact sheet before the PDF exists. For validated HTML only, if execution is unavailable, the user can open the HTML and choose `PDF保存`, or use Chrome/Edge `Ctrl+P` and select `PDFに保存`.

## Compact roadmap build for the free profile

For a dated high-stakes exercise roadmap, edit only a copied compact brief and execute:

```text
python scripts/build_free_roadmap.py --brief WORK_DIR/roadmap-brief.json --work-state WORK_DIR/work-state.json --template assets/deck-template.html --output OUTPUT_DIR/deck-draft.html --deck-output WORK_DIR/deck.json --report WORK_DIR/static-qa.json
```

Do not open the Python, JavaScript, template, font, or generated full model before the first HTML is returned. `PASS` means the unchanged strict validator accepted the expanded model. `DRAFT` still creates an HTML checkpoint with a visible non-executable banner; return it and defer correction instead of retrying until the session ends.

When a phase table contains more than four rows, the compact builder splits it into front and back slides and shifts all evidence references automatically. After a `PASS`, return the report's `user_review_points` with the HTML so the user can confirm proposed distances, session intensity, and start/stop conditions before requesting PDF.

## Full render and visual QA

Use the heavier full renderer for a paid-capacity workflow or a later explicit `仕上げQA` turn:

```text
node scripts/render_deck.mjs --html OUTPUT_DIR/deck-draft.html --pdf OUTPUT_DIR/deck-draft.pdf --renders WORK_DIR/renders --report WORK_DIR/render-qa.json --work-state WORK_DIR/work-state.json
```

Both exporters verify production approval. When `delivery_profile` is `staged`, they also require `phase: "pdf_requested"` or `phase: "qa"` and the exact follow-up reply in `pdf_request.user_reply`. They must reject PDF work during the HTML-only stage.

The script requires Playwright. If it is unavailable, use the environment's browser or PDF capability while preserving the same approval and staged-delivery gates, then the same order: final HTML first, all-slide render, then PDF.

Inspect `contact-sheet.png`, then inspect all generated slide PNGs at readable size. Record issues together, edit `deck.json`, rebuild once, and rerender affected and related pages as a batch. Generate the final PDF only after the final HTML passes.

Rename the validated pair without `draft` only after final QA.

## Supported layouts

- `cover`
- `agenda`
- `section_divider`
- `single_message`
- `text_focus`
- `text_visual`
- `comparison`
- `process`
- `data_focus`
- `bar_chart`
- `table`
- `decision_flow`
- `exercise`
- `summary_action`
- `sources_appendix`

Use `text_visual` for a simple text-and-image slide. The renderer must wait for `document.fonts.ready` and fail if the bundled font is unavailable. For a visual form the schema cannot express without loss, create a small, task-specific extension while preserving the template tokens, fixed areas, print rules, and validator contract. Do not replace the entire template.
