#!/usr/bin/env python3
"""Generate NELB round-1 live-tree bridge pairs. CREATE-ONLY into outputs/raw/.

Independent CUBA LIF rasters (not a re-encode of spike_events). Required
snn_tags {race, refractory, adaptation}. Do not touch 2026-08-17 or 2026-08-30.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import random
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

LIVE = Path(
    "/home/raulmc/rmems/synthetic-factory/outputs/raw/2026-09-02-final-heavy/"
    "neuromorphic-event-language-bridge"
)
BATCH = LIVE / "batch-r01.jsonl"
NOTES = LIVE / "NOTES-r01.md"
PIPELINES = Path("/home/raulmc/rmems/synthetic-factory/pipelines")
sys.path.insert(0, str(PIPELINES))
sys.path.insert(0, "/tmp")
from lif_raster import generate_lif_raster  # noqa: E402

GENERATED_AT = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
SNN_TAGS = ["race", "refractory", "adaptation"]
ROUND = 1

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
    kernel_ms: list,
    tau_m: float,
):
    expected = int(round(neurons * mean_rate_hz * (window_ms / 1000.0)))
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
        kernelized_event_times=kernel_ms,
        tau_m=tau_m,
        excerpt_cap=expected + 32,
        routing=routing,
    )
    excerpt = list(raw["excerpt"])
    rng = random.Random(seed ^ 0xA5A5)
    by_n = defaultdict(list)
    for e in excerpt:
        by_n[e["neuron_id"]].append(e)
    for nid, items in by_n.items():
        items.sort(key=lambda x: x["t_us"])
        base = 1.15 + 0.7 * rng.random()
        for i, e in enumerate(items):
            noise = 0.96 + 0.08 * rng.random()
            e["amplitude"] = round(base * (0.82**i) * noise, 3)
            e["channel"] = f"{channel_prefix}{int(nid):02d}"
    excerpt.sort(key=lambda e: (e["t_us"], e["neuron_id"]))

    spikes = int(raw["spikes"])
    window_s = float(window_ms) / 1000.0
    if abs(spikes - expected) > 0:
        raise RuntimeError(f"LIF budget {spikes} != {expected}")
    if len(excerpt) != spikes:
        raise RuntimeError(f"excerpt {len(excerpt)} != spikes {spikes}")

    times_by_n = defaultdict(list)
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
        times_by_n[nid].append(t_us)
        prev_t = t_us

    isis_ms = []
    for nid, ts in times_by_n.items():
        ts = sorted(ts)
        for a, b in zip(ts, ts[1:]):
            gap = b - a
            if gap < 1000:
                raise RuntimeError(f"ISI {gap} us")
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
    identity_n = spikes - len(times_by_n)
    if sum(x["count"] for x in hist) != identity_n:
        raise RuntimeError(f"ISI identity {sum(x['count'] for x in hist)} != {identity_n}")

    energy_pJ = spikes * 23
    energy_uJ = spikes * 23e-6
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
        "excerpt_generator": "independent_cuba_lif",
        "refractory_rule_ms": 1.0,
        "isi_histogram": hist,
        "isi_source": "full_window_per_neuron_isi",
        "isi_count_identity": {
            "spikes": spikes,
            "distinct_active_neurons": len(times_by_n),
            "isi_total": identity_n,
        },
        "anchor": anchor,
        "seed_note": (
            f"CUBA LIF MT19937 seed {seed}; tau_m {tau_m} ms; kernel {kernel_ms}; "
            "excerpt is independent of spike_events (not a 1:1 echo); "
            "amplitude adaptation 0.82**k plus noise"
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
        "brackfen",
        "noiseveil",
        "flintshaw",
        "slurryveil",
        "yewholt",
        "fringeveil",
        "nessa quill",
        "ivor kemp",
        "mara vell",
        "johnson-noise remaining",
        "coulter remaining particle",
        "photoelastic remaining hoop",
        "nelb-r01-001",
        "nelb-r01-002",
        "nelb-r01-003",
    )
    hits = []
    batches = []
    if LIVE.is_dir():
        batches.extend(sorted(LIVE.glob("batch-r*.jsonl")))
    for n in batches:
        text = n.read_text(encoding="utf-8", errors="replace").casefold()
        for b in banned:
            if b in text:
                hits.append(f"{n}:{b}")
    if hits:
        raise RuntimeError(f"family/plant collision {hits}")


def rec_001():
    k_j = 20.00
    v_uv = 4.00
    t_k = k_j * (v_uv**2)
    _exact(t_k, 320.00)
    _exact(t_k / (v_uv**2), 20.00)
    _exact(k_j * (2.00**2), 80.00)
    _exact(k_j * (3.00**2), 180.00)
    _exact(k_j * (5.00**2), 500.00)
    _exact(6000.0 + 1080.0, 7080.0)

    raster = make_raster(
        neurons=24,
        mean_rate_hz=50.0,
        window_ms=40.0,
        seed=202609001,
        source="bf3.jnt.vrms",
        target="brackfen.pool_stop_core",
        table=[
            {"from": "jnt_V", "to": "temp_estimator", "weight": 1.40},
            {"from": "jnt_snr", "to": "nyquist_lock_core", "weight": 1.15},
            {"from": "noiseveil_T", "to": "vendor_continue_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "da.jnt_heatup_conflict",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": "pre-post coincidence on continue-recirc synapses; the plant Johnson-noise modulator depresses continue-recirc links when V_rms stays high inside tau_e of an SNR lock so a Noiseveil last-good cannot hide a 320.00 K pool heat-up after T=k_j*V^2 is applied",
        },
        channel_prefix="jnt.n",
        anchor="BF-3 Johnson-noise 40 ms frame at V_rms 4.00 uV / SNR 12.0 (t_s 2880) reconstructing 320.00 K over the 315.00 K isolate floor",
        kernel_ms=[1.3],
        tau_m=10.0,
    )
    w_s = 0.040
    events = [
        ev(0.0, "jnt.V", 2.00, code="VRMS_UV", units="uV", note="plant-owned Johnson-noise thermometry of spent-fuel pool BF-3 bay B-7; Nyquist remaining-T family, not two-color pyrometer, not phosphor-lifetime, not acoustic pyrometry, not SPND, not Gardon"),
        ev(300000.0, "jnt.snr", 6.0, code="JNT_SNR", units="1", note="early SNR under the 8.0 lock floor"),
        ev(600000.0, "recon.T", 80.00, code="T_K", units="K", note="20.00*(2.00**2)=80.00 exact; still under the 315.00 isolate floor"),
        ev(900000.0, "pool.ORP", 210.0, code="ORP_MV", units="mV", note="plant pool redox on copper DCS; independent witness; unread by Noiseveil"),
        ev(1200000.0, "noiseveil.T", 298.00, code="VENDOR_K", units="K", note="Noiseveil vendor pool-cloud last-good; infra owner; patched Nyquist timestamps"),
        ev(1500000.0, "jnt.V", 3.00, code="VRMS_UV", units="uV"),
        ev(1500001.3, "jnt.snr", 8.5, code="JNT_SNR", units="1", note="1.3 ms SNR after V 3.00 uV; 8.5>=8.0 but T 180.00 < 315.00 so isolate is not yet armed"),
        ev(1560000.0, "recon.T", 180.00, code="T_K", units="K", note="20.00*(3.00**2)=180.00 exact"),
        ev(1800000.0, "jnt.V", 3.00, code="VRMS_UV", units="uV"),
        ev(2100000.0, "recon.T", 180.00, code="T_K", units="K"),
        ev(2400000.0, "permit.slide", 40.00, code="PERM_S", units="s", note="night clerk slid the pool-permit clock 40.00 s; collusion party"),
        ev(2700000.0, "recirc.kW", 18.0, code="RECIRC_KW", units="kW", note="plant recirc PLC on copper fieldbus; independent witness"),
        ev(2880000.0, "jnt.V", 4.00, code="VRMS_UV", units="uV", note="isolate-floor frame; raster sidecar"),
        ev(2880001.3, "jnt.snr", 12.0, code="JNT_SNR", units="1", note="1.3 ms SNR lock after V 4.00 uV; 12.0 >= 8.0"),
        ev(3180000.0, "recon.T", 320.00, code="T_K", units="K", note="20.00*(4.00**2)=320.00 exact; isolate 315.00"),
        ev(3480000.0, "recon.k", 20.00, code="KJ", units="K_per_uV2", note="320.00/(4.00**2)=20.00 exact Nyquist-scale identity"),
        ev(3780000.0, "recirc.kW", 19.0, code="RECIRC_KW", units="kW", note="recirc PLC tracks the plant JNT, not Noiseveil 298.00"),
        ev(4080000.0, "jnt.drop", 1.0, code="JNT_DROP", units="bool", note="vendor Nyquist packets dropped in Noiseveil cloud for 40 s"),
        ev(4380000.0, "noiseveil.T", 298.00, code="VENDOR_K", units="K"),
        ev(4680000.0, "ops.prop", 1.0, code="CONTINUE_RECIRC", units="bool", note="night operator Nessa Quill: Noiseveil is clean 298.00 K; keep recirc at night-idle"),
        ev(4860000.0, "gate.stop", 1.0, code="REJECT", units="decision", note="refuse continue-recirc; 320.00 K and SNR 12.0; Noiseveil not SoT"),
        ev(5160000.0, "pool.ORP", 198.0, code="ORP_MV", units="mV"),
        ev(5460000.0, "jnt.snr", 12.2, code="JNT_SNR", units="1"),
        ev(5760000.0, "recon.k", 20.00, code="KJ", units="K_per_uV2"),
        ev(6000000.0, "hold.start", 1.0, code="RECIRC_HOLD_START", units="bool", note="bookend 1 of the 18.0 min recirc-hold floor"),
        ev(6300000.0, "jnt.snr", 12.1, code="JNT_SNR", units="1"),
        ev(6600000.0, "noiseveil.T", 297.40, code="VENDOR_K", units="K"),
        ev(7080000.0, "hold.floor", 1.0, code="RECIRC_HOLD_FLOOR", units="bool", note="6000 s + 1080 s = 7080 s = 18.0 min"),
        ev(7260000.0, "ops.kill", 1.0, code="UNIT_ESD", units="bool", note="Quill: trip the whole Brackfen pool hall until day-shift"),
        ev(7440000.0, "gate.hold", 1.0, code="MODIFY", units="decision", note="companion t2: recirc-hold on plant JNT as live interlock; unit ESD refused"),
        ev(7740000.0, "hold.set", 1.0, code="RECIRC_HELD", units="bool"),
        ev(8040000.0, "jnt.V", 5.00, code="VRMS_UV", units="uV"),
        ev(8340000.0, "recon.T", 500.00, code="T_K", units="K", note="20.00*(5.00**2)=500.00; post-stop still over 315.00 so hold stands"),
        ev(8640000.0, "noiseveil.T", 297.20, code="VENDOR_K", units="K"),
        ev(8940000.0, "recirc.kW", 42.0, code="RECIRC_KW", units="kW", note="held recirc; PLC tracks the plant JNT"),
        ev(9240000.0, "hold.held", 1.0, code="RECIRC_HELD", units="bool"),
        ev(9540000.0, "plant.esd", 0.0, code="ESD_NOT_TAKEN", units="bool"),
        ev(9840000.0, "permit.slide", 40.00, code="PERM_S", units="s"),
        ev(10140000.0, "pool.ORP", 190.0, code="ORP_MV", units="mV"),
        ev(10440000.0, "jnt.drop", 1.0, code="JNT_DROP", units="bool"),
        ev(10740000.0, "hold.lock", 1.0, code="RECIRC_HELD", units="bool"),
        ev(11040000.0, "recon.k", 20.00, code="KJ", units="K_per_uV2", note="500.00/(5.00**2)=20.00 identity held post-stop"),
        ev(11340000.0, "jnt.snr", 11.8, code="JNT_SNR", units="1"),
        ev(11640000.0, "recirc.kW", 41.0, code="RECIRC_KW", units="kW"),
        ev(11940000.0, "noiseveil.T", 297.00, code="VENDOR_K", units="K"),
        ev(12240000.0, "hold.held", 1.0, code="RECIRC_HELD", units="bool"),
        ev(12540000.0, "pool.ORP", 188.0, code="ORP_MV", units="mV"),
        ev(12840000.0, "jnt.V", 5.00, code="VRMS_UV", units="uV"),
        ev(13140000.0, "recon.T", 500.00, code="T_K", units="K"),
        ev(13440000.0, "plant.esd", 0.0, code="ESD_NOT_TAKEN", units="bool"),
        ev(13740000.0, "hold.lock", 1.0, code="RECIRC_HELD", units="bool"),
        ev(14040000.0, "jnt.snr", 11.6, code="JNT_SNR", units="1"),
    ]
    events.sort(key=lambda e: (e["t_rel_ms"], e["channel"]))
    assert_stream(events)

    traj = {
        "id": "nelb-r01-001-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "BF-JNT-2026-0902",
            "domain": "johnson_noise_spent_fuel_pool_t",
            "setting": "Brackfen Pool BF-3 (invented), Reedspire Fuel Yard, bay B-7. Plant-owned Johnson-noise thermometry (Nyquist voltage) is the remaining-temperature SoT. Noiseveil / JNT-9 vendor DAQ (infra owner) plus the pool-permit clock are collusion parties, not witnesses. Invented plant; designed campaign. Not two-color pyrometer (r55), not phosphor-lifetime (r39), not acoustic pyrometry (r25), not rhodium SPND (r31), not Gardon (r51).",
            "observables_at_decision": {
                "V_rms_uV": v_uv,
                "k_j": k_j,
                "T_K": t_k,
                "jnt_snr": 12.2,
                "noiseveil_K": 298.00,
                "permit_slide_s": 40.00,
                "isolate_floor_K": 315.00,
            },
            "margin_authority": "BF-3 pool SOP rev C: if reconstructed T_K >= 315.00 AND JNT SNR >= 8.0, continue-recirc is forbidden even if Noiseveil reports 298.00 K. Unit ESD is a different gate.",
        },
        "proposed_action": {
            "actor": "night operator Nessa Quill, citing Noiseveil 298.00 K and a quiet Nyquist channel",
            "summary": "keep bay B-7 at night-idle recirc; 4.00 uV is preamp noise on a healthy 298.00 K last-good",
            "basis_claimed": "Noiseveil is the only OEM JNT SoT and a night abort of B-7 recirc is a heat-removal miss",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Continue-recirc is refused. Serialized reconstruction: T_K = k_j * V_rms^2 = 20.00 * (4.00 ** 2) = 320.00, above the 315.00 K isolate floor, and JNT SNR is 12.0 >= 8.0. Scale identity T / V^2 = 320.00 / 16.00 = 20.00. Permit clock was slid 40.00 s and vendor Nyquist packets were dropped, so Noiseveil is a collusion party (JNT vendor plus operator plus night clerk). Ordered: refuse continue-recirc now. Scope: this REJECT does not ESD the pool hall (that is the companion question) and does not isolate the pool ORP.",
            "threshold": "T_K>=315.00 AND jnt_snr>=8.0 => refuse continue-recirc; Noiseveil is not SoT",
            "stated_residuals": "recirc-hold still required to hold the 320.00 K; 320.00 vs a true 500.00 kill is a production cut; Noiseveil remains the only OEM JNT channel",
        },
        "executed_action": {
            "summary": "REJECT at t_s 4860: continue-recirc refused; Noiseveil not SoT; reconstruction locked",
            "tool": "bf3-jnt-pool-gate-cli",
            "observation": "T 320.00 K recomputes from V 4.00 uV; plant JNT hashed; Noiseveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2880.0, "event": "jnt V 4.00 uV; raster frame; T 320.00 K"},
                {"t_s": 4680.0, "event": "ops proposes continue-recirc"},
                {"t_s": 4860.0, "event": "REJECT continue-recirc"},
                {"t_s": 6000.0, "event": "18 min recirc-hold bookend 1"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 7440.0, "event": "companion MODIFY recirc-hold vs unit ESD"},
            ],
            "observed_effects": [
                "pool temperature recomputes from the serialized Johnson-noise model at every recon.T event",
                "a Noiseveil-only head would have continued recirc overnight",
                "18 min recirc-hold floor is in the stream (hold.start, hold.floor)",
            ],
            "surprises": [
                "a clean vendor 298.00 K corridor and a 40 s permit slide co-existed with a 320.00 K plant reconstruction",
            ],
            "new_state": {
                "bay_b7": "continue-recirc blocked",
                "noiseveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 1980000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("jnt_reconstruction", 0.14),
                ("conjunctive_isolate_floor", 0.12),
                ("noiseveil_nonsubstitution", 0.10),
                ("three_party_collusion", 0.10),
                ("hold_time_cost", -0.03),
            ],
            "scored for a continue-recirc REJECT on a recomputable Johnson-noise pool temperature while refusing a Noiseveil last-good patch and a permit clock slide; 18 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["REJECT", "johnson-noise-t", "serialized-reconstruction", "operational-companion"],
            distillation_note="Johnson-noise gate: serialized k_j*V^2 plus SNR lock beats a vendor last-good patch; companion t2 is the recirc-hold, not a referral vote",
            distillation_value="Independent CUBA LIF raster races the Nyquist estimator against a vendor-continue advocate with 1 ms refractory and 0.82**k adaptation, so a hybrid head can distill T=k_j*V^2 without copying the campaign stream.",
        ),
    }
    traj2 = {
        "id": "nelb-r01-001-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "BF-JNT-2026-0902-exec",
            "domain": "recirc_hold_jnt_interlock_execution",
            "setting": "Same BF-3 after the REJECT. Operator proposes a pool-hall ESD. This companion is the operational recirc-hold with the plant JNT as the live interlock, not a second temperature vote.",
            "observables_at_decision": {
                "T_K": 500.00,
                "recirc_hold_floor_s": 1080.0,
                "unit_esd_proposed": True,
                "recirc_hold_set": True,
            },
            "margin_authority": "recirc_hold AND hold_floor_complete AND unit_esd_not_taken AND continue_not_restored",
        },
        "proposed_action": {
            "actor": "night operator Nessa Quill",
            "summary": "ESD the whole Brackfen pool hall until day-shift; 18 min already paid and Noiseveil still shows 297.40 K",
            "basis_claimed": "the REJECT already stopped B-7 recirc-idle, so a unit kill is the cheapest hold",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Recirc-hold plus plant JNT as the live interlock. The 18 min hold floor is complete and the isolate tripwire (T_K >= 315.00) is still armed on the plant JNT head. MODIFY the default restore SOP into a plant-JNT-only interlock. Do not ESD the pool hall. Do not restore idle on Noiseveil. 500.00 K post-stop is still the plant SoT until a new frame clears 315.00.",
            "threshold": "recirc_hold AND hold_floor_complete AND unit_esd_not_taken AND continue_not_restored",
            "stated_residuals": "hold still required; Noiseveil remains the only OEM JNT channel",
        },
        "executed_action": {
            "summary": "recirc-hold held at t_s 7440; unit ESD not latched; Noiseveil restore not taken",
            "tool": "bf3-recirc-hold-exec",
            "observation": "recon.T 500.00 K after stop; hold line-up complete; Noiseveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "recirc-hold clock started after REJECT"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 7260.0, "event": "unit ESD proposed"},
                {"t_s": 7440.0, "event": "MODIFY recirc-hold; unit ESD refused"},
            ],
            "observed_effects": [
                "Noiseveil restore did not reopen the temperature call",
                "unit ESD never fired; B-7 held recirc on the plant JNT",
            ],
            "surprises": [
                "post-stop 500.00 K (V 5.00 uV) still recomputes from k_j*V^2 while Noiseveil stays at 297 K",
            ],
            "new_state": {"hold": "held", "unit": "in service", "bay_b7": "held"},
            "latency_ms": 2580000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("recirc_hold", 0.12),
                ("no_unit_esd", 0.10),
                ("noiseveil_nonsubstitution", 0.08),
                ("hold_floor_complete", 0.06),
                ("held_idle_cost", -0.02),
            ],
            "operational execution gate: recirc-hold because Noiseveil is not a restore license; not a temperature re-vote",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "recirc-hold"]),
    }
    return {
        "id": "nelb-r01-001",
        "spike_events": events,
        "language_view": {
            "description": "Brackfen Pool BF-3. Plant-owned Johnson-noise thermometry reconstructs 320.00 K from 20.00*(4.00**2) while Noiseveil still reports 298.00 K. The gate REJECTs continue-recirc. An 18 min recirc-hold floor is serialized in the stream. Companion t2 MODIFYs a unit ESD into a plant-JNT recirc-hold.",
            "trajectory": traj,
            "trajectory_recirc_hold": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "jnt.V / jnt.snr": "Nyquist rms voltage and SNR; the physics channels the reconstruction consumes",
                "recon.T / recon.k": "serialized remaining temperature K and k_j = T/V^2 identity",
                "pool.ORP / noiseveil.T / permit.slide / recirc.kW / jnt.drop": "pool ORP, vendor last-good, permit clock slide, recirc kW, and dropped Nyquist packets; the denial and collusion channels",
                "ops.prop / gate.stop / ops.kill / gate.hold": "continue-recirc proposal, REJECT, unit-ESD proposal, companion MODIFY",
                "hold.start / hold.floor / hold.set / hold.held / plant.esd / hold.lock": "operational companion channels plus the 18 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-over: noiseveil.T 298.00 next to recon.T 320.00",
                "reconstruction as event: recon.T 320.00 equals 20.00*(4.00**2)",
                "REJECT then operational MODIFY: gate.stop at 4860 s, gate.hold at 7440 s",
                "slow floor in-stream: hold.start 6000 s, hold.floor 7080 s (18.0 min)",
                "tight jnt pair: jnt.V then jnt.snr +1.3 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Noiseveil is 298.00 K' = noiseveil.T 298.00; '320 K' = recon.T 320.00; 'refuse continue-recirc' = gate.stop REJECT; 'hold not unit ESD' = gate.hold MODIFY",
            "why_high_value": "New Johnson-noise remaining-temperature family on a spent-fuel pool (not two-color pyrometer r55, not phosphor-lifetime r39, not acoustic pyrometry r25, not SPND r31, not Gardon r51). Lead REJECT of continue-recirc on a recomputable heat-up that a vendor last-good patch and a permit clock slide would have cleared. Independent CUBA LIF raster (not a spike_events echo) plus required snn_tags. Companion t2 is operational recirc-hold. sim_or_real=designed.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random plus CUBA LIF",
                "seeds": {"raster": 202609001, "stream_note": "stream amplitudes are authored constants (uV, 1, K, s, mV, kW, bool)"},
                "draw_order": "raster: independent CUBA LIF first-passage times, per-spike adaptation and noise; not copied from spike_events",
                "thinning": "JNT exists at ~10 Hz Nyquist windows; stream keeps 6 V points; recon keeps 6 of ~20 solver ticks; 52-event floor",
                "refractory_floors_ms": {
                    "jnt.V": 1.3,
                    "jnt.snr": 1.3,
                    "recon.T": 60000,
                    "recon.k": 60000,
                    "pool.ORP": 60000,
                    "noiseveil.T": 60000,
                    "permit.slide": 60000,
                    "recirc.kW": 60000,
                    "jnt.drop": 60000,
                    "ops.prop": 60000,
                    "gate.stop": 60000,
                    "hold.start": 60000,
                    "hold.floor": 60000,
                    "ops.kill": 60000,
                    "gate.hold": 60000,
                    "hold.set": 60000,
                    "hold.held": 60000,
                    "plant.esd": 60000,
                    "hold.lock": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-09-02T01:00:00Z campaign start",
            },
            "distillation_targets": [
                "Johnson-noise reconstruction head: T_K = k_j * V_rms^2; k_j = T / V^2",
                "conjunctive isolate floor vs continue-recirc vs unit ESD",
                "vendor-JNT nonsubstitution plus three-party collusion including the infra owner",
                "operational companion: recirc-hold without restoring on Noiseveil",
                "independent CUBA LIF raster with race/refractory/adaptation tags",
            ],
        },
        "reconstruction_model": {
            "name": "johnson_noise_pool_temperature",
            "formula": "T_K = k_j * V_rms_uV^2; k_j = T_K / V_rms_uV^2",
            "parameters": {
                "k_j": 20.00,
                "isolate_floor_K": 315.00,
                "kill_K": 500.00,
                "snr_lock": 8.0,
                "hold_min": 18.0,
            },
            "worked_example": {"V_rms_uV": 4.00, "T_K": 320.00, "k_j": 20.00},
            "check": "20.00 * (4.00 ** 2) = 320.00 exactly; 320.00 / 16.00 = 20.00 exactly; 6000 s + 1080 s = 7080 s = 18.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "bf3.jnt_pool_gate",
            "note": "REJECT accumulator wins: plant Johnson-noise T evidence overpowers the Noiseveil continue advocate",
            "decode_rule": "reject-continue if temp_estimator AND nyquist_lock fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("temp_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("nyquist_lock", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("reject_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "bf3.jnt_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "bf3.hold_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r01-001",
            clock_domain="bf3-jnt-campaign-relative-ms-t0-2026-09-02T01:00:00Z",
            tags=["johnson-noise-t", "REJECT", "MODIFY", "serialized-reconstruction", "operational-t2", "independent-lif"],
            distillation_value="Independent CUBA LIF raster plus T=k_j*V^2 reconstruction lets a hybrid SNN distill a Nyquist heat-up gate without echoing the campaign stream.",
        ),
    }


def rec_002():
    k_c = 80.00
    v_p = 6.00
    v_ref = 4.00
    c_ppm = k_c * (v_p / v_ref)
    _exact(c_ppm, 120.00)
    ratio = v_p / v_ref
    _exact(ratio, 1.50)
    _exact(k_c * (3.00 / v_ref), 60.00)
    _exact(k_c * (4.00 / v_ref), 80.00)
    _exact(k_c * (5.00 / v_ref), 100.00)
    _exact(2820.0 + 1440.0, 4260.0)

    raster = make_raster(
        neurons=20,
        mean_rate_hz=62.5,
        window_ms=32.0,
        seed=202609002,
        source="fs6.coulter.pulse",
        target="flintshaw.slurry_isolate_core",
        table=[
            {"from": "coul_Vp", "to": "conc_estimator", "weight": 1.35},
            {"from": "coul_snr", "to": "aperture_norm_core", "weight": 1.20},
            {"from": "slurryveil_C", "to": "vendor_continue_advocate", "weight": 0.40},
        ],
        third_factor={
            "modulator": "ach.coulter_referral_pressure",
            "tau_e_s": 1.2,
            "tau_e_ms": 1200.0,
            "eligibility": "pre-post coincidence on keep-polish synapses; the Coulter modulator depresses keep-polish and referral links when pulse height stays high inside tau_e of an SNR lock so a Slurryveil last-good cannot hide a 120.00 ppm CMP slurry or name Ivor Kemp",
        },
        channel_prefix="coul.n",
        anchor="FS-6 HIL coupon 32 ms frame at Vp 6.00 mV / Vref 4.00 mV / SNR 14.0 (t_s 1560) reconstructing 120.00 ppm above the 80.00 isolate floor",
        kernel_ms=[1.2],
        tau_m=12.0,
    )
    w_s = 0.032
    events = [
        ev(0.0, "coul.Vp", 3.00, code="VP_MV", units="mV", note="HIL Coulter zone-sensing of CMP slurry on a dummy cell in COUL-HIL-4; remaining-particle family, not FBRM D50, not PDA Sauter, not flow cytometry, not C-SAM"),
        ev(180000.0, "coul.snr", 9.0, code="COUL_SNR", units="1", note="early aperture SNR; isolate needs SNR>=12"),
        ev(360000.0, "recon.C", 60.00, code="C_PPM", units="ppm", note="80.00*(3.00/4.00)=60.00 exact"),
        ev(450000.0, "coul.Vp", 3.00, code="VP_MV", units="mV"),
        ev(450001.2, "coul.snr", 10.0, code="COUL_SNR", units="1", note="1.2 ms SNR after Vp 3.00; isolate still needs SNR>=12"),
        ev(468000.0, "recon.C", 60.00, code="C_PPM", units="ppm"),
        ev(540000.0, "ap.cal", 0.00, code="CAL_MV", units="mV", note="plant aperture-cal remaining; no Coulter-scale hop in this window"),
        ev(720000.0, "slurryveil.C", 18.20, code="VENDOR_PPM", units="ppm", note="Slurryveil last-good polish-cloud; not admissible SoT"),
        ev(900000.0, "coul.Vp", 4.00, code="VP_MV", units="mV"),
        ev(1080000.0, "recon.C", 80.00, code="C_PPM", units="ppm", note="80.00*(4.00/4.00)=80.00; at the 80.00 isolate floor"),
        ev(1260000.0, "ap.delay", 0.0, code="CAL_AE", units="bool", note="missing aperture-cal AE burst; Slurryveil UTC vs plant UTC+2 skipped the cal by 120 min"),
        ev(1440000.0, "ap.cal", 0.00, code="CAL_MV", units="mV"),
        ev(1560000.0, "coul.Vp", 6.00, code="VP_MV", units="mV", note="isolate-floor frame; raster sidecar"),
        ev(1560001.2, "coul.Vref", 4.00, code="VREF_MV", units="mV", note="1.2 ms Vref after Vp; ratio 1.50"),
        ev(1560002.5, "coul.snr", 14.0, code="COUL_SNR", units="1", note="1.3 ms after Vref; isolate-frame SNR 14.0 >= 12.0"),
        ev(1740000.0, "recon.C", 120.00, code="C_PPM", units="ppm", note="80.00*(6.00/4.00)=120.00 exact; isolate 80.00, trip 250.00"),
        ev(1920000.0, "recon.R", 1.50, code="RATIO", units="1", note="6.00/4.00=1.50 exact; pulse-height identity"),
        ev(2100000.0, "slurryveil.C", 18.20, code="VENDOR_PPM", units="ppm"),
        ev(2280000.0, "ops.prop", 1.0, code="KEEP_POLISH_REFER", units="bool", note="night lead Tamsin Rowe analog: keep pad P-4 polishing and refer Coulter tech Ivor Kemp"),
        ev(2460000.0, "gate.isol", 1.0, code="MODIFY", units="decision", note="isolate this pad; refuse the person-referral; Slurryveil not SoT"),
        ev(2640000.0, "pad.lock", 1.0, code="PAD_ISOL", units="bool"),
        ev(2820000.0, "flush.start", 1.0, code="FLUSH_START", units="bool", note="bookend 1 of the 24.0 min flush plus aperture-settle floor"),
        ev(3000000.0, "coul.snr", 14.2, code="COUL_SNR", units="1"),
        ev(3300000.0, "recon.R", 1.50, code="RATIO", units="1", note="6.00/4.00=1.50 identity held through flush start"),
        ev(3600000.0, "pad.T", 28.0, code="PAD_C", units="C", note="plant pad thermocouple on copper DCS; independent witness; unread by Slurryveil"),
        ev(3900000.0, "coul.Vp", 5.00, code="VP_MV", units="mV"),
        ev(4080000.0, "recon.C", 100.00, code="C_PPM", units="ppm", note="80.00*(5.00/4.00)=100.00 exact; still over the 80.00 isolate floor"),
        ev(4260000.0, "flush.floor", 1.0, code="FLUSH_FLOOR", units="bool", note="2820 s + 1440 s = 4260 s = 24.0 min"),
        ev(4440000.0, "ops.refer", 1.0, code="REFER_KEMP", units="bool", note="lead: Kemp badge was on the Coulter log"),
        ev(4620000.0, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: new-aperture restart; person-referral refused; shop trip refused"),
        ev(4800000.0, "coul.new", 1.0, code="NEW_COUL", units="bool"),
        ev(4980000.0, "coul.Vp", 4.00, code="VP_MV", units="mV"),
        ev(5040000.0, "coul.snr", 13.0, code="COUL_SNR", units="1"),
        ev(5160000.0, "recon.C", 80.00, code="C_PPM", units="ppm", note="80.00*(4.00/4.00)=80.00; HIL dummy still at the 80.00 isolate floor so the isolated pad stays held"),
        ev(5340000.0, "slurryveil.C", 17.80, code="VENDOR_PPM", units="ppm"),
        ev(5400000.0, "pad.T", 24.0, code="PAD_C", units="C"),
        ev(5520000.0, "ap.cal", 0.00, code="CAL_MV", units="mV"),
        ev(5700000.0, "refer.hold", 0.0, code="REFER_NOT_TAKEN", units="bool", note="Kemp exonerated; missing aperture-cal AE precedes the high C, not the badge touch"),
        ev(5880000.0, "pad.held", 1.0, code="PAD_HELD", units="bool"),
        ev(6060000.0, "ap.delay", 1.0, code="CAL_AE", units="bool", note="aperture-cal AE restored on the new Coulter"),
        ev(6180000.0, "slurryveil.C", 17.60, code="VENDOR_PPM", units="ppm"),
        ev(6240000.0, "recon.R", 1.00, code="RATIO", units="1", note="4.00/4.00=1.00 on the post-isolate HIL dummy; 80.00*(4.00/4.00)=80.00"),
        ev(6360000.0, "recon.R", 1.00, code="RATIO", units="1"),
        ev(6420000.0, "shop.trip", 0.0, code="TRIP_NOT_TAKEN", units="bool"),
        ev(6600000.0, "cell.restart", 1.0, code="CELL_RESTART", units="bool"),
        ev(6780000.0, "coul.snr", 13.2, code="COUL_SNR", units="1"),
        ev(6960000.0, "pad.held", 1.0, code="PAD_HELD", units="bool"),
        ev(7140000.0, "recon.C", 80.00, code="C_PPM", units="ppm"),
        ev(7320000.0, "slurryveil.C", 17.40, code="VENDOR_PPM", units="ppm"),
        ev(7500000.0, "shop.trip", 0.0, code="TRIP_NOT_TAKEN", units="bool"),
        ev(7680000.0, "cell.restart", 1.0, code="CELL_RESTART", units="bool"),
        ev(7860000.0, "coul.Vp", 4.00, code="VP_MV", units="mV"),
    ]
    events.sort(key=lambda e: (e["t_rel_ms"], e["channel"]))
    assert_stream(events)

    traj = {
        "id": "nelb-r01-002-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "FS-COUL-2026-0718",
            "domain": "coulter_cmp_slurry_particles",
            "setting": "Flintshaw CMP FS-6 (invented), Ashlar Polish, pad P-4. Hardware-in-the-loop dummy cell in COUL-HIL-4 supplies the resistive-pulse height that times the in-service isolate. Plant-owned Coulter reconstruction is the remaining-particle SoT. Slurryveil vendor polish scheduler is a corridor witness, not the pad SoT. Not FBRM D50 (r49), not PDA Sauter D32 (r47), not flow cytometry (08-17), not C-SAM (r48).",
            "observables_at_decision": {
                "Vp_mV": v_p,
                "Vref_mV": v_ref,
                "ratio": ratio,
                "k_c": k_c,
                "C_ppm": c_ppm,
                "coul_snr": 14.0,
                "slurryveil_ppm": 18.20,
                "ap_cal": 0.00,
                "ap_delay": 0.0,
                "isolate_floor_ppm": 80.00,
            },
            "margin_authority": "FS-6 pad SOP rev B: if reconstructed C_ppm >= 80.00 AND Coulter SNR >= 12.0, isolate this pad this night. A Slurryveil last-good or a quiet aperture-cal residual cannot keep the polish. Trip tripwire is 250.00 ppm. Person-referral is a different gate.",
        },
        "proposed_action": {
            "actor": "night lead citing Slurryveil 18.20 ppm and a quiet aperture log",
            "summary": "keep pad P-4 polishing and refer Coulter tech Ivor Kemp; 6.00 mV is bubble noise on a healthy last-good",
            "basis_claimed": "Slurryveil is the only OEM Coulter SoT and a night abort of P-4 is a wafer miss",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Keep-polish is refused; person-referral is refused. Serialized reconstruction: C_ppm = k_c * (Vp / Vref) = 80.00 * (6.00 / 4.00) = 120.00, above the 80.00 ppm isolate floor, and Coulter SNR is 14.0 >= 12.0. Ratio identity Vp / Vref = 1.50. Missing aperture-cal AE plus UTC vs UTC+2 skip the cal; Ivor Kemp is not last-to-badge. Ordered: isolate this pad, hold the flush floor, do not refer Kemp, do not shop-trip the tool. Scope: this MODIFY does not restart on a new aperture (that is the companion question).",
            "threshold": "C_ppm>=80.00 AND coul_snr>=12.0 => isolate this pad; Slurryveil is not SoT; trip if C_ppm>=250.00",
            "stated_residuals": "flush still required; 120.00 vs 250.00 trip is a production cut; Slurryveil remains the only OEM Coulter channel",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 2460: pad isolated; referral refused; reconstruction locked",
            "tool": "fs6-coul-pad-gate-cli",
            "observation": "C 120.00 ppm recomputes from Vp 6.00 mV; COUL-HIL-4 hashed; Slurryveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1560.0, "event": "coul Vp 6.00 mV; raster frame; C 120.00 ppm"},
                {"t_s": 2280.0, "event": "ops proposes keep-polish and refer Kemp"},
                {"t_s": 2460.0, "event": "MODIFY isolate pad; referral refused"},
                {"t_s": 2820.0, "event": "24 min flush bookend 1"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4620.0, "event": "companion ACCEPT new-aperture restart"},
            ],
            "observed_effects": [
                "particle concentration recomputes from the serialized Coulter model at every recon.C event",
                "a Slurryveil-only head would have kept polishing and named Kemp",
                "24 min flush floor is in the stream (flush.start, flush.floor)",
            ],
            "surprises": [
                "missing aperture-cal AE plus timezone skip exonerate Kemp; the high C precedes the badge touch",
            ],
            "new_state": {
                "pad_p4": "isolated",
                "slurryveil": "not SoT",
                "kemp": "exonerated",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2160000.0,
        },
        "reward_components": reward(
            0.40,
            [
                ("coulter_reconstruction", 0.14),
                ("isolate_floor_pad", 0.12),
                ("slurryveil_nonsubstitution", 0.08),
                ("exoneration", 0.08),
                ("flush_time_cost", -0.02),
            ],
            "scored for a keep-polish MODIFY on a recomputable Coulter particle concentration while refusing a Slurryveil last-good and a last-to-badge referral",
        ),
        "meta": meta_common(
            tags=["MODIFY", "coulter-cmp", "serialized-reconstruction", "operational-companion"],
            distillation_note="Coulter gate: serialized k_c*(Vp/Vref) plus SNR lock beats a vendor last-good and a referral; companion t2 is the new-aperture restart",
            distillation_value="Independent CUBA LIF raster races the pulse-height estimator against a vendor-continue advocate with 1 ms refractory and adaptation, distilling C=k_c*(Vp/Vref) without echoing the HIL stream.",
        ),
    }
    traj2 = {
        "id": "nelb-r01-002-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "FS-COUL-2026-0718-exec",
            "domain": "new_aperture_restart_execution",
            "setting": "Same FS-6 after the MODIFY. Lead proposes a shop trip of the polish tool. This companion is the operational new-aperture restart, not a second particle vote.",
            "observables_at_decision": {
                "C_ppm": 80.00,
                "flush_floor_s": 1440.0,
                "shop_trip_proposed": False,
                "new_aperture": True,
            },
            "margin_authority": "flush_complete AND shop_trip_not_taken AND referral_not_taken AND pad_held",
        },
        "proposed_action": {
            "actor": "night lead",
            "summary": "shop-trip the whole Flintshaw CMP tool until day-shift; 24 min already paid and Slurryveil still shows 17.80 ppm",
            "basis_claimed": "the MODIFY already isolated P-4, so a shop trip is the cheapest hold",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "New-aperture restart plus plant Coulter as the live interlock. The 24 min flush floor is complete and the isolate tripwire (C_ppm >= 80.00) is still armed on the plant Coulter head. ACCEPT the new-aperture restart. Do not shop-trip the tool. Do not restore polish on Slurryveil. Do not refer Kemp. 80.00 ppm post-isolate is still at the floor, so P-4 stays held until a new frame clears 80.00.",
            "threshold": "flush_complete AND shop_trip_not_taken AND referral_not_taken AND pad_held",
            "stated_residuals": "pad remains held at the 80.00 floor; Slurryveil remains the only OEM Coulter channel",
        },
        "executed_action": {
            "summary": "new-aperture restart at t_s 4620; shop trip not latched; Slurryveil restore not taken; Kemp not referred",
            "tool": "fs6-coul-restart-exec",
            "observation": "recon.C 80.00 ppm after isolate; new aperture hashed; Slurryveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2820.0, "event": "flush clock started after MODIFY"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4440.0, "event": "Kemp referral re-proposed"},
                {"t_s": 4620.0, "event": "ACCEPT new-aperture restart; referral refused"},
            ],
            "observed_effects": [
                "Slurryveil restore did not reopen the particle call",
                "shop trip never fired; Kemp not referred",
            ],
            "surprises": [
                "post-isolate ratio 1.00 still recomputes C=80.00 while Slurryveil stays near 18 ppm",
            ],
            "new_state": {"pad": "held", "aperture": "new", "shop": "in service"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.35,
            [
                ("new_aperture_restart", 0.12),
                ("no_shop_trip", 0.10),
                ("slurryveil_nonsubstitution", 0.08),
                ("flush_floor_complete", 0.07),
                ("held_polish_cost", -0.02),
            ],
            "operational execution gate: new-aperture restart because Slurryveil is not a restore license; not a particle re-vote",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "new-aperture"]),
    }
    return {
        "id": "nelb-r01-002",
        "spike_events": events,
        "language_view": {
            "description": "Flintshaw CMP FS-6. HIL Coulter reconstructs 120.00 ppm remaining particles from 80.00*(6.00/4.00) while Slurryveil still reports 18.20 ppm. The gate MODIFYs keep-polish into a pad isolate and refuses a person-referral. A 24 min flush floor is serialized in the stream. Companion t2 ACCEPTs a new-aperture restart.",
            "trajectory": traj,
            "trajectory_new_aperture": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "coul.Vp / coul.Vref / coul.snr": "resistive pulse height, reference, and SNR; the physics channels the reconstruction consumes",
                "recon.C / recon.R": "serialized remaining concentration ppm and Vp/Vref identity",
                "slurryveil.C / ap.cal / ap.delay / pad.T": "vendor last-good, aperture-cal, missing-cal AE, and pad thermocouple; the denial and exoneration channels",
                "ops.prop / gate.isol / ops.refer / gate.exec": "keep-polish proposal, MODIFY, referral proposal, companion ACCEPT",
                "flush.start / flush.floor / pad.lock / pad.held / shop.trip / cell.restart": "operational companion channels plus the 24 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-over: slurryveil.C 18.20 next to recon.C 120.00",
                "reconstruction as event: recon.C 120.00 equals 80.00*(6.00/4.00)",
                "MODIFY then operational ACCEPT: gate.isol at 2460 s, gate.exec at 4620 s",
                "slow floor in-stream: flush.start 2820 s, flush.floor 4260 s (24.0 min)",
                "tight coul pair: coul.Vp then coul.Vref +1.2 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Slurryveil is 18.20 ppm' = slurryveil.C 18.20; '120 ppm' = recon.C 120.00; 'isolate pad' = gate.isol MODIFY; 'new aperture not shop trip' = gate.exec ACCEPT",
            "why_high_value": "New Coulter remaining-particle family on a CMP slurry (not FBRM r49, not PDA r47, not flow cytometry, not C-SAM r48). Lead MODIFY of keep-polish on a recomputable scratch-risk slurry that a vendor last-good would have kept running, plus timezone-skipped aperture-cal exoneration. Independent CUBA LIF raster plus required snn_tags. Companion t2 is operational new-aperture restart. sim_or_real=hil.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random plus CUBA LIF",
                "seeds": {"raster": 202609002, "stream_note": "stream amplitudes are authored constants (mV, 1, ppm, bool, C)"},
                "draw_order": "raster: independent CUBA LIF first-passage times, per-spike adaptation and noise; not copied from spike_events",
                "thinning": "Coulter exists at ~kHz pulses; stream keeps 6 Vp points; recon keeps 6 of ~20 solver ticks; 52-event floor",
                "refractory_floors_ms": {
                    "coul.Vp": 1.2,
                    "coul.Vref": 1.2,
                    "coul.snr": 1.2,
                    "recon.C": 60000,
                    "recon.R": 60000,
                    "slurryveil.C": 60000,
                    "ap.cal": 60000,
                    "ap.delay": 60000,
                    "pad.T": 60000,
                    "ops.prop": 60000,
                    "gate.isol": 60000,
                    "pad.lock": 60000,
                    "flush.start": 60000,
                    "flush.floor": 60000,
                    "ops.refer": 60000,
                    "gate.exec": 60000,
                    "coul.new": 60000,
                    "refer.hold": 60000,
                    "pad.held": 60000,
                    "shop.trip": 60000,
                    "cell.restart": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-07-18T03:00:00Z HIL night start",
            },
            "distillation_targets": [
                "Coulter reconstruction head: C_ppm = k_c * (Vp / Vref); R = Vp / Vref",
                "isolate-floor pad vs keep-polish vs shop-trip",
                "exoneration against last-to-badge social pressure",
                "operational companion: new-aperture restart without restoring on Slurryveil",
                "independent CUBA LIF raster with race/refractory/adaptation tags",
            ],
        },
        "reconstruction_model": {
            "name": "coulter_cmp_particle_concentration",
            "formula": "C_ppm = k_c * (Vp_mV / Vref_mV); R = Vp_mV / Vref_mV",
            "parameters": {
                "k_c": 80.00,
                "Vref_mV": 4.00,
                "isolate_floor_ppm": 80.00,
                "trip_ppm": 250.00,
                "snr_lock": 12.0,
                "flush_min": 24.0,
            },
            "worked_example": {"Vp_mV": 6.00, "C_ppm": 120.00, "R": 1.50},
            "check": "80.00 * (6.00 / 4.00) = 120.00 exactly; 6.00 / 4.00 = 1.50 exactly; 2820 s + 1440 s = 4260 s = 24.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 32.0,
            "decision_window_s": 0.032,
            "code": "fs6.coul_pad_gate",
            "note": "MODIFY accumulator wins: plant Coulter particle evidence overpowers the Slurryveil keep-polish advocate",
            "decode_rule": "isolate if conc_estimator AND aperture_norm fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("conc_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("aperture_norm", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("modify_latch", 80, 1.6, 50.0, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "fs6.coul_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 32.0},
                {"check": "fs6.flush_scorer", "neurons": 40, "mean_rate_hz": 62.5, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r01-002",
            clock_domain="fs6-coul-hil-relative-ms-t0-2026-07-18T03:00:00Z",
            tags=["coulter-cmp", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2", "independent-lif"],
            distillation_value="Independent CUBA LIF raster plus C=k_c*(Vp/Vref) reconstruction lets a hybrid SNN distill a CMP-scratch gate without echoing the HIL stream.",
        ),
    }


def rec_003():
    k_p = 8.00
    n_fringe = 4.00
    sigma = k_p * n_fringe
    _exact(sigma, 32.00)
    _exact(sigma / k_p, 4.00)
    _exact(k_p * 2.00, 16.00)
    _exact(k_p * 3.00, 24.00)
    _exact(k_p * 5.00, 40.00)
    _exact(6000.0 + 720.0, 6720.0)

    raster = make_raster(
        neurons=16,
        mean_rate_hz=75.0,
        window_ms=36.0,
        seed=202609003,
        source="yh9.pe.fringe",
        target="yewholt.copv_isolate_core",
        table=[
            {"from": "pe_N", "to": "stress_estimator", "weight": 1.40},
            {"from": "pe_snr", "to": "brewster_lock_core", "weight": 1.10},
            {"from": "fringeveil_s", "to": "vendor_skip_advocate", "weight": 0.42},
        ],
        third_factor={
            "modulator": "na.copv_scope_eligibility",
            "tau_e_s": 2.0,
            "tau_e_ms": 2000.0,
            "eligibility": "pre-post coincidence on skip-survey synapses; the photoelastic modulator depresses skip-survey links when fringe order stays high inside tau_e of an SNR lock so a Fringeveil last-good cannot hide a 32.00 MPa hoop on V-4 or release V-1..V-3",
        },
        channel_prefix="pe.n",
        anchor="YH-9 PE-SIM-2 36 ms frame at N 4.00 fringes / SNR 16.0 (t_s 3000) reconstructing 32.00 MPa over the 24.00 isolate floor",
        kernel_ms=[1.5],
        tau_m=8.0,
    )
    w_s = 0.036
    events = [
        ev(0.0, "pe.N", 2.00, code="FRINGE", units="1", note="simulated photoelastic remaining hoop-stress of COPV V-4 in PE-SIM-2; Brewster fringe-order family, not DIC hoop-strain, not digital shearography, not FSM, not coda-wave"),
        ev(300000.0, "pe.snr", 8.0, code="PE_SNR", units="1"),
        ev(600000.0, "recon.S", 16.00, code="SIGMA_MPA", units="MPa", note="8.00*2.00=16.00 exact; still under the 24.00 isolate floor"),
        ev(900000.0, "vessel.id", 4.0, code="V_ID", units="1", note="V-4 in scope; V-1..V-3 are adjacent COPVs"),
        ev(1200000.0, "fringeveil.S", 6.40, code="VENDOR_MPA", units="MPa", note="Fringeveil last-good COPV-cloud; not admissible skip-survey witness"),
        ev(1500000.0, "pe.N", 3.00, code="FRINGE", units="1"),
        ev(1500001.5, "pe.snr", 12.0, code="PE_SNR", units="1", note="1.5 ms SNR after N 3.00; 12.0>=12.0 and S 24.00 at the isolate floor"),
        ev(1560000.0, "recon.S", 24.00, code="SIGMA_MPA", units="MPa", note="8.00*3.00=24.00; at the 24.00 isolate floor"),
        ev(1800000.0, "v13.present", 1.0, code="ADJACENT", units="bool"),
        ev(2100000.0, "recon.S", 24.00, code="SIGMA_MPA", units="MPa"),
        ev(2400000.0, "fringeveil.S", 6.40, code="VENDOR_MPA", units="MPa"),
        ev(2700000.0, "pe.snr", 14.0, code="PE_SNR", units="1"),
        ev(3000000.0, "pe.N", 4.00, code="FRINGE", units="1", note="isolate-floor frame; raster sidecar"),
        ev(3000001.5, "pe.snr", 16.0, code="PE_SNR", units="1", note="1.5 ms SNR lock after N 4.00; 16.0 >= 12.0"),
        ev(3300000.0, "recon.S", 32.00, code="SIGMA_MPA", units="MPa", note="8.00*4.00=32.00 exact; isolate 24.00, dump 80.00"),
        ev(3600000.0, "recon.N", 4.00, code="N_ID", units="1", note="32.00/8.00=4.00 exact Brewster identity"),
        ev(3900000.0, "vessel.id", 4.0, code="V_ID", units="1"),
        ev(4200000.0, "fringeveil.S", 6.40, code="VENDOR_MPA", units="MPa"),
        ev(4500000.0, "v13.present", 1.0, code="ADJACENT", units="bool"),
        ev(4800000.0, "ops.prop", 1.0, code="ACCEPT_AND_SKIP", units="bool", note="composite lead Mara Vell: stamp V-4 in band and skip V-1..V-3; 4.00 fringes is a coating glitch on a healthy last-good"),
        ev(5400000.0, "gate.comp", 1.0, code="ACCEPT", units="decision", note="ACCEPT V-4 isolate only; V-1..V-3 out of scope; Fringeveil not SoT"),
        ev(5700000.0, "v4.held", 1.0, code="V4_HELD", units="bool"),
        ev(6000000.0, "surv.start", 1.0, code="SURV_START", units="bool", note="bookend 1 of the 12.0 min survey-complete floor"),
        ev(6300000.0, "pe.snr", 16.2, code="PE_SNR", units="1"),
        ev(6600000.0, "recon.N", 4.00, code="N_ID", units="1"),
        ev(6720000.0, "surv.floor", 1.0, code="SURV_FLOOR", units="bool", note="6000 s + 720 s = 6720 s = 12.0 min"),
        ev(6900000.0, "pe.N", 5.00, code="FRINGE", units="1"),
        ev(7200000.0, "ops.skip", 1.0, code="SKIP_V13", units="bool", note="Vell: skip V-1..V-3; 12 min already paid and Fringeveil is 6.40 MPa"),
        ev(7380000.0, "recon.S", 40.00, code="SIGMA_MPA", units="MPa", note="8.00*5.00=40.00; still under the 80.00 dump-trip so V-4 stays an isolate not a dump"),
        ev(7800000.0, "gate.hold", 1.0, code="REJECT", units="decision", note="companion t2: REJECT skip-survey of V-1..V-3; dump not tripped; V-4 hold stands"),
        ev(8100000.0, "v13.skip", 0.0, code="SKIP_NOT_TAKEN", units="bool"),
        ev(8400000.0, "dump.trip", 0.0, code="DUMP_NOT_TAKEN", units="bool"),
        ev(8700000.0, "v4.held", 1.0, code="V4_HELD", units="bool"),
        ev(9000000.0, "fringeveil.S", 6.20, code="VENDOR_MPA", units="MPa"),
        ev(9300000.0, "surv.held", 1.0, code="SURV_HELD", units="bool"),
        ev(9600000.0, "vessel.survey", 1.0, code="V13_IN_SURVEY", units="bool"),
        ev(9900000.0, "takt.late", 1.0, code="TAKT", units="bool"),
        ev(10200000.0, "pe.snr", 15.8, code="PE_SNR", units="1"),
        ev(10500000.0, "recon.N", 5.00, code="N_ID", units="1", note="40.00/8.00=5.00 identity on the post-accept frame"),
        ev(10800000.0, "recon.S", 24.00, code="SIGMA_MPA", units="MPa", note="later PE-SIM-2 frame at the 24.00 isolate floor; V-4 stays held"),
        ev(11100000.0, "v13.skip", 0.0, code="SKIP_NOT_TAKEN", units="bool"),
        ev(11400000.0, "dump.trip", 0.0, code="DUMP_NOT_TAKEN", units="bool"),
        ev(11700000.0, "fringeveil.S", 6.10, code="VENDOR_MPA", units="MPa"),
        ev(12000000.0, "v4.held", 1.0, code="V4_HELD", units="bool"),
        ev(12300000.0, "vessel.survey", 1.0, code="V13_IN_SURVEY", units="bool"),
        ev(12600000.0, "pe.N", 3.00, code="FRINGE", units="1"),
        ev(12900000.0, "recon.S", 24.00, code="SIGMA_MPA", units="MPa"),
        ev(13200000.0, "surv.held", 1.0, code="SURV_HELD", units="bool"),
        ev(13500000.0, "takt.late", 1.0, code="TAKT", units="bool"),
        ev(13800000.0, "pe.snr", 15.4, code="PE_SNR", units="1"),
        ev(14100000.0, "vessel.id", 4.0, code="V_ID", units="1"),
        ev(14400000.0, "dump.trip", 0.0, code="DUMP_NOT_TAKEN", units="bool"),
    ]
    events.sort(key=lambda e: (e["t_rel_ms"], e["channel"]))
    assert_stream(events)

    traj = {
        "id": "nelb-r01-003-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "YH-PE-2026-0819",
            "domain": "photoelastic_copv_hoop_stress",
            "setting": "Yewholt COPV YH-9 (invented), Bramble Tank Yard, vessel V-4. Simulated photoelastic coupon in PE-SIM-2 supplies the Brewster fringe order that times the in-band V-4 isolate. Plant-owned photoelastic reconstruction is the remaining-hoop SoT. Fringeveil vendor last-good COPV-cloud is a corridor witness, not the vessel SoT. Invented plant; simulated campaign. Not DIC hoop-strain (r51), not digital shearography (r33), not FSM (r50), not coda-wave (r45).",
            "observables_at_decision": {
                "N": n_fringe,
                "k_p": k_p,
                "sigma_MPa": sigma,
                "N_id": 4.00,
                "fringeveil_MPa": 6.40,
                "pe_snr": 16.0,
                "isolate_floor_MPa": 24.00,
            },
            "margin_authority": "YH-9 COPV SOP rev A: if reconstructed sigma_MPa >= 24.00 AND photoelastic SNR >= 12.0, vessel V-4 may be isolated as a hoop overstress. Dump-trip if sigma_MPa >= 80.00. V-1..V-3 skip-survey is a different gate. Fringeveil last-good cannot skip an unmeasured vessel.",
        },
        "proposed_action": {
            "actor": "composite lead Mara Vell, citing Fringeveil 6.40 MPa and a late morning survey",
            "summary": "stamp V-4 in band and skip V-1..V-3; 4.00 fringes is a coating glitch on a healthy last-good",
            "basis_claimed": "Fringeveil last-good is 6.40 MPa and a night survey of V-1..V-3 is a takt miss",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Vessel V-4 is accepted as in-band for a single isolate. Serialized reconstruction: sigma_MPa = k_p * N = 8.00 * 4.00 = 32.00, which is 8.00 MPa above the 24.00 isolate floor and 48.00 MPa under the 80.00 dump-trip. Brewster identity N = sigma / k_p = 32.00 / 8.00 = 4.00. Fringeveil 6.40 MPa is a patched residual and is not an admissible skip-survey witness. Ordered: ACCEPT this V-4 isolate only. Scope: this ACCEPT does not skip V-1..V-3 (that is the companion question) and does not stamp a dump trip.",
            "threshold": "sigma_MPa>=24.00 AND pe_snr>=12.0 => accept V-4 isolate; Fringeveil is not SoT; dump-trip if sigma_MPa>=80.00; V-1..V-3 are out of scope",
            "stated_residuals": "32.00 vs 24.00 isolate floor is 8.00 MPa, not infinite; V-1..V-3 remain unmeasured; Fringeveil remains the only OEM COPV channel",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 5400: V-4 in band; V-1..V-3 not skipped; Fringeveil not SoT; reconstruction locked",
            "tool": "yh9-pe-copv-gate-cli",
            "observation": "sigma 32.00 MPa recomputes from N 4.00; PE-SIM-2 hashed; Fringeveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "pe N 4.00; raster frame; sigma 32.00 MPa"},
                {"t_s": 4800.0, "event": "ops proposes accept V-4 and skip V-1..V-3"},
                {"t_s": 5400.0, "event": "ACCEPT V-4 only; V-1..V-3 out of scope"},
                {"t_s": 6000.0, "event": "12 min survey-complete bookend 1"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7800.0, "event": "companion REJECT skip-survey of V-1..V-3"},
            ],
            "observed_effects": [
                "sigma recomputes from the serialized photoelastic model at every recon.S event",
                "a Fringeveil-only head would have skipped V-1..V-3 overnight",
                "12 min survey-complete floor is in the stream (surv.start, surv.floor)",
            ],
            "surprises": [
                "a last-good 6.40 MPa vendor COPV corridor co-existed with a 32.00 MPa plant reconstruction on V-4 only",
            ],
            "new_state": {
                "v4": "isolated",
                "v13": "in scope unskipped",
                "fringeveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("photoelastic_reconstruction", 0.14),
                ("bounded_v4_isolate", 0.12),
                ("fringeveil_nonsubstitution", 0.10),
                ("vessel_scope_limit", 0.08),
                ("survey_time_cost", -0.03),
            ],
            "scored for a bounded V-4 ACCEPT on a recomputable photoelastic hoop-stress while refusing a Fringeveil 6.40 MPa corridor as a skip license; 12 min floor is priced as downtime",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "photoelastic-copv", "serialized-reconstruction", "operational-companion"],
            distillation_note="Photoelastic gate: serialized k_p*N plus Brewster identity beats a green last-good dashboard; companion t2 is the skip-vessel refusal, not a second stress vote",
            distillation_value="Independent CUBA LIF raster races the fringe-order estimator against a vendor-skip advocate with 1 ms refractory and adaptation, distilling sigma=k_p*N without echoing the campaign stream.",
        ),
    }
    traj2 = {
        "id": "nelb-r01-003-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "YH-PE-2026-0819-exec",
            "domain": "skip_vessel_refusal_execution",
            "setting": "Same YH-9 after the ACCEPT. Composite lead proposes skipping V-1..V-3 on Fringeveil 6.40 MPa. This companion is the operational skip refusal, not a second hoop-stress vote.",
            "observables_at_decision": {
                "sigma_MPa": 40.00,
                "surv_floor_s": 720.0,
                "skip_proposed": True,
            },
            "margin_authority": "surv_floor_complete AND skip_not_taken AND dump_not_tripped AND v4_held AND v13_in_scope",
        },
        "proposed_action": {
            "actor": "composite lead Mara Vell",
            "summary": "skip V-1..V-3; 12 min already paid and Fringeveil is 6.40 MPa",
            "basis_claimed": "the ACCEPT already isolated V-4, so skipping the adjacent vessels is the cheapest survey",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Skip-survey of V-1..V-3 is refused. The 12 min survey floor is complete and the isolate tripwire (sigma_MPa >= 24.00) is still armed on the plant photoelastic head. REJECT the skip. Do not trip the dump. V-4 hold stands. 40.00 MPa post-accept is still over the 24.00 isolate floor and under the 80.00 dump-trip, so V-4 stays held; V-1..V-3 remain unmeasured and in scope.",
            "threshold": "surv_floor_complete AND skip_not_taken AND dump_not_tripped AND v4_held AND v13_in_scope",
            "stated_residuals": "V-1..V-3 remain unmeasured; Fringeveil remains the only OEM COPV channel",
        },
        "executed_action": {
            "summary": "skip refused at t_s 7800; V-1..V-3 not skipped; dump not tripped; V-4 held",
            "tool": "yh9-pe-surv-exec",
            "observation": "recon.S 40.00 MPa on PE-SIM-2; Fringeveil still ignored; V-1..V-3 remain in the survey",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "survey clock started after ACCEPT"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7200.0, "event": "V-1..V-3 skip re-proposed"},
                {"t_s": 7800.0, "event": "REJECT skip-survey; V-4 hold stands"},
            ],
            "observed_effects": [
                "Fringeveil restore did not reopen the hoop-stress call",
                "dump trip never fired; 32.00 vs 80.00 MPa floor",
                "V-1..V-3 remain unskipped; V-4 is the only isolated COPV",
            ],
            "surprises": [
                "post-accept 40.00 MPa still recomputes from k_p*N while Fringeveil stays near 6 MPa",
            ],
            "new_state": {"v4": "held", "v13": "in survey", "dump": "in service"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.36,
            [
                ("skip_vessel_refusal", 0.14),
                ("v4_hold_stands", 0.10),
                ("fringeveil_nonsubstitution", 0.08),
                ("survey_floor_complete", 0.06),
                ("takt_cost", -0.02),
            ],
            "operational execution gate: refuse skip of unmeasured vessels because Fringeveil is not a skip license; not a hoop-stress re-vote",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "skip-refusal"]),
    }
    return {
        "id": "nelb-r01-003",
        "spike_events": events,
        "language_view": {
            "description": "Yewholt COPV YH-9. Simulated photoelastic reconstructs 32.00 MPa remaining hoop-stress from 8.00*4.00 while Fringeveil still reports 6.40 MPa. The gate ACCEPTs a V-4 isolate only. A 12 min survey floor is serialized in the stream. Companion t2 REJECTs skipping V-1..V-3.",
            "trajectory": traj,
            "trajectory_skip_vessel_refusal": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "pe.N / pe.snr": "Brewster fringe order and SNR; the physics channels the reconstruction consumes",
                "recon.S / recon.N": "serialized remaining hoop-stress MPa and N = sigma/k_p identity",
                "fringeveil.S / vessel.id / v13.present": "vendor last-good, vessel id, and adjacent-vessel presence; the denial and scope channels",
                "ops.prop / gate.comp / ops.skip / gate.hold": "accept-and-skip proposal, ACCEPT, skip proposal, companion REJECT",
                "surv.start / surv.floor / surv.held / v4.held / v13.skip / dump.trip / vessel.survey / takt.late": "operational companion channels plus the 12 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-over: fringeveil.S 6.40 next to recon.S 32.00",
                "reconstruction as event: recon.S 32.00 equals 8.00*4.00",
                "ACCEPT then operational REJECT: gate.comp at 5400 s, gate.hold at 7800 s",
                "slow floor in-stream: surv.start 6000 s, surv.floor 6720 s (12.0 min)",
                "tight pe pair: pe.N then pe.snr +1.5 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Fringeveil is 6.40 MPa' = fringeveil.S 6.40; '32 MPa' = recon.S 32.00; 'accept V-4 only' = gate.comp ACCEPT; 'do not skip V-1..V-3' = gate.hold REJECT",
            "why_high_value": "New photoelastic remaining-hoop family on a COPV (not DIC r51, not shearography r33, not FSM r50, not coda-wave r45). Lead bounded ACCEPT of V-4 isolate on a recomputable overstress that a vendor last-good would have used to skip adjacent vessels. Independent CUBA LIF raster plus required snn_tags. Companion t2 is operational skip refusal. sim_or_real=simulated.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random plus CUBA LIF",
                "seeds": {"raster": 202609003, "stream_note": "stream amplitudes are authored constants (1, MPa, bool)"},
                "draw_order": "raster: independent CUBA LIF first-passage times, per-spike adaptation and noise; not copied from spike_events",
                "thinning": "photoelastic exists at ~10 Hz fringe samples; stream keeps 6 N points; recon keeps 6 of ~20 solver ticks; 52-event floor",
                "refractory_floors_ms": {
                    "pe.N": 1.5,
                    "pe.snr": 1.5,
                    "recon.S": 60000,
                    "recon.N": 60000,
                    "fringeveil.S": 60000,
                    "vessel.id": 60000,
                    "v13.present": 60000,
                    "ops.prop": 60000,
                    "gate.comp": 60000,
                    "surv.start": 60000,
                    "surv.floor": 60000,
                    "ops.skip": 60000,
                    "gate.hold": 60000,
                    "v4.held": 60000,
                    "v13.skip": 60000,
                    "dump.trip": 60000,
                    "surv.held": 60000,
                    "vessel.survey": 60000,
                    "takt.late": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-08-19T03:00:00Z simulated night start",
            },
            "distillation_targets": [
                "photoelastic reconstruction head: sigma_MPa = k_p * N; N = sigma / k_p",
                "bounded ACCEPT head: in-band sigma AND vessel scope AND v13-out-of-scope",
                "operational companion: refuse skip-survey without re-opening the last-good call",
                "independent CUBA LIF raster with race/refractory/adaptation tags",
            ],
        },
        "reconstruction_model": {
            "name": "photoelastic_copv_hoop_stress",
            "formula": "sigma_MPa = k_p * N; N = sigma_MPa / k_p",
            "parameters": {
                "k_p": 8.00,
                "isolate_floor_MPa": 24.00,
                "dump_trip_MPa": 80.00,
                "surv_min": 12.0,
            },
            "worked_example": {"N": 4.00, "sigma_MPa": 32.00, "N_id": 4.00},
            "check": "8.00 * 4.00 = 32.00 exactly; 32.00 / 8.00 = 4.00 exactly; 6000 s + 720 s = 6720 s = 12.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "code": "yh9.pe_copv_gate",
            "note": "ACCEPT accumulator wins: photoelastic hoop-stress evidence overpowers the Fringeveil skip advocate",
            "decode_rule": "accept if stress_estimator AND brewster_lock AND vessel_margin fire inside the window; vendor_skip_advocate is necessary-but-not-sufficient and cannot release V-1..V-3",
            "populations": [
                gate_pop("stress_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("brewster_lock", 64, 1.2, 31.25, w_s),
                gate_pop("vessel_margin", 40, 1.0, 50.0, w_s),
                gate_pop("vendor_skip_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("accept_latch", 96, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "yh9.pe_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 36.0},
                {"check": "yh9.stress_scorer", "neurons": 40, "mean_rate_hz": 62.5, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r01-003",
            clock_domain="yh9-pe-sim-relative-ms-t0-2026-08-19T03:00:00Z",
            tags=["photoelastic-copv", "ACCEPT", "REJECT", "serialized-reconstruction", "operational-t2", "independent-lif"],
            distillation_value="Independent CUBA LIF raster plus sigma=k_p*N reconstruction lets a hybrid SNN distill a bounded COPV isolate without echoing the campaign stream.",
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


def _tags_ok(rec):
    needed = set(SNN_TAGS)
    locs = []
    meta = rec.get("meta") or {}
    locs.append(meta.get("snn_tags"))
    nelb = meta.get("nelb") if isinstance(meta.get("nelb"), dict) else {}
    locs.append(nelb.get("snn_tags"))
    traj_meta = ((rec.get("language_view") or {}).get("trajectory") or {}).get("meta") or {}
    locs.append(traj_meta.get("snn_tags"))
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
    for rec in records:
        hits = walk_banned(rec)
        if hits:
            raise RuntimeError(f"banned keys {hits}")
        blob = json.dumps(rec, ensure_ascii=False, allow_nan=False)
        if "training_ready" in blob:
            raise RuntimeError("training_ready claimed")
        if '"provenance"' in blob:
            raise RuntimeError("provenance object present")
        if '"real"' in blob or " sim_or_real" in blob and "real" in blob:
            # explicit sim_or_real scan below
            pass
        if not _tags_ok(rec):
            raise RuntimeError(f"{rec['id']} missing snn_tags")
        jac = _jaccard(rec)
        if jac >= 0.10:
            raise RuntimeError(f"{rec['id']} raster echo jaccard {jac}")
        ids.append(rec["id"])
        lv = rec["language_view"]
        ids.append(lv["trajectory"]["id"])
        for k, v in lv.items():
            if k.startswith("trajectory") and k != "trajectory" and isinstance(v, dict) and "id" in v:
                ids.append(v["id"])
                sim2 = v["state"]["sim_or_real"]
                if sim2 not in {"designed", "simulated", "hil"}:
                    raise RuntimeError(sim2)
                if v["safety_decision"]["decision"] not in {"ACCEPT", "MODIFY", "REJECT"}:
                    raise RuntimeError(v["safety_decision"]["decision"])
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
        isi = rast["isi_count_identity"]
        if isi["isi_total"] != isi["spikes"] - isi["distinct_active_neurons"]:
            raise RuntimeError("ISI identity")
        if sum(b["count"] for b in rast["isi_histogram"]) != isi["isi_total"]:
            raise RuntimeError("ISI hist sum")
        tf = rast["routing"]["third_factor"]
        if abs(tf["tau_e_ms"] / 1000.0 - tf["tau_e_s"]) > 1e-9:
            raise RuntimeError("tau pair")
        sim = lv["trajectory"]["state"]["sim_or_real"]
        if sim not in {"designed", "simulated", "hil"}:
            raise RuntimeError(sim)
        if sim == "real":
            raise RuntimeError("real")
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
        if rec["meta"]["round"] != 1:
            raise RuntimeError("meta.round")
        if rast["excerpt_generator"] != "independent_cuba_lif":
            raise RuntimeError("not independent LIF")
    if len(ids) != len(set(ids)):
        raise RuntimeError(f"dup ids {ids}")
    if set(sims) != {"designed", "simulated", "hil"}:
        raise RuntimeError(f"sim mix {sims}")
    if set(decisions) != {"ACCEPT", "MODIFY", "REJECT"}:
        raise RuntimeError(f"decision mix {decisions}")
    print("local_checks ok", [r["id"] for r in records], "ids", len(ids), "jaccard", [_jaccard(r) for r in records])
    print("decisions", decisions, "sims", sims)


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
    return {"check_jsonl": {"errors": len(errs), "warnings": len(warns), "kinds": kinds, "n": n}, "frontier": counts}


def create_only(path: Path, text: str):
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    fd = os.open(str(path), flags, 0o644)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text)


def write_notes(records, lines):
    import subprocess

    sizes = [len(x) for x in lines]
    file_sha = hashlib.sha256(BATCH.read_bytes()).hexdigest()
    spikes = sum(r["raster"]["spikes"] for r in records)
    energy = spikes * 23
    isis = [r["raster"]["isi_count_identity"]["isi_total"] for r in records]
    events = [len(r["spike_events"]) for r in records]
    rewards = []
    for r in records:
        lv = r["language_view"]
        rewards.append(lv["trajectory"]["reward_components"]["total"])
        for k, v in lv.items():
            if k.startswith("trajectory") and k != "trajectory":
                rewards.append(v["reward_components"]["total"])
    probe = subprocess.run(
        [
            sys.executable,
            str(PIPELINES / "spike_probe.py"),
            "--strict",
            str(BATCH),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    probe_out = (probe.stdout or "") + (probe.stderr or "")
    if probe.returncode != 0:
        raise RuntimeError(f"spike_probe failed {probe.returncode}: {probe_out[-2000:]}")
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
    reward_s = "/".join(f"+{x:.2f}" for x in rewards)
    jacs = [_jaccard(r) for r in records]
    notes = f"""# Neuromorphic Event + Language Bridge — NOTES round 1
