#!/usr/bin/env python3
"""Mill browser-tool-use-factory from r395. Unique CSS leftover, not r01–r394 clones."""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("brw_mill_r212", HERE / "brw-mill-r212.py")
_m = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_m)

FACTORY = "browser-tool-use-factory"
GEN = "grok-4.6"
CATALOG_FIRST = 395

# Unused leftover: not r01–r394 catalogs (flex-grow r394, resize r393, …). Pair codes are not 409.
PAIRS: list[dict] = [
    {
        "prefix": "fshrk", "aux": "fsk", "ok_place": "cystoseiracot", "bad_place": "sargassumholt",
        "widget": "flex-shrink", "err_slug": "fsk-428", "code": 428, "err": "flex_shrink",
        "css": "flex-shrink", "from": "1", "to": "0", "js": "flexShrink",
        "item": "CH-4", "neigh": "CH-5", "fail_item": "CH-5", "ref": "c4", "nref": "c5", "fref": "c5",
        "x0": 96, "x1": 160, "y": 64, "btn": "Shrink 0", "title": "Chips", "verb": "Keep",
        "path": "chips", "keep": "CY", "note": "CH-4 cystoseira",
        "seed_ok": "css-flex-shrink-0-shift", "seed_bad": "css-flex-shrink-0-428",
        "new": "`flex-shrink:0` refuses to shrink so stored shrink-x is CH-5.",
        "not": "Not r394 flex-grow, not r307 flex-basis:content.",
        "teach": "flex-shrink is live. Keep CH-4 by ref.",
        "next": "align-self.",
    },
    {
        "prefix": "aself", "aux": "asf", "ok_place": "fucusbar", "bad_place": "pelvetiafen",
        "widget": "align-self", "err_slug": "asf-410", "code": 410, "err": "align_self",
        "css": "align-self", "from": "auto", "to": "end", "js": "alignSelf",
        "item": "CH-2", "neigh": "CH-3", "fail_item": "CH-3", "ref": "c2", "nref": "c3", "fref": "c3",
        "x0": 80, "x1": 80, "y": 40, "btn": "Self end", "title": "Chips", "verb": "Keep",
        "path": "chips", "keep": "FC", "note": "CH-2 fucus",
        "seed_ok": "css-align-self-end-shift", "seed_bad": "css-align-self-end-410",
        "new": "`align-self:end` slides one item so stored auto y is CH-3.",
        "not": "Not r350 align-items:baseline, not r309 justify-self, not r374 place-self.",
        "teach": "align-self is per-item. Keep CH-2 by ref.",
        "next": "gap shorthand.",
    },
    {
        "prefix": "gapsh", "aux": "gsh", "ok_place": "himanthaliaquay", "bad_place": "ascophyllumcot",
        "widget": "gap-shorthand", "err_slug": "gsh-412", "code": 412, "err": "gap_shorthand",
        "css": "gap", "from": "0px", "to": "24px", "js": "gap",
        "item": "CH-3", "neigh": "CH-4", "fail_item": "CH-4", "ref": "c3", "nref": "c4", "fref": "c4",
        "x0": 120, "x1": 144, "y": 64, "btn": "Gap 24", "title": "Chips", "verb": "Keep",
        "path": "chips", "keep": "HM", "note": "CH-3 himanthalia",
        "seed_ok": "css-gap-shorthand-24", "seed_bad": "css-gap-shorthand-412",
        "new": "`gap:24px` (shorthand) restacks both axes so stored 0-gap x is CH-4.",
        "not": "Not r365 row-gap, not r373 column-gap.",
        "teach": "The gap shorthand is live metrics. Keep CH-3 by ref.",
        "next": "inset-inline-start.",
    },
    {
        "prefix": "inlst", "aux": "iis", "ok_place": "dictyotafen", "bad_place": "padinabar",
        "widget": "inset-inline-start", "err_slug": "iis-412", "code": 412, "err": "inset_inline",
        "css": "inset-inline-start", "from": "0px", "to": "40px", "js": "insetInlineStart",
        "item": "AB-2", "neigh": "AB-3", "fail_item": "AB-3", "ref": "c2", "nref": "c3", "fref": "c3",
        "x0": 16, "x1": 56, "y": 48, "btn": "Inset 40", "title": "Abspos", "verb": "Keep",
        "path": "abspos", "keep": "DT", "note": "AB-2 dictyota",
        "seed_ok": "css-inset-inline-start-40", "seed_bad": "css-inset-inline-start-412",
        "new": "`inset-inline-start:40px` slides abspos so stored 0-inset x is empty.",
        "not": "Not r313 translate property, not r164 offset-path.",
        "teach": "Logical inset is live. Keep AB-2 by ref.",
        "next": "margin-inline.",
    },
    {
        "prefix": "mrgin", "aux": "mri", "ok_place": "undariaholt", "bad_place": "eckloniacot",
        "widget": "margin-inline", "err_slug": "mri-412", "code": 412, "err": "margin_inline",
        "css": "margin-inline", "from": "0px", "to": "24px", "js": "marginInline",
        "item": "CH-4", "neigh": "CH-5", "fail_item": "CH-5", "ref": "c4", "nref": "c5", "fref": "c5",
        "x0": 96, "x1": 120, "y": 64, "btn": "Margin 24", "title": "Chips", "verb": "Keep",
        "path": "chips", "keep": "UN", "note": "CH-4 undaria",
        "seed_ok": "css-margin-inline-24-shift", "seed_bad": "css-margin-inline-412",
        "new": "`margin-inline:24px` pushes the chip so stored 0-margin x is CH-5.",
        "not": "Not r176 margin-trim, not r373 column-gap.",
        "teach": "Logical margin is live. Keep CH-4 by ref.",
        "next": "padding-block.",
    },
    {
        "prefix": "padbk", "aux": "pdb", "ok_place": "lessoniabar", "bad_place": "macrocystisfen",
        "widget": "padding-block", "err_slug": "pdb-410", "code": 410, "err": "padding_block",
        "css": "padding-block", "from": "0px", "to": "20px", "js": "paddingBlock",
        "item": "RW-2", "neigh": "RW-3", "fail_item": "RW-3", "ref": "c2", "nref": "c3", "fref": "c3",
        "x0": 24, "x1": 24, "y": 72, "btn": "Pad block", "title": "Rows", "verb": "Keep",
        "path": "rows", "keep": "LS", "note": "RW-2 lessonia",
        "seed_ok": "css-padding-block-20-cover", "seed_bad": "css-padding-block-410",
        "new": "`padding-block:20px` grows the used box so stored y is RW-3.",
        "not": "Not r341 line-height, not r365 row-gap.",
        "teach": "Block padding is live. Keep RW-2 by ref.",
        "next": "border-inline-end-width.",
    },
    {
        "prefix": "biewd", "aux": "bie", "ok_place": "nereocystisholt", "bad_place": "postelsiacot",
        "widget": "border-inline-end", "err_slug": "bie-404", "code": 404, "err": "border_inline_end",
        "css": "border-inline-end-width", "from": "0px", "to": "16px", "js": "borderInlineEndWidth",
        "item": "CH-3", "neigh": "CH-4", "fail_item": "CH-4", "ref": "c3", "nref": "c4", "fref": "c4",
        "x0": 148, "x1": 148, "y": 64, "btn": "Border 16", "title": "Chips", "verb": "Keep",
        "path": "chips", "keep": "NR", "note": "CH-3 nereocystis",
        "seed_ok": "css-border-inline-end-16-paint", "seed_bad": "css-border-inline-end-404",
        "new": "`border-inline-end-width:16px` paints a gutter. Center click on the border is not CH-3.",
        "not": "Not r306 column-rule-width, not r390 outline-offset.",
        "teach": "The logical border is paint. Keep the content-box ref.",
        "next": "overflow-block.",
    },
    {
        "prefix": "ovblk", "aux": "ovbk", "ok_place": "pterygophorabar", "bad_place": "durvillaeaholt",
        "widget": "overflow-block", "err_slug": "ovbk-404", "code": 404, "err": "overflow_block",
        "css": "overflow-block", "from": "visible", "to": "clip", "js": "overflowBlock",
        "item": "CH-6", "neigh": "CH-7", "fail_item": "CH-7", "ref": "c6", "nref": "c7", "fref": "c7",
        "x0": 200, "x1": 200, "y": 96, "btn": "Clip block", "title": "Chips", "verb": "Keep",
        "path": "chips", "keep": "PT", "note": "CH-6 pterygophora",
        "seed_ok": "css-overflow-block-clip", "seed_bad": "css-overflow-block-404",
        "new": "`overflow-block:clip` cuts the overflowing chip. Stored visible y is empty.",
        "not": "Not r378 overflow-x:clip, not r112 overflow:clip.",
        "teach": "Block-axis clip is not x-clip. Keep the remaining lobe ref.",
        "next": "block-size.",
    },
    {
        "prefix": "blksz", "aux": "bsz", "ok_place": "iridaeafen", "bad_place": "chondrusbar",
        "widget": "block-size", "err_slug": "bsz-410", "code": 410, "err": "block_size",
        "css": "block-size", "from": "auto", "to": "120px", "js": "blockSize",
        "item": "CD-3", "neigh": "CD-4", "fail_item": "CD-4", "ref": "c3", "nref": "c4", "fref": "c4",
        "x0": 40, "x1": 40, "y": 80, "btn": "Block 120", "title": "Cards", "verb": "Keep",
        "path": "cards", "keep": "IR", "note": "CD-3 iridaea",
        "seed_ok": "css-block-size-120-cover", "seed_bad": "css-block-size-410",
        "new": "`block-size:120px` grows height so stored auto y is CD-4.",
        "not": "Not r353 height:stretch, not r351 aspect-ratio.",
        "teach": "Logical block-size is live. Keep CD-3 by ref.",
        "next": "inline-size.",
    },
    {
        "prefix": "inlsz", "aux": "isz", "ok_place": "mastocarpuscot", "bad_place": "gigartinafen",
        "widget": "inline-size", "err_slug": "isz-428", "code": 428, "err": "inline_size_longhand",
        "css": "inline-size", "from": "auto", "to": "80px", "js": "inlineSize",
        "item": "CH-2", "neigh": "CH-3", "fail_item": "CH-3", "ref": "c2", "nref": "c3", "fref": "c3",
        "x0": 160, "x1": 80, "y": 64, "btn": "Inline 80", "title": "Chips", "verb": "Keep",
        "path": "chips", "keep": "MS", "note": "CH-2 mastocarpus",
        "seed_ok": "css-inline-size-80-shrink", "seed_bad": "css-inline-size-428",
        "new": "`inline-size:80px` shrinks the chip so stored auto x is CH-3.",
        "not": "Not r387 contain:inline-size, not r352 width:fit-content.",
        "teach": "Logical inline-size is live. Keep CH-2 by ref.",
        "next": "min-block-size.",
    },
    {
        "prefix": "mnbks", "aux": "mbs", "ok_place": "calliblepharisbar", "bad_place": "palmariaholt",
        "widget": "min-block-size", "err_slug": "mbs-410", "code": 410, "err": "min_block_size",
        "css": "min-block-size", "from": "0px", "to": "96px", "js": "minBlockSize",
        "item": "RW-3", "neigh": "RW-4", "fail_item": "RW-4", "ref": "c3", "nref": "c4", "fref": "c4",
        "x0": 24, "x1": 24, "y": 70, "btn": "Min block 96", "title": "Rows", "verb": "Keep",
        "path": "rows", "keep": "CB", "note": "RW-3 calliblepharis",
        "seed_ok": "css-min-block-size-96", "seed_bad": "css-min-block-size-410",
        "new": "`min-block-size:96px` forbids shrinking so stored y is RW-4.",
        "not": "Not r354 min-width:min-content, not this mill's block-size longhand.",
        "teach": "min-block-size is live. Keep RW-3 by ref.",
        "next": "max-inline-size.",
    },
    {
        "prefix": "mxinl", "aux": "mxi", "ok_place": "rhodymeniacot", "bad_place": "ceramiumfen",
        "widget": "max-inline-size", "err_slug": "mxi-428", "code": 428, "err": "max_inline_size",
        "css": "max-inline-size", "from": "none", "to": "100px", "js": "maxInlineSize",
        "item": "CH-5", "neigh": "CH-6", "fail_item": "CH-6", "ref": "c5", "nref": "c6", "fref": "c6",
        "x0": 180, "x1": 100, "y": 64, "btn": "Max inline 100", "title": "Chips", "verb": "Keep",
        "path": "chips", "keep": "RH", "note": "CH-5 rhodymenia",
        "seed_ok": "css-max-inline-size-100", "seed_bad": "css-max-inline-size-428",
        "new": "`max-inline-size:100px` caps width so stored unconstrained x is CH-6.",
        "not": "Not r370 clamp() width, not this mill's inline-size longhand.",
        "teach": "max-inline-size is live. Keep CH-5 by ref.",
        "next": "font-feature-settings.",
    },
    {
        "prefix": "ffeat", "aux": "ffs", "ok_place": "polysiphoniabar", "bad_place": "dasyaholt",
        "widget": "font-feature-settings", "err_slug": "ffs-412", "code": 412, "err": "feature_settings",
        "css": "font-feature-settings", "from": "normal", "to": '"ss01" 1', "js": "fontFeatureSettings",
        "item": "GL-2", "neigh": "GL-3", "fail_item": "GL-3", "ref": "c2", "nref": "c3", "fref": "c3",
        "x0": 88, "x1": 104, "y": 56, "btn": "ss01 on", "title": "Glyphs", "verb": "Keep",
        "path": "glyphs", "keep": "PS", "note": "GL-2 polysiphonia",
        "seed_ok": "css-font-feature-settings-ss01", "seed_bad": "css-font-feature-settings-412",
        "new": '`font-feature-settings: "ss01" 1` swaps a wider glyph so stored x is GL-3.',
        "not": "Not r337 font-variant-alternates:swash, not r326 font-kerning.",
        "teach": "OpenType ss01 is live metrics. Keep GL-2 by ref.",
        "next": "font-variant-caps.",
    },
    {
        "prefix": "fvcps", "aux": "fvc", "ok_place": "laurenciacot", "bad_place": "chondriafen",
        "widget": "font-variant-caps", "err_slug": "fvc-415", "code": 415, "err": "variant_caps",
        "css": "font-variant-caps", "from": "normal", "to": "all-small-caps", "js": "fontVariantCaps",
        "item": "File", "neigh": "FILE", "fail_item": "FILE", "ref": "e5", "nref": "c9", "fref": "c9",
        "x0": 70, "x1": 70, "y": 96, "btn": "Small caps", "title": "Type", "verb": "File",
        "path": "type", "keep": "LR", "note": "File laurencia",
        "seed_ok": "css-font-variant-caps-all-small", "seed_bad": "css-font-variant-caps-415",
        "new": "`font-variant-caps:all-small-caps` paints FILE so OCR reads a different control.",
        "not": "Not r237 font-synthesis-small-caps:none, not r327 ligatures.",
        "teach": "Small-caps paint is not a new verb. File the button ref.",
        "next": "text-underline-position.",
    },
    {
        "prefix": "undps", "aux": "tup", "ok_place": "acanthophorabar", "bad_place": "hypneaholt",
        "widget": "underline-position", "err_slug": "tup-404", "code": 404, "err": "underline_position",
        "css": "text-underline-position", "from": "auto", "to": "under", "js": "textUnderlinePosition",
        "item": "Link", "neigh": "File", "fail_item": "File", "ref": "a1", "nref": "e5", "fref": "e5",
        "x0": 90, "x1": 90, "y": 118, "btn": "Underline under", "title": "Links", "verb": "File",
        "path": "links", "keep": "AP", "note": "Link acanthophora",
        "seed_ok": "css-text-underline-position-under", "seed_bad": "css-text-underline-position-404",
        "new": "`text-underline-position:under` drops the line onto File so a y-click hits decoration.",
        "not": "Not r257 text-underline-offset, not r163 :focus-visible outline, not this mill's underline-position.",
        "teach": "Underline position is paint. Link is a1; File is e5.",
        "next": "text-decoration-thickness.",
    },
    {
        "prefix": "dthck", "aux": "tdt", "ok_place": "solieriacot", "bad_place": "eucheumafen",
        "widget": "decoration-thickness", "err_slug": "tdt-404", "code": 404, "err": "decoration_thickness",
        "css": "text-decoration-thickness", "from": "auto", "to": "8px", "js": "textDecorationThickness",
        "item": "LB-4", "neigh": "LB-5", "fail_item": "LB-5", "ref": "c4", "nref": "c5", "fref": "c5",
        "x0": 160, "x1": 160, "y": 72, "btn": "Thick 8", "title": "Labels", "verb": "Keep",
        "path": "labels", "keep": "SO", "note": "LB-4 solieria",
        "seed_ok": "css-text-decoration-thickness-8", "seed_bad": "css-text-decoration-thickness-404",
        "new": "`text-decoration-thickness:8px` paints a fat strike. Center click on the bar is not LB-4.",
        "not": "Not r258 skip-ink, not this mill's underline-position.",
        "teach": "Thickness is paint. Keep the label ref.",
        "next": "text-emphasis-style.",
    },
    {
        "prefix": "emsty", "aux": "tes", "ok_place": "kappaphycusbar", "bad_place": "gelidiumholt",
        "widget": "emphasis-style", "err_slug": "tes-415", "code": 415, "err": "emphasis_style",
        "css": "text-emphasis-style", "from": "none", "to": "filled sesame", "js": "textEmphasisStyle",
        "item": "KM-2", "neigh": "dot", "fail_item": "dot", "ref": "c2", "nref": "d1", "fref": "d1",
        "x0": 100, "x1": 100, "y": 40, "btn": "Sesame", "title": "Marks", "verb": "Keep",
        "path": "marks", "keep": "KP", "note": "KM-2 kappaphycus",
        "seed_ok": "css-text-emphasis-style-sesame", "seed_bad": "css-text-emphasis-style-415",
        "new": "`text-emphasis-style:filled sesame` paints dots above. OCR of a sesame is not KM-2.",
        "not": "Not r195 text-emphasis-position, not r179 initial-letter.",
        "teach": "Emphasis marks are not the name. Keep the article ref.",
        "next": "text-transform.",
    },
    {
        "prefix": "ttfrm", "aux": "ttx", "ok_place": "pterocladiacot", "bad_place": "ahnfeltiafen",
        "widget": "text-transform", "err_slug": "ttx-415", "code": 415, "err": "text_transform",
        "css": "text-transform", "from": "none", "to": "uppercase", "js": "textTransform",
        "item": "open", "neigh": "OPEN", "fail_item": "OPEN", "ref": "c1", "nref": "c2", "fref": "c2",
        "x0": 80, "x1": 88, "y": 70, "btn": "Uppercase", "title": "Verbs", "verb": "File",
        "path": "verbs", "keep": "PC", "note": "open pterocladia",
        "seed_ok": "css-text-transform-uppercase", "seed_bad": "css-text-transform-415",
        "new": "`text-transform:uppercase` widens glyphs so OCR OPEN is not the a11y name open.",
        "not": "Not r014 font-variant-caps, not r170 contrast-color OCR.",
        "teach": "Transform is paint. File the a11y string.",
        "next": "caption-side.",
    },
    {
        "prefix": "capsd", "aux": "cps", "ok_place": "phyllophorabar", "bad_place": "odontaliaholt",
        "widget": "caption-side", "err_slug": "cps-410", "code": 410, "err": "caption_side",
        "css": "caption-side", "from": "top", "to": "bottom", "js": "captionSide",
        "item": "CAP-1", "neigh": "ROW-1", "fail_item": "ROW-1", "ref": "c1", "nref": "r1", "fref": "r1",
        "x0": 40, "x1": 40, "y": 16, "btn": "Caption bottom", "title": "Tables", "verb": "Keep",
        "path": "tables", "keep": "PH", "note": "CAP-1 phyllophora",
        "seed_ok": "css-caption-side-bottom", "seed_bad": "css-caption-side-410",
        "new": "`caption-side:bottom` moves the caption so stored top y is ROW-1.",
        "not": "Not r347 list-style-position:inside, not r300 ::marker.",
        "teach": "Caption side is live. Keep CAP-1 by ref.",
        "next": "empty-cells.",
    },
    {
        "prefix": "emptc", "aux": "emc", "ok_place": "bangiacot", "bad_place": "erythrotrichiafen",
        "widget": "empty-cells", "err_slug": "emc-404", "code": 404, "err": "empty_cells",
        "css": "empty-cells", "from": "show", "to": "hide", "js": "emptyCells",
        "item": "TD-2", "neigh": "hole", "fail_item": "hole", "ref": "c2", "nref": "h1", "fref": "h1",
        "x0": 120, "x1": 120, "y": 48, "btn": "Hide empty", "title": "Tables", "verb": "Keep",
        "path": "tables", "keep": "BA", "note": "TD-2 bangia",
        "seed_ok": "css-empty-cells-hide", "seed_bad": "css-empty-cells-404",
        "new": "`empty-cells:hide` unpaints an empty td. Stored center x is a hole, not TD-2.",
        "not": "Not r219 background-clip:text, not r358 mask-size hole.",
        "teach": "Hidden empty cells are still the cell ref. Do not keep the hole.",
        "next": "table-layout.",
    },
    {
        "prefix": "tblfx", "aux": "tlf", "ok_place": "goniotrichumbar", "bad_place": "batrachospermumholt",
        "widget": "table-layout", "err_slug": "tlf-428", "code": 428, "err": "table_fixed",
        "css": "table-layout", "from": "auto", "to": "fixed", "js": "tableLayout",
        "item": "COL-2", "neigh": "COL-3", "fail_item": "COL-3", "ref": "c2", "nref": "c3", "fref": "c3",
        "x0": 200, "x1": 140, "y": 36, "btn": "Fixed table", "title": "Tables", "verb": "Keep",
        "path": "tables", "keep": "GT", "note": "COL-2 goniotrichum",
        "seed_ok": "css-table-layout-fixed", "seed_bad": "css-table-layout-428",
        "new": "`table-layout:fixed` equalizes columns so stored auto x is COL-3.",
        "not": "Not r369 minmax columns, not r375 grid-auto-columns.",
        "teach": "Fixed tables restack. Keep COL-2 by ref.",
        "next": "border-collapse.",
    },
    {
        "prefix": "bcoll", "aux": "bcl", "ok_place": "lemaneacot", "bad_place": "nemalionfen",
        "widget": "border-collapse", "err_slug": "bcl-412", "code": 412, "err": "border_collapse",
        "css": "border-collapse", "from": "separate", "to": "collapse", "js": "borderCollapse",
        "item": "TD-3", "neigh": "TD-4", "fail_item": "TD-4", "ref": "c3", "nref": "c4", "fref": "c4",
        "x0": 168, "x1": 152, "y": 48, "btn": "Collapse", "title": "Tables", "verb": "Keep",
        "path": "tables", "keep": "LM", "note": "TD-3 lemanea",
        "seed_ok": "css-border-collapse-shift", "seed_bad": "css-border-collapse-412",
        "new": "`border-collapse:collapse` drops spacing so stored separate x is TD-4.",
        "not": "Not this mill's border-spacing, not r306 column-rule.",
        "teach": "Collapsed borders are live metrics. Keep TD-3 by ref.",
        "next": "border-spacing.",
    },
    {
        "prefix": "bspcg", "aux": "bsp", "ok_place": "scinaiabar", "bad_place": "galaxauraholt",
        "widget": "border-spacing", "err_slug": "bsp-412", "code": 412, "err": "border_spacing",
        "css": "border-spacing", "from": "8px", "to": "0px", "js": "borderSpacing",
        "item": "TD-2", "neigh": "TD-3", "fail_item": "TD-3", "ref": "c2", "nref": "c3", "fref": "c3",
        "x0": 140, "x1": 124, "y": 48, "btn": "Spacing 0", "title": "Tables", "verb": "Keep",
        "path": "tables", "keep": "SC", "note": "TD-2 scinaia",
        "seed_ok": "css-border-spacing-0", "seed_bad": "css-border-spacing-412",
        "new": "`border-spacing:0` (still separate) pulls cells so stored 8px x is TD-3.",
        "not": "Not this mill's border-collapse, not r373 column-gap.",
        "teach": "Spacing is not collapse. Keep TD-2 by ref.",
        "next": "visibility collapse.",
    },
    {
        "prefix": "viscl", "aux": "vcl", "ok_place": "liagoracot", "bad_place": "tricleocarpafen",
        "widget": "visibility-collapse", "err_slug": "vcl-410", "code": 410, "err": "visibility_collapse",
        "css": "visibility", "from": "visible", "to": "collapse", "js": "visibility",
        "item": "TR-3", "neigh": "TR-4", "fail_item": "TR-4", "ref": "c3", "nref": "c4", "fref": "c4",
        "x0": 24, "x1": 24, "y": 96, "btn": "Collapse row", "title": "Rows", "verb": "Keep",
        "path": "rows", "keep": "LI", "note": "TR-3 liagora",
        "seed_ok": "css-visibility-collapse-row", "seed_bad": "css-visibility-collapse-410",
        "new": "`visibility:collapse` on a table row removes it so stored y is TR-4.",
        "not": "Not r197 position-visibility, not this mill's border-collapse.",
        "teach": "Collapsed rows are gone. Re-find TR-3 or stop.",
        "next": "counter-increment.",
    },
    {
        "prefix": "ctrin", "aux": "cin", "ok_place": "actinothrixbar", "bad_place": "nemastomaholt",
        "widget": "counter-increment", "err_slug": "cin-506", "code": 506, "err": "counter_skip",
        "css": "counter-increment", "from": "item 1", "to": "item 2", "js": "counterIncrement",
        "item": "4", "neigh": "6", "fail_item": "6", "ref": "c4", "nref": "c6", "fref": "c6",
        "x0": 36, "x1": 36, "y": 144, "btn": "Skip 2", "title": "Lists", "verb": "Keep",
        "path": "lists", "keep": "AX", "note": "4 actinothrix",
        "seed_ok": "css-counter-increment-skip", "seed_bad": "css-counter-increment-506",
        "new": "`counter-increment:item 2` paints 6 on item 4. OCR 6 is not item 6.",
        "not": "Not r216 @counter-style symbols, not r347 list-style-position.",
        "teach": "A skipped counter glyph is not the item id. Keep the listitem ref.",
        "next": "list-style-image.",
    },
    {
        "prefix": "lsdim", "aux": "lsig", "ok_place": "plocamiumcot", "bad_place": "sphaerococcusfen",
        "widget": "list-style-image", "err_slug": "lsig-449", "code": 449, "err": "list_image",
        "css": "list-style-image", "from": "none", "to": "url(#mark)", "js": "listStyleImage",
        "item": "LI-2", "neigh": "mark", "fail_item": "mark", "ref": "c2", "nref": "m1", "fref": "m1",
        "x0": 8, "x1": 8, "y": 40, "btn": "Image marker", "title": "Lists", "verb": "Keep",
        "path": "lists", "keep": "PL", "note": "LI-2 plocamium",
        "seed_ok": "css-list-style-image-marker", "seed_bad": "css-list-style-image-449",
        "new": "`list-style-image:url(#mark)` is a generated hit. Clicking the image is not LI-2.",
        "not": "Not r300 ::marker, not r347 list-style-position:inside.",
        "teach": "The image marker is not the item. Keep the listitem ref.",
        "next": "border-image-outset.",
    },
    {
        "prefix": "bimgo", "aux": "bio", "ok_place": "griffithsiabar", "bad_place": "spyriadiaholt",
        "widget": "border-image-outset", "err_slug": "bio-404", "code": 404, "err": "border_image_outset",
        "css": "border-image-outset", "from": "0", "to": "12px", "js": "borderImageOutset",
        "item": "FL-3", "neigh": "FL-4", "fail_item": "FL-4", "ref": "c3", "nref": "c4", "fref": "c4",
        "x0": 148, "x1": 148, "y": 80, "btn": "Outset 12", "title": "Floats", "verb": "Keep",
        "path": "floats", "keep": "GR", "note": "FL-3 griffithsia",
        "seed_ok": "css-border-image-outset-12", "seed_bad": "css-border-image-outset-404",
        "new": "`border-image-outset:12px` paints outside the border box. Screenshot of the slice is not FL-3.",
        "not": "Not r390 outline-offset, not r316 inset box-shadow.",
        "teach": "Outset is paint, not hit. Keep the border-box ref.",
        "next": "box-sizing.",
    },
    {
        "prefix": "boxsz", "aux": "bxsg", "ok_place": "wrangeliacot", "bad_place": "dasysiphoniafen",
        "widget": "box-sizing", "err_slug": "bxsg-428", "code": 428, "err": "box_sizing",
        "css": "box-sizing", "from": "content-box", "to": "border-box", "js": "boxSizing",
        "item": "CH-4", "neigh": "CH-5", "fail_item": "CH-5", "ref": "c4", "nref": "c5", "fref": "c5",
        "x0": 200, "x1": 168, "y": 64, "btn": "Border-box", "title": "Chips", "verb": "Keep",
        "path": "chips", "keep": "WR", "note": "CH-4 wrangelia",
        "seed_ok": "css-box-sizing-border-box", "seed_bad": "css-box-sizing-428",
        "new": "`box-sizing:border-box` includes the border in width so stored content-box x is CH-5.",
        "not": "Not this mill's border-inline-end-width, not r352 fit-content.",
        "teach": "Box-sizing is live used width. Keep CH-4 by ref.",
        "next": "transform-origin.",
    },
    {
        "prefix": "tforg", "aux": "tfo", "ok_place": "heterosiphoniabar", "bad_place": "pterosiphoniaholt",
        "widget": "transform-origin", "err_slug": "tfo-520", "code": 520, "err": "transform_origin",
        "css": "transform-origin", "from": "center", "to": "left top", "js": "transformOrigin",
        "item": "CD-3", "neigh": "CD-4", "fail_item": "CD-4", "ref": "c3", "nref": "c4", "fref": "c4",
        "x0": 160, "x1": 120, "y": 80, "btn": "Origin left", "title": "Cards", "verb": "Keep",
        "path": "cards", "keep": "HS", "note": "CD-3 heterosiphonia",
        "seed_ok": "css-transform-origin-left-top", "seed_bad": "css-transform-origin-520",
        "new": "`transform-origin:left top` plus rotate turns about a different point so stored center x misses.",
        "not": "Not r314 rotate property, not r311 transform-box:fill-box.",
        "teach": "Origin changes the used box. Keep the card ref.",
        "next": "perspective-origin.",
    },
    {
        "prefix": "porig", "aux": "pso", "ok_place": "herposiphoniacot", "bad_place": "amansiafen",
        "widget": "perspective-origin", "err_slug": "pso-404", "code": 404, "err": "perspective_origin",
        "css": "perspective-origin", "from": "50% 50%", "to": "0% 0%", "js": "perspectiveOrigin",
        "item": "CD-2", "neigh": "CD-3", "fail_item": "CD-3", "ref": "c2", "nref": "c3", "fref": "c3",
        "x0": 140, "x1": 110, "y": 90, "btn": "Origin 0 0", "title": "Cards", "verb": "Keep",
        "path": "cards", "keep": "HP", "note": "CD-2 herposiphonia",
        "seed_ok": "css-perspective-origin-00", "seed_bad": "css-perspective-origin-404",
        "new": "`perspective-origin:0% 0%` foreshortens from a corner so stored center x is CD-3.",
        "not": "Not r333 perspective:200px, not r334 preserve-3d.",
        "teach": "Perspective origin is live. Keep CD-2 by ref.",
        "next": "grid-template-rows.",
    },
    {
        "prefix": "gtrws", "aux": "gtr", "ok_place": "vidaliabar", "bad_place": "osmundariaholt",
        "widget": "grid-template-rows", "err_slug": "gtr-410", "code": 410, "err": "grid_template_rows",
        "css": "grid-template-rows", "from": "auto auto", "to": "80px 80px", "js": "gridTemplateRows",
        "item": "RW-2", "neigh": "RW-3", "fail_item": "RW-3", "ref": "c2", "nref": "c3", "fref": "c3",
        "x0": 24, "x1": 24, "y": 64, "btn": "Rows 80", "title": "Rows", "verb": "Keep",
        "path": "rows", "keep": "VD", "note": "RW-2 vidalia",
        "seed_ok": "css-grid-template-rows-80", "seed_bad": "css-grid-template-rows-410",
        "new": "`grid-template-rows:80px 80px` restacks so stored auto y is RW-3.",
        "not": "Not r368 grid-template-areas, not r369 minmax columns.",
        "teach": "Template rows are live. Keep RW-2 by ref.",
        "next": "grid-auto-rows.",
    },
    {
        "prefix": "gatrw", "aux": "gar", "ok_place": "lenormandiacot", "bad_place": "martensiafen",
        "widget": "grid-auto-rows", "err_slug": "gar-410", "code": 410, "err": "grid_auto_rows",
        "css": "grid-auto-rows", "from": "auto", "to": "64px", "js": "gridAutoRows",
        "item": "RW-6", "neigh": "RW-7", "fail_item": "RW-7", "ref": "c6", "nref": "c7", "fref": "c7",
        "x0": 24, "x1": 24, "y": 200, "btn": "Auto rows 64", "title": "Rows", "verb": "Keep",
        "path": "rows", "keep": "LN", "note": "RW-6 lenormandia",
        "seed_ok": "css-grid-auto-rows-64", "seed_bad": "css-grid-auto-rows-410",
        "new": "`grid-auto-rows:64px` sizes implicit rows so stored auto y is RW-7.",
        "not": "Not r375 grid-auto-columns, not this mill's grid-template-rows.",
        "teach": "Implicit row size is live. Keep RW-6 by ref.",
        "next": "grid-row.",
    },
    {
        "prefix": "growa", "aux": "grw", "ok_place": "caloglossabar", "bad_place": "murrayellaholt",
        "widget": "grid-row-span", "err_slug": "grw-428", "code": 428, "err": "grid_row_span",
        "css": "grid-row", "from": "auto", "to": "1 / span 2", "js": "gridRow",
        "item": "CD-1", "neigh": "CD-2", "fail_item": "CD-2", "ref": "c1", "nref": "c2", "fref": "c2",
        "x0": 40, "x1": 40, "y": 120, "btn": "Span 2", "title": "Cards", "verb": "Keep",
        "path": "cards", "keep": "CG", "note": "CD-1 caloglossa",
        "seed_ok": "css-grid-row-span-2", "seed_bad": "css-grid-row-span-428",
        "new": "`grid-row:1 / span 2` covers the next row so stored CD-2 y is CD-1.",
        "not": "Not r368 grid-template-areas, not r353 height:stretch.",
        "teach": "A spanning item is still CD-1. Do not keep the covered cell.",
        "next": "animation-delay.",
    },
    {
        "prefix": "adely", "aux": "adl", "ok_place": "bostrychiacot", "bad_place": "stictosiphoniafen",
        "widget": "animation-delay", "err_slug": "adl-508", "code": 508, "err": "animation_delay",
        "css": "animation-delay", "from": "0s", "to": "0.4s", "js": "animationDelay",
        "item": "EN-6", "neigh": "EN-1", "fail_item": "EN-1", "ref": "c6", "nref": "c1", "fref": "c1",
        "x0": 40, "x1": 120, "y": 90, "btn": "Delay 400ms", "title": "Entries", "verb": "Keep",
        "path": "entries", "keep": "BO", "note": "EN-6 bostrychia",
        "seed_ok": "css-animation-delay-400", "seed_bad": "css-animation-delay-508",
        "new": "`animation-delay:0.4s` means a mid-delay x is still the from-state, not settled EN-6.",
        "not": "Not r223 animation-range entry, not r150 starting-style.",
        "teach": "Delay is not the end state. Wait or use the ref.",
        "next": "scroll-snap-type.",
    },
    {
        "prefix": "snpty", "aux": "snt", "ok_place": "cladophorabar", "bad_place": "chaetomorphaholt",
        "widget": "scroll-snap-type", "err_slug": "snt-425", "code": 425, "err": "snap_type",
        "css": "scroll-snap-type", "from": "none", "to": "x mandatory", "js": "scrollSnapType",
        "item": "LN-4", "neigh": "LN-5", "fail_item": "LN-6", "ref": "c4", "nref": "c5", "fref": "c6",
        "x0": 240, "x1": 40, "y": 24, "btn": "Snap x", "title": "Lanes", "verb": "Keep",
        "path": "lanes", "keep": "CL", "note": "LN-4 cladophora",
        "seed_ok": "css-scroll-snap-type-x-mandatory", "seed_bad": "css-scroll-snap-type-425",
        "new": "`scroll-snap-type:x mandatory` restacks a free scroll so stored none-x is LN-6.",
        "not": "Not r380 scroll-snap-align:end, not r245 snap-stop.",
        "teach": "Snap type is not align. Keep the snapped item ref.",
        "next": "overscroll-behavior-y.",
    },
    {
        "prefix": "osbhy", "aux": "osy", "ok_place": "rhizocloniumcot", "bad_place": "ulothrixfen",
        "widget": "overscroll-y", "err_slug": "osy-452", "code": 452, "err": "overscroll_y",
        "css": "overscroll-behavior-y", "from": "auto", "to": "none", "js": "overscrollBehaviorY",
        "item": "PG-2", "neigh": "parent", "fail_item": "parent", "ref": "c2", "nref": "p1", "fref": "p1",
        "x0": 12, "x1": 12, "y": 400, "btn": "Y none", "title": "Pages", "verb": "Keep",
        "path": "pages", "keep": "RZ", "note": "PG-2 rhizoclonium",
        "seed_ok": "css-overscroll-behavior-y-none", "seed_bad": "css-overscroll-behavior-y-452",
        "new": "`overscroll-behavior-y:none` drops chained parent pans. Stored auto y is the parent, not PG-2.",
        "not": "Not r381 touch-action:pan-y, not r295 overscroll-x none.",
        "teach": "Y overscroll is not X. Keep the inner page ref.",
        "next": "mask-clip.",
    },
    {
        "prefix": "mclip", "aux": "mcl", "ok_place": "spirogyrabar", "bad_place": "zygnemaholt",
        "widget": "mask-clip", "err_slug": "mcl-404", "code": 404, "err": "mask_clip",
        "css": "mask-clip", "from": "border-box", "to": "content-box", "js": "maskClip",
        "item": "SL-5", "neigh": "SL-6", "fail_item": "SL-6", "ref": "c5", "nref": "c6", "fref": "c6",
        "x0": 200, "x1": 200, "y": 100, "btn": "Clip content", "title": "Seals", "verb": "Keep",
        "path": "seals", "keep": "SP", "note": "SL-5 spirogyra",
        "seed_ok": "css-mask-clip-content-box", "seed_bad": "css-mask-clip-404",
        "new": "`mask-clip:content-box` makes padding a hole. Stored border-box center is empty.",
        "not": "Not r247 mask-mode:alpha, not r219 background-clip:text.",
        "teach": "Mask clip is not mode. Use the content-box ref, not padding x.",
        "next": "mask-origin.",
    },
    {
        "prefix": "morig", "aux": "mog", "ok_place": "mougeotiacot", "bad_place": "cosmariumfen",
        "widget": "mask-origin", "err_slug": "mog-404", "code": 404, "err": "mask_origin",
        "css": "mask-origin", "from": "border-box", "to": "content-box", "js": "maskOrigin",
        "item": "MK-2", "neigh": "MK-3", "fail_item": "MK-3", "ref": "c2", "nref": "c3", "fref": "c3",
        "x0": 180, "x1": 196, "y": 90, "btn": "Origin content", "title": "Masks", "verb": "Keep",
        "path": "masks", "keep": "MG", "note": "MK-2 mougeotia",
        "seed_ok": "css-mask-origin-content-box", "seed_bad": "css-mask-origin-404",
        "new": "`mask-origin:content-box` insets the lobe. Stored border-box x is a hole.",
        "not": "Not r037 mask-clip, not r359 mask-position.",
        "teach": "Mask origin is not position. Keep the remaining lobe ref.",
        "next": "mask-repeat.",
    },
    {
        "prefix": "mrept", "aux": "mrp", "ok_place": "closteriumbar", "bad_place": "micrasteriasholt",
        "widget": "mask-repeat", "err_slug": "mrp-404", "code": 404, "err": "mask_repeat",
        "css": "mask-repeat", "from": "no-repeat", "to": "repeat-x", "js": "maskRepeat",
        "item": "MK-2", "neigh": "tile", "fail_item": "tile", "ref": "c2", "nref": "t1", "fref": "t1",
        "x0": 80, "x1": 80, "y": 90, "btn": "Repeat x", "title": "Masks", "verb": "Keep",
        "path": "masks", "keep": "CS", "note": "MK-2 closterium",
        "seed_ok": "css-mask-repeat-x", "seed_bad": "css-mask-repeat-404",
        "new": "`mask-repeat:repeat-x` paints extra lobes. A tile is not MK-2.",
        "not": "Not r358 mask-size, not r359 mask-position.",
        "teach": "Repeated mask paint is not extra items. Keep MK-2 by ref.",
        "next": "background-size.",
    },
    {
        "prefix": "bgsiz", "aux": "bgs", "ok_place": "pediastrumcot", "bad_place": "scenedesmusfen",
        "widget": "background-size", "err_slug": "bgs-404", "code": 404, "err": "background_size",
        "css": "background-size", "from": "cover", "to": "40%", "js": "backgroundSize",
        "item": "BD-2", "neigh": "BD-3", "fail_item": "BD-3", "ref": "c2", "nref": "c3", "fref": "c3",
        "x0": 140, "x1": 140, "y": 80, "btn": "Size 40%", "title": "Badges", "verb": "Keep",
        "path": "badges", "keep": "PD", "note": "BD-2 pediastrum",
        "seed_ok": "css-background-size-40", "seed_bad": "css-background-size-404",
        "new": "`background-size:40%` shrinks the blob so stored cover-center is empty.",
        "not": "Not r356 background-attachment, not r357 background-origin.",
        "teach": "Background size is paint. Keep the badge ref.",
        "next": "background-repeat.",
    },
    {
        "prefix": "bgrpt", "aux": "bgr", "ok_place": "hydrodictyonbar", "bad_place": "volvoxholt",
        "widget": "background-repeat", "err_slug": "bgr-404", "code": 404, "err": "background_repeat",
        "css": "background-repeat", "from": "no-repeat", "to": "repeat-x", "js": "backgroundRepeat",
        "item": "BD-2", "neigh": "tile", "fail_item": "tile", "ref": "c2", "nref": "t1", "fref": "t1",
        "x0": 80, "x1": 80, "y": 80, "btn": "Repeat x", "title": "Badges", "verb": "Keep",
        "path": "badges", "keep": "HD", "note": "BD-2 hydrodictyon",
        "seed_ok": "css-background-repeat-x", "seed_bad": "css-background-repeat-404",
        "new": "`background-repeat:repeat-x` paints extra tiles. A tile is not BD-2.",
        "not": "Not this mill's background-size, not this mill's mask-repeat.",
        "teach": "Repeated background paint is not extra badges. Keep BD-2 by ref.",
        "next": "background-position.",
    },
    {
        "prefix": "bgpos", "aux": "bgp", "ok_place": "chlamydomonascot", "bad_place": "dunaliellafen",
        "widget": "background-position", "err_slug": "bgp-404", "code": 404, "err": "background_position",
        "css": "background-position", "from": "center", "to": "right top", "js": "backgroundPosition",
        "item": "BD-2", "neigh": "BD-3", "fail_item": "BD-3", "ref": "c2", "nref": "c3", "fref": "c3",
        "x0": 140, "x1": 200, "y": 80, "btn": "Pos right", "title": "Badges", "verb": "Keep",
        "path": "badges", "keep": "CM", "note": "BD-2 chlamydomonas",
        "seed_ok": "css-background-position-right-top", "seed_bad": "css-background-position-404",
        "new": "`background-position:right top` slides the blob. Stored center x is empty.",
        "not": "Not r320 object-position, not r357 background-origin.",
        "teach": "Background position is paint. Keep the badge ref.",
        "next": "filter grayscale.",
    },
    {
        "prefix": "gryfl", "aux": "gry", "ok_place": "haematococcusbar", "bad_place": "chlorellaholt",
        "widget": "filter-grayscale", "err_slug": "gry-415", "code": 415, "err": "filter_gray",
        "css": "filter", "from": "none", "to": "grayscale(1)", "js": "filter",
        "item": "OPEN", "neigh": "FILE", "fail_item": "FILE", "ref": "c1", "nref": "c2", "fref": "c2",
        "x0": 110, "x1": 110, "y": 70, "btn": "Grayscale", "title": "Verbs", "verb": "File",
        "path": "verbs", "keep": "HA", "note": "OPEN haematococcus",
        "seed_ok": "css-filter-grayscale-ocr", "seed_bad": "css-filter-grayscale-415",
        "new": "`filter:grayscale(1)` remaps luminance so OCR reads FILE, not OPEN.",
        "not": "Not r361 filter:blur, not r249 filter:url displace, not r317 drop-shadow.",
        "teach": "Grayscale screenshots are not the accessible name.",
        "next": "mix-blend-mode hue.",
    },
    {
        "prefix": "huebm", "aux": "hue", "ok_place": "tetraselmiscot", "bad_place": "nannochloropsisfen",
        "widget": "blend-hue", "err_slug": "hue-464", "code": 464, "err": "blend_hue",
        "css": "mix-blend-mode", "from": "normal", "to": "hue", "js": "mixBlendMode",
        "item": "SW-2", "neigh": "SW-3", "fail_item": "SW-3", "ref": "c2", "nref": "c3", "fref": "c3",
        "x0": 154, "x1": 154, "y": 88, "btn": "Hue blend", "title": "Blends", "verb": "Keep",
        "path": "blends", "keep": "TS", "note": "SW-2 tetraselmis",
        "seed_ok": "css-mix-blend-hue", "seed_bad": "css-mix-blend-hue-464",
        "new": "`mix-blend-mode:hue` steals chroma so the selected chip looks unselected.",
        "not": "Not r218 plus-lighter, not r178 multiply, not r355 difference.",
        "teach": "Hue blend is not unselected. Keep aria-selected / the ref.",
        "next": "box-shadow outset.",
    },
    {
        "prefix": "bxout", "aux": "bxo", "ok_place": "isochrysisbar", "bad_place": "pavlovaholt",
        "widget": "box-shadow-outset", "err_slug": "bxo-415", "code": 415, "err": "shadow_outset",
        "css": "box-shadow", "from": "none", "to": "12px 0 0 currentColor", "js": "boxShadow",
        "item": "OPEN", "neigh": "OPE N", "fail_item": "OPE", "ref": "c1", "nref": "c1", "fref": "c0",
        "x0": 80, "x1": 80, "y": 70, "btn": "Outset 12", "title": "Verbs", "verb": "File",
        "path": "verbs", "keep": "IS", "note": "OPEN isochrysis",
        "seed_ok": "css-box-shadow-outset-ghost", "seed_bad": "css-box-shadow-outset-415",
        "new": "`box-shadow:12px 0` ghosts a second box. Not r316 inset, not r252 text-shadow.",
        "not": "Not r316 inset box-shadow, not r252 text-shadow, not r317 drop-shadow.",
        "teach": "An outset shadow is not a second control. File the a11y name.",
        "next": "border-start-start-radius.",
    },
    {
        "prefix": "bssrd", "aux": "bss", "ok_place": "emilianiacot", "bad_place": "gephyrocapsafen",
        "widget": "start-start-radius", "err_slug": "bss-404", "code": 404, "err": "start_start_radius",
        "css": "border-start-start-radius", "from": "0px", "to": "24px", "js": "borderStartStartRadius",
        "item": "CH-2", "neigh": "hole", "fail_item": "hole", "ref": "c2", "nref": "h1", "fref": "h1",
        "x0": 16, "x1": 16, "y": 16, "btn": "Radius 24", "title": "Chips", "verb": "Keep",
        "path": "chips", "keep": "EM", "note": "CH-2 emiliania",
        "seed_ok": "css-border-start-start-radius-24", "seed_bad": "css-border-start-start-radius-404",
        "new": "`border-start-start-radius:24px` makes the logical corner a hole. Corner x is empty.",
        "not": "Not r175 corner-shape, not r360 clip-path ellipse.",
        "teach": "A radius hole is still the chip if you use the ref.",
        "next": "float inline-start.",
    },
    {
        "prefix": "fltin", "aux": "flt", "ok_place": "coccolithusbar", "bad_place": "thoracosphaeraholt",
        "widget": "float-inline-start", "err_slug": "flt-428", "code": 428, "err": "float_inline",
        "css": "float", "from": "none", "to": "inline-start", "js": "cssFloat",
        "item": "FL-2", "neigh": "FL-3", "fail_item": "FL-3", "ref": "c2", "nref": "c3", "fref": "c3",
        "x0": 200, "x1": 16, "y": 40, "btn": "Float start", "title": "Floats", "verb": "Keep",
        "path": "floats", "keep": "CC", "note": "FL-2 coccolithus",
        "seed_ok": "css-float-inline-start", "seed_bad": "css-float-inline-start-428",
        "new": "`float:inline-start` pulls the item so stored none x is empty.",
        "not": "Not r181 reading-flow, not r331 order.",
        "teach": "Logical float is live. Keep FL-2 by ref.",
        "next": "word-break break-all.",
    },
    {
        "prefix": "brkal", "aux": "bal", "ok_place": "prochlorococcuscot", "bad_place": "synechococcusfen",
        "widget": "break-all", "err_slug": "bal-400", "code": 400, "err": "break_all",
        "css": "word-break", "from": "normal", "to": "break-all", "js": "wordBreak",
        "item": "TOKEN", "neigh": "TOK", "fail_item": "TOK", "ref": "c1", "nref": "c1", "fref": "c0",
        "x0": 20, "x1": 20, "y": 44, "btn": "Break all", "title": "Tokens", "verb": "File",
        "path": "tokens", "keep": "PR", "note": "TOKEN prochlorococcus",
        "seed_ok": "css-word-break-break-all", "seed_bad": "css-word-break-break-all-400",
        "new": "`word-break:break-all` splits TOKEN so the first line is TOK. OCR is not the value.",
        "not": "Not r344 word-break:keep-all, not r386 word-break:auto-phrase, not r235 line-break:anywhere.",
        "teach": "break-all fragments are not the token. File the a11y string.",
        "next": "shape-image-threshold.",
    },
    {
        "prefix": "shthr", "aux": "sit", "ok_place": "trichodesmiumcot", "bad_place": "nostocfen",
        "widget": "shape-image-threshold", "err_slug": "sit-404", "code": 404, "err": "shape_threshold",
        "css": "shape-image-threshold", "from": "0", "to": "0.8", "js": "shapeImageThreshold",
        "item": "LN-3", "neigh": "LN-4", "fail_item": "LN-4", "ref": "c3", "nref": "c4", "fref": "c4",
        "x0": 160, "x1": 188, "y": 64, "btn": "Threshold 0.8", "title": "Lines", "verb": "Keep",
        "path": "lines", "keep": "TR", "note": "LN-3 trichodesmium",
        "seed_ok": "css-shape-image-threshold-08", "seed_bad": "css-shape-image-threshold-404",
        "new": "`shape-image-threshold:0.8` grows the exclusion so stored wrap x is LN-4.",
        "not": "Not r174 shape-outside, not r319 shape-margin.",
        "teach": "Threshold is not margin. Keep LN-3 by ref.",
        "next": "hyphenate-limit-lines.",
    },
    {
        "prefix": "hylns", "aux": "hln", "ok_place": "anabaenabar", "bad_place": "oscillatoriaholt",
        "widget": "hyphenate-limit-lines", "err_slug": "hln-414", "code": 414, "err": "limit_lines",
        "css": "hyphenate-limit-lines", "from": "no-limit", "to": "1", "js": "hyphenateLimitLines",
        "item": "COMPLETE", "neigh": "COM-", "fail_item": "COM", "ref": "c1", "nref": "c1", "fref": "c0",
        "x0": 28, "x1": 28, "y": 50, "btn": "Limit 1 line", "title": "Labels", "verb": "File",
        "path": "labels", "keep": "AN", "note": "COMPLETE anabaena",
        "seed_ok": "css-hyphenate-limit-lines-1", "seed_bad": "css-hyphenate-limit-lines-414",
        "new": "`hyphenate-limit-lines:1` forbids stacked hyphens so the box reflows vs no-limit OCR COM-.",
        "not": "Not r189 hyphenate-limit-chars, not r229 hyphenate-limit-last, not r233 hyphenate-limit-zone.",
        "teach": "Line limits are not the accessible name. File COMPLETE.",
        "next": "text-align end.",
    },
    {
        "prefix": "talen", "aux": "tae", "ok_place": "spirulinacot", "bad_place": "lyngbyafen",
        "widget": "text-align-end", "err_slug": "tae-412", "code": 412, "err": "align_end",
        "css": "text-align", "from": "start", "to": "end", "js": "textAlign",
        "item": "WD-2", "neigh": "WD-3", "fail_item": "WD-3", "ref": "c2", "nref": "c3", "fref": "c3",
        "x0": 24, "x1": 180, "y": 60, "btn": "Align end", "title": "Words", "verb": "Keep",
        "path": "words", "keep": "SR", "note": "WD-2 spirulina",
        "seed_ok": "css-text-align-end-shift", "seed_bad": "css-text-align-end-412",
        "new": "`text-align:end` slides the run so stored start x is empty.",
        "not": "Not r325 text-align-last:justify, not r366 justify-content space-evenly.",
        "teach": "text-align is live. Keep WD-2 by ref.",
        "next": "vertical-align middle.",
    },
    {
        "prefix": "valmd", "aux": "vmd", "ok_place": "microcystisbar", "bad_place": "aphanizomenonholt",
        "widget": "vertical-align-middle", "err_slug": "vmd-416", "code": 416, "err": "align_middle",
        "css": "vertical-align", "from": "baseline", "to": "middle", "js": "verticalAlign",
        "item": "CH-2", "neigh": "File", "fail_item": "File", "ref": "c2", "nref": "e5", "fref": "e5",
        "x0": 96, "x1": 96, "y": 88, "btn": "Middle", "title": "Chips", "verb": "File",
        "path": "chips", "keep": "MC", "note": "CH-2 microcystis",
        "seed_ok": "css-vertical-align-middle", "seed_bad": "css-vertical-align-middle-416",
        "new": "`vertical-align:middle` (not super) shifts the used box onto File.",
        "not": "Not r342 vertical-align:super, not r339 font-variant-position:super.",
        "teach": "Middle align is a used box. File is still the button ref.",
        "next": "user-select none.",
    },
    {
        "prefix": "usnon", "aux": "usn", "ok_place": "gloeocapscot", "bad_place": "merismopediafen",
        "widget": "user-select-none", "err_slug": "usn-419", "code": 419, "err": "select_none",
        "css": "user-select", "from": "auto", "to": "none", "js": "userSelect",
        "item": "NT-5", "neigh": "NT-6", "fail_item": "NT-6", "ref": "c5", "nref": "c6", "fref": "c6",
        "x0": 160, "x1": 160, "y": 80, "btn": "Select none", "title": "Notes", "verb": "Keep",
        "path": "notes", "keep": "GL", "note": "NT-5 gloeocapsa",
        "seed_ok": "css-user-select-none", "seed_bad": "css-user-select-none-419",
        "new": "`user-select:none` kills the highlight. A drag-select is not NT-6 and not a value.",
        "not": "Not r231 user-select:contain, not r190 ::highlight(search).",
        "teach": "none is not contain. Keep the article ref, not a missing highlight.",
        "next": "resize horizontal.",
    },
    {
        "prefix": "rszhx", "aux": "rzh", "ok_place": "rivulariabar", "bad_place": "calothrixholt",
        "widget": "resize-horizontal", "err_slug": "rzh-422", "code": 422, "err": "resize_horizontal",
        "css": "resize", "from": "none", "to": "horizontal", "js": "resize",
        "item": "NT-2", "neigh": "NT-3", "fail_item": "NT-3", "ref": "c2", "nref": "c3", "fref": "c3",
        "x0": 160, "x1": 220, "y": 80, "btn": "Resize x", "title": "Notes", "verb": "Keep",
        "path": "notes", "keep": "RV", "note": "NT-2 rivularia",
        "seed_ok": "css-resize-horizontal", "seed_bad": "css-resize-horizontal-422",
        "new": "`resize:horizontal` lets the note grow on x only so stored x is NT-3 after a drag.",
        "not": "Not r393 resize:both, not r370 clamp() width.",
        "teach": "A horizontal resize is live. Keep NT-2 by ref, not the handle.",
        "next": "contain size.",
    },
    {
        "prefix": "cnsiz", "aux": "csz", "ok_place": "scytonemacot", "bad_place": "stigonemafen",
        "widget": "contain-size", "err_slug": "csz-428", "code": 428, "err": "contain_size",
        "css": "contain", "from": "none", "to": "size", "js": "contain",
        "item": "CH-2", "neigh": "CH-3", "fail_item": "CH-3", "ref": "c2", "nref": "c3", "fref": "c3",
        "x0": 180, "x1": 120, "y": 70, "btn": "Contain size", "title": "Chips", "verb": "Keep",
        "path": "chips", "keep": "SY", "note": "CH-2 scytonema",
        "seed_ok": "css-contain-size-reflow", "seed_bad": "css-contain-size-428",
        "new": "`contain:size` sizes from specified width/height ignoring children so stored uncontained x is CH-3.",
        "not": "Not r387 contain:inline-size, not r136 contain:strict.",
        "teach": "size containment is live metrics. Keep CH-2 by ref.",
        "next": "contain paint.",
    },
    {
        "prefix": "cnpnt", "aux": "cpt", "ok_place": "fischerellabar", "bad_place": "hapalosiphonholt",
        "widget": "contain-paint", "err_slug": "cpt-404", "code": 404, "err": "contain_paint",
        "css": "contain", "from": "none", "to": "paint", "js": "contain",
        "item": "CH-6", "neigh": "CH-7", "fail_item": "CH-7", "ref": "c6", "nref": "c7", "fref": "c7",
        "x0": 200, "x1": 200, "y": 96, "btn": "Contain paint", "title": "Chips", "verb": "Keep",
        "path": "chips", "keep": "FS", "note": "CH-6 fischerella",
        "seed_ok": "css-contain-paint-clip", "seed_bad": "css-contain-paint-404",
        "new": "`contain:paint` clips overflowing paint. Stored visible overflow x is empty.",
        "not": "Not r387 contain:inline-size, not this mill's contain:size, not r378 overflow-x:clip.",
        "teach": "Paint containment is not size. Keep the clipped chip ref.",
        "next": "content-visibility hidden.",
    },
    {
        "prefix": "cvhid", "aux": "cvh", "ok_place": "westiellacot", "bad_place": "tolypothrixfen",
        "widget": "content-visibility-hidden", "err_slug": "cvh-410", "code": 410, "err": "cv_hidden",
        "css": "content-visibility", "from": "visible", "to": "hidden", "js": "contentVisibility",
        "item": "RW-12", "neigh": "RW-13", "fail_item": "RW-1", "ref": "c12", "nref": "c13", "fref": "c1",
        "x0": 0, "x1": 0, "y": 480, "btn": "Hide content", "title": "Rows", "verb": "Keep",
        "path": "rows", "keep": "WE", "note": "RW-12 westiella",
        "seed_ok": "css-content-visibility-hidden", "seed_bad": "css-content-visibility-hidden-410",
        "new": "`content-visibility:hidden` skips render so stale scrollY lands in an empty slot (r251 was auto).",
        "not": "Not r251 content-visibility:auto, not r335 contain-intrinsic-block-size.",
        "teach": "hidden is not auto virtualize. Re-find the row ref or stop.",
        "next": "position-anchor.",
    },
    {
        "prefix": "posan", "aux": "pan", "ok_place": "cylindrospermumbar", "bad_place": "nodulariaholt",
        "widget": "position-anchor", "err_slug": "pan-507", "code": 507, "err": "position_anchor",
        "css": "position-anchor", "from": "auto", "to": "--chip", "js": "positionAnchor",
        "item": "FL-1", "neigh": "File", "fail_item": "gone", "ref": "c1", "nref": "e5", "fref": "c0",
        "x0": 220, "x1": 80, "y": 40, "btn": "Anchor chip", "title": "Floats", "verb": "File",
        "path": "floats", "keep": "CY", "note": "FL-1 cylindrospermum",
        "seed_ok": "css-position-anchor-named", "seed_bad": "css-position-anchor-507",
        "new": "`position-anchor:--chip` retargets the abspos so stored auto-anchor x is File.",
        "not": "Not r125 position-try flip, not r167 anchor-size, not r197 position-visibility.",
        "teach": "Named anchors are live. Re-find the invoker or use the ref.",
        "next": "math-depth.",
    },
    {
        "prefix": "mdep", "aux": "mdp", "ok_place": "aphanocapscot", "bad_place": "chroococcusfen",
        "widget": "math-depth", "err_slug": "mdp-418", "code": 418, "err": "math_depth",
        "css": "math-depth", "from": "auto", "to": "2", "js": "mathDepth",
        "item": "EQ-4", "neigh": "EQ-5", "fail_item": "EQ-5", "ref": "c4", "nref": "c5", "fref": "c5",
        "x0": 110, "x1": 92, "y": 88, "btn": "Depth 2", "title": "Equations", "verb": "File",
        "path": "equations", "keep": "AP", "note": "EQ-4 aphanocapsa",
        "seed_ok": "css-math-depth-2-shrink", "seed_bad": "css-math-depth-2-418",
        "new": "`math-depth:2` nested-script shrinks display math so stored auto x is EQ-5.",
        "not": "Not r383 math-style:compact, not r226 math-shift compact.",
        "teach": "math-depth is a used box. File EQ-4 by ref.",
        "next": "text-wrap-style stable.",
    },
    {
        "prefix": "twstb", "aux": "tws", "ok_place": "pleurocapscot", "bad_place": "dermocarpafen",
        "widget": "text-wrap-style", "err_slug": "tws-414", "code": 414, "err": "wrap_stable",
        "css": "text-wrap-style", "from": "auto", "to": "stable", "js": "textWrapStyle",
        "item": "BINDING-COMPLETE", "neigh": "BINDING…", "fail_item": "BIND", "ref": "c1", "nref": "c1", "fref": "c0",
        "x0": 24, "x1": 24, "y": 48, "btn": "Wrap stable", "title": "Labels", "verb": "File",
        "path": "labels", "keep": "PC", "note": "BINDING-COMPLETE pleurocapsa",
        "seed_ok": "css-text-wrap-style-stable", "seed_bad": "css-text-wrap-style-414",
        "new": "`text-wrap-style:stable` keeps prior breaks so a resize does not rebalance; OCR BIND… is stale auto wrap.",
        "not": "Not r141 text-wrap:balance, not r159 text-wrap:pretty.",
        "teach": "Stable wrap is not pretty/balance. File the a11y string.",
        "next": "catalog continue.",
    },
]

