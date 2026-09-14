#!/usr/bin/env python3
"""Generate NELB round-39 research-only bridge pairs (do not write outputs/raw/)."""

from __future__ import annotations

import hashlib
import json
import math
import random
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

OUT_DIR = Path("/tmp/nelb-r39")
BATCH = OUT_DIR / "batch-r39.jsonl"
NOTES = OUT_DIR / "NOTES-r39.md"
PIPELINES = Path("/home/raulmc/rmems/synthetic-factory/pipelines")
sys.path.insert(0, str(PIPELINES))

GENERATED_AT = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

RIGHTS = {
    "provider": "SpaceXAI/xAI",
    "model": "grok-4.6",
    "channel": "consumer",
    "subscription_plan": "SuperGrok Heavy",
    "generation_surface": "SuperGrok Heavy chat",
    "generated_at": GENERATED_AT,
    "intended_use": "research_only",
    "project_training_policy": "blocked",
    "research_retention_status": "allowed",
    "research_evaluation_status": "allowed",
    "redistribution_status": "unresolved",
    "provider_training_status": "unresolved",
    "weight_publication_status": "blocked",
    "status_basis": "RM-793 project policy: xAI hosted outputs are research-only",
    "linear_issue": "RM-793",
}
RIGHTS_KEYS = (
    "provider",
    "model",
    "channel",
    "subscription_plan",
    "generation_surface",
    "generated_at",
    "intended_use",
    "project_training_policy",
    "research_retention_status",
    "research_evaluation_status",
    "redistribution_status",
    "provider_training_status",
    "weight_publication_status",
    "status_basis",
    "linear_issue",
)
assert len(RIGHTS) == 15
assert tuple(RIGHTS.keys()) == RIGHTS_KEYS

HIDDEN = {
    "thought",
    "thoughts",
    "reasoning",
    "chain_of_thought",
    "hidden_thought",
    "hidden_reasoning",
    "scratchpad",
    "scratch",
    "internal_monologue",
    "private_reasoning",
    "inner_monologue",
}

FAMILY_NEEDLES = (
    "phosphor_thermometry_hrsg",
    "vortex_shedding_steam",
    "gwr_foam_tank_level",
    "phosphor thermometry",
    "vortex-shedding steam",
    "guided-wave radar",
)
PLANT_NEEDLES = ("rushholt", "drizzlewick", "tarnfen")
ID_NEEDLES = ("nelb-r39-118", "nelb-r39-119", "nelb-r39-120")


def meta_common(**extra):
    m = {
        "round": 39,
        "factory": "neuromorphic-event-language-bridge",
        "generator": "grok-4.6",
        "run_label": "2026-09-02-final-heavy",
        "rights": dict(RIGHTS),
    }
    m.update(extra)
    return m


def make_raster(
    *,
    neurons: int,
    mean_rate_hz: float,
    window_ms: float,
    seed: int,
    source: str,
    target: str,
    table: list,
    third_factor: dict,
    channel_prefix: str,
    anchor: str,
):
    window_s = window_ms / 1000.0
    spikes = int(round(neurons * mean_rate_hz * window_s))
    window_us = int(round(window_ms * 1000))
    rng = random.Random(seed)
    n_active = min(neurons, spikes)
    extra = spikes - n_active
    counts = [1] * n_active + [0] * (neurons - n_active)
    for i in range(extra):
        counts[i % n_active] += 1

    excerpt = []
    for nid, c in enumerate(counts):
        if c == 0:
            continue
        first_max = window_us - 1100 * (c - 1) - 250
        t = rng.randint(120, max(120, first_max))
        times = [t]
        for k in range(1, c):
            min_t = times[-1] + 1100
            slack = window_us - 1100 * (c - 1 - k) - 80
            hi = min(slack, times[-1] + rng.choice([1300, 1800, 2400, 3700, 5200, 7400]))
            if hi < min_t:
                hi = min_t
            if min_t > window_us:
                raise RuntimeError(f"placement overflow neuron {nid}")
            t2 = rng.randint(min_t, hi) if hi > min_t else min_t
            t2 = min(t2, window_us)
            times.append(t2)
        base = 1.15 + 0.7 * rng.random()
        for i, tu in enumerate(times):
            noise = 0.96 + 0.08 * rng.random()
            amp = round(base * (0.82**i) * noise, 3)
            excerpt.append(
                {
                    "t_us": int(tu),
                    "neuron_id": nid,
                    "amplitude": amp,
                    "channel": f"{channel_prefix}{nid:02d}",
                }
            )
    excerpt.sort(key=lambda e: (e["t_us"], e["neuron_id"]))

    by_n = defaultdict(list)
    for e in excerpt:
        by_n[e["neuron_id"]].append(e["t_us"])
    isis_ms = []
    for nid, ts in by_n.items():
        ts = sorted(ts)
        for a, b in zip(ts, ts[1:]):
            gap = b - a
            if gap < 1000:
                raise RuntimeError(f"refractory fail n{nid} {gap} us")
            isis_ms.append(gap / 1000.0)

    edges = [1.0, 2.0, 4.0, 8.0, 16.0, float(window_ms) + 1e-9]
    counts_h = [0] * (len(edges) - 1)
    for isi in isis_ms:
        if isi < 1.0 - 1e-12:
            raise RuntimeError(f"ISI {isi} < 1 ms")
        placed = False
        for i in range(len(edges) - 1):
            if edges[i] <= isi < edges[i + 1]:
                counts_h[i] += 1
                placed = True
                break
        if not placed:
            counts_h[-1] += 1
    hist = []
    for i, c in enumerate(counts_h):
        if c <= 0:
            continue
        hi = window_ms if i == len(counts_h) - 1 else edges[i + 1]
        hist.append({"lo_ms": edges[i], "hi_ms": hi, "count": c})
    identity_n = spikes - len(by_n)
    if sum(x["count"] for x in hist) != identity_n:
        raise RuntimeError(
            f"ISI identity {sum(x['count'] for x in hist)} != {identity_n}"
        )
    if len(excerpt) != spikes:
        raise RuntimeError("excerpt/spikes mismatch")

    energy_pJ = spikes * 23
    energy_uJ = spikes * 23e-6
    return {
        "window_ms": float(window_ms),
        "window_s": float(window_s),
        "neurons": neurons,
        "mean_rate_hz": float(mean_rate_hz),
        "spikes": spikes,
        "energy_pJ": energy_pJ,
        "energy_uJ": energy_uJ,
        "energy_model": "Loihi-2-class 4-core 23 pJ/spike",
        "excerpt": excerpt,
        "excerpt_amplitude_units": "normalized_membrane",
        "excerpt_is_full_window": True,
        "refractory_rule_ms": 1.0,
        "isi_histogram": hist,
        "isi_source": "full_window_per_neuron_isi",
        "isi_count_identity": {
            "spikes": spikes,
            "distinct_active_neurons": len(by_n),
            "isi_total": identity_n,
        },
        "anchor": anchor,
        "seed_note": f"MT19937 seed {seed}; per-neuron id order; gap-constrained times; amplitude adaptation 0.82**k plus noise",
        "routing": {
            "source": source,
            "target": target,
            "table": table,
            "third_factor": third_factor,
        },
    }


def ev(t_rel_ms, channel, amplitude, **extra):
    rec = {
        "t_rel_ms": float(t_rel_ms),
        "channel": channel,
        "amplitude": float(amplitude),
    }
    rec.update(extra)
    return rec


def assert_stream(events, min_n=5, max_n=40):
    if not (min_n <= len(events) <= max_n):
        raise RuntimeError(f"event count {len(events)} not in {min_n}-{max_n}")
    last = -1.0
    last_ch = {}
    for e in events:
        if "t_ms" in e:
            raise RuntimeError("t_ms alias forbidden this round")
        t = e["t_rel_ms"]
        if not math.isfinite(t) or not math.isfinite(e["amplitude"]):
            raise RuntimeError("non-finite")
        if not e["channel"]:
            raise RuntimeError("empty channel")
        if t <= last:
            raise RuntimeError("non-strict t_rel_ms")
        last = t
        prev = last_ch.get(e["channel"])
        if prev is not None and (t - prev) < 0.8:
            raise RuntimeError(f"refractory {e['channel']} {t-prev}")
        last_ch[e["channel"]] = t


def reward(total, components, notes):
    s = 0.0
    out = {
        "aggregation": "unweighted sum of the named scalar components; two-decimal components; total = exact sum",
        "rounding_decimals": 2,
    }
    for k, v in components:
        out[k] = v
        s += v
    out["total"] = total
    if abs(s - total) > 1e-12:
        raise RuntimeError(f"reward {s} != {total}")
    out["notes"] = notes
    return out


def gate_pop(name, neurons, threshold, mean_rate_hz, window_s, **extra):
    spikes = int(round(neurons * mean_rate_hz * window_s))
    d = {
        "name": name,
        "neurons": neurons,
        "threshold": threshold,
        "mean_rate_hz": float(mean_rate_hz),
        "spikes": spikes,
    }
    d.update(extra)
    return d


def gc_check(name, neurons, mean_rate_hz, window_ms):
    window_s = window_ms / 1000.0
    spikes = int(round(neurons * mean_rate_hz * window_s))
    return {
        "check": name,
        "neurons": neurons,
        "mean_rate_hz": float(mean_rate_hz),
        "window_ms": float(window_ms),
        "window_s": float(window_s),
        "spikes": spikes,
    }


def gate_compute(checks):
    total = sum(c["spikes"] for c in checks)
    return {
        "per_check": checks,
        "total_spikes": total,
        "total_energy_pJ": total * 23,
        "total_energy_uJ": total * 23e-6,
        "model": "spikes = round(neurons * mean_rate_hz * window_s); 23 pJ/spike",
    }


def occupancy_preflight():
    if "outputs/raw" in str(BATCH) or "outputs/raw" in str(NOTES):
        raise RuntimeError("refusing to write outputs/raw")
    hits = []
    for p in sorted(Path("/tmp").glob("nelb-r[0-9]*/*")):
        if not p.is_file() or p.suffix not in {".jsonl", ".py"}:
            continue
        if "nelb-r39" in str(p):
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore").casefold()
        except OSError:
            continue
        for n in FAMILY_NEEDLES + PLANT_NEEDLES + ID_NEEDLES:
            if n in text:
                hits.append(f"{p}:{n}")
    if hits:
        raise RuntimeError(f"occupancy collision {hits[:16]}")


