#!/usr/bin/env python3
"""Patch cloned gen_r47.py with r47 domains, plants, and lagged-tag wrong-modify."""
from pathlib import Path

P = Path("/tmp/ttf-r47/gen_r47.py")
src = P.read_text()

src = src.replace(
    '''THIS_DOMAINS = {
    "geothermal-binary-ORC",
    "ammonia-converter",
    "foundry-core-shooter",
    "photovoltaic-laminator",
    "urea-prill-tower",
}''',
    '''THIS_DOMAINS = {
    "visbreaker-soaker",
    "electrode-calender",
    "longwall-shearer",
    "nonwoven-spunbond",
    "gypsum-kettle",
}''',
)

# extra occupancy that landed after r35 clone
EXTRA_BANNED = '''    "visbreaker-soaker-USED-GUARD",
    "mine-skip-winder",
    "geothermal-flash-separator",
    "HRSG-attemperator",
    "overland-conveyor",
    "mushroom-compost-tunnel",
    "fcc-riser-regenerator",
    "mri-helium-quench",
    "chocolate-conche",
    "uht-sterilizer",
    "ore-sinter-strand",
    "fcc-riser",
    "nickel-electrowinning",
    "hydrogen-PSA-bed",
    "cold-tandem-mill",
    "sulfur-claus-furnace",
    "pvc-suspension-kettle",
    "corrugator-singlefacer",
    "once-through-steam-gen",
    "stenter-frame",
    "delayed-coker",
    "tissue-yankee-dryer",
    "copper-flash-smelter",
    "galvanize-kettle",
    "hot-isostatic-press",
    "sinter-strand",
    "cold-pilger-mill",
    "yankee-tissue-dryer",
    "osb-hot-press",
    "midrex-dri-shaft",
    "carbon-black-reactor",
    "asphalt-drum-mixer",
    "esr-ingot-melt",
    "hip-isostatic-press",
    "fcc-riser-cracker",
    "galvanize-pot-line",
    "ethylene-cracker-coil",
    "steam-methane-reformer",
    "polyethylene-loop-reactor",
    "glass-fiber-bushing",
    "brick-tunnel-kiln",
    "stacker-reclaimer-boom",
    "copper-electrorefining",
    "oil-pipeline-pig-trap",
    "Bayer-digester",
'''
if "mine-skip-winder" not in src.split("BANNED_DOMAINS")[1][:4000]:
    src = src.replace(
        '    "cement-precalciner",\n}',
        '    "cement-precalciner",\n' + EXTRA_BANNED + "}",
        1,
    )

EXTRA_PLANTS = '''    "Winze-Capstan",
    "Fumarole-Dyke",
    "Spray-Header",
    "Flight-Furlong",
    "Prill-Garth",
    "Peat-Rake",
    "Zeolite-Knap",
    "Dewar-Nave",
    "Cocoa-Noll",
    "Still-Croft",
    "Pyrite-Hood",
    "Zeolite-Riser",
    "Laterite-Vat",
    "Adiabat-Sieve",
    "Finisher-Coil",
    "Pyrite-Gill",
    "Vinyl-Garth",
    "Flute-Wick",
    "Otter-Brae",
    "Tenter-Howe",
    "Bitumen-Cairn",
    "Crepe-Nave",
    "Matte-Fell",
    "Spelter-Holt",
    "Isostat-Wold",
    "Pallet-Rigg",
    "Mandrel-Sike",
    "Yankee-Crest",
    "Crepe-Cap",
    "Bustle-Shaw",
    "Gorse-Weir",
    "Haber-Knoll",
    "Loam-Hurst",
    "Lamina-Kame",
    "Prill-Flue",
    "Olefin-Noll",
    "Methane-Howe",
    "Lampblack-Fen",
    "Flue-Cairn",
    "Bauxite-Naze",
    "Cathode-Howe",
    "Scraper-Ness",
'''
if "Winze-Capstan" not in src:
    src = src.replace(
        '    "Amber-Arm",\n)',
        '    "Amber-Arm",\n' + EXTRA_PLANTS + ")",
        1,
    )

src = src.replace(
    'channels = ["lif.clamp" if t < 20000 else "lif.silica" for t, _ in picked]',
    'channels = ["lif.clamp" if t < 20000 else "lif.coke" for t, _ in picked]',
)
src = src.replace(
    "Neurons 0-11 carry +0.64 isobutane-pump clamp bias; stim 20-23 ms is the silica-plate burst.",
    "Neurons 0-11 carry +0.64 residue-pump clamp bias; stim 20-23 ms is the coke-lens burst.",
)

def slice_fn(text, name, nxt):
    a = text.index(f"def {name}():")
    b = text.index(f"def {nxt}(")
    return a, b, text[a:b]

