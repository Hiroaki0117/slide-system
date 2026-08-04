# HTML and PDF output

Use the bundled deterministic path instead of writing a complete HTML/CSS/JavaScript deck from scratch.

## Files

- `assets/deck-template.html`: warm_clean styling, fixed layout classes, navigation, page numbering, responsive scaling, and print rules.
- `assets/deck-schema-example.json`: compact content model and supported fields.
- `scripts/build_deck.py`: validates the content model and creates one self-contained HTML file.
- `scripts/render_deck.mjs`: opens the HTML, tests navigation, renders every slide, makes a contact sheet, and exports PDF in one run.

## Build

1. Copy `assets/deck-schema-example.json` to the task working directory as `deck.json`.
2. Replace the example content and delete unused example slides.
3. Use only supported layout names. Prefer a different existing layout or split a slide instead of adding new CSS.
4. Run:

```text
python scripts/build_deck.py --input deck.json --template assets/deck-template.html --output OUTPUT_DIR/deck-draft.html --report WORK_DIR/static-qa.json
```

The build must exit successfully with no `FAIL` item before rendering.

## Render and export

After static validation passes, run one batch command:

```text
node scripts/render_deck.mjs --html OUTPUT_DIR/deck-draft.html --pdf OUTPUT_DIR/deck-draft.pdf --renders WORK_DIR/renders --report WORK_DIR/render-qa.json
```

The script requires Playwright. If it is unavailable, use the environment's browser or PDF capability while preserving the same order: final HTML first, all-slide render, then PDF.

Inspect `contact-sheet.png`, then inspect all generated slide PNGs at readable size. Record issues together, edit `deck.json`, rebuild once, and rerender affected and related pages as a batch. Generate the final PDF only after the final HTML passes.

Rename the validated pair without `draft` only after final QA.

## Supported layouts

- `cover`
- `single_message`
- `text_focus`
- `comparison`
- `process`
- `data_focus`
- `table`
- `summary_action`
- `sources_appendix`

Use `text_focus` with an embedded image for a simple text-and-image slide. For a visual form the schema cannot express without loss, create a small, task-specific extension while preserving the template tokens, fixed areas, print rules, and validator contract. Do not replace the entire template.