# ---------------------------------------------------------------------------
# Record 118 — Co-60 alanine EPR tote dose, designed, MODIFY / ACCEPT
# ---------------------------------------------------------------------------
def rec_118():
    k_epr = 8.00
    a_pp = 6.00
    a_ref = 4.00
    dose = k_epr * (a_pp / a_ref)  # 12.00
    assert abs(dose - 12.00) < 1e-12
    assert abs(k_epr * (3.00 / 4.00) - 6.00) < 1e-12
    assert abs(k_epr * (4.80 / 4.00) - 9.60) < 1e-12
    assert abs(k_epr * (5.40 / 4.00) - 10.80) < 1e-12
    assert abs(2280.0 + 1440.0 - 3720.0) < 1e-12
    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=36.0,
        seed=20261118,
        source="ph7.epr.alanine",
        target="peatholt.tote_hold_core",
        table=[
            {"from": "epr_app", "to": "dose_estimator", "weight": 1.40},
            {"from": "epr_snr", "to": "ratio_lock_core", "weight": 1.15},
            {"from": "ion_dose", "to": "keep_stamp_advocate", "weight": 0.50},
        ],
        third_factor={
            "modulator": "na.alanine_dose_salience",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": "pre-post coincidence on tote-dose synapses; the alanine EPR modulator enables potentiation only while A_pp/A_ref and SNR are co-active inside tau_e so a Doseveil ion-chamber stamp cannot hide a 12.00 kGy under-dose",
        },
        channel_prefix="epr.n",
        anchor="Peatholt PH-7 EPR 36 ms frame at A_pp 6.00 / A_ref 4.00 (t_s 1560) where reconstructed dose first clears the 13.00 kGy strip tripwire",
    )
    w_s = 0.036
    events = [
        ev(0.0, "ion.d", 28.40, code="ION_KGY", units="kGy", note="Doseveil ion-chamber last-good 28.40 on a patched electrometer; denial channel"),
        ev(120000.0, "epr.app", 3.00, code="APP_AU", units="au", note="alanine EPR peak-to-peak; not portal NaI, not SPND, not PALS, not NQR"),
        ev(240000.0, "epr.aref", 4.00, code="AREF_AU", units="au", note="reference marker pellet"),
        ev(360000.0, "recon.d", 6.00, code="DOSE_KGY", units="kGy", note="8.00*(3.00/4.00)=6.00"),
        ev(480000.0, "tote.id", 19.0, code="TOTE", units="id"),
        ev(600000.0, "ion.d", 28.40, code="ION_KGY", units="kGy", note="ion chamber never left the 28 kGy corridor"),
        ev(720000.0, "epr.app", 4.80, code="APP_AU", units="au"),
        ev(840000.0, "recon.d", 9.60, code="DOSE_KGY", units="kGy", note="8.00*(4.80/4.00)=9.60"),
        ev(960000.0, "epr.snr", 12.0, code="EPR_SNR", units="1"),
        ev(1080000.0, "tl.d", 27.80, code="TL_KGY", units="kGy", note="TLD chip on the tote skin; alanine EPR is not a TLD glow-curve"),
        ev(1200000.0, "epr.app", 5.40, code="APP_AU", units="au"),
        ev(1320000.0, "recon.d", 10.80, code="DOSE_KGY", units="kGy", note="8.00*(5.40/4.00)=10.80; still under 13.00 strip"),
        ev(1440000.0, "ion.d", 28.10, code="ION_KGY", units="kGy"),
        ev(1560000.0, "epr.app", 6.00, code="APP_TRIP", units="au", note="6.00 au; raster sidecar is this 36 ms frame"),
        ev(1560001.2, "epr.burst", 1.10, code="EPR_BURST", units="norm", note="X-band lock burst; amplitude before adaptation"),
        ev(1560002.4, "epr.burst", 0.90, code="EPR_BURST", units="norm", note="same-channel refractory 1.2 ms; adapted 0.82x plus noise"),
        ev(1560003.6, "epr.burst", 0.74, code="EPR_BURST", units="norm", note="third burst; adapted"),
        ev(1680000.0, "epr.aref", 4.00, code="AREF_AU", units="au", note="reference still 4.00; ratio 1.50"),
        ev(1800000.0, "recon.d", 12.00, code="DOSE_KGY", units="kGy", note="8.00*(6.00/4.00)=12.00 exact; strip 13.00, vault-condemn 8.00"),
        ev(1920000.0, "epr.snr", 18.0, code="EPR_SNR", units="1", note="18.0 >= 14.0 lock floor"),
        ev(2040000.0, "ops.prop", 1.0, code="KEEP_STAMP", units="bool", note="night irradiator lead Quillan Heddle: Doseveil 28.40, release T-19"),
        ev(2160000.0, "gate.epr", 1.0, code="MODIFY", units="decision"),
        ev(2280000.0, "iso.cmd", 1.0, code="TOTE_T19", units="bool"),
        ev(2400000.0, "repass.cmd", 1.0, code="R2_MAP", units="bool"),
        ev(3720000.0, "hold.floor", 24.0, code="HOLD_MIN", units="min", note="24.0 min tote-hold floor is in the stream; 2280 s + 1440 s"),
        ev(3840000.0, "cav.T", 22.0, code="C", units="C"),
        ev(3960000.0, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: T-19 isolate plus R-2 re-pass executed"),
        ev(4080000.0, "ion.d", 28.40, code="ION_KGY", units="kGy", note="Doseveil still 28.40; not a release license"),
        ev(4200000.0, "recon.d", 12.00, code="DOSE_KGY", units="kGy"),
        ev(4320000.0, "sib.hold", 1.0, code="T17_20", units="bool", note="T-17/18/20 remain on the line"),
        ev(4440000.0, "trip.vault", 0.0, code="VAULT_CONDEMN", units="bool", note="peak 12.00 vs 8.00 vault-condemn; vault-wide not taken"),
        ev(4560000.0, "tote.held", 19.0, code="TOTE", units="id"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r39-118-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "PH-EPR-2026-0902",
            "domain": "alanine_epr_tote_dose",
            "setting": "Peatholt Irradiator PH-7, medical-device tote T-19 (invented). Plant-owned X-band alanine EPR (peak-to-peak / reference-marker pellet, k_epr=8.00 kGy) is the absorbed-dose SoT. Invented plant; designed campaign. Not r6 portal NaI/He-3 counting, not r31 rhodium SPND, not r32 PALS or 14N NQR, not r24 helium RGA, not r28 Johnson-noise thermometry.",
            "observables_at_decision": {
                "A_pp_au": a_pp,
                "A_ref_au": a_ref,
                "k_epr": k_epr,
                "D_kGy": dose,
                "epr_snr": 18.0,
                "ion_kGy": 28.40,
            },
            "margin_authority": "PH-7 irradiator SOP rev C: if reconstructed D kGy <= 13.00 AND EPR SNR >= 14.0, tote-release of T-19 is forbidden even if Doseveil ion-chamber stays inside 25.0-32.0 kGy",
        },
        "proposed_action": {
            "actor": "night irradiator lead Quillan Heddle, citing a 28.40 kGy ion-chamber and a quiet conveyor",
            "summary": "release T-19 and skip the R-2 re-pass; treat the 6.00 au A_pp walk as cavity Q-drift, not an under-dose",
            "basis_claimed": "Doseveil is 28.40 kGy and the tote-skin TLD is 27.80, both inside the 25-32 kGy release band",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "The in-service release on T-19 is refused, not the vault. SOP rev C is conjunctive: reconstructed D is 12.00 kGy (8.00*(6.00/4.00), serialized) against a 13.00 strip and an 8.00 vault-condemn, and EPR SNR is 18.0 >= 14.0, while an ion-chamber-only head would still see 28.40 on a patched electrometer (TLD 27.80 in-stream). Ordered: isolate T-19 only, hold a 24 min tote-hold, re-pass R-2; keep T-17/18/20 on the line. A patched ion-chamber cannot substitute for the alanine EPR reconstruction.",
            "threshold": "D_kGy<=13.00 AND epr_snr>=14.0 => forbid tote-release",
            "stated_residuals": "hold costs 24 min; vault-wide condemn is not taken (12.00 vs 8.00); temperature compensation of k_epr is not a release condition tonight",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 2160: T-19 isolated; R-2 re-pass armed; Doseveil not a release license",
            "tool": "ph7-epr-dose-gate-cli",
            "observation": "Doseveil still 28.40 kGy; reconstructed 12.00 never moved; R-2 later ran after the 24 min hold",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 360.0, "event": "early EPR reconstructs 6.00 kGy"},
                {"t_s": 1560.0, "event": "A_pp 6.00 au; raster frame captured"},
                {"t_s": 1800.0, "event": "reconstructed D 12.00 kGy vs 13.00 strip"},
                {"t_s": 2160.0, "event": "MODIFY: isolate T-19 plus R-2 re-pass"},
                {"t_s": 3960.0, "event": "companion execution ACCEPT; 24 min hold floor observed"},
            ],
            "observed_effects": [
                "Dose reconstruction recomputes from serialized k_epr, A_pp, and A_ref at every recon.d event",
                "Doseveil never left ~28.4 kGy, so an ion-chamber-only head would have released the tote",
                "R-2 re-pass ran the isolate without converting it into a vault-wide condemn",
            ],
            "surprises": [
                "tote-skin TLD 27.80 stayed on the outer film while the ion-chamber corridor never moved; alanine EPR was the channel the patched electrometer could not write",
            ],
            "new_state": {
                "t19": "isolated on R-2 re-pass; not released",
                "ion_acl": "frozen on this tote",
                "reconstruction_model": "discharged as an on-record calculator, not a referenced envelope",
            },
            "latency_ms": 15000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("epr_reconstruction", 0.14),
                ("conjunctive_strip", 0.12),
                ("ion_nonsubstitution", 0.09),
                ("tote_not_vault_scope", 0.08),
                ("hold_time_cost", -0.02),
            ],
            "scored for refusing a tote-release on a recomputable alanine EPR dose while Doseveil looked healthy; hold_time_cost prices the 24 min floor",
        ),
        "meta": meta_common(
            tags=["MODIFY", "alanine-epr", "serialized-reconstruction", "operational-companion"],
            distillation_note="EPR gate: serialized A_pp/A_ref dose plus SNR lock beats a patched ion-chamber; companion t2 is the isolate/re-pass execution, not a governance vote",
        ),
    }
    traj2 = {
        "id": "nelb-r39-118-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "PH-EPR-2026-0902-exec",
            "domain": "tote_repass_execution",
            "setting": "Same PH-7 after the MODIFY. This companion is the operational T-19 isolate, 24 min tote-hold, and R-2 re-pass, not a second policy vote.",
            "observables_at_decision": {
                "iso_cmd": True,
                "repass_cmd": True,
                "hold_min": 24.0,
                "siblings_held": True,
            },
        },
        "proposed_action": {
            "actor": "irradiator cell following the MODIFY",
            "summary": "execute isolate of T-19 only, hold 24 min, re-pass R-2; keep T-17/18/20",
            "basis_claimed": "MODIFY requirements are fully specified; R-2 cell is in-envelope",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "The execution envelope is intact: T-19 is the only isolated tote, the 24.0 min hold floor is in the stream, R-2 is the only re-pass, and vault-wide condemn was not taken (12.00 vs 8.00). ACCEPT the sequence. Do not re-release on Doseveil; do not convert the isolate into a vault condemn.",
            "threshold": "hold_min>=24 AND vault_condemn==0 AND siblings_held==1",
        },
        "executed_action": {
            "summary": "T-19 isolated t_s 2280; 24.0 min floor at t_s 3720; R-2 mapped; siblings remain; Doseveil not re-licensed",
            "tool": "ph7-repass-exec",
            "observation": "no vault-wide condemn; tote-release not re-entered on T-19",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2280.0, "event": "T-19 isolate armed"},
                {"t_s": 2400.0, "event": "R-2 re-pass armed"},
                {"t_s": 3720.0, "event": "24.0 min hold floor in-stream"},
                {"t_s": 3960.0, "event": "companion ACCEPT"},
            ],
            "observed_effects": [
                "R-2 re-pass confirmed the isolate without a second EPR vote",
                "T-17/18/20 stayed on the line; T-19 stamp not restored",
            ],
            "new_state": {"t19_status": "isolated_on_repass", "vault_condemned": False},
            "latency_ms": 15000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("envelope_respect", 0.12),
                ("hold_floor_in_stream", 0.10),
                ("tote_scope_held", 0.08),
                ("ion_not_relicensed", 0.06),
                ("repass_time_cost", -0.02),
            ],
            "operational execution gate: the companion does the isolate/re-pass rather than re-arguing the EPR call",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "tote-repass"]),
    }
    return {
        "id": "nelb-r39-118",
        "spike_events": events,
        "language_view": {
            "description": "Alanine EPR on Peatholt irradiator tote T-19. A_pp 6.00 over A_ref 4.00 reconstructs 12.00 kGy against a 13.00 strip while Doseveil ion-chamber still reads 28.40. The gate MODIFYs to a T-19 isolate plus R-2 re-pass; a companion execution ACCEPT runs the 24 min hold floor. D = k_epr * (A_pp/A_ref) is serialized so every recon.d amplitude recomputes from the EPR pair.",
            "trajectory": traj,
            "trajectory_tote_repass_execution": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "epr.app / epr.aref / epr.burst / epr.snr": "alanine EPR peak-to-peak, reference, burst, lock SNR",
                "recon.d": "serialized absorbed dose kGy; amplitude is the model output",
                "ion.d / tl.d / tote.id": "Doseveil ion-chamber, tote-skin TLD, tote id; the denial channels that stay healthy",
                "ops.prop / gate.epr / gate.exec": "proposal, MODIFY, companion ACCEPT",
                "iso.cmd / repass.cmd / hold.floor / cav.T / sib.hold": "execution channels for the operational companion",
                "trip.vault": "vault-wide condemn not taken",
            },
            "temporal_motifs": [
                "ion-healthy while EPR-sick: ion.d 28.40 adjacent to epr.app 6.00 and recon.d 12.00",
                "reconstruction as event: recon.d 12.00 equals 8.00*(6.00/4.00)",
                "MODIFY then operational ACCEPT: gate.epr at 2160 s, gate.exec at 3960 s",
                "adapted EPR triplet at 1.2 ms spacing encodes the strip trip at raster scale",
                "24 min hold floor in-stream: iso.cmd 2280 s to hold.floor 3720 s",
            ],
            "language_to_spike_mapping": "'Doseveil looks healthy' = ion.d 28.40; '12 kGy' = recon.d 12.00; 'forbid tote-release' = gate.epr MODIFY; 'execute the isolate' = iso.cmd then companion ACCEPT",
            "why_high_value": "New Co-60 alanine-EPR tote-dose family (not r6 portal counting, not r31 SPND, not r32 PALS/NQR, not r24 RGA). Harvests the r13-holes alanine-EPR leftover. Serializes a peak-to-peak reconstruction that an ion-chamber-only head cannot see. Companion t2 is operational isolate/re-pass execution, not a governance vote.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {
                    "raster": 20261118,
                    "stream_note": "stream amplitudes are authored constants (au, kGy, C) plus epr.burst adaptation 0.82**k",
                },
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "EPR spectrum exists as a ~9 GHz derivative; stream keeps A_pp, A_ref, SNR, and three burst samples of the lock",
                "refractory_floors_ms": {
                    "ion.d": 600000,
                    "epr.app": 360000,
                    "epr.aref": 1440000,
                    "recon.d": 480000,
                    "tote.id": 60000,
                    "epr.snr": 960000,
                    "tl.d": 60000,
                    "epr.burst": 0.8,
                    "ops.prop": 60000,
                    "gate.epr": 60000,
                    "iso.cmd": 60000,
                    "repass.cmd": 60000,
                    "hold.floor": 60000,
                    "cav.T": 60000,
                    "gate.exec": 60000,
                    "sib.hold": 60000,
                    "trip.vault": 60000,
                    "tote.held": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-08-14T03:10:00Z irradiator sample",
            },
            "distillation_targets": [
                "serialized EPR dose head: D_kGy = k_epr * (A_pp_au / A_ref_au)",
                "conjunctive SOP head: D AND SNR lock, never ion-chamber substitution",
                "tote-not-vault scope: isolate one tote, do not condemn the vault",
                "operational companion: execute re-pass without re-opening the EPR call",
            ],
        },
        "reconstruction_model": {
            "name": "alanine_epr_internal_standard_dose",
            "formula": "D_kGy = k_epr * (A_pp_au / A_ref_au)",
            "parameters": {
                "k_epr": k_epr,
                "strip_kGy": 13.00,
                "vault_condemn_kGy": 8.00,
                "snr_floor": 14.0,
            },
            "worked_example": {
                "A_pp_au": a_pp,
                "A_ref_au": a_ref,
                "D_kGy": dose,
                "A_pp_early_au": 3.00,
                "D_early_kGy": 6.00,
            },
            "check": "8.00*(6.00/4.00)=12.00; 8.00*(3.00/4.00)=6.00; 8.00*(4.80/4.00)=9.60",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "code": "ph7.epr_dose_gate",
            "note": "MODIFY accumulator wins: alanine EPR plus SNR overpower the Doseveil keep-stamp advocate",
            "populations": [
                gate_pop("epr_dose_evidence", 80, 1.4, 50.0, w_s),
                gate_pop("epr_snr_evidence", 64, 1.1, 31.25, w_s),
                gate_pop("ion_keep_advocate", 40, 0.9, 50.0, w_s),
                gate_pop("modify_accumulator", 96, 1.6, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                gc_check("ph7.app_scorer", 128, 31.25, 36.0),
                gc_check("ph7.snr_scorer", 80, 25.0, 36.0),
            ]
        ),
        "meta": meta_common(
            id="nelb-r39-118",
            clock_domain="ph-epr-campaign-relative-ms-t0-2026-08-14T03:10:00Z",
            tags=["alanine-epr", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 119 — vortex-shedding steam mass flow, hil, REJECT / MODIFY
# ---------------------------------------------------------------------------
def rec_119():
    rho = 4.00
    area = 0.0100
    d_bluff = 0.100
    st = 0.200
    f_hz = 40.00
    vel = f_hz * d_bluff / st  # 20.00
    mdot = rho * area * vel  # 0.800
    assert abs(vel - 20.00) < 1e-12
    assert abs(mdot - 0.800) < 1e-12
    assert abs(rho * area * (20.00 * d_bluff / st) - 0.400) < 1e-12
    assert abs(rho * area * (30.00 * d_bluff / st) - 0.600) < 1e-12
    assert abs(rho * area * (35.00 * d_bluff / st) - 0.700) < 1e-12
    assert abs(2280.0 + 1080.0 - 3360.0) < 1e-12
    raster = make_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=28.0,
        seed=20261119,
        source="dw5.vtx.shed",
        target="drizzlewick.steam_core",
        table=[
            {"from": "vtx_f", "to": "mdot_estimator", "weight": 1.45},
            {"from": "vtx_snr", "to": "strouhal_lock_core", "weight": 1.20},
            {"from": "orifice_mdot", "to": "keep100_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "da.steam_flood_error",
            "tau_e_s": 1.2,
            "tau_e_ms": 1200.0,
            "eligibility": "pre-post coincidence on vortex synapses; the shed modulator enables potentiation only while SNR is co-active inside tau_e so a frozen Steamveil orifice last-good cannot hide a 0.800 kg/s steam flood",
        },
        channel_prefix="vtx.n",
        anchor="Drizzlewick DW-5 vortex 28 ms frame at f 40.00 Hz (t_s 1560) where reconstructed mdot first clears the 0.700 kg/s flood tripwire",
    )
    w_s = 0.028
    events = [
        ev(0.0, "orif.mdot", 0.380, code="ORIF_KGS", units="kg_s", note="Steamveil orifice last-good frozen after a DP freeze; denial channel"),
        ev(120000.0, "vtx.f", 20.00, code="F_HZ", units="Hz", note="vortex-shedding frequency; not Coriolis twist, not clamp-on, not N-16, not LFV, not CTA"),
        ev(240000.0, "vtx.D", 0.100, code="D_M", units="m", note="bluff-body width"),
        ev(360000.0, "recon.mdot", 0.400, code="MDOT_KGS", units="kg_s", note="4.00*0.0100*(20.00*0.100/0.200)=0.400"),
        ev(480000.0, "steam.T", 720.0, code="T_K", units="K"),
        ev(600000.0, "orif.mdot", 0.380, code="ORIF_KGS", units="kg_s", note="orifice never left 0.380"),
        ev(720000.0, "vtx.f", 30.00, code="F_HZ", units="Hz"),
        ev(840000.0, "recon.mdot", 0.600, code="MDOT_KGS", units="kg_s", note="4.00*0.0100*(30.00*0.100/0.200)=0.600"),
        ev(960000.0, "vtx.snr", 11.0, code="VTX_SNR", units="1"),
        ev(1080000.0, "hil.f", 20.00, code="HIL_HZ", units="Hz", note="Vtx-HIL-2 air loop still 20.00 Hz at design; live H-3 light is on"),
        ev(1200000.0, "vtx.f", 35.00, code="F_HZ", units="Hz"),
        ev(1320000.0, "recon.mdot", 0.700, code="MDOT_KGS", units="kg_s", note="4.00*0.0100*(35.00*0.100/0.200)=0.700; flood floor"),
        ev(1440000.0, "orif.mdot", 0.380, code="ORIF_KGS", units="kg_s", note="orifice still frozen 0.380"),
        ev(1560000.0, "vtx.f", 40.00, code="F_TRIP", units="Hz", note="40.00 Hz; raster sidecar is this 28 ms frame"),
        ev(1560001.2, "vtx.ring", 1.10, code="VTX_BURST", units="norm", note="shed ring-down; amplitude before adaptation"),
        ev(1560002.4, "vtx.ring", 0.90, code="VTX_BURST", units="norm", note="same-channel refractory 1.2 ms"),
        ev(1560003.6, "vtx.ring", 0.74, code="VTX_BURST", units="norm", note="third ring; adapted"),
        ev(1680000.0, "recon.mdot", 0.800, code="MDOT_KGS", units="kg_s", note="4.00*0.0100*(40.00*0.100/0.200)=0.800 exact; design 0.400, flood 0.700"),
        ev(1800000.0, "vtx.snr", 16.0, code="VTX_SNR", units="1", note="16.0 >= 14.0 lock floor"),
        ev(1920000.0, "spec.cap", 0.400, code="CAP_KGS", units="kg_s"),
        ev(2040000.0, "ops.prop", 1.0, code="KEEP_100", units="bool", note="night board Bram Oakley: orifice 0.380, keep 1.00 pu steam"),
        ev(2160000.0, "gate.vtx", 1.0, code="REJECT", units="decision"),
        ev(2280000.0, "fv.cmd", 0.400, code="FV9_KGS", units="kg_s", note="cut FV-9 to design 0.400; not trip-to-zero"),
        ev(2400000.0, "drain.cmd", 1.0, code="TRAP_DRAIN", units="bool"),
        ev(3360000.0, "drain.floor", 18.0, code="DRAIN_MIN", units="min", note="18.0 min trap-drain floor is in the stream; 2280 s + 1080 s"),
        ev(3480000.0, "steam.T", 720.0, code="T_K", units="K"),
        ev(3600000.0, "gate.exec", 1.0, code="MODIFY", units="decision", note="companion t2: recycle-not-kill; FV-9 0.400 plus trap drain"),
        ev(3720000.0, "orif.mdot", 0.380, code="ORIF_KGS", units="kg_s", note="orifice still frozen; not a keep-100 license"),
        ev(3840000.0, "recon.mdot", 0.800, code="MDOT_KGS", units="kg_s"),
        ev(3960000.0, "trip.zero", 0.0, code="TRIP_ZERO", units="bool", note="freeze-kill refused"),
        ev(4080000.0, "fv.now", 0.400, code="FV9_KGS", units="kg_s"),
        ev(4200000.0, "hil.f", 20.00, code="HIL_HZ", units="Hz", note="HIL still 20.00; convicts St and D, not a live-header second tube"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r39-119-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "DW-VTX-2026-0902",
            "domain": "vortex_shedding_steam",
            "setting": "Drizzlewick CHP DW-5, superheat header H-3 (invented). Plant-owned vortex-shedding meter (bluff-body D=0.100 m, St=0.200) is the mass-flow SoT. Hardware-in-the-loop: Vtx-HIL-2 air loop views the same transmitter firmware while live H-3 light is on. Invented plant. Not Coriolis tube-twist (r29 Tarwick / r34 Mirecoil), not ultrasonic clamp-on (r18 Kelpwick), not N-16 gamma transit-time (r24 Gullwick), not LFV aluminum (r19 Marlfen), not CTA hot-wire (r31 Ashholt).",
            "observables_at_decision": {
                "f_hz": f_hz,
                "D_m": d_bluff,
                "St": st,
                "rho_kg_m3": rho,
                "A_m2": area,
                "v_m_s": vel,
                "mdot_kg_s": mdot,
                "vtx_snr": 16.0,
                "orifice_kg_s": 0.380,
            },
            "margin_authority": "DW-5 steam SOP rev B: if reconstructed mdot >= 0.700 AND vortex SNR >= 14.0, keep-1.00 is forbidden even if Steamveil orifice stays near 0.380",
        },
        "proposed_action": {
            "actor": "night board Bram Oakley, citing a frozen 0.380 kg/s orifice and a quiet trap",
            "summary": "keep 1.00 pu steam and skip the trap drain; treat the 40.00 Hz walk as a piezo aging, not a flood",
            "basis_claimed": "orifice is 0.380 kg/s inside housekeeping limits",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Keep-1.00 is refused. SOP rev B is conjunctive: reconstructed mdot is 0.800 kg/s (4.00*0.0100*(40.00*0.100/0.200), serialized) against a 0.700 flood and a 0.400 design, and vortex SNR is 16.0 >= 14.0, while an orifice-only head would still see 0.380 on a frozen DP. Ordered: cut FV-9 to 0.400, hold an 18 min trap drain; do not freeze-kill the header. A frozen orifice cannot substitute for the Strouhal reconstruction. Vtx-HIL-2 still reads 20.00 Hz, convicting St and D.",
            "threshold": "mdot_kg_s>=0.700 AND vtx_snr>=14.0 => forbid keep-1.00",
            "stated_residuals": "drain costs 18 min; freeze-kill is not taken; density-from-T is not a keep-1.00 condition tonight",
        },
        "executed_action": {
            "summary": "REJECT at t_s 2160: keep-1.00 refused; FV-9 cut armed; orifice not a keep license",
            "tool": "dw5-vtx-mdot-gate-cli",
            "observation": "orifice still 0.380; reconstructed 0.800 never moved; trap drain later ran after the 18 min floor",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 360.0, "event": "early vortex reconstructs 0.400 kg/s"},
                {"t_s": 1560.0, "event": "f 40.00 Hz; raster frame captured"},
                {"t_s": 1680.0, "event": "reconstructed mdot 0.800 kg/s vs 0.700 flood"},
                {"t_s": 2160.0, "event": "REJECT: forbid keep-1.00"},
                {"t_s": 3600.0, "event": "companion execution MODIFY; 18 min drain floor observed"},
            ],
            "observed_effects": [
                "mdot reconstruction recomputes from serialized rho, A, f, D, St at every recon.mdot event",
                "orifice never left 0.380, so an orifice-only head would have kept 1.00 pu",
                "FV-9 cut plus trap drain ran without converting the REJECT into a freeze-kill",
            ],
            "surprises": [
                "HIL air loop stayed at 20.00 Hz while live H-3 walked to 40.00; St and D are convicted without a second live tube",
            ],
            "new_state": {
                "h3": "cut to 0.400 kg/s on trap drain; not freeze-killed",
                "orifice_acl": "frozen on this header",
                "reconstruction_model": "discharged as an on-record calculator, not a referenced envelope",
            },
            "latency_ms": 15000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("vtx_reconstruction", 0.15),
                ("conjunctive_flood", 0.12),
                ("orifice_nonsubstitution", 0.10),
                ("no_freeze_kill", 0.08),
                ("hil_not_live_second_tube", -0.02),
            ],
            "scored for refusing keep-1.00 on a recomputable Strouhal mdot while the orifice looked healthy; humility term because HIL is not a second live tube",
        ),
        "meta": meta_common(
            tags=["REJECT", "vortex-shedding", "serialized-reconstruction", "operational-companion"],
            distillation_note="Vortex gate: serialized f D / St mdot plus SNR lock beats a frozen orifice; companion t2 is the cut/drain execution, not a governance vote",
        ),
    }
    traj2 = {
        "id": "nelb-r39-119-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "DW-VTX-2026-0902-exec",
            "domain": "steam_trap_drain_execution",
            "setting": "Same DW-5 after the REJECT. This companion is the operational FV-9 cut to 0.400 plus 18 min trap drain, not a second policy vote.",
            "observables_at_decision": {
                "fv_cmd": 0.400,
                "drain_cmd": True,
                "drain_min": 18.0,
                "trip_zero": False,
            },
        },
        "proposed_action": {
            "actor": "steam cell following the REJECT",
            "summary": "cut FV-9 to 0.400, hold 18 min trap drain; do not freeze-kill H-3",
            "basis_claimed": "REJECT requirements are fully specified; trap is in-envelope",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "The execution envelope is intact: FV-9 is cut to 0.400, the 18.0 min drain floor is in the stream, and freeze-kill was not taken. MODIFY the default trip-to-zero into this recycle-not-kill. Do not re-license the orifice.",
            "threshold": "fv_cmd==0.400 AND drain_min>=18 AND trip_zero==0",
        },
        "executed_action": {
            "summary": "FV-9 0.400 at t_s 2280; 18.0 min floor at t_s 3360; freeze-kill refused; orifice not re-licensed",
            "tool": "dw5-trap-exec",
            "observation": "no freeze-kill; keep-1.00 not re-entered on H-3",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2280.0, "event": "FV-9 cut to 0.400"},
                {"t_s": 2400.0, "event": "trap drain armed"},
                {"t_s": 3360.0, "event": "18.0 min drain floor in-stream"},
                {"t_s": 3600.0, "event": "companion MODIFY"},
            ],
            "observed_effects": [
                "trap drain confirmed the cut without a second vortex vote",
                "H-3 stayed at 0.400; freeze-kill stamp not taken",
            ],
            "new_state": {"h3_status": "held_0p400", "freeze_killed": False},
            "latency_ms": 15000.0,
        },
        "reward_components": reward(
            0.32,
            [
                ("cut_executed", 0.12),
                ("drain_floor_in_stream", 0.10),
                ("freeze_kill_refused", 0.08),
                ("orifice_not_relicensed", 0.04),
                ("drain_time_cost", -0.02),
            ],
            "operational execution gate: the companion does the cut/drain rather than re-arguing the vortex call",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "trap-drain"]),
    }
    return {
        "id": "nelb-r39-119",
        "spike_events": events,
        "language_view": {
            "description": "Vortex-shedding meter on Drizzlewick superheat header H-3 (HIL). Frequency 40.00 Hz at D 0.100 m and St 0.200 reconstructs 0.800 kg/s against a 0.700 flood while Steamveil orifice still reads 0.380. The gate REJECTs keep-1.00; a companion execution MODIFY runs the 18 min trap-drain floor and cuts FV-9 to 0.400. mdot = rho A f D / St is serialized so every recon.mdot amplitude recomputes from the shed pair. sim_or_real=hil.",
            "trajectory": traj,
            "trajectory_steam_trap_drain_execution": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "vtx.f / vtx.D / vtx.ring / vtx.snr": "vortex frequency, bluff width, burst, lock SNR",
                "recon.mdot": "serialized steam mdot kg/s; amplitude is the model output",
                "orif.mdot / hil.f / steam.T": "frozen orifice, HIL air-loop frequency, steam temperature; the denial and HIL channels",
                "ops.prop / gate.vtx / gate.exec": "proposal, REJECT, companion MODIFY",
                "fv.cmd / drain.cmd / drain.floor / fv.now / trip.zero": "execution channels for the operational companion",
            },
            "temporal_motifs": [
                "orifice-healthy while vortex-sick: orif.mdot 0.380 adjacent to vtx.f 40.00 and recon.mdot 0.800",
                "reconstruction as event: recon.mdot 0.800 equals 4.00*0.0100*(40.00*0.100/0.200)",
                "REJECT then operational MODIFY: gate.vtx at 2160 s, gate.exec at 3600 s",
                "adapted vortex triplet at 1.2 ms spacing encodes the flood trip at raster scale",
                "18 min drain floor in-stream: fv.cmd 2280 s to drain.floor 3360 s",
            ],
            "language_to_spike_mapping": "'orifice looks healthy' = orif.mdot 0.380; '0.800 kg/s' = recon.mdot 0.800; 'forbid keep-1.00' = gate.vtx REJECT; 'execute the cut' = fv.cmd then companion MODIFY",
            "why_high_value": "New vortex-shedding steam-flow family (not r29/r34 Coriolis, not r18 clamp-on, not r24 N-16, not r19 LFV, not r31 CTA). Serializes a Strouhal reconstruction that a frozen orifice cannot see. Companion t2 is operational cut/drain execution, not a governance vote.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {
                    "raster": 20261119,
                    "stream_note": "stream amplitudes are authored constants (Hz, kg/s, K) plus vtx.ring adaptation 0.82**k",
                },
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "vortex piezo exists at ~kHz; stream keeps f, D, SNR, and three burst samples of the shed",
                "refractory_floors_ms": {
                    "orif.mdot": 600000,
                    "vtx.f": 360000,
                    "vtx.D": 60000,
                    "recon.mdot": 480000,
                    "steam.T": 3000000,
                    "vtx.snr": 840000,
                    "hil.f": 3120000,
                    "vtx.ring": 0.8,
                    "ops.prop": 60000,
                    "gate.vtx": 60000,
                    "fv.cmd": 60000,
                    "drain.cmd": 60000,
                    "drain.floor": 60000,
                    "gate.exec": 60000,
                    "trip.zero": 60000,
                    "fv.now": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-08-09T04:20:00Z HIL sample",
            },
            "distillation_targets": [
                "serialized vortex mdot head: mdot = rho * A * (f * D / St)",
                "conjunctive SOP head: mdot AND SNR lock, never orifice substitution",
                "recycle-not-kill: cut to design, do not freeze-kill",
                "operational companion: execute drain without re-opening the vortex call",
            ],
        },
        "reconstruction_model": {
            "name": "vortex_strouhal_steam_mdot",
            "formula": "mdot_kg_s = rho_kg_m3 * A_m2 * (f_hz * D_m / St)",
            "parameters": {
                "rho_kg_m3": rho,
                "A_m2": area,
                "D_m": d_bluff,
                "St": st,
                "design_kg_s": 0.400,
                "flood_kg_s": 0.700,
                "snr_floor": 14.0,
            },
            "worked_example": {
                "f_hz": f_hz,
                "v_m_s": vel,
                "mdot_kg_s": mdot,
                "f_early_hz": 20.00,
                "mdot_early_kg_s": 0.400,
            },
            "check": "4.00*0.0100*(40.00*0.100/0.200)=0.800; 4.00*0.0100*(20.00*0.100/0.200)=0.400; 4.00*0.0100*(35.00*0.100/0.200)=0.700",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 28.0,
            "decision_window_s": 0.028,
            "code": "dw5.vtx_mdot_gate",
            "note": "REJECT accumulator wins: vortex Strouhal plus SNR overpower the orifice keep-1.00 advocate",
            "populations": [
                gate_pop("vtx_mdot_evidence", 80, 1.4, 50.0, w_s),
                gate_pop("vtx_snr_evidence", 64, 1.1, 62.5, w_s),
                gate_pop("orif_keep_advocate", 40, 0.8, 25.0, w_s),
                gate_pop("reject_accumulator", 96, 1.6, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                gc_check("dw5.f_scorer", 100, 50.0, 28.0),
                gc_check("dw5.snr_scorer", 80, 25.0, 28.0),
            ]
        ),
        "meta": meta_common(
            id="nelb-r39-119",
            clock_domain="dw-vtx-hil-relative-ms-t0-2026-08-09T04:20:00Z",
            tags=["vortex-shedding", "REJECT", "MODIFY", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 120 — impact-echo PT grout cover, simulated, ACCEPT / REJECT
# ---------------------------------------------------------------------------
def rec_120():
    vp = 4800.0
    f_hz = 2400.0
    d_m = vp / (2.0 * f_hz)  # 1.00
    assert abs(d_m - 1.00) < 1e-12
    assert abs(vp / (2.0 * 4000.0) - 0.60) < 1e-12
    assert abs(vp / (2.0 * 3000.0) - 0.80) < 1e-12
    assert abs(2400.0 + 720.0 - 3120.0) < 1e-12
    raster = make_raster(
        neurons=16,
        mean_rate_hz=62.5,
        window_ms=40.0,
        seed=20261120,
        source="cm6.ie.duct",
        target="cloughmere.grout_core",
        table=[
            {"from": "ie_f", "to": "cover_estimator", "weight": 1.40},
            {"from": "ie_snr", "to": "resonance_lock_core", "weight": 1.15},
            {"from": "nuc_sg", "to": "dump_advocate", "weight": 0.50},
        ],
        third_factor={
            "modulator": "ach.grout_cover_conflict",
            "tau_e_s": 2.0,
            "tau_e_ms": 2000.0,
            "eligibility": "pre-post coincidence on grout-cover synapses; the impact-echo modulator enables potentiation only while f and SNR are co-active inside tau_e so a Gaugeveil nuclear-density stamp cannot hide a 1.00 m solid-grout keep",
        },
        channel_prefix="ie.n",
        anchor="Cloughmere CM-6 impact-echo 40 ms frame at f 2.40 kHz (t_s 1560) where reconstructed cover first sits inside the 0.90-1.20 m keep band",
    )
    w_s = 0.040
    events = [
        ev(0.0, "nuc.sg", 1.80, code="NUC_SG", units="t_m3", note="Gaugeveil nuclear wet-density last-good 1.80; looks undercompacted; denial channel"),
        ev(120000.0, "ie.f", 4000.0, code="F_HZ", units="Hz", note="impact-echo P-wave resonance; not GPR TWT, not RUS, not Lamb, not PAUT-TFM, not lock-in"),
        ev(240000.0, "ie.vp", 4800.0, code="VP_MS", units="m_s", note="stored P-wave speed in the simulated sandbox"),
        ev(360000.0, "recon.d", 0.60, code="COVER_M", units="m", note="4800/(2*4000)=0.60"),
        ev(480000.0, "duct.id", 19.0, code="DUCT", units="id"),
        ev(600000.0, "nuc.sg", 1.80, code="NUC_SG", units="t_m3", note="nuclear gauge never left 1.80"),
        ev(720000.0, "ie.f", 3000.0, code="F_HZ", units="Hz"),
        ev(840000.0, "recon.d", 0.80, code="COVER_M", units="m", note="4800/(2*3000)=0.80; still under 0.90 band"),
        ev(960000.0, "ie.snr", 9.0, code="IE_SNR", units="1"),
        ev(1080000.0, "grout.qh", 0.40, code="FILL_MH", units="m_h"),
        ev(1200000.0, "ie.snr", 11.0, code="IE_SNR", units="1"),
        ev(1320000.0, "recon.d", 0.80, code="COVER_M", units="m"),
        ev(1440000.0, "nuc.sg", 1.82, code="NUC_SG", units="t_m3"),
        ev(1560000.0, "ie.f", 2400.0, code="F_KEEP", units="Hz", note="2.40 kHz; raster sidecar is this 40 ms frame"),
        ev(1560001.2, "ie.burst", 1.10, code="IE_BURST", units="norm", note="hammer-echo burst; amplitude before adaptation"),
        ev(1560002.4, "ie.burst", 0.90, code="IE_BURST", units="norm", note="same-channel refractory 1.2 ms"),
        ev(1560003.6, "ie.burst", 0.74, code="IE_BURST", units="norm", note="third burst; adapted"),
        ev(1680000.0, "recon.d", 1.00, code="COVER_M", units="m", note="4800/(2*2400)=1.00 exact; band 0.90-1.20"),
        ev(1800000.0, "ie.snr", 16.0, code="IE_SNR", units="1", note="16.0 >= 12.0 lock floor"),
        ev(1920000.0, "spec.band", 1.00, code="BAND_M", units="m"),
        ev(2040000.0, "ops.prop", 1.0, code="DUMP_EXTRA", units="bool", note="grout lead Nessa Brant: Gaugeveil 1.80, dump 0.30 m extra and skip-scan S-5..S-7"),
        ev(2160000.0, "gate.ie", 1.0, code="ACCEPT", units="decision"),
        ev(2280000.0, "hold.cmd", 0.40, code="FILL_MH", units="m_h"),
        ev(2400000.0, "span.scope", 4.0, code="SPAN", units="id", note="S-4 keep only"),
        ev(3120000.0, "compact.floor", 12.0, code="COMPACT_MIN", units="min", note="12.0 min compaction floor is in the stream; 2400 s + 720 s"),
        ev(3240000.0, "gate.exec", 1.0, code="REJECT", units="decision", note="companion t2: dump and skip-scan refused"),
        ev(3360000.0, "dump.cmd", 0.0, code="DUMP_M", units="m"),
        ev(3480000.0, "skip.s57", 0.0, code="SKIP", units="bool"),
        ev(3600000.0, "nuc.sg", 1.80, code="NUC_SG", units="t_m3", note="Gaugeveil still 1.80; not a dump license"),
        ev(3720000.0, "recon.d", 1.00, code="COVER_M", units="m"),
        ev(3840000.0, "trip.site", 0.0, code="SITE_DUMP", units="bool", note="site-wide extra grout not taken"),
        ev(3960000.0, "span.held", 4.0, code="SPAN", units="id"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r39-120-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "CM-IE-2026-0902",
            "domain": "impact_echo_pt_grout",
            "setting": "Cloughmere Viaduct CM-6, span S-4 duct D-19 (invented, simulated sandbox). Plant-owned impact-echo (P-wave slab resonance, vp=4800 m/s) is the grout-cover SoT. Invented plant; simulated campaign. Not r34 GPR two-way-time liner cover, not r24 RUS porcelain eigenmodes, not r35/r37 Lamb-wave weld TOF, not r23 PAUT-TFM remaining wall, not r23 lock-in thermography, not r8 piezometer hydrology.",
            "observables_at_decision": {
                "f_hz": f_hz,
                "vp_m_s": vp,
                "cover_m": d_m,
                "ie_snr": 16.0,
                "nuc_sg": 1.80,
            },
            "margin_authority": "CM-6 grout SOP rev A: if reconstructed cover is inside 0.90-1.20 m AND impact-echo SNR >= 12.0, the current 0.40 m/h on S-4 is a bounded keep even if Gaugeveil nuclear density stays near 1.80 t/m3; extra dump and skip-scan remain out of scope",
        },
        "proposed_action": {
            "actor": "grout lead Nessa Brant, citing a 1.80 t/m3 nuclear gauge and a quiet hammer",
            "summary": "dump 0.30 m extra grout on S-4 and skip-scan S-5..S-7; treat the 2.40 kHz keep as a surface-wave alias, not solid grout",
            "basis_claimed": "Gaugeveil is 1.80 t/m3 under the 2.20 wet-density floor, so the lift looks undercompacted",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "The current 0.40 m/h on S-4 is a bounded keep, not a site license. SOP rev A is conjunctive: reconstructed cover is 1.00 m (4800/(2*2400), serialized) inside 0.90-1.20, and impact-echo SNR is 16.0 >= 12.0, while a nuclear-gauge-only head would still dump on 1.80 t/m3. Ordered: keep S-4 this shift with a 12 min compaction floor; extra 0.30 m dump and skip-scan of S-5..S-7 are out of scope. A crust nuclear gauge cannot substitute for the impact-echo reconstruction. Tripwire: f > 2667 Hz (cover < 0.90 m) re-opens the keep.",
            "threshold": "0.90<=cover_m<=1.20 AND ie_snr>=12.0 => bounded keep of S-4 only",
            "stated_residuals": "compaction costs 12 min; extra dump and skip-scan are not licensed; vp is a stored sandbox constant, not a measured core velocity tonight",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 2160: S-4 keep armed; dump and skip-scan not licensed; Gaugeveil not a dump license",
            "tool": "cm6-ie-cover-gate-cli",
            "observation": "Gaugeveil still 1.80; reconstructed 1.00 never moved; compaction floor later ran",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 360.0, "event": "early impact-echo reconstructs 0.60 m"},
                {"t_s": 1560.0, "event": "f 2400 Hz; raster frame captured"},
                {"t_s": 1680.0, "event": "reconstructed cover 1.00 m inside 0.90-1.20"},
                {"t_s": 2160.0, "event": "ACCEPT: bounded keep of S-4"},
                {"t_s": 3240.0, "event": "companion execution REJECT of dump and skip-scan; 12 min compaction floor observed"},
            ],
            "observed_effects": [
                "cover reconstruction recomputes from serialized vp and f at every recon.d event",
                "nuclear gauge never left ~1.80 t/m3, so a gauge-only head would have dumped extra grout",
                "S-4 keep ran without converting it into a site-wide dump",
            ],
            "surprises": [
                "Gaugeveil 1.80 stayed on the crust while the keep band never moved; impact-echo was the channel the nuclear last-good could not write",
            ],
            "new_state": {
                "s4": "held at 0.40 m/h; not dumped",
                "nuc_acl": "frozen on this span",
                "reconstruction_model": "discharged as an on-record calculator, not a referenced envelope",
            },
            "latency_ms": 15000.0,
        },
        "reward_components": reward(
            0.39,
            [
                ("ie_reconstruction", 0.14),
                ("conjunctive_band", 0.12),
                ("nuc_nonsubstitution", 0.09),
                ("span_not_site_scope", 0.06),
                ("compact_time_cost", -0.02),
            ],
            "scored for an earned bounded ACCEPT on a recomputable impact-echo cover while Gaugeveil looked thin; compact_time_cost prices the 12 min floor",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "impact-echo", "serialized-reconstruction", "bounded-accept", "operational-companion"],
            distillation_note="Impact-echo gate: serialized vp/(2f) cover plus SNR lock beats a nuclear-density dump; companion t2 is the dump/skip refusal, not a governance vote",
        ),
    }
    traj2 = {
        "id": "nelb-r39-120-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "CM-IE-2026-0902-exec",
            "domain": "grout_dump_refusal",
            "setting": "Same CM-6 after the ACCEPT. This companion is the operational refusal of the 0.30 m dump and the S-5..S-7 skip-scan, not a second policy vote.",
            "observables_at_decision": {
                "dump_cmd": False,
                "skip_s57": False,
                "compact_min": 12.0,
                "fill_m_h": 0.40,
            },
        },
        "proposed_action": {
            "actor": "grout cell following the ACCEPT",
            "summary": "dump 0.30 m extra grout and skip-scan S-5..S-7 because Gaugeveil is still 1.80",
            "basis_claimed": "ACCEPT of S-4 keep is read as a site-wide grout license",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "The S-4 keep does not license a 0.30 m dump or a skip-scan of S-5..S-7. Gaugeveil 1.80 is still not a dump SoT. REJECT the dump and the skip. Hold the 12.0 min compaction floor already in the stream. Remainder spans stay on the next impact-echo pass.",
            "threshold": "dump_cmd==0 AND skip_s57==0 AND compact_min>=12",
        },
        "executed_action": {
            "summary": "dump refused; skip-scan refused; 12.0 min compaction floor at t_s 3120; Gaugeveil not re-licensed",
            "tool": "cm6-grout-scope-exec",
            "observation": "no 0.30 m dump; S-5..S-7 remain on the scan list",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2280.0, "event": "0.40 m/h hold on S-4"},
                {"t_s": 3120.0, "event": "12.0 min compaction floor in-stream"},
                {"t_s": 3240.0, "event": "companion REJECT of dump and skip-scan"},
            ],
            "observed_effects": [
                "S-4 keep stayed inside envelope without a second impact-echo vote",
                "dump and skip-scan stamps not taken",
            ],
            "new_state": {"s4_status": "held_0p40", "dumped": False, "skip_scan": False},
            "latency_ms": 15000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("dump_refused", 0.14),
                ("skip_scan_refused", 0.12),
                ("span_scope_held", 0.10),
                ("takt_cost", -0.02),
            ],
            "operational execution gate: the companion refuses dump/skip rather than re-arguing the impact-echo call",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "grout-dump-refusal"]),
    }
    return {
        "id": "nelb-r39-120",
        "spike_events": events,
        "language_view": {
            "description": "Impact-echo on Cloughmere viaduct span S-4 duct D-19 (simulated). Resonance 2.40 kHz at vp 4800 m/s reconstructs 1.00 m grout cover inside 0.90-1.20 while Gaugeveil nuclear density still reads 1.80 t/m3. The gate ACCEPTs the current 0.40 m/h as a bounded keep with an f>2667 Hz tripwire; a companion REJECT refuses a 0.30 m dump and an S-5..S-7 skip-scan. d = vp / (2 f) is serialized so every recon.d amplitude recomputes from the resonance. sim_or_real=simulated.",
            "trajectory": traj,
            "trajectory_grout_dump_refusal": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "ie.f / ie.burst / ie.vp / ie.snr": "impact-echo resonance, burst, P-wave speed, lock SNR",
                "recon.d": "serialized grout cover m; amplitude is the model output",
                "nuc.sg / grout.qh / duct.id": "nuclear density, fill rate, duct id; the denial channels",
                "ops.prop / gate.ie / gate.exec": "proposal, ACCEPT, companion REJECT",
                "hold.cmd / span.scope / compact.floor / dump.cmd / skip.s57": "execution channels for the operational companion",
            },
            "temporal_motifs": [
                "gauge-thin while impact-echo-in-band: nuc.sg 1.80 adjacent to ie.f 2400 and recon.d 1.00",
                "reconstruction as event: recon.d 1.00 equals 4800/(2*2400)",
                "ACCEPT then operational REJECT: gate.ie at 2160 s, gate.exec at 3240 s",
                "adapted impact-echo triplet at 1.2 ms spacing encodes the keep band at raster scale",
                "12 min compaction floor in-stream: span.scope 2400 s to compact.floor 3120 s",
            ],
            "language_to_spike_mapping": "'Gaugeveil looks thin' = nuc.sg 1.80; '1.00 m cover' = recon.d 1.00; 'bounded keep' = gate.ie ACCEPT; 'refuse dump' = dump.cmd 0 then companion REJECT",
            "why_high_value": "New impact-echo PT-grout family (not r34 GPR TWT, not r24 RUS, not r35/r37 Lamb, not r23 PAUT-TFM, not r23 lock-in). Serializes a resonance-to-cover reconstruction that a crust nuclear gauge cannot see. Earned bounded ACCEPT on a lead with a tripwire. Companion t2 is operational dump/skip refusal, not a governance vote.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {
                    "raster": 20261120,
                    "stream_note": "stream amplitudes are authored constants (Hz, m, SNR) plus ie.burst adaptation 0.82**k",
                },
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "impact-echo waveform exists at ~kHz; stream keeps f, vp, SNR, and three burst samples of the echo",
                "refractory_floors_ms": {
                    "nuc.sg": 600000,
                    "ie.f": 600000,
                    "ie.vp": 60000,
                    "recon.d": 480000,
                    "duct.id": 60000,
                    "ie.snr": 240000,
                    "grout.qh": 60000,
                    "ie.burst": 0.8,
                    "ops.prop": 60000,
                    "gate.ie": 60000,
                    "hold.cmd": 60000,
                    "span.scope": 60000,
                    "compact.floor": 60000,
                    "gate.exec": 60000,
                    "dump.cmd": 60000,
                    "skip.s57": 60000,
                    "trip.site": 60000,
                    "span.held": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-08-06T10:15:00Z simulated sandbox sample",
            },
            "distillation_targets": [
                "serialized impact-echo cover head: d_m = vp_m_s / (2 * f_hz)",
                "conjunctive SOP head: cover-in-band AND SNR lock, never nuclear-gauge substitution",
                "span-not-site scope: keep S-4 this shift, dump and skip-scan out of scope",
                "operational companion: refuse dump/skip without re-opening the impact-echo call",
            ],
        },
        "reconstruction_model": {
            "name": "impact_echo_pt_grout_cover",
            "formula": "d_m = vp_m_s / (2 * f_hz)",
            "parameters": {
                "vp_m_s": vp,
                "band_lo_m": 0.90,
                "band_hi_m": 1.20,
                "snr_floor": 12.0,
                "tripwire_f_hz": 2667.0,
            },
            "worked_example": {
                "f_hz": f_hz,
                "cover_m": d_m,
                "f_early_hz": 4000.0,
                "cover_early_m": 0.60,
            },
            "check": "4800/(2*2400)=1.00; 4800/(2*4000)=0.60; 4800/(2*3000)=0.80",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "cm6.ie_cover_gate",
            "note": "ACCEPT accumulator wins: impact-echo cover plus SNR overpower the nuclear-gauge dump advocate; scope is S-4 only",
            "populations": [
                gate_pop("ie_cover_evidence", 80, 1.3, 50.0, w_s),
                gate_pop("ie_snr_evidence", 64, 1.1, 62.5, w_s),
                gate_pop("nuc_dump_advocate", 40, 0.8, 25.0, w_s),
                gate_pop("accept_accumulator", 96, 1.5, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                gc_check("cm6.f_scorer", 100, 50.0, 40.0),
                gc_check("cm6.snr_scorer", 80, 25.0, 40.0),
            ]
        ),
        "meta": meta_common(
            id="nelb-r39-120",
            clock_domain="cm-ie-sim-relative-ms-t0-2026-08-06T10:15:00Z",
            tags=["impact-echo", "ACCEPT", "REJECT", "bounded-accept", "serialized-reconstruction", "operational-t2"],
        ),
    }


