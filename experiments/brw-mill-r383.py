#!/usr/bin/env python3
"""Mill browser-tool-use-factory from r383. Unique CSS leftover, not r212–r382 clones."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("brw_mill_r212", HERE / "brw-mill-r212.py")
_m = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_m)

FACTORY = "browser-tool-use-factory"
GEN = "grok-4.6"
CATALOG_FIRST = 383

# Unused CSS leftover: not r105–r382 catalogs. Pair codes are not 409.
PAIRS: list[dict] = [
    {
        "prefix": "mathst", "aux": "mst", "ok_place": "glasswortcot", "bad_place": "samphirefen",
        "widget": "math-style", "err_slug": "mst-418", "code": 418, "err": "math_style",
        "css": "math-style", "from": "normal", "to": "compact", "js": "mathStyle",
        "item": "EQ-4", "neigh": "EQ-5", "fail_item": "EQ-5", "ref": "c4", "nref": "c5", "fref": "c5",
        "x0": 110, "x1": 92, "y": 88, "btn": "Compact style", "title": "Equations", "verb": "File",
        "path": "equations", "keep": "GW", "note": "EQ-4 glasswort",
        "seed_ok": "css-math-style-compact-box", "seed_bad": "css-math-style-compact-418",
        "new": "`math-style:compact` shrinks display math so stored x is EQ-5 (r226 was math-shift).",
        "not": "Not r226 math-shift compact, not r179 initial-letter.",
        "teach": "math-style is a used box. File EQ-4 by ref.",
        "next": "ruby-merge.",
    },
    {
        "prefix": "rubym", "aux": "rmg", "ok_place": "seablitecot", "bad_place": "pickleweedbar",
        "widget": "ruby-merge", "err_slug": "rmg-403", "code": 403, "err": "ruby_merge",
        "css": "ruby-merge", "from": "separate", "to": "collapse", "js": "rubyMerge",
        "item": "Gloss", "neigh": "rt", "fail_item": "rt", "ref": "c1", "nref": "r1", "fref": "r1",
        "x0": 120, "x1": 96, "y": 72, "btn": "Merge ruby", "title": "Rubies", "verb": "Keep",
        "path": "rubies", "keep": "SB", "note": "Gloss seablite",
        "seed_ok": "css-ruby-merge-collapse-shift", "seed_bad": "css-ruby-merge-collapse-403",
        "new": "`ruby-merge:collapse` joins adjacent rt so stored separate-x is the neighbor rt.",
        "not": "Not r232 ruby-position under, not r188 ruby-overhang.",
        "teach": "Collapsed ruby is still Gloss. Do not keep rt.",
        "next": "grid-auto-flow dense.",
    },
    {
        "prefix": "dense", "aux": "gaf", "ok_place": "laminariacot", "bad_place": "wrackholt",
        "widget": "grid-auto-flow", "err_slug": "gaf-428", "code": 428, "err": "dense_pack",
        "css": "grid-auto-flow", "from": "row", "to": "dense", "js": "gridAutoFlow",
        "item": "CD-3", "neigh": "CD-4", "fail_item": "CD-1", "ref": "c3", "nref": "c4", "fref": "c1",
        "x0": 200, "x1": 80, "y": 64, "btn": "Dense pack", "title": "Cards", "verb": "Keep",
        "path": "cards", "keep": "LM", "note": "CD-3 laminaria",
        "seed_ok": "css-grid-auto-flow-dense-restack", "seed_bad": "css-grid-auto-flow-dense-428",
        "new": "`grid-auto-flow:dense` backfills holes so stored row-x is CD-1.",
        "not": "Not r165 masonry pack, not r368 grid-template-areas.",
        "teach": "Dense packing restacks. Keep CD-3 by ref.",
        "next": "word-break auto-phrase.",
    },
    {
        "prefix": "phrase", "aux": "wbp", "ok_place": "dulsebar", "bad_place": "noriholt",
        "widget": "word-break-auto-phrase", "err_slug": "wbp-414", "code": 414, "err": "auto_phrase",
        "css": "word-break", "from": "normal", "to": "auto-phrase", "js": "wordBreak",
        "item": "BINDING-COMPLETE", "neigh": "BINDING…", "fail_item": "BIND", "ref": "c1", "nref": "c1", "fref": "c0",
        "x0": 24, "x1": 24, "y": 48, "btn": "Auto phrase", "title": "Labels", "verb": "File",
        "path": "labels", "keep": "DL", "note": "BINDING-COMPLETE dulse",
        "seed_ok": "css-word-break-auto-phrase-wrap", "seed_bad": "css-word-break-auto-phrase-414",
        "new": "`word-break:auto-phrase` wraps on phrase boundaries so OCR reads BINDING… not BINDING-COMPLETE.",
        "not": "Not r215 line-clamp, not r182 text-autospace.",
        "teach": "Phrase wrap is not the accessible name. File BINDING-COMPLETE.",
        "next": "contain inline-size.",
    },
    {
        "prefix": "cins", "aux": "cis", "ok_place": "wakamecot", "bad_place": "kombufen",
        "widget": "contain-inline-size", "err_slug": "cis-428", "code": 428, "err": "inline_size",
        "css": "contain", "from": "none", "to": "inline-size", "js": "contain",
        "item": "CH-2", "neigh": "CH-3", "fail_item": "CH-3", "ref": "c2", "nref": "c3", "fref": "c3",
        "x0": 180, "x1": 140, "y": 70, "btn": "Contain inline", "title": "Chips", "verb": "Keep",
        "path": "chips", "keep": "WK", "note": "CH-2 wakame",
        "seed_ok": "css-contain-inline-size-reflow", "seed_bad": "css-contain-inline-size-428",
        "new": "`contain:inline-size` ignores children for inline size so stored uncontained x is CH-3.",
        "not": "Not r112 overflow clip, not r370 clamp().",
        "teach": "Inline-size containment is live metrics. Keep CH-2 by ref.",
        "next": "appearance base-select.",
    },
    {
        "prefix": "basesel", "aux": "aps", "ok_place": "hijikifen", "bad_place": "aramebar",
        "widget": "appearance-base-select", "err_slug": "aps-501", "code": 501, "err": "base_select",
        "css": "appearance", "from": "auto", "to": "base-select", "js": "appearance",
        "item": "opt-2", "neigh": "Open", "fail_item": "unset", "ref": "i2", "nref": "e4", "fref": "i0",
        "x0": 40, "x1": 40, "y": 96, "btn": "Base select", "title": "Selects", "verb": "Save",
        "path": "selects", "keep": "HJ", "note": "opt-2 hijiki",
        "seed_ok": "css-appearance-base-select-picker", "seed_bad": "css-appearance-base-select-501",
        "new": "`appearance:base-select` restyles the picker. Clicking Open is not choosing opt-2.",
        "not": "Not r218 command show-picker, not r113 native showPicker.",
        "teach": "The base picker chrome is not a value. Save after opt-2 is selected.",
        "next": "text-overflow fade.",
    },
    {
        "prefix": "fadeov", "aux": "tof", "ok_place": "lavercot", "bad_place": "bladderwrackfen",
        "widget": "text-overflow-fade", "err_slug": "tof-410", "code": 410, "err": "fade_empty",
        "css": "text-overflow", "from": "clip", "to": "fade", "js": "textOverflow",
        "item": "LB-6", "neigh": "LB-7", "fail_item": "LB-7", "ref": "c6", "nref": "c7", "fref": "c7",
        "x0": 200, "x1": 200, "y": 56, "btn": "Fade overflow", "title": "Labels", "verb": "Keep",
        "path": "labels", "keep": "LV", "note": "LB-6 laver",
        "seed_ok": "css-text-overflow-fade-hole", "seed_bad": "css-text-overflow-fade-410",
        "new": "`text-overflow:fade` paints a transparent tail. Center click on the fade is empty.",
        "not": "Not r215 line-clamp ellipsis, not r219 background-clip text.",
        "teach": "The fade is still LB-6. Do not keep the neighbor under the hole.",
        "next": "outline-offset.",
    },
    {
        "prefix": "outl", "aux": "olo", "ok_place": "thongweedbar", "bad_place": "oarweedholt",
        "widget": "outline-offset", "err_slug": "olo-404", "code": 404, "err": "outline_miss",
        "css": "outline-offset", "from": "0px", "to": "12px", "js": "outlineOffset",
        "item": "FL-3", "neigh": "FL-4", "fail_item": "FL-4", "ref": "c3", "nref": "c4", "fref": "c4",
        "x0": 148, "x1": 148, "y": 80, "btn": "Offset outline", "title": "Floats", "verb": "Keep",
        "path": "floats", "keep": "TW", "note": "FL-3 thongweed",
        "seed_ok": "css-outline-offset-paint", "seed_bad": "css-outline-offset-404",
        "new": "`outline-offset:12px` paints outside the border box. Screenshot of the ring is not FL-3.",
        "not": "Not r163 :focus-visible outline, not r129 clip-path.",
        "teach": "Outline offset is paint, not hit. Keep the border-box ref.",
        "next": "white-space break-spaces.",
    },
    {
        "prefix": "brsp", "aux": "wsb", "ok_place": "sugarwrackcot", "bad_place": "dabberlockfen",
        "widget": "white-space-break-spaces", "err_slug": "wsb-413", "code": 413, "err": "break_spaces",
        "css": "white-space", "from": "pre-wrap", "to": "break-spaces", "js": "whiteSpace",
        "item": "memo", "neigh": "SP", "fail_item": "memo-sp", "ref": "e1", "nref": "e1", "fref": "e0",
        "x0": 16, "x1": 16, "y": 40, "btn": "Break spaces", "title": "Memos", "verb": "File",
        "path": "memos", "keep": "SW", "note": "memo sugarwrack",
        "seed_ok": "css-white-space-break-spaces", "seed_bad": "css-white-space-break-spaces-413",
        "new": "`white-space:break-spaces` wraps on trailing spaces so the visual line is not the pre-wrap payload.",
        "not": "Not r183 white-space-collapse, not r221 textarea wrap=hard.",
        "teach": "Trailing-space wrap is not the value. File without inserted breaks.",
        "next": "hyphens manual.",
    },
    {
        "prefix": "hyman", "aux": "hym", "ok_place": "sealettucebar", "bad_place": "ulvacot",
        "widget": "hyphens-manual", "err_slug": "hym-400", "code": 400, "err": "manual_hyphen",
        "css": "hyphens", "from": "auto", "to": "manual", "js": "hyphens",
        "item": "COMPLETE", "neigh": "COM-", "fail_item": "COM", "ref": "c1", "nref": "c1", "fref": "c0",
        "x0": 28, "x1": 28, "y": 50, "btn": "Manual hyphens", "title": "Labels", "verb": "File",
        "path": "labels", "keep": "SL", "note": "COMPLETE sealettuce",
        "seed_ok": "css-hyphens-manual-shy", "seed_bad": "css-hyphens-manual-400",
        "new": "`hyphens:manual` only breaks at &shy; so auto-hyphen OCR COM- is gone and the box reflows.",
        "not": "Not r189 hyphenate-limit-chars, not r229 hyphenate-limit-last.",
        "teach": "Manual hyphens are not the accessible name. File COMPLETE.",
        "next": "resize both.",
    },
    {
        "prefix": "resz", "aux": "rzb", "ok_place": "porphyraholt", "bad_place": "gracilariacot",
        "widget": "resize-both", "err_slug": "rzb-422", "code": 422, "err": "resize_box",
        "css": "resize", "from": "none", "to": "both", "js": "resize",
        "item": "NT-2", "neigh": "NT-3", "fail_item": "NT-3", "ref": "c2", "nref": "c3", "fref": "c3",
        "x0": 160, "x1": 220, "y": 80, "btn": "Resize both", "title": "Notes", "verb": "Keep",
        "path": "notes", "keep": "PH", "note": "NT-2 porphyra",
        "seed_ok": "css-resize-both-used-box", "seed_bad": "css-resize-both-422",
        "new": "`resize:both` lets the note grow so stored x is NT-3 after a drag.",
        "not": "Not r370 clamp() width, not r352 fit-content.",
        "teach": "A resized box is live. Keep NT-2 by ref, not the handle.",
        "next": "flex-grow.",
    },
    {
        "prefix": "flxg", "aux": "fxg", "ok_place": "alariacot", "bad_place": "eiseniabar",
        "widget": "flex-grow", "err_slug": "fxg-412", "code": 412, "err": "flex_grow",
        "css": "flex-grow", "from": "0", "to": "2", "js": "flexGrow",
        "item": "CH-4", "neigh": "CH-5", "fail_item": "CH-5", "ref": "c4", "nref": "c5", "fref": "c5",
        "x0": 96, "x1": 180, "y": 64, "btn": "Grow 2", "title": "Chips", "verb": "Keep",
        "path": "chips", "keep": "AL", "note": "CH-4 alaria",
        "seed_ok": "css-flex-grow-2-shift", "seed_bad": "css-flex-grow-2-412",
        "new": "`flex-grow:2` eats leftover space so stored flex-grow:0 x is CH-5.",
        "not": "Not r366 justify-content space-evenly, not r172 sibling-count gap.",
        "teach": "flex-grow is live. Keep CH-4 by ref.",
        "next": "catalog continue.",
    },
]


def spec_for_round(rnd: int) -> dict:
    idx = rnd - CATALOG_FIRST
    if idx < 0 or idx >= len(PAIRS):
        raise SystemExit(f"no plant for r{rnd} (catalog {CATALOG_FIRST}+{len(PAIRS)})")
    return PAIRS[idx]


def build_round(rnd: int):
    spec = spec_for_round(rnd)
    if spec["prefix"] == spec["aux"] or spec["prefix"] == "api" or spec["aux"] == "api":
        raise SystemExit(f"r{rnd}: prefix/aux/api must be distinct")
    eps = [_m.success_episode(rnd, spec), _m.fail_episode(rnd, spec)]
    errs: list[str] = []
    for ep in eps:
        errs.extend(_m.contract_ok(ep))
    if _m.USED_HOSTS.exists():
        used = set(_m.USED_HOSTS.read_text().split())
        for ep in eps:
            blob = json.dumps(ep)
            for h in __import__("re").findall(r"https://([a-z0-9.-]+\.example)", blob):
                if h in used:
                    errs.append(f"reused host {h}")
    if _m.USED_PLACES.exists():
        used_p = set(_m.USED_PLACES.read_text().split())
        for p in (spec["ok_place"], spec["bad_place"]):
            if p in used_p:
                errs.append(f"reused place {p}")
    if errs:
        raise SystemExit("contract:\n" + "\n".join(errs))
    return eps, _m.notes_for(rnd, spec)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    eps, notes = build_round(args.round)
    _m.write_stage(args.out, args.round, eps, notes)
    print(json.dumps({"round": args.round, "ids": [e["id"] for e in eps], "bytes": sum(len(json.dumps(e)) for e in eps)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