a, b, body = slice_fn(src, "record_251", "record_252")
repl_251 = [
    ("Gorse-Weir GW-4 binary island", "Tar-Brae TB-4 visbreaker soaker"),
    ("Gorse-Weir GW-4", "Tar-Brae TB-4"),
    ("evaporator shell 14.8 bar", "soaker shell 14.8 bar"),
    ("12.5 bar license, isobutane pump still at 42 kg/s. Turbine encoder leftover",
     "12.5 bar license, residue pump still at 42 kg/s. Heater encoder leftover"),
    ("Latch the working-fluid pump to 28 kg/s on the PT win",
     "Latch the residue pump to 28 kg/s on the PT win"),
    ("Plate P-11 already carries a silica lens", "Coil C-11 already carries a coke lens"),
    ("not PT or the encoder.", "not PT or the heater encoder."),
    ("geothermal-binary-ORC", "visbreaker-soaker"),
    ("Finish the GW-4 charge with evaporator pressure <= 12.5 bar and without parting "
     "plate P-11.",
     "Finish the TB-4 soak with soaker pressure <= 12.5 bar and without packing coil C-11."),
    ("pt.evap.bar 14.8 bar", "pt.soaker.bar 14.8 bar"),
    ("enc.turb.rpm 1.8 pct residual", "enc.heater.pct 1.8 pct residual"),
    ("Pressure-first latches working-fluid clamp 42 -> 28 kg/s; rpm-first keeps",
     "Pressure-first latches residue clamp 42 -> 28 kg/s; residual-first keeps"),
    ("one 2 kHz evaporator-PT slot minus turbine-encoder group delay",
     "one 2 kHz soaker-PT slot minus heater-encoder group delay"),
    ("on this binary-cycle bus.", "on this visbreaker bus."),
    ("PT 28 + encoder 32", "PT 28 + heater 32"),
    ("evaporator shell PT, 2 kHz, 28 us timestamp jitter",
     "soaker shell PT, 2 kHz, 28 us timestamp jitter"),
    ("turbine RPM encoder 0-3600, 32 us jitter",
     "heater residual encoder 0-100, 32 us jitter"),
    ("plate AE puck, 50 kHz (context)", "coil AE puck, 50 kHz (context)"),
    ("brine-inlet RTD (context)", "soaker-inlet RTD (context)"),
    ("evap_cap_bar", "soaker_cap_bar"),
    ("observed_pt_bar", "observed_pt_bar"),
    ("proposed_wf_kg_s", "proposed_res_kg_s"),
    ("turb_rpm_residual_pct", "heater_residual_pct"),
    ("ORC-Train B indexed onto GW-4; isobutane pump 42 kg/s armed.",
     "Soak-Train B indexed onto TB-4; residue pump 42 kg/s armed."),
    ("Evaporator PT 14.8 bar; turbine residual 1.8 percent.",
     "Soaker PT 14.8 bar; heater residual 1.8 percent."),
    ("Encoder precursor at 1.210 ms; PT warm-start 14.8 bar.",
     "Heater-encoder precursor at 1.210 ms; PT warm-start 14.8 bar."),
    ("opens on the binary-cycle bus.", "opens on the visbreaker bus."),
    ("pt.evap.bar 14.8 bar at 4.960 ms (winner).",
     "pt.soaker.bar 14.8 bar at 4.960 ms (winner)."),
    ("enc.turb.rpm 1.8 pct at 5.118 ms (loser by 158 us).",
     "enc.heater.pct 1.8 pct at 5.118 ms (loser by 158 us)."),
    ("MODIFY clamp 42 -> 28 kg/s.", "MODIFY clamp residue 42 -> 28 kg/s."),
    ("At 21.400 ms a seated silica lens parts plate P-11; AE burst.",
     "At 21.400 ms a seated coke lens packs coil C-11; AE burst."),
    ("16 min plate swap (abort_s=960)", "16 min coil decoke (abort_s=960)"),
    ("cruise_wf_pump", "cruise_res_pump"),
    ("wf_kg_s", "res_kg_s"),
    ('("train", "ORC-Train-B")', '("train", "Soak-Train-B")'),
    ("evap_pt_bar", "soaker_pt_bar"),
    ("predicted_unclamped_next_bar", "predicted_unclamped_next_bar"),
    ("42 kg/s isobutane", "42 kg/s residue"),
    ("1.8 percent RPM residual looks like turbine "
                "spin-up, not an evaporator over-cap, and plate P-11 is treated as still sealed.",
     "1.8 percent heater residual looks like still firing "
                "up, not a soaker over-cap, and coil C-11 is treated as still open."),
    ("Evaporator PT 14.8 bar won by 158 us, so the working cap is already loaded, not "
                "still spinning up. Holding 42 kg/s predicts next-sample 13.6 bar > 12.5 cap. "
                "MODIFY: isobutane 42 -> 28 kg/s. Observed after clamp 12.1 bar < 12.5. A full "
                "REJECT is not indicated: a clean charge accepts 28 kg/s.",
     "Soaker PT 14.8 bar won by 158 us, so the working cap is already loaded, not "
                "still firing up. Holding 42 kg/s predicts next-sample 13.6 bar > 12.5 cap. "
                "MODIFY: residue 42 -> 28 kg/s. Observed after clamp 12.1 bar < 12.5. A full "
                "REJECT is not indicated: a clean soak accepts 28 kg/s."),
    ("evap_pressure_bar", "soaker_pressure_bar"),
    ("clamped_wf_kg_s", "clamped_res_kg_s"),
    ("clamped_wf_pump", "clamped_res_pump"),
    ("MODIFY: isobutane 42 -> 28 kg/s. Process-correct vs the 12.5 bar cap. Plate P-11 "
                "still parts at 21.400 ms.",
     "MODIFY: residue 42 -> 28 kg/s. Process-correct vs the 12.5 bar cap. Coil C-11 "
                "still packs at 21.400 ms."),
    ("Process-correct MODIFY held evaporator pressure at 12.1 bar. At 21.400 ms a silica "
                "lens already seated on plate P-11 parted the exchanger. Clamp reduced dump energy; "
                "it did not prevent the burst. Partnered negative: process heads stay honest; world "
                "loss is named, not netted.",
     "Process-correct MODIFY held soaker pressure at 12.1 bar. At 21.400 ms a coke "
                "lens already seated on coil C-11 packed the tube. Clamp reduced dump energy; "
                "it did not prevent the pack. Partnered negative: process heads stay honest; world "
                "loss is named, not netted."),
    ('("evaporator", "clamp executed; peak 12.1 bar < 12.5 cap")',
     '("soaker", "clamp executed; peak 12.1 bar < 12.5 cap")'),
    ('("plate", "parted at 21.400 ms")', '("coil", "packed at 21.400 ms")'),
    ('("repair", "16 min plate swap (abort_s=960)")',
     '("repair", "16 min coil decoke (abort_s=960)")'),
    ('("mission", "GW-4 charge incomplete this circuit")',
     '("mission", "TB-4 soak incomplete this circuit")'),
    ("Neither evaporator PT nor turbine RPM predicted the seated silica lens; ae.plate.crack is a new channel at 21.400 ms, 15.740 ms after the gate, still inside the 40 ms raster.",
     "Neither soaker PT nor heater residual predicted the seated coke lens; ae.coil.coke is a new channel at 21.400 ms, 15.740 ms after the gate, still inside the 40 ms raster."),
    ("16 min plate swap. Named un-netted loss, not folded into task_progress.",
     "16 min coil decoke. Named un-netted loss, not folded into task_progress."),
    ("16 min plate swap after P-11 part. Safety head -0.62 prices the burst; "
                "task_progress stays +0.32 because the isobutane clamp completed under the 12.5 bar "
                "cap. World loss is named here, not subtracted from process heads.",
     "16 min coil decoke after C-11 pack. Safety head -0.62 prices the burst; "
                "task_progress stays +0.32 because the residue clamp completed under the 12.5 bar "
                "cap. World loss is named here, not subtracted from process heads."),
    ('("winner", "pt.evap.bar (4.960 ms, 14.8 bar)")',
     '("winner", "pt.soaker.bar (4.960 ms, 14.8 bar)")'),
    ('("loser", "enc.turb.rpm (5.118 ms, 1.8 pct)")',
     '("loser", "enc.heater.pct (5.118 ms, 1.8 pct)")'),
    ("42 kg/s; predicted next-sample 13.6 bar would have exceeded the "
                            "12.5 bar cap even without the plate burst. The MODIFY is still the "
                            "correct process. The burst is a later world charge either way, cheaper "
                            "with the clamp than without.",
     "42 kg/s; predicted next-sample 13.6 bar would have exceeded the "
                            "12.5 bar cap even without the coke pack. The MODIFY is still the "
                            "correct process. The pack is a later world charge either way, cheaper "
                            "with the clamp than without."),
    ("40 ms raster. The correct MODIFY at 5.660 ms is in the same excerpt. Do not put "
                "inflection on the abort_s=960 swap tick.",
     "40 ms raster. The correct MODIFY at 5.660 ms is in the same excerpt. Do not put "
                "inflection on the abort_s=960 decoke tick."),
    ('spike("enc.turb.rpm"', 'spike("enc.heater.pct"'),
    ('spike("pt.evap.bar"', 'spike("pt.soaker.bar"'),
    ('spike("ae.plate.crack"', 'spike("ae.coil.coke"'),
    ('"thalamic-relay.evap-pt"', '"thalamic-relay.soaker-pt"'),
    ('"spikenaut.policy.wf-clamp"', '"spikenaut.policy.res-clamp"'),
    ('("relay.pt.evap", "policy.wf_clamp", 0.68)',
     '("relay.pt.soaker", "policy.res_clamp", 0.68)'),
    ('("relay.enc.turb", "policy.rpm_hold", 0.30)',
     '("relay.enc.heater", "policy.heater_hold", 0.30)'),
    ('("relay.ae.plate", "policy.wf_clamp", -0.42)',
     '("relay.ae.coil", "policy.res_clamp", -0.42)'),
    ("trace that still covers the 21.400 ms plate burst",
     "trace that still covers the 21.400 ms coke pack"),
    ('pop_budget("wf_clamp"', 'pop_budget("res_clamp"'),
    ('pop_budget("rpm_hold"', 'pop_budget("heater_hold"'),
    ("evaporator PT beats turbine RPM by 158 us; correct "
                "MODIFY still eats an in-window silica-plate part (partnered negative total -0.46)",
     "soaker PT beats heater residual by 158 us; correct "
                "MODIFY still eats an in-window coke-lens pack (partnered negative total -0.46)"),
    ("Named plate "
                    "swap (abort_s=960) is not netted into task_progress.",
     "Named coil "
                    "decoke (abort_s=960) is not netted into task_progress."),
    ("16 min plate swap.", "16 min coil decoke."),
]
for old, new in repl_251:
    if old not in body:
        print("251 MISSING", old[:90].replace("\n", " "))
    else:
        body = body.replace(old, new)