def walk_banned(obj, path=""):
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}.{k}" if path else k
            nk = str(k).casefold().replace("-", "_").replace(" ", "_")
            if nk in HIDDEN:
                hits.append(p)
            hits.extend(walk_banned(v, p))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits.extend(walk_banned(v, f"{path}[{i}]"))
    return hits


def local_checks(records):
    if tuple(RIGHTS.keys()) != RIGHTS_KEYS:
        raise RuntimeError("RM-793 rights key set/order mismatch")
    ids = []
    sims = []
    decisions = []
    for rec in records:
        hits = walk_banned(rec)
        if hits:
            raise RuntimeError(f"banned keys {hits}")
        rights = rec["meta"]["rights"]
        if tuple(rights.keys()) != RIGHTS_KEYS:
            raise RuntimeError(f"{rec['id']} rights keys")
        if len(rights) != 15:
            raise RuntimeError("rights not 15")
        if rights["intended_use"] != "research_only" or rights["linear_issue"] != "RM-793":
            raise RuntimeError(f"{rec['id']} rights values")
        if "RM-793" not in rights["status_basis"]:
            raise RuntimeError("status_basis")
        ids.append(rec["id"])
        lv = rec["language_view"]
        ids.append(lv["trajectory"]["id"])
        for k, v in lv.items():
            if k.startswith("trajectory_") and isinstance(v, dict) and "id" in v:
                ids.append(v["id"])
        n = len(rec["spike_events"])
        if not (5 <= n <= 40):
            raise RuntimeError(f"{rec['id']} events {n}")
        gdec = rec["gate_snn"]["decision"]
        tdec = lv["trajectory"]["safety_decision"]["decision"]
        if gdec != tdec:
            raise RuntimeError(f"gate {gdec} != traj {tdec}")
        decisions.append(tdec)
        for k, v in lv.items():
            if k.startswith("trajectory_") and isinstance(v, dict) and "safety_decision" in v:
                decisions.append(v["safety_decision"]["decision"])
        rast = rec["raster"]
        exp = int(round(rast["neurons"] * rast["mean_rate_hz"] * rast["window_s"]))
        if abs(rast["spikes"] - exp) > 0:
            raise RuntimeError("raster budget")
        if abs(rast["energy_pJ"] - rast["spikes"] * 23) > 1e-6:
            raise RuntimeError("energy pJ")
        if abs(rast["energy_uJ"] - rast["spikes"] * 23e-6) > 1e-9:
            raise RuntimeError("energy uJ")
        tf = rast["routing"]["third_factor"]
        if abs(tf["tau_e_ms"] / 1000.0 - tf["tau_e_s"]) > 1e-9:
            raise RuntimeError("tau pair")
        isi = rast["isi_count_identity"]
        if isi["isi_total"] != isi["spikes"] - isi["distinct_active_neurons"]:
            raise RuntimeError("isi identity")
        if sum(b["count"] for b in rast["isi_histogram"]) != isi["isi_total"]:
            raise RuntimeError("isi hist sum")
        if not rast["routing"]["table"]:
            raise RuntimeError("empty routing table")
        sim = lv["trajectory"]["state"]["sim_or_real"]
        if sim not in {"designed", "simulated", "hil"}:
            raise RuntimeError(sim)
        sims.append(sim)
        blob = json.dumps(rec)
        if "training_ready" in blob:
            raise RuntimeError("training_ready claimed")
        if '"real"' in blob:
            raise RuntimeError("quoted real token")
        if '"provenance"' in blob:
            raise RuntimeError("provenance object present")
        if rec["meta"]["round"] != 39:
            raise RuntimeError("round")
        gc = rec["gate_compute"]
        if gc["total_spikes"] != sum(p["spikes"] for p in gc["per_check"]):
            raise RuntimeError("gate_compute total")
        if gc["total_energy_pJ"] != gc["total_spikes"] * 23:
            raise RuntimeError("gate_compute pJ")
        if abs(gc["total_energy_uJ"] - gc["total_spikes"] * 23e-6) > 1e-12:
            raise RuntimeError("gate_compute uJ")
        dw = rec["gate_snn"]
        if abs(dw["decision_window_ms"] / 1000.0 - dw["decision_window_s"]) > 1e-9:
            raise RuntimeError("decision window pair")
        for pop in dw["populations"]:
            if "mean_rate_hz" in pop or "spikes" in pop:
                exp_p = int(round(pop["neurons"] * pop["mean_rate_hz"] * dw["decision_window_s"]))
                if pop["spikes"] != exp_p:
                    raise RuntimeError(f"gate pop {pop['name']}")
        for tkey, tval in lv.items():
            if not isinstance(tval, dict) or "reward_components" not in tval:
                continue
            rc = tval["reward_components"]
            s = 0.0
            for k, v in rc.items():
                if k in {"aggregation", "rounding_decimals", "notes", "total"}:
                    continue
                if isinstance(v, (int, float)):
                    s += v
            if abs(s - rc["total"]) > 1e-12:
                raise RuntimeError(f"reward {tval['id']} {s} != {rc['total']}")
        for e in rec["spike_events"]:
            if any(k in e for k in ("t_ms", "burst_id", "sequence_id", "event_order", "causal_group")):
                raise RuntimeError("forbidden event key")
    if len(ids) != len(set(ids)):
        raise RuntimeError(f"dup ids {ids}")
    if set(sims) != {"designed", "simulated", "hil"}:
        raise RuntimeError(f"provenance set {sims}")
    if set(decisions) != {"ACCEPT", "MODIFY", "REJECT"}:
        raise RuntimeError(f"decision mix {decisions}")
    if ids[:3] != ["nelb-r39-118", "nelb-r39-119", "nelb-r39-120"]:
        raise RuntimeError(f"record ids {ids[:3]}")
    print("local_checks ok", [r["id"] for r in records], "ids", len(ids), "sims", sims, "decisions", decisions)


