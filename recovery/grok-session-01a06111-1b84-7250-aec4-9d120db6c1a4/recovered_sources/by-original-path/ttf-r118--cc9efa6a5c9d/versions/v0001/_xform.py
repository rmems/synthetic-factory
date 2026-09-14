#!/usr/bin/env python3
"""Rewrite cloned r110 generator into r118 (IDs 606-610, NE107 wrong-reject)."""
from pathlib import Path

p = Path("/tmp/ttf-r118/gen_r118.py")
t = p.read_text(encoding="utf-8")

# --- ID / round / path (longest first) ---
repls = [
    ("ttf-r110-566..570", "ttf-r118-606..610"),
    ("ttf-r110-566", "ttf-r118-606"),
    ("ttf-r110-567", "ttf-r118-607"),
    ("ttf-r110-568", "ttf-r118-608"),
    ("ttf-r110-569", "ttf-r118-609"),
    ("ttf-r110-570", "ttf-r118-610"),
    ("record_566", "record_606"),
    ("record_567", "record_607"),
    ("record_568", "record_608"),
    ("record_569", "record_609"),
    ("record_570", "record_610"),
    ("lif_566_excerpt", "lif_606_excerpt"),
    ("110566", "118606"),
    ("110567", "118607"),
    ("110568", "118608"),
    ("110569", "118609"),
    ("110570", "118610"),
    ("1762300000000566", "1762300000000606"),
    ("1762300000000567", "1762300000000607"),
    ("1762300000000568", "1762300000000608"),
    ("1762300000000569", "1762300000000609"),
    ("1762300000000570", "1762300000000610"),
    ('range(566, 571)', "range(606, 611)"),
    ("/tmp/ttf-r110", "/tmp/ttf-r118"),
    ("batch-r110.jsonl", "batch-r118.jsonl"),
    ("NOTES-r110.md", "NOTES-r118.md"),
    ("NOTES-r110", "NOTES-r118"),
    ("gen_r110.py", "gen_r118.py"),
    ("Emit TTF r110", "Emit TTF r118"),
    ('("round", 110)', '("round", 118)'),
    ("meta.round != 110", "meta.round != 118"),
    ('path.parent.name == "ttf-r110"', 'path.parent.name == "ttf-r118"'),
    ('"r110" in path.name', '"r118" in path.name'),
    ("path.name == \"gen_r110.py\"", "path.name == \"gen_r118.py\""),
]
for a, b in repls:
    t = t.replace(a, b)

# leftover hardcoded 566/567/568 comments inside self_check
t = t.replace("566 missing independent_lif", "606 missing independent_lif")
t = t.replace("566 inflection outside window", "606 inflection outside window")
t = t.replace("566 partnered-neg total not negative", "606 partnered-neg total not negative")
t = t.replace("567 routing has go_accept", "607 routing has go_accept")
t = t.replace("567 missing hold_reject routing", "607 missing hold_reject routing")
t = t.replace("567 live not under trip", "607 live not under trip")
t = t.replace("567 leftover burnout-upscale not tagged", "607 leftover NE107-maintenance not tagged")
t = t.replace("567 executed feed not zero", "607 executed feed not zero")
t = t.replace("567 missing recovery", "607 missing recovery")

