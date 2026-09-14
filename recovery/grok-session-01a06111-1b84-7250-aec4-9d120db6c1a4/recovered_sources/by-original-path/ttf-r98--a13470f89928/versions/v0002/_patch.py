#!/usr/bin/env python3
"""Rewrite cloned gen_r86.py into gen_r98.py (even-round wrong-reject)."""
from pathlib import Path

p = Path("/tmp/ttf-r98/gen_r98.py")
t = p.read_text(encoding="utf-8")

# --- identity (longest IDs first) ---
repls = [
    ("ttf-r86-450", "ttf-r98-510"),
    ("ttf-r86-449", "ttf-r98-509"),
    ("ttf-r86-448", "ttf-r98-508"),
    ("ttf-r86-447", "ttf-r98-507"),
    ("ttf-r86-446", "ttf-r98-506"),
    ("record_450()", "record_510()"),
    ("record_449()", "record_509()"),
    ("record_448()", "record_508()"),
    ("record_447()", "record_507()"),
    ("record_446()", "record_506()"),
    ("def record_450", "def record_510"),
    ("def record_449", "def record_509"),
    ("def record_448", "def record_508"),
    ("def record_447", "def record_507"),
    ("def record_446", "def record_506"),
    ("lif_446_excerpt", "lif_506_excerpt"),
    ("range(446, 451)", "range(506, 511)"),
    ("batch-r86.jsonl", "batch-r98.jsonl"),
    ("NOTES-r86.md", "NOTES-r98.md"),
    ("NOTES-r86", "NOTES-r98"),
    ("Emit TTF r86 JSONL (ttf-r86-446..450)", "Emit TTF r98 JSONL (ttf-r98-506..510)"),
    ('Path("/tmp/ttf-r86")', 'Path("/tmp/ttf-r98")'),
    ("ttf-r86", "ttf-r98"),
    ("gen_r86.py", "gen_r98.py"),
    ('"generated_at", "2026-09-02T18:25:00Z"', '"generated_at", "2026-09-02T18:45:00Z"'),
    ('NOVEL_COVERAGE_LINE = "Novel coverage: 16.0%"', 'NOVEL_COVERAGE_LINE = "Novel coverage: 16.5%"'),
    ("if rec[\"meta\"][\"round\"] != 86:", "if rec[\"meta\"][\"round\"] != 98:"),
    ("86446", "98506"),
    ("86447", "98507"),
    ("86448", "98508"),
    ("86449", "98509"),
    ("86450", "98510"),
    ("1756850400000446", "1756850400000506"),
    ("1756850400000447", "1756850400000507"),
    ("1756850400000448", "1756850400000508"),
    ("1756850400000449", "1756850400000509"),
    ("1756850400000450", "1756850400000510"),
    ('issues.append("446 missing independent_lif")', 'issues.append("506 missing independent_lif")'),
    ('issues.append("446 inflection outside window")', 'issues.append("506 inflection outside window")'),
    ('issues.append("446 partnered-neg total not negative")', 'issues.append("506 partnered-neg total not negative")'),
    ('issues.append("447 routing has etbe_go")', 'issues.append("507 routing has mibk_go")'),
    ('issues.append("447 missing etbe_hold routing")', 'issues.append("507 missing mibk_hold routing")'),
]
for a, b in repls:
    t = t.replace(a, b)

# domains / plants
dom_plant = [
    ("dimethyl-carbonate-transester", "sodium-dithionite-reducer"),
    ("ethyl-tert-butyl-ether", "methyl-isobutyl-ketone-still"),
    ("sodium-perchlorate-cell", "lithium-cobalt-oxide-calciner"),
    ("pentaerythritol-aldol", "gamma-butyrolactone-dehydro"),
    ("ptfe-dispersion-autoclave", "ppta-polymerizer"),
    ("Dimcarb-Twine", "Dithion-Hawse"),
    ("Etherbut-Lynns", "Mibk-Grain"),
    ("Perchlate-Meres", "Lithcox-Beck"),
    ("Pentaol-Croftle", "Gbl-Reen"),
    ("Fluoropl-Staithe", "Ppta-Slack"),
    ("DT-5", "DH-5"),
    ("EL-3", "MG-3"),
    ("EC-4", "ST-4"),
    ("PM-HIL", "LB-HIL"),
    ("PC-6", "GR-6"),
    ("FS-8", "PS-8"),
    ("TX-2", "RD-2"),
    ("CL-7", "KN-7"),
    ("AD-1", "DH-1"),
    ("AC-3", "PZ-3"),
]
for a, b in dom_plant:
    t = t.replace(a, b)

