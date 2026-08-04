# PowerPoint output

Use this path only when the user requests PowerPoint, PPTX, editability, or a supplied PowerPoint template.

- Treat PPTX as the primary artifact and PDF as its derivative unless the user requests PPTX only.
- Use the environment's native PowerPoint creation capability and its prescribed workflow.
- Preserve editable text. Keep tables, charts, and simple shapes editable where practical.
- If a PPTX template or reference deck is supplied, inspect every source slide and preserve its master, layout, hierarchy, and visual language. Do not mix `warm_clean` into it unless explicitly requested.
- Do not rasterize the whole deck to simulate editability.
- Keep 16:9 unless the source template or user specifies otherwise.
- Validate overflow, clipping, unintended wrapping, placeholders, speaker notes when required, source notes, and font substitution.
- Render every final slide and inspect all pages in batches.
- Generate PDF only from the final validated PPTX, then verify page count and layout fidelity.
- Save a checkpointed draft before expensive rendering or PDF conversion.
- If PPTX generation or conversion is unavailable, explain the limitation and propose HTML/PDF or a single available format. Do not change formats without approval.