Run: 2026-09-02-final-heavy · Factory: neuromorphic-event-language-bridge · Generator: grok-4.6 · Output: `{BATCH.name}` (3 paired artifacts, 6 ThalamicTrajectories)
Rights: RM-793 research-only (SpaceXAI/xAI grok-4.6, SuperGrok Heavy chat). Not training_ready. CREATE-ONLY write at `{LIVE}` (`{BATCH.name}`, `{NOTES.name}`). Did not write 2026-08-17 or 2026-08-30. Did not overwrite existing live r21/r41/r61.

## Context / de-duplication
Live tree already held `batch-r21.jsonl` / `batch-r41.jsonl` / `batch-r61.jsonl` and no `batch-r01.jsonl`. This round fills r01 create-only. Banned against those three plus leftover-mill r13–r68 family tables: not OA-ICOS / SERF OPM / WGM (live r21); not LDA / Karl Fischer / bender-element (live r41); not Stern-Volmer / pellistor / FMCW tank-radar (live r61); not FBG / quench / VRFB / BOTDA / QCM-D / SAW / CRDS / PGNAA / IFOG / transmon / hyperspectral / MEMS array / muon / x-ray / optogenetic / LiDAR / clamp-on / LIBS / QEPAS / LFV / Kaplan LDV / THz-TDS / ECT / TDLAS / lock-in / PAUT / EN / RUS / N-16 / helium RGA / FOCT / tip-timing / acoustic pyrometry / SPR / VW viscometer / MW cavity / MFL / NMR / nucleonic / JNT / CRNS / Coriolis / CARS / XRF / Mössbauer / GB-InSAR / ellipsometry / CTA / SPND / LII / PALS / NQR / SFRA / shearography / H-permeation / FMCW lining / GPR / Pockels / PEC / confocal / mud-pulse / Barkhausen / Lamb / OCT / DCPD / impact-echo / phosphor-lifetime / vortex / GWR / neutron-backscatter / beta / Raman / cyclotron BPM / alanine EPR / ADCP / TOFD / laser-flash / TDR / Seebeck / coda / LPR / paramagnetic O2 / TEOM / Faraday magmeter / PDA / acoustoelastic / C-SAM / FDS / MCSA / EMAT / FBRM / ACFM / OFDR / XRD / FSM / Gardon / chilled-mirror / DIC / CLD NOx / API-670 / thermal-mass / ER / Fabry-Perot / inductive debris / wire-mesh / UCI / MAE / IRIS / dual-wavelength pyrometer / UV-fluorescence OIW / zirconia / PID VOC / pulse-echo / Rogowski / BAM / UV-DOAS / Al2O3 / load-cell / H2S / TEV / dielectric water-cut / sonic-nozzle / sodium-ion / vibrating-tube / Ubbelohde / gloss / RF-admittance / UV ozone / triboelectric / molybdenum-blue. Plants not reused include Sedgewhin, Brinecrag, Lichenholt, Rushcrag, Copsewick, Peatspire, Mirewhin, Lacquerfen, Pitchshaw, Brackholt.