# 506 partnered-neg process nouns
proc506 = [
    ("packed transester", "SO2-formate reducer"),
    ("Transester", "Reducer"),
    ("transester", "reducer"),
    ("methanolate", "formate"),
    ("Methanolate", "Formate"),
    ("packed-bed", "reducer-bed"),
    ("Packed-bed", "Reducer-bed"),
    ("packed bed", "reducer bed"),
    ("Packed bed", "Reducer bed"),
    ("DMC pass", "dithionite pass"),
    ("DMC bus", "dithionite bus"),
    ("this dimethyl-carbonate", "this sodium-dithionite"),
    ("CO2-feed FT (context)", "SO2-feed FT (context)"),
    ("dmc_tph", "dithion_tph"),
    ("co2_tph", "so2_tph"),
    ("enc.meoh.ctx", "enc.formate.ctx"),
    ("ft.meoh.tph", "ft.formate.tph"),
    ("meoh_tph", "formate_tph"),
    ("meoh_clamp", "formate_clamp"),
    ("meoh_hold", "formate_hold"),
    ("cruise_meoh_142", "cruise_formate_142"),
    ("clamped_meoh_96", "clamped_formate_96"),
    ("thalamic-relay.dmc-hotspot", "thalamic-relay.dithion-hotspot"),
    ("spikenaut.policy.meoh-clamp", "spikenaut.policy.formate-clamp"),
    ("relay.ft.meoh", "relay.ft.formate"),
    ("policy.meoh_clamp", "policy.formate_clamp"),
    ("policy.meoh_hold", "policy.formate_hold"),
    ("catalyst-skin", "liquor-skin"),
    ("16 mm packed-bed patch", "16 mm reducer-bed patch"),
    ("16 mm packed-bed slump", "16 mm reducer-bed slump"),
    ("16 mm packed-bed", "16 mm reducer-bed"),
    ("bed isolate", "reducer isolate"),
    ("Bed isolate", "Reducer isolate"),
    ("ae.bed.slump", "ae.reducer.slump"),
    ("relay.ae.bed", "relay.ae.reducer"),
    ("feed-preheat spike", "formate-preheat spike"),
    ("TX-2 volume", "RD-2 volume"),
    ("sound DMC", "sound dithionite"),
    ("methanolate-feed", "formate-feed"),
    ("methanolate still", "formate still"),
    ("cut methanolate", "cut formate"),
]
for a, b in proc506:
    t = t.replace(a, b)

# leftover meoh tokens in 506
t = t.replace("meoh", "formate")

