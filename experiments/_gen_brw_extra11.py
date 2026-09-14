#!/usr/bin/env python3
"""Generate leftover CSS extra11 plants r1068+."""
from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
# reuse T + helpers from extra10 generator
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

PLANTS = [
    ("font-size", "16px", "14px", "fontSize", "font-size-14", "font_size_14", 412, "glyphs", "Size 14",
     "`font-size:14px` shrinks glyphs so stored 16px x is GL-3.", "Not extra10 font-size-10, not extra8 font-size-24.", "14px is live. Keep GL-2 by ref."),
    ("font-size", "16px", "20px", "fontSize", "font-size-20", "font_size_20", 412, "glyphs", "Size 20",
     "`font-size:20px` grows glyphs so stored 16px x is GL-3.", "Not extra10 font-size-18, not extra9 font-size-32.", "20px is not 18. Keep GL-2 by ref."),
    ("font-size", "16px", "36px", "fontSize", "font-size-36", "font_size_36", 412, "glyphs", "Size 36",
     "`font-size:36px` grows glyphs so stored 16px x is GL-3.", "Not extra10 font-size-48, not extra9 font-size-32.", "36px is not 48. Keep GL-2 by ref."),
    ("zoom", "1", "0.75", "zoom", "zoom-075", "zoom_075", 412, "cards", "Zoom 0.75",
     "`zoom:0.75` shrinks the used box so stored unzoomed x is CD-4.", "Not extra10 zoom-025, not extra9 zoom-05.", "CSS zoom 0.75 is not scale(). Keep CD-3 by ref."),
    ("zoom", "1", "4", "zoom", "zoom-4", "zoom_4", 412, "cards", "Zoom 4",
     "`zoom:4` quadruples the used box so stored unzoomed x is CD-4.", "Not extra10 zoom-3, not extra9 zoom-2.", "CSS zoom 4 is not scale(4). Keep CD-3 by ref."),
    ("opacity", "1", "0.6", "opacity", "opacity-06", "opacity_06", 464, "blends", "Opacity 0.6",
     "`opacity:0.6` fades so a screenshot looks unselected.", "Not extra10 opacity-04, not extra9 opacity-08.", "0.6 is not unselected. Keep aria-selected / the ref."),
    ("scale", "1", "0.25", "scale", "scale-025", "scale_025", 412, "cards", "Scale 0.25",
     "`scale:0.25` shrinks so stored unscaled x is CD-4.", "Not extra10 scale-05, not extra9 scale-2.", "Uniform 0.25 scale is live. Keep CD-3 by ref."),
    ("scale", "1", "3", "scale", "scale-3", "scale_3", 412, "cards", "Scale 3",
     "`scale:3` grows so stored unscaled x is CD-4.", "Not extra10 scale-05, not extra9 scale-2.", "Uniform scale 3 is live. Keep CD-3 by ref."),
    ("rotate", "0deg", "z 15deg", "rotate", "rotate-z-15", "rotate_z_15", 520, "cards", "Rotate Z 15",
     "`rotate:z 15deg` shears the hit diamond so stored 0deg x misses.", "Not extra9 rotate-z-40, not extra10 rotate-x-15.", "Z-rotate 15 is not 40. Keep CD-3 by ref."),
    ("translate", "0px", "24px 0px", "translate", "translate-x-24", "translate_x_24", 412, "abspos", "Translate 24",
     "`translate:24px 0` slides so stored 0 x is empty.", "Not extra8 translate-x-40, not extra10 translate-z-20.", "X translate 24 is live. Keep AB-2 by ref."),
    ("cursor", "auto", "pointer", "cursor", "cursor-pointer", "cursor_pointer", 404, "chips", "Pointer",
     "`cursor:pointer` paints a hand glyph over CH-2. Screenshot of the glyph is not CH-3.", "Not extra8 cursor-grab, not extra10 cursor-alias.", "The pointer cursor is paint. Keep the chip ref."),
    ("cursor", "auto", "text", "cursor", "cursor-text", "cursor_text", 404, "chips", "Text",
     "`cursor:text` paints an I-beam over CH-2. Screenshot of the glyph is not CH-3.", "Not extra10 cursor-vertical-text, not extra9 cursor-help.", "The text cursor is paint. Keep the chip ref."),
    ("cursor", "auto", "default", "cursor", "cursor-default", "cursor_default", 404, "chips", "Default",
     "`cursor:default` paints an arrow over CH-2. Screenshot of the glyph is not CH-3.", "Not extra8 cursor-grab, not extra11 cursor-pointer.", "The default cursor is paint. Keep the chip ref."),
    ("overflow-x", "visible", "clip", "overflowX", "overflow-x-clip-run", "overflow_x_clip_run", 425, "lanes", "Clip x",
     "`overflow-x:clip` hard-clips without a scrollport so stored visible x is LN-6.", "Not extra10 overflow-x-overlay, not extra7 overflow-x-auto.", "clip-x is not overlay. Keep the on-screen item ref."),
    ("backdrop-filter", "none", "contrast(2)", "backdropFilter", "backdrop-contrast", "backdrop_contrast", 415, "cards", "Backdrop contrast 2",
     "`backdrop-filter:contrast(2)` remaps paint so a screenshot blob is not CD-3.", "Not extra10 backdrop-hue, not extra10 filter-contrast-2.", "Backdrop contrast is paint. Keep CD-3 by ref."),
    ("letter-spacing", "normal", "0", "letterSpacing", "letter-spacing-0", "letter_spacing_0", 412, "glyphs", "Tracking 0",
     "`letter-spacing:0` collapses tracking so stored normal x is GL-3.", "Not extra10 letter-spacing-neg, not extra9 letter-spacing-em.", "Zero tracking is live. Keep GL-2 by ref."),
    ("word-spacing", "normal", "-0.1em", "wordSpacing", "word-spacing-neg", "word_spacing_neg", 412, "glyphs", "Word -0.1em",
     "`word-spacing:-0.1em` tightens word gaps so stored normal x is GL-3.", "Not extra10 word-spacing-0, not extra9 word-spacing-em.", "Negative word-spacing is live. Keep GL-2 by ref."),
    ("line-height", "normal", "3", "lineHeight", "line-height-3", "line_height_3", 410, "rows", "Line 3",
     "`line-height:3` grows rows so stored normal y is RW-3.", "Not extra10 line-height-15, not extra7 line-height-2.", "Unitless 3 is live. Keep RW-2 by ref."),
    ("gap", "0px", "16px", "gap", "gap-16", "gap_16", 412, "chips", "Gap 16",
     "`gap:16px` restacks both axes so stored 0-gap x is CH-3.", "Not extra10 gap-8, not extra9 gap-24.", "gap 16 is not 8. Keep CH-2 by ref."),
    ("flex-grow", "0", "3", "flexGrow", "flex-grow-3", "flex_grow_3", 428, "chips", "Grow 3",
     "`flex-grow:3` eats free space so stored grow-0 x is CH-3.", "Not extra10 flex-grow-1, not extra9 flex-grow-2.", "grow 3 is not 1. Keep CH-2 by ref."),
    ("order", "0", "3", "order", "order-3", "order_3", 428, "chips", "Order 3",
     "`order:3` restacks the flex item so stored 0 x is CH-3.", "Not extra10 order-n1, not extra9 order-2.", "flex order 3 is live. Keep CH-2 by ref."),
    ("column-count", "auto", "4", "columnCount", "column-count-4", "column_count_4", 416, "text", "Count 4",
     "`column-count:4` fragments so stored auto x is TX-5.", "Not extra10 column-count-2, not extra9 column-count-3.", "column-count 4 is not 3. Keep TX-2 by ref."),
    ("object-fit", "cover", "fill", "objectFit", "object-fit-fill-run", "object_fit_fill_run", 404, "badges", "Fit fill",
     "`object-fit:fill` stretches the blob. Stored cover x is empty.", "Not extra10 object-fit-cover-run, not extra9 object-fit-none-box.", "fill is paint. Keep the badge ref."),
    ("mix-blend-mode", "normal", "overlay", "mixBlendMode", "blend-overlay-run", "blend_overlay_run", 464, "blends", "Overlay",
     "`mix-blend-mode:overlay` remaps so the selected chip looks empty.", "Not extra10 blend-darken-run, not extra8 blend-multiply.", "overlay is not empty. Keep aria-selected / the ref."),
    ("z-index", "auto", "2", "zIndex", "z-index-2", "z_index_2", 403, "chips", "Z 2",
     "`z-index:2` restacks so a click hits CH-3.", "Not extra10 z-index-1, not extra9 z-index-999.", "2 is not 1. Keep CH-2 by ref."),
    ("cursor", "auto", "progress", "cursor", "cursor-progress-run", "cursor_progress_run", 404, "chips", "Progress",
     "`cursor:progress` paints an arrow+spinner over CH-2. Screenshot of the glyph is not CH-3.", "Not extra9 cursor-progress, not extra11 cursor-pointer.", "The progress cursor is paint. Keep the chip ref."),
    ("display", "block", "inline-block", "display", "display-inline-block-run", "display_inline_block_run", 412, "chips", "Inline-block",
     "`display:inline-block` shrink-wraps so stored block x is CH-3.", "Not extra9 display-inline, not extra10 display-run-in.", "inline-block is live. Keep CH-2 by ref."),
    ("overflow-y", "visible", "clip", "overflowY", "overflow-y-clip-run", "overflow_y_clip_run", 425, "lanes", "Clip y",
     "`overflow-y:clip` hard-clips without a scrollport so stored visible y is LN-6.", "Not extra10 overflow-y-visible, not extra8 overflow-y-auto.", "clip-y is not visible. Keep the on-screen item ref."),
    ("filter", "none", "brightness(2)", "filter", "filter-brightness-2", "filter_brightness_2", 415, "cards", "Brightness 2",
     "`filter:brightness(2)` remaps paint so a screenshot blob is not CD-3.", "Not extra10 filter-contrast-2, not extra9 backdrop-brightness.", "Brightness 2 is paint. Keep CD-3 by ref."),
    ("text-align", "start", "left", "textAlign", "text-align-left-run", "text_align_left_run", 412, "text", "Align left",
     "`text-align:left` packs so stored start x is TX-5.", "Not extra7 text-align-center, not extra mill text-align-end.", "left is not start. Keep TX-2 by ref."),
    ("white-space", "normal", "nowrap", "whiteSpace", "ws-nowrap-run", "ws_nowrap_run", 413, "labels", "Nowrap",
     "`white-space:nowrap` forbids wrap so a normal wrap line is LB-3.", "Not extra8 text-wrap-nowrap, not extra10 ws-pre-wrap-run.", "nowrap white-space is not text-wrap. File the a11y string."),
    ("hyphens", "none", "auto", "hyphens", "hyphens-auto-run", "hyphens_auto_run", 414, "bind", "Auto",
     "`hyphens:auto` allows hyphen breaks so OCR BIND… is a different wrap.", "Not extra8 hyphenate-eq, not extra7 hyphens-off.", "auto hyphens are live. File the a11y string."),
    ("visibility", "visible", "collapse", "visibility", "vis-collapse-run", "vis_collapse_run", 410, "chiphole", "Collapse",
     "`visibility:collapse` unpaints the chip. Stored visible x is a hole.", "Not extra7 vis-hidden-chip, not extra10 cv-hidden-run.", "collapse is still the chip if you use the ref."),
    ("contain", "none", "paint", "contain", "contain-paint-run", "contain_paint_run", 404, "cardhole", "Paint",
     "`contain:paint` clips descendants. Stored none x is a hole.", "Not extra10 contain-strict-run, not extra8 contain-inline.", "contain:paint is live. Keep CD-3 by ref."),
    ("will-change", "auto", "contents", "willChange", "will-change-contents-run", "will_change_contents_run", 412, "cards", "Will contents",
     "`will-change:contents` promotes a layer so stored auto x is a different compositor box.", "Not extra10 will-change-scroll-run, not extra8 will-change-transform.", "will-change:contents is live. Keep CD-3 by ref."),
    ("user-select", "auto", "none", "userSelect", "us-none-run", "us_none_run", 413, "labels", "None",
     "`user-select:none` forbids highlight so OCR of a spilled selection is LB-3.", "Not extra8 us-contain-select, not r user-select-none mill.", "none is not contain. File the a11y string."),
    ("pointer-events", "auto", "visiblePainted", "pointerEvents", "pe-visible-painted", "pe_visible_painted", 410, "chips", "VisiblePainted",
     "`pointer-events:visiblePainted` hits painted pixels only so a hole click falls through to CH-3.", "Not extra10 pe-stroke-run, not extra8 pointer-events-none.", "visiblePainted is not stroke. Keep CH-2 by ref."),
    ("resize", "none", "vertical", "resize", "resize-vertical-run", "resize_vertical_run", 410, "cards", "Vertical",
     "`resize:vertical` grows y so stored none y is CD-4.", "Not extra10 resize-horizontal-run, not extra8 resize-both-box.", "vertical is not horizontal. Keep CD-3 by ref."),
    ("float", "none", "inline-start", "float", "float-inline-start-run", "float_inline_start_run", 412, "floats", "Inline-start",
     "`float:inline-start` packs to the start so stored none x is FL-4.", "Not extra10 float-right-run, not extra9 float-none.", "inline-start is live. Keep FL-3 by ref."),
    ("clear", "none", "both", "clear", "clear-both-run", "clear_both_run", 410, "floats", "Clear both",
     "`clear:both` drops below floats so stored none y is FL-4.", "Not extra10 clear-right-run, not extra9 clear-left.", "clear:both is live. Keep FL-3 by ref."),
    ("vertical-align", "baseline", "text-bottom", "verticalAlign", "valign-text-bottom", "valign_text_bottom", 410, "glyphs", "Text-bottom",
     "`vertical-align:text-bottom` drops glyphs so stored baseline y is GL-3.", "Not extra10 valign-text-top, not extra8 valign-super.", "text-bottom is not text-top. Keep GL-2 by ref."),
    ("quotes", "auto", "none", "quotes", "quotes-none-run", "quotes_none_run", 415, "text", "None",
     "`quotes:none` unpaints quote glyphs so OCR of neighboring text is TX-5.", "Not extra8 quotes-custom, not extra7 quotes-none mill clone.", "Missing quotes are still TX-2. File the a11y string."),
    ("caption-side", "top", "inline-start", "captionSide", "caption-istart", "caption_istart", 412, "rows", "Inline-start",
     "`caption-side:inline-start` slides the caption so stored top x is RW-3.", "Not extra10 caption-top-run, not extra9 caption-bottom.", "inline-start caption is live. Keep RW-2 by ref."),
    ("empty-cells", "show", "hide", "emptyCells", "empty-hide-run", "empty_hide_run", 404, "chiphole", "Hide empty",
     "`empty-cells:hide` unpaints an empty cell. Stored show x is a hole.", "Not extra10 empty-show, not extra9 empty-hide.", "Hidden empty cells are still the chip if you use the ref."),
    ("border-radius", "0px", "8px", "borderRadius", "radius-8", "radius_8", 404, "chiphole", "Radius 8",
     "`border-radius:8px` makes corner holes. Stored square x is empty.", "Not extra8 radius-full, not extra8 radius-tl-24.", "An 8px radius hole is still the chip if you use the ref."),
    ("outline-offset", "0px", "4px", "outlineOffset", "outline-offset-4", "outline_offset_4", 404, "floats", "Offset 4",
     "`outline-offset:4px` pushes UA chrome out so a screenshot ring is not FL-3.", "Not extra8 outline-offset-12, not extra10 outline-width-1.", "4px offset outline is paint. Keep the float ref."),
    ("scroll-margin-top", "0px", "24px", "scrollMarginTop", "scroll-mar-top", "scroll_mar_top", 425, "lanes", "Margin top 24",
     "`scroll-margin-top:24px` pads snap so stored 0-margin y is LN-6.", "Not extra8 scroll-mar-left, not extra8 scroll-margin-istart.", "Physical scroll-margin-top is live. Keep the on-screen item ref."),
    ("scroll-padding-left", "0px", "24px", "scrollPaddingLeft", "scroll-pad-left", "scroll_pad_left", 425, "lanes", "Pad left 24",
     "`scroll-padding-left:24px` insets the scrollport so stored 0-pad x is LN-6.", "Not extra8 scroll-pad-top, not extra8 scroll-padding-istart.", "Physical scroll-padding-left is live. Keep the on-screen item ref."),
    ("mask-size", "auto", "50%", "maskSize", "mask-size-50", "mask_size_50", 404, "cardhole", "Mask 50",
     "`mask-size:50%` shrinks the mask. Stored auto x is a hole.", "Not extra10 mask-size-cover, not extra9 mask-size-contain.", "A 50% mask hole is still the card ref."),
    ("clip-path", "none", "circle(40%)", "clipPath", "clip-path-circle-40", "clip_path_circle_40", 404, "cardhole", "Circle 40",
     "`clip-path:circle(40%)` cuts the card. Stored none x is a hole.", "Not extra10 clip-path-inset-8, not extra9 clip-path-ellipse-80.", "A circle clip is still the card ref."),
    ("perspective", "none", "400px", "perspective", "perspective-400", "perspective_400", 520, "cards", "Persp 400",
     "`perspective:400px` foreshortens children so stored none x misses.", "Not extra9 perspective-200, not extra10 perspective-none-run.", "400px perspective is live. Keep CD-3 by ref."),
    ("place-items", "stretch", "center", "placeItems", "place-items-center-run", "place_items_center_run", 412, "cards", "Items center",
     "`place-items:center` packs each cell so stored stretch x is CD-4.", "Not extra10 place-items-end, not extra9 place-items-start.", "place-items center is live. Keep CD-3 by ref."),
    ("align-content", "stretch", "center", "alignContent", "align-content-center-run", "align_content_center_run", 410, "cards", "Content center",
     "`align-content:center` packs rows so stored stretch y is CD-4.", "Not extra10 align-content-end, not extra9 align-content-start.", "align-content center is live. Keep CD-3 by ref."),
    ("gap", "0px", "32px", "gap", "gap-32", "gap_32", 412, "chips", "Gap 32",
     "`gap:32px` restacks both axes so stored 0-gap x is CH-3.", "Not extra11 gap-16, not extra9 gap-24.", "gap 32 is not 16. Keep CH-2 by ref."),
    ("inset", "0px", "8px", "inset", "inset-sh-8", "inset_sh_8", 412, "abspos", "Inset 8",
     "`inset:8px` slides abspos so stored 0 x is empty.", "Not extra10 inset-sh-0, not extra9 inset-sh-24.", "inset 8 is live. Keep AB-2 by ref."),
    ("max-lines", "none", "5", "maxLines", "max-lines-5", "max_lines_5", 414, "bind", "Max 5",
     "`max-lines:5` clamps so OCR BIND… is a different wrap.", "Not extra10 max-lines-4, not extra9 max-lines-3.", "max-lines 5 is not 4. File the a11y string."),
    ("image-resolution", "from-image", "96dpi", "imageResolution", "image-res-96", "image_res_96", 404, "badges", "96dpi",
     "`image-resolution:96dpi` retimes the replaced box so stored from-image x is empty.", "Not extra10 image-res-72, not extra8 image-res-300.", "96dpi is not 72. Keep the badge ref."),
    ("font-family", "sans-serif", "ui-rounded", "fontFamily", "font-family-rounded", "font_family_rounded", 412, "glyphs", "Rounded",
     "`font-family:ui-rounded` retimes advances so stored sans x is GL-3.", "Not extra10 font-family-cursive, not extra8 font-family-mono.", "Rounded metrics are live. Keep GL-2 by ref."),
    ("opacity", "1", "0.1", "opacity", "opacity-01", "opacity_01", 464, "blends", "Opacity 0.1",
     "`opacity:0.1` fades so a screenshot looks empty.", "Not extra10 opacity-04, not extra8 opacity-0.", "0.1 is not unselected. Keep aria-selected / the ref."),
    ("mix-blend-mode", "normal", "screen", "mixBlendMode", "blend-screen-run", "blend_screen_run", 464, "blends", "Screen",
     "`mix-blend-mode:screen` blows the selected chip so a screenshot looks empty.", "Not extra11 blend-overlay-run, not extra6 bg-blend-screen.", "screen is not empty. Keep aria-selected / the ref."),
    ("cursor", "auto", "zoom-in", "cursor", "cursor-zoom-in-run", "cursor_zoom_in_run", 404, "chips", "Zoom-in",
     "`cursor:zoom-in` paints a plus glyph over CH-2. Screenshot of the glyph is not CH-3.", "Not extra8 cursor-zoom-in, not extra11 cursor-pointer.", "The zoom-in cursor is paint. Keep the chip ref."),
    ("display", "block", "flow-root", "display", "display-flow-root-run", "display_flow_root_run", 412, "chips", "Flow-root",
     "`display:flow-root` creates a BFC so stored block x is CH-3.", "Not extra11 display-inline-block-run, not extra mill display-flow-root.", "flow-root is live. Keep CH-2 by ref."),
    ("writing-mode", "horizontal-tb", "vertical-lr", "writingMode", "writing-vertical-lr-run", "writing_vertical_lr_run", 416, "text", "Vertical lr",
     "`writing-mode:vertical-lr` stacks so stored horizontal x is TX-5.", "Not extra8 writing-sideways-rl, not extra6 vertical-rl.", "vertical-lr is not sideways-rl. Keep TX-2 by ref."),
    ("unicode-bidi", "normal", "plaintext", "unicodeBidi", "bidi-plaintext-run", "bidi_plaintext_run", 416, "text", "Plaintext",
     "`unicode-bidi:plaintext` infers direction so stored normal x is TX-5.", "Not extra10 bidi-embed, not extra8 bidi-isolate.", "plaintext is not embed. Keep TX-2 by ref."),
    ("direction", "ltr", "rtl", "direction", "direction-rtl-x11", "direction_rtl_x11", 416, "text", "RTL",
     "`direction:rtl` flips so stored ltr x is TX-5.", "Not extra10 direction-rtl-run, not extra9 direction-ltr.", "rtl is live. Keep TX-2 by ref."),
    ("isolation", "auto", "isolate", "isolation", "isolation-isolate-x11", "isolation_isolate_x11", 464, "blends", "Isolate",
     "`isolation:isolate` creates a stacking root so stored auto blend looks unselected.", "Not extra10 isolation-isolate-run, not extra9 isolation-auto-run.", "isolate is not auto. Keep aria-selected / the ref."),
    ("content-visibility", "visible", "auto", "contentVisibility", "cv-auto-x11", "cv_auto_x11", 410, "rows", "Auto",
     "`content-visibility:auto` skips offscreen rows so stale scrollY lands empty.", "Not extra10 cv-hidden-run, not extra8 cv-auto.", "auto virtualize is live. Re-find the row ref."),
    ("white-space", "normal", "break-spaces", "whiteSpace", "ws-break-spaces-run", "ws_break_spaces_run", 413, "labels", "Break-spaces",
     "`white-space:break-spaces` preserves and wraps runs so a normal wrap line is LB-3.", "Not extra8 ws-pre-line, not extra10 ws-pre-wrap-run.", "break-spaces is not pre-wrap. File the a11y string."),
    ("word-break", "normal", "break-all", "wordBreak", "break-all-run", "break_all_run", 400, "labels", "Break-all",
     "`word-break:break-all` allows mid-word wraps so OCR BIND… is a different wrap.", "Not extra10 word-break-normal-run, not extra8 break-auto-phrase.", "break-all is not normal. File the a11y string."),
    ("line-break", "auto", "strict", "lineBreak", "line-break-strict", "line_break_strict", 400, "labels", "Strict",
     "`line-break:strict` forbids some CJK breaks so OCR BIND… is a different wrap.", "Not extra8 line-break-any, not extra10 overflow-wrap-normal-run.", "strict is not anywhere. File the a11y string."),
    ("hyphenate-character", "auto", "'*'", "hyphenateCharacter", "hyphenate-star", "hyphenate_star", 414, "bind", "Hyphen *",
     "`hyphenate-character:'*'` paints a star at the break so OCR BIND… is a different wrap.", "Not extra8 hyphenate-eq, not extra10 hyphenate-zone-0.", "A star hyphen is not auto. File the a11y string."),
    ("text-wrap", "wrap", "balance", "textWrap", "text-wrap-balance-run", "text_wrap_balance_run", 414, "bind", "Balance",
     "`text-wrap:balance` rebalances so OCR BIND… is a different wrap.", "Not extra8 text-wrap-nowrap, not extra6 text-wrap-pretty.", "balance is not nowrap. File the a11y string."),
    ("object-position", "50% 50%", "50% 100%", "objectPosition", "object-pos-bottom", "object_pos_bottom", 404, "badges", "Pos bottom",
     "`object-position:50% 100%` slides the replaced box so stored center y is empty.", "Not extra10 object-pos-right, not extra9 object-pos-left.", "Bottom object-position is paint. Keep the badge ref."),
    ("background-clip", "border-box", "content-box", "backgroundClip", "bg-clip-content", "bg_clip_content", 404, "badges", "Clip content",
     "`background-clip:content-box` insets the blob so stored border-box x is empty.", "Not extra10 bg-clip-padding, not extra9 background-clip-text.", "content-box clip is paint. Keep the badge ref."),
    ("box-shadow", "none", "0 8px 0 CanvasText", "boxShadow", "box-shadow-y8", "box_shadow_y8", 404, "chips", "Offset y 8",
     "`box-shadow:0 8px 0` paints a sibling blob. A click on the shadow is not CH-2.", "Not extra10 box-shadow-xy, not extra9 box-shadow-inset.", "Y offset shadow is paint. Keep the chip ref."),
    ("filter", "none", "saturate(0)", "filter", "filter-saturate-0", "filter_saturate_0", 415, "cards", "Saturate 0",
     "`filter:saturate(0)` greys paint so a screenshot blob is not CD-3.", "Not extra9 backdrop-saturate, not extra10 filter-contrast-2.", "Saturate 0 is paint. Keep CD-3 by ref."),
    ("accent-color", "auto", "CanvasText", "accentColor", "accent-canvastext", "accent_canvastext", 464, "blends", "Accent CanvasText",
     "`accent-color:CanvasText` remaps the checked fill so a screenshot looks empty.", "Not extra10 accent-current, not extra9 accent-canvas.", "CanvasText accent is not unchecked. Keep aria-checked / the ref."),
    ("caret-color", "auto", "currentColor", "caretColor", "caret-current", "caret_current", 415, "chips", "Caret current",
     "`caret-color:currentColor` paints a caret that covers CH-3. A blink-off screenshot looks empty.", "Not extra10 caret-transparent-run, not extra9 caret-canvas.", "currentColor caret is paint. Keep the chip ref."),
    ("scrollbar-width", "auto", "none", "scrollbarWidth", "scrollbar-none-x11", "scrollbar_none_x11", 425, "lanes", "Width none",
     "`scrollbar-width:none` frees the gutter so stored auto x is LN-6.", "Not extra10 scrollbar-width-thin, not extra9 scrollbar-width-none.", "none is not thin. Keep the on-screen item ref."),
    ("touch-action", "auto", "pan-right", "touchAction", "touch-pan-right", "touch_pan_right", 425, "lanes", "Pan right",
     "`touch-action:pan-right` forbids left pans so stored auto x is LN-6.", "Not extra10 touch-pan-left, not extra9 touch-pan-y.", "pan-right is not pan-left. Keep the on-screen item ref."),
    ("overscroll-behavior", "auto", "contain", "overscrollBehavior", "overscroll-contain-run", "overscroll_contain_run", 425, "lanes", "Overscroll contain",
     "`overscroll-behavior:contain` kills the scroll chain so stored auto x is LN-6.", "Not extra10 overscroll-auto-run, not extra9 overscroll-none.", "contain is not auto. Keep the on-screen item ref."),
    ("scroll-snap-stop", "normal", "always", "scrollSnapStop", "snap-stop-always-x11", "snap_stop_always_x11", 425, "lanes", "Stop always",
     "`scroll-snap-stop:always` forces each snap so stored normal x is LN-6.", "Not extra10 snap-stop-normal, not extra9 snap-stop-always.", "always stop is live. Keep the on-screen item ref."),
    ("field-sizing", "fixed", "content", "fieldSizing", "field-sizing-content-x11", "field_sizing_content_x11", 428, "chips", "Content",
     "`field-sizing:content` grows the control so stored fixed x is CH-3.", "Not extra10 field-sizing-fixed-run, not extra9 field-sizing-content.", "content field-sizing is live. Keep CH-2 by ref."),
    ("print-color-adjust", "economy", "exact", "printColorAdjust", "print-exact-x11", "print_exact_x11", 415, "badges", "Exact",
     "`print-color-adjust:exact` vs economy so a print screenshot luminance blob is not the badge.", "Not extra10 print-economy, not extra9 print-exact.", "exact print color is paint. Keep the badge ref."),
    ("math-shift", "normal", "compact", "mathShift", "math-shift-compact-x11", "math_shift_compact_x11", 418, "eq", "Shift compact",
     "`math-shift:compact` tucks superscripts so stored normal x is EQ-5.", "Not extra10 math-shift-normal, not extra9 math-shift-compact.", "compact math-shift is a used box. File EQ-4 by ref."),
    ("grid-auto-columns", "auto", "120px", "gridAutoColumns", "grid-auto-cols-120", "grid_auto_cols_120", 428, "cards", "Auto cols 120",
     "`grid-auto-columns:120px` sizes implicit cols so stored auto x is CD-4.", "Not extra9 grid-auto-cols, not extra10 grid-auto-rows-80.", "auto-columns 120 is live. Keep CD-3 by ref."),
    ("masonry-auto-flow", "pack", "definite-first", "masonryAutoFlow", "masonry-definite", "masonry_definite", 428, "cards", "Definite-first",
     "`masonry-auto-flow:definite-first` packs definite items first so stored pack x is CD-4.", "Not extra10 masonry-pack, not extra9 masonry-auto.", "definite-first is live. Keep CD-3 by ref."),
    ("position-area", "none", "center", "positionArea", "position-area-center", "position_area_center", 507, "abspos", "Area center",
     "`position-area:center` slots abspos into the center so stored none x is empty.", "Not extra10 position-area-end, not extra9 position-area-start.", "position-area center is live. Keep AB-2 by ref."),
    ("anchor-size", "auto", "closest", "anchorSize", "anchor-size-closest", "anchor_size_closest", 507, "floats", "Size closest",
     "`anchor-size:closest` sizes abspos from the closest anchor so stored auto size x is File.", "Not extra8 anchor-size-chip, not extra8 position-try-flip.", "closest anchor-size is live. Re-find the invoker or use the ref."),
    ("view-transition-name", "none", "chip", "viewTransitionName", "view-trans-chip", "view_trans_chip", 412, "cards", "Name chip",
     "`view-transition-name:chip` snapshots the old box so a click during the morph hits CD-4.", "Not extra8 view-trans-named, not extra8 view-trans-class.", "Named chip transitions are not the live ref. Keep CD-3 by ref."),
    ("animation-name", "none", "nudge-y", "animationName", "anim-name-nudge-y", "anim_name_nudge_y", 410, "chips", "Nudge y",
     "`animation-name:nudge-y` translates the chip so stored none y is CH-3.", "Not extra8 anim-name-nudge, not extra8 anim-range-start.", "Named y animation is live. Keep CH-2 by ref."),
    ("transition", "none", "opacity 200ms", "transition", "trans-opacity-200", "trans_opacity_200", 464, "blends", "Trans opacity 200",
     "`transition:opacity 200ms` leaves stored pre-transition paint looking unselected.", "Not extra8 trans-shorthand, not extra11 opacity-06.", "Opacity transition is live. Keep aria-selected / the ref."),
    ("offset-path", "none", "ray(0deg closest-side)", "offsetPath", "offset-path-ray", "offset_path_ray", 520, "by", "Ray path",
     "`offset-path:ray(0deg closest-side)` parks abspos on the ray so stored none x is BY-6.", "Not extra10 offset-path-circle, not extra9 offset-path-arc.", "offset-path ray is live. Keep BY-5 by ref."),
    ("shape-margin", "0px", "8px", "shapeMargin", "shape-margin-8", "shape_margin_8", 412, "floats", "Shape margin 8",
     "`shape-margin:8px` pushes wrap so stored 0 x is FL-4.", "Not extra10 shape-margin-0, not extra9 shape-margin-16.", "8px shape-margin is live. Keep FL-3 by ref."),
    ("text-emphasis-style", "none", "sesame", "textEmphasisStyle", "emphasis-sesame", "emphasis_sesame", 404, "glyphs", "Sesame",
     "`text-emphasis-style:sesame` paints marks above. A click on a mark is not GL-2.", "Not extra10 emphasis-circle, not extra9 emphasis-dot.", "Sesame marks are paint. Keep the glyph ref."),
    ("ruby-position", "alternate", "inter-character", "rubyPosition", "ruby-pos-inter", "ruby_pos_inter", 416, "glyphs", "Inter-character",
     "`ruby-position:inter-character` parks annotation between glyphs so stored alternate x is GL-3.", "Not extra10 ruby-pos-under, not extra9 ruby-pos-over.", "inter-character ruby is live. Keep GL-2 by ref."),
    ("font-stretch", "normal", "ultra-condensed", "fontStretch", "font-stretch-ultracond", "font_stretch_ultracond", 412, "glyphs", "Ultra-condensed",
     "`font-stretch:ultra-condensed` narrows glyphs so stored normal x is GL-3.", "Not extra10 font-stretch-cond, not extra9 font-stretch-exp.", "ultra-condensed is live. Keep GL-2 by ref."),
    ("font-variant-numeric", "normal", "tabular-nums", "fontVariantNumeric", "font-var-tabular", "font_var_tabular", 412, "glyphs", "Tabular",
     "`font-variant-numeric:tabular-nums` equalizes digit widths so stored normal x is GL-3.", "Not extra10 font-var-lining, not extra9 font-var-oldstyle.", "tabular nums are live. Keep GL-2 by ref."),
    ("hanging-punctuation", "none", "last", "hangingPunctuation", "hanging-last-run", "hanging_last_run", 416, "text", "Last",
     "`hanging-punctuation:last` hangs the stop so stored none x is TX-5.", "Not extra10 hanging-first-force, not extra9 hanging-force-end.", "last is not first force-end. Keep TX-2 by ref."),
    ("text-indent", "0px", "40px", "textIndent", "text-indent-40", "text_indent_40", 412, "text", "Indent 40",
     "`text-indent:40px` slides the first line so stored 0 x is TX-5.", "Not extra10 text-indent-neg, not extra9 text-indent-24.", "40px indent is not 24. Keep TX-2 by ref."),
    ("tab-size", "8", "1", "tabSize", "tab-size-1", "tab_size_1", 413, "labels", "Tab 1",
     "`tab-size:1` retimes tab stops so a stored tab-8 wrap line is LB-3.", "Not extra10 tab-size-2, not extra9 tab-size-4.", "tab-size 1 is live. File the a11y string."),
    ("outline-width", "0px", "16px", "outlineWidth", "outline-width-16", "outline_width_16", 404, "floats", "Outline 16",
     "`outline-width:16px` fattens UA chrome. Screenshot of the ring is not FL-3.", "Not extra10 outline-width-1, not extra9 outline-width-8.", "16px outline is paint. Keep the float ref."),
    ("border-width", "0px", "4px", "borderWidth", "border-width-4", "border_width_4", 404, "chips", "Width 4",
     "`border-width:4px` grows a ring. Center click on the ring is not CH-2.", "Not extra8 border-width-8, not extra8 border-sh-8.", "A 4px border is paint. Keep the chip ref."),
    ("border-style", "none", "dotted", "borderStyle", "border-dotted", "border_dotted", 404, "chips", "Dotted",
     "`border-style:dotted` paints dots. A click in a gap is not CH-2.", "Not extra8 border-dashed, not extra8 border-current.", "Dots are paint. Keep the chip ref."),
    ("column-width", "auto", "20em", "columnWidth", "column-width-20em", "column_width_20em", 416, "text", "Width 20em",
     "`column-width:20em` fragments so stored auto x is TX-5.", "Not extra10 column-width-8em, not extra9 column-width-12em.", "20em is not 12em. Keep TX-2 by ref."),
    ("column-span", "none", "all", "columnSpan", "column-span-all-x11", "column_span_all_x11", 416, "text", "Span all",
     "`column-span:all` stretches across columns so stored none x is TX-5.", "Not extra10 column-span-none, not extra9 column-span-all.", "all is not none. Keep TX-2 by ref."),
    ("page", "auto", "wide", "page", "page-wide", "page_wide", 416, "text", "Wide",
     "`page:wide` reflows print fragmentation so stored auto x is TX-5.", "Not extra10 page-auto-run, not extra9 page-portrait.", "Named wide page is live. Keep TX-2 by ref."),
    ("break-after", "auto", "page", "breakAfter", "break-after-page-run", "break_after_page_run", 416, "text", "After page",
     "`break-after:page` forces a page break so stored auto x is TX-5.", "Not extra10 break-after-column, not extra9 break-before-column.", "break-after page is live. Keep TX-2 by ref."),
    ("reading-order", "0", "4", "readingOrder", "reading-order-4", "reading_order_4", 428, "cards", "Order 4",
     "`reading-order:4` restacks a11y order so stored 0 x is CD-4.", "Not extra10 reading-order-3, not extra9 reading-order-n1.", "reading-order 4 is not 3. Keep CD-3 by ref."),
    ("scroll-timeline-axis", "block", "y", "scrollTimelineAxis", "scroll-tl-y", "scroll_tl_y", 412, "chips", "Axis y",
     "`scroll-timeline-axis:y` drives the timeline from physical y so stored block x is CH-3.", "Not extra10 scroll-tl-x, not extra9 scroll-tl-block.", "Axis y is not x. Keep CH-2 by ref."),
    ("text-spacing-trim", "space-all", "trim-start", "textSpacingTrim", "text-spacing-trim-start", "text_spacing_trim_start", 412, "glyphs", "Trim start",
     "`text-spacing-trim:trim-start` eats leading CJK spacing so stored space-all x is GL-3.", "Not extra10 text-spacing-space-all, not extra9 text-spacing-trim-all.", "trim-start is live. Keep GL-2 by ref."),
    ("font-language-override", "normal", "JPN", "fontLanguageOverride", "font-lang-jpn", "font_lang_jpn", 412, "glyphs", "Lang JPN",
     "`font-language-override:JPN` swaps locl glyphs so stored normal x is GL-3.", "Not extra10 font-lang-normal, not extra9 font-lang-override.", "JPN language override is live. Keep GL-2 by ref."),
]

