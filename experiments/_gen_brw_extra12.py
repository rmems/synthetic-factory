#!/usr/bin/env python3
"""Generate leftover CSS extra12 plants r1180+."""
from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
_ns: dict = {"__file__": str(HERE / "_gen_brw_extra10.py")}
_src = (HERE / "_gen_brw_extra10.py").read_text()
exec(_src.split("# css, from, to, js, widget")[0], _ns)
T = _ns["T"]
KEYS = _ns["KEYS"]
SETS = _ns["SETS"]


def load_set(name: str) -> set[str]:
    return {ln.strip() for ln in (SETS / f"{name}.txt").read_text().splitlines() if ln.strip()}


def mint(base: str, used: set[str], n: int = 4) -> str:
    cand = "".join(ch for ch in base.lower() if ch.isalnum())[:n]
    if len(cand) < 3:
        cand = (cand + "x" * 3)[:n]
    if cand not in used and cand != "api":
        used.add(cand)
        return cand
    for i in range(2, 80):
        suffix = str(i)
        body = cand[: max(1, n - len(suffix))] + suffix
        if body not in used and body != "api":
            used.add(body)
            return body
    raise SystemExit(f"cannot mint {base}")


def keep_code(genus: str, used: set[str]) -> str:
    letters = "".join(ch for ch in genus if ch.isalpha())
    base = (letters[:1] + letters[-1:]).upper()
    if len(base) < 2:
        base = (letters[:2] or "XX").upper()
    if base not in used:
        used.add(base)
        return base
    for a in letters.upper():
        for b in letters.upper()[::-1]:
            tok = a + b
            if tok not in used:
                used.add(tok)
                return tok
    for a in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        for b in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            tok = a + b
            if tok not in used:
                used.add(tok)
                return tok
    raise SystemExit(f"keep {genus}")