# 507 wrong-reject: watchdog-timeout-as-PV (not handshake/heartbeat)
wr = [
    ("ether-column", "MIBK-still"),
    ("Ether-Column", "MIBK-Still"),
    ("etherifier", "ketone still"),
    ("Etherifier", "Ketone still"),
    ("etherification", "ketone-quality"),
    ("ETBE distillate", "MIBK distillate"),
    ("ETBE", "MIBK"),
    ("etbe_hold", "mibk_hold"),
    ("etbe_go", "mibk_go"),
    ("etbe_hold_wrong_handshake", "mibk_hold_wrong_watchdog"),
    ("policy.etbe_hold", "policy.mibk_hold"),
    ("policy.etbe_go", "policy.mibk_go"),
    ("hb.echo.bar", "wd.timeout.bar"),
    ("relay.hb.echo", "relay.wd.timeout"),
    ("hb_ctx", "wd_ctx"),
    ("STALE_HANDSHAKE", "WATCHDOG_TIMEOUT"),
    ("stale-handshake-heartbeat-as-pv", "watchdog-timeout-as-pv"),
    ("stale-handshake / heartbeat-as-PV", "watchdog-timeout-as-PV"),
    ("stale handshake", "watchdog timeout"),
    ("Stale handshake", "Watchdog timeout"),
    ("handshake_echo_bar", "watchdog_shadow_bar"),
    ("handshake_age_ms", "watchdog_age_ms"),
    ("max_legal_handshake_age_ms", "max_legal_watchdog_age_ms"),
    ("handshake_status", "watchdog_status"),
    ("heartbeat_is_pv", "watchdog_is_pv"),
    ("heartbeat payload", "watchdog payload"),
    ("heartbeat flag", "watchdog flag"),
    ("keep-alive echo", "watchdog freeze"),
    ("keep-alive", "watchdog freeze"),
    ("HART handshake echo", "PLC watchdog freeze"),
    ("HART handshake", "PLC watchdog"),
    ("HART keep-alive", "PLC watchdog freeze"),
    ("stale HART", "stale PLC watchdog"),
    ("Handshake-first", "Watchdog-first"),
    ("handshake-first", "watchdog-first"),
    ("Handshake echo", "Watchdog freeze"),
    ("handshake echo", "watchdog freeze"),
    ("stale handshake echo", "watchdog timeout freeze"),
    ("leftover HART", "leftover PLC watchdog"),
    ("comms diagnostic", "watchdog diagnostic"),
    ("handshake_cap_stdp", "watchdog_cap_stdp"),
    ("ACh tags the (wrong) etbe_hold bind at the stale handshake echo",
     "ACh tags the (wrong) mibk_hold bind at the watchdog timeout freeze"),
    ("ACh tags the (wrong) mibk_hold bind at the stale handshake echo",
     "ACh tags the (wrong) mibk_hold bind at the watchdog timeout freeze"),
]
for a, b in wr:
    t = t.replace(a, b)

# leftover handshake/heartbeat in 507
t = t.replace("handshake", "watchdog")
t = t.replace("Handshake", "Watchdog")
t = t.replace("heartbeat", "watchdog")
t = t.replace("Heartbeat", "Watchdog")
t = t.replace("HART", "PLC")

# 508 LCO calciner
proc508 = [
    ("electrolyte", "kiln-bed"),
    ("Electrolyte", "Kiln-bed"),
    ("elyte", "kbed"),
    ("Elyte", "Kbed"),
    ("rtd.kbed.C", "rtd.kbed.C"),
    ("Cell KN-7", "Kiln KN-7"),
    ("cell CL-7", "kiln KN-7"),
    ("Cell CL-7", "Kiln KN-7"),
    ("perchlorate-cell mockup", "LCO-calciner mockup"),
    ("perchlorate-start floor", "LCO-start floor"),
    ("sodium-perchlorate HIL bus", "LCO-calciner HIL bus"),
    ("sodium-perchlorate cell", "LCO calciner"),
    ("sodium-perchlorate bus", "LCO-calciner feed"),
    ("live electrolyzer", "live calciner"),
    ("NaClO3 thermocouple (context)", "Co3O4 thermocouple (context)"),
    ("bus current", "precursor feed"),
    ("bus 18 kA", "precursor 18 t/h"),
    ("18 kA", "18 t/h"),
    ("0.0 kA", "0.0 t/h"),
    ("bus_kA", "precursor_tph"),
    ("walk_ka_18", "walk_tph_18"),
    ("ka_hold", "kiln_hold"),
    ("ka_commit", "kiln_commit"),
    ("kbed_veto", "kbed_veto"),
    ("policy.ka_hold", "policy.kiln_hold"),
    ("policy.ka_commit", "policy.kiln_commit"),
    ("thalamic-relay.naclo4-elyte", "thalamic-relay.lco-kbed"),
    ("thalamic-relay.naclo4-kbed", "thalamic-relay.lco-kbed"),
    ("spikenaut.policy.ka-hold", "spikenaut.policy.kiln-hold"),
    ("hood-spectrum", "hood-spectrum"),
    ("tc.cell.ctx", "tc.kiln.ctx"),
    ("relay.tc.cell", "relay.tc.kiln"),
    ("across the cell", "across the kiln"),
    ("the cell.", "the kiln."),
    ("(\"cell\",", "(\"kiln\","),
    ("illegal bus walk", "illegal kiln walk"),
    ("bus walk", "kiln walk"),
    ("Bus walk", "Kiln walk"),
    ("bus walk deferred", "kiln walk deferred"),
    ("startfloor_stdp; DA at kiln-bed win", "startfloor_stdp; DA at kiln-bed win"),
]
for a, b in proc508:
    t = t.replace(a, b)

