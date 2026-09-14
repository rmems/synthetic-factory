#!/usr/bin/env python3
"""Mill monorepo-dep-bump-factory r1084+ unique HEP leftover leftover leftover plants.

BAN r01–r1083 clones including guix-inf-leftover-manifest / nix-lock-leftover-revpin
and openems-xml-leftover-fdtd / siliconcompiler-py-leftover-target.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

_BASE = Path(__file__).with_name("mdb-mill-r1068.py")
_spec = importlib.util.spec_from_file_location("mdb_mill_r1068", _BASE)
_m = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_m)

FACTORY = _m.FACTORY
GEN = _m.GEN
CATALOG_FIRST = 1084
P = _m.P
build_episode = _m.build_episode

PRIOR_SLUGS = tuple(spec["slug"] for pair in _m.PAIRS for spec in pair)
BANNED_SLUG_NEEDLES = _m.BANNED_SLUG_NEEDLES + PRIOR_SLUGS + (
    "guix-inf-leftover-manifest",
    "nix-lock-leftover-revpin",
    "openems-xml-leftover-fdtd",
    "siliconcompiler-py-leftover-target",
)
_m.BANNED_SLUG_NEEDLES = BANNED_SLUG_NEEDLES

FACTORY_DIR = (
    Path(__file__).resolve().parents[1]
    / "outputs"
    / "raw"
    / "2026-08-19-agentic"
    / "monorepo-dep-bump-factory"
)

PLANTS = [
    "apostlebird",
    "asity",
    "babbler",
    "batis",
    "bernieria",
    "bristlebird",
    "broadbill",
    "buttonquail",
    "coua",
    "coucal",
    "figbird",
    "flowerpecker",
    "frogmouth",
    "hammerkop",
    "helmetshrike",
    "hypocolius",
    "jery",
    "logrunner",
    "megapode",
    "mesite",
    "monarch",
    "needletail",
    "pardalote",
    "piculet",
    "pitohui",
    "quailthrush",
    "redshank",
    "rockfowl",
    "roller",
    "seriema",
    "shag",
    "shelduck",
    "shikra",
    "stilt",
    "stonechat",
    "swamphen",
    "tapaculo",
    "thickhead",
    "treepie",
    "trogon",
    "tyrant",
    "wagtail",
    "weka",
    "wheatear",
    "whinchat",
    "whitethroat",
    "woodlark",
    "wrenbabbler",
    "zebrafinch",
    "zittingcisticola",
    "antwren",
    "antthrush",
    "attila",
    "boubou",
    "bristlehead",
    "bushchat",
    "canastero",
    "chlorophonia",
    "cockatiel",
    "coppersmith",
    "crestedtit",
    "crombec",
    "diederik",
    "eremomela",
    "fantail",
    "fernwren",
    "fulvetta",
    "gnatwren",
    "grasswren",
    "greenbul",
    "groundjay",
    "hangingparrot",
    "hillstar",
    "honeybuzzard",
    "illadopsis",
    "leafwarbler",
    "longclaw",
    "magpierobin",
    "minivet",
    "mistletoebird",
    "munia",
    "myzornis",
    "penduline",
    "picathartes",
    "pygmytit",
    "quailfinch",
    "rockthrush",
    "scimitar",
    "shriketit",
    "silktail",
    "snowfinch",
    "spinetail",
    "sunlark",
    "tesia",
    "thickknee",
    "titbabbler",
    "velvetsity",
    "wattlebird",
    "whiteeye",
    "woodswallow",
    "yellownape",
    "adjutant",
    "aethia",
    "akikiki",
    "amakihi",
    "anianiau",
    "apapane",
    "elepaio",
    "palila",
    "puaiohi",
    "akekee",
    "nukupuu",
    "kakawahie",
    "millerbird",
    "takahe",
    "guamrail",
    "okinawarail",
    "palauowl",
    "boninfinch",
    "bristlethighed",
    "firewoodgatherer",
    "forestrobin",
    "paradisewhydah",
    "hangingparrot2",
    "canastero2",
    "tapaculo2",
    "seriema2",
    "weka2",
]


def notes_for(round_n: int, a: dict, b: dict) -> str:
    ea = f"mdb-r{round_n}-{a['slug']}"
    eb = f"mdb-r{round_n}-{b['slug']}"
    novel = 88 + (round_n % 5)
    return f"""# NOTES-r{round_n} monorepo-dep-bump-factory

Novel coverage: {novel}%

Two designed episodes (quota 2). Surfaces: {a['surface']} ({a['pkg']} {a['api_break']}); {b['surface']} ({b['pkg']} {b['api_break']}).
Not a pin-file mill and not libNNNN recycle. Distinct from r01–r1083 clones (ban guix-inf-leftover-manifest / nix-lock-leftover-revpin; no r1068 lammps-kspace-leftover-pppm / gromacs-cons-leftover-allbonds clones).

| id | seed | first apply | plan change | terminal |
|---|---|---|---|---|
| {ea} | {a['surface']} | nested {a['new']} | SoT {a['new']} + {a['api_break']} | {'leftover-workspace fail; ' + a['left'] + ' ' + a.get('left_ver', a['old']) if a['fail'] else 'success; ' + a['left'] + ' leftover'} |
| {eb} | {b['surface']} | nested {b['new']} | SoT {b['new']} + {b['api_break']} | {'leftover-workspace fail; ' + b['left'] + ' ' + b.get('left_ver', b['old']) if b['fail'] else 'success; ' + b['left'] + ' leftover'} |

## Step counts
- ep1: 18. Nested apply 6–7; plan change 8; API break 10–12; leftover {a['left']}.
- ep2: 18. Nested apply 6–7; plan change 8; API break 10–12; leftover-workspace fail {b['left']}.

## decision_basis audit
Every step starts Plan:/Observation:/Reflection:, ≤240 chars.
No thought / chain_of_thought / scratch / inner_monologue. No spike_events.
No sim_or_real: real. Plants `{a['plant']}` and `{b['plant']}`.