# --- plants / domains (record 606) ---
chem = [
    # 606 formic carbonylation
    ("Glyoxal-Wath", "Formyl-Thorp"),
    ("glyoxal-oxidizer", "formic-acid-carbonylation"),
    ("Glyoxal air-oxidizer G-4", "Formic carbonylation C-4"),
    ("G-4 air-oxidation pass", "C-4 carbonylation pass"),
    ("G-4 indexed", "C-4 indexed"),
    ("G-4 volume", "C-4 volume"),
    ("G-4 / air-oxidizer", "C-4 / methanol-carbonylation"),
    ("ethylene-glycol", "methanol"),
    ("Ethylene-glycol", "Methanol"),
    ("eg_tph", "meoh_tph"),
    ("eg.tph", "meoh.tph"),
    ("ft.eg", "ft.meoh"),
    ("enc.eg", "enc.meoh"),
    ("policy.eg_", "policy.meoh_"),
    ("eg_clamp", "meoh_clamp"),
    ("eg_hold", "meoh_hold"),
    ("cruise_eg_8p2", "cruise_meoh_6p8"),
    ("clamped_eg_4p6", "clamped_meoh_3p4"),
    ("packing-support buckle", "packing-gasket blow"),
    ("packing-support", "packing-gasket"),
    ("packing support", "packing gasket"),
    ("Packing-support", "Packing-gasket"),
    ("ae.pack.buckle", "ae.pack.gasket"),
    ("lif.buckle", "lif.gasket"),
    ("oxidizer isolate", "carbonylation isolate"),
    ("air-oxidizer", "carbonylation"),
    ("air-oxidation", "carbonylation"),
    ("glyoxal-assay", "formic-assay"),
    ("glyoxal assay", "formic assay"),
    ("bed-glyoxal", "bed-formic"),
    ("blower_pct", "compressor_pct"),
    ("air_ratio", "co_ratio"),
    ("glycol-orifice", "methanol-orifice"),
    ("glycol-clamp", "methanol-clamp"),
    ("glycol clamp", "methanol clamp"),
    ("Glycol precursor", "Methanol precursor"),
    ("glycol FT", "methanol FT"),
    ("Holding 8.2 t/h", "Holding 6.8 t/h"),
    # keep 8.2 numeric in this record? leave numbers; names carry novelty
    ("selectivity cap", "carbonylation cap"),
    ("packing AE puck", "gasket AE puck"),
    ("packing is loading heat", "gasket is loading heat"),
    ("packing contact", "gasket contact"),
    ("packing charge", "gasket charge"),
    ("Neurons 0-18 carry +0.69 glycol-clamp bias; stim 21.4-25.2 ms is the packing-support buckle.",
     "Neurons 0-18 carry +0.69 methanol-clamp bias; stim 21.4-25.2 ms is the packing-gasket blow."),
    # 607 HAS crystallizer + NE107 (plants first)
    ("Succiny-Wray", "Hydroxyl-Beck"),
    ("succinic-anhydride-dehydrator", "hydroxylamine-sulfate-crystallizer"),
    ("succinic-anhydride still", "hydroxylamine-sulfate magma"),
    ("succinic bus", "HAS bus"),
    ("anhydride window", "HAS window"),
    ("Maleic dehydrator D-2", "HAS crystallizer X-3"),
    ("dehydrator D-2", "crystallizer X-3"),
    ("D-2 latched", "X-3 latched"),
    ("D-2 Type-K", "X-3 RTD"),
    ("on D-2", "on X-3"),
    ("froze D-2", "froze X-3"),
    ("live D-2", "live X-3"),
    ("sister D-3", "sister X-4"),
    ("D-2's slot", "X-3's slot"),
    ("maleic acid", "hydroxylamine sulfate"),
    ("maleic_tph", "has_tph"),
    ("maleic_5p6", "has_5p6"),
    ("maleic_hold_burnout", "has_hold_ne107"),
    ("proposed_maleic_tph", "proposed_has_tph"),
    ("executed_maleic_tph", "executed_has_tph"),
    ("ft.maleic.ctx", "ft.has.ctx"),
    ("Keep 5.6 t/h maleic", "Keep 5.6 t/h HAS"),
    ("maleic 5.6", "HAS 5.6"),
    ("Maleic-FT", "HAS-FT"),
    ("maleic feed FT", "HAS feed FT"),
    ("(\"maleic\"", "(\"has\""),
    ("(\"maleic\",", "(\"has\","),
    ("hold maleic", "hold HAS"),
    ("acetic make-up FT", "ammonium-sulfate make-up FT"),
    # 608 PPS HIL
    ("Butacryl-Holm", "Phenylsulf-Wath"),
    ("BA-HIL", "PS-HIL"),
    ("butyl-acrylate-esterifier", "polyphenylene-sulfide-kettle"),
    ("Esterifier E-8", "PPS kettle K-8"),
    ("esterifier pad", "PPS pad"),
    ("the esterifier", "the PPS kettle"),
    ("acrylic acid", "sodium sulfide"),
    ("t/h acrylic", "t/h Na2S"),
    ("foam-collapse", "oligomer-foam"),
    ("collapsing foam bed", "collapsing oligomer bed"),
    # 609 PEI
    ("Polycarb-Glen", "Etherimid-Dene"),
    ("polycarbonate-interfacial", "polyetherimide-still"),
    ("Interfacial polycarbonate kettle K-11", "PEI still S-11"),
    ("interfacial pass", "imidization pass"),
    ("interfacial", "imidization"),
    ("phosgene", "diamine"),
    ("enc.phos", "enc.mpda"),
    ("2.6 t/h diamine", "1.9 t/h diamine"),  # may no-op if still phosgene at this point
    # 610 FKM
    ("Norborn-Mire", "Fluorelast-Pike"),
    ("norbornene-polymerizer", "fluoroelastomer-emulsion"),
    ("Norbornene polymerizer P-5", "FKM emulsion E-5"),
    ("norbornene", "VDF"),
    ("enc.nb", "enc.vdf"),
    ("rtd.nb", "rtd.fkm"),
    ("ROMP pass", "FKM pass"),
    ("the polymerizer hold", "the emulsion hold"),
]
for a, b in chem:
    t = t.replace(a, b)