# 509 GBL dehydro
proc509 = [
    ("Aldol DH-1", "Dehydro DH-1"),
    ("Aldol indexed", "Dehydro indexed"),
    ("formaldehyde", "butanediol"),
    ("Formaldehyde", "Butanediol"),
    ("dissolved formaldehyde", "dissolved butanediol"),
    ("dissolved-formaldehyde", "dissolved-butanediol"),
    ("hcho_cap_wt", "bdo_cap_wt"),
    ("observed_hcho_wt", "observed_bdo_wt"),
    ("proposed_hcho_wt", "proposed_bdo_wt"),
    ("hcho_wt", "bdo_wt"),
    ("hcho_28", "bdo_28"),
    ("clamped_hcho_12", "clamped_bdo_12"),
    ("an.hcho.wt", "an.bdo.wt"),
    ("relay.an.hcho", "relay.an.bdo"),
    ("hcho_clamp", "bdo_clamp"),
    ("hcho_veto", "bdo_veto"),
    ("policy.hcho_clamp", "policy.bdo_clamp"),
    ("thalamic-relay.ald-hcho", "thalamic-relay.gbl-bdo"),
    ("spikenaut.policy.hcho-clamp", "spikenaut.policy.bdo-clamp"),
    ("ald_reseq_s", "gbl_reseq_s"),
    ("aldehyde_stdp", "lactone_stdp"),
    ("acetaldehyde ceiling", "GBL ceiling"),
    ("acetaldehyde cap", "GBL cap"),
    ("Acetaldehyde occupies", "GBL occupies"),
    ("acetald_tph", "gbl_tph"),
    ("acetald-cap", "gbl-cap"),
    ("hcho-vs-canopy", "bdo-vs-canopy"),
    ("lime load cell (context)", "hydrogen load cell (context)"),
    ("kettle formaldehyde analyzer", "kettle butanediol analyzer"),
    ("this pentaerythritol aldol bus", "this gamma-butyrolactone dehydro bus"),
    ("pentaerythritol make", "GBL make"),
    ("formalin", "BDO feed"),
    ("HCHO", "BDO"),
    ("(HCHO 33", "(BDO 33"),
]
for a, b in proc509:
    t = t.replace(a, b)

# 510 PPTA polymerizer
proc510 = [
    ("Autoclave PZ-3", "Polymerizer PZ-3"),
    ("autoclave PT", "kettle PT"),
    ("Autoclave PT", "Kettle PT"),
    ("Autoclave-first", "Kettle-first"),
    ("autoclave-first", "kettle-first"),
    ("Autoclave-PT", "Kettle-PT"),
    ("autoclave-PT", "kettle-PT"),
    ("pt.auto.ctx", "pt.kett.ctx"),
    ("pt.auto.bar", "pt.kett.bar"),
    ("relay.pt.auto", "relay.pt.kett"),
    ("thalamic-relay.auto-pt", "thalamic-relay.kett-pt"),
    ("observed_auto_bar", "observed_kett_bar"),
    ("auto_bar", "kett_bar"),
    ("auto_C", "kett_C"),
    ("PTFE dispersion", "PPTA dope"),
    ("PTFE autoclave", "PPTA polymerizer"),
    ("PTFE survey", "PPTA survey"),
    ("PTFE feed", "PPTA feed"),
    ("this PTFE dispersion simulation", "this PPTA polymerizer simulation"),
    ("legal PTFE", "legal PPTA"),
    ("TFE charge", "PPD charge"),
    ("TFE orifice (context)", "PPD orifice (context)"),
    ("TFE pressure", "PPD pressure"),
    ("TFE load", "PPD load"),
    ("not TFE", "not PPD"),
    ("high-TFE", "high-PPD"),
    ("(\"TFE\",", "(\"PPD\","),
    ("\"ptfe\"", "\"ppta\""),
    ("autoclave-vs-shell", "kettle-vs-shell"),
    ("simulated-lighting", "simulated-lighting"),
    ("sits at 18.4 bar TFE", "sits at 18.4 bar PPD dope"),
    ("legal PTFE dispersion", "legal PPTA dope"),
    ("Run PZ-3 when autoclave", "Run PZ-3 when kettle"),
    ("Run PZ-3 when kettle PT is", "Run PZ-3 when kettle PT is"),
]
for a, b in proc510:
    t = t.replace(a, b)

