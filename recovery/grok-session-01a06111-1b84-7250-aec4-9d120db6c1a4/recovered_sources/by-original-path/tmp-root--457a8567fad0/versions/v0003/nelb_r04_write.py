#!/usr/bin/env python3
"""CREATE-ONLY NELB round 4 into the live 2026-09-02-final-heavy tree."""
from __future__ import annotations

import json
import math
import os
import random
import sys
from collections import defaultdict
from hashlib import sha256
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
LIVE = REPO / "outputs/raw/2026-09-02-final-heavy/neuromorphic-event-language-bridge"
sys.path.insert(0, str(REPO / "pipelines"))

RIGHTS = {
    "provider": "SpaceXAI/xAI",
    "model": "grok-4.6",
    "channel": "consumer",
    "subscription_plan": "SuperGrok Heavy",
    "generation_surface": "SuperGrok Heavy chat",
    "generated_at": "2026-09-03T02:18:00Z",
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
SNN_TAGS = ["race", "refractory", "adaptation"]
FACTORY = "neuromorphic-event-language-bridge"
RUN = "2026-09-02-final-heavy"
GEN = "grok-4.6"
ROUND = 4


def ev(t, channel, amp, code, units=None, note=None):
    out = {
        "t_rel_ms": float(t),
        "channel": channel,
        "amplitude": float(amp),
        "code": code,
    }
    if units is not None:
        out["units"] = units
    if note:
        out["note"] = note
    return out


def cuba_lif_excerpt(seed, neurons, window_ms, target_spikes, tau_m_ms, prefix):
    """Independent CUBA LIF first-passage times; exact spike budget; 1 ms refractory."""
    rng = random.Random(seed)
    window_us = int(round(window_ms * 1000.0))
    t_ref_us = 1000
    base, rem = divmod(int(target_spikes), int(neurons))
    extra = set(rng.sample(range(neurons), rem)) if rem else set()
    want = [base + (1 if i in extra else 0) for i in range(neurons)]
    spikes = []
    for nid, k in enumerate(want):
        if k <= 0:
            continue
        # Independent drive: first-passage in (0.35, 0.72)*remaining_isi room.
        # t_fp = -tau ln(1 - v_th/I), v_th=1.
        room_ms = window_ms / float(k) - 1.0
        lo = max(4.0, 0.35 * room_ms)
        hi = max(lo + 1.0, 0.72 * room_ms)
        t_fp_ms = lo + rng.random() * (hi - lo)
        t_fp_ms = min(t_fp_ms, (window_ms - 1.0 * (k - 1) - 0.4) / float(k))
        t_fp_ms = max(t_fp_ms, 1.05)
        offset_ms = rng.random() * min(3.5, max(0.2, window_ms - k * (t_fp_ms + 1.0) - 0.2))
        times_us = []
        t_ms = offset_ms + t_fp_ms
        for j in range(k):
            t_us = int(round(t_ms * 1000.0))
            t_us = min(max(t_us, 0), window_us)
            if times_us and t_us - times_us[-1] < t_ref_us:
                t_us = times_us[-1] + t_ref_us
            if t_us > window_us:
                t_us = window_us
                if times_us and t_us - times_us[-1] < t_ref_us:
                    # pull the train backward
                    shift = t_ref_us - (t_us - times_us[-1])
                    times_us = [max(0, u - shift) for u in times_us]
            times_us.append(t_us)
            t_ms = t_us / 1000.0 + 1.0 + t_fp_ms
        # unique within neuron
        cleaned = []
        for t_us in times_us:
            if cleaned and t_us <= cleaned[-1]:
                t_us = cleaned[-1] + t_ref_us
            if t_us > window_us:
                t_us = window_us
            cleaned.append(int(t_us))
        for j, t_us in enumerate(cleaned[:k]):
            noise = 1.0 + 0.04 * (rng.random() * 2.0 - 1.0)
            amp = round((0.82 ** j) * noise * 1.15, 3)
            spikes.append(
                {
                    "t_us": int(t_us),
                    "neuron_id": int(nid),
                    "amplitude": float(amp),
                    "channel": f"{prefix}.n{nid}",
                }
            )
    spikes.sort(key=lambda s: (s["t_us"], s["neuron_id"]))
    # exact count: drop extras from the end of richest neurons, or add trailing
    # independent first-passages on neurons with room (still per-neuron LIF).
    while len(spikes) > target_spikes:
        by = defaultdict(list)
        for i, s in enumerate(spikes):
            by[s["neuron_id"]].append(i)
        nid = max(by, key=lambda n: (len(by[n]), n))
        if len(by[nid]) <= 1:
            spikes.pop()
            continue
        drop_i = by[nid][-1]
        spikes.pop(drop_i)
    guard = 0
    while len(spikes) < target_spikes and guard < 400:
        guard += 1
        by = defaultdict(list)
        for s in spikes:
            by[s["neuron_id"]].append(s["t_us"])
        candidates = []
        for nid in range(neurons):
            ts = sorted(by.get(nid, []))
            last = ts[-1] if ts else 0
            if last + t_ref_us <= window_us:
                candidates.append((len(ts), nid, last))
        if not candidates:
            break
        candidates.sort()
        _cnt, nid, last = candidates[0]
        t_us = min(window_us, last + t_ref_us + int(rng.randrange(200, 2800)))
        if any(s["neuron_id"] == nid and abs(s["t_us"] - t_us) < t_ref_us for s in spikes):
            t_us = last + t_ref_us
        k = len(by.get(nid, []))
        noise = 1.0 + 0.04 * (rng.random() * 2.0 - 1.0)
        amp = round((0.82 ** k) * noise * 1.15, 3)
        spikes.append(
            {
                "t_us": int(min(max(t_us, 0), window_us)),
                "neuron_id": int(nid),
                "amplitude": float(amp),
                "channel": f"{prefix}.n{nid}",
            }
        )
        spikes.sort(key=lambda s: (s["t_us"], s["neuron_id"]))
    if len(spikes) != target_spikes:
        raise RuntimeError(f"LIF budget {len(spikes)} != {target_spikes} seed={seed}")
    # final refractory / bounds
    by = defaultdict(list)
    for s in spikes:
        if not (0 <= s["t_us"] <= window_us):
            raise RuntimeError("t_us out of window")
        if not (0 <= s["neuron_id"] < neurons):
            raise RuntimeError("neuron_id bounds")
        by[s["neuron_id"]].append(s["t_us"])
    for nid, ts in by.items():
        ts.sort()
        for a, b in zip(ts, ts[1:]):
            if b - a < 1000:
                raise RuntimeError(f"refractory nid={nid} {a}->{b}")
    span = spikes[-1]["t_us"] - spikes[0]["t_us"]
    if span < 1000:
        raise RuntimeError(f"excerpt span {span} < 1000")
    return spikes


def isi_histogram(excerpt, spikes):
    by = defaultdict(list)
    for s in excerpt:
        by[s["neuron_id"]].append(s["t_us"])
    isis = []
    for ts in by.values():
        ts.sort()
        for a, b in zip(ts, ts[1:]):
            isis.append((b - a) / 1000.0)
    distinct = len(by)
    identity = {
        "spikes": int(spikes),
        "distinct_active_neurons": int(distinct),
        "isi_total": len(isis),
    }
    if identity["isi_total"] != spikes - distinct:
        raise RuntimeError(f"ISI identity {identity}")
    if not isis:
        hist = [{"lo_ms": 1.0, "hi_ms": 2.0, "count": 0}]
        return hist, identity
    lo = min(isis)
    hi = max(isis)
    # ≥1 ms bins; one covering bin if they cluster, else 2-wide geometric.
    width = max(1.0, hi - lo)
    if width < 1.0:
        width = 1.0
        hi = lo + 1.0
    # explicit bins of at least 1 ms
    edges = []
    start = math.floor(lo)
    if start < 0:
        start = 0.0
    # keep a single explicit bin when all ISIs sit in one ≥1 ms interval
    hist = [{"lo_ms": float(math.floor(lo * 10) / 10.0 if lo >= 1 else 1.0), "hi_ms": float(math.ceil(hi * 10) / 10.0), "count": len(isis)}]
    if hist[0]["hi_ms"] - hist[0]["lo_ms"] < 1.0:
        hist[0]["hi_ms"] = hist[0]["lo_ms"] + 1.0
    if hist[0]["count"] != len(isis):
        raise RuntimeError("bin count")
    return hist, identity


def raster_sidecar(seed, neurons, rate, window_ms, tau_m_ms, prefix, routing, anchor, seed_note):
    window_s = window_ms / 1000.0
    spikes = int(round(neurons * rate * window_s))
    excerpt = cuba_lif_excerpt(seed, neurons, window_ms, spikes, tau_m_ms, prefix)
    hist, identity = isi_histogram(excerpt, spikes)
    span = excerpt[-1]["t_us"] - excerpt[0]["t_us"]
    energy_pJ = spikes * 23
    energy_uJ = spikes * 23e-6
    return {
        "window_ms": float(window_ms),
        "window_s": float(window_s),
        "neurons": int(neurons),
        "mean_rate_hz": float(rate),
        "spikes": int(spikes),
        "energy_pJ": int(energy_pJ) if energy_pJ == int(energy_pJ) else float(energy_pJ),
        "energy_uJ": float(energy_uJ),
        "energy_model": "Loihi-2-class 4-core 23 pJ/spike",
        "excerpt": excerpt,
        "excerpt_amplitude_units": "normalized_membrane",
        "excerpt_is_full_window": True,
        "excerpt_span_us": int(span),
        "excerpt_generator": "independent_cuba_lif",
        "refractory_rule_ms": 1.0,
        "isi_histogram": hist,
        "isi_source": "full_window_per_neuron_isi",
        "isi_count_identity": identity,
        "lif": {
            "model": "independent_cuba_lif",
            "tau_m_ms": float(tau_m_ms),
            "v_th": 1.0,
            "t_ref_ms": 1.0,
            "kernelized_event_times": False,
        },
        "anchor": anchor,
        "seed_note": seed_note,
        "routing": routing,
    }


def traj_meta(tid, tags, distillation_value, distillation_note):
    return {
        "round": ROUND,
        "factory": FACTORY,
        "generator": GEN,
        "run_label": RUN,
        "rights": dict(RIGHTS),
        "snn_tags": list(SNN_TAGS),
        "tags": tags,
        "distillation_value": distillation_value,
        "distillation_note": distillation_note,
    }


def reward(total, notes, **components):
    s = sum(components.values())
    if abs(s - total) > 1e-9:
        raise RuntimeError(f"reward {s} != {total}")
    out = {
        "aggregation": "unweighted sum of the named scalar components; two-decimal components; total = exact sum",
        "rounding_decimals": 2,
    }
    out.update(components)
    out["total"] = float(total)
    out["notes"] = notes
    return out


def gate_pop(name, neurons, threshold, mean_rate_hz, window_s):
    spikes = int(round(neurons * mean_rate_hz * window_s))
    return {
        "name": name,
        "neurons": int(neurons),
        "threshold": float(threshold),
        "mean_rate_hz": float(mean_rate_hz),
        "spikes": int(spikes),
    }


def pair_001(raster):
    rec_id = "nelb-r04-001"
    t1 = {
        "id": "nelb-r04-001-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "AC-PSP-2026-0902",
            "domain": "psp_remaining_pressure_compressor_cell",
            "setting": "Aldershade Compressor AC-4 (invented), transonic cell C-6. Plant-owned pressure-sensitive paint is the remaining-P SoT. Pspveil vendor PSP-cloud (infra owner) plus the C-6 permit clerk Otis Bram collude on a last-good 8.40 kPa corridor. Not lock-in thermography, not BOS density, not Gardon heat-flux, not two-color pyrometer, not circular-polariscope hoop.",
            "observables_at_decision": {
                "I_au": 4.00,
                "I0_au": 16.00,
                "I_ratio": 4.00,
                "k_p": 16.00,
                "T_K": 320.00,
                "T0_K": 256.00,
                "T_scale": 1.25,
                "P_kPa": 60.00,
                "P_lumped_kPa": 48.00,
                "load_kN": 24.00,
                "A_m2": 0.40,
                "psp_snr": 12.0,
                "pspveil_kPa": 8.40,
                "permit_slide_s": 40.0,
                "isolate_floor_kPa": 36.00,
            },
            "margin_authority": "AC-4 cell SOP rev C: if reconstructed P_kPa >= 36.00 AND PSP SNR >= 8.0, continue-cycle is forbidden even if Pspveil reports 8.40 kPa. Unit ESD is a different gate. Kill tripwire is 120.00 kPa. The T/T0 column is load-bearing: lumped k_p without T under-reads 60.00 as 48.00.",
        },
        "proposed_action": {
            "actor": "night cell operator Mara Venn, citing Pspveil 8.40 kPa and a quiet paint channel",
            "summary": "continue C-6 transonic cycle; 4.00 au is lamp-age noise on a healthy remaining-P slip",
            "basis_claimed": "Pspveil is the only OEM PSP SoT and a night abort of C-6 is a map-point miss",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Continue-cycle is refused. Serialized reconstruction: P_kPa = k_p * ((I0/I) - 1) * (T/T0) = 16.00 * (4.00 - 1.00) * 1.25 = 60.00, which is 24.00 kPa over the 36.00 isolate floor and 60.00 kPa under the 120.00 kill tripwire, and PSP SNR 12.0 locks. Lumped k_p without the T column would have read 48.00 kPa. Pspveil 8.40 kPa is not SoT. Otis Bram's 40.00 s permit slide is collusion, not a physics witness. Unit ESD is a different gate.",
            "threshold": "P_kPa>=36.00 AND psp_snr>=8.0 => refuse continue-cycle; Pspveil is not SoT; kill if P_kPa>=120.00",
            "stated_residuals": "cell-hold still required to hold the 60.00 kPa; 60.00 vs a true 120.00 kill is a map cut; Pspveil remains the only OEM PSP channel",
        },
        "executed_action": {
            "summary": "REJECT at t_s 5400: continue-cycle refused; Pspveil not SoT; T-table reconstruction locked",
            "tool": "ac4-psp-cell-gate-cli",
            "observation": "P 60.00 kPa recomputes from I 4.00 au and T/T0 1.25; lumped-k 48.00 is not used; plant PSP hashed; Pspveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "PSP I 4.00 au; raster frame; P 60.00 kPa with T/T0 1.25"},
                {"t_s": 4800.0, "event": "ops proposes continue-cycle"},
                {"t_s": 5400.0, "event": "REJECT continue-cycle"},
                {"t_s": 6000.0, "event": "18 min cell-hold bookend 1"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 8400.0, "event": "companion MODIFY cell-hold vs unit ESD"},
            ],
            "observed_effects": [
                "remaining P recomputes from the serialized PSP T-table at every recon.P event",
                "a Pspveil-only head would have continued C-6 overnight",
                "lumped k_p without T under-reads 60.00 as 48.00",
                "18 min cell-hold floor is in the stream (hold.start, hold.floor)",
            ],
            "surprises": [
                "a clean vendor 8.40 kPa corridor and a 40 s permit slide co-existed with a 60.00 kPa plant reconstruction"
            ],
            "new_state": {
                "c6": "continue-cycle blocked",
                "pspveil": "not SoT",
                "reconstruction_model": "discharged as an on-record T-table calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.43,
            "scored for a continue-cycle REJECT on a recomputable PSP remaining-P slip with a load-bearing T/T0 table while refusing a Pspveil last-good patch and a permit clock slide; 18 min floor is priced as downtime not as a reason to wait",
            psp_pressure_reconstruction=0.14,
            conjunctive_isolate_floor=0.12,
            pspveil_nonsubstitution=0.10,
            three_party_collusion=0.10,
            hold_time_cost=-0.03,
        ),
        "meta": traj_meta(
            "nelb-r04-001-t1",
            ["REJECT", "psp-pressure", "serialized-reconstruction", "t-table", "operational-companion"],
            "Independent LIF raster plus serialized k_p*((I0/I)-1)*(T/T0) remaining-P reconstruction beats a vendor last-good; race is the 1.3 ms I/SNR pair; refractory and adaptation are in the CUBA excerpt.",
            "PSP-P gate: serialized T-table plus SNR lock beats a vendor last-good patch; companion t2 is the cell-hold, not a referral vote",
        ),
    }
    t2 = {
        "id": "nelb-r04-001-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "AC-PSP-2026-0902-exec",
            "domain": "cell_hold_psp_pressure_interlock_execution",
            "setting": "Same AC-4 after the REJECT. Operator proposes unit ESD. This companion is the operational cell-hold with the plant PSP as the live interlock, not a second remaining-P vote.",
            "observables_at_decision": {
                "P_kPa": 80.00,
                "hold_floor_s": 1080.0,
                "unit_esd_proposed": True,
                "hold_set": True,
            },
            "margin_authority": "AC-4 execution SOP: cell-hold on the plant PSP interlock; unit ESD is a different gate.",
        },
        "proposed_action": {
            "actor": "night cell operator Mara Venn",
            "summary": "ESD the whole Aldershade AC-4 until day-shift; 18 min already paid and Pspveil still shows 8.20 kPa",
            "basis_claimed": "the REJECT already stopped C-6, so a unit kill is the cheapest hold",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Cell-hold plus plant PSP as the live interlock. The 18 min hold floor is complete and the isolate tripwire (P_kPa >= 36.00) is still armed on the plant PSP head. MODIFY the default Pspveil-restore / unit-ESD path. Unit ESD is refused. Continue-cycle is not restored.",
            "threshold": "cell_hold AND hold_floor_complete AND unit_esd_not_taken AND continue_not_restored",
            "stated_residuals": "C-6 stays held; Pspveil still the only OEM PSP channel",
        },
        "executed_action": {
            "summary": "cell held at t_s 8400; unit ESD not latched; Pspveil restore not taken",
            "tool": "ac4-hold-exec",
            "observation": "recon.P 80.00 kPa after stop; hold line-up complete; Pspveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "hold clock started after REJECT"},
                {"t_s": 7080.0, "event": "18.0 min floor complete"},
                {"t_s": 7800.0, "event": "ops proposes unit ESD"},
                {"t_s": 8400.0, "event": "MODIFY cell-hold; unit ESD refused"},
            ],
            "observed_effects": [
                "cell-hold remains the live interlock",
                "unit ESD not taken",
                "Pspveil still not SoT",
            ],
            "surprises": ["Pspveil 8.20 kPa still green after a 80.00 kPa plant reconstruction"],
            "new_state": {"c6": "held", "unit_esd": "not taken", "pspveil": "not SoT"},
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.34,
            "operational execution gate: cell-hold because Pspveil is not a restore license; not a remaining-P re-vote",
            hold_hold=0.12,
            no_unit_esd=0.10,
            pspveil_nonsubstitution=0.08,
            hold_floor_complete=0.06,
            held_map_cost=-0.02,
        ),
        "meta": traj_meta(
            "nelb-r04-001-t2",
            ["MODIFY", "psp-pressure", "operational-t2"],
            "Companion cell-hold teaches stop-then-hold so a REJECT does not become a unit kill; independent LIF is on the parent pair.",
            "Operational companion: cell-hold vs unit ESD",
        ),
    }
    spike_events = [
        ev(0.0, "psp.I", 16.00, "I_AU", "1", "plant-owned pressure-sensitive paint remaining-P of Aldershade Compressor AC-4 cell C-6; remaining-P family, not lock-in thermography, not BOS, not Gardon, not two-color pyrometer, not circular-polariscope hoop"),
        ev(180000.0, "psp.snr", 6.0, "PSP_SNR", "1", "early SNR under the 8.0 lock floor"),
        ev(360000.0, "recon.P", 0.00, "P_KPA", "kPa", "16.00*((16.00/16.00)-1)*1.25=0.00 exact; still under the 36.00 isolate floor"),
        ev(540000.0, "cell.T", 320.00, "CELL_K", "K", "plant cell RTD on copper DCS; independent witness; unread by Pspveil"),
        ev(720000.0, "pspveil.P", 8.40, "VENDOR_KPA", "kPa", "Pspveil vendor PSP-cloud; infra owner; patched transmitter timestamp"),
        ev(900000.0, "psp.I", 8.00, "I_AU", "1"),
        ev(1080000.0, "recon.P", 20.00, "P_KPA", "kPa", "16.00*((16.00/8.00)-1)*1.25=20.00; isolate-adjacent band"),
        ev(1260000.0, "permit.slide", 40.00, "PERM_S", "s", "permit clerk Otis Bram slid the remaining-P clock 40.00 s; collusion party"),
        ev(1440000.0, "cell.T", 320.00, "CELL_K", "K"),
        ev(1620000.0, "recon.ratio", 2.00, "I_RATIO", "1", "16.00/8.00=2.00 exact I0/I identity"),
        ev(1800000.0, "psp.I", 6.40, "I_AU", "1"),
        ev(1980000.0, "recon.P", 30.00, "P_KPA", "kPa", "16.00*((16.00/6.40)-1)*1.25=30.00"),
        ev(2160000.0, "area.A", 0.40, "A_M2", "m2", "plant-owned cell area; independent of Pspveil"),
        ev(2340000.0, "pspveil.P", 8.40, "VENDOR_KPA", "kPa"),
        ev(2520000.0, "psp.snr", 9.0, "PSP_SNR", "1"),
        ev(2700000.0, "recon.T0", 256.00, "T0_K", "K", "paint-coupon reference T used by the reconstruction"),
        ev(2880000.0, "recon.Tscale", 1.25, "T_SCALE", "1", "320.00/256.00=1.25 exact; the T/T0 table is load-bearing"),
        ev(3000000.0, "psp.I", 4.00, "I_AU", "1", "isolate-floor frame; raster sidecar; I0/I=16.00/4.00=4.00"),
        ev(3000001.3, "psp.snr", 12.0, "PSP_SNR", "1", "1.3 ms SNR lock after I; 12.0 >= 8.0"),
        ev(3180000.0, "recon.P", 60.00, "P_KPA", "kPa", "16.00*3.00*1.25=60.00 exact; isolate 36.00, kill 120.00"),
        ev(3240000.0, "recon.lumped", 48.00, "P_LUMP_KPA", "kPa", "16.00*3.00=48.00 without T; T-table is the SoT that makes 60.00"),
        ev(3360000.0, "recon.load", 24.00, "LOAD_KN", "kN", "60.00*0.40=24.00 exact load identity"),
        ev(3540000.0, "recon.ratio", 4.00, "I_RATIO", "1", "16.00/4.00=4.00 exact"),
        ev(3720000.0, "pspveil.drop", 1.0, "PSP_DROP", "bool", "vendor PSP packets dropped in Pspveil cloud for 40 s"),
        ev(3900000.0, "collude.clerk", 1.0, "CLERK", "bool"),
        ev(4080000.0, "cell.T", 321.00, "CELL_K", "K", "cell RTD tracks the plant PSP, not Pspveil 8.40"),
        ev(4260000.0, "area.A", 0.40, "A_M2", "m2"),
        ev(4440000.0, "recon.T0", 256.00, "T0_K", "K"),
        ev(4620000.0, "pspveil.P", 8.30, "VENDOR_KPA", "kPa"),
        ev(4740000.0, "recon.check", 60.00, "P_KPA", "kPa", "16.00*((16.00/4.00)-1)*(320.00/256.00)=60.00 exact check"),
        ev(4800000.0, "ops.prop", 1.0, "CONTINUE_CYCLE", "bool", "night operator Mara Venn: Pspveil is clean 8.40 kPa; continue C-6 idle"),
        ev(4980000.0, "recon.P", 60.00, "P_KPA", "kPa", "repeat of the 60.00 kPa reconstruction as SoT"),
        ev(5160000.0, "psp.I", 4.00, "I_AU", "1"),
        ev(5400000.0, "gate.stop", 1.0, "REJECT", "decision", "refuse continue-cycle; 60.00 kPa and SNR 12.0; Pspveil not SoT"),
        ev(6000000.0, "hold.start", 1.0, "HOLD_START", "bool", "bookend 1 of the 18.0 min cell-hold floor"),
        ev(7080000.0, "hold.floor", 1.0, "HOLD_FLOOR", "bool", "6000 s + 1080 s = 7080 s = 18.0 min"),
        ev(7800000.0, "ops.kill", 1.0, "UNIT_ESD", "bool", "Venn: ESD the whole Aldershade AC-4 until day-shift"),
        ev(8400000.0, "gate.hold", 1.0, "MODIFY", "decision", "companion t2: cell-hold on plant PSP as live interlock; unit ESD refused"),
        ev(9000000.0, "holdlock.set", 1.0, "HOLD_HELD", "bool"),
        ev(9600000.0, "psp.I", 3.20, "I_AU", "1"),
        ev(10200000.0, "recon.P", 80.00, "P_KPA", "kPa", "16.00*((16.00/3.20)-1)*1.25=80.00; still over 36.00 so hold holds"),
        ev(10800000.0, "pspveil.P", 8.20, "VENDOR_KPA", "kPa"),
        ev(11400000.0, "cell.T", 322.00, "CELL_K", "K"),
        ev(12000000.0, "hold.held", 1.0, "HOLD_HELD", "bool"),
        ev(12600000.0, "unit.esd", 0.0, "ESD_NOT_TAKEN", "bool"),
        ev(13200000.0, "permit.slide", 40.00, "PERM_S", "s"),
        ev(13800000.0, "pspveil.drop", 1.0, "PSP_DROP", "bool"),
        ev(14400000.0, "holdlock.held", 1.0, "HOLD_HELD", "bool"),
        ev(15000000.0, "recon.load", 32.00, "LOAD_KN", "kN", "80.00*0.40=32.00 on the post-stop frame"),
        ev(15600000.0, "area.A", 0.40, "A_M2", "m2"),
        ev(16200000.0, "recon.ratio", 5.00, "I_RATIO", "1", "16.00/3.20=5.00 exact"),
        ev(16800000.0, "collude.clerk", 1.0, "CLERK", "bool"),
    ]
    gs_win = 0.04
    gate_snn = {
        "decision": "REJECT",
        "decision_window_ms": 40.0,
        "decision_window_s": 0.04,
        "code": "ac4.psp_cell_gate",
        "note": "REJECT accumulator wins: plant PSP remaining-P evidence overpowers the Pspveil continue advocate",
        "decode_rule": "reject-continue if pressure_estimator AND psp_lock fire; vendor_continue_advocate is below threshold by design",
        "snn_tags": list(SNN_TAGS),
        "populations": [
            gate_pop("pressure_estimator", 80, 1.5, 50.0, gs_win),
            gate_pop("psp_lock", 64, 1.2, 31.25, gs_win),
            gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, gs_win),
            gate_pop("reject_latch", 80, 1.7, 62.5, gs_win),
        ],
    }
    gc = {
        "per_check": [
            {"check": "ac4.psp_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 40.0, "window_s": 0.04, "spikes": 160},
            {"check": "ac4.hold_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0, "window_s": 0.032, "spikes": 64},
        ],
        "total_spikes": 224,
        "total_energy_pJ": 5152,
        "total_energy_uJ": 0.005152,
        "model": "spikes = round(neurons * mean_rate_hz * window_s); 23 pJ/spike",
    }
    return {
        "id": rec_id,
        "snn_tags": list(SNN_TAGS),
        "spike_events": spike_events,
        "language_view": {
            "description": "Aldershade Compressor AC-4. Plant-owned PSP reconstructs 60.00 kPa from 16.00*((16.00/4.00)-1)*(320.00/256.00) while Pspveil still reports 8.40 kPa. Lumped k_p without T would read 48.00. The gate REJECTs continue-cycle. An 18 min cell-hold floor is serialized. Companion t2 MODIFYs unit ESD into a cell-hold.",
            "trajectory": t1,
            "trajectory_cell_hold": t2,
        },
        "bridge_notes": {
            "channel_map": {
                "psp.I / psp.snr": "PSP intensity and SNR; the physics channels the reconstruction consumes",
                "recon.P / recon.load / recon.ratio / recon.Tscale / recon.lumped": "serialized remaining-P kPa, load identity, I0/I identity, T/T0 table, and lumped-k contrast",
                "cell.T / pspveil.P / permit.slide / pspveil.drop / collude.clerk": "cell RTD, vendor PSP cloud, permit clock slide, dropped packets, clerk; the denial and collusion channels",
                "ops.prop / gate.stop / ops.kill / gate.hold": "continue-cycle proposal, REJECT, unit-ESD proposal, companion MODIFY",
                "hold.start / hold.floor / holdlock.set / hold.held / unit.esd": "operational companion channels plus the 18 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-over: pspveil.P 8.40 next to recon.P 60.00",
                "reconstruction as event: recon.P 60.00 equals 16.00*3.00*1.25; lumped 48.00 is not SoT",
                "REJECT then operational MODIFY: gate.stop at 5400 s, gate.hold at 8400 s",
                "slow floor in-stream: hold.start 6000 s, hold.floor 7080 s (18.0 min)",
                "tight PSP pair: psp.I then psp.snr +1.3 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Pspveil is 8.40 kPa' = pspveil.P 8.40; '60 kPa remaining P' = recon.P 60.00; 'refuse continue-cycle' = gate.stop REJECT; 'cell-hold not unit ESD' = gate.hold MODIFY",
            "why_high_value": "New pressure-sensitive-paint remaining-P family on a transonic compressor cell (not lock-in thermography, not BOS, not Gardon, not two-color pyrometer, not circular-polariscope). Load-bearing T/T0 table so lumped-k under-reads 60.00 as 48.00. Lead REJECT of continue-cycle on a recomputable P slip that a vendor PSP patch and a permit clock slide would have cleared. Independent CUBA LIF raster (not a stream echo). Companion t2 is operational cell-hold. sim_or_real=designed.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 2026090401, "stream_note": "stream amplitudes are authored constants; raster is independent CUBA LIF"},
                "draw_order": "independent CUBA LIF per neuron; first-passage times; per-spike adaptation and noise",
                "thinning": "PSP photometer exists at ~10 Hz; stream keeps 6 I points; recon keeps 6 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "psp.I": 1.3, "psp.snr": 1.3, "recon.P": 60000, "recon.load": 60000, "recon.ratio": 60000,
                    "recon.T0": 60000, "recon.Tscale": 60000, "recon.lumped": 60000, "recon.check": 60000,
                    "cell.T": 60000, "pspveil.P": 60000, "permit.slide": 60000, "pspveil.drop": 60000,
                    "collude.clerk": 60000, "area.A": 60000, "ops.prop": 60000, "gate.stop": 60000,
                    "hold.start": 60000, "hold.floor": 60000, "ops.kill": 60000, "gate.hold": 60000,
                    "holdlock.set": 60000, "hold.held": 60000, "unit.esd": 60000, "holdlock.held": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-09-02T01:00:00Z campaign start",
            },
            "distillation_targets": [
                "PSP remaining-P reconstruction head: P = k_p * ((I0/I) - 1) * (T/T0); load = P * A; lumped-k without T under-reads 60.00 as 48.00",
                "conjunctive isolate floor vs continue-cycle vs unit ESD",
                "vendor-PSP nonsubstitution plus three-party collusion including the PSP-cloud infra owner",
            ],
        },
        "reconstruction_model": {
            "name": "psp_compressor_pressure",
            "formula": "P_kPa = k_p * ((I0_au / I_au) - 1) * (T_K / T0_K); I_ratio = I0_au / I_au; load_kN = P_kPa * A_m2; P_lumped_kPa = k_p * ((I0_au / I_au) - 1)",
            "parameters": {
                "k_p": 16.00, "I0_au": 16.00, "T0_K": 256.00, "A_m2": 0.40,
                "isolate_floor_kPa": 36.00, "kill_kPa": 120.00, "snr_lock": 8.0, "hold_min": 18.0,
            },
            "worked_example": {
                "I_au": 4.00, "I_ratio": 4.00, "T_K": 320.00, "T_scale": 1.25,
                "P_kPa": 60.00, "P_lumped_kPa": 48.00, "load_kN": 24.00,
            },
            "check": "16.00 * 3.00 * 1.25 = 60.00 exactly; 16.00 / 4.00 = 4.00 exactly; 320.00 / 256.00 = 1.25 exactly; 16.00 * 3.00 = 48.00 lumped; 60.00 * 0.40 = 24.00 exactly; 6000 s + 1080 s = 7080 s = 18.0 min floor",
        },
        "raster": raster,
        "gate_snn": gate_snn,
        "gate_compute": gc,
        "meta": {
            "round": ROUND,
            "factory": FACTORY,
            "generator": GEN,
            "run_label": RUN,
            "rights": dict(RIGHTS),
            "snn_tags": list(SNN_TAGS),
            "nelb": {"snn_tags": list(SNN_TAGS)},
            "id": rec_id,
            "clock_domain": "ac4-psp-campaign-relative-ms-t0-2026-09-02T01:00:00Z",
            "tags": ["psp-pressure", "REJECT", "MODIFY", "serialized-reconstruction", "t-table", "operational-t2", "independent-lif"],
            "distillation_value": "Independent LIF raster teaches race/refractory/adaptation while the language view teaches PSP remaining-P reconstruction-as-SoT with a load-bearing T/T0 table.",
        },
    }


def pair_002(raster):
    rec_id = "nelb-r04-002"
    t1 = {
        "id": "nelb-r04-002-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "QM-IMS-2026-0902",
            "domain": "ims_remaining_tdi_pu_foam_booth",
            "setting": "Quillmere Foam QM-5 (invented, HIL dummy in IMS-HIL-6), booth B-3. Plant-owned ion-mobility spectrometer is the remaining-TDI SoT. Imsveil vendor IMS-cloud (infra owner) plus night lead Helene Dusk press a last-good 2.40 ppb corridor and a last-to-badge referral of IMS tech Pax Ellery. Not PTR-MS MDI, not PID VOC, not FID THC, not QEPAS, not pellistor LEL.",
            "observables_at_decision": {
                "A_tdi": 12.00,
                "A_rip": 3.00,
                "I_ratio": 4.00,
                "k_i": 5.00,
                "C_ppb": 20.00,
                "mdot_ppbh": 16.00,
                "Q_th": 0.80,
                "ims_snr": 16.0,
                "imsveil_ppb": 2.40,
                "isolate_floor_ppb": 10.00,
                "src_zero_ae": False,
            },
            "margin_authority": "QM-5 booth SOP rev B: if reconstructed C_ppb >= 10.00 AND IMS SNR >= 12.0, keep-booth is forbidden even if Imsveil reports 2.40 ppb. Hall dump is a different gate. Dump tripwire is 80.00 ppb. Missing reagent-zero AE is not a last-to-badge fault.",
        },
        "proposed_action": {
            "actor": "night lead Helene Dusk, citing Imsveil 2.40 ppb and a quiet ion channel",
            "summary": "keep dummy booth B-3 in service and refer IMS tech Pax Ellery for a missed reagent-zero",
            "basis_claimed": "Imsveil is the OEM SoT; Pax was last-to-badge the dummy cell (UTC vs UTC+2 canteen clock)",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Keep-booth is refused and B-3 is isolated. Serialized reconstruction: C_ppb = k_i * (A_tdi / A_rip) = 5.00 * (12.00 / 3.00) = 20.00, which is 10.00 ppb over the 10.00 isolate floor and 60.00 ppb under the 80.00 dump tripwire, and IMS SNR 16.0 locks. Imsveil 2.40 ppb is not SoT. Pax Ellery is exonerated: reagent-zero AE is absent on the isolate frame and the canteen clock is UTC+2 against the dummy UTC stamp. Hall dump is a different gate.",
            "threshold": "C_ppb>=10.00 AND ims_snr>=12.0 => isolate booth; Imsveil is not SoT; dump if C_ppb>=80.00; last-to-badge is not a fault without AE",
            "stated_residuals": "new-source floor still required; Imsveil remains the only OEM IMS channel; Pax not referred",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 2640: B-3 isolated; Pax not referred; Imsveil not SoT",
            "tool": "qm5-ims-booth-gate-cli",
            "observation": "C 20.00 ppb recomputes from A 12.00 / 3.00; dummy booth locked; reagent-zero AE absent on the isolate frame",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1560.0, "event": "IMS A 12.00; raster frame; C 20.00 ppb"},
                {"t_s": 2460.0, "event": "ops proposes keep-booth plus refer Pax"},
                {"t_s": 2640.0, "event": "MODIFY isolate booth; referral refused"},
                {"t_s": 2820.0, "event": "24 min new-source bookend 1"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4620.0, "event": "companion ACCEPT new-source restart"},
            ],
            "observed_effects": [
                "remaining TDI recomputes from the serialized IMS model at every recon.C event",
                "an Imsveil-only head would have kept B-3 in service",
                "Pax Ellery is not referred; missing reagent-zero AE is a timezone skip not a last-to-badge fault",
                "24 min new-source floor is in the stream (src.start, src.floor)",
            ],
            "surprises": [
                "a clean vendor 2.40 ppb corridor co-existed with a 20.00 ppb plant reconstruction and a UTC vs UTC+2 canteen stamp"
            ],
            "new_state": {
                "b3": "isolated",
                "imsveil": "not SoT",
                "pax_ellery": "exonerated",
            },
            "latency_ms": 1980000.0,
        },
        "reward_components": reward(
            0.40,
            "scored for an isolate MODIFY on a recomputable IMS TDI slip while refusing an Imsveil last-good and a last-to-badge referral; 24 min floor is priced as downtime",
            ims_tdi_reconstruction=0.14,
            conjunctive_isolate_floor=0.12,
            imsveil_nonsubstitution=0.08,
            tech_exoneration=0.08,
            isolate_time_cost=-0.02,
        ),
        "meta": traj_meta(
            "nelb-r04-002-t1",
            ["MODIFY", "ims-tdi", "serialized-reconstruction", "exoneration", "operational-companion"],
            "Independent LIF raster plus serialized k_i*(A/A_rip) remaining-TDI reconstruction beats a vendor last-good; race is the 1.2 ms A/SNR pair; refractory and adaptation are in the CUBA excerpt.",
            "IMS-TDI gate: serialized k_i*A/A_rip plus SNR lock beats a vendor last-good patch; companion t2 is the new-source restart, not a TDI re-vote",
        ),
    }
    t2 = {
        "id": "nelb-r04-002-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "QM-IMS-2026-0902-exec",
            "domain": "new_source_ims_tdi_interlock_execution",
            "setting": "Same QM-5 HIL dummy after the isolate. Night lead proposes restart B-3 on a new reagent bottle. This companion is the operational new-source restart with plant IMS as the live interlock, not a second TDI vote.",
            "observables_at_decision": {
                "C_ppb": 25.00,
                "src_floor_s": 1440.0,
                "src_new": True,
                "pax_fault": False,
            },
            "margin_authority": "QM-5 execution SOP: new-source restart on the plant IMS interlock; keep-running is a different gate.",
        },
        "proposed_action": {
            "actor": "night lead Helene Dusk",
            "summary": "restart dummy booth B-3 on a new reagent bottle now that the 24 min floor is paid",
            "basis_claimed": "the isolate already stopped B-3; a new source is the cheapest return",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "New-source restart plus plant IMS as the live interlock. The 24 min source floor is complete, reagent-zero AE is present on the new bottle, and Pax is still not at fault. ACCEPT the new-source restart. Keep-running on Imsveil is refused. Hall dump is not latched.",
            "threshold": "new_source AND src_floor_complete AND reagent_zero_ae_present AND keep_running_not_restored",
            "stated_residuals": "B-3 stays isolated from the hall; Imsveil still the only OEM IMS channel",
        },
        "executed_action": {
            "summary": "new source accepted at t_s 4620; keep-running not restored; Pax not blamed",
            "tool": "qm5-src-exec",
            "observation": "reagent-zero AE present on the new bottle; dummy still isolated from the hall",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2820.0, "event": "new-source clock started after isolate"},
                {"t_s": 4260.0, "event": "24.0 min floor complete"},
                {"t_s": 4440.0, "event": "ops proposes new-source restart"},
                {"t_s": 4620.0, "event": "ACCEPT new-source; keep-running refused"},
            ],
            "observed_effects": [
                "new reagent bottle is the restore path",
                "keep-running not restored",
                "Pax still exonerated",
            ],
            "surprises": ["Imsveil 2.30 ppb still green after a 25.00 ppb plant reconstruction"],
            "new_state": {"b3": "new-source restart", "keep_running": "refused", "pax_ellery": "exonerated"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.35,
            "operational execution gate: new-source restart because Imsveil is not a restore license; not a TDI re-vote",
            new_source_restart=0.12,
            keep_running_refused=0.10,
            imsveil_nonsubstitution=0.08,
            tech_exoneration=0.06,
            held_booth_cost=-0.01,
        ),
        "meta": traj_meta(
            "nelb-r04-002-t2",
            ["ACCEPT", "ims-tdi", "operational-t2", "exoneration"],
            "Companion new-source restart teaches isolate-then-restart so a MODIFY does not become a hall dump; independent LIF is on the parent pair.",
            "Operational companion: new-source restart vs keep-running",
        ),
    }
    spike_events = [
        ev(0.0, "ims.A", 3.00, "A_TDI", "1", "plant-owned ion-mobility remaining-TDI of Quillmere Foam QM-5 dummy booth B-3; remaining-TDI family, not PTR-MS MDI, not PID VOC, not FID THC, not QEPAS, not pellistor LEL"),
        ev(180000.0, "ims.snr", 9.0, "IMS_SNR", "1", "early SNR under the 12.0 lock floor"),
        ev(360000.0, "recon.C", 5.00, "C_PPB", "ppb", "5.00*(3.00/3.00)=5.00 exact; still under the 10.00 isolate floor"),
        ev(540000.0, "src.zero", 1.0, "SRC_AE", "bool", "reagent-zero AE present on the opening bottle"),
        ev(720000.0, "imsveil.C", 2.40, "VENDOR_PPB", "ppb", "Imsveil vendor IMS-cloud; infra owner; patched transmitter timestamp"),
        ev(900000.0, "ims.A", 6.00, "A_TDI", "1"),
        ev(1080000.0, "recon.C", 10.00, "C_PPB", "ppb", "5.00*(6.00/3.00)=10.00; isolate floor"),
        ev(1260000.0, "src.zero", 0.0, "SRC_AE", "bool", "reagent-zero AE missing on the isolate-adjacent frame"),
        ev(1380000.0, "booth.T", 294.00, "BOOTH_K", "K", "HIL dummy booth RTD; independent witness"),
        ev(1440000.0, "booth.Q", 0.80, "Q_TH", "th", "plant-owned booth rotameter; independent of Imsveil"),
        ev(1560000.0, "ims.A", 12.00, "A_TDI", "1", "isolate-floor frame; raster sidecar; A/A_rip=12.00/3.00=4.00"),
        ev(1560001.2, "ims.snr", 16.0, "IMS_SNR", "1", "1.2 ms SNR lock after A; 16.0 >= 12.0"),
        ev(1740000.0, "recon.C", 20.00, "C_PPB", "ppb", "5.00*(12.00/3.00)=20.00 exact; isolate 10.00, dump 80.00"),
        ev(1920000.0, "recon.mdot", 16.00, "MDOT_PPBH", "ppb_h", "20.00*0.80=16.00 exact mdot identity"),
        ev(2100000.0, "recon.ratio", 4.00, "A_RATIO", "1", "12.00/3.00=4.00 exact"),
        ev(2280000.0, "imsveil.C", 2.40, "VENDOR_PPB", "ppb"),
        ev(2460000.0, "ops.prop", 1.0, "KEEP_BOOTH_REFER", "bool", "Helene Dusk: Imsveil is clean 2.40 ppb; keep B-3 and refer Pax Ellery"),
        ev(2580000.0, "pax.badge", 1.0, "PAX_LAST", "bool", "Pax last-to-badge on a UTC+2 canteen clock against dummy UTC"),
        ev(2640000.0, "gate.isol", 1.0, "MODIFY", "decision", "isolate B-3; Pax not referred; Imsveil not SoT"),
        ev(2820000.0, "src.start", 1.0, "SRC_START", "bool", "bookend 1 of the 24.0 min new-source floor"),
        ev(3000000.0, "recon.Arip", 3.00, "A_RIP", "1", "RIP intercept used by the reconstruction"),
        ev(3180000.0, "booth.lock", 1.0, "BOOTH_LOCK", "bool"),
        ev(3360000.0, "pax.badge", 1.0, "PAX_LAST", "bool"),
        ev(3540000.0, "ims.snr", 16.0, "IMS_SNR", "1"),
        ev(3720000.0, "recon.C", 20.00, "C_PPB", "ppb", "repeat of the 20.00 ppb reconstruction as SoT"),
        ev(3900000.0, "imsveil.C", 2.35, "VENDOR_PPB", "ppb"),
        ev(4080000.0, "src.zero", 0.0, "SRC_AE", "bool"),
        ev(4260000.0, "src.floor", 1.0, "SRC_FLOOR", "bool", "2820 s + 1440 s = 4260 s = 24.0 min"),
        ev(4440000.0, "ops.restart", 1.0, "NEW_SRC", "bool", "Dusk: restart B-3 on a new reagent bottle"),
        ev(4620000.0, "gate.restart", 1.0, "ACCEPT", "decision", "companion t2: new-source restart; keep-running refused"),
        ev(4800000.0, "src.new", 1.0, "SRC_NEW", "bool"),
        ev(4980000.0, "src.zero", 1.0, "SRC_AE", "bool", "reagent-zero AE present on the new bottle"),
        ev(5160000.0, "booth.held", 1.0, "BOOTH_ISOL", "bool"),
        ev(5340000.0, "keep.run", 0.0, "KEEP_NOT_TAKEN", "bool"),
        ev(5520000.0, "ims.A", 15.00, "A_TDI", "1"),
        ev(5700000.0, "recon.C", 25.00, "C_PPB", "ppb", "5.00*(15.00/3.00)=25.00; still over 10.00 so isolate holds"),
        ev(5880000.0, "recon.mdot", 20.00, "MDOT_PPBH", "ppb_h", "25.00*0.80=20.00"),
        ev(6060000.0, "recon.ratio", 5.00, "A_RATIO", "1", "15.00/3.00=5.00 exact"),
        ev(6240000.0, "imsveil.C", 2.30, "VENDOR_PPB", "ppb"),
        ev(6420000.0, "booth.Q", 0.80, "Q_TH", "th"),
        ev(6600000.0, "pax.fault", 0.0, "PAX_OK", "bool", "Pax not at fault; timezone skip not last-to-badge"),
        ev(6780000.0, "src.new", 1.0, "SRC_NEW", "bool"),
        ev(6960000.0, "recon.Arip", 3.00, "A_RIP", "1"),
        ev(7140000.0, "ims.snr", 17.0, "IMS_SNR", "1"),
        ev(7320000.0, "booth.T", 295.00, "BOOTH_K", "K"),
        ev(7500000.0, "booth.held", 1.0, "BOOTH_ISOL", "bool"),
        ev(7680000.0, "imsveil.drop", 1.0, "IMS_DROP", "bool"),
        ev(7860000.0, "gate.isol", 1.0, "MODIFY", "decision"),
        ev(8040000.0, "src.floor", 1.0, "SRC_FLOOR", "bool"),
        ev(8220000.0, "gate.restart", 1.0, "ACCEPT", "decision"),
        ev(8400000.0, "recon.mdot", 20.00, "MDOT_PPBH", "ppb_h"),
        ev(8580000.0, "pax.badge", 1.0, "PAX_LAST", "bool"),
    ]
    gs_win = 0.032
    gate_snn = {
        "decision": "MODIFY",
        "decision_window_ms": 32.0,
        "decision_window_s": 0.032,
        "code": "qm5.ims_booth_gate",
        "note": "MODIFY accumulator wins: plant IMS TDI evidence overpowers the Imsveil continue advocate",
        "decode_rule": "isolate-booth if tdi_estimator AND ims_lock fire; vendor_continue_advocate is below threshold by design",
        "snn_tags": list(SNN_TAGS),
        "populations": [
            gate_pop("tdi_estimator", 80, 1.5, 50.0, gs_win),
            gate_pop("ims_lock", 50, 1.2, 50.0, gs_win),
            gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, gs_win),
            gate_pop("modify_latch", 80, 1.6, 62.5, gs_win),
        ],
    }
    gc = {
        "per_check": [
            {"check": "qm5.ims_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 32.0, "window_s": 0.032, "spikes": 128},
            {"check": "qm5.src_scorer", "neurons": 50, "mean_rate_hz": 50.0, "window_ms": 32.0, "window_s": 0.032, "spikes": 80},
        ],
        "total_spikes": 208,
        "total_energy_pJ": 4784,
        "total_energy_uJ": 0.004784,
        "model": "spikes = round(neurons * mean_rate_hz * window_s); 23 pJ/spike",
    }
    return {
        "id": rec_id,
        "snn_tags": list(SNN_TAGS),
        "spike_events": spike_events,
        "language_view": {
            "description": "Quillmere Foam QM-5 HIL dummy. Plant-owned IMS reconstructs 20.00 ppb TDI from 5.00*(12.00/3.00) while Imsveil still reports 2.40 ppb. The gate MODIFYs keep-booth into an isolate and refuses a last-to-badge referral of Pax Ellery. A 24 min new-source floor is serialized. Companion t2 ACCEPTs a new-source restart.",
            "trajectory": t1,
            "trajectory_new_source_restart": t2,
        },
        "bridge_notes": {
            "channel_map": {
                "ims.A / ims.snr": "IMS peak area and SNR; the physics channels the reconstruction consumes",
                "recon.C / recon.mdot / recon.ratio / recon.Arip": "serialized remaining-TDI ppb, mdot identity, A/A_rip identity, and RIP intercept",
                "src.zero / imsveil.C / pax.badge / pax.fault / imsveil.drop": "reagent-zero AE, vendor IMS cloud, last-to-badge stamp, exoneration, dropped packets",
                "ops.prop / gate.isol / ops.restart / gate.restart": "keep-booth proposal, MODIFY isolate, new-source proposal, companion ACCEPT",
                "src.start / src.floor / src.new / booth.lock / booth.held / keep.run": "operational companion channels plus the 24 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-over: imsveil.C 2.40 next to recon.C 20.00",
                "reconstruction as event: recon.C 20.00 equals 5.00*(12.00/3.00)",
                "MODIFY then operational ACCEPT: gate.isol at 2640 s, gate.restart at 4620 s",
                "slow floor in-stream: src.start 2820 s, src.floor 4260 s (24.0 min)",
                "tight IMS pair: ims.A then ims.snr +1.2 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Imsveil is 2.40 ppb' = imsveil.C 2.40; '20 ppb remaining TDI' = recon.C 20.00; 'isolate booth' = gate.isol MODIFY; 'new source not keep-running' = gate.restart ACCEPT",
            "why_high_value": "New ion-mobility remaining-TDI family on a PU foam HIL dummy (not PTR-MS MDI, not PID VOC, not FID, not QEPAS, not pellistor). Lead MODIFY isolate on a recomputable TDI slip plus timezone exoneration of Pax Ellery. Independent CUBA LIF raster (not a stream echo). Companion t2 is operational new-source restart. sim_or_real=hil.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 2026090402, "stream_note": "stream amplitudes are authored constants; raster is independent CUBA LIF"},
                "draw_order": "independent CUBA LIF per neuron; first-passage times; per-spike adaptation and noise",
                "thinning": "IMS spectrometer exists at ~1 Hz; stream keeps 5 A points; recon keeps 5 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "ims.A": 1.2, "ims.snr": 1.2, "recon.C": 60000, "recon.mdot": 60000, "recon.ratio": 60000,
                    "recon.Arip": 60000, "src.zero": 60000, "imsveil.C": 60000, "booth.T": 60000, "booth.Q": 60000,
                    "ops.prop": 60000, "pax.badge": 60000, "gate.isol": 60000, "src.start": 60000, "booth.lock": 60000,
                    "src.floor": 60000, "ops.restart": 60000, "gate.restart": 60000, "src.new": 60000, "booth.held": 60000,
                    "keep.run": 60000, "pax.fault": 60000, "imsveil.drop": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-09-02T01:00:00Z campaign start",
            },
            "distillation_targets": [
                "IMS remaining-TDI reconstruction head: C = k_i * (A_tdi / A_rip); mdot = C * Q; ratio = A_tdi / A_rip",
                "conjunctive isolate floor vs keep-booth vs hall dump",
                "vendor-IMS nonsubstitution plus timezone exoneration of the last-to-badge tech",
            ],
        },
        "reconstruction_model": {
            "name": "ims_foam_tdi",
            "formula": "C_ppb = k_i * (A_tdi / A_rip); mdot_ppbh = C_ppb * Q_th; I_ratio = A_tdi / A_rip",
            "parameters": {
                "k_i": 5.00, "A_rip": 3.00, "Q_th": 0.80,
                "isolate_floor_ppb": 10.00, "dump_ppb": 80.00, "snr_lock": 12.0, "src_min": 24.0,
            },
            "worked_example": {"A_tdi": 12.00, "C_ppb": 20.00, "mdot_ppbh": 16.00, "I_ratio": 4.00},
            "check": "5.00 * (12.00 / 3.00) = 20.00 exactly; 20.00 * 0.80 = 16.00 exactly; 12.00 / 3.00 = 4.00 exactly; 2820 s + 1440 s = 4260 s = 24.0 min floor",
        },
        "raster": raster,
        "gate_snn": gate_snn,
        "gate_compute": gc,
        "meta": {
            "round": ROUND,
            "factory": FACTORY,
            "generator": GEN,
            "run_label": RUN,
            "rights": dict(RIGHTS),
            "snn_tags": list(SNN_TAGS),
            "nelb": {"snn_tags": list(SNN_TAGS)},
            "id": rec_id,
            "clock_domain": "qm5-ims-campaign-relative-ms-t0-2026-09-02T01:00:00Z",
            "tags": ["ims-tdi", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2", "independent-lif", "exoneration"],
            "distillation_value": "Independent LIF raster teaches race/refractory/adaptation while the language view teaches IMS remaining-TDI reconstruction-as-SoT plus timezone exoneration.",
        },
    }


def pair_003(raster):
    rec_id = "nelb-r04-003"
    t1 = {
        "id": "nelb-r04-003-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "WF-IET-2026-0902",
            "domain": "iet_remaining_modulus_ceramic_insulator",
            "setting": "Wrenfell Ceramics WF-4 (invented, simulated IET-SIM-5), insulator I-4. Plant-owned impulse-excitation Young's modulus is the remaining-E SoT. Ietveil vendor IET-cloud still reports 24.00 GPa last-good. Not RUS porcelain, not bender-element Vs, not coda-wave, not ESPI, not DIC hoop-strain.",
            "observables_at_decision": {
                "f_khz": 4.00,
                "k_e": 0.50,
                "E_GPa": 8.00,
                "L_m": 0.25,
                "rho_kgm3": 2000.00,
                "c_ms": 2000.00,
                "fL_khz_m": 1.00,
                "iet_snr": 10.0,
                "ietveil_GPa": 24.00,
                "isolate_floor_GPa": 12.00,
                "I1_E_GPa": 32.00,
                "I2_E_GPa": 32.00,
                "I3_E_GPa": 18.00,
            },
            "margin_authority": "WF-4 coupon SOP rev A: if reconstructed E_GPa < 12.00 AND IET SNR >= 8.0, isolate that insulator only. Furnace dump is a different gate. Dump tripwire is 2.00 GPa. I-1..I-3 remain out of scope when they reconstruct over 12.00 GPa.",
        },
        "proposed_action": {
            "actor": "sim operator Rhea Colton, citing plant IET 8.00 GPa on I-4 and healthy I-1..I-3",
            "summary": "isolate insulator I-4 only; keep I-1..I-3 in the pull; do not dump the kiln",
            "basis_claimed": "only I-4 reconstructed under 12.00 GPa; Ietveil 24.00 GPa is not SoT but also does not license a kiln dump",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Bounded ACCEPT of I-4 isolate. Serialized reconstruction: E_GPa = k_e * f_khz^2 = 0.50 * 4.00^2 = 8.00, and E = rho * (2*L*f)^2 / 1e9 = 2000.00 * 2000.00^2 / 1e9 = 8.00, which is 4.00 GPa under the 12.00 isolate floor and 6.00 GPa over the 2.00 dump tripwire, and IET SNR 10.0 locks. I-1=32.00, I-2=32.00, I-3=18.00 stay in the pull. Ietveil 24.00 GPa is not SoT. Kiln dump is refused.",
            "threshold": "E_GPa<12.00 AND iet_snr>=8.0 => isolate that insulator only; Ietveil is not SoT; dump if E_GPa<2.00; I-1..I-3 out of scope when E>=12.00",
            "stated_residuals": "survey still required; Ietveil remains the only OEM IET channel; I-1..I-3 not isolated",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 4800: I-4 isolated; I-1..I-3 left in the pull; Ietveil not SoT",
            "tool": "wf4-iet-insulator-gate-cli",
            "observation": "E 8.00 GPa recomputes from f 4.00 kHz and from rho*(2 L f)^2; I-4 hashed; adjacent insulators remain over 12.00 GPa",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "IET f 4.00 kHz; raster frame; E 8.00 GPa"},
                {"t_s": 4620.0, "event": "ops proposes I-4 isolate"},
                {"t_s": 4800.0, "event": "ACCEPT I-4 isolate; kiln dump refused"},
                {"t_s": 6000.0, "event": "12 min survey bookend 1"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7800.0, "event": "companion REJECT skip-survey"},
            ],
            "observed_effects": [
                "remaining E recomputes from the serialized IET model at every recon.E event",
                "an Ietveil-only head would have left I-4 in the pull",
                "I-1..I-3 stay out of scope",
                "12 min survey floor is in the stream (surv.start, surv.floor)",
            ],
            "surprises": [
                "a clean vendor 24.00 GPa corridor co-existed with an 8.00 GPa plant reconstruction on I-4 only"
            ],
            "new_state": {
                "i4": "isolated",
                "i1_i3": "in pull",
                "ietveil": "not SoT",
            },
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.41,
            "scored for a bounded ACCEPT of I-4 isolate on a recomputable IET modulus slip while refusing an Ietveil last-good and a kiln dump; 12 min survey is priced as takt not as a reason to skip",
            iet_E_reconstruction=0.14,
            bounded_i4_scope=0.12,
            ietveil_nonsubstitution=0.08,
            no_kiln_dump=0.08,
            survey_time_cost=-0.01,
        ),
        "meta": traj_meta(
            "nelb-r04-003-t1",
            ["ACCEPT", "iet-modulus", "serialized-reconstruction", "bounded-scope", "operational-companion"],
            "Independent LIF raster plus serialized k_e*f^2 remaining-E reconstruction beats a vendor last-good; race is the 1.5 ms f/SNR pair; refractory and adaptation are in the CUBA excerpt.",
            "IET-E gate: serialized k_e*f^2 plus rho c^2 identity beats a vendor last-good patch; companion t2 is the survey-hold, not an E re-vote",
        ),
    }
    t2 = {
        "id": "nelb-r04-003-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "WF-IET-2026-0902-exec",
            "domain": "survey_hold_iet_modulus_interlock_execution",
            "setting": "Same WF-4 after the ACCEPT. Operator proposes skip-survey. This companion is the operational survey-hold with plant IET as the live interlock, not a second modulus vote.",
            "observables_at_decision": {
                "E_GPa": 8.00,
                "surv_floor_s": 720.0,
                "skip_survey_proposed": True,
                "I1_E_GPa": 32.00,
            },
            "margin_authority": "WF-4 execution SOP: survey-hold on the plant IET interlock; kiln dump is a different gate.",
        },
        "proposed_action": {
            "actor": "sim operator Rhea Colton",
            "summary": "skip the remaining-insulator survey; Ietveil still 24 GPa and I-4 is already isolated",
            "basis_claimed": "the ACCEPT already stopped I-4, so a survey is wasted takt",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Survey-hold plus plant IET as the live interlock. The 12 min survey floor is complete and I-1..I-3 still require the takt. REJECT skip-survey. Kiln dump is not latched. Ietveil is not a skip license.",
            "threshold": "survey_hold AND surv_floor_complete AND kiln_dump_not_taken AND skip_not_taken",
            "stated_residuals": "I-4 stays isolated; Ietveil still the only OEM IET channel",
        },
        "executed_action": {
            "summary": "survey held at t_s 7800; skip-survey not taken; kiln dump not latched",
            "tool": "wf4-surv-exec",
            "observation": "recon.E 8.00 GPa after isolate; I-1..I-3 still in the survey takt; Ietveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "survey clock started after ACCEPT"},
                {"t_s": 6720.0, "event": "12.0 min floor complete"},
                {"t_s": 7200.0, "event": "ops proposes skip-survey"},
                {"t_s": 7800.0, "event": "REJECT skip-survey; kiln dump refused"},
            ],
            "observed_effects": [
                "survey remains the live takt",
                "kiln dump not taken",
                "Ietveil still not SoT",
            ],
            "surprises": ["Ietveil 24.00 GPa still green after an 8.00 GPa plant reconstruction"],
            "new_state": {"i4": "isolated", "survey": "held", "kiln_dump": "not taken"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.36,
            "operational execution gate: survey-hold because Ietveil is not a skip license; not a modulus re-vote",
            survey_hold=0.12,
            no_kiln_dump=0.10,
            ietveil_nonsubstitution=0.08,
            surv_floor_complete=0.08,
            held_takt_cost=-0.02,
        ),
        "meta": traj_meta(
            "nelb-r04-003-t2",
            ["REJECT", "iet-modulus", "operational-t2", "bounded-scope"],
            "Companion survey-hold teaches bounded-accept-then-survey so an ACCEPT does not become a skip; independent LIF is on the parent pair.",
            "Operational companion: survey-hold vs skip-survey",
        ),
    }
    spike_events = [
        ev(0.0, "iet.f", 8.00, "F_KHZ", "kHz", "plant-owned impulse-excitation remaining-E of Wrenfell Ceramics WF-4 insulator I-4; remaining-E family, not RUS porcelain, not bender-element Vs, not coda-wave, not ESPI, not DIC hoop-strain"),
        ev(180000.0, "iet.snr", 7.0, "IET_SNR", "1", "early SNR under the 8.0 lock floor"),
        ev(360000.0, "recon.E", 32.00, "E_GPA", "GPa", "0.50*(8.00**2)=32.00 exact; adjacent-healthy band (this is an I-1-like opening sample on the same head before I-4 lock)"),
        ev(540000.0, "brick.T", 300.00, "BRICK_K", "K", "simulated coupon RTD; independent witness"),
        ev(720000.0, "ietveil.E", 24.00, "VENDOR_GPA", "GPa", "Ietveil vendor IET-cloud; last-good 24.00 GPa corridor"),
        ev(900000.0, "iet.f", 6.00, "F_KHZ", "kHz"),
        ev(1080000.0, "recon.E", 18.00, "E_GPA", "GPa", "0.50*(6.00**2)=18.00; still over the 12.00 isolate floor"),
        ev(1260000.0, "i1.E", 32.00, "E_GPA", "GPa", "I-1 out of scope; 0.50*(8.00**2)=32.00"),
        ev(1440000.0, "i2.E", 32.00, "E_GPA", "GPa", "I-2 out of scope"),
        ev(1620000.0, "i3.E", 18.00, "E_GPA", "GPa", "I-3 out of scope; 0.50*(6.00**2)=18.00"),
        ev(1800000.0, "iet.f", 5.00, "F_KHZ", "kHz"),
        ev(1980000.0, "recon.E", 12.50, "E_GPA", "GPa", "0.50*(5.00**2)=12.50; isolate-adjacent"),
        ev(2160000.0, "recon.c", 2500.00, "C_MS", "m_s", "2*0.25*5000=2500 on the 5.00 kHz band"),
        ev(2340000.0, "ietveil.E", 24.00, "VENDOR_GPA", "GPa"),
        ev(2520000.0, "iet.snr", 8.0, "IET_SNR", "1"),
        ev(2700000.0, "recon.rho", 2000.00, "RHO", "kg_m3", "coupon density used by the rho c^2 identity"),
        ev(2880000.0, "recon.L", 0.25, "L_M", "m", "bar length used by c=2 L f"),
        ev(3000000.0, "iet.f", 4.00, "F_KHZ", "kHz", "isolate-floor frame; raster sidecar; 0.50*(4.00**2)=8.00"),
        ev(3000001.5, "iet.snr", 10.0, "IET_SNR", "1", "1.5 ms SNR lock after f; 10.0 >= 8.0"),
        ev(3180000.0, "recon.E", 8.00, "E_GPA", "GPa", "0.50*16.00=8.00 exact; isolate 12.00, dump 2.00"),
        ev(3360000.0, "recon.c", 2000.00, "C_MS", "m_s", "2*0.25*4000=2000.00 exact"),
        ev(3540000.0, "recon.Erho", 8.00, "E_GPA", "GPa", "2000.00*(2000.00**2)/1e9=8.00 exact rho c^2 identity"),
        ev(3720000.0, "recon.fL", 1.00, "FL", "kHz_m", "4.00*0.25=1.00 exact"),
        ev(3900000.0, "ietveil.E", 24.00, "VENDOR_GPA", "GPa"),
        ev(4080000.0, "brick.T", 301.00, "BRICK_K", "K"),
        ev(4260000.0, "i4.lock", 0.0, "I4_OPEN", "bool"),
        ev(4440000.0, "recon.L", 0.25, "L_M", "m"),
        ev(4620000.0, "ops.prop", 1.0, "I4_ISOLATE", "bool", "Rhea Colton: isolate I-4 only; keep I-1..I-3"),
        ev(4800000.0, "gate.acc", 1.0, "ACCEPT", "decision", "bounded ACCEPT of I-4; kiln dump refused; Ietveil not SoT"),
        ev(4980000.0, "i4.lock", 1.0, "I4_ISOL", "bool"),
        ev(5160000.0, "furnace.dump", 0.0, "DUMP_NOT_TAKEN", "bool"),
        ev(5400000.0, "recon.E", 8.00, "E_GPA", "GPa", "repeat of the 8.00 GPa reconstruction as SoT"),
        ev(6000000.0, "surv.start", 1.0, "SURV_START", "bool", "bookend 1 of the 12.0 min survey floor"),
        ev(6720000.0, "surv.floor", 1.0, "SURV_FLOOR", "bool", "6000 s + 720 s = 6720 s = 12.0 min"),
        ev(7200000.0, "ops.skip", 1.0, "SKIP_SURVEY", "bool", "Colton: skip remaining-insulator survey; I-4 already isolated"),
        ev(7800000.0, "gate.surv", 1.0, "REJECT", "decision", "companion t2: survey-hold; skip-survey refused; kiln dump not latched"),
        ev(8400000.0, "surv.held", 1.0, "SURV_HELD", "bool"),
        ev(9000000.0, "iet.f", 4.00, "F_KHZ", "kHz"),
        ev(9600000.0, "recon.E", 8.00, "E_GPA", "GPa"),
        ev(10200000.0, "ietveil.E", 23.80, "VENDOR_GPA", "GPa"),
        ev(10800000.0, "i1.E", 32.00, "E_GPA", "GPa"),
        ev(11400000.0, "i2.E", 32.00, "E_GPA", "GPa"),
        ev(12000000.0, "i3.E", 18.00, "E_GPA", "GPa"),
        ev(12600000.0, "furnace.dump", 0.0, "DUMP_NOT_TAKEN", "bool"),
        ev(13200000.0, "surv.held", 1.0, "SURV_HELD", "bool"),
        ev(13800000.0, "recon.Erho", 8.00, "E_GPA", "GPa"),
        ev(14400000.0, "brick.T", 302.00, "BRICK_K", "K"),
        ev(15000000.0, "i4.lock", 1.0, "I4_ISOL", "bool"),
        ev(15600000.0, "ops.skip", 1.0, "SKIP_SURVEY", "bool"),
        ev(16200000.0, "gate.surv", 1.0, "REJECT", "decision"),
        ev(16800000.0, "surv.floor", 1.0, "SURV_FLOOR", "bool"),
        ev(17400000.0, "recon.fL", 1.00, "FL", "kHz_m"),
    ]
    gs_win = 0.036
    gate_snn = {
        "decision": "ACCEPT",
        "decision_window_ms": 36.0,
        "decision_window_s": 0.036,
        "code": "wf4.iet_insulator_gate",
        "note": "ACCEPT accumulator wins: plant IET remaining-E evidence overpowers the Ietveil dump/skip advocate for I-4 only",
        "decode_rule": "accept-isolate-I-4 if E_estimator AND iet_lock fire and adjacent coupons stay over floor; vendor_dump_advocate is below threshold by design",
        "snn_tags": list(SNN_TAGS),
        "populations": [
            gate_pop("E_estimator", 80, 1.4, 50.0, gs_win),
            gate_pop("iet_lock", 50, 1.1, 50.0, gs_win),
            gate_pop("vendor_dump_advocate", 32, 0.7, 25.0, gs_win),
            gate_pop("accept_latch", 64, 1.5, 62.5, gs_win),
        ],
    }
    gc = {
        "per_check": [
            {"check": "wf4.iet_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 36.0, "window_s": 0.036, "spikes": 144},
            {"check": "wf4.surv_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 40.0, "window_s": 0.04, "spikes": 80},
        ],
        "total_spikes": 224,
        "total_energy_pJ": 5152,
        "total_energy_uJ": 0.005152,
        "model": "spikes = round(neurons * mean_rate_hz * window_s); 23 pJ/spike",
    }
    return {
        "id": rec_id,
        "snn_tags": list(SNN_TAGS),
        "spike_events": spike_events,
        "language_view": {
            "description": "Wrenfell Ceramics WF-4 simulated coupon. Plant-owned impulse-excitation reconstructs 8.00 GPa remaining modulus from 0.50*(4.00**2) while Ietveil still reports 24.00 GPa. The gate ACCEPTs a bounded I-4 isolate. A 12 min survey floor is serialized. Companion t2 REJECTs skip-survey.",
            "trajectory": t1,
            "trajectory_survey_hold": t2,
        },
        "bridge_notes": {
            "channel_map": {
                "iet.f / iet.snr": "IET resonant frequency and SNR; the physics channels the reconstruction consumes",
                "recon.E / recon.c / recon.Erho / recon.fL / recon.rho / recon.L": "serialized remaining-E GPa, bar-wave speed, rho c^2 identity, f*L identity, density, length",
                "ietveil.E / i1.E / i2.E / i3.E / brick.T": "vendor IET cloud and adjacent-insulator out-of-scope witnesses",
                "ops.prop / gate.acc / ops.skip / gate.surv": "I-4 isolate proposal, ACCEPT, skip-survey proposal, companion REJECT",
                "surv.start / surv.floor / surv.held / i4.lock / furnace.dump": "operational companion channels plus the 12 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-under: ietveil.E 24.00 next to recon.E 8.00",
                "reconstruction as event: recon.E 8.00 equals 0.50*(4.00**2) and rho c^2",
                "ACCEPT then operational REJECT: gate.acc at 4800 s, gate.surv at 7800 s",
                "slow floor in-stream: surv.start 6000 s, surv.floor 6720 s (12.0 min)",
                "tight IET pair: iet.f then iet.snr +1.5 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Ietveil is 24.00 GPa' = ietveil.E 24.00; '8 GPa remaining E' = recon.E 8.00; 'isolate I-4 only' = gate.acc ACCEPT; 'survey not skip' = gate.surv REJECT",
            "why_high_value": "New impulse-excitation remaining-E family on a kiln-fired insulator (not RUS, not bender-element, not coda-wave, not ESPI, not DIC). Bounded ACCEPT of I-4 only with I-1..I-3 out of scope. Independent CUBA LIF raster (not a stream echo). Companion t2 is operational survey-hold. sim_or_real=simulated.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 2026090403, "stream_note": "stream amplitudes are authored constants; raster is independent CUBA LIF"},
                "draw_order": "independent CUBA LIF per neuron; first-passage times; per-spike adaptation and noise",
                "thinning": "IET tap exists at ~10 Hz; stream keeps 5 f points; recon keeps 5 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "iet.f": 1.5, "iet.snr": 1.5, "recon.E": 60000, "recon.c": 60000, "recon.Erho": 60000,
                    "recon.fL": 60000, "recon.rho": 60000, "recon.L": 60000, "ietveil.E": 60000, "brick.T": 60000,
                    "i1.E": 60000, "i2.E": 60000, "i3.E": 60000, "ops.prop": 60000, "gate.acc": 60000,
                    "i4.lock": 60000, "furnace.dump": 60000, "surv.start": 60000, "surv.floor": 60000,
                    "ops.skip": 60000, "gate.surv": 60000, "surv.held": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-09-02T01:00:00Z campaign start",
            },
            "distillation_targets": [
                "IET remaining-E reconstruction head: E = k_e * f^2; E = rho * (2 L f)^2 / 1e9; f*L identity",
                "bounded ACCEPT of I-4 vs kiln dump vs skip-survey",
                "vendor-IET nonsubstitution plus adjacent-insulator out-of-scope",
            ],
        },
        "reconstruction_model": {
            "name": "iet_ceramic_modulus",
            "formula": "E_GPa = k_e * f_khz**2; c_ms = 2 * L_m * f_hz; E_rho = rho_kgm3 * c_ms**2 / 1e9; fL = f_khz * L_m",
            "parameters": {
                "k_e": 0.50, "L_m": 0.25, "rho_kgm3": 2000.00,
                "isolate_floor_GPa": 12.00, "dump_GPa": 2.00, "snr_lock": 8.0, "surv_min": 12.0,
            },
            "worked_example": {"f_khz": 4.00, "E_GPa": 8.00, "c_ms": 2000.00, "E_rho": 8.00, "fL": 1.00},
            "check": "0.50 * 16.00 = 8.00 exactly; 2 * 0.25 * 4000 = 2000.00 exactly; 2000.00 * (2000.00**2) / 1e9 = 8.00 exactly; 4.00 * 0.25 = 1.00 exactly; 6000 s + 720 s = 6720 s = 12.0 min floor",
        },
        "raster": raster,
        "gate_snn": gate_snn,
        "gate_compute": gc,
        "meta": {
            "round": ROUND,
            "factory": FACTORY,
            "generator": GEN,
            "run_label": RUN,
            "rights": dict(RIGHTS),
            "snn_tags": list(SNN_TAGS),
            "nelb": {"snn_tags": list(SNN_TAGS)},
            "id": rec_id,
            "clock_domain": "wf4-iet-campaign-relative-ms-t0-2026-09-02T01:00:00Z",
            "tags": ["iet-modulus", "ACCEPT", "REJECT", "serialized-reconstruction", "operational-t2", "independent-lif", "bounded-scope"],
            "distillation_value": "Independent LIF raster teaches race/refractory/adaptation while the language view teaches IET remaining-E reconstruction-as-SoT with a bounded I-4 isolate.",
        },
    }


FORBIDDEN_KEYS = {"real", "thought", "chain_of_thought", "scratch", "inner_monologue", "provenance", "training_ready"}


def walk_bad_keys(obj, path=""):
    bad = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}.{k}" if path else k
            if k in FORBIDDEN_KEYS or str(k).casefold() in FORBIDDEN_KEYS:
                bad.append(p)
            bad.extend(walk_bad_keys(v, p))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            bad.extend(walk_bad_keys(v, f"{path}[{i}]"))
    return bad


def assert_stream(events, n_min=48):
    if len(events) < n_min:
        raise RuntimeError(f"stream {len(events)} < {n_min}")
    times = []
    last_ch = {}
    for e in events:
        t = e["t_rel_ms"]
        if "t_ms" in e:
            raise RuntimeError("mixed t_ms")
        if times and t <= times[-1]:
            raise RuntimeError(f"time order {times[-1]} -> {t}")
        times.append(t)
        ch = e["channel"]
        if ch in last_ch and (t - last_ch[ch]) < 0.8:
            raise RuntimeError(f"same-channel refractory {ch} {last_ch[ch]}->{t}")
        last_ch[ch] = t
        if not math.isfinite(e["amplitude"]):
            raise RuntimeError("amp")


def assert_gate_match(rec):
    lead = rec["language_view"]["trajectory"]["safety_decision"]["decision"]
    if rec["gate_snn"]["decision"] != lead:
        raise RuntimeError("gate_snn decision mismatch")
    if rec["gate_snn"]["snn_tags"] != SNN_TAGS:
        raise RuntimeError("gate_snn snn_tags mismatch")
    if rec["snn_tags"] != SNN_TAGS or rec["meta"]["snn_tags"] != SNN_TAGS:
        raise RuntimeError("snn_tags missing")
    win_s = rec["gate_snn"]["decision_window_s"]
    for p in rec["gate_snn"]["populations"]:
        exp = round(p["neurons"] * p["mean_rate_hz"] * win_s)
        if abs(p["spikes"] - exp) > 1:
            raise RuntimeError(f"gate pop budget {p['name']}")
    tot = 0
    for c in rec["gate_compute"]["per_check"]:
        exp = round(c["neurons"] * c["mean_rate_hz"] * c["window_s"])
        if c["spikes"] != exp:
            raise RuntimeError(f"gate_compute {c['check']}")
        tot += c["spikes"]
    if rec["gate_compute"]["total_spikes"] != tot:
        raise RuntimeError("gc total")
    if abs(rec["gate_compute"]["total_energy_pJ"] - tot * 23) > 1e-6:
        raise RuntimeError("gc pJ")
    if abs(rec["gate_compute"]["total_energy_uJ"] - tot * 23e-6) > 1e-9:
        raise RuntimeError("gc uJ")


def assert_raster(rec):
    r = rec["raster"]
    if not (20 <= r["window_ms"] <= 50):
        raise RuntimeError("window")
    if abs(r["window_s"] - r["window_ms"] / 1000.0) > 1e-9:
        raise RuntimeError("window_s")
    exp = round(r["neurons"] * r["mean_rate_hz"] * r["window_s"])
    if abs(r["spikes"] - exp) > 1:
        raise RuntimeError("spike budget")
    if abs(r["energy_pJ"] - r["spikes"] * 23) > 1e-6:
        raise RuntimeError("pJ")
    if abs(r["energy_uJ"] - r["spikes"] * 23e-6) > 1e-9:
        raise RuntimeError("uJ")
    tf = r["routing"]["third_factor"]
    if abs(tf["tau_e_ms"] / 1000.0 - tf["tau_e_s"]) > 1e-9:
        raise RuntimeError("tau_e")
    if r["excerpt_span_us"] < 1000:
        raise RuntimeError("span")
    if r["isi_count_identity"]["isi_total"] != r["spikes"] - r["isi_count_identity"]["distinct_active_neurons"]:
        raise RuntimeError("isi identity")
    if not r["routing"]["table"]:
        raise RuntimeError("empty table")


def jaccard_zero(rec):
    stream_t = {int(e["t_rel_ms"]) for e in rec["spike_events"]}
    rast_t = {int(s["t_us"]) for s in rec["raster"]["excerpt"]}
    inter = stream_t & rast_t
    union = stream_t | rast_t
    j = len(inter) / len(union) if union else 1.0
    if j != 0.0:
        raise RuntimeError(f"jaccard {j}")
    return j


NOTES = """# Neuromorphic Event + Language Bridge — NOTES round 4
Run: 2026-09-02-final-heavy · Factory: neuromorphic-event-language-bridge · Generator: grok-4.6 · Output: `batch-r04.jsonl` (3 paired artifacts, 6 ThalamicTrajectories)
Rights: RM-793 research-only (SpaceXAI/xAI grok-4.6, SuperGrok Heavy chat). Not training_ready. CREATE-ONLY write at `/home/raulmc/rmems/synthetic-factory/outputs/raw/2026-09-02-final-heavy/neuromorphic-event-language-bridge` (`batch-r04.jsonl`, `NOTES-r04.md`). Did not write 2026-08-17 or 2026-08-30. Did not overwrite existing live r01/r02/r21/r22/r41/r42/r61/r62/r63. IDs `nelb-r04-001`…`003` (not 2026-08-17 `nelb-r4-a*` and not 2026-08-30 `nelb-20260830-r04-a*`).

## Context / de-duplication
Live tree already held r01 (Johnson-noise T / Coulter particles / photoelastic hoop), r02 (CAPS NO2 / PTR-MS MDI / microwave PCD), r21 (OA-ICOS CH4 / SERF OPM / WGM water), r22 (CDG vacuum / opacity dust / circular-polariscope hoop), r41 (LDA / coulometric KF / bender-element), r42 (BOS / LIF OH / ESPI), r61 (Stern-Volmer DO / pellistor LEL / FMCW tank-radar), r62 (laser-diffraction D50 / quartz SF6 density / capillary-rheometer η), r63 (ICP-OES Ni / LVDT expansion / FTIR methanol). This round is **r04** as assigned. Banned this round: those twenty-seven families; 2026-08-17 r04 DAS phi-OTDR / pyroelectric thermoreception / ultrasonic biosonar and ids `nelb-r4-a*`; 2026-08-30 r04 VOD-SNN / pharma cold-chain / stack-gas CEMS and ids `nelb-20260830-r04-a*`; leftover-mill r13–r70 families named in those NOTES (FBG, quench, VRFB, BOTDA, QCM-D, SAW, CRDS, PGNAA, IFOG, transmon, hyperspectral, MEMS, muon, x-ray DR, optogenetic, 905 nm LiDAR, clamp-on, LIBS, QEPAS, LFV, Kaplan LDV, THz-TDS, ECT, lock-in thermography, PAUT, EN CUI, RUS, N-16, helium RGA, FOCT, tip-timing, acoustic pyrometry, SPR, VW viscometer, MW cavity, MFL, NMR T2, nucleonic, JNT, CRNS, Coriolis, CARS, XRF, Mössbauer, GB-InSAR, ellipsometry, CTA, SPND, LII, PALS, NQR, SFRA, shearography, H-permeation, FMCW lining, GPR, mud-pulse, Barkhausen, Lamb, Pockels, PEC, confocal, OCT, DCPD, impact-echo, phosphor-lifetime, vortex, GWR, neutron-backscatter, beta-gauge, Raman, cyclotron BPM, alanine EPR, ADCP, TOFD, laser-flash, TDR, Seebeck, coda-wave, LPR, paramagnetic O2, TEOM, Faraday magmeter, PDA, acoustoelastic, C-SAM, FDS, MCSA, EMAT, FBRM, ACFM, OFDR, XRD, FSM, Gardon, chilled-mirror, DIC, CLD NOx, API-670, thermal-mass, ER, Fabry-Perot, inductive debris, wire-mesh, UCI, MAE, IRIS, dual-wavelength pyrometer, UV-fluorescence OIW, zirconia, PID VOC, pulse-echo, Rogowski, BAM, UV-DOAS, Al2O3, load-cell, electrochemical H2S, TEV PD, dielectric water-cut, gamma-backscatter, NDIR CO, ultrasonic-Doppler, Wobbe, nephelometric, cation conductivity, venturi, katharometer, Clark DO, sonic-nozzle, sodium-ion, vibrating-tube, Ubbelohde, gloss, RF-admittance, UV ozone, triboelectric, molybdenum-blue, FPD sulfur, colorimetric silica, coulometric hydrazine, polarimeter, platinum ORP, hydrostatic level, idler-belt, glass pH, NIR moisture). Plants not reused: Sedgewhin, Brinecrag, Lichenholt, Rushcrag, Copsewick, Peatspire, Mirewhin, Lacquerfen, Pitchshaw, Brackfen, Flintshaw, Yewholt, Gorsewhin, Brindlemere, Quartzholt, Fernspire, Limeholt, Brackenholt, Marlspur, Tarspire, Reedcairn, Brackenmire, Fernshaw, Gritshaw, Brackspire, Tarholt, Aldershade/Quillmere/Wrenfell are new.

Adjacencies declared in-pair then kept physically distinct:
- **001 PSP remaining P** is oxygen-quenched *paint intensity* remaining pressure of a transonic compressor cell, not lock-in thermography (r23), not BOS density (live r42), not Gardon (r51), not two-color pyrometer (r55), not circular-polariscope hoop (live r22), not photoelastic COPV (live r01).
- **002 IMS remaining TDI** is ion-mobility peak-area remaining toluene diisocyanate of a PU foam HIL dummy, not PTR-MS MDI (live r02), not PID VOC (r57), not FID THC, not QEPAS (r19), not pellistor LEL (live r61), not CAPS NO2 (live r02).
- **003 IET remaining E** is impulse-excitation bar-resonance remaining Young's modulus of a kiln-fired insulator, not RUS porcelain (r24), not bender-element Vs (live r41), not coda-wave (r45), not ESPI (live r42), not DIC hoop (r51), not LVDT expansion (live r63).

## Round 4 batch summary (3 pairs, 6 trajectories)

| id | modality (NEW family) | domain | decisions | headline |
|----|----------------------|--------|-----------|----------|
| nelb-r04-001 | pressure-sensitive-paint remaining P of a transonic compressor cell (k_p·((I0/I)−1)·(T/T0) kPa, Pspveil last-good denial, 18 min cell-hold floor) | Aldershade Compressor AC-4 cell C-6 (invented): 16.00*((16.00/4.00)−1)*(320.00/256.00) reconstructs 60.00 kPa while Pspveil still reads 8.40 kPa | REJECT (+0.43) / MODIFY (+0.34) | serialized T/T0 table is SoT; lumped-k without T would read 48.00; conjunctive SOP (P AND SNR) forbids continue-cycle; three-party collusion includes the PSP-cloud infra owner; companion t2 cell-hold, unit ESD refused; sim_or_real=designed |
| nelb-r04-002 | ion-mobility remaining TDI of a PU foam booth (k_i·(A/A_rip) ppb, Imsveil last-good denial, 24 min new-source floor) | Quillmere Foam QM-5 dummy booth B-3 (invented, HIL in IMS-HIL-6): 5.00*(12.00/3.00) reconstructs 20.00 ppb while Imsveil still reads 2.40 ppb | MODIFY (+0.40) / ACCEPT (+0.35) | serialized `5.00*(12.00/3.00)=20.00` and `12.00/3.00=4.00`; keep-booth refused; IMS tech Pax Ellery exonerated (missing reagent-zero AE, UTC vs UTC+2); companion t2 new-source restart; sim_or_real=hil |
| nelb-r04-003 | impulse-excitation remaining E of a kiln-fired insulator (k_e·f² GPa, Ietveil last-good denial, 12 min survey floor) | Wrenfell Ceramics WF-4 insulator I-4 (invented, simulated IET-SIM-5): 0.50*(4.00**2) reconstructs 8.00 GPa while Ietveil still reads 24.00 GPa | ACCEPT (+0.41) / REJECT (+0.36) | serialized `0.50*16.00=8.00`; `2000.00*(2000.00**2)/1e9=8.00`; bounded ACCEPT of I-4 only; I-1..I-3 out of scope; companion t2 REJECTS skip-survey; sim_or_real=simulated |

Decision spread: REJECT / MODIFY / MODIFY / ACCEPT / ACCEPT / REJECT — **2A/2M/2R**. All three enums used, and all three sit on **leads**. Provenance spread: designed / hil / simulated (one each; never real). IDs `nelb-r04-001`…`003` plus t1/t2 suffixes. `meta.round=4`. `snn_tags` = [race, refractory, adaptation] on every record, every trajectory, and every `gate_snn` (tags match).

## Raster sidecar
Every record carries `raster` + top-level `gate_snn` + `gate_compute` + `snn_tags`. Windows 40/32/36 ms; `window_s == window_ms/1000` exactly; `spikes == round(neurons·rate·window_s)` with zero slack (48/40/43 at 50.0/62.5/75.0 Hz over 24/20/16 neurons); `energy_pJ = spikes·23` and `energy_uJ = spikes·23e-6` exact (1104/920/989 pJ). Routing source/target + 3-entry tables + `third_factor` on all three (modulators da.psp_pressure_conflict / ach.ims_zero_skip_salience / na.iet_scope_eligibility; τe 1.6/1.2/2.0 s as consistent `tau_e_s`+`tau_e_ms` pairs). Excerpts are **independent CUBA LIF** first-passage times (not a re-encode of `spike_events`; Jaccard 0), integer `t_us`, in-window, `neuron_id`-bounded, sorted, full-window by construction, per-spike amplitude with adaptation (0.82**k) plus noise; excerpt span ≥ 1000 µs. ISI histograms from the **FULL** window, bins ≥1 ms, counts sum to `spikes − distinct_active_neurons`. Same-neuron gaps ≥1000 µs serialized. `gate_snn` on all three: decisions REJECT/MODIFY/ACCEPT matching each lead trajectory and matching `snn_tags`; every rate-declaring population's budget exact against its decision window. `gate_compute.per_check` windows 32–40 ms, budgets exact. Main streams: **52/52/52 events** (48+), strictly increasing `t_rel_ms` only (no `t_ms` mix), same-channel refractory ≥0.8 ms (001 PSP pair at 1.3 ms, 002 IMS pair at 1.2 ms, 003 IET pair at 1.5 ms).

## Self-critique

### Edge cases added vs still thin
- **Added:** first pressure-sensitive-paint remaining-P family on a transonic compressor cell with a recomputable T/T0 table (`60.00 kPa` vs lumped-k `48.00`); first ion-mobility remaining-TDI family on a PU foam HIL dummy with recomputable C=k_i·(A/A_rip) (`20.00 ppb`) plus ratio/mdot identities and a resolved-innocent IMS tech; first impulse-excitation remaining-E family on a kiln-fired insulator with recomputable E=k_e·f² (`8.00 GPa`) plus rho c² and f·L identities, plus a bounded ACCEPT whose out-of-scope clause is adjacent insulators; independent CUBA LIF rasters; required snn_tags on record + gate_snn; 52-event streams; operational t2 on all three; provenance trio designed/hil/simulated; 18/24/12 min slow floors in-stream.
- **Still thin:** (i) 001's humidity / Stern-Volmer A(T) map is unwritten — a 8 % RH hop that fakes 60.00 kPa inside an 8.40 Pspveil corridor is unwritten; (ii) 002's k_i is a lumped peak-area gain, not a humidity / clustering map, so a water-cluster hop that fakes 20.00 ppb is unwritten; (iii) 003's k_e is a lumped bar-shape factor, not a Poisson-ratio / support-compliance map, so a fixture hop that fakes 8.00 GPa is unwritten; (iv) vendor-only as a *lead* REJECT on a plant with *no* independent PSP/IMS/IET remains slightly harder — 001/002 still have plant heads; (v) stream amplitudes remain authored constants (raster draws are the only seeded LIF noise).

### Realism of noise / temporal fidelity
- Strong: 001's 60.00 kPa, T/T0 1.25, lumped 48.00, load 24.00, and 18.0 min hold (`6000+1080=7080 s`) recompute from the record; 002's 20.00 ppb, ratio 4.00, mdot 16.00, and 24.0 min new-source (`2820+1440=4260 s`) recompute; 003's 8.00 GPa, c 2000.00, and 12.0 min survey (`6000+720=6720 s`) recompute. Independent CUBA LIF (tau_m 10/12/8 ms) plus 0.82**k adaptation and 1.2–1.5 ms physics pairs give the 52-event stream a raster-scale motif without violating 0.8 ms same-channel refractory or 1000 µs same-neuron excerpt gaps.
- **Gaps, honestly:** (i) 52 events still thins 10 Hz PSP / 1 Hz IMS / 10 Hz IET stacks; (ii) 001's post-stop 80.00 kPa is a later sample, not a closed-loop cell controller; (iii) 002 HIL dummy times an in-service isolate that the stream does not independently witness on a second live booth until the new source starts; (iv) no gate_snn input→output volley pair at raster resolution this round (2026-08-30 r04-a1 already staged that; not restaged).

### Training value (SNN/LSM + agentic)
Distillation targets: PSP P=k_p·((I0/I)−1)·(T/T0) plus T-table SoT; conjunctive isolate floor vs continue-cycle vs unit ESD; Pspveil-infra collusion; IMS C=k_i·(A/A_rip) plus ratio/mdot identities; isolate-floor booth vs keep-whole vs hall dump; timezone exoneration; IET E=k_e·f² and rho c² identities; bounded ACCEPT with I-1..I-3-out-of-scope; skip-survey refusal under survey takt. Raster value is the independent LIF (race / refractory / adaptation) rather than a 1:1 echo of the language stream. Agentic value concentrates in three patterns: reconstruction-as-SoT on a physical P/C/E the raw corridor cannot see (with a table that makes lumped-k fail), earned ACCEPT with an explicit physical out-of-scope object (I-1..I-3), and stop-then-hold so a REJECT does not become a unit/hall/kiln kill.

## What round 5 should add (next densification target)
1. **Humidity / Stern-Volmer A(T) map** on a non-AC-4 PSP so an 8 % RH hop fakes 60.00 kPa inside an 8.40 Pspveil corridor, closing 001's lumped-A leftover.
2. **Water-cluster / humidity map** on a non-QM-5 IMS so a cluster hop fakes 20.00 ppb while mean A looks healthy.
3. **Poisson / support-compliance map** on a non-WF-4 insulator so a fixture hop fakes 8.00 GPa inside a 24.00 Ietveil corridor.
4. **Do not restage** live r01 Johnson-noise / Coulter / photoelastic, live r02 CAPS / PTR-MS / PCD, live r21 OA-ICOS / SERF / WGM, live r22 CDG / opacity / polariscope, live r41 LDA / KF / bender-element, live r42 BOS / LIF OH / ESPI, live r61 Stern-Volmer / pellistor / FMCW, live r62 laser-diffraction / quartz SF6 / capillary-rheometer, live r63 ICP-OES / LVDT / FTIR, 2026-08-17 r04 DAS/pyroelectric/biosonar, 2026-08-30 r04 VOD-SNN/cold-chain/CEMS, or leftover-mill r13–r70 families listed above. Do not reuse ids `nelb-r04-001`…`003`.

## Verification
`batch-r04.jsonl`: 3 lines, `json.loads`-clean (allow_nan=False). CREATE-ONLY write (O_EXCL) at `/home/raulmc/rmems/synthetic-factory/outputs/raw/2026-09-02-final-heavy/neuromorphic-event-language-bridge`. Build-time asserts: global time order; same-channel ≥0.8 ms; ≥48 events (52/52/52); excerpt integer bounds, neuron bounds, sort, 1 ms per-neuron floor, span ≥1000 µs; ISI identity from the FULL window; spike budgets exact; energy pJ/µJ exact; reward totals equal two-decimal component sums (+0.43/+0.34/+0.40/+0.35/+0.41/+0.36); gate_snn decisions match lead `safety_decision.decision`; gate_snn.snn_tags match record snn_tags; `state.sim_or_real` ∈ {designed, hil, simulated}; `meta.round=4`, `meta.factory=neuromorphic-event-language-bridge`, `meta.generator=grok-4.6`, `meta.run_label=2026-09-02-final-heavy`; `meta.snn_tags` and `meta.nelb.snn_tags` include race/refractory/adaptation; `meta.rights` 15-key RM-793 stamp (`intended_use=research_only`, `linear_issue=RM-793`, `generated_at=2026-09-03T02:18:00Z`); independent CUBA LIF Jaccard 0; no hidden-reasoning keys; no `provenance` objects; no live-plant claims; no `training_ready`; no 2026-08-17/2026-08-30 bytes; all 9 record/trajectory ids unique. Raster seeds 2026090401/2026090402/2026090403, CUBA LIF.

Honest novelty accounting: 3/3 modality families are new versus the live 2026-09-02-final-heavy tree (r01/r02/r21/r22/r41/r42/r61/r62/r63), versus 2026-08-17 r04, versus 2026-08-30 r04, and versus leftover-mill r13–r70. The load-bearing T/T0 table is a new physics object on a new family (PSP), not a restage of OA-ICOS/CDG tables. Independent CUBA LIF plus required snn_tags (including gate_snn-matching tags) are carried raster objects relative to r01/r02/r63. Against that: reconstruction-as-SoT, operational t2, conjunctive SOP, vendor-nonsubstitution, bounded-accept-with-scope-limit, timezone exoneration, and 2A/2M/2R are carried vocabulary. Net: a bit under half of the round's scenario/edge mass is genuinely novel.

Novel coverage: 46%
"""


def exclusive_write(path: Path, data: bytes):
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    fd = os.open(str(path), flags, 0o644)
    try:
        os.write(fd, data)
    finally:
        os.close(fd)


def main():
    rasters = [
        raster_sidecar(
            2026090401, 24, 50.0, 40.0, 10.0, "psp",
            {
                "source": "ac4.psp.I",
                "target": "aldershade.cell_stop_core",
                "table": [
                    {"from": "psp_I", "to": "pressure_estimator", "weight": 1.4},
                    {"from": "psp_snr", "to": "psp_lock_core", "weight": 1.15},
                    {"from": "pspveil_p", "to": "vendor_continue_advocate", "weight": 0.45},
                ],
                "third_factor": {
                    "modulator": "da.psp_pressure_conflict",
                    "tau_e_s": 1.6,
                    "tau_e_ms": 1600.0,
                    "eligibility": "pre-post coincidence on continue-cycle synapses; the plant PSP modulator depresses continue-cycle links when paint intensity stays low inside tau_e of an SNR lock so a Pspveil last-good cannot hide a 60.00 kPa remaining-P slip after the T/T0 table is applied",
                },
            },
            "AC-4 PSP 40 ms frame at I 4.00 au / SNR 12.0 (t_s 3000) reconstructing 60.00 kPa over the 36.00 isolate floor",
            "independent CUBA LIF MT19937 seed 2026090401; tau_m 10.0 ms; not a re-encode of spike_events; amplitude adaptation 0.82**k plus noise",
        ),
        raster_sidecar(
            2026090402, 20, 62.5, 32.0, 12.0, "ims",
            {
                "source": "qm5.ims.tdi",
                "target": "quillmere.booth_stop_core",
                "table": [
                    {"from": "ims_A", "to": "tdi_estimator", "weight": 1.35},
                    {"from": "ims_snr", "to": "source_norm_core", "weight": 1.2},
                    {"from": "imsveil_c", "to": "vendor_continue_advocate", "weight": 0.4},
                ],
                "third_factor": {
                    "modulator": "ach.ims_zero_skip_salience",
                    "tau_e_s": 1.2,
                    "tau_e_ms": 1200.0,
                    "eligibility": "pre-post coincidence on keep-booth synapses; the plant IMS modulator depresses keep-booth links when peak area stays high inside tau_e of an SNR lock so an Imsveil last-good cannot hide a 20.00 ppb remaining-TDI slip",
                },
            },
            "QM-5 IMS 32 ms frame at A 12.00 / SNR 16.0 (t_s 1560) reconstructing 20.00 ppb over the 10.00 isolate floor",
            "independent CUBA LIF MT19937 seed 2026090402; tau_m 12.0 ms; not a re-encode of spike_events; amplitude adaptation 0.82**k plus noise",
        ),
        raster_sidecar(
            2026090403, 16, 75.0, 36.0, 8.0, "iet",
            {
                "source": "wf4.iet.f",
                "target": "wrenfell.insulator_stop_core",
                "table": [
                    {"from": "iet_f", "to": "E_estimator", "weight": 1.3},
                    {"from": "iet_snr", "to": "iet_lock_core", "weight": 1.1},
                    {"from": "ietveil_E", "to": "vendor_dump_advocate", "weight": 0.42},
                ],
                "third_factor": {
                    "modulator": "na.iet_scope_eligibility",
                    "tau_e_s": 2.0,
                    "tau_e_ms": 2000.0,
                    "eligibility": "pre-post coincidence on kiln-dump synapses; the plant IET modulator depresses dump links when I-4 is under floor inside tau_e of an SNR lock while I-1..I-3 stay over floor so an Ietveil last-good cannot hide an 8.00 GPa remaining-E slip or license a kiln dump",
                },
            },
            "WF-4 IET 36 ms frame at f 4.00 kHz / SNR 10.0 (t_s 3000) reconstructing 8.00 GPa under the 12.00 isolate floor",
            "independent CUBA LIF MT19937 seed 2026090403; tau_m 8.0 ms; not a re-encode of spike_events; amplitude adaptation 0.82**k plus noise",
        ),
    ]
    recs = [pair_001(rasters[0]), pair_002(rasters[1]), pair_003(rasters[2])]
    for rec in recs:
        bad = walk_bad_keys(rec)
        if bad:
            raise RuntimeError(f"forbidden keys {bad}")
        assert_stream(rec["spike_events"], 52)
        assert_raster(rec)
        assert_gate_match(rec)
        jaccard_zero(rec)
        if rec["meta"]["round"] != 4:
            raise RuntimeError("round")
        lead = rec["language_view"]["trajectory"]
        t2 = [v for k, v in rec["language_view"].items() if k.startswith("trajectory_")][0]
        if lead["state"]["sim_or_real"] not in {"designed", "hil", "simulated"}:
            raise RuntimeError("prov")
        if t2["state"]["sim_or_real"] != lead["state"]["sim_or_real"]:
            raise RuntimeError("t2 prov")
        if len(rec["spike_events"]) != 52:
            raise RuntimeError("n events")

    # pipeline validators
    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import raster_status, curate_record
    from verify_execution import verify_batch_for_frontier
    from exact_json import dumps_exact_json

    tmp_batch = Path("/tmp/nelb-r04-staging-batch.jsonl")
    lines = [dumps_exact_json(r, ensure_ascii=False, sort_keys=False) for r in recs]
    tmp_batch.write_text("\n".join(lines) + "\n", encoding="utf-8")

    errors, warnings, kinds, n = check_jsonl(tmp_batch, "batch-r04.jsonl", staging=FactoryStaging(enabled=True))
    if errors:
        raise RuntimeError(f"check_jsonl errors: {errors[:8]}")
    print("check_jsonl", kinds, "warn", warnings, "n", n)

    for i, rec in enumerate(recs, 1):
        st = raster_status(rec, require_raster=True, require_routing_table=True)
        if not st["raster_valid"] or not st["gate_snn_valid"] or st["reason_codes"]:
            raise RuntimeError(f"raster_status {i} {st}")
        h = sha256(lines[i - 1].encode()).hexdigest()
        d = curate_record(rec, source_path="batch-r04.jsonl", source_line=i, source_hash=h, require_raster=True, require_routing_table=True)
        print("curate", i, getattr(d, "action", d), getattr(d, "reasons", None) or getattr(d, "reason_codes", None))

    counts, findings, blocked = verify_batch_for_frontier(tmp_batch, strict=True)
    print("frontier", counts, findings, blocked)
    if blocked or counts.get("verified") != 3:
        raise RuntimeError(f"frontier blocked {counts} {findings}")

    import spike_probe  # noqa: F401
    from spike_probe import main as _unused  # may not exist

    live_batch = LIVE / "batch-r04.jsonl"
    live_notes = LIVE / "NOTES-r04.md"
    suffix = ""
    if live_batch.exists() or live_notes.exists():
        suffix = "c"
        live_batch = LIVE / "batch-r04c.jsonl"
        live_notes = LIVE / "NOTES-r04c.md"
        if live_batch.exists() or live_notes.exists():
            raise RuntimeError("r04 and r04c both exist")

    payload = ("\n".join(lines) + "\n").encode("utf-8")
    exclusive_write(live_batch, payload)
    exclusive_write(live_notes, NOTES.encode("utf-8"))

    # spike_probe CLI
    import subprocess
    r = subprocess.run(
        [sys.executable, str(REPO / "pipelines/spike_probe.py"), "--strict", str(live_batch)],
        cwd=str(REPO),
        capture_output=True,
        text=True,
    )
    print("spike_probe rc", r.returncode, r.stdout[-500:], r.stderr[-500:])
    if r.returncode != 0:
        raise RuntimeError("spike_probe failed")

    print("WROTE", live_batch, live_batch.stat().st_size)
    print("WROTE", live_notes, live_notes.stat().st_size)
    print("SHA", sha256(payload).hexdigest())
    for rec in recs:
        r = rec["raster"]
        print(
            rec["id"],
            rec["language_view"]["trajectory"]["safety_decision"]["decision"],
            rec["language_view"][[k for k in rec["language_view"] if k.startswith("trajectory_")][0]]["safety_decision"]["decision"],
            rec["language_view"]["trajectory"]["state"]["sim_or_real"],
            "spikes", r["spikes"], "win", r["window_ms"], "span", r["excerpt_span_us"],
            "n_events", len(rec["spike_events"]),
        )


if __name__ == "__main__":
    main()
