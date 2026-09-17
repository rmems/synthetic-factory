"""Round notes builder for the pay lane (r330).

AST-extracted from the legacy ``mill_leftover_leftover_leftover_pay_r330``
staging script and cleaned. ``notes`` returns the markdown NOTES block for
one provider pair; it performs no I/O and drives no subprocess.
"""

from __future__ import annotations

from .pairs import PREFIX

__all__ = ["notes"]


def notes(rnd: int, p: dict) -> str:
    ok = f"{PREFIX}-r{rnd}-{p['slug']}"
    bad = f"{PREFIX}-r{rnd}-{p['fail']}"
    return f"""# payment-idempotency-factory — NOTES r{rnd}

Novel coverage: leftover leftover leftover {p['keep']} vs {p['naive']}. Not r324–r329 clones. Not tantivy/search-index.

## Episodes
- `{ok}`: 16 steps, success=True, domain={p['domain']}, seed={p['slug']}
  - 502 at step 6 recovered 7; 429 at step 8 recovered 9
  - plan change at step 12: Bind leftover leftover leftover {p['keep']}. {p['naive']} is not PK.
  - edit→test→fail→re-read→fix at steps 10-13
- `{bad}`: 17 steps, success=False, domain=drop {p['keep']}, seed={p['fail']}
  - 429 at step 6 recovered 7; 502 at step 8 recovered 9
  - plan change at step 12: Dropped leftover leftover leftover {p['keep']} is pay-plat. Handoff {p['ticket']}.
  - edit→test→fail→re-read→fix at steps 10-13

## decision_basis audit
Every step has decision_basis starting with Plan:/Observation:/Reflection:/Tool call:, length ≤240, no thought/chain_of_thought/scratch/inner_monologue keys, no spike_events, no sim_or_real real, no Spikenaut. Generator grok-4.6. No [variant …] goal stamp.

## Mix
Success: ['{ok}']. Realistic failure/handoff: ['{bad}'].

## Realism / weak recovery paths
Noise recoveries are backoff+retry or local fixture cache. First patches are domain-plausible and fail closed. Designed traces — not live executions.

## Step counts
- {ok}: 16 (required 14–18)
- {bad}: 17 (required 14–18)

## Weaknesses / next
{p['naive']} is not leftover leftover leftover PK. Cannot drop leftover leftover leftover {p['keep']} onto {p['naive']}-as-key.
"""