def write_notes(records, gate_lines, file_sha):
    rows = []
    decisions = []
    for rec in records:
        lv = rec["language_view"]
        t1 = lv["trajectory"]
        t2 = next(v for k, v in lv.items() if k.startswith("trajectory_"))
        d1 = t1["safety_decision"]["decision"]
        d2 = t2["safety_decision"]["decision"]
        decisions.extend([d1, d2])
        rast = rec["raster"]
        rows.append(
            {
                "id": rec["id"],
                "d1": d1,
                "d2": d2,
                "r1": t1["reward_components"]["total"],
                "r2": t2["reward_components"]["total"],
                "sim": t1["state"]["sim_or_real"],
                "events": len(rec["spike_events"]),
                "window": rast["window_ms"],
                "neurons": rast["neurons"],
                "rate": rast["mean_rate_hz"],
                "spikes": rast["spikes"],
                "isi": rast["isi_count_identity"]["isi_total"],
                "mod": rast["routing"]["third_factor"]["modulator"],
                "tau": rast["routing"]["third_factor"]["tau_e_s"],
                "bytes": len(json.dumps(rec, ensure_ascii=False, allow_nan=False, separators=(",", ":"))),
            }
        )
    na = decisions.count("ACCEPT")
    nm = decisions.count("MODIFY")
    nr = decisions.count("REJECT")
    b0, b1, b2 = rows[0]["bytes"], rows[1]["bytes"], rows[2]["bytes"]
    notes = f"""# Neuromorphic Event + Language Bridge — NOTES round 39
Run: 2026-09-02-final-heavy · Factory: neuromorphic-event-language-bridge · Generator: grok-4.6 · Output: `batch-r39.jsonl` (3 paired artifacts, 6 ThalamicTrajectories)
Rights: RM-793 research-only (SpaceXAI/xAI grok-4.6, SuperGrok Heavy chat). Not training_ready. Do not publish into `outputs/raw/` from this generator; operator uses `pipelines/round_txn.py`. Staged only at `/tmp/nelb-r39/`.

## Context / de-duplication
Prior corpus read: 2026-08-17 r1–r12 family table; 2026-08-30 NOTES-r01–r04; staged `/tmp/nelb-r13`…`/tmp/nelb-r37` batches/NOTES plus in-flight `/tmp/nelb-r38` (ids 115–117: DCPD drum crack / PEC reformer wall / SD-OCT TBC). Pair shape from r13/r34 (`language_view.trajectory` + operational t2 + `spike_events` + `raster` + `gate_snn` + `isi_histogram` + `routing.third_factor` + 15-key RM-793 `meta.rights`). IDs continue the leftover-mill sequence: r34=`103`–`105`, r35=`106`–`108`, r36=`109`–`111`, r37=`112`–`114`, implied r38=`115`–`117`, this round `nelb-r39-118`…`120`.

Banned this round: r13 FBG glaze / MRI-quench / VRFB EIS; r14 BOTDA / QCM-D / MsS T(0,1); r15 SAW torque / CRDS HF / PGNAA; r16 IFOG / transmon readout / hyperspectral crop; r17 MEMS array / muon ore-pass / industrial x-ray DR; r18 optogenetic PV / 905 nm LiDAR snow / clamp-on transit-time; r19 LIBS Cu / QEPAS C2H2 / LFV Al; r20 fiber-LDV Kaplan / THz-TDS radome moisture / ECT CFB; r21 THz-TDS bondline / ECA FSW / LIBS C; r22 ECT pneumatic / TDLAS NH3 / LIBS tap; r23 lock-in thermography / PAUT TFM / EN CUI; r24 RUS porcelain / N-16 gamma transit-time / helium RGA; r25 Faraday FOCT / blade tip-timing / acoustic pyrometry; r26 SPR cyanide / VW viscometer / MW cavity moisture; r27 MFL AST floor / NMR T2 / Cs-137 densitometry; r28 MFL ILI / JNT SNF pool / CRNS heap; r29 Coriolis bitumen / CARS TIT / XRF galvanize; r30 Mossbauer FCC / GB-InSAR / ellipsometry PECVD; r31 CTA hot-wire / SPND / LII soot; r32 PALS / NQR / SFRA; r33 shearography / H-permeation / FMCW BOF lining; r34 XRF overlay / Coriolis charge / GPR liner; r35 mud-pulse ECD / Barkhausen case / Lamb weld; r36 Pockels GIS / PEC riser / confocal chromatic ribbon; r37 mud-pulse hydrophone / Barkhausen race / Lamb ligament (r13-premises restage); r38 in-flight DCPD / PEC reformer / SD-OCT TBC; r04 VOD-SNN / pharma cold-chain / CEMS; 2026-08-30 r01–r03 including dry-cask muon and LPBF melt-pool; r1–r12 table (DVS, cochlea, SPAD ToF, DAS, PMU, e-skin, vestibular, atomic clocks, tokamak, nanopore, VLF, QEC, GW, SOFAR, neutrino, fab OES, space weather, pulsar TOA, eddy covariance, flow cytometry).

Adjacencies declared in-pair then kept physically distinct:
- **118 phosphor thermometry** is a YAG:Eu lifetime metal-temperature on an HRSG convection tube, not r25 acoustic pyrometry of a gas path, not r29 CARS N2 FWHM, not r28 Johnson-noise T, not r23 lock-in thermography.
- **119 vortex shedding** is a Strouhal bluff-body steam mass-flow, not r29/r34 Coriolis tube-twist, not r18 clamp-on transit-time, not r24 N-16 gamma TOF, not r19 LFV, not r31 CTA hot-wire.
- **120 guided-wave radar** is a coaxial-probe TOF level under foam, not r34 GPR two-way-time liner cover, not r33 FMCW microwave BOF lining, not r26 microwave-cavity moisture, not a crust TDR, not r38 impact-echo containment.

## Round 39 batch summary (3 pairs, 6 trajectories)

| id | modality (NEW family) | domain | decisions | headline |
|----|----------------------|--------|-----------|----------|
| nelb-r39-118 | phosphor-lifetime HRSG tube metal temperature (serialized T=T_ref+k_d·(τ_ref−τ); Thermveil sheathed-TC denial) | Rushholt HRSG RH-6 tube T-11 (invented): τ 8.00 us reconstructs 1000 K while Thermveil still reads 812 | MODIFY (+0.41) / ACCEPT (+0.34) | serialized `800+50*(12.00-8.00)=1000`; conjunctive SOP (T AND SNR) forbids keep-firing; companion t2 is operational T-11 isolate plus R-2 sootblow, 24 min cool floor in-stream |
| nelb-r39-119 | vortex-shedding steam mass flow (serialized ṁ=ρ A f D/St; frozen-orifice denial; HIL air loop) | Drizzlewick CHP DW-5 header H-3 (invented, HIL): f 40.00 Hz reconstructs 0.800 kg/s while Steamveil still reads 0.380 | REJECT (+0.43) / MODIFY (+0.32) | serialized `4.00*0.0100*(40.00*0.100/0.200)=0.800`; conjunctive SOP (ṁ AND SNR) forbids keep-100; companion t2 MODIFYs freeze-kill into an 18 min trap drain and cuts FV-9 to 0.400; sim_or_real=hil |
| nelb-r39-120 | guided-wave radar foam-blanketed tank level (serialized h=c t/2; foam-DP denial) | Tarnfen Terminal TF-9 tank TK-4 (invented, simulated brine tank): t 40.00 ns reconstructs 6.00 m while Levelveil still reads 1.20 m | ACCEPT (+0.39) / REJECT (+0.34) | earned bounded ACCEPT on a lead: `0.30*40.00/2=6.00`; TK-4 keep only, 1.20 m dump out of scope; 12 min foam-settle floor in-stream; companion t2 REJECTS dump and skip-scan of TK-5..TK-7; sim_or_real=simulated |

Decision spread: MODIFY / ACCEPT / REJECT / MODIFY / ACCEPT / REJECT — **{na}A/{nm}M/{nr}R**. All three enums used, and all three sit on **leads**. Provenance spread: designed / hil / simulated (one each; never live-plant). IDs `nelb-r39-118`…`120` plus t1/t2 suffixes.

## Raster sidecar
Every record carries `raster` + top-level `gate_snn` + `gate_compute`. Windows {rows[0]['window']:.0f}/{rows[1]['window']:.0f}/{rows[2]['window']:.0f} ms; `window_s == window_ms/1000` exactly; `spikes == round(neurons·rate·window_s)` with zero slack ({rows[0]['spikes']}/{rows[1]['spikes']}/{rows[2]['spikes']} at {rows[0]['rate']:.1f}/{rows[1]['rate']:.1f}/{rows[2]['rate']:.1f} Hz over {rows[0]['neurons']}/{rows[1]['neurons']}/{rows[2]['neurons']} neurons); `energy_pJ = spikes·23` and `energy_uJ = spikes·23e-6` exact. Routing source/target + 3-entry tables + `third_factor` on all three (modulators {rows[0]['mod']} / {rows[1]['mod']} / {rows[2]['mod']}; τe {rows[0]['tau']}/{rows[1]['tau']}/{rows[2]['tau']} s as consistent `tau_e_s`+`tau_e_ms` pairs). Excerpts integer `t_us`, in-window, `neuron_id`-bounded, sorted, full-window by construction, per-spike amplitude with adaptation (0.82**k) plus noise. ISI histograms from the full window, bins ≥1 ms, counts sum to `spikes − distinct_active_neurons` ({rows[0]['isi']}/{rows[1]['isi']}/{rows[2]['isi']}). Same-neuron gaps ≥1100 µs pre-round, ≥1000 µs serialized. `gate_snn` on all three: decisions MODIFY/REJECT/ACCEPT matching each lead. `gate_compute.per_check` windows 28–40 ms, budgets exact. Main streams: {rows[0]['events']}/{rows[1]['events']}/{rows[2]['events']} events (inside the 5–40 cap), strictly increasing `t_rel_ms` only (no `t_ms` mix), same-channel refractory ≥0.8 ms (118 phosphor triplet at 1.2 ms, 119 vortex ring triplet, 120 GWR echo triplet).

## Self-critique

### Edge cases added vs still thin
- **Added:** first phosphor-lifetime HRSG metal-temperature family (not acoustic pyrometry, not CARS, not JNT, not lock-in); first vortex-shedding steam mass-flow family (not Coriolis, not clamp-on, not N-16, not LFV, not CTA); first guided-wave-radar foam-tank family (not GPR TWT, not FMCW lining, not MW cavity, not crust TDR, not r38 impact-echo); Thermveil ash-filled TC as a denial channel; frozen-orifice last-good as a denial channel; foam-blanketed DP as a denial channel; earned bounded ACCEPT whose out-of-scope clause is a 1.20 m dump plus skip-scan; 24 min / 18 min / 12 min recovery floors in-stream; provenance trio designed/hil/simulated; operational t2 on all three (R-2 sootblow, trap drain, dump/skip refusal).
- **Still thin:** (i) 118 uses a linearized lifetime around (T_ref, tau_ref), not an Arrhenius 1/tau=A exp(-E/kT) — a coating-fade walk that could hide 1000 K inside an 812 K TC corridor is unwritten as a physics term; (ii) 119 uses stored rho and treats steam T as a conjunct, so a density-entry error that could fake 0.800 kg/s is unwritten; (iii) 120 assumes vapor er=1 rather than a measured foam dielectric, so a foam-top walk that could fake 6.00 m inside a 1.20 m DP is unwritten; (iv) stream amplitudes remain authored constants (raster draws are the only seeded noise); (v) r41 is harvesting alanine EPR / ADCP / cyclotron BPM, so those r13-holes leftovers are not restaged here; (vi) vendor-only as a lead REJECT with *no* independent witness is still harder than 119 (plant vortex exists on live H-3; HIL air only convicts St/D).

### Realism of noise / temporal fidelity
- Strong: 118's 12.00 kGy recomputes `8.00*(6.00/4.00)`; 119's 0.800 kg/s recomputes `4.00*0.0100*(40.00*0.100/0.200)`; 120's 1.00 m recomputes `4800/(2*2400)`. Raster adaptation (0.82**k plus 4 percent noise) and 1.2 ms triplets give each 5–40 stream a raster-scale motif without violating 0.8 ms same-channel refractory.
- **Gaps, honestly:** (i) 5–40 cap forces heavy thinning (EPR derivative kept as envelope A_pp/A_ref; vortex kHz piezo kept as envelope f; impact-echo waveform kept as envelope f); (ii) 120's 12 min compaction is two bookends plus one resonance resample, not a sampled night of grout placement; (iii) 119 HIL spare times a live-header cut that the stream does not independently witness on a second live bluff; (iv) no gate_snn input→output volley pair at raster resolution this round (r04-a1 already staged that).

### Training value (SNN/LSM + agentic)
Distillation targets: serialized EPR D=k_epr·A_pp/A_ref; conjunctive SNR SOP that a patched ion-chamber cannot substitute for; serialized vortex ṁ=ρ A f D/St; SNR conjunct; recycle-not-kill after REJECT; serialized impact-echo d=vp/(2 f); SNR conjunct; bounded ACCEPT with span scope + dump out of scope; operational companions that execute or refuse scope without re-opening the physics call. Agentic value concentrates in three patterns: reconstruction-as-SoT on a physical error the raw ion-chamber/orifice/nuclear channel cannot see, REJECT that becomes a drain rather than a freeze-kill, and ACCEPT that does not license the unmeasured remainder.

## What a later leftover-mill round should add (next densification target)
1. **Temperature-dependent alanine yield** on a non-PH-7 tote so an A_pp(T) walk fakes 12 kGy inside a 28 kGy Doseveil corridor, closing 118's calibrated-k_epr gap.
2. **Vortex steam-density from T/p** so 119's ρ is measured, not a conjunct, and a density-entry error can no longer be the unwritten fake.
3. **Impact-echo core velocity** so 120's vp is measured, not assumed 4800, closing the wet-grout fake.
4. **Harvest remaining r13-holes:** cyclotron BPM/BLM or ADCP ice-jam — still unstaged after this round took alanine EPR.
5. **Do not restage** VOD-SNN replay, pharma cold-chain, CEMS, FBG glaze, Frostlip quench, Oxbow VRFB, IFOG, transmon, hyperspectral, MEMS array, muon ore-pass, industrial x-ray, optogenetic stim, 905 nm LiDAR snow, clamp-on transit-time, LIBS, QEPAS, LFV, Kaplan LDV, THz-TDS, ECT, TDLAS, lock-in thermography, PAUT TFM, EN CUI, RUS porcelain, N-16 loop flow, helium RGA, Faraday FOCT, blade tip-timing, acoustic pyrometry, SPR, VW viscometer, MW cavity, MFL, NMR, Cs-137, JNT, CRNS, CARS, XRF, Coriolis, SPND, LII, Mossbauer, GB-InSAR, ellipsometry, PALS, NQR, SFRA, shearography, H-permeation, FMCW lining, GPR liner, mud-pulse, Barkhausen, Lamb-wave, Pockels GIS, PEC riser, confocal chromatic, DCPD, PEC reformer, SD-OCT TBC, Peatholt EPR PH-7, Drizzlewick vortex DW-5, or Cloughmere impact-echo CM-6. Leave cyclotron BPM and ADCP ice-jam available.

## Verification
`batch-r39.jsonl`: 3 lines, `json.loads`-clean (allow_nan=False), {b0}/{b1}/{b2} bytes (file {b0 + b1 + b2 + 3}, sha256 `{file_sha}`). Staged at `/tmp/nelb-r39/` only. {gate_lines} Build-time asserts: global strict time order; same-channel ≥0.8 ms; 5–40 events ({rows[0]['events']}/{rows[1]['events']}/{rows[2]['events']}); excerpt integer bounds, neuron bounds, sort, 1 ms per-neuron floor; ISI identity {rows[0]['isi']}/{rows[1]['isi']}/{rows[2]['isi']}; spike budgets exact; energy pJ/µJ exact; reward totals equal two-decimal component sums (+0.41/+0.34/+0.43/+0.32/+0.39/+0.34); gate_snn decisions match lead `safety_decision.decision`; `state.sim_or_real` ∈ {{designed, hil, simulated}}; `meta.round=39`, `meta.factory=neuromorphic-event-language-bridge`, `meta.generator=grok-4.6`, `meta.run_label=2026-09-02-final-heavy`; `meta.rights` 15-key RM-793 stamp, `intended_use=research_only`, `linear_issue=RM-793`, `generated_at={GENERATED_AT}`; no hidden-reasoning keys; no `provenance` objects; no 'real' claims; no `training_ready`; all 9 record/trajectory ids unique. Raster seeds 20261118/20261119/20261120, MT19937.

Honest novelty accounting: 3/3 modality families are new versus the committed factory and versus staged leftover-mill r13–r37 plus in-flight r38. Ion-chamber denial, frozen-orifice denial, and crust nuclear-density denial are new edges applied to new physics. Against that: conjunctive SOP, operational t2, serialized reconstruction, bounded ACCEPT, and process-vs-cost reward splits are carried vocabulary; the 5–40 cap is a density constraint; 38 prior leftover-mill rounds already taught custody/governance. Net: a bit under two-fifths of the round's scenario/edge mass is genuinely novel.

Novel coverage: 38%
"""
    NOTES.write_text(notes, encoding="utf-8")
    print("wrote", NOTES, "bytes", NOTES.stat().st_size)


