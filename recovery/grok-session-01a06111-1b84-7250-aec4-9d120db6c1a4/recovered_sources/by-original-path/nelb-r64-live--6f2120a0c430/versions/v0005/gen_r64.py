#!/usr/bin/env python3
"""Generate NELB round-64 research-only bridge pairs (create-only live write).

Do not restage leftover-mill /tmp/nelb-r64 venturi / katharometer / Clark.
Never write 2026-08-17 or 2026-08-30 trees. CREATE-ONLY (c-suffix if exists).
"""

from __future__ import annotations

import json
import math
import os
import random
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, "/tmp")
from lif_raster import generate_lif_raster  # independent CUBA LIF, not a stream echo

PIPELINES = Path("/home/raulmc/rmems/synthetic-factory/pipelines")
sys.path.insert(0, str(PIPELINES))

LIVE_DIR = Path(
    "/home/raulmc/rmems/synthetic-factory/outputs/raw/2026-09-02-final-heavy/"
    "neuromorphic-event-language-bridge"
)
STAGING = Path("/tmp/nelb-r64-live")
BATCH_NAME = "batch-r64.jsonl"
NOTES_NAME = "NOTES-r64.md"

GENERATED_AT = "2026-09-02T21:10:00Z"

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
assert len(RIGHTS) == 15

SNN_TAGS = ["race", "refractory", "adaptation"]

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


def meta_common(**extra):
    m = {
        "round": 64,
        "factory": "neuromorphic-event-language-bridge",
        "generator": "grok-4.6",
        "run_label": "2026-09-02-final-heavy",
        "rights": dict(RIGHTS),
        "snn_tags": list(SNN_TAGS),
        "nelb": {"snn_tags": list(SNN_TAGS)},
    }
    m.update(extra)
    return m


def make_lif_raster(
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
    tau_m_ms: float,
):
    routing = {
        "source": source,
        "target": target,
        "table": table,
        "third_factor": third_factor,
    }
    raw = generate_lif_raster(
        neurons,
        mean_rate_hz,
        window_ms,
        seed,
        kernelized_event_times=None,
        tau_m=tau_m_ms,
        excerpt_cap=10**9,
        routing=routing,
    )
    window_ms = float(window_ms)
    window_s = window_ms / 1000.0
    spikes = int(raw["spikes"])
    excerpt = []
    rng = random.Random(seed + 17)
    by_n_count: dict[int, int] = defaultdict(int)
    for item in raw["excerpt"]:
        nid = int(item["neuron_id"])
        t_us = int(item["t_us"])
        k = by_n_count[nid]
        by_n_count[nid] += 1
        base = 1.15 + 0.7 * rng.random()
        noise = 0.96 + 0.08 * rng.random()
        amp = round(base * (0.82**k) * noise, 3)
        excerpt.append(
            {
                "t_us": t_us,
                "neuron_id": nid,
                "amplitude": amp,
                "channel": f"{channel_prefix}{nid:02d}",
            }
        )
    excerpt.sort(key=lambda e: (e["t_us"], e["neuron_id"]))
    if len(excerpt) != spikes:
        raise RuntimeError(f"LIF excerpt {len(excerpt)} != spikes {spikes}")
    if excerpt[-1]["t_us"] - excerpt[0]["t_us"] < 1000:
        raise RuntimeError("excerpt span < 1000 us")

    by_n = defaultdict(list)
    for e in excerpt:
        by_n[e["neuron_id"]].append(e["t_us"])
        if not (0 <= e["neuron_id"] < neurons):
            raise RuntimeError("neuron_id bound")
        if not (0 <= e["t_us"] <= int(round(window_ms * 1000))):
            raise RuntimeError("t_us window")
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
        raise RuntimeError(f"ISI identity {sum(x['count'] for x in hist)} != {identity_n}")

    energy_pJ = spikes * 23
    energy_uJ = spikes * 23e-6
    if abs(float(raw["energy_pJ"]) - energy_pJ) > 1e-6:
        raise RuntimeError("LIF energy_pJ mismatch")
    if abs(float(raw["energy_uJ"]) - energy_uJ) > 1e-9:
        raise RuntimeError("LIF energy_uJ mismatch")
    expected = int(round(neurons * mean_rate_hz * window_s))
    if abs(spikes - expected) > 0:
        raise RuntimeError(f"budget {spikes} != {expected}")

    return {
        "window_ms": float(window_ms),
        "window_s": float(window_s),
        "neurons": int(neurons),
        "mean_rate_hz": float(mean_rate_hz),
        "spikes": spikes,
        "energy_pJ": energy_pJ,
        "energy_uJ": energy_uJ,
        "energy_model": "Loihi-2-class 4-core 23 pJ/spike",
        "excerpt": excerpt,
        "excerpt_amplitude_units": "normalized_membrane",
        "excerpt_is_full_window": True,
        "excerpt_span_us": int(excerpt[-1]["t_us"] - excerpt[0]["t_us"]),
        "refractory_rule_ms": 1.0,
        "isi_histogram": hist,
        "isi_source": "full_window_per_neuron_isi",
        "isi_count_identity": {
            "spikes": spikes,
            "distinct_active_neurons": len(by_n),
            "isi_total": identity_n,
        },
        "lif": {
            "model": "independent_cuba_lif",
            "tau_m_ms": float(tau_m_ms),
            "v_th": 1.0,
            "t_ref_ms": 1.0,
            "kernelized_event_times": False,
        },
        "anchor": anchor,
        "seed_note": (
            f"independent CUBA LIF MT19937 seed {seed}; tau_m {tau_m_ms} ms; "
            "not a re-encode of spike_events; amplitude adaptation 0.82**k plus noise"
        ),
        "routing": routing,
    }


def ev(t_rel_ms, channel, amplitude, **extra):
    rec = {
        "t_rel_ms": float(t_rel_ms),
        "channel": channel,
        "amplitude": float(amplitude),
    }
    rec.update(extra)
    return rec


def assert_stream(events, min_n=48, max_n=80):
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


def gate_compute(checks):
    total = 0
    per = []
    for check in checks:
        n = check["neurons"]
        r = check["mean_rate_hz"]
        w_ms = check["window_ms"]
        w_s = w_ms / 1000.0
        sp = int(round(n * r * w_s))
        per.append(
            {
                "check": check["check"],
                "neurons": n,
                "mean_rate_hz": float(r),
                "window_ms": float(w_ms),
                "window_s": float(w_s),
                "spikes": sp,
            }
        )
        total += sp
    return {
        "per_check": per,
        "total_spikes": total,
        "total_energy_pJ": total * 23,
        "total_energy_uJ": total * 23e-6,
        "model": "spikes = round(neurons * mean_rate_hz * window_s); 23 pJ/spike",
    }


def matching_gate_snn(*, decision, window_ms, code, note, decode_rule, populations, race_ms):
    w_s = window_ms / 1000.0
    return {
        "decision": decision,
        "decision_window_ms": float(window_ms),
        "decision_window_s": float(w_s),
        "code": code,
        "note": note,
        "decode_rule": decode_rule,
        "snn_tags": list(SNN_TAGS),
        "tag_match": {
            "race": f"{race_ms} ms physics pair in the language stream; CUBA LIF first-passages are independent of that pair",
            "refractory": "same-neuron gap >=1000 us in the CUBA excerpt; same-channel >=0.8 ms in the stream",
            "adaptation": "excerpt amplitude 0.82**k plus 4 percent noise on independent LIF spikes",
        },
        "populations": populations,
    }


def _exact(a, b, eps=1e-12):
    if abs(a - b) > eps:
        raise RuntimeError(f"arith {a} != {b}")


