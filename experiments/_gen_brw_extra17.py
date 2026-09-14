#!/usr/bin/env python3
"""Generate leftover CSS extra17 plants from unused extra16 RAW after extra16's 200-cap."""
from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
_ns: dict = {"__file__": str(HERE / "_gen_brw_extra16.py")}
exec((HERE / "_gen_brw_extra16.py").read_text().split("def extra_used")[0], _ns)
T = _ns["T"]
KEYS = _ns["KEYS"]
PLANTS = _ns["PLANTS"]
keep_code = _ns["keep_code"]
mint = _ns["mint"]
story = _ns["story"]

GENERA = [
    "spicantopsis", "cibotium", "lophosoria", "metaxya", "culcita", "calochlaena",
    "thyrsopteris", "sphaeropteris", "gymnosphaera", "alsophilax", "sphaeropterix",
    "gymnosphaerax", "cyatheax", "dicksonix", "cibotiumx", "lophosorix",
    "diphasiastrum", "huperzia", "phlegmariurus", "palhinhaea", "pseudolycopodiella",
    "lateristachys", "phylloglossum", "stylites", "lepidodendron", "sigillaria",
    "pleuromeia", "nataliella", "cyclostigma", "bothrodendron", "ulodendron",
    "lepidophloios", "hippochaete", "allostelites", "equisetites", "schizaea",
    "lygodium", "anemia", "mohria", "actinostachys", "leptochilus",
    "phaeoceros", "notothylas", "dendroceros", "megaceros", "paraphymatoceros",
    "phymatoceros", "fodiella", "dumortiera", "tesselina", "cavicularia",
    "calobryum", "scaphophyllum", "kurzia", "telaranea", "zoopsis", "arachniopsis",
    "trichocolea", "ptilidium", "herberta", "mastigophora", "solenostoma",
    "barbilophozia", "leiocolea", "anastrophyllum", "tetralophozia", "sphenolobopsis",
    "cephalozia", "cladopodiella", "hygobiella", "schistochilopsis", "syzygiella",
    "adelanthus", "myriocoleopsis", "microlejeunea", "cheilolejeunea", "lopholejeunea",
    "archilejeunea", "ptychanthus", "thysananthus", "bryopteris", "maschalolejeunea",
    "acrolejeunea", "psilotum", "tmesipteris", "ophioglossum", "botrychium",
    "helminthostachys", "mankyua", "cheiroglossa", "ophioderma", "rhizoglossum",
    "baragwanathia", "asteroxylon", "drepanophycus", "zosterophyllum", "sawdonia",
    "gosslingia", "rhynia", "horneophyton", "aglaophyton", "cooksonia",
    "prototaxites", "nematothallus", "sciadophyton", "stockmansella", "huvenia",
    "salopella", "tortilicaulis", "uskiella", "hostinella", "taeniocrada",
    "psaronius", "angiopteris", "danaea", "christensenia", "marattia",
    "ptisana", "eupodium", "kaulfussia", "calamitesx", "sphenophyllumx",
    "annulariax", "palaeostachya", "archaeocalamites", "knorriax", "asterotheca",
    "pecopterisx", "sphenopterisx", "mariopterisx", "lyginopteris", "medullosa",
    "callistophyton", "glossopterisx", "gangamopteris", "vertebrariax", "dictyopteridium",
]


def mill_used():
    spec = importlib.util.spec_from_file_location("brw_mill_r395", HERE / "brw-mill-r395.py")
    mill = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mill)
    used_w, used_es, used_pl, used_pr, used_ax, used_seed, used_err = (
        set(), set(), set(), set(), set(), set(), set(),
    )
    used_keep: set[str] = set()
    used_css_to: set[tuple[str, str]] = set()
    for p in mill.PAIRS:
        used_w.add(p["widget"]); used_es.add(p["err_slug"])
        used_pl.add(p["ok_place"]); used_pl.add(p["bad_place"])
        used_pr.add(p["prefix"]); used_ax.add(p["aux"])
        used_seed.add(p["seed_ok"]); used_seed.add(p["seed_bad"]); used_err.add(p["err"])
        used_keep.add(p["keep"])
        used_css_to.add((p["css"], p["to"]))
    return used_w, used_es, used_pl, used_pr, used_ax, used_seed, used_err, used_keep, used_css_to