# leftover autoclave in 510 titles/summaries
t = t.replace("autoclave 18.4 bar", "kettle 18.4 bar")
t = t.replace("Autoclave 18.4 bar", "Kettle 18.4 bar")
t = t.replace("the PTFE autoclave", "the PPTA polymerizer")
t = t.replace("legal autoclave PT", "legal kettle PT")
t = t.replace("(\"autoclave\",", "(\"polymerizer\",")
t = t.replace("autoclave remains 18.4", "kettle remains 18.4")
t = t.replace("autoclave at 18.4 bar under", "kettle at 18.4 bar under")
t = t.replace("autoclave PT 18.4 bar is under", "kettle PT 18.4 bar is under")
t = t.replace("PZ-3 seeded; autoclave", "PZ-3 seeded; kettle")
t = t.replace("shell-pyrometer", "shell-pyrometer")

# occupancy harvest extras
old_globs = '''    for glob_name in (
        "ttf-r*/gen_r*.py",
        "ttf-r*/_records.py",
        "ttf-r*/_records_r*.py",
        "ttf-r*/_head.py",
        "ttf-r*/_tail.py",
        "ttf-r*/_tail2.py",
        "ttf-r*/_head_helpers.py",
        "ttf-r*/_helpers.py",
        "ttf-r*/_helpers_from_r*.py",
        "ttf-r*/_prefix.py",
        "ttf-r*/_part_records.py",
        "ttf-r*/_records_body.py",
        "ttf-r*/_wrap.py",
        "ttf-r*/_rest.py",
        "ttf-r*/_suffix_raw.py",
        "ttf-r*/_head_src.py",
        "ttf-r*/_tail_raw.py",
        "ttf-r*/_new_records.py",
    ):'''
new_globs = '''    for glob_name in (
        "ttf-r*/gen_r*.py",
        "ttf-r*/_records.py",
        "ttf-r*/_records_r*.py",
        "ttf-r*/_head.py",
        "ttf-r*/_tail.py",
        "ttf-r*/_tail2.py",
        "ttf-r*/_head_helpers.py",
        "ttf-r*/_helpers.py",
        "ttf-r*/_helpers_from_r*.py",
        "ttf-r*/_prefix.py",
        "ttf-r*/_part_records.py",
        "ttf-r*/_records_body.py",
        "ttf-r*/_wrap.py",
        "ttf-r*/_rest.py",
        "ttf-r*/_rest2.py",
        "ttf-r*/_rest3.py",
        "ttf-r*/_suffix_raw.py",
        "ttf-r*/_suffix.py",
        "ttf-r*/_head_src.py",
        "ttf-r*/_tail_raw.py",
        "ttf-r*/_tail_src.py",
        "ttf-r*/_new_records.py",
        "ttf-r*/_body.py",
        "ttf-r*/_head_r*.py",
        "ttf-r*/_tail_r*.py",
        "ttf-r*/_banned_src.py",
        "ttf-r*/occ-*.txt",
    ):'''
if old_globs not in t:
    raise SystemExit("glob block not found")
t = t.replace(old_globs, new_globs)

old_return = """            plants.update(PLANT_RE.findall(txt))
    return domains, plants"""
new_return = """            plants.update(PLANT_RE.findall(txt))
    for path in sorted(Path("/tmp").glob("ttf-r*-occ-*.txt")):
        try:
            lines = [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        except OSError:
            continue
        if "domain" in path.name:
            domains.update(lines)
        else:
            plants.update(lines)
            plants.update(PLANT_RE.findall("\\n".join(lines)))
    return domains, plants"""