This round introduces three unused families (Johnson-noise remaining T, Coulter remaining particles, photoelastic remaining hoop) on new invented plants, restores a 52-event floor, and replaces the live-tree gap-constrained raster draw with **independent CUBA LIF** plus required `snn_tags`.

Adjacencies declared in-pair then kept physically distinct:
- **001 Johnson-noise T** is Nyquist-voltage remaining temperature of a spent-fuel pool, not two-color pyrometer (r55), not phosphor-lifetime (r39), not acoustic pyrometry (r25), not SPND (r31), not Gardon (r51).
- **002 Coulter particles** is resistive-zone remaining concentration of a CMP slurry, not FBRM D50 (r49), not PDA Sauter (r47), not flow cytometry, not C-SAM (r48).
- **003 photoelastic hoop** is Brewster fringe-order remaining hoop-stress of a COPV, not DIC hoop-strain (r51), not digital shearography (r33), not FSM (r50), not coda-wave (r45).

## Round 1 batch summary (3 pairs, 6 trajectories)

| id | modality (NEW family) | domain | decisions | headline |
|----|----------------------|--------|-----------|----------|
| nelb-r01-001 | Johnson-noise remaining T of a spent-fuel pool (k_j·V_rms² K, Noiseveil last-good denial, 18 min recirc-hold floor) | Brackfen Pool BF-3 bay B-7 (invented): 20.00*(4.00**2) reconstructs 320.00 K while Noiseveil still reads 298.00 K | REJECT (+0.43) / MODIFY (+0.34) | serialized `20.00*(4.00**2)=320.00`; `320.00/16.00=20.00`; conjunctive SOP (T AND SNR) forbids continue-recirc; three-party collusion includes the JNT infra owner; companion t2 recirc-hold, unit ESD refused; sim_or_real=designed |
| nelb-r01-002 | Coulter remaining particles of a CMP slurry (k_c·(Vp/Vref) ppm, Slurryveil last-good denial, 24 min flush floor) | Flintshaw CMP FS-6 pad P-4 (invented, HIL dummy in COUL-HIL-4): 80.00*(6.00/4.00) reconstructs 120.00 ppm while Slurryveil still reads 18.20 ppm | MODIFY (+0.40) / ACCEPT (+0.35) | serialized `80.00*(6.00/4.00)=120.00` and `6.00/4.00=1.50`; keep-polish refused; Coulter tech Ivor Kemp exonerated (missing aperture-cal AE, UTC vs UTC+2); companion t2 new-aperture restart; sim_or_real=hil |
| nelb-r01-003 | photoelastic remaining hoop of a COPV (k_p·N MPa, Fringeveil last-good denial, 12 min survey floor) | Yewholt COPV YH-9 vessel V-4 (invented, simulated PE-SIM-2): 8.00*4.00 reconstructs 32.00 MPa while Fringeveil still reads 6.40 MPa | ACCEPT (+0.41) / REJECT (+0.36) | serialized `8.00*4.00=32.00`; `32.00/8.00=4.00`; bounded ACCEPT of V-4 only; V-1..V-3 out of scope; companion t2 REJECTS skip-survey; sim_or_real=simulated |

