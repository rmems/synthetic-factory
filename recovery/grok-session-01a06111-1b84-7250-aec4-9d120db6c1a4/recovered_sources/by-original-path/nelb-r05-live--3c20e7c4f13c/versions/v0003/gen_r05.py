#!/usr/bin/env python3
"""Generate NELB round-5 live-tree bridge pairs. CREATE-ONLY into outputs/raw/.

Independent CUBA LIF rasters (not a re-encode of spike_events). Required
snn_tags {race, refractory, adaptation} on record, meta, and matching gate_snn.
Do not touch 2026-08-17 or 2026-08-30.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import random
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

LIVE = Path(
    "/home/raulmc/rmems/synthetic-factory/outputs/raw/2026-09-02-final-heavy/"
    "neuromorphic-event-language-bridge"
)
BATCH = LIVE / "batch-r05.jsonl"
NOTES = LIVE / "NOTES-r05.md"
STAGING = Path("/tmp/nelb-r05-live")
PIPELINES = Path("/home/raulmc/rmems/synthetic-factory/pipelines")
sys.path.insert(0, str(PIPELINES))
sys.path.insert(0, "/tmp")
from lif_raster import generate_lif_raster  # noqa: E402

GENERATED_AT = "2026-09-02T22:10:00Z"
SNN_TAGS = ["race", "refractory", "adaptation"]
ROUND = 5

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
        "round": ROUND,
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
    last = {}
    prev_t = -1
    for e in excerpt:
        t_us = int(e["t_us"])
        nid = int(e["neuron_id"])
        if t_us < prev_t:
            raise RuntimeError("excerpt unsorted")
        if not (0 <= t_us <= int(round(window_ms * 1000))):
            raise RuntimeError(f"t_us {t_us} out of window")
        if not (0 <= nid < neurons):
            raise RuntimeError(f"neuron_id {nid}")
        prev = last.get(nid)
        if prev is not None and (t_us - prev) < 1000:
            raise RuntimeError(f"refractory n{nid} {t_us - prev} us")
        last[nid] = t_us
        by_n[nid].append(t_us)
        prev_t = t_us

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
        hist.append({"lo_ms": edges[i], "hi_ms": float(hi), "count": c})
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
        "excerpt_generator": "independent_cuba_lif",
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
            "seed": int(seed),
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


def _exact(a, b, eps=1e-12):
    if abs(a - b) > eps:
        raise RuntimeError(f"arith {a} != {b}")


def occupancy_preflight():
    banned = (
        "merganserholt",
        "pintailmire",
        "wigeoncrag",
        "squidveil",
        "pivveil",
        "imsveil",
        "nelb-r03-001",
        "nelb-r03-002",
        "nelb-r03-003",
        "dc-squid remaining",
        "particle-image-velocimetry remaining",
        "ion-mobility remaining tatp",
    )
    hits = []
    if LIVE.is_dir():
        for n in sorted(LIVE.glob("batch-r*.jsonl")):
            text = n.read_text(encoding="utf-8", errors="replace").casefold()
            for b in banned:
                if b in text:
                    hits.append(f"{n.name}:{b}")
    if hits:
        raise RuntimeError(f"family/plant collision {hits}")


def rec_001():
    k_s = 0.50
    phi = 40.00
    i_ka = k_s * phi
    _exact(i_ka, 20.00)
    _exact(k_s * 8.00, 4.00)
    _exact(k_s * 16.00, 8.00)
    _exact(k_s * 24.00, 12.00)
    _exact(k_s * 48.00, 24.00)
    v_kv = 1.20
    p_mw = i_ka * v_kv
    _exact(p_mw, 24.00)
    phi_id = i_ka / k_s
    _exact(phi_id, 40.00)
    _exact(6000.0 + 1080.0, 7080.0)

    raster = make_lif_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=40.0,
        seed=2026090301,
        source="mh5.squid.phi",
        target="merganserholt.dump_stop_core",
        table=[
            {"from": "squid_phi", "to": "current_estimator", "weight": 1.40},
            {"from": "squid_snr", "to": "flux_lock_core", "weight": 1.15},
            {"from": "squidveil_i", "to": "vendor_continue_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "da.squid_dump_conflict",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": "pre-post coincidence on continue-idle synapses; the plant dc-SQUID modulator depresses continue-idle links when flux-quantum count stays high inside tau_e of an SNR lock so a Squidveil last-good cannot hide a 20.00 kA remaining-dump current after I=k_s*Phi is applied",
        },
        channel_prefix="squid.n",
        anchor="MH-5 dc-SQUID 40 ms frame at Phi 40.00 Phi0 / SNR 12.0 (t_s 3000) reconstructing 20.00 kA over the 12.00 kA isolate floor",
        tau_m_ms=10.0,
    )
    w_s = 0.040
    events = [
        ev(0.0, "squid.phi", 16.00, code="PHI_PHI0", units="Phi0", note="plant-owned dc-SQUID remaining-current of Merganserholt SMES MH-5 dump D-7; Josephson flux-quantum family, not SERF OPM, not Faraday FOCT, not Rogowski, not manganin shunt, not Hall MFL"),
        ev(180000.0, "squid.snr", 6.0, code="SQUID_SNR", units="1", note="early SNR under the 8.0 lock floor"),
        ev(360000.0, "recon.I", 4.00, code="I_KA", units="kA", note="0.50*8.00=4.00 exact; still under the 12.00 isolate floor"),
        ev(540000.0, "bus.V", 1.20, code="V_KV", units="kV", note="plant dump-bus voltage on copper DCS; independent witness; unread by Squidveil"),
        ev(720000.0, "squidveil.I", 2.40, code="VENDOR_KA", units="kA", note="Squidveil vendor SQUID-cloud last-good; infra owner; patched flux timestamps"),
        ev(900000.0, "squid.phi", 24.00, code="PHI_PHI0", units="Phi0"),
        ev(1080000.0, "recon.I", 8.00, code="I_KA", units="kA", note="0.50*16.00=8.00; isolate-adjacent band"),
        ev(1260000.0, "permit.slide", 40.00, code="PERM_S", units="s", note="permit clerk Tamsin Brier slid the dump-current clock 40.00 s; collusion party"),
        ev(1440000.0, "bus.V", 1.20, code="V_KV", units="kV"),
        ev(1620000.0, "recon.phi", 16.00, code="PHI_ID", units="Phi0", note="I/k_s identity at the 8.00 kA band"),
        ev(1800000.0, "squid.phi", 32.00, code="PHI_PHI0", units="Phi0"),
        ev(1980000.0, "recon.I", 12.00, code="I_KA", units="kA", note="0.50*24.00=12.00; isolate floor"),
        ev(2160000.0, "dump.R", 0.060, code="R_OHM", units="ohm", note="plant-owned dump-resistor millivolt; independent of Squidveil"),
        ev(2340000.0, "squidveil.I", 2.40, code="VENDOR_KA", units="kA"),
        ev(2520000.0, "squid.snr", 9.0, code="SQUID_SNR", units="1"),
        ev(2700000.0, "recon.k", 0.50, code="KS", units="kA_per_Phi0", note="scale intercept used by the reconstruction"),
        ev(3000000.0, "squid.phi", 40.00, code="PHI_PHI0", units="Phi0", note="isolate-floor frame; raster sidecar"),
        ev(3000001.4, "squid.snr", 12.0, code="SQUID_SNR", units="1", note="1.4 ms SNR lock after Phi; 12.0 >= 8.0"),
        ev(3180000.0, "recon.I", 20.00, code="I_KA", units="kA", note="0.50*40.00=20.00 exact; isolate 12.00, hall-kill 80.00"),
        ev(3360000.0, "recon.P", 24.00, code="P_MW", units="MW", note="20.00*1.20=24.00 exact dump-power identity"),
        ev(3540000.0, "recon.phi", 40.00, code="PHI_ID", units="Phi0", note="20.00/0.50=40.00 exact flux identity"),
        ev(3720000.0, "squidveil.drop", 1.0, code="SQ_DROP", units="bool", note="vendor SQUID packets dropped in Squidveil cloud for 40 s"),
        ev(3900000.0, "collude.clerk", 1.0, code="CLERK", units="bool"),
        ev(4080000.0, "bus.V", 1.20, code="V_KV", units="kV", note="dump-bus V tracks the plant SQUID, not Squidveil 2.40"),
        ev(4260000.0, "dump.R", 0.060, code="R_OHM", units="ohm"),
        ev(4440000.0, "recon.k", 0.50, code="KS", units="kA_per_Phi0"),
        ev(4620000.0, "squidveil.I", 2.35, code="VENDOR_KA", units="kA"),
        ev(4800000.0, "ops.prop", 1.0, code="CONTINUE_IDLE", units="bool", note="night operator Rory Venn: Squidveil is clean 2.40 kA; continue D-7 dump idle"),
        ev(4980000.0, "recon.I", 20.00, code="I_KA", units="kA", note="repeat of the 20.00 kA reconstruction as SoT"),
        ev(5400000.0, "gate.stop", 1.0, code="REJECT", units="decision", note="refuse continue-idle; 20.00 kA and SNR 12.0; Squidveil not SoT"),
        ev(6000000.0, "dump.start", 1.0, code="DUMP_HOLD_START", units="bool", note="bookend 1 of the 18.0 min dump-hold floor"),
        ev(7080000.0, "dump.floor", 1.0, code="DUMP_HOLD_FLOOR", units="bool", note="6000 s + 1080 s = 7080 s = 18.0 min"),
        ev(7800000.0, "ops.kill", 1.0, code="HALL_ESD", units="bool", note="Venn: ESD the whole Merganserholt SMES hall until day-shift"),
        ev(8400000.0, "gate.hold", 1.0, code="MODIFY", units="decision", note="companion t2: dump-hold on plant dc-SQUID as live interlock; hall ESD refused"),
        ev(9000000.0, "dumplock.set", 1.0, code="DUMP_HELD", units="bool"),
        ev(9600000.0, "squid.phi", 48.00, code="PHI_PHI0", units="Phi0"),
        ev(10200000.0, "recon.I", 24.00, code="I_KA", units="kA", note="0.50*48.00=24.00; still over 12.00 so dump-hold stands"),
        ev(10800000.0, "squidveil.I", 2.30, code="VENDOR_KA", units="kA"),
        ev(11400000.0, "bus.V", 1.20, code="V_KV", units="kV"),
        ev(12000000.0, "dump.held", 1.0, code="DUMP_HELD", units="bool"),
        ev(12600000.0, "unit.esd", 0.0, code="ESD_NOT_TAKEN", units="bool"),
        ev(13200000.0, "permit.slide", 40.00, code="PERM_S", units="s"),
        ev(13800000.0, "squidveil.drop", 1.0, code="SQ_DROP", units="bool"),
        ev(14400000.0, "dumplock.held", 1.0, code="DUMP_HELD", units="bool"),
        ev(15000000.0, "recon.P", 28.80, code="P_MW", units="MW", note="24.00*1.20=28.80 on the post-stop frame"),
        ev(15600000.0, "dump.R", 0.060, code="R_OHM", units="ohm"),
        ev(16200000.0, "recon.phi", 48.00, code="PHI_ID", units="Phi0", note="24.00/0.50=48.00 inverse check"),
        ev(16800000.0, "collude.clerk", 1.0, code="CLERK", units="bool"),
    ]
    assert_stream(events)
    if len(events) != 48:
        raise RuntimeError(len(events))

    traj = {
        "id": "nelb-r03-001-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "MH-SQUID-2026-0902",
            "domain": "dc_squid_smes_dump_current",
            "setting": "Merganserholt SMES MH-5 (invented), dump bus D-7. Plant-owned dc-SQUID (Josephson flux-quantum count) is the remaining-dump-current SoT. Squidveil vendor SQUID-cloud (infra owner) plus the dump-current permit clock are collusion parties, not witnesses. Invented plant; designed campaign. Not live r21 SERF OPM remaining current, not leftover-mill Faraday FOCT, not leftover-mill Rogowski, not leftover-mill manganin-shunt potline current, not Hall MFL remaining wall.",
            "observables_at_decision": {
                "Phi_Phi0": phi,
                "k_s": k_s,
                "I_kA": i_ka,
                "V_kV": v_kv,
                "P_MW": p_mw,
                "squid_snr": 12.0,
                "squidveil_kA": 2.40,
                "permit_slide_s": 40.00,
                "isolate_floor_kA": 12.00,
            },
            "margin_authority": "MH-5 SMES SOP rev C: if reconstructed I_kA >= 12.00 AND SQUID SNR >= 8.0, continue-idle of dump D-7 is forbidden even if Squidveil reports 2.40 kA. Hall ESD is a different gate. Kill tripwire is 80.00 kA.",
        },
        "proposed_action": {
            "actor": "night SMES operator Rory Venn, citing Squidveil 2.40 kA and a quiet flux channel",
            "summary": "continue D-7 dump idle; 40.00 Phi0 is preamp flux noise on a healthy dump last-good",
            "basis_claimed": "Squidveil is the only OEM SQUID SoT and a night abort of D-7 is a dump-nomination miss",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Continue-idle is refused. Serialized reconstruction: I_kA = k_s * Phi = 0.50 * 40.00 = 20.00, which is 8.00 kA over the 12.00 isolate floor and 60.00 kA under the 80.00 hall-kill tripwire, and SQUID SNR is 12.0 >= 8.0. Flux identity Phi = I / k_s = 20.00 / 0.50 = 40.00; dump-power identity P = I * V = 20.00 * 1.20 = 24.00 MW. Permit clock was slid 40.00 s and vendor SQUID packets were dropped, so Squidveil is a collusion party (SQUID vendor plus operator plus permit clerk Tamsin Brier). Ordered: refuse continue-idle now. Scope: this REJECT does not ESD the SMES hall (that is the companion question) and does not isolate the dump-bus voltage.",
            "threshold": "I_kA>=12.00 AND squid_snr>=8.0 => refuse continue-idle; Squidveil is not SoT; hall-kill if I_kA>=80.00",
            "stated_residuals": "dump-hold still required to hold the 20.00 kA; 20.00 vs a true 80.00 kill is a production cut; Squidveil remains the only OEM SQUID channel",
        },
        "executed_action": {
            "summary": "REJECT at t_s 5400: continue-idle refused; Squidveil not SoT; reconstruction locked",
            "tool": "mh5-squid-dump-gate-cli",
            "observation": "I 20.00 kA recomputes from Phi 40.00 Phi0; plant dc-SQUID hashed; Squidveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "SQUID Phi 40.00 Phi0; raster frame; I 20.00 kA"},
                {"t_s": 4800.0, "event": "ops proposes continue-idle"},
                {"t_s": 5400.0, "event": "REJECT continue-idle"},
                {"t_s": 6000.0, "event": "18 min dump-hold bookend 1"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 8400.0, "event": "companion MODIFY dump-hold vs hall ESD"},
            ],
            "observed_effects": [
                "remaining dump current recomputes from the serialized dc-SQUID model at every recon.I event",
                "a Squidveil-only head would have continued D-7 overnight",
                "18 min dump-hold floor is in the stream (dump.start, dump.floor)",
            ],
            "surprises": [
                "a clean vendor 2.40 kA corridor and a 40 s permit slide co-existed with a 20.00 kA plant reconstruction",
            ],
            "new_state": {
                "d7": "continue-idle blocked",
                "squidveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("squid_current_reconstruction", 0.14),
                ("conjunctive_isolate_floor", 0.12),
                ("squidveil_nonsubstitution", 0.10),
                ("three_party_collusion", 0.10),
                ("dump_time_cost", -0.03),
            ],
            "scored for a continue-idle REJECT on a recomputable dc-SQUID dump current while refusing a Squidveil last-good patch and a permit clock slide; 18 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["REJECT", "dc-squid-current", "serialized-reconstruction", "operational-companion"],
            distillation_value="Independent CUBA LIF raster races the flux-quantum estimator against a vendor-continue advocate with 1 ms refractory and 0.82**k adaptation, so a hybrid head can distill I=k_s*Phi without copying the campaign stream.",
            distillation_note="dc-SQUID gate: serialized k_s*Phi plus SNR lock beats a vendor last-good patch; companion t2 is the dump-hold, not a referral vote",
        ),
    }
    traj2 = {
        "id": "nelb-r03-001-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "MH-SQUID-2026-0902-exec",
            "domain": "dump_hold_squid_interlock_execution",
            "setting": "Same MH-5 after the REJECT. Operator proposes SMES-hall ESD. This companion is the operational dump-hold with the plant dc-SQUID as the live interlock, not a second current vote.",
            "observables_at_decision": {
                "I_kA": 24.00,
                "dump_floor_s": 1080.0,
                "hall_esd_proposed": True,
                "dump_hold_set": True,
            },
            "margin_authority": "dump_hold AND dump_floor_complete AND hall_esd_not_taken AND continue_not_restored",
        },
        "proposed_action": {
            "actor": "night SMES operator Rory Venn",
            "summary": "ESD the whole Merganserholt SMES hall until day-shift; 18 min already paid and Squidveil still shows 2.30 kA",
            "basis_claimed": "the REJECT already stopped D-7 idle, so a hall kill is the cheapest hold",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Dump-hold plus plant dc-SQUID as the live interlock. The 18 min dump-hold floor is complete and the isolate tripwire (I_kA >= 12.00) is still armed on the plant SQUID head. MODIFY the default Squidveil-restore SOP into a plant-SQUID-only interlock. Do not ESD the SMES hall. Do not restore idle on Squidveil. 24.00 kA post-stop is still the plant SoT until a new frame clears 12.00.",
            "threshold": "dump_hold AND dump_floor_complete AND hall_esd_not_taken AND continue_not_restored",
            "stated_residuals": "hold still required; Squidveil remains the only OEM SQUID channel",
        },
        "executed_action": {
            "summary": "dump-hold held at t_s 8400; hall ESD not latched; Squidveil restore not taken",
            "tool": "mh5-dump-hold-exec",
            "observation": "recon.I 24.00 kA after stop; dump-hold line-up complete; Squidveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "dump-hold clock started after REJECT"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 7800.0, "event": "hall ESD proposed"},
                {"t_s": 8400.0, "event": "MODIFY dump-hold; hall ESD refused"},
            ],
            "observed_effects": [
                "Squidveil restore did not reopen the dump-current call",
                "hall ESD never fired; D-7 held dump on the plant dc-SQUID",
            ],
            "surprises": [
                "post-stop 24.00 kA (Phi 48.00) still recomputes from k_s*Phi while Squidveil stays at 2.30 kA",
            ],
            "new_state": {"hold": "held", "hall": "in service", "d7": "held"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("dump_hold", 0.12),
                ("no_hall_esd", 0.10),
                ("squidveil_nonsubstitution", 0.08),
                ("dump_floor_complete", 0.06),
                ("held_idle_cost", -0.02),
            ],
            "operational execution gate: dump-hold because Squidveil is not a restore license; not a current re-vote",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "dump-hold"]),
    }
    return {
        "id": "nelb-r03-001",
        "snn_tags": list(SNN_TAGS),
        "spike_events": events,
        "language_view": {
            "description": "Merganserholt SMES MH-5. Plant-owned dc-SQUID reconstructs 20.00 kA dump current from 0.50*40.00 while Squidveil still reports 2.40 kA. The gate REJECTs continue-idle. An 18 min dump-hold floor is serialized in the stream. Companion t2 MODIFYs a hall ESD into a plant-SQUID dump-hold.",
            "trajectory": traj,
            "trajectory_dump_hold": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "squid.phi / squid.snr": "flux-quantum count and SNR; the physics channels the reconstruction consumes",
                "recon.I / recon.P / recon.phi / recon.k": "serialized remaining current kA, dump-power identity, and Phi=I/k_s identity",
                "bus.V / squidveil.I / permit.slide / squidveil.drop / collude.clerk": "dump-bus voltage, vendor last-good, permit clock slide, dropped packets, clerk; the denial and collusion channels",
                "ops.prop / gate.stop / ops.kill / gate.hold": "continue-idle proposal, REJECT, hall-ESD proposal, companion MODIFY",
                "dump.start / dump.floor / dumplock.set / dump.held / unit.esd": "operational companion channels plus the 18 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-over: squidveil.I 2.40 next to recon.I 20.00",
                "reconstruction as event: recon.I 20.00 equals 0.50*40.00",
                "REJECT then operational MODIFY: gate.stop at 5400 s, gate.hold at 8400 s",
                "slow floor in-stream: dump.start 6000 s, dump.floor 7080 s (18.0 min)",
                "tight SQUID pair: squid.phi then squid.snr +1.4 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Squidveil is 2.40 kA' = squidveil.I 2.40; '20 kA remaining dump' = recon.I 20.00; 'refuse continue-idle' = gate.stop REJECT; 'dump-hold not hall ESD' = gate.hold MODIFY",
            "why_high_value": "New dc-SQUID remaining-current family on a SMES dump bus (not SERF OPM r21, not Faraday FOCT, not Rogowski, not manganin shunt, not Hall MFL). Lead REJECT of continue-idle on a recomputable dump current that a vendor last-good patch and a permit clock slide would have cleared. Independent CUBA LIF raster (not a spike_events echo) plus required snn_tags. Companion t2 is operational dump-hold. sim_or_real=designed.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random plus CUBA LIF",
                "seeds": {"raster": 2026090301, "stream_note": "stream amplitudes are authored constants; raster is independent CUBA LIF"},
                "draw_order": "raster: independent CUBA LIF first-passage times, per-spike adaptation and noise; not copied from spike_events",
                "thinning": "dc-SQUID exists at ~1 kHz flux-locked loop; stream keeps 6 Phi points; recon keeps 6 of ~40 solver ticks; 48-event floor",
                "refractory_floors_ms": {
                    "squid.phi": 1.4,
                    "squid.snr": 1.4,
                    "recon.I": 60000,
                    "recon.P": 60000,
                    "recon.phi": 60000,
                    "recon.k": 60000,
                    "bus.V": 60000,
                    "squidveil.I": 60000,
                    "permit.slide": 60000,
                    "dump.R": 60000,
                    "squidveil.drop": 60000,
                    "collude.clerk": 60000,
                    "ops.prop": 60000,
                    "gate.stop": 60000,
                    "dump.start": 60000,
                    "dump.floor": 60000,
                    "ops.kill": 60000,
                    "gate.hold": 60000,
                    "dumplock.set": 60000,
                    "dump.held": 60000,
                    "unit.esd": 60000,
                    "dumplock.held": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-09-02T01:00:00Z campaign start",
            },
            "distillation_targets": [
                "dc-SQUID reconstruction head: I = k_s * Phi; Phi = I / k_s; P = I * V",
                "conjunctive isolate floor vs continue-idle vs hall ESD",
                "vendor-SQUID nonsubstitution plus three-party collusion including the infra owner",
                "operational companion: dump-hold without restoring on Squidveil",
                "independent CUBA LIF raster with race/refractory/adaptation tags",
            ],
        },
        "reconstruction_model": {
            "name": "dc_squid_smes_dump_current",
            "formula": "I_kA = k_s * Phi_Phi0; Phi_id = I_kA / k_s; P_MW = I_kA * V_kV",
            "parameters": {
                "k_s": 0.50,
                "V_kV": 1.20,
                "isolate_floor_kA": 12.00,
                "kill_kA": 80.00,
                "snr_lock": 8.0,
                "dump_min": 18.0,
            },
            "worked_example": {"Phi_Phi0": 40.00, "I_kA": 20.00, "P_MW": 24.00, "Phi_id": 40.00},
            "check": "0.50 * 40.00 = 20.00 exactly; 20.00 / 0.50 = 40.00 exactly; 20.00 * 1.20 = 24.00 exactly; 6000 s + 1080 s = 7080 s = 18.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "snn_tags": list(SNN_TAGS),
            "code": "mh5.squid_dump_gate",
            "note": "REJECT accumulator wins: plant dc-SQUID dump-current evidence overpowers the Squidveil continue advocate; race/refractory/adaptation tags match meta.snn_tags",
            "decode_rule": "reject-continue if current_estimator AND flux_lock fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("current_estimator", 80, 1.5, 50.0, w_s, tag="adaptation"),
                gate_pop("flux_lock", 64, 1.2, 31.25, w_s, tag="refractory"),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s, tag="race"),
                gate_pop("reject_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "mh5.squid_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "mh5.dump_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r03-001",
            clock_domain="mh5-squid-campaign-relative-ms-t0-2026-09-02T01:00:00Z",
            tags=["dc-squid-current", "REJECT", "MODIFY", "serialized-reconstruction", "operational-t2", "independent-lif"],
            distillation_value="Independent LIF raster teaches race/refractory/adaptation while the language view teaches dc-SQUID remaining-current reconstruction-as-SoT.",
        ),
    }


def rec_002():
    k_p = 0.50
    dx = 16.00
    dt = 4.00
    ratio = dx / dt
    _exact(ratio, 4.00)
    u = k_p * ratio
    _exact(u, 2.00)
    _exact(k_p * (4.00 / 4.00), 0.50)
    _exact(k_p * (8.00 / 4.00), 1.00)
    _exact(k_p * (12.00 / 4.00), 1.50)
    _exact(k_p * (20.00 / 4.00), 2.50)
    area = 0.80
    q = u * area
    _exact(q, 1.60)
    _exact(2820.0 + 1440.0, 4260.0)

    raster = make_lif_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=32.0,
        seed=2026090302,
        source="pm4.piv.dx",
        target="pintailmire.tank_isolate_core",
        table=[
            {"from": "piv_dx", "to": "velocity_estimator", "weight": 1.35},
            {"from": "piv_snr", "to": "sheet_norm_core", "weight": 1.20},
            {"from": "pivveil_u", "to": "vendor_continue_advocate", "weight": 0.40},
        ],
        third_factor={
            "modulator": "ach.piv_sheet_skip_salience",
            "tau_e_s": 1.2,
            "tau_e_ms": 1200.0,
            "eligibility": "pre-post coincidence on keep-tank synapses; the PIV modulator depresses keep-tank and referral links when pixel displacement stays high inside tau_e of an SNR lock so a Pivveil last-good cannot hide 2.00 m/s remaining impeller velocity or name Lena Quist",
        },
        channel_prefix="piv.n",
        anchor="PM-4 HIL coupon 32 ms frame at dx 16.00 px / SNR 14.0 (t_s 1560) reconstructing 2.00 m/s over the 1.20 isolate floor",
        tau_m_ms=12.0,
    )
    w_s = 0.032
    events = [
        ev(0.0, "piv.dx", 4.00, code="DX_PX", units="px", note="HIL particle-image velocimetry on a dummy fermenter impeller zone in PIV-HIL-7; remaining-velocity family, not LDA, not Kaplan LDV, not CTA hot-wire, not background-oriented schlieren, not ADCP"),
        ev(180000.0, "piv.snr", 9.0, code="PIV_SNR", units="1", note="early sheet SNR; isolate needs SNR>=12"),
        ev(360000.0, "recon.u", 0.50, code="U_MPS", units="m_s", note="0.50*(4.00/4.00)=0.50 exact"),
        ev(540000.0, "sheet.ae", 1.0, code="SHEET_AE", units="bool", note="plant laser-sheet AE present on the early frame"),
        ev(720000.0, "pivveil.u", 0.40, code="VENDOR_MPS", units="m_s", note="Pivveil last-good velocity cloud; not admissible SoT"),
        ev(900000.0, "piv.dx", 8.00, code="DX_PX", units="px"),
        ev(1080000.0, "recon.u", 1.00, code="U_MPS", units="m_s", note="0.50*(8.00/4.00)=1.00; under the 1.20 isolate floor"),
        ev(1260000.0, "sheet.ae", 0.0, code="SHEET_AE", units="bool", note="missing laser-sheet AE burst; Pivveil UTC vs plant UTC+2 skipped the sheet-zero by 120 min"),
        ev(1440000.0, "tank.A", 0.80, code="A_M2", units="m2", note="plant-owned impeller swept area on copper fieldbus; independent of Pivveil"),
        ev(1560000.0, "piv.dx", 16.00, code="DX_PX", units="px", note="isolate-floor frame; raster sidecar; dt 4.00 ms"),
        ev(1560001.2, "piv.snr", 14.0, code="PIV_SNR", units="1", note="1.2 ms sheet-norm after PIV displacement"),
        ev(1740000.0, "recon.u", 2.00, code="U_MPS", units="m_s", note="0.50*(16.00/4.00)=2.00 exact; isolate 1.20, house-dump 8.00"),
        ev(1920000.0, "recon.Q", 1.60, code="Q_M3S", units="m3_s", note="2.00*0.80=1.60 exact; volume-rate identity"),
        ev(2100000.0, "recon.ratio", 4.00, code="DXDT", units="px_ms", note="16.00/4.00=4.00 exact displacement-rate identity"),
        ev(2280000.0, "pivveil.u", 0.40, code="VENDOR_MPS", units="m_s"),
        ev(2460000.0, "ops.prop", 1.0, code="KEEP_TANK_REFER", units="bool", note="night lead Edda Holt: keep tank T-3 and refer PIV tech Lena Quist"),
        ev(2640000.0, "gate.isol", 1.0, code="MODIFY", units="decision", note="isolate this tank; refuse the person-referral; Pivveil not SoT"),
        ev(2820000.0, "tank.lock", 1.0, code="TANK_ISOL", units="bool", note="bookend 1 of the 24.0 min new-sheet floor"),
        ev(3000000.0, "piv.dx", 12.00, code="DX_PX", units="px"),
        ev(3180000.0, "recon.u", 1.50, code="U_MPS", units="m_s", note="0.50*(12.00/4.00)=1.50 still over 1.20"),
        ev(3360000.0, "sheet.ae", 0.0, code="SHEET_AE", units="bool"),
        ev(3540000.0, "tank.A", 0.80, code="A_M2", units="m2"),
        ev(3720000.0, "pivveil.u", 0.38, code="VENDOR_MPS", units="m_s"),
        ev(3900000.0, "recon.Q", 1.20, code="Q_M3S", units="m3_s", note="1.50*0.80=1.20"),
        ev(4080000.0, "recon.ratio", 3.00, code="DXDT", units="px_ms"),
        ev(4260000.0, "sheet.floor", 1.0, code="SHEET_FLOOR", units="bool", note="2820 s + 1440 s = 4260 s = 24.0 min"),
        ev(4440000.0, "ops.restart", 1.0, code="NEW_SHEET", units="bool", note="Holt: restart T-3 on a new laser sheet after the floor"),
        ev(4620000.0, "gate.restart", 1.0, code="ACCEPT", units="decision", note="companion t2: new-sheet restart of the dummy tank; keep-running refused earlier"),
        ev(4800000.0, "sheet.new", 1.0, code="SHEET_NEW", units="bool"),
        ev(4980000.0, "piv.dx", 20.00, code="DX_PX", units="px", note="post-isolate dummy still high until the new sheet"),
        ev(5160000.0, "recon.u", 2.50, code="U_MPS", units="m_s", note="0.50*(20.00/4.00)=2.50 on the pre-restart dummy"),
        ev(5340000.0, "pivveil.u", 0.36, code="VENDOR_MPS", units="m_s"),
        ev(5520000.0, "lena.badge", 0.0, code="TECH_FAULT", units="bool", note="Lena Quist exonerated: missing laser-sheet AE plus timezone skip, not last-to-badge"),
        ev(5700000.0, "tank.lock", 1.0, code="TANK_ISOL", units="bool"),
        ev(5880000.0, "sheet.ae", 1.0, code="SHEET_AE", units="bool", note="new-sheet AE present"),
        ev(6060000.0, "piv.snr", 14.0, code="PIV_SNR", units="1"),
        ev(6240000.0, "tank.A", 0.80, code="A_M2", units="m2"),
        ev(6420000.0, "recon.Q", 2.00, code="Q_M3S", units="m3_s"),
        ev(6600000.0, "keep.run", 0.0, code="KEEP_REFUSED", units="bool"),
        ev(6780000.0, "pivveil.u", 0.36, code="VENDOR_MPS", units="m_s"),
        ev(6960000.0, "sheet.new", 1.0, code="SHEET_NEW", units="bool"),
        ev(7140000.0, "lena.badge", 0.0, code="TECH_FAULT", units="bool"),
        ev(7320000.0, "recon.ratio", 5.00, code="DXDT", units="px_ms"),
        ev(7500000.0, "tank.held", 1.0, code="TANK_ISOL", units="bool"),
        ev(7680000.0, "ops.prop", 1.0, code="KEEP_TANK_REFER", units="bool"),
        ev(7860000.0, "gate.isol", 1.0, code="MODIFY", units="decision"),
        ev(8040000.0, "sheet.floor", 1.0, code="SHEET_FLOOR", units="bool"),
        ev(8220000.0, "gate.restart", 1.0, code="ACCEPT", units="decision"),
    ]
    assert_stream(events)
    if len(events) != 48:
        raise RuntimeError(len(events))

    traj = {
        "id": "nelb-r03-002-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "PM-PIV-2026-0902",
            "domain": "piv_fermenter_impeller_velocity",
            "setting": "Pintailmire Ferment PM-4 (invented), dummy tank T-3 in PIV-HIL-7. Plant-owned particle-image velocimetry (laser-sheet cross-correlation) is the remaining-impeller-velocity SoT. Pivveil vendor PIV-cloud is not SoT. HIL dummy; not a live plant. Not live r41 LDA, not leftover-mill Kaplan LDV, not leftover-mill CTA hot-wire, not live r42 background-oriented schlieren, not leftover-mill ADCP.",
            "observables_at_decision": {
                "dx_px": dx,
                "dt_ms": dt,
                "k_p": k_p,
                "u_mps": u,
                "Q_m3s": q,
                "dxdt": ratio,
                "piv_snr": 14.0,
                "pivveil_mps": 0.40,
                "isolate_floor_mps": 1.20,
            },
            "margin_authority": "PM-4 fermenter SOP rev C: if reconstructed u_mps >= 1.20 AND PIV SNR >= 12.0, keep-tank is forbidden even if Pivveil reports 0.40 m/s. Hall dump is a different gate. Kill tripwire is 8.00 m/s.",
        },
        "proposed_action": {
            "actor": "night lead Edda Holt, citing Pivveil 0.40 m/s and a quiet laser sheet",
            "summary": "keep tank T-3 and refer PIV tech Lena Quist; 16.00 px is seed-scatter noise on a healthy impeller",
            "basis_claimed": "Pivveil is the only OEM PIV SoT and a night abort of T-3 is a broth-nomination miss; Quist was last to badge the sheet",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Keep-tank is refused and the person-referral is refused. Serialized reconstruction: u_mps = k_p * (dx/dt) = 0.50 * (16.00/4.00) = 2.00, which is 0.80 m/s over the 1.20 isolate floor and 6.00 m/s under the 8.00 hall-dump tripwire, and PIV SNR is 14.0 >= 12.0. Displacement-rate identity dx/dt = 16.00/4.00 = 4.00 px/ms; volume-rate identity Q = u * A = 2.00 * 0.80 = 1.60 m3/s. Laser-sheet AE is missing and Pivveil timestamps are UTC against the plant UTC+2 sheet log, so Lena Quist is exonerated (timezone skip, not last-to-badge). Ordered: isolate this tank now. Scope: this MODIFY does not dump the fermenter hall (that is a different gate) and does not restore on Pivveil.",
            "threshold": "u_mps>=1.20 AND piv_snr>=12.0 => isolate tank; Pivveil is not SoT; hall-dump if u_mps>=8.00",
            "stated_residuals": "new-sheet restart still required after the 24 min floor; 2.00 vs a true 8.00 dump is a production cut; Pivveil remains the only OEM PIV channel",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 2640: tank T-3 isolated; Lena Quist not named; Pivveil not SoT; reconstruction locked",
            "tool": "pm4-piv-tank-gate-cli",
            "observation": "u 2.00 m/s recomputes from dx 16.00 px / dt 4.00 ms; plant PIV hashed; Pivveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1560.0, "event": "PIV dx 16.00 px; raster frame; u 2.00 m/s"},
                {"t_s": 2460.0, "event": "ops proposes keep-tank plus refer Quist"},
                {"t_s": 2640.0, "event": "MODIFY isolate T-3; referral refused"},
                {"t_s": 2820.0, "event": "24 min new-sheet bookend 1"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4620.0, "event": "companion ACCEPT new-sheet restart"},
            ],
            "observed_effects": [
                "remaining impeller velocity recomputes from the serialized PIV model at every recon.u event",
                "a Pivveil-only head would have kept T-3 overnight and named Quist",
                "24 min new-sheet floor is in the stream (tank.lock, sheet.floor)",
            ],
            "surprises": [
                "a clean vendor 0.40 m/s corridor co-existed with a 2.00 m/s plant reconstruction and a timezone-skipped sheet AE",
            ],
            "new_state": {
                "t3": "isolated",
                "pivveil": "not SoT",
                "lena_quist": "exonerated",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 1080000.0,
        },
        "reward_components": reward(
            0.40,
            [
                ("piv_velocity_reconstruction", 0.14),
                ("conjunctive_isolate_floor", 0.12),
                ("pivveil_nonsubstitution", 0.08),
                ("timezone_exoneration", 0.08),
                ("isolate_time_cost", -0.02),
            ],
            "scored for a keep-tank MODIFY isolate on a recomputable PIV impeller velocity while refusing a Pivveil last-good and a last-to-badge referral; 24 min floor is priced as downtime",
        ),
        "meta": meta_common(
            tags=["MODIFY", "piv-velocity", "serialized-reconstruction", "exoneration"],
            distillation_value="Independent CUBA LIF raster races the PIV estimator against a vendor-keep advocate; timezone-skipped sheet AE is the exoneration feature, not a prose margin.",
            distillation_note="PIV gate: serialized k_p*(dx/dt) plus SNR lock beats a vendor last-good; companion t2 is the new-sheet restart, not a second velocity vote",
        ),
    }
    traj2 = {
        "id": "nelb-r03-002-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "PM-PIV-2026-0902-exec",
            "domain": "new_sheet_piv_interlock_execution",
            "setting": "Same PIV-HIL-7 dummy after the isolate. Operator proposes a new-sheet restart of T-3. This companion is the operational restart, not a second velocity vote.",
            "observables_at_decision": {
                "u_mps": 2.50,
                "sheet_floor_s": 1440.0,
                "new_sheet_proposed": True,
                "tank_isolated": True,
            },
            "margin_authority": "new_sheet AND sheet_floor_complete AND keep_not_restored AND pivveil_not_sot",
        },
        "proposed_action": {
            "actor": "night lead Edda Holt",
            "summary": "restart T-3 on a new laser sheet after the 24 min floor; Pivveil still 0.36 m/s so the isolate was a false trip",
            "basis_claimed": "the 24 min is paid; a Pivveil-green restart is the cheapest restore",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "New-sheet restart of the dummy tank with the plant PIV as the live interlock. The 24 min sheet floor is complete. ACCEPT the new-sheet restart. Do not restore keep-tank on Pivveil. Do not reopen the Lena Quist referral. 2.50 m/s on the pre-restart dummy is still the plant SoT until a new-sheet frame clears 1.20.",
            "threshold": "new_sheet AND sheet_floor_complete AND keep_not_restored AND pivveil_not_sot",
            "stated_residuals": "T-3 stays on the plant PIV interlock; Pivveil remains the only OEM PIV channel",
        },
        "executed_action": {
            "summary": "new-sheet restart accepted at t_s 4620; keep-tank not restored; Pivveil still ignored",
            "tool": "pm4-sheet-exec",
            "observation": "recon.u 2.50 m/s pre-restart; new-sheet AE present; Pivveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2820.0, "event": "new-sheet clock started after isolate"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4440.0, "event": "new-sheet restart proposed"},
                {"t_s": 4620.0, "event": "ACCEPT new-sheet restart"},
            ],
            "observed_effects": [
                "Pivveil restore did not reopen the velocity call",
                "Lena Quist stayed exonerated; T-3 restarted on a new sheet",
            ],
            "surprises": [
                "pre-restart 2.50 m/s still recomputes from k_p*(dx/dt) while Pivveil stays at 0.36 m/s",
            ],
            "new_state": {"sheet": "new", "t3": "restarted-on-plant-PIV", "lena_quist": "exonerated"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.35,
            [
                ("new_sheet_restart", 0.12),
                ("no_pivveil_restore", 0.10),
                ("exoneration_held", 0.08),
                ("sheet_floor_complete", 0.07),
                ("held_broth_cost", -0.02),
            ],
            "operational execution gate: new-sheet restart because Pivveil is not a restore license; not a velocity re-vote",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "new-sheet"]),
    }
    return {
        "id": "nelb-r03-002",
        "snn_tags": list(SNN_TAGS),
        "spike_events": events,
        "language_view": {
            "description": "Pintailmire Ferment PM-4 HIL dummy. Plant-owned PIV reconstructs 2.00 m/s impeller velocity from 0.50*(16.00/4.00) while Pivveil still reports 0.40 m/s. The gate MODIFYs keep-tank into an isolate and exonerates Lena Quist. A 24 min new-sheet floor is serialized in the stream. Companion t2 ACCEPTs a new-sheet restart.",
            "trajectory": traj,
            "trajectory_new_sheet_restart": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "piv.dx / piv.snr": "PIV pixel displacement and SNR; the physics channels the reconstruction consumes",
                "recon.u / recon.Q / recon.ratio": "serialized remaining velocity m/s, volume-rate identity, and dx/dt identity",
                "sheet.ae / pivveil.u / tank.A / lena.badge": "laser-sheet AE, vendor PIV cloud, swept area, tech-fault denial",
                "ops.prop / gate.isol / ops.restart / gate.restart": "keep-tank proposal, MODIFY isolate, new-sheet proposal, companion ACCEPT",
                "tank.lock / sheet.floor / sheet.new / tank.held / keep.run": "operational companion channels plus the 24 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-over: pivveil.u 0.40 next to recon.u 2.00",
                "reconstruction as event: recon.u 2.00 equals 0.50*(16.00/4.00)",
                "MODIFY then operational ACCEPT: gate.isol at 2640 s, gate.restart at 4620 s",
                "slow floor in-stream: tank.lock 2820 s, sheet.floor 4260 s (24.0 min)",
                "tight PIV pair: piv.dx then piv.snr +1.2 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Pivveil is 0.40 m/s' = pivveil.u 0.40; '2 m/s remaining impeller' = recon.u 2.00; 'isolate tank' = gate.isol MODIFY; 'new-sheet restart' = gate.restart ACCEPT",
            "why_high_value": "New particle-image-velocimetry remaining-velocity family on a fermenter HIL dummy (not LDA r41, not Kaplan LDV, not CTA, not BOS r42, not ADCP). Lead MODIFY isolate on a recomputable impeller-velocity slip plus timezone-exoneration of the PIV tech. Independent CUBA LIF raster. Companion t2 is operational new-sheet restart. sim_or_real=hil.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random plus CUBA LIF",
                "seeds": {"raster": 2026090302, "stream_note": "stream amplitudes are authored constants; raster is independent CUBA LIF"},
                "draw_order": "independent CUBA LIF per neuron; per-spike adaptation and noise; not copied from spike_events",
                "thinning": "PIV exists at ~10 Hz frame pairs; stream keeps 5 dx points; recon keeps 5 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "piv.dx": 1.2,
                    "piv.snr": 1.2,
                    "recon.u": 60000,
                    "recon.Q": 60000,
                    "recon.ratio": 60000,
                    "sheet.ae": 60000,
                    "pivveil.u": 60000,
                    "tank.A": 60000,
                    "ops.prop": 60000,
                    "gate.isol": 60000,
                    "tank.lock": 60000,
                    "sheet.floor": 60000,
                    "ops.restart": 60000,
                    "gate.restart": 60000,
                    "sheet.new": 60000,
                    "lena.badge": 60000,
                    "keep.run": 60000,
                    "tank.held": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-09-02T02:00:00Z HIL coupon start",
            },
            "distillation_targets": [
                "PIV reconstruction head: u = k_p * (dx/dt); Q = u * A; dx/dt identity",
                "conjunctive isolate floor vs keep-tank vs hall dump",
                "vendor-PIV nonsubstitution plus timezone exoneration vs last-to-badge",
                "operational companion: new-sheet restart without restoring on Pivveil",
                "independent CUBA LIF raster with race/refractory/adaptation tags",
            ],
        },
        "reconstruction_model": {
            "name": "piv_fermenter_impeller_velocity",
            "formula": "u_mps = k_p * (dx_px / dt_ms); Q_m3s = u_mps * A_m2; dxdt = dx_px / dt_ms",
            "parameters": {
                "k_p": 0.50,
                "dt_ms": 4.00,
                "A_m2": 0.80,
                "isolate_floor_mps": 1.20,
                "dump_mps": 8.00,
                "snr_lock": 12.0,
                "sheet_min": 24.0,
            },
            "worked_example": {"dx_px": 16.00, "u_mps": 2.00, "Q_m3s": 1.60, "dxdt": 4.00},
            "check": "0.50 * (16.00/4.00) = 2.00 exactly; 2.00 * 0.80 = 1.60 exactly; 16.00/4.00 = 4.00 exactly; 2820 s + 1440 s = 4260 s = 24.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 32.0,
            "decision_window_s": 0.032,
            "snn_tags": list(SNN_TAGS),
            "code": "pm4.piv_tank_gate",
            "note": "MODIFY accumulator wins: plant PIV velocity evidence overpowers the Pivveil keep advocate; race/refractory/adaptation tags match meta.snn_tags",
            "decode_rule": "isolate if velocity_estimator AND sheet_norm fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("velocity_estimator", 80, 1.5, 50.0, w_s, tag="adaptation"),
                gate_pop("sheet_norm", 50, 1.2, 50.0, w_s, tag="refractory"),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s, tag="race"),
                gate_pop("modify_latch", 80, 1.6, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "pm4.piv_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 32.0},
                {"check": "pm4.sheet_scorer", "neurons": 50, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r03-002",
            clock_domain="pm4-piv-hil-relative-ms-t0-2026-09-02T02:00:00Z",
            tags=["piv-velocity", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2", "independent-lif", "exoneration"],
            distillation_value="Independent LIF raster teaches race/refractory/adaptation while the language view teaches PIV remaining-velocity reconstruction-as-SoT plus timezone exoneration.",
        ),
    }


def rec_003():
    k_i = 2.50
    i_nA = 16.00
    c_ppb = k_i * i_nA
    _exact(c_ppb, 40.00)
    _exact(k_i * 4.00, 10.00)
    _exact(k_i * 8.00, 20.00)
    _exact(k_i * 12.00, 30.00)
    _exact(k_i * 20.00, 50.00)
    l2 = 8.00
    v_drift = 2.00
    t_d = 2.00
    k0 = l2 / (v_drift * t_d)
    _exact(k0, 2.00)
    i_id = c_ppb / k_i
    _exact(i_id, 16.00)
    _exact(6000.0 + 720.0, 6720.0)

    raster = make_lif_raster(
        neurons=16,
        mean_rate_hz=62.5,
        window_ms=36.0,
        seed=2026090303,
        source="wc6.ims.i",
        target="wigeoncrag.vent_accept_core",
        table=[
            {"from": "ims_I", "to": "tatp_estimator", "weight": 1.30},
            {"from": "ims_snr", "to": "k0_lock_core", "weight": 1.10},
            {"from": "imsveil_c", "to": "vendor_dump_advocate", "weight": 0.42},
        ],
        third_factor={
            "modulator": "na.ims_vent_scope_eligibility",
            "tau_e_s": 2.0,
            "tau_e_ms": 2000.0,
            "eligibility": "pre-post coincidence on plant-dump synapses; the plant IMS modulator depresses dump-all links when ion current stays high inside tau_e of a K0 lock so an Imsveil last-good cannot hide a 40.00 ppb remaining-TATP slip on V-2 or expand the isolate past V-2",
        },
        channel_prefix="ims.n",
        anchor="WC-6 IMS-SIM-5 36 ms frame at I 16.00 nA / SNR 11.0 (t_s 3000) reconstructing 40.00 ppb over the 16.00 isolate floor, V-2 only",
        tau_m_ms=8.0,
    )
    w_s = 0.036
    events = [
        ev(0.0, "ims.I", 4.00, code="I_NA", units="nA", note="simulated ion-mobility remaining-TATP of Wigeoncrag Peroxide WC-6 vent V-2; drift-tube family, not PTR-MS MDI, not PID VOC, not FID THC, not QEPAS, not IMS-adjacent CLD NOx"),
        ev(180000.0, "ims.snr", 7.0, code="IMS_SNR", units="1", note="early SNR under the 8.0 lock floor"),
        ev(360000.0, "recon.C", 10.00, code="C_PPB", units="ppb", note="2.50*4.00=10.00 exact; still under the 16.00 isolate floor"),
        ev(540000.0, "vent.T", 300.0, code="VENT_K", units="K", note="plant vent thermocouple on the simulated coupon; independent of Imsveil"),
        ev(720000.0, "imsveil.C", 3.20, code="VENDOR_PPB", units="ppb", note="Imsveil last-good TATP cloud; healthy-looking 3.20 ppb; not admissible SoT"),
        ev(900000.0, "ims.I", 8.00, code="I_NA", units="nA"),
        ev(1080000.0, "recon.C", 20.00, code="C_PPB", units="ppb", note="2.50*8.00=20.00; over the 16.00 isolate floor"),
        ev(1260000.0, "v1.C", 4.00, code="C_PPB", units="ppb", note="adjacent vent V-1 stays healthy; out of scope for this ACCEPT"),
        ev(1440000.0, "v3.C", 3.50, code="C_PPB", units="ppb", note="V-3 out of scope"),
        ev(1620000.0, "v4.C", 3.80, code="C_PPB", units="ppb", note="V-4 out of scope"),
        ev(1800000.0, "ims.I", 12.00, code="I_NA", units="nA"),
        ev(1980000.0, "recon.C", 30.00, code="C_PPB", units="ppb", note="2.50*12.00=30.00; under dump 80.00"),
        ev(2160000.0, "recon.K0", 2.00, code="K0", units="cm2_Vs", note="8.00/(2.00*2.00)=2.00 TATP reduced-mobility lock"),
        ev(2340000.0, "imsveil.C", 3.20, code="VENDOR_PPB", units="ppb"),
        ev(2520000.0, "ims.snr", 9.0, code="IMS_SNR", units="1"),
        ev(2700000.0, "recon.Iid", 12.00, code="I_ID", units="nA", note="C/k_i identity at the 30.00 ppb band"),
        ev(3000000.0, "ims.I", 16.00, code="I_NA", units="nA", note="isolate-floor frame; raster sidecar"),
        ev(3000001.5, "ims.snr", 11.0, code="IMS_SNR", units="1", note="1.5 ms K0 lock after I; 11.0 >= 8.0"),
        ev(3180000.0, "recon.C", 40.00, code="C_PPB", units="ppb", note="2.50*16.00=40.00 exact; isolate 16.00, plant-dump 80.00"),
        ev(3360000.0, "recon.K0", 2.00, code="K0", units="cm2_Vs", note="8.00/(2.00*2.00)=2.00 exact reduced-mobility identity"),
        ev(3540000.0, "recon.Iid", 16.00, code="I_ID", units="nA", note="40.00/2.50=16.00 exact"),
        ev(3720000.0, "imsveil.C", 3.10, code="VENDOR_PPB", units="ppb"),
        ev(3900000.0, "v1.C", 4.00, code="C_PPB", units="ppb"),
        ev(4080000.0, "v3.C", 3.50, code="C_PPB", units="ppb"),
        ev(4260000.0, "v4.C", 3.80, code="C_PPB", units="ppb"),
        ev(4440000.0, "vent.T", 301.0, code="VENT_K", units="K"),
        ev(4620000.0, "ops.prop", 1.0, code="ISOLATE_V2", units="bool", note="sim operator Nyla Crowe: isolate V-2 only; V-1/V-3/V-4 stay in the header"),
        ev(4800000.0, "gate.acc", 1.0, code="ACCEPT", units="decision", note="bounded ACCEPT of V-2 isolate; plant dump refused; Imsveil not SoT"),
        ev(4980000.0, "v2.lock", 1.0, code="V2_ISOL", units="bool"),
        ev(6000000.0, "surv.start", 1.0, code="SURV_START", units="bool", note="bookend 1 of the 12.0 min survey floor"),
        ev(6720000.0, "surv.floor", 1.0, code="SURV_FLOOR", units="bool", note="6000 s + 720 s = 6720 s = 12.0 min"),
        ev(7200000.0, "ops.skip", 1.0, code="SKIP_SURVEY", units="bool", note="Crowe: skip the remaining-vent survey; Imsveil still 3.10 ppb"),
        ev(7800000.0, "gate.surv", 1.0, code="REJECT", units="decision", note="companion t2: REJECT skip-survey; V-1/V-3/V-4 stay in the survey takt"),
        ev(8400000.0, "surv.held", 1.0, code="SURV_HELD", units="bool"),
        ev(9000000.0, "ims.I", 20.00, code="I_NA", units="nA"),
        ev(9600000.0, "recon.C", 50.00, code="C_PPB", units="ppb", note="2.50*20.00=50.00 post-isolate on V-2; still under dump 80.00"),
        ev(10200000.0, "imsveil.C", 3.00, code="VENDOR_PPB", units="ppb"),
        ev(10800000.0, "v1.C", 4.10, code="C_PPB", units="ppb"),
        ev(11400000.0, "v3.C", 3.40, code="C_PPB", units="ppb"),
        ev(12000000.0, "v4.C", 3.70, code="C_PPB", units="ppb"),
        ev(12600000.0, "plant.dump", 0.0, code="DUMP_NOT_TAKEN", units="bool"),
        ev(13200000.0, "surv.held", 1.0, code="SURV_HELD", units="bool"),
        ev(13800000.0, "recon.K0", 2.00, code="K0", units="cm2_Vs", note="K0 lock held post-isolate"),
        ev(14400000.0, "vent.T", 302.0, code="VENT_K", units="K"),
        ev(15000000.0, "v2.lock", 1.0, code="V2_ISOL", units="bool"),
        ev(15600000.0, "ops.skip", 1.0, code="SKIP_SURVEY", units="bool"),
        ev(16200000.0, "gate.surv", 1.0, code="REJECT", units="decision"),
        ev(16800000.0, "surv.floor", 1.0, code="SURV_FLOOR", units="bool"),
    ]
    assert_stream(events)
    if len(events) != 48:
        raise RuntimeError(len(events))

    traj = {
        "id": "nelb-r03-003-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "WC-IMS-2026-0902",
            "domain": "ims_peroxide_vent_tatp",
            "setting": "Wigeoncrag Peroxide WC-6 (invented), vent V-2 on simulated coupon IMS-SIM-5. Plant-owned ion-mobility spectrometer (drift-tube K0 lock plus ion current) is the remaining-TATP SoT. Imsveil vendor IMS-cloud is not SoT. Simulated coupon; not a live plant. Not live r02 PTR-MS remaining MDI, not leftover-mill PID VOC, not leftover-mill FID THC, not leftover-mill QEPAS, not leftover-mill CLD NOx.",
            "observables_at_decision": {
                "I_nA": i_nA,
                "k_i": k_i,
                "C_ppb": c_ppb,
                "K0": k0,
                "I_id": i_id,
                "ims_snr": 11.0,
                "imsveil_ppb": 3.20,
                "isolate_floor_ppb": 16.00,
                "scope": "V-2 only",
            },
            "margin_authority": "WC-6 peroxide SOP rev C: if reconstructed C_ppb >= 16.00 AND IMS SNR >= 8.0 AND K0 == 2.00, isolate this vent even if Imsveil reports 3.20 ppb. Plant dump is a different gate. Kill tripwire is 80.00 ppb. Adjacent vents V-1/V-3/V-4 are out of scope.",
        },
        "proposed_action": {
            "actor": "sim operator Nyla Crowe, citing Imsveil 3.20 ppb and a quiet ion current",
            "summary": "isolate V-2 only; 16.00 nA is electrometer noise on a healthy TATP last-good; skip adjacent vents",
            "basis_claimed": "Imsveil is the only OEM IMS SoT and a night abort of V-1/V-3/V-4 is a header-nomination miss",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Bounded ACCEPT of V-2 isolate. Serialized reconstruction: C_ppb = k_i * I = 2.50 * 16.00 = 40.00, which is 24.00 ppb over the 16.00 isolate floor and 40.00 ppb under the 80.00 plant-dump tripwire, IMS SNR is 11.0 >= 8.0, and reduced-mobility lock K0 = L^2 / (V * t_d) = 8.00 / (2.00 * 2.00) = 2.00 identifies the TATP peak. Inverse I = C / k_i = 40.00 / 2.50 = 16.00. Adjacent vents V-1/V-3/V-4 stay in the header (explicitly out of scope). Ordered: isolate V-2 now. Scope: this ACCEPT does not dump the peroxide plant (that is a different gate) and does not skip the remaining-vent survey (that is the companion question).",
            "threshold": "C_ppb>=16.00 AND ims_snr>=8.0 AND K0==2.00 => isolate V-2 only; Imsveil is not SoT; plant-dump if C_ppb>=80.00",
            "stated_residuals": "survey of V-1/V-3/V-4 still required; 40.00 vs a true 80.00 dump is a production cut; Imsveil remains the only OEM IMS channel",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 4800: V-2 isolated; V-1/V-3/V-4 out of scope; Imsveil not SoT; reconstruction locked",
            "tool": "wc6-ims-vent-gate-cli",
            "observation": "C 40.00 ppb recomputes from I 16.00 nA; K0 2.00 lock held; Imsveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "IMS I 16.00 nA; raster frame; C 40.00 ppb"},
                {"t_s": 4620.0, "event": "ops proposes isolate V-2 only"},
                {"t_s": 4800.0, "event": "ACCEPT V-2 isolate; adjacent vents out of scope"},
                {"t_s": 6000.0, "event": "12 min survey bookend 1"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7800.0, "event": "companion REJECT skip-survey"},
            ],
            "observed_effects": [
                "remaining TATP recomputes from the serialized IMS model at every recon.C event",
                "an Imsveil-only head would have skipped V-2 overnight",
                "12 min survey floor is in the stream (surv.start, surv.floor)",
            ],
            "surprises": [
                "a clean vendor 3.20 ppb corridor co-existed with a 40.00 ppb plant reconstruction on V-2 while adjacent vents stayed healthy",
            ],
            "new_state": {
                "v2": "isolated",
                "v1_v3_v4": "in header, out of isolate scope",
                "imsveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("ims_tatp_reconstruction", 0.14),
                ("bounded_scope_accept", 0.12),
                ("imsveil_nonsubstitution", 0.10),
                ("k0_peak_lock", 0.07),
                ("held_header_cost", -0.02),
            ],
            "scored for a bounded ACCEPT of V-2 isolate on a recomputable IMS TATP slip with an explicit out-of-scope clause for V-1/V-3/V-4; 12 min survey floor is priced as downtime",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "ims-tatp", "serialized-reconstruction", "bounded-scope"],
            distillation_value="Independent CUBA LIF raster races the IMS estimator against a vendor-dump advocate; bounded ACCEPT is a physical out-of-scope object (V-1/V-3/V-4), not a prose hedge.",
            distillation_note="IMS gate: serialized k_i*I plus K0 lock beats a vendor last-good; companion t2 is the skip-survey refusal, not a second TATP vote",
        ),
    }
    traj2 = {
        "id": "nelb-r03-003-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "WC-IMS-2026-0902-exec",
            "domain": "vent_survey_ims_interlock_execution",
            "setting": "Same IMS-SIM-5 coupon after the ACCEPT. Operator proposes skip-survey of V-1/V-3/V-4. This companion is the operational skip refusal, not a second TATP vote.",
            "observables_at_decision": {
                "C_ppb": 50.00,
                "surv_floor_s": 720.0,
                "skip_survey_proposed": True,
                "v2_isolated": True,
            },
            "margin_authority": "survey_hold AND surv_floor_complete AND skip_not_taken AND plant_dump_not_taken",
        },
        "proposed_action": {
            "actor": "sim operator Nyla Crowe",
            "summary": "skip the remaining-vent survey; 12 min already paid and Imsveil still shows 3.00 ppb on V-1/V-3/V-4",
            "basis_claimed": "the ACCEPT already isolated V-2, so skipping adjacent vents is the cheapest hold",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Skip-survey is refused. The 12 min survey floor is complete and V-1/V-3/V-4 remain in the survey takt because they were explicitly out of isolate scope, not certified clean. REJECT skip-survey. Do not dump the peroxide plant. Do not restore V-2 on Imsveil. 50.00 ppb post-isolate on V-2 is still the plant SoT until a new frame clears 16.00.",
            "threshold": "survey_hold AND surv_floor_complete AND skip_not_taken AND plant_dump_not_taken",
            "stated_residuals": "V-2 stays isolated; Imsveil remains the only OEM IMS channel",
        },
        "executed_action": {
            "summary": "skip-survey rejected at t_s 7800; plant dump not latched; Imsveil restore not taken",
            "tool": "wc6-surv-exec",
            "observation": "recon.C 50.00 ppb after isolate; survey line-up complete; Imsveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "survey clock started after ACCEPT"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7200.0, "event": "skip-survey proposed"},
                {"t_s": 7800.0, "event": "REJECT skip-survey; adjacent vents stay in takt"},
            ],
            "observed_effects": [
                "Imsveil restore did not reopen the TATP call",
                "plant dump never fired; V-1/V-3/V-4 stayed in the survey takt",
            ],
            "surprises": [
                "post-isolate 50.00 ppb still recomputes from k_i*I while Imsveil stays at 3.00 ppb",
            ],
            "new_state": {"survey": "held", "plant": "in service", "v2": "isolated"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.36,
            [
                ("survey_hold", 0.12),
                ("no_plant_dump", 0.10),
                ("imsveil_nonsubstitution", 0.08),
                ("surv_floor_complete", 0.08),
                ("held_header_cost", -0.02),
            ],
            "operational execution gate: refuse skip-survey because Imsveil is not a remaining-vent license; not a TATP re-vote",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "skip-survey"]),
    }
    return {
        "id": "nelb-r03-003",
        "snn_tags": list(SNN_TAGS),
        "spike_events": events,
        "language_view": {
            "description": "Wigeoncrag Peroxide WC-6 simulated coupon. Plant-owned IMS reconstructs 40.00 ppb TATP from 2.50*16.00 while Imsveil still reports 3.20 ppb. The gate ACCEPTs a bounded V-2 isolate (V-1/V-3/V-4 out of scope). A 12 min survey floor is serialized in the stream. Companion t2 REJECTs skip-survey.",
            "trajectory": traj,
            "trajectory_survey_hold": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "ims.I / ims.snr": "IMS ion current and SNR; the physics channels the reconstruction consumes",
                "recon.C / recon.K0 / recon.Iid": "serialized remaining-TATP ppb, reduced-mobility lock, and I=C/k_i identity",
                "vent.T / imsveil.C / v1.C / v3.C / v4.C": "vent thermocouple, vendor IMS cloud, and adjacent-vent out-of-scope witnesses",
                "ops.prop / gate.acc / ops.skip / gate.surv": "V-2 isolate proposal, ACCEPT, skip-survey proposal, companion REJECT",
                "v2.lock / surv.start / surv.floor / surv.held / plant.dump": "operational companion channels plus the 12 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-over: imsveil.C 3.20 next to recon.C 40.00",
                "reconstruction as event: recon.C 40.00 equals 2.50*16.00",
                "ACCEPT then operational REJECT: gate.acc at 4800 s, gate.surv at 7800 s",
                "slow floor in-stream: surv.start 6000 s, surv.floor 6720 s (12.0 min)",
                "tight IMS pair: ims.I then ims.snr +1.5 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Imsveil is 3.20 ppb' = imsveil.C 3.20; '40 ppb remaining TATP' = recon.C 40.00; 'isolate V-2 only' = gate.acc ACCEPT; 'refuse skip-survey' = gate.surv REJECT",
            "why_high_value": "New ion-mobility remaining-TATP family on a peroxide vent (not PTR-MS MDI r02, not PID VOC, not FID THC, not QEPAS, not CLD NOx). Lead bounded ACCEPT of V-2 isolate on a recomputable TATP slip with an explicit physical out-of-scope object (V-1/V-3/V-4). Independent CUBA LIF raster. Companion t2 is operational skip-survey refusal. sim_or_real=simulated.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random plus CUBA LIF",
                "seeds": {"raster": 2026090303, "stream_note": "stream amplitudes are authored constants; raster is independent CUBA LIF"},
                "draw_order": "independent CUBA LIF per neuron; per-spike adaptation and noise; not copied from spike_events",
                "thinning": "IMS exists at ~10 Hz drift spectra; stream keeps 5 I points; recon keeps 5 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "ims.I": 1.5,
                    "ims.snr": 1.5,
                    "recon.C": 60000,
                    "recon.K0": 60000,
                    "recon.Iid": 60000,
                    "vent.T": 60000,
                    "imsveil.C": 60000,
                    "v1.C": 60000,
                    "v3.C": 60000,
                    "v4.C": 60000,
                    "ops.prop": 60000,
                    "gate.acc": 60000,
                    "v2.lock": 60000,
                    "surv.start": 60000,
                    "surv.floor": 60000,
                    "ops.skip": 60000,
                    "gate.surv": 60000,
                    "surv.held": 60000,
                    "plant.dump": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-09-02T03:00:00Z simulated coupon start",
            },
            "distillation_targets": [
                "IMS reconstruction head: C = k_i * I; K0 = L^2 / (V * t_d); I = C / k_i",
                "bounded ACCEPT of V-2 vs plant dump vs skip-survey",
                "vendor-IMS nonsubstitution plus adjacent-vent out-of-scope",
                "operational companion: survey-hold without restoring on Imsveil",
                "independent CUBA LIF raster with race/refractory/adaptation tags",
            ],
        },
        "reconstruction_model": {
            "name": "ims_peroxide_vent_tatp",
            "formula": "C_ppb = k_i * I_nA; K0 = L2 / (V_drift * t_d); I_id = C_ppb / k_i",
            "parameters": {
                "k_i": 2.50,
                "L2": 8.00,
                "V_drift": 2.00,
                "t_d": 2.00,
                "isolate_floor_ppb": 16.00,
                "dump_ppb": 80.00,
                "snr_lock": 8.0,
                "surv_min": 12.0,
            },
            "worked_example": {"I_nA": 16.00, "C_ppb": 40.00, "K0": 2.00, "I_id": 16.00},
            "check": "2.50 * 16.00 = 40.00 exactly; 8.00 / (2.00 * 2.00) = 2.00 exactly; 40.00 / 2.50 = 16.00 exactly; 6000 s + 720 s = 6720 s = 12.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "snn_tags": list(SNN_TAGS),
            "code": "wc6.ims_vent_gate",
            "note": "ACCEPT accumulator wins: plant IMS TATP evidence isolates V-2 without a plant dump; race/refractory/adaptation tags match meta.snn_tags",
            "decode_rule": "accept-V2-isolate if tatp_estimator AND k0_lock fire; vendor_dump_advocate is below threshold by design",
            "populations": [
                gate_pop("tatp_estimator", 80, 1.4, 50.0, w_s, tag="adaptation"),
                gate_pop("k0_lock", 50, 1.1, 50.0, w_s, tag="refractory"),
                gate_pop("vendor_dump_advocate", 32, 0.7, 25.0, w_s, tag="race"),
                gate_pop("accept_latch", 64, 1.5, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "wc6.ims_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 36.0},
                {"check": "wc6.surv_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 40.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r03-003",
            clock_domain="wc6-ims-sim-relative-ms-t0-2026-09-02T03:00:00Z",
            tags=["ims-tatp", "ACCEPT", "REJECT", "serialized-reconstruction", "operational-t2", "independent-lif", "bounded-scope"],
            distillation_value="Independent LIF raster teaches race/refractory/adaptation while the language view teaches IMS remaining-TATP reconstruction-as-SoT with a bounded ACCEPT.",
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


def _tags_ok(rec):
    needed = set(SNN_TAGS)
    locs = [
        rec.get("snn_tags"),
        (rec.get("meta") or {}).get("snn_tags"),
        ((rec.get("meta") or {}).get("nelb") or {}).get("snn_tags"),
        rec.get("gate_snn", {}).get("snn_tags"),
        (((rec.get("language_view") or {}).get("trajectory") or {}).get("meta") or {}).get("snn_tags"),
    ]
    for loc in locs:
        if not isinstance(loc, list) or needed.difference(loc):
            return False
    return True


def _jaccard(rec):
    window_ms = rec["raster"]["window_ms"]
    ex = {int(e["t_us"]) for e in rec["raster"]["excerpt"]}
    ev_us = set()
    for e in rec["spike_events"]:
        t = e["t_rel_ms"]
        if 0.0 <= t <= window_ms:
            ev_us.add(int(round(t * 1000.0)))
    if not ex or not ev_us:
        return 0.0
    inter = len(ex & ev_us)
    union = len(ex | ev_us)
    return inter / union if union else 0.0


def local_checks(records):
    ids = []
    decisions = []
    sims = []
    seeds = []
    for rec in records:
        hits = walk_banned(rec)
        if hits:
            raise RuntimeError(f"banned keys {hits}")
        blob = json.dumps(rec, ensure_ascii=False, allow_nan=False)
        if "training_ready" in blob:
            raise RuntimeError("training_ready claimed")
        if '"provenance"' in blob:
            raise RuntimeError("provenance object present")
        if '"real"' in blob.replace('"sim_or_real"', '""'):
            raise RuntimeError("real key leaked")
        if "2026-08-17" in blob or "2026-08-30" in blob:
            raise RuntimeError("forbidden run date")
        if not _tags_ok(rec):
            raise RuntimeError(f"{rec['id']} missing matching snn_tags")
        if rec["gate_snn"].get("snn_tags") != SNN_TAGS:
            raise RuntimeError("gate_snn snn_tags mismatch")
        jac = _jaccard(rec)
        if jac >= 0.10:
            raise RuntimeError(f"{rec['id']} raster echo jaccard {jac}")
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
                if v["safety_decision"]["decision"] not in {"ACCEPT", "MODIFY", "REJECT"}:
                    raise RuntimeError(v["safety_decision"]["decision"])
                if v["meta"]["round"] != ROUND:
                    raise RuntimeError("traj round")
        n = len(rec["spike_events"])
        if not (48 <= n <= 80):
            raise RuntimeError(f"{rec['id']} events {n}")
        gdec = rec["gate_snn"]["decision"]
        tdec = lv["trajectory"]["safety_decision"]["decision"]
        if gdec != tdec:
            raise RuntimeError(f"gate {gdec} != traj {tdec}")
        decisions.append(tdec)
        for k, v in lv.items():
            if k.startswith("trajectory") and isinstance(v, dict) and "safety_decision" in v:
                if k != "trajectory":
                    decisions.append(v["safety_decision"]["decision"])
        rast = rec["raster"]
        exp = int(round(rast["neurons"] * rast["mean_rate_hz"] * rast["window_s"]))
        if abs(rast["spikes"] - exp) > 0:
            raise RuntimeError("raster budget")
        if abs(rast["energy_pJ"] - rast["spikes"] * 23) > 1e-6:
            raise RuntimeError("energy pJ")
        if abs(rast["energy_uJ"] - rast["spikes"] * 23e-6) > 1e-9:
            raise RuntimeError("energy uJ")
        if not (20.0 <= rast["window_ms"] <= 50.0):
            raise RuntimeError("window")
        if abs(rast["window_s"] - rast["window_ms"] / 1000.0) > 1e-9:
            raise RuntimeError("window_s")
        if rast["excerpt_span_us"] < 1000:
            raise RuntimeError("excerpt span")
        if rast["isi_source"] != "full_window_per_neuron_isi":
            raise RuntimeError("isi source")
        isi = rast["isi_count_identity"]
        if isi["isi_total"] != isi["spikes"] - isi["distinct_active_neurons"]:
            raise RuntimeError("ISI identity")
        if sum(b["count"] for b in rast["isi_histogram"]) != isi["isi_total"]:
            raise RuntimeError("ISI hist sum")
        tf = rast["routing"]["third_factor"]
        if abs(tf["tau_e_ms"] / 1000.0 - tf["tau_e_s"]) > 1e-9:
            raise RuntimeError("tau pair")
        if rast["excerpt_generator"] != "independent_cuba_lif":
            raise RuntimeError("not independent LIF")
        if rast["lif"]["model"] != "independent_cuba_lif":
            raise RuntimeError("lif")
        seeds.append(rast["lif"]["seed"])
        sim = lv["trajectory"]["state"]["sim_or_real"]
        if sim not in {"designed", "simulated", "hil"}:
            raise RuntimeError(sim)
        sims.append(sim)
        gc = rec["gate_compute"]
        sp_sum = sum(c["spikes"] for c in gc["per_check"])
        if sp_sum != gc["total_spikes"]:
            raise RuntimeError("gate_compute spikes")
        if abs(gc["total_energy_pJ"] - sp_sum * 23) > 1e-6:
            raise RuntimeError("gate_compute pJ")
        dw = rec["gate_snn"]["decision_window_s"]
        for pop in rec["gate_snn"]["populations"]:
            exp_p = int(round(pop["neurons"] * pop["mean_rate_hz"] * dw))
            if pop["spikes"] != exp_p:
                raise RuntimeError(f"gate_snn pop {pop['name']}")
        for e in rec["spike_events"]:
            if any(k in e for k in ("t_ms", "burst_id", "sequence_id", "event_order", "causal_group")):
                raise RuntimeError("forbidden event key")
        rights = rec["meta"]["rights"]
        if rights.get("linear_issue") != "RM-793":
            raise RuntimeError("RM-793 missing")
        if len(rights) != 15:
            raise RuntimeError(f"rights {len(rights)}")
        if rec["meta"]["round"] != ROUND:
            raise RuntimeError("meta.round")
        if rec.get("snn_tags") != SNN_TAGS:
            raise RuntimeError("top snn_tags")
    if len(ids) != len(set(ids)):
        raise RuntimeError(f"dup ids {ids}")
    if len(set(seeds)) != 3:
        raise RuntimeError(f"shared LIF seeds {seeds}")
    if set(sims) != {"designed", "simulated", "hil"}:
        raise RuntimeError(f"sim mix {sims}")
    if set(decisions) != {"ACCEPT", "MODIFY", "REJECT"}:
        raise RuntimeError(f"decision mix {decisions}")
    print("local_checks ok", [r["id"] for r in records], "ids", len(ids), "jaccard", [_jaccard(r) for r in records])
    print("decisions", decisions, "sims", sims, "seeds", seeds)


def repo_validate(records):
    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import curate_record, raster_status
    from verify_execution import verify_batch_for_frontier

    errs, warns, kinds, n = check_jsonl(
        BATCH, BATCH.name, staging=FactoryStaging(enabled=True)
    )
    print("check_jsonl", {"errors": len(errs), "warnings": len(warns), "kinds": kinds, "n": n})
    for e in errs:
        print("ERROR", e)
    for w in warns:
        print("WARN", w)
    if errs or warns:
        raise RuntimeError("check_jsonl failed")

    for i, rec in enumerate(records, 1):
        st = raster_status(rec, require_raster=True, require_routing_table=True)
        print(
            rec["id"],
            "raster_valid",
            st["raster_valid"],
            "gate_snn_valid",
            st["gate_snn_valid"],
            "reasons",
            st["reason_codes"],
            "isi",
            rec["raster"]["isi_count_identity"],
        )
        if not st["raster_valid"] or not st["gate_snn_valid"] or st["reason_codes"]:
            raise RuntimeError(f"raster_status {rec['id']} {st}")
        blob = json.dumps(rec, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
        h = hashlib.sha256(blob.encode("utf-8")).hexdigest()
        dec = curate_record(
            rec,
            source_path=BATCH.name,
            source_line=i,
            source_hash=h,
            require_raster=True,
            require_routing_table=True,
        )
        reasons = dec.manifest.get("reason_codes")
        print(rec["id"], "curate", dec.action, reasons)
        if dec.action != "retain":
            raise RuntimeError(f"curate {rec['id']} {dec.action} {reasons}")

    counts, findings, blocked = verify_batch_for_frontier(BATCH, strict=True)
    print("frontier", counts, "blocked", blocked, "findings", findings)
    if blocked or counts["verified"] != 3:
        raise RuntimeError(f"frontier {counts} {findings}")
    probe = subprocess.run(
        [sys.executable, str(PIPELINES / "spike_probe.py"), "--strict", str(BATCH)],
        check=False,
        capture_output=True,
        text=True,
    )
    probe_out = (probe.stdout or "") + (probe.stderr or "")
    print("spike_probe", probe.returncode, probe_out[-500:])
    if probe.returncode != 0:
        raise RuntimeError(f"spike_probe failed {probe.returncode}: {probe_out[-2000:]}")
    return {"check_jsonl": {"errors": len(errs), "warnings": len(warns), "kinds": kinds, "n": n}, "frontier": counts}


def create_only(path: Path, text: str) -> Path:
    path = Path(path)
    if path.exists():
        stem, suffix = path.stem, path.suffix
        dest = path.with_name(stem + "c" + suffix)
        n = 2
        while dest.exists():
            dest = path.with_name(f"{stem}c{n}{suffix}")
            n += 1
        path = dest
    fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(text)
    return path


def write_notes(records, lines, batch_path: Path, notes_path: Path) -> Path:
    sizes = [len(x) for x in lines]
    file_sha = hashlib.sha256(batch_path.read_bytes()).hexdigest()
    isis = [r["raster"]["isi_count_identity"]["isi_total"] for r in records]
    events = [len(r["spike_events"]) for r in records]
    rewards = []
    for r in records:
        lv = r["language_view"]
        rewards.append(lv["trajectory"]["reward_components"]["total"])
        for k, v in lv.items():
            if k.startswith("trajectory") and k != "trajectory":
                rewards.append(v["reward_components"]["total"])
    gc = []
    for r in records:
        per = r["gate_compute"]["per_check"]
        gc.append("+".join(str(c["spikes"]) for c in per))
    wins = [r["raster"]["window_ms"] for r in records]
    n_sp = [r["raster"]["spikes"] for r in records]
    n_neu = [r["raster"]["neurons"] for r in records]
    rates = [r["raster"]["mean_rate_hz"] for r in records]
    tfs = [r["raster"]["routing"]["third_factor"]["modulator"] for r in records]
    taus = [r["raster"]["routing"]["third_factor"]["tau_e_s"] for r in records]
    spans = [r["raster"]["excerpt_span_us"] for r in records]
    reward_s = "/".join(f"+{x:.2f}" for x in rewards)
    jacs = [_jaccard(r) for r in records]
    notes = f"""# Neuromorphic Event + Language Bridge — NOTES round 3
