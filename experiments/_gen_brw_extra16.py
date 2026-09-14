#!/usr/bin/env python3
"""Generate leftover CSS extra16 plants after extra15 (ferns clough/dene)."""
from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
_ns: dict = {"__file__": str(HERE / "_gen_brw_extra13.py")}
exec((HERE / "_gen_brw_extra13.py").read_text().split("# leftover CSS:")[0], _ns)
T = _ns["T"]
KEYS = _ns["KEYS"]
keep_code = _ns["keep_code"]
load_set = _ns["load_set"]
story = _ns["story"]


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


RAW: list[tuple] = []


def add(css, fr, to, js, widget, err, code, tmpl, btn):
    RAW.append((css, fr, to, js, widget, err, code, tmpl, btn))


for px in (6, 25, 27, 29, 31, 33, 35, 37, 39, 41, 43, 45, 46, 50, 54, 58, 62, 68, 76, 88):
    add("font-size", "16px", f"{px}px", "fontSize", f"font-size-{px}", f"font_size_{px}", 412, "glyphs", f"Size {px}")
for to, slug in (("0.12", "012"), ("0.18", "018"), ("0.22", "022"), ("0.28", "028"), ("0.32", "032"),
                 ("0.38", "038"), ("0.42", "042"), ("0.48", "048"), ("0.52", "052"), ("0.58", "058"),
                 ("0.62", "062"), ("0.68", "068"), ("0.72", "072"), ("0.78", "078"), ("0.82", "082"),
                 ("0.88", "088"), ("0.92", "092"), ("1.05", "105"), ("1.35", "135"), ("1.6", "16"),
                 ("1.8", "18"), ("2.2", "22"), ("3.5", "35"), ("7", "7"), ("9", "9")):
    add("zoom", "1", to, "zoom", f"zoom-{slug}-x16", f"zoom_{slug}_x16", 412, "cards", f"Zoom {to}")
for to, slug in (("0.05", "005"), ("0.14", "014"), ("0.16", "016"), ("0.24", "024"), ("0.26", "026"),
                 ("0.32", "032"), ("0.38", "038"), ("0.48", "048"), ("0.52", "052"), ("0.58", "058"),
                 ("0.68", "068"), ("0.72", "072"), ("0.82", "082"), ("0.88", "088"), ("0.94", "094")):
    add("opacity", "1", to, "opacity", f"opacity-{slug}-x16", f"opacity_{slug}_x16", 464, "blends", f"Opacity {to}")
for to, slug in (("0.12", "012"), ("0.18", "018"), ("0.22", "022"), ("0.28", "028"), ("0.32", "032"),
                 ("0.38", "038"), ("0.42", "042"), ("0.48", "048"), ("0.52", "052"), ("0.58", "058"),
                 ("0.62", "062"), ("0.68", "068"), ("0.72", "072"), ("0.78", "078"), ("0.82", "082"),
                 ("0.88", "088"), ("0.92", "092"), ("1.05", "105"), ("1.35", "135"), ("1.6", "16"),
                 ("1.8", "18"), ("2.2", "22"), ("3.5", "35"), ("7", "7"), ("9", "9")):
    add("scale", "1", to, "scale", f"scale-{slug}-x16", f"scale_{slug}_x16", 412, "cards", f"Scale {to}")
for axis, deg in (("x", 4), ("x", 12), ("x", 18), ("x", 36), ("x", 75),
                  ("y", 4), ("y", 12), ("y", 18), ("y", 36), ("y", 75),
                  ("z", 10), ("z", 18), ("z", 36), ("z", 75), ("z", 90)):
    add("rotate", "0deg", f"{axis} {deg}deg", "rotate", f"rotate-{axis}-{deg}-x16",
        f"rotate_{axis}_{deg}_x16", 520, "cards", f"Rotate {axis.upper()} {deg}")
for axis, px, code, tmpl in (("x", 6, 412, "abspos"), ("x", 10, 412, "abspos"), ("x", 20, 412, "abspos"),
                             ("x", 28, 412, "abspos"), ("x", 36, 412, "abspos"),
                             ("y", 6, 410, "abspos"), ("y", 10, 410, "abspos"), ("y", 20, 410, "abspos"),
                             ("y", 28, 410, "abspos"), ("y", 36, 410, "abspos"),
                             ("z", 6, 520, "cards"), ("z", 10, 520, "cards"), ("z", 20, 520, "cards"),
                             ("z", 28, 520, "cards"), ("z", 36, 520, "cards")):
    to = f"{px}px 0px" if axis == "x" else (f"0px {px}px" if axis == "y" else f"0px 0px {px}px")
    add("translate", "0px", to, "translate", f"translate-{axis}-{px}-x16",
        f"translate_{axis}_{px}_x16", code, tmpl, f"Translate {axis} {px}")
