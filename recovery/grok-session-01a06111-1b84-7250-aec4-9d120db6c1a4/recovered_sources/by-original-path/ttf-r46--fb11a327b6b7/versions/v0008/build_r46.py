#!/usr/bin/env python3
"""Clone gen_r34 into gen_r46 with new plants/domains. Never writes outputs/raw/."""
from __future__ import annotations

from pathlib import Path

SRC = Path("/tmp/ttf-r34/gen_r34.py")
DST = Path("/tmp/ttf-r46/gen_r46.py")

EXTRA_DOMAINS = """
    "transformer-oltc",
    "electrostatic-precipitator",
    "wind-tunnel-balance",
    "composite-autoclave",
    "electron-linac",
    "helium-liquefier",
    "escalator-comb",
    "jet-fuel-hydrant",
    "czochralski-puller",
    "sawmill-carriage",
    "perlite-expander",
    "kaolin-filter-press",
    "malt-kiln-turn",
    "hydro-wicket-gate",
    "wind-turbine-pitch",
    "escalator-comb-plate",
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
    "trona-calciner",
    "kraft-recovery-boiler",
    "var-ingot-melt",
    "msf-flash-desal",
    "hot-strip-mill",
    "spiral-freezer",
    "offset-web-press",
    "bascule-bridge",
    "vacuum-induction-melt",
    "airport-jetbridge",
    "coke-oven-battery",
    "chlor-alkali-membrane",
    "air-separation-coldbox",
    "eaf-arc-furnace",
    "spray-dryer-tower",
    "geothermal-binary-ORC",
    "ammonia-converter",
    "foundry-core-shooter",
    "photovoltaic-laminator",
    "urea-prill-tower",
"""

EXTRA_PLANTS = """
    "Gable-Retort",
    "Flue-Bank",
    "Soda-Weir",
    "Membrane-Bay",
    "Argon-Cist",
    "Draw-Valve",
    "Hearth-Knap",
    "Roof-Ring",
    "Slurry-Crown",
    "Atom-Disk",
    "Haber-Knoll",
    "Loam-Hurst",
    "Floe-Helix",
    "Nahcolite-Kettle",
    "Ingot-Cairn",
    "Muscovado-Well",
    "Foehn-Nacelle",
    "Bloom-Weir",
    "Clinker-Spire",
    "Whey-Rill",
    "Skim-Loom",
    "Comb-Sill",
    "Leaf-Pike",
    "Boron-Veld",
    "Pumice-Loft",
    "Cachet-Croft",
    "Boule-Knap",
    "Green-Bladder",
    "Veer-Nacelle",
    "Spume-Rack",
    "Treacle-Kettle",
    "Gorse-Weir",
    "Kerf-Spur",
    "Kerosene-Wharf",
    "Ink-Noll",
    "Lamina-Kame",
    "Preform-Wold",
    "Prill-Flue",
    "Smelt-Spur",
    "Looper-Holt",
    "Crucible-Wold",
    "Tile-Warden",
    "Wych-Bore",
    "Gneiss-Tap",
    "China-Clay",
    "Expand-Kiln",
    "Pilot-Stem",
    "Turner-Tine",
    "Malt-Loft",
    "Klystron-Fen",
    "Soot-Kettle",
    "Gulley-Tunnel",
    "Sprue-Nook",
    "Dee-Keeper",
    "Hood-Pike",
    "Hood-Ring",
    "Penstock-Gate",
    "Plow-Sled",
    "Strike-Pan",
    "Felt-Reach",
    "Oxbow-Pound",
    "Sedge-Cell",
    "Retort-Fen",
    "Halite-Keel",
    "Caldera-Mold",
    "Drupe-Press",
    "Lay-Sound",
    "Isotope-Pad",
    "Osmia-Reach",
    "Gull-Pontoon",
    "Marl-Knap",
    "Marl-Rake",
    "Bight-Lay",
    "Cryolite-Hall",
    "Massecuite-Kettle",
    "Surge-Adit",
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
    "Fjord-Convert",
    "Skerries-Trench",
    "Iodine-Well",
    "Wort-Cairn",
    "Firn-Span",
    "Sleet-Row",
    "Tuyere-Holt",
    "Bracken-Wire",
    "Cullet-Reach",
    "Rime-Causeway",
    "Abyss-Joint",
    "Gnomon-Well",
    "Scree-Hitch",
    "Flux-Kettle",
    "Mire-Cask",
    "Slack-Firth",
    "Chaff-Rise",
    "Apside-Yard",
    "Sump-Drift",
    "Frost-Cist",
    "Clothoid-Bowl",
    "Amber-Arm",
    "Lye-Rake",
    "Rime-Haul",
    "Glycol-Loop",
    "Burden-Pike",
    "Oolite-Span",
    "Fathom-Lock",
    "Loess-Stride",
    "Swage-Holt",
    "Slag-Siding",
    "Solder-Kite",
    "Bog-Drum",
    "Ebb-Latch",
    "Plunger-P4",
    "Kelp-Jetty",
    "Lyo-Deck",
    "Target-Cart",
    "Rime-Vault",
    "Sinter-Gown",
    "Kettle-Stack",
    "Barrow-Mezz",
    "Grit-Sump",
    "Firth-Spur",
    "Spindrift-Rack",
"""


def apply_pairs(text: str, pairs: list[tuple[str, str]], label: str = "") -> str:
    missing = []
    for old, new in pairs:
        if old == new:
            continue
        if old not in text:
            if new in text:
                continue
            missing.append(old)
            continue
        text = text.replace(old, new)
    if missing:
        raise SystemExit(f"{label} missing {len(missing)} fragments:\n" + "\n".join(repr(m) for m in missing))
    return text


def transform_head(head: str) -> str:
    head = apply_pairs(
        head,
        [
            (
                '"""Emit TTF r34 JSONL (ttf-r34-186..190) into /tmp/ttf-r34/. Never writes outputs/raw/."""',
                '"""Emit TTF r46 JSONL (ttf-r46-246..250) into /tmp/ttf-r46/. Never writes outputs/raw/."""',
            ),
            ('OUT_DIR = Path("/tmp/ttf-r34")', 'OUT_DIR = Path("/tmp/ttf-r46")'),
            ('BATCH_PATH = OUT_DIR / "batch-r34.jsonl"', 'BATCH_PATH = OUT_DIR / "batch-r46.jsonl"'),
            ('NOTES_PATH = OUT_DIR / "NOTES-r34.md"', 'NOTES_PATH = OUT_DIR / "NOTES-r46.md"'),
            ('("generated_at", "2026-09-02T18:45:00Z")', '("generated_at", "2026-09-02T19:50:00Z")'),
            ('    "tunnel-boring",\n}', '    "tunnel-boring",' + EXTRA_DOMAINS + "}"),
            ('    "Oxbow-Pound",\n)', EXTRA_PLANTS.rstrip() + "\n)"),
            ("def lif_186_excerpt():", "def lif_246_excerpt():"),
            ("    seed = 34186", "    seed = 46246"),
            ('            ("seed", 34186),', '            ("seed", 46246),'),
            (
                '                "Neurons 0-13 carry +0.64 pusher-clamp bias; stim 21-25 ms is the wall-tie snap.",',
                '                "Neurons 0-13 carry +0.64 feed-clamp bias; stim 21-25 ms is the tube-skin split.",',
            ),
            ('            ("round", 34),', '            ("round", 46),'),
            ('channels = ["lif.clamp" if t < 21000 else "lif.tie" for t, _ in picked]',
             'channels = ["lif.clamp" if t < 21000 else "lif.split" for t, _ in picked]'),
        ],
        "head",
    )
    return head


