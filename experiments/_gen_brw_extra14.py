#!/usr/bin/env python3
"""Generate leftover CSS extra14 plants after extra13 (lichens wyke/gill)."""
from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
_ns: dict = {"__file__": str(HERE / "_gen_brw_extra13.py")}
exec((HERE / "_gen_brw_extra13.py").read_text().split("def extra_used")[0], _ns)
T = _ns["T"]
KEYS = _ns["KEYS"]
PLANTS = _ns["PLANTS"]
keep_code = _ns["keep_code"]
load_set = _ns["load_set"]


def mint(base: str, used: set[str], n: int = 4) -> str:
    raw = "".join(ch for ch in base.lower() if ch.isalnum()) or "ecp"
    for ntry in (n, n + 1, n + 2, 6):
        cand = (raw + "x" * ntry)[:ntry]
        if cand not in used and cand != "api":
            used.add(cand)
            return cand
        for i in range(2, 500):
            suffix = str(i)
            body = cand[: max(1, ntry - len(suffix))] + suffix
            if body not in used and body != "api" and body.isalnum():
                used.add(body)
                return body
    raise SystemExit(f"cannot mint {base}")

GENERA = [
    "cladonia", "cetraria", "peltigera", "xanthoria", "physcia", "physconia", "usnea", "alectoria",
    "ramalina", "evernia", "pseudevernia", "hypogymnia", "parmelia", "punctelia", "flavoparmelia",
    "melanohalea", "melanelia", "nephroma", "solorina", "lobaria", "sticta", "pseudocyphellaria",
    "degelia", "pannaria", "fuscopannaria", "collema", "leptogium", "scytinium", "enchylium",
    "lathagrium", "bacidia", "lecidea", "porpidia", "rhizocarpon", "buellia", "rinodina",
    "caloplaca", "rusavskia", "teloschistes", "squamarina", "psora", "toninia", "catillaria",
    "micarea", "arthonia", "graphis", "opegrapha", "enterographa", "lecania", "lecanora",
    "protoparmeliopsis", "ochrolechia", "pertusaria", "varicellaria", "diploschistes", "thelotrema",
    "chiodecton", "dirina", "roccella", "dendrographa", "schismatomma", "lepraria", "chrysothrix",
    "pycnora", "trapelia", "trapeliopsis", "placynthiella", "fuscidea", "sarea", "elixia",
    "protoblastenia", "haematomma", "ramboldia", "miriquidica", "tephromela", "mycoblastus",
    "japewia", "farnoldia", "immersaria", "koerberia", "koerberiella", "loncographa", "phaeographis",
    "phaeographina", "sarcographa", "glyphis", "fissurina", "platygramme", "anisomeridium",
    "acrocordia", "pyrenula", "anthracothecium", "lithothelium", "polymeridium", "trypethelium",
    "astrothelium", "viridothelium", "polymeris", "lauderlindsaya", "strigula", "phylloporis",
    "porina", "trichothelium", "clathroporina", "thelenella", "topeliopsis", "gyalecta",
    "cryptolechia", "pectenia", "fuscopannariax", "pannariax", "protopannaria", "moelleropsis",
    "vahllella", "lichina", "lathagriopsis", "scytiniumx", "leprocaulon", "stereocaulon",
    "pilophorus", "argopsis", "bunodophoron", "sphaerophorus", "acalospora", "placopsis",
    "ionaspis", "hymenelia", "aspicilia", "circinaria", "lobothallia", "megaspora", "ochrolechopsis",
    "varicosporopsis", "varicospora", "coccotrema", "thelenellopsis", "gvalectidium", "coenogonium",
    "dyplolabia", "phaeographopsis", "diorygma", "thalloloma", "helographa", "platygrammeopsis",
    "sclerophyton", "lecanactis", "mazosia", "mazosiella", "eopyrenula", "julella", "pleomassaria",
    "melanotopelia", "topelia", "ramonia", "gvalecta", "cryptodiscus", "absconditella",
    "thelocarpon", "thrombium", "thromboideum", "protothelenella", "thelenellina", "belonia",
    "gvalideopsis", "coenogoniopsis", "dyplolabiella", "graphinas", "phaeosphaeriax", "anisomeridella",
    "pyrenulopsis", "lithotheliopsis", "polymeridiella", "tryptheliumx", "astrotheliopsis",
    "strigulopsis", "phylloporopsis", "porinopsis", "trichotheliopsis", "clathroporinella",
    "thelenellopsisx", "topeliopsella", "pecteniopsis", "protopannariella", "moelleropsella",
    "lichinella", "leprocaulopsis", "stereocaulopsis", "pilophoropsis", "bunodophoropsis",
    "sphaerophoropsis", "acalosporopsis", "placopsella", "ionaspopsis", "hymeneliopsis",
    "aspiciliopsis", "circinariella", "lobothalliopsis", "megasporopsis", "coccotremopsis",
    "gvalectidella", "coenogoniella", "thallolomopsis", "sclerophytonella", "lecanactopsis",
    "mazosiopsis", "eopyrenulopsis", "julellopsis", "melanotopelopsis", "topeliella", "ramoniopsis",
    "absconditellopsis", "thelocarponella", "thrombiopsis", "protothelenellopsis", "beloniopsis",
]