add("gap", "0px", "5px", "gap", "gap-5", "gap_5", 412, "chips", "Gap 5")
add("gap", "0px", "7px", "gap", "gap-7", "gap_7", 412, "chips", "Gap 7")
add("gap", "0px", "9px", "gap", "gap-9", "gap_9", 412, "chips", "Gap 9")
add("gap", "0px", "14px", "gap", "gap-14", "gap_14", 412, "chips", "Gap 14")
add("gap", "0px", "18px", "gap", "gap-18", "gap_18", 412, "chips", "Gap 18")
add("gap", "0px", "28px", "gap", "gap-28", "gap_28", 412, "chips", "Gap 28")
add("gap", "0px", "40px", "gap", "gap-40", "gap_40", 412, "chips", "Gap 40")
add("gap", "0px", "56px", "gap", "gap-56", "gap_56", 412, "chips", "Gap 56")
add("flex-grow", "0", "7", "flexGrow", "flex-grow-7", "flex_grow_7", 428, "chips", "Grow 7")
add("flex-grow", "0", "9", "flexGrow", "flex-grow-9", "flex_grow_9", 428, "chips", "Grow 9")
add("flex-shrink", "1", "4", "flexShrink", "flex-shrink-4", "flex_shrink_4", 428, "chips", "Shrink 4")
add("flex-shrink", "1", "5", "flexShrink", "flex-shrink-5", "flex_shrink_5", 428, "chips", "Shrink 5")
add("order", "0", "6", "order", "order-6", "order_6", 428, "chips", "Order 6")
add("order", "0", "7", "order", "order-7", "order_7", 428, "chips", "Order 7")
add("order", "0", "-4", "order", "order-n4", "order_n4", 428, "chips", "Order -4")
add("z-index", "auto", "7", "zIndex", "z-index-7", "z_index_7", 403, "chips", "Z 7")
add("z-index", "auto", "9", "zIndex", "z-index-9", "z_index_9", 403, "chips", "Z 9")
add("z-index", "auto", "12", "zIndex", "z-index-12", "z_index_12", 403, "chips", "Z 12")
add("z-index", "auto", "-4", "zIndex", "z-index-neg4", "z_index_neg4", 403, "chips", "Z -4")
add("column-count", "auto", "9", "columnCount", "column-count-9", "column_count_9", 416, "text", "Count 9")
add("column-count", "auto", "10", "columnCount", "column-count-10", "column_count_10", 416, "text", "Count 10")
add("letter-spacing", "normal", "0.15em", "letterSpacing", "letter-spacing-015em", "letter_spacing_015em", 412, "glyphs", "Tracking 0.15em")
add("letter-spacing", "normal", "0.25em", "letterSpacing", "letter-spacing-025em", "letter_spacing_025em", 412, "glyphs", "Tracking 0.25em")
add("letter-spacing", "normal", "2px", "letterSpacing", "letter-spacing-2px", "letter_spacing_2px", 412, "glyphs", "Tracking 2px")
add("word-spacing", "normal", "0.3em", "wordSpacing", "word-spacing-03em", "word_spacing_03em", 412, "glyphs", "Word 0.3em")
add("word-spacing", "normal", "0.6em", "wordSpacing", "word-spacing-06em", "word_spacing_06em", 412, "glyphs", "Word 0.6em")
add("line-height", "normal", "0.7", "lineHeight", "line-height-07", "line_height_07", 410, "rows", "Line 0.7")
add("line-height", "normal", "1.05", "lineHeight", "line-height-105", "line_height_105", 410, "rows", "Line 1.05")
add("line-height", "normal", "1.35", "lineHeight", "line-height-135", "line_height_135", 410, "rows", "Line 1.35")
add("line-height", "normal", "5", "lineHeight", "line-height-5", "line_height_5", 410, "rows", "Line 5")
add("border-radius", "0px", "3px", "borderRadius", "radius-3", "radius_3", 404, "chiphole", "Radius 3")
add("border-radius", "0px", "10px", "borderRadius", "radius-10", "radius_10", 404, "chiphole", "Radius 10")
add("border-radius", "0px", "18px", "borderRadius", "radius-18", "radius_18", 404, "chiphole", "Radius 18")
add("border-radius", "0px", "28px", "borderRadius", "radius-28", "radius_28", 404, "chiphole", "Radius 28")
add("border-radius", "0px", "40px", "borderRadius", "radius-40", "radius_40", 404, "chiphole", "Radius 40")
add("outline-offset", "0px", "3px", "outlineOffset", "outline-offset-3", "outline_offset_3", 404, "floats", "Offset 3")
add("outline-offset", "0px", "6px", "outlineOffset", "outline-offset-6", "outline_offset_6", 404, "floats", "Offset 6")
add("outline-offset", "0px", "10px", "outlineOffset", "outline-offset-10", "outline_offset_10", 404, "floats", "Offset 10")
add("outline-offset", "0px", "40px", "outlineOffset", "outline-offset-40", "outline_offset_40", 404, "floats", "Offset 40")
add("border-width", "0px", "5px", "borderWidth", "border-width-5", "border_width_5", 404, "chips", "Width 5")
add("border-width", "0px", "7px", "borderWidth", "border-width-7", "border_width_7", 404, "chips", "Width 7")
add("border-width", "0px", "14px", "borderWidth", "border-width-14", "border_width_14", 404, "chips", "Width 14")
add("border-width", "0px", "18px", "borderWidth", "border-width-18", "border_width_18", 404, "chips", "Width 18")
add("inset", "0px", "2px", "inset", "inset-sh-2", "inset_sh_2", 412, "abspos", "Inset 2")
add("inset", "0px", "10px", "inset", "inset-sh-10", "inset_sh_10", 412, "abspos", "Inset 10")
add("inset", "0px", "20px", "inset", "inset-sh-20", "inset_sh_20", 412, "abspos", "Inset 20")
add("inset", "0px", "40px", "inset", "inset-sh-40", "inset_sh_40", 412, "abspos", "Inset 40")
add("max-lines", "none", "11", "maxLines", "max-lines-11", "max_lines_11", 414, "bind", "Max 11")
add("max-lines", "none", "12", "maxLines", "max-lines-12", "max_lines_12", 414, "bind", "Max 12")
add("perspective", "none", "75px", "perspective", "perspective-75", "perspective_75", 520, "cards", "Persp 75")
add("perspective", "none", "150px", "perspective", "perspective-150", "perspective_150", 520, "cards", "Persp 150")
add("perspective", "none", "250px", "perspective", "perspective-250", "perspective_250", 520, "cards", "Persp 250")
add("perspective", "none", "600px", "perspective", "perspective-600", "perspective_600", 520, "cards", "Persp 600")
add("perspective", "none", "2000px", "perspective", "perspective-2000", "perspective_2000", 520, "cards", "Persp 2000")
add("clip-path", "none", "inset(16%)", "clipPath", "clip-path-inset-16", "clip_path_inset_16", 404, "cardhole", "Inset 16")
add("clip-path", "none", "circle(20%)", "clipPath", "clip-path-circle-20", "clip_path_circle_20", 404, "cardhole", "Circle 20")
add("clip-path", "none", "circle(60%)", "clipPath", "clip-path-circle-60", "clip_path_circle_60", 404, "cardhole", "Circle 60")
add("mask-size", "auto", "30%", "maskSize", "mask-size-30", "mask_size_30", 404, "cardhole", "Mask 30")
add("mask-size", "auto", "40%", "maskSize", "mask-size-40", "mask_size_40", 404, "cardhole", "Mask 40")
add("mask-size", "auto", "70%", "maskSize", "mask-size-70", "mask_size_70", 404, "cardhole", "Mask 70")
add("image-resolution", "from-image", "120dpi", "imageResolution", "image-res-120", "image_res_120", 404, "badges", "120dpi")
add("image-resolution", "from-image", "180dpi", "imageResolution", "image-res-180", "image_res_180", 404, "badges", "180dpi")
add("font-family", "sans-serif", "emoji", "fontFamily", "font-family-emoji-x16", "font_family_emoji_x16", 412, "glyphs", "Emoji")
add("font-family", "sans-serif", "fangsong", "fontFamily", "font-family-fangsong", "font_family_fangsong", 412, "glyphs", "Fangsong")
add("font-language-override", "normal", "THA", "fontLanguageOverride", "font-lang-tha", "font_lang_tha", 412, "glyphs", "Lang THA")
add("font-language-override", "normal", "ZHT", "fontLanguageOverride", "font-lang-zht", "font_lang_zht", 412, "glyphs", "Lang ZHT")
add("font-language-override", "normal", "VIE", "fontLanguageOverride", "font-lang-vie", "font_lang_vie", 412, "glyphs", "Lang VIE")
add("text-indent", "0px", "6px", "textIndent", "text-indent-6", "text_indent_6", 412, "text", "Indent 6")
add("text-indent", "0px", "10px", "textIndent", "text-indent-10", "text_indent_10", 412, "text", "Indent 10")
add("text-indent", "0px", "20px", "textIndent", "text-indent-20", "text_indent_20", 412, "text", "Indent 20")
add("text-indent", "0px", "48px", "textIndent", "text-indent-48", "text_indent_48", 412, "text", "Indent 48")
add("tab-size", "8", "7", "tabSize", "tab-size-7", "tab_size_7", 413, "labels", "Tab 7")
add("tab-size", "8", "9", "tabSize", "tab-size-9", "tab_size_9", 413, "labels", "Tab 9")
add("tab-size", "8", "12", "tabSize", "tab-size-12", "tab_size_12", 413, "labels", "Tab 12")
add("outline-width", "0px", "5px", "outlineWidth", "outline-width-5", "outline_width_5", 404, "floats", "Outline 5")
add("outline-width", "0px", "10px", "outlineWidth", "outline-width-10", "outline_width_10", 404, "floats", "Outline 10")
add("column-width", "auto", "5em", "columnWidth", "column-width-5em", "column_width_5em", 416, "text", "Width 5em")
add("column-width", "auto", "7em", "columnWidth", "column-width-7em", "column_width_7em", 416, "text", "Width 7em")
add("column-width", "auto", "16em", "columnWidth", "column-width-16em", "column_width_16em", 416, "text", "Width 16em")
add("reading-order", "0", "7", "readingOrder", "reading-order-7", "reading_order_7", 428, "cards", "Order 7")
add("reading-order", "0", "8", "readingOrder", "reading-order-8", "reading_order_8", 428, "cards", "Order 8")
add("grid-auto-columns", "auto", "24px", "gridAutoColumns", "grid-auto-cols-24", "grid_auto_cols_24", 428, "cards", "Auto cols 24")
add("grid-auto-columns", "auto", "60px", "gridAutoColumns", "grid-auto-cols-60", "grid_auto_cols_60", 428, "cards", "Auto cols 60")
add("grid-auto-rows", "auto", "24px", "gridAutoRows", "grid-auto-rows-24", "grid_auto_rows_24", 428, "cards", "Auto rows 24")
add("grid-auto-rows", "auto", "60px", "gridAutoRows", "grid-auto-rows-60", "grid_auto_rows_60", 428, "cards", "Auto rows 60")
add("row-gap", "0px", "6px", "rowGap", "row-gap-6", "row_gap_6", 410, "cards", "Row gap 6")
add("row-gap", "0px", "20px", "rowGap", "row-gap-20", "row_gap_20", 410, "cards", "Row gap 20")
add("column-gap", "0px", "6px", "columnGap", "column-gap-6", "column_gap_6", 412, "chips", "Col gap 6")
add("column-gap", "0px", "20px", "columnGap", "column-gap-20", "column_gap_20", 412, "chips", "Col gap 20")
add("flex-basis", "auto", "24px", "flexBasis", "flex-basis-24", "flex_basis_24", 428, "chips", "Basis 24")
add("flex-basis", "auto", "80px", "flexBasis", "flex-basis-80", "flex_basis_80", 428, "chips", "Basis 80")
add("aspect-ratio", "auto", "3 / 2", "aspectRatio", "aspect-ratio-32", "aspect_ratio_32", 428, "cards", "3/2")
add("aspect-ratio", "auto", "21 / 9", "aspectRatio", "aspect-ratio-219", "aspect_ratio_219", 428, "cards", "21/9")
add("aspect-ratio", "auto", "2 / 3", "aspectRatio", "aspect-ratio-23", "aspect_ratio_23", 428, "cards", "2/3")
add("line-clamp", "none", "3", "lineClamp", "line-clamp-3", "line_clamp_3", 414, "bind", "Clamp 3")
add("line-clamp", "none", "5", "lineClamp", "line-clamp-5", "line_clamp_5", 414, "bind", "Clamp 5")
add("line-clamp", "none", "9", "lineClamp", "line-clamp-9", "line_clamp_9", 414, "bind", "Clamp 9")
add("orphans", "2", "3", "orphans", "orphans-3", "orphans_3", 416, "text", "Orphans 3")
add("orphans", "2", "5", "orphans", "orphans-5", "orphans_5", 416, "text", "Orphans 5")
add("widows", "2", "3", "widows", "widows-3", "widows_3", 416, "text", "Widows 3")
add("widows", "2", "5", "widows", "widows-5", "widows_5", 416, "text", "Widows 5")
add("text-underline-offset", "auto", "2px", "textUnderlineOffset", "underline-offset-2", "underline_offset_2", 404, "glyphs", "Under 2")
add("text-underline-offset", "auto", "12px", "textUnderlineOffset", "underline-offset-12", "underline_offset_12", 404, "glyphs", "Under 12")
add("font-size-adjust", "none", "0.4", "fontSizeAdjust", "font-size-adjust-04", "font_size_adjust_04", 412, "glyphs", "Adjust 0.4")
add("font-size-adjust", "none", "0.6", "fontSizeAdjust", "font-size-adjust-06", "font_size_adjust_06", 412, "glyphs", "Adjust 0.6")
add("font-variation-settings", "normal", "'wght' 350", "fontVariationSettings", "font-var-wght-350", "font_var_wght_350", 412, "glyphs", "Wght 350")
add("font-variation-settings", "normal", "'slnt' -8", "fontVariationSettings", "font-var-slnt-n8", "font_var_slnt_n8", 412, "glyphs", "Slnt -8")
add("caret-shape", "auto", "block", "caretShape", "caret-shape-block-x16", "caret_shape_block_x16", 415, "chips", "Caret block")
add("scroll-behavior", "auto", "smooth", "scrollBehavior", "scroll-behavior-smooth-x16", "scroll_behavior_smooth_x16", 425, "lanes", "Smooth")
add("text-justify", "auto", "distribute", "textJustify", "text-justify-distribute", "text_justify_distribute", 412, "text", "Distribute")
add("text-align-last", "auto", "start", "textAlignLast", "text-align-last-start", "text_align_last_start", 412, "text", "Last start")
add("text-align-last", "auto", "end", "textAlignLast", "text-align-last-end", "text_align_last_end", 412, "text", "Last end")
add("color-scheme", "normal", "dark light", "colorScheme", "color-scheme-dark-light", "color_scheme_dark_light", 464, "blends", "Dark light")
add("filter", "none", "blur(2px)", "filter", "filter-blur-2", "filter_blur_2", 415, "cards", "Blur 2")
add("filter", "none", "blur(12px)", "filter", "filter-blur-12", "filter_blur_12", 415, "cards", "Blur 12")
add("filter", "none", "brightness(1.6)", "filter", "filter-brightness-16", "filter_brightness_16", 415, "cards", "Bright 1.6")
add("backdrop-filter", "none", "blur(2px)", "backdropFilter", "backdrop-blur-2", "backdrop_blur_2", 415, "cards", "Back blur 2")
add("backdrop-filter", "none", "blur(12px)", "backdropFilter", "backdrop-blur-12", "backdrop_blur_12", 415, "cards", "Back blur 12")
add("mix-blend-mode", "normal", "saturation", "mixBlendMode", "blend-saturation-x16", "blend_saturation_x16", 464, "blends", "Saturation")
add("box-shadow", "none", "6px 0 0 CanvasText", "boxShadow", "box-shadow-x6", "box_shadow_x6", 404, "chips", "Offset 6")
add("box-shadow", "none", "12px 0 0 CanvasText", "boxShadow", "box-shadow-x12", "box_shadow_x12", 404, "chips", "Offset 12")
add("box-shadow", "none", "40px 0 0 CanvasText", "boxShadow", "box-shadow-x40", "box_shadow_x40", 404, "chips", "Offset 40")
add("shape-margin", "0px", "6px", "shapeMargin", "shape-margin-6", "shape_margin_6", 412, "floats", "Shape margin 6")
add("shape-margin", "0px", "10px", "shapeMargin", "shape-margin-10", "shape_margin_10", 412, "floats", "Shape margin 10")
add("offset-distance", "0", "25%", "offsetDistance", "offset-distance-25", "offset_distance_25", 520, "by", "Distance 25")
add("offset-distance", "0", "75%", "offsetDistance", "offset-distance-75", "offset_distance_75", 520, "by", "Distance 75")
add("offset-rotate", "auto", "15deg", "offsetRotate", "offset-rotate-15", "offset_rotate_15", 520, "by", "Offset rot 15")
add("offset-rotate", "auto", "90deg", "offsetRotate", "offset-rotate-90", "offset_rotate_90", 520, "by", "Offset rot 90")
add("will-change", "auto", "right", "willChange", "will-change-right-x16", "will_change_right_x16", 412, "cards", "Will right")
add("will-change", "auto", "bottom", "willChange", "will-change-bottom-x16", "will_change_bottom_x16", 412, "cards", "Will bottom")
add("contain", "none", "paint style", "contain", "contain-paint-style-x16", "contain_paint_style_x16", 428, "chips", "Paint style")
add("content-visibility", "visible", "hidden", "contentVisibility", "cv-hidden-x16", "cv_hidden_x16", 410, "chiphole", "CV hidden")
add("font-stretch", "normal", "ultra-condensed", "fontStretch", "font-stretch-ultracond-x16", "font_stretch_ultracond_x16", 412, "glyphs", "Ultra condensed")
add("font-stretch", "normal", "semi-expanded", "fontStretch", "font-stretch-semiexp", "font_stretch_semiexp", 412, "glyphs", "Semi expanded")
add("font-width", "normal", "semi-condensed", "fontWidth", "font-width-semicond", "font_width_semicond", 412, "glyphs", "Width semicond")
add("text-emphasis-style", "none", "double-circle", "textEmphasisStyle", "emphasis-dblcircle-x16", "emphasis_dblcircle_x16", 404, "glyphs", "Double circle")
add("text-transform", "none", "full-size-kana", "textTransform", "text-transform-kana", "text_transform_kana", 412, "glyphs", "Kana")
add("hyphens", "none", "manual", "hyphens", "hyphens-manual-x16", "hyphens_manual_x16", 414, "bind", "Manual")
add("white-space", "normal", "pre-wrap", "whiteSpace", "ws-pre-wrap-x16", "ws_pre_wrap_x16", 413, "labels", "Pre-wrap")
add("overflow-wrap", "normal", "break-word", "overflowWrap", "overflow-wrap-bw-x16", "overflow_wrap_bw_x16", 414, "bind", "Break-word")
add("word-break", "normal", "break-word", "wordBreak", "word-break-word-x16", "word_break_word_x16", 414, "bind", "Break-word")
add("text-overflow", "clip", "ellipsis", "textOverflow", "text-overflow-ellip-x16", "text_overflow_ellip_x16", 414, "bind", "Ellipsis")
add("display", "block", "inline-table", "display", "display-inline-table-x16", "display_inline_table_x16", 412, "chips", "Inline-table")
add("display", "block", "ruby-text", "display", "display-ruby-text-x16", "display_ruby_text_x16", 416, "glyphs", "Ruby-text")
add("overflow-x", "visible", "auto", "overflowX", "overflow-x-auto-x16", "overflow_x_auto_x16", 425, "lanes", "Auto x")
add("overflow-y", "visible", "overlay", "overflowY", "overflow-y-overlay-x16", "overflow_y_overlay_x16", 425, "lanes", "Overlay y")
add("float", "none", "inline-start", "float", "float-inline-start-x16", "float_inline_start_x16", 412, "floats", "Inline start")
add("clear", "none", "inline-end", "clear", "clear-inline-end-x16", "clear_inline_end_x16", 410, "floats", "Clear iend")
add("vertical-align", "baseline", "text-bottom", "verticalAlign", "valign-text-bottom-x16", "valign_text_bottom_x16", 410, "glyphs", "Text-bottom")
add("place-items", "stretch", "center", "placeItems", "place-items-center-x16", "place_items_center_x16", 412, "cards", "Items center")
add("align-content", "start", "end", "alignContent", "align-content-end-x16", "align_content_end_x16", 410, "cards", "Content end")
add("pointer-events", "auto", "visibleStroke", "pointerEvents", "pe-visible-stroke-x16", "pe_visible_stroke_x16", 410, "chips", "Visible stroke")
add("user-select", "auto", "all", "userSelect", "us-all-x16", "us_all_x16", 413, "labels", "All")
add("resize", "none", "horizontal", "resize", "resize-horizontal-x16", "resize_horizontal_x16", 428, "cards", "Horizontal")
add("cursor", "auto", "not-allowed", "cursor", "cursor-not-allowed-x16", "cursor_not_allowed_x16", 404, "chips", "Not-allowed")
add("cursor", "auto", "grabbing", "cursor", "cursor-grabbing-x16", "cursor_grabbing_x16", 404, "chips", "Grabbing")
add("touch-action", "auto", "pinch-zoom", "touchAction", "touch-pinch-x16", "touch_pinch_x16", 425, "lanes", "Pinch")
add("overscroll-behavior", "auto", "none", "overscrollBehavior", "overscroll-none-x16", "overscroll_none_x16", 425, "lanes", "None")
add("scroll-snap-align", "none", "start", "scrollSnapAlign", "snap-align-start-x16", "snap_align_start_x16", 425, "lanes", "Align start")
add("scrollbar-width", "auto", "thin", "scrollbarWidth", "scrollbar-thin-x16", "scrollbar_thin_x16", 425, "lanes", "Thin")
add("object-fit", "cover", "scale-down", "objectFit", "object-fit-scale-down-x16", "object_fit_scale_down_x16", 404, "badges", "Scale-down")
add("object-position", "0 0", "75% 75%", "objectPosition", "object-pos-7575", "object_pos_7575", 404, "badges", "Pos 75")
add("background-clip", "border-box", "padding-box", "backgroundClip", "bg-clip-padding-x16", "bg_clip_padding_x16", 404, "badges", "Clip padding")
add("image-orientation", "from-image", "flip", "imageOrientation", "image-orient-flip-x16", "image_orient_flip_x16", 404, "badges", "Orient flip")
add("print-color-adjust", "economy", "exact", "printColorAdjust", "print-exact-x16", "print_exact_x16", 415, "badges", "Exact")
add("math-shift", "normal", "compact", "mathShift", "math-shift-compact-x16", "math_shift_compact_x16", 418, "eq", "Compact")
add("field-sizing", "fixed", "content", "fieldSizing", "field-sizing-content-x16", "field_sizing_content_x16", 428, "chips", "Content")
add("appearance", "none", "menulist", "appearance", "appearance-menulist-x16", "appearance_menulist_x16", 404, "chips", "Menulist")
add("accent-color", "auto", "CanvasText", "accentColor", "accent-canvastext-x16", "accent_canvastext_x16", 464, "blends", "Accent CanvasText")
add("caret-color", "auto", "currentColor", "caretColor", "caret-current-x16", "caret_current_x16", 415, "chips", "Caret current")
add("isolation", "auto", "isolate", "isolation", "isolation-isolate-x16", "isolation_isolate_x16", 464, "blends", "Isolate")
add("visibility", "visible", "hidden", "visibility", "vis-hidden-x16", "vis_hidden_x16", 410, "chiphole", "Hidden")
add("transform-origin", "50% 50%", "0 100%", "transformOrigin", "transform-origin-sw", "transform_origin_sw", 520, "cards", "Origin sw")
add("transform-style", "flat", "preserve-3d", "transformStyle", "transform-style-3d-x16", "transform_style_3d_x16", 520, "cards", "Preserve 3d")
add("backface-visibility", "visible", "hidden", "backfaceVisibility", "backface-hidden-x16", "backface_hidden_x16", 520, "cards", "Backface hidden")
add("writing-mode", "horizontal-tb", "vertical-rl", "writingMode", "writing-vertical-rl-x16", "writing_vertical_rl_x16", 416, "text", "Vertical rl")
add("text-orientation", "mixed", "sideways", "textOrientation", "text-orientation-side-x16", "text_orientation_side_x16", 416, "glyphs", "Sideways")
add("page", "auto", "narrow-x16", "page", "page-narrow-x16", "page_narrow_x16", 416, "text", "Narrow")
add("break-before", "auto", "column", "breakBefore", "break-before-column-x16", "break_before_column_x16", 416, "text", "Before column")
add("break-after", "auto", "avoid", "breakAfter", "break-after-avoid-x16", "break_after_avoid_x16", 416, "text", "After avoid")
add("view-transition-name", "none", "lane", "viewTransitionName", "view-trans-lane-x16", "view_trans_lane_x16", 412, "cards", "Name lane")
add("animation-name", "none", "pulse", "animationName", "anim-name-pulse-x16", "anim_name_pulse_x16", 412, "chips", "Pulse")
add("transition", "none", "height 200ms", "transition", "trans-height-200", "trans_height_200", 412, "chips", "Trans height 200")
add("offset-path", "none", "ray(0deg closest-side)", "offsetPath", "offset-path-ray-0", "offset_path_ray_0", 520, "by", "Ray 0")
add("position-area", "none", "start", "positionArea", "position-area-start-x16", "position_area_start_x16", 507, "abspos", "Area start")
add("anchor-size", "auto", "self-inline", "anchorSize", "anchor-size-self-inline", "anchor_size_self_inline", 507, "floats", "Self inline")
add("masonry-auto-flow", "pack", "next", "masonryAutoFlow", "masonry-next-x16", "masonry_next_x16", 428, "cards", "Next")
add("scroll-timeline-axis", "block", "inline", "scrollTimelineAxis", "scroll-tl-inline-x16", "scroll_tl_inline_x16", 412, "chips", "Axis inline")
add("text-spacing-trim", "space-all", "trim-start", "textSpacingTrim", "text-spacing-trim-start-x16", "text_spacing_trim_start_x16", 412, "glyphs", "Trim start")
add("hanging-punctuation", "none", "last", "hangingPunctuation", "hanging-last-x16", "hanging_last_x16", 416, "text", "Last")
add("ruby-position", "alternate", "under", "rubyPosition", "ruby-pos-under-x16", "ruby_pos_under_x16", 416, "glyphs", "Ruby under")
add("font-variant-numeric", "normal", "proportional-nums", "fontVariantNumeric", "font-var-propnums", "font_var_propnums", 412, "glyphs", "Prop nums")
add("list-style-type", "disc", "circle", "listStyleType", "list-type-circle-x16", "list_type_circle_x16", 449, "lists", "Circle")
add("quotes", "auto", "'“' '”'", "quotes", "quotes-curly-x16", "quotes_curly_x16", 415, "text", "Curly")
add("empty-cells", "show", "hide", "emptyCells", "empty-hide-x16", "empty_hide_x16", 428, "chips", "Hide")
add("caption-side", "top", "block-end", "captionSide", "caption-block-end-x16", "caption_block_end_x16", 410, "rows", "Block-end")
add("table-layout", "fixed", "auto", "tableLayout", "table-layout-auto-x16", "table_layout_auto_x16", 428, "chips", "Auto")
add("box-sizing", "border-box", "content-box", "boxSizing", "box-sizing-content-x16", "box_sizing_content_x16", 428, "chips", "Content-box")
add("overflow-anchor", "auto", "none", "overflowAnchor", "overflow-anchor-none-x16", "overflow_anchor_none_x16", 425, "lanes", "Anchor none")
add("scroll-snap-type", "none", "both mandatory", "scrollSnapType", "scroll-snap-both-mand", "scroll_snap_both_mand", 425, "lanes", "Both mandatory")
add("overscroll-behavior-x", "auto", "contain", "overscrollBehaviorX", "overscroll-x-contain-x16", "overscroll_x_contain_x16", 425, "lanes", "X contain")
add("scrollbar-gutter", "auto", "stable both-edges", "scrollbarGutter", "scrollbar-gutter-both-x16", "scrollbar_gutter_both_x16", 425, "lanes", "Both edges")
add("justify-content", "normal", "space-between", "justifyContent", "justify-between-x16", "justify_between_x16", 412, "chips", "Between")
add("align-items", "stretch", "end", "alignItems", "align-items-end-x16", "align_items_end_x16", 412, "chips", "Items end")
add("flex-direction", "row", "row-reverse", "flexDirection", "flex-dir-row-rev-x16", "flex_dir_row_rev_x16", 428, "chips", "Row reverse")
add("flex-wrap", "nowrap", "wrap", "flexWrap", "flex-wrap-wrap-x16", "flex_wrap_wrap_x16", 428, "chips", "Wrap")
add("grid-auto-flow", "row", "dense", "gridAutoFlow", "grid-flow-dense-x16", "grid_flow_dense_x16", 428, "cards", "Dense")
add("columns", "auto", "4", "columns", "columns-4-x16", "columns_4_x16", 416, "text", "Columns 4")
add("column-rule-width", "0px", "8px", "columnRuleWidth", "column-rule-w8", "column_rule_w8", 416, "text", "Rule 8")
add("column-span", "none", "all", "columnSpan", "column-span-all-x16", "column_span_all_x16", 416, "text", "Span all")
add("break-inside", "auto", "avoid-page", "breakInside", "break-inside-avoid-page-x16", "break_inside_avoid_page_x16", 416, "text", "Avoid page")
add("initial-letter", "normal", "2", "initialLetter", "initial-letter-2", "initial_letter_2", 416, "text", "Initial 2")
add("hyphenate-character", "auto", "'-'", "hyphenateCharacter", "hyphenate-char-hyphen-x16", "hyphenate_char_hyphen_x16", 414, "bind", "Hyphen")
add("hyphenate-limit-chars", "auto", "4 2 2", "hyphenateLimitChars", "hyphenate-limit-422", "hyphenate_limit_422", 414, "bind", "Limit 4 2 2")
add("counter-reset", "none", "ch 1", "counterReset", "counter-reset-ch1", "counter_reset_ch1", 449, "lists", "Reset 1")
add("counter-increment", "none", "ch", "counterIncrement", "counter-inc-ch", "counter_inc_ch", 449, "lists", "Inc 1")
add("content", "normal", "close-quote", "content", "content-close-quote-x16", "content_close_quote_x16", 415, "text", "Close-quote")
add("list-style-position", "inside", "outside", "listStylePosition", "list-pos-outside-x16", "list_pos_outside_x16", 449, "lists", "Outside")
add("shape-outside", "none", "ellipse(50% 40%)", "shapeOutside", "shape-outside-ellipse-x16", "shape_outside_ellipse_x16", 412, "floats", "Ellipse")
add("shape-image-threshold", "0", "0.25", "shapeImageThreshold", "shape-thresh-025", "shape_thresh_025", 412, "floats", "Thresh 0.25")
add("mask-repeat", "repeat", "space", "maskRepeat", "mask-repeat-space-x16", "mask_repeat_space_x16", 404, "cardhole", "Space")
add("mask-clip", "border-box", "padding-box", "maskClip", "mask-clip-padding-x16", "mask_clip_padding_x16", 404, "cardhole", "Clip padding")
add("mask-origin", "border-box", "padding-box", "maskOrigin", "mask-origin-padding-x16", "mask_origin_padding_x16", 404, "cardhole", "Origin padding")
add("mask-mode", "match-source", "alpha", "maskMode", "mask-mode-alpha-x16", "mask_mode_alpha_x16", 404, "cardhole", "Alpha")
add("mask-composite", "add", "exclude", "maskComposite", "mask-comp-exclude-x16", "mask_comp_exclude_x16", 404, "cardhole", "Exclude")
add("background-origin", "padding-box", "content-box", "backgroundOrigin", "bg-origin-content-x16", "bg_origin_content_x16", 404, "badges", "Origin content")
add("background-size", "auto", "contain", "backgroundSize", "bg-size-contain-x16", "bg_size_contain_x16", 404, "badges", "Size contain")
add("background-repeat", "repeat", "round", "backgroundRepeat", "bg-repeat-round-x16", "bg_repeat_round_x16", 404, "badges", "Repeat round")
add("background-attachment", "scroll", "fixed", "backgroundAttachment", "bg-attach-fixed-x16", "bg_attach_fixed_x16", 404, "badges", "Attach fixed")
add("object-view-box", "none", "inset(8%)", "objectViewBox", "object-view-inset-8-x16", "object_view_inset_8_x16", 404, "badges", "View 8")
add("image-rendering", "auto", "smooth", "imageRendering", "image-render-smooth-x16", "image_render_smooth_x16", 404, "badges", "Smooth")
add("forced-color-adjust", "auto", "none", "forcedColorAdjust", "forced-color-none-x16", "forced_color_none_x16", 464, "blends", "Forced none")
add("mix-blend-mode", "normal", "plus-lighter", "mixBlendMode", "blend-plus-lighter-x16", "blend_plus_lighter_x16", 464, "blends", "Plus-lighter")
add("background-blend-mode", "normal", "multiply", "backgroundBlendMode", "bg-blend-multiply-x16", "bg_blend_multiply_x16", 464, "blends", "Bg multiply")
add("filter", "none", "grayscale(1)", "filter", "filter-grayscale-x16", "filter_grayscale_x16", 415, "cards", "Grayscale")
add("filter", "none", "sepia(1)", "filter", "filter-sepia-x16", "filter_sepia_x16", 415, "cards", "Sepia")
add("backdrop-filter", "none", "invert(1)", "backdropFilter", "backdrop-invert-x16", "backdrop_invert_x16", 415, "cards", "Back invert")
add("will-change", "auto", "contents", "willChange", "will-change-contents-x16", "will_change_contents_x16", 412, "cards", "Will contents")
add("contain", "none", "strict", "contain", "contain-strict-x16", "contain_strict_x16", 428, "chips", "Strict")
add("container-type", "normal", "size", "containerType", "container-type-size-x16", "container_type_size_x16", 428, "chips", "Type size")
add("anchor-name", "none", "--card", "anchorName", "anchor-name-card-x16", "anchor_name_card_x16", 507, "floats", "Name card")
add("position-anchor", "auto", "--card", "positionAnchor", "position-anchor-card-x16", "position_anchor_card_x16", 507, "abspos", "Anchor card")
add("position-try-fallbacks", "none", "flip-inline", "positionTryFallbacks", "position-try-flip-inline", "position_try_flip_inline", 507, "abspos", "Flip inline")
add("position-visibility", "always", "anchors-valid", "positionVisibility", "pos-vis-anchors-valid", "pos_vis_anchors_valid", 507, "abspos", "Anchors valid")
add("overlay", "none", "auto", "overlay", "overlay-none-to-auto-x16", "overlay_none_to_auto_x16", 410, "chips", "Overlay auto")
add("interactivity", "auto", "inert", "interactivity", "interactivity-inert-x16", "interactivity_inert_x16", 410, "chips", "Inert")
add("appearance", "none", "base", "appearance", "appearance-base-x16", "appearance_base_x16", 404, "chips", "Base")
add("math-style", "normal", "compact", "mathStyle", "math-style-compact-x16", "math_style_compact_x16", 418, "eq", "Compact")
add("corner-shape", "round", "squircle", "cornerShape", "corner-shape-squircle", "corner_shape_squircle", 404, "chiphole", "Squircle")
add("font-kerning", "auto", "none", "fontKerning", "font-kerning-none-x16", "font_kerning_none_x16", 412, "glyphs", "Kern none")
add("font-optical-sizing", "auto", "none", "fontOpticalSizing", "font-optical-none-x16", "font_optical_none_x16", 412, "glyphs", "Optical none")
add("font-variant-ligatures", "normal", "none", "fontVariantLigatures", "font-liga-none-x16", "font_liga_none_x16", 412, "glyphs", "Liga none")
add("font-variant-east-asian", "normal", "jis83", "fontVariantEastAsian", "font-ea-jis83", "font_ea_jis83", 412, "glyphs", "JIS83")
add("font-variant-emoji", "normal", "unicode", "fontVariantEmoji", "font-emoji-unicode", "font_emoji_unicode", 412, "glyphs", "Unicode emoji")
add("font-variant-position", "normal", "sub", "fontVariantPosition", "font-var-pos-sub", "font_var_pos_sub", 412, "glyphs", "Pos sub")
add("box-decoration-break", "slice", "clone", "boxDecorationBreak", "box-deco-clone-x16", "box_deco_clone_x16", 404, "chips", "Clone")
add("ruby-align", "space-around", "space-between", "rubyAlign", "ruby-align-between", "ruby_align_between", 416, "glyphs", "Ruby between")
add("dominant-baseline", "auto", "middle", "dominantBaseline", "dominant-baseline-middle", "dominant_baseline_middle", 410, "glyphs", "Middle")
add("baseline-shift", "0", "20%", "baselineShift", "baseline-shift-20pct", "baseline_shift_20pct", 410, "glyphs", "Shift 20%")
add("animation-composition", "replace", "add", "animationComposition", "anim-comp-add-x16", "anim_comp_add_x16", 412, "chips", "Comp add")
add("timeline-scope", "none", "all", "timelineScope", "timeline-scope-all-x16", "timeline_scope_all_x16", 412, "chips", "Scope all")
add("view-timeline-name", "none", "--lane", "viewTimelineName", "view-tl-name-lane-x16", "view_tl_name_lane_x16", 412, "cards", "View tl lane")
add("animation-timeline", "auto", "view()", "animationTimeline", "anim-tl-view-x16", "anim_tl_view_x16", 412, "chips", "Tl view")
add("animation-range", "normal", "contain 0% contain 100%", "animationRange", "anim-range-contain", "anim_range_contain", 412, "chips", "Range contain")
add("scroll-timeline-name", "none", "--chip", "scrollTimelineName", "scroll-tl-name-chip-x16", "scroll_tl_name_chip_x16", 412, "chips", "Tl chip")
add("place-self", "auto", "start", "placeSelf", "place-self-start-x16", "place_self_start_x16", 412, "cards", "Place self start")
add("justify-self", "auto", "end", "justifySelf", "justify-self-end-x16", "justify_self_end_x16", 412, "cards", "Justify self end")
add("align-self", "auto", "stretch", "alignSelf", "align-self-stretch-x16", "align_self_stretch_x16", 412, "chips", "Self stretch")
add("text-decoration-skip-ink", "auto", "all", "textDecorationSkipInk", "deco-skip-ink-all", "deco_skip_ink_all", 404, "glyphs", "Skip all")
add("scrollbar-color", "auto", "Canvas CanvasText", "scrollbarColor", "scrollbar-color-flip", "scrollbar_color_flip", 425, "lanes", "Color flip")
add("caret-shape", "auto", "underscore", "caretShape", "caret-shape-under-x16", "caret_shape_under_x16", 415, "chips", "Caret under")
add("font-synthesis-weight", "auto", "none", "fontSynthesisWeight", "font-synth-weight-none-x16", "font_synth_weight_none_x16", 412, "glyphs", "Synth wt none")