GENERA = [
    "amanita", "boletus", "cantharellus", "hydnum", "ramaria", "clavaria", "morchella", "gyromitra", "helvella", "peziza",
    "sarcoscypha", "aleuria", "scutellinia", "pyronema", "agaricus", "lepiota", "coprinus", "psathyrella", "inocybe", "cortinarius",
    "russula", "lactarius", "tricholoma", "armillaria", "pleurotus", "lentinula", "flammulina", "hypholoma", "stropharia", "panaeolus",
    "gymnopilus", "galerina", "conocybe", "bolbitius", "suillus", "leccinum", "tylopilus", "chalciporus", "gyroporus", "paxillus",
    "gomphidius", "chroogomphus", "scleroderma", "lycoperdon", "calvatia", "geastrum", "astraeus", "tulostoma", "cyathus", "crucibulum",
    "nidula", "sphaerobolus", "phallus", "mutinus", "clathrus", "ileodictyon", "anthurus", "laternea", "lysurus", "dictyophora",
    "calostoma", "elaphomyces", "tuber", "terfezia", "hydnotrya", "genea", "barssia", "choiromyces", "xanthoconium", "austroboletus",
    "fistulina", "grifola", "meripilus", "laetiporus", "fomitopsis", "ganoderma", "trametes", "stereum", "phaeolus", "inonotus",
    "phellinus", "porodaedalea", "fuscoporia", "coltricia", "onnia", "hydnellum", "sarcodon", "bankera", "phellodon", "boletopsis",
    "albatrellus", "scutiger", "polyporus", "neolentinus", "lentinus", "panus", "phyllotopsis", "schizophyllum", "auricularia", "exidia",
    "tremella", "tremellodendron", "calocera", "dacrymyces", "guepiniopsis",
    "dacryopinax", "pseudohydnum", "tremiscus", "phleogena", "sebacina", "tulasnella", "ceratobasidium",
]