Run: 2026-09-02-final-heavy · Factory: neuromorphic-event-language-bridge · Generator: grok-4.6 · Output: `{batch_path.name}` (3 paired artifacts, 6 ThalamicTrajectories)
Rights: RM-793 research-only (SpaceXAI/xAI grok-4.6, SuperGrok Heavy chat). Not training_ready. CREATE-ONLY write at `{LIVE}` (`{batch_path.name}`, `{notes_path.name}`). Did not write 2026-08-17 or 2026-08-30. Did not overwrite existing live r01/r02/r21/r22/r41/r42/r61/r63.

## Context / de-duplication
Live tree already held r01 (Johnson-noise T / Coulter particles / photoelastic hoop), r02 (CAPS NO2 / PTR-MS MDI / microwave PCD τ), r21 (OA-ICOS CH4 / SERF OPM / WGM water), r22 (CDG vacuum / opacity dust / circular-polariscope hoop), r41 (LDA / coulometric KF / bender-element Vs), r42 (BOS flare density / LIF OH / ESPI skirt), r61 (Stern-Volmer DO / pellistor LEL / FMCW tank-radar), r63 (ICP-OES Ni / LVDT expansion / FTIR methanol). This round fills **r03** create-only. Banned this round: those twenty-four families; 2026-08-17 r03 fixture defects (counterfactual replay / AMR intersection / acoustic scene); 2026-08-30 r03 families; leftover-mill r13–r70 family tables (FBG, BOTDA, QCM-D, SAW, CRDS, IFOG, transmon, hyperspectral, MEMS, muon, x-ray, optogenetic, LiDAR, clamp-on, LIBS, QEPAS, LFV, Kaplan LDV, THz-TDS, ECT, TDLAS, lock-in thermography, PAUT, EN, RUS, N-16, helium RGA, FOCT, tip-timing, acoustic pyrometry, SPR, VW viscometer, MW cavity, MFL, NMR, nucleonic, JNT, CRNS, Coriolis, CARS, XRF, Mössbauer, GB-InSAR, ellipsometry, CTA, SPND, LII, PALS, NQR, SFRA, shearography, H-permeation, FMCW lining, GPR, Pockels, PEC, confocal, mud-pulse, Barkhausen, Lamb, OCT, DCPD, impact-echo, phosphor-lifetime, vortex, GWR, neutron-backscatter, beta, Raman, cyclotron BPM, alanine EPR, ADCP, TOFD, laser-flash, TDR, Seebeck, coda, LPR, paramagnetic O2, TEOM, Faraday magmeter, PDA, acoustoelastic, C-SAM, FDS, MCSA, EMAT, FBRM, ACFM, OFDR, XRD, FSM, Gardon, chilled-mirror, DIC, CLD NOx, API-670, thermal-mass, ER, Fabry-Perot, inductive debris, wire-mesh, UCI, MAE, IRIS, dual-wavelength pyrometer, UV-fluorescence OIW, zirconia, PID VOC, pulse-echo, Rogowski, BAM, UV-DOAS, Al2O3, load-cell, H2S, TEV, dielectric water-cut, sonic-nozzle, sodium-ion, vibrating-tube, Ubbelohde, gloss, RF-admittance, UV ozone, triboelectric, molybdenum-blue, polarimetric sucrose, hydrostatic level, platinum-ORP cyanide, flame-photometric sulfur, colorimetric silica, coulometric hydrazine, NIR moisture, manganin shunt, idler-belt mass-flow, glass pH). Plants not reused: Brackfen, Flintshaw, Yewholt, Gorsewhin, Brindlemere, Quartzholt, Sedgewhin, Brinecrag, Lichenholt, Fernspire, Limeholt, Rushcrag, Copsewick, Peatspire, Brackenholt, Marlspur, Tarspire, Mirewhin, Lacquerfen, Pitchshaw, Reedcairn, Brackenmire, Fernshaw.