# css, from, to, js, widget, err, code, tmpl, btn, new, not, teach
PLANTS = [
    ("font-size", "16px", "11px", "fontSize", "font-size-11", "font_size_11", 412, "glyphs", "Size 11",
     "`font-size:11px` shrinks glyphs so stored 16px x is GL-3.", "Not extra11 font-size-14, not extra10 font-size-10.", "11px is live. Keep GL-2 by ref."),
    ("font-size", "16px", "13px", "fontSize", "font-size-13", "font_size_13", 412, "glyphs", "Size 13",
     "`font-size:13px` shrinks glyphs so stored 16px x is GL-3.", "Not extra12 font-size-11, not extra11 font-size-14.", "13px is not 14. Keep GL-2 by ref."),
    ("font-size", "16px", "15px", "fontSize", "font-size-15", "font_size_15", 412, "glyphs", "Size 15",
     "`font-size:15px` shrinks glyphs so stored 16px x is GL-3.", "Not extra11 font-size-14, not extra10 font-size-18.", "15px is not 14. Keep GL-2 by ref."),
    ("font-size", "16px", "22px", "fontSize", "font-size-22", "font_size_22", 412, "glyphs", "Size 22",
     "`font-size:22px` grows glyphs so stored 16px x is GL-3.", "Not extra8 font-size-24, not extra11 font-size-20.", "22px is not 24. Keep GL-2 by ref."),
    ("font-size", "16px", "28px", "fontSize", "font-size-28", "font_size_28", 412, "glyphs", "Size 28",
     "`font-size:28px` grows glyphs so stored 16px x is GL-3.", "Not extra9 font-size-32, not extra11 font-size-36.", "28px is not 32. Keep GL-2 by ref."),
    ("font-size", "16px", "40px", "fontSize", "font-size-40", "font_size_40", 412, "glyphs", "Size 40",
     "`font-size:40px` grows glyphs so stored 16px x is GL-3.", "Not extra10 font-size-48, not extra11 font-size-36.", "40px is not 48. Keep GL-2 by ref."),
    ("font-size", "16px", "64px", "fontSize", "font-size-64", "font_size_64", 412, "glyphs", "Size 64",
     "`font-size:64px` grows glyphs so stored 16px x is GL-3.", "Not extra12 font-size-40, not extra10 font-size-48.", "64px is not 48. Keep GL-2 by ref."),
    ("zoom", "1", "0.33", "zoom", "zoom-033", "zoom_033", 412, "cards", "Zoom 0.33",
     "`zoom:0.33` shrinks the used box so stored unzoomed x is CD-4.", "Not extra10 zoom-025, not extra11 zoom-075.", "CSS zoom 0.33 is not scale(). Keep CD-3 by ref."),
    ("zoom", "1", "0.6", "zoom", "zoom-06", "zoom_06", 412, "cards", "Zoom 0.6",
     "`zoom:0.6` shrinks the used box so stored unzoomed x is CD-4.", "Not extra9 zoom-05, not extra11 zoom-075.", "CSS zoom 0.6 is not 0.5. Keep CD-3 by ref."),
    ("zoom", "1", "0.9", "zoom", "zoom-09", "zoom_09", 412, "cards", "Zoom 0.9",
     "`zoom:0.9` shrinks the used box so stored unzoomed x is CD-4.", "Not extra8 zoom-08, not extra12 zoom-06.", "CSS zoom 0.9 is not 0.8. Keep CD-3 by ref."),
    ("zoom", "1", "1.1", "zoom", "zoom-11", "zoom_11", 412, "cards", "Zoom 1.1",
     "`zoom:1.1` grows the used box so stored unzoomed x is CD-4.", "Not extra8 zoom-15, not extra5 zoom-125.", "CSS zoom 1.1 is not 1.25. Keep CD-3 by ref."),
    ("zoom", "1", "5", "zoom", "zoom-5", "zoom_5", 412, "cards", "Zoom 5",
     "`zoom:5` grows the used box so stored unzoomed x is CD-4.", "Not extra11 zoom-4, not extra10 zoom-3.", "CSS zoom 5 is not 4. Keep CD-3 by ref."),
    ("opacity", "1", "0.3", "opacity", "opacity-03", "opacity_03", 464, "blends", "Opacity 0.3",
     "`opacity:0.3` fades so a screenshot looks unselected.", "Not extra10 opacity-04, not extra7 opacity-02.", "0.3 is not unselected. Keep aria-selected / the ref."),
    ("opacity", "1", "0.7", "opacity", "opacity-07", "opacity_07", 464, "blends", "Opacity 0.7",
     "`opacity:0.7` fades so a screenshot looks unselected.", "Not extra11 opacity-06, not extra9 opacity-08.", "0.7 is not unselected. Keep aria-selected / the ref."),
    ("opacity", "1", "0.9", "opacity", "opacity-09", "opacity_09", 464, "blends", "Opacity 0.9",
     "`opacity:0.9` fades so a screenshot looks unselected.", "Not extra12 opacity-07, not extra9 opacity-08.", "0.9 is not unselected. Keep aria-selected / the ref."),
    ("scale", "1", "0.33", "scale", "scale-033", "scale_033", 412, "cards", "Scale 0.33",
     "`scale:0.33` shrinks so stored unscaled x is CD-4.", "Not extra11 scale-025, not extra10 scale-05.", "Uniform 0.33 scale is live. Keep CD-3 by ref."),
    ("scale", "1", "0.6", "scale", "scale-06", "scale_06", 412, "cards", "Scale 0.6",
     "`scale:0.6` shrinks so stored unscaled x is CD-4.", "Not extra10 scale-05, not extra12 scale-033.", "Uniform 0.6 scale is live. Keep CD-3 by ref."),
    ("scale", "1", "0.75", "scale", "scale-075", "scale_075", 412, "cards", "Scale 0.75",
     "`scale:0.75` shrinks so stored unscaled x is CD-4.", "Not extra8 scale-08 mill, not extra12 scale-06.", "Uniform 0.75 scale is live. Keep CD-3 by ref."),
    ("scale", "1", "4", "scale", "scale-4", "scale_4", 412, "cards", "Scale 4",
     "`scale:4` grows so stored unscaled x is CD-4.", "Not extra11 scale-3, not extra9 scale-2.", "Uniform scale 4 is live. Keep CD-3 by ref."),
    ("rotate", "0deg", "x 45deg", "rotate", "rotate-x-45", "rotate_x_45", 520, "cards", "Rotate X 45",
     "`rotate:x 45deg` shears the hit diamond so stored 0deg x misses.", "Not extra10 rotate-x-15, not extra8 rotate-y-40.", "X-rotate 45 is not 15. Keep CD-3 by ref."),
    ("rotate", "0deg", "y 15deg", "rotate", "rotate-y-15", "rotate_y_15", 520, "cards", "Rotate Y 15",
     "`rotate:y 15deg` shears the hit diamond so stored 0deg x misses.", "Not extra8 rotate-y-40, not extra12 rotate-x-45.", "Y-rotate 15 is not 40. Keep CD-3 by ref."),
    ("rotate", "0deg", "z 8deg", "rotate", "rotate-z-8", "rotate_z_8", 520, "cards", "Rotate Z 8",
     "`rotate:z 8deg` shears the hit diamond so stored 0deg x misses.", "Not extra11 rotate-z-15, not extra9 rotate-z-40.", "Z-rotate 8 is not 15. Keep CD-3 by ref."),
    ("translate", "0px", "8px 0px", "translate", "translate-x-8", "translate_x_8", 412, "abspos", "Translate 8",
     "`translate:8px 0` slides so stored 0 x is empty.", "Not extra11 translate-x-24, not extra8 translate-x-40.", "X translate 8 is live. Keep AB-2 by ref."),
    ("translate", "0px", "0px 8px", "translate", "translate-y-8", "translate_y_8", 410, "abspos", "Translate y 8",
     "`translate:0 8px` slides block so stored 0 y is empty.", "Not extra9 translate-y-40, not extra12 translate-x-8.", "Y translate 8 is live. Keep AB-2 by ref."),
    ("translate", "0px", "0px 0px 8px", "translate", "translate-z-8", "translate_z_8", 520, "cards", "Translate z 8",
     "`translate:0 0 8px` lifts on z so stored 0 x misses under perspective.", "Not extra10 translate-z-20, not extra12 translate-x-8.", "Z translate 8 is live. Keep CD-3 by ref."),
    ("cursor", "auto", "wait", "cursor", "cursor-wait-x12", "cursor_wait_x12", 404, "chips", "Wait",
     "`cursor:wait` paints a spinner glyph over CH-2. Screenshot of the glyph is not CH-3.", "Not extra9 cursor-wait, not extra11 cursor-pointer.", "The wait cursor is paint. Keep the chip ref."),
    ("cursor", "auto", "help", "cursor", "cursor-help-x12", "cursor_help_x12", 404, "chips", "Help",
     "`cursor:help` paints a question glyph over CH-2. Screenshot of the glyph is not CH-3.", "Not extra9 cursor-help, not extra11 cursor-text.", "The help cursor is paint. Keep the chip ref."),
    ("cursor", "auto", "move", "cursor", "cursor-move-x12", "cursor_move_x12", 404, "chips", "Move",
     "`cursor:move` paints a four-arrow glyph over CH-2. Screenshot of the glyph is not CH-3.", "Not extra9 cursor-move, not extra11 cursor-default.", "The move cursor is paint. Keep the chip ref."),
    ("cursor", "auto", "copy", "cursor", "cursor-copy-x12", "cursor_copy_x12", 404, "chips", "Copy",
     "`cursor:copy` paints a plus-copy glyph over CH-2. Screenshot of the glyph is not CH-3.", "Not extra10 cursor-copy, not extra11 cursor-pointer.", "The copy cursor is paint. Keep the chip ref."),
    ("cursor", "auto", "grab", "cursor", "cursor-grab-x12", "cursor_grab_x12", 404, "chips", "Grab",
     "`cursor:grab` paints an open-hand glyph over CH-2. Screenshot of the glyph is not CH-3.", "Not extra8 cursor-grab, not extra11 cursor-pointer.", "The grab cursor is paint. Keep the chip ref."),
    ("cursor", "auto", "none", "cursor", "cursor-none-x12", "cursor_none_x12", 404, "chips", "None",
     "`cursor:none` unpaints the pointer. Screenshot of a missing glyph is not CH-3.", "Not r cursor-none mill, not extra7 cursor-not-allowed.", "A missing cursor is paint. Keep the chip ref."),
    ("cursor", "auto", "crosshair", "cursor", "cursor-crosshair-x12", "cursor_crosshair_x12", 404, "chips", "Crosshair",
     "`cursor:crosshair` paints a plus over CH-2. Screenshot of the glyph is not CH-3.", "Not extra9 cursor-crosshair, not extra11 cursor-default.", "The crosshair is paint. Keep the chip ref."),
    ("cursor", "auto", "cell", "cursor", "cursor-cell-x12", "cursor_cell_x12", 404, "chips", "Cell",
     "`cursor:cell` paints a cell glyph over CH-2. Screenshot of the glyph is not CH-3.", "Not extra10 cursor-cell, not extra11 cursor-text.", "The cell cursor is paint. Keep the chip ref."),
    ("cursor", "auto", "not-allowed", "cursor", "cursor-not-allowed-x12", "cursor_not_allowed_x12", 404, "chips", "Not-allowed",
     "`cursor:not-allowed` paints a banned glyph over CH-2. Screenshot of the glyph is not CH-3.", "Not extra7 cursor-not-allowed, not extra10 cursor-no-drop.", "The banned cursor is paint. Keep the chip ref."),
    ("display", "block", "inline", "display", "display-inline-x12", "display_inline_x12", 412, "chips", "Inline",
     "`display:inline` shrink-wraps so stored block x is CH-3.", "Not extra9 display-inline, not extra11 display-inline-block-run.", "inline is live. Keep CH-2 by ref."),
    ("display", "block", "table", "display", "display-table-x12", "display_table_x12", 428, "chips", "Table",
     "`display:table` equalizes columns so stored block x is CH-3.", "Not extra6 display-table, not extra9 display-table-cell.", "table display is live. Keep CH-2 by ref."),
    ("display", "block", "none", "display", "display-none-x12", "display_none_x12", 410, "chiphole", "None",
     "`display:none` removes the box. Stored block x is a hole.", "Not extra8 display-none, not extra11 vis-collapse-run.", "none is still the chip if you use the ref."),
    ("overflow-x", "visible", "hidden", "overflowX", "overflow-x-hidden-x12", "overflow_x_hidden_x12", 425, "lanes", "Hidden x",
     "`overflow-x:hidden` clips without a scrollport so stored visible x is LN-6.", "Not extra11 overflow-x-clip-run, not extra7 overflow-x-auto.", "hidden-x is not clip. Keep the on-screen item ref."),
    ("overflow-y", "visible", "hidden", "overflowY", "overflow-y-hidden-x12", "overflow_y_hidden_x12", 425, "lanes", "Hidden y",
     "`overflow-y:hidden` clips without a scrollport so stored visible y is LN-6.", "Not extra11 overflow-y-clip-run, not extra8 overflow-y-auto.", "hidden-y is not clip. Keep the on-screen item ref."),
    ("overflow-x", "visible", "scroll", "overflowX", "overflow-x-scroll-x12", "overflow_x_scroll_x12", 425, "lanes", "Scroll x",
     "`overflow-x:scroll` creates an x scrollport so stored visible x is LN-6.", "Not extra7 overflow-x-auto, not extra12 overflow-x-hidden-x12.", "scroll-x is not auto. Keep the on-screen item ref."),
    ("overflow-y", "visible", "scroll", "overflowY", "overflow-y-scroll-x12", "overflow_y_scroll_x12", 425, "lanes", "Scroll y",
     "`overflow-y:scroll` creates a y scrollport so stored visible y is LN-6.", "Not extra8 overflow-y-auto, not extra12 overflow-y-hidden-x12.", "scroll-y is not auto. Keep the on-screen item ref."),
    ("letter-spacing", "normal", "0.1em", "letterSpacing", "letter-spacing-em-x12", "letter_spacing_em_x12", 412, "glyphs", "Tracking 0.1em",
     "`letter-spacing:0.1em` widens glyphs so stored normal x is GL-3.", "Not extra9 letter-spacing-em, not extra11 letter-spacing-0.", "0.1em tracking is live. Keep GL-2 by ref."),
    ("word-spacing", "normal", "0.2em", "wordSpacing", "word-spacing-em-x12", "word_spacing_em_x12", 412, "glyphs", "Word 0.2em",
     "`word-spacing:0.2em` widens word gaps so stored normal x is GL-3.", "Not extra9 word-spacing-em, not extra11 word-spacing-neg.", "0.2em word-spacing is live. Keep GL-2 by ref."),
    ("line-height", "normal", "1.25", "lineHeight", "line-height-125", "line_height_125", 410, "rows", "Line 1.25",
     "`line-height:1.25` packs rows so stored normal y is RW-3.", "Not extra10 line-height-15, not extra11 line-height-3.", "Unitless 1.25 is live. Keep RW-2 by ref."),
    ("line-height", "normal", "2.5", "lineHeight", "line-height-25", "line_height_25", 410, "rows", "Line 2.5",
     "`line-height:2.5` grows rows so stored normal y is RW-3.", "Not extra7 line-height-2, not extra11 line-height-3.", "Unitless 2.5 is live. Keep RW-2 by ref."),
    ("gap", "0px", "4px", "gap", "gap-4", "gap_4", 412, "chips", "Gap 4",
     "`gap:4px` restacks both axes so stored 0-gap x is CH-3.", "Not extra10 gap-8, not extra11 gap-16.", "gap 4 is not 8. Keep CH-2 by ref."),
    ("gap", "0px", "12px", "gap", "gap-12", "gap_12", 412, "chips", "Gap 12",
     "`gap:12px` restacks both axes so stored 0-gap x is CH-3.", "Not extra11 gap-16, not extra12 gap-4.", "gap 12 is not 16. Keep CH-2 by ref."),
    ("gap", "0px", "48px", "gap", "gap-48", "gap_48", 412, "chips", "Gap 48",
     "`gap:48px` restacks both axes so stored 0-gap x is CH-3.", "Not extra11 gap-32, not extra9 gap-24.", "gap 48 is not 32. Keep CH-2 by ref."),
    ("flex-grow", "0", "4", "flexGrow", "flex-grow-4", "flex_grow_4", 428, "chips", "Grow 4",
     "`flex-grow:4` eats free space so stored grow-0 x is CH-3.", "Not extra11 flex-grow-3, not extra9 flex-grow-2.", "grow 4 is not 3. Keep CH-2 by ref."),
    ("order", "0", "4", "order", "order-4", "order_4", 428, "chips", "Order 4",
     "`order:4` restacks the flex item so stored 0 x is CH-3.", "Not extra11 order-3, not extra9 order-2.", "flex order 4 is live. Keep CH-2 by ref."),
    ("column-count", "auto", "5", "columnCount", "column-count-5", "column_count_5", 416, "text", "Count 5",
     "`column-count:5` fragments so stored auto x is TX-5.", "Not extra11 column-count-4, not extra9 column-count-3.", "column-count 5 is not 4. Keep TX-2 by ref."),
    ("z-index", "auto", "4", "zIndex", "z-index-4", "z_index_4", 403, "chips", "Z 4",
     "`z-index:4` restacks so a click hits CH-3.", "Not extra11 z-index-2, not extra10 z-index-1.", "4 is not 2. Keep CH-2 by ref."),
    ("z-index", "auto", "10", "zIndex", "z-index-10", "z_index_10", 403, "chips", "Z 10",
     "`z-index:10` restacks so a click hits CH-3.", "Not extra9 z-index-999, not extra12 z-index-4.", "10 is not 999. Keep CH-2 by ref."),
    ("mix-blend-mode", "normal", "color-dodge", "mixBlendMode", "blend-color-dodge-run", "blend_color_dodge_run", 464, "blends", "Color-dodge",
     "`mix-blend-mode:color-dodge` blows the selected chip so a screenshot looks empty.", "Not r blend-color-dodge mill, not extra11 blend-screen-run.", "color-dodge is not empty. Keep aria-selected / the ref."),
    ("mix-blend-mode", "normal", "color-burn", "mixBlendMode", "blend-color-burn-run", "blend_color_burn_run", 464, "blends", "Color-burn",
     "`mix-blend-mode:color-burn` darkens so the selected chip looks empty.", "Not extra6 blend-color-burn, not extra10 blend-darken-run.", "color-burn is not empty. Keep aria-selected / the ref."),
    ("mix-blend-mode", "normal", "hard-light", "mixBlendMode", "blend-hard-light-run", "blend_hard_light_run", 464, "blends", "Hard-light",
     "`mix-blend-mode:hard-light` remaps so the selected chip looks empty.", "Not r blend-hard-light mill, not extra11 blend-overlay-run.", "hard-light is not empty. Keep aria-selected / the ref."),
    ("mix-blend-mode", "normal", "soft-light", "mixBlendMode", "blend-soft-light-run", "blend_soft_light_run", 464, "blends", "Soft-light",
     "`mix-blend-mode:soft-light` remaps so the selected chip looks empty.", "Not r blend-soft-light mill, not extra12 blend-hard-light-run.", "soft-light is not empty. Keep aria-selected / the ref."),
    ("backdrop-filter", "none", "blur(4px)", "backdropFilter", "backdrop-blur-x12", "backdrop_blur_x12", 415, "cards", "Backdrop blur 4",
     "`backdrop-filter:blur(4px)` grows the screenshot blob past the used box.", "Not extra6 backdrop-blur, not extra11 backdrop-contrast.", "Backdrop blur 4 is paint. Keep CD-3 by ref."),
    ("filter", "none", "invert(1)", "filter", "filter-invert-run", "filter_invert_run", 415, "cards", "Invert",
     "`filter:invert(1)` remaps paint so a screenshot blob is not CD-3.", "Not extra8 backdrop-invert, not extra5 filter-invert.", "Invert is paint. Keep CD-3 by ref."),
    ("filter", "none", "grayscale(1)", "filter", "filter-grayscale-run", "filter_grayscale_run", 415, "cards", "Grayscale",
     "`filter:grayscale(1)` remaps paint so a screenshot blob is not CD-3.", "Not extra5 filter-grayscale, not extra11 filter-saturate-0.", "Grayscale is paint. Keep CD-3 by ref."),
    ("filter", "none", "sepia(1)", "filter", "filter-sepia-run", "filter_sepia_run", 415, "cards", "Sepia",
     "`filter:sepia(1)` remaps paint so OCR / a screenshot blob is not CD-3.", "Not r641 filter-sepia, not extra9 backdrop-sepia.", "Sepia is paint. Keep CD-3 by ref."),
    ("filter", "none", "hue-rotate(90deg)", "filter", "filter-hue-90", "filter_hue_90", 415, "cards", "Hue 90",
     "`filter:hue-rotate(90deg)` remaps paint so a screenshot blob is not CD-3.", "Not extra5 filter-hue-rotate, not extra10 backdrop-hue.", "Hue 90 is paint. Keep CD-3 by ref."),
    ("text-align", "start", "right", "textAlign", "text-align-right-run", "text_align_right_run", 412, "text", "Align right",
     "`text-align:right` packs so stored start x is TX-5.", "Not extra11 text-align-left-run, not extra7 text-align-center.", "right is not left. Keep TX-2 by ref."),
    ("text-align", "start", "justify", "textAlign", "text-align-justify-run", "text_align_justify_run", 412, "text", "Justify",
     "`text-align:justify` stretches so stored start x is TX-5.", "Not r text-align-justify mill, not extra12 text-align-right-run.", "justify is not right. Keep TX-2 by ref."),
    ("white-space", "normal", "pre", "whiteSpace", "ws-pre-x12", "ws_pre_x12", 413, "labels", "Pre",
     "`white-space:pre` keeps spaces and forbids wrap so a normal wrap line is LB-3.", "Not extra9 ws-pre, not extra11 ws-nowrap-run.", "pre is not nowrap. File the a11y string."),
    ("hyphens", "auto", "none", "hyphens", "hyphens-none-x12", "hyphens_none_x12", 414, "bind", "None",
     "`hyphens:none` forbids hyphen breaks so OCR BIND… is a different wrap.", "Not extra11 hyphens-auto-run, not extra7 hyphens-off.", "none is not auto. File the a11y string."),
    ("visibility", "visible", "hidden", "visibility", "vis-hidden-x12", "vis_hidden_x12", 410, "chiphole", "Hidden",
     "`visibility:hidden` unpaints the chip. Stored visible x is a hole.", "Not extra7 vis-hidden-chip, not extra11 vis-collapse-run.", "Hidden is still the chip if you use the ref."),
    ("contain", "none", "size", "contain", "contain-size-run", "contain_size_run", 428, "chips", "Size",
     "`contain:size` sizes independently so stored none x is CH-3.", "Not extra10 contain-strict-run, not extra11 contain-paint-run.", "contain:size is live. Keep CH-2 by ref."),
    ("will-change", "auto", "transform", "willChange", "will-change-transform-x12", "will_change_transform_x12", 412, "cards", "Will transform",
     "`will-change:transform` promotes a layer so stored auto x is a different compositor box.", "Not extra8 will-change-transform, not extra11 will-change-contents-run.", "will-change:transform is live. Keep CD-3 by ref."),
    ("user-select", "auto", "all", "userSelect", "us-all-run", "us_all_run", 413, "labels", "All",
     "`user-select:all` selects the whole control so OCR of a spilled highlight is LB-3.", "Not extra11 us-none-run, not extra8 us-contain-select.", "all is not none. File the a11y string."),
    ("pointer-events", "auto", "none", "pointerEvents", "pe-none-x12", "pe_none_x12", 410, "chips", "None",
     "`pointer-events:none` lets the click fall through so stored auto x hits CH-3.", "Not extra8 pointer-events-none, not extra11 pe-visible-painted.", "none is not visiblePainted. Keep CH-2 by ref."),
    ("resize", "none", "both", "resize", "resize-both-x12", "resize_both_x12", 428, "cards", "Both",
     "`resize:both` grows the used box so stored none x is CD-4.", "Not extra8 resize-both-box, not extra11 resize-vertical-run.", "both is not vertical. Keep CD-3 by ref."),
    ("float", "none", "left", "float", "float-left-x12", "float_left_x12", 412, "floats", "Left",
     "`float:left` packs to the start so stored none x is FL-4.", "Not extra11 float-inline-start-run, not extra10 float-right-run.", "left is not inline-start. Keep FL-3 by ref."),
    ("clear", "none", "left", "clear", "clear-left-x12", "clear_left_x12", 410, "floats", "Clear left",
     "`clear:left` drops below a left float so stored none y is FL-4.", "Not extra9 clear-left, not extra11 clear-both-run.", "clear:left is live. Keep FL-3 by ref."),
    ("vertical-align", "baseline", "middle", "verticalAlign", "valign-middle-x12", "valign_middle_x12", 410, "glyphs", "Middle",
     "`vertical-align:middle` centers glyphs so stored baseline y is GL-3.", "Not r vertical-align-middle, not extra11 valign-text-bottom.", "middle is not text-bottom. Keep GL-2 by ref."),
    ("border-radius", "0px", "12px", "borderRadius", "radius-12", "radius_12", 404, "chiphole", "Radius 12",
     "`border-radius:12px` makes corner holes. Stored square x is empty.", "Not extra11 radius-8, not extra8 radius-full.", "A 12px radius hole is still the chip if you use the ref."),
    ("border-radius", "0px", "4px", "borderRadius", "radius-4", "radius_4", 404, "chiphole", "Radius 4",
     "`border-radius:4px` makes corner holes. Stored square x is empty.", "Not extra12 radius-12, not extra11 radius-8.", "A 4px radius hole is still the chip if you use the ref."),
    ("outline-offset", "0px", "8px", "outlineOffset", "outline-offset-8", "outline_offset_8", 404, "floats", "Offset 8",
     "`outline-offset:8px` pushes UA chrome out so a screenshot ring is not FL-3.", "Not extra11 outline-offset-4, not extra8 outline-offset-12.", "8px offset outline is paint. Keep the float ref."),
    ("border-width", "0px", "2px", "borderWidth", "border-width-2", "border_width_2", 404, "chips", "Width 2",
     "`border-width:2px` grows a ring. Center click on the ring is not CH-2.", "Not extra11 border-width-4, not extra8 border-width-8.", "A 2px border is paint. Keep the chip ref."),
    ("border-style", "none", "dashed", "borderStyle", "border-dashed-x12", "border_dashed_x12", 404, "chips", "Dashed",
     "`border-style:dashed` paints gaps. A click in a dash gap is not CH-2.", "Not extra8 border-dashed, not extra11 border-dotted.", "Dashes are paint. Keep the chip ref."),
    ("border-style", "none", "solid", "borderStyle", "border-solid-x12", "border_solid_x12", 404, "chips", "Solid",
     "`border-style:solid` paints a ring. Center click on the ring is not CH-2.", "Not extra8 border-sh-8, not extra12 border-dashed-x12.", "A solid border is paint. Keep the chip ref."),
    ("scroll-margin-right", "0px", "24px", "scrollMarginRight", "scroll-mar-right", "scroll_mar_right", 425, "lanes", "Margin right 24",
     "`scroll-margin-right:24px` pads snap so stored 0-margin x is LN-6.", "Not extra8 scroll-mar-left, not extra11 scroll-mar-top.", "Physical scroll-margin-right is live. Keep the on-screen item ref."),
    ("scroll-padding-bottom", "0px", "24px", "scrollPaddingBottom", "scroll-pad-bottom", "scroll_pad_bottom", 425, "lanes", "Pad bottom 24",
     "`scroll-padding-bottom:24px` insets the scrollport so stored 0-pad y is LN-6.", "Not extra8 scroll-pad-top, not extra11 scroll-pad-left.", "Physical scroll-padding-bottom is live. Keep the on-screen item ref."),
    ("mask-size", "auto", "80%", "maskSize", "mask-size-80", "mask_size_80", 404, "cardhole", "Mask 80",
     "`mask-size:80%` shrinks the mask. Stored auto x is a hole.", "Not extra11 mask-size-50, not extra10 mask-size-cover.", "An 80% mask hole is still the card ref."),
    ("clip-path", "none", "inset(4%)", "clipPath", "clip-path-inset-4", "clip_path_inset_4", 404, "cardhole", "Inset 4",
     "`clip-path:inset(4%)` cuts the card. Stored none x is a hole.", "Not extra10 clip-path-inset-8, not extra11 clip-path-circle-40.", "A 4% inset clip is still the card ref."),
    ("perspective", "none", "100px", "perspective", "perspective-100", "perspective_100", 520, "cards", "Persp 100",
     "`perspective:100px` foreshortens children so stored none x misses.", "Not extra9 perspective-200, not extra11 perspective-400.", "100px perspective is live. Keep CD-3 by ref."),
    ("place-items", "start", "stretch", "placeItems", "place-items-stretch-run", "place_items_stretch_run", 412, "cards", "Items stretch",
     "`place-items:stretch` grows each cell so stored start x is CD-4.", "Not extra11 place-items-center-run, not extra9 place-items-start.", "place-items stretch is live. Keep CD-3 by ref."),
    ("align-content", "start", "stretch", "alignContent", "align-content-stretch-x12", "align_content_stretch_x12", 410, "cards", "Content stretch",
     "`align-content:stretch` grows rows so stored start y is CD-4.", "Not extra11 align-content-center-run, not extra9 align-content-start.", "align-content stretch is live. Keep CD-3 by ref."),
    ("inset", "0px", "16px", "inset", "inset-sh-16", "inset_sh_16", 412, "abspos", "Inset 16",
     "`inset:16px` slides abspos so stored 0 x is empty.", "Not extra11 inset-sh-8, not extra9 inset-sh-24.", "inset 16 is live. Keep AB-2 by ref."),
    ("max-lines", "none", "6", "maxLines", "max-lines-6", "max_lines_6", 414, "bind", "Max 6",
     "`max-lines:6` clamps so OCR BIND… is a different wrap.", "Not extra11 max-lines-5, not extra10 max-lines-4.", "max-lines 6 is not 5. File the a11y string."),
    ("image-resolution", "from-image", "150dpi", "imageResolution", "image-res-150", "image_res_150", 404, "badges", "150dpi",
     "`image-resolution:150dpi` retimes the replaced box so stored from-image x is empty.", "Not extra11 image-res-96, not extra10 image-res-72.", "150dpi is not 96. Keep the badge ref."),
    ("font-family", "sans-serif", "ui-serif", "fontFamily", "font-family-serif-x12", "font_family_serif_x12", 412, "glyphs", "Serif",
     "`font-family:ui-serif` retimes advances so stored sans x is GL-3.", "Not extra9 font-family-serif, not extra11 font-family-rounded.", "Serif metrics are live. Keep GL-2 by ref."),
    ("font-family", "sans-serif", "ui-monospace", "fontFamily", "font-family-mono-x12", "font_family_mono_x12", 412, "glyphs", "Mono",
     "`font-family:ui-monospace` retimes advances so stored sans x is GL-3.", "Not extra8 font-family-mono, not extra12 font-family-serif-x12.", "Mono metrics are live. Keep GL-2 by ref."),
    ("object-fit", "cover", "contain", "objectFit", "object-fit-contain-x12", "object_fit_contain_x12", 404, "badges", "Fit contain",
     "`object-fit:contain` letterboxes. Stored cover x is empty.", "Not extra6 object-fit-contain, not extra11 object-fit-fill-run.", "contain is paint. Keep the badge ref."),
    ("object-position", "0 0", "50% 50%", "objectPosition", "object-pos-center", "object_pos_center", 404, "badges", "Pos center",
     "`object-position:50% 50%` recenters the replaced box so stored left x is empty.", "Not extra11 object-pos-bottom, not extra9 object-pos-left.", "Center object-position is paint. Keep the badge ref."),
    ("background-clip", "content-box", "border-box", "backgroundClip", "bg-clip-border", "bg_clip_border", 404, "badges", "Clip border",
     "`background-clip:border-box` expands the blob so stored content-box x is empty.", "Not extra11 bg-clip-content, not extra10 bg-clip-padding.", "border-box clip is paint. Keep the badge ref."),
    ("box-shadow", "none", "16px 0 0 CanvasText", "boxShadow", "box-shadow-x16", "box_shadow_x16", 404, "chips", "Offset 16",
     "`box-shadow:16px 0 0` paints a sibling blob. A click on the shadow is not CH-2.", "Not extra10 box-shadow-xy, not extra11 box-shadow-y8.", "16px offset shadow is paint. Keep the chip ref."),
    ("accent-color", "Canvas", "auto", "accentColor", "accent-auto-run", "accent_auto_run", 464, "blends", "Accent auto",
     "`accent-color:auto` restores UA fill so a screenshot looks empty against Canvas.", "Not extra9 accent-canvas, not extra11 accent-canvastext.", "auto accent is not Canvas. Keep aria-checked / the ref."),
    ("caret-color", "transparent", "auto", "caretColor", "caret-auto-run", "caret_auto_run", 415, "chips", "Caret auto",
     "`caret-color:auto` paints a UA caret that covers CH-3. A blink-off screenshot looks empty.", "Not extra11 caret-current, not extra10 caret-transparent-run.", "auto caret is paint. Keep the chip ref."),
    ("scrollbar-width", "auto", "thin", "scrollbarWidth", "scrollbar-thin-x12", "scrollbar_thin_x12", 425, "lanes", "Width thin",
     "`scrollbar-width:thin` shrinks the gutter so stored auto x is LN-6.", "Not extra10 scrollbar-width-thin, not extra11 scrollbar-none-x11.", "thin is not none. Keep the on-screen item ref."),
    ("touch-action", "auto", "pan-up", "touchAction", "touch-pan-up", "touch_pan_up", 425, "lanes", "Pan up",
     "`touch-action:pan-up` forbids down pans so stored auto y is LN-6.", "Not extra11 touch-pan-right, not extra10 touch-pan-left.", "pan-up is not pan-right. Keep the on-screen item ref."),
    ("overscroll-behavior", "auto", "none", "overscrollBehavior", "overscroll-none-x12", "overscroll_none_x12", 425, "lanes", "Overscroll none",
     "`overscroll-behavior:none` kills the scroll chain so stored auto x is LN-6.", "Not extra9 overscroll-none, not extra11 overscroll-contain-run.", "none is not contain. Keep the on-screen item ref."),
    ("scroll-snap-stop", "always", "normal", "scrollSnapStop", "snap-stop-normal-x12", "snap_stop_normal_x12", 425, "lanes", "Stop normal",
     "`scroll-snap-stop:normal` allows skipping so stored always x is LN-6.", "Not extra10 snap-stop-normal, not extra11 snap-stop-always-x11.", "normal stop is not always. Keep the on-screen item ref."),
    ("field-sizing", "content", "fixed", "fieldSizing", "field-sizing-fixed-x12", "field_sizing_fixed_x12", 428, "chips", "Fixed",
     "`field-sizing:fixed` caps the control so stored content x is CH-3.", "Not extra10 field-sizing-fixed-run, not extra11 field-sizing-content-x11.", "fixed field-sizing is live. Keep CH-2 by ref."),
    ("print-color-adjust", "exact", "economy", "printColorAdjust", "print-economy-x12", "print_economy_x12", 415, "badges", "Economy",
     "`print-color-adjust:economy` lets the UA remap so a print screenshot blob is not the badge.", "Not extra10 print-economy, not extra11 print-exact-x11.", "economy print color is paint. Keep the badge ref."),
    ("math-shift", "compact", "normal", "mathShift", "math-shift-normal-x12", "math_shift_normal_x12", 418, "eq", "Shift normal",
     "`math-shift:normal` restores superscripts so stored compact x is EQ-5.", "Not extra10 math-shift-normal, not extra11 math-shift-compact-x11.", "normal math-shift is a used box. File EQ-4 by ref."),
    ("grid-auto-columns", "auto", "40px", "gridAutoColumns", "grid-auto-cols-40", "grid_auto_cols_40", 428, "cards", "Auto cols 40",
     "`grid-auto-columns:40px` sizes implicit cols so stored auto x is CD-4.", "Not extra11 grid-auto-cols-120, not extra9 grid-auto-cols.", "auto-columns 40 is live. Keep CD-3 by ref."),
    ("masonry-auto-flow", "pack", "next", "masonryAutoFlow", "masonry-next-x12", "masonry_next_x12", 428, "cards", "Masonry next",
     "`masonry-auto-flow:next` forbids packing holes so stored pack x is CD-4.", "Not extra9 masonry-auto, not extra11 masonry-definite.", "masonry next is live. Keep CD-3 by ref."),
    ("position-area", "none", "end", "positionArea", "position-area-end-x12", "position_area_end_x12", 507, "abspos", "Area end",
     "`position-area:end` slots abspos into the end region so stored none x is empty.", "Not extra10 position-area-end, not extra11 position-area-center.", "position-area end is live. Keep AB-2 by ref."),
    ("anchor-size", "auto", "self", "anchorSize", "anchor-size-self", "anchor_size_self", 507, "floats", "Size self",
     "`anchor-size:self` sizes abspos from itself so stored auto size x is File.", "Not extra8 anchor-size-chip, not extra11 anchor-size-closest.", "self anchor-size is live. Re-find the invoker or use the ref."),
    ("view-transition-name", "none", "card", "viewTransitionName", "view-trans-card-x12", "view_trans_card_x12", 412, "cards", "Name card",
     "`view-transition-name:card` snapshots the old box so a click during the morph hits CD-4.", "Not extra8 view-trans-named, not extra11 view-trans-chip.", "Named card transitions are not the live ref. Keep CD-3 by ref."),
    ("animation-name", "none", "nudge-x", "animationName", "anim-name-nudge-x12", "anim_name_nudge_x12", 412, "chips", "Nudge x",
     "`animation-name:nudge-x` translates the chip so stored none x is CH-3.", "Not extra8 anim-name-nudge, not extra11 anim-name-nudge-y.", "Named x animation is live. Keep CH-2 by ref."),
    ("transition", "none", "transform 200ms", "transition", "trans-transform-200", "trans_transform_200", 412, "chips", "Trans transform 200",
     "`transition:transform 200ms` leaves stored pre-transition x at CH-3.", "Not extra8 trans-shorthand, not extra11 trans-opacity-200.", "Transform transition is live. Keep CH-2 by ref after it settles."),
    ("offset-path", "none", "path('M0,0 L24,0')", "offsetPath", "offset-path-path", "offset_path_path", 520, "by", "Path 24",
     "`offset-path:path(...)` parks abspos at 24px so stored none x is BY-6.", "Not extra11 offset-path-ray, not extra8 offset-sh.", "offset-path path is live. Keep BY-5 by ref."),
    ("shape-margin", "0px", "4px", "shapeMargin", "shape-margin-4", "shape_margin_4", 412, "floats", "Shape margin 4",
     "`shape-margin:4px` pushes wrap so stored 0 x is FL-4.", "Not extra11 shape-margin-8, not extra9 shape-margin-16.", "4px shape-margin is live. Keep FL-3 by ref."),
    ("text-emphasis-style", "none", "dot", "textEmphasisStyle", "emphasis-dot-x12", "emphasis_dot_x12", 404, "glyphs", "Dot",
     "`text-emphasis-style:dot` paints marks above. A click on a mark is not GL-2.", "Not extra9 emphasis-dot, not extra11 emphasis-sesame.", "Dot marks are paint. Keep the glyph ref."),
    ("ruby-position", "alternate", "over", "rubyPosition", "ruby-pos-over-x12", "ruby_pos_over_x12", 416, "glyphs", "Ruby over",
     "`ruby-position:over` parks annotation above so stored alternate y is GL-3.", "Not extra9 ruby-pos-over, not extra11 ruby-pos-inter.", "over is not inter-character. Keep GL-2 by ref."),
    ("font-stretch", "normal", "expanded", "fontStretch", "font-stretch-expanded-x12", "font_stretch_expanded_x12", 412, "glyphs", "Expanded",
     "`font-stretch:expanded` widens glyphs so stored normal x is GL-3.", "Not extra9 font-stretch-exp, not extra11 font-stretch-ultracond.", "expanded stretch is live. Keep GL-2 by ref."),
    ("font-variant-numeric", "normal", "lining-nums", "fontVariantNumeric", "font-var-lining-x12", "font_var_lining_x12", 412, "glyphs", "Lining",
     "`font-variant-numeric:lining-nums` changes digit metrics so stored normal x is GL-3.", "Not extra10 font-var-lining, not extra11 font-var-tabular.", "lining nums are live. Keep GL-2 by ref."),
    ("hanging-punctuation", "none", "first", "hangingPunctuation", "hanging-first-x12", "hanging_first_x12", 416, "text", "First",
     "`hanging-punctuation:first` hangs the open quote so stored none x is TX-5.", "Not extra11 hanging-last-run, not extra10 hanging-first-force.", "first is not last. Keep TX-2 by ref."),
    ("text-indent", "0px", "8px", "textIndent", "text-indent-8", "text_indent_8", 412, "text", "Indent 8",
     "`text-indent:8px` slides the first line so stored 0 x is TX-5.", "Not extra11 text-indent-40, not extra9 text-indent-24.", "8px indent is not 40. Keep TX-2 by ref."),
    ("tab-size", "8", "3", "tabSize", "tab-size-3", "tab_size_3", 413, "labels", "Tab 3",
     "`tab-size:3` retimes tab stops so a stored tab-8 wrap line is LB-3.", "Not extra11 tab-size-1, not extra10 tab-size-2.", "tab-size 3 is live. File the a11y string."),
    ("outline-width", "0px", "2px", "outlineWidth", "outline-width-2", "outline_width_2", 404, "floats", "Outline 2",
     "`outline-width:2px` paints hairline UA chrome. Screenshot of the ring is not FL-3.", "Not extra10 outline-width-1, not extra11 outline-width-16.", "2px outline is paint. Keep the float ref."),
    ("column-width", "auto", "6em", "columnWidth", "column-width-6em", "column_width_6em", 416, "text", "Width 6em",
     "`column-width:6em` fragments so stored auto x is TX-5.", "Not extra10 column-width-8em, not extra11 column-width-20em.", "6em is not 8em. Keep TX-2 by ref."),
    ("column-span", "all", "none", "columnSpan", "column-span-none-x12", "column_span_none_x12", 416, "text", "Span none",
     "`column-span:none` drops the stretch so stored all x is TX-5.", "Not extra10 column-span-none, not extra11 column-span-all-x11.", "none is not all. Keep TX-2 by ref."),
    ("page", "auto", "narrow", "page", "page-narrow", "page_narrow", 416, "text", "Narrow",
     "`page:narrow` reflows print fragmentation so stored auto x is TX-5.", "Not extra11 page-wide, not extra10 page-auto-run.", "Named narrow page is live. Keep TX-2 by ref."),
    ("break-before", "auto", "page", "breakBefore", "break-before-page", "break_before_page", 416, "text", "Before page",
     "`break-before:page` forces a page break so stored auto x is TX-5.", "Not extra11 break-after-page-run, not extra9 break-before-column.", "break-before page is live. Keep TX-2 by ref."),
    ("reading-order", "0", "5", "readingOrder", "reading-order-5", "reading_order_5", 428, "cards", "Order 5",
     "`reading-order:5` restacks a11y order so stored 0 x is CD-4.", "Not extra11 reading-order-4, not extra10 reading-order-3.", "reading-order 5 is not 4. Keep CD-3 by ref."),
    ("scroll-timeline-axis", "inline", "block", "scrollTimelineAxis", "scroll-tl-block-x12", "scroll_tl_block_x12", 412, "chips", "Axis block",
     "`scroll-timeline-axis:block` drives the timeline from y-scroll so stored inline x is CH-3.", "Not extra9 scroll-tl-block, not extra11 scroll-tl-y.", "Axis block is not y. Keep CH-2 by ref."),
    ("text-spacing-trim", "space-all", "trim-end", "textSpacingTrim", "text-spacing-trim-end", "text_spacing_trim_end", 412, "glyphs", "Trim end",
     "`text-spacing-trim:trim-end` eats trailing CJK spacing so stored space-all x is GL-3.", "Not extra11 text-spacing-trim-start, not extra9 text-spacing-trim-all.", "trim-end is not trim-start. Keep GL-2 by ref."),
    ("font-language-override", "normal", "KOR", "fontLanguageOverride", "font-lang-kor", "font_lang_kor", 412, "glyphs", "Lang KOR",
     "`font-language-override:KOR` swaps locl glyphs so stored normal x is GL-3.", "Not extra11 font-lang-jpn, not extra9 font-lang-override.", "KOR is not JPN. Keep GL-2 by ref."),
    ("order", "0", "-2", "order", "order-n2", "order_n2", 428, "chips", "Order -2",
     "`order:-2` pulls the item first so stored 0 x is CH-3.", "Not extra10 order-n1, not extra12 order-4.", "flex order -2 is live. Keep CH-2 by ref."),
    ("z-index", "auto", "-2", "zIndex", "z-index-neg2", "z_index_neg2", 403, "chips", "Z -2",
     "`z-index:-2` drops the stacking context so a click hits CH-3.", "Not extra7 z-index-neg, not extra12 z-index-4.", "-2 is not auto. Keep CH-2 by ref."),
    ("flex-shrink", "1", "0", "flexShrink", "flex-shrink-0-x12", "flex_shrink_0_x12", 428, "chips", "Shrink 0",
     "`flex-shrink:0` refuses to shrink so stored shrink-x is CH-3.", "Not r395 flex-shrink, not extra12 flex-grow-4.", "shrink 0 is live. Keep CH-2 by ref."),
    ("line-height", "normal", "0.8", "lineHeight", "line-height-08", "line_height_08", 410, "rows", "Line 0.8",
     "`line-height:0.8` packs rows so stored normal y is RW-3.", "Not extra12 line-height-125, not extra9 line-height-1.", "Unitless 0.8 is live. Keep RW-2 by ref."),
    ("gap", "0px", "2px", "gap", "gap-2", "gap_2", 412, "chips", "Gap 2",
     "`gap:2px` restacks both axes so stored 0-gap x is CH-3.", "Not extra12 gap-4, not extra10 gap-8.", "gap 2 is not 4. Keep CH-2 by ref."),
    ("letter-spacing", "normal", "0.05em", "letterSpacing", "letter-spacing-05", "letter_spacing_05", 412, "glyphs", "Tracking 0.05em",
     "`letter-spacing:0.05em` widens glyphs so stored normal x is GL-3.", "Not extra12 letter-spacing-em-x12, not extra11 letter-spacing-0.", "0.05em tracking is live. Keep GL-2 by ref."),
    ("word-spacing", "normal", "0.05em", "wordSpacing", "word-spacing-02", "word_spacing_02", 412, "glyphs", "Word 0.05em",
     "`word-spacing:0.05em` widens word gaps so stored normal x is GL-3.", "Not extra12 word-spacing-em-x12, not extra11 word-spacing-neg.", "0.05em word-spacing is live. Keep GL-2 by ref."),
    ("mix-blend-mode", "normal", "multiply", "mixBlendMode", "blend-multiply-x12", "blend_multiply_x12", 464, "blends", "Multiply",
     "`mix-blend-mode:multiply` darkens so the selected chip looks empty.", "Not extra8 blend-multiply, not extra12 blend-color-burn-run.", "multiply is not empty. Keep aria-selected / the ref."),
    ("filter", "none", "contrast(3)", "filter", "filter-contrast-3", "filter_contrast_3", 415, "cards", "Contrast 3",
     "`filter:contrast(3)` remaps paint so a screenshot blob is not CD-3.", "Not extra10 filter-contrast-2, not extra11 backdrop-contrast.", "Contrast 3 is paint. Keep CD-3 by ref."),
    ("text-align", "start", "end", "textAlign", "text-align-end-x12", "text_align_end_x12", 412, "text", "Align end",
     "`text-align:end` packs so stored start x is TX-5.", "Not extra7 text-align-end mill, not extra12 text-align-right-run.", "end is not right. Keep TX-2 by ref."),
    ("white-space", "normal", "pre-line", "whiteSpace", "ws-pre-line-x12", "ws_pre_line_x12", 413, "labels", "Pre-line",
     "`white-space:pre-line` keeps newlines so a normal wrap line is LB-3.", "Not extra8 ws-pre-line, not extra12 ws-pre-x12.", "pre-line is not pre. File the a11y string."),
    ("hyphens", "none", "manual", "hyphens", "hyphens-manual-x12", "hyphens_manual_x12", 414, "bind", "Manual",
     "`hyphens:manual` only breaks at &shy; so OCR BIND… is a different wrap.", "Not extra12 hyphens-none-x12, not extra11 hyphens-auto-run.", "manual is not none. File the a11y string."),
    ("contain", "none", "layout", "contain", "contain-layout-run", "contain_layout_run", 428, "chips", "Layout",
     "`contain:layout` isolates layout so stored none x is CH-3.", "Not extra12 contain-size-run, not extra11 contain-paint-run.", "contain:layout is live. Keep CH-2 by ref."),
    ("will-change", "auto", "opacity", "willChange", "will-change-opacity-x12", "will_change_opacity_x12", 412, "cards", "Will opacity",
     "`will-change:opacity` promotes a layer so stored auto x is a different compositor box.", "Not extra9 will-change-opacity, not extra12 will-change-transform-x12.", "will-change:opacity is live. Keep CD-3 by ref."),
    ("user-select", "auto", "text", "userSelect", "us-text-run", "us_text_run", 413, "labels", "Text",
     "`user-select:text` limits selection so OCR of a spilled highlight is LB-3.", "Not extra12 us-all-run, not extra11 us-none-run.", "text is not all. File the a11y string."),
    ("pointer-events", "none", "auto", "pointerEvents", "pe-auto-x12", "pe_auto_x12", 410, "chips", "Auto",
     "`pointer-events:auto` restores hit-testing so stored none x hits CH-3.", "Not extra12 pe-none-x12, not extra11 pe-visible-painted.", "auto is not none. Keep CH-2 by ref."),
    ("float", "none", "right", "float", "float-right-x12", "float_right_x12", 412, "floats", "Right",
     "`float:right` packs to the end so stored none x is FL-4.", "Not extra10 float-right-run, not extra12 float-left-x12.", "right is not left. Keep FL-3 by ref."),
    ("vertical-align", "baseline", "super", "verticalAlign", "valign-super-x12", "valign_super_x12", 410, "glyphs", "Super",
     "`vertical-align:super` raises glyphs so stored baseline y is GL-3.", "Not extra8 valign-super, not extra12 valign-middle-x12.", "super is not middle. Keep GL-2 by ref."),
    ("border-radius", "0px", "16px", "borderRadius", "radius-16", "radius_16", 404, "chiphole", "Radius 16",
     "`border-radius:16px` makes corner holes. Stored square x is empty.", "Not extra12 radius-12, not extra8 radius-full.", "A 16px radius hole is still the chip if you use the ref."),
    ("outline-offset", "0px", "2px", "outlineOffset", "outline-offset-2", "outline_offset_2", 404, "floats", "Offset 2",
     "`outline-offset:2px` pushes UA chrome out so a screenshot ring is not FL-3.", "Not extra12 outline-offset-8, not extra11 outline-offset-4.", "2px offset outline is paint. Keep the float ref."),
    ("border-width", "0px", "12px", "borderWidth", "border-width-12", "border_width_12", 404, "chips", "Width 12",
     "`border-width:12px` grows a ring. Center click on the ring is not CH-2.", "Not extra8 border-width-8, not extra12 border-width-2.", "A 12px border is paint. Keep the chip ref."),
    ("scroll-margin-bottom", "0px", "24px", "scrollMarginBottom", "scroll-mar-bottom", "scroll_mar_bottom", 425, "lanes", "Margin bottom 24",
     "`scroll-margin-bottom:24px` pads snap so stored 0-margin y is LN-6.", "Not extra12 scroll-mar-right, not extra11 scroll-mar-top.", "Physical scroll-margin-bottom is live. Keep the on-screen item ref."),
    ("mask-position", "left top", "center", "maskPosition", "mask-pos-center", "mask_pos_center", 404, "cardhole", "Mask center",
     "`mask-position:center` slides the mask. Stored left x is a hole.", "Not extra9 mask-pos-left, not extra10 mask-pos-right.", "A centered mask hole is still the card ref."),
    ("clip-path", "none", "ellipse(50% 40%)", "clipPath", "clip-ellipse-x12", "clip_ellipse_x12", 404, "cardhole", "Ellipse 50",
     "`clip-path:ellipse(50% 40%)` cuts the card. Stored none x is a hole.", "Not extra9 clip-path-ellipse-80, not extra12 clip-path-inset-4.", "An ellipse clip is still the card ref."),
    ("perspective", "none", "800px", "perspective", "perspective-800", "perspective_800", 520, "cards", "Persp 800",
     "`perspective:800px` foreshortens children so stored none x misses.", "Not extra12 perspective-100, not extra11 perspective-400.", "800px perspective is live. Keep CD-3 by ref."),
    ("place-items", "stretch", "end", "placeItems", "place-items-end-x12", "place_items_end_x12", 412, "cards", "Items end",
     "`place-items:end` packs each cell so stored stretch x is CD-4.", "Not extra10 place-items-end, not extra12 place-items-stretch-run.", "place-items end is live. Keep CD-3 by ref."),
    ("inset", "0px", "32px", "inset", "inset-sh-32", "inset_sh_32", 412, "abspos", "Inset 32",
     "`inset:32px` slides abspos so stored 0 x is empty.", "Not extra12 inset-sh-16, not extra9 inset-sh-24.", "inset 32 is live. Keep AB-2 by ref."),
    ("max-lines", "none", "8", "maxLines", "max-lines-8", "max_lines_8", 414, "bind", "Max 8",
     "`max-lines:8` clamps so OCR BIND… is a different wrap.", "Not extra12 max-lines-6, not extra11 max-lines-5.", "max-lines 8 is not 6. File the a11y string."),
    ("font-size", "16px", "9px", "fontSize", "font-size-9", "font_size_9", 412, "glyphs", "Size 9",
     "`font-size:9px` shrinks glyphs so stored 16px x is GL-3.", "Not extra10 font-size-10, not extra12 font-size-11.", "9px is not 10. Keep GL-2 by ref."),
    ("opacity", "1", "0.5", "opacity", "opacity-05-x12", "opacity_05_x12", 464, "blends", "Opacity 0.5",
     "`opacity:0.5` fades so a screenshot looks unselected.", "Not extra mill opacity-half, not extra12 opacity-03.", "0.5 is not unselected. Keep aria-selected / the ref."),
    ("zoom", "1", "1.5", "zoom", "zoom-15-x12", "zoom_15_x12", 412, "cards", "Zoom 1.5",
     "`zoom:1.5` grows the used box so stored unzoomed x is CD-4.", "Not extra8 zoom-15, not extra12 zoom-11.", "CSS zoom 1.5 is not 1.1. Keep CD-3 by ref."),
    ("scale", "1", "1.5", "scale", "scale-15-x12", "scale_15_x12", 412, "cards", "Scale 1.5",
     "`scale:1.5` grows so stored unscaled x is CD-4.", "Not extra8 scale-15, not extra12 scale-4.", "Uniform 1.5 scale is live. Keep CD-3 by ref."),
    ("cursor", "auto", "progress", "cursor", "cursor-progress-x12", "cursor_progress_x12", 404, "chips", "Progress",
     "`cursor:progress` paints an arrow+spinner over CH-2. Screenshot of the glyph is not CH-3.", "Not extra11 cursor-progress-run, not extra9 cursor-progress.", "The progress cursor is paint. Keep the chip ref."),
    ("display", "block", "list-item", "display", "display-list-item-x12", "display_list_item_x12", 449, "lists", "List-item",
     "`display:list-item` paints a marker. Clicking the marker slot is not LI-2.", "Not extra6 display-list-item, not extra8 list-pos-inside.", "A marker is not the item. Keep the listitem ref."),
    ("backdrop-filter", "none", "opacity(0.5)", "backdropFilter", "backdrop-opacity-x12", "backdrop_opacity_x12", 415, "cards", "Backdrop opacity 0.5",
     "`backdrop-filter:opacity(0.5)` fades the backdrop so a screenshot blob is not CD-3.", "Not extra10 backdrop-opacity, not extra12 backdrop-blur-x12.", "Backdrop opacity 0.5 is paint. Keep CD-3 by ref."),
    ("image-orientation", "from-image", "flip", "imageOrientation", "image-orient-flip-x12", "image_orient_flip_x12", 404, "badges", "Orient flip",
     "`image-orientation:flip` mirrors the replaced box so stored from-image x is empty.", "Not extra10 image-orient-flip, not extra9 image-orient-none.", "flip orientation is paint. Keep the badge ref."),
]

