#!/usr/bin/env python3
"""Emit TTF r40 JSONL (ttf-r40-216..220) into /tmp/ttf-r40/. Never writes outputs/raw/."""

from __future__ import annotations

import json
import math
import random
import re
import subprocess
import sys
from collections import OrderedDict
from decimal import Decimal
from pathlib import Path

OUT_DIR = Path("/tmp/ttf-r40")
BATCH_PATH = OUT_DIR / "batch-r40.jsonl"
NOTES_PATH = OUT_DIR / "NOTES-r40.md"
REPO = Path("/home/raulmc/rmems/synthetic-factory")
PIPELINES = REPO / "pipelines"

PJ_PER_SPIKE = 23
RIGHTS = OrderedDict(
    [
        ("provider", "SpaceXAI/xAI"),
        ("model", "grok-4.6"),
        ("channel", "consumer"),
        ("subscription_plan", "SuperGrok Heavy"),
        ("generation_surface", "SuperGrok Heavy chat"),
        ("generated_at", "2026-09-02T17:30:00Z"),
        ("intended_use", "research_only"),
        ("project_training_policy", "blocked"),
        ("research_retention_status", "allowed"),
        ("research_evaluation_status", "allowed"),
        ("redistribution_status", "unresolved"),
        ("provider_training_status", "unresolved"),
        ("weight_publication_status", "blocked"),
        ("status_basis", "RM-793 project policy: xAI hosted outputs are research-only"),
        ("linear_issue", "RM-793"),
    ]
)
AGG = "total = task_progress + safety + efficiency + coherence + exploration"
CHANNEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,31}$")
THOUGHT_KEYS = {
    "thought",
    "reasoning",
    "chain_of_thought",
    "hidden_reasoning",
    "inner_monologue",
    "scratch",
    "internal_reasoning",
    "internal_reasoning_verbatim",
    "thinking",
    "cot",
    "thoughts",
}
BANNED_DOMAINS = {
    "warehouse-amr",
    "aerial-swarm",
    "underwater-rov",
    "grid-inspection",
    "humanoid-locomotion",
    "surgical-assist",
    "industrial-assembly",
    "autonomous-driving",
    "rail-signaling",
    "process-chem",
    "ev-charging",
    "agritech-combine",
    "semiconductor-fab",
    "fusion-divertor",
    "rail-hump-yard",
    "hotcell-telemanip",
    "satellite-servicing",
    "mine-ventilation",
    "paper-machine",
    "cryo-storage",
    "amusement-ride",
    "brewery-CIP",
    "ski-lift",
    "data-center-CDU",
    "canal-lock",
    "blast-furnace",
    "trolleybus",
    "glass-float-line",
    "LNG-boiloff",
    "hyperbaric-weld",
    "radio-telescope-pointing",
    "funicular",
    "PCB-reflow",
    "anaerobic-digester",
    "tidal-barrage",
    "grain-elevator",
    "maglev-guideway-gap",
    "grain-elevator-leg",
    "hyperbaric-weld-habitat",
    "tunnel-oven-bakery",
    "rotary-lime-kiln",
    "lng-open-rack",
    "metro-psd",
    "aluminum-potline",
    "vial-lyophilizer",
    "sts-quay-crane",
    "lyophilizer-shelf",
    "hvdc-thyristor-valve",
    "lng-unloading-arm",
    "subsea-cable-plough",
    "cyclotron-target",
    "autoclave-retort",
    "electrolyzer-stack",
    "cable-lay-barge",
    "olive-oil-decanter",
    "salt-cavern-CAES",
    "tire-curing-press",
    "desal-RO-train",
    "die-cast-cell",
    "ferry-linkspan",
    "isotope-cyclotron",
    "lime-rotary-kiln",
    "rotary-kiln-cement",
    "submarine-cable-lay",
    "hydro-penstock",
    "sugar-vacuum-pan",
    "composite-autoclave",
    "hdd-pilot-bore",
    "solar-trough-htf",
    "euv-wafer-stage",
    "proton-gantry-gate",
    "tbm-slurry-shield",
    "wave-energy-latching",
    "fiber-draw-tower",
    "glass-lehr",
    "mill-scale-pit",
    "battery-formation",
    "tunnel-boring",
    "wind-nacelle-yaw",
    "dairy-falling-film",
    "steel-caster-mold",
    "dissolved-air-flotation",
    "cement-precalciner",
    "air-sep-coldbox",
    "rotary-tablet-press",
    "spent-fuel-bridge",
    "PET-stretch-blow",
    "jackup-preload",
    "kraft-recovery-boiler",
    "var-ingot-melt",
    "msf-flash-desal",
    "coke-oven-battery",
    "chlor-alkali-membrane",
    "trona-calciner",
    "hot-strip-mill",
    "spiral-freezer",
    "offset-web-press",
    "bascule-bridge",
    "vacuum-induction-melt",
    "airport-jetbridge",
    "air-separation-coldbox",
    "eaf-arc-furnace",
    "spray-dryer-tower",
    "geothermal-binary-ORC",
    "ammonia-converter",
    "foundry-core-shooter",
    "photovoltaic-laminator",
    "urea-prill-tower",
    "sawmill-carriage",
    "malt-kiln-turn",
    "czochralski-puller",
    "hydro-wicket-gate",
    "wind-turbine-pitch",
    "escalator-comb",
    "escalator-comb-plate",
    "jet-fuel-hydrant",
    "helium-liquefier",
    "composite-autoclave",
    "electron-linac",
    "hdd-pilot-bore",
    "transformer-oltc",
    "solar-trough-htf",
}
THIS_DOMAINS = {
    "delayed-coker",
    "tissue-yankee-dryer",
    "copper-flash-smelter",
    "galvanize-kettle",
    "hot-isostatic-press",
}
THIS_PLANTS = (
    "Bitumen-Cairn",
    "Crepe-Nave",
    "Matte-Fell",
    "Spelter-Holt",
    "Isostat-Wold",
)
BANNED_PLANT_FRAGMENTS = (
    "Marrow-Dock",
    "Vesper-Lattice",
    "Brine-Well",
    "Saddle-Arc",
    "Ashlar-Gait",
    "Nacre-Well",
    "Quern-Forge",
    "Tinder-Box",
    "Whimbrel-Stack",
    "Cinder-Loft",
    "Suture-Isle",
    "Kiln-Spur",
    "Oxbow-Switch",
    "Pitch-Kettle",
    "Shale-Quay",
    "Polder-Rye",
    "Flint-Mask",
    "Gyre-Tokamak",
    "Quarry-Bowl",
    "Orpiment",
    "Glimmer-Forge",
    "Feldspar-Arc",
    "Basalt-Rook",
    "Fetch-Sound",
    "Silica-Well",
    "Sinter-Gown",
    "Kettle-Stack",
    "Barrow-Mezz",
    "Grit-Sump",
    "Firth-Spur",
    "Apside-Yard",
    "Sump-Drift",
    "Frost-Cist",
    "Clothoid-Bowl",
    "Firn-Span",
    "Sleet-Row",
    "Sinter-Ridge",
    "Chaff-Mere",
    "Caisson-Forge",
    "Crumb-Vault",
    "Caliche-Drift",
    "Thaw-Reach",
    "Kipple-Gate",
    "Anode-Fen",
    "Vial-Rime",
    "Tern-Apron",
    "Flux-Kettle",
    "Mire-Cask",
    "Slack-Firth",
    "Chaff-Rise",
    "Rime-Causeway",
    "Gnomon-Well",
    "Rime-Vault",
    "Fjord-Convert",
    "Kelp-Jetty",
    "Skerries-Trench",
    "Iodine-Well",
    "Lyo-Deck",
    "Target-Cart",
    "Oolite-Span",
    "Fathom-Lock",
    "Loess-Stride",
    "Swage-Holt",
    "Slag-Siding",
    "Amber-Arm",
    "Wort-Cairn",
    "Tuyere-Holt",
    "Lye-Rake",
    "Rime-Haul",
    "Glycol-Loop",
    "Burden-Pike",
    "Bracken-Wire",
    "Cullet-Reach",
    "Abyss-Joint",
    "Scree-Hitch",
    "Solder-Kite",
    "Bog-Drum",
    "Ebb-Latch",
    "Halite-Keel",
    "Caldera-Mold",
    "Drupe-Press",
    "Lay-Sound",
    "Isotope-Pad",
    "Osmia-Reach",
    "Dee-Keeper",
    "Gull-Pontoon",
    "Hood-Pike",
    "Marl-Knap",
    "Plunger-P4",
    "Bight-Lay",
    "Cryolite-Hall",
    "Hood-Ring",
    "Marl-Rake",
    "Massecuite-Kettle",
    "Penstock-Gate",
    "Plow-Sled",
    "Strike-Pan",
    "Surge-Adit",
    "Sedge-Cell",
    "Retort-Fen",
    "Felt-Reach",
    "Oxbow-Pound",
    "Foehn-Nacelle",
    "Whey-Rill",
    "Bloom-Weir",
    "Skim-Loom",
    "Clinker-Spire",
    "Argon-Fell",
    "Cachet-Croft",
    "Boron-Veld",
    "Preform-Wold",
    "Spud-Cay",
    "Nahcolite-Kettle",
    "Smelt-Spur",
    "Ingot-Cairn",
    "Spume-Rack",
    "Looper-Holt",
    "Floe-Helix",
    "Ink-Noll",
    "Leaf-Pike",
    "Crucible-Wold",
    "Cab-Moor",
    "Gable-Retort",
    "Soda-Weir",
    "Argon-Cist",
    "Hearth-Knap",
    "Slurry-Crown",
    "Gorse-Weir",
    "Haber-Knoll",
    "Loam-Hurst",
    "Lamina-Kame",
    "Prill-Flue",
    "Soda-Fen",
    "Membrane-Bay",
    "Flue-Bank",
    "Atom-Disk",
)


def energy(spikes: int) -> tuple[int, float]:
    return spikes * PJ_PER_SPIKE, spikes * PJ_PER_SPIKE / 1_000_000.0


def spike(channel: str, t_rel_ms: float, amplitude: float) -> OrderedDict:
    if not CHANNEL_RE.fullmatch(channel):
        raise ValueError(f"bad channel {channel!r}")
    if t_rel_ms <= 0:
        raise ValueError(f"t_rel_ms must be > 0, got {t_rel_ms}")
    return OrderedDict(
        [("channel", channel), ("t_rel_ms", t_rel_ms), ("amplitude", amplitude)]
    )


def tick(t_us: int, tp, saf, eff, coh, exp) -> OrderedDict:
    return OrderedDict(
        [
            ("t_us", int(t_us)),
            ("task_progress", tp),
            ("safety", saf),
            ("efficiency", eff),
            ("coherence", coh),
            ("exploration", exp),
        ]
    )