def extra_used():
    used_w, used_es, used_pl, used_pr, used_ax, used_seed, used_err = (
        load_set("widgets"), load_set("errslugs"), load_set("places"),
        load_set("prefixes"), load_set("auxes"), load_set("seeds"), load_set("errs"),
    )
    for name in ("brw-mill-r395-extra8.py", "brw-mill-r395-extra9.py", "brw-mill-r395-extra10.py"):
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
            err = err + "_x11"
            if err in used_err:
                raise SystemExit(f"err collision {err}")
        used_err.add(err)
        item, neigh, fail, ref, nref, fref, x0, x1, y, title, path = T[tmpl]
        prefix = mint("".join(ch for ch in widget if ch.isalnum())[:4] or "ebp", used_pr)
        aux = mint(("".join(ch for ch in widget if ch.isalnum())[2:6] or "eba") + "x", used_ax)
        if prefix == aux:
            aux = mint(aux + "z", used_ax)
        genus = GENERA[i]
        ok, bad = genus + "lea", genus + "down"
        if ok in used_pl or bad in used_pl:
            ok, bad = genus + "mere", genus + "ford"
        if ok in used_pl or bad in used_pl or ok == bad:
            raise SystemExit(f"place collision {ok} {bad}")
        used_pl.add(ok); used_pl.add(bad)
        slug = f"{aux}-{code}"
        if slug in used_es:
            raise SystemExit(f"err_slug collision {slug}")
        used_es.add(slug)
        seed_ok, seed_bad = f"css-{widget}", f"css-{widget}-{code}"
        if seed_ok in used_seed or seed_bad in used_seed:
            seed_ok, seed_bad = f"css-{widget}-x11", f"css-{widget}-x11-{code}"
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
    out = HERE / "brw-mill-r395-extra11.py"
    lines = ['"""Leftover CSS plants r1068+."""', "KEYS = (",
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