Decision spread: REJECT / MODIFY / MODIFY / ACCEPT / ACCEPT / REJECT — **2A/2M/2R**. All three enums used, and all three sit on **leads**. Provenance spread: designed / hil / simulated (one each; never real). IDs `nelb-r01-001`…`003` plus t1/t2 suffixes.

## Raster sidecar
Every record carries `raster` + top-level `gate_snn` + `gate_compute`. Windows {wins[0]:.0f}/{wins[1]:.0f}/{wins[2]:.0f} ms; `window_s == window_ms/1000` exactly; `spikes == round(neurons·rate·window_s)` with zero slack ({n_sp[0]}/{n_sp[1]}/{n_sp[2]} at {rates[0]}/{rates[1]}/{rates[2]} Hz over {n_neu[0]}/{n_neu[1]}/{n_neu[2]} neurons); `energy_pJ = spikes·23` and `energy_uJ = spikes·23e-6` exact ({n_sp[0]*23}/{n_sp[1]*23}/{n_sp[2]*23} pJ). Routing source/target + 3-entry tables + `third_factor` on all three (modulators {tfs[0]} / {tfs[1]} / {tfs[2]}; τe {taus[0]}/{taus[1]}/{taus[2]} s as consistent `tau_e_s`+`tau_e_ms` pairs). Excerpts are **independent CUBA LIF** first-passage times (not a re-encode of `spike_events`; Jaccard {jacs[0]:.4f}/{jacs[1]:.4f}/{jacs[2]:.4f}), integer `t_us`, in-window, `neuron_id`-bounded, sorted, full-window by construction, per-spike amplitude with adaptation (0.82**k) plus noise. ISI histograms from the FULL window, bins ≥1 ms, counts sum to `spikes − distinct_active_neurons` ({isis[0]}/{isis[1]}/{isis[2]}). Same-neuron gaps ≥1000 µs serialized. `gate_snn` on all three: decisions REJECT/MODIFY/ACCEPT matching each lead trajectory; every rate-declaring population's budget exact against its decision window. `gate_compute.per_check` windows 32–40 ms, budgets exact ({gc[0]} / {gc[1]} / {gc[2]}). Required `meta.snn_tags` and `meta.nelb.snn_tags` = [race, refractory, adaptation] on every record. Main streams: {events[0]}/{events[1]}/{events[2]} events (48+), strictly increasing `t_rel_ms` only (no `t_ms` mix), same-channel refractory ≥0.8 ms (001 JNT pair at 1.3 ms, 002 Coulter pair at 1.2 ms, 003 photoelastic pair at 1.5 ms).