src = src[:a] + body + src[b:]

# 253 longwall
a, b, body = slice_fn(src, "record_253", "record_254")
repl_253 = [
    ("Loam-Hurst LH-HIL Shooter S-8 magazine is over-pressure: blow PT 6.80 bar against "
                "a 5.50 bar fire license. Binder pyrometer 42 C is 48 K under the 90 C gel abort. "
                "Freeze the shot on the blow win; treating the cold IR as a permit would fire 0.45 s "
                "into an over-pressure box.",
     "Shear-Wold SW-HIL Drum D-8 haul is over-pressure: haul PT 6.80 MPa against "
                "a 5.50 MPa haul license. Pick IR 42 C is 48 K under the 90 C pick abort. "
                "Freeze the drum on the haul win; treating the cold IR as a permit would run 0.45 s "
                "into an over-haul face."),
    ("foundry-core-shooter", "longwall-shearer"),
    ("Keep the shot unfired unless blow PT <= 5.50 bar; do not treat 42 C binder IR as "
                "a gelling permit.",
     "Keep the drum unfired unless haul PT <= 5.50 MPa; do not treat 42 C pick IR as "
                "a cutting permit."),
    ("pt.blow.bar 6.80 bar", "pt.haul.MPa 6.80 MPa"),
    ("ir.binder.C 42 C", "ir.pick.C 42 C"),
    ("Blow-first REJECTs the 0.45 s shot (6.80 > 5.50 bar cap). IR-first would "
                            "ACCEPT on a cold-box reading mistaken for a gel-ready permit.",
     "Haul-first REJECTs the 0.45 s drum (6.80 > 5.50 MPa cap). IR-first would "
                            "ACCEPT on a cold-pick reading mistaken for a cut-ready permit."),
    ("340 us = one blow-PT sample minus binder-IR group delay on this HIL "
                            "core-shooter bus.",
     "340 us = one haul-PT sample minus pick-IR group delay on this HIL "
                            "shearer bus."),
    ("would have kept the 0.45 s shot armed on 42 C binder.",
     "would have kept the 0.45 s drum armed on 42 C pick."),
    ("blow-line PT, 5 kHz burst, 26 us jitter",
     "haul-line PT, 5 kHz burst, 26 us jitter"),
    ("binder IR pyrometer, 2 kHz, 32 us jitter",
     "pick IR pyrometer, 2 kHz, 32 us jitter"),
    ("box thermocouple (context)", "face thermocouple (context)"),
    ("HIL magazine-pressure monitor (context)",
     "HIL AFC-pressure monitor (context)"),
    ("blow_cap_bar", "haul_cap_MPa"),
    ("observed_blow_bar", "observed_haul_MPa"),
    ("binder_C", "pick_C"),
    ("binder_abort_C", "pick_abort_C"),
    ("proposed_shot_s", "proposed_drum_s"),
    ('("pad", "Loam-Hurst LH-HIL core-shooter bench")',
     '("pad", "Shear-Wold SW-HIL longwall shearer bench")'),
    ("blow-pressure burst + cold-binder IR packet",
     "haul-pressure burst + cold-pick IR packet"),
    ("Hardware-in-the-loop foundry shooter. Invented plant; not a live mold line.",
     "Hardware-in-the-loop longwall shearer. Invented plant; not a live coal face."),
    ("Shooter S-8 on the LH-HIL bench; 0.45 s shot armed.",
     "Drum D-8 on the SW-HIL bench; 0.45 s drum armed."),
    ("Cold-binder IR packet injected 110-150 us before the blow-PT volume.",
     "Cold-pick IR packet injected 110-150 us before the haul-PT volume."),
    ("Box-temp precursor at 1.210 ms.", "Face-temp precursor at 1.210 ms."),
    ("pt.blow.bar 6.80 bar at 6.210 ms (winner).",
     "pt.haul.MPa 6.80 MPa at 6.210 ms (winner)."),
    ("ir.binder.C 42 C at 6.368 ms (loser by 158 us).",
     "ir.pick.C 42 C at 6.368 ms (loser by 158 us)."),
    ("REJECT hold shot 0 s; do not fire.",
     "REJECT hold drum 0 s; do not cut."),
    ("Blow pressure remains over the 5.50 bar cap this cycle.",
     "Haul pressure remains over the 5.50 MPa cap this cycle."),
    ("Binder 42 C stays a cold-box artifact, not a gel-ready permit.",
     "Pick 42 C stays a cold-pick artifact, not a cut-ready permit."),
    ("7 min box dump and magazine retune.",
     "7 min face dump and AFC retune."),
    ("shot_045", "drum_045"),
    ("shot_s", "drum_s"),
    ("blow_bar", "haul_MPa"),
    ("blow_cap_bar", "haul_cap_MPa"),  # may already be replaced
    ("Planner proposes a 0.45 s shot because binder 42 C looks like a cold, ungelled "
                "box; it has not yet bound blow 6.80 bar to the 5.50 bar fire cap.",
     "Planner proposes a 0.45 s drum because pick 42 C looks like a cold, uncut "
                "face; it has not yet bound haul 6.80 MPa to the 5.50 MPa haul cap."),
    ("Blow PT 6.80 bar won by 158 us, so the fire cap is already violated. Binder 42 C "
                "is under the 90 C abort and is a cold-box reading. REJECT: shot 0 s, fire false. "
                "A MODIFY that keeps the magazine armed is not indicated: next-sample blow is 6.9 bar.",
     "Haul PT 6.80 MPa won by 158 us, so the haul cap is already violated. Pick 42 C "
                "is under the 90 C abort and is a cold-pick reading. REJECT: drum 0 s, fire false. "
                "A MODIFY that keeps the AFC armed is not indicated: next-sample haul is 6.9 MPa."),
    ("executed_shot_s", "executed_drum_s"),
    ("shot_hold", "drum_hold"),
    ("REJECT: shot 0.45 -> 0 s. Blow cap held. Binder IR unused as a go signal.",
     "REJECT: drum 0.45 -> 0 s. Haul cap held. Pick IR unused as a go signal."),
    ("Correct REJECT held S-8 at 0 s. Blow 6.80 bar was over the 5.50 bar cap; binder "
                "42 C was a cold-box artifact. 7 min box dump (abort_s=420).",
     "Correct REJECT held D-8 at 0 s. Haul 6.80 MPa was over the 5.50 MPa cap; pick "
                "42 C was a cold-pick artifact. 7 min face dump (abort_s=420)."),
    ('("shot", "held; 0 s")', '("drum", "held; 0 s")'),
    ('("blow", "still 6.80 bar > 5.50 cap")', '("haul", "still 6.80 MPa > 5.50 cap")'),
    ('("binder", "42 C unused")', '("pick", "42 C unused")'),
    ('("mission", "fire deferred")', '("mission", "cut deferred")'),
    ("Cold-binder IR arrived 158 us after blow PT; reversing that order would have kept the shot armed over the fire cap.",
     "Cold-pick IR arrived 158 us after haul PT; reversing that order would have kept the drum armed over the haul cap."),
    ("7 min box dump and magazine-pressure retune.",
     "7 min face dump and AFC-pressure retune."),
    ('("winner", "pt.blow.bar (6.210 ms, 6.80 bar)")',
     '("winner", "pt.haul.MPa (6.210 ms, 6.80 MPa)")'),
    ('("loser", "ir.binder.C (6.368 ms, 42 C)")',
     '("loser", "ir.pick.C (6.368 ms, 42 C)")'),
    ("0.45 s shot armed on 42 C binder while blow stayed over 5.50 bar.",
     "0.45 s drum armed on 42 C pick while haul stayed over 5.50 MPa."),
    ('spike("tc.box.ctx"', 'spike("tc.face.ctx"'),
    ('spike("pt.blow.bar"', 'spike("pt.haul.MPa"'),
    ('spike("ir.binder.C"', 'spike("ir.pick.C"'),
    ('"thalamic-relay.blow-pt"', '"thalamic-relay.haul-pt"'),
    ('"spikenaut.policy.shot-hold"', '"spikenaut.policy.drum-hold"'),
    ('("relay.pt.blow", "policy.shot_hold", 0.72)',
     '("relay.pt.haul", "policy.drum_hold", 0.72)'),
    ('("relay.ir.binder", "policy.shot_go", 0.23)',
     '("relay.ir.pick", "policy.drum_go", 0.23)'),
    ("cap_stdp; DA tags the blow-cap bind at the PT win",
     "cap_stdp; DA tags the haul-cap bind at the PT win"),
    ('pop_budget("shot_hold"', 'pop_budget("drum_hold"'),
    ('pop_budget("shot_go"', 'pop_budget("drum_go"'),
    ('pop_budget("blow_ctx"', 'pop_budget("haul_ctx"'),
    ("Loam-Hurst LH-HIL / Shooter S-8: blow 6.80 bar beats binder IR 42 C; correct "
                "REJECT holds the shot",
     "Shear-Wold SW-HIL / Drum D-8: haul 6.80 MPa beats pick IR 42 C; correct "
                "REJECT holds the drum"),
    ("Correct REJECT. Blow 6.80 > 5.50 bar cap; binder 42 C is cold-box, not gel. ",
     "Correct REJECT. Haul 6.80 > 5.50 MPa cap; pick 42 C is cold-pick, not cut. "),
    ('"blow-vs-binder"', '"haul-vs-pick"'),
    ('"cold-box-artifact"', '"cold-pick-artifact"'),
    ("Teaches that a cold-binder IR packet can lose to blow PT inside a 340 us "
                    "window; reversing 158 us would have kept the shot armed over the fire cap.",
     "Teaches that a cold-pick IR packet can lose to haul PT inside a 340 us "
                    "window; reversing 158 us would have kept the drum armed over the haul cap."),
]
for old, new in repl_253:
    if old not in body:
        print("253 MISSING", old[:100].replace("\n", " "))
    else:
        body = body.replace(old, new)