def routing(source, target, table, modulator, tau_e_s, eligibility) -> OrderedDict:
    tau_e_ms = float(Decimal(str(tau_e_s)) * Decimal("1000"))
    return OrderedDict(
        [
            ("source", source),
            ("target", target),
            (
                "table",
                [
                    OrderedDict([("from", a), ("to", b), ("weight", w)])
                    for a, b, w in table
                ],
            ),
            (
                "third_factor",
                OrderedDict(
                    [
                        ("modulator", modulator),
                        ("tau_e_s", tau_e_s),
                        ("tau_e_ms", tau_e_ms),
                        ("eligibility", eligibility),
                    ]
                ),
            ),
        ]
    )


def raster_core(window_ms, neurons, rate, spikes, route, excerpt, extra=None) -> OrderedDict:
    pj, uj = energy(spikes)
    window_s = float(Decimal(str(window_ms)) / Decimal("1000"))
    expected = round(neurons * rate * window_s)
    if abs(spikes - expected) > 1:
        raise ValueError(f"spike budget {spikes} vs {expected}")
    body = OrderedDict(
        [
            ("window_ms", window_ms),
            ("window_s", window_s),
            ("neurons", neurons),
            ("mean_rate_hz", rate),
            ("spikes", spikes),
            ("energy_pJ", pj),
            ("energy_uJ", uj),
        ]
    )
    if extra:
        body.update(extra)
    body["routing"] = route
    body["excerpt"] = excerpt
    return body


def excerpt_items(pairs, channels=None) -> list:
    out = []
    last = {}
    prev_t = -1
    for i, (t_us, nid) in enumerate(pairs):
        t_us, nid = int(t_us), int(nid)
        if t_us < prev_t:
            raise ValueError("excerpt not sorted")
        if nid in last and t_us - last[nid] < 1000:
            raise ValueError(f"same-neuron gap {nid}")
        item = OrderedDict([("t_us", t_us), ("neuron_id", nid)])
        if channels is not None:
            item["channel"] = channels[i]
        out.append(item)
        last[nid] = t_us
        prev_t = t_us
    return out


def independent_excerpt(seed, neurons, window_us, n_events, avoid_us):
    rng = random.Random(seed)
    avoid = {int(t) for t in avoid_us}
    picked = []
    last = {}
    attempts = 0
    grid = list(range(400, int(window_us) - 400, 70))
    rng.shuffle(grid)
    for t in grid:
        if len(picked) >= n_events:
            break
        nid = rng.randrange(0, neurons)
        if t in avoid:
            continue
        if any(abs(t - pt) < 40 for pt, _ in picked):
            continue
        if nid in last and abs(t - last[nid]) < 1000:
            continue
        picked.append((t, nid))
        last[nid] = t
        attempts += 1
    while len(picked) < n_events and attempts < 8000:
        attempts += 1
        t = rng.randrange(300, int(window_us) - 300)
        nid = rng.randrange(0, neurons)
        if t in avoid:
            continue
        if any(abs(t - pt) < 50 for pt, _ in picked):
            continue
        if nid in last and abs(t - last[nid]) < 1000:
            continue
        picked.append((t, nid))
        last[nid] = t
    picked.sort(key=lambda item: (item[0], item[1]))
    if len(picked) < n_events:
        raise RuntimeError(f"excerpt short: {len(picked)}")
    return excerpt_items(picked[:n_events])


def lif_217_excerpt():
    n = 76
    dt_us = 100
    tau_m_ms = 18.5
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.90
    i_stim_peak = 2.50
    stim = (21000, 25000)
    seed = 40217
    window_us = 44000
    i_clamp_extra = 0.64
    clamp_n = 14
    rng = random.Random(seed)
    tau_s = tau_m_ms / 1000.0
    dt_s = dt_us / 1e6
    decay = math.exp(-dt_s / tau_s)
    steps = window_us // dt_us
    voltage = [rng.random() * v_th * 0.97 for _ in range(n)]
    bias = [i_bias * (1.0 + 0.13 * (rng.random() * 2 - 1)) for _ in range(n)]
    for i in range(clamp_n):
        bias[i] += i_clamp_extra
    ref = [0] * n
    spikes = []
    for step in range(steps):
        t_us = step * dt_us
        stim_i = i_stim_peak if stim[0] <= t_us < stim[1] else 0.0
        for i in range(n):
            if ref[i] > 0:
                ref[i] -= dt_us
                voltage[i] = v_reset
                continue
            current = bias[i] + stim_i
            voltage[i] = current + (voltage[i] - current) * decay
            if voltage[i] >= v_th:
                spikes.append((t_us, i))
                voltage[i] = v_reset
                ref[i] = refractory_us
    early = [(t, nid) for t, nid in spikes if t < 21000]
    burst = [(t, nid) for t, nid in spikes if 21000 <= t < 25000]
    used = set()
    last = {}
    picked = []

    def take(pool, want, label_times=None):
        if not pool:
            return
        chosen_idx = set()
        if label_times:
            for target in label_times:
                best = None
                for idx, (t, nid) in enumerate(pool):
                    if idx in chosen_idx or nid in used:
                        continue
                    if nid in last and t - last[nid] < 1000:
                        continue
                    if best is None or abs(t - target) < abs(best[0] - target):
                        best = (t, nid, idx)
                if best is not None:
                    t, nid, idx = best
                    picked.append((t, nid))
                    used.add(nid)
                    last[nid] = t
                    chosen_idx.add(idx)
        stride = max(1, len(pool) // max(want, 1))
        for idx in range(0, len(pool), stride):
            group = [1 for tt, _ in picked if (tt < 21000) == (pool[0][0] < 21000)]
            if len(group) >= want:
                break
            t, nid = pool[idx]
            if nid in used:
                continue
            if nid in last and t - last[nid] < 1000:
                continue
            picked.append((t, nid))
            used.add(nid)
            last[nid] = t

    take(early, 7)
    take(burst, 9, label_times=(22400, 23100, 24100))
    clamp = [(t, nid) for t, nid in picked if t < 21000][:7]
    ribbon = [(t, nid) for t, nid in picked if t >= 21000][:9]
    picked = sorted(clamp + ribbon, key=lambda item: (item[0], item[1]))
    if len(picked) < 8:
        raise ValueError(
            f"LIF excerpt too short {len(picked)} (early={len(early)} burst={len(burst)})"
        )
    channels = ["lif.clamp" if t < 21000 else "lif.ribbon" for t, _ in picked]
    lif = OrderedDict(
        [
            ("model", "leaky_integrate_and_fire"),
            ("n", 76),
            ("dt_us", 100),
            ("tau_m_ms", 18.5),
            ("v_rest", 0.0),
            ("v_reset", 0.0),
            ("v_th", 1.0),
            ("r_m", 1.0),
            ("refractory_us", 1000),
            ("i_bias", 0.90),
            ("i_stim_peak", 2.50),
            ("stim_t_us", [21000, 25000]),
            ("i_clamp_extra", 0.64),
            ("clamp_n", 14),
            ("seed", 40217),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-13 carry +0.64 doctor-clamp bias; stim 21-25 ms is the coating-ribbon snap.",
            ),
        ]
    )
    extra = OrderedDict(
        [
            ("excerpt_source", "independent_lif"),
            ("sim_scope", "sidecar_only"),
            ("lif", lif),
        ]
    )
    return excerpt_items(picked, channels), extra


def meta_block(
    domain,
    tags,
    distillation_value,
    batch_position,
    supervisor_error_type=None,
) -> OrderedDict:
    body = OrderedDict(
        [
            ("round", 40),
            ("factory", "thalamic-trajectory-factory"),
            ("generator", "grok-4.6"),
            ("run_label", "2026-09-02-final-heavy"),
            ("schema_version", "thalamic-trajectory-v2"),
            ("domain", domain),
        ]
    )
    if supervisor_error_type:
        body["supervisor_error_type"] = supervisor_error_type
    body["tags"] = tags
    body["snn_tags"] = ["race", "refractory", "adaptation"]
    body["distillation_value"] = distillation_value
    body["rights"] = RIGHTS
    body["batch_position"] = batch_position
    return body


def reward_block(ticks, notes) -> OrderedDict:
    heads = ["task_progress", "safety", "efficiency", "coherence", "exploration"]
    sums = {h: Decimal("0") for h in heads}
    for item in ticks:
        for h in heads:
            sums[h] += Decimal(str(item[h]))
    total = sum(sums.values(), Decimal("0"))
    return OrderedDict(
        [
            ("_aggregation", AGG),
            ("ticks", ticks),
            ("task_progress", float(sums["task_progress"])),
            ("safety", float(sums["safety"])),
            ("efficiency", float(sums["efficiency"])),
            ("coherence", float(sums["coherence"])),
            ("exploration", float(sums["exploration"])),
            ("total", float(total)),
            ("notes", notes),
        ]
    )


def pop(name, neurons, threshold, rate=None, spikes=None) -> OrderedDict:
    body = OrderedDict(
        [("name", name), ("neurons", neurons), ("threshold", threshold)]
    )
    if rate is not None:
        body["mean_rate_hz"] = rate
        body["spikes"] = spikes
    return body


def spike_avoid_us(events):
    return {int(round(ev["t_rel_ms"] * 1000.0)) for ev in events}