for _extra_name in (
    "brw-mill-r395-extra.py",
    "brw-mill-r395-extra2.py",
    "brw-mill-r395-extra3.py",
    "brw-mill-r395-extra4.py",
    "brw-mill-r395-extra5.py",
    "brw-mill-r395-extra6.py",
    "brw-mill-r395-extra7.py",
    "brw-mill-r395-extra8.py",
    "brw-mill-r395-extra9.py",
    "brw-mill-r395-extra10.py",
    "brw-mill-r395-extra11.py",
    "brw-mill-r395-extra12.py",
    "brw-mill-r395-extra13.py",
    "brw-mill-r395-extra14.py",
    "brw-mill-r395-extra15.py",
    "brw-mill-r395-extra16.py",
    "brw-mill-r395-extra17.py",
):
    _extra_path = HERE / _extra_name
    if _extra_path.exists():
        _espec = importlib.util.spec_from_file_location(_extra_name.replace("-", "_").replace(".", "_"), _extra_path)
        _extra = importlib.util.module_from_spec(_espec)
        assert _espec.loader is not None
        _espec.loader.exec_module(_extra)
        PAIRS.extend(_extra.EXTRA)


def _used_host_prefs() -> set[str]:
    prefs: set[str] = set()
    if _m.USED_HOSTS.exists():
        for h in _m.USED_HOSTS.read_text().split():
            prefs.add(h.split(".")[0])
    return prefs


