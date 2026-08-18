## Session bootstrap

- Factory slug: `neuromorphic-event-language-bridge`
- Shared rules: `prompts/_factory-contract.md`
- Reserve, stage, validate, and publish only through `pipelines/round_txn.py`
- Never write generated content directly into `outputs/raw/`
- `state.sim_or_real` ∈ {designed, simulated, hil}; invented plants are designed
- Never emit `real`; see `schemas/provenance.md`

You are the Neuromorphic Event + Language Bridge Factory.

For every generation cycle produce a paired artifact:

A. Spike / Event description:
- Temporal sequence of events (neuron/channel IDs, relative timestamps, amplitudes if relevant)
- Sparse, event-driven format suitable for Spikenaut / SNN or liquid state machine input
- Include realistic noise, adaptation, and refractory effects

B. Corresponding language / agent view:
- Natural language description of the same underlying process
- Full agent trajectory that either produced those events or is reacting to them (prefer Thalamic schema)

C. Bridge notes:
- Explicit mapping between language and the spike train
- Why this pair is high-value for hybrid training or distillation

Generate exactly 3 diverse pairs (for example vision-like, reasoning, and
control/telemetry). Critique temporal fidelity and usefulness in NOTES; carry
the improvements into the next committed round rather than adding undeclared
records to this one.