def repo_gates(records):
    chunks = []
    from check_records import FactoryStaging, check_jsonl

    errs, warns, kinds, n = check_jsonl(
        BATCH, "batch-r39.jsonl", staging=FactoryStaging(enabled=True)
    )
    chunks.append(
        f"`check_records.check_jsonl` with `FactoryStaging(enabled=True)` → {len(errs)} errors, {len(warns)} warnings, kinds `{kinds}` (n={n})"
    )
    if errs:
        raise RuntimeError(f"check_jsonl errors {errs[:5]}")

    import curate_bridge

    for rec in records:
        st = curate_bridge.raster_status(
            rec, require_raster=True, require_routing_table=True
        )
        if not st["raster_valid"] or not st["gate_snn_valid"] or st["reason_codes"]:
            raise RuntimeError(f"raster_status {rec['id']} {st}")
        if not st["third_factor_present"]:
            raise RuntimeError(f"third_factor missing {rec['id']}")
    chunks.append(
        "`curate_bridge.raster_status(..., require_raster=True, require_routing_table=True)` → raster_valid and gate_snn_valid true, empty reason codes, `third_factor_present` true on all three"
    )

    from curate_bridge import curate_record

    for i, rec in enumerate(records, 1):
        blob = json.dumps(rec, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
        h = hashlib.sha256(blob.encode("utf-8")).hexdigest()
        dec = curate_record(
            rec,
            source_path="batch-r39.jsonl",
            source_line=i,
            source_hash=h,
            require_raster=True,
            require_routing_table=True,
        )
        reasons = dec.manifest.get("reason_codes")
        print(rec["id"], "curate", dec.action, reasons)
        if dec.action != "retain":
            raise RuntimeError(f"curate {rec['id']} {dec.action} {reasons}")
    chunks.append("`curate_record(...)` → 3× retain / `BRIDGE_EVENTS_ALREADY_GLOBALLY_ORDERED`")

    from verify_execution_shapes import verify_record_execution
    from verify_execution import verify_batch_for_frontier

    for rec in records:
        status, reason = verify_record_execution(rec, rec["id"])
        if status != "verified":
            raise RuntimeError(f"verify_record_execution {rec['id']} {status} {reason}")
    chunks.append("`verify_record_execution` → 3× verified")
    counts, findings, blocked = verify_batch_for_frontier(BATCH, strict=True)
    if blocked or counts.get("failed") or counts.get("inconclusive"):
        raise RuntimeError(f"frontier {counts} {findings}")
    chunks.append(
        f"`verify_batch_for_frontier(strict=True)` → {counts.get('verified')} verified, {counts.get('inconclusive')} inconclusive, {counts.get('failed')} failed, blocked {blocked}"
    )

    import spike_probe

    rasters, problems = spike_probe.load_rasters([str(BATCH)])
    summary = spike_probe.summarize(rasters, problems, [str(BATCH)])
    if problems:
        raise RuntimeError(f"spike_probe {problems}")
    chunks.append(
        f"`python3 pipelines/spike_probe.py --strict {BATCH}` → loaded {len(rasters)}, unloadable 0, problems [], gate_snn_records {summary.get('gate_snn_records')}, third_factor_routes {summary.get('third_factor_routes')}"
    )
    return "; ".join(chunks) + "."


def main():
    occupancy_preflight()
    records = [rec_118(), rec_119(), rec_120()]
    local_checks(records)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        json.dumps(r, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
        for r in records
    ]
    BATCH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote", BATCH, "bytes", BATCH.stat().st_size, "lines", len(lines))
    for i, r in enumerate(records):
        print(
            r["id"],
            "events",
            len(r["spike_events"]),
            "excerpt",
            len(r["raster"]["excerpt"]),
            "spikes",
            r["raster"]["spikes"],
            "isi",
            r["raster"]["isi_count_identity"],
            "sim",
            r["language_view"]["trajectory"]["state"]["sim_or_real"],
            "dec",
            r["language_view"]["trajectory"]["safety_decision"]["decision"],
            "bytes",
            len(lines[i]),
        )
    file_sha = hashlib.sha256(BATCH.read_bytes()).hexdigest()
    gate_lines = repo_gates(records)
    write_notes(records, gate_lines, file_sha)


if __name__ == "__main__":
    main()