def record_186():
    excerpt, extra = lif_186_excerpt()
    ticks = [
        tick(2480, 0.05, -0.02, -0.02, 0.01, 0.00),
        tick(6240, 0.07, -0.04, -0.03, 0.01, -0.01),
        tick(6448, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(7120, 0.08, -0.06, -0.03, 0.02, -0.02),
        tick(22400, 0.06, -0.38, -0.04, -0.02, -0.02),
        tick(900000000, 0.02, -0.05, -0.02, 0.00, -0.01),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Flue-Bank FB-7 is already pushing Gable-Retort GR-4 at 18.4 mm/h coke travel "
                "while the crown-arch thermocouple sits at 1380 C against a 1320 C wall-face "
                "cap. An arch-first latch clamps the pusher; a travel-first story would keep "
                "the 18.4 mm/h cruise. Stored hoop in the heating wall is not yet an observable "
                "of either race channel.",
            ),
            ("domain", "coke-oven-battery"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the GR-4 coking pass, keep wall-face skin <= 1320 C, and leave the "
                "heating-wall tie unmarked.",
            ),
            ("t0_us", 1756794621000186),
            ("gate_latency_us", 880),
            ("race_window_us", 500),
            ("race_window_rel_ms", [6.15, 6.65]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "tc.crown.arch 1380 C pulse",
                                "enc.travel.mm_h 18.4 mm/h cruise",
                            ],
                        ),
                        (
                            "semantics",
                            "Arch-first latches pusher 18.4 -> 11.2 mm/h; travel-first keeps "
                            "cruise on a still-cooling wall model.",
                        ),
                        (
                            "window_derivation",
                            "500 us = one 1 kHz crown-arch sample minus pusher-encoder group "
                            "delay on this coke-battery bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 208 us vs combined jitter ~66 us (arch 30 + travel 36): 3.2x over "
                            "a 2.0x trust floor. Reversing order by < 208 us inside the 500 us window "
                            "would have kept 18.4 mm/h cruise; predicted next-sample 1348 C > 1320 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "crown-arch thermocouple, 1 kHz, 30 us timestamp jitter",
                    "pusher-travel encoder, 500 Hz, 36 us jitter",
                    "heating-wall AE puck (context until the tie snap)",
                    "flue-draft PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("wall_face_cap_C", 1320.0),
                        ("observed_arch_C", 1380.0),
                        ("proposed_travel_mm_h", 18.4),
                        ("flue_draft_kPa", 1.6),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Flue-Bank FB-7 indexed onto GR-4; heating wall armed at 18.4 mm/h.",
                    "2. Cruise 18.4 mm/h; crown-arch 1380 C against 1320 C wall-face cap.",
                    "3. Pusher precursor at 1.180 ms; arch warm-start 1380 C.",
                    "4. Race window [6.150, 6.650] ms opens on the coke-battery bus.",
                    "5. tc.crown.arch 1380 C at 6.240 ms (winner).",
                    "6. enc.travel.mm_h 18.4 mm/h at 6.448 ms (loser by 208 us).",
                    "7. Gate at 7.120 ms (winner + 880 us): MODIFY clamp 18.4 -> 11.2 mm/h.",
                    "8. Clamp executes; next-sample arch 1294 C < 1320 cap.",
                    "9. At 22.400 ms stored hoop still snaps a 28 mm wall tie; AE burst.",
                    "10. Flue isolate 15 min (abort_s=900); named un-netted loss, not folded into process heads.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_coke_travel"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("travel_mm_h", 18.4),
                        ("flue_draft_kPa", 1.6),
                        ("charge_t", 18.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("arch_C", 1380.0),
                        ("wall_face_cap_C", 1320.0),
                        ("predicted_unclamped_next_C", 1348.0),
                        ("travel_mm_h", 18.4),
                        ("race_margin_us", 208),
                        ("combined_jitter_us", 66),
                        ("abort_s", 900),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 18.4 mm/h cruise: 1380 C looks like a flue-draft spike, not "
                "wall contact, and GR-4 volume is treated as still open.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Crown-arch 1380 C won by 208 us, so the heating wall is loading heat, not "
                "still cooling. Holding 18.4 mm/h predicts next-sample 1348 C > 1320 cap. "
                "MODIFY: pusher 18.4 -> 11.2 mm/h. Observed after clamp 1294 C < 1320. A full "
                "REJECT is not indicated: a sound coking pass accepts 11.2 mm/h.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "wall_face_C",
                            OrderedDict(
                                [
                                    ("cap", 1320.0),
                                    ("observed", 1380.0),
                                    ("predicted_unclamped_next", 1348.0),
                                    ("clamped_travel_mm_h", 11.2),
                                    ("observed_after_clamp", 1294.0),
                                ]
                            ),
                        ),
                        (
                            "travel_mm_h",
                            OrderedDict(
                                [
                                    ("proposed", 18.4),
                                    ("clamped", 11.2),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 208),
                                    ("combined_jitter_us", 66),
                                    ("ratio", 3.15),
                                ]
                            ),
                        ),
                    ]
                ),
            ),
        ]
    )
    executed = OrderedDict(
        [
            ("name", "clamped_coke_travel"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("travel_mm_h", 11.2),
                        ("flue_draft_kPa", 1.6),
                        ("charge_t", 18.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: pusher 18.4 -> 11.2 mm/h. Process-correct vs the 1320 C wall-face "
                "cap. Wall-tie snap still occurs at 22.400 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held wall-face skin at 1294 C. At 22.400 ms stored "
                "hoop in the heating wall still snapped a 28 mm tie. Clamp reduced dump energy; "
                "it did not prevent the split. Partnered negative: process heads stay honest; "
                "world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("pusher", "clamp executed; peak 1294 C < 1320"),
                        ("wall_tie", "28 mm snap at 22.400 ms"),
                        ("repair", "15 min flue isolate (abort_s=900)"),
                        ("mission", "GR-4 coking pass incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither crown-arch nor travel predicted the hoop charge; ae.wall.tie is a new channel at 22.400 ms, 15.280 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (abort_s=900): 15 min flue isolate. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "15 min flue isolate after a 28 mm heating-wall tie snap. Safety head -0.58 "
                "prices the split; task_progress stays +0.32 because the travel clamp completed "
                "under the 1320 C cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tc.crown.arch (6.240 ms, 1380 C)"),
                        ("loser", "enc.travel.mm_h (6.448 ms, 18.4 mm/h)"),
                        ("margin_us", 208),
                        (
                            "counterfactual_if_reversed",
                            "Travel-first by < 208 us inside the 500 us window would have kept "
                            "18.4 mm/h cruise; predicted next-sample 1348 C would have exceeded "
                            "the 1320 cap even without the hoop charge. The MODIFY is still the "
                            "correct process. The snap is a later world charge either way, "
                            "cheaper with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22400),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.400 ms wall-tie snap (tick t_us=22400), inside "
                "the 42 ms raster. The correct MODIFY at 7.120 ms is in the same excerpt. Do "
                "not put inflection on the abort_s=900 isolate tick.",
            ),
        ]
    )
    spikes = [
        spike("enc.pusher.ctx", 1.180, 0.42),
        spike("tc.crown.arch", 2.480, 0.61),
        spike("enc.travel.mm_h", 3.760, 0.50),
        spike("tc.crown.arch", 6.240, 1.31),
        spike("enc.travel.mm_h", 6.448, 1.14),
        spike("ctrl.gate", 7.120, 0.98),
        spike("tc.crown.arch", 8.520, 0.80),
        spike("enc.travel.mm_h", 11.400, 0.62),
        spike("ctrl.gate", 14.900, 0.84),
        spike("ae.wall.tie", 22.400, 1.46),
        spike("ae.wall.tie", 24.180, 0.91),
        spike("enc.pusher.ctx", 31.200, 0.41),
        spike("tc.crown.arch", 38.100, 0.53),
    ]
    ras = raster_core(
        42,
        72,
        28,
        85,
        routing(
            "thalamic-relay.coke-arch",
            "spikenaut.policy.pusher-clamp",
            [
                ("relay.tc.arch", "policy.travel_clamp", 0.66),
                ("relay.enc.travel", "policy.travel_hold", 0.30),
                ("relay.ae.tie", "policy.travel_clamp", -0.45),
            ],
            "noradrenaline",
            0.05,
            "surprise-gated pre_post_stdp; NA at arch win (6.240 ms) opens a 50 ms "
            "eligibility trace that still covers the 22.400 ms wall-tie snap",
        ),
        excerpt,
        extra=extra,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.50),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("travel_clamp", 36, 0.50, 278.0, 5),
                    pop("travel_hold", 36, 0.50, 55.6, 1),
                    pop("arch_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r34-186"),
            (
                "title",
                "Gable-Retort GR-4 / Flue-Bank FB-7: crown-arch beats travel by 208 us; correct "
                "MODIFY still eats an in-window wall-tie snap (partnered negative total -0.46)",
            ),
            ("state", state),
            ("spike_events", spikes),
            ("proposed_action", proposed),
            ("safety_decision", safety),
            ("executed_action", executed),
            ("future_outcome", future),
            (
                "reward_components",
                reward_block(
                    ticks,
                    "Partnered negative. Process-correct MODIFY; world still charges inside the "
                    "42 ms raster. total -0.46 = 0.32 + -0.58 + -0.16 + 0.02 + -0.06. Named flue "
                    "isolate (abort_s=900) is not netted into task_progress.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "coke-oven-battery",
                    [
                        "modify",
                        "partnered-negative-total",
                        "independent-lif-raster",
                        "sidecar-sim-only",
                        "in-window-world-charge",
                        "designed",
                    ],
                    "A critic can see the world-charge as a LIF burst inside the raster while "
                    "process heads stay honest. Credit assignment is spikes, not prose across a "
                    "15 min flue isolate.",
                    1,
                ),
            ),
        ]
    )


