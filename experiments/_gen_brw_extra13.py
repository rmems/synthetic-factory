#!/usr/bin/env python3
"""Generate leftover CSS extra13 plants r1347+ (moss hosts ness/firth)."""
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


def story(css: str, fr: str, to: str, tmpl: str) -> tuple[str, str, str]:
    used = {
        "glyphs": (
            f"`{css}:{to}` retimes glyphs so stored {fr} x is GL-3.",
            f"Not extra12 {css} mill, not extra11 {css}.",
            f"{css}:{to} is live. Keep GL-2 by ref.",
        ),
        "chips": (
            f"`{css}:{to}` restacks so stored {fr} x is CH-3.",
            f"Not extra12 {css} mill, not extra11 {css}.",
            f"{css}:{to} is live. Keep CH-2 by ref.",
        ),
        "chiphole": (
            f"`{css}:{to}` unpaints a hole. Stored {fr} x is empty.",
            f"Not extra12 {css} mill, not extra11 {css}.",
            "The hole is still the chip if you use the ref.",
        ),
        "cards": (
            f"`{css}:{to}` grows or shears the used box so stored {fr} x is CD-4.",
            f"Not extra12 {css} mill, not extra11 {css}.",
            f"{css}:{to} is live. Keep CD-3 by ref.",
        ),
        "cardhole": (
            f"`{css}:{to}` cuts the card. Stored {fr} x is a hole.",
            f"Not extra12 {css} mill, not extra11 {css}.",
            "The hole is still the card ref.",
        ),
        "badges": (
            f"`{css}:{to}` retimes the replaced box so stored {fr} x is empty.",
            f"Not extra12 {css} mill, not extra11 {css}.",
            "Paint is not the badge. Keep the badge ref.",
        ),
        "rows": (
            f"`{css}:{to}` packs rows so stored {fr} y is RW-3.",
            f"Not extra12 {css} mill, not extra11 {css}.",
            f"{css}:{to} is live. Keep RW-2 by ref.",
        ),
        "text": (
            f"`{css}:{to}` reflows so stored {fr} x is TX-5.",
            f"Not extra12 {css} mill, not extra11 {css}.",
            f"{css}:{to} is live. Keep TX-2 by ref.",
        ),
        "labels": (
            f"`{css}:{to}` retimes wrap so a stored {fr} line is LB-3.",
            f"Not extra12 {css} mill, not extra11 {css}.",
            "File the a11y string.",
        ),
        "bind": (
            f"`{css}:{to}` clamps wrap so OCR BIND… is a different wrap.",
            f"Not extra12 {css} mill, not extra11 {css}.",
            "File the a11y string.",
        ),
        "lanes": (
            f"`{css}:{to}` changes the scrollport so stored {fr} x is LN-6.",
            f"Not extra12 {css} mill, not extra11 {css}.",
            "Keep the on-screen item ref.",
        ),
        "floats": (
            f"`{css}:{to}` packs wrap so stored {fr} x is FL-4.",
            f"Not extra12 {css} mill, not extra11 {css}.",
            f"{css}:{to} is live. Keep FL-3 by ref.",
        ),
        "abspos": (
            f"`{css}:{to}` slides abspos so stored {fr} x is empty.",
            f"Not extra12 {css} mill, not extra11 {css}.",
            f"{css}:{to} is live. Keep AB-2 by ref.",
        ),
        "blends": (
            f"`{css}:{to}` remaps paint so a screenshot looks empty.",
            f"Not extra12 {css} mill, not extra11 {css}.",
            "Paint is not unselected. Keep aria-selected / the ref.",
        ),
        "eq": (
            f"`{css}:{to}` retimes math so stored {fr} x is EQ-5.",
            f"Not extra12 {css} mill, not extra11 {css}.",
            "File EQ-4 by ref.",
        ),
        "lists": (
            f"`{css}:{to}` paints a marker. Clicking the marker slot is not LI-2.",
            f"Not extra12 {css} mill, not extra11 {css}.",
            "A marker is not the item. Keep the listitem ref.",
        ),
        "by": (
            f"`{css}:{to}` parks abspos so stored {fr} x is BY-6.",
            f"Not extra12 {css} mill, not extra11 {css}.",
            f"{css}:{to} is live. Keep BY-5 by ref.",
        ),
        "verbs": (
            f"`{css}:{to}` remaps the verb box so stored {fr} x is FILE.",
            f"Not extra12 {css} mill, not extra11 {css}.",
            "Keep OPEN by ref.",
        ),
    }
    return used[tmpl]


# leftover CSS: unused properties + unused values. widget names unique vs extra8–extra12.
# css, from, to, js, widget, err, code, tmpl, btn
RAW: list[tuple] = []

def add(css, fr, to, js, widget, err, code, tmpl, btn):
    RAW.append((css, fr, to, js, widget, err, code, tmpl, btn))


# unused font-size px
for px in (7, 8, 17, 19, 21, 23, 26, 30, 34, 38, 42, 44, 52, 56, 60, 72):
    add("font-size", "16px", f"{px}px", "fontSize", f"font-size-{px}", f"font_size_{px}", 412, "glyphs", f"Size {px}")

# unused zoom
for to, slug in (("0.15", "015"), ("0.2", "02"), ("0.35", "035"), ("0.4", "04"), ("0.55", "055"),
                 ("0.65", "065"), ("0.7", "07"), ("0.85", "085"), ("1.15", "115"), ("1.75", "175"),
                 ("2.5", "25"), ("6", "6"), ("8", "8"), ("10", "10")):
    add("zoom", "1", to, "zoom", f"zoom-{slug}-x13", f"zoom_{slug}_x13", 412, "cards", f"Zoom {to}")

# unused opacity
for to, slug in (("0.12", "012"), ("0.18", "018"), ("0.22", "022"), ("0.28", "028"), ("0.35", "035"),
                 ("0.42", "042"), ("0.55", "055"), ("0.65", "065"), ("0.78", "078"), ("0.85", "085"),
                 ("0.92", "092"), ("0.98", "098")):
    add("opacity", "1", to, "opacity", f"opacity-{slug}-x13", f"opacity_{slug}_x13", 464, "blends", f"Opacity {to}")

# unused scale
for to, slug in (("0.15", "015"), ("0.2", "02"), ("0.4", "04"), ("0.55", "055"), ("0.7", "07"),
                 ("0.85", "085"), ("1.15", "115"), ("1.25", "125"), ("2.5", "25"), ("5", "5"),
                 ("6", "6"), ("8", "8")):
    add("scale", "1", to, "scale", f"scale-{slug}-x13", f"scale_{slug}_x13", 412, "cards", f"Scale {to}")

# unused rotate axes/angles (not r648 scale-y; not extra12 rotate-x-45 / y-15 / z-8)
for axis, deg, code in (("x", 8, 520), ("x", 22, 520), ("x", 30, 520), ("x", 60, 520),
                        ("y", 8, 520), ("y", 22, 520), ("y", 30, 520), ("y", 60, 520),
                        ("z", 4, 520), ("z", 6, 520), ("z", 12, 520), ("z", 22, 520),
                        ("z", 30, 520), ("z", 45, 520), ("z", 60, 520)):
    add("rotate", "0deg", f"{axis} {deg}deg", "rotate", f"rotate-{axis}-{deg}-x13",
        f"rotate_{axis}_{deg}_x13", code, "cards", f"Rotate {axis.upper()} {deg}")

# unused translate
for axis, px, code, tmpl in (("x", 4, 412, "abspos"), ("x", 12, 412, "abspos"), ("x", 16, 412, "abspos"),
                             ("x", 32, 412, "abspos"), ("x", 48, 412, "abspos"),
                             ("y", 4, 410, "abspos"), ("y", 12, 410, "abspos"), ("y", 16, 410, "abspos"),
                             ("y", 32, 410, "abspos"),
                             ("z", 4, 520, "cards"), ("z", 12, 520, "cards"), ("z", 16, 520, "cards"),
                             ("z", 32, 520, "cards"), ("z", 48, 520, "cards")):
    if axis == "x":
        to = f"{px}px 0px"
    elif axis == "y":
        to = f"0px {px}px"
    else:
        to = f"0px 0px {px}px"
    add("translate", "0px", to, "translate", f"translate-{axis}-{px}-x13",
        f"translate_{axis}_{px}_x13", code, tmpl, f"Translate {axis} {px}")

# leftover cursor compass (not extra9/10/12 wait/help/move/copy/grab/cell/crosshair/progress)
for cur in ("n-resize", "s-resize", "e-resize", "w-resize", "ne-resize", "nw-resize",
            "se-resize", "sw-resize", "grabbing-x13", "zoom-out-x13"):
    slug = cur.replace("-", "_")
    val = cur.replace("-x13", "")
    add("cursor", "auto", val, "cursor", f"cursor-{cur}", f"cursor_{slug}", 404, "chips", val.replace("-", " ").title())