# leftover maleic / glycol / glyoxal / esterifier / norborn / polycarb tokens
more = [
    ("maleic", "HAS"),
    ("Maleic", "HAS"),
    ("glycol", "methanol"),
    ("Glycol", "Methanol"),
    ("glyoxal", "formic"),
    ("Glyoxal", "Formic"),
    ("esterifier", "PPS kettle"),
    ("Esterifier", "PPS kettle"),
    ("Run E-8", "Run K-8"),
    ("Run K-11", "Run S-11"),
    ("Run P-5", "Run E-5"),
    ("K-11 at", "S-11 at"),
    ("P-5 at", "E-5 at"),
    ("38 C liquor", "44 C still-base"),
    ("Liquor-first", "Still-base-first"),
    ("liquor stays", "still-base stays"),
    ("coil IR smear", "condenser IR smear"),
    ("already-legal imidization", "already-legal PEI"),
    ("4.4 t/h VDF", "3.2 t/h VDF"),
    ("2.6 t/h diamine", "1.9 t/h diamine"),
    ("7.1 t/h Na2S", "5.3 t/h Na2S"),
    ("7.1 t/h", "5.3 t/h"),
    ("8.2 t/h", "6.8 t/h"),
    ("4.6 t/h", "3.4 t/h"),
    ("2.6 t/h", "1.9 t/h"),
    ("4.4 t/h", "3.2 t/h"),
]
for a, b in more:
    t = t.replace(a, b)

# --- NE107 class (after burnout strings still present in 607) ---
ne = [
    ("IEC 60584 burnout-upscale jumper", "NAMUR NE107 maintenance-required latch"),
    ("IEC 60584 burnout-upscale URV", "NAMUR NE107 maintenance EU"),
    ("IEC 60584 burnout-upscale", "NAMUR NE107 maintenance"),
    ("leftover burnout-upscale jumper", "leftover NE107 maintenance latch"),
    ("leftover burnout-upscale EU", "leftover NE107 maintenance EU"),
    ("leftover burnout-upscale", "leftover NE107 maintenance"),
    ("burnout-upscale jumper", "NE107 maintenance latch"),
    ("burnout-upscale URV", "NE107 maintenance EU"),
    ("burnout-upscale-as-PV", "ne107-maintenance-as-PV"),
    ("burnout-upscale-as-pv", "ne107-maintenance-as-pv"),
    ("Burnout-upscale leftover", "NE107-maintenance leftover"),
    ("Burnout-first", "Maintenance-first"),
    ("burnout-first", "maintenance-first"),
    ("bus.burn.up", "bus.ne107.m"),
    ("relay.burnout.upscale", "relay.ne107.maint"),
    ("relay.burn.up", "relay.ne107.m"),
    ("burnout_upscale_stdp", "ne107_maint_stdp"),
    ("burnout_upscale", "ne107_maintenance"),
    ("burnout_is_pv", "ne107_is_pv"),
    ("burnout_as_eu", "ne107_as_eu"),
    ("burnout_C", "maint_shadow_C"),
    ("burnout_mA", "ne107_status_mA"),
    ("burnout_flag", "ne107_flag"),
    ("bound_tc", "bound_pv"),
    ("live_type_k", "live_rtd"),
    ("Type-K bed", "RTD magma"),
    ("Type-K", "RTD"),
    ("live.bed.C", "live.magma.C"),
    ("relay.live.bed", "relay.live.magma"),
    ("burnout_ctx", "ne107_ctx"),
    ("misbound_burnout_C", "misbound_maint_C"),
    ("wrong_burnout_C", "wrong_maint_C"),
    ("1372 C", "246.0 C"),
    ("1372.0", "246.0"),
    ("21.6 mA URV failsafe", "NE107 M-bit shadow at 16.4 mA"),
    ("21.6 mA", "16.4 mA"),
    ("URV failsafe STALE", "NE107 M-bit STALE"),
    ("URV failsafe", "NE107 M-bit"),
    ("iec-60584-urv", "namur-ne107-m"),
    ("live TC", "live RTD"),
    ("Live-TC-first", "Live-RTD-first"),
    ("live-TC-first", "live-RTD-first"),
    ("live-TC win", "live-RTD win"),
    ("LIVE Type-K", "LIVE RTD"),
    ("LIVE analog", "LIVE analog RTD"),
    ("bed RTD, 4 kHz", "magma RTD, 4 kHz"),
]
for a, b in ne:
    t = t.replace(a, b)