def validate_catalog() -> None:
    """Internal uniqueness. Used host/place checks are per-round in build_round."""
    seen_w: set[str] = set()
    seen_pr: set[str] = set()
    seen_ax: set[str] = set()
    seen_pl: set[str] = set()
    seen_seed: set[str] = set()
    seen_slug: set[str] = set()
    errs: list[str] = []
    for i, spec in enumerate(PAIRS):
        rnd = CATALOG_FIRST + i
        for key in ("prefix", "aux", "ok_place", "bad_place", "widget", "err_slug"):
            if spec[key] != spec[key].lower() or " " in spec[key]:
                errs.append(f"r{rnd}: {key} must be lowercase token")
        if spec["prefix"] == spec["aux"] or spec["prefix"] == "api" or spec["aux"] == "api":
            errs.append(f"r{rnd}: prefix/aux/api collide")
        if spec["code"] == 409:
            errs.append(f"r{rnd}: code 409 banned")
        if spec["ok_place"] == spec["bad_place"]:
            errs.append(f"r{rnd}: places collide")
        for label, bag in (
            (spec["widget"], seen_w),
            (spec["prefix"], seen_pr),
            (spec["aux"], seen_ax),
            (spec["ok_place"], seen_pl),
            (spec["bad_place"], seen_pl),
            (spec["seed_ok"], seen_seed),
            (spec["seed_bad"], seen_seed),
            (spec["err_slug"], seen_slug),
        ):
            if label in bag:
                errs.append(f"r{rnd}: duplicate {label}")
            bag.add(label)
    if errs:
        raise SystemExit("catalog:\n" + "\n".join(errs[:40]) + (f"\n… +{len(errs)-40}" if len(errs) > 40 else ""))