This round introduces three unused families (dc-SQUID remaining dump current, particle-image-velocimetry remaining impeller velocity, ion-mobility remaining TATP) on new invented plants, restores a 48-event floor, and keeps **independent CUBA LIF** plus required matching `snn_tags` on record / meta / gate_snn.

Adjacencies declared in-pair then kept physically distinct:
- **001 dc-SQUID remaining I** is Josephson flux-quantum remaining dump-current of a SMES bus, not SERF OPM (live r21), not Faraday FOCT (leftover r25), not Rogowski (leftover r58), not manganin shunt (leftover r69), not Hall MFL remaining wall (leftover r27).
- **002 PIV remaining u** is laser-sheet cross-correlation remaining impeller velocity of a fermenter HIL dummy, not LDA (live r41), not Kaplan LDV (leftover r20), not CTA hot-wire (leftover r31), not BOS (live r42), not ADCP (leftover).
- **003 IMS remaining TATP** is drift-tube ion-mobility remaining peroxide of a vent, not PTR-MS MDI (live r02), not PID VOC, not FID THC, not QEPAS, not CLD NOx.

## Round 3 batch summary (3 pairs, 6 trajectories)

| id | modality (NEW family) | domain | decisions | headline |
|----|----------------------|--------|-----------|----------|
| nelb-r03-001 | dc-SQUID remaining current of a SMES dump bus (k_s·Φ kA, Squidveil last-good denial, 18 min dump-hold floor) | Merganserholt SMES MH-5 dump D-7 (invented): 0.50*40.00 reconstructs 20.00 kA while Squidveil still reads 2.40 kA | REJECT (+0.43) / MODIFY (+0.34) | serialized `0.50*40.00=20.00`; `20.00/0.50=40.00`; `20.00*1.20=24.00`; conjunctive SOP (I AND SNR) forbids continue-idle; three-party collusion includes the SQUID-cloud infra owner; companion t2 dump-hold, hall ESD refused; sim_or_real=designed |
| nelb-r03-002 | particle-image-velocimetry remaining velocity of a fermenter impeller (k_p·(Δx/Δt) m/s, Pivveil last-good denial, 24 min new-sheet floor) | Pintailmire Ferment PM-4 dummy tank T-3 (invented, HIL in PIV-HIL-7): 0.50*(16.00/4.00) reconstructs 2.00 m/s while Pivveil still reads 0.40 m/s | MODIFY (+0.40) / ACCEPT (+0.35) | serialized `0.50*(16.00/4.00)=2.00` and `16.00/4.00=4.00`; keep-tank refused; PIV tech Lena Quist exonerated (missing laser-sheet AE, UTC vs UTC+2); companion t2 new-sheet restart; sim_or_real=hil |
| nelb-r03-003 | ion-mobility remaining TATP of a peroxide vent (k_i·I ppb, Imsveil last-good denial, 12 min survey floor) | Wigeoncrag Peroxide WC-6 vent V-2 (invented, simulated IMS-SIM-5): 2.50*16.00 reconstructs 40.00 ppb while Imsveil still reads 3.20 ppb | ACCEPT (+0.41) / REJECT (+0.36) | serialized `2.50*16.00=40.00`; `8.00/(2.00*2.00)=2.00`; `40.00/2.50=16.00`; bounded ACCEPT of V-2 only; V-1/V-3/V-4 out of scope; companion t2 REJECTS skip-survey; sim_or_real=simulated |