# leftover unused properties
add("caret-shape", "auto", "block", "caretShape", "caret-shape-block", "caret_shape_block", 415, "chips", "Caret block")
add("caret-shape", "auto", "underscore", "caretShape", "caret-shape-under", "caret_shape_under", 415, "chips", "Caret under")
add("caret-shape", "auto", "bar", "caretShape", "caret-shape-bar", "caret_shape_bar", 415, "chips", "Caret bar")
add("scroll-behavior", "auto", "smooth", "scrollBehavior", "scroll-behavior-smooth", "scroll_behavior_smooth", 425, "lanes", "Smooth")
add("scrollbar-color", "auto", "CanvasText Canvas", "scrollbarColor", "scrollbar-color-canvas", "scrollbar_color_canvas", 425, "lanes", "Color canvas")
add("text-justify", "auto", "inter-word", "textJustify", "text-justify-inter-word", "text_justify_inter_word", 412, "text", "Inter-word")
add("text-justify", "auto", "inter-character", "textJustify", "text-justify-inter-char", "text_justify_inter_char", 412, "text", "Inter-char")
add("text-align-last", "auto", "center", "textAlignLast", "text-align-last-center", "text_align_last_center", 412, "text", "Last center")
add("text-align-last", "auto", "justify", "textAlignLast", "text-align-last-justify", "text_align_last_justify", 412, "text", "Last justify")
add("text-underline-offset", "auto", "4px", "textUnderlineOffset", "underline-offset-4", "underline_offset_4", 404, "glyphs", "Under 4")
add("text-underline-offset", "auto", "8px", "textUnderlineOffset", "underline-offset-8", "underline_offset_8", 404, "glyphs", "Under 8")
add("text-decoration-skip-ink", "auto", "none", "textDecorationSkipInk", "deco-skip-ink-none", "deco_skip_ink_none", 404, "glyphs", "Skip none")
add("font-kerning", "auto", "none", "fontKerning", "font-kerning-none", "font_kerning_none", 412, "glyphs", "Kern none")
add("font-kerning", "auto", "normal", "fontKerning", "font-kerning-normal-x13", "font_kerning_normal_x13", 412, "glyphs", "Kern normal")
add("font-optical-sizing", "auto", "none", "fontOpticalSizing", "font-optical-none", "font_optical_none", 412, "glyphs", "Optical none")
add("font-size-adjust", "none", "0.5", "fontSizeAdjust", "font-size-adjust-05", "font_size_adjust_05", 412, "glyphs", "Adjust 0.5")
add("font-size-adjust", "none", "ex-height 0.5", "fontSizeAdjust", "font-size-adjust-ex", "font_size_adjust_ex", 412, "glyphs", "Adjust ex")
add("font-variation-settings", "normal", "'wght' 250", "fontVariationSettings", "font-var-wght-250", "font_var_wght_250", 412, "glyphs", "Wght 250")
add("font-variation-settings", "normal", "'wdth' 75", "fontVariationSettings", "font-var-wdth-75", "font_var_wdth_75", 412, "glyphs", "Wdth 75")
add("font-variant-ligatures", "normal", "none", "fontVariantLigatures", "font-liga-none", "font_liga_none", 412, "glyphs", "Liga none")
add("font-variant-ligatures", "normal", "no-common-ligatures", "fontVariantLigatures", "font-liga-no-common", "font_liga_no_common", 412, "glyphs", "No common")
add("font-variant-east-asian", "normal", "jis78", "fontVariantEastAsian", "font-ea-jis78", "font_ea_jis78", 412, "glyphs", "JIS78")
add("font-variant-east-asian", "normal", "proportional-width", "fontVariantEastAsian", "font-ea-prop", "font_ea_prop", 412, "glyphs", "EA prop")
add("font-variant-emoji", "normal", "emoji", "fontVariantEmoji", "font-emoji-emoji", "font_emoji_emoji", 412, "glyphs", "Emoji")
add("font-variant-emoji", "normal", "text", "fontVariantEmoji", "font-emoji-text", "font_emoji_text", 412, "glyphs", "Text emoji")
add("font-variant-position", "normal", "super", "fontVariantPosition", "font-var-pos-super", "font_var_pos_super", 412, "glyphs", "Pos super")
add("orphans", "2", "1", "orphans", "orphans-1", "orphans_1", 416, "text", "Orphans 1")
add("orphans", "2", "4", "orphans", "orphans-4", "orphans_4", 416, "text", "Orphans 4")
add("widows", "2", "1", "widows", "widows-1", "widows_1", 416, "text", "Widows 1")
add("widows", "2", "4", "widows", "widows-4", "widows_4", 416, "text", "Widows 4")
add("box-decoration-break", "slice", "clone", "boxDecorationBreak", "box-deco-clone", "box_deco_clone", 404, "chips", "Clone")
add("aspect-ratio", "auto", "1", "aspectRatio", "aspect-ratio-1", "aspect_ratio_1", 428, "cards", "Ratio 1")
add("aspect-ratio", "auto", "16 / 9", "aspectRatio", "aspect-ratio-169", "aspect_ratio_169", 428, "cards", "16/9")
add("aspect-ratio", "auto", "4 / 3", "aspectRatio", "aspect-ratio-43", "aspect_ratio_43", 428, "cards", "4/3")
add("aspect-ratio", "auto", "1 / 2", "aspectRatio", "aspect-ratio-12", "aspect_ratio_12", 428, "cards", "1/2")
add("offset-rotate", "auto", "0deg", "offsetRotate", "offset-rotate-0", "offset_rotate_0", 520, "by", "Offset rot 0")
add("offset-rotate", "auto", "45deg", "offsetRotate", "offset-rotate-45", "offset_rotate_45", 520, "by", "Offset rot 45")
add("offset-position", "normal", "0 0", "offsetPosition", "offset-pos-00", "offset_pos_00", 520, "by", "Offset 0 0")
add("offset-position", "normal", "100% 50%", "offsetPosition", "offset-pos-end", "offset_pos_end", 520, "by", "Offset end")
add("color-scheme", "normal", "dark", "colorScheme", "color-scheme-dark", "color_scheme_dark", 464, "blends", "Dark")
add("color-scheme", "normal", "light", "colorScheme", "color-scheme-light", "color_scheme_light", 464, "blends", "Light")
add("color-scheme", "normal", "only dark", "colorScheme", "color-scheme-only-dark", "color_scheme_only_dark", 464, "blends", "Only dark")
add("forced-color-adjust", "auto", "none", "forcedColorAdjust", "forced-color-none", "forced_color_none", 464, "blends", "Forced none")
add("flex-basis", "auto", "40px", "flexBasis", "flex-basis-40", "flex_basis_40", 428, "chips", "Basis 40")
add("flex-basis", "auto", "120px", "flexBasis", "flex-basis-120", "flex_basis_120", 428, "chips", "Basis 120")
add("flex-basis", "auto", "0px", "flexBasis", "flex-basis-0", "flex_basis_0", 428, "chips", "Basis 0")
add("flex-wrap", "nowrap", "wrap-reverse", "flexWrap", "flex-wrap-reverse-x13", "flex_wrap_reverse_x13", 428, "chips", "Wrap reverse")
add("flex-direction", "row", "column-reverse", "flexDirection", "flex-dir-col-rev", "flex_dir_col_rev", 428, "chips", "Col reverse")
add("align-self", "auto", "start", "alignSelf", "align-self-start-x13", "align_self_start_x13", 412, "chips", "Self start")
add("align-self", "auto", "center", "alignSelf", "align-self-center-x13", "align_self_center_x13", 412, "chips", "Self center")
add("align-self", "auto", "end", "alignSelf", "align-self-end-x13", "align_self_end_x13", 412, "chips", "Self end")
add("place-self", "auto", "center", "placeSelf", "place-self-center-x13", "place_self_center_x13", 412, "cards", "Place self center")
add("place-self", "auto", "end", "placeSelf", "place-self-end-x13", "place_self_end_x13", 412, "cards", "Place self end")
add("justify-self", "auto", "start", "justifySelf", "justify-self-start-x13", "justify_self_start_x13", 412, "cards", "Justify self start")
add("justify-self", "auto", "center", "justifySelf", "justify-self-center-x13", "justify_self_center_x13", 412, "cards", "Justify self center")
add("row-gap", "0px", "4px", "rowGap", "row-gap-4", "row_gap_4", 410, "cards", "Row gap 4")
add("row-gap", "0px", "12px", "rowGap", "row-gap-12", "row_gap_12", 410, "cards", "Row gap 12")
add("row-gap", "0px", "48px", "rowGap", "row-gap-48", "row_gap_48", 410, "cards", "Row gap 48")
add("column-gap", "0px", "4px", "columnGap", "column-gap-4", "column_gap_4", 412, "chips", "Col gap 4")
add("column-gap", "0px", "12px", "columnGap", "column-gap-12", "column_gap_12", 412, "chips", "Col gap 12")
add("column-gap", "0px", "48px", "columnGap", "column-gap-48", "column_gap_48", 412, "chips", "Col gap 48")
add("text-transform", "none", "uppercase", "textTransform", "text-transform-upper", "text_transform_upper", 412, "glyphs", "Upper")
add("text-transform", "none", "lowercase", "textTransform", "text-transform-lower", "text_transform_lower", 412, "glyphs", "Lower")
add("text-transform", "none", "capitalize", "textTransform", "text-transform-caps", "text_transform_caps", 412, "glyphs", "Caps")
add("text-transform", "none", "full-width", "textTransform", "text-transform-fullwidth", "text_transform_fullwidth", 412, "glyphs", "Full-width")
add("line-clamp", "none", "2", "lineClamp", "line-clamp-2", "line_clamp_2", 414, "bind", "Clamp 2")
add("line-clamp", "none", "4", "lineClamp", "line-clamp-4", "line_clamp_4", 414, "bind", "Clamp 4")
add("line-clamp", "none", "7", "lineClamp", "line-clamp-7", "line_clamp_7", 414, "bind", "Clamp 7")
add("ruby-align", "space-around", "center", "rubyAlign", "ruby-align-center", "ruby_align_center", 416, "glyphs", "Ruby center")
add("ruby-align", "space-around", "start", "rubyAlign", "ruby-align-start", "ruby_align_start", 416, "glyphs", "Ruby start")
add("dominant-baseline", "auto", "hanging", "dominantBaseline", "dominant-baseline-hanging", "dominant_baseline_hanging", 410, "glyphs", "Hanging")
add("dominant-baseline", "auto", "ideographic", "dominantBaseline", "dominant-baseline-ideo", "dominant_baseline_ideo", 410, "glyphs", "Ideo")
add("baseline-shift", "0", "sub", "baselineShift", "baseline-shift-sub", "baseline_shift_sub", 410, "glyphs", "Shift sub")
add("baseline-shift", "0", "super", "baselineShift", "baseline-shift-super", "baseline_shift_super", 410, "glyphs", "Shift super")
add("animation-composition", "replace", "add", "animationComposition", "anim-comp-add", "anim_comp_add", 412, "chips", "Comp add")
add("animation-composition", "replace", "accumulate", "animationComposition", "anim-comp-accum", "anim_comp_accum", 412, "chips", "Comp accum")
add("timeline-scope", "none", "all", "timelineScope", "timeline-scope-all", "timeline_scope_all", 412, "chips", "Scope all")
add("position-visibility", "always", "anchors-visible", "positionVisibility", "pos-vis-anchors", "pos_vis_anchors", 507, "abspos", "Anchors visible")
add("position-visibility", "always", "no-overflow", "positionVisibility", "pos-vis-no-overflow", "pos_vis_no_overflow", 507, "abspos", "No overflow")
add("overlay", "none", "auto", "overlay", "overlay-none-to-auto", "overlay_none_to_auto", 410, "chips", "Overlay auto")
add("interactivity", "auto", "inert", "interactivity", "interactivity-inert", "interactivity_inert", 410, "chips", "Inert")
add("appearance", "none", "base", "appearance", "appearance-base", "appearance_base", 404, "chips", "Base")
add("appearance", "none", "base-select", "appearance", "appearance-base-select", "appearance_base_select", 404, "chips", "Base select")
add("math-style", "normal", "compact", "mathStyle", "math-style-compact-x13", "math_style_compact_x13", 418, "eq", "Compact")
add("corner-shape", "round", "scoop", "cornerShape", "corner-shape-scoop-x13", "corner_shape_scoop_x13", 404, "chiphole", "Scoop")
add("corner-shape", "round", "bevel", "cornerShape", "corner-shape-bevel", "corner_shape_bevel", 404, "chiphole", "Bevel")
add("corner-shape", "round", "notch", "cornerShape", "corner-shape-notch", "corner_shape_notch", 404, "chiphole", "Notch")
add("font-width", "normal", "condensed", "fontWidth", "font-width-cond", "font_width_cond", 412, "glyphs", "Width cond")
add("font-width", "normal", "expanded", "fontWidth", "font-width-exp", "font_width_exp", 412, "glyphs", "Width exp")
add("font-synthesis-weight", "auto", "none", "fontSynthesisWeight", "font-synth-weight-none", "font_synth_weight_none", 412, "glyphs", "Synth wt none")
add("hyphenate-character", "auto", "'='", "hyphenateCharacter", "hyphenate-char-eq-x13", "hyphenate_char_eq_x13", 414, "bind", "Hyphen =")
add("mix-blend-mode", "normal", "difference", "mixBlendMode", "blend-difference-x13", "blend_difference_x13", 464, "blends", "Difference")
add("background-blend-mode", "normal", "difference", "backgroundBlendMode", "bg-blend-diff", "bg_blend_diff", 464, "blends", "Bg difference")
add("background-blend-mode", "normal", "overlay", "backgroundBlendMode", "bg-blend-overlay-x13", "bg_blend_overlay_x13", 464, "blends", "Bg overlay")
add("isolation", "auto", "isolate", "isolation", "isolation-isolate-x13", "isolation_isolate_x13", 464, "blends", "Isolate")
add("filter", "none", "blur(4px)", "filter", "filter-blur-4", "filter_blur_4", 415, "cards", "Blur 4")
add("filter", "none", "blur(8px)", "filter", "filter-blur-8", "filter_blur_8", 415, "cards", "Blur 8")
add("filter", "none", "brightness(0.4)", "filter", "filter-brightness-04", "filter_brightness_04", 415, "cards", "Bright 0.4")
add("filter", "none", "saturate(4)", "filter", "filter-saturate-4", "filter_saturate_4", 415, "cards", "Saturate 4")
add("backdrop-filter", "none", "blur(8px)", "backdropFilter", "backdrop-blur-8", "backdrop_blur_8", 415, "cards", "Back blur 8")
add("backdrop-filter", "none", "saturate(0)", "backdropFilter", "backdrop-saturate-0", "backdrop_saturate_0", 415, "cards", "Back sat 0")
add("mask-mode", "match-source", "alpha", "maskMode", "mask-mode-alpha", "mask_mode_alpha", 404, "cardhole", "Mask alpha")
add("mask-mode", "match-source", "luminance", "maskMode", "mask-mode-luma", "mask_mode_luma", 404, "cardhole", "Mask luma")
add("mask-composite", "add", "subtract", "maskComposite", "mask-comp-subtract-x13", "mask_comp_subtract_x13", 404, "cardhole", "Subtract")
add("mask-composite", "add", "intersect", "maskComposite", "mask-comp-intersect", "mask_comp_intersect", 404, "cardhole", "Intersect")
add("image-rendering", "auto", "crisp-edges", "imageRendering", "image-render-crisp-x13", "image_render_crisp_x13", 404, "badges", "Crisp")
add("image-rendering", "auto", "pixelated", "imageRendering", "image-render-pixel", "image_render_pixel", 404, "badges", "Pixelated")
add("object-view-box", "none", "inset(10%)", "objectViewBox", "object-view-inset-10", "object_view_inset_10", 404, "badges", "View 10")
add("gap", "0px", "1px", "gap", "gap-1", "gap_1", 412, "chips", "Gap 1")
add("gap", "0px", "6px", "gap", "gap-6", "gap_6", 412, "chips", "Gap 6")
add("gap", "0px", "10px", "gap", "gap-10", "gap_10", 412, "chips", "Gap 10")
add("gap", "0px", "20px", "gap", "gap-20", "gap_20", 412, "chips", "Gap 20")
add("gap", "0px", "36px", "gap", "gap-36", "gap_36", 412, "chips", "Gap 36")
add("gap", "0px", "64px", "gap", "gap-64", "gap_64", 412, "chips", "Gap 64")
add("flex-grow", "0", "5", "flexGrow", "flex-grow-5", "flex_grow_5", 428, "chips", "Grow 5")
add("flex-grow", "0", "8", "flexGrow", "flex-grow-8", "flex_grow_8", 428, "chips", "Grow 8")
add("flex-shrink", "1", "2", "flexShrink", "flex-shrink-2", "flex_shrink_2", 428, "chips", "Shrink 2")
add("flex-shrink", "1", "3", "flexShrink", "flex-shrink-3", "flex_shrink_3", 428, "chips", "Shrink 3")
add("order", "0", "5", "order", "order-5", "order_5", 428, "chips", "Order 5")
add("order", "0", "8", "order", "order-8", "order_8", 428, "chips", "Order 8")
add("order", "0", "-3", "order", "order-n3", "order_n3", 428, "chips", "Order -3")
add("z-index", "auto", "5", "zIndex", "z-index-5", "z_index_5", 403, "chips", "Z 5")
add("z-index", "auto", "8", "zIndex", "z-index-8", "z_index_8", 403, "chips", "Z 8")
add("z-index", "auto", "-3", "zIndex", "z-index-neg3", "z_index_neg3", 403, "chips", "Z -3")
add("z-index", "auto", "50", "zIndex", "z-index-50", "z_index_50", 403, "chips", "Z 50")
add("column-count", "auto", "6", "columnCount", "column-count-6", "column_count_6", 416, "text", "Count 6")
add("column-count", "auto", "8", "columnCount", "column-count-8", "column_count_8", 416, "text", "Count 8")
add("letter-spacing", "normal", "0.2em", "letterSpacing", "letter-spacing-02em", "letter_spacing_02em", 412, "glyphs", "Tracking 0.2em")
add("letter-spacing", "normal", "0.3em", "letterSpacing", "letter-spacing-03em", "letter_spacing_03em", 412, "glyphs", "Tracking 0.3em")
add("letter-spacing", "normal", "-0.1em", "letterSpacing", "letter-spacing-n01", "letter_spacing_n01", 412, "glyphs", "Tracking -0.1em")
add("word-spacing", "normal", "0.4em", "wordSpacing", "word-spacing-04em", "word_spacing_04em", 412, "glyphs", "Word 0.4em")
add("word-spacing", "normal", "1em", "wordSpacing", "word-spacing-1em", "word_spacing_1em", 412, "glyphs", "Word 1em")
add("line-height", "normal", "0.9", "lineHeight", "line-height-09", "line_height_09", 410, "rows", "Line 0.9")
add("line-height", "normal", "1.1", "lineHeight", "line-height-11", "line_height_11", 410, "rows", "Line 1.1")
add("line-height", "normal", "1.75", "lineHeight", "line-height-175", "line_height_175", 410, "rows", "Line 1.75")
add("line-height", "normal", "4", "lineHeight", "line-height-4", "line_height_4", 410, "rows", "Line 4")
add("border-radius", "0px", "2px", "borderRadius", "radius-2", "radius_2", 404, "chiphole", "Radius 2")
add("border-radius", "0px", "20px", "borderRadius", "radius-20", "radius_20", 404, "chiphole", "Radius 20")
add("border-radius", "0px", "24px", "borderRadius", "radius-24", "radius_24", 404, "chiphole", "Radius 24")
add("border-radius", "0px", "32px", "borderRadius", "radius-32", "radius_32", 404, "chiphole", "Radius 32")
add("border-radius", "0px", "50%", "borderRadius", "radius-50pct", "radius_50pct", 404, "chiphole", "Radius 50%")
add("outline-offset", "0px", "1px", "outlineOffset", "outline-offset-1", "outline_offset_1", 404, "floats", "Offset 1")
add("outline-offset", "0px", "16px", "outlineOffset", "outline-offset-16", "outline_offset_16", 404, "floats", "Offset 16")
add("outline-offset", "0px", "24px", "outlineOffset", "outline-offset-24", "outline_offset_24", 404, "floats", "Offset 24")
add("border-width", "0px", "1px", "borderWidth", "border-width-1", "border_width_1", 404, "chips", "Width 1")
add("border-width", "0px", "6px", "borderWidth", "border-width-6", "border_width_6", 404, "chips", "Width 6")
add("border-width", "0px", "10px", "borderWidth", "border-width-10", "border_width_10", 404, "chips", "Width 10")
add("border-width", "0px", "20px", "borderWidth", "border-width-20", "border_width_20", 404, "chips", "Width 20")
add("border-style", "none", "double", "borderStyle", "border-double-x13", "border_double_x13", 404, "chips", "Double")
add("border-style", "none", "groove", "borderStyle", "border-groove-x13", "border_groove_x13", 404, "chips", "Groove")
add("border-style", "none", "ridge", "borderStyle", "border-ridge-x13", "border_ridge_x13", 404, "chips", "Ridge")
add("border-style", "none", "inset", "borderStyle", "border-inset-x13", "border_inset_x13", 404, "chips", "Inset")
add("border-style", "none", "outset", "borderStyle", "border-outset-x13", "border_outset_x13", 404, "chips", "Outset")
add("inset", "0px", "4px", "inset", "inset-sh-4", "inset_sh_4", 412, "abspos", "Inset 4")
add("inset", "0px", "12px", "inset", "inset-sh-12", "inset_sh_12", 412, "abspos", "Inset 12")
add("inset", "0px", "48px", "inset", "inset-sh-48", "inset_sh_48", 412, "abspos", "Inset 48")
add("max-lines", "none", "7", "maxLines", "max-lines-7", "max_lines_7", 414, "bind", "Max 7")
add("max-lines", "none", "9", "maxLines", "max-lines-9", "max_lines_9", 414, "bind", "Max 9")
add("max-lines", "none", "10", "maxLines", "max-lines-10", "max_lines_10", 414, "bind", "Max 10")
add("perspective", "none", "50px", "perspective", "perspective-50", "perspective_50", 520, "cards", "Persp 50")
add("perspective", "none", "300px", "perspective", "perspective-300", "perspective_300", 520, "cards", "Persp 300")
add("perspective", "none", "500px", "perspective", "perspective-500", "perspective_500", 520, "cards", "Persp 500")
add("perspective", "none", "1200px", "perspective", "perspective-1200", "perspective_1200", 520, "cards", "Persp 1200")
add("clip-path", "none", "inset(12%)", "clipPath", "clip-path-inset-12", "clip_path_inset_12", 404, "cardhole", "Inset 12")
add("clip-path", "none", "circle(30%)", "clipPath", "clip-path-circle-30", "clip_path_circle_30", 404, "cardhole", "Circle 30")
add("clip-path", "none", "polygon(0 0,100% 0,50% 100%)", "clipPath", "clip-path-tri-x13", "clip_path_tri_x13", 404, "cardhole", "Triangle")
add("mask-size", "auto", "25%", "maskSize", "mask-size-25", "mask_size_25", 404, "cardhole", "Mask 25")
add("mask-size", "auto", "60%", "maskSize", "mask-size-60", "mask_size_60", 404, "cardhole", "Mask 60")
add("mask-size", "auto", "90%", "maskSize", "mask-size-90", "mask_size_90", 404, "cardhole", "Mask 90")
add("image-resolution", "from-image", "200dpi", "imageResolution", "image-res-200", "image_res_200", 404, "badges", "200dpi")
add("image-resolution", "from-image", "240dpi", "imageResolution", "image-res-240", "image_res_240", 404, "badges", "240dpi")
add("font-family", "sans-serif", "fantasy", "fontFamily", "font-family-fantasy", "font_family_fantasy", 412, "glyphs", "Fantasy")
add("font-family", "sans-serif", "system-ui", "fontFamily", "font-family-system", "font_family_system", 412, "glyphs", "System")
add("font-family", "sans-serif", "ui-sans-serif", "fontFamily", "font-family-uisans", "font_family_uisans", 412, "glyphs", "UI sans")
add("font-family", "sans-serif", "math", "fontFamily", "font-family-math", "font_family_math", 412, "glyphs", "Math")
add("object-position", "0 0", "0 100%", "objectPosition", "object-pos-bottom-left", "object_pos_bottom_left", 404, "badges", "Pos bottom left")
add("object-position", "0 0", "25% 25%", "objectPosition", "object-pos-2525", "object_pos_2525", 404, "badges", "Pos 25")
add("box-shadow", "none", "4px 0 0 CanvasText", "boxShadow", "box-shadow-x4", "box_shadow_x4", 404, "chips", "Offset 4")
add("box-shadow", "none", "24px 0 0 CanvasText", "boxShadow", "box-shadow-x24", "box_shadow_x24", 404, "chips", "Offset 24")
add("box-shadow", "none", "32px 0 0 CanvasText", "boxShadow", "box-shadow-x32", "box_shadow_x32", 404, "chips", "Offset 32")
add("text-indent", "0px", "4px", "textIndent", "text-indent-4", "text_indent_4", 412, "text", "Indent 4")
add("text-indent", "0px", "12px", "textIndent", "text-indent-12", "text_indent_12", 412, "text", "Indent 12")
add("text-indent", "0px", "16px", "textIndent", "text-indent-16", "text_indent_16", 412, "text", "Indent 16")
add("text-indent", "0px", "32px", "textIndent", "text-indent-32", "text_indent_32", 412, "text", "Indent 32")
add("tab-size", "8", "5", "tabSize", "tab-size-5", "tab_size_5", 413, "labels", "Tab 5")
add("tab-size", "8", "6", "tabSize", "tab-size-6", "tab_size_6", 413, "labels", "Tab 6")
add("tab-size", "8", "10", "tabSize", "tab-size-10", "tab_size_10", 413, "labels", "Tab 10")
add("outline-width", "0px", "3px", "outlineWidth", "outline-width-3", "outline_width_3", 404, "floats", "Outline 3")
add("outline-width", "0px", "4px", "outlineWidth", "outline-width-4", "outline_width_4", 404, "floats", "Outline 4")
add("outline-width", "0px", "6px", "outlineWidth", "outline-width-6", "outline_width_6", 404, "floats", "Outline 6")
add("outline-width", "0px", "12px", "outlineWidth", "outline-width-12", "outline_width_12", 404, "floats", "Outline 12")
add("column-width", "auto", "4em", "columnWidth", "column-width-4em", "column_width_4em", 416, "text", "Width 4em")
add("column-width", "auto", "10em", "columnWidth", "column-width-10em", "column_width_10em", 416, "text", "Width 10em")
add("column-width", "auto", "14em", "columnWidth", "column-width-14em", "column_width_14em", 416, "text", "Width 14em")
add("reading-order", "0", "6", "readingOrder", "reading-order-6", "reading_order_6", 428, "cards", "Order 6")
add("reading-order", "0", "-2", "readingOrder", "reading-order-n2", "reading_order_n2", 428, "cards", "Order -2")
add("font-language-override", "normal", "ZHS", "fontLanguageOverride", "font-lang-zhs", "font_lang_zhs", 412, "glyphs", "Lang ZHS")
add("font-language-override", "normal", "DEU", "fontLanguageOverride", "font-lang-deu", "font_lang_deu", 412, "glyphs", "Lang DEU")
add("font-language-override", "normal", "FRA", "fontLanguageOverride", "font-lang-fra", "font_lang_fra", 412, "glyphs", "Lang FRA")
add("font-language-override", "normal", "RUS", "fontLanguageOverride", "font-lang-rus", "font_lang_rus", 412, "glyphs", "Lang RUS")
add("font-language-override", "normal", "ARA", "fontLanguageOverride", "font-lang-ara", "font_lang_ara", 412, "glyphs", "Lang ARA")
add("text-spacing-trim", "space-all", "space-first", "textSpacingTrim", "text-spacing-space-first", "text_spacing_space_first", 412, "glyphs", "Space first")
add("text-spacing-trim", "space-all", "trim-both", "textSpacingTrim", "text-spacing-trim-both", "text_spacing_trim_both", 412, "glyphs", "Trim both")
add("grid-auto-columns", "auto", "20px", "gridAutoColumns", "grid-auto-cols-20", "grid_auto_cols_20", 428, "cards", "Auto cols 20")
add("grid-auto-columns", "auto", "80px", "gridAutoColumns", "grid-auto-cols-80", "grid_auto_cols_80", 428, "cards", "Auto cols 80")
add("grid-auto-columns", "auto", "160px", "gridAutoColumns", "grid-auto-cols-160", "grid_auto_cols_160", 428, "cards", "Auto cols 160")
add("grid-auto-rows", "auto", "20px", "gridAutoRows", "grid-auto-rows-20", "grid_auto_rows_20", 428, "cards", "Auto rows 20")
add("touch-action", "auto", "pan-down", "touchAction", "touch-pan-down", "touch_pan_down", 425, "lanes", "Pan down")
add("scroll-margin-left", "0px", "8px", "scrollMarginLeft", "scroll-mar-left-8", "scroll_mar_left_8", 425, "lanes", "Mar left 8")
add("scroll-padding-top", "0px", "8px", "scrollPaddingTop", "scroll-pad-top-8", "scroll_pad_top_8", 425, "lanes", "Pad top 8")
add("scroll-snap-align", "none", "center", "scrollSnapAlign", "snap-align-center-x13", "snap_align_center_x13", 425, "lanes", "Align center")
add("scroll-snap-align", "none", "end", "scrollSnapAlign", "snap-align-end-x13", "snap_align_end_x13", 425, "lanes", "Align end")
add("will-change", "auto", "filter", "willChange", "will-change-filter-x13", "will_change_filter_x13", 412, "cards", "Will filter")
add("will-change", "auto", "left", "willChange", "will-change-left-x13", "will_change_left_x13", 412, "cards", "Will left")
add("contain", "none", "style layout", "contain", "contain-style-layout", "contain_style_layout", 428, "chips", "Style layout")
add("user-select", "auto", "contain", "userSelect", "us-contain-x13", "us_contain_x13", 413, "labels", "Contain")
add("pointer-events", "auto", "bounding-box", "pointerEvents", "pe-bounding-box", "pe_bounding_box", 410, "chips", "Bounding box")
add("pointer-events", "auto", "visibleFill", "pointerEvents", "pe-visible-fill", "pe_visible_fill", 410, "chips", "Visible fill")
add("pointer-events", "auto", "painted", "pointerEvents", "pe-painted", "pe_painted", 410, "chips", "Painted")
add("visibility", "visible", "collapse", "visibility", "vis-collapse-x13", "vis_collapse_x13", 410, "chiphole", "Collapse")
add("display", "block", "table-column", "display", "display-table-column-x13", "display_table_column_x13", 428, "chips", "Table-column")
add("display", "block", "table-header-group", "display", "display-table-header-x13", "display_table_header_x13", 410, "rows", "Table-header")
add("display", "block", "contents", "display", "display-contents-x13", "display_contents_x13", 412, "chips", "Contents")
add("overflow-x", "visible", "clip", "overflowX", "overflow-x-clip-x13", "overflow_x_clip_x13", 425, "lanes", "Clip x")
add("overflow-y", "visible", "auto", "overflowY", "overflow-y-auto-x13", "overflow_y_auto_x13", 425, "lanes", "Auto y")
add("white-space", "normal", "break-spaces", "whiteSpace", "ws-break-spaces-x13", "ws_break_spaces_x13", 413, "labels", "Break-spaces")
add("hyphens", "none", "auto", "hyphens", "hyphens-auto-x13", "hyphens_auto_x13", 414, "bind", "Auto")
add("float", "none", "inline-end", "float", "float-inline-end-x13", "float_inline_end_x13", 412, "floats", "Inline end")
add("clear", "none", "inline-start", "clear", "clear-inline-start-x13", "clear_inline_start_x13", 410, "floats", "Clear istart")
add("vertical-align", "baseline", "bottom", "verticalAlign", "valign-bottom-x13", "valign_bottom_x13", 410, "glyphs", "Bottom")
add("vertical-align", "baseline", "top", "verticalAlign", "valign-top-x13", "valign_top_x13", 410, "glyphs", "Top")
add("place-items", "stretch", "start", "placeItems", "place-items-start-x13", "place_items_start_x13", 412, "cards", "Items start")
add("place-items", "stretch", "baseline", "placeItems", "place-items-baseline-x13", "place_items_baseline_x13", 412, "cards", "Items baseline")
add("align-content", "start", "space-between", "alignContent", "align-content-between-x13", "align_content_between_x13", 410, "cards", "Content between")
add("align-content", "start", "space-around", "alignContent", "align-content-around-x13", "align_content_around_x13", 410, "cards", "Content around")
add("align-content", "start", "space-evenly", "alignContent", "align-content-evenly-x13", "align_content_evenly_x13", 410, "cards", "Content evenly")
add("shape-margin", "0px", "2px", "shapeMargin", "shape-margin-2", "shape_margin_2", 412, "floats", "Shape margin 2")
add("shape-margin", "0px", "12px", "shapeMargin", "shape-margin-12", "shape_margin_12", 412, "floats", "Shape margin 12")
add("text-emphasis-style", "none", "filled", "textEmphasisStyle", "emphasis-filled-x13", "emphasis_filled_x13", 404, "glyphs", "Filled")
add("text-emphasis-style", "none", "open", "textEmphasisStyle", "emphasis-open-x13", "emphasis_open_x13", 404, "glyphs", "Open")
add("text-emphasis-style", "none", "triangle", "textEmphasisStyle", "emphasis-triangle-x13", "emphasis_triangle_x13", 404, "glyphs", "Triangle")
add("font-stretch", "normal", "ultra-expanded", "fontStretch", "font-stretch-ultraexp", "font_stretch_ultraexp", 412, "glyphs", "Ultra expanded")
add("font-stretch", "normal", "semi-condensed", "fontStretch", "font-stretch-semicond", "font_stretch_semicond", 412, "glyphs", "Semi condensed")
add("font-stretch", "normal", "extra-expanded", "fontStretch", "font-stretch-extraexp", "font_stretch_extraexp", 412, "glyphs", "Extra expanded")
add("font-variant-numeric", "normal", "slashed-zero", "fontVariantNumeric", "font-var-slashed-zero", "font_var_slashed_zero", 412, "glyphs", "Slashed zero")
add("font-variant-numeric", "normal", "ordinal", "fontVariantNumeric", "font-var-ordinal", "font_var_ordinal", 412, "glyphs", "Ordinal")
add("font-variant-numeric", "normal", "diagonal-fractions", "fontVariantNumeric", "font-var-diagfrac", "font_var_diagfrac", 412, "glyphs", "Diag frac")
add("hanging-punctuation", "none", "allow-end", "hangingPunctuation", "hanging-allow-end", "hanging_allow_end", 416, "text", "Allow end")
add("page", "auto", "wide-x13", "page", "page-wide-x13", "page_wide_x13", 416, "text", "Wide")
add("break-before", "auto", "avoid", "breakBefore", "break-before-avoid", "break_before_avoid", 416, "text", "Before avoid")
add("break-before", "auto", "left", "breakBefore", "break-before-left", "break_before_left", 416, "text", "Before left")
add("break-before", "auto", "right", "breakBefore", "break-before-right", "break_before_right", 416, "text", "Before right")
add("scroll-timeline-axis", "block", "x", "scrollTimelineAxis", "scroll-tl-x-x13", "scroll_tl_x_x13", 412, "chips", "Axis x")
add("view-transition-name", "none", "item", "viewTransitionName", "view-trans-item-x13", "view_trans_item_x13", 412, "cards", "Name item")
add("animation-name", "none", "fade", "animationName", "anim-name-fade-x13", "anim_name_fade_x13", 412, "chips", "Fade")
add("transition", "none", "width 200ms", "transition", "trans-width-200", "trans_width_200", 412, "chips", "Trans width 200")
add("transition", "none", "color 200ms", "transition", "trans-color-200", "trans_color_200", 412, "chips", "Trans color 200")
add("offset-path", "none", "circle(40px)", "offsetPath", "offset-path-circle-40", "offset_path_circle_40", 520, "by", "Circle 40")
add("position-area", "none", "span-all", "positionArea", "position-area-span-all", "position_area_span_all", 507, "abspos", "Span all")
add("anchor-size", "auto", "width", "anchorSize", "anchor-size-width", "anchor_size_width", 507, "floats", "Size width")
add("anchor-size", "auto", "height", "anchorSize", "anchor-size-height", "anchor_size_height", 507, "floats", "Size height")
add("masonry-auto-flow", "pack", "definite-first", "masonryAutoFlow", "masonry-definite-first", "masonry_definite_first", 428, "cards", "Definite first")
add("field-sizing", "fixed", "content", "fieldSizing", "field-sizing-content-x13", "field_sizing_content_x13", 428, "chips", "Content")
add("print-color-adjust", "economy", "exact", "printColorAdjust", "print-exact-x13", "print_exact_x13", 415, "badges", "Exact")
add("math-shift", "normal", "compact", "mathShift", "math-shift-compact-x13", "math_shift_compact_x13", 418, "eq", "Shift compact")
add("scrollbar-width", "auto", "none", "scrollbarWidth", "scrollbar-none-x13", "scrollbar_none_x13", 425, "lanes", "Width none")
add("overscroll-behavior", "auto", "contain", "overscrollBehavior", "overscroll-contain-x13", "overscroll_contain_x13", 425, "lanes", "Overscroll contain")
add("scroll-snap-stop", "normal", "always", "scrollSnapStop", "snap-stop-always-x13", "snap_stop_always_x13", 425, "lanes", "Stop always")
add("resize", "none", "block", "resize", "resize-block-x13", "resize_block_x13", 428, "cards", "Block")
add("resize", "none", "inline", "resize", "resize-inline-x13", "resize_inline_x13", 428, "cards", "Inline")
add("transform-origin", "50% 50%", "0 0", "transformOrigin", "transform-origin-00", "transform_origin_00", 520, "cards", "Origin 0 0")
add("transform-origin", "50% 50%", "100% 100%", "transformOrigin", "transform-origin-end", "transform_origin_end", 520, "cards", "Origin end")
add("transform-style", "flat", "preserve-3d", "transformStyle", "transform-style-3d", "transform_style_3d", 520, "cards", "Preserve 3d")
add("backface-visibility", "visible", "hidden", "backfaceVisibility", "backface-hidden-x13", "backface_hidden_x13", 520, "cards", "Backface hidden")
add("writing-mode", "horizontal-tb", "sideways-lr", "writingMode", "writing-sideways-lr-x13", "writing_sideways_lr_x13", 416, "text", "Sideways lr")
add("text-orientation", "mixed", "upright", "textOrientation", "text-orientation-upright", "text_orientation_upright", 416, "glyphs", "Upright")
add("object-fit", "cover", "none", "objectFit", "object-fit-none-x13", "object_fit_none_x13", 404, "badges", "Fit none")
add("background-clip", "border-box", "text", "backgroundClip", "bg-clip-text-x13", "bg_clip_text_x13", 404, "badges", "Clip text")
add("caret-color", "auto", "CanvasText", "caretColor", "caret-canvastext-x13", "caret_canvastext_x13", 415, "chips", "Caret CanvasText")
add("accent-color", "auto", "Canvas", "accentColor", "accent-canvas-x13", "accent_canvas_x13", 464, "blends", "Accent Canvas")
add("content-visibility", "visible", "auto", "contentVisibility", "cv-auto-x13", "cv_auto_x13", 410, "chiphole", "CV auto")
add("contain-intrinsic-size", "none", "80px 40px", "containIntrinsicSize", "contain-int-80-40", "contain_int_80_40", 428, "chips", "Int 80 40")
add("list-style-type", "disc", "square", "listStyleType", "list-type-square", "list_type_square", 449, "lists", "Square")
add("list-style-type", "disc", "decimal", "listStyleType", "list-type-decimal", "list_type_decimal", 449, "lists", "Decimal")
add("quotes", "auto", "none", "quotes", "quotes-none-x13", "quotes_none_x13", 415, "text", "Quotes none")
add("empty-cells", "show", "hide", "emptyCells", "empty-hide-x13", "empty_hide_x13", 428, "chips", "Hide")
add("caption-side", "top", "bottom", "captionSide", "caption-bottom-x13", "caption_bottom_x13", 410, "rows", "Caption bottom")
add("table-layout", "auto", "fixed", "tableLayout", "table-layout-fixed-x13", "table_layout_fixed_x13", 428, "chips", "Fixed x13")
add("overflow-wrap", "normal", "anywhere", "overflowWrap", "overflow-wrap-any-x13", "overflow_wrap_any_x13", 414, "bind", "Anywhere")
add("word-break", "normal", "break-all", "wordBreak", "break-all-x13", "break_all_x13", 414, "bind", "Break all")
add("word-break", "normal", "keep-all", "wordBreak", "keep-all-x13", "keep_all_x13", 414, "bind", "Keep all")
add("text-overflow", "clip", "ellipsis", "textOverflow", "text-overflow-ellipsis-x13", "text_overflow_ellipsis_x13", 414, "bind", "Ellipsis")
add("hyphenate-limit-chars", "auto", "6 3 2", "hyphenateLimitChars", "hyphenate-limit-632", "hyphenate_limit_632", 414, "bind", "Limit 6 3 2")
add("initial-letter", "normal", "3", "initialLetter", "initial-letter-3", "initial_letter_3", 416, "text", "Initial 3")
add("box-sizing", "content-box", "border-box", "boxSizing", "box-sizing-border-x13", "box_sizing_border_x13", 428, "chips", "Border-box")
add("overflow-anchor", "auto", "none", "overflowAnchor", "overflow-anchor-none-x13", "overflow_anchor_none_x13", 425, "lanes", "Anchor none")
add("scroll-snap-type", "none", "x mandatory", "scrollSnapType", "scroll-snap-x-mand", "scroll_snap_x_mand", 425, "lanes", "X mandatory")
add("scroll-snap-type", "none", "y proximity", "scrollSnapType", "scroll-snap-y-prox", "scroll_snap_y_prox", 425, "lanes", "Y proximity")
add("overscroll-behavior-x", "auto", "none", "overscrollBehaviorX", "overscroll-x-none-x13", "overscroll_x_none_x13", 425, "lanes", "X none")
add("overscroll-behavior-y", "auto", "none", "overscrollBehaviorY", "overscroll-y-none-x13", "overscroll_y_none_x13", 425, "lanes", "Y none")
add("touch-action", "auto", "manipulation", "touchAction", "touch-manip-x13", "touch_manip_x13", 425, "lanes", "Manipulation")
add("scrollbar-gutter", "auto", "stable", "scrollbarGutter", "scrollbar-gutter-stable-x13", "scrollbar_gutter_stable_x13", 425, "lanes", "Gutter stable")
add("offset-distance", "0", "50%", "offsetDistance", "offset-distance-50", "offset_distance_50", 520, "by", "Distance 50")
add("offset-distance", "0", "100%", "offsetDistance", "offset-distance-100", "offset_distance_100", 520, "by", "Distance 100")
add("offset-anchor", "auto", "0 0", "offsetAnchor", "offset-anchor-00", "offset_anchor_00", 520, "by", "Anchor 0 0")
add("perspective-origin", "50% 50%", "0 0", "perspectiveOrigin", "perspective-origin-00", "perspective_origin_00", 520, "cards", "Persp origin 0")
add("perspective-origin", "50% 50%", "100% 0", "perspectiveOrigin", "perspective-origin-end", "perspective_origin_end", 520, "cards", "Persp origin end")
add("grid-auto-flow", "row", "column dense", "gridAutoFlow", "grid-flow-col-dense", "grid_flow_col_dense", 428, "cards", "Col dense")
add("align-items", "stretch", "start", "alignItems", "align-items-start-x13", "align_items_start_x13", 412, "chips", "Items start")
add("align-items", "stretch", "baseline", "alignItems", "align-items-baseline-x13", "align_items_baseline_x13", 412, "chips", "Items baseline")
add("justify-content", "normal", "space-evenly", "justifyContent", "justify-evenly-x13", "justify_evenly_x13", 412, "chips", "Evenly")
add("justify-content", "normal", "space-around", "justifyContent", "justify-around-x13", "justify_around_x13", 412, "chips", "Around")
add("flex-flow", "row nowrap", "column wrap", "flexFlow", "flex-flow-col-wrap", "flex_flow_col_wrap", 428, "chips", "Col wrap")
add("columns", "auto", "3", "columns", "columns-3-x13", "columns_3_x13", 416, "text", "Columns 3")
add("column-rule-width", "0px", "4px", "columnRuleWidth", "column-rule-w4", "column_rule_w4", 416, "text", "Rule 4")
add("column-rule-style", "none", "dashed", "columnRuleStyle", "column-rule-dashed", "column_rule_dashed", 416, "text", "Rule dashed")
add("break-inside", "auto", "avoid", "breakInside", "break-inside-avoid-x13", "break_inside_avoid_x13", 416, "text", "Inside avoid")
add("break-after", "auto", "page", "breakAfter", "break-after-page-x13", "break_after_page_x13", 416, "text", "After page")
add("page-break-before", "auto", "always", "pageBreakBefore", "page-break-before-always", "page_break_before_always", 416, "text", "Always")
add("counter-reset", "none", "ch 3", "counterReset", "counter-reset-ch3", "counter_reset_ch3", 449, "lists", "Reset 3")
add("counter-increment", "none", "ch 2", "counterIncrement", "counter-inc-ch2", "counter_inc_ch2", 449, "lists", "Inc 2")
add("content", "normal", "open-quote", "content", "content-open-quote-x13", "content_open_quote_x13", 415, "text", "Open-quote")
add("quotes", "auto", "'«' '»'", "quotes", "quotes-guillemet", "quotes_guillemet", 415, "text", "Guillemet")
add("list-style-position", "outside", "inside", "listStylePosition", "list-pos-inside-x13", "list_pos_inside_x13", 449, "lists", "Inside")
add("shape-outside", "none", "circle(50%)", "shapeOutside", "shape-outside-circle-50", "shape_outside_circle_50", 412, "floats", "Circle 50")
add("shape-image-threshold", "0", "0.5", "shapeImageThreshold", "shape-thresh-05", "shape_thresh_05", 412, "floats", "Thresh 0.5")
add("mask-repeat", "repeat", "no-repeat", "maskRepeat", "mask-repeat-none-x13", "mask_repeat_none_x13", 404, "cardhole", "No-repeat")
add("mask-clip", "border-box", "content-box", "maskClip", "mask-clip-content-x13", "mask_clip_content_x13", 404, "cardhole", "Clip content")
add("mask-origin", "border-box", "content-box", "maskOrigin", "mask-origin-content-x13", "mask_origin_content_x13", 404, "cardhole", "Origin content")
add("background-origin", "padding-box", "content-box", "backgroundOrigin", "bg-origin-content-x13", "bg_origin_content_x13", 404, "badges", "Origin content")
add("background-size", "auto", "cover", "backgroundSize", "bg-size-cover-x13", "bg_size_cover_x13", 404, "badges", "Size cover")
add("background-repeat", "repeat", "space", "backgroundRepeat", "bg-repeat-space-x13", "bg_repeat_space_x13", 404, "badges", "Repeat space")
add("background-attachment", "scroll", "local", "backgroundAttachment", "bg-attach-local-x13", "bg_attach_local_x13", 404, "badges", "Attach local")
add("object-view-box", "none", "xywh(10% 10% 80% 80%)", "objectViewBox", "object-view-xywh-x13", "object_view_xywh_x13", 404, "badges", "xywh 80")
add("image-orientation", "from-image", "none", "imageOrientation", "image-orient-none-x13", "image_orient_none_x13", 404, "badges", "Orient none")
add("print-color-adjust", "economy", "exact", "printColorAdjust", "print-exact-dupcheck", "print_exact_dupcheck", 415, "badges", "Exact dup")  # filtered if collide
add("caret-color", "auto", "transparent", "caretColor", "caret-transparent-x13", "caret_transparent_x13", 415, "chips", "Caret transparent")
add("accent-color", "auto", "currentColor", "accentColor", "accent-current-x13", "accent_current_x13", 464, "blends", "Accent current")
add("color-scheme", "normal", "light dark", "colorScheme", "color-scheme-light-dark", "color_scheme_light_dark", 464, "blends", "Light dark")
add("forced-color-adjust", "auto", "preserve-parent-color", "forcedColorAdjust", "forced-color-preserve-x13", "forced_color_preserve_x13", 464, "blends", "Preserve parent")
add("mix-blend-mode", "normal", "exclusion", "mixBlendMode", "blend-exclusion-x13", "blend_exclusion_x13", 464, "blends", "Exclusion")
add("mix-blend-mode", "normal", "hue", "mixBlendMode", "blend-hue-x13", "blend_hue_x13", 464, "blends", "Hue")
add("mix-blend-mode", "normal", "luminosity", "mixBlendMode", "blend-luminosity-x13", "blend_luminosity_x13", 464, "blends", "Luminosity")
add("filter", "none", "drop-shadow(8px 0 0 CanvasText)", "filter", "filter-drop-8", "filter_drop_8", 415, "cards", "Drop 8")
add("filter", "none", "opacity(0.4)", "filter", "filter-opacity-04", "filter_opacity_04", 415, "cards", "Filt opacity 0.4")
add("backdrop-filter", "none", "brightness(0.5)", "backdropFilter", "backdrop-brightness-05", "backdrop_brightness_05", 415, "cards", "Back bright 0.5")
add("backdrop-filter", "none", "grayscale(1)", "backdropFilter", "backdrop-grayscale-x13", "backdrop_grayscale_x13", 415, "cards", "Back gray")
add("will-change", "auto", "top", "willChange", "will-change-top-x13", "will_change_top_x13", 412, "cards", "Will top")
add("will-change", "auto", "scale", "willChange", "will-change-scale-x13", "will_change_scale_x13", 412, "cards", "Will scale")
add("contain", "none", "inline-size", "contain", "contain-inline-size-x13", "contain_inline_size_x13", 428, "chips", "Inline size")
add("content-visibility", "visible", "hidden", "contentVisibility", "cv-hidden-x13", "cv_hidden_x13", 410, "chiphole", "CV hidden")
add("container-type", "normal", "size", "containerType", "container-type-size-x13", "container_type_size_x13", 428, "chips", "Type size")
add("container-type", "normal", "inline-size", "containerType", "container-type-inline-x13", "container_type_inline_x13", 428, "chips", "Type inline")
add("anchor-name", "none", "--chip", "anchorName", "anchor-name-chip-x13", "anchor_name_chip_x13", 507, "floats", "Name chip")
add("position-anchor", "auto", "--chip", "positionAnchor", "position-anchor-chip-x13", "position_anchor_chip_x13", 507, "abspos", "Anchor chip")
add("position-try-fallbacks", "none", "flip-block", "positionTryFallbacks", "position-try-flip-block", "position_try_flip_block", 507, "abspos", "Flip block")
add("inset-area", "none", "start", "insetArea", "inset-area-start-x13", "inset_area_start_x13", 507, "abspos", "Area start")
add("view-timeline-name", "none", "--card", "viewTimelineName", "view-tl-name-card", "view_tl_name_card", 412, "cards", "View tl card")
add("animation-timeline", "auto", "scroll()", "animationTimeline", "anim-tl-scroll-x13", "anim_tl_scroll_x13", 412, "chips", "Tl scroll")
add("animation-range", "normal", "cover 0% cover 100%", "animationRange", "anim-range-cover", "anim_range_cover", 412, "chips", "Range cover")
add("scroll-timeline-name", "none", "--lane", "scrollTimelineName", "scroll-tl-name-lane", "scroll_tl_name_lane", 412, "chips", "Tl lane")
add("overlay", "auto", "none", "overlay", "overlay-auto-to-none", "overlay_auto_to_none", 410, "chips", "Overlay none")
add("field-sizing", "content", "fixed", "fieldSizing", "field-sizing-fixed-x13", "field_sizing_fixed_x13", 428, "chips", "Fixed x13")
add("appearance", "none", "auto", "appearance", "appearance-auto-x13", "appearance_auto_x13", 404, "chips", "Auto x13")
add("user-select", "auto", "none", "userSelect", "us-none-x13", "us_none_x13", 413, "labels", "None")
add("pointer-events", "auto", "none", "pointerEvents", "pe-none-x13", "pe_none_x13", 410, "chips", "None")
add("cursor", "auto", "zoom-in", "cursor", "cursor-zoom-in-x13", "cursor_zoom_in_x13", 404, "chips", "Zoom-in")
add("cursor", "auto", "alias", "cursor", "cursor-alias-x13", "cursor_alias_x13", 404, "chips", "Alias")
add("display", "block", "inline-flex", "display", "display-inline-flex-x13", "display_inline_flex_x13", 412, "chips", "Inline-flex")
add("display", "block", "inline-grid", "display", "display-inline-grid-x13", "display_inline_grid_x13", 412, "chips", "Inline-grid")
add("display", "block", "flow-root", "display", "display-flow-root-x13", "display_flow_root_x13", 412, "chips", "Flow-root")
add("overflow-x", "visible", "overlay", "overflowX", "overflow-x-overlay-x13", "overflow_x_overlay_x13", 425, "lanes", "Overlay x")
add("letter-spacing", "normal", "1px", "letterSpacing", "letter-spacing-1px", "letter_spacing_1px", 412, "glyphs", "Tracking 1px")
add("word-spacing", "normal", "-0.1em", "wordSpacing", "word-spacing-n01em", "word_spacing_n01em", 412, "glyphs", "Word -0.1em")
add("line-height", "normal", "3.5", "lineHeight", "line-height-35", "line_height_35", 410, "rows", "Line 3.5")
add("gap", "0px", "3px", "gap", "gap-3", "gap_3", 412, "chips", "Gap 3")
add("flex-grow", "0", "6", "flexGrow", "flex-grow-6", "flex_grow_6", 428, "chips", "Grow 6")
add("z-index", "auto", "6", "zIndex", "z-index-6", "z_index_6", 403, "chips", "Z 6")
add("column-count", "auto", "7", "columnCount", "column-count-7", "column_count_7", 416, "text", "Count 7")
add("border-radius", "0px", "6px", "borderRadius", "radius-6", "radius_6", 404, "chiphole", "Radius 6")
add("outline-offset", "0px", "32px", "outlineOffset", "outline-offset-32", "outline_offset_32", 404, "floats", "Offset 32")
add("border-width", "0px", "3px", "borderWidth", "border-width-3", "border_width_3", 404, "chips", "Width 3")
add("inset", "0px", "6px", "inset", "inset-sh-6", "inset_sh_6", 412, "abspos", "Inset 6")
add("max-lines", "none", "1", "maxLines", "max-lines-1", "max_lines_1", 414, "bind", "Max 1")
add("perspective", "none", "1600px", "perspective", "perspective-1600", "perspective_1600", 520, "cards", "Persp 1600")
add("font-size", "16px", "80px", "fontSize", "font-size-80", "font_size_80", 412, "glyphs", "Size 80")
add("font-size", "16px", "96px", "fontSize", "font-size-96", "font_size_96", 412, "glyphs", "Size 96")
add("opacity", "1", "0.08", "opacity", "opacity-008-x13", "opacity_008_x13", 464, "blends", "Opacity 0.08")
add("zoom", "1", "12", "zoom", "zoom-12-x13", "zoom_12_x13", 412, "cards", "Zoom 12")
add("scale", "1", "12", "scale", "scale-12-x13", "scale_12_x13", 412, "cards", "Scale 12")