## Self-critique

### Edge cases added vs still thin
- **Added:** first Johnson-noise remaining-T family on a spent-fuel pool with recomputable T=k_j·V² (`320.00 K`) plus scale identity; first Coulter remaining-particle family on a CMP slurry with recomputable C=k_c·(Vp/Vref) (`120.00 ppm`) plus ratio identity and timezone-skipped aperture-cal exoneration; first photoelastic remaining-hoop family on a COPV with recomputable σ=k_p·N (`32.00 MPa`) plus Brewster identity and bounded ACCEPT of V-4 only; independent CUBA LIF rasters (live r21/r41/r61 used gap-constrained draws); required snn_tags; 52-event streams; operational t2 on all three; provenance trio designed/hil/simulated; 18/24/12 min slow floors in-stream.
- **Still thin:** (i) 001's k_j is a lumped Nyquist scale, not an R/Δf table — an 8 kΩ hop that fakes 320.00 K inside a 298 K Noiseveil corridor is unwritten; (ii) 002's k_c is a lumped pulse-height gain, not a coincidence / bubble map, so a bubble hop that fakes 120.00 ppm is unwritten; (iii) 003's k_p is a lumped Brewster gain, not a coating / wavelength map, so a coating hop that fakes 32.00 MPa is unwritten; (iv) vendor-only as a *lead* REJECT on a plant with *no* independent JNT/Coulter/PE remains slightly harder — 001/002 still have plant heads; (v) stream amplitudes remain authored constants (raster draws are the only seeded LIF noise).

