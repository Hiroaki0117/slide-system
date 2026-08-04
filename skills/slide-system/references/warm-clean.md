# warm_clean theme

Use a bright, calm, friendly editorial tone. Keep generous margins, clear hierarchy, restrained rounded shapes, and soft coral or mint accents. Avoid corporate navy, heavy gradients, glossy effects, and dense dashboard cards.

## Color tokens

| Token | Value | Use |
|---|---|---|
| background | `#FFF8F4` | Main background |
| surface | `#FFFFFF` | Limited grouping surfaces |
| text primary | `#3F3639` | Titles, body, key numbers |
| text secondary | `#665B5E` | Notes and secondary information |
| coral text | `#B94D48` | Small headings and emphasized words |
| coral accent | `#E96E68` | Lines, icons, small shapes |
| coral soft | `#FFD2C7` | Large pale accent areas |
| mint soft | `#C5E7E1` | Supporting or comparison areas |
| divider | `#E8DFDC` | Rules and table borders |
| dark background | `#3F3639` | Rare strong divider or conclusion |
| inverse text | `#FFF8F4` | Text on dark background |

Use `text primary` for ordinary titles and body. Never use the soft colors as body text. Do not communicate meaning by color alone.

## Typography

Use the bundled `assets/fonts/NotoSansJP-Variable.ttf` for final HTML/PDF output. Embed it in the self-contained HTML and confirm that the browser loaded `Slide Noto Sans JP` before rendering. Do not treat a system-font fallback as a final result. System fonts may be used only for a temporary diagnostic preview, with the limitation recorded.

Minimum sizes:

- cover title: 50 pt;
- slide title: 35 pt;
- subheading or callout heading: 24 pt;
- body: 16 pt;
- sources, notes, page numbers: 10 pt when necessary.

Prefer 18–22 pt body text for self-contained slides and 22–26 pt for presented slides. Shorten or split before shrinking below the minimum.

## Composition

- Align body content left by default.
- Reserve centering for covers, section dividers, and genuine single-message slides.
- Keep the strongest emphasis to one location per slide.
- Use typography first, color second, and a background shape last.
- Use one or two large soft circles or curves mainly on covers, dividers, or single-message slides.
- In content slides, use small lines, circles, or pale areas sparingly.
- Do not repeat the same corner circles mechanically on every slide.
- Prefer editorial bands, timelines, charts, callouts, and asymmetric text-visual compositions over grids of UI-like cards.
- Avoid shadows, gradients, 3D, glossy effects, repeated outer frames, and making every group a card.
- Put short sources at the common lower-left position.
- Number every page from the cover as `01`, `02`, and so on at the common lower-right position.