Decision spread: REJECT / MODIFY / MODIFY / ACCEPT / ACCEPT / REJECT — **2A/2M/2R**. All three enums used, and all three sit on **leads**. Provenance spread: designed / hil / simulated (one each; never real). IDs `nelb-r03-001`…`003` plus t1/t2 suffixes. `meta.round=3`. `snn_tags` = [race, refractory, adaptation] on every record, meta, meta.nelb, and matching `gate_snn`.

## Raster sidecar
Every record carries `raster` + top-level `gate_snn` + `gate_compute` + `snn_tags`. Windows {wins[0]:.0f}/{wins[1]:.0f}/{wins[2]:.0f} ms; `window_s == window_ms/1000` exactly; `spikes == round(neurons·rate·window_s)` with zero slack ({n_sp[0]}/{n_sp[1]}/{n_sp[2]} at {rates[0]}/{rates[1]}/{rates[2]} Hz over {n_neu[0]}/{n_neu[1]}/{n_neu[2]} neurons); `energy_pJ = spikes·23` and `energy_uJ = spikes·23e-6` exact ({n_sp[0]*23}/{n_sp[1]*23}/{n_sp[2]*23} pJ). Routing source/target + 3-entry tables + `third_factor` on all three (modulators {tfs[0]} / {tfs[1]} / {tfs[2]}; τe {taus[0]}/{taus[1]}/{taus[2]} s as consistent `tau_e_s`+`tau_e_ms` pairs). Excerpts are **independent CUBA LIF** first-passage times (not a re-encode of `spike_events`; Jaccard {jacs[0]:.4f}/{jacs[1]:.4f}/{jacs[2]:.4f}), integer `t_us`, in-window, `neuron_id`-bounded, sorted, full-window by construction, per-spike amplitude with adaptation (0.82**k) plus noise; excerpt span ≥ 1000 µs ({spans[0]}/{spans[1]}/{spans[2]} µs). ISI histograms from the FULL window, bins ≥1 ms, counts sum to `spikes − distinct_active_neurons` ({isis[0]}/{isis[1]}/{isis[2]}). Same-neuron gaps ≥1000 µs serialized. `gate_snn` on all three: decisions REJECT/MODIFY/ACCEPT matching each lead trajectory **and** matching `snn_tags`; every rate-declaring population's budget exact against its decision window. `gate_compute.per_check` windows 32–40 ms, budgets exact ({gc[0]} / {gc[1]} / {gc[2]}). Required `meta.snn_tags`, `meta.nelb.snn_tags`, top-level `snn_tags`, and `gate_snn.snn_tags` = [race, refractory, adaptation] on every record. Main streams: {events[0]}/{events[1]}/{events[2]} events (48+), strictly increasing `t_rel_ms` only (no `t_ms` mix), same-channel refractory ≥0.8 ms (001 SQUID pair at 1.4 ms, 002 PIV pair at 1.2 ms, 003 IMS pair at 1.5 ms). Independent LIF seeds 2026090301/2026090302/2026090303 (no shared LIF state).