# THIS_DOMAINS / PLANTS tuples
old_dom = '''THIS_DOMAINS = (
    "formic-acid-carbonylation",
    "hydroxylamine-sulfate-crystallizer",
    "polyphenylene-sulfide-kettle",
    "polyetherimide-still",
    "fluoroelastomer-emulsion",
)'''
# after chem replace, glyoxal-oxidizer already became formic-acid-carbonylation etc.
# verify:
if "formic-acid-carbonylation" not in t or "THIS_DOMAINS" not in t:
    raise SystemExit("domain tuple missing after replace")

old_plants_expect = '''THIS_PLANTS = (
    "Formyl-Thorp",
    "Hydroxyl-Beck",
    "Phenylsulf-Wath",
    "Etherimid-Dene",
    "Fluorelast-Pike",
)'''
if "Formyl-Thorp" not in t or "Fluorelast-Pike" not in t:
    raise SystemExit("plants missing")

# executed feed check: maleic_tph already has_tph
t = t.replace(
    'if rec["executed_action"]["parameters"]["has_tph"] != 0.0:',
    'if rec["executed_action"]["parameters"]["has_tph"] != 0.0:',
)
# evidence tag check
t = t.replace(
    'if ev.get("ne107_maintenance") is not True or ev.get("ne107_is_pv") is not False:',
    'if ev.get("ne107_maintenance") is not True or ev.get("ne107_is_pv") is not False:',
)
# if still burnout keys in self_check, fix
t = t.replace(
    'if ev.get("burnout_upscale") is not True or ev.get("burnout_is_pv") is not False:',
    'if ev.get("ne107_maintenance") is not True or ev.get("ne107_is_pv") is not False:',
)
t = t.replace(
    '["parameters"]["maleic_tph"]',
    '["parameters"]["has_tph"]',
)

p.write_text(t, encoding="utf-8")
print("wrote", p, "chars", len(t))
# sanity
need = [
    "ttf-r118-606", "ttf-r118-610", "formic-acid-carbonylation",
    "hydroxylamine-sulfate-crystallizer", "polyphenylene-sulfide-kettle",
    "polyetherimide-still", "fluoroelastomer-emulsion",
    "Formyl-Thorp", "Hydroxyl-Beck", "Phenylsulf-Wath", "Etherimid-Dene",
    "Fluorelast-Pike", "ne107_maintenance", "NAMUR NE107",
    "relay.ne107.maint", "wrong-reject", "record_606", "record_610",
    "meta.round != 118",
]
for s in need:
    if s not in t:
        print("MISSING", s)
forbid = [
    "ttf-r110-", "Glyoxal-Wath", "Succiny-Wray", "Butacryl-Holm",
    "Polycarb-Glen", "Norborn-Mire", "glyoxal-oxidizer",
    "succinic-anhydride-dehydrator", "butyl-acrylate-esterifier",
    "outputs/raw",
]
for s in forbid:
    if s in t and s != "outputs/raw":
        print("STALE", s)
    elif s == "outputs/raw" and "Never writes outputs/raw" not in t and "outputs/raw/" in t:
        print("RAW WRITE?", t[t.find("outputs/raw")-40:t.find("outputs/raw")+40])
print("stale ttf-r110 count", t.count("ttf-r110"))
print("burnout leftover count", t.lower().count("burnout"))
print("maleic leftover", t.lower().count("maleic"))
print("glycol leftover", t.lower().count("glycol"))