REC246_PAIRS = [
    ("def record_186():", "def record_246():"),
    ("excerpt, extra = lif_186_excerpt()", "excerpt, extra = lif_246_excerpt()"),
    (
        '"Flue-Bank FB-7 is already pushing Gable-Retort GR-4 at 18.4 mm/h coke travel "',
        '"Coil-Pass CP-4 is already feeding Pyro-Ness PN-9 at 18.4 t/h naphtha "',
    ),
    (
        '"while the crown-arch thermocouple sits at 1380 C against a 1320 C wall-face "',
        '"while the coil-outlet thermocouple sits at 878 C against a 860 C tube-metal "',
    ),
    (
        '"cap. An arch-first latch clamps the pusher; a travel-first story would keep "',
        '"cap. A COT-first latch clamps the naphtha valve; a feed-first story would keep "',
    ),
    (
        '"the 18.4 mm/h cruise. Stored hoop in the heating wall is not yet an observable "',
        '"the 18.4 t/h cruise. Stored hoop in the radiant coil is not yet an observable "',
    ),
    ('("domain", "coke-oven-battery")', '("domain", "ethylene-steam-cracker")'),
    (
        '"Finish the GR-4 coking pass, keep wall-face skin <= 1320 C, and leave the "',
        '"Finish the PN-9 cracking pass, keep tube-metal skin <= 860 C, and leave the "',
    ),
    ('"heating-wall tie unmarked.",', '"radiant-coil skin unmarked.",'),
    ("1756794621000186", "1756794621000246"),
    (
        '"500 us = one 1 kHz crown-arch sample minus pusher-encoder group "',
        '"500 us = one 1 kHz coil-outlet sample minus naphtha-encoder group "',
    ),
    ('"delay on this coke-battery bus.",', '"delay on this cracker-bus.",'),
    ('"tc.crown.arch 1380 C pulse"', '"tc.cot.C 878 C pulse"'),
    ('"enc.travel.mm_h 18.4 mm/h cruise"', '"enc.feed.tph 18.4 t/h cruise"'),
    (
        '"Arch-first latches pusher 18.4 -> 11.2 mm/h; travel-first keeps "',
        '"COT-first latches naphtha 18.4 -> 12.6 t/h; feed-first keeps "',
    ),
    ('"cruise on a still-cooling wall model.",', '"cruise on a still-cooling coil model.",'),
    (
        '"Margin 208 us vs combined jitter ~66 us (arch 30 + travel 36): 3.2x over "',
        '"Margin 208 us vs combined jitter ~66 us (COT 30 + feed 36): 3.2x over "',
    ),
    (
        '"would have kept 18.4 mm/h cruise; predicted next-sample 1348 C > 1320 cap.",',
        '"would have kept 18.4 t/h cruise; predicted next-sample 872 C > 860 cap.",',
    ),
    ('"crown-arch thermocouple, 1 kHz, 30 us timestamp jitter"', '"coil-outlet thermocouple, 1 kHz, 30 us timestamp jitter"'),
    ('"pusher-travel encoder, 500 Hz, 36 us jitter"', '"naphtha-feed encoder, 500 Hz, 36 us jitter"'),
    ('"heating-wall AE puck (context until the tie snap)"', '"radiant-coil AE puck (context until the tube-skin split)"'),
    ('"flue-draft PT (context)"', '"steam-draft PT (context)"'),
    ('("wall_face_cap_C", 1320.0)', '("tube_metal_cap_C", 860.0)'),
    ('("observed_arch_C", 1380.0)', '("observed_cot_C", 878.0)'),
    ('("proposed_travel_mm_h", 18.4)', '("proposed_feed_tph", 18.4)'),
    ('("flue_draft_kPa", 1.6)', '("steam_draft_kPa", 1.6)'),
    (
        '"1. Flue-Bank FB-7 indexed onto GR-4; heating wall armed at 18.4 mm/h.",',
        '"1. Coil-Pass CP-4 indexed onto PN-9; radiant coil armed at 18.4 t/h.",',
    ),
    (
        '"2. Cruise 18.4 mm/h; crown-arch 1380 C against 1320 C wall-face cap.",',
        '"2. Cruise 18.4 t/h; coil-outlet 878 C against 860 C tube-metal cap.",',
    ),
    (
        '"3. Pusher precursor at 1.180 ms; arch warm-start 1380 C.",',
        '"3. Feed precursor at 1.180 ms; COT warm-start 878 C.",',
    ),
    (
        '"4. Race window [6.150, 6.650] ms opens on the coke-battery bus.",',
        '"4. Race window [6.150, 6.650] ms opens on the cracker-bus.",',
    ),
    ('"5. tc.crown.arch 1380 C at 6.240 ms (winner).",', '"5. tc.cot.C 878 C at 6.240 ms (winner).",'),
    ('"6. enc.travel.mm_h 18.4 mm/h at 6.448 ms (loser by 208 us).",', '"6. enc.feed.tph 18.4 t/h at 6.448 ms (loser by 208 us).",'),
    (
        '"7. Gate at 7.120 ms (winner + 880 us): MODIFY clamp 18.4 -> 11.2 mm/h.",',
        '"7. Gate at 7.120 ms (winner + 880 us): MODIFY clamp 18.4 -> 12.6 t/h.",',
    ),
    (
        '"8. Clamp executes; next-sample arch 1294 C < 1320 cap.",',
        '"8. Clamp executes; next-sample COT 848 C < 860 cap.",',
    ),
    (
        '"9. At 22.400 ms stored hoop still snaps a 28 mm wall tie; AE burst.",',
        '"9. At 22.400 ms stored hoop still splits a 28 mm tube skin; AE burst.",',
    ),
    (
        '"10. Flue isolate 15 min (abort_s=900); named un-netted loss, not folded into process heads.",',
        '"10. Coil isolate 15 min (abort_s=900); named un-netted loss, not folded into process heads.",',
    ),
    ('("name", "cruise_coke_travel")', '("name", "cruise_naphtha_feed")'),
    ('("travel_mm_h", 18.4)', '("feed_tph", 18.4)'),
    ('("flue_draft_kPa", 1.6)', '("steam_draft_kPa", 1.6)'),
    ('("charge_t", 18.0)', '("coil_pass", 18.0)'),
    ('("arch_C", 1380.0)', '("cot_C", 878.0)'),
    ('("wall_face_cap_C", 1320.0)', '("tube_metal_cap_C", 860.0)'),
    ('("predicted_unclamped_next_C", 1348.0)', '("predicted_unclamped_next_C", 872.0)'),
    ('("travel_mm_h", 18.4)', '("feed_tph", 18.4)'),
    (
        '"Planner proposes 18.4 mm/h cruise: 1380 C looks like a flue-draft spike, not "',
        '"Planner proposes 18.4 t/h cruise: 878 C looks like a steam-draft spike, not "',
    ),
    (
        '"wall contact, and GR-4 volume is treated as still open.",',
        '"tube contact, and PN-9 volume is treated as still open.",',
    ),
    (
        '"Crown-arch 1380 C won by 208 us, so the heating wall is loading heat, not "',
        '"Coil-outlet 878 C won by 208 us, so the radiant coil is loading heat, not "',
    ),
    (
        '"still cooling. Holding 18.4 mm/h predicts next-sample 1348 C > 1320 cap. "',
        '"still cooling. Holding 18.4 t/h predicts next-sample 872 C > 860 cap. "',
    ),
    (
        '"MODIFY: pusher 18.4 -> 11.2 mm/h. Observed after clamp 1294 C < 1320. A full "',
        '"MODIFY: naphtha 18.4 -> 12.6 t/h. Observed after clamp 848 C < 860. A full "',
    ),
    (
        '"REJECT is not indicated: a sound coking pass accepts 11.2 mm/h.",',
        '"REJECT is not indicated: a sound cracking pass accepts 12.6 t/h.",',
    ),
    ('("wall_face_C"', '("tube_metal_C"'),
    ('("cap", 1320.0)', '("cap", 860.0)'),
    ('("observed", 1380.0)', '("observed", 878.0)'),
    ('("predicted_unclamped_next", 1348.0)', '("predicted_unclamped_next", 872.0)'),
    ('("clamped_travel_mm_h", 11.2)', '("clamped_feed_tph", 12.6)'),
    ('("observed_after_clamp", 1294.0)', '("observed_after_clamp", 848.0)'),
    ('("travel_mm_h"', '("feed_tph"'),
    ('("proposed", 18.4)', '("proposed", 18.4)'),
    ('("clamped", 11.2)', '("clamped", 12.6)'),
    ('("name", "clamped_coke_travel")', '("name", "clamped_naphtha_feed")'),
    ('("travel_mm_h", 11.2)', '("feed_tph", 12.6)'),
    (
        '"MODIFY: pusher 18.4 -> 11.2 mm/h. Process-correct vs the 1320 C wall-face "',
        '"MODIFY: naphtha 18.4 -> 12.6 t/h. Process-correct vs the 860 C tube-metal "',
    ),
    ('"cap. Wall-tie snap still occurs at 22.400 ms.",', '"cap. Tube-skin split still occurs at 22.400 ms.",'),
    (
        '"Process-correct MODIFY held wall-face skin at 1294 C. At 22.400 ms stored "',
        '"Process-correct MODIFY held tube-metal skin at 848 C. At 22.400 ms stored "',
    ),
    (
        '"hoop in the heating wall still snapped a 28 mm tie. Clamp reduced dump energy; "',
        '"hoop in the radiant coil still split a 28 mm skin. Clamp reduced dump energy; "',
    ),
    ('("pusher", "clamp executed; peak 1294 C < 1320")', '("naphtha", "clamp executed; peak 848 C < 860")'),
    ('("wall_tie", "28 mm snap at 22.400 ms")', '("tube_skin", "28 mm split at 22.400 ms")'),
    ('("repair", "15 min flue isolate (abort_s=900)")', '("repair", "15 min coil isolate (abort_s=900)")'),
    ('("mission", "GR-4 coking pass incomplete this circuit")', '("mission", "PN-9 cracking pass incomplete this circuit")'),
    (
        '"Neither crown-arch nor travel predicted the hoop charge; ae.wall.tie is a new channel at 22.400 ms, 15.280 ms after the gate, still inside the 42 ms raster.",',
        '"Neither coil-outlet nor feed predicted the hoop charge; ae.tube.split is a new channel at 22.400 ms, 15.280 ms after the gate, still inside the 42 ms raster.",',
    ),
    (
        '"Delayed (abort_s=900): 15 min flue isolate. Named un-netted loss, not folded into task_progress.",',
        '"Delayed (abort_s=900): 15 min coil isolate. Named un-netted loss, not folded into task_progress.",',
    ),
    (
        '"15 min flue isolate after a 28 mm heating-wall tie snap. Safety head -0.58 "',
        '"15 min coil isolate after a 28 mm radiant-coil skin split. Safety head -0.58 "',
    ),
    (
        '"prices the split; task_progress stays +0.32 because the travel clamp completed "',
        '"prices the split; task_progress stays +0.32 because the feed clamp completed "',
    ),
    (
        '"under the 1320 C cap. World loss is named here, not subtracted from process heads.",',
        '"under the 860 C cap. World loss is named here, not subtracted from process heads.",',
    ),
    ('("winner", "tc.crown.arch (6.240 ms, 1380 C)")', '("winner", "tc.cot.C (6.240 ms, 878 C)")'),
    ('("loser", "enc.travel.mm_h (6.448 ms, 18.4 mm/h)")', '("loser", "enc.feed.tph (6.448 ms, 18.4 t/h)")'),
    (
        '"Travel-first by < 208 us inside the 500 us window would have kept "',
        '"Feed-first by < 208 us inside the 500 us window would have kept "',
    ),
    (
        '"18.4 mm/h cruise; predicted next-sample 1348 C would have exceeded "',
        '"18.4 t/h cruise; predicted next-sample 872 C would have exceeded "',
    ),
    (
        '"the 1320 cap even without the hoop charge. The MODIFY is still the "',
        '"the 860 cap even without the hoop charge. The MODIFY is still the "',
    ),
    (
        '"Safety collapses at the 22.400 ms wall-tie snap (tick t_us=22400), inside "',
        '"Safety collapses at the 22.400 ms tube-skin split (tick t_us=22400), inside "',
    ),
    ('spike("enc.pusher.ctx", 1.180, 0.42)', 'spike("enc.feed.ctx", 1.180, 0.42)'),
    ('spike("tc.crown.arch", 2.480, 0.61)', 'spike("tc.cot.C", 2.480, 0.61)'),
    ('spike("enc.travel.mm_h", 3.760, 0.50)', 'spike("enc.feed.tph", 3.760, 0.50)'),
    ('spike("tc.crown.arch", 6.240, 1.31)', 'spike("tc.cot.C", 6.240, 1.31)'),
    ('spike("enc.travel.mm_h", 6.448, 1.14)', 'spike("enc.feed.tph", 6.448, 1.14)'),
    ('spike("tc.crown.arch", 8.520, 0.80)', 'spike("tc.cot.C", 8.520, 0.80)'),
    ('spike("enc.travel.mm_h", 11.400, 0.62)', 'spike("enc.feed.tph", 11.400, 0.62)'),
    ('spike("ae.wall.tie", 22.400, 1.46)', 'spike("ae.tube.split", 22.400, 1.46)'),
    ('spike("ae.wall.tie", 24.180, 0.91)', 'spike("ae.tube.split", 24.180, 0.91)'),
    ('spike("enc.pusher.ctx", 31.200, 0.41)', 'spike("enc.feed.ctx", 31.200, 0.41)'),
    ('spike("tc.crown.arch", 38.100, 0.53)', 'spike("tc.cot.C", 38.100, 0.53)'),
    ('"thalamic-relay.coke-arch"', '"thalamic-relay.cracker-cot"'),
    ('"spikenaut.policy.pusher-clamp"', '"spikenaut.policy.feed-clamp"'),
    ('("relay.tc.arch", "policy.travel_clamp", 0.66)', '("relay.tc.cot", "policy.feed_clamp", 0.66)'),
    ('("relay.enc.travel", "policy.travel_hold", 0.30)', '("relay.enc.feed", "policy.feed_hold", 0.30)'),
    ('("relay.ae.tie", "policy.travel_clamp", -0.45)', '("relay.ae.split", "policy.feed_clamp", -0.45)'),
    (
        '"surprise-gated pre_post_stdp; NA at arch win (6.240 ms) opens a 50 ms "',
        '"surprise-gated pre_post_stdp; NA at COT win (6.240 ms) opens a 50 ms "',
    ),
    ('"eligibility trace that still covers the 22.400 ms wall-tie snap"',
     '"eligibility trace that still covers the 22.400 ms tube-skin split"'),
    ('pop("travel_clamp", 36, 0.50, 278.0, 5)', 'pop("feed_clamp", 36, 0.50, 278.0, 5)'),
    ('pop("travel_hold", 36, 0.50, 55.6, 1)', 'pop("feed_hold", 36, 0.50, 55.6, 1)'),
    ('pop("arch_veto", 24, 0.75)', 'pop("cot_veto", 24, 0.75)'),
    ('("id", "ttf-r34-186")', '("id", "ttf-r46-246")'),
    (
        '"Gable-Retort GR-4 / Flue-Bank FB-7: crown-arch beats travel by 208 us; correct "',
        '"Pyro-Ness PN-9 / Coil-Pass CP-4: coil-outlet beats feed by 208 us; correct "',
    ),
    (
        '"MODIFY still eats an in-window wall-tie snap (partnered negative total -0.46)"',
        '"MODIFY still eats an in-window tube-skin split (partnered negative total -0.46)"',
    ),
    (
        '"42 ms raster. total -0.46 = 0.32 + -0.58 + -0.16 + 0.02 + -0.06. Named flue "',
        '"42 ms raster. total -0.46 = 0.32 + -0.58 + -0.16 + 0.02 + -0.06. Named coil "',
    ),
    ('"coke-oven-battery"', '"ethylene-steam-cracker"'),
]