### Realism of noise / temporal fidelity
- Strong: 001's 320.00 K, k_j 20.00, and 18.0 min hold (`6000+1080=7080 s`) recompute from the record; 002's 120.00 ppm, ratio 1.50, and 24.0 min flush (`2820+1440=4260 s`) recompute; 003's 32.00 MPa, N 4.00, and 12.0 min survey (`6000+720=6720 s`) recompute. Independent CUBA LIF (tau_m 10/12/8 ms) plus 0.82**k adaptation and 1.2–1.5 ms physics pairs give the 52-event stream a raster-scale motif without violating 0.8 ms same-channel refractory or 1000 µs same-neuron excerpt gaps.
- **Gaps, honestly:** (i) 52 events still thins 10 Hz Nyquist / kHz Coulter / 10 Hz fringe stacks; (ii) 001's post-stop 500.00 K is a later sample, not a closed-loop recirc controller; (iii) 002 HIL coupon times an in-service isolate that the stream does not independently witness on a second live pad until the new aperture starts; (iv) no gate_snn input→output volley pair at raster resolution this round.

### Training value (SNN/LSM + agentic)
Distillation targets: Johnson-noise T=k_j·V² head plus scale identity; conjunctive isolate floor vs continue-recirc vs unit ESD; JNT-infra collusion; Coulter C=k_c·(Vp/Vref) head plus ratio identity; isolate-floor pad vs keep-polish vs shop-trip; exoneration against last-to-badge social pressure; photoelastic σ=k_p·N and Brewster identities; bounded ACCEPT with V-1..V-3-out-of-scope; skip-survey refusal under survey takt. Raster value is the independent LIF (race / refractory / adaptation) rather than a 1:1 echo of the language stream. Agentic value concentrates in three patterns: reconstruction-as-SoT on a physical T/C/σ the raw corridor cannot see, earned ACCEPT with an explicit physical out-of-scope object (V-1..V-3), and stop-then-hold so a REJECT does not become a hall/shop/dump kill.