GENERA = [
    "nuphar", "nymphoides", "brasenia", "cabomba", "nelumbo", "victoria", "euryale", "barclaya", "ondinea", "callitriche",
    "hippuris", "hottonia", "utricularia", "aldrovanda", "drosera", "pinguicula", "genlisea", "dionaea", "sarracenia", "darlingtonia",
    "heliamphora", "nepenthes", "cephalotus", "roridula", "byblis", "drosophyllum", "philcoxia", "stylidium", "myriophyllum", "ceratophyllum",
    "potamogeton", "zostera", "posidonia", "cymodocea", "halodule", "thalassia", "enhalus", "syringodium", "elodea", "egeria",
    "hydrilla", "vallisneria", "ottelia", "blyxa", "najas", "zannichellia", "ruppia", "lepilaena", "lemna", "spirodela",
    "wolffia", "wolffiella", "landoltia", "chara", "nitella", "tolypella", "lychnothamnus", "lamprothamnium", "nitellopsis", "sphaerochara",
    "vaucheria", "botrydium", "xanthidium", "micrasterias", "closterium", "staurastrum", "desmidium", "hyalotheca", "bambusina", "spirogyra",
    "zygnema", "mougeotia", "sirogonium", "temnogyra", "debarya", "zygnemopsis", "ulva", "monostroma", "ulvaria", "umbraulva",
    "gayralia", "ulvella", "blidingia", "codium", "bryopsis", "derbesia", "halimeda", "udotea", "penicillus", "rhipocephalus",
    "avrainvillea", "chlorodesmis", "caulerpa", "acetabularia", "batophora", "dasycladus", "neomeris", "bornetella", "cymopolia", "polyphysa",
    "padina", "dictyota", "zonalria", "stypopodium", "lobophora", "spatoglossum", "dictyopteris", "taonia", "canistrocarpus", "rugulopteryx",
    "sargassum", "fucus", "ascophyllum", "pelvetia", "himanthalia", "durvillaea", "macrocystis", "nereocystis", "postelsia", "eisenia",
    "laminaria", "saccharina", "alaria", "undaria", "eckonia", "lessonia", "eualaria", "agrum", "costaria", "pleurophycus",
    "porphyra", "pyropia", "palmaria", "chondrus", "mastocarpus", "gigartina", "mazzaella", "iridaea", "gracilariopsis", "hydropuntia",
    "gelidium", "pterocladiella", "ahnfeltia", "phyllophora", "coccotylus", "oddonthia", "rhodymenia",
    "lomentaria", "champia", "gastroclonium", "coeloseira", "ceramium", "centroceras", "spyridea", "plocamium",
    "delesseria", "membranooptera", "phycodrys", "nitophyllum", "cryptopleura", "haraldiophyllum", "myriogramme",
    "dasya", "heterosiphonia", "polynerua", "brongniartella", "piloniella",
]


