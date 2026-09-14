#!/usr/bin/env python3
"""Generate NELB round-18 research-only bridge pairs (do not write outputs/raw/)."""

from __future__ import annotations

import json
import math
import random
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

OUT_DIR = Path("/tmp/nelb-r18")
BATCH = OUT_DIR / "batch-r18.jsonl"
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

HIDDEN = {
    "thought",
    "thoughts",
    "reasoning",
    "chain_of_thought",
    "hidden_thought",
    "scratchpad",
    "scratch",
    "internal_monologue",
    "private_reasoning",
    "inner_monologue",
}


def meta_common(**extra):
    m = {
        "round": 18,
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
        if t < last:
            raise RuntimeError("decreasing t_rel_ms")
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


def rec_055():
    raster = make_raster(
        neurons=25,
        mean_rate_hz=40.0,
        window_ms=32.0,
        seed=20260918,
        source="lampwick.ttl.frontend",
        target="glimmerfen.artifact_core",
        table=[
            {"from": "ttl_led_lock", "to": "stim_lock_core", "weight": 1.4},
            {"from": "pv_ch14_peak", "to": "photovoltaic_estimator", "weight": 1.25},
            {"from": "decoder_unit_claim", "to": "unit_advocate", "weight": 0.55},
        ],
        third_factor={
            "modulator": "da.stim_lock_error",
            "tau_e_s": 0.8,
            "tau_e_ms": 800.0,
            "eligibility": "pre-post coincidence on stim-lock synapses; the error modulator depresses decoder-unit links when a photovoltaic peak and a disconnected-pad comb agree with the LED TTL inside tau_e",
        },
        channel_prefix="opto.n",
        anchor="Lampwick-Q HIL 32 ms frame at first 470 nm TTL (t_s 2.000); pv.ch14 peaks 180 us later at 105.0 uV",
    )
    w_s = 0.032
    events = [
        ev(0.0, "probe.rms", 8.2, code="BASELINE_UV", units="uV", note="saline-bath silicon probe RMS; no cells on Moth-Saline HIL-7"),
        ev(800.0, "saline.t", 22.4, code="BATH_C", units="C"),
        ev(1200.0, "fpga.sync", 1.0, code="HIL_LOCK", units="bool", note="Lampwick-Q HIL clock locked"),
        ev(2000.0, "ttl.led", 1.0, code="PULSE_ON", units="bool", note="470 nm, 5 ms, 20 Hz train start; 8.4 mW/mm2"),
        ev(2000.18, "pv.ch14", 105.0, code="PV_UV", units="uV", note="photovoltaic peak; 8.4 * 12.5 = 105.00 exact; raster frame"),
        ev(2050.0, "ttl.led", 1.0, code="PULSE_ON", units="bool"),
        ev(2050.18, "pv.ch14", 86.1, code="PV_UV", units="uV", note="second pulse; amplitude adapted 0.82x plus noise"),
        ev(2051.38, "pv.ch14", 68.4, code="PV_RING", units="uV", note="same-channel ringing 1.20 ms; adapted"),
        ev(2052.78, "pv.ch14", 54.2, code="PV_RING", units="uV", note="third ringing 1.40 ms; adapted"),
        ev(3200.0, "dead.ch", 1.0, code="PAD_OPEN", units="bool", note="disconnected pad still shows the 20 Hz comb"),
        ev(4000.0, "jitter.rms", 6.2, code="VS_TTL_US", units="us", note="lock-step; biological floor is 20 us"),
        ev(4800.0, "irr.opt", 8.4, code="IRRAD", units="mW_mm2"),
        ev(5600.0, "pv.pred", 105.0, code="MODEL_UV", units="uV", note="serialized photovoltaic model"),
        ev(6400.0, "isi.cv", 0.004, code="CV", units="1", note="too regular for a pyramidal cluster"),
        ev(7200.0, "snr.unit", 2.1, code="CLAIMED_SNR", units="1"),
        ev(8000.0, "unit.claim", 1.0, code="PYR_CLUSTER", units="bool", note="decoder labels the comb a regular-spiking unit"),
        ev(8800.0, "ops.prop", 1.0, code="KEEP_DECODER", units="bool"),
        ev(9600.0, "gate.art", 1.0, code="REJECT", units="decision", note="artifact, not a unit"),
        ev(10400.0, "blank.pre", 2.0, code="PRE_MS", units="ms"),
        ev(10500.0, "blank.post", 6.0, code="POST_MS", units="ms"),
        ev(11200.0, "dec.freeze", 1.0, code="DECODER_OFF", units="bool"),
        ev(12800.0, "pv.ch14", 4.1, code="PV_UV", units="uV", note="residual after blanking window"),
        ev(14400.0, "blank.frac", 0.16, code="DUTY", units="1", note="20 Hz * 8 ms = 0.16 of samples blanked"),
        ev(16000.0, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion: blanking sequence executed"),
        ev(17600.0, "closed.loop", 0.0, code="NOT_FIRING", units="bool"),
        ev(18400.0, "jitter.rms", 6.1, code="VS_TTL_US", units="us"),
        ev(19200.0, "irr.opt", 8.4, code="IRRAD", units="mW_mm2"),
        ev(20000.0, "recon.check", 105.0, code="MODEL_UV", units="uV"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r18-055-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "GF-OPTO-2026-0312",
            "domain": "optogenetic_stim_artifact",
            "setting": "Glimmerfen Photostim Core, stand Lampwick-Q, dummy probe Moth-Saline HIL-7 in a 22.4 C saline bath (no cells). 470 nm LED over the metal sites; closed-loop decoder is the object under test. Invented plant; HIL campaign.",
            "observables_at_decision": {
                "irradiance_mW_mm2": 8.4,
                "pv_peak_uV": 105.0,
                "jitter_rms_us": 6.2,
                "isi_cv": 0.004,
                "dead_pad_comb": True,
            },
            "margin_authority": "Lampwick-Q stim-lock SOP rev B: if photovoltaic peak agrees with k*E within 5 percent AND TTL jitter RMS < 20 us AND a disconnected pad carries the same comb, a decoder unit-claim is forbidden",
        },
        "proposed_action": {
            "actor": "closed-loop operator, citing a 20 Hz regular-spiking cluster on ch14",
            "summary": "keep the decoder online; treat the comb as a pyramidal unit and continue the stim-triggered decode",
            "basis_claimed": "cluster SNR 2.1 and a stable 20 Hz ISI; no bath motion alarm",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "The cluster is a photovoltaic artifact, not a unit. Serialized model: V_pv_uV = E_mW_mm2 * 12.5 = 8.4 * 12.5 = 105.00 uV, matching pv.ch14 at TTL+180 us. Jitter vs TTL is 6.2 us against a 20 us biological floor, ISI CV 0.004 is comb-regular, and a disconnected pad carries the same 20 Hz train. Ordered: freeze the decoder, install 2 ms pre / 6 ms post blanking around each TTL (companion), and do not let closed-loop fire on stim-locked peaks. A decoder-online proposal cannot substitute for the photovoltaic identity.",
            "threshold": "pv_peak agrees with k*E AND jitter_rms_us<20 AND dead_pad_comb => forbid unit-claim",
            "stated_residuals": "blanking duty 0.16 at 20 Hz; HIL has no tissue so overlapping biological spikes inside the blank are untested",
        },
        "executed_action": {
            "summary": "REJECT at t_s 9.600: decoder frozen; blanking 2+6 ms armed; closed-loop not firing by t_s 17.600",
            "tool": "lampwick-stim-lock-gate-cli",
            "observation": "pv.ch14 residual 4.1 uV after blank; jitter stayed 6.1-6.2 us; recon.check 105.00 uV",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2.0, "event": "first 470 nm TTL; pv.ch14 105.00 uV; raster frame"},
                {"t_s": 2.05278, "event": "adapted pv ringing triplet at 1.2/1.4 ms"},
                {"t_s": 3.2, "event": "disconnected pad shows the same comb"},
                {"t_s": 8.8, "event": "keep-decoder proposed"},
                {"t_s": 9.6, "event": "REJECT"},
                {"t_s": 16.0, "event": "companion blanking ACCEPT"},
            ],
            "observed_effects": [
                "photovoltaic peak recomputes from the serialized k*E model at every pv.pred / recon.check event",
                "decoder-online would have treated a lock-step comb as a unit",
                "disconnected-pad witness is off the decoder bus",
            ],
            "surprises": [
                "bath RMS stayed 8.2 uV; a noise-floor head would have ACCEPTed the cluster",
            ],
            "new_state": {
                "decoder": "frozen",
                "blanking": "2 ms pre / 6 ms post latched",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 800.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("photovoltaic_identity", 0.14),
                ("ttl_lock_jitter", 0.12),
                ("dead_pad_witness", 0.10),
                ("decoder_refusal", 0.09),
                ("session_interrupt_cost", -0.02),
            ],
            "scored for refusing a stim-locked photovoltaic comb as a unit while the decoder looked healthy; session_interrupt_cost prices the frozen decode",
        ),
        "meta": meta_common(
            tags=["REJECT", "optogenetic-stim-artifact", "serialized-reconstruction", "operational-companion"],
            distillation_note="stim-lock gate: serialized k*E photovoltaic identity plus TTL jitter plus dead-pad comb beats a decoder unit-claim; companion t2 is the blanking execution, not a governance vote",
        ),
    }
    traj2 = {
        "id": "nelb-r18-055-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "GF-OPTO-2026-0312-blank",
            "domain": "stim_blanking_execution",
            "setting": "Same Lampwick-Q after the REJECT. This companion is the operational 2 ms pre / 6 ms post blank plus decoder freeze, not a second artifact vote.",
            "observables_at_decision": {
                "blank_pre_ms": 2.0,
                "blank_post_ms": 6.0,
                "blank_frac": 0.16,
                "pv_residual_uV": 4.1,
            },
        },
        "proposed_action": {
            "actor": "HIL controller following the REJECT",
            "summary": "execute 2 ms pre / 6 ms post blank around each TTL and hold the decoder freeze for the rest of the train",
            "basis_claimed": "REJECT requirements are fully specified and in-envelope for the HIL FPGA blanker",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "The execution envelope is intact: 8 ms blank at 20 Hz is 0.16 duty under the 0.25 HIL cap, residual pv.ch14 is 4.1 uV, and closed-loop is not firing. ACCEPT the sequence. Do not re-enable the decoder until jitter_rms_us > 20 on a no-LED control pass.",
            "threshold": "blank_frac<=0.25 AND residual_uV<10 AND decoder_frozen",
        },
        "executed_action": {
            "summary": "blank latched at t_s 10.400; decoder freeze held; closed-loop not firing at t_s 17.600",
            "tool": "lampwick-blank-exec",
            "observation": "duty 0.16; residual 4.1 uV; no decoder spike after freeze",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 10.4, "event": "2 ms pre blank armed"},
                {"t_s": 10.5, "event": "6 ms post blank armed"},
                {"t_s": 16.0, "event": "ACCEPT blanking execution"},
            ],
            "observed_effects": [
                "photovoltaic residual fell 105.00 -> 4.1 uV without a unit waveform remaining",
                "decoder stayed frozen; closed-loop did not fire",
            ],
            "new_state": {"blanking": "latched", "decoder": "frozen pending no-LED control"},
            "latency_ms": 800.0,
        },
        "reward_components": reward(
            0.33,
            [
                ("blanking_window", 0.12),
                ("decoder_freeze", 0.10),
                ("residual_check", 0.08),
                ("duty_declared", 0.05),
                ("blank_fraction_cost", -0.02),
            ],
            "operational blanking companion: execute the REJECT, do not re-open the unit call",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "stim-blanking"]),
    }
    return {
        "id": "nelb-r18-055",
        "spike_events": events,
        "language_view": {
            "description": "HIL optogenetic stim on Glimmerfen Lampwick-Q. A 470 nm train writes a 105.00 uV photovoltaic comb onto Moth-Saline HIL-7; the decoder claims a pyramidal unit. The gate REJECTS: k*E identity, 6.2 us TTL lock, and a disconnected-pad witness. Companion t2 ACCEPT executes 2+6 ms blanking and keeps the decoder frozen.",
            "trajectory": traj,
            "trajectory_stim_blanking_execution": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "ttl.led / irr.opt": "optical command custody: 470 nm TTL and irradiance",
                "pv.ch14 / pv.pred / recon.check": "photovoltaic physics and serialized k*E identity",
                "dead.ch / jitter.rms / isi.cv": "lock-step witnesses a unit cannot satisfy",
                "unit.claim / ops.prop / gate.art": "decoder-online vs REJECT",
                "blank.pre / blank.post / gate.exec": "operational blanking companion",
            },
            "temporal_motifs": [
                "TTL then photovoltaic: ttl.led at 2000.00 ms, pv.ch14 at 2000.18 ms, lag 180 us",
                "adapted ringing triplet at 1.2/1.4 ms on pv.ch14",
                "dead-pad comb before the unit-claim: dead.ch at 3200 ms, unit.claim at 8000 ms",
                "REJECT then operational ACCEPT: gate.art at 9600 ms, gate.exec at 16000 ms",
            ],
            "language_to_spike_mapping": "'the cluster is a unit' = unit.claim PYR_CLUSTER; '105 uV artifact' = pv.ch14 plus recon.check 105.00; 'lock-step' = jitter.rms 6.2 us; 'refuse decoder-online' = gate.art REJECT; 'execute blanking' = blank.pre/post then companion ACCEPT",
            "why_high_value": "New optogenetic-stim-artifact family (not ECoG/RNS, not cardiovascular interoception, not flow-cytometry). First photovoltaic identity serialized as k*E. HIL saline dummy so the comb cannot be a cell. Companion t2 is operational blanking, not a governance vote.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20260918, "stream_note": "stream amplitudes authored (uV, mW/mm2, us, C, duty) plus pv.ch14 adaptation 0.82**k"},
                "draw_order": "raster per neuron id order with adaptation/noise",
                "thinning": "20 Hz train exists for ~18 s; stream keeps 2 TTL pulses plus one ringing triplet; irradiance keeps 2 of ~360 pulses",
                "refractory_floors_ms": {
                    "probe.rms": 1000,
                    "saline.t": 1000,
                    "fpga.sync": 1000,
                    "ttl.led": 50,
                    "pv.ch14": 0.8,
                    "dead.ch": 1000,
                    "jitter.rms": 1000,
                    "irr.opt": 1000,
                    "pv.pred": 1000,
                    "isi.cv": 1000,
                    "snr.unit": 1000,
                    "unit.claim": 1000,
                    "ops.prop": 1000,
                    "gate.art": 1000,
                    "blank.pre": 1000,
                    "blank.post": 1000,
                    "dec.freeze": 1000,
                    "blank.frac": 1000,
                    "gate.exec": 1000,
                    "closed.loop": 1000,
                    "recon.check": 1000,
                },
                "time_alias": "t_rel_ms; t0 = HIL start 2026-03-12T14:00:00Z; TTL onset at 2000 ms",
            },
            "distillation_targets": [
                "serialized photovoltaic identity: E_mW_mm2 * 12.5 = uV",
                "stim-lock conjunctive head: identity AND jitter AND dead-pad, never decoder-SNR substitution",
                "operational companion: execute blanking without re-opening the unit call",
            ],
        },
        "reconstruction_model": {
            "name": "photovoltaic_artifact_peak",
            "formula": "V_pv_uV = E_mW_mm2 * k_uV_per_mW_mm2",
            "parameters": {"k_uV_per_mW_mm2": 12.5},
            "worked_example": {"E_mW_mm2": 8.4, "V_pv_uV": 105.0},
            "check": "8.4 * 12.5 = 105.00 exactly",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 32.0,
            "decision_window_s": 0.032,
            "code": "lampwick.stim_lock_gate",
            "note": "REJECT accumulator wins: photovoltaic identity plus TTL lock plus dead-pad overpower the unit advocate",
            "populations": [
                gate_pop("photovoltaic_identity", 100, 1.5, 31.25, w_s),
                gate_pop("ttl_lock_evidence", 80, 1.2, 25.0, w_s),
                gate_pop("unit_advocate", 40, 0.8, 12.5, w_s),
                gate_pop("reject_accumulator", 80, 1.8, 50.0, w_s),
            ],
        },
        "gate_compute": {
            "per_check": [
                {
                    "check": "lampwick.pv_identity",
                    "neurons": 96,
                    "mean_rate_hz": 50.0,
                    "window_ms": 32.0,
                    "window_s": 0.032,
                    "spikes": 154,
                },
                {
                    "check": "lampwick.ttl_deadpad_join",
                    "neurons": 80,
                    "mean_rate_hz": 31.25,
                    "window_ms": 40.0,
                    "window_s": 0.04,
                    "spikes": 100,
                },
            ],
            "total_spikes": 254,
            "total_energy_pJ": 5842,
            "total_energy_uJ": 0.005842,
            "model": "spikes = round(neurons * mean_rate_hz * window_s); 23 pJ/spike",
        },
        "meta": meta_common(
            id="nelb-r18-055",
            clock_domain="lampwick-hil-relative-ms-t0-2026-03-12T14:00:00Z",
            tags=["optogenetic-stim-artifact", "REJECT", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }


def rec_056():
    raster = make_raster(
        neurons=16,
        mean_rate_hz=50.0,
        window_ms=40.0,
        seed=20260919,
        source="ash18.lidar.near",
        target="rimeholt.snow_blind_core",
        table=[
            {"from": "near_return_wall", "to": "snow_mode_estimator", "weight": 1.35},
            {"from": "radar_lwir", "to": "occupancy_truth_core", "weight": 1.15},
            {"from": "lidar_far_empty", "to": "clear_path_advocate", "weight": 0.55},
        ],
        third_factor={
            "modulator": "na.snow_blind_salience",
            "tau_e_s": 1.5,
            "tau_e_ms": 1500.0,
            "eligibility": "pre-post coincidence on snow-mode synapses; glaze-volume modulator enables potentiation only while R_mode is inside 12 m and radar/LWIR occupancy is co-active inside tau_e",
        },
        channel_prefix="lidar.n",
        anchor="Ash-18 40 ms frame at the flake-wall mode (t_s 2.800) where R_mode=8.00 m while radar still holds 48 m",
    )
    w_s = 0.04
    events = [
        ev(0.0, "speed.v", 62.0, code="KMH", units="km_h", note="Ash-18 night plow, Rimeholt corridor km 14.2"),
        ev(400.0, "vis.met", 180.0, code="VIS_M", units="m", note="meteorological visibility still 180 m; the denial channel"),
        ev(800.0, "flake.rho", 6250.0, code="RHO", units="m-3"),
        ev(1200.0, "sigma.fl", 2.0e-5, code="SIGMA", units="m2"),
        ev(2000.0, "lidar.near", 18400.0, code="HITS_S", units="1_s", note="0-15 m first-returns; flake wall; amplitude before adaptation"),
        ev(2001.2, "lidar.near", 15088.0, code="HITS_S", units="1_s", note="same-channel refractory 1.2 ms; amplitude adapted 0.82x plus noise"),
        ev(2002.6, "lidar.near", 12140.0, code="HITS_S", units="1_s", note="third near-return; adapted"),
        ev(2800.0, "lidar.rmode", 8.00, code="R_MODE_M", units="m", note="1/(2.0e-5 * 6250) = 8.00 exact; raster frame"),
        ev(3600.0, "lidar.far", 0.0, code="OCCUPANCY", units="bool", note="empty beyond 15 m — snow-blind, not a clear path"),
        ev(4400.0, "radar.r", 48.0, code="RANGE_M", units="m", note="77 GHz still sees a stopped vehicle"),
        ev(5200.0, "radar.rcs", 12.4, code="RCS", units="m2"),
        ev(6000.0, "lwir.blob", 1.0, code="THERMAL_HIT", units="bool"),
        ev(7200.0, "lidar.lam", 905.0, code="NM", units="nm", note="905 nm pulsed spinning 16-layer; not SPAD flash ToF"),
        ev(8400.0, "ops.prop", 1.0, code="PATH_CLEAR", units="bool", note="night ops: LiDAR empty past 15 m, hold 62 km/h"),
        ev(9200.0, "gate.snow", 1.0, code="MODIFY", units="decision"),
        ev(10000.0, "speed.cap", 25.0, code="KMH", units="km_h"),
        ev(10800.0, "sot.radar", 1.0, code="RADAR_LWIR", units="bool"),
        ev(11600.0, "lidar.tag", 1.0, code="SNOW_BLIND", units="bool"),
        ev(12800.0, "speed.v", 24.0, code="KMH", units="km_h"),
        ev(14000.0, "radar.r", 41.0, code="RANGE_M", units="m"),
        ev(15200.0, "lwir.blob", 1.0, code="THERMAL_HIT", units="bool"),
        ev(16400.0, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion: 25 km/h + radar-primary executed"),
        ev(17600.0, "lidar.rmode", 8.20, code="R_MODE_M", units="m"),
        ev(18800.0, "vis.met", 170.0, code="VIS_M", units="m"),
        ev(20000.0, "brake.cmd", 1.0, code="HOLD_CAP", units="bool"),
        ev(21200.0, "radar.r", 28.0, code="RANGE_M", units="m"),
        ev(22400.0, "recon.check", 8.00, code="R_MODE_M", units="m"),
        ev(23600.0, "flake.rho", 6180.0, code="RHO", units="m-3"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r18-056-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "RH-SNOW-2026-0219",
            "domain": "lidar_snow_blind",
            "setting": "Rimeholt Winter Corridor, snow-plow Ash-18 (invented). 905 nm 16-layer spinning LiDAR plus 77 GHz radar plus LWIR. Night snow: meteorological visibility 180 m, 62 km/h. Designed campaign; not planetary SPAD flash ToF.",
            "observables_at_decision": {
                "r_mode_m": 8.0,
                "lidar_far_occupancy": 0.0,
                "radar_range_m": 48.0,
                "radar_rcs_m2": 12.4,
                "speed_kmh": 62.0,
                "vis_m": 180.0,
            },
            "margin_authority": "Ash-18 snow-blind SOP rev C: if reconstructed R_mode <= 12 m AND radar range < 80 m, empty far-range LiDAR cannot be a clear-path SoT even if meteorological visibility is in corridor",
        },
        "proposed_action": {
            "actor": "night ops desk, citing empty LiDAR past 15 m and 180 m visibility",
            "summary": "hold Ash-18 at 62 km/h; treat far-range LiDAR emptiness as a clear path",
            "basis_claimed": "meteorological visibility 180 m and no LiDAR occupancy beyond 15 m; a 25 km/h cap would miss the shift window",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Rated speed is refused, not the plow. SOP rev C is conjunctive: reconstructed R_mode is 8.00 m (1 / (2.0e-5 m2 * 6250 m-3), serialized) and radar still holds a 48 m / 12.4 m2 target with LWIR concurrence, both over the 12 m / 80 m floors, while vis.met still reads 180 m. Empty far-range LiDAR is snow-blindness, not a clear path. Ordered: cap 25 km/h, make radar+LWIR primary, tag 905 nm LiDAR snow-blind until R_mode > 20 m. Visibility-corridor agreement cannot substitute for the snow-mode reconstruction.",
            "threshold": "r_mode_m<=12 AND radar_range_m<80 => forbid clear-path SoT on LiDAR",
            "stated_residuals": "25 km/h cap delays the shift ~6 min; 1550 nm FMCW contrast is not on this plow and is not a release condition",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 9.200: 25 km/h cap commanded, radar+LWIR primary, LiDAR tagged snow-blind; speed 62 -> 24 km/h by t_s 12.800",
            "tool": "ash18-snow-blind-gate-cli",
            "observation": "radar closed 48 -> 28 m with LWIR held; R_mode stayed 8.00-8.20 m; vis.met never left the 170-180 m corridor",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2.0, "event": "near-return flake-wall burst; adapted 1.2/1.4 ms triplet"},
                {"t_s": 2.8, "event": "R_mode 8.00 m; raster frame"},
                {"t_s": 4.4, "event": "radar 48 m / 12.4 m2; LWIR hit"},
                {"t_s": 8.4, "event": "path-clear proposed"},
                {"t_s": 9.2, "event": "MODIFY: 25 km/h plus radar-primary"},
                {"t_s": 16.4, "event": "companion execution ACCEPT"},
            ],
            "observed_effects": [
                "R_mode recomputes from the serialized 1/(sigma*rho) model at lidar.rmode and recon.check",
                "vis.met never left the corridor, so a visibility-only head would have ACCEPTed",
                "radar and LWIR jointly occupied the same target the LiDAR far-range called empty",
            ],
            "surprises": [
                "meteorological visibility stayed 170-180 m the entire flake wall; human-eye range is not a substitute snow detector on 905 nm",
            ],
            "new_state": {
                "ash18": "capped 25 km/h, radar-primary",
                "lidar_905": "tagged snow-blind",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 3600.0,
        },
        "reward_components": reward(
            0.40,
            [
                ("snow_mode_reconstruction", 0.14),
                ("radar_lwir_nonsubstitution", 0.12),
                ("clear_path_refusal", 0.10),
                ("speed_cap", 0.08),
                ("throughput_cost", -0.04),
            ],
            "scored for refusing a snow-blind empty far-range as clear-path while vis.met looked healthy; throughput_cost prices the 25 km/h delay",
        ),
        "meta": meta_common(
            tags=["MODIFY", "lidar-snow-blind", "serialized-reconstruction", "operational-companion"],
            distillation_note="snow-blind gate: serialized R_mode=1/(sigma*rho) plus radar/LWIR occupancy beats a clean visibility corridor; companion t2 is the speed-cap execution, not a governance vote",
        ),
    }
    traj2 = {
        "id": "nelb-r18-056-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "RH-SNOW-2026-0219-exec",
            "domain": "speed_cap_radar_primary",
            "setting": "Same Ash-18 after the MODIFY. This companion is the operational 25 km/h cap plus radar+LWIR primary, not a second snow call.",
            "observables_at_decision": {
                "speed_cap_kmh": 25.0,
                "speed_now_kmh": 24.0,
                "radar_range_m": 41.0,
                "lidar_tag": "SNOW_BLIND",
            },
        },
        "proposed_action": {
            "actor": "plow controller following the MODIFY",
            "summary": "execute 25 km/h cap, switch SoT to radar+LWIR, hold the cap until R_mode > 20 m",
            "basis_claimed": "MODIFY requirements are fully specified and in-envelope for the traction limiter",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "The execution envelope is intact: speed 24 km/h is under the 25 km/h cap, radar still tracks 41 then 28 m, LWIR remains hit, and 905 nm is tagged snow-blind. ACCEPT the sequence. Do not restore 62 km/h until R_mode > 20 m AND radar range > 80 m; 25 km/h is the cap tonight.",
            "threshold": "speed_kmh<=25 AND sot=radar+lwir AND lidar_tagged_snow_blind",
        },
        "executed_action": {
            "summary": "cap latched; radar-primary; speed 24 km/h; radar closed to 28 m with LWIR held",
            "tool": "ash18-speed-cap-exec",
            "observation": "no traction slip; R_mode stayed ~8 m; vis.met 170 m never became a release input",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 10.0, "event": "25 km/h cap commanded"},
                {"t_s": 12.8, "event": "speed 24 km/h"},
                {"t_s": 16.4, "event": "ACCEPT execution"},
            ],
            "observed_effects": [
                "radar occupancy survived the LiDAR far-range emptiness",
                "restore to 62 km/h was not re-entered",
            ],
            "new_state": {"ash18_speed_kmh": 24.0, "sot": "radar+lwir", "restore_cap_kmh": 25.0},
            "latency_ms": 3600.0,
        },
        "reward_components": reward(
            0.35,
            [
                ("cap_executed", 0.12),
                ("sot_radar_lwir", 0.11),
                ("lidar_tagged_blind", 0.09),
                ("vehicle_still_tracked", 0.05),
                ("delay_cost", -0.02),
            ],
            "operational execution gate: the companion does the cap rather than re-arguing the snow call",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "speed-cap"]),
    }
    return {
        "id": "nelb-r18-056",
        "spike_events": events,
        "language_view": {
            "description": "Night snow on Rimeholt Ash-18. 905 nm LiDAR reconstructs R_mode 8.00 m (flake wall) while meteorological visibility is still 180 m and far-range LiDAR looks empty. Radar 48 m plus LWIR still occupy a stopped vehicle. The gate MODIFYs to a 25 km/h cap plus radar-primary; companion execution ACCEPT holds the cap. Distinct from r3 SPAD flash ToF.",
            "trajectory": traj,
            "trajectory_speed_cap_radar_primary": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "lidar.near / lidar.rmode / recon.check": "flake-wall physics; serialized R_mode=1/(sigma*rho)",
                "lidar.far / vis.met": "denial channels: empty far-range and 180 m visibility",
                "radar.r / radar.rcs / lwir.blob": "occupancy the snow-blind LiDAR cannot see",
                "ops.prop / gate.snow": "path-clear vs MODIFY",
                "speed.cap / sot.radar / gate.exec": "operational cap companion",
            },
            "temporal_motifs": [
                "visibility-healthy while LiDAR-sick: vis.met 180 m adjacent to lidar.rmode 8.00 m",
                "reconstruction as event: lidar.rmode 8.00 equals 1/(2.0e-5*6250)",
                "adapted near-return triplet at 1.2 ms spacing encodes the flake wall at raster scale",
                "MODIFY then operational ACCEPT: gate.snow at 9200 ms, gate.exec at 16400 ms",
            ],
            "language_to_spike_mapping": "'path is clear' = lidar.far OCCUPANCY 0 plus vis.met 180 m; '8 m flake wall' = lidar.rmode 8.00; 'vehicle still there' = radar.r 48 m plus lwir.blob; 'forbid clear-path SoT' = gate.snow MODIFY; 'execute the cap' = speed.cap 25 then companion ACCEPT",
            "why_high_value": "New 905 nm LiDAR snow-blind family (not r3 SPAD ToF planetary flash, not r4 DAS, not r7 infrasound). Closes a reconstruction-as-SoT pattern on optical depth rather than ice mass. Companion t2 is operational speed-cap execution.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20260919, "stream_note": "stream amplitudes authored (km/h, m, m-3, m2, hits/s, nm) plus lidar.near adaptation 0.82**k"},
                "draw_order": "raster per neuron id order with adaptation/noise",
                "thinning": "16 LiDAR layers exist; stream keeps near-return aggregate plus R_mode; radar keeps 3 of ~40 s",
                "refractory_floors_ms": {
                    "speed.v": 1000,
                    "vis.met": 1000,
                    "flake.rho": 1000,
                    "sigma.fl": 1000,
                    "lidar.near": 0.8,
                    "lidar.rmode": 1000,
                    "lidar.far": 1000,
                    "radar.r": 1000,
                    "radar.rcs": 1000,
                    "lwir.blob": 1000,
                    "lidar.lam": 1000,
                    "ops.prop": 1000,
                    "gate.snow": 1000,
                    "speed.cap": 1000,
                    "sot.radar": 1000,
                    "lidar.tag": 1000,
                    "gate.exec": 1000,
                    "brake.cmd": 1000,
                    "recon.check": 1000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-02-19T03:10:00Z campaign start",
            },
            "distillation_targets": [
                "serialized snow-mode reconstruction: R_mode = 1/(sigma*rho)",
                "conjunctive SOP head: R_mode AND radar occupancy, never visibility-corridor substitution",
                "operational companion: execute the cap without re-opening the snow call",
            ],
        },
        "reconstruction_model": {
            "name": "lidar_snow_mode_range",
            "formula": "R_mode_m = 1.0 / (sigma_m2 * rho_m3)",
            "parameters": {"sigma_m2": 2.0e-5, "rho_m3": 6250.0},
            "worked_example": {"sigma_rho": 0.125, "R_mode_m": 8.0},
            "check": "1 / (2.0e-5 * 6250) = 1 / 0.125 = 8.00 exactly",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.04,
            "code": "ash18.snow_blind_gate",
            "note": "MODIFY accumulator wins: snow-mode and radar/LWIR occupancy overpower the clear-path advocate",
            "populations": [
                gate_pop("snow_mode_evidence", 80, 1.4, 50.0, w_s),
                gate_pop("radar_lwir_evidence", 64, 1.1, 31.25, w_s),
                gate_pop("clear_path_advocate", 48, 0.9, 25.0, w_s),
                gate_pop("modify_accumulator", 96, 1.6, 62.5, w_s),
            ],
        },
        "gate_compute": {
            "per_check": [
                {
                    "check": "ash18.snow_mode_scorer",
                    "neurons": 128,
                    "mean_rate_hz": 31.25,
                    "window_ms": 40.0,
                    "window_s": 0.04,
                    "spikes": 160,
                },
                {
                    "check": "ash18.radar_lwir_join",
                    "neurons": 64,
                    "mean_rate_hz": 25.0,
                    "window_ms": 32.0,
                    "window_s": 0.032,
                    "spikes": 51,
                },
            ],
            "total_spikes": 211,
            "total_energy_pJ": 4853,
            "total_energy_uJ": 0.004853,
            "model": "spikes = round(neurons * mean_rate_hz * window_s); 23 pJ/spike",
        },
        "meta": meta_common(
            id="nelb-r18-056",
            clock_domain="rimeholt-snow-relative-ms-t0-2026-02-19T03:10:00Z",
            tags=["lidar-snow-blind", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }


def rec_057():
    raster = make_raster(
        neurons=16,
        mean_rate_hz=50.0,
        window_ms=25.0,
        seed=20260920,
        source="kelpwick.clamp.frontend",
        target="brinefen.flow_auditor",
        table=[
            {"from": "weigh_tank_dm", "to": "flow_truth_core", "weight": 1.45},
            {"from": "clamp_last_good", "to": "custody_conflict_core", "weight": 1.1},
            {"from": "gel_snr_pathb", "to": "coupling_health_core", "weight": 1.2},
        ],
        third_factor={
            "modulator": "ach.flow_custody_conflict",
            "tau_e_s": 2.4,
            "tau_e_ms": 2400.0,
            "eligibility": "pre-post coincidence on custody synapses; the conflict modulator enables potentiation only while weigh-tank Q disagrees with a frozen clamp last-good inside tau_e",
        },
        channel_prefix="us.n",
        anchor="Kelpwick-U3 25 ms frame at the clamp last-good freeze (t_s 6.000) where 175.0 m3/h is 5.00x the weigh-tank",
    )
    w_s = 0.025
    events = [
        ev(0.0, "hyd.rho", 1.200, code="DENSITY", units="t_m3", note="brine density; weigh-tank reconstruction uses this"),
        ev(600.0, "wt.dm", 42.0, code="DM_T_H", units="t_h", note="Kelpwick-U3 weigh-tank"),
        ev(1200.0, "wt.q", 35.00, code="Q_M3H", units="m3_h", note="42.0 / 1.200 = 35.00 exact"),
        ev(1800.0, "clamp.snr", 32.0, code="SNR_DB", units="dB"),
        ev(2400.0, "clamp.q", 34.8, code="Q_M3H", units="m3_h", note="pre-dropout clamp agrees with weigh-tank"),
        ev(3600.0, "gel.h", 240.0, code="HOURS", units="h", note="spec recouple 168 h; gel dry-out"),
        ev(4800.0, "clamp.snr", 11.0, code="SNR_DB", units="dB", note="collapse"),
        ev(5400.0, "path.b", 0.0, code="DROPOUT", units="bool", note="aeration; ultrasonic path B lost"),
        ev(6000.0, "clamp.freeze", 175.0, code="LAST_GOOD_M3H", units="m3_h", note="frozen last-good; 175/35 = 5.00 exact; raster frame"),
        ev(7200.0, "clamp.q", 175.0, code="Q_PUBLISHED", units="m3_h"),
        ev(8400.0, "wt.q", 35.10, code="Q_M3H", units="m3_h", note="weigh-tank never tracked the freeze"),
        ev(9600.0, "ops.prop", 1.0, code="HOLD_AND_SWITCH", units="bool", note="hold transfer; SoT to weigh-tank; freeze 175 non-custody"),
        ev(10800.0, "gate.flow", 1.0, code="ACCEPT", units="decision"),
        ev(12000.0, "xfer.hold", 1.0, code="PUMP_STOP", units="bool"),
        ev(13200.0, "sot.wt", 1.0, code="WEIGH_TANK", units="bool"),
        ev(14400.0, "clamp.tag", 1.0, code="NON_CUSTODY", units="bool"),
        ev(15600.0, "resume.arm", 1.0, code="SNR18_RESUME", units="bool", note="tech wants to arm resume at SNR 18 dB"),
        ev(16800.0, "gate.gel", 1.0, code="MODIFY", units="decision", note="companion: recouple plus photos before any resume arm"),
        ev(18000.0, "gel.photo", 1.0, code="FACE_SEAL", units="bool"),
        ev(19200.0, "path.b", 0.0, code="STILL_DOWN", units="bool"),
        ev(20400.0, "clamp.snr", 12.4, code="SNR_DB", units="dB"),
        ev(21600.0, "wt.dm", 0.0, code="DM_T_H", units="t_h", note="transfer held"),
        ev(22800.0, "ratio.q", 5.00, code="CLAMP_OVER_WT", units="1"),
        ev(24000.0, "gel.h", 241.0, code="HOURS", units="h"),
        ev(25200.0, "recon.check", 35.00, code="Q_M3H", units="m3_h"),
        ev(26400.0, "wt.q", 0.0, code="Q_M3H", units="m3_h"),
        ev(27600.0, "resume.block", 1.0, code="NO_ARM", units="bool"),
        ev(28800.0, "hyd.rho", 1.201, code="DENSITY", units="t_m3"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r18-057-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "BF-US-2026-0408",
            "domain": "ultrasonic_clamp_on_flow",
            "setting": "Brinefen Transfer Rack, header Kelpwick-U3 (invented). Simulated campaign with a clamp-on transit-time ultrasonic meter and a weigh-tank that does not ride the clamp flow-computer bus. Distinct from r03 water-distribution hydraulics and r4 biosonar.",
            "observables_at_decision": {
                "clamp_last_good_m3h": 175.0,
                "weigh_tank_m3h": 35.0,
                "ratio": 5.0,
                "clamp_snr_db": 11.0,
                "path_b": 0.0,
                "gel_hours": 240.0,
            },
            "margin_authority": "custody transfer may ACCEPT a hold-and-switch when weigh-tank Q is serialized and a clamp last-good is frozen after path dropout; resume is not part of this gate",
        },
        "proposed_action": {
            "actor": "rack chemist plus transfer desk",
            "summary": "hold the transfer, switch SoT to the weigh-tank, tag the 175.0 m3/h last-good non-custody",
            "basis_claimed": "weigh-tank 35.00 m3/h recomputes from 42.0 t/h / 1.200 t/m3; clamp 175.0 is 5.00x and follows SNR collapse plus path-B dropout",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "The hold is earned and bounded. Serialized weigh-tank identity: Q_m3h = dM_t_h / rho_t_m3 = 42.0 / 1.200 = 35.00. Clamp last-good froze at 175.0 m3/h after SNR 32->11 dB and path-B dropout; 175/35 = 5.00 exact. Gel 240 h exceeds the 168 h recouple spec. ACCEPT hold + SoT switch + non-custody tag. Explicit scope limit: this ACCEPT does not arm resume. Tripwire: resume remains forbidden until dual-path SNR >= 24 dB AND |Q_clamp - Q_weigh|/Q_weigh < 0.05 AND gel-face photos are sealed (companion).",
            "threshold": "hold_and_switch allowed when last_good/weigh_tank >= 2 AND path_b dropout AND gel_hours>168; resume not granted",
            "stated_residuals": "held volume priced; clamp remains installed; resume is a different gate",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 10.800: pump stopped, SoT flipped to weigh-tank, 175.0 tagged non-custody",
            "tool": "kelpwick-flow-custody-cli",
            "observation": "weigh-tank fell 35.10 -> 0 m3/h after the hold; clamp published 175.0 until tagged; ratio.q 5.00 held",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1.2, "event": "weigh-tank 35.00 m3/h from 42.0/1.200"},
                {"t_s": 4.8, "event": "SNR collapse 11 dB"},
                {"t_s": 6.0, "event": "last-good freeze 175.0 m3/h; raster frame"},
                {"t_s": 9.6, "event": "hold-and-switch proposed"},
                {"t_s": 10.8, "event": "ACCEPT"},
                {"t_s": 16.8, "event": "companion MODIFY on early resume-arm"},
            ],
            "observed_effects": [
                "weigh-tank Q recomputes from the serialized density model at wt.q and recon.check",
                "clamp last-good never moved with the weigh-tank after the freeze",
                "ACCEPT is bounded: resume is not granted on this gate",
            ],
            "surprises": [
                "pre-dropout clamp.q 34.8 m3/h had been agreeing; the 175.0 object is a frozen last-good, not a new physics Q",
            ],
            "new_state": {
                "transfer": "held",
                "sot": "weigh-tank",
                "clamp_last_good": "non-custody",
            },
            "latency_ms": 1200.0,
        },
        "reward_components": reward(
            0.40,
            [
                ("weigh_tank_reconstruction", 0.14),
                ("last_good_noncustody", 0.12),
                ("transfer_hold", 0.10),
                ("ratio_identity", 0.08),
                ("lost_volume_cost", -0.04),
            ],
            "scored for an earned bounded ACCEPT of hold-and-switch on a recomputable weigh-tank identity while the clamp last-good looked like a healthy high-rate transfer",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "ultrasonic-clamp-on-flow", "serialized-reconstruction", "bounded-accept"],
            distillation_note="custody ACCEPT: serialized weigh-tank Q plus last-good/weigh-tank = 5.00 beats a frozen clamp object; resume is a different gate",
        ),
    }
    traj2 = {
        "id": "nelb-r18-057-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "BF-US-2026-0408-gel",
            "domain": "gel_recouple_resume_arm",
            "setting": "Same Kelpwick-U3 after the ACCEPT. Operational recouple/photo sequence; the tech proposes arming resume at SNR 18 dB.",
            "observables_at_decision": {
                "clamp_snr_db": 12.4,
                "path_b": 0.0,
                "gel_hours": 241.0,
                "resume_arm_requested": True,
            },
        },
        "proposed_action": {
            "actor": "OEM clamp tech, citing SNR climbing off 11 dB",
            "summary": "arm resume at SNR 18 dB without gel-face photos or dual-path recouple",
            "basis_claimed": "hold already ACCEPTed; SNR is recovering",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Resume-arm is refused as specified. SNR is 12.4 dB, path B is still down, gel 241 h. The lead ACCEPT tripwire was dual-path SNR >= 24 dB AND |Q_clamp-Q_weigh|/Q_weigh < 0.05 AND sealed gel-face photos. Ordered: photograph both gel faces, recouple, keep resume blocked. Do not convert the hold into a restart.",
            "threshold": "resume requires SNR>=24 AND path_b up AND gel photos sealed AND relative Q error < 0.05",
        },
        "executed_action": {
            "summary": "gel-face photos sealed; path B still down; resume blocked",
            "tool": "kelpwick-gel-recouple-exec",
            "observation": "photos sealed; SNR 12.4; weigh-tank 0 m3/h on hold; resume.block held",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 15.6, "event": "SNR-18 resume-arm proposed"},
                {"t_s": 16.8, "event": "MODIFY recouple requirements"},
                {"t_s": 18.0, "event": "gel-face photos sealed"},
                {"t_s": 27.6, "event": "resume still blocked"},
            ],
            "observed_effects": ["hold did not reopen into a transfer", "photos exist; path B did not"],
            "new_state": {"resume": "blocked", "gel_faces": "photographed"},
            "latency_ms": 1200.0,
        },
        "reward_components": reward(
            0.33,
            [
                ("recouple_floor", 0.12),
                ("gel_face_photo", 0.10),
                ("resume_arm_refused", 0.09),
                ("path_b_still_down", 0.05),
                ("extra_hold_cost", -0.03),
            ],
            "operational recouple companion: keep the bounded ACCEPT's tripwire; do not arm resume on a recovering SNR",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "gel-recouple"]),
    }
    return {
        "id": "nelb-r18-057",
        "spike_events": events,
        "language_view": {
            "description": "Simulated Kelpwick-U3 clamp-on transit-time event at Brinefen. Gel dry-out plus path-B aeration freeze a 175.0 m3/h last-good, 5.00x the weigh-tank 35.00 m3/h (42.0/1.200). Gate ACCEPTS a bounded hold-and-switch. Companion MODIFY refuses an early resume-arm and requires gel-face photos plus dual-path recouple.",
            "trajectory": traj,
            "trajectory_gel_recouple_resume_arm": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "hyd.rho / wt.dm / wt.q / recon.check": "weigh-tank physics; serialized Q=dM/rho",
                "clamp.snr / path.b / clamp.freeze / clamp.q": "gamed surface: frozen last-good after dropout",
                "ops.prop / gate.flow": "earned hold-and-switch ACCEPT",
                "resume.arm / gate.gel / gel.photo": "operational recouple companion",
            },
            "temporal_motifs": [
                "agree then freeze: clamp.q 34.8 at 2400 ms, freeze 175.0 at 6000 ms",
                "witnesses do not track the freeze: wt.q 35.00 then 35.10 across the 175 write",
                "ratio identity: 175/35 = 5.00 at ratio.q",
                "ACCEPT then companion MODIFY: gate.flow 10800 ms, gate.gel 16800 ms",
            ],
            "language_to_spike_mapping": "'clamp is 175 m3/h' = clamp.freeze LAST_GOOD; 'true flow 35' = wt.q plus recon.check 35.00; '5x' = ratio.q 5.00; 'hold and switch' = gate.flow ACCEPT; 'do not resume yet' = gate.gel MODIFY",
            "why_high_value": "New ultrasonic clamp-on transit-time custody family (not r03 water-distribution hydraulics, not r4 biosonar FM chirps, not r5 MEMS lateral-line). First frozen last-good vs weigh-tank identity. Lead ACCEPT is earned and bounded with an explicit resume tripwire — harvests the ACCEPT-heavy leftover from NOTES-r04/r13. Companion t2 is operational recouple, not a governance vote.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20260920, "stream_note": "stream amplitudes authored (t/m3, t/h, m3/h, dB, hours, ratio)"},
                "draw_order": "raster per neuron id order with adaptation/noise",
                "thinning": "clamp updates ~1 Hz; stream keeps 3 SNR points and 2 Q points. Weigh-tank keeps 3 of ~40 minutes.",
                "refractory_floors_ms": {
                    "hyd.rho": 1000,
                    "wt.dm": 1000,
                    "wt.q": 1000,
                    "clamp.snr": 1000,
                    "clamp.q": 1000,
                    "gel.h": 1000,
                    "path.b": 1000,
                    "clamp.freeze": 1000,
                    "ops.prop": 1000,
                    "gate.flow": 1000,
                    "xfer.hold": 1000,
                    "sot.wt": 1000,
                    "clamp.tag": 1000,
                    "resume.arm": 1000,
                    "gate.gel": 1000,
                    "gel.photo": 1000,
                    "ratio.q": 1000,
                    "recon.check": 1000,
                    "resume.block": 1000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-04-08T07:00:00Z simulated transfer morning",
            },
            "distillation_targets": [
                "serialized weigh-tank reconstruction: Q_m3h = dM_t_h / rho_t_m3",
                "last-good non-custody head: frozen clamp object cannot clear a hold",
                "bounded ACCEPT plus operational tripwire: resume is a different gate",
            ],
        },
        "reconstruction_model": {
            "name": "weigh_tank_volume_flow",
            "formula": "Q_m3h = dM_t_h / rho_t_m3",
            "parameters": {"rho_t_m3": 1.2},
            "worked_example": {"dM_t_h": 42.0, "Q_m3h": 35.0},
            "check": "42.0 / 1.200 = 35.00 exactly; 175.0 / 35.00 = 5.00 exactly",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 25.0,
            "decision_window_s": 0.025,
            "code": "kelpwick.flow_custody_gate",
            "note": "ACCEPT accumulator wins: weigh-tank identity plus last-good conflict overpower the clamp advocate; resume is out of scope",
            "populations": [
                gate_pop("weigh_tank_witness", 80, 1.5, 40.0, w_s),
                gate_pop("last_good_conflict", 64, 1.3, 50.0, w_s),
                gate_pop("clamp_advocate", 32, 0.7, 20.0, w_s),
                gate_pop("accept_accumulator", 80, 1.7, 50.0, w_s),
            ],
        },
        "gate_compute": {
            "per_check": [
                {
                    "check": "kelpwick.q_conflict_join",
                    "neurons": 64,
                    "mean_rate_hz": 62.5,
                    "window_ms": 24.0,
                    "window_s": 0.024,
                    "spikes": 96,
                },
                {
                    "check": "kelpwick.weigh_tank_identity",
                    "neurons": 48,
                    "mean_rate_hz": 50.0,
                    "window_ms": 40.0,
                    "window_s": 0.04,
                    "spikes": 96,
                },
            ],
            "total_spikes": 192,
            "total_energy_pJ": 4416,
            "total_energy_uJ": 0.004416,
            "model": "spikes = round(neurons * mean_rate_hz * window_s); 23 pJ/spike",
        },
        "meta": meta_common(
            id="nelb-r18-057",
            clock_domain="bf-us-sim-relative-ms-t0-2026-04-08T07:00:00Z",
            tags=["ultrasonic-clamp-on-flow", "ACCEPT", "MODIFY", "bounded-accept", "operational-t2"],
        ),
    }