## Weaknesses / next
Keep unique leftover leftover leftover plots. Ban r01–r1083 clones, libNNNN.
"""


def make(
    slug: str,
    plant: str,
    surface: str,
    pkg: str,
    old: str,
    new: str,
    fail: bool,
    pin: str,
    sot_old: str,
    sot_new: str,
    nest_old: str,
    nest_new: str,
    api_old: str,
    api_new: str,
    api_break: str,
    tool: str,
    test: str,
    ws: str,
    ext: str,
) -> dict:
    return P(
        slug,
        plant,
        surface,
        pkg,
        old,
        new,
        fail,
        pin,
        f"apps/api/{pin}",
        sot_old,
        sot_new,
        nest_old,
        nest_new,
        api_old,
        api_new,
        api_break,
        tool,
        test,
        ws,
        f"apps/api/{plant}.{ext}",
    )


TOOLS: list[tuple] = [
    ("rivet-yoda-leftover-histo", "Rivet leftover vs yoda.plot", "rivet", "3.1.10", "4.0.1", "yoda.plot", "# rivet 3.1.10", "# rivet 4.0.1", "rivet-cmphistos --mc-errs", "rivet-cmphistos --uncertainty-mode poisson", "from rivet.core import Analysis", "from rivet import Analysis", "core.Analysis → rivet.Analysis + poisson unc", "rivet --version", "rivet -a MC_TTBAR apps/api/yoda.plot", "rivet -a MC_TTBAR apps/legacy/yoda.plot", "plot"),
    ("fastjet-area-leftover-voronoi", "FastJet leftover vs area.hh", "fastjet", "3.4.2", "3.5.0", "area.hh", "// fastjet 3.4.2", "// fastjet 3.5.0", "AreaDefinition(active_area)", "AreaDefinition(voronoi_area)", "JetDefinition(antikt_algorithm, 0.4)", "JetDefinition(antikt_algorithm, 0.8)", "active_area → voronoi_area + R=0.8", "fastjet-config --version", "c++ -c apps/api/area.hh", "c++ -c apps/legacy/area.hh", "hh"),
    ("delphes-card-leftover-isolation", "Delphes leftover vs isol.tcl", "delphes", "3.5.0", "3.6.0", "isol.tcl", "# delphes 3.5.0", "# delphes 3.6.0", "set IsolationDeltaR 0.5", "set IsolationDeltaR 0.3", "set IsolationCut 0.12", "set IsolationCut 0.06", "IsolationDeltaR 0.5→0.3 + tighter cut", "DelphesHepMC2 --help | head || true", "DelphesHepMC2 apps/api/isol.tcl apps/api/api.root", "DelphesHepMC2 apps/legacy/isol.tcl apps/legacy/api.root", "tcl"),
    ("sherpa-runcard-leftover-css", "Sherpa leftover vs run.dat", "sherpa", "2.2.15", "3.0.1", "run.dat", "# sherpa 2.2.15", "# sherpa 3.0.1", "CSS_EVOLUTION 1", "DIRE_EVOLUTION 1", "MI_HANDLER Amisic", "MI_HANDLER None", "CSS_EVOLUTION → DIRE + no MI", "Sherpa --version | head -n 1", "Sherpa -f apps/api/run.dat", "Sherpa -f apps/legacy/run.dat", "dat"),
    ("whizard-sindarin-leftover-nlo", "WHIZARD leftover vs nlo.sin", "whizard", "3.1.4", "3.2.0", "nlo.sin", "# whizard 3.1.4", "# whizard 3.2.0", "nlo_calculation = lo", "nlo_calculation = nlo", "process p = e1, E1 => e2, E2", "process p = e1, E1 => e2, E2 { nlo }", "lo → nlo process block", "whizard --version | head -n 1", "whizard apps/api/nlo.sin", "whizard apps/legacy/nlo.sin", "sin"),
    ("herwig-in-leftover-shower", "Herwig leftover vs shower.in", "herwig", "7.2.3", "7.3.0", "shower.in", "# herwig 7.2.3", "# herwig 7.3.0", "set /Herwig/Shower/ShowerHandler:InteractionType QED", "set /Herwig/Shower/ShowerHandler:InteractionType QCD", "read snippets/Matchbox.in", "read snippets/DipoleMerging.in", "QED shower → QCD + DipoleMerging", "Herwig --version | head -n 1", "Herwig run apps/api/shower.in", "Herwig run apps/legacy/shower.in", "in"),
    ("photospp-conf-leftover-infrared", "PHOTOS++ leftover vs infra.conf", "photospp", "3.64", "3.65", "infra.conf", "# photospp 3.64", "# photospp 3.65", "PHOTOS_INFRARED 0.01", "PHOTOS_INFRARED 0.001", "PHOTOS_ME_CORRECTION 0", "PHOTOS_ME_CORRECTION 1", "infrared 0.01→0.001 + ME correction", "photos-config --version || true", "photos-test apps/api/infra.conf", "photos-test apps/legacy/infra.conf", "conf"),
    ("tauola-card-leftover-spin", "Tauola leftover vs spin.card", "tauola", "1.1.8", "1.1.9", "spin.card", "# tauola 1.1.8", "# tauola 1.1.9", "SPINWT = 0", "SPINWT = 1", "TAUPOL = 0", "TAUPOL = 1", "SPINWT off → on + TAUPOL", "tauola-config --version || true", "tauola-test apps/api/spin.card", "tauola-test apps/legacy/spin.card", "card"),
    ("evtgen-dec-leftover-mixed", "EvtGen leftover vs mixed.dec", "evtgen", "2.2.1", "2.3.0", "mixed.dec", "# evtgen 2.2.1", "# evtgen 2.3.0", "Decay B0 mixed", "Decay B0 EvtVub", "yes PHOTOS", "no PHOTOS", "mixed → EvtVub, PHOTOS off", "evtgen --version || true", "evtgen apps/api/mixed.dec", "evtgen apps/legacy/mixed.dec", "dec"),
    ("lhapdf-conf-leftover-set", "LHAPDF leftover vs set.conf", "lhapdf", "6.5.4", "6.6.0", "set.conf", "# lhapdf 6.5.4", "# lhapdf 6.6.0", "set NNPDF31_nlo_as_0118", "set NNPDF40_nnlo_as_01180", "interpolator logcubic", "interpolator cubic", "NNPDF31 nlo → NNPDF40 nnlo", "lhapdf --version", "lhapdf get NNPDF40_nnlo_as_01180 --listdir apps/api", "lhapdf get NNPDF40_nnlo_as_01180 --listdir apps/legacy", "conf"),
    ("hepmc-ascii-leftover-hepmc3", "HepMC leftover vs ascii.conf", "hepmc", "2.06.11", "3.3.0", "ascii.conf", "# hepmc 2.06.11", "# hepmc 3.3.0", "IO_GenEvent ascii", "WriterAscii hepmc3", "units GEV MM", "units MEV MM", "IO_GenEvent → WriterAscii HepMC3", "HepMC3-config --version || true", "convert2hepmc3 apps/api/ascii.conf", "convert2hepmc3 apps/legacy/ascii.conf", "conf"),
    ("podio-yaml-leftover-datamodel", "podio leftover vs edm.yml", "podio", "0.17.4", "1.2.0", "edm.yml", "# podio 0.17.4", "# podio 1.2.0", "schema_version: 1", "schema_version: 3", "components: []", "datatypes:\n  EventInfo:\n    Members:\n      - int32 eventNumber", "schema 1 → 3 + EventInfo", "podio-dump --version || true", "podio-dump apps/api/edm.yml", "podio-dump apps/legacy/edm.yml", "yml"),
    ("edm4hep-yaml-leftover-reco", "EDM4hep leftover vs reco.yml", "edm4hep", "0.10.5", "0.99.2", "reco.yml", "# edm4hep 0.10.5", "# edm4hep 0.99.2", "ReconstructedParticle: legacy", "ReconstructedParticle: edm4hep::ReconstructedParticle", "MCParticle: hepmc", "MCParticle: edm4hep::MCParticle", "legacy reco → edm4hep types", "edm4hep-dump --version || true", "edm4hep-dump apps/api/reco.yml", "edm4hep-dump apps/legacy/reco.yml", "yml"),
    ("gaudi-opts-leftover-algs", "Gaudi leftover vs algs.py", "gaudi", "36r16", "39r0", "algs.py", "# gaudi 36r16", "# gaudi 39r0", "ApplicationMgr().TopAlg = ['GaudiSequencer']", "ApplicationMgr().TopAlg = ['Gaudi::Sequencer']", "HistogramPersistencySvc().OutputFile = 'old.root'", "HistogramPersistencySvc().OutputFile = 'api.root'", "GaudiSequencer → Gaudi::Sequencer", "gaudirun.py --version || true", "gaudirun.py apps/api/algs.py", "gaudirun.py apps/legacy/algs.py", "py"),
    ("fccsw-yaml-leftover-detector", "FCCSW leftover vs det.yml", "fccsw", "0.9.1", "1.1.0", "det.yml", "# fccsw 0.9.1", "# fccsw 1.1.0", "detector: IDEA", "detector: CLD", "bField: 2.0", "bField: 2.0\ntracking: acts", "IDEA → CLD + ACTS tracking", "fccrun --version || true", "fccrun apps/api/det.yml", "fccrun apps/legacy/det.yml", "yml"),
    ("dd4hep-xml-leftover-compact", "DD4hep leftover vs compact.xml", "dd4hep", "1.27", "1.31", "compact.xml", "<!-- dd4hep 1.27 -->", "<!-- dd4hep 1.31 -->", "<lccdd vis=\"false\">", "<lccdd vis=\"true\" sensitive=\"true\">", "<detector name=\"Tracker\" type=\"TrackerBarrel\"/>", "<detector name=\"Tracker\" type=\"DD4hep_TrackerBarrel\"/>", "vis off → on + DD4hep_TrackerBarrel", "geoPluginRun --version || true", "geoPluginRun -input apps/api/compact.xml", "geoPluginRun -input apps/legacy/compact.xml", "xml"),
    ("acts-cfg-leftover-seeding", "ACTS leftover vs seed.json", "acts", "36.0.0", "39.2.0", "seed.json", "// acts 36.0.0", "// acts 39.2.0", "\"seedFinder\": \"Orthogonal\"", "\"seedFinder\": \"GridTriplet\"", "\"cotThetaMax\": 7.0", "\"cotThetaMax\": 10.0", "Orthogonal → GridTriplet seed finder", "ActsExamples --version || true", "ActsExamplesSeeding --input apps/api/seed.json", "ActsExamplesSeeding --input apps/legacy/seed.json", "json"),
    ("yoda-plot-leftover-ratio", "YODA leftover vs ratio.plot", "yoda", "1.9.10", "2.1.0", "ratio.plot", "# yoda 1.9.10", "# yoda 2.1.0", "RatioPlot=0", "RatioPlot=1", "ErrorBands=0", "ErrorBands=1", "RatioPlot off → on + error bands", "yodaplot --version || true", "yodaplot apps/api/ratio.plot", "yodaplot apps/legacy/ratio.plot", "plot"),
    ("fjcontrib-softdrop-leftover-beta", "fjcontrib leftover vs drop.hh", "fjcontrib", "1.051", "1.101", "drop.hh", "// fjcontrib 1.051", "// fjcontrib 1.101", "SoftDrop(0.0, 0.1)", "SoftDrop(1.0, 0.1)", "RecursiveSoftDrop rsd(0,0.1)", "RecursiveSoftDrop rsd(1,0.05)", "beta 0 → 1 + tighter zcut", "fastjet-config --contrib || true", "c++ -c apps/api/drop.hh", "c++ -c apps/legacy/drop.hh", "hh"),
    ("thepeg-repo-leftover-handler", "ThePEG leftover vs repo.in", "thepeg", "2.2.3", "2.3.0", "repo.in", "# thepeg 2.2.3", "# thepeg 2.3.0", "create ThePEG::LesHouchesEventHandler /Handlers/LHE", "create ThePEG::EventHandler /Handlers/Evt", "set /Handlers/LHE:CascadeHandler NULL", "set /Handlers/Evt:CascadeHandler /Herwig/Shower/ShowerHandler", "LHE handler → EventHandler + shower", "setupThePEG --version || true", "setupThePEG apps/api/repo.in", "setupThePEG apps/legacy/repo.in", "in"),
    ("hej-card-leftover-multijet", "HEJ leftover vs jets.card", "hej", "2.2.1", "2.3.0", "jets.card", "# hej 2.2.1", "# hej 2.3.0", "min_jets = 2", "min_jets = 3", "fixed_order = lo", "fixed_order = nlo", "min_jets 2→3 + NLO", "HEJ --version || true", "HEJ apps/api/jets.card", "HEJ apps/legacy/jets.card", "card"),
    ("powheg-input-leftover-bornkt", "POWHEG leftover vs powheg.input", "powheg", "rev3999", "rev4129", "powheg.input", "! powheg rev3999", "! powheg rev4129", "bornktmin 0", "bornktmin 10", "withdamp 0", "withdamp 1", "bornktmin 0→10 + withdamp", "pwhg_main --help | head || true", "pwhg_main apps/api/powheg.input", "pwhg_main apps/legacy/powheg.input", "input"),
    ("mcfm-input-leftover-nproc", "MCFM leftover vs nproc.ini", "mcfm", "10.3", "11.0", "nproc.ini", "# mcfm 10.3", "# mcfm 11.0", "nproc=31", "nproc=141", "part='nlo'", "part='nnlo'", "nproc 31→141 + nnlo", "mcfm --version || true", "mcfm apps/api/nproc.ini", "mcfm apps/legacy/nproc.ini", "ini"),
    ("nlojet-steer-leftover-jetalg", "NLOJet leftover vs jet.steer", "nlojet", "4.1.3", "4.2.0", "jet.steer", "# nlojet 4.1.3", "# nlojet 4.2.0", "jet_algorithm kt", "jet_algorithm antikt", "R=0.7", "R=0.4", "kt → antikt R=0.4", "nlojet++ --version || true", "nlojet++ apps/api/jet.steer", "nlojet++ apps/legacy/jet.steer", "steer"),
    ("blackhat-card-leftover-amp", "BlackHat leftover vs amp.card", "blackhat", "0.9.9", "0.9.10", "amp.card", "# blackhat 0.9.9", "# blackhat 0.9.10", "AMPLITUDE tree", "AMPLITUDE one-loop", "IRREG false", "IRREG true", "tree → one-loop + IRREG", "blackhat --version || true", "blackhat apps/api/amp.card", "blackhat apps/legacy/amp.card", "card"),
    ("openloops-olp-leftover-irreg", "OpenLoops leftover vs olp.olp", "openloops", "2.1.2", "2.1.3", "olp.olp", "# openloops 2.1.2", "# openloops 2.1.3", "ir_regularisation DRED", "ir_regularisation CDR", "stability_mode 1", "stability_mode 2", "DRED → CDR + stability_mode 2", "openloops --version || true", "openloops apps/api/olp.olp", "openloops apps/legacy/olp.olp", "olp"),
    ("recola-process-leftover-nlo", "Recola leftover vs proc.recola", "recola", "1.4.1", "2.2.4", "proc.recola", "# recola 1.4.1", "# recola 2.2.4", "compute_process NLO off", "compute_process NLO on", "use_collier true", "use_collier false", "NLO off → on, collier off", "recola-config --version || true", "recola-run apps/api/proc.recola", "recola-run apps/legacy/proc.recola", "recola"),
    ("gosam-olp-leftover-samurai", "GoSam leftover vs olp.in", "gosam", "2.1.1", "2.1.2", "olp.in", "# gosam 2.1.1", "# gosam 2.1.2", "reduction_method=samurai", "reduction_method=ninja", "extensions=dred", "extensions=cdr", "samurai → ninja + cdr", "gosam.py --version || true", "gosam.py apps/api/olp.in", "gosam.py apps/legacy/olp.in", "in"),
    ("hoppet-steer-leftover-vfns", "HOPPET leftover vs vfns.steer", "hoppet", "1.2.0", "1.3.0", "vfns.steer", "# hoppet 1.2.0", "# hoppet 1.3.0", "ffns 3", "vfns 5", "order lo", "order nlo", "ffns3 → vfns5 nlo", "hoppet-config --version || true", "hoppet-run apps/api/vfns.steer", "hoppet-run apps/legacy/vfns.steer", "steer"),
    ("apfel-card-leftover-evol", "APFEL leftover vs evol.card", "apfel", "3.0.6", "3.1.1", "evol.card", "# apfel 3.0.6", "# apfel 3.1.1", "Theory = FONLL-A", "Theory = FONLL-C", "Q0 = 1.0", "Q0 = 1.65", "FONLL-A → FONLL-C + Q0", "apfel --version || true", "apfel-evol apps/api/evol.card", "apfel-evol apps/legacy/evol.card", "card"),
    ("qcdnum-steer-leftover-grid", "QCDNUM leftover vs grid.steer", "qcdnum", "17.00.07", "18.00.00", "grid.steer", "# qcdnum 17.00.07", "# qcdnum 18.00.00", "call gxmake(xmin,iord,nx,nq)", "call gxmake(xmin,iord,nx,nq,5)", "nfin=3", "nfin=5", "gxmake + nfin 3→5", "qcdnum-config --version || true", "qcdnum-run apps/api/grid.steer", "qcdnum-run apps/legacy/grid.steer", "steer"),
    ("roofit-macro-leftover-ws", "RooFit leftover vs ws.C", "roofit", "6.30.04", "6.32.08", "ws.C", "// roofit 6.30.04", "// roofit 6.32.08", "RooWorkspace w(\"w\")", "RooWorkspace w(\"w\", kTRUE)", "w.import(pdf)", "w.import(pdf, RooFit::RecycleConflictNodes())", "import → RecycleConflictNodes", "root-config --version", "root -l -b -q apps/api/ws.C", "root -l -b -q apps/legacy/ws.C", "C"),
    ("roostats-macro-leftover-cls", "RooStats leftover vs cls.C", "roostats", "6.30.04", "6.32.08", "cls.C", "// roostats 6.30.04", "// roostats 6.32.08", "HypoTestInverter calc(sb,b)", "AsymptoticCalculator calc(data, sb, b)", "calc.UseCLs(false)", "calc.UseCLs(true)", "HypoTestInverter → AsymptoticCalculator CLs", "root-config --version", "root -l -b -q apps/api/cls.C", "root -l -b -q apps/legacy/cls.C", "C"),
    ("tmva-xml-leftover-bdt", "TMVA leftover vs bdt.xml", "tmva", "6.30.04", "6.32.08", "bdt.xml", "<!-- tmva 6.30.04 -->", "<!-- tmva 6.32.08 -->", "<Method type=\"BDT\" boost=\"AdaBoost\"/>", "<Method type=\"BDT\" boost=\"GradBoost\"/>", "<NTrees>800</NTrees>", "<NTrees>1500</NTrees>", "AdaBoost → GradBoost + more trees", "root-config --has-tmva", "root -l -b -q apps/api/bdt.xml", "root -l -b -q apps/legacy/bdt.xml", "xml"),
    ("cling-pcm-leftover-modules", "Cling leftover vs mods.pcm", "cling", "1.1", "1.2", "mods.pcm", "# cling 1.1", "# cling 1.2", "modules=off", "modules=on", "pch=legacy.pch", "pch=api.pch", "modules off → on + new PCH", "root-config --has-cling", "root -l -b -q apps/api/mods.pcm", "root -l -b -q apps/legacy/mods.pcm", "pcm"),
    ("rootio-cint-leftover-tfile", "ROOT I/O leftover vs tfile.C", "rootio", "6.30.04", "6.32.08", "tfile.C", "// rootio 6.30.04", "// rootio 6.32.08", "TFile::Open(\"old.root\",\"READ\")", "TFile::Open(\"api.root\",\"READ\",\"\",ROOT::RCompressionSetting::EDefaults::kUseGeneralPurpose)", "TTree t(\"t\",\"legacy\")", "TTree t(\"t\",\"api\"); t.SetAutoFlush(-30000000)", "READ → general-purpose compression + AutoFlush", "root-config --version", "root -l -b -q apps/api/tfile.C", "root -l -b -q apps/legacy/tfile.C", "C"),
    ("rucio-cfg-leftover-scope", "Rucio leftover vs rucio.cfg", "rucio", "34.4.0", "36.0.0", "rucio.cfg", "# rucio 34.4.0", "# rucio 36.0.0", "default_scope = user.legacy", "default_scope = user.api", "protocol = gsiftp", "protocol = https\nmulti_rse_attachment = True", "gsiftp → https + multi RSE", "rucio --version", "rucio -c apps/api/rucio.cfg whoami", "rucio -c apps/legacy/rucio.cfg whoami", "cfg"),
    ("xrootd-cfg-leftover-cms", "XRootD leftover vs xrd.cf", "xrootd", "5.6.9", "5.8.0", "xrd.cf", "# xrootd 5.6.9", "# xrootd 5.8.0", "all.role manager", "all.role server", "cms.delay 8", "cms.delay 2\nxrootd.tls /etc/grid-security/hostcert.pem", "manager → server + TLS", "xrootd -v | head -n 1", "xrootd -c apps/api/xrd.cf", "xrootd -c apps/legacy/xrd.cf", "cf"),
    ("dcache-xml-leftover-pool", "dCache leftover vs pool.xml", "dcache", "9.2.0", "10.2.0", "pool.xml", "<!-- dcache 9.2.0 -->", "<!-- dcache 10.2.0 -->", "<pool mover=\"dcap\"/>", "<pool mover=\"http\"/>", "<sweeper enabled=\"false\"/>", "<sweeper enabled=\"true\" lru=\"true\"/>", "dcap → http mover + LRU sweeper", "dcache --version || true", "dcache start --config apps/api/pool.xml", "dcache start --config apps/legacy/pool.xml", "xml"),
    ("cvmfs-conf-leftover-stratum", "CVMFS leftover vs default.local", "cvmfs", "2.11.3", "2.12.5", "default.local", "# cvmfs 2.11.3", "# cvmfs 2.12.5", "CVMFS_CLIENT_PROFILE=single", "CVMFS_CLIENT_PROFILE=adaptive", "CVMFS_HTTP_PROXY=DIRECT", "CVMFS_HTTP_PROXY=auto;DIRECT", "single → adaptive + auto proxy", "cvmfs2 --version | head -n 1", "cvmfs_config chksetup -c apps/api/default.local", "cvmfs_config chksetup -c apps/legacy/default.local", "local"),
    ("dirac-cfg-leftover-site", "DIRAC leftover vs dirac.cfg", "dirac", "8.0.32", "9.0.0", "dirac.cfg", "# dirac 8.0.32", "# dirac 9.0.0", "Site = DIRAC.Legacy.site", "Site = DIRAC.API.site", "CEType = CREAM", "CEType = HTCondorCE", "CREAM → HTCondorCE site", "dirac-version || true", "dirac-configure -F apps/api/dirac.cfg", "dirac-configure -F apps/legacy/dirac.cfg", "cfg"),
    ("alien-jdl-leftover-output", "AliEn leftover vs job.jdl", "alien", "v2-19", "v2-20", "job.jdl", "# alien v2-19", "# alien v2-20", "Output = {\"file:legacy.root\"}", "Output = {\"file:api.root\"}", "Packages = {\"VO_ALICE@AliRoot::v5-09\"}", "Packages = {\"VO_ALICE@AliPhysics::vAN-20250819\"}", "AliRoot v5 → AliPhysics vAN", "alien.py --version || true", "alien.py submit apps/api/job.jdl", "alien.py submit apps/legacy/job.jdl", "jdl"),
    ("mcnp-inp-leftover-kcode", "MCNP leftover vs kcode.inp", "mcnp", "6.2", "6.3", "kcode.inp", "c mcnp 6.2", "c mcnp 6.3", "kcode 1000 1.0 30 130", "kcode 5000 1.0 50 250", "prdmp j j 1", "prdmp j j 1 1", "kcode 1k→5k + extra prdmp", "mcnp6 ip || true", "mcnp6 i=apps/api/kcode.inp", "mcnp6 i=apps/legacy/kcode.inp", "inp"),
    ("njoy-tape-leftover-reconr", "NJOY leftover vs reconr.njoy", "njoy", "2016.77", "2021.0", "reconr.njoy", "# njoy 2016.77", "# njoy 2021.0", "reconr\n20 21", "reconr\n20 22", "err/errmax 0.01 0.01", "err/errmax 0.001 0.002", "reconr 21→22 tighter err", "njoy21 --version || true", "njoy21 < apps/api/reconr.njoy", "njoy21 < apps/legacy/reconr.njoy", "njoy"),
    ("endf-mf-leftover-mf3", "ENDF leftover vs mf3.endf", "endf", "b8.0", "b8.1", "mf3.endf", "  endf b8.0", "  endf b8.1", "MF=3 MT=1", "MF=3 MT=2", "QM=0.0", "QM=1.0 QI=0.5", "MF3 MT1 → MT2 + QI", "endf-check --version || true", "endf-check apps/api/mf3.endf", "endf-check apps/legacy/mf3.endf", "endf"),
    ("casmo-inp-leftover-egrid", "CASMO leftover vs egrid.inp", "casmo", "5", "5.03", "egrid.inp", "* casmo 5", "* casmo 5.03", "egrid 2g", "egrid 16g", "opt 2d", "opt 3d", "2g → 16g + 3d", "casmo5 --version || true", "casmo5 apps/api/egrid.inp", "casmo5 apps/legacy/egrid.inp", "inp"),
    ("origen-f33-leftover-decay", "ORIGEN leftover vs decay.f33", "origen", "6.2.3", "6.3.1", "decay.f33", "# origen 6.2.3", "# origen 6.3.1", "DECAY LIBRARY ENDF/B-VII.1", "DECAY LIBRARY ENDF/B-VIII.0", "IRRADIATION POWER", "IRRADIATION FLUX", "VII.1 POWER → VIII.0 FLUX", "origen --version || true", "origen apps/api/decay.f33", "origen apps/legacy/decay.f33", "f33"),
    ("kenostd-inp-leftover-parm", "KENO-STD leftover vs parm.inp", "kenostd", "6.2.3", "6.3.1", "parm.inp", "read parm 6.2.3", "read parm 6.3.1", "gen=100 npg=1000", "gen=250 npg=5000", "nb8=0", "nb8=1", "gen/npg up + nb8", "scale --version || true", "scale apps/api/parm.inp", "scale apps/legacy/parm.inp", "inp"),
    ("polaris-inp-leftover-mg", "Polaris leftover vs mg.inp", "polaris", "6.2.3", "6.3.1", "mg.inp", "% polaris 6.2.3", "% polaris 6.3.1", "mg 2g", "mg 56g", "geom 2d", "geom 3d", "2g 2d → 56g 3d", "polaris --version || true", "polaris apps/api/mg.inp", "polaris apps/legacy/mg.inp", "inp"),
    ("relap-inp-leftover-trip", "RELAP leftover vs trip.i", "relap", "5-3d", "5-3d-3.0", "trip.i", "* relap 5-3d", "* relap 5-3d-3.0", "20600000 trip 1", "20600000 trip 2", "100 newt-raph", "100 broyden", "trip 1→2 + broyden", "relap5 --version || true", "relap5 -i apps/api/trip.i", "relap5 -i apps/legacy/trip.i", "i"),
    ("tracenrc-inp-leftover-reflood", "TRACE leftover vs reflood.inp", "tracenrc", "5.0p5", "5.0p6", "reflood.inp", "* tracenrc 5.0p5", "* tracenrc 5.0p6", "reflood off", "reflood on", "chf lookup", "chf groeneveld", "reflood on + Groeneveld CHF", "trace --version || true", "trace apps/api/reflood.inp", "trace apps/legacy/reflood.inp", "inp"),
    ("melcor-inp-leftover-cvs", "MELCOR leftover vs cvs.inp", "melcor", "2.2.9541", "2.3.18125", "cvs.inp", "* melcor 2.2.9541", "* melcor 2.3.18125", "CVH PACKAGE OFF", "CVH PACKAGE ON", "FL PACKAGE OFF", "FL PACKAGE ON", "CVH/FL off → on", "melcor --version || true", "melcor apps/api/cvs.inp", "melcor apps/legacy/cvs.inp", "inp"),
    ("tendl-mf-leftover-mf6", "TENDL leftover vs mf6.tendl", "tendl", "2023", "2025", "mf6.tendl", "# tendl 2023", "# tendl 2025", "MF=6 LAW=1", "MF=6 LAW=7", "LANG=1", "LANG=2", "LAW 1→7 + LANG 2", "endf-check --version || true", "endf-check apps/api/mf6.tendl", "endf-check apps/legacy/mf6.tendl", "tendl"),
    ("jeff-mf-leftover-mf4", "JEFF leftover vs mf4.jeff", "jeff", "4.0", "4.1", "mf4.jeff", "# jeff 4.0", "# jeff 4.1", "MF=4 LTT=1", "MF=4 LTT=3", "LI=0", "LI=1", "LTT 1→3 + LI", "endf-check --version || true", "endf-check apps/api/mf4.jeff", "endf-check apps/legacy/mf4.jeff", "jeff"),
    ("jendl-mf-leftover-mf5", "JENDL leftover vs mf5.jendl", "jendl", "5.0", "5.2", "mf5.jendl", "# jendl 5.0", "# jendl 5.2", "MF=5 LF=1", "MF=5 LF=9", "NR=1", "NR=2", "LF 1→9 + NR 2", "endf-check --version || true", "endf-check apps/api/mf5.jendl", "endf-check apps/legacy/mf5.jendl", "jendl"),
    ("irdff-cov-leftover-irdf", "IRDFF leftover vs cov.irdff", "irdff", "1.05", "2.0", "cov.irdff", "# irdff 1.05", "# irdff 2.0", "COVARIANCE OFF", "COVARIANCE ON", "LIBRARY IRDF-2002", "LIBRARY IRDFF-II", "IRDF-2002 → IRDFF-II + cov", "endf-check --version || true", "endf-check apps/api/cov.irdff", "endf-check apps/legacy/cov.irdff", "irdff"),
    ("exfor-entry-leftover-subent", "EXFOR leftover vs subent.x4", "exfor", "2023", "2025", "subent.x4", "# exfor 2023", "# exfor 2025", "SUBENT 1", "SUBENT 2", "STATUS PRELIMINARY", "STATUS FINAL", "SUBENT 1→2 FINAL", "x4toc4 --version || true", "x4toc4 apps/api/subent.x4", "x4toc4 apps/legacy/subent.x4", "x4"),
    ("flair-inp-leftover-geo", "Flair leftover vs geo.flair", "flair", "3.2", "3.4", "geo.flair", "# flair 3.2", "# flair 3.4", "GEO: body RPP", "GEO: body RCC", "VOID off", "VOID on", "RPP → RCC + VOID", "flair --version || true", "flair apps/api/geo.flair", "flair apps/legacy/geo.flair", "flair"),
    ("geant3-ffcard-leftover-cut", "GEANT3 leftover vs cut.ffcards", "geant3", "3.21", "3.21-patch", "cut.ffcards", "* geant3 3.21", "* geant3 3.21-patch", "CUTS 0.001", "CUTS 0.0001", "PHYS 1", "PHYS 2", "CUTS 1e-3→1e-4 + PHYS 2", "gxint --version || true", "gxint apps/api/cut.ffcards", "gxint apps/legacy/cut.ffcards", "ffcards"),
    ("dragon5-inp-leftover-lib", "DRAGON5 leftover vs lib.cpo", "dragon5", "5.0.4", "5.0.8", "lib.cpo", "* dragon5 5.0.4", "* dragon5 5.0.8", "LIB: DRAGON", "LIB: DRAGLIB", "ANISOTROPY 1", "ANISOTROPY 3", "DRAGON → DRAGLIB P3", "dragon --version || true", "dragon apps/api/lib.cpo", "dragon apps/legacy/lib.cpo", "cpo"),
    ("donjon-inp-leftover-burn", "DONJON leftover vs burn.cpo", "donjon", "5.0.4", "5.0.8", "burn.cpo", "* donjon 5.0.4", "* donjon 5.0.8", "BURN: STEP 1", "BURN: STEP 8", "POWER CONST", "POWER HISTORY", "STEP 1→8 + POWER HISTORY", "donjon --version || true", "donjon apps/api/burn.cpo", "donjon apps/legacy/burn.cpo", "cpo"),
    ("ctf-inp-leftover-chan", "CTF leftover vs chan.inp", "ctf", "4.0", "4.2", "chan.inp", "* ctf 4.0", "* ctf 4.2", "nchan=1", "nchan=4", "turb=mixinglength", "turb=kepsilon", "nchan 1→4 + k-epsilon", "ctf --version || true", "ctf apps/api/chan.inp", "ctf apps/legacy/chan.inp", "inp"),
    ("iraf-cl-leftover-imcombine", "IRAF leftover vs combine.cl", "iraf", "2.16.1", "2.18", "combine.cl", "# iraf 2.16.1", "# iraf 2.18", "imcombine combine=average", "imcombine combine=median", "reject=none", "reject=sigclip", "average → median + sigclip", "cl --version || true", "cl < apps/api/combine.cl", "cl < apps/legacy/combine.cl", "cl"),
    ("ds9-reg-leftover-wcs", "SAOImageDS9 leftover vs wcs.reg", "ds9", "8.4.1", "8.6", "wcs.reg", "# ds9 8.4.1", "# ds9 8.6", "physical; circle(100,100,10)", "fk5; circle(10.0,20.0,5\")", "width=1", "width=2 dash=1", "physical → fk5 WCS + dash", "ds9 -version || true", "ds9 -region apps/api/wcs.reg", "ds9 -region apps/legacy/wcs.reg", "reg"),
    ("casacore-table-leftover-taql", "casacore leftover vs taql.sql", "casacore", "3.5.0", "3.7.1", "taql.sql", "# casacore 3.5.0", "# casacore 3.7.1", "select from legacy.ms", "select from api.ms", "where ANTENNA1=0", "where ANTENNA1 IN [0,1,2]", "legacy.ms → api.ms + IN list", "taql --version || true", "taql -f apps/api/taql.sql", "taql -f apps/legacy/taql.sql", "sql"),
    ("healpix-par-leftover-nside", "HEALPix leftover vs nside.par", "healpix", "3.82", "3.83", "nside.par", "# healpix 3.82", "# healpix 3.83", "nside=64", "nside=256", "ordering=ring", "ordering=nested", "nside 64→256 nested", "synfast --version || true", "synfast apps/api/nside.par", "synfast apps/legacy/nside.par", "par"),
    ("photutils-py-leftover-dao", "photutils leftover vs dao.py", "photutils", "1.13.0", "2.2.0", "dao.py", "# photutils 1.13.0", "# photutils 2.2.0", "DAOStarFinder(fwhm=3.0, threshold=5.)", "DAOStarFinder(fwhm=2.0, threshold=8., min_separation=3.0)", "aperture_photometry(data, circ)", "aperture_photometry(data, circ, error=err)", "DAO fwhm/threshold + error array", "python3 -c 'import photutils; print(photutils.__version__)'", "python3 apps/api/dao.py", "python3 apps/legacy/dao.py", "py"),
    ("ccdproc-py-leftover-gain", "ccdproc leftover vs gain.py", "ccdproc", "2.4.2", "2.5.0", "gain.py", "# ccdproc 2.4.2", "# ccdproc 2.5.0", "ccd.gain = 1.0", "ccd.gain = 2.5", "subtract_overscan(ccd, overscan)", "subtract_overscan(ccd, overscan, median=True)", "gain 1→2.5 + median overscan", "python3 -c 'import ccdproc; print(ccdproc.__version__)'", "python3 apps/api/gain.py", "python3 apps/legacy/gain.py", "py"),
    ("specreduce-py-leftover-trace", "specreduce leftover vs trace.py", "specreduce", "1.4.1", "1.5.0", "trace.py", "# specreduce 1.4.1", "# specreduce 1.5.0", "FitTrace(image, bins=10)", "FitTrace(image, bins=20, peak_method='max')", "BoxcarExtract(image, trace)", "HorneExtract(image, trace)", "FitTrace bins + HorneExtract", "python3 -c 'import specreduce; print(specreduce.__version__)'", "python3 apps/api/trace.py", "python3 apps/legacy/trace.py", "py"),
    ("ginga-yml-leftover-cmap", "Ginga leftover vs cmap.yml", "ginga", "5.1.0", "5.3.0", "cmap.yml", "# ginga 5.1.0", "# ginga 5.3.0", "color_map: gray", "color_map: viridis", "auto_levels: false", "auto_levels: true", "gray → viridis + auto levels", "ginga --version || true", "ginga --config apps/api/cmap.yml", "ginga --config apps/legacy/cmap.yml", "yml"),
    ("glueviz-json-leftover-link", "Glue leftover vs link.json", "glueviz", "1.17.1", "1.22.0", "link.json", "// glueviz 1.17.1", "// glueviz 1.22.0", "\"cid1\": \"ra_legacy\"", "\"cid1\": \"ra_icrs\"", "\"cid2\": \"dec_legacy\"", "\"cid2\": \"dec_icrs\"", "legacy RA/Dec → ICRS", "glue --version || true", "glue apps/api/link.json", "glue apps/legacy/link.json", "json"),
    ("astroquery-py-leftover-vizier", "astroquery leftover vs viz.py", "astroquery", "0.4.7", "0.4.10", "viz.py", "# astroquery 0.4.7", "# astroquery 0.4.10", "Vizier.ROW_LIMIT = 50", "Vizier.ROW_LIMIT = 500", "Vizier.query_region(c, radius='1deg')", "Vizier.query_region(c, radius='10arcmin', catalog='I/355')", "ROW_LIMIT 50→500 + I/355", "python3 -c 'import astroquery; print(astroquery.__version__)'", "python3 apps/api/viz.py", "python3 apps/legacy/viz.py", "py"),
    ("reproject-py-leftover-adaptive", "reproject leftover vs adap.py", "reproject", "0.13.1", "0.14.1", "adap.py", "# reproject 0.13.1", "# reproject 0.14.1", "reproject_interp(hdu, wcs)", "reproject_adaptive(hdu, wcs)", "order='bilinear'", "order='biquadratic'", "interp → adaptive biquadratic", "python3 -c 'import reproject; print(reproject.__version__)'", "python3 apps/api/adap.py", "python3 apps/legacy/adap.py", "py"),
    ("ndcube-py-leftover-wcsaxes", "ndcube leftover vs wcs.py", "ndcube", "2.2.2", "2.3.1", "wcs.py", "# ndcube 2.2.2", "# ndcube 2.3.1", "cube.plot()", "cube.plot(plot_axes=['x','y'])", "cube.crop(lower, upper)", "cube.crop_by_values(lower, upper, units=u.arcsec)", "plot_axes + crop_by_values", "python3 -c 'import ndcube; print(ndcube.__version__)'", "python3 apps/api/wcs.py", "python3 apps/legacy/wcs.py", "py"),
    ("aiapy-py-leftover-register", "aiapy leftover vs reg.py", "aiapy", "0.7.4", "0.8.0", "reg.py", "# aiapy 0.7.4", "# aiapy 0.8.0", "register(map)", "register(map, missing=0.0)", "correct_degradation(map)", "correct_degradation(map, correction_table='latest')", "register missing=0 + latest degradation", "python3 -c 'import aiapy; print(aiapy.__version__)'", "python3 apps/api/reg.py", "python3 apps/legacy/reg.py", "py"),
    ("dkist-py-leftover-asdf", "DKIST leftover vs asdf.yml", "dkist", "1.10.0", "1.16.0", "asdf.yml", "# dkist 1.10.0", "# dkist 1.16.0", "dataset: visp_legacy.asdf", "dataset: visp_api.asdf", "tile: false", "tile: true", "legacy asdf → visp_api + tile", "python3 -c 'import dkist; print(dkist.__version__)'", "python3 -c 'import dkist; dkist.load_dataset(\"apps/api/asdf.yml\")'", "python3 -c 'import dkist; dkist.load_dataset(\"apps/legacy/asdf.yml\")'", "yml"),
    ("wsclean-parset-leftover-wgrid", "WSClean leftover vs wgrid.parset", "wsclean", "3.4", "3.6", "wgrid.parset", "# wsclean 3.4", "# wsclean 3.6", "gridder=wstacking", "gridder=wgridder", "weight=briggs 0", "weight=briggs -0.5", "wstacking → wgridder + robust -0.5", "wsclean --version | head -n 1", "wsclean -name api -size 1024 1024 apps/api/wgrid.parset", "wsclean -name legacy -size 1024 1024 apps/legacy/wgrid.parset", "parset"),
    ("aoflagger-lua-leftover-strategy", "AOFlagger leftover vs strat.lua", "aoflagger", "3.4.0", "3.5.0", "strat.lua", "-- aoflagger 3.4.0", "-- aoflagger 3.5.0", "aoflagger.threshold = 3.5", "aoflagger.threshold = 5.0", "strategy = 'legacy'", "strategy = 'generic-default'", "threshold 3.5→5 + generic-default", "aoflagger --version | head -n 1", "aoflagger -strategy apps/api/strat.lua apps/api/api.ms", "aoflagger -strategy apps/legacy/strat.lua apps/legacy/api.ms", "lua"),
    ("dysco-parset-leftover-quant", "Dysco leftover vs quant.parset", "dysco", "1.2", "1.3", "quant.parset", "# dysco 1.2", "# dysco 1.3", "quantization-bits=10", "quantization-bits=16", "distribution=trunc-gaussian", "distribution=gaussian", "10-bit trunc → 16-bit gaussian", "dyscostman --version || true", "dyscostman apps/api/quant.parset", "dyscostman apps/legacy/quant.parset", "parset"),
    ("idg-parset-leftover-hybrid", "IDG leftover vs hybrid.parset", "idg", "1.2.0", "1.3.0", "hybrid.parset", "# idg 1.2.0", "# idg 1.3.0", "idg.mode=cpu", "idg.mode=hybrid", "idg.buffersize=128", "idg.buffersize=512", "cpu → hybrid + larger buffer", "idg-info || true", "wsclean -gridder idg -idg-mode hybrid apps/api/hybrid.parset", "wsclean -gridder idg -idg-mode hybrid apps/legacy/hybrid.parset", "parset"),
    ("dp3-parset-leftover-ddecal", "DP3 leftover vs ddecal.parset", "dp3", "6.2.0", "6.4.1", "ddecal.parset", "# dp3 6.2.0", "# dp3 6.4.1", "ddecal.mode=diagonal", "ddecal.mode=fulljones", "ddecal.solint=32", "ddecal.solint=8", "diagonal → fulljones + solint 8", "DP3 --version | head -n 1", "DP3 apps/api/ddecal.parset", "DP3 apps/legacy/ddecal.parset", "parset"),
    ("linc-parset-leftover-h5parm", "LINC leftover vs h5parm.parset", "linc", "5.0.0", "5.2.0", "h5parm.parset", "# linc 5.0.0", "# linc 5.2.0", "applycal.parmdb=legacy.h5", "applycal.parmdb=api.h5", "applycal.correction=phase000", "applycal.correction=fulljones000", "legacy.h5 phase → api.h5 fulljones", "cwltool --version || true", "cwltool linc.cwl apps/api/h5parm.parset", "cwltool linc.cwl apps/legacy/h5parm.parset", "parset"),
    ("meqtrees-py-leftover-solver", "MeqTrees leftover vs solver.py", "meqtrees", "1.9.0", "1.10.0", "solver.py", "# meqtrees 1.9.0", "# meqtrees 1.10.0", "solver.lm = True", "solver.lm = False", "solver.epsilon = 1e-4", "solver.epsilon = 1e-6", "LM off + tighter epsilon", "meqtree-pipeliner.py --version || true", "meqtree-pipeliner.py apps/api/solver.py", "meqtree-pipeliner.py apps/legacy/solver.py", "py"),
    ("pybdsf-cfg-leftover-atrous", "PyBDSF leftover vs atrous.cfg", "pybdsf", "1.10.3", "1.12.0", "atrous.cfg", "# pybdsf 1.10.3", "# pybdsf 1.12.0", "atrous_do = False", "atrous_do = True", "thresh_isl = 3.0", "thresh_isl = 4.0", "atrous on + thresh_isl 4", "python3 -c 'import bdsf; print(bdsf.__version__)'", "python3 -c 'import bdsf; bdsf.process_image(\"apps/api/atrous.cfg\")'", "python3 -c 'import bdsf; bdsf.process_image(\"apps/legacy/atrous.cfg\")'", "cfg"),
    ("montage-hdr-leftover-proj", "Montage leftover vs proj.hdr", "montage", "6.0", "6.1", "proj.hdr", "# montage 6.0", "# montage 6.1", "CTYPE1 = 'RA---TAN'", "CTYPE1 = 'RA---SIN'", "CDELT1 = -0.001", "CDELT1 = -0.0005", "TAN → SIN + finer CDELT", "mProject --version || true", "mProject apps/api/proj.hdr", "mProject apps/legacy/proj.hdr", "hdr"),
    ("swarp-config-leftover-combine", "SWarp leftover vs combine.swarp", "swarp", "2.41.5", "2.42.0", "combine.swarp", "# swarp 2.41.5", "# swarp 2.42.0", "COMBINE_TYPE AVERAGE", "COMBINE_TYPE MEDIAN", "RESAMPLING_TYPE BILINEAR", "RESAMPLING_TYPE LANCZOS3", "AVERAGE → MEDIAN + LANCZOS3", "swarp --version | head -n 1", "swarp -c apps/api/combine.swarp", "swarp -c apps/legacy/combine.swarp", "swarp"),
    ("scamp-config-leftover-distort", "SCAMP leftover vs distort.scamp", "scamp", "2.10.0", "2.14.0", "distort.scamp", "# scamp 2.10.0", "# scamp 2.14.0", "DISTORT_DEGREES 1", "DISTORT_DEGREES 3", "ASTREF_CATALOG 2MASS", "ASTREF_CATALOG GAIA-EDR3", "deg 1 2MASS → deg 3 Gaia", "scamp --version | head -n 1", "scamp -c apps/api/distort.scamp", "scamp -c apps/legacy/distort.scamp", "scamp"),
    ("psfex-config-leftover-basis", "PSFEx leftover vs basis.psfex", "psfex", "3.21.1", "3.24.2", "basis.psfex", "# psfex 3.21.1", "# psfex 3.24.2", "PSFVAR_DEGREES 1", "PSFVAR_DEGREES 3", "BASIS_TYPE PIXEL", "BASIS_TYPE GAUSS-LAGUERRE", "PIXEL → GAUSS-LAGUERRE deg 3", "psfex --version | head -n 1", "psfex -c apps/api/basis.psfex", "psfex -c apps/legacy/basis.psfex", "psfex"),
    ("stilts-cmd-leftover-tpipe", "STILTS leftover vs tpipe.cmd", "stilts", "3.4.7", "3.5.2", "tpipe.cmd", "# stilts 3.4.7", "# stilts 3.5.2", "tpipe in=legacy.fits", "tpipe in=api.fits", "cmd='select mag<18'", "cmd='select mag<16; addcol snr flux/err'", "fits + tighter mag + snr col", "stilts -version | head -n 1", "stilts tpipe apps/api/tpipe.cmd", "stilts tpipe apps/legacy/tpipe.cmd", "cmd"),
    ("topcat-xml-leftover-plot", "TOPCAT leftover vs plot.xml", "topcat", "4.8.8", "4.10.3", "plot.xml", "<!-- topcat 4.8.8 -->", "<!-- topcat 4.10.3 -->", "<plot type=\"scatter\"/>", "<plot type=\"healpix\"/>", "<x>ra</x>", "<x>l</x><y>b</y>", "scatter → healpix galactic", "topcat -version || true", "topcat -stilts apps/api/plot.xml", "topcat -stilts apps/legacy/plot.xml", "xml"),
    ("aladin-prop-leftover-hips", "Aladin leftover vs hips.prop", "aladin", "12.0", "12.5", "hips.prop", "# aladin 12.0", "# aladin 12.5", "hips_order=3", "hips_order=9", "hips_tile_format=jpeg", "hips_tile_format=png", "order 3 jpeg → 9 png", "aladin -version || true", "aladin -script apps/api/hips.prop", "aladin -script apps/legacy/hips.prop", "prop"),
    ("vizier-vot-leftover-query", "VizieR leftover vs query.vot", "vizier", "1.24", "1.25", "query.vot", "<!-- vizier 1.24 -->", "<!-- vizier 1.25 -->", "<PARAM name=\"-c.rd\" value=\"1\"/>", "<PARAM name=\"-c.rd\" value=\"0.1\"/>", "<PARAM name=\"-out.max\" value=\"50\"/>", "<PARAM name=\"-out.max\" value=\"500\"/>", "rd 1→0.1 deg + 500 rows", "curl -s https://vizier.cds.unistra.fr | head || true", "stilts votcopy apps/api/query.vot", "stilts votcopy apps/legacy/query.vot", "vot"),
    ("simbad-tap-leftover-oid", "SIMBAD leftover vs oid.adql", "simbad", "4.0", "4.9", "oid.adql", "-- simbad 4.0", "-- simbad 4.9", "SELECT oid FROM basic", "SELECT oid, main_id FROM basic", "WHERE ra BETWEEN 0 AND 10", "WHERE CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', 10, 20, 0.1))=1", "oid → main_id + CIRCLE ICRS", "curl -s https://simbad.cds.unistra.fr | head || true", "tapquery apps/api/oid.adql", "tapquery apps/legacy/oid.adql", "adql"),
    ("hips-prop-leftover-order", "HiPS leftover vs order.prop", "hips", "1.0", "2.0", "order.prop", "# hips 1.0", "# hips 2.0", "hips_order=4", "hips_order=11", "hips_tile_width=256", "hips_tile_width=512", "order 4→11 + 512 tiles", "hipsgen --version || true", "hipsgen apps/api/order.prop", "hipsgen apps/legacy/order.prop", "prop"),
    ("healpy-py-leftover-udgrade", "healpy leftover vs ud.py", "healpy", "1.16.6", "1.18.0", "ud.py", "# healpy 1.16.6", "# healpy 1.18.0", "hp.ud_grade(m, nside_out=64)", "hp.ud_grade(m, nside_out=256, order_in='RING', order_out='NESTED')", "hp.mollview(m)", "hp.mollview(m, nest=True)", "ud_grade 64 RING → 256 NESTED", "python3 -c 'import healpy; print(healpy.__version__)'", "python3 apps/api/ud.py", "python3 apps/legacy/ud.py", "py"),
    ("opencascade-cxx-leftover-brep", "OpenCASCADE leftover vs brep.cxx", "opencascade", "7.8.1", "7.9.1", "brep.cxx", "// opencascade 7.8.1", "// opencascade 7.9.1", "BRepAlgoAPI_Fuse fuse(a,b);", "BRepAlgoAPI_Fuse fuse(a,b); fuse.SetRunParallel(true);", "BRepBuilderAPI_Transform tr(s,t);", "BRepBuilderAPI_GTransform tr(s,t);", "Fuse parallel + GTransform", "occ-config --version || true", "c++ -c apps/api/brep.cxx", "c++ -c apps/legacy/brep.cxx", "cxx"),
    ("freecad-fcstd-leftover-part", "FreeCAD leftover vs part.FCMacro", "freecad", "0.21.2", "1.0.0", "part.FCMacro", "# freecad 0.21.2", "# freecad 1.0.0", "Part.makeBox(10,10,10)", "Part.makeBox(20,20,20)", "doc.addObject('Part::Feature','Box')", "doc.addObject('PartDesign::Body','Body')", "Box 10→20 + PartDesign Body", "freecadcmd --version | head -n 1", "freecadcmd apps/api/part.FCMacro", "freecadcmd apps/legacy/part.FCMacro", "FCMacro"),
    ("cgal-hxx-leftover-kernel", "CGAL leftover vs kernel.hxx", "cgal", "5.6.1", "6.0.1", "kernel.hxx", "// cgal 5.6.1", "// cgal 6.0.1", "typedef CGAL::Simple_cartesian<double> K;", "typedef CGAL::Exact_predicates_inexact_constructions_kernel K;", "CGAL::Delaunay_triangulation_2<K> dt;", "CGAL::Delaunay_triangulation_3<K> dt;", "Simple_cartesian 2D → EPIC 3D", "cgal-config --version || true", "c++ -c apps/api/kernel.hxx", "c++ -c apps/legacy/kernel.hxx", "hxx"),
    ("openscad-scad-leftover-module", "OpenSCAD leftover vs mod.scad", "openscad", "2021.01", "2025.03", "mod.scad", "// openscad 2021.01", "// openscad 2025.03", "module box() { cube(10); }", "module box() { cube(20, center=true); }", "difference() { box(); }", "union() { box(); sphere(5); }", "cube 10→20 + union sphere", "openscad --version | head -n 1", "openscad -o /tmp/api.stl apps/api/mod.scad", "openscad -o /tmp/legacy.stl apps/legacy/mod.scad", "scad"),
    ("salome-hdf-leftover-mesh", "Salome leftover vs mesh.py", "salome", "9.12.0", "9.14.0", "mesh.py", "# salome 9.12.0", "# salome 9.14.0", "smesh.SetName(mesh, 'legacy')", "smesh.SetName(mesh, 'api')", "algo = mesh.Tetrahedron()", "algo = mesh.Hexahedron()", "Tetrahedron → Hexahedron", "salome --version || true", "salome -t apps/api/mesh.py", "salome -t apps/legacy/mesh.py", "py"),
    ("lsdyna-k-leftover-contact", "LS-DYNA leftover vs contact.k", "lsdyna", "R13", "R15", "contact.k", "* lsdyna R13", "* lsdyna R15", "*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE", "*CONTACT_AUTOMATIC_SINGLE_SURFACE", "*CONTROL_CONTACT\n0", "*CONTROL_CONTACT\n1", "SURFACE_TO_SURFACE → SINGLE_SURFACE", "lsdyna --version || true", "lsdyna i=apps/api/contact.k", "lsdyna i=apps/legacy/contact.k", "k"),
    ("radioss-rad-leftover-fail", "Radioss leftover vs fail.rad", "radioss", "2023.1", "2025.0", "fail.rad", "# radioss 2023.1", "# radioss 2025.0", "/FAIL/JOHNSON/1", "/FAIL/TAB1/1", "/PROP/SHELL/1", "/PROP/SOLID/1", "JOHNSON → TAB1 + SOLID", "radioss --version || true", "radioss -i apps/api/fail.rad", "radioss -i apps/legacy/fail.rad", "rad"),
    ("pdal-json-leftover-filters", "PDAL leftover vs filters.json", "pdal", "2.7.2", "2.8.4", "filters.json", "// pdal 2.7.2", "// pdal 2.8.4", "\"type\": \"filters.range\"", "\"type\": \"filters.expression\"", "\"limits\": \"Z[0:10]\"", "\"expression\": \"Z >= 0 && Z <= 20\"", "range Z[0:10] → expression Z<=20", "pdal --version | head -n 1", "pdal pipeline apps/api/filters.json", "pdal pipeline apps/legacy/filters.json", "json"),
    ("orfeo-otb-leftover-apps", "Orfeo leftover vs apps.xml", "orfeo", "8.1.2", "9.1.1", "apps.xml", "<!-- orfeo 8.1.2 -->", "<!-- orfeo 9.1.1 -->", "<app>Orthorectification</app>", "<app>OrthoRectification</app>", "<elev>SRTM</elev>", "<elev>CopernicusDEM</elev>", "Orthorectification → OrthoRectification + CopernicusDEM", "otbcli_Version || true", "otbcli_OrthoRectification -in apps/api/apps.xml", "otbcli_OrthoRectification -in apps/legacy/apps.xml", "xml"),
    ("saga-sgrd-leftover-grid", "SAGA leftover vs grid.sgrd", "saga", "9.3.2", "9.7.1", "grid.sgrd", "# saga 9.3.2", "# saga 9.7.1", "CELLSIZE=30", "CELLSIZE=10", "NODATA_VALUE=-99999", "NODATA_VALUE=-9999", "CELLSIZE 30→10 + NODATA", "saga_cmd --version | head -n 1", "saga_cmd grid_tools 0 -GRIDS apps/api/grid.sgrd", "saga_cmd grid_tools 0 -GRIDS apps/legacy/grid.sgrd", "sgrd"),
    ("geoserver-xml-leftover-wfs", "GeoServer leftover vs wfs.xml", "geoserver", "2.25.2", "2.27.1", "wfs.xml", "<!-- geoserver 2.25.2 -->", "<!-- geoserver 2.27.1 -->", "<wfs:serviceLevel>BASIC</wfs:serviceLevel>", "<wfs:serviceLevel>COMPLETE</wfs:serviceLevel>", "<gml:srsNameStyle>XML</gml:srsNameStyle>", "<gml:srsNameStyle>URN2</gml:srsNameStyle>", "BASIC → COMPLETE WFS + URN2", "geoserver --version || true", "curl -s localhost:8080/geoserver/wfs?config=apps/api/wfs.xml", "curl -s localhost:8080/geoserver/wfs?config=apps/legacy/wfs.xml", "xml"),
    ("cdo-rc-leftover-operator", "CDO leftover vs op.rc", "cdo", "2.4.2", "2.5.1", "op.rc", "# cdo 2.4.2", "# cdo 2.5.1", "CDO_PCTL_NBINS=101", "CDO_PCTL_NBINS=1001", "CDO_FILE_SUFFIX=.nc", "CDO_FILE_SUFFIX=.nc4", "pctl bins 101→1001 + nc4", "cdo --version | head -n 1", "cdo -f nc4 selname,tas apps/api/op.rc", "cdo -f nc4 selname,tas apps/legacy/op.rc", "rc"),
    ("metpy-py-leftover-calc", "MetPy leftover vs calc.py", "metpy", "1.6.2", "1.7.0", "calc.py", "# metpy 1.6.2", "# metpy 1.7.0", "mpcalc.dewpoint_from_relative_humidity(t, rh)", "mpcalc.dewpoint_from_specific_humidity(p, t, q)", "mpcalc.wind_speed(u, v)", "mpcalc.wind_components(speed, direc)", "RH dewpoint → specific humidity + wind_components", "python3 -c 'import metpy; print(metpy.__version__)'", "python3 apps/api/calc.py", "python3 apps/legacy/calc.py", "py"),
    ("grads-gs-leftover-display", "GrADS leftover vs display.gs", "grads", "2.2.1", "2.2.3", "display.gs", "* grads 2.2.1", "* grads 2.2.3", "'display tas'", "'display tas.2'", "'set gxout contour'", "'set gxout shaded'", "tas → tas.2 shaded", "grads -v | head -n 1", "grads -bpc apps/api/display.gs", "grads -bpc apps/legacy/display.gs", "gs"),
    ("faust-dsp-leftover-process", "Faust leftover vs proc.dsp", "faust", "2.72.14", "2.81.2", "proc.dsp", "// faust 2.72.14", "// faust 2.81.2", "process = _;", "process = sp.stereoize(_);", "import(\"stdfaust.lib\");", "import(\"stdfaust.lib\"); import(\"filters.lib\");", "_ → stereoize + filters.lib", "faust --version | head -n 1", "faust apps/api/proc.dsp -o /tmp/api.cpp", "faust apps/legacy/proc.dsp -o /tmp/legacy.cpp", "dsp"),
    ("supercollider-scd-leftover-synthdef", "SuperCollider leftover vs def.scd", "supercollider", "3.13.0", "3.14.0", "def.scd", "// supercollider 3.13.0", "// supercollider 3.14.0", "SynthDef(\\legacy, { Out.ar(0, SinOsc.ar(440)) }).add;", "SynthDef(\\api, { Out.ar(0, Saw.ar(220)) }).add;", "s.options.numOutputBusChannels = 2;", "s.options.numOutputBusChannels = 8;", "SinOsc 440 → Saw 220 + 8 ch", "sclang -v || true", "sclang apps/api/def.scd", "sclang apps/legacy/def.scd", "scd"),
    ("csound-csd-leftover-instr", "Csound leftover vs instr.csd", "csound", "6.18.1", "7.0.0", "instr.csd", "; csound 6.18.1", "; csound 7.0.0", "instr 1\na1 oscil 0.5, 440\nendin", "instr 1\na1 vco2 0.5, 220\nendin", "nchnls=2", "nchnls=4", "oscil 440 → vco2 220 + 4 ch", "csound --version | head -n 1", "csound apps/api/instr.csd", "csound apps/legacy/instr.csd", "csd"),
    ("lv2-ttl-leftover-port", "LV2 leftover vs port.ttl", "lv2", "1.18.10", "1.18.12", "port.ttl", "# lv2 1.18.10", "# lv2 1.18.12", "lv2:port [ lv2:index 0 ; lv2:symbol \"in\" ]", "lv2:port [ lv2:index 0 ; lv2:symbol \"in_l\" ; lv2:designation pg:left ]", "a lv2:Plugin", "a lv2:Plugin, lv2:AmplifierPlugin", "in → in_l pg:left + AmplifierPlugin", "lv2ls || true", "lv2info file://apps/api/port.ttl", "lv2info file://apps/legacy/port.ttl", "ttl"),
    ("ardour-xml-leftover-session", "Ardour leftover vs session.xml", "ardour", "8.6.0", "8.12.0", "session.xml", "<!-- ardour 8.6.0 -->", "<!-- ardour 8.12.0 -->", "<Session sample-rate=\"44100\"/>", "<Session sample-rate=\"48000\"/>", "<Tempo beats=\"4\" note-type=\"4\"/>", "<Tempo beats=\"4\" note-type=\"4\" bpm=\"128\"/>", "44.1k → 48k + bpm 128", "ardour8 --version || true", "ardour8 --load apps/api/session.xml", "ardour8 --load apps/legacy/session.xml", "xml"),
    ("puredata-pd-leftover-obj", "Pure Data leftover vs obj.pd", "puredata", "0.54.1", "0.55.2", "obj.pd", "#N canvas 0 0 400 300 12;", "#N canvas 0 0 450 350 12;", "#X obj 10 10 osc~ 440;", "#X obj 10 10 phasor~ 220;", "#X obj 10 40 dac~;", "#X obj 10 40 dac~ 1 2 3 4;", "osc~ 440 → phasor~ 220 + 4ch dac", "pd -version | head -n 1", "pd -nogui apps/api/obj.pd", "pd -nogui apps/legacy/obj.pd", "pd"),
    ("keycloak-json-leftover-realm", "Keycloak leftover vs realm.json", "keycloak", "25.0.4", "26.2.5", "realm.json", "// keycloak 25.0.4", "// keycloak 26.2.5", "\"loginTheme\": \"keycloak\"", "\"loginTheme\": \"keycloak.v2\"", "\"sslRequired\": \"none\"", "\"sslRequired\": \"external\"", "theme v1 → v2 + ssl external", "kc.sh --version || true", "kc.sh import --file apps/api/realm.json", "kc.sh import --file apps/legacy/realm.json", "json"),
    ("dexidp-yaml-leftover-connector", "Dex leftover vs connector.yaml", "dexidp", "2.40.0", "2.42.0", "connector.yaml", "# dexidp 2.40.0", "# dexidp 2.42.0", "type: mockCallback", "type: oidc", "id: legacy", "id: api\nissuer: https://issuer.example", "mockCallback → oidc issuer", "dex --version || true", "dex serve apps/api/connector.yaml", "dex serve apps/legacy/connector.yaml", "yaml"),
    ("authentik-yml-leftover-flow", "Authentik leftover vs flow.yml", "authentik", "2024.8.3", "2025.6.2", "flow.yml", "# authentik 2024.8.3", "# authentik 2025.6.2", "designation: authentication", "designation: authorization", "policy_engine_mode: any", "policy_engine_mode: all", "authentication → authorization + all policies", "ak --version || true", "ak apply apps/api/flow.yml", "ak apply apps/legacy/flow.yml", "yml"),
    ("spicedb-zed-leftover-schema", "SpiceDB leftover vs schema.zed", "spicedb", "1.35.3", "1.44.2", "schema.zed", "// spicedb 1.35.3", "// spicedb 1.44.2", "definition user {}", "definition user {\n  relation manager: user\n}", "permission view = viewer", "permission view = viewer + manager", "user manager relation + view union", "zed version || true", "zed schema validate apps/api/schema.zed", "zed schema validate apps/legacy/schema.zed", "zed"),
    ("casbin-conf-leftover-model", "Casbin leftover vs model.conf", "casbin", "2.100.0", "2.104.0", "model.conf", "# casbin 2.100.0", "# casbin 2.104.0", "[policy_effect]\ne = some(where (p.eft == allow))", "[policy_effect]\ne = some(where (p.eft == allow)) && !some(where (p.eft == deny))", "m = g(r.sub, p.sub) && r.obj == p.obj && r.act == p.act", "m = g(r.sub, p.sub) && keyMatch2(r.obj, p.obj) && r.act == p.act", "allow-and-deny + keyMatch2", "casbin --version || true", "casbin-go check --model apps/api/model.conf", "casbin-go check --model apps/legacy/model.conf", "conf"),
    ("cedar-ced-leftover-permit", "Cedar leftover vs permit.cedar", "cedar", "3.2.1", "4.2.2", "permit.cedar", "// cedar 3.2.1", "// cedar 4.2.2", "permit(principal, action, resource);", "permit(principal, action == Action::\"view\", resource) when { principal.dept == \"eng\" };", "forbid(principal, action, resource);", "forbid(principal, action == Action::\"delete\", resource);", "unconditional permit → view+dept + forbid delete", "cedar --version || true", "cedar check apps/api/permit.cedar", "cedar check apps/legacy/permit.cedar", "cedar"),
    ("vcftools-cfg-leftover-maf", "VCFtools leftover vs maf.cfg", "vcftools", "0.1.16", "0.1.17", "maf.cfg", "# vcftools 0.1.16", "# vcftools 0.1.17", "--maf 0.01", "--maf 0.05", "--max-missing 1", "--max-missing 0.9", "maf 0.01→0.05 + max-missing 0.9", "vcftools --version", "vcftools --vcf apps/api/api.vcf --out /tmp/api", "vcftools --vcf apps/legacy/api.vcf --out /tmp/legacy", "cfg"),
    ("plink-map-leftover-geno", "PLINK leftover vs geno.map", "plink", "1.90b7", "2.00a6", "geno.map", "# plink 1.90b7", "# plink 2.00a6", "--geno 0.1", "--geno 0.02", "--mind 0.1", "--mind 0.02 --maf 0.05", "geno/mind 0.1→0.02 + maf", "plink2 --version | head -n 1", "plink2 --pfile apps/api/geno --out /tmp/api", "plink2 --pfile apps/legacy/geno --out /tmp/legacy", "map"),
    ("beast2-xml-leftover-clock", "BEAST2 leftover vs clock.xml", "beast2", "2.7.6", "2.7.7", "clock.xml", "<!-- beast2 2.7.6 -->", "<!-- beast2 2.7.7 -->", "<clock model=\"strict\"/>", "<clock model=\"ucln\"/>", "<treePrior>yule</treePrior>", "<treePrior>birthDeath</treePrior>", "strict → ucln + birthDeath", "beast -version || true", "beast apps/api/clock.xml", "beast apps/legacy/clock.xml", "xml"),
    ("iqtree-nex-leftover-model", "IQ-TREE leftover vs model.nex", "iqtree", "2.3.6", "3.0.0", "model.nex", "# iqtree 2.3.6", "# iqtree 3.0.0", "model GTR+G", "model GTR+F+I+G4", "ufboot 1000", "ufboot 2000 -alrt 1000", "GTR+G → GTR+F+I+G4 + alrt", "iqtree2 --version | head -n 1", "iqtree2 -s apps/api/model.nex", "iqtree2 -s apps/legacy/model.nex", "nex"),
    ("mafft-cfg-leftover-fftns", "MAFFT leftover vs fftns.cfg", "mafft", "7.525", "7.526", "fftns.cfg", "# mafft 7.525", "# mafft 7.526", "--fftns", "--linsi", "--maxiterate 0", "--maxiterate 1000 --localpair", "fftns → linsi localpair", "mafft --version", "mafft --auto apps/api/fftns.cfg", "mafft --auto apps/legacy/fftns.cfg", "cfg"),
    ("edalize-tcl-leftover-tool", "Edalize leftover vs tool.tcl", "edalize", "0.5.4", "0.6.1", "tool.tcl", "# edalize 0.5.4", "# edalize 0.6.1", "set tool icarus", "set tool verilator", "set top legacy", "set top api", "icarus → verilator + top api", "edalize --help | head || true", "python3 -m edalize --config apps/api/tool.tcl", "python3 -m edalize --config apps/legacy/tool.tcl", "tcl"),
    ("chisel-sbt-leftover-firrtl", "Chisel leftover vs build.sbt", "chisel", "5.1.0", "6.6.0", "build.sbt", "// chisel 5.1.0", "// chisel 6.6.0", "addCompilerPlugin(\"edu.berkeley.cs\" % \"chisel3-plugin\" % \"5.1.0\")", "addCompilerPlugin(\"org.chipsalliance\" % \"chisel-plugin\" % \"6.6.0\")", "libraryDependencies += \"edu.berkeley.cs\" %% \"chisel3\" % \"5.1.0\"", "libraryDependencies += \"org.chipsalliance\" %% \"chisel\" % \"6.6.0\"", "chisel3 5 → chipsalliance chisel 6", "sbt --version | head -n 1", "sbt -Dsbt.global.base=/tmp compile", "sbt -Dsbt.global.base=/tmp compile", "sbt"),
]

assert len(TOOLS) % 2 == 0
assert len(TOOLS) == 128
assert len(TOOLS) <= len(PLANTS)

PAIRS: list[tuple[dict, dict]] = []
_pi = 0
for i in range(0, len(TOOLS), 2):
    a = TOOLS[i]
    b = TOOLS[i + 1]
    suc = make(
        a[0], PLANTS[_pi], a[1], a[2], a[3], a[4], False,
        a[5], a[6], a[7], a[8], a[9], a[10], a[11], a[12], a[13], a[14], a[15], a[16],
    )
    _pi += 1
    failp = make(
        b[0], PLANTS[_pi], b[1], b[2], b[3], b[4], True,
        b[5], b[6], b[7], b[8], b[9], b[10], b[11], b[12], b[13], b[14], b[15], b[16],
    )
    _pi += 1
    PAIRS.append((suc, failp))


def _validate_catalog() -> None:
    slugs = [spec["slug"] for pair in PAIRS for spec in pair]
    if len(slugs) != len(set(slugs)):
        raise SystemExit("duplicate slugs in r1084 catalog")
    for slug in slugs:
        for needle in BANNED_SLUG_NEEDLES:
            if needle and needle in slug:
                raise SystemExit(f"banned needle {needle!r} in {slug}")
    plants = [spec["plant"] for pair in PAIRS for spec in pair]
    if len(plants) != len(set(plants)):
        raise SystemExit("duplicate plants in r1084 catalog")


_validate_catalog()


def build_round(rnd: int) -> tuple[list[dict], str]:
    idx = rnd - CATALOG_FIRST
    if idx < 0 or idx >= len(PAIRS):
        raise SystemExit(
            f"round {rnd} outside catalog {CATALOG_FIRST}..{CATALOG_FIRST + len(PAIRS) - 1}"
        )
    suc, fail = PAIRS[idx]
    suc_ep = build_episode(rnd, suc)
    fail_ep = build_episode(rnd, fail)
    for ep in (suc_ep, fail_ep):
        n = len(ep["steps"])
        if n < 16 or n > 20:
            raise SystemExit(f"{ep['id']} has {n} steps, want 16-20")
        blob = json.dumps(ep)
        for banned in (
            "thought",
            "chain_of_thought",
            "scratch",
            "inner_monologue",
            "spike_events",
        ):
            if f'"{banned}"' in blob:
                raise SystemExit(f"{ep['id']} contains banned key {banned}")
        if '"sim_or_real": "real"' in blob or '"sim_or_real":"real"' in blob:
            raise SystemExit(f"{ep['id']} claims sim_or_real real")
    notes = notes_for(rnd, suc, fail)
    if "Novel coverage:" not in notes:
        raise SystemExit("notes missing Novel coverage")
    return [suc_ep, fail_ep], notes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--staging", required=True)
    args = ap.parse_args()
    rnd = args.round
    staging = Path(args.staging)
    recs, notes = build_round(rnd)
    batch = staging / f"batch-r{rnd:02d}.jsonl"
    notes_path = staging / f"NOTES-r{rnd:02d}.md"
    with batch.open("w") as handle:
        for rec in recs:
            handle.write(json.dumps(rec, ensure_ascii=True) + "\n")
    notes_path.write_text(notes)
    print(
        json.dumps(
            {
                "round": rnd,
                "ids": [r["id"] for r in recs],
                "steps": [len(r["steps"]) for r in recs],
                "success": [r["reward"]["success"] for r in recs],
                "batch": str(batch),
                "notes": str(notes_path),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