src = src[:a] + body + src[b:]

a, b, body = slice_fn(src, "record_254", "record_255")
repl_254 = [
    ("Lamina-Kame LK-3 Press PL-2 is already in an 8.0 min EVA dwell. Gel pyrometer "
                "118 C is 27 K shy of the 145 C ceiling. Chamber vacuum 0.80 mbar is leftover "
                "pump-down, not a bubble flag. Gel-led ACCEPT keeps the dwell; a vacuum-led abort "
                "would scrap a legal sheet.",
     "Web-Fen WF-6 Beam B-2 is already in an 8.0 kg/h spunbond. Die pyrometer "
                "118 C is 27 K shy of the 145 C ceiling. Gauge 0.80 mil is leftover "
                "web-start, not a hole flag. Die-led ACCEPT keeps the beam; a gauge-led abort "
                "would scrap a legal web."),
    ("photovoltaic-laminator", "nonwoven-spunbond"),
    ("Hold an 8.0 min dwell while EVA gel stays <= 145 C; do not abort on a 0.80 mbar "
                "pump residual.",
     "Hold an 8.0 kg/h beam while die stays <= 145 C; do not abort on a 0.80 mil "
                "web residual."),
    ("ir.eva.C 118 C", "ir.die.C 118 C"),
    ("vac.chamber.mbar 0.80 mbar residual", "gauge.web.mil 0.80 mil residual"),
    ("Gel-first ACCEPTS the 8.0 min dwell (already under 145 C). Vacuum-first "
                            "would REJECT on a pump residual.",
     "Die-first ACCEPTS the 8.0 kg/h beam (already under 145 C). Gauge-first "
                            "would REJECT on a web residual."),
    ("400 us = one EVA-IR sample minus vacuum-tap group delay on this "
                            "laminator bus.",
     "400 us = one die-IR sample minus gauge-tap group delay on this "
                            "spunbond bus."),
    ("would have REJECTED a legal 8.0 min dwell.",
     "would have REJECTED a legal 8.0 kg/h beam."),
    ("EVA gel IR, 2 kHz, 28 us jitter", "die IR, 2 kHz, 28 us jitter"),
    ("chamber vacuum tap 0-10 mbar, 34 us jitter",
     "web gauge tap 0-10 mil, 34 us jitter"),
    ("platen encoder (context)", "beam encoder (context)"),
    ("membrane RTD (context)", "quench RTD (context)"),
    ("gel_cap_C", "die_cap_C"),
    ("observed_gel_C", "observed_die_C"),
    ("vac_mbar", "gauge_mil"),
    ("vac_abort_mbar", "gauge_abort_mil"),
    ("proposed_dwell_min", "proposed_beam_kg_h"),
    ("lumped EVA gel + 1-D vacuum decay, seed 47254; 6 layer nodes, "
                            "12 min pump-down; NOT CFD, NOT a live laminator",
     "lumped die + 1-D web decay, seed 47254; 6 filament nodes, "
                            "12 min beam-up; NOT CFD, NOT a live spunbond line"),
    ("Linear gel kinetics; no bubble nucleation. Raster is kernelized events, "
                            "not an independent LIF.",
     "Linear die kinetics; no hole nucleation. Raster is kernelized events, "
                            "not an independent LIF."),
    ("Press PL-2 indexed on LK-3; 8.0 min dwell armed.",
     "Beam B-2 indexed on WF-6; 8.0 kg/h beam armed."),
    ("Gel IR 118 C; vacuum residual 0.80 mbar.",
     "Die IR 118 C; gauge residual 0.80 mil."),
    ("Platen-encoder precursor at 1.080 ms.",
     "Beam-encoder precursor at 1.080 ms."),
    ("ir.eva.C 118 C at 5.080 ms (winner).",
     "ir.die.C 118 C at 5.080 ms (winner)."),
    ("vac.chamber.mbar 0.80 mbar at 5.246 ms (loser by 166 us).",
     "gauge.web.mil 0.80 mil at 5.246 ms (loser by 166 us)."),
    ("ACCEPT 8.0 min; executed identical to proposed.",
     "ACCEPT 8.0 kg/h; executed identical to proposed."),
    ("Dwell continues; peak gel 121 C < 145 cap.",
     "Beam continues; peak die 121 C < 145 cap."),
    ("Vacuum 0.80 mbar remains a pump residual, not a gel loop.",
     "Gauge 0.80 mil remains a web residual, not a hole loop."),
    ("5 min coupon peel on the next sheet.",
     "5 min coupon peel on the next beam."),
    ("dwell_80", "beam_80"),
    ("dwell_min", "beam_kg_h"),
    ("8.0", "8.0"),
    ("platen_kN", "nip_kN"),
    ("gel_C", "die_C"),
    ("gel_cap_C", "die_cap_C"),
    ("Planner proposes an 8.0 min dwell because gel 118 C is under the 145 C cap; "
                "vacuum 0.80 mbar is under the 4.0 abort and is treated as pump residual, not gel.",
     "Planner proposes an 8.0 kg/h beam because die 118 C is under the 145 C cap; "
                "gauge 0.80 mil is under the 4.0 abort and is treated as web residual, not a hole."),
    ("Gel 118 C won by 166 us and is under the 145 C cap. Vacuum 0.80 mbar is under "
                "the 4.0 mbar abort. ACCEPT the already-legal 8.0 min dwell. A REJECT on pump "
                "residual would stall a legal laminate.",
     "Die 118 C won by 166 us and is under the 145 C cap. Gauge 0.80 mil is under "
                "the 4.0 mil abort. ACCEPT the already-legal 8.0 kg/h beam. A REJECT on web "
                "residual would stall a legal spunbond."),
    ("executed_dwell_min", "executed_beam_kg_h"),
    ("ACCEPT: dwell 8.0 min unchanged. Gel stayed 118-121 C < 145 cap.",
     "ACCEPT: beam 8.0 kg/h unchanged. Die stayed 118-121 C < 145 cap."),
    ("Correct ACCEPT kept PL-2 at 8.0 min. Gel 118 C was under the 145 C cap; vacuum "
                "0.80 mbar was pump residual. 5 min coupon peel (survey_s=300).",
     "Correct ACCEPT kept B-2 at 8.0 kg/h. Die 118 C was under the 145 C cap; gauge "
                "0.80 mil was web residual. 5 min coupon peel (survey_s=300)."),
    ('("dwell", "8.0 min continued")', '("beam", "8.0 kg/h continued")'),
    ('("gel", "peak 121 C < 145 cap")', '("die", "peak 121 C < 145 cap")'),
    ('("vacuum", "0.80 mbar unused as a hold")', '("gauge", "0.80 mil unused as a hold")'),
    ('("mission", "laminate continues")', '("mission", "spunbond continues")'),
    ("Vacuum residual arrived 166 us after the gel IR; reversing that order would have REJECTED a legal dwell.",
     "Gauge residual arrived 166 us after the die IR; reversing that order would have REJECTED a legal beam."),
    ("5 min coupon peel on the next sheet, not a gel event.",
     "5 min coupon peel on the next beam, not a hole event."),
    ('("winner", "ir.eva.C (5.080 ms, 118 C)")',
     '("winner", "ir.die.C (5.080 ms, 118 C)")'),
    ('("loser", "vac.chamber.mbar (5.246 ms, 0.80 mbar)")',
     '("loser", "gauge.web.mil (5.246 ms, 0.80 mil)")'),
    ("an already-legal 8.0 min dwell on a 0.80 mbar pump residual.",
     "an already-legal 8.0 kg/h beam on a 0.80 mil web residual."),
    ('spike("enc.press.ctx"', 'spike("enc.beam.ctx"'),
    ('spike("ir.eva.C"', 'spike("ir.die.C"'),
    ('spike("vac.chamber.mbar"', 'spike("gauge.web.mil"'),
    ('"thalamic-relay.eva-ir"', '"thalamic-relay.die-ir"'),
    ('"spikenaut.policy.dwell-go"', '"spikenaut.policy.beam-go"'),
    ('("relay.ir.eva", "policy.dwell_go", 0.69)',
     '("relay.ir.die", "policy.beam_go", 0.69)'),
    ('("relay.vac.chamber", "policy.vac_hold", 0.27)',
     '("relay.gauge.web", "policy.gauge_hold", 0.27)'),
    ("gel_stdp; 5-HT tags the already-legal gel bind",
     "die_stdp; 5-HT tags the already-legal die bind"),
    ('pop_budget("dwell_go"', 'pop_budget("beam_go"'),
    ('pop_budget("vac_hold"', 'pop_budget("gauge_hold"'),
    ('pop_budget("gel_ctx"', 'pop_budget("die_ctx"'),
    ("Lamina-Kame LK-3 / Press PL-2: EVA gel 118 C beats vacuum 0.80 mbar by 166 us; "
                "correct ACCEPT of an already-legal 8.0 min dwell",
     "Web-Fen WF-6 / Beam B-2: die 118 C beats gauge 0.80 mil by 166 us; "
                "correct ACCEPT of an already-legal 8.0 kg/h beam"),
    ("Correct ACCEPT. Gel 118 < 145 cap; vacuum is pump residual, not gel. ",
     "Correct ACCEPT. Die 118 < 145 cap; gauge is web residual, not a hole. "),
    ('"laminator"', '"spunbond"'),
    ('"gel-vs-vacuum"', '"die-vs-gauge"'),
    ('"simulated-gel"', '"simulated-die"'),
    ("Teaches that a vacuum-tap residual can lose to EVA gel IR inside a 400 us "
                    "window; reversing 166 us would have REJECTED an already-legal dwell.",
     "Teaches that a gauge-tap residual can lose to die IR inside a 400 us "
                    "window; reversing 166 us would have REJECTED an already-legal beam."),
]
for old, new in repl_254:
    if old not in body:
        print("254 MISSING", old[:100].replace("\n", " "))
    else:
        body = body.replace(old, new)