REC248_PAIRS = [
    ("def record_188():", "def record_248():"),
    ("independent_excerpt(34188, 104, 40000, 15, spike_avoid_us(spikes))",
     "independent_excerpt(46248, 104, 40000, 15, spike_avoid_us(spikes))"),
    (
        '"Draw-Valve DV-6 is frozen on Argon-Cist AC-2\'s HIL coldbox while an oxygen "',
        '"TMGa-Line TL-6 is frozen on Susceptor-HIL SH-2\'s HIL MOCVD pad while a "',
    ),
    (
        '"paramagnetic cell reports 98.2 pct against a 99.0 pct liquid-draw floor. A "',
        '"pyrometer reports 986 C against a 1020 C growth-temperature floor. A "',
    ),
    (
        '"nitrogen tap, lit by the pad lamp spectrum, still reads 99.6 pct apparent. "',
        '"wafer thermocouple, lit by the pad lamp spectrum, still reads 1048 C apparent. "',
    ),
    (
        '"O2-first latches REJECT hold; N2-first would commit a liquid draw on an "',
        '"Pyro-first latches REJECT hold; TC-first would commit TMGa flow on an "',
    ),
    ('("domain", "air-separation-coldbox")', '("domain", "gan-mocvd-reactor")'),
    (
        '"Do not draw liquid oxygen unless O2 purity >= 99.0 pct; keep draw 0.0 L/s "',
        '"Do not open TMGa unless pyro growth T >= 1020 C; keep TMGa 0.0 sccm "',
    ),
    ('"until the injected impurity packet drops.",', '"until the injected under-temp packet drops.",'),
    ("1756794621000188", "1756794621000248"),
    ('"o2.cell.pct 98.2 pct"', '"ir.pyro.C 986 C"'),
    ('"n2.tap.pct 99.6 pct apparent"', '"tc.wafer.C 1048 C apparent"'),
    (
        '"O2-first latches REJECT hold 0.0 L/s; N2-first would commit "',
        '"Pyro-first latches REJECT hold 0.0 sccm; TC-first would commit "',
    ),
    ('"12 L/s on an apparent 99.6 pct under-read.",', '"180 sccm on an apparent 1048 C under-read.",'),
    (
        '"380 us = one paramagnetic O2 slot versus N2-tap integration on this "',
        '"380 us = one pyrometer slot versus wafer-TC integration on this "',
    ),
    ('"coldbox HIL bus.",', '"MOCVD HIL bus.",'),
    (
        '"Margin 171 us vs combined jitter ~58 us (O2 26 + N2 32): 2.9x "',
        '"Margin 171 us vs combined jitter ~58 us (pyro 26 + TC 32): 2.9x "',
    ),
    (
        '"O2 cell (geometric lag, not a sensor fault); the apparent "',
        '"pyrometer (geometric lag, not a sensor fault); the apparent "',
    ),
    (
        '"99.6 pct packet is still the loser in this 380 us window.",',
        '"1048 C packet is still the loser in this 380 us window.",',
    ),
    ('"paramagnetic O2 cell, 5 kHz burst, 26 us jitter"', '"susceptor pyrometer, 5 kHz burst, 26 us jitter"'),
    ('"N2 purity tap, 200 Hz, 32 us jitter"', '"wafer thermocouple, 200 Hz, 32 us jitter"'),
    ('"coldbox skin thermocouple (context)"', '"chamber skin thermocouple (context)"'),
    ('"HIL lamp-spectrum monitor (context)"', '"HIL lamp-spectrum monitor (context)"'),
    ('("o2_draw_floor_pct", 99.0)', '("growth_floor_C", 1020.0)'),
    ('("observed_o2_pct", 98.2)', '("observed_pyro_C", 986.0)'),
    ('("n2_apparent_pct", 99.6)', '("tc_apparent_C", 1048.0)'),
    ('("proposed_draw_L_s", 12.0)', '("proposed_tmga_sccm", 180.0)'),
    ('("pad", "Argon-Cist AC-2 coldbox mockup")', '("pad", "Susceptor-HIL SH-2 MOCVD mockup")'),
    ('("injected", "O2 impurity packet + N2-tap lamp spectrum")',
     '("injected", "under-temp packet + wafer-TC lamp spectrum")'),
    (
        '"Hardware-in-the-loop coldbox. Invented plant; not a live ASU.",',
        '"Hardware-in-the-loop MOCVD pad. Invented plant; not a live epi tool.",',
    ),
    (
        '"1. Draw-Valve DV-6 on the AC-2 HIL coldbox; draw 12 L/s armed.",',
        '"1. TMGa-Line TL-6 on the SH-2 HIL pad; TMGa 180 sccm armed.",',
    ),
    (
        '"2. Lamp injected 110-150 us before O2 cell sees the impurity packet.",',
        '"2. Lamp injected 110-150 us before pyrometer sees the under-temp packet.",',
    ),
    ('"3. Skin precursor at 1.380 ms.",', '"3. Skin precursor at 1.380 ms.",'),
    ('"5. o2.cell.pct 98.2 pct at 5.760 ms (winner).",', '"5. ir.pyro.C 986 C at 5.760 ms (winner).",'),
    ('"6. n2.tap.pct 99.6 pct at 5.931 ms (loser by 171 us).",', '"6. tc.wafer.C 1048 C at 5.931 ms (loser by 171 us).",'),
    (
        '"7. Gate at 6.860 ms: REJECT hold 0.0 L/s; do not draw 12 L/s.",',
        '"7. Gate at 6.860 ms: REJECT hold 0.0 sccm; do not open 180 sccm.",',
    ),
    (
        '"8. Column remains under floor this cycle; liquid-draw floor held.",',
        '"8. Chamber remains under floor this cycle; TMGa growth floor held.",',
    ),
    (
        '"9. Flux recycle queued on the pad.",',
        '"9. Recipe recycle queued on the pad.",',
    ),
    (
        '"10. Delayed (abort_s=540): 9 min column retune and lamp-spectrum retune.",',
        '"10. Delayed (abort_s=540): 9 min chamber retune and lamp-spectrum retune.",',
    ),
    ('("name", "draw_lox_12")', '("name", "tmga_open_180")'),
    ('("draw_L_s", 12.0)', '("tmga_sccm", 180.0)'),
    ('("n2_authoritative", True)', '("tc_authoritative", True)'),
    ('("o2_pct", 98.2)', '("pyro_C", 986.0)'),
    ('("o2_draw_floor_pct", 99.0)', '("growth_floor_C", 1020.0)'),
    ('("n2_apparent_pct", 99.6)', '("tc_apparent_C", 1048.0)'),
    (
        '"Planner proposes 12 L/s liquid draw because N2-tap apparent 99.6 pct looks "',
        '"Planner proposes 180 sccm TMGa because wafer-TC apparent 1048 C looks "',
    ),
    (
        '"over the 99.0 pct floor, treating O2 98.2 pct as a noisy sheath echo.",',
        '"over the 1020 C floor, treating pyro 986 C as a noisy sheath echo.",',
    ),
    (
        '"O2 purity 98.2 pct is under the 99.0 pct liquid-draw floor. N2-tap apparent "',
        '"Pyrometer 986 C is under the 1020 C growth-temperature floor. Wafer-TC apparent "',
    ),
    (
        '"99.6 pct is a HIL lamp under-read of impurity, not a clearance. REJECT: hold "',
        '"1048 C is a HIL lamp under-read of wafer T, not a clearance. REJECT: hold "',
    ),
    (
        '"0.0 L/s; do not commit 12 L/s across the column.",',
        '"0.0 sccm; do not commit 180 sccm across the chamber.",',
    ),
    ('("o2_pct"', '("pyro_C"'),
    ('("floor", 99.0)', '("floor", 1020.0)'),
    ('("observed_o2", 98.2)', '("observed_pyro", 986.0)'),
    ('("n2_apparent", 99.6)', '("tc_apparent", 1048.0)'),
    ('("draw_L_s"', '("tmga_sccm"'),
    ('("proposed", 12.0)', '("proposed", 180.0)'),
    ('("executed", 0.0)', '("executed", 0.0)'),
    ('("name", "hold_for_o2_floor")', '("name", "hold_for_growth_floor")'),
    ('("draw_L_s", 0.0)', '("tmga_sccm", 0.0)'),
    ('("n2_authoritative", False)', '("tc_authoritative", False)'),
    (
        '"REJECT: hold 0.0 L/s; 12 L/s draw cancelled. O2 98.2 < 99.0 floor.",',
        '"REJECT: hold 0.0 sccm; 180 sccm TMGa cancelled. Pyro 986 < 1020 floor.",',
    ),
    (
        '"Correct REJECT held Draw-Valve DV-6 at 0.0 L/s. Column under floor this cycle; "',
        '"Correct REJECT held TMGa-Line TL-6 at 0.0 sccm. Chamber under floor this cycle; "',
    ),
    (
        '"liquid-draw floor held. N2-tap apparent was not treated as an O2 clearance.",',
        '"growth-temperature floor held. Wafer-TC apparent was not treated as a pyro clearance.",',
    ),
    ('("draw_valve", "held; speed 0.0 L/s")', '("tmga_line", "held; flow 0.0 sccm")'),
    ('("column", "still under 99.0 pct this cycle")', '("chamber", "still under 1020 C this cycle")'),
    ('("n2_tap", "99.6 pct unused as clearance")', '("wafer_tc", "1048 C unused as clearance")'),
    ('("mission", "draw deferred")', '("mission", "TMGa deferred")'),
    (
        '"Geometric lag: lamp was injected 110-150 us before the O2 cell, yet O2 still won the 380 us race.",',
        '"Geometric lag: lamp was injected 110-150 us before the pyrometer, yet pyro still won the 380 us race.",',
    ),
    (
        '"Delayed (abort_s=540): pad policy update forbids treating N2-tap apparent as an O2 substitute after a 9 min column retune.",',
        '"Delayed (abort_s=540): pad policy update forbids treating wafer-TC apparent as a pyro substitute after a 9 min chamber retune.",',
    ),
    ('("winner", "o2.cell.pct (5.760 ms, 98.2 pct)")', '("winner", "ir.pyro.C (5.760 ms, 986 C)")'),
    ('("loser", "n2.tap.pct (5.931 ms, 99.6 pct)")', '("loser", "tc.wafer.C (5.931 ms, 1048 C)")'),
    (
        '"N2-first by < 171 us inside the 380 us window would have committed "',
        '"TC-first by < 171 us inside the 380 us window would have committed "',
    ),
    (
        '"12 L/s with O2 98.2 < 99.0 floor. Order, not amplitude, selected the hold.",',
        '"180 sccm with pyro 986 < 1020 floor. Order, not amplitude, selected the hold.",',
    ),
    (
        '"Safety and coherence step up at the REJECT gate (6.860 ms, tick 4) as the hold "',
        '"Safety and coherence step up at the REJECT gate (6.860 ms, tick 4) as the hold "',
    ),
    ('"locks in over the illegal draw.",', '"locks in over the illegal TMGa open.",'),
    ('spike("tc.box.ctx", 1.380, 0.43)', 'spike("tc.box.ctx", 1.380, 0.43)'),
    ('spike("o2.cell.pct", 2.680, 0.62)', 'spike("ir.pyro.C", 2.680, 0.62)'),
    ('spike("n2.tap.pct", 4.180, 0.49)', 'spike("tc.wafer.C", 4.180, 0.49)'),
    ('spike("o2.cell.pct", 5.760, 1.35)', 'spike("ir.pyro.C", 5.760, 1.35)'),
    ('spike("n2.tap.pct", 5.931, 1.12)', 'spike("tc.wafer.C", 5.931, 1.12)'),
    ('spike("o2.cell.pct", 9.020, 0.77)', 'spike("ir.pyro.C", 9.020, 0.77)'),
    ('spike("n2.tap.pct", 17.100, 0.58)', 'spike("tc.wafer.C", 17.100, 0.58)'),
    ('spike("o2.cell.pct", 30.000, 0.54)', 'spike("ir.pyro.C", 30.000, 0.54)'),
    ('spike("n2.tap.pct", 39.100, 0.46)', 'spike("tc.wafer.C", 39.100, 0.46)'),
    ('"thalamic-relay.coldbox-o2"', '"thalamic-relay.mocvd-pyro"'),
    ('"spikenaut.policy.draw-hold"', '"spikenaut.policy.tmga-hold"'),
    ('("relay.o2.cell", "policy.draw_hold", 0.69)', '("relay.ir.pyro", "policy.tmga_hold", 0.69)'),
    ('("relay.n2.apparent", "policy.draw_commit", 0.27)', '("relay.tc.wafer", "policy.tmga_commit", 0.27)'),
    ('("relay.tc.box", "policy.draw_hold", 0.11)', '("relay.tc.box", "policy.tmga_hold", 0.11)'),
    (
        '"purity_stdp; DA at O2 win (5.760 ms) tags draw_hold over draw_commit"',
        '"growth_stdp; DA at pyro win (5.760 ms) tags tmga_hold over tmga_commit"',
    ),
    ('pop("draw_hold", 52, 0.50, 253.0, 5)', 'pop("tmga_hold", 52, 0.50, 253.0, 5)'),
    ('pop("draw_commit", 40, 0.50, 65.8, 1)', 'pop("tmga_commit", 40, 0.50, 65.8, 1)'),
    ('pop("o2_veto", 32, 0.75)', 'pop("pyro_veto", 32, 0.75)'),
    ('("id", "ttf-r34-188")', '("id", "ttf-r46-248")'),
    (
        '"Argon-Cist AC-2 HIL / Draw-Valve DV-6: O2 98.2 pct beats N2-tap 99.6; "',
        '"Susceptor-HIL SH-2 HIL / TMGa-Line TL-6: pyro 986 C beats wafer-TC 1048; "',
    ),
    ('"correct REJECT holds the liquid draw"', '"correct REJECT holds the TMGa open"'),
    (
        '"Correct REJECT. O2 under floor; N2-tap lamp under-read unused as clearance. "',
        '"Correct REJECT. Pyro under floor; wafer-TC lamp under-read unused as clearance. "',
    ),
    ('"air-separation-coldbox"', '"gan-mocvd-reactor"'),
    ('"hil-coldbox"', '"hil-mocvd"'),
    ('"o2-vs-n2"', '"pyro-vs-tc"'),
    ('"liquid-draw-floor"', '"growth-temp-floor"'),
    (
        '"Teaches that a HIL N2-tap lamp under-read can lose to paramagnetic O2 inside a "',
        '"Teaches that a HIL wafer-TC lamp under-read can lose to a susceptor pyro inside a "',
    ),
    (
        '"380 us window; reversing 171 us would have selected an illegal liquid draw.",',
        '"380 us window; reversing 171 us would have selected an illegal TMGa open.",',
    ),
]