PLANTS = []
for css, fr, to, js, widget, err, code, tmpl, btn in RAW:
    new, not_, teach = story(css, fr, to, tmpl)
    not_ = f"Not extra15 {css} mill, not extra14 {css}."
    PLANTS.append((css, fr, to, js, widget, err, code, tmpl, btn, new, not_, teach))

GENERA = [
    "asplenium", "polypodium", "dryopteris", "athyrium", "cystopteris", "gymnocarpium", "thelypteris",
    "phegopteris", "oreopteris", "christella", "cyclosorus", "macrothelypteris", "pseudophegopteris",
    "amauropelta", "goniopteris", "meniscium", "steiropteris", "amblovenatum", "pleocnemia", "tectaria",
    "lastreopsis", "parapolystichum", "coveniella", " rumohra".replace(" ", ""), "polystichum", "cyrtomium",
    "phenerophlebia", "arachniodes", "polystichopsis", "maxonia", "didymochlaena", "hypodematium",
    "woodsia", "physematium", "protowoodsia", "cheilanthopsis", "dennstaedtia", "microlepia",
    "leptomischus", "monachosorum", "pteridium", "paesia", "hypolepis", "blotiella", "histiopteris",
    "lonchitis", "saccoloma", "orthiopteris", "lindsaea", "odonto splenium".replace(" ", ""), "sphenomeris",
    "odontoloma", "tapeinidium", "xykopteris", "osmunda", "osmundastrum", "plen asium".replace(" ", ""),
    "todea", "leptopteris", "gleichenia", "dicranopteris", "sticherus", "diplopterygium", "stromatopteris",
    "matonia", "phanerosorus", "dipteris", "cheiropleuria", "hymenophyllum", "trichomanes", "crepidomanes",
    "didymoglossum", "polyphlebium", "abrodictyum", "callistopteris", "cephalomanes", "vandenboschia",
    "crepidopteris", "hymenoglossum", "serpyllopsis", "davallia", "humata", "scydopria", "arachniodesx",
    "oleandra", "arthropteris", "nephrolepis", "cyclopeltis", "lomariopsis", "thysanosoria", "teratophyllum",
    "lomagramma", "bolbitis", "elaphoglossum", "peltapteris", "microgramma", "pleopeltis", "campyloneurum",
    "niphidium", "phlebodium", "serpocaulon", "pecluma", "pleurosoriopsis", "lemmaphyllum", "lepidomicrosorium",
    "neocheiropteris", "tricholepidium", "goniophlebium", "selliguea", "arthromeris", "gymnogrammitis",
    "drynaria", "aigleomorphia", "photinopteris", "platycerium", "pyrrosia", "drymoglossum", "saxiglossum",
    "christiopteris", "microsorum", "lecanopteris", "colysis", "dendroconche", "bosmania", "zealandia",
    "notogrammitis", "grammitis", "adenophorus", "calymmodon", "ctenopteris", "xanthopteris", "themelium",
    "prosaptia", "scleroglossum", "oreogrammitis", "radiogrammitis", "tomophyllum", "chrysogrammitis",
    "ceradenia", "enterosora", "melpomene", "terpsichore", "alansmia", "moranopteris", "stenogrammitis",
    "mycopteris", "leucotrichum", "cochlidium", "micromeriax", "pteris", "neurocallis", "ochropteris",
    "anopteris", "hemionitis", "pityrogramma", "anogramma", "cosentinia", "cheilanthes", "myriopteris",
    "aleyrodium", "notholaena", "argyrochosma", "pentagramma", "astrolepis", "pellaea", "parabrya",
    "doryopteris", "adjanthopsis", "adiantum", "vittaria", "antrophyum", "hemi dicyum".replace(" ", ""),
    "monogramma", "radiovittaria", "haplopteris", "polytaenium", "scoliosorus", "ananthacorus",
    "acrostichum", "stenochlaena", "blechnum", "doodia", "woodwardia", "anchistea", "lorinseria",
    "brainea", "sadleria", "salpichlaena", "steochlaena", "lomariocycas", "cranfillia", "austroblechnum",
    "parablechnum", "neoblechnum", "oceaniopteris", "cleistoblechnum", "diploblechnum", "iseblechnum",
    "lomaridium", "struthiopteris", "spicantopsis", "cibotium", "dicksonia", "lophosoria", "metaxya",
    "culcita", "calochlaena", "thyrsopteris", "cyathea", "alsophila", "sphaeropteris", "gymnosphaera",
    "alsophilax", "sphaeropterix", "gymnosphaerax", "cyatheax", "dicksonix", "cibotiumx", "lophosorix",
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
        "brw-mill-r395-extra14.py", "brw-mill-r395-extra15.py",
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
            err = err + "_x16"
            if err in used_err:
                skipped += 1
                used_w.discard(widget)
                continue
        used_err.add(err)
        kept.append((css, fr, to, js, widget, err, code, tmpl, btn, new, not_, teach))
    kept = kept[:200]
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
            seed_ok, seed_bad = f"css-{widget}-x16", f"css-{widget}-x16-{code}"
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
    out = HERE / "brw-mill-r395-extra16.py"
    lines = ['"""Leftover CSS plants after extra15 ferns clough/dene."""', "KEYS = (",
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
