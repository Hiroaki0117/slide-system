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
- Before building, record every material high-stakes recommendation in top-level `claim_evidence`. Read the cited source and describe what it directly supports. Also record `evidence_design` and `claim_strength`; observational evidence permits association or inference wording, not a causal promise. A related source, title match, or citation in the footer is not enough.
- A page-level source marker must map to evidence recorded for that same page. Do not cite an official event page for a training pace, or a return-to-run guideline for an unsupported weekly distance progression.
- Show the inputs, assumptions, and main limitation beside a prediction or derived number.
- Do not convert population-level guidance into a fixed individualized schedule without the user's current condition, baseline, response, and recovery information.
- For a progressive plan, include the starting condition, progression condition, recovery or easier period, regression condition, and stop or consultation condition. If any safety-critical condition is unknown, label the plan as provisional rather than executable.
- Do not make an immediate action the conclusion unless the information needed to decide that action has been confirmed.

### Progressive exercise plans

- Set `safety.progressive_plan: true` and record non-empty `progression_conditions`, `recovery_conditions`, `regression_conditions`, and `consultation_conditions` in addition to `stop_conditions`.
- When the plan is tied to a known event or deadline, set top-level `dated_roadmap: true` and record `timeline.current_date`, `timeline.target_date`, `timeline.duration_text`, and the slide where that exact duration is visible.
- Record `phase_guidance` for every phase. Each entry needs `name`, `period`, `long_session_distance_or_time`, `purpose`, `checkpoint`, `progression_condition`, `hold_or_regress_condition`, and the slide where the period and load guide are visible.
- `long_session_distance_or_time` must contain a numeric distance or time and a conditional range, current-load ceiling, or maintenance instruction. A vague phrase such as `少しずつ延ばす` is not sufficient.
- Record `session_guidance` for every recurring session type. Each entry needs `session_type`, `current_method`, `recommendation_decision`, `pace_or_effort`, `progression`, `purpose`, `decision_reason`, `adjustment_condition`, `intensity_class`, and `basis` before building.
- Use `maintain`, `change`, or `stop` for `recommendation_decision`. Do not copy `current_method` into `pace_or_effort` with `change` or `stop`. If the proposal intentionally matches the current method, use `maintain` and state the reason.
- Also record `basis_type`, `source_ids`, and `slide` for every recurring session. Use `user_confirmed`, `calculation`, `authoritative_source`, `effort_only`, or `inference`. An `authoritative_source` basis requires a source ID whose content directly supports the prescription.
- Record the current method's basis separately as `current_basis_type`. When either `current_basis_type` or `basis_type` is `user_confirmed`, save the user's exact wording as `confirmation_quote` and copy that wording into `work-state.confirmed_conditions`. A derived target metric may be labelled as a calculation, but calculation alone must not prescribe a recurring workout pace.
- State the pace or effort for long sessions, easy or recovery sessions, and quality sessions separately. Keep long-session pace distinct from goal-pace segments unless an authoritative source and the confirmed condition support combining them.
- Use a subjective effort or talk-test description alongside a numeric pace. Avoid false precision when weather, terrain, fatigue, injury status, or recent training makes the number uncertain.
- Do not make all regular sessions demanding. Show where recovery occurs and what condition changes a demanding session into easy work or rest.
- For beginners or return from injury, set `novice_or_returning: true`. Include at least one `easy` or `recovery` session and no more than one `quality` session among the recurring weekly sessions.
- If current pain is present, recurrent, focal, or not clearly improving, do not present progression as cleared. Put assessment or consultation before distance or intensity progression and keep any plan provisional.
- For `symptomatic` or `unknown`, record visible `pre_clearance_actions` and `action_slide`. Add a visible `execution_condition` to every phase and recurring session so no later page reads as unconditional permission to run. Support the stop or consultation action with `kind: safety` claim evidence.
- Record `condition_status` as `pain_free`, `symptomatic`, `unknown`, or `not_applicable`. A symptomatic or unknown progressive plan must use `plan_status: provisional`, visibly show `plan_status_text` and `clearance_condition`, and identify `status_slide`.
- Event preparation needs distinct recovery and taper phases. Record `taper_days`; normally keep it within 14–21 days unless directly supported evidence and confirmed circumstances justify otherwise.
- Record official start, cutoff, timing basis, course implication, strategy slide, and official source IDs in top-level `event_facts` when they affect the requested outcome.
- Add `goal_basis` and `pace_buffer_note` to `event_facts` when the requested result depends on gross/net timing or start-line delay.
- Record `event_strategy` with at least three visible segments plus fueling, equipment, rehearsal, source IDs, and its slide. An official-facts table alone does not satisfy this requirement.
- For a dated event plan, record `weekly_long_sessions` for every remaining week. Each entry needs `week`, `period`, `distance_or_time`, `condition`, `recovery_week`, and `slide`; include at least one easier recovery week before taper.
- If the supplied current performance and target have comparable units, set `comparable_performance_data: true` and record `current_target_comparison` so both values use the same unit, `comparison_basis` is explicit, and the interpretation is visible together.