REC249_PAIRS = [
    ("def record_189():", "def record_249():"),
    ("independent_excerpt(34189, 60, 30000, 13, spike_avoid_us(spikes))",
     "independent_excerpt(46249, 60, 30000, 13, spike_avoid_us(spikes))"),
    (
        '"Roof-Ring RR-3 at Hearth-Knap HK-6 still holds an 18.0 MW electrode while a "',
        '"Cooler-C3 at Grate-Shaw GS-5 still holds a 14.0 spm grate while an "',
    ),
    (
        '"68 kPa roof-pressure pulse sits over a 55 kPa baghouse cap. A baghouse staff "',
        '"8.4 kPa undergrate pulse sits over a 6.5 kPa hood cap. A hood staff "',
    ),
    (
        '"on the same duct still claims 4.2 kPa false-draft. Roof-first latches a power "',
        '"on the same plenum still claims 1.1 kPa false-draft. Undergrate-first latches a grate "',
    ),
    (
        '"clamp; staff-first would keep 18.0 MW into a close-out surge.",',
        '"clamp; staff-first would keep 14.0 spm into a close-out surge.",',
    ),
    ('("domain", "eaf-arc-furnace")', '("domain", "clinker-grate-cooler")'),
    (
        '"Stroke the HK-6 electrode only if roof pressure <= 55 kPa; otherwise clamp "',
        '"Stroke the GS-5 grate only if undergrate pressure <= 6.5 kPa; otherwise clamp "',
    ),
    (
        '"power so the baghouse surge is not made at 18.0 MW.",',
        '"speed so the hood surge is not made at 14.0 spm.",',
    ),
    ("1756794621000189", "1756794621000249"),
    ('"pt.roof.kPa 68 kPa"', '"pt.under.kPa 8.4 kPa"'),
    ('"staff.bag.kPa 4.2 kPa false-draft"', '"staff.hood.kPa 1.1 kPa false-draft"'),
    (
        '"Roof-first latches electrode clamp 18.0 -> 11.0 MW; staff-first keeps "',
        '"Undergrate-first latches grate clamp 14.0 -> 9.0 spm; staff-first keeps "',
    ),
    ('"18.0 MW on a false-draft duct.",', '"14.0 spm on a false-draft plenum.",'),
    (
        '"520 us = one 2 kHz roof-PT sample versus baghouse staff decode on this "',
        '"520 us = one 2 kHz undergrate-PT sample versus hood staff decode on this "',
    ),
    ('"furnace bus.",', '"cooler-bus.",'),
    (
        '"Margin 218 us vs combined jitter ~71 us (roof 33 + staff 38): 3.1x over "',
        '"Margin 218 us vs combined jitter ~71 us (undergrate 33 + staff 38): 3.1x over "',
    ),
    (
        '"window would have kept 18.0 MW into a 68 kPa pulse.",',
        '"window would have kept 14.0 spm into an 8.4 kPa pulse.",',
    ),
    ('"roof-pressure PT, 2 kHz, 33 us jitter"', '"undergrate-pressure PT, 2 kHz, 33 us jitter"'),
    ('"baghouse staff gauge, 200 Hz, 38 us jitter"', '"hood staff gauge, 200 Hz, 38 us jitter"'),
    ('"fourth-hole draft PT (context)"', '"cooler-fan draft PT (context)"'),
    ('"electrode hydraulic pressure (context)"', '"grate hydraulic pressure (context)"'),
    ('("baghouse_cap_kPa", 55.0)', '("hood_cap_kPa", 6.5)'),
    ('("observed_roof_kPa", 68.0)', '("observed_under_kPa", 8.4)'),
    ('("proposed_power_MW", 18.0)', '("proposed_spm", 14.0)'),
    ('("staff_kPa", 4.2)', '("staff_kPa", 1.1)'),
    (
        '"1. Electrode indexed onto HK-6 hearth; RR-3 armed at 18.0 MW.",',
        '"1. Grate indexed onto GS-5 cooler; C3 armed at 14.0 spm.",',
    ),
    (
        '"2. Staff reports 4.2 kPa false-draft; roof already sees 68 kPa.",',
        '"2. Staff reports 1.1 kPa false-draft; undergrate already sees 8.4 kPa.",',
    ),
    ('"5. pt.roof.kPa 68 kPa at 6.840 ms (winner).",', '"5. pt.under.kPa 8.4 kPa at 6.840 ms (winner).",'),
    ('"6. staff.bag.kPa 4.2 kPa at 7.058 ms (loser by 218 us).",',
     '"6. staff.hood.kPa 1.1 kPa at 7.058 ms (loser by 218 us).",'),
    (
        '"7. Gate at 7.280 ms: MODIFY electrode 18.0 -> 11.0 MW.",',
        '"7. Gate at 7.280 ms: MODIFY grate 14.0 -> 9.0 spm.",',
    ),
    (
        '"8. Power applies; next-sample roof 51 kPa < 55 cap.",',
        '"8. Grate applies; next-sample undergrate 5.8 kPa < 6.5 cap.",',
    ),
    ('"9. Duct occupies; next heat queued.",', '"9. Bed occupies; next kiln string queued.",'),
    (
        '"10. Delayed (hearth_reseq_s=420): dispatcher resequences the following heat +7 min.",',
        '"10. Delayed (cooler_reseq_s=420): dispatcher resequences the following string +7 min.",',
    ),
    ('("name", "electrode_18_mw")', '("name", "grate_14_spm")'),
    ('("power_MW", 18.0)', '("spm", 14.0)'),
    ('("servo_bar", 22.0)', '("servo_bar", 22.0)'),
    ('("hearth_id", 6)', '("cooler_id", 3)'),
    ('("roof_kPa", 68.0)', '("under_kPa", 8.4)'),
    ('("baghouse_cap_kPa", 55.0)', '("hood_cap_kPa", 6.5)'),
    ('("hearth_reseq_s", 420)', '("cooler_reseq_s", 420)'),
    (
        '"Planner proposes 18.0 MW electrode because the baghouse staff claims the duct "',
        '"Planner proposes 14.0 spm grate because the hood staff claims the plenum "',
    ),
    (
        '"is calm, treating roof 68 kPa as a sidelobe.",',
        '"is calm, treating undergrate 8.4 kPa as a sidelobe.",',
    ),
    (
        '"Roof 68 kPa won by 218 us, so the pulse is inside the 55 kPa baghouse cap. "',
        '"Undergrate 8.4 kPa won by 218 us, so the pulse is inside the 6.5 kPa hood cap. "',
    ),
    (
        '"Staff-gauge false-draft is not a pressure. MODIFY: electrode 18.0 -> 11.0 MW. "',
        '"Staff-gauge false-draft is not a pressure. MODIFY: grate 14.0 -> 9.0 spm. "',
    ),
    (
        '"A full REJECT (kill the arc) is not indicated: 11.0 MW is a legal catch-and-pass.",',
        '"A full REJECT (kill the grate) is not indicated: 9.0 spm is a legal catch-and-pass.",',
    ),
    ('("roof_kPa"', '("under_kPa"'),
    ('("cap", 55.0)', '("cap", 6.5)'),
    ('("observed", 68.0)', '("observed", 8.4)'),
    ('("observed_after_clamp", 51.0)', '("observed_after_clamp", 5.8)'),
    ('("power_MW"', '("spm"'),
    ('("proposed", 18.0)', '("proposed", 14.0)'),
    ('("clamped", 11.0)', '("clamped", 9.0)'),
    ('("name", "clamped_electrode_11")', '("name", "clamped_grate_9")'),
    ('("power_MW", 11.0)', '("spm", 9.0)'),
    (
        '"MODIFY: electrode 18.0 -> 11.0 MW. Process-correct vs the 55 kPa baghouse cap.",',
        '"MODIFY: grate 14.0 -> 9.0 spm. Process-correct vs the 6.5 kPa hood cap.",',
    ),
    (
        '"Correct MODIFY held RR-3 at 11.0 MW. Next-sample roof 51 kPa under the "',
        '"Correct MODIFY held C3 at 9.0 spm. Next-sample undergrate 5.8 kPa under the "',
    ),
    (
        '"55 kPa cap. Staff 4.2 kPa false-draft was not treated as a pressure clearance.",',
        '"6.5 kPa cap. Staff 1.1 kPa false-draft was not treated as a pressure clearance.",',
    ),
    ('("electrode", "clamped 18.0 -> 11.0 MW")', '("grate", "clamped 14.0 -> 9.0 spm")'),
    ('("roof", "51 kPa < 55 cap after clamp")', '("undergrate", "5.8 kPa < 6.5 cap after clamp")'),
    ('("staff", "4.2 kPa unused as clearance")', '("staff", "1.1 kPa unused as clearance")'),
    ('("mission", "heat completed under cap")', '("mission", "string completed under cap")'),
    (
        '"Staff-gauge false-draft lagged the roof pulse by 218 us; order, not amplitude, selected the clamp.",',
        '"Staff-gauge false-draft lagged the undergrate pulse by 218 us; order, not amplitude, selected the clamp.",',
    ),
    (
        '"Delayed (hearth_reseq_s=420): dispatcher resequences the following heat +7 min. Not a safety inflection.",',
        '"Delayed (cooler_reseq_s=420): dispatcher resequences the following string +7 min. Not a safety inflection.",',
    ),
    ('("winner", "pt.roof.kPa (6.840 ms, 68 kPa)")', '("winner", "pt.under.kPa (6.840 ms, 8.4 kPa)")'),
    ('("loser", "staff.bag.kPa (7.058 ms, 4.2 kPa)")', '("loser", "staff.hood.kPa (7.058 ms, 1.1 kPa)")'),
    (
        '"Staff-first by < 218 us inside the 520 us window would have kept "',
        '"Staff-first by < 218 us inside the 520 us window would have kept "',
    ),
    (
        '"18.0 MW into a 68 kPa pulse over the 55 cap. The MODIFY is "',
        '"14.0 spm into an 8.4 kPa pulse over the 6.5 cap. The MODIFY is "',
    ),
    (
        '"Tick 6 is "\n                "hearth_reseq_s=420.",',
        '"Tick 6 is "\n                "cooler_reseq_s=420.",',
    ),
    ('spike("pt.roof.kPa", 3.040, 0.59)', 'spike("pt.under.kPa", 3.040, 0.59)'),
    ('spike("staff.bag.kPa", 4.980, 0.48)', 'spike("staff.hood.kPa", 4.980, 0.48)'),
    ('spike("pt.roof.kPa", 6.840, 1.31)', 'spike("pt.under.kPa", 6.840, 1.31)'),
    ('spike("staff.bag.kPa", 7.058, 1.09)', 'spike("staff.hood.kPa", 7.058, 1.09)'),
    ('spike("pt.roof.kPa", 9.480, 0.73)', 'spike("pt.under.kPa", 9.480, 0.73)'),
    ('spike("staff.bag.kPa", 18.200, 0.57)', 'spike("staff.hood.kPa", 18.200, 0.57)'),
    ('spike("pt.roof.kPa", 26.700, 0.51)', 'spike("pt.under.kPa", 26.700, 0.51)'),
    ('"thalamic-relay.eaf-roof"', '"thalamic-relay.cooler-under"'),
    ('"spikenaut.policy.power-clamp"', '"spikenaut.policy.grate-clamp"'),
    ('("relay.pt.roof", "policy.power_clamp", 0.64)', '("relay.pt.under", "policy.grate_clamp", 0.64)'),
    ('("relay.staff.bag", "policy.staff_hold", 0.29)', '("relay.staff.hood", "policy.staff_hold", 0.29)'),
    ('("relay.pt.draft", "policy.power_clamp", 0.12)', '("relay.pt.draft", "policy.grate_clamp", 0.12)'),
    (
        '"baghouse_stdp; 5-HT at roof win (6.840 ms) tags power_clamp over staff_hold"',
        '"hood_stdp; 5-HT at undergrate win (6.840 ms) tags grate_clamp over staff_hold"',
    ),
    ('pop("power_clamp", 30, 0.50, 256.4, 4)', 'pop("grate_clamp", 30, 0.50, 256.4, 4)'),
    ('pop("roof_veto", 20, 0.75)', 'pop("under_veto", 20, 0.75)'),
    ('("id", "ttf-r34-189")', '("id", "ttf-r46-249")'),
    (
        '"Hearth-Knap HK-6 / Roof-Ring RR-3: roof 68 kPa beats staff false-draft; "',
        '"Grate-Shaw GS-5 / Cooler-C3: undergrate 8.4 kPa beats staff false-draft; "',
    ),
    (
        '"correct MODIFY clamps electrode 18.0 -> 11.0 MW"',
        '"correct MODIFY clamps grate 14.0 -> 9.0 spm"',
    ),
    (
        '"Correct MODIFY. Roof over cap; staff false-draft unused. total +0.92 = "',
        '"Correct MODIFY. Undergrate over cap; staff false-draft unused. total +0.92 = "',
    ),
    ('"eaf-arc-furnace"', '"clinker-grate-cooler"'),
    ('"roof-vs-staff"', '"undergrate-vs-staff"'),
    ('"baghouse"', '"cooler-hood"'),
    (
        '"Teaches that a false-draft baghouse staff can lose to a legal roof PT inside "',
        '"Teaches that a false-draft hood staff can lose to a legal undergrate PT inside "',
    ),
    (
        '"a 520 us window; reversing 218 us would have kept an illegal 18.0 MW arc.",',
        '"a 520 us window; reversing 218 us would have kept an illegal 14.0 spm grate.",',
    ),
]