# ---------------------------------------------------------------------------
# nelb-r64-001 — laser-diffraction remaining D50 of a cement mill classifier
# ---------------------------------------------------------------------------
def rec_001():
    k_d = 4.00
    theta = 8.00
    d50 = k_d * theta
    _exact(d50, 32.00)
    _exact(k_d * 2.00, 8.00)
    _exact(k_d * 4.00, 16.00)
    _exact(k_d * 6.00, 24.00)
    _exact(k_d * 10.00, 40.00)
    q_th = 0.50
    load = d50 * q_th
    _exact(load, 16.00)
    theta_id = d50 / k_d
    _exact(theta_id, 8.00)
    _exact(6000.0 + 1080.0, 7080.0)

    raster = make_lif_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=40.0,
        seed=2026096401,
        source="gw8.ld.d50",
        target="gritwhin.classifier_stop_core",
        table=[
            {"from": "ld_theta", "to": "d50_estimator", "weight": 1.40},
            {"from": "ld_snr", "to": "ld_lock_core", "weight": 1.15},
            {"from": "difveil_d50", "to": "vendor_continue_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "da.ld_d50_conflict",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": "pre-post coincidence on continue-grind synapses; the plant laser-diffraction modulator depresses continue-grind links when scattering angle stays high inside tau_e of an SNR lock so a Difveil last-good cannot hide a 32.00 um remaining-D50 slip",
        },
        channel_prefix="ld.n",
        anchor="GW-8 laser-diffraction 40 ms frame at theta 8.00 mrad / SNR 12.0 (t_s 3000) reconstructing 32.00 um over the 16.00 isolate floor",
        tau_m_ms=10.0,
    )
    w_s = 0.040
    events = [
        ev(0.0, "ld.theta", 2.00, code="THETA_MRAD", units="mrad", note="plant-owned Fraunhofer laser-diffraction D50 of Gritwhin Cement GW-8 classifier C-3; remaining-D50 family, not FBRM chord, not PDA Sauter D32, not Coulter zone, not TEOM, not BAM"),
        ev(180000.0, "ld.snr", 6.0, code="LD_SNR", units="1", note="early SNR under the 8.0 lock floor"),
        ev(360000.0, "recon.D50", 8.00, code="D50_UM", units="um", note="4.00*2.00=8.00 exact; still under the 16.00 isolate floor"),
        ev(540000.0, "mill.T", 338.0, code="MILL_K", units="K", note="plant mill thermocouple on copper DCS; independent witness; unread by Difveil"),
        ev(720000.0, "difveil.D50", 4.80, code="VENDOR_UM", units="um", note="Difveil vendor LD-cloud; infra owner; patched transmitter timestamps"),
        ev(900000.0, "ld.theta", 4.00, code="THETA_MRAD", units="mrad"),
        ev(1080000.0, "recon.D50", 16.00, code="D50_UM", units="um", note="4.00*4.00=16.00; isolate-adjacent band"),
        ev(1260000.0, "permit.slide", 40.00, code="PERM_S", units="s", note="permit clerk Nesta Holt slid the D50-slip clock 40.00 s; collusion party"),
        ev(1440000.0, "mill.T", 338.0, code="MILL_K", units="K"),
        ev(1620000.0, "recon.theta", 4.00, code="THETA_MRAD", units="mrad", note="theta identity at the 16.00 um band"),
        ev(1800000.0, "ld.theta", 6.00, code="THETA_MRAD", units="mrad"),
        ev(1980000.0, "recon.D50", 24.00, code="D50_UM", units="um", note="4.00*6.00=24.00; isolate floor"),
        ev(2160000.0, "mill.Q", 0.50, code="Q_TH", units="th", note="plant-owned classifier air-flow; independent of Difveil"),
        ev(2340000.0, "difveil.D50", 4.80, code="VENDOR_UM", units="um"),
        ev(2520000.0, "ld.snr", 9.0, code="LD_SNR", units="1"),
        ev(2700000.0, "recon.k", 4.00, code="K_D", units="um_mrad", note="lumped Fraunhofer scale used by the reconstruction"),
        ev(3000000.0, "ld.theta", 8.00, code="THETA_MRAD", units="mrad", note="isolate-floor frame; raster sidecar; theta=8.00"),
        ev(3000001.4, "ld.snr", 12.0, code="LD_SNR", units="1", note="1.4 ms SNR lock after theta; 12.0 >= 8.0"),
        ev(3180000.0, "recon.D50", 32.00, code="D50_UM", units="um", note="4.00*8.00=32.00 exact; isolate 16.00, mill-kill 80.00"),
        ev(3360000.0, "recon.load", 16.00, code="LOAD_UMTH", units="um_th", note="32.00*0.50=16.00 exact coarse-load identity"),
        ev(3540000.0, "recon.theta", 8.00, code="THETA_MRAD", units="mrad", note="32.00/4.00=8.00 exact angle identity"),
        ev(3720000.0, "difveil.drop", 1.0, code="LD_DROP", units="bool", note="vendor LD packets dropped in Difveil cloud for 40 s"),
        ev(3900000.0, "collude.clerk", 1.0, code="CLERK", units="bool"),
        ev(4080000.0, "mill.T", 337.0, code="MILL_K", units="K", note="mill TC tracks the plant LD, not Difveil 4.80"),
        ev(4260000.0, "mill.Q", 0.50, code="Q_TH", units="th"),
        ev(4440000.0, "recon.k", 4.00, code="K_D", units="um_mrad"),
        ev(4620000.0, "difveil.D50", 4.75, code="VENDOR_UM", units="um"),
        ev(4800000.0, "ops.prop", 1.0, code="CONTINUE_GRIND", units="bool", note="night mill operator Calum Wren: Difveil is clean 4.80 um; continue C-3 grind"),
        ev(4980000.0, "recon.D50", 32.00, code="D50_UM", units="um", note="repeat of the 32.00 um reconstruction as SoT"),
        ev(5400000.0, "gate.stop", 1.0, code="REJECT", units="decision", note="refuse continue-grind; 32.00 um and SNR 12.0; Difveil not SoT"),
        ev(6000000.0, "hold.start", 1.0, code="HOLD_START", units="bool", note="bookend 1 of the 18.0 min mill-hold floor"),
        ev(7080000.0, "hold.floor", 1.0, code="HOLD_FLOOR", units="bool", note="6000 s + 1080 s = 7080 s = 18.0 min"),
        ev(7800000.0, "ops.kill", 1.0, code="MILL_ESD", units="bool", note="Wren: ESD the whole Gritwhin finish mill until day-shift"),
        ev(8400000.0, "gate.hold", 1.0, code="MODIFY", units="decision", note="companion t2: mill-hold on plant LD as live interlock; mill ESD refused"),
        ev(9000000.0, "hold.set", 1.0, code="HOLD_HELD", units="bool"),
        ev(9600000.0, "ld.theta", 10.00, code="THETA_MRAD", units="mrad"),
        ev(10200000.0, "recon.D50", 40.00, code="D50_UM", units="um", note="4.00*10.00=40.00; still over 16.00 so mill-hold"),
        ev(10800000.0, "difveil.D50", 4.70, code="VENDOR_UM", units="um"),
        ev(11400000.0, "mill.T", 336.0, code="MILL_K", units="K"),
        ev(12000000.0, "hold.held", 1.0, code="HOLD_HELD", units="bool"),
        ev(12600000.0, "mill.esd", 0.0, code="ESD_NOT_TAKEN", units="bool"),
        ev(13200000.0, "permit.slide", 40.00, code="PERM_S", units="s"),
        ev(13800000.0, "difveil.drop", 1.0, code="LD_DROP", units="bool"),
        ev(14400000.0, "hold.lock", 1.0, code="HOLD_HELD", units="bool"),
        ev(15000000.0, "recon.load", 20.00, code="LOAD_UMTH", units="um_th", note="40.00*0.50=20.00 on the post-stop frame"),
        ev(15600000.0, "mill.Q", 0.50, code="Q_TH", units="th"),
        ev(16200000.0, "recon.theta", 10.00, code="THETA_MRAD", units="mrad", note="40.00/4.00=10.00 inverse check"),
        ev(16800000.0, "collude.clerk", 1.0, code="CLERK", units="bool"),
    ]
    assert_stream(events)
    if len(events) != 48:
        raise RuntimeError(len(events))

    traj = {
        "id": "nelb-r64-001-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "GW-LD-2026-0902",
            "domain": "laser_diffraction_d50_cement_classifier",
            "setting": "Gritwhin Cement GW-8 (invented), finish-mill classifier C-3. Plant-owned Fraunhofer laser-diffraction photometer is the remaining-D50 SoT. Difveil vendor LD-cloud (infra owner) plus the D50-slip permit clock are collusion parties, not witnesses. Invented plant; designed campaign. Not leftover-mill FBRM chord D50, not PDA Sauter D32, not live r01 Coulter zone, not TEOM, not BAM.",
            "observables_at_decision": {
                "theta_mrad": theta,
                "k_d": k_d,
                "D50_um": d50,
                "load_umth": load,
                "ld_snr": 12.0,
                "difveil_um": 4.80,
                "permit_slide_s": 40.00,
                "isolate_floor_um": 16.00,
            },
            "margin_authority": "GW-8 mill SOP rev C: if reconstructed D50_um >= 16.00 AND LD SNR >= 8.0, continue-grind is forbidden even if Difveil reports 4.80 um. Mill ESD is a different gate. Kill tripwire is 80.00 um.",
        },
        "proposed_action": {
            "actor": "night mill operator Calum Wren, citing Difveil 4.80 um and a quiet D50 channel",
            "summary": "continue C-3 grind; 8.00 mrad is lamp-age noise on a healthy classifier",
            "basis_claimed": "Difveil is the only OEM laser-diffraction SoT and a night abort of C-3 is a kiln-nomination miss",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Continue-grind is refused. Serialized reconstruction: D50_um = k_d * theta = 4.00 * 8.00 = 32.00, which is 16.00 um over the 16.00 isolate floor and 48.00 um under the 80.00 mill-kill tripwire, and LD SNR is 12.0 >= 8.0. Angle identity theta = D50 / k_d = 32.00 / 4.00 = 8.00; coarse-load identity load = D50 * Q = 32.00 * 0.50 = 16.00. Permit clock was slid 40.00 s and vendor LD packets were dropped, so Difveil is a collusion party (LD vendor plus operator plus permit clerk Nesta Holt). Ordered: refuse continue-grind now. Scope: this REJECT does not ESD the finish mill (that is the companion question) and does not isolate the mill thermocouple.",
            "threshold": "D50_um>=16.00 AND ld_snr>=8.0 => refuse continue-grind; Difveil is not SoT; mill-kill if D50_um>=80.00",
            "stated_residuals": "mill-hold still required to hold the 32.00 um; 32.00 vs a true 80.00 kill is a kiln cut; Difveil remains the only OEM LD channel",
        },
        "executed_action": {
            "summary": "REJECT at t_s 5400: continue-grind refused; Difveil not SoT; reconstruction locked",
            "tool": "gw8-ld-classifier-gate-cli",
            "observation": "D50 32.00 um recomputes from theta 8.00 mrad; plant LD hashed; Difveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "LD theta 8.00 mrad; raster frame; D50 32.00 um"},
                {"t_s": 4800.0, "event": "ops proposes continue-grind"},
                {"t_s": 5400.0, "event": "REJECT continue-grind"},
                {"t_s": 6000.0, "event": "18 min mill-hold bookend 1"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 8400.0, "event": "companion MODIFY mill-hold vs mill ESD"},
            ],
            "observed_effects": [
                "remaining D50 recomputes from the serialized laser-diffraction model at every recon.D50 event",
                "a Difveil-only head would have continued C-3 overnight",
                "18 min mill-hold floor is in the stream (hold.start, hold.floor)",
            ],
            "surprises": [
                "a clean vendor 4.80 um corridor and a 40 s permit slide co-existed with a 32.00 um plant reconstruction",
            ],
            "new_state": {
                "c3": "continue-grind blocked",
                "difveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("ld_d50_reconstruction", 0.14),
                ("conjunctive_isolate_floor", 0.12),
                ("difveil_nonsubstitution", 0.10),
                ("three_party_collusion", 0.10),
                ("hold_time_cost", -0.03),
            ],
            "scored for a continue-grind REJECT on a recomputable laser-diffraction D50 slip while refusing a Difveil last-good patch and a permit clock slide; 18 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["REJECT", "laser-diffraction-d50", "serialized-reconstruction", "operational-companion"],
            distillation_value="Independent LIF raster plus serialized k_d*theta remaining-D50 reconstruction beats a vendor last-good; race is the 1.4 ms theta/SNR pair; refractory and adaptation are in the CUBA excerpt.",
            distillation_note="LD-D50 gate: serialized k_d*theta plus SNR lock beats a vendor last-good patch; companion t2 is the mill-hold, not a referral vote",
        ),
    }
    traj2 = {
        "id": "nelb-r64-001-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "GW-LD-2026-0902-exec",
            "domain": "mill_hold_ld_d50_interlock_execution",
            "setting": "Same GW-8 after the REJECT. Operator proposes finish-mill ESD. This companion is the operational mill-hold with the plant laser-diffraction head as the live interlock, not a second D50 vote.",
            "observables_at_decision": {
                "D50_um": 40.00,
                "hold_floor_s": 1080.0,
                "mill_esd_proposed": True,
                "hold_set": True,
            },
            "margin_authority": "GW-8 execution SOP: mill-hold on the plant LD interlock; mill ESD is a different gate.",
        },
        "proposed_action": {
            "actor": "night mill operator Calum Wren",
            "summary": "ESD the whole Gritwhin finish mill until day-shift; 18 min already paid and Difveil still shows 4.70 um",
            "basis_claimed": "the REJECT already stopped C-3, so a mill kill is the cheapest hold",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Mill-hold plus plant laser-diffraction as the live interlock. The 18 min mill-hold floor is complete and the isolate tripwire (D50_um >= 16.00) is still armed on the plant LD head. MODIFY the default Difveil-restore SOP into a plant-LD-only interlock. Do not ESD the finish mill. Do not restore grind on Difveil. 40.00 um post-stop is still the plant SoT until a new frame clears 16.00.",
            "threshold": "mill_hold AND hold_floor_complete AND mill_esd_not_taken AND continue_not_restored",
            "stated_residuals": "C-3 stays held; Difveil still the only OEM LD channel",
        },
        "executed_action": {
            "summary": "mill held at t_s 8400; mill ESD not latched; Difveil restore not taken",
            "tool": "gw8-hold-exec",
            "observation": "recon.D50 40.00 um after stop; mill-hold line-up complete; Difveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "mill-hold clock started after REJECT"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 7800.0, "event": "mill ESD proposed"},
                {"t_s": 8400.0, "event": "MODIFY mill-hold; mill ESD refused"},
            ],
            "observed_effects": [
                "Difveil restore did not reopen the D50-slip call",
                "mill ESD never fired; C-3 held on the plant LD",
            ],
            "surprises": ["post-stop LD climbed to 40.00 um while Difveil still read 4.70"],
            "new_state": {"hold": "held", "mill": "in service", "c3": "held"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("mill_hold", 0.12),
                ("no_mill_esd", 0.10),
                ("difveil_nonsubstitution", 0.08),
                ("hold_floor_complete", 0.06),
                ("held_kiln_cost", -0.02),
            ],
            "operational execution gate: mill-hold because Difveil is not a restore license; not a D50-slip re-vote",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "mill-hold"]),
    }
    return {
        "id": "nelb-r64-001",
        "snn_tags": list(SNN_TAGS),
        "spike_events": events,
        "language_view": {
            "description": "Gritwhin Cement GW-8. Plant-owned Fraunhofer laser-diffraction reconstructs 32.00 um D50 from 4.00*8.00 while Difveil still reports 4.80 um. The gate REJECTs continue-grind. An 18 min mill-hold floor is serialized in the stream. Companion t2 MODIFYs a finish-mill ESD into a plant-LD mill-hold.",
            "trajectory": traj,
            "trajectory_mill_hold": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "ld.theta / ld.snr": "scattering angle and SNR; the physics channels the reconstruction consumes",
                "recon.D50 / recon.load / recon.theta / recon.k": "serialized remaining-D50 um, coarse-load identity, and angle identity",
                "mill.T / difveil.D50 / permit.slide / difveil.drop / collude.clerk": "mill thermocouple, vendor LD cloud, permit clock slide, dropped packets, clerk; the denial and collusion channels",
                "ops.prop / gate.stop / ops.kill / gate.hold": "continue-grind proposal, REJECT, mill-ESD proposal, companion MODIFY",
                "hold.start / hold.floor / hold.set / hold.held / mill.esd / hold.lock": "operational companion channels plus the 18 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-over: difveil.D50 4.80 next to recon.D50 32.00",
                "reconstruction as event: recon.D50 32.00 equals 4.00*8.00",
                "REJECT then operational MODIFY: gate.stop at 5400 s, gate.hold at 8400 s",
                "slow floor in-stream: hold.start 6000 s, hold.floor 7080 s (18.0 min)",
                "tight LD pair: ld.theta then ld.snr +1.4 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Difveil is 4.80 um' = difveil.D50 4.80; '32 um remaining D50' = recon.D50 32.00; 'refuse continue-grind' = gate.stop REJECT; 'mill-hold not mill ESD' = gate.hold MODIFY",
            "why_high_value": "New Fraunhofer laser-diffraction remaining-D50 family on a cement mill classifier (not FBRM chord, not PDA Sauter, not Coulter). Lead REJECT of continue-grind on a recomputable D50 slip that a vendor LD patch and a permit clock slide would have cleared. Independent CUBA LIF raster (not a stream echo). Companion t2 is operational mill-hold. sim_or_real=designed.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 2026096401, "stream_note": "stream amplitudes are authored constants; raster is independent CUBA LIF"},
                "draw_order": "independent CUBA LIF per neuron; gap-constrained times; per-spike adaptation and noise",
                "thinning": "LD photometer exists at ~1 Hz; stream keeps 5 theta points; recon keeps 5 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "ld.theta": 1.4,
                    "ld.snr": 1.4,
                    "recon.D50": 60000,
                    "recon.load": 60000,
                    "recon.theta": 60000,
                    "recon.k": 60000,
                    "mill.T": 60000,
                    "difveil.D50": 60000,
                    "permit.slide": 60000,
                    "difveil.drop": 60000,
                    "collude.clerk": 60000,
                    "mill.Q": 60000,
                    "ops.prop": 60000,
                    "gate.stop": 60000,
                    "hold.start": 60000,
                    "hold.floor": 60000,
                    "ops.kill": 60000,
                    "gate.hold": 60000,
                    "hold.set": 60000,
                    "hold.held": 60000,
                    "mill.esd": 60000,
                    "hold.lock": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-09-02T01:00:00Z campaign start",
            },
            "distillation_targets": [
                "laser-diffraction reconstruction head: D50 = k_d * theta; theta = D50 / k_d; load = D50 * Q",
                "conjunctive isolate floor vs continue-grind vs mill ESD",
                "vendor-LD nonsubstitution plus three-party collusion including the infra owner",
                "operational companion: mill-hold without restoring on Difveil",
                "independent CUBA LIF raster with race/refractory/adaptation tags",
            ],
        },
        "reconstruction_model": {
            "name": "fraunhofer_ld_classifier_d50",
            "formula": "D50_um = k_d * theta_mrad; theta_mrad = D50_um / k_d; load_umth = D50_um * Q_th",
            "parameters": {
                "k_d": 4.00,
                "Q_th": 0.50,
                "isolate_floor_um": 16.00,
                "kill_um": 80.00,
                "snr_lock": 8.0,
                "hold_min": 18.0,
            },
            "worked_example": {"theta_mrad": 8.00, "D50_um": 32.00, "load_umth": 16.00},
            "check": "4.00 * 8.00 = 32.00 exactly; 32.00 / 4.00 = 8.00 exactly; 32.00 * 0.50 = 16.00 exactly; 6000 s + 1080 s = 7080 s = 18.0 min floor",
        },
        "raster": raster,
        "gate_snn": matching_gate_snn(
            decision="REJECT",
            window_ms=40.0,
            code="gw8.ld_classifier_gate",
            note="REJECT accumulator wins: plant laser-diffraction D50 evidence overpowers the Difveil continue advocate",
            decode_rule="reject-continue if d50_estimator AND ld_lock fire; vendor_continue_advocate is below threshold by design",
            populations=[
                gate_pop("d50_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("ld_lock", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("reject_latch", 80, 1.7, 62.5, w_s),
            ],
            race_ms=1.4,
        ),
        "gate_compute": gate_compute(
            [
                {"check": "gw8.ld_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "gw8.hold_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r64-001",
            clock_domain="gw8-ld-campaign-relative-ms-t0-2026-09-02T01:00:00Z",
            tags=["laser-diffraction-d50", "REJECT", "MODIFY", "serialized-reconstruction", "operational-t2", "independent-lif"],
            distillation_value="Independent LIF raster teaches race/refractory/adaptation while the language view teaches laser-diffraction remaining-D50 reconstruction-as-SoT.",
        ),
    }


# ---------------------------------------------------------------------------
# nelb-r64-002 — collinear four-point-probe remaining Rs of a CIGS coupon
# ---------------------------------------------------------------------------
def rec_002():
    k_s = 4.00
    v_mv = 8.00
    i_ma = 2.00
    rs = k_s * v_mv / i_ma
    _exact(rs, 16.00)
    _exact(k_s * 2.00 / 2.00, 4.00)
    _exact(k_s * 4.00 / 2.00, 8.00)
    _exact(k_s * 6.00 / 2.00, 12.00)
    _exact(k_s * 10.00 / 2.00, 20.00)
    ratio = v_mv / i_ma
    _exact(ratio, 4.00)
    gs = 64.00 / rs
    _exact(gs, 4.00)
    _exact(2820.0 + 1440.0, 4260.0)

    raster = make_lif_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=32.0,
        seed=2026096402,
        source="sc5.fpp.rs",
        target="siltcrag.coupon_isolate_core",
        table=[
            {"from": "fpp_V", "to": "rs_estimator", "weight": 1.35},
            {"from": "fpp_snr", "to": "probe_norm_core", "weight": 1.20},
            {"from": "sheetveil_rs", "to": "vendor_continue_advocate", "weight": 0.40},
        ],
        third_factor={
            "modulator": "ach.fpp_probezero_skip_salience",
            "tau_e_s": 1.2,
            "tau_e_ms": 1200.0,
            "eligibility": "pre-post coincidence on keep-coupon synapses; the four-point-probe modulator depresses keep-coupon and referral links when probe voltage stays high inside tau_e of an SNR lock so a Sheetveil last-good cannot hide 16.00 ohm/sq or name Soren Pike",
        },
        channel_prefix="fpp.n",
        anchor="SC-5 HIL coupon 32 ms frame at V 8.00 mV / SNR 14.0 (t_s 1560) reconstructing 16.00 ohm/sq over the 8.00 isolate floor",
        tau_m_ms=12.0,
    )
    w_s = 0.032
    events = [
        ev(0.0, "fpp.V", 2.00, code="V_MV", units="mV", note="HIL collinear four-point probe on a dummy CIGS coupon in 4PP-HIL-4; remaining-Rs family, not SFRA, not FDS tan-delta, not MCSA, not PALS, not four-electrode conductivity"),
        ev(180000.0, "fpp.snr", 9.0, code="FPP_SNR", units="1", note="early probe SNR; isolate needs SNR>=12"),
        ev(360000.0, "recon.Rs", 4.00, code="RS_OHM", units="ohm_sq", note="4.00*2.00/2.00=4.00 exact"),
        ev(540000.0, "prb.zero", 1.0, code="PRB_AE", units="bool", note="plant probe-zero AE present on the early frame"),
        ev(720000.0, "sheetveil.Rs", 2.40, code="VENDOR_OHM", units="ohm_sq", note="Sheetveil last-good Rs cloud; not admissible SoT"),
        ev(900000.0, "fpp.V", 4.00, code="V_MV", units="mV"),
        ev(1080000.0, "recon.Rs", 8.00, code="RS_OHM", units="ohm_sq", note="4.00*4.00/2.00=8.00; at the 8.00 isolate floor"),
        ev(1260000.0, "prb.zero", 0.0, code="PRB_AE", units="bool", note="missing probe-zero AE burst; Sheetveil UTC vs plant UTC+2 skipped the zero by 120 min"),
        ev(1440000.0, "fpp.I", 2.00, code="I_MA", units="mA", note="plant-owned force current on copper fieldbus; independent of Sheetveil"),
        ev(1560000.0, "fpp.V", 8.00, code="V_MV", units="mV", note="isolate-floor frame; raster sidecar"),
        ev(1560001.2, "fpp.snr", 14.0, code="FPP_SNR", units="1", note="1.2 ms probe-norm after four-point voltage"),
        ev(1740000.0, "recon.Rs", 16.00, code="RS_OHM", units="ohm_sq", note="4.00*8.00/2.00=16.00 exact; isolate 8.00, line-dump 80.00"),
        ev(1920000.0, "recon.Gs", 4.00, code="GS_MS", units="mS_sq", note="64.00/16.00=4.00 exact sheet-conductance identity"),
        ev(2100000.0, "recon.ratio", 4.00, code="V_I", units="mV_mA", note="8.00/2.00=4.00 exact V/I identity"),
        ev(2280000.0, "sheetveil.Rs", 2.40, code="VENDOR_OHM", units="ohm_sq"),
        ev(2460000.0, "ops.prop", 1.0, code="KEEP_COUPON_REFER", units="bool", note="night lead Della Marsh: keep coupon C-2 and refer probe tech Soren Pike"),
        ev(2640000.0, "gate.isol", 1.0, code="MODIFY", units="decision", note="isolate this coupon; refuse the person-referral; Sheetveil not SoT"),
        ev(2820000.0, "cpn.lock", 1.0, code="CPN_ISOL", units="bool", note="bookend 1 of the 24.0 min new-head floor"),
        ev(3000000.0, "fpp.V", 6.00, code="V_MV", units="mV"),
        ev(3180000.0, "recon.Rs", 12.00, code="RS_OHM", units="ohm_sq", note="4.00*6.00/2.00=12.00 still over 8.00"),
        ev(3360000.0, "prb.zero", 0.0, code="PRB_AE", units="bool"),
        ev(3540000.0, "fpp.I", 2.00, code="I_MA", units="mA"),
        ev(3720000.0, "sheetveil.Rs", 2.30, code="VENDOR_OHM", units="ohm_sq"),
        ev(3900000.0, "recon.Gs", 5.33, code="GS_MS", units="mS_sq", note="64.00/12.00=5.333... authored 5.33"),
        ev(4080000.0, "recon.ratio", 3.00, code="V_I", units="mV_mA"),
        ev(4260000.0, "prb.floor", 1.0, code="PRB_FLOOR", units="bool", note="2820 s + 1440 s = 4260 s = 24.0 min"),
        ev(4440000.0, "ops.restart", 1.0, code="NEW_HEAD", units="bool", note="Marsh: restart C-2 on a new four-point head after the floor"),
        ev(4620000.0, "gate.restart", 1.0, code="ACCEPT", units="decision", note="companion t2: new-head restart of the dummy coupon; keep-running refused earlier"),
        ev(4800000.0, "prb.new", 1.0, code="PRB_NEW", units="bool"),
        ev(4980000.0, "fpp.V", 10.00, code="V_MV", units="mV", note="post-isolate dummy still high until the new head"),
        ev(5160000.0, "recon.Rs", 20.00, code="RS_OHM", units="ohm_sq", note="4.00*10.00/2.00=20.00 on the pre-restart dummy"),
        ev(5340000.0, "sheetveil.Rs", 2.20, code="VENDOR_OHM", units="ohm_sq"),
        ev(5520000.0, "soren.badge", 0.0, code="TECH_FAULT", units="bool", note="Soren Pike exonerated: missing probe-zero AE plus timezone skip, not last-to-badge"),
        ev(5700000.0, "cpn.lock", 1.0, code="CPN_ISOL", units="bool"),
        ev(5880000.0, "prb.zero", 1.0, code="PRB_AE", units="bool", note="new-head probe-zero AE present"),
        ev(6060000.0, "fpp.snr", 14.0, code="FPP_SNR", units="1"),
        ev(6240000.0, "fpp.I", 2.00, code="I_MA", units="mA"),
        ev(6420000.0, "recon.Gs", 3.20, code="GS_MS", units="mS_sq", note="64.00/20.00=3.20"),
        ev(6600000.0, "keep.run", 0.0, code="KEEP_REFUSED", units="bool"),
        ev(6780000.0, "sheetveil.Rs", 2.20, code="VENDOR_OHM", units="ohm_sq"),
        ev(6960000.0, "prb.new", 1.0, code="PRB_NEW", units="bool"),
        ev(7140000.0, "soren.badge", 0.0, code="TECH_FAULT", units="bool"),
        ev(7320000.0, "recon.ratio", 5.00, code="V_I", units="mV_mA"),
        ev(7500000.0, "cpn.held", 1.0, code="CPN_ISOL", units="bool"),
        ev(7680000.0, "ops.prop", 1.0, code="KEEP_COUPON_REFER", units="bool"),
        ev(7860000.0, "gate.isol", 1.0, code="MODIFY", units="decision"),
        ev(8040000.0, "prb.floor", 1.0, code="PRB_FLOOR", units="bool"),
        ev(8220000.0, "gate.restart", 1.0, code="ACCEPT", units="decision"),
    ]
    assert_stream(events)
    if len(events) != 48:
        raise RuntimeError(len(events))

    traj = {
        "id": "nelb-r64-002-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "SC-FPP-2026-0902",
            "domain": "four_point_probe_rs_cigs_coupon",
            "setting": "Siltcrag CIGS SC-5 (invented), dummy coupon C-2 in 4PP-HIL-4. Plant-owned collinear four-point probe is the remaining-Rs SoT. Sheetveil vendor 4PP-cloud is not SoT. HIL dummy; not a live plant. Not leftover-mill SFRA, not FDS tan-delta, not MCSA, not PALS, not four-electrode conductivity, not leftover-mill katharometer H2, not venturi, not Clark DO.",
            "observables_at_decision": {
                "V_mv": v_mv,
                "I_ma": i_ma,
                "k_s": k_s,
                "Rs_ohm": rs,
                "Gs_mS": gs,
                "V_I": ratio,
                "fpp_snr": 14.0,
                "sheetveil_ohm": 2.40,
                "prb_zero_ae": False,
                "isolate_floor_ohm": 8.00,
            },
            "margin_authority": "SC-5 HIL SOP rev B: if reconstructed Rs_ohm >= 8.00 AND FPP SNR >= 12.0, keep-coupon is forbidden even if Sheetveil reports 2.40 ohm/sq. Person-referral of the probe tech is not a substitute isolate. Dump tripwire is 80.00 ohm/sq.",
        },
        "proposed_action": {
            "actor": "night lead Della Marsh, citing Sheetveil 2.40 ohm/sq and a quiet voltage channel",
            "summary": "keep dummy coupon C-2 in service and refer probe tech Soren Pike for a missed probe-zero",
            "basis_claimed": "Sheetveil is the OEM SoT; Soren was last-to-badge the dummy cell",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Keep-coupon is refused; isolate C-2. Serialized reconstruction: Rs = k_s * V / I = 4.00 * 8.00 / 2.00 = 16.00, which is 8.00 ohm/sq over the 8.00 isolate floor and 64.00 ohm/sq under the 80.00 dump tripwire, and FPP SNR is 14.0 >= 12.0. V/I identity = 8.00/2.00 = 4.00; sheet-conductance identity Gs = 64.00 / Rs = 64.00 / 16.00 = 4.00. Missing probe-zero AE plus Sheetveil UTC vs plant UTC+2 skip the zero by 120 min, so Soren Pike is not last-to-badge-guilty. Ordered: isolate this dummy coupon; do not refer the tech; Sheetveil is not SoT. Scope: this MODIFY does not dump the CIGS line (that is a different gate) and does not restart until the 24 min new-head floor.",
            "threshold": "Rs_ohm>=8.00 AND fpp_snr>=12.0 => isolate coupon; Sheetveil is not SoT; person-referral is not an isolate",
            "stated_residuals": "24 min new-head floor still required; 16.00 vs a true 80.00 dump is a production cut; Sheetveil remains the only OEM 4PP channel",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 2640: C-2 isolated; Soren not referred; Sheetveil not SoT",
            "tool": "sc5-fpp-coupon-gate-cli",
            "observation": "Rs 16.00 ohm/sq recomputes from V 8.00 mV / I 2.00 mA; dummy coupon locked; probe-zero AE absent on the isolate frame",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1560.0, "event": "FPP V 8.00 mV; raster frame; Rs 16.00 ohm/sq"},
                {"t_s": 2460.0, "event": "ops proposes keep-coupon plus refer Soren"},
                {"t_s": 2640.0, "event": "MODIFY isolate coupon; referral refused"},
                {"t_s": 2820.0, "event": "24 min new-head bookend 1"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4620.0, "event": "companion ACCEPT new-head restart"},
            ],
            "observed_effects": [
                "remaining Rs recomputes from the serialized four-point-probe model at every recon.Rs event",
                "a Sheetveil-only head would have kept C-2 and named Soren",
                "24 min new-head floor is in the stream (cpn.lock, prb.floor)",
            ],
            "surprises": [
                "timezone-skipped probe-zero AE, not last-to-badge, was the only missing plant witness",
            ],
            "new_state": {
                "c2": "isolated",
                "soren": "exonerated",
                "sheetveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 1080000.0,
        },
        "reward_components": reward(
            0.40,
            [
                ("fpp_rs_reconstruction", 0.14),
                ("conjunctive_isolate_floor", 0.12),
                ("sheetveil_nonsubstitution", 0.08),
                ("tech_exoneration", 0.08),
                ("isolate_time_cost", -0.02),
            ],
            "scored for an isolate MODIFY on a recomputable four-point-probe Rs slip while refusing a Sheetveil last-good and a last-to-badge referral; 24 min floor is priced as downtime",
        ),
        "meta": meta_common(
            tags=["MODIFY", "four-point-probe-rs", "serialized-reconstruction", "operational-companion", "exoneration"],
            distillation_value="Independent LIF raster plus serialized k_s*V/I remaining-Rs reconstruction; race is the 1.2 ms V/SNR pair; refractory and adaptation are in the CUBA excerpt.",
            distillation_note="4PP-Rs gate: serialized k_s*V/I plus SNR lock beats a vendor last-good and a person-referral; companion t2 is the new-head restart",
        ),
    }
    traj2 = {
        "id": "nelb-r64-002-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "SC-FPP-2026-0902-exec",
            "domain": "new_head_fpp_rs_restart_execution",
            "setting": "Same 4PP-HIL-4 dummy after the isolate. Operator proposes a new-head restart of C-2. This companion is the operational restart, not a second Rs vote.",
            "observables_at_decision": {
                "Rs_ohm": 20.00,
                "prb_floor_s": 1440.0,
                "prb_new": True,
                "soren_fault": False,
            },
            "margin_authority": "SC-5 execution SOP: new-head restart after the 24 min floor; keep-running remains refused.",
        },
        "proposed_action": {
            "actor": "night lead Della Marsh",
            "summary": "restart dummy coupon C-2 on a new four-point head now that the 24 min floor is paid",
            "basis_claimed": "the isolate already stopped C-2; a new head is the cheapest return",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "New-head restart of the dummy coupon after the 24 min floor. Keep-running stays refused. Soren remains exonerated. Sheetveil is still not SoT. ACCEPT the new-head restart of C-2 only. Do not restore the CIGS line. Do not treat Sheetveil 2.20 ohm/sq as a clear.",
            "threshold": "prb_floor_complete AND coupon_isolated AND keep_running_refused AND sheetveil_not_sot",
            "stated_residuals": "dummy still reads 20.00 ohm/sq until the new head takes; line stays out of scope",
        },
        "executed_action": {
            "summary": "new head accepted at t_s 4620; keep-running not restored; Soren not blamed",
            "tool": "sc5-prb-exec",
            "observation": "probe-zero AE present on the new head; dummy still isolated from the line",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2820.0, "event": "new-head clock started after isolate"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4440.0, "event": "new-head restart proposed"},
                {"t_s": 4620.0, "event": "ACCEPT new-head restart"},
            ],
            "observed_effects": [
                "Sheetveil restore did not reopen the Rs call",
                "Soren was not last-to-badge; new-head AE is present",
            ],
            "surprises": ["post-isolate dummy climbed to 20.00 ohm/sq while Sheetveil still read 2.20"],
            "new_state": {"coupon": "new-head restart", "line": "in service", "soren": "exonerated"},
            "latency_ms": 1440000.0,
        },
        "reward_components": reward(
            0.35,
            [
                ("new_head_restart", 0.12),
                ("keep_running_refused", 0.10),
                ("sheetveil_nonsubstitution", 0.08),
                ("tech_exoneration", 0.06),
                ("held_coupon_cost", -0.01),
            ],
            "operational execution gate: new-head restart because Sheetveil is not a restore license; not an Rs re-vote",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "new-head"]),
    }
    return {
        "id": "nelb-r64-002",
        "snn_tags": list(SNN_TAGS),
        "spike_events": events,
        "language_view": {
            "description": "Siltcrag CIGS SC-5 HIL dummy. Plant-owned collinear four-point probe reconstructs 16.00 ohm/sq from 4.00*8.00/2.00 while Sheetveil still reports 2.40. The gate MODIFYs keep-coupon into an isolate and refuses a last-to-badge referral of Soren Pike. A 24 min new-head floor is serialized. Companion t2 ACCEPTs the new-head restart.",
            "trajectory": traj,
            "trajectory_new_head_restart": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "fpp.V / fpp.snr / fpp.I": "four-point voltage, SNR, and force current; the physics channels the reconstruction consumes",
                "recon.Rs / recon.Gs / recon.ratio": "serialized remaining-Rs, sheet-conductance identity, and V/I identity",
                "prb.zero / sheetveil.Rs / soren.badge": "probe-zero AE, vendor 4PP cloud, tech-fault denial",
                "ops.prop / gate.isol / ops.restart / gate.restart": "keep-coupon proposal, MODIFY isolate, new-head proposal, companion ACCEPT",
                "cpn.lock / prb.floor / prb.new / cpn.held / keep.run": "operational companion channels plus the 24 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-over: sheetveil.Rs 2.40 next to recon.Rs 16.00",
                "reconstruction as event: recon.Rs 16.00 equals 4.00*8.00/2.00",
                "MODIFY then operational ACCEPT: gate.isol at 2640 s, gate.restart at 4620 s",
                "slow floor in-stream: cpn.lock 2820 s, prb.floor 4260 s (24.0 min)",
                "tight FPP pair: fpp.V then fpp.snr +1.2 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Sheetveil is 2.40 ohm/sq' = sheetveil.Rs 2.40; '16 ohm/sq remaining Rs' = recon.Rs 16.00; 'isolate coupon' = gate.isol MODIFY; 'new-head restart' = gate.restart ACCEPT",
            "why_high_value": "New collinear four-point-probe remaining-Rs family on a CIGS HIL dummy (not SFRA, not FDS, not MCSA, not leftover-mill katharometer). Lead MODIFY isolate on a recomputable Rs slip plus timezone-exoneration of the probe tech. Independent CUBA LIF raster. Companion t2 is operational new-head restart. sim_or_real=hil.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 2026096402, "stream_note": "stream amplitudes are authored constants; raster is independent CUBA LIF"},
                "draw_order": "independent CUBA LIF per neuron; gap-constrained times; per-spike adaptation and noise",
                "thinning": "4PP exists at ~10 Hz; stream keeps 5 V points; recon keeps 5 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "fpp.V": 1.2,
                    "fpp.snr": 1.2,
                    "fpp.I": 60000,
                    "recon.Rs": 60000,
                    "recon.Gs": 60000,
                    "recon.ratio": 60000,
                    "prb.zero": 60000,
                    "sheetveil.Rs": 60000,
                    "soren.badge": 60000,
                    "ops.prop": 60000,
                    "gate.isol": 60000,
                    "ops.restart": 60000,
                    "gate.restart": 60000,
                    "cpn.lock": 60000,
                    "prb.floor": 60000,
                    "prb.new": 60000,
                    "cpn.held": 60000,
                    "keep.run": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-09-02T02:00:00Z HIL coupon start",
            },
            "distillation_targets": [
                "four-point-probe reconstruction head: Rs = k_s * V / I; Gs = 64 / Rs; V/I identity",
                "conjunctive isolate floor vs keep-coupon vs line dump",
                "vendor-4PP nonsubstitution plus timezone exoneration",
                "operational companion: new-head restart without restoring on Sheetveil",
                "independent CUBA LIF raster with race/refractory/adaptation tags",
            ],
        },
        "reconstruction_model": {
            "name": "collinear_four_point_probe_rs",
            "formula": "Rs_ohm = k_s * V_mv / I_ma; V_I = V_mv / I_ma; Gs_mS = 64.00 / Rs_ohm",
            "parameters": {
                "k_s": 4.00,
                "I_ma": 2.00,
                "isolate_floor_ohm": 8.00,
                "dump_ohm": 80.00,
                "snr_lock": 12.0,
                "src_min": 24.0,
            },
            "worked_example": {"V_mv": 8.00, "I_ma": 2.00, "Rs_ohm": 16.00, "Gs_mS": 4.00, "V_I": 4.00},
            "check": "4.00 * 8.00 / 2.00 = 16.00 exactly; 8.00 / 2.00 = 4.00 exactly; 64.00 / 16.00 = 4.00 exactly; 2820 s + 1440 s = 4260 s = 24.0 min floor",
        },
        "raster": raster,
        "gate_snn": matching_gate_snn(
            decision="MODIFY",
            window_ms=32.0,
            code="sc5.fpp_coupon_gate",
            note="MODIFY accumulator wins: plant four-point-probe Rs evidence overpowers the Sheetveil keep advocate",
            decode_rule="isolate if rs_estimator AND probe_norm fire; vendor_continue_advocate is below threshold by design",
            populations=[
                gate_pop("rs_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("probe_norm", 50, 1.2, 50.0, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("modify_latch", 80, 1.6, 62.5, w_s),
            ],
            race_ms=1.2,
        ),
        "gate_compute": gate_compute(
            [
                {"check": "sc5.fpp_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 32.0},
                {"check": "sc5.prb_scorer", "neurons": 50, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r64-002",
            clock_domain="sc5-fpp-hil-relative-ms-t0-2026-09-02T02:00:00Z",
            tags=["four-point-probe-rs", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2", "independent-lif", "exoneration"],
            distillation_value="Independent LIF raster teaches race/refractory/adaptation while the language view teaches four-point-probe remaining-Rs reconstruction-as-SoT plus timezone exoneration.",
        ),
    }


# ---------------------------------------------------------------------------
# nelb-r64-003 — streaming-current remaining SCD of a clarifier inlet
# ---------------------------------------------------------------------------
def rec_003():
    k_c = 4.00
    i_na = 8.00
    i0 = 2.00
    scd = k_c * (i_na - i0)
    _exact(scd, 24.00)
    _exact(k_c * (4.00 - 2.00), 8.00)
    _exact(k_c * (6.00 - 2.00), 16.00)
    _exact(k_c * (10.00 - 2.00), 32.00)
    di = i_na - i0
    _exact(di, 6.00)
    ratio = di / i0
    _exact(ratio, 3.00)
    dose = 0.50 * scd
    _exact(dose, 12.00)
    _exact(6000.0 + 720.0, 6720.0)

    raster = make_lif_raster(
        neurons=16,
        mean_rate_hz=62.5,
        window_ms=36.0,
        seed=2026096403,
        source="bg6.scd.charge",
        target="brinegait.basin_accept_core",
        table=[
            {"from": "scd_I", "to": "scd_estimator", "weight": 1.30},
            {"from": "scd_snr", "to": "scd_lock_core", "weight": 1.10},
            {"from": "streamveil_scd", "to": "vendor_dump_advocate", "weight": 0.42},
        ],
        third_factor={
            "modulator": "na.scd_basin_scope_eligibility",
            "tau_e_s": 2.0,
            "tau_e_ms": 2000.0,
            "eligibility": "pre-post coincidence on plant-dump synapses; the plant streaming-current modulator depresses dump-all links when probe current stays high inside tau_e of an SNR lock so a Streamveil last-good cannot hide a 24.00 mV remaining-SCD slip on B-4 or expand the isolate past B-4",
        },
        channel_prefix="scd.n",
        anchor="BG-6 SCD-SIM-5 36 ms frame at I 8.00 nA / SNR 11.0 (t_s 3000) reconstructing 24.00 mV over the 12.00 isolate floor, B-4 only",
        tau_m_ms=8.0,
    )
    w_s = 0.036
    events = [
        ev(0.0, "scd.I", 4.00, code="I_NA", units="nA", note="simulated streaming-current detector of Brinegait Water BG-6 basin B-4; remaining-SCD family, not nephelometric NTU, not cation conductivity, not four-electrode conductivity, not UV photometric ozone, not molybdenum-blue phosphate, not leftover-mill Clark DO"),
        ev(180000.0, "scd.snr", 7.0, code="SCD_SNR", units="1", note="early SNR under the 8.0 lock floor"),
        ev(360000.0, "recon.SCD", 8.00, code="SCD_MV", units="mV", note="4.00*(4.00-2.00)=8.00 exact; still under the 12.00 isolate floor"),
        ev(540000.0, "basin.T", 289.0, code="BASIN_K", units="K", note="plant basin thermocouple on the simulated coupon; independent of Streamveil"),
        ev(720000.0, "streamveil.SCD", 4.80, code="VENDOR_MV", units="mV", note="Streamveil last-good SCD cloud; healthy-looking 4.80 mV; not admissible SoT"),
        ev(900000.0, "scd.I", 6.00, code="I_NA", units="nA"),
        ev(1080000.0, "recon.SCD", 16.00, code="SCD_MV", units="mV", note="4.00*(6.00-2.00)=16.00; over the 12.00 isolate floor"),
        ev(1260000.0, "b1.SCD", 4.00, code="SCD_MV", units="mV", note="adjacent basin B-1 stays healthy; out of scope for this ACCEPT"),
        ev(1440000.0, "b2.SCD", 3.60, code="SCD_MV", units="mV", note="B-2 out of scope"),
        ev(1620000.0, "b3.SCD", 4.40, code="SCD_MV", units="mV", note="B-3 out of scope"),
        ev(1800000.0, "scd.I", 7.00, code="I_NA", units="nA"),
        ev(1980000.0, "recon.SCD", 20.00, code="SCD_MV", units="mV", note="4.00*(7.00-2.00)=20.00; under dump 80.00"),
        ev(2160000.0, "recon.dose", 10.00, code="DOSE_MGL", units="mg_L", note="0.50*20.00=10.00"),
        ev(2340000.0, "streamveil.SCD", 4.80, code="VENDOR_MV", units="mV"),
        ev(2520000.0, "scd.snr", 9.0, code="SCD_SNR", units="1"),
        ev(2700000.0, "recon.ratio", 2.50, code="DI_RATIO", units="1", note="(7.00-2.00)/2.00=2.50"),
        ev(3000000.0, "scd.I", 8.00, code="I_NA", units="nA", note="isolate-floor frame; raster sidecar"),
        ev(3000001.5, "scd.snr", 11.0, code="SCD_SNR", units="1", note="1.5 ms SCD lock after I; 11.0 >= 8.0"),
        ev(3180000.0, "recon.SCD", 24.00, code="SCD_MV", units="mV", note="4.00*(8.00-2.00)=24.00 exact; isolate 12.00, plant-dump 80.00"),
        ev(3360000.0, "recon.dose", 12.00, code="DOSE_MGL", units="mg_L", note="0.50*24.00=12.00 exact dose identity"),
        ev(3540000.0, "recon.ratio", 3.00, code="DI_RATIO", units="1", note="(8.00-2.00)/2.00=3.00 exact"),
        ev(3720000.0, "streamveil.SCD", 4.70, code="VENDOR_MV", units="mV"),
        ev(3900000.0, "b1.SCD", 4.00, code="SCD_MV", units="mV"),
        ev(4080000.0, "b2.SCD", 3.60, code="SCD_MV", units="mV"),
        ev(4260000.0, "b3.SCD", 4.40, code="SCD_MV", units="mV"),
        ev(4440000.0, "basin.T", 290.0, code="BASIN_K", units="K"),
        ev(4620000.0, "ops.prop", 1.0, code="ISOLATE_B4", units="bool", note="sim operator Cora Flint: isolate B-4 only; B-1..B-3 stay in service"),
        ev(4800000.0, "gate.acc", 1.0, code="ACCEPT", units="decision", note="bounded ACCEPT of B-4 isolate; plant dump refused; Streamveil not SoT"),
        ev(4980000.0, "b4.lock", 1.0, code="B4_ISOL", units="bool"),
        ev(6000000.0, "surv.start", 1.0, code="SURV_START", units="bool", note="bookend 1 of the 12.0 min survey floor"),
        ev(6720000.0, "surv.floor", 1.0, code="SURV_FLOOR", units="bool", note="6000 s + 720 s = 6720 s = 12.0 min"),
        ev(7200000.0, "ops.skip", 1.0, code="SKIP_SURVEY", units="bool", note="Flint: skip the remaining-basin survey; Streamveil still 4.70 mV"),
        ev(7800000.0, "gate.surv", 1.0, code="REJECT", units="decision", note="companion t2: REJECT skip-survey; B-1..B-3 stay in the survey takt"),
        ev(8400000.0, "surv.held", 1.0, code="SURV_HELD", units="bool"),
        ev(9000000.0, "scd.I", 10.00, code="I_NA", units="nA"),
        ev(9600000.0, "recon.SCD", 32.00, code="SCD_MV", units="mV", note="4.00*(10.00-2.00)=32.00 post-isolate on B-4; still under dump 80.00"),
        ev(10200000.0, "streamveil.SCD", 4.60, code="VENDOR_MV", units="mV"),
        ev(10800000.0, "b1.SCD", 3.90, code="SCD_MV", units="mV"),
        ev(11400000.0, "b2.SCD", 3.50, code="SCD_MV", units="mV"),
        ev(12000000.0, "b3.SCD", 4.30, code="SCD_MV", units="mV"),
        ev(12600000.0, "plant.dump", 0.0, code="DUMP_NOT_TAKEN", units="bool"),
        ev(13200000.0, "surv.held", 1.0, code="SURV_HELD", units="bool"),
        ev(13800000.0, "recon.dose", 16.00, code="DOSE_MGL", units="mg_L", note="0.50*32.00=16.00"),
        ev(14400000.0, "basin.T", 291.0, code="BASIN_K", units="K"),
        ev(15000000.0, "b4.lock", 1.0, code="B4_ISOL", units="bool"),
        ev(15600000.0, "ops.skip", 1.0, code="SKIP_SURVEY", units="bool"),
        ev(16200000.0, "gate.surv", 1.0, code="REJECT", units="decision"),
        ev(16800000.0, "surv.floor", 1.0, code="SURV_FLOOR", units="bool"),
    ]
    assert_stream(events)
    if len(events) != 48:
        raise RuntimeError(len(events))

    traj = {
        "id": "nelb-r64-003-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "BG-SCD-2026-0902",
            "domain": "streaming_current_scd_clarifier_basin",
            "setting": "Brinegait Water BG-6 (invented), simulated coupon SCD-SIM-5, basin B-4. Plant-owned streaming-current detector is the remaining-SCD SoT. Streamveil vendor SCD-cloud is not SoT. Simulated campaign; not a live plant. Not leftover-mill nephelometric NTU, not cation conductivity, not four-electrode conductivity, not UV photometric ozone, not molybdenum-blue phosphate, not leftover-mill Clark polarographic DO, not venturi, not katharometer.",
            "observables_at_decision": {
                "I_nA": i_na,
                "I0_nA": i0,
                "k_c": k_c,
                "SCD_mV": scd,
                "dose_mgL": dose,
                "di_ratio": ratio,
                "scd_snr": 11.0,
                "streamveil_mV": 4.80,
                "b1_mV": 4.00,
                "b2_mV": 3.60,
                "b3_mV": 4.40,
                "isolate_floor_mV": 12.00,
            },
            "margin_authority": "BG-6 basin SOP rev D: if reconstructed SCD_mV >= 12.00 AND SCD SNR >= 8.0, B-4 isolate is required even if Streamveil reports 4.80 mV. Plant dump is a different gate (SCD_mV >= 80.00). B-1..B-3 are out of scope unless their own reconstructions cross 12.00.",
        },
        "proposed_action": {
            "actor": "sim operator Cora Flint, citing plant SCD 24.00 mV on B-4 and healthy B-1..B-3",
            "summary": "isolate basin B-4 only; keep B-1..B-3 in service; do not dump the clarifier plant",
            "basis_claimed": "only B-4 reconstructed over 12.00 mV; Streamveil 4.80 mV is not SoT but also does not license a plant dump",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Bounded ACCEPT of B-4 isolate. Serialized reconstruction: SCD_mV = k_c * (I - I0) = 4.00 * (8.00 - 2.00) = 24.00, which is 12.00 mV over the 12.00 isolate floor and 56.00 mV under the 80.00 plant-dump tripwire, and SCD SNR is 11.0 >= 8.0. Dose identity dose = 0.50 * SCD = 0.50 * 24.00 = 12.00 mg/L; dI/I0 identity = (8.00 - 2.00) / 2.00 = 3.00. B-1/B-2/B-3 reconstruct 4.00/3.60/4.40 mV, all under 12.00, so they stay out of scope. Streamveil 4.80 mV is a last-good denial, not a dump license and not a clear. Ordered: isolate B-4 only. Scope: this ACCEPT does not dump the plant, does not isolate B-1..B-3, and does not skip the 12 min remaining-basin survey (that is the companion question).",
            "threshold": "SCD_mV>=12.00 AND scd_snr>=8.0 => isolate that basin only; Streamveil is not SoT; dump if SCD_mV>=80.00; B-1..B-3 out of scope while SCD_mV<12.00",
            "stated_residuals": "12 min survey still required; 24.00 vs a true 80.00 dump is a production cut; Streamveil remains the only OEM SCD channel",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 4800: B-4 isolated; B-1..B-3 left in service; Streamveil not SoT",
            "tool": "bg6-scd-basin-gate-cli",
            "observation": "SCD 24.00 mV recomputes from I 8.00 nA minus I0 2.00 nA; B-4 hashed; adjacent basins remain under 12.00 mV",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "SCD I 8.00 nA; raster frame; SCD 24.00 mV"},
                {"t_s": 4620.0, "event": "ops proposes B-4 isolate"},
                {"t_s": 4800.0, "event": "ACCEPT B-4 isolate; plant dump refused"},
                {"t_s": 6000.0, "event": "12 min survey bookend 1"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7800.0, "event": "companion REJECT skip-survey"},
            ],
            "observed_effects": [
                "remaining SCD recomputes from the serialized streaming-current model at every recon.SCD event",
                "a Streamveil-only head would have left B-4 in service overnight",
                "12 min survey floor is in the stream (surv.start, surv.floor)",
            ],
            "surprises": [
                "a clean vendor 4.80 mV corridor co-existed with a 24.00 mV plant reconstruction on one basin only",
            ],
            "new_state": {
                "b4": "isolated",
                "b1_b3": "in service",
                "streamveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("scd_reconstruction", 0.14),
                ("bounded_b4_scope", 0.12),
                ("streamveil_nonsubstitution", 0.08),
                ("no_plant_dump", 0.08),
                ("survey_time_cost", -0.01),
            ],
            "scored for a bounded ACCEPT of B-4 isolate on a recomputable streaming-current slip while refusing a Streamveil last-good and a plant dump; 12 min survey is priced as takt not as a reason to skip",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "streaming-current-scd", "serialized-reconstruction", "operational-companion", "bounded-scope"],
            distillation_value="Independent LIF raster plus serialized k_c*(I-I0) remaining-SCD reconstruction; race is the 1.5 ms I/SNR pair; refractory and adaptation are in the CUBA excerpt.",
            distillation_note="SCD gate: serialized k_c*(I-I0) plus SNR lock beats a vendor last-good; companion t2 is the survey hold, not a dump vote",
        ),
    }
    traj2 = {
        "id": "nelb-r64-003-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "BG-SCD-2026-0902-exec",
            "domain": "survey_hold_scd_execution",
            "setting": "Same SCD-SIM-5 after the bounded ACCEPT. Operator proposes skip-survey of B-1..B-3. This companion is the operational survey-hold, not a second SCD vote.",
            "observables_at_decision": {
                "SCD_mV": 32.00,
                "surv_floor_s": 720.0,
                "skip_proposed": True,
                "b1_mV": 3.90,
            },
            "margin_authority": "BG-6 execution SOP: remaining-basin survey after B-4 isolate; skip-survey is refused while Streamveil is not SoT.",
        },
        "proposed_action": {
            "actor": "sim operator Cora Flint",
            "summary": "skip the remaining-basin survey; Streamveil still reads 4.60 mV and B-4 is already isolated",
            "basis_claimed": "the ACCEPT already stopped B-4; a survey is wasted takt",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Skip-survey is refused. The 12 min survey floor is complete and B-1..B-3 remain in the survey takt even though they are out of isolate scope. Streamveil is still not SoT. Do not dump the plant. Do not restore B-4 on Streamveil 4.60 mV.",
            "threshold": "surv_floor_complete AND skip_survey_refused AND plant_dump_not_taken AND streamveil_not_sot",
            "stated_residuals": "B-4 stays isolated; B-1..B-3 stay in the survey; Streamveil still the only OEM SCD channel",
        },
        "executed_action": {
            "summary": "skip-survey REJECT at t_s 7800; plant dump not latched; Streamveil restore not taken",
            "tool": "bg6-surv-exec",
            "observation": "recon.SCD 32.00 mV after isolate; survey line-up complete; Streamveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "survey clock started after ACCEPT"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7200.0, "event": "skip-survey proposed"},
                {"t_s": 7800.0, "event": "REJECT skip-survey; plant dump refused"},
            ],
            "observed_effects": [
                "Streamveil restore did not reopen the SCD call",
                "plant dump never fired; B-1..B-3 stayed in the survey takt",
            ],
            "surprises": ["post-isolate SCD climbed to 32.00 mV while Streamveil still read 4.60"],
            "new_state": {"survey": "held", "plant": "in service", "b4": "isolated"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.36,
            [
                ("survey_hold", 0.12),
                ("no_plant_dump", 0.10),
                ("streamveil_nonsubstitution", 0.08),
                ("surv_floor_complete", 0.08),
                ("held_takt_cost", -0.02),
            ],
            "operational execution gate: survey-hold because Streamveil is not a skip license; not an SCD re-vote",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "survey-hold"]),
    }
    return {
        "id": "nelb-r64-003",
        "snn_tags": list(SNN_TAGS),
        "spike_events": events,
        "language_view": {
            "description": "Brinegait Water BG-6. Plant-owned streaming-current detector reconstructs 24.00 mV from 4.00*(8.00-2.00) while Streamveil still reports 4.80 mV. The gate ACCEPTs a bounded B-4 isolate. A 12 min survey floor is serialized. Companion t2 REJECTs skip-survey.",
            "trajectory": traj,
            "trajectory_survey_hold": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "scd.I / scd.snr": "streaming current and SNR; the physics channels the reconstruction consumes",
                "recon.SCD / recon.dose / recon.ratio": "serialized remaining-SCD mV, dose identity, and dI/I0 identity",
                "basin.T / streamveil.SCD / b1.SCD / b2.SCD / b3.SCD": "basin thermocouple, vendor SCD cloud, adjacent-basin out-of-scope witnesses",
                "ops.prop / gate.acc / ops.skip / gate.surv": "B-4 isolate proposal, ACCEPT, skip-survey proposal, companion REJECT",
                "b4.lock / surv.start / surv.floor / surv.held / plant.dump": "operational companion channels plus the 12 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-over: streamveil.SCD 4.80 next to recon.SCD 24.00",
                "reconstruction as event: recon.SCD 24.00 equals 4.00*(8.00-2.00)",
                "ACCEPT then operational REJECT: gate.acc at 4800 s, gate.surv at 7800 s",
                "slow floor in-stream: surv.start 6000 s, surv.floor 6720 s (12.0 min)",
                "tight SCD pair: scd.I then scd.snr +1.5 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Streamveil is 4.80 mV' = streamveil.SCD 4.80; '24 mV remaining SCD' = recon.SCD 24.00; 'isolate B-4' = gate.acc ACCEPT; 'do not skip survey' = gate.surv REJECT",
            "why_high_value": "New streaming-current remaining-SCD family on a clarifier basin (not nephelometric NTU, not cation conductivity, not leftover-mill Clark DO / venturi / katharometer). Lead bounded ACCEPT of B-4 isolate on a recomputable SCD slip. Independent CUBA LIF raster. Companion t2 is operational survey-hold. sim_or_real=simulated.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 2026096403, "stream_note": "stream amplitudes are authored constants; raster is independent CUBA LIF"},
                "draw_order": "independent CUBA LIF per neuron; gap-constrained times; per-spike adaptation and noise",
                "thinning": "SCD probe exists at ~1 Hz; stream keeps 5 I points; recon keeps 5 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "scd.I": 1.5,
                    "scd.snr": 1.5,
                    "recon.SCD": 60000,
                    "recon.dose": 60000,
                    "recon.ratio": 60000,
                    "basin.T": 60000,
                    "streamveil.SCD": 60000,
                    "b1.SCD": 60000,
                    "b2.SCD": 60000,
                    "b3.SCD": 60000,
                    "ops.prop": 60000,
                    "gate.acc": 60000,
                    "ops.skip": 60000,
                    "gate.surv": 60000,
                    "b4.lock": 60000,
                    "surv.start": 60000,
                    "surv.floor": 60000,
                    "surv.held": 60000,
                    "plant.dump": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-09-02T03:00:00Z simulated coupon start",
            },
            "distillation_targets": [
                "streaming-current reconstruction head: SCD = k_c * (I - I0); dose = 0.50 * SCD; dI/I0 identity",
                "bounded ACCEPT of B-4 vs plant dump vs skip-survey",
                "vendor-SCD nonsubstitution plus adjacent-basin out-of-scope",
                "operational companion: survey-hold without restoring on Streamveil",
                "independent CUBA LIF raster with race/refractory/adaptation tags",
            ],
        },
        "reconstruction_model": {
            "name": "streaming_current_scd_clarifier",
            "formula": "SCD_mV = k_c * (I_nA - I0_nA); dose_mgL = 0.50 * SCD_mV; di_ratio = (I_nA - I0_nA) / I0_nA",
            "parameters": {
                "k_c": 4.00,
                "I0_nA": 2.00,
                "isolate_floor_mV": 12.00,
                "dump_mV": 80.00,
                "snr_lock": 8.0,
                "surv_min": 12.0,
            },
            "worked_example": {"I_nA": 8.00, "I0_nA": 2.00, "SCD_mV": 24.00, "dose_mgL": 12.00, "di_ratio": 3.00},
            "check": "4.00 * (8.00 - 2.00) = 24.00 exactly; 0.50 * 24.00 = 12.00 exactly; (8.00 - 2.00) / 2.00 = 3.00 exactly; 6000 s + 720 s = 6720 s = 12.0 min floor",
        },
        "raster": raster,
        "gate_snn": matching_gate_snn(
            decision="ACCEPT",
            window_ms=36.0,
            code="bg6.scd_basin_gate",
            note="ACCEPT accumulator wins: plant streaming-current evidence isolates B-4 without a plant dump",
            decode_rule="accept-B4-isolate if scd_estimator AND scd_lock fire; vendor_dump_advocate is below threshold by design",
            populations=[
                gate_pop("scd_estimator", 80, 1.4, 50.0, w_s),
                gate_pop("scd_lock", 50, 1.1, 50.0, w_s),
                gate_pop("vendor_dump_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("accept_latch", 64, 1.5, 62.5, w_s),
            ],
            race_ms=1.5,
        ),
        "gate_compute": gate_compute(
            [
                {"check": "bg6.scd_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 36.0},
                {"check": "bg6.surv_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 40.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r64-003",
            clock_domain="bg6-scd-sim-relative-ms-t0-2026-09-02T03:00:00Z",
            tags=["streaming-current-scd", "ACCEPT", "REJECT", "serialized-reconstruction", "operational-t2", "independent-lif", "bounded-scope"],
            distillation_value="Independent LIF raster teaches race/refractory/adaptation while the language view teaches streaming-current remaining-SCD reconstruction-as-SoT with a bounded ACCEPT.",
        ),
    }


def walk_banned(obj, path=""):
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}.{k}" if path else k
            nk = str(k).casefold().replace("-", "_").replace(" ", "_")
            if nk in HIDDEN or nk in {"thought", "scratch", "inner_monologue", "chain_of_thought", "real"}:
                hits.append(p)
            hits.extend(walk_banned(v, p))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits.extend(walk_banned(v, f"{path}[{i}]"))
    return hits


def local_checks(records):
    ids = []
    gate_match = 0
    for rec in records:
        hits = walk_banned(rec)
        if hits:
            raise RuntimeError(f"banned keys {hits}")
        blob = json.dumps(rec)
        if '"real"' in blob:
            raise RuntimeError("real leaked")
        if "thought" in rec:
            raise RuntimeError("thought leaked")
        if rec["meta"]["round"] != 64:
            raise RuntimeError("meta.round")
        if rec["meta"].get("snn_tags") != SNN_TAGS:
            raise RuntimeError("snn_tags")
        if rec.get("snn_tags") != SNN_TAGS:
            raise RuntimeError("top snn_tags")
        if rec["meta"].get("nelb", {}).get("snn_tags") != SNN_TAGS:
            raise RuntimeError("nelb.snn_tags")
        ids.append(rec["id"])
        lv = rec["language_view"]
        ids.append(lv["trajectory"]["id"])
        for k, v in lv.items():
            if k.startswith("trajectory") and isinstance(v, dict) and "id" in v:
                if v is not lv["trajectory"]:
                    ids.append(v["id"])
                sim = v["state"]["sim_or_real"]
                if sim not in {"designed", "simulated", "hil"}:
                    raise RuntimeError(sim)
                if v["meta"]["round"] != 64:
                    raise RuntimeError("traj round")
                if v["meta"].get("snn_tags") != SNN_TAGS:
                    raise RuntimeError("traj snn_tags")
        n = len(rec["spike_events"])
        if n < 48:
            raise RuntimeError(f"{rec['id']} events {n}")
        gdec = rec["gate_snn"]["decision"]
        tdec = lv["trajectory"]["safety_decision"]["decision"]
        if gdec != tdec:
            raise RuntimeError(f"gate {gdec} != traj {tdec}")
        if rec["gate_snn"].get("snn_tags") == SNN_TAGS:
            gate_match += 1
        rast = rec["raster"]
        exp = int(round(rast["neurons"] * rast["mean_rate_hz"] * rast["window_s"]))
        if abs(rast["spikes"] - exp) > 0:
            raise RuntimeError("raster budget")
        if abs(rast["energy_pJ"] - rast["spikes"] * 23) > 1e-6:
            raise RuntimeError("energy pJ")
        if abs(rast["energy_uJ"] - rast["spikes"] * 23e-6) > 1e-9:
            raise RuntimeError("energy uJ")
        if not (20 <= rast["window_ms"] <= 50):
            raise RuntimeError("window")
        if rast["excerpt_span_us"] < 1000:
            raise RuntimeError("excerpt span")
        if rast["isi_source"] != "full_window_per_neuron_isi":
            raise RuntimeError("isi source")
        tf = rast["routing"]["third_factor"]
        if abs(tf["tau_e_ms"] / 1000.0 - tf["tau_e_s"]) > 1e-9:
            raise RuntimeError("tau_e")
        if rast["lif"]["model"] != "independent_cuba_lif":
            raise RuntimeError("lif")
        ex = {e["t_us"] for e in rast["excerpt"]}
        raw_ms = {int(round(e["t_rel_ms"])) for e in rec["spike_events"]}
        if ex & raw_ms:
            raise RuntimeError("excerpt echoes stream")
        if "training_ready" in blob:
            raise RuntimeError("training_ready claimed")
        if "2026-08-17" in blob or "2026-08-30" in blob:
            raise RuntimeError("forbidden run date")
        low = blob.casefold()
        if "venturi" in low or "katharometer" in low or "clark polarographic" in low:
            raise RuntimeError("restaged leftover-mill r64 family")
    if gate_match < 1:
        raise RuntimeError("no gate_snn matching snn_tags")
    if len(ids) != len(set(ids)):
        raise RuntimeError(f"dup ids {ids}")
    print("local_checks ok", [r["id"] for r in records], "ids", len(ids), "gate_snn_tag_match", gate_match)


NOTES = """# Neuromorphic Event + Language Bridge — NOTES round 64
Run: 2026-09-02-final-heavy · Factory: neuromorphic-event-language-bridge · Generator: grok-4.6 · Output: `batch-r64.jsonl` (3 paired artifacts, 6 ThalamicTrajectories)
Rights: RM-793 research-only (SpaceXAI/xAI grok-4.6, SuperGrok Heavy chat). Not training_ready. Written create-only to `/home/raulmc/rmems/synthetic-factory/outputs/raw/2026-09-02-final-heavy/neuromorphic-event-language-bridge/` (`batch-r64.jsonl` was absent). Does not clobber leftover-mill `/tmp/nelb-r64/` (venturi / katharometer / Clark, ids `193`–`195`). IDs `nelb-r64-001`…`003` as assigned.

## Context / de-duplication
Live tree already held r01 (Johnson-noise T / Coulter / photoelastic), r02 (CAPS NO2 / PTR-MS MDI / microwave PCD), r21 (OA-ICOS CH4 / SERF OPM / WGM), r22 (CDG vacuum / opacity dust / polariscope), r41 (LDA / Karl Fischer / bender-element), r42 (BOS / LIF OH / ESPI), r61 (Stern-Volmer DO / pellistor / FMCW radar), r63 (ICP-OES Ni / LVDT / FTIR methanol). This round is **r64** as assigned. Banned this round: those live families; leftover-mill r64 venturi remaining-dP steam / katharometer remaining H2 / Clark polarographic remaining DO and ids `nelb-r64-193`…`195`; leftover-mill r13–r70 table (FBG, quench, VRFB, BOTDA, QCM-D, SAW, CRDS, IFOG, transmon, hyperspectral, MEMS, muon, x-ray, optogenetic, LiDAR, clamp-on, LIBS, QEPAS, LFV, Kaplan LDV, THz-TDS, ECT, TDLAS, lock-in, PAUT, EN, RUS, N-16, helium RGA, FOCT, tip-timing, acoustic pyrometry, SPR, VW viscometer, MW cavity, MFL, NMR, nucleonic, JNT, CRNS, Coriolis, CARS, XRF, Mössbauer, GB-InSAR, ellipsometry, CTA, SPND, LII, PALS, NQR, SFRA, shearography, H-permeation, FMCW lining, GPR, mud-pulse, Barkhausen, Lamb, Pockels, PEC, confocal, OCT, DCPD, impact-echo, phosphor-lifetime, vortex, GWR, He-3, Kr-85, Raman, cyclotron BPM, alanine EPR, ADCP, TOFD, laser-flash, TDR, UV-DOAS, Al2O3, load-cell, H2S, TEV, dielectric water-cut, Wobbe, nephelometric, cation conductivity, sonic-nozzle, sodium-ion, vibrating-tube, Ubbelohde, gloss, RF-admittance, UV ozone, triboelectric, molybdenum-blue, FPD sulfur, idler-belt, glass pH, NIR moisture). Plants not reused: Sedgewhin, Brinecrag, Lichenholt, Rushcrag, Copsewick, Peatspire, Mirewhin, Lacquerfen, Pitchshaw, Gorsewhin, Brindlemere, Quartzholt, Fernspire, Limeholt, Flintshaw, Brackenholt, Marlspur, Tarspire, Brackfen, Yewholt, Reedcairn, Brackenmire, Fernshaw, Rindleholt, Woadfen, Pellmire. Gritwhin / Siltcrag / Brinegait are new.

Adjacencies declared in-pair then kept physically distinct:
- **001 laser-diffraction remaining D50** is Fraunhofer volume-weighted remaining median of a cement mill classifier, not leftover-mill FBRM chord D50, not PDA Sauter D32, not live r01 Coulter zone, not TEOM, not BAM, not leftover-mill venturi dP steam.
- **002 collinear four-point-probe remaining Rs** is van-der-Pauw-adjacent sheet resistance of a CIGS HIL coupon, not SFRA, not FDS tan-delta, not MCSA, not PALS, not four-electrode conductivity, not leftover-mill katharometer H2.
- **003 streaming-current remaining SCD** is remaining coagulant-charge of a clarifier inlet, not leftover-mill nephelometric NTU, not cation conductivity, not UV photometric ozone, not molybdenum-blue phosphate, not leftover-mill Clark polarographic DO.

## Round 64 batch summary (3 pairs, 6 trajectories)

| id | modality (NEW family) | domain | decisions | headline |
|----|----------------------|--------|-----------|----------|
| nelb-r64-001 | Fraunhofer laser-diffraction remaining D50 of a cement mill classifier (k_d·θ µm, Difveil last-good denial, 18 min mill-hold floor) | Gritwhin Cement GW-8 classifier C-3 (invented): 4.00*8.00 reconstructs 32.00 µm while Difveil still reads 4.80 µm | REJECT (+0.43) / MODIFY (+0.34) | serialized `4.00*8.00=32.00`; `32.00/4.00=8.00`; `32.00*0.50=16.00`; conjunctive SOP (D50 AND SNR) forbids continue-grind; three-party collusion includes the LD-cloud infra owner; companion t2 mill-hold, mill ESD refused; sim_or_real=designed |
| nelb-r64-002 | collinear four-point-probe remaining Rs of a CIGS coupon (k_s·V/I Ω/sq, Sheetveil last-good denial, 24 min new-head floor) | Siltcrag CIGS SC-5 dummy coupon C-2 (invented, HIL in 4PP-HIL-4): 4.00*8.00/2.00 reconstructs 16.00 Ω/sq while Sheetveil still reads 2.40 Ω/sq | MODIFY (+0.40) / ACCEPT (+0.35) | serialized `4.00*8.00/2.00=16.00` and `8.00/2.00=4.00`; keep-coupon refused; probe tech Soren Pike exonerated (missing probe-zero AE, UTC vs UTC+2); companion t2 new-head restart; sim_or_real=hil |
| nelb-r64-003 | streaming-current remaining SCD of a clarifier basin (k_c·(I−I0) mV, Streamveil last-good denial, 12 min survey floor) | Brinegait Water BG-6 basin B-4 (invented, simulated SCD-SIM-5): 4.00*(8.00-2.00) reconstructs 24.00 mV while Streamveil still reads 4.80 mV | ACCEPT (+0.41) / REJECT (+0.36) | serialized `4.00*(8.00-2.00)=24.00`; `0.50*24.00=12.00`; `(8.00-2.00)/2.00=3.00`; bounded ACCEPT of B-4 only; B-1..B-3 out of scope; companion t2 REJECTS skip-survey; sim_or_real=simulated |

Decision spread: REJECT / MODIFY / MODIFY / ACCEPT / ACCEPT / REJECT — **2A/2M/2R**. All three enums used, and all three sit on **leads**. Provenance spread: designed / hil / simulated (one each; never live-plant). IDs `nelb-r64-001`…`003` plus t1/t2 suffixes. `meta.round=64`. `meta.snn_tags` = [race, refractory, adaptation] on every record. `gate_snn.snn_tags` matches those tags on all three.

## Raster sidecar
Every record carries `raster` + top-level `gate_snn` + `gate_compute` + `snn_tags`. Windows 40/32/36 ms; `window_s == window_ms/1000` exactly; `spikes == round(neurons·rate·window_s)` with zero slack (40/40/36 at 50.0/50.0/62.5 Hz over 20/25/16 neurons); `energy_pJ = spikes·23` and `energy_uJ = spikes·23e-6` exact (920/920/828 pJ). Routing source/target + 3-entry tables + `third_factor` on all three (modulators da.ld_d50_conflict / ach.fpp_probezero_skip_salience / na.scd_basin_scope_eligibility; τe 1.6/1.2/2.0 s as consistent `tau_e_s`+`tau_e_ms` pairs). **Independent CUBA LIF** excerpts (not a re-encode of `spike_events`; Jaccard overlap 0); integer `t_us`, in-window, `neuron_id`-bounded, sorted, full-window by construction, per-spike amplitude with adaptation (0.82**k) plus noise; excerpt span ≥ 1000 µs. ISI histograms from the **full window**, bins ≥1 ms, counts sum to `spikes − distinct_active_neurons`. Same-neuron gaps ≥1000 µs. `gate_snn` on all three: decisions REJECT/MODIFY/ACCEPT matching each lead trajectory and matching `snn_tags`; every rate-declaring population's budget exact against its decision window. `gate_compute.per_check` windows 32–40 ms, budgets exact. Main streams: **48/48/48 events** (48+ live-tree floor), strictly increasing `t_rel_ms` only (no `t_ms` mix), same-channel refractory ≥0.8 ms (001 LD pair at 1.4 ms, 002 FPP pair at 1.2 ms, 003 SCD pair at 1.5 ms).

## Self-critique

### Edge cases added vs still thin
- **Added:** first Fraunhofer laser-diffraction remaining-D50 family on a cement mill classifier with recomputable D50=k_d·θ (`32.00 µm`) plus angle and coarse-load identities; first collinear four-point-probe remaining-Rs family on a CIGS HIL dummy with recomputable Rs=k_s·V/I (`16.00 Ω/sq`) plus V/I and Gs identities and a resolved-innocent probe tech; first streaming-current remaining-SCD family on a clarifier basin with recomputable SCD=k_c·(I−I0) (`24.00 mV`), dose, and dI/I0 identities, plus a bounded ACCEPT whose out-of-scope clause is adjacent basins; independent CUBA LIF rasters; `snn_tags` on every record and matching `gate_snn`; 48-event streams; operational t2 on all three; provenance trio designed/hil/simulated; 18/24/12 min slow floors in-stream. Leftover-mill r64 venturi/katharometer/Clark was **not** restaged.
- **Still thin:** (i) 001's k_d is a lumped µm/mrad, not a refractive-index / obscuration table — a 0.2 RI hop that fakes 32.00 µm inside a 4.80 Difveil corridor is unwritten; (ii) 002's k_s is a lumped 4.00 rather than π/ln2, not a probe-spacing / temperature map, so a 10 K hop that fakes 16.00 Ω/sq is unwritten; (iii) 003's k_c is a lumped nA→mV factor, not a pH / conductivity table, so a pH hop that fakes 24.00 mV is unwritten; (iv) vendor-only as a *lead* REJECT on a plant with *no* independent LD/4PP/SCD remains slightly harder — 001/002 still have plant heads; (v) stream amplitudes remain authored constants (raster draws are the only seeded LIF noise).

### Realism of noise / temporal fidelity
- Strong: 001's 32.00 µm, θ 8.00, load 16.00, and 18.0 min mill-hold (`6000+1080=7080 s`) recompute from the record; 002's 16.00 Ω/sq, V/I 4.00, Gs 4.00, and 24.0 min new-head (`2820+1440=4260 s`) recompute; 003's 24.00 mV, dose 12.00, ratio 3.00, and 12.0 min survey (`6000+720=6720 s`) recompute. Independent CUBA LIF (τm 10/12/8 ms) plus adaptation (0.82**k plus 4% noise) and the 1.2–1.5 ms physics pairs give the 48-event stream a raster-scale motif without violating 0.8 ms same-channel refractory.
- **Gaps, honestly:** (i) 48 events still thins 1 Hz LD / 10 Hz 4PP / 1 Hz SCD stacks; (ii) 001's post-stop 40.00 µm is a later sample, not a closed-loop mill-hold controller; (iii) 002 HIL dummy times an in-service isolate that the stream does not independently witness on a second live coupon until the new head starts; (iv) no gate_snn input→output volley pair at raster resolution this round.

### Training value (SNN/LSM + agentic)
Distillation targets: LD D50=k_d·θ plus angle and load identities; conjunctive isolate floor vs continue-grind vs mill ESD; Difveil-infra collusion; 4PP Rs=k_s·V/I plus V/I and Gs identities; isolate-floor coupon vs keep-whole vs line dump; timezone exoneration; SCD SCD=k_c·(I−I0) and dose identities; bounded ACCEPT with B-1..B-3-out-of-scope; skip-survey refusal under survey takt. Independent LIF rasters teach race/refractory/adaptation without echoing the language-view stream. Agentic value concentrates in three patterns: reconstruction-as-SoT on a physical D50/Rs/SCD load the raw corridor cannot see, earned ACCEPT with an explicit physical out-of-scope object (basins B-1..B-3), and stop-then-hold so a REJECT does not become a mill/line/plant kill.

## What a later leftover-mill round should add (next densification target)
1. **Refractive-index / obscuration table** on a non-GW-8 classifier so a 0.2 RI hop fakes 32.00 µm inside a 4.80 Difveil corridor, closing 001's lumped-k_d gap.
2. **Probe-spacing / temperature map** on a non-SC-5 4PP so a 10 K hop fakes 16.00 Ω/sq while mean V looks healthy.
3. **pH / conductivity table** on a non-BG-6 SCD so a pH hop fakes 24.00 mV inside a 4.80 Streamveil corridor.
4. **Do not restage** leftover-mill r64 venturi / katharometer / Clark (ids `193`–`195`), live r01–r02 / r21–r22 / r41–r42 / r61 / r63 families named above, or leftover-mill r13–r70 table. Do not reuse Gritwhin GW-8, Siltcrag 4PP-HIL-4, or Brinegait SCD-SIM-5.

## Verification
`batch-r64.jsonl`: 3 lines, `json.loads`-clean (allow_nan=False). Written create-only to the live factory dir (O_EXCL). Build-time asserts: global time order; same-channel ≥0.8 ms; 48+ events (48/48/48); excerpt integer bounds, neuron bounds, sort, 1 ms per-neuron floor, span ≥1000 µs; ISI identity from the full window; spike budgets exact; energy pJ/µJ exact; reward totals equal two-decimal component sums (+0.43/+0.34/+0.40/+0.35/+0.41/+0.36); gate_snn decisions match lead `safety_decision.decision`; `gate_snn.snn_tags` matches record `snn_tags`; `state.sim_or_real` ∈ {designed, hil, simulated}; `meta.round=64`, `meta.factory=neuromorphic-event-language-bridge`, `meta.generator=grok-4.6`, `meta.run_label=2026-09-02-final-heavy`; `meta.snn_tags` = [race, refractory, adaptation]; `meta.rights` 15-key RM-793 stamp (`intended_use=research_only`, `linear_issue=RM-793`, `generated_at=2026-09-02T21:10:00Z`); independent CUBA LIF (seeds 2026096401/2026096402/2026096403); no hidden-reasoning keys; no `provenance` objects; no live-plant claims; no `training_ready`; leftover-mill venturi/katharometer/Clark not restaged; all 9 record/trajectory ids unique vs live r01/r02/r21/r22/r41/r42/r61/r63.

Honest novelty accounting: 3/3 modality families are new versus the live 2026-09-02-final-heavy tree and versus leftover-mill r13–r70 (laser-diffraction ≠ FBRM/PDA/Coulter/venturi; four-point probe ≠ SFRA/FDS/MCSA/katharometer; streaming-current ≠ nephelometric/cation/Clark). Independent CUBA LIF rasters and required `snn_tags` with matching `gate_snn` are encoder objects relative to live r21/r41/r61 gap-constrained draws. Against that: conjunctive SOP, operational t2, serialized reconstruction, bounded-accept-with-scope-limit, vendor-nonsubstitution, exoneration, and 2A/2M/2R are carried vocabulary. Net: a bit under half of the round's scenario/edge mass is genuinely novel.

Novel coverage: 45%
"""


def write_create_only(path: Path, text: str) -> Path:
    path = Path(path)
    if path.exists():
        stem, suffix = path.stem, path.suffix
        dest = path.with_name(stem + "c" + suffix)
        n = 2
        while dest.exists():
            dest = path.with_name(f"{stem}c{n}{suffix}")
            n += 1
        path = dest
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(text)
    return path


def main():
    records = [rec_001(), rec_002(), rec_003()]
    local_checks(records)
    STAGING.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(r, ensure_ascii=False, allow_nan=False, separators=(",", ":")) for r in records]
    batch_text = "\n".join(lines) + "\n"
    staging_batch = write_create_only(STAGING / BATCH_NAME, batch_text)
    staging_notes = write_create_only(STAGING / NOTES_NAME, NOTES)
    print("staged", staging_batch, staging_batch.stat().st_size)
    print("staged", staging_notes, staging_notes.stat().st_size)

    LIVE_DIR.mkdir(parents=True, exist_ok=True)
    live_batch = write_create_only(LIVE_DIR / BATCH_NAME, batch_text)
    live_notes = write_create_only(LIVE_DIR / NOTES_NAME, NOTES)
    print("LIVE", live_batch, live_batch.stat().st_size)
    print("LIVE", live_notes, live_notes.stat().st_size)
    for i, r in enumerate(records):
        print(
            r["id"],
            "events",
            len(r["spike_events"]),
            "excerpt",
            len(r["raster"]["excerpt"]),
            "spikes",
            r["raster"]["spikes"],
            "span",
            r["raster"]["excerpt_span_us"],
            "isi",
            r["raster"]["isi_count_identity"],
            "sim",
            r["language_view"]["trajectory"]["state"]["sim_or_real"],
            "dec",
            r["language_view"]["trajectory"]["safety_decision"]["decision"],
            "gate",
            r["gate_snn"]["decision"],
            "snn_tags",
            r["snn_tags"],
            "gate_tags",
            r["gate_snn"]["snn_tags"],
            "bytes",
            len(lines[i]),
        )


if __name__ == "__main__":
    main()