def main() -> int:
    if len(set(GENERA)) != len(GENERA):
        from collections import Counter
        c = Counter(GENERA)
        raise SystemExit(f"dup genera {[k for k, v in c.items() if v > 1]}")
    used_w, used_es, used_pl, used_pr, used_ax, used_seed, used_err, used_keep, used_css_to = mill_used()
    skipped = 0
    kept: list[tuple] = []
    for plant in PLANTS:
        css, fr, to, js, widget, err, code, tmpl, btn, new, not_, teach = plant
        if code == 409:
            raise SystemExit(f"{widget}: 409 banned")
        if widget in used_w or (css, to) in used_css_to:
            skipped += 1
            continue
        used_w.add(widget)
        used_css_to.add((css, to))
        if err in used_err:
            err = err + "_x17"
            if err in used_err:
                skipped += 1
                used_w.discard(widget)
                continue
        used_err.add(err)
        new, _old_not, teach = story(css, fr, to, tmpl)
        not_ = f"Not extra16 {css} mill, not extra15 {css}."
        kept.append((css, fr, to, js, widget, err, code, tmpl, btn, new, not_, teach))
    if not kept:
        raise SystemExit("no leftover plants")
    free_genera = []
    for genus in GENERA:
        ok, bad = genus + "clough", genus + "dene"
        if ok in used_pl or bad in used_pl:
            ok, bad = genus + "ford", genus + "hythe"
        if ok in used_pl or bad in used_pl or ok == bad:
            continue
        free_genera.append(genus)
    if len(kept) > len(free_genera):
        raise SystemExit(f"need more genera {len(kept)}>{len(free_genera)}")
    rows = []
    for i, plant in enumerate(kept):
        css, fr, to, js, widget, err, code, tmpl, btn, new, not_, teach = plant
        item, neigh, fail, ref, nref, fref, x0, x1, y, title, path = T[tmpl]
        prefix = mint("".join(ch for ch in widget if ch.isalnum())[:4] or "ecp", used_pr)
        aux = mint(("".join(ch for ch in widget if ch.isalnum())[2:6] or "eca") + "x", used_ax)
        if prefix == aux:
            aux = mint(aux + "z", used_ax)
        genus = free_genera[i]
        ok, bad = genus + "clough", genus + "dene"
        if ok in used_pl or bad in used_pl:
            ok, bad = genus + "ford", genus + "hythe"
        if ok in used_pl or bad in used_pl or ok == bad:
            raise SystemExit(f"place collision {ok} {bad}")
        used_pl.add(ok); used_pl.add(bad)
        slug = f"{aux}-{code}"
        if slug in used_es:
            raise SystemExit(f"err_slug collision {slug}")
        used_es.add(slug)
        seed_ok, seed_bad = f"css-{widget}", f"css-{widget}-{code}"
        if seed_ok in used_seed or seed_bad in used_seed:
            seed_ok, seed_bad = f"css-{widget}-x17", f"css-{widget}-x17-{code}"
        if seed_ok in used_seed or seed_bad in used_seed:
            raise SystemExit(f"seed collision {seed_ok}")
        used_seed.add(seed_ok); used_seed.add(seed_bad)
        keep = keep_code(genus, used_keep)
        nxt = kept[i + 1][4] if i + 1 < len(kept) else "catalog continue."
        rows.append((
            prefix, aux, ok, bad, widget, slug, code, err,
            css, fr, to, js, item, neigh, fail, ref, nref, fref,
            x0, x1, y, btn, title, "Keep", path, keep, f"{item} {genus}", seed_ok, seed_bad,
            new, not_, teach, nxt + ".",
        ))
    out = HERE / "brw-mill-r395-extra17.py"
    lines = ['"""Leftover CSS plants after extra16 tree-fern clough/dene 200-cap."""', "KEYS = (",
             '    "prefix", "aux", "ok_place", "bad_place", "widget", "err_slug", "code", "err",',
             '    "css", "from", "to", "js", "item", "neigh", "fail_item", "ref", "nref", "fref",',
             '    "x0", "x1", "y", "btn", "title", "verb", "path", "keep", "note", "seed_ok", "seed_bad",',
             '    "new", "not", "teach", "next",', ")", "ROWS = ["]
    for row in rows:
        lines.append("(" + ",".join(repr(v) for v in row) + "),")
    lines += ["]", "EXTRA = [dict(zip(KEYS, row)) for row in ROWS]", ""]
    out.write_text("\n".join(lines))
    print(f"wrote {out} plants={len(rows)} skipped={skipped} last={rows[-1][4]} {rows[-1][2]} first={rows[0][4]} {rows[0][2]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