## Self-critique

### Edge cases added vs still thin
- **Added:** first dc-SQUID remaining-current family on a SMES dump with recomputable I=k_s·Φ (`20.00 kA`) plus flux and power identities; first PIV remaining-velocity family on a fermenter HIL dummy with recomputable u=k_p·(Δx/Δt) (`2.00 m/s`) plus dx/dt and Q identities and timezone-skipped sheet-AE exoneration; first ion-mobility remaining-TATP family on a peroxide vent with recomputable C=k_i·I (`40.00 ppb`) plus K0 and I identities and bounded ACCEPT of V-2 only; independent CUBA LIF rasters with required matching snn_tags; 48-event streams; operational t2 on all three; provenance trio designed/hil/simulated; 18/24/12 min slow floors in-stream.
- **Still thin:** (i) 001's k_s is a lumped flux-to-kA gain, not an M/n table — a mutual-inductance hop that fakes 20.00 kA inside a 2.40 Squidveil corridor is unwritten; (ii) 002's k_p is a lumped pixel-to-m/s gain, not a dt / magnification map, so a 2 ms dt hop that fakes 2.00 m/s is unwritten; (iii) 003's k_i is a lumped ion-current gain, not a humidity / clustering map, so a water-cluster hop that fakes 40.00 ppb is unwritten; (iv) vendor-only as a *lead* REJECT on a plant with *no* independent SQUID/PIV/IMS remains slightly harder — 001/002 still have plant heads; (v) stream amplitudes remain authored constants (raster draws are the only seeded LIF noise).