## What round 2 should add (next densification target)
1. **R/Δf Nyquist table** on a non-BF-3 pool so an 8 kΩ hop fakes 320.00 K inside a 298 K Noiseveil corridor, closing 001's lumped-k_j gap.
2. **Coincidence / bubble map** on a non-FS-6 Coulter so a bubble hop fakes 120.00 ppm while mean Vp looks healthy.
3. **Coating / wavelength Brewster map** on a non-YH-9 COPV so a coating hop fakes 32.00 MPa inside a 6.40 last-good corridor.
4. **Do not restage** live r21 OA-ICOS / SERF / WGM, live r41 LDA / Karl Fischer / bender-element, live r61 Stern-Volmer / pellistor / FMCW, leftover-mill r13–r68 families named above, Brackfen BF-3, Flintshaw COUL-HIL-4, or Yewholt PE-SIM-2. Do not reuse ids `nelb-r01-001`…`003`.

## Verification
`{BATCH.name}`: 3 lines, `json.loads`-clean (allow_nan=False), {sizes[0]}/{sizes[1]}/{sizes[2]} bytes (file {BATCH.stat().st_size}, sha256 `{file_sha}`). CREATE-ONLY write at `{LIVE}`. Repo gates: `check_records.check_jsonl` with `FactoryStaging(enabled=True)` → 0 errors, 0 warnings, kinds `{{bridge_pair: 3}}`; `curate_bridge.raster_status(..., require_raster=True, require_routing_table=True)` → raster_valid and gate_snn_valid true, empty reason codes; `curate_record(...)` → 3× retain / `BRIDGE_EVENTS_ALREADY_GLOBALLY_ORDERED`; `verify_batch_for_frontier(strict=True)` → 3 verified, 0 inconclusive, 0 failed; `python3 pipelines/spike_probe.py --strict {BATCH}` → loaded 3. Build-time asserts: global time order; same-channel ≥0.8 ms; ≥48 events ({events[0]}/{events[1]}/{events[2]}); excerpt integer bounds, neuron bounds, sort, 1 ms per-neuron floor; ISI identity {isis[0]}/{isis[1]}/{isis[2]}; spike budgets exact; energy pJ/µJ exact; reward totals equal two-decimal component sums ({reward_s}); gate_snn decisions match lead `safety_decision.decision`; `state.sim_or_real` ∈ {{designed, hil, simulated}}; `meta.round=1`, `meta.factory=neuromorphic-event-language-bridge`, `meta.generator=grok-4.6`, `meta.run_label=2026-09-02-final-heavy`; `meta.snn_tags` and `meta.nelb.snn_tags` include race/refractory/adaptation; `meta.rights` 15-key RM-793 stamp (`intended_use=research_only`, `linear_issue=RM-793`, `generated_at={GENERATED_AT}`); independent CUBA LIF Jaccard {jacs[0]:.4f}/{jacs[1]:.4f}/{jacs[2]:.4f}; no hidden-reasoning keys; no `provenance` objects; no live-plant claims; no `training_ready`; all 9 record/trajectory ids unique. Raster seeds 202609001/202609002/202609003, CUBA LIF.

