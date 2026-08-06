# HTML and PDF output

Use the bundled deterministic path instead of writing a complete slide framework from scratch.

## Files

- `assets/deck-template.html`: warm_clean styling, layout classes, navigation, page numbering, responsive scaling, embedded-font marker, and print rules.
- `assets/fonts/NotoSansJP-Variable.ttf`: Japanese font embedded into final HTML/PDF.
- `assets/deck-schema-example.json`: generic content model and supported fields.
- `assets/work-state-example.json`: production phase and approval receipt.
- `scripts/build_deck.py`: validates the content model and creates one self-contained HTML file.
- `scripts/recover_deck.py`: restores `deck.json` from current slide-system HTML.
- `scripts/render_deck.mjs`: full navigation, render, contact-sheet, and PDF QA.
- `scripts/export_pdf.mjs`: resource-saving PDF conversion and parity checks.

Every built HTML embeds its editable model in `slide-deck-data`. This is not displayed and lets a later chat revise the deck without repeating research.

## Existing HTML and PDF

Choose the path from supplied artifacts before rebuilding.

- Task folder with `deck.json` and `work-state.json`: use them as the editing source.
- Current slide-system HTML: recover with:
  `python scripts/recover_deck.py --html EXISTING.html --output WORK_DIR/deck.json`
- Current HTML and PDF: edit the model recovered from HTML. Use PDF only as a visual reference.
- Older HTML without embedded data: inspect it, reconstruct a compact model, present the reconstruction and requested changes, and wait for confirmation.
- PDF only: render and inspect pages, reconstruct a compact model, and obtain confirmation before building.

For a bounded correction, preserve unaffected pages and sources. Update HTML first. Repeat research only for changed claims. Never edit PDF independently.

## Build

1. Copy `assets/work-state-example.json` to the task directory.
2. Record blocking questions and confirmation phases defined by `SKILL.md`.
3. After explicit approval, record the exact approval reply and set the phase to `approved`.
4. Copy `assets/deck-schema-example.json` to `deck.json`.
5. Replace example content and delete unused example slides.
6. Use supported layouts. Split content before adding custom CSS.
7. Run:

```text
python scripts/build_deck.py --input deck.json --work-state work-state.json --template assets/deck-template.html --output OUTPUT_DIR/deck-draft.html --report WORK_DIR/static-qa.json
```

The build must finish with no `FAIL` item. `PRODUCTION_NOT_APPROVED` means return to the confirmation checkpoint. Review warnings rather than ignoring them.

## Staged PDF export

After the user has received HTML and requests PDF:

```text
node scripts/export_pdf.mjs --html OUTPUT_DIR/deck-draft.html --pdf OUTPUT_DIR/deck-draft.pdf --report WORK_DIR/pdf-export-qa.json --work-state WORK_DIR/work-state.json
```

This is conversion-only. Do not recover or rebuild the content, repeat research, render screenshots, or create a contact sheet before the PDF exists.

If execution is unavailable, the user can open the validated HTML and use its PDF-save button or Chrome/Edge `Ctrl+P` → save as PDF.

## Full visual QA

Use the heavier renderer for a paid-capacity workflow or a later explicit visual-QA turn:

```text
node scripts/render_deck.mjs --html OUTPUT_DIR/deck-draft.html --pdf OUTPUT_DIR/deck-draft.pdf --renders WORK_DIR/renders --report WORK_DIR/render-qa.json --work-state WORK_DIR/work-state.json
```

Both exporters verify approval. With staged delivery, PDF work also requires `phase: "pdf_requested"` or `phase: "qa"` and the user's exact follow-up reply.

Inspect the contact sheet and all page renders. Collect issues, edit `deck.json`, rebuild once, and rerender affected and related pages together. Rename the final pair without `draft` only after QA.

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

The renderer must wait for `document.fonts.ready` and fail if the bundled font is unavailable. For a visual the schema cannot express without loss, create a small task-specific extension while preserving theme tokens, fixed areas, print rules, and validation. Do not replace the whole template.