REC250_PAIRS = [
    ("def record_190():", "def record_250():"),
    ("independent_excerpt(34190, 84, 22000, 12, spike_avoid_us(spikes))",
     "independent_excerpt(46250, 84, 22000, 12, spike_avoid_us(spikes))"),
    (
        '"Atom-Disk AD-11 in Slurry-Crown SC-8 is already at 84.0 C outlet while a "',
        '"Yankee-Y4 in Crepe-Ness CN-8 is already at 96.0 C shell while an "',
    ),
    (
        '"NIR cake glint still reports 112 against a 95.0 C stick cap that the "',
        '"IR hood glint still reports 128 against a 110.0 C stick cap that the "',
    ),
    (
        '"outlet RTD has not crossed. Outlet-first should ACCEPT the already-legal "',
        '"shell RTD has not crossed. Shell-first should ACCEPT the already-legal "',
    ),
    (
        '"18500 rpm atomize; glint-first would hold a legal spin on lighting.",',
        '"1100 m/min crepe; glint-first would hold a legal yankee on lighting.",',
    ),
    ('("domain", "spray-dryer-tower")', '("domain", "tissue-yankee-dryer")'),
    (
        '"Spin AD-11 when outlet RTD is <= 95.0 C; do not spend a NIR cake glint "',
        '"Run Y4 when shell RTD is <= 110.0 C; do not spend an IR hood glint "',
    ),
    ('"on a hold.",', '"on a hold.",'),
    ("1756794621000190", "1756794621000250"),
    ('"rtd.outlet.C 84.0 C"', '"rtd.shell.C 96.0 C"'),
    ('"ir.cake.glint 112 lighting"', '"ir.hood.glint 128 lighting"'),
    (
        '"Outlet-first ACCEPTS the already-legal 84.0 C atomize. Glint-first "',
        '"Shell-first ACCEPTS the already-legal 96.0 C crepe. Glint-first "',
    ),
    (
        '"would REJECT a legal spin on a 112 C lighting.",',
        '"would REJECT a legal yankee on a 128 C lighting.",',
    ),
    (
        '"240 us = one outlet-RTD sample minus NIR-cake integration on this "',
        '"240 us = one shell-RTD sample minus IR-hood integration on this "',
    ),
    ('"tower-bus simulation.",', '"yankee-bus simulation.",'),
    (
        '"Margin 118 us vs combined jitter ~50 us (RTD 22 + NIR 28): 2.4x over "',
        '"Margin 118 us vs combined jitter ~50 us (RTD 22 + IR 28): 2.4x over "',
    ),
    (
        '"window would have invented a cake hold on an already-legal 84.0 C outlet.",',
        '"window would have invented a hood hold on an already-legal 96.0 C shell.",',
    ),
    ('"outlet RTD, 2 kHz, 22 us jitter"', '"shell RTD, 2 kHz, 22 us jitter"'),
    ('"NIR cake camera, 200 Hz, 28 us jitter"', '"IR hood camera, 200 Hz, 28 us jitter"'),
    ('"chamber PT (context)"', '"hood PT (context)"'),
    ('"inlet air flow (context)"', '"pocket air flow (context)"'),
    ('("stick_cap_C", 95.0)', '("stick_cap_C", 110.0)'),
    ('("observed_outlet_C", 84.0)', '("observed_shell_C", 96.0)'),
    ('("nir_cake_glint_C", 112.0)', '("ir_hood_glint_C", 128.0)'),
    ('("proposed_rpm", 18500.0)', '("proposed_m_min", 1100.0)'),
    (
        '"1. AD-11 seeded; slurry at 84.0 C outlet under 95.0 stick cap.",',
        '"1. Y4 seeded; sheet at 96.0 C shell under 110.0 stick cap.",',
    ),
    (
        '"2. NIR cake glint 112 from chamber lighting, not wall cake.",',
        '"2. IR hood glint 128 from hood lighting, not sheet stick.",',
    ),
    ('"3. Chamber precursor at 0.700 ms.",', '"3. Hood precursor at 0.700 ms.",'),
    ('"5. rtd.outlet.C 84.0 C at 3.740 ms (winner).",', '"5. rtd.shell.C 96.0 C at 3.740 ms (winner).",'),
    ('"6. ir.cake.glint 112 at 3.858 ms (loser by 118 us).",', '"6. ir.hood.glint 128 at 3.858 ms (loser by 118 us).",'),
    (
        '"7. Gate at 4.300 ms: ACCEPT 18500 rpm as proposed.",',
        '"7. Gate at 4.300 ms: ACCEPT 1100 m/min as proposed.",',
    ),
    (
        '"8. Spin executes; outlet remains 84.0 C < 95.0.",',
        '"8. Yankee executes; shell remains 96.0 C < 110.0.",',
    ),
    ('"9. Disk emptied; next pass queued.",', '"9. Reel emptied; next pass queued.",'),
    (
        '"10. Delayed (survey_hold_s=280): 4.7 min PSD survey. Not a safety inflection.",',
        '"10. Delayed (survey_hold_s=280): 4.7 min basis-weight survey. Not a safety inflection.",',
    ),
    ('("name", "atomize_18500")', '("name", "crepe_1100")'),
    ('("rpm", 18500.0)', '("m_min", 1100.0)'),
    ('("inlet_kPa", 22.0)', '("pocket_kPa", 22.0)'),
    ('("outlet_C", 84.0)', '("shell_C", 96.0)'),
    ('("stick_cap_C", 95.0)', '("stick_cap_C", 110.0)'),
    ('("nir_cake_glint_C", 112.0)', '("ir_hood_glint_C", 128.0)'),
    (
        '"Planner proposes 18500 rpm because outlet RTD 84.0 C is under the 95.0 C "',
        '"Planner proposes 1100 m/min because shell RTD 96.0 C is under the 110.0 C "',
    ),
    (
        '"stick cap; NIR 112 C is lighting, not cake.",',
        '"stick cap; IR 128 C is lighting, not sheet stick.",',
    ),
    (
        '"Outlet RTD 84.0 C is under the 95.0 C stick cap. NIR cake 112 C is a "',
        '"Shell RTD 96.0 C is under the 110.0 C stick cap. IR hood 128 C is a "',
    ),
    (
        '"chamber lighting glint, not wall load. ACCEPT the proposed 18500 rpm; do "',
        '"hood lighting glint, not sheet load. ACCEPT the proposed 1100 m/min; do "',
    ),
    ('"not invent a hold.",', '"not invent a hold.",'),
    ('("outlet_C"', '("shell_C"'),
    ('("cap", 95.0)', '("cap", 110.0)'),
    ('("observed", 84.0)', '("observed", 96.0)'),
    ('("nir_cake_glint_C", 112.0)', '("ir_hood_glint_C", 128.0)'),
    ('("rpm"', '("m_min"'),
    ('("proposed", 18500.0)', '("proposed", 1100.0)'),
    ('("executed", 18500.0)', '("executed", 1100.0)'),
    (
        '"ACCEPT: proposed 18500 rpm executed unchanged. Outlet 84.0 C < 95.0; NIR glint unused.",',
        '"ACCEPT: proposed 1100 m/min executed unchanged. Shell 96.0 C < 110.0; IR glint unused.",',
    ),
    (
        '"Correct ACCEPT spun AD-11 at 84.0 C outlet. NIR 112 C was lighting, not cake. "',
        '"Correct ACCEPT ran Y4 at 96.0 C shell. IR 128 C was lighting, not sheet stick. "',
    ),
    (
        '"The proposal was already legal; reversing 118 us would have invented a hold.",',
        '"The proposal was already legal; reversing 118 us would have invented a hold.",',
    ),
    ('("disk", "spin executed; outlet 84.0 C < 95.0")', '("yankee", "run executed; shell 96.0 C < 110.0")'),
    ('("nir", "112 C glint unused as cake")', '("ir", "128 C glint unused as stick")'),
    ('("chamber", "held 22.0 kPa through the pass")', '("hood", "held 22.0 kPa through the pass")'),
    ('("mission", "atomize committed")', '("mission", "crepe committed")'),
    (
        '"NIR 112 C is a legal lighting glint, not a high-outlet alarm; outlet-first discarded a false hold.",',
        '"IR 128 C is a legal lighting glint, not a high-shell alarm; shell-first discarded a false hold.",',
    ),
    (
        '"Delayed (4.7 min / survey_hold_s=280): particle-size survey. Not a safety inflection.",',
        '"Delayed (4.7 min / survey_hold_s=280): basis-weight survey. Not a safety inflection.",',
    ),
    ('("winner", "rtd.outlet.C (3.740 ms, 84.0 C)")', '("winner", "rtd.shell.C (3.740 ms, 96.0 C)")'),
    ('("loser", "ir.cake.glint (3.858 ms, 112 lighting)")', '("loser", "ir.hood.glint (3.858 ms, 128 lighting)")'),
    (
        '"Glint-first by < 118 us inside the 240 us window would have held "',
        '"Glint-first by < 118 us inside the 240 us window would have held "',
    ),
    (
        '"the spin on a false high-outlet story. The proposal was already "',
        '"the yankee on a false high-shell story. The proposal was already "',
    ),
    (
        '"under the 95.0 cap, so the correct gate is still ACCEPT.",',
        '"under the 110.0 cap, so the correct gate is still ACCEPT.",',
    ),
    ('spike("pt.chamber.ctx", 0.700, 0.39)', 'spike("pt.hood.ctx", 0.700, 0.39)'),
    ('spike("rtd.outlet.C", 1.580, 0.57)', 'spike("rtd.shell.C", 1.580, 0.57)'),
    ('spike("ir.cake.glint", 2.400, 0.48)', 'spike("ir.hood.glint", 2.400, 0.48)'),
    ('spike("rtd.outlet.C", 3.740, 1.29)', 'spike("rtd.shell.C", 3.740, 1.29)'),
    ('spike("ir.cake.glint", 3.858, 1.10)', 'spike("ir.hood.glint", 3.858, 1.10)'),
    ('spike("rtd.outlet.C", 6.120, 0.76)', 'spike("rtd.shell.C", 6.120, 0.76)'),
    ('spike("ir.cake.glint", 8.800, 0.61)', 'spike("ir.hood.glint", 8.800, 0.61)'),
    ('spike("pt.chamber.ctx", 15.900, 0.41)', 'spike("pt.hood.ctx", 15.900, 0.41)'),
    ('spike("rtd.outlet.C", 19.400, 0.54)', 'spike("rtd.shell.C", 19.400, 0.54)'),
    ('spike("ir.cake.glint", 21.200, 0.46)', 'spike("ir.hood.glint", 21.200, 0.46)'),
    ('"thalamic-relay.dryer-outlet"', '"thalamic-relay.yankee-shell"'),
    ('"spikenaut.policy.atom-accept"', '"spikenaut.policy.yankee-accept"'),
    ('("relay.rtd.outlet", "policy.atom_go", 0.62)', '("relay.rtd.shell", "policy.yankee_go", 0.62)'),
    ('("relay.ir.cake", "policy.glint_hold", 0.28)', '("relay.ir.hood", "policy.glint_hold", 0.28)'),
    ('("relay.pt.chamber", "policy.atom_go", 0.14)', '("relay.pt.hood", "policy.yankee_go", 0.14)'),
    (
        '"pre_post_stdp; adenosine at outlet win (3.740 ms) opens 160 ms eligibility covering the 4.300 ms accept"',
        '"pre_post_stdp; adenosine at shell win (3.740 ms) opens 160 ms eligibility covering the 4.300 ms accept"',
    ),
    ('pop("atom_go", 42, 0.50, 297.6, 3)', 'pop("yankee_go", 42, 0.50, 297.6, 3)'),
    ('pop("stick_veto", 20, 0.80)', 'pop("crepe_veto", 20, 0.80)'),
    ('("id", "ttf-r34-190")', '("id", "ttf-r46-250")'),
    (
        '"Slurry-Crown SC-8 / Atom-Disk AD-11: outlet 84.0 C beats NIR cake glint; "',
        '"Crepe-Ness CN-8 / Yankee-Y4: shell 96.0 C beats IR hood glint; "',
    ),
    (
        '"correct ACCEPT of an already-legal 18500 rpm (total +1.16)"',
        '"correct ACCEPT of an already-legal 1100 m/min (total +1.16)"',
    ),
    (
        '"Correct ACCEPT. Outlet 84.0 C < 95.0; NIR glint is lighting, not cake. "',
        '"Correct ACCEPT. Shell 96.0 C < 110.0; IR glint is lighting, not sheet stick. "',
    ),
    ('"spray-dryer-tower"', '"tissue-yankee-dryer"'),
    ('"simulated-lighting"', '"simulated-lighting"'),
    ('"outlet-vs-nir"', '"shell-vs-ir"'),
    ('"atomize"', '"crepe"'),
    (
        '"Teaches that a NIR cake lighting glint can lose to a legal outlet RTD "',
        '"Teaches that an IR hood lighting glint can lose to a legal shell RTD "',
    ),
    (
        '"inside a 240 us window; reversing 118 us would have invented a hold on an "',
        '"inside a 240 us window; reversing 118 us would have invented a hold on an "',
    ),
    ('"already-legal spin.",', '"already-legal yankee.",'),
]