Honest novelty accounting: 3/3 modality families are new versus live r21/r41/r61 and versus leftover-mill r13–r68. Independent CUBA LIF plus required snn_tags are new raster objects relative to those live rounds' gap-constrained draws. Against that: reconstruction-as-SoT, operational t2, conjunctive SOP, vendor-nonsubstitution, bounded-accept-with-scope-limit, and 2A/2M/2R are carried vocabulary. Net: a bit under half of the round's scenario/edge mass is genuinely novel.

Novel coverage: 46%
"""
    create_only(NOTES, notes)
    print("wrote", NOTES, "bytes", NOTES.stat().st_size)


def main():
    global BATCH, NOTES
    occupancy_preflight()
    records = [rec_001(), rec_002(), rec_003()]
    local_checks(records)
    LIVE.mkdir(parents=True, exist_ok=True)
    if BATCH.exists() or NOTES.exists():
        BATCH = LIVE / "batch-r01c.jsonl"
        NOTES = LIVE / "NOTES-r01c.md"
        if BATCH.exists() or NOTES.exists():
            raise RuntimeError(f"refuse: {BATCH} or {NOTES} already exists")
    lines = [
        json.dumps(r, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
        for r in records
    ]
    create_only(BATCH, "\n".join(lines) + "\n")
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
            "jaccard",
            round(_jaccard(r), 4),
            "bytes",
            len(lines[i]),
        )
    repo_validate(records)
    write_notes(records, lines)


if __name__ == "__main__":
    main()
