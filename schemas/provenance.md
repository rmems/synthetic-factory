# Provenance

This file is the identity-lane remap (`state.sim_or_real` →
`provenance.kind`). `identity.unresolved_provenance` means that remap
could not run. It is not the #154 actor graph; missing task_author /
solver / reviewer / oracle stay `vset.*` codes on actor-provenance-v1.

Cleaned records carry `provenance.kind`. Allowed values:

`designed` | `simulated` | `hil` | `unknown`

Never emit `real` in cleaned output. Raw stays as written (`state.sim_or_real` and any other claimed string).

## Remap

Apply the **first matching** rule, case-insensitive, to the claimed string (typically `state.sim_or_real`):

| Claimed string (case-insensitive) | provenance.kind |
|---|---|
| starts with `real` or `live` or contains `actions live` / `production` | designed (keep original in `provenance.claimed`) |
| contains `simulation` / `simulat` / `high-fidelity` | simulated |
| contains `hardware-in-the-loop` / `hil` | hil |
| missing | unknown |

If the field is present but matches no row, use `unknown` and keep the original in `provenance.claimed`.

## Shape

```
provenance.kind      designed | simulated | hil | unknown
provenance.claimed   original claimed string (required on designed remaps)
```

Invented plants are `designed`. New factory writes set `state.sim_or_real` to `designed`, `simulated`, or `hil` — never `real`, never `unknown`.