RECORD_247 = r'''def record_247():
    ticks = [
        tick(1760, -0.02, -0.01, -0.02, -0.01, 0.01),
        tick(4180, -0.04, -0.02, -0.04, -0.02, 0.01),
        tick(4332, -0.03, -0.01, -0.03, -0.02, 0.01),
        tick(4920, -0.07, -0.04, -0.09, -0.05, 0.02),
        tick(6410, -0.02, -0.01, -0.02, -0.01, 0.01),
        tick(1320000000, -0.02, -0.01, -0.02, -0.01, 0.00),
    ]
    spikes = [
        spike("dp.digest.ctx", 0.880, 0.40),
        spike("pt.live.MPa", 1.760, 0.58),
        spike("tx.raw.kPa", 2.520, 0.51),
        spike("pt.live.MPa", 4.180, 1.32),
        spike("tx.raw.kPa", 4.332, 1.15),
        spike("ctrl.gate", 4.920, 1.00),
        spike("pt.live.MPa", 6.410, 0.74),
        spike("tx.raw.kPa", 8.100, 0.61),
        spike("ctrl.gate", 12.000, 0.82),
        spike("dp.digest.ctx", 16.200, 0.42),
        spike("pt.live.MPa", 20.600, 0.53),
        spike("tx.raw.kPa", 23.200, 0.47),
    ]
    excerpt = independent_excerpt(46247, 88, 24000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Digest-A DA-2 on Laterite-Shaw LS-5 is armed for a 1.80 m3/min blow "
                "with live vessel 1.18 MPa against a 1.45 MPa cap. A kPa-scaled transmitter "
                "still reports raw 1180 on the same tap. Live-SI-first should ACCEPT the blow; "
                "a weak supervisor that binds the kPa count as MPa will REJECT a legal move.",
            ),
            ("domain", "bayer-digest-train"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Execute the 1.80 m3/min blow while live vessel stays <= 1.45 MPa; do "
                "not spend a kPa raw count as if it were MPa.",
            ),
            ("t0_us", 1756794621000247),
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
                                "pt.live.MPa 1.18 MPa",
                                "tx.raw.kPa 1180 kPa",
                            ],
                        ),
                        (
                            "semantics",
                            "Live-SI-first should ACCEPT 1.80 m3/min (1.18 MPa < 1.45 MPa cap). "
                            "Raw-kPa-first tempts a weak supervisor to treat 1180 as 1180 MPa.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one live-SI PT sample minus kPa-transmitter group delay "
                            "on this dual-EU skid.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 152 us vs combined jitter ~54 us (live 24 + raw 30): 2.8x over "
                            "a 2.0x trust floor. Order is correctly live-SI-first. The error is which "
                            "engineering unit the REJECT is bound to, not the race.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "live-SI vessel PT, 4 kHz, 24 us jitter",
                    "kPa-scaled transmitter, 4 kHz, 30 us jitter",
                    "digest differential pressure (context)",
                    "blow-valve LVDT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("cap_MPa", 1.45),
                        ("live_MPa", 1.18),
                        ("tx_raw_kPa", 1180.0),
                        ("tx_eu", "kPa"),
                        ("proposed_blow_m3_min", 1.8),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. DA-2 vessel latched; blow 1.80 m3/min armed on LS-5.",
                    "2. Live-SI 1.18 MPa; kPa transmitter raw 1180 on the same tap.",
                    "3. Digest-dp precursor at 0.880 ms.",
                    "4. Race window [4.120, 4.440] ms.",
                    "5. pt.live.MPa 1.18 MPa at 4.180 ms (winner).",
                    "6. tx.raw.kPa 1180 at 4.332 ms (loser by 152 us).",
                    "7. Gate at 4.920 ms: REJECT hold 0.00 m3/min (incorrect).",
                    "8. Legal blow cancelled; vessel still 1.18 MPa < 1.45 MPa cap.",
                    "9. Raw 1180 kPa remains 1.18 MPa in SI; never a 1180 MPa reading.",
                    "10. Delayed missed_window_s=1320 (22 min alumina-quality window) while the train waits.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "blow_180"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("blow_m3_min", 1.8),
                        ("hold", False),
                        ("eu", "MPa"),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_MPa", 1.18),
                        ("cap_MPa", 1.45),
                        ("tx_raw_kPa", 1180.0),
                        ("tx_eu", "kPa"),
                        ("supervisor_eu", "MPa"),
                        ("supervisor_compared_as_MPa", 1180.0),
                        ("proposed_blow_m3_min", 1.8),
                        ("race_margin_us", 152),
                        ("combined_jitter_us", 54),
                        ("missed_window_s", 1320),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 1.80 m3/min blow because live-SI 1.18 MPa is under "
                "the 1.45 MPa cap; raw 1180 is the same tap in kPa, not a second pressure.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Raw 1180 looks like a pressure excursion over a 1.45 MPa cap, so the "
                "supervisor holds the blow at 0.00 m3/min. Live-SI-first is treated as a noisy echo "
                "of the same loop. Over-caution on a dual-EU skid is the stated doctrine.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "live_MPa",
                            OrderedDict(
                                [
                                    ("cap", 1.45),
                                    ("observed", 1.18),
                                    ("executed_blow_m3_min", 0.0),
                                    ("eu", "MPa"),
                                ]
                            ),
                        ),
                        (
                            "tx_raw_kPa",
                            OrderedDict(
                                [
                                    ("raw", 1180.0),
                                    ("eu", "kPa"),
                                    ("misbound_as", "MPa"),
                                    ("supervisor_compared_as_MPa", 1180.0),
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
            ("name", "blow_hold_wrong_eu"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("blow_m3_min", 0.0),
                        ("hold", True),
                        ("eu", "MPa"),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (incorrect): blow 1.80 -> 0.00 m3/min. Routing relay.tx.kPa -> "
                "policy.blow_hold; live 1.18 MPa left unused as a go signal.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-REJECT held DA-2 at 0.00 m3/min. Live 1.18 MPa was under the 1.45 MPa cap; "
                "raw 1180 was the same tap in kPa. 22 min alumina-quality window "
                "missed (missed_window_s=1320). Correct gate was ACCEPT of the 1.80 m3/min blow.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("vessel", "held; blow 0.00 m3/min; live still 1.18 MPa < 1.45 MPa"),
                        ("transmitter", "1180 kPa unused, still 1.18 MPa in SI"),
                        ("train", "22 min alumina-quality window missed"),
                        ("mission", "blow deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Live-SI-first was the correct order and the live number was legal; the REJECT spent that win on a kPa-as-MPa bind.",
                    "Delayed (missed_window_s=1320): LS-5 loses the 22 min alumina-quality window; next window 5.4 h.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "ACCEPT the 1.80 m3/min blow; bind live 1.18 MPa against the 1.45 MPa cap in the same SI.",
                        ),
                        ("correct_eu", "MPa"),
                        ("wrong_eu", "kPa_as_MPa"),
                        (
                            "wrong_edit_applied",
                            OrderedDict([("blow_m3_min", 0.0), ("hold", True)]),
                        ),
                        (
                            "cost",
                            "Missed 22 min alumina-quality window (task/efficiency); vessel never exceeded 1.18 MPa (safety near-miss of a false hold).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "pt.live.MPa (4.180 ms, 1.18 MPa)"),
                        ("loser", "tx.raw.kPa (4.332 ms, 1180 kPa)"),
                        ("margin_us", 152),
                        (
                            "counterfactual_if_reversed",
                            "Raw-kPa-first by < 152 us would still be 1.18 MPa in SI; "
                            "a correct gate binds pt.live.MPa to blow_go either way. The wrong "
                            "REJECT spent the live win on the wrong engineering unit.",
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
            "relay.tx.kPa",
            "policy.blow_hold",
            [
                ("relay.tx.kPa", "policy.blow_hold", 0.73),
                ("relay.pt.live", "policy.blow_hold", 0.21),
            ],
            "acetylcholine",
            0.06,
            "eu_cap_stdp; ACh tags the (wrong) blow_hold bind at the kPa raw count",
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
                    pop("blow_hold", 48, 0.50, 260.4, 4),
                    pop("blow_go", 48, 0.80, 6.5, 0),
                    pop("eu_ctx", 32, 0.55, 97.7, 1),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r46-247"),
            (
                "title",
                "WRONG-REJECT at Laterite-Shaw LS-5 / Digest-A DA-2: live 1.18 MPa < 1.45 MPa cap; "
                "supervisor treats kPa raw 1180 as MPa",
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
                    "Wrong-reject. Sidecar arithmetic 1.18 < 1.45 on live SI is true; REJECT bound "
                    "to kPa-as-MPa. total -0.58 = -0.20 + -0.10 + -0.22 + -0.12 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "bayer-digest-train",
                    [
                        "reject",
                        "wrong-gate",
                        "eu-mismatch",
                        "kPa-as-MPa",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches a probe that a correct live-SI-first race can still be a wrong gate "
                    "when the REJECT binds a kPa raw count as MPa. Convictable from "
                    "EU IDs and caps without Bayer physics.",
                    2,
                    supervisor_error_type="wrong-reject",
                ),
            ),
        ]
    )


'''