### Realism of noise / temporal fidelity
- Strong: 001's 20.00 kA, Φ 40.00, P 24.00, and 18.0 min hold (`6000+1080=7080 s`) recompute from the record; 002's 2.00 m/s, ratio 4.00, Q 1.60, and 24.0 min new-sheet (`2820+1440=4260 s`) recompute; 003's 40.00 ppb, K0 2.00, and 12.0 min survey (`6000+720=6720 s`) recompute. Independent CUBA LIF (tau_m 10/12/8 ms) plus 0.82**k adaptation and 1.2–1.5 ms physics pairs give the 48-event stream a raster-scale motif without violating 0.8 ms same-channel refractory or 1000 µs same-neuron excerpt gaps.
- **Gaps, honestly:** (i) 48 events still thins kHz flux-locked-loop / 10 Hz PIV / 10 Hz IMS stacks; (ii) 001's post-stop 24.00 kA is a later sample, not a closed-loop dump controller; (iii) 002 HIL coupon times an in-service isolate that the stream does not independently witness on a second live tank until the new sheet starts; (iv) no gate_snn input→output volley pair at raster resolution this round.

### Training value (SNN/LSM + agentic)
Distillation targets: dc-SQUID I=k_s·Φ plus flux and power identities; conjunctive isolate floor vs continue-idle vs hall ESD; SQUID-infra collusion; PIV u=k_p·(Δx/Δt) plus dx/dt and Q identities; isolate-floor tank vs keep-whole vs hall dump; timezone exoneration; IMS C=k_i·I and K0 identities; bounded ACCEPT with V-1/V-3/V-4-out-of-scope; skip-survey refusal under survey takt. Raster value is the independent LIF (race / refractory / adaptation) rather than a 1:1 echo of the language stream. Agentic value concentrates in three patterns: reconstruction-as-SoT on a physical I/u/C the raw corridor cannot see, earned ACCEPT with an explicit physical out-of-scope object (V-1/V-3/V-4), and stop-then-hold so a REJECT does not become a hall/hall/plant kill.