Use this compact model shape before building:

```json
{
  "dated_roadmap": true,
  "timeline": {
    "current_date": "YYYY-MM-DD",
    "target_date": "YYYY-MM-DD",
    "duration_text": "exact days plus natural rounded weeks",
    "slide": 4
  },
  "safety": {
    "progressive_plan": true,
    "novice_or_returning": true,
    "event_preparation": true,
    "current_condition": "confirmed condition or explicit unknown",
    "condition_status": "pain_free | symptomatic | unknown | not_applicable",
    "plan_status": "executable | provisional",
    "plan_status_text": "visible status wording",
    "clearance_condition": "visible condition before execution",
    "status_slide": 2,
    "taper_days": 21,
    "comparable_performance_data": true,
    "limitations": ["what is not established"],
    "progression_conditions": ["when load may increase"],
    "recovery_conditions": ["where easier work or rest occurs"],
    "regression_conditions": ["when to reduce or hold"],
    "stop_conditions": ["when to stop"],
    "consultation_conditions": ["when to seek qualified assessment"],
    "phase_guidance": [
      {
        "name": "phase name",
        "period": "week or date range shown on the slide",
        "phase_type": "base | build | peak | recovery | taper | other",
        "long_session_distance_or_time": "numeric conditional range or current-load ceiling",
        "purpose": "why this phase exists",
        "checkpoint": "what to review before advancing",
        "progression_condition": "when the next phase is allowed",
        "hold_or_regress_condition": "when to hold, shorten, or step back",
        "slide": 4
      }
    ],
    "session_guidance": [
      {
        "session_type": "recurring session name",
        "current_method": "method copied from the user's source notes",
        "current_basis_type": "user_confirmed | inference",
        "recommendation_decision": "maintain | change | stop",
        "recommendation_label": "visible localized decision label",
        "pace_or_effort": "numeric range plus effort cue, or effort cue alone",
        "progression": "how the proposal changes across phases or conditions",
        "purpose": "why this session exists",
        "decision_reason": "why the current method is maintained, changed, or stopped",
        "adjustment_condition": "when to change it to easier work or rest",
        "intensity_class": "easy | recovery | quality | long_easy | other",
        "basis": "specific explanation of the basis",
        "basis_type": "user_confirmed | calculation | authoritative_source | effort_only | inference",
        "confirmation_quote": "exact user wording when a current or proposed value is user-confirmed",
        "source_ids": ["S2"],
        "slide": 5
      }
    ]
  },
  "claim_evidence": [
    {
      "claim": "material recommendation or fact",
      "visible_text": "exact wording visible on the slide",
      "slide": 5,
      "basis_type": "authoritative_source",
      "source_ids": ["S2"],
      "support": "what the cited source directly supports"
    }
  ],
  "event_facts": {
    "official_event_name": "official name visible on the strategy slide",
    "start_time": "official start visible on the strategy slide",
    "cutoff": "official cutoff visible on the strategy slide",
    "timing_basis": "gross or net timing basis visible on the strategy slide",
    "course_summary": "course implication visible on the strategy slide",
    "strategy_slide": 7,
    "source_ids": ["S1"]
  },
  "current_target_comparison": {
    "current_value": "current value with unit",
    "target_value": "target value with unit",
    "meaning": "visible interpretation and limitation",
    "slide": 2
  }
}
```

## Assets and rights

- Use a user-requested image or logo when provided, unless there is a material rights or safety problem.
- Do not replace requested material silently.
- Do not copy an image directly from search results.
- Record provider, page, URL, access date, and known usage conditions for external material.
- Label user-provided and AI-generated material distinctly in the source record.
- If usage conditions cannot be established, propose an official asset, a clearly licensed asset, an original diagram, or an AI-generated alternative.