NOTES = r'''NOTES = """# Thalamic Trajectory Factory — NOTES-r46

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- Quality: Q=5
- IDs: `ttf-r46-246` … `ttf-r46-250`
- Domains this batch: `ethylene-steam-cracker`, `bayer-digest-train`, `gan-mocvd-reactor`, `clinker-grate-cooler`, `tissue-yankee-dryer`

These five domain slugs sit outside the prompt 8-pool and outside staged r13–r35 occupancy (including r34 coke/chlor-alkali/ASU/EAF/spray-dryer and r35 ORC/ammonia/shooter/laminator/prill). All five plants are invented. Do not restack r12–r35 plants (Marrow-Dock, Vesper-Lattice, Brine-Well, Saddle-Arc, Ashlar-Gait, Nacre-Well, Quern-Forge, Tinder-Box, Whimbrel-Stack, Cinder-Loft, Gable-Retort, Flue-Bank, Soda-Weir, Membrane-Bay, Argon-Cist, Hearth-Knap, Roof-Ring, Slurry-Crown, Atom-Disk, Haber-Knoll, Loam-Hurst, Floe-Helix, Nahcolite-Kettle, Ingot-Cairn, Foehn-Nacelle, Bloom-Weir, Clinker-Spire).

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
| ttf-r46-246 | ethylene-steam-cracker | MODIFY | correct | designed | **−0.46** | process-correct feed clamp; tube-skin split inside 42 ms raster; independent LIF |
| ttf-r46-247 | bayer-digest-train | REJECT | **incorrect (wrong-reject)** | designed | −0.58 | live 1.18 MPa < 1.45 cap; supervisor treats kPa raw 1180 as MPa |
| ttf-r46-248 | gan-mocvd-reactor | REJECT | correct | hil | +0.78 | pyro 986 C beats wafer-TC 1048; hold, do not open TMGa |
| ttf-r46-249 | clinker-grate-cooler | MODIFY | correct | designed | +0.92 | undergrate 8.4 kPa vs staff false-draft; clamp grate 14.0 → 9.0 spm |
| ttf-r46-250 | tissue-yankee-dryer | ACCEPT | correct | simulated | +1.16 | shell 96.0 C vs IR hood glint 128; proposed 1100 m/min already legal |

Gate mix: 1 ACCEPT, 2 MODIFY, 1 correct REJECT, 1 incorrect REJECT (wrong-reject). Provenance: designed×3, simulated×1, hil×1 (Susceptor-HIL SH-2 MOCVD mockup). Intra-batch Jaccard on `state.description` filled at emit.

## Wrong-reject

**ttf-r46-247** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-reject`). Alternate vs odd rounds: even rounds host wrong-reject. This subclass is **EU-mismatch / kPa-as-MPa**, not r12 induced-kV, not r16 reticle-as-wafer, not r18 empty-tank, not r20 oscillation-as-PSV, not r22 class-transplant, not r26 wrong-loop, not r28 wrong-circuit, not r30 stale-firmware, not r32 stale-peak-hold, not r34 wrong-bus. Do not emit a wrong-ACCEPT.

Laterite-Shaw LS-5 / Digest-A DA-2 reads live vessel `1.18 MPa` against a **1.45 MPa** cap. The same tap's kPa-scaled transmitter raw is **1180**. Sidecar arithmetic `1.18 < 1.45` is true. A weak supervisor treats the kPa count as MPa (1180 >> 1.45), REJECTs the 1.80 m³/min blow, and holds the vessel. Convictable without Bayer physics: `evidence.live_MPa < evidence.cap_MPa`, `tx_eu == kPa`, `supervisor_eu == MPa`, `supervisor_compared_as_MPa == 1180`, `executed_action` sets `blow_m3_min=0` without a live over-cap, `raster.routing.table` sends `relay.tx.kPa` → `policy.blow_hold` (weight 0.73) with no positive weight to `policy.blow_go`, and `gate_snn` has `blow_hold` above threshold while `blow_go` is not (`spikes=0`). Recovery: ACCEPT the 1.80 m³/min blow; bind live 1.18 MPa to the 1.45 MPa cap in the same SI. Cost: missed 22 min alumina-quality window (`missed_window_s=1320`).

## Partnered-negative in-window (246)

**ttf-r46-246** is the partnered negative: process-correct MODIFY (tube-metal held 848 C < 860 cap) while the world still charges. Safety −0.58 prices the 28 mm tube-skin split at **22.400 ms**; `task_progress` stays +0.32 because the clamp completed. Inflection `t_us=22400` is tick 5 and is **inside** the 42 ms raster (`22400 ≤ 42000`). Named un-netted loss: 15 min coil isolate (`abort_s=900`). Not folded into process heads.

Independent LIF (the one labeled sidecar sim): `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 46246, stim `[21000, 25000]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.split` 21–25 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks). Tick 6 is bound to a published sidecar (`abort_s`, `missed_window_s`, `cooler_reseq_s`, `survey_hold_s`) and is strictly after the raster window. Inflection `t_us` is an actual tick.

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
| 246 | 6 | +0.32 | −0.58 | −0.16 | +0.02 | −0.06 | −0.46 | 5 (22400) |
| 247 | 6 | −0.20 | −0.10 | −0.22 | −0.12 | +0.06 | −0.58 | 4 (4920) |
| 248 | 6 | +0.10 | +0.40 | +0.12 | +0.10 | +0.06 | +0.78 | 4 (6860) |
| 249 | 6 | +0.34 | +0.30 | +0.14 | +0.10 | +0.04 | +0.92 | 4 (7280) |
| 250 | 6 | +0.44 | +0.34 | +0.18 | +0.12 | +0.08 | +1.16 | 4 (4300) |

Tick-6 sidecar bind: 246 `abort_s=900`, 247 `missed_window_s=1320`, 248 `abort_s=540`, 249 `cooler_reseq_s=420`, 250 `survey_hold_s=280`.

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
| 246 | ethylene-steam-cracker | 72 | 28 | 42 | 85 | 1955 | 0.001955 |
| 247 | bayer-digest-train | 88 | 36 | 24 | 76 | 1748 | 0.001748 |
| 248 | gan-mocvd-reactor | 104 | 22 | 40 | 92 | 2116 | 0.002116 |
| 249 | clinker-grate-cooler | 60 | 44 | 30 | 79 | 1817 | 0.001817 |
| 250 | tissue-yankee-dryer | 84 | 32 | 22 | 59 | 1357 | 0.001357 |

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator (NA / ACh / DA / 5-HT / adenosine), `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms. Non-246 excerpts are kernelized and independent of `spike_events` times (overlap < 0.8).

## Local checks (staging, not raw)

See generator stdout: `check_jsonl` FactoryStaging, `validate_run.check_line`, `dumps_exact_json`, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`, tick sums, refractory, Jaccard.

Never `training_ready`. Never `sim_or_real=real`. Never wrote `outputs/raw/`.

## Residual weaknesses (honest)

1. Only **one** labeled independent LIF (246). The other four excerpts are independent of `spike_events` times but are not declared population sims.
2. Wrong-ACCEPT still absent (guard).
3. Tick-6 sidecar bind is a densification of r14/r16, not a new class.
4. Five domain slugs leave the prompt's 8-item pool; a later round that must stay inside the pool will have to rotate sit-outs instead.
5. 247 wrong-reject is sidecar-convictable (routing `to` / EU IDs) and is a new error *class* vs r34 wrong-bus.
6. 250 ACCEPT is an already-legal proposal confirmed by race order; a later round could pair an ACCEPT with a world charge that does not go negative.

## Next densification target

Labeled LIF on a second record, or an ISI histogram sidecar. Remaining unused wrong-REJECT subclasses include wet-leg / density-uncorrected DP. Wrong-ACCEPT remains structurally absent until a prompt amendment.

Novel coverage: 19.0%
"""
'''