PLANTS: list[tuple] = []
for css, fr, to, js, widget, err, code, tmpl, btn in RAW:
    new, not_, teach = story(css, fr, to, tmpl)
    PLANTS.append((css, fr, to, js, widget, err, code, tmpl, btn, new, not_, teach))

GENERA = [
    "sphagnum", "polytrichum", "mnium", "atrichum", "funaria", "physcomitrium", "tortula", "barbula",
    "syntrichia", "grimmia", "racomitrium", "dicranum", "dicranella", "campylopus", "leucobryum", "fissidens",
    "tetraphis", "buxbaumia", "pottia", "didymodon", "gymnostomum", "eucladium", "trichostomum", "aloina",
    "crossidium", "weissia", "hymenostomum", "orthotrichum", "ulota", "zygodon", "macronitrium", "schlotheimia",
    "cryphaea", "leucodon", "forsstroemia", "neckera", "homalia", "porotrichum", "thamnobryum", "hookeria",
    "distichophyllum", "cyclodictyon", "calliergon", "warnstorfia", "scorpidium", "drepanocladus", "sanionia",
    "straminergon", "hamatocaulis", "palustriella", "cratoneuron", "campylium", "amblystegium", "lepidictyum",
    "hygrohypnum", "hypnum", "pterigynandrum", "heterocladium", "abietinella", "climacium", "pleurozium",
    "hylocomium", "rhytidiadelphus", "rhytidium", "ptilium", "ctenidium", "myuroclada", "plagiomnium",
    "rhizomnium", "cyrtomnium", "pohlia", "bryum", "rhodobryum", "plagiobryum", "anomobryum", "schistidium",
    "ptychomitrium", "glyphomitrium", "andreaea", "takakia", "tetrodontium", "oedipodium", "splachnum",
    "tetraplodon", "tayloria", "meesia", "paludella", "catoscopium", "timmia", "encalypta", "hedwigia",
    "braunia", "fontinalis", "dichelyma", "climaciadelphus", "pseudobryum", "tomentypnum", "loeskeobryum",
    "orthothecium", "isothecium", "homalothecium", "camptothecium", "brachythecium", "sciurohypnum",
    "kindbergia", "eurhynchium", "rhynchostegium", "osehrhynchium", "cirriphyllum", "scorodocarpus",
    "plasteurhynchium", "scleropodium", "homalotheciella", "clasmatodon", "bestia", "alsia", "dendroalsia",
    "antitricha", "fontinalia", "wardia", "brachelyma", "dichelymella", "hydropogon", "necckeropsis",
    "porothamnium", "thamniopsis", "homaliadelphus", "neckerera", "cryptoleptodon", "pendulothecium",
    "lomacoa", "isodrepanium", "homaliodendron", "brachytheciella", "eurhynchiadelphus", "kindbergiella",
    "marchantia", "riccia", "ricciocarpos", "lunularia", "conocephalum", "reboulia", "preissia", "targionia",
    "athalamia", "sphaerocarpos", "riella", "pellia", "pallavicinia", "moerckia", "blasia", "fossombronia",
    "petalophyllum", "treubia", "haplomitrium", "metzgeria", "riccardia", "aneura", "cryptothallus",
    "schiffneria", "radula", "frullania", "jubula", "lejeunea", "marchesinia", "cololejeunea",
    "drepanolejeunea", "harpalejeunea", "diplasiolejeunea", "colura", "diplophyllum", "scapania",
    "lophocolea", "chiloscyphus", "heteroscyphus", "geocalyx", "harpanthus", "sphenolobus", "tritomaria",
    "lophozia", "barbilophozia", "leiocolea", "gymnocolea", "anastrophyllum", "mesoptychia", "jungermannia",
    "solenostoma", "nardia", "plectocolea", "mylia", "plagiochila", "calypogeia", "kantius", "mnioloma",
    "odontochisma", "cephaloziella", "cephaloziia", "nowellia", "clavastylis", "hygrolembidium", "telaranea",
    "kurzia", "lepidoziella", "zoopsis", "araucariella", "pseudocephalozia", "hyalolepidozia", "sprucella",
    "trichocolea", "trichocoleopsis", "pleurozia", "ebrodtmannia", "herzogiella", "brotherella", "sematophyllum",
    "acroporium", "trichosteleum", "wijkia", "pterobryopsis", "garovaglia", "meteorium", "aerobryopsis",
    "barbella", "floribundaria", "plychomitriopsis", "macvicaria", "rutenbergia", "hypopterygium",
    "cyathophorum", "lopidium", "catharomnion", "saurotropis", "calomnion", "rhizogonium", "pyrrhobryum",
    "mesochaete", "goniobryum", "hymenodon", "mitthenia", "eucamptodon", "dicnemon", "eucamptodontopsis",
    "bescherellia", "spiridens", "hypnodendron", "mniodendron", "sciadocladus", "braithwaitea", "pleuroziopsis",
    "climaciumoss", "dendroceros", "notothylas", "phaeoceros", "anthoceros", "megaceros", "paraphymatoceros",
    "follmanniella", "phaeomegaceros", "nothoceros", "sphaerosporoceros", "leptoceros", "hasioceros",
]