# params dwell_min 8.0 -> beam_kg_h 8.0 if leftover
body = body.replace('("dwell_min", 8.0)', '("beam_kg_h", 8.0)')
src = src[:a] + body + src[b:]

a, b, body = slice_fn(src, "record_255", "tokenize")
repl_255 = [
    ("Prill-Flue PF-6 Head-H3 is spraying urea at 0.42 kg/s. Melt RTD 138 C sits 17 K "
                "below the 155 C freeze license. The viscometer's 4.2 cP is a steam-jacket smear, "
                "not a freeze. Keep the spray if melt wins; a visc-led abort would idle a legal "
                "tower.",
     "Plaster-Holt PH-8 Kettle K-3 is calcining gypsum at 0.42 kg/s. Bed RTD 138 C sits 17 K "
                "below the 155 C over-calcine license. The dewpoint 4.2 C is a steam-jacket smear, "
                "not a freeze. Keep the kettle if bed wins; a dew-led abort would idle a legal "
                "calciner."),
    ("urea-prill-tower", "gypsum-kettle"),
    ("Hold 0.42 kg/s spray while melt stays <= 155 C; do not abort on a 4.2 cP steam-jacket film.",
     "Hold 0.42 kg/s kettle while bed stays <= 155 C; do not abort on a 4.2 C steam-jacket dew."),
    ("rtd.head.C 138 C", "rtd.bed.C 138 C"),
    ("visc.spray.cP 4.2 cP film", "dew.jacket.C 4.2 C film"),
    ("Melt-first ACCEPTS 0.42 kg/s (138 C < 155 C freeze-cap). Visc-first "
                            "would REJECT on a steam-jacket film.",
     "Bed-first ACCEPTS 0.42 kg/s (138 C < 155 C over-calcine cap). Dew-first "
                            "would REJECT on a steam-jacket film."),
    ("300 us = one head-RTD sample minus spray-viscometer group delay on "
                            "this prill-tower bus.",
     "300 us = one bed-RTD sample minus jacket-dewpoint group delay on "
                            "this gypsum-kettle bus."),
    ("would have REJECTED a legal 0.42 kg/s spray.",
     "would have REJECTED a legal 0.42 kg/s kettle."),
    ("head melt RTD, 4 kHz, 24 us jitter", "kettle bed RTD, 4 kHz, 24 us jitter"),
    ("spray viscometer, 4 kHz, 30 us jitter", "jacket dewpoint, 4 kHz, 30 us jitter"),
    ("head encoder (context)", "kettle encoder (context)"),
    ("tower air RTD (context)", "calciner air RTD (context)"),
    ("melt_cap_C", "bed_cap_C"),
    ("observed_melt_C", "observed_bed_C"),
    ("visc_cP", "dew_C"),
    ("visc_abort_cP", "dew_abort_C"),
    ("proposed_spray_kg_s", "proposed_kettle_kg_s"),
    ("Head-H3 indexed on PF-6; spray 0.42 kg/s armed.",
     "Kettle K-3 indexed on PH-8; calcine 0.42 kg/s armed."),
    ("Melt 138 C; viscometer 4.2 cP from a jacket film.",
     "Bed 138 C; dewpoint 4.2 C from a jacket film."),
    ("Head-encoder precursor at 0.680 ms.",
     "Kettle-encoder precursor at 0.680 ms."),
    ("rtd.head.C 138 C at 3.920 ms (winner).",
     "rtd.bed.C 138 C at 3.920 ms (winner)."),
    ("visc.spray.cP 4.2 cP at 4.068 ms (loser by 148 us).",
     "dew.jacket.C 4.2 C at 4.068 ms (loser by 148 us)."),
    ("ACCEPT 0.42 kg/s; executed identical to proposed.",
     "ACCEPT 0.42 kg/s; executed identical to proposed."),
    ("Spray continues; peak melt 141 C < 155 cap.",
     "Kettle continues; peak bed 141 C < 155 cap."),
    ("Visc 4.2 cP remains a steam-jacket film, not a freeze.",
     "Dew 4.2 C remains a steam-jacket film, not a freeze."),
    ("4 min sieve QC on the next lot.",
     "4 min Blaine QC on the next lot."),
    ("spray_042", "kettle_042"),
    ("spray_kg_s", "kettle_kg_s"),
    ("head_rpm", "kettle_rpm"),
    ("melt_C", "bed_C"),
    ("Planner proposes 0.42 kg/s because melt 138 C is under the 155 C freeze-cap; "
                "visc 4.2 cP is under the 16.0 abort and is treated as a jacket film, not a freeze.",
     "Planner proposes 0.42 kg/s because bed 138 C is under the 155 C over-calcine cap; "
                "dew 4.2 C is under the 16.0 abort and is treated as a jacket film, not a freeze."),
    ("Melt 138 C won by 148 us and is under the 155 C cap. Visc 4.2 cP is under the "
                "16.0 abort. ACCEPT the already-legal 0.42 kg/s spray. A REJECT on jacket film "
                "would stall a legal prill.",
     "Bed 138 C won by 148 us and is under the 155 C cap. Dew 4.2 C is under the "
                "16.0 abort. ACCEPT the already-legal 0.42 kg/s kettle. A REJECT on jacket film "
                "would stall a legal calcine."),
    ("executed_spray_kg_s", "executed_kettle_kg_s"),
    ("ACCEPT: spray 0.42 kg/s unchanged. Melt stayed 138-141 C < 155 cap.",
     "ACCEPT: kettle 0.42 kg/s unchanged. Bed stayed 138-141 C < 155 cap."),
    ("Correct ACCEPT kept Head-H3 at 0.42 kg/s. Melt 138 C was under the 155 C cap; "
                "visc 4.2 cP was a steam-jacket film. 4 min sieve QC (qc_s=240).",
     "Correct ACCEPT kept Kettle K-3 at 0.42 kg/s. Bed 138 C was under the 155 C cap; "
                "dew 4.2 C was a steam-jacket film. 4 min Blaine QC (qc_s=240)."),
    ('("spray", "0.42 kg/s continued")', '("kettle", "0.42 kg/s continued")'),
    ('("melt", "peak 141 C < 155 cap")', '("bed", "peak 141 C < 155 cap")'),
    ('("visc", "4.2 cP unused as a hold")', '("dew", "4.2 C unused as a hold")'),
    ('("mission", "prill continues")', '("mission", "calcine continues")'),
    ("Steam-jacket film arrived 148 us after the head RTD; reversing that order would have REJECTED a legal spray.",
     "Steam-jacket dew arrived 148 us after the bed RTD; reversing that order would have REJECTED a legal kettle."),
    ("4 min sieve QC on the next lot, not a freeze event.",
     "4 min Blaine QC on the next lot, not a freeze event."),
    ('("winner", "rtd.head.C (3.920 ms, 138 C)")',
     '("winner", "rtd.bed.C (3.920 ms, 138 C)")'),
    ('("loser", "visc.spray.cP (4.068 ms, 4.2 cP)")',
     '("loser", "dew.jacket.C (4.068 ms, 4.2 C)")'),
    ("an already-legal 0.42 kg/s spray on a 4.2 cP jacket film.",
     "an already-legal 0.42 kg/s kettle on a 4.2 C jacket dew."),
    ('spike("enc.head.ctx"', 'spike("enc.kettle.ctx"'),
    ('spike("rtd.head.C"', 'spike("rtd.bed.C"'),
    ('spike("visc.spray.cP"', 'spike("dew.jacket.C"'),
    ('"thalamic-relay.head-rtd"', '"thalamic-relay.bed-rtd"'),
    ('"spikenaut.policy.spray-go"', '"spikenaut.policy.kettle-go"'),
    ('("relay.rtd.head", "policy.spray_go", 0.70)',
     '("relay.rtd.bed", "policy.kettle_go", 0.70)'),
    ('("relay.visc.spray", "policy.visc_hold", 0.26)',
     '("relay.dew.jacket", "policy.dew_hold", 0.26)'),
    ("melt_stdp; HA tags the already-legal head-RTD bind",
     "bed_stdp; HA tags the already-legal bed-RTD bind"),
    ('pop_budget("spray_go"', 'pop_budget("kettle_go"'),
    ('pop_budget("visc_hold"', 'pop_budget("dew_hold"'),
    ('pop_budget("melt_ctx"', 'pop_budget("bed_ctx"'),
    ("Prill-Flue PF-6 / Head-H3: melt 138 C beats visc film 4.2 cP by 148 us; correct "
                "ACCEPT of an already-legal 0.42 kg/s spray",
     "Plaster-Holt PH-8 / Kettle K-3: bed 138 C beats dew film 4.2 C by 148 us; correct "
                "ACCEPT of an already-legal 0.42 kg/s kettle"),
    ("Correct ACCEPT. Melt 138 < 155 cap; visc is jacket film, not freeze. ",
     "Correct ACCEPT. Bed 138 < 155 cap; dew is jacket film, not freeze. "),
    ('"prill-tower"', '"gypsum-kettle"'),
    ('"melt-vs-visc"', '"bed-vs-dew"'),
    ("Teaches that a steam-jacket visc film can lose to head RTD inside a 300 us "
                    "window; reversing 148 us would have REJECTED an already-legal spray.",
     "Teaches that a steam-jacket dew film can lose to bed RTD inside a 300 us "
                    "window; reversing 148 us would have REJECTED an already-legal kettle."),
]
for old, new in repl_255:
    if old not in body:
        print("255 MISSING", old[:100].replace("\n", " "))
    else:
        body = body.replace(old, new)
src = src[:a] + body + src[b:]

P.write_text(src)
print("patched bytes", P.stat().st_size)