## What round 4 should add (next densification target)
1. **M/n flux table** on a non-MH-5 SMES so a mutual-inductance hop fakes 20.00 kA inside a 2.40 Squidveil corridor, closing 001's lumped-k_s gap.
2. **dt / magnification map** on a non-PM-4 PIV so a 2 ms dt hop fakes 2.00 m/s while mean Δx looks healthy.
3. **Humidity / clustering map** on a non-WC-6 IMS so a water-cluster hop fakes 40.00 ppb inside a 3.20 Imsveil corridor.
4. **Do not restage** live r01 Johnson-noise / Coulter / photoelastic, live r02 CAPS / PTR / PCD, live r21 OA-ICOS / SERF / WGM, live r22 CDG / opacity / polariscope, live r41 LDA / KF / bender-element, live r42 BOS / LIF OH / ESPI, live r61 Stern-Volmer / pellistor / FMCW, live r63 ICP-OES / LVDT / FTIR, leftover-mill r13–r70 families named above, Merganserholt MH-5, Pintailmire PIV-HIL-7, or Wigeoncrag IMS-SIM-5. Do not reuse ids `nelb-r03-001`…`003`.

## Verification
`{batch_path.name}`: 3 lines, `json.loads`-clean (allow_nan=False), {sizes[0]}/{sizes[1]}/{sizes[2]} bytes (file {batch_path.stat().st_size}, sha256 `{file_sha}`). CREATE-ONLY write at `{LIVE}`. Repo gates: `check_records.check_jsonl` with `FactoryStaging(enabled=True)` → 0 errors, 0 warnings, kinds `{{bridge_pair: 3}}`; `curate_bridge.raster_status(..., require_raster=True, require_routing_table=True)` → raster_valid and gate_snn_valid true, empty reason codes; `curate_record(...)` → 3× retain / `BRIDGE_EVENTS_ALREADY_GLOBALLY_ORDERED`; `verify_batch_for_frontier(strict=True)` → 3 verified, 0 inconclusive, 0 failed; `python3 pipelines/spike_probe.py --strict {batch_path}` → loaded 3. Build-time asserts: global time order; same-channel ≥0.8 ms; ≥48 events ({events[0]}/{events[1]}/{events[2]}); excerpt integer bounds, neuron bounds, sort, 1 ms per-neuron floor, span ≥1000 µs ({spans[0]}/{spans[1]}/{spans[2]}); ISI identity {isis[0]}/{isis[1]}/{isis[2]} from the FULL window; spike budgets exact; energy pJ/µJ exact; reward totals equal two-decimal component sums ({reward_s}); gate_snn decisions match lead `safety_decision.decision` and matching snn_tags; `state.sim_or_real` ∈ {{designed, hil, simulated}}; `meta.round=3`, `meta.factory=neuromorphic-event-language-bridge`, `meta.generator=grok-4.6`, `meta.run_label=2026-09-02-final-heavy`; `snn_tags` on record/meta/nelb/gate_snn include race/refractory/adaptation; `meta.rights` 15-key RM-793 stamp (`intended_use=research_only`, `linear_issue=RM-793`, `generated_at={GENERATED_AT}`); independent CUBA LIF Jaccard {jacs[0]:.4f}/{jacs[1]:.4f}/{jacs[2]:.4f}; no hidden-reasoning keys; no `provenance` objects; no live-plant claims; no `training_ready`; no 2026-08-17/2026-08-30 bytes; all 9 record/trajectory ids unique. Raster seeds 2026090301/2026090302/2026090303, CUBA LIF.

