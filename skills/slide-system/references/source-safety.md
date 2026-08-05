# Sources and safety

Use this reference when research, rights, or high-stakes guidance is involved.

## Research

- Verify information that may have changed, including schedules, laws, product details, prices, roles, and event information.
- Prefer official sources for event, organization, government, product, and policy facts.
- Prefer peer-reviewed primary research, clinical guidance from recognized medical institutions, or official public-health guidance for health claims.
- Record title, publisher, URL, publication date when available, and access date.
- Separate fact, estimate, recommendation, and inference in both wording and visual treatment.
- If a calculation is used, preserve inputs, units, method, rounding, and limitation.

## High-stakes topics

- Set `high_stakes: true` in the content model. Add a `safety` object containing the confirmed current condition, limitations, and stop or consultation conditions before building.
- Do not diagnose, guarantee outcomes, or present general guidance as individualized professional advice.
- Identify missing information that changes safety. Ask one concise question when needed.
- Use conditional wording and decision criteria.
- State when to stop, step back, or consult a qualified professional.
- Put limitations beside the relevant recommendation, not only on the final sources slide.
- For an exercise plan with an injury history, ask whether pain is currently present before production. If pain is present or status is unknown, do not present the plan as cleared for execution; show a stop condition and recommend qualified medical assessment.
- Do not add remembered numeric rules, pace predictions, progression percentages, exercise prescriptions, or return-to-running thresholds without an authoritative source that directly supports them.
- Match the strength of each claim to the evidence. A calculator, prediction formula, benchmark, or single past result may support a rough estimate, but not a categorical statement that an outcome is achievable.
- Show the inputs, assumptions, and main limitation beside a prediction or derived number.
- Do not convert population-level guidance into a fixed individualized schedule without the user's current condition, baseline, response, and recovery information.
- For a progressive plan, include the starting condition, progression condition, recovery or easier period, regression condition, and stop or consultation condition. If any safety-critical condition is unknown, label the plan as provisional rather than executable.
- Do not make an immediate action the conclusion unless the information needed to decide that action has been confirmed.

### Progressive exercise plans

- Set `safety.progressive_plan: true` and record non-empty `progression_conditions`, `recovery_conditions`, `regression_conditions`, and `consultation_conditions` in addition to `stop_conditions`.
- Record `session_guidance` for every recurring session type. Each entry needs `session_type`, `pace_or_effort`, `purpose`, and `adjustment_condition` before building.
- State the pace or effort for long sessions, easy or recovery sessions, and quality sessions separately. Keep long-session pace distinct from goal-pace segments unless an authoritative source and the confirmed condition support combining them.
- Use a subjective effort or talk-test description alongside a numeric pace. Avoid false precision when weather, terrain, fatigue, injury status, or recent training makes the number uncertain.
- Do not make all regular sessions demanding. Show where recovery occurs and what condition changes a demanding session into easy work or rest.
- If current pain is present, recurrent, focal, or not clearly improving, do not present progression as cleared. Put assessment or consultation before distance or intensity progression and keep any plan provisional.

Use this compact model shape before building:

```json
{
  "progressive_plan": true,
  "current_condition": "confirmed condition or explicit unknown",
  "limitations": ["what is not established"],
  "progression_conditions": ["when load may increase"],
  "recovery_conditions": ["where easier work or rest occurs"],
  "regression_conditions": ["when to reduce or hold"],
  "stop_conditions": ["when to stop"],
  "consultation_conditions": ["when to seek qualified assessment"],
  "session_guidance": [
    {
      "session_type": "recurring session name",
      "pace_or_effort": "numeric range plus effort cue, or effort cue alone",
      "purpose": "why this session exists",
      "adjustment_condition": "when to change it to easier work or rest"
    }
  ]
}
```

## Assets and rights

- Use a user-requested image or logo when provided, unless there is a material rights or safety problem.
- Do not replace requested material silently.
- Do not copy an image directly from search results.
- Record provider, page, URL, access date, and known usage conditions for external material.
- Label user-provided and AI-generated material distinctly in the source record.
- If usage conditions cannot be established, propose an official asset, a clearly licensed asset, an original diagram, or an AI-generated alternative.