def extra_used():
    used_w, used_es, used_pl, used_pr, used_ax, used_seed, used_err = (
        load_set("widgets"), load_set("errslugs"), load_set("places"),
        load_set("prefixes"), load_set("auxes"), load_set("seeds"), load_set("errs"),
    )
    for name in (
        "brw-mill-r395-extra8.py", "brw-mill-r395-extra9.py",
        "brw-mill-r395-extra10.py", "brw-mill-r395-extra11.py",
        "brw-mill-r395-extra12.py", "brw-mill-r395-extra13.py",
    ):
        spec = importlib.util.spec_from_file_location(name, HERE / name)
        mod = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(mod)
        for p in mod.EXTRA:
            used_w.add(p["widget"]); used_es.add(p["err_slug"])
            used_pl.add(p["ok_place"]); used_pl.add(p["bad_place"])
            used_pr.add(p["prefix"]); used_ax.add(p["aux"])
            used_seed.add(p["seed_ok"]); used_seed.add(p["seed_bad"]); used_err.add(p["err"])
    return used_w, used_es, used_pl, used_pr, used_ax, used_seed, used_err


def main() -> int:
    if len(set(GENERA)) != len(GENERA):
        from collections import Counter
        c = Counter(GENERA)
        raise SystemExit(f"dup genera {[k for k,v in c.items() if v>1]}")
    used_w, used_es, used_pl, used_pr, used_ax, used_seed, used_err = extra_used()
    used_keep: set[str] = set()
    skipped = 0
    kept: list[tuple] = []
    for plant in PLANTS:
        css, fr, to, js, widget, err, code, tmpl, btn, new, not_, teach = plant
        if code == 409:
            raise SystemExit(f"{widget}: 409 banned")
        if widget in used_w:
            skipped += 1
            continue
        used_w.add(widget)
        if err in used_err:
            err = err + "_x14"
            if err in used_err:
                skipped += 1
                used_w.discard(widget)
                continue
        used_err.add(err)
        kept.append((css, fr, to, js, widget, err, code, tmpl, btn, new, not_, teach))
    kept = kept[:180]
    if len(kept) > len(GENERA):
        raise SystemExit(f"need more genera {len(kept)}>{len(GENERA)}")
    rows = []
    for i, plant in enumerate(kept):
        css, fr, to, js, widget, err, code, tmpl, btn, new, not_, teach = plant
        item, neigh, fail, ref, nref, fref, x0, x1, y, title, path = T[tmpl]
        prefix = mint("".join(ch for ch in widget if ch.isalnum())[:4] or "ecp", used_pr)
        aux = mint(("".join(ch for ch in widget if ch.isalnum())[2:6] or "eca") + "x", used_ax)
        if prefix == aux:
            aux = mint(aux + "z", used_ax)
        genus = GENERA[i]
        ok, bad = genus + "wyke", genus + "gill"
        if ok in used_pl or bad in used_pl:
            ok, bad = genus + "mere", genus + "slack"
        if ok in used_pl or bad in used_pl or ok == bad:
            raise SystemExit(f"place collision {ok} {bad}")
        used_pl.add(ok); used_pl.add(bad)
        slug = f"{aux}-{code}"
        if slug in used_es:
            raise SystemExit(f"err_slug collision {slug}")
        used_es.add(slug)
        seed_ok, seed_bad = f"css-{widget}", f"css-{widget}-{code}"
        if seed_ok in used_seed or seed_bad in used_seed:
            seed_ok, seed_bad = f"css-{widget}-x14", f"css-{widget}-x14-{code}"
        if seed_ok in used_seed or seed_bad in used_seed:
            raise SystemExit(f"seed collision {seed_ok}")
        used_seed.add(seed_ok); used_seed.add(seed_bad)
        keep = keep_code(genus, used_keep)
        nxt = kept[i + 1][4] if i + 1 < len(kept) else "catalog continue."
        not_ = not_.replace("extra12", "extra13").replace("extra11", "extra12")
        rows.append((
            prefix, aux, ok, bad, widget, slug, code, err,
            css, fr, to, js, item, neigh, fail, ref, nref, fref,
            x0, x1, y, btn, title, "Keep", path, keep, f"{item} {genus}", seed_ok, seed_bad,
            new, not_, teach, nxt + ".",
        ))
    out = HERE / "brw-mill-r395-extra14.py"
    lines = ['"""Leftover CSS plants after extra13 lichens wyke/gill."""', "KEYS = (",
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
