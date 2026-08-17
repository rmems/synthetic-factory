# Cleaned provenance

This tree is a promotion of a raw factory run. **Raw JSONL is the source of truth (SoT)** and was not modified.

Cleaned `provenance.kind` is one of `designed` | `simulated` | `hil` | `unknown`. Cleaned records **never emit `real`** in `state.sim_or_real` or `provenance.kind`. The original claim is kept in `provenance.claimed`.

Invented plants and labels that start with `real`/`live` or mention production / actions live are `designed` stories, not live telemetry.

If a `spike_events` train was not globally time-ordered, the cleaned copy is sorted and `meta.spike_events_resorted` is true.