if old_return not in t:
    raise SystemExit("harvest return not found")
t = t.replace(old_return, new_return, 1)

# extra banned domains from r85-r95 in-flight gens
insert_banned = '''    "phosphate-defluor-kiln",
    "silicon-carbide-acheson",
    "imperial-smelting-furnace",
    "lfp-carbothermal-kiln",
    "ammonia-oxidation-burner",
    "waelz-kiln",
    "autothermal-reformer",
    "peirce-smith-converter",
    "propane-dehydrogenation",
    "silicomanganese-furnace",
}'''
extra_banned = '''    "phosphate-defluor-kiln",
    "silicon-carbide-acheson",
    "imperial-smelting-furnace",
    "lfp-carbothermal-kiln",
    "ammonia-oxidation-burner",
    "waelz-kiln",
    "autothermal-reformer",
    "peirce-smith-converter",
    "propane-dehydrogenation",
    "silicomanganese-furnace",
    "molybdenum-concentrate-roaster",
    "chlorosilane-disproportionation",
    "tantalum-sodium-reducer",
    "pbt-esterification-kettle",
    "v2o5-flake-furnace",
    "carbon-disulfide-retort",
    "methanol-lurgi-converter",
    "ferronickel-rkef",
    "acetaldehyde-wacker",
    "titanium-tetrachloride-chlorinator",
    "pentaerythritol-condenser",
    "vanadium-pentoxide-flaker",
    "titanium-tetrachloride-still",
    "neopentyl-glycol-aldol",
    "isoprene-acetonitrile-extract",
    "gallium-arsenide-czochralski",
    "cyanuric-chloride-loop",
    "zirconium-tetrachloride-still",
    "xanthan-gum-fermenter",
    "indium-cementation-cell",
    "silicone-d4-equilibrator",
    "polyether-polyol-alkoxylator",
    "pmma-bulk-reactor",
    "h2o2-ao-hydrogenator",
    "optical-fiber-mcvd",
    "zirconium-sand-chlorinator",
    "indium-sulfate-electrowin",
    "niobium-aluminotherm-crucible",
    "calcium-cyanamide-rotary",
    "gallium-arsenide-lec-puller",
    "caprolactone-baeyer-villiger",
    "polyether-polyol-alkoxylation",
    "indium-phosphide-lpe",
    "boron-nitride-hotpress",
    "potassium-permanganate-oxidizer",
    "hexamethylenediamine-hydrogenator",
    "ethyl-acetate-tishchenko",
    "precipitated-silica-reactor",
    "nmc-precursor-coprecip",
    "copper-foil-electrodeposition",
    "hexamethylene-diamine-hydrogenator",
    "mek-dehydrogenation-bed",
    "zirconium-kroll-retort",
    "linear-alkylbenzene-hf-alkylation",
    "lactide-ring-opening",
    "arsenic-trioxide-sublimer",
    "cyclohexanone-oxime-rearranger",
    "gadolinium-electrorefiner",
    "tetrahydrofuran-dehydrator",
    "indium-phosphide-mbe",
    "dimethyl-carbonate-transester",
    "ethyl-tert-butyl-ether",
    "sodium-perchlorate-cell",
    "pentaerythritol-aldol",
    "ptfe-dispersion-autoclave",
}'''
if insert_banned not in t:
    raise SystemExit("banned insert point not found")
t = t.replace(insert_banned, extra_banned)

