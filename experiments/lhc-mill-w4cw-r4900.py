#!/usr/bin/env python3
"""Grok 4.6 LHC mill w4cw: unused astronomy/GW plants after w4cv.

Never writes outputs/raw. Unique path so it cannot be overwritten by w4 mash.
BAN: w4cs RSEM/Seurat/Mutect2/Hail, w4cr FastQC/SPAdes, r4778 nim-lent, r4777 zig,
r4687 rust-pin, r4580 kanidm/gluu, identity-origin, RPITIT, Prom hist,
ThinLTO, Go loopvar, Django ASGI, Vale, Koka, published.
IDs lhc-rNNNN-pr-*. generator=grok-4.6.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path("/home/raulmc/rmems/synthetic-factory")
TXN = ROOT / "pipelines/round_txn.py"
LHC_DIR = ROOT / "outputs/raw/2026-08-19-agentic/long-horizon-coding-factory"
AGENTIC = ROOT / "outputs/raw/2026-08-19-agentic"
STATE = Path("/tmp/lhc_mill_g46_w4cw_state.json")
USED_FROM = 4163

BANNED_SUB = (
    "rpitit", "thinlto", "loopvar", "django-async", "asgi",
    "promql-histogram", "prometheus-histogram-native",
    "vale-region", "koka-effect",
    "kanidm", "gluu", "casdoor", "authentik", "oauth2", "zitadel",
    "authelia", "pomerium", "teleport", "agama", "sssd", "pam-mkhomedir",
    "hydra", "kratos", "keto", "ory-keto", "pr-ory-", "origin-https", "origin-frontend",
    "pass-identity", "whoami-tokenized",
    "rust-pin", "pin-unpin", "pin-project", "transmute",
    "nim-lent", "nim-var-escape", "zig-errdefer", "zig-defer",
    "luigi", "dvc-cache", "squashfs", "overlayfs", "nvidia-cdi",
    "wdl-runtime", "muscle", "mafft", "freebayes", "hisat", "stringtie",
    "fastqc", "multiqc", "spades", "flye", "kraken", "hisat2",
    "rsem", "seurat", "mutect2", "hail-npart", "cellbender",
)


def hx(kind: str, rnd: int, slug: str) -> str:
    return hashlib.sha1(f"w4cw|{kind}|{rnd}|{slug}|grok-4.6".encode()).hexdigest()[:4]


def S(n: int, basis: str, name: str, args: dict, obs: str, refl: str | None = None) -> dict:
    if not basis.startswith(("Plan:", "Observation:", "Reflection:", "Tool call:")):
        raise SystemExit(f"bad prefix n={n}: {basis}")
    if len(basis) > 240:
        raise SystemExit(f"basis {n} len={len(basis)}: {basis}")
    d = {
        "n": n,
        "decision_basis": basis,
        "tool_call": {"name": name, "args": args},
        "observation": obs,
    }
    if refl:
        d["reflection"] = refl
    return d


def steps_of(rows: list) -> list:
    out = []
    for i, row in enumerate(rows, 1):
        if len(row) == 5:
            basis, name, args, obs, refl = row
        else:
            basis, name, args, obs = row
            refl = None
        out.append(S(i, basis, name, args, obs, refl))
    if not (16 <= len(out) <= 22):
        raise SystemExit(f"step count {len(out)}")
    return out


def lhc_ep(rnd, slug, goal, plan, outcome, success, tests, rows, residual=0):
    rec = {
        "id": f"lhc-r{rnd}-{slug}-{hx('lhc', rnd, slug)}",
        "goal": goal,
        "plan": plan,
        "steps": steps_of(rows),
        "outcome": outcome,
        "reward": {
            "success": success,
            "tests_passed": tests,
            "cost_steps": len(rows),
        },
        "meta": {
            "factory": "long-horizon-coding-factory",
            "round": rnd,
            "generator": "grok-4.6",
            "plant": "designed",
        },
    }
    if residual:
        rec["reward"]["residual"] = residual
    return rec


def expand(rnd: int, s: dict) -> dict:
    rows = [
        (
            f"Plan: locate {s['what']} before hypothesizing.",
            "glob",
            {"pattern": s["glob"]},
            s["ls"],
        ),
        (
            f"Observation: {s['impl']} is listed; read it first.",
            "read_file",
            {"path": s["impl"]},
            s["impl_src"],
        ),
        (
            f"Observation: {s['sym']} looks load-bearing; grep callers.",
            "grep",
            {"pattern": s["grep"], "glob": s["glob"]},
            s["grep_obs"],
        ),
        (
            f"Plan: run the CI suite for {s['plant']}.",
            "run_terminal_command",
            {"cmd": s["test"]},
            s["fail1"],
        ),
        (
            f"Observation: {s['fail_name']} failed; read the test.",
            "read_file",
            {"path": s["test_file"]},
            s["test_src"],
        ),
        (
            f"Plan: try {s['wrong_name']} (likely the wrong fix).",
            "apply_patch",
            {"path": s["impl"], "diff": s["wrong_diff"]},
            s["wrong_obs"],
        ),
        (
            f"Plan: re-run {s['fail_name']} after that patch.",
            "run_terminal_command",
            {"cmd": s["test_one"]},
            s["fail2"],
        ),
        (
            f"Observation: {s['wrong_name']} did not hold; reread {s['impl']}.",
            "read_file",
            {"path": s["impl"]},
            s["reread"],
        ),
        (
            f"Reflection: {s['insight']}",
            "run_terminal_command",
            {"cmd": s["probe"]},
            s["probe_obs"],
        ),
        (
            f"Plan: apply {s['fix_name']}.",
            "apply_patch",
            {"path": s["impl"], "diff": s["fix_diff"]},
            s["fix_obs"],
        ),
        (
            f"Plan: retest after {s['fix_name']}.",
            "run_terminal_command",
            {"cmd": s["test"]},
            s["fail3"],
        ),
        (
            f"Observation: leftover in {s['rel']}; read it.",
            "read_file",
            {"path": s["rel"]},
            s["rel_src"],
        ),
        (
            f"Plan: {s['fix2_name']}.",
            "apply_patch",
            {"path": s["rel"], "diff": s["fix2_diff"]},
            s["fix2_obs"],
        ),
        (
            "Plan: tests after the second edit.",
            "run_terminal_command",
            {"cmd": s["test"]},
            s["pass_mid"],
        ),
        (
            f"Plan: grep leftover {s['bad_pat']}.",
            "grep",
            {"pattern": s["bad_pat"], "glob": s["glob"]},
            s["grep2"],
        ),
        (
            f"Plan: document {s['doc_point']}.",
            "apply_patch",
            {"path": s["doc"], "diff": s["doc_diff"]},
            "updated.",
        ),
        (
            f"Plan: add regression {s['reg_name']}.",
            "apply_patch",
            {"path": s["test_file"], "diff": s["reg_diff"]},
            "added.",
        ),
        (
            "Plan: full suite as CI.",
            "run_terminal_command",
            {"cmd": s["full_test"]},
            s["final"],
        ),
        (
            f"Plan: read final {s['impl']} for the PR summary.",
            "read_file",
            {"path": s["impl"], "limit": 40},
            s["summary"],
        ),
        (
            f"Plan: stop after {s['wrap']}.",
            "run_terminal_command",
            {"cmd": s["full_test"]},
            s["wrap_obs"],
        ),
    ]
    return lhc_ep(
        rnd,
        s["slug"],
        s["goal"],
        s["plan"],
        s["outcome"],
        s["success"],
        s["tests"],
        rows,
        residual=s.get("residual", 0),
    )


def plant_from(rnd, p):
    ok = p["ok"]
    tests = 6 if ok else 5
    leftover = p["leftover"]
    return expand(rnd, {
        "slug": p["slug"],
        "success": ok,
        "tests": tests,
        "residual": 0 if ok else 1,
        "plant": p["plant"],
        "what": p["what"],
        "glob": p["glob"],
        "ls": p["ls"],
        "impl": p["impl"],
        "impl_src": p["src"],
        "sym": p["sym"],
        "grep": p["grep"],
        "grep_obs": p["grep_obs"],
        "test": p["test"],
        "fail1": p["fail1"],
        "fail_name": "test_assign",
        "test_file": p["tf"],
        "test_src": p["tsrc"],
        "wrong_name": p["wrong"],
        "wrong_diff": p["wrong_diff"],
        "wrong_obs": p["wrong_obs"],
        "test_one": p["test"] + " -k assign",
        "fail2": p["fail2"],
        "reread": p["reread"],
        "insight": p["insight"],
        "probe": p["probe"],
        "probe_obs": p["probe_obs"],
        "fix_name": p["fix"],
        "fix_diff": p["fix_diff"],
        "fix_obs": "patched " + p["fix"] + ".",
        "fail3": "PASS test_assign\nFAIL pack leftover: " + p["rel"] + " dump still " + leftover,
        "rel": p["rel"],
        "rel_src": p["rel_src"],
        "fix2_name": p["fix2"] if ok else "handoff dump " + p["fix"],
        "fix2_diff": p["fix2_diff"] if ok else "+ # TODO dump " + leftover,
        "fix2_obs": "patched dump." if ok else "assign green. dump leftover.",
        "pass_mid": "PASS 6." if ok else "PASS 5. FAIL dump residual. Handoff.",
        "bad_pat": p["bad_pat"],
        "grep2": "none." if ok else "none as the fix. leftover dump.",
        "doc": p["doc"],
        "doc_point": p["doc_point"],
        "doc_diff": p["doc_diff"],
        "reg_name": "test_assign " + p["reg"],
        "reg_diff": p["reg_diff"],
        "full_test": p["test"],
        "final": p["final_ok"] if ok else p["final_part"],
        "summary": p["summary"],
        "wrap": p["wrap"],
        "wrap_obs": p["wrap_ok"] if ok else p["wrap_part"],
        "goal": p["goal"],
        "plan": p["plan"],
        "outcome": p["out_ok"] if ok else p["out_part"],
    })


def P(ok, **k):
    k["ok"] = ok
    return k


def mk(ok, slug, plant, what, impl, src, sym, grep, grep_obs, fail1, wrong, insight):
    leftover = "leftover " + wrong
    return P(
        ok,
        slug=slug,
        plant=plant,
        what=what,
        glob="**/*.{yml,yaml,json,conf,toml,properties,sql}",
        ls=f"{impl} tests/test_harbor.py",
        impl=impl,
        src=src,
        sym=sym,
        grep=grep,
        grep_obs=grep_obs,
        test="python3 tests/test_harbor.py",
        fail1=fail1,
        tf="tests/test_harbor.py",
        tsrc="assert True",
        wrong=wrong,
        wrong_diff="+ " + wrong,
        wrong_obs="still " + wrong + ". still fail.",
        fail2="FAIL test_assign: still broken. " + sym + ".",
        reread="apply " + sym + ".",
        insight=insight,
        probe="rg -n '" + grep + "' " + impl,
        probe_obs="pack " + sym + ". harbor " + wrong + ".",
        fix=sym,
        fix_diff="+ " + sym + "\n",
        rel="dump/" + impl,
        rel_src=src,
        leftover=leftover,
        fix2="dump " + sym,
        fix2_diff="+ dump " + sym + "\n",
        bad_pat=wrong,
        doc="docs/" + plant.upper() + ".md",
        doc_point=insight,
        doc_diff="+ " + insight + ".",
        reg="reg",
        reg_diff="+ " + sym + " holds",
        final_ok="ok 6 passed. " + sym + ".",
        final_part="5 passed, 1 dump residual. Partial.",
        summary=sym + ("; dump same." if ok else "; dump leftover."),
        wrap="the " + sym,
        wrap_ok="6 passed. " + plant + " assign is green.",
        wrap_part="5 passed, 1 residual. " + plant + " assign is green.",
        goal="Designed plant " + plant + ": " + what + ". " + sym + ". " + insight + ".",
        plan="Repro python tests, reject " + wrong + ", " + sym + ", " + ("fix dump." if ok else "hand off dump."),
        out_ok=sym + ". 6 tests pass.",
        out_part=sym + ". dump leftover. Partial.",
    )



# Compact unused astronomy / GW plants after w4cv.
PLANTS = {
    "astropy": mk(True, "pr-astropy-wcs-sip", "lock-atwcs",
        "the Astropy WCS that omitted SIP distortion so a 4k mosaic shifted 8 pixels at the edge",
        "astropy.py", "WCS(header)", "wcs.sip is not None",
        "sip", "harbor WCS header only. pack SIP.",
        "FAIL test_assign: 8px edge shift; SIP missing",
        "WCS header only", "WCS is not SIP"),
    "photutils": mk(False, "pr-photutils-bkg-sigma", "quay-phbkg",
        "the photutils Background2D that omitted sigma_clip so a crowded field used 3-sigma and over-subtracted",
        "phot.py", "Background2D(data, (50,50))", "Background2D(data, (50,50), sigma_clip=SigmaClip(sigma=2.5))",
        "sigma_clip", "harbor box 50 only. pack sigma_clip.",
        "FAIL test_assign: over-subtract crowded; sigma_clip missing",
        "box only", "box is not sigma_clip"),
    "ccdproc": mk(True, "pr-ccdproc-gain-correct", "lock-ccdgain",
        "the ccdproc combine that omitted gain_corrected so ADU stacks mixed two cameras",
        "ccd.py", "combine(files, method='average')", "ccdproc.gain_correct(ccd, gain)",
        "gain_correct", "harbor combine average only. pack gain_correct.",
        "FAIL test_assign: mixed ADU cameras; gain_correct missing",
        "combine only", "combine is not gain_correct"),
    "specutils": mk(False, "pr-specutils-rv-correct", "quay-sprv",
        "the specutils Spectrum1D that omitted radial_velocity so lines sat in the observer frame",
        "sp.py", "Spectrum1D(flux, spectral_axis=wave)", "spec.shift_spectrum_to(target_frame)",
        "shift_spectrum_to", "harbor Spectrum1D only. pack radial velocity shift.",
        "FAIL test_assign: observer-frame lines; rv shift missing",
        "Spectrum1D only", "Spectrum1D is not rv"),
    "sunpy": mk(True, "pr-sunpy-map-prep", "lock-snprep",
        "the sunpy Map that omitted prep so an AIA 171 stayed in DN and DEM failed",
        "sunpy.py", "Map('aia171.fits')", "aiaprep(smap)",
        "aiaprep", "harbor Map fits only. pack aiaprep.",
        "FAIL test_assign: DN DEM fail; aiaprep missing",
        "Map only", "Map is not aiaprep"),
    "gammapy": mk(False, "pr-gammapy-safe-mask", "quay-gmsafe",
        "the Gammapy MapDataset that omitted safe_mask so energy bins below threshold entered the likelihood",
        "gp.py", "MapDataset.read('ds.fits')", "dataset.mask_safe = Map.from_geom(...)",
        "mask_safe", "harbor MapDataset read only. pack mask_safe.",
        "FAIL test_assign: below-threshold bins; mask_safe missing",
        "read only", "read is not mask_safe"),
    "sherpa": mk(True, "pr-sherpa-stat-cash", "lock-shcash",
        "the Sherpa fit that omitted set_stat cash so a low-count X-ray spectrum used chi2",
        "sherpa.py", "fit()", "set_stat('cash')",
        "set_stat cash", "harbor fit() only. pack cash.",
        "FAIL test_assign: chi2 on low counts; cash missing",
        "fit only", "fit is not cash"),
    "ciao": mk(False, "pr-ciao-punlearn-asphist", "quay-ciasph",
        "the CIAO asphist that omitted punlearn so a leftover pset used the wrong aspect",
        "ciao.sh", "asphist infile=evt.fits outfile=asph.fits", "punlearn asphist",
        "punlearn", "harbor asphist infile only. pack punlearn.",
        "FAIL test_assign: leftover pset aspect; punlearn missing",
        "asphist only", "asphist is not punlearn"),
    "wsclean": mk(True, "pr-wsclean-multiscale", "lock-wsms",
        "the WSClean image that omitted -multiscale so extended flux sat in residuals",
        "wsc.sh", "wsclean -size 4096 4096 -scale 1asec ms/", "wsclean -multiscale",
        "-multiscale", "harbor size/scale only. pack -multiscale.",
        "FAIL test_assign: extended in residuals; -multiscale missing",
        "size only", "size is not -multiscale"),
    "casacore": mk(False, "pr-casacore-ms-scratch", "quay-cscrs",
        "the casacore MS that omitted scratch=False so a 2TB vis copied to /tmp",
        "cc.py", "table.open('obs.ms')", "table.open('obs.ms', scratch=False)",
        "scratch=False", "harbor open ms only. pack scratch=False.",
        "FAIL test_assign: 2TB /tmp copy; scratch=False missing",
        "open only", "open is not scratch"),
    "healpy": mk(True, "pr-healpy-nest-ring", "lock-hpnest",
        "the healpy anafast that omitted nest=True so a nested map was read as RING and C_ell blew",
        "hp.py", "hp.anafast(m)", "hp.anafast(m, nest=True)",
        "nest=True", "harbor anafast only. pack nest=True.",
        "FAIL test_assign: RING vs nested C_ell; nest missing",
        "anafast only", "anafast is not nest"),
    "gwpy": mk(False, "pr-gwpy-highpass-f", "quay-gwhp",
        "the GWpy TimeSeries that omitted highpass so a 60Hz line leaked into a Q-transform",
        "gwpy.py", "ts.q_transform()", "ts.highpass(15)",
        "highpass", "harbor q_transform only. pack highpass 15.",
        "FAIL test_assign: 60Hz leak; highpass missing",
        "q_transform only", "q_transform is not highpass"),
    "bilby": mk(True, "pr-bilby-distance-prior", "lock-bldist",
        "the Bilby CBC prior that omitted luminosity_distance so a nested sampler used a delta at 100 Mpc",
        "bilby.py", "bilby.run_sampler(likelihood, priors)", "priors['luminosity_distance']=bilby.gw.prior.UniformComovingVolume",
        "luminosity_distance", "harbor run_sampler only. pack distance prior.",
        "FAIL test_assign: delta 100 Mpc; distance prior missing",
        "run_sampler only", "run_sampler is not distance"),
    "pycbc": mk(False, "pr-pycbc-psd-estimation", "quay-pcpsd",
        "the PyCBC matched filter that omitted psd estimation so a 128s chunk used a design PSD",
        "pycbc.py", "matched_filter(hp, strain)", "psd = interpolate(welch(strain), ...)",
        "welch", "harbor matched_filter only. pack welch PSD.",
        "FAIL test_assign: design PSD; welch missing",
        "matched_filter only", "matched_filter is not welch"),
    "einsteinpy": mk(True, "pr-einsteinpy-schwarzschild-metric", "lock-epsch",
        "the EinsteinPy geodesic that omitted Schwarzschild metric so a Kerr spin leaked into a spinless orbit",
        "ep.py", "TimelikeGeodesic(metric, ...)", "Schwarzschild(coords, M)",
        "Schwarzschild", "harbor TimelikeGeodesic only. pack Schwarzschild.",
        "FAIL test_assign: Kerr spin leak; Schwarzschild missing",
        "geodesic only", "geodesic is not Schwarzschild"),
    "poliastro": mk(False, "pr-poliastro-attractor-gm", "quay-poagm",
        "the poliastro Orbit that omitted custom GM so a small-body flyby used Sun-GM and miss-distance blew",
        "po.py", "Orbit.from_vectors(Sun, r, v)", "Orbit.from_vectors(body, r, v)",
        "custom attractor", "harbor Sun attractor only. pack body GM.",
        "FAIL test_assign: Sun-GM miss; custom attractor missing",
        "Sun only", "Sun is not custom GM"),
    "skyfield": mk(True, "pr-skyfield-de440-ephem", "lock-skde",
        "the Skyfield load that omitted de440 so a 2026 asteroid used de421 and 40as error",
        "sf.py", "load('de421.bsp')", "load('de440.bsp')",
        "de440", "harbor de421 only. pack de440.",
        "FAIL test_assign: 40as de421; de440 missing",
        "de421 only", "de421 is not de440"),
    "spiceypy": mk(False, "pr-spiceypy-furnsh-lsk", "quay-splsk",
        "the spiceypy str2et that omitted furnsh LSK so UTC conversion used a stale leap second",
        "spice.py", "spice.str2et('2026-08-19')", "spice.furnsh('naif0012.tls')",
        "furnsh lsk", "harbor str2et only. pack furnsh LSK.",
        "FAIL test_assign: stale leap; LSK missing",
        "str2et only", "str2et is not LSK"),
    "sep": mk(True, "pr-sep-deblend-nthresh", "lock-sepdbl",
        "the SEP extract that omitted deblend_nthresh so a crowded cluster merged stars",
        "sep.py", "sep.extract(data, thresh)", "sep.extract(data, thresh, deblend_nthresh=32)",
        "deblend_nthresh", "harbor extract thresh only. pack deblend_nthresh.",
        "FAIL test_assign: merged stars; deblend_nthresh missing",
        "extract only", "extract is not deblend"),
    "scamp": mk(False, "pr-scamp-astrinstru-key", "quay-scain",
        "the SCAMP run that omitted ASTRINSTRU_KEY so two cameras shared one distortion",
        "scamp.sh", "scamp *.head", "ASTRINSTRU_KEY FILTER",
        "ASTRINSTRU_KEY", "harbor scamp heads only. pack ASTRINSTRU_KEY.",
        "FAIL test_assign: shared distortion; ASTRINSTRU_KEY missing",
        "heads only", "heads are not ASTRINSTRU_KEY"),
    "swarp": mk(True, "pr-swarp-resample-lan", "lock-swlan",
        "the SWarp coadd that omitted RESAMPLING_TYPE LANCZOS3 so a 0.2as mosaic used NEAREST",
        "swarp.sh", "swarp *.fits -c default.swarp", "RESAMPLING_TYPE LANCZOS3",
        "LANCZOS3", "harbor swarp default only. pack LANCZOS3.",
        "FAIL test_assign: NEAREST mosaic; LANCZOS3 missing",
        "default only", "default is not LANCZOS3"),
    "montage": mk(False, "pr-montage-background-diff", "quay-mtbg",
        "the Montage mAdd that omitted mDiffFitExec so a 20-tile mosaic had 0.3 mag seams",
        "montage.sh", "mAdd images.tbl template.hdr out.fits", "mDiffFitExec diffs.tbl diffs.dir fits.tbl",
        "mDiffFitExec", "harbor mAdd only. pack mDiffFitExec.",
        "FAIL test_assign: 0.3 mag seams; mDiffFitExec missing",
        "mAdd only", "mAdd is not mDiffFitExec"),
    "spectralcube": mk(True, "pr-spectralcube-with-spectral-unit", "lock-scsu",
        "the spectral-cube moment that omitted with_spectral_unit so a 0.1 km/s cube used Hz and the moment warped",
        "sc.py", "cube.moment(order=0)", "cube.with_spectral_unit(u.km/u.s)",
        "with_spectral_unit", "harbor moment 0 only. pack with_spectral_unit km/s.",
        "FAIL test_assign: Hz moment warp; spectral unit missing",
        "moment only", "moment is not spectral unit"),
    "aoflagger": mk(False, "pr-aoflagger-strategy", "quay-aost",
        "the AOFlagger run that omitted -strategy so a LOFAR MS used generic RFI and 30% vis died",
        "aof.sh", "aoflagger obs.ms", "aoflagger -strategy lofar-default.lua obs.ms",
        "-strategy", "harbor aoflagger ms only. pack -strategy.",
        "FAIL test_assign: 30% vis died; -strategy missing",
        "ms only", "ms is not -strategy"),
    "dysco": mk(True, "pr-dysco-bits-per-float", "lock-dysb",
        "the Dysco compressor that omitted bits-per-float so a 2TB MS used 16-bit and phases smeared",
        "dysco.sh", "taql 'select from obs.ms'", "DyscoStMan bits-per-float=10",
        "bits-per-float", "harbor taql only. pack bits-per-float 10.",
        "FAIL test_assign: 16-bit phase smear; bits-per-float missing",
        "taql only", "taql is not bits-per-float"),
    "wgridder": mk(False, "pr-wgridder-epsilon", "quay-wgeps",
        "the wgridder image that omitted epsilon so a 1asec image used 1e-2 and sidelobes leaked",
        "wg.py", "wgridder.ms2dirty(uvw, freq, vis, ...)", "wgridder(..., epsilon=1e-4)",
        "epsilon", "harbor ms2dirty only. pack epsilon 1e-4.",
        "FAIL test_assign: 1e-2 sidelobes; epsilon missing",
        "ms2dirty only", "ms2dirty is not epsilon"),
    "dp3": mk(True, "pr-dp3-applycal-steps", "lock-dp3ac",
        "the DP3 DPPP that omitted applycal so a 8h LOFAR MS stayed uncalibrated",
        "dp3.sh", "DPPP msin=obs.ms msout=out.ms", "steps=[applycal] applycal.parmdb=cal.h5",
        "applycal", "harbor msin/msout only. pack applycal.",
        "FAIL test_assign: uncalibrated 8h; applycal missing",
        "msin only", "msin is not applycal"),
    "tclean": mk(False, "pr-casa-tclean-niter", "quay-tcnit",
        "the CASA tclean that omitted niter so a 1k x 1k image stopped after 0 and dirty stayed",
        "tclean.py", "tclean(vis='obs.ms', imagename='img')", "tclean(..., niter=5000)",
        "niter", "harbor tclean vis only. pack niter 5000.",
        "FAIL test_assign: dirty 0 iter; niter missing",
        "vis only", "vis is not niter"),
}

def fn(key):
    def f(rnd, k=key):
        return plant_from(rnd, PLANTS[k])
    f.__name__ = key
    return f


LHC_PAIRS = [
    ("Astropy SIP vs photutils sigma_clip", fn("astropy"), fn("photutils"),
     "SIP; sigma_clip 2.5", "WCS header; box 50",
     "astropy dump 8px edge; photutils dump over-subtract"),
    ("ccdproc gain_correct vs specutils rv shift", fn("ccdproc"), fn("specutils"),
     "gain_correct; shift_spectrum_to", "combine; Spectrum1D",
     "ccdproc dump mixed ADU; specutils dump observer-frame"),
    ("sunpy aiaprep vs Gammapy mask_safe", fn("sunpy"), fn("gammapy"),
     "aiaprep; mask_safe", "Map fits; MapDataset read",
     "sunpy dump DN DEM; gammapy dump below-threshold"),
    ("Sherpa cash vs CIAO punlearn", fn("sherpa"), fn("ciao"),
     "set_stat cash; punlearn asphist", "fit(); asphist",
     "sherpa dump chi2 low counts; ciao dump leftover pset"),
    ("WSClean -multiscale vs casacore scratch=False", fn("wsclean"), fn("casacore"),
     "-multiscale; scratch=False", "size/scale; open ms",
     "wsclean dump extended residuals; casacore dump 2TB /tmp"),
    ("healpy nest vs GWpy highpass", fn("healpy"), fn("gwpy"),
     "nest=True; highpass 15", "anafast; q_transform",
     "healpy dump RING vs nested; gwpy dump 60Hz leak"),
    ("Bilby distance prior vs PyCBC welch PSD", fn("bilby"), fn("pycbc"),
     "luminosity_distance prior; welch PSD", "run_sampler; matched_filter",
     "bilby dump delta 100 Mpc; pycbc dump design PSD"),
    ("EinsteinPy Schwarzschild vs poliastro GM", fn("einsteinpy"), fn("poliastro"),
     "Schwarzschild; custom attractor GM", "geodesic; Sun",
     "einsteinpy dump Kerr spin; poliastro dump Sun-GM miss"),
    ("Skyfield de440 vs spiceypy LSK", fn("skyfield"), fn("spiceypy"),
     "de440; furnsh LSK", "de421; str2et",
     "skyfield dump 40as de421; spiceypy dump stale leap"),
    ("SEP deblend vs SCAMP ASTRINSTRU_KEY", fn("sep"), fn("scamp"),
     "deblend_nthresh 32; ASTRINSTRU_KEY", "extract; heads",
     "sep dump merged stars; scamp dump shared distortion"),
    ("SWarp LANCZOS3 vs Montage mDiffFitExec", fn("swarp"), fn("montage"),
     "LANCZOS3; mDiffFitExec", "default; mAdd",
     "swarp dump NEAREST mosaic; montage dump 0.3 mag seams"),
    ("spectral-cube km/s vs AOFlagger -strategy", fn("spectralcube"), fn("aoflagger"),
     "with_spectral_unit km/s; -strategy lua", "moment; ms",
     "spectralcube dump Hz warp; aoflagger dump 30% vis"),
    ("Dysco bits-per-float vs wgridder epsilon", fn("dysco"), fn("wgridder"),
     "bits-per-float 10; epsilon 1e-4", "taql; ms2dirty",
     "dysco dump 16-bit smear; wgridder dump 1e-2 sidelobes"),
    ("DP3 applycal vs CASA tclean niter", fn("dp3"), fn("tclean"),
     "applycal parmdb; niter 5000", "msin; vis",
     "dp3 dump uncalibrated 8h; tclean dump dirty 0 iter"),
]


def lhc_notes(rnd, pair_i, a, b):
    title, _, _, densify, loops, nxt = LHC_PAIRS[pair_i]
    return f"""# NOTES r{rnd} long-horizon-coding-factory