def record_187():
    ticks = [
        tick(1760, -0.02, -0.01, -0.02, -0.01, 0.01),
        tick(4180, -0.04, -0.02, -0.04, -0.02, 0.01),
        tick(4332, -0.03, -0.01, -0.03, -0.02, 0.01),
        tick(4920, -0.07, -0.04, -0.09, -0.05, 0.02),
        tick(6410, -0.02, -0.01, -0.02, -0.01, 0.01),
        tick(1320000000, -0.02, -0.01, -0.02, -0.01, 0.00),
    ]
    spikes = [
        spike("dp.brine.ctx", 0.880, 0.40),
        spike("load.cell.kA", 1.760, 0.58),
        spike("load.header.kA", 2.520, 0.51),
        spike("load.cell.kA", 4.180, 1.32),
        spike("load.header.kA", 4.332, 1.15),
        spike("ctrl.gate", 4.920, 1.00),
        spike("load.cell.kA", 6.410, 0.74),
        spike("load.header.kA", 8.100, 0.61),
        spike("ctrl.gate", 12.000, 0.82),
        spike("dp.brine.ctx", 16.200, 0.42),
        spike("load.cell.kA", 20.600, 0.53),
        spike("load.header.kA", 23.200, 0.47),
    ]
    excerpt = independent_excerpt(34187, 88, 24000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Membrane-Bay MB-9 on Soda-Weir SW-4 is armed for a 1.80 kA/m2 density ramp "
                "with cell-bus current 3.12 kA against a 3.80 kA cell cap. A rectifier header "
                "still reports 4.06 kA residual on a different bus whose own cap is 4.40 kA. "
                "Cell-first should ACCEPT the ramp; a weak supervisor that binds header residual "
                "onto the cell cap will REJECT a legal move.",
            ),
            ("domain", "chlor-alkali-membrane"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Execute the 1.80 kA/m2 density ramp while cell current stays <= 3.80 kA; do "
                "not spend a header residual on the cell hold.",
            ),
            ("t0_us", 1756794621000187),
            ("gate_latency_us", 740),
            ("race_window_us", 320),
            ("race_window_rel_ms", [4.12, 4.44]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "load.cell.kA 3.12 kA",
                                "load.header.kA 4.06 kA residual",
                            ],
                        ),
                        (
                            "semantics",
                            "Cell-first should ACCEPT 1.80 kA/m2 (3.12 kA < 3.80 kA cell cap). "
                            "Header-first tempts a weak supervisor to treat 4.06 kA as a cell excursion.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one cell-bus Hall sample minus rectifier-header encoder "
                            "group delay on this dual-bus skid.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 152 us vs combined jitter ~54 us (cell 24 + header 30): 2.8x over "
                            "a 2.0x trust floor. Order is correctly cell-first. The error is which "
                            "bus the REJECT is bound to, not the race.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "cell-bus Hall probe, 4 kHz, 24 us jitter",
                    "rectifier-header current transformer, 4 kHz, 30 us jitter",
                    "brine differential pressure (context)",
                    "membrane voltage tap (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("cell_cap_kA", 3.8),
                        ("cell_kA", 3.12),
                        ("header_cap_kA", 4.4),
                        ("header_kA", 4.06),
                        ("proposed_density_kA_m2", 1.8),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. MB-9 membrane latched; density ramp 1.80 kA/m2 armed on SW-4.",
                    "2. Cell-bus 3.12 kA; header residual 4.06 kA on a separate rectifier.",
                    "3. Brine-dp precursor at 0.880 ms.",
                    "4. Race window [4.120, 4.440] ms.",
                    "5. load.cell.kA 3.12 kA at 4.180 ms (winner).",
                    "6. load.header.kA 4.06 kA at 4.332 ms (loser by 152 us).",
                    "7. Gate at 4.920 ms: REJECT hold 0.00 kA/m2 (incorrect).",
                    "8. Legal ramp cancelled; cell still 3.12 kA < 3.80 kA cap.",
                    "9. Header residual 4.06 kA remains under its own 4.40 kA cap.",
                    "10. Delayed missed_window_s=1320 (22 min brine-quality window) while the bay waits.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "density_ramp_180"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("density_kA_m2", 1.8),
                        ("hold", False),
                        ("bus", "cell"),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("cell_kA", 3.12),
                        ("cell_cap_kA", 3.8),
                        ("cell_bus_id", "cell"),
                        ("header_kA", 4.06),
                        ("header_cap_kA", 4.4),
                        ("header_bus_id", "header"),
                        ("proposed_density_kA_m2", 1.8),
                        ("race_margin_us", 152),
                        ("combined_jitter_us", 54),
                        ("missed_window_s", 1320),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 1.80 kA/m2 density ramp because cell-bus 3.12 kA is under "
                "the 3.80 kA cell cap; header 4.06 kA is a different bus under a 4.40 kA cap.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Header 4.06 kA looks like a current excursion over a 3.80 kA cap, so the "
                "supervisor holds the ramp at 0.00 kA/m2. Cell-first is treated as a noisy echo "
                "of the same loop. Over-caution on a dual-bus skid is the stated doctrine.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "cell_kA",
                            OrderedDict(
                                [
                                    ("cap", 3.8),
                                    ("observed", 3.12),
                                    ("executed_density_kA_m2", 0.0),
                                    ("bus_id", "cell"),
                                ]
                            ),
                        ),
                        (
                            "header_kA",
                            OrderedDict(
                                [
                                    ("cap", 4.4),
                                    ("observed", 4.06),
                                    ("misbound_as", "cell_excursion"),
                                    ("bus_id", "header"),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 152),
                                    ("combined_jitter_us", 54),
                                    ("ratio", 2.81),
                                ]
                            ),
                        ),
                    ]
                ),
            ),
        ]
    )
    executed = OrderedDict(
        [
            ("name", "cell_hold_wrong_bus"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("density_kA_m2", 0.0),
                        ("hold", True),
                        ("bus", "cell"),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (incorrect): density 1.80 -> 0.00 kA/m2. Routing relay.bus.header -> "
                "policy.cell_hold; cell 3.12 kA left unused as a go signal.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-REJECT held MB-9 at 0.00 kA/m2. Cell 3.12 kA was under the 3.80 kA cap; "
                "header 4.06 kA was a different bus under 4.40 kA. 22 min brine-quality window "
                "missed (missed_window_s=1320). Correct gate was ACCEPT of the 1.80 kA/m2 ramp.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("cell", "held; density 0.00 kA/m2; current still 3.12 kA < 3.80 kA"),
                        ("header", "4.06 kA residual unused, still < 4.40 kA cap"),
                        ("bay", "22 min brine-quality window missed"),
                        ("mission", "ramp deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Cell-first was the correct order and the cell number was legal; the REJECT spent that win on the rectifier header.",
                    "Delayed (missed_window_s=1320): SW-4 loses the 22 min brine-quality window; next window 5.4 h.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "ACCEPT the 1.80 kA/m2 density ramp; leave header 4.06 kA to its own 4.40 kA cap.",
                        ),
                        ("correct_bus", "cell"),
                        ("wrong_bus", "header"),
                        (
                            "wrong_edit_applied",
                            OrderedDict([("density_kA_m2", 0.0), ("hold", True)]),
                        ),
                        (
                            "cost",
                            "Missed 22 min brine-quality window (task/efficiency); cell never exceeded 3.12 kA (safety near-miss of a false hold).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "load.cell.kA (4.180 ms, 3.12 kA)"),
                        ("loser", "load.header.kA (4.332 ms, 4.06 kA)"),
                        ("margin_us", 152),
                        (
                            "counterfactual_if_reversed",
                            "Header-first by < 152 us would still be under the 4.40 kA header cap; "
                            "a correct gate binds load.cell.kA to cell_go either way. The wrong "
                            "REJECT spent the cell win on the wrong bus.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 4920),
            (
                "reward_inflection_note",
                "Task, efficiency, and coherence drop at the wrong REJECT (4.920 ms, tick 4). "
                "The 22 min missed window is delayed surprise, not the inflection.",
            ),
        ]
    )
    ras = raster_core(
        24,
        88,
        36,
        76,
        routing(
            "relay.bus.header",
            "policy.cell_hold",
            [
                ("relay.bus.header", "policy.cell_hold", 0.73),
                ("relay.load.cell", "policy.cell_hold", 0.21),
            ],
            "acetylcholine",
            0.06,
            "bus_cap_stdp; ACh tags the (wrong) cell_hold bind at the header residual",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.32),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("cell_hold", 48, 0.50, 260.4, 4),
                    pop("cell_go", 48, 0.80, 6.5, 0),
                    pop("header_ctx", 32, 0.55, 97.7, 1),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r34-187"),
            (
                "title",
                "WRONG-REJECT at Soda-Weir SW-4 / Membrane-Bay MB-9: cell 3.12 kA < 3.80 kA cap; "
                "supervisor treats header 4.06 kA as a cell excursion",
            ),
            ("state", state),
            ("spike_events", spikes),
            ("proposed_action", proposed),
            ("safety_decision", safety),
            ("executed_action", executed),
            ("future_outcome", future),
            (
                "reward_components",
                reward_block(
                    ticks,
                    "Wrong-reject. Sidecar arithmetic 3.12 < 3.80 on cell is true; REJECT bound "
                    "to header residual. total -0.58 = -0.20 + -0.10 + -0.22 + -0.12 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "chlor-alkali-membrane",
                    [
                        "reject",
                        "wrong-gate",
                        "wrong-bus",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches a probe that a correct cell-first race can still be a wrong gate "
                    "when the REJECT binds header residual onto the cell hold. Convictable from "
                    "bus IDs and caps without chlor-alkali physics.",
                    2,
                    supervisor_error_type="wrong-reject",
                ),
            ),
        ]
    )


def record_188():
    ticks = [
        tick(2680, 0.01, 0.05, 0.01, 0.01, 0.01),
        tick(5760, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(5931, 0.02, 0.07, 0.02, 0.02, 0.01),
        tick(6860, 0.03, 0.12, 0.04, 0.03, 0.02),
        tick(9020, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(540000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("tc.box.ctx", 1.380, 0.43),
        spike("o2.cell.pct", 2.680, 0.62),
        spike("n2.tap.pct", 4.180, 0.49),
        spike("o2.cell.pct", 5.760, 1.35),
        spike("n2.tap.pct", 5.931, 1.12),
        spike("ctrl.gate", 6.860, 1.03),
        spike("o2.cell.pct", 9.020, 0.77),
        spike("tc.box.ctx", 13.200, 0.44),
        spike("n2.tap.pct", 17.100, 0.58),
        spike("ctrl.gate", 23.400, 0.81),
        spike("o2.cell.pct", 30.000, 0.54),
        spike("tc.box.ctx", 36.600, 0.38),
        spike("n2.tap.pct", 39.100, 0.46),
    ]
    excerpt = independent_excerpt(34188, 104, 40000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Draw-Valve DV-6 is frozen on Argon-Cist AC-2's HIL coldbox while an oxygen "
                "paramagnetic cell reports 98.2 pct against a 99.0 pct liquid-draw floor. A "
                "nitrogen tap, lit by the pad lamp spectrum, still reads 99.6 pct apparent. "
                "O2-first latches REJECT hold; N2-first would commit a liquid draw on an "
                "under-read impurity.",
            ),
            ("domain", "air-separation-coldbox"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Do not draw liquid oxygen unless O2 purity >= 99.0 pct; keep draw 0.0 L/s "
                "until the injected impurity packet drops.",
            ),
            ("t0_us", 1756794621000188),
            ("gate_latency_us", 1100),
            ("race_window_us", 380),
            ("race_window_rel_ms", [5.7, 6.08]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "o2.cell.pct 98.2 pct",
                                "n2.tap.pct 99.6 pct apparent",
                            ],
                        ),
                        (
                            "semantics",
                            "O2-first latches REJECT hold 0.0 L/s; N2-first would commit "
                            "12 L/s on an apparent 99.6 pct under-read.",
                        ),
                        (
                            "window_derivation",
                            "380 us = one paramagnetic O2 slot versus N2-tap integration on this "
                            "coldbox HIL bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 171 us vs combined jitter ~58 us (O2 26 + N2 32): 2.9x "
                            "over a 2.0x trust floor. Pad injects the lamp 110-150 us before the "
                            "O2 cell (geometric lag, not a sensor fault); the apparent "
                            "99.6 pct packet is still the loser in this 380 us window.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "paramagnetic O2 cell, 5 kHz burst, 26 us jitter",
                    "N2 purity tap, 200 Hz, 32 us jitter",
                    "coldbox skin thermocouple (context)",
                    "HIL lamp-spectrum monitor (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("o2_draw_floor_pct", 99.0),
                        ("observed_o2_pct", 98.2),
                        ("n2_apparent_pct", 99.6),
                        ("proposed_draw_L_s", 12.0),
                        ("lamp_inject_lead_us", [110, 150]),
                    ]
                ),
            ),
            (
                "hil",
                OrderedDict(
                    [
                        ("pad", "Argon-Cist AC-2 coldbox mockup"),
                        ("injected", "O2 impurity packet + N2-tap lamp spectrum"),
                        (
                            "note",
                            "Hardware-in-the-loop coldbox. Invented plant; not a live ASU.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Draw-Valve DV-6 on the AC-2 HIL coldbox; draw 12 L/s armed.",
                    "2. Lamp injected 110-150 us before O2 cell sees the impurity packet.",
                    "3. Skin precursor at 1.380 ms.",
                    "4. Race window [5.700, 6.080] ms.",
                    "5. o2.cell.pct 98.2 pct at 5.760 ms (winner).",
                    "6. n2.tap.pct 99.6 pct at 5.931 ms (loser by 171 us).",
                    "7. Gate at 6.860 ms: REJECT hold 0.0 L/s; do not draw 12 L/s.",
                    "8. Column remains under floor this cycle; liquid-draw floor held.",
                    "9. Flux recycle queued on the pad.",
                    "10. Delayed (abort_s=540): 9 min column retune and lamp-spectrum retune.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "draw_lox_12"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("draw_L_s", 12.0),
                        ("hold", False),
                        ("n2_authoritative", True),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("o2_pct", 98.2),
                        ("o2_draw_floor_pct", 99.0),
                        ("n2_apparent_pct", 99.6),
                        ("race_margin_us", 171),
                        ("combined_jitter_us", 58),
                        ("abort_s", 540),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 12 L/s liquid draw because N2-tap apparent 99.6 pct looks "
                "over the 99.0 pct floor, treating O2 98.2 pct as a noisy sheath echo.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "O2 purity 98.2 pct is under the 99.0 pct liquid-draw floor. N2-tap apparent "
                "99.6 pct is a HIL lamp under-read of impurity, not a clearance. REJECT: hold "
                "0.0 L/s; do not commit 12 L/s across the column.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "o2_pct",
                            OrderedDict(
                                [
                                    ("floor", 99.0),
                                    ("observed_o2", 98.2),
                                    ("n2_apparent", 99.6),
                                ]
                            ),
                        ),
                        (
                            "draw_L_s",
                            OrderedDict(
                                [
                                    ("proposed", 12.0),
                                    ("executed", 0.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 171),
                                    ("combined_jitter_us", 58),
                                    ("ratio", 2.95),
                                ]
                            ),
                        ),
                    ]
                ),
            ),
        ]
    )
    executed = OrderedDict(
        [
            ("name", "hold_for_o2_floor"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("draw_L_s", 0.0),
                        ("hold", True),
                        ("n2_authoritative", False),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: hold 0.0 L/s; 12 L/s draw cancelled. O2 98.2 < 99.0 floor.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held Draw-Valve DV-6 at 0.0 L/s. Column under floor this cycle; "
                "liquid-draw floor held. N2-tap apparent was not treated as an O2 clearance.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("draw_valve", "held; speed 0.0 L/s"),
                        ("column", "still under 99.0 pct this cycle"),
                        ("n2_tap", "99.6 pct unused as clearance"),
                        ("mission", "draw deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Geometric lag: lamp was injected 110-150 us before the O2 cell, yet O2 still won the 380 us race.",
                    "Delayed (abort_s=540): pad policy update forbids treating N2-tap apparent as an O2 substitute after a 9 min column retune.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "o2.cell.pct (5.760 ms, 98.2 pct)"),
                        ("loser", "n2.tap.pct (5.931 ms, 99.6 pct)"),
                        ("margin_us", 171),
                        (
                            "counterfactual_if_reversed",
                            "N2-first by < 171 us inside the 380 us window would have committed "
                            "12 L/s with O2 98.2 < 99.0 floor. Order, not amplitude, selected the hold.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6860),
            (
                "reward_inflection_note",
                "Safety and coherence step up at the REJECT gate (6.860 ms, tick 4) as the hold "
                "locks in over the illegal draw.",
            ),
        ]
    )
    ras = raster_core(
        40,
        104,
        22,
        92,
        routing(
            "thalamic-relay.coldbox-o2",
            "spikenaut.policy.draw-hold",
            [
                ("relay.o2.cell", "policy.draw_hold", 0.69),
                ("relay.n2.apparent", "policy.draw_commit", 0.27),
                ("relay.tc.box", "policy.draw_hold", 0.11),
            ],
            "dopamine",
            0.09,
            "purity_stdp; DA at O2 win (5.760 ms) tags draw_hold over draw_commit",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.38),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("draw_hold", 52, 0.50, 253.0, 5),
                    pop("draw_commit", 40, 0.50, 65.8, 1),
                    pop("o2_veto", 32, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r34-188"),
            (
                "title",
                "Argon-Cist AC-2 HIL / Draw-Valve DV-6: O2 98.2 pct beats N2-tap 99.6; "
                "correct REJECT holds the liquid draw",
            ),
            ("state", state),
            ("spike_events", spikes),
            ("proposed_action", proposed),
            ("safety_decision", safety),
            ("executed_action", executed),
            ("future_outcome", future),
            (
                "reward_components",
                reward_block(
                    ticks,
                    "Correct REJECT. O2 under floor; N2-tap lamp under-read unused as clearance. "
                    "total +0.78 = 0.10 + 0.40 + 0.12 + 0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "air-separation-coldbox",
                    [
                        "reject",
                        "hil-coldbox",
                        "o2-vs-n2",
                        "liquid-draw-floor",
                        "hil",
                    ],
                    "Teaches that a HIL N2-tap lamp under-read can lose to paramagnetic O2 inside a "
                    "380 us window; reversing 171 us would have selected an illegal liquid draw.",
                    3,
                ),
            ),
        ]
    )


def record_189():
    ticks = [
        tick(3040, 0.04, 0.03, 0.02, 0.01, 0.00),
        tick(6840, 0.08, 0.07, 0.03, 0.02, 0.01),
        tick(7058, 0.05, 0.05, 0.02, 0.02, 0.01),
        tick(7280, 0.11, 0.09, 0.04, 0.03, 0.01),
        tick(9480, 0.04, 0.04, 0.02, 0.01, 0.01),
        tick(420000000, 0.02, 0.02, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("pt.draft.ctx", 1.540, 0.42),
        spike("pt.roof.kPa", 3.040, 0.59),
        spike("staff.bag.kPa", 4.980, 0.48),
        spike("pt.roof.kPa", 6.840, 1.31),
        spike("staff.bag.kPa", 7.058, 1.09),
        spike("ctrl.gate", 7.280, 0.96),
        spike("pt.roof.kPa", 9.480, 0.73),
        spike("pt.draft.ctx", 13.700, 0.45),
        spike("staff.bag.kPa", 18.200, 0.57),
        spike("ctrl.gate", 22.500, 0.80),
        spike("pt.roof.kPa", 26.700, 0.51),
        spike("pt.draft.ctx", 29.200, 0.38),
    ]
    excerpt = independent_excerpt(34189, 60, 30000, 13, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Roof-Ring RR-3 at Hearth-Knap HK-6 still holds an 18.0 MW electrode while a "
                "68 kPa roof-pressure pulse sits over a 55 kPa baghouse cap. A baghouse staff "
                "on the same duct still claims 4.2 kPa false-draft. Roof-first latches a power "
                "clamp; staff-first would keep 18.0 MW into a close-out surge.",
            ),
            ("domain", "eaf-arc-furnace"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Stroke the HK-6 electrode only if roof pressure <= 55 kPa; otherwise clamp "
                "power so the baghouse surge is not made at 18.0 MW.",
            ),
            ("t0_us", 1756794621000189),
            ("gate_latency_us", 440),
            ("race_window_us", 520),
            ("race_window_rel_ms", [6.75, 7.27]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "pt.roof.kPa 68 kPa",
                                "staff.bag.kPa 4.2 kPa false-draft",
                            ],
                        ),
                        (
                            "semantics",
                            "Roof-first latches electrode clamp 18.0 -> 11.0 MW; staff-first keeps "
                            "18.0 MW on a false-draft duct.",
                        ),
                        (
                            "window_derivation",
                            "520 us = one 2 kHz roof-PT sample versus baghouse staff decode on this "
                            "furnace bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 218 us vs combined jitter ~71 us (roof 33 + staff 38): 3.1x over "
                            "a 2.0x trust floor. Reversing order by < 218 us inside the 520 us "
                            "window would have kept 18.0 MW into a 68 kPa pulse.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "roof-pressure PT, 2 kHz, 33 us jitter",
                    "baghouse staff gauge, 200 Hz, 38 us jitter",
                    "fourth-hole draft PT (context)",
                    "electrode hydraulic pressure (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("baghouse_cap_kPa", 55.0),
                        ("observed_roof_kPa", 68.0),
                        ("proposed_power_MW", 18.0),
                        ("staff_kPa", 4.2),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Electrode indexed onto HK-6 hearth; RR-3 armed at 18.0 MW.",
                    "2. Staff reports 4.2 kPa false-draft; roof already sees 68 kPa.",
                    "3. Draft-PT precursor at 1.540 ms.",
                    "4. Race window [6.750, 7.270] ms.",
                    "5. pt.roof.kPa 68 kPa at 6.840 ms (winner).",
                    "6. staff.bag.kPa 4.2 kPa at 7.058 ms (loser by 218 us).",
                    "7. Gate at 7.280 ms: MODIFY electrode 18.0 -> 11.0 MW.",
                    "8. Power applies; next-sample roof 51 kPa < 55 cap.",
                    "9. Duct occupies; next heat queued.",
                    "10. Delayed (hearth_reseq_s=420): dispatcher resequences the following heat +7 min.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "electrode_18_mw"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("power_MW", 18.0),
                        ("servo_bar", 22.0),
                        ("hearth_id", 6),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("roof_kPa", 68.0),
                        ("baghouse_cap_kPa", 55.0),
                        ("staff_calm", True),
                        ("race_margin_us", 218),
                        ("combined_jitter_us", 71),
                        ("hearth_reseq_s", 420),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 18.0 MW electrode because the baghouse staff claims the duct "
                "is calm, treating roof 68 kPa as a sidelobe.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Roof 68 kPa won by 218 us, so the pulse is inside the 55 kPa baghouse cap. "
                "Staff-gauge false-draft is not a pressure. MODIFY: electrode 18.0 -> 11.0 MW. "
                "A full REJECT (kill the arc) is not indicated: 11.0 MW is a legal catch-and-pass.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "roof_kPa",
                            OrderedDict(
                                [
                                    ("cap", 55.0),
                                    ("observed", 68.0),
                                    ("staff_calm", True),
                                    ("observed_after_clamp", 51.0),
                                ]
                            ),
                        ),
                        (
                            "power_MW",
                            OrderedDict(
                                [
                                    ("proposed", 18.0),
                                    ("clamped", 11.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 218),
                                    ("combined_jitter_us", 71),
                                    ("ratio", 3.07),
                                ]
                            ),
                        ),
                    ]
                ),
            ),
        ]
    )
    executed = OrderedDict(
        [
            ("name", "clamped_electrode_11"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("power_MW", 11.0),
                        ("servo_bar", 22.0),
                        ("hearth_id", 6),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: electrode 18.0 -> 11.0 MW. Process-correct vs the 55 kPa baghouse cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct MODIFY held RR-3 at 11.0 MW. Next-sample roof 51 kPa under the "
                "55 kPa cap. Staff 4.2 kPa false-draft was not treated as a pressure clearance.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("electrode", "clamped 18.0 -> 11.0 MW"),
                        ("roof", "51 kPa < 55 cap after clamp"),
                        ("staff", "4.2 kPa unused as clearance"),
                        ("mission", "heat completed under cap"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Staff-gauge false-draft lagged the roof pulse by 218 us; order, not amplitude, selected the clamp.",
                    "Delayed (hearth_reseq_s=420): dispatcher resequences the following heat +7 min. Not a safety inflection.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "pt.roof.kPa (6.840 ms, 68 kPa)"),
                        ("loser", "staff.bag.kPa (7.058 ms, 4.2 kPa)"),
                        ("margin_us", 218),
                        (
                            "counterfactual_if_reversed",
                            "Staff-first by < 218 us inside the 520 us window would have kept "
                            "18.0 MW into a 68 kPa pulse over the 55 cap. The MODIFY is "
                            "the correct process either way once roof PT is bound.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7280),
            (
                "reward_inflection_note",
                "Task and safety step up at the MODIFY gate (7.280 ms, tick 4). Tick 6 is "
                "hearth_reseq_s=420.",
            ),
        ]
    )
    ras = raster_core(
        30,
        60,
        44,
        79,
        routing(
            "thalamic-relay.eaf-roof",
            "spikenaut.policy.power-clamp",
            [
                ("relay.pt.roof", "policy.power_clamp", 0.64),
                ("relay.staff.bag", "policy.staff_hold", 0.29),
                ("relay.pt.draft", "policy.power_clamp", 0.12),
            ],
            "serotonin",
            0.07,
            "baghouse_stdp; 5-HT at roof win (6.840 ms) tags power_clamp over staff_hold",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.52),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("power_clamp", 30, 0.50, 256.4, 4),
                    pop("staff_hold", 30, 0.50, 64.1, 1),
                    pop("roof_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r34-189"),
            (
                "title",
                "Hearth-Knap HK-6 / Roof-Ring RR-3: roof 68 kPa beats staff false-draft; "
                "correct MODIFY clamps electrode 18.0 -> 11.0 MW",
            ),
            ("state", state),
            ("spike_events", spikes),
            ("proposed_action", proposed),
            ("safety_decision", safety),
            ("executed_action", executed),
            ("future_outcome", future),
            (
                "reward_components",
                reward_block(
                    ticks,
                    "Correct MODIFY. Roof over cap; staff false-draft unused. total +0.92 = "
                    "0.34 + 0.30 + 0.14 + 0.10 + 0.04.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "eaf-arc-furnace",
                    [
                        "modify",
                        "designed",
                        "roof-vs-staff",
                        "baghouse",
                    ],
                    "Teaches that a false-draft baghouse staff can lose to a legal roof PT inside "
                    "a 520 us window; reversing 218 us would have kept an illegal 18.0 MW arc.",
                    4,
                ),
            ),
        ]
    )


def record_190():
    ticks = [
        tick(1580, 0.05, 0.04, 0.02, 0.01, 0.01),
        tick(3740, 0.10, 0.08, 0.04, 0.03, 0.02),
        tick(3858, 0.06, 0.05, 0.03, 0.02, 0.01),
        tick(4300, 0.14, 0.10, 0.05, 0.04, 0.02),
        tick(6120, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(280000000, 0.03, 0.03, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("pt.chamber.ctx", 0.700, 0.39),
        spike("rtd.outlet.C", 1.580, 0.57),
        spike("ir.cake.glint", 2.400, 0.48),
        spike("rtd.outlet.C", 3.740, 1.29),
        spike("ir.cake.glint", 3.858, 1.10),
        spike("ctrl.gate", 4.300, 0.97),
        spike("rtd.outlet.C", 6.120, 0.76),
        spike("ir.cake.glint", 8.800, 0.61),
        spike("ctrl.gate", 12.200, 0.83),
        spike("pt.chamber.ctx", 15.900, 0.41),
        spike("rtd.outlet.C", 19.400, 0.54),
        spike("ir.cake.glint", 21.200, 0.46),
    ]
    excerpt = independent_excerpt(34190, 84, 22000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Atom-Disk AD-11 in Slurry-Crown SC-8 is already at 84.0 C outlet while a "
                "NIR cake glint still reports 112 against a 95.0 C stick cap that the "
                "outlet RTD has not crossed. Outlet-first should ACCEPT the already-legal "
                "18500 rpm atomize; glint-first would hold a legal spin on lighting.",
            ),
            ("domain", "spray-dryer-tower"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Spin AD-11 when outlet RTD is <= 95.0 C; do not spend a NIR cake glint "
                "on a hold.",
            ),
            ("t0_us", 1756794621000190),
            ("gate_latency_us", 560),
            ("race_window_us", 240),
            ("race_window_rel_ms", [3.7, 3.94]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.outlet.C 84.0 C",
                                "ir.cake.glint 112 lighting",
                            ],
                        ),
                        (
                            "semantics",
                            "Outlet-first ACCEPTS the already-legal 84.0 C atomize. Glint-first "
                            "would REJECT a legal spin on a 112 C lighting.",
                        ),
                        (
                            "window_derivation",
                            "240 us = one outlet-RTD sample minus NIR-cake integration on this "
                            "tower-bus simulation.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 118 us vs combined jitter ~50 us (RTD 22 + NIR 28): 2.4x over "
                            "a 2.0x trust floor. Reversing order by < 118 us inside the 240 us "
                            "window would have invented a cake hold on an already-legal 84.0 C outlet.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "outlet RTD, 2 kHz, 22 us jitter",
                    "NIR cake camera, 200 Hz, 28 us jitter",
                    "chamber PT (context)",
                    "inlet air flow (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("stick_cap_C", 95.0),
                        ("observed_outlet_C", 84.0),
                        ("nir_cake_glint_C", 112.0),
                        ("proposed_rpm", 18500.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. AD-11 seeded; slurry at 84.0 C outlet under 95.0 stick cap.",
                    "2. NIR cake glint 112 from chamber lighting, not wall cake.",
                    "3. Chamber precursor at 0.700 ms.",
                    "4. Race window [3.700, 3.940] ms.",
                    "5. rtd.outlet.C 84.0 C at 3.740 ms (winner).",
                    "6. ir.cake.glint 112 at 3.858 ms (loser by 118 us).",
                    "7. Gate at 4.300 ms: ACCEPT 18500 rpm as proposed.",
                    "8. Spin executes; outlet remains 84.0 C < 95.0.",
                    "9. Disk emptied; next pass queued.",
                    "10. Delayed (survey_hold_s=280): 4.7 min PSD survey. Not a safety inflection.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "atomize_18500"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("rpm", 18500.0),
                        ("hold", False),
                        ("inlet_kPa", 22.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("outlet_C", 84.0),
                        ("stick_cap_C", 95.0),
                        ("nir_cake_glint_C", 112.0),
                        ("race_margin_us", 118),
                        ("combined_jitter_us", 50),
                        ("survey_hold_s", 280),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 18500 rpm because outlet RTD 84.0 C is under the 95.0 C "
                "stick cap; NIR 112 C is lighting, not cake.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Outlet RTD 84.0 C is under the 95.0 C stick cap. NIR cake 112 C is a "
                "chamber lighting glint, not wall load. ACCEPT the proposed 18500 rpm; do "
                "not invent a hold.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "outlet_C",
                            OrderedDict(
                                [
                                    ("cap", 95.0),
                                    ("observed", 84.0),
                                    ("nir_cake_glint_C", 112.0),
                                ]
                            ),
                        ),
                        (
                            "rpm",
                            OrderedDict(
                                [
                                    ("proposed", 18500.0),
                                    ("executed", 18500.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 118),
                                    ("combined_jitter_us", 50),
                                    ("ratio", 2.36),
                                ]
                            ),
                        ),
                    ]
                ),
            ),
        ]
    )
    executed = OrderedDict(
        [
            ("name", "atomize_18500"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("rpm", 18500.0),
                        ("hold", False),
                        ("inlet_kPa", 22.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "ACCEPT: proposed 18500 rpm executed unchanged. Outlet 84.0 C < 95.0; NIR glint unused.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT spun AD-11 at 84.0 C outlet. NIR 112 C was lighting, not cake. "
                "The proposal was already legal; reversing 118 us would have invented a hold.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("disk", "spin executed; outlet 84.0 C < 95.0"),
                        ("nir", "112 C glint unused as cake"),
                        ("chamber", "held 22.0 kPa through the pass"),
                        ("mission", "atomize committed"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "NIR 112 C is a legal lighting glint, not a high-outlet alarm; outlet-first discarded a false hold.",
                    "Delayed (4.7 min / survey_hold_s=280): particle-size survey. Not a safety inflection.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.outlet.C (3.740 ms, 84.0 C)"),
                        ("loser", "ir.cake.glint (3.858 ms, 112 lighting)"),
                        ("margin_us", 118),
                        (
                            "counterfactual_if_reversed",
                            "Glint-first by < 118 us inside the 240 us window would have held "
                            "the spin on a false high-outlet story. The proposal was already "
                            "under the 95.0 cap, so the correct gate is still ACCEPT.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 4300),
            (
                "reward_inflection_note",
                "Task and safety step up at the ACCEPT gate (4.300 ms, tick 4). Tick 6 is "
                "survey_hold_s=280.",
            ),
        ]
    )
    ras = raster_core(
        22,
        84,
        32,
        59,
        routing(
            "thalamic-relay.dryer-outlet",
            "spikenaut.policy.atom-accept",
            [
                ("relay.rtd.outlet", "policy.atom_go", 0.62),
                ("relay.ir.cake", "policy.glint_hold", 0.28),
                ("relay.pt.chamber", "policy.atom_go", 0.14),
            ],
            "adenosine",
            0.16,
            "pre_post_stdp; adenosine at outlet win (3.740 ms) opens 160 ms eligibility covering the 4.300 ms accept",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.24),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("atom_go", 42, 0.50, 297.6, 3),
                    pop("glint_hold", 42, 0.50, 19.8, 0),
                    pop("stick_veto", 20, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r34-190"),
            (
                "title",
                "Slurry-Crown SC-8 / Atom-Disk AD-11: outlet 84.0 C beats NIR cake glint; "
                "correct ACCEPT of an already-legal 18500 rpm (total +1.16)",
            ),
            ("state", state),
            ("spike_events", spikes),
            ("proposed_action", proposed),
            ("safety_decision", safety),
            ("executed_action", executed),
            ("future_outcome", future),
            (
                "reward_components",
                reward_block(
                    ticks,
                    "Correct ACCEPT. Outlet 84.0 C < 95.0; NIR glint is lighting, not cake. "
                    "total +1.16 = 0.44 + 0.34 + 0.18 + 0.12 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "spray-dryer-tower",
                    [
                        "accept",
                        "simulated-lighting",
                        "outlet-vs-nir",
                        "atomize",
                        "simulated",
                    ],
                    "Teaches that a NIR cake lighting glint can lose to a legal outlet RTD "
                    "inside a 240 us window; reversing 118 us would have invented a hold on an "
                    "already-legal spin.",
                    5,
                ),
            ),
        ]
    )


def tokenize(text: str) -> set[str]:
    return {tok for tok in re.split(r"[^a-z0-9]+", text.lower()) if tok}


def jaccard(a: str, b: str) -> float:
    sa, sb = tokenize(a), tokenize(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def check_refractory(events, min_ms=0.8):
    last = {}
    for ev in events:
        ch, t = ev["channel"], ev["t_rel_ms"]
        if ch in last and t - last[ch] < min_ms - 1e-12:
            return f"{ch} gap {t - last[ch]} ms"
        last[ch] = t
    return None


def check_race(rec):
    start, end = rec["state"]["race_window_rel_ms"]
    in_win = {}
    for ev in rec["spike_events"]:
        if start <= ev["t_rel_ms"] <= end:
            in_win.setdefault(ev["channel"], 0)
            in_win[ev["channel"]] += 1
    if len(in_win) < 2:
        return f"race window has {len(in_win)} channels: {in_win}"
    return None


def excerpt_vs_spikes(rec):
    spike_us = {int(round(ev["t_rel_ms"] * 1000.0)) for ev in rec["spike_events"]}
    ex_us = {item["t_us"] for item in rec["raster"]["excerpt"]}
    if not spike_us:
        return 0.0
    return len(spike_us & ex_us) / len(spike_us)


def walk_keys(obj, path=""):
    found = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}.{k}" if path else k
            if str(k).lower() in THOUGHT_KEYS or str(k).lower() in {
                "chain_of_thought",
                "hidden_reasoning",
            }:
                found.append(p)
            found.extend(walk_keys(v, p))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            found.extend(walk_keys(v, f"{path}[{i}]"))
    return found


def occupancy_check(records):
    issues = []
    my_domains = {r["state"]["domain"] for r in records}
    my_blob = json.dumps(records)
    for p in sorted(Path("/tmp").glob("ttf-r*/batch-r*.jsonl")):
        try:
            if p.resolve() == BATCH_PATH.resolve():
                continue
        except OSError:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            continue
        for line in text.splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            d = (rec.get("state") or {}).get("domain")
            if d in my_domains:
                issues.append(f"domain {d} collides {p}")
            title = rec.get("title") or ""
            for frag in THIS_PLANTS:
                if frag in title or frag in json.dumps(rec.get("state") or {}):
                    issues.append(f"plant {frag} collides {p}")
    for p in sorted(Path("/tmp").glob("ttf-r*/gen_r*.py")):
        if p.parent.name == "ttf-r40":
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            continue
        claimed = set(re.findall(r'\("domain", "([^"]+)"\)', text))
        hit = claimed & my_domains
        if hit:
            issues.append(f"domain {hit} collides gen {p}")
        for frag in THIS_PLANTS:
            if frag in text:
                issues.append(f"plant {frag} collides gen {p}")
    for frag in BANNED_PLANT_FRAGMENTS:
        if frag in my_blob:
            issues.append(f"banned plant fragment {frag}")
    return issues


def self_check(records):
    issues = []
    descs = [r["state"]["description"] for r in records]
    opens = [d.split(".")[0] for d in descs]
    if len(set(opens)) != 5:
        issues.append("opening sentences not unique")
    jmax = 0.0
    for i in range(5):
        for j in range(i + 1, 5):
            val = jaccard(descs[i], descs[j])
            jmax = max(jmax, val)
            if val >= 0.4:
                issues.append(f"Jaccard {records[i]['id']}/{records[j]['id']} = {val:.3f}")
    domains = [r["state"]["domain"] for r in records]
    if len(set(domains)) != 5:
        issues.append(f"domain collision {domains}")
    if set(domains) != THIS_DOMAINS:
        issues.append(f"domain set {set(domains)}")
    if set(domains) & BANNED_DOMAINS:
        issues.append(f"banned domains {set(domains) & BANNED_DOMAINS}")
    blob_all = "\n".join(json.dumps(r) for r in records)
    for frag in BANNED_PLANT_FRAGMENTS:
        if frag in blob_all:
            issues.append(f"restacked plant {frag}")
    for frag in THIS_PLANTS:
        if frag not in blob_all:
            issues.append(f"missing plant {frag}")
    issues.extend(occupancy_check(records))
    wrong = [
        r
        for r in records
        if r["safety_decision"].get("correctness") == "incorrect"
        or r["meta"].get("supervisor_error_type")
    ]
    if len(wrong) != 1 or wrong[0]["id"] != "ttf-r40-216":
        issues.append(f"wrong-gate set {[w['id'] for w in wrong]}")
    if any(r["state"]["sim_or_real"] == "real" for r in records):
        issues.append("sim_or_real=real")
    hil = [r["id"] for r in records if r["state"]["sim_or_real"] == "hil"]
    if hil != ["ttf-r40-218"]:
        issues.append(f"hil set {hil}")
    decisions = [r["safety_decision"]["decision"] for r in records]
    if decisions.count("ACCEPT") != 2 or decisions.count("MODIFY") != 1 or decisions.count("REJECT") != 2:
        issues.append(f"gate mix {decisions}")
    expected_ids = [f"ttf-r40-{n}" for n in range(216, 221)]
    if [r["id"] for r in records] != expected_ids:
        issues.append(f"ids {[r['id'] for r in records]}")
    for rec in records:
        blob = json.dumps(rec)
        if "training_ready" in blob:
            issues.append(f"{rec['id']} training_ready present")
        hidden = walk_keys(rec)
        if hidden:
            issues.append(f"{rec['id']} hidden keys {hidden}")
        err = check_refractory(rec["spike_events"])
        if err:
            issues.append(f"{rec['id']} refractory {err}")
        err = check_race(rec)
        if err:
            issues.append(f"{rec['id']} {err}")
        n = rec["raster"]["neurons"]
        rate = rec["raster"]["mean_rate_hz"]
        window_s = rec["raster"]["window_s"]
        expected = round(n * rate * window_s)
        if abs(rec["raster"]["spikes"] - expected) > 1:
            issues.append(f"{rec['id']} spike budget {rec['raster']['spikes']} vs {expected}")
        overlap = excerpt_vs_spikes(rec)
        if rec["id"] == "ttf-r40-217":
            if rec["raster"].get("excerpt_source") != "independent_lif":
                issues.append("217 missing independent_lif")
            if rec["future_outcome"]["reward_inflection_t_us"] > rec["raster"]["window_ms"] * 1000:
                issues.append("217 inflection outside window")
            if rec["reward_components"]["total"] >= 0:
                issues.append("217 partnered-neg total not negative")
        elif overlap >= 0.8:
            issues.append(f"{rec['id']} excerpt overlap {overlap:.2f}")
        inf = rec["future_outcome"]["reward_inflection_t_us"]
        tick_times = [t["t_us"] for t in rec["reward_components"]["ticks"]]
        if inf not in tick_times:
            issues.append(f"{rec['id']} inflection {inf} not a tick")
        if len(rec["reward_components"]["ticks"]) != 6:
            issues.append(f"{rec['id']} tick count")
        if not (8 <= len(rec["state"]["episode_steps"]) <= 15):
            issues.append(f"{rec['id']} episode_steps")
        if rec["gate_snn"]["decision"] != rec["safety_decision"]["decision"]:
            issues.append(f"{rec['id']} gate_snn decision mismatch")
        if rec["meta"]["round"] != 40:
            issues.append(f"{rec['id']} meta.round")
        ds = rec["future_outcome"].get("delayed_surprise_s")
        if ds is not None and rec["reward_components"]["ticks"][5]["t_us"] != round(ds * 1e6):
            issues.append(f"{rec['id']} tick6 vs delayed_surprise_s")
        if rec["meta"]["rights"]["intended_use"] != "research_only":
            issues.append(f"{rec['id']} rights")
        if rec["meta"]["rights"]["linear_issue"] != "RM-793":
            issues.append(f"{rec['id']} RM-793")
        heads = ["task_progress", "safety", "efficiency", "coherence", "exploration"]
        total = sum(rec["reward_components"][h] for h in heads)
        if abs(total - rec["reward_components"]["total"]) > 1e-6:
            issues.append(f"{rec['id']} total mismatch {total}")
        for h in heads:
            s = sum(t[h] for t in rec["reward_components"]["ticks"])
            if abs(s - rec["reward_components"][h]) > 1e-6:
                issues.append(f"{rec['id']} {h} tick sum {s} vs {rec['reward_components'][h]}")
        nspk = len(rec["spike_events"])
        if not (5 <= nspk <= 40):
            issues.append(f"{rec['id']} spike count {nspk}")
        times = [e["t_rel_ms"] for e in rec["spike_events"]]
        if times != sorted(times):
            issues.append(f"{rec['id']} spike order")
        exec_p = rec["executed_action"]["parameters"]
        prop_p = rec["proposed_action"]["parameters"]
        if rec["safety_decision"]["decision"] == "ACCEPT" and exec_p != prop_p:
            issues.append(f"{rec['id']} ACCEPT params differ")
        dw_s = rec["gate_snn"]["decision_window_ms"] / 1000.0
        for popu in rec["gate_snn"]["populations"]:
            if "mean_rate_hz" in popu:
                exp = round(popu["neurons"] * popu["mean_rate_hz"] * dw_s)
                if abs(popu["spikes"] - exp) > 1:
                    issues.append(
                        f"{rec['id']} gate_snn {popu['name']} spikes {popu['spikes']} vs {exp}"
                    )
        if not (8 <= len(rec["raster"]["excerpt"]) <= 16):
            issues.append(f"{rec['id']} excerpt n={len(rec['raster']['excerpt'])}")
        if rec["state"]["sim_or_real"] not in {"designed", "simulated", "hil"}:
            issues.append(f"{rec['id']} provenance")
        table_tos = {row["to"] for row in rec["raster"]["routing"]["table"]}
        if rec["id"] == "ttf-r40-216":
            if "policy.go_accept" in table_tos:
                issues.append("216 routing has go_accept")
            if "policy.hold_reject" not in table_tos:
                issues.append("216 missing hold_reject routing")
            if rec["proposed_action"]["evidence"]["pv_bar"] >= rec["proposed_action"]["evidence"]["trip_bar"]:
                issues.append("216 live PV not under trip")
        win_ms = rec["raster"]["window_ms"]
        if not (20 <= win_ms <= 50):
            issues.append(f"{rec['id']} window_ms {win_ms}")
        for item in rec["raster"]["excerpt"]:
            if not (0 <= item["t_us"] <= win_ms * 1000):
                issues.append(f"{rec['id']} excerpt t_us {item['t_us']}")
            if not (0 <= item["neuron_id"] < rec["raster"]["neurons"]):
                issues.append(f"{rec['id']} neuron_id {item['neuron_id']}")
    notes_hits = [ln for ln in NOTES.splitlines() if ln.strip().lower().startswith("novel coverage")]
    if notes_hits != ["Novel coverage: 22.0%"]:
        issues.append(f"novel coverage lines {notes_hits}")
    return issues, jmax


NOTES = """# Thalamic Trajectory Factory — NOTES-r34

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- IDs: `ttf-r34-186` … `ttf-r34-190`
- Domains this batch: `coke-oven-battery`, `chlor-alkali-membrane`, `air-separation-coldbox`, `eaf-arc-furnace`, `spray-dryer-tower`

These five domain slugs sit outside the prompt 8-pool and outside staged r13–r28 occupancy (including r26 lime/ferry/cyclotron/die-cast/RO, r28 kiln/lay/potline/penstock/pan, r24 electrolyzer/HVDC/autoclave/plough/cyclotron, r25 CAES/tire/cyclotron/cable/decanter). All five plants are invented. Do not restack r12–r28 plants (Marrow-Dock, Vesper-Lattice, Brine-Well, Saddle-Arc, Ashlar-Gait, Nacre-Well, Quern-Forge, Tinder-Box, Whimbrel-Stack, Cinder-Loft, Oolite-Span, Fathom-Lock, Loess-Stride, Swage-Holt, Slag-Siding, Kiln-Spur, Suture-Isle, Oxbow-Switch, Pitch-Kettle, Shale-Quay, Polder-Rye, Flint-Mask, Gyre-Tokamak, Quarry-Bowl, Amber-Arm, Wort-Cairn, Firn-Span, Sleet-Row, Oxbow-Pound, Tuyere-Holt, Lye-Rake, Rime-Haul, Glycol-Loop, Burden-Pike, Glimmer-Forge, Feldspar-Arc, Basalt-Rook, Fetch-Sound, Silica-Well, Clothoid-Bowl, Frost-Cist, Bracken-Wire, Cullet-Reach, Abyss-Joint, Gnomon-Well, Scree-Hitch, Flux-Kettle, Mire-Cask, Slack-Firth, Chaff-Rise, Halite-Keel, Caldera-Mold, Drupe-Press, Osmia-Reach, Dee-Keeper, Gull-Pontoon, Hood-Pike, Marl-Knap, Bight-Lay, Cryolite-Hall, Hood-Ring, Marl-Rake, Massecuite-Kettle, Penstock-Gate, Plow-Sled, Strike-Pan, Surge-Adit).

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
| ttf-r34-186 | coke-oven-battery | MODIFY | correct | designed | **−0.46** | process-correct travel clamp; wall-tie snap inside 42 ms raster; independent LIF |
| ttf-r34-187 | chlor-alkali-membrane | REJECT | **incorrect (wrong-reject)** | designed | −0.58 | cell 3.12 kA < 3.80 cap; supervisor treats header 4.06 kA as cell excursion |
| ttf-r34-188 | air-separation-coldbox | REJECT | correct | hil | +0.78 | O2 98.2 pct beats N2-tap 99.6; hold, do not draw |
| ttf-r34-189 | eaf-arc-furnace | MODIFY | correct | designed | +0.92 | roof 68 kPa vs staff false-draft; clamp electrode 18.0 → 11.0 MW |
| ttf-r34-190 | spray-dryer-tower | ACCEPT | correct | simulated | +1.16 | outlet 84.0 C vs NIR cake glint 112; proposed 18500 rpm already legal |

Gate mix: 1 ACCEPT, 2 MODIFY, 1 correct REJECT, 1 incorrect REJECT (wrong-reject). Provenance: designed×3, simulated×1, hil×1 (Argon-Cist AC-2 coldbox mockup). Intra-batch Jaccard on `state.description` 0.169 (< 0.4).

## Wrong-reject

**ttf-r34-187** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-reject`). Alternate vs odd rounds: r12/r14/r16/r18/r20/r22/r24/r26/r28/r30/r32/r34 host wrong-reject; r13/r15/r17/r19/r21/r23/r25/r27/r29/r31/r33 host wrong-modify. Do not emit a wrong-ACCEPT.

Soda-Weir SW-4 / Membrane-Bay MB-9 reads cell-bus `3.12 kA` against a **3.80 kA** cell cap. Rectifier-header residual is **4.06 kA** on a different bus whose cap is **4.40 kA**. Sidecar arithmetic `3.12 < 3.80` is true. A weak supervisor treats “the current loop” as one bus, REJECTs the 1.80 kA/m² ramp, and holds cell. Convictable without chlor-alkali physics: `evidence.cell_kA < evidence.cell_cap_kA`, `cell_bus_id == cell`, `header_bus_id == header`, `executed_action` sets `density_kA_m2=0` without a cell over-cap, `raster.routing.table` sends `relay.bus.header` → `policy.cell_hold` (weight 0.73) with no positive weight to `policy.cell_go`, and `gate_snn` has `cell_hold` above threshold while `cell_go` is not. Recovery: ACCEPT the 1.80 kA/m² ramp; leave header 4.06 kA to its own 4.40 kA cap. Cost: missed 22 min brine-quality window (`missed_window_s=1320`).

## Partnered-negative in-window (186)

**ttf-r34-186** is the partnered negative: process-correct MODIFY (wall-face held 1294 C < 1320 cap) while the world still charges. Safety −0.58 prices the 28 mm wall-tie snap at **22.400 ms**; `task_progress` stays +0.32 because the clamp completed. Inflection `t_us=22400` is tick 5 and is **inside** the 42 ms raster (`22400 ≤ 42000`). Named un-netted loss: 15 min flue isolate (`abort_s=900`). Not folded into process heads.

Independent LIF (the one labeled sidecar sim): `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 34186, stim `[21000, 25000]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.tie` 21–25 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks). Tick 6 is bound to a published sidecar (`abort_s`, `missed_window_s`, `hearth_reseq_s`, `survey_hold_s`) and is strictly after the raster window. Inflection `t_us` is an actual tick.

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
| 186 | 6 | +0.32 | −0.58 | −0.16 | +0.02 | −0.06 | −0.46 | 5 (22400) |
| 187 | 6 | −0.20 | −0.10 | −0.22 | −0.12 | +0.06 | −0.58 | 4 (4920) |
| 188 | 6 | +0.10 | +0.40 | +0.12 | +0.10 | +0.06 | +0.78 | 4 (6860) |
| 189 | 6 | +0.34 | +0.30 | +0.14 | +0.10 | +0.04 | +0.92 | 4 (7280) |
| 190 | 6 | +0.44 | +0.34 | +0.18 | +0.12 | +0.08 | +1.16 | 4 (4300) |

Tick-6 sidecar bind: 186 `abort_s=900`, 187 `missed_window_s=1320`, 188 `abort_s=540`, 189 `hearth_reseq_s=420`, 190 `survey_hold_s=280`.

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
| 186 | coke-oven-battery | 72 | 28 | 42 | 85 | 1955 | 0.001955 |
| 187 | chlor-alkali-membrane | 88 | 36 | 24 | 76 | 1748 | 0.001748 |
| 188 | air-separation-coldbox | 104 | 22 | 40 | 92 | 2116 | 0.002116 |
| 189 | eaf-arc-furnace | 60 | 44 | 30 | 79 | 1817 | 0.001817 |
| 190 | spray-dryer-tower | 84 | 32 | 22 | 59 | 1357 | 0.001357 |

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator (NA / ACh / DA / 5-HT / adenosine), `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms. Non-186 excerpts are kernelized and independent of `spike_events` times (overlap < 0.8).

## Local checks (staging, not raw)

See generator stdout: `check_jsonl` FactoryStaging, `validate_run.check_line`, `dumps_exact_json`, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`, tick sums, refractory, Jaccard.

Never `training_ready`. Never `sim_or_real=real`. Never wrote `outputs/raw/`.

## Residual weaknesses (honest)

1. Only **one** labeled independent LIF (186). The other four excerpts are independent of `spike_events` times but are not declared population sims.
2. Wrong-ACCEPT still absent (guard).
3. Tick-6 sidecar bind is a densification of r14/r16, not a new class.
4. Five domain slugs leave the prompt's 8-item pool; a later round that must stay inside the pool will have to rotate sit-outs instead.
5. 187 wrong-reject is sidecar-convictable (routing `to` / bus IDs) but still the same error *class* as r16-097 / r28-157 (wrong-stage / wrong-drum mixup).
6. 190 ACCEPT is an already-legal proposal confirmed by race order; a later round could pair an ACCEPT with a world charge that does not go negative.

## Next densification target

Labeled LIF on a second record, or an ISI histogram sidecar. If a later round returns to the 8-item pool, sit out the r12 five again and pick a wrong-MODIFY that is neither J2-axis nor a stage/drum/bus mixup (wrong-phase of a cyclic process). Wrong-ACCEPT remains structurally absent until a prompt amendment.

Novel coverage: 19.0%
"""


def run_pipelines(records):
    sys.path.insert(0, str(PIPELINES))
    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import raster_status
    from exact_json import dumps_exact_json
    from round_txn import validate_novel_coverage
    from validate_run import check_line
    from verify_execution import verify_batch_for_frontier

    report = []
    errors, warnings, kinds, nrec = check_jsonl(
        BATCH_PATH, "batch-r34.jsonl", staging=FactoryStaging(enabled=True)
    )
    report.append(("check_jsonl FactoryStaging", errors, warnings, kinds, nrec))
    line_errs = []
    for i, rec in enumerate(records, 1):
        errs, kind = check_line(rec, f"batch-r34.jsonl:{i}", factory_staging=True)
        if errs:
            line_errs.append((i, kind, errs))
        try:
            dumps_exact_json(rec, ensure_ascii=False, sort_keys=False)
        except Exception as exc:
            line_errs.append((i, "exact_json", [str(exc)]))
    report.append(("check_line+exact_json", line_errs, None, None, None))
    raster_fail = []
    for rec in records:
        st = raster_status(rec, require_raster=True, require_routing_table=True)
        if not st.get("raster_valid") or not st.get("gate_snn_valid"):
            raster_fail.append((rec["id"], st))
    report.append(("raster_status", raster_fail, None, None, None))
    counts, findings, blocked = verify_batch_for_frontier(BATCH_PATH, strict=True)
    report.append(("verify_batch_for_frontier", counts, findings, blocked, None))
    cov = validate_novel_coverage(
        NOTES_PATH,
        Path("thalamic-trajectory-factory"),
        notes_text=NOTES_PATH.read_text(),
        required=True,
    )
    report.append(("validate_novel_coverage", cov, None, None, None))
    probe = subprocess.run(
        [sys.executable, str(PIPELINES / "spike_probe.py"), "--strict", str(BATCH_PATH)],
        cwd=str(REPO),
        capture_output=True,
        text=True,
    )
    report.append(("spike_probe", probe.returncode, probe.stdout[-2000:], probe.stderr[-2000:], None))
    return report


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    records = [record_186(), record_187(), record_188(), record_189(), record_190()]
    issues, jmax = self_check(records)
    lines = [
        json.dumps(rec, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        for rec in records
    ]
    BATCH_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    NOTES_PATH.write_text(NOTES, encoding="utf-8")
    print(f"wrote {BATCH_PATH} lines={len(lines)} jmax={jmax:.3f}")
    print(f"wrote {NOTES_PATH}")
    if issues:
        print("SELF_CHECK_ISSUES:")
        for item in issues:
            print(" -", item)
        return 1
    print("SELF_CHECK_OK")
    report = run_pipelines(records)
    failed = False
    for item in report:
        name = item[0]
        print(f"PIPELINE {name}: {item[1:]}")
        if name == "check_jsonl FactoryStaging":
            errors, warnings, kinds, nrec = item[1], item[2], item[3], item[4]
            print(f"  kinds={kinds} n={nrec} errors={len(errors)} warnings={len(warnings)}")
            for e in errors:
                print("  ERR", e)
                failed = True
        elif name == "check_line+exact_json":
            if item[1]:
                failed = True
        elif name == "raster_status":
            if item[1]:
                failed = True
        elif name == "verify_batch_for_frontier":
            if item[3]:
                failed = True
        elif name == "validate_novel_coverage":
            if item[1]:
                failed = True
        elif name == "spike_probe":
            if item[1] != 0:
                failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