def extra_used():
    used_w, used_es, used_pl, used_pr, used_ax, used_seed, used_err = (
        load_set("widgets"), load_set("errslugs"), load_set("places"),
        load_set("prefixes"), load_set("auxes"), load_set("seeds"), load_set("errs"),
    )
    for name in (
        "brw-mill-r395-extra8.py", "brw-mill-r395-extra9.py",
        "brw-mill-r395-extra10.py", "brw-mill-r395-extra11.py",
        "brw-mill-r395-extra12.py",
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
            err = err + "_x13"
            if err in used_err:
                skipped += 1
                used_w.discard(widget)
                continue
        used_err.add(err)
        kept.append((css, fr, to, js, widget, err, code, tmpl, btn, new, not_, teach))
    kept = kept[:180]
    if len(kept) > len(GENERA):
        raise SystemExit(f"need more genera {len(kept)}>{len(GENERA)}")
    if len({g for g in GENERA}) != len(GENERA):
        raise SystemExit("duplicate genera")
    rows = []
    for i, plant in enumerate(kept):
        css, fr, to, js, widget, err, code, tmpl, btn, new, not_, teach = plant
        item, neigh, fail, ref, nref, fref, x0, x1, y, title, path = T[tmpl]
        prefix = mint("".join(ch for ch in widget if ch.isalnum())[:4] or "ecp", used_pr)
        aux = mint(("".join(ch for ch in widget if ch.isalnum())[2:6] or "eca") + "x", used_ax)
        if prefix == aux:
            aux = mint(aux + "z", used_ax)
        genus = GENERA[i]
        ok, bad = genus + "ness", genus + "firth"
        if ok in used_pl or bad in used_pl:
            ok, bad = genus + "howe", genus + "knoll"
        if ok in used_pl or bad in used_pl or ok == bad:
            raise SystemExit(f"place collision {ok} {bad}")
        used_pl.add(ok); used_pl.add(bad)
        slug = f"{aux}-{code}"
        if slug in used_es:
            raise SystemExit(f"err_slug collision {slug}")
        used_es.add(slug)
        seed_ok, seed_bad = f"css-{widget}", f"css-{widget}-{code}"
        if seed_ok in used_seed or seed_bad in used_seed:
            seed_ok, seed_bad = f"css-{widget}-x13", f"css-{widget}-x13-{code}"
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
    out = HERE / "brw-mill-r395-extra13.py"
    lines = ['"""Leftover CSS plants r1347+ moss ness/firth."""', "KEYS = (",
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