# extra banned plants
insert_plants = '''    "Nasicon-Holt",
)'''
extra_plants = '''    "Nasicon-Holt",
    "Powellite-Strath",
    "Chlorosil-Ingle",
    "Tantalate-Lode",
    "Butylene-Moor",
    "Vanadate-Stow",
    "Dimcarb-Twine",
    "Etherbut-Lynns",
    "Perchlate-Meres",
    "Pentaol-Croftle",
    "Fluoropl-Staithe",
    "Disulfid-Linn",
    "Lurgi-Thwaite",
    "Garnier-Beck",
    "Wacker-Holm",
    "Chlorid-Hope",
    "Pentaol-Bield",
    "Flaker-Sneck",
    "Titantet-Stell",
    "Neopent-Lair",
    "Isopren-Twine",
    "Gaas-Wynd",
    "Cyanur-Stow",
    "Zirconyl-Thwaite",
    "Xanthan-Toft",
    "Indium-Grain",
    "Silox-Frith",
    "Alkox-Grove",
    "Pmma-Chine",
    "Hydranth-Ley",
    "McVd-Hanger",
    "Indate-Slack",
    "Niobate-Combe",
    "Cyanamid-Rigg",
    "Gallate-Sike",
    "Caprol-Stang",
    "Alkoxyl-Nab",
    "Indphos-Lythe",
    "Nitridex-Dike",
    "Permang-Edge",
    "Diamine-Law",
    "Acetate-Glen",
    "Silica-Leat",
    "Precursor-Moss",
    "Foil-Crag",
    "Adnamine-Wray",
    "Mekone-Howe",
    "Zirconia-Yair",
    "Alkylate-Naze",
    "Polylact-Eyot",
    "Arsenolite-Gair",
    "Ketoxime-Dene",
    "Gadolinia-Voe",
    "Oxolane-Reen",
    "Phosphide-Cairn",
)'''
if insert_plants not in t:
    raise SystemExit("plant insert point not found")
t = t.replace(insert_plants, extra_plants)

# THIS_DOMAINS / THIS_PLANTS header
t = t.replace(
    '''THIS_DOMAINS = (
    "sodium-dithionite-reducer",
    "methyl-isobutyl-ketone-still",
    "lithium-cobalt-oxide-calciner",
    "gamma-butyrolactone-dehydro",
    "ppta-polymerizer",
)
THIS_PLANTS = (
    "Dithion-Hawse",
    "Mibk-Grain",
    "Lithcox-Beck",
    "Gbl-Reen",
    "Ppta-Slack",
)''',
    '''THIS_DOMAINS = (
    "sodium-dithionite-reducer",
    "methyl-isobutyl-ketone-still",
    "lithium-cobalt-oxide-calciner",
    "gamma-butyrolactone-dehydro",
    "ppta-polymerizer",
)
THIS_PLANTS = (
    "Dithion-Hawse",
    "Mibk-Grain",
    "Lithcox-Beck",
    "Gbl-Reen",
    "Ppta-Slack",
)''',
)

# 507 self-check still looking for etbe after earlier replace of issues strings
t = t.replace("policy.etbe_go", "policy.mibk_go")
t = t.replace("policy.etbe_hold", "policy.mibk_hold")
t = t.replace('"etbe_go"', '"mibk_go"')
t = t.replace('"etbe_hold"', '"mibk_hold"')

# LIF note leftover methanolate
t = t.replace("formate-clamp bias", "formate-clamp bias")
t = t.replace("Neurons 0-13 carry +0.64 formate-clamp bias", "Neurons 0-13 carry +0.64 formate-clamp bias")
t = t.replace("16 mm packed-bed slump", "16 mm reducer-bed slump")
t = t.replace("16 mm reducer-bed slump", "16 mm reducer-bed slump")

p.write_text(t, encoding="utf-8")
print("patched", p, "bytes", p.stat().st_size)
# sanity
need = [
    "ttf-r98-506",
    "watchdog_is_pv",
    "WATCHDOG_TIMEOUT",
    "sodium-dithionite-reducer",
    "Ppta-Slack",
    "policy.mibk_hold",
    "record_510",
    "meta.round != 98",
]
for n in need:
    if n not in t:
        print("MISSING", n)
bad = ["ttf-r86", "etbe_hold", "STALE_HANDSHAKE", "heartbeat_is_pv", "Dimcarb-Twine"]
for n in bad:
    if n in t:
        print("LEFTOVER", n, t.count(n))
print("handshake leftover", t.count("handshake"), "HART leftover", t.count("HART"))
print("autoclave leftover", t.count("autoclave"), "electrolyte leftover", t.count("electrolyte"))
print("formaldehyde leftover", t.count("formaldehyde"), "methanolate leftover", t.count("methanolate"))
print("meoh leftover", t.count("meoh"))
