# HTML and PDF output

Use the bundled deterministic path instead of writing a complete HTML/CSS/JavaScript deck from scratch.

## Files

- `assets/deck-template.html`: warm_clean styling, fixed layout classes, navigation, page numbering, responsive scaling, embedded-font marker, and print rules.
- `assets/fonts/NotoSansJP-Variable.ttf`: bundled Japanese font embedded into every final HTML/PDF deck.
- `assets/deck-schema-example.json`: compact content model and supported fields.
- `assets/work-state-example.json`: production phase and approval receipt required by the build gate.
- `scripts/build_deck.py`: validates the content model and creates one self-contained HTML file.
- `scripts/render_deck.mjs`: opens the HTML, tests navigation, renders every slide, makes a contact sheet, and exports PDF in one run.

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

## Render and export

After static validation passes, run one batch command:

```text
node scripts/render_deck.mjs --html OUTPUT_DIR/deck-draft.html --pdf OUTPUT_DIR/deck-draft.pdf --renders WORK_DIR/renders --report WORK_DIR/render-qa.json --work-state WORK_DIR/work-state.json
```

The renderer verifies production approval. When `delivery_profile` is `staged`, it also requires `phase: "pdf_requested"` or `phase: "qa"` and the exact follow-up reply in `pdf_request.user_reply`. It must reject PDF work during the HTML-only stage.

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