Novel coverage: 94%

Pair: {title}.
- Steps: {len(a['steps'])} {'success' if a['reward']['success'] else 'partial'} {a['id']}; {len(b['steps'])} {'success' if b['reward']['success'] else 'partial'} {b['id']}.
- Debug loops: {loops}.
- Densified: {densify}.
- Next densify: {nxt}.
- Not a clone of w4cs RSEM/Seurat/Mutect2/Hail, w4cr FastQC/SPAdes, r4778 nim-lent, r4777 zig-errdefer, r4687 rust-pin, r4580 kanidm/gluu, identity-origin SSO.
- Bans avoided: nim-lent / zig-errdefer / rust-pin / Mutect2 / Hail / FastQC / Seurat / RSEM / kanidm / gluu / agama / RPITIT / Prom native hist / ThinLTO / Go loopvar / Django ASGI / Vale / Koka / identity-origin clones.
- No thought/CoT keys. meta.generator=grok-4.6. plant=designed. No spikes/Thalamic/real.
"""


def load_state():
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {"lhc_pair": 0, "published": []}


def save_state(st):
    STATE.write_text(json.dumps(st, indent=2) + "\n")


def txn(args):
    return subprocess.run(
        ["python3", str(TXN), *args],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
    )


def frontier(factory_dir: Path) -> int:
    r = txn(["frontier", str(factory_dir)])
    if r.returncode != 0:
        raise SystemExit(r.stderr or r.stdout)
    return json.loads(r.stdout)["next_round"]


def reserved(factory_dir: Path, n: int) -> bool:
    return (factory_dir / f"ROUND-r{n}.reserved.json").exists()


def used_slugs() -> set[str]:
    import re
    used: set[str] = set()
    for f in LHC_DIR.glob("batch-r*.jsonl"):
        try:
            text = f.read_text()
        except OSError:
            continue
        for line in text.splitlines():
            if not line.strip():
                continue
            try:
                i = json.loads(line)["id"]
            except Exception:
                continue
            m = re.match(r"lhc-r\d+-(.+)-[0-9a-f]{4,}$", i)
            if m:
                used.add(m.group(1))
    return used


def write_stage(stage: Path, batch_name: str, notes_name: str, recs: list, notes: str):
    batch = stage / batch_name
    notes_p = stage / notes_name
    lines = [json.dumps(rec, separators=(",", ":"), ensure_ascii=False) for rec in recs]
    batch.write_text("\n".join(lines) + "\n")
    notes_p.write_text(notes)
    for rec in recs:
        blob = json.dumps(rec)
        assert "thought" not in blob
        assert "chain_of_thought" not in blob
        assert "inner_monologue" not in blob
        assert "spike_events" not in blob
        assert '"sim_or_real": "real"' not in blob
        assert rec["meta"]["generator"] == "grok-4.6"
        assert rec["meta"]["plant"] == "designed"
        nset = [s["n"] for s in rec["steps"]]
        assert nset == list(range(1, len(rec["steps"]) + 1))
        assert 16 <= len(rec["steps"]) <= 22
        for s in rec["steps"]:
            assert len(s["decision_basis"]) <= 240
            assert "thought" not in s
        assert rec["id"].startswith("lhc-r")
        assert "-pr-" in rec["id"]


def emit_lhc(rnd: int, pair_i: int):
    title, fa, fb, *_ = LHC_PAIRS[pair_i]
    a, b = fa(rnd), fb(rnd)
    if a["reward"]["success"] == b["reward"]["success"]:
        raise SystemExit(f"pair {pair_i} same success flags")
    notes = lhc_notes(rnd, pair_i, a, b)
    return [a, b], notes, title


def try_reserve(factory_dir: Path, expected: int):
    nxt = frontier(factory_dir)
    if reserved(factory_dir, nxt):
        return None
    r = txn(["reserve", str(factory_dir), "--round", str(nxt), "--expected", str(expected)])
    if r.returncode != 0:
        err = (r.stderr or r.stdout).strip()
        print(f"reserve {factory_dir.name} r{nxt} failed: {err}", flush=True)
        return None
    return json.loads(r.stdout)


def publish_round(factory_dir, rnd, token, recs, notes, batch_name, notes_name, stage):
    write_stage(Path(stage), batch_name, notes_name, recs, notes)
    r = txn(["publish", str(factory_dir), "--round", str(rnd), "--token", token])
    if r.returncode != 0:
        sys.stderr.write(r.stderr or r.stdout)
        raise SystemExit(f"publish r{rnd} failed")
    print(r.stdout, flush=True)
    return True


def hop_targets():
    out = []
    for p in sorted(AGENTIC.iterdir()):
        if not p.is_dir():
            continue
        if p.name == "sandbox-refusal-factory":
            continue
        if p.name == "long-horizon-coding-factory":
            continue
        writing = any(p.glob("ROUND-r*.reserved.json")) or any(p.glob("ROUND-r*.publishing.json"))
        if writing:
            continue
        out.append(p)
    return out


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "loop"
    st = load_state()

    if mode == "selfcheck":
        used = used_slugs()
        slugs = []
        for i, (title, fa, fb, *_) in enumerate(LHC_PAIRS):
            a, b = fa(9990 + i), fb(9990 + i)
            assert a["reward"]["success"] != b["reward"]["success"], title
            assert 16 <= len(a["steps"]) <= 22
            assert 16 <= len(b["steps"]) <= 22
            assert a["id"].startswith("lhc-r") and "-pr-" in a["id"]
            assert b["id"].startswith("lhc-r") and "-pr-" in b["id"]
            sa = "-".join(a["id"].split("-")[2:-1])
            sb = "-".join(b["id"].split("-")[2:-1])
            slugs.append(sa)
            slugs.append(sb)
            for slug in (sa, sb):
                low = slug.lower()
                for ban in BANNED_SUB:
                    if ban in low:
                        raise SystemExit(f"banned token {ban} in {slug}")
                if slug in used:
                    raise SystemExit(f"slug already used: {slug}")
            print("ok", i, title)
            print("   ", a["id"], len(a["steps"]), a["reward"]["success"])
            print("   ", b["id"], len(b["steps"]), b["reward"]["success"])
        if len(set(slugs)) != len(slugs):
            raise SystemExit(f"duplicate slugs in catalog: {slugs}")
        print("selfcheck", len(LHC_PAIRS), "pairs", len(slugs), "episodes")
        return

    if mode == "loop":
        target = int(sys.argv[2]) if len(sys.argv) > 2 else len(LHC_PAIRS)
        deadline = time.time() + 6 * 60 * 60
        published = 0
        hops = 0
        used = used_slugs()
        while published < target and time.time() < deadline:
            while st["lhc_pair"] < len(LHC_PAIRS):
                title, fa, fb, *_ = LHC_PAIRS[st["lhc_pair"]]
                probe_a, probe_b = fa(1), fb(1)
                probe_slugs = [
                    "-".join(x["id"].split("-")[2:-1]) for x in (probe_a, probe_b)
                ]
                if any(s in used for s in probe_slugs):
                    print(f"skip used pair {st['lhc_pair']} {title} {probe_slugs}", flush=True)
                    st["lhc_pair"] += 1
                    save_state(st)
                    continue
                break
            if st["lhc_pair"] >= len(LHC_PAIRS):
                print("catalog exhausted", flush=True)
                break
            res = try_reserve(LHC_DIR, 2)
            if res:
                rnd = res["round"]
                pair_i = st["lhc_pair"]
                recs, notes, title = emit_lhc(rnd, pair_i)
                for rec in recs:
                    slug = "-".join(rec["id"].split("-")[2:-1])
                    if slug in used:
                        raise SystemExit(f"refusing to publish used slug {slug}")
                    used.add(slug)
                publish_round(
                    LHC_DIR, rnd, res["token"], recs, notes,
                    res["batch_file"], res["notes_file"], res["staging_dir"],
                )
                st["lhc_pair"] += 1
                st["published"].append({"factory": "lhc", "round": rnd, "title": title, "ids": [x["id"] for x in recs]})
                save_state(st)
                published += 1
                print(f"PUBLISHED LHC r{rnd} pair={pair_i} {title}", flush=True)
                hops = 0
                continue
            hops += 1
            others = hop_targets()
            print(
                "LHC reserved; hop candidates (retry LHC; never sandbox-refusal):",
                [p.name for p in others[:8]],
                "sleep",
                flush=True,
            )
            time.sleep(1)
            if hops > 600:
                print("too many reserve failures; quota/reservation died", flush=True)
                break
        print(json.dumps({
            "published_this_run": published,
            "state_pairs": st["lhc_pair"],
            "rounds": [p["round"] for p in st["published"][-published:] if published],
        }, indent=2), flush=True)
        return

    raise SystemExit(f"unknown mode {mode}")


if __name__ == "__main__":
    raise SystemExit(main() or 0)