def spec_for_round(rnd: int) -> dict:
    idx = rnd - CATALOG_FIRST
    if idx < 0 or idx >= len(PAIRS):
        raise SystemExit(f"no plant for r{rnd} (catalog {CATALOG_FIRST}+{len(PAIRS)})")
    return PAIRS[idx]


def build_round(rnd: int, spec: dict | None = None):
    spec = spec if spec is not None else spec_for_round(rnd)
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
            for h in re.findall(r"https://([a-z0-9.-]+\.example)", blob):
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


def append_used(eps: list[dict], spec: dict) -> None:
    Path("/tmp/brw-used").mkdir(parents=True, exist_ok=True)
    hosts: list[str] = []
    for ep in eps:
        hosts.extend(re.findall(r"https://([a-z0-9.-]+\.example)", json.dumps(ep)))
    with _m.USED_HOSTS.open("a") as handle:
        for h in sorted(set(hosts)):
            handle.write(h + "\n")
    with _m.USED_PLACES.open("a") as handle:
        handle.write(spec["ok_place"] + "\n")
        handle.write(spec["bad_place"] + "\n")
    seeds_path = Path("/tmp/brw-used/seeds.txt")
    with seeds_path.open("a") as handle:
        handle.write(spec["seed_ok"] + "\n")
        handle.write(spec["seed_bad"] + "\n")
    ids_path = Path("/tmp/brw-used/ids.txt")
    with ids_path.open("a") as handle:
        for ep in eps:
            handle.write(ep["id"] + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    validate_catalog()
    eps, notes = build_round(args.round)
    _m.write_stage(args.out, args.round, eps, notes)
    print(json.dumps({"round": args.round, "ids": [e["id"] for e in eps], "bytes": sum(len(json.dumps(e)) for e in eps)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
