# Source and safety rules

Use these rules when the deck contains researched claims, current facts, rights-sensitive material, or high-impact recommendations.

## Source hierarchy

Prefer sources in this order:

1. user-supplied documents and data for facts about the user's own situation;
2. official organizations, laws, standards, product documentation, and primary datasets;
3. peer-reviewed primary research and recognized professional guidance;
4. reliable secondary summaries when primary sources are unavailable.

Do not treat a search summary, commercial blog, calculator, or remembered rule as authoritative when a stronger source is available.

## Claim-to-source mapping

- Put a short source marker on the slide where a material external claim appears.
- Put full title, publisher, URL, and access date in the sources appendix.
- Record each material high-stakes claim in `claim_evidence` with:
  - `claim`
  - `visible_text`
  - `slide`
  - `basis_type`
  - `source_ids`
  - `support`
  - `evidence_design`
  - `claim_strength`
- A page-level source ID must map to evidence for that page.
- A source that merely appears in the appendix does not support an unrelated statement.
- Distinguish user-provided facts, calculations, sourced claims, and model inference.

Supported `basis_type` values:

- `user_confirmed`
- `calculation`
- `authoritative_source`
- `effort_only`
- `inference`

## Evidence strength

- Match certainty to the evidence.
- Label forecasts, calculations, benchmarks, and formula-derived values as estimates.
- Put the main assumption or limitation beside the derived value.
- Observational evidence may support association or inference wording, not causal wording.
- Do not turn a population-level finding into a precise individual prescription without explaining the gap.
- If evidence does not support a number, use qualified non-numeric wording or mark the point unresolved.

## High-impact content

For medical, legal, financial, safety, or other high-impact material:

- confirm the current condition or context needed to avoid a misleading recommendation;
- list important limitations and stop, review, or consultation conditions;
- identify unresolved assumptions;
- mark the plan provisional when execution depends on an unresolved condition;
- show the clearance or execution condition on the slide it constrains;
- recommend a qualified professional when the requested decision exceeds the evidence or the tool's role.

Do not hide critical conditions only in metadata or the source appendix.

A generic safety object may use:

```json
{
  "current_condition": "confirmed context or explicitly unknown",
  "limitations": ["important limitation"],
  "stop_conditions": ["condition that stops execution"],
  "review_conditions": ["condition that triggers review"],
  "consultation_conditions": ["condition that requires a qualified professional"],
  "plan_status": "executable | provisional",
  "plan_status_text": "visible status wording",
  "clearance_condition": "visible condition for execution",
  "status_slide": 2,
  "critical_constraints": [
    {
      "text": "constraint shown verbatim on the affected slide",
      "slide": 4
    }
  ]
}
```

Use only fields relevant to the current request. Do not force one domain's schema onto another topic.

## Dated and progressive plans

For a dated roadmap:

- calculate from exact ISO dates;
- show one consistent duration;
- avoid misleading rounding;
- verify that each period is chronologically complete.

For a progressive or conditional plan:

- show starting condition, progression condition, hold condition, regression condition, and stop or review condition;
- give each stage a clear scope, period, purpose, and checkpoint;
- keep constraints next to the action they govern;
- separate current state from recommendation;
- do not invent a universal progression rule from a sample case.

The relevant domain facts and numeric guidance must be researched for the current request. They do not belong in this reusable skill.

## Rights and supplied assets

- Prefer user-supplied assets when the user asks for them and their use is allowed.
- Record source and permission status for external assets.
- Do not remove watermarks or imply ownership.
- Do not substitute another image when the user requires a specific supplied image.
- If rights are unclear, propose a licensed, public-domain, or original alternative before production.

## Failure handling

If a mandatory source, right, or safety condition cannot be satisfied:

1. explain the exact unresolved issue;
2. propose the safest usable alternative;
3. keep unsupported material out of executable guidance;
4. preserve a clearly labelled draft if it still helps review;
5. do not claim final QA has passed.