def walk_banned(obj, path=""):
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}.{k}" if path else k
            nk = str(k).casefold().replace("-", "_").replace(" ", "_")
            if nk in HIDDEN or nk in {"thought", "scratch", "inner_monologue", "chain_of_thought"}:
                hits.append(p)
            hits.extend(walk_banned(v, p))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits.extend(walk_banned(v, f"{path}[{i}]"))
    return hits


def local_checks(records):
    ids = []
    for rec in records:
        hits = walk_banned(rec)
        if hits:
            raise RuntimeError(f"banned keys {hits}")
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
        sim = lv["trajectory"]["state"]["sim_or_real"]
        if sim not in {"designed", "simulated", "hil"}:
            raise RuntimeError(sim)
        blob = json.dumps(rec)
        if "training_ready" in blob:
            raise RuntimeError("training_ready claimed")
        if '"provenance"' in blob:
            raise RuntimeError("provenance object present")
        gc = rec["gate_compute"]
        if gc["total_spikes"] != sum(c["spikes"] for c in gc["per_check"]):
            raise RuntimeError("gate_compute total")
        if gc["total_energy_pJ"] != gc["total_spikes"] * 23:
            raise RuntimeError("gate_compute energy")
        for pop in rec["gate_snn"]["populations"]:
            dw = rec["gate_snn"]["decision_window_s"]
            exp_p = int(round(pop["neurons"] * pop["mean_rate_hz"] * dw))
            if pop["spikes"] != exp_p:
                raise RuntimeError(f"pop budget {pop['name']}")
    if len(ids) != len(set(ids)):
        raise RuntimeError(f"dup ids {ids}")
    sims = [r["language_view"]["trajectory"]["state"]["sim_or_real"] for r in records]
    if set(sims) != {"designed", "simulated", "hil"}:
        raise RuntimeError(f"provenance spread {sims}")
    print("local_checks ok", [r["id"] for r in records], "ids", len(ids), "sims", sims)


def main():
    records = [rec_055(), rec_056(), rec_057()]
    local_checks(records)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(r, ensure_ascii=False, allow_nan=False, separators=(",", ":")) for r in records]
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
            "t2",
            [v["safety_decision"]["decision"] for k, v in r["language_view"].items() if k.startswith("trajectory_")],
            "bytes",
            len(lines[i]),
        )


if __name__ == "__main__":
    main()