def extra_used():
    used_w, used_es, used_pl, used_pr, used_ax, used_seed, used_err = (
        load_set("widgets"), load_set("errslugs"), load_set("places"),
        load_set("prefixes"), load_set("auxes"), load_set("seeds"), load_set("errs"),
    )
    for name in (
        "brw-mill-r395-extra8.py", "brw-mill-r395-extra9.py",
        "brw-mill-r395-extra10.py", "brw-mill-r395-extra11.py",
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
    used_w, used_es, used_pl, used_pr, used_ax, used_seed, used_err = extra_used()
    used_keep: set[str] = set()
    assert len(PLANTS) <= len(GENERA), (len(PLANTS), len(GENERA))
    rows = []
    for i, plant in enumerate(PLANTS):
        css, fr, to, js, widget, err, code, tmpl, btn, new, not_, teach = plant
        if code == 409:
            raise SystemExit(f"{widget}: 409 banned")
        if widget in used_w:
            raise SystemExit(f"widget collision {widget}")
        used_w.add(widget)
        if err in used_err:
            err = err + "_x12"
            if err in used_err:
                raise SystemExit(f"err collision {err}")
        used_err.add(err)
        item, neigh, fail, ref, nref, fref, x0, x1, y, title, path = T[tmpl]
        prefix = mint("".join(ch for ch in widget if ch.isalnum())[:4] or "ecp", used_pr)
        aux = mint(("".join(ch for ch in widget if ch.isalnum())[2:6] or "eca") + "x", used_ax)
        if prefix == aux:
            aux = mint(aux + "z", used_ax)
        genus = GENERA[i]
        ok, bad = genus + "shaw", genus + "beck"
        if ok in used_pl or bad in used_pl:
            ok, bad = genus + "peak", genus + "tor"
        if ok in used_pl or bad in used_pl or ok == bad:
            raise SystemExit(f"place collision {ok} {bad}")
        used_pl.add(ok); used_pl.add(bad)
        slug = f"{aux}-{code}"
        if slug in used_es:
            raise SystemExit(f"err_slug collision {slug}")
        used_es.add(slug)
        seed_ok, seed_bad = f"css-{widget}", f"css-{widget}-{code}"
        if seed_ok in used_seed or seed_bad in used_seed:
            seed_ok, seed_bad = f"css-{widget}-x12", f"css-{widget}-x12-{code}"
        if seed_ok in used_seed or seed_bad in used_seed:
            raise SystemExit(f"seed collision {seed_ok}")
        used_seed.add(seed_ok); used_seed.add(seed_bad)
        keep = keep_code(genus, used_keep)
        nxt = PLANTS[i + 1][4] if i + 1 < len(PLANTS) else "catalog continue."
        rows.append((
            prefix, aux, ok, bad, widget, slug, code, err,
            css, fr, to, js, item, neigh, fail, ref, nref, fref,
            x0, x1, y, btn, title, "Keep", path, keep, f"{item} {genus}", seed_ok, seed_bad,
            new, not_, teach, nxt + ".",
        ))
    out = HERE / "brw-mill-r395-extra12.py"
    lines = ['"""Leftover CSS plants r1180+."""', "KEYS = (",
             '    "prefix", "aux", "ok_place", "bad_place", "widget", "err_slug", "code", "err",',
             '    "css", "from", "to", "js", "item", "neigh", "fail_item", "ref", "nref", "fref",',
             '    "x0", "x1", "y", "btn", "title", "verb", "path", "keep", "note", "seed_ok", "seed_bad",',
             '    "new", "not", "teach", "next",', ")", "ROWS = ["]
    for row in rows:
        lines.append("(" + ",".join(repr(v) for v in row) + "),")
    lines += ["]", "EXTRA = [dict(zip(KEYS, row)) for row in ROWS]", ""]
    out.write_text("\n".join(lines))
    print(f"wrote {out} plants={len(rows)} last={rows[-1][4]} {rows[-1][2]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