def transform_tail(tail: str) -> str:
    tail = apply_pairs(
        tail,
        [
            ('if rec["id"] == "ttf-r34-186":', 'if rec["id"] == "ttf-r46-246":'),
            ('issues.append("186 missing independent_lif")', 'issues.append("246 missing independent_lif")'),
            ('issues.append("186 inflection outside window")', 'issues.append("246 inflection outside window")'),
            ('issues.append("186 partnered-neg total not negative")', 'issues.append("246 partnered-neg total not negative")'),
            ('if rec["meta"]["round"] != 34:', 'if rec["meta"]["round"] != 46:'),
            ('if rec["id"] == "ttf-r34-187":', 'if rec["id"] == "ttf-r46-247":'),
            ('if "policy.cell_go" in table_tos:', 'if "policy.blow_go" in table_tos:'),
            ('issues.append("187 routing has cell_go")', 'issues.append("247 routing has blow_go")'),
            ('if "policy.cell_hold" not in table_tos:', 'if "policy.blow_hold" not in table_tos:'),
            ('issues.append("187 missing cell_hold routing")', 'issues.append("247 missing blow_hold routing")'),
            ('or wrong[0]["id"] != "ttf-r34-187":', 'or wrong[0]["id"] != "ttf-r46-247":'),
            ('if hil != ["ttf-r34-188"]:', 'if hil != ["ttf-r46-248"]:'),
            ('expected_ids = [f"ttf-r34-{n}" for n in range(186, 191)]',
             'expected_ids = [f"ttf-r46-{n}" for n in range(246, 251)]'),
            ('BATCH_PATH, "batch-r34.jsonl", staging=FactoryStaging(enabled=True)',
             'BATCH_PATH, "batch-r46.jsonl", staging=FactoryStaging(enabled=True)'),
            ('errs, kind = check_line(rec, f"batch-r34.jsonl:{i}", factory_staging=True)',
             'errs, kind = check_line(rec, f"batch-r46.jsonl:{i}", factory_staging=True)'),
            (
                "records = [record_186(), record_187(), record_188(), record_189(), record_190()]",
                "records = [record_246(), record_247(), record_248(), record_249(), record_250()]",
            ),
        ],
        "tail",
    )
    start = tail.index("NOTES = ")
    end = tail.index("\ndef run_pipelines")
    tail = tail[:start] + NOTES + tail[end:]
    return tail


def main() -> None:
    src = SRC.read_text()
    i186 = src.index("def record_186():")
    i187 = src.index("def record_187():")
    i188 = src.index("def record_188():")
    i189 = src.index("def record_189():")
    i190 = src.index("def record_190():")
    itok = src.index("def tokenize(")
    head = transform_head(src[:i186])
    rec246 = apply_pairs(src[i186:i187], REC246_PAIRS, "rec246")
    rec248 = apply_pairs(src[i188:i189], REC248_PAIRS, "rec248")
    rec249 = apply_pairs(src[i189:i190], REC249_PAIRS, "rec249")
    rec250 = apply_pairs(src[i190:itok], REC250_PAIRS, "rec250")
    tail = transform_tail(src[itok:])
    out = head + rec246 + RECORD_247 + rec248 + rec249 + rec250 + tail
    rec_span = out[out.index("def record_246():") : out.index("def tokenize(")]
    leftover = []
    for needle in (
        "ttf-r34",
        "record_186",
        "record_187",
        "record_188",
        "record_189",
        "record_190",
        "/tmp/ttf-r34",
        "batch-r34",
        "NOTES-r34",
        "Gable-Retort",
        "Soda-Weir",
        "Argon-Cist",
        "Hearth-Knap",
        "Slurry-Crown",
        "coke-oven-battery",
        "chlor-alkali-membrane",
        "air-separation-coldbox",
        "eaf-arc-furnace",
        "spray-dryer-tower",
    ):
        if needle in rec_span or (needle.startswith("ttf-r34") and needle in out) or needle in (
            "record_186",
            "/tmp/ttf-r34",
            "batch-r34",
            "NOTES-r34",
        ) and needle in out:
            if needle in rec_span:
                leftover.append(needle)
            elif needle in ("ttf-r34", "record_186", "record_187", "record_188", "record_189", "record_190", "/tmp/ttf-r34", "batch-r34", "NOTES-r34") and needle in out:
                leftover.append(f"file:{needle}")
    DST.write_text(out)
    print(f"wrote {DST} bytes={len(out)} leftover={leftover}")


if __name__ == "__main__":
    main()