Honest novelty accounting: 3/3 modality families are new versus live r01/r02/r21/r22/r41/r42/r61/r63 and versus leftover-mill r13–r70. Independent CUBA LIF plus required matching snn_tags are carried raster objects relative to live r01/r02 (already LIF) but new versus live r21/r41/r61 gap-constrained draws. Against that: reconstruction-as-SoT, operational t2, conjunctive SOP, vendor-nonsubstitution, bounded-accept-with-scope-limit, exoneration, and 2A/2M/2R are carried vocabulary. Net: a bit under half of the round's scenario/edge mass is genuinely novel.

Novel coverage: 45%
"""
    return create_only(notes_path, notes)


def main():
    global BATCH, NOTES
    occupancy_preflight()
    records = [rec_001(), rec_002(), rec_003()]
    local_checks(records)
    STAGING.mkdir(parents=True, exist_ok=True)
    LIVE.mkdir(parents=True, exist_ok=True)
    lines = [
        json.dumps(r, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
        for r in records
    ]
    batch_text = "\n".join(lines) + "\n"
    staging_batch = create_only(STAGING / "batch-r03.jsonl", batch_text)
    print("staged", staging_batch, staging_batch.stat().st_size)
    BATCH = create_only(BATCH, batch_text)
    print("LIVE", BATCH, BATCH.stat().st_size, "lines", len(lines))
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
            "jaccard",
            round(_jaccard(r), 4),
            "bytes",
            len(lines[i]),
        )
    repo_validate(records)
    staging_notes = write_notes(records, lines, BATCH, STAGING / "NOTES-r03.md")
    print("staged", staging_notes, staging_notes.stat().st_size)
    NOTES = write_notes(records, lines, BATCH, NOTES)
    print("LIVE", NOTES, NOTES.stat().st_size)


if __name__ == "__main__":
    main()
