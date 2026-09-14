#!/usr/bin/env python3
"""Generate leftover CSS extra8 plants r745+ (unique vs r01-r744)."""
from __future__ import annotations

from pathlib import Path

SETS = Path("/tmp/brw-used/sets")
HERE = Path(__file__).resolve().parent

KEYS = (
    "prefix", "aux", "ok_place", "bad_place", "widget", "err_slug", "code", "err",
    "css", "from", "to", "js", "item", "neigh", "fail_item", "ref", "nref", "fref",
    "x0", "x1", "y", "btn", "title", "verb", "path", "keep", "note", "seed_ok", "seed_bad",
    "new", "not", "teach", "next",
)

# leftover CSS (unused properties or unused values). Widget names are new.
# (css, from, to, js, widget, err, code, item, neigh, fail, ref, nref, fref, x0, x1, y, btn, title, verb, path, new, not, teach)
PLANTS = [
    ("font-size", "16px", "24px", "fontSize", "font-size-24", "font_size_24", 412,
     "GL-2", "GL-3", "GL-3", "c2", "c3", "c3", 88, 110, 56, "Size 24", "Glyphs", "Keep", "glyphs",
     "`font-size:24px` grows glyphs so stored 16px x is GL-3.",
     "Not r font-weight-700, not extra7 font-style-italic.",
     "Font-size is live metrics. Keep GL-2 by ref."),
    ("font-family", "sans-serif", "ui-monospace", "fontFamily", "font-family-mono", "font_family_mono", 412,
     "GL-2", "GL-3", "GL-3", "c2", "c3", "c3", 88, 104, 56, "Mono", "Glyphs", "Keep", "glyphs",
     "`font-family:ui-monospace` retimes advances so stored sans x is GL-3.",
     "Not r font-feature-settings, not extra7 font-weight-700.",
     "Family metrics are live. Keep GL-2 by ref."),
    ("background-image", "none", "linear-gradient(90deg, Canvas, CanvasText)", "backgroundImage", "bg-image-gradient", "bg_image_gradient", 404,
     "BD-2", "BD-3", "BD-3", "c2", "c3", "c3", 140, 140, 80, "Gradient", "Badges", "Keep", "badges",
     "`background-image:linear-gradient(...)` paints a stripe. Center click on the stripe is not BD-2.",
     "Not r background-size, not extra7 bg-canvas.",
     "A gradient is paint. Keep the badge ref."),
    ("border-radius", "0px", "50%", "borderRadius", "radius-full", "radius_full", 404,
     "CH-2", "hole", "hole", "c2", "h1", "h1", 16, 16, 80, "Radius 50", "Chips", "Keep", "chips",
     "`border-radius:50%` (shorthand) makes corner holes. Stored square x is empty.",
     "Not r start-start-radius, not extra5 start-end-radius.",
     "A radius hole is still the chip if you use the ref."),
    ("border-style", "none", "dashed", "borderStyle", "border-dashed", "border_dashed", 404,
     "CH-2", "CH-3", "CH-3", "c2", "c3", "c3", 80, 80, 64, "Dashed", "Chips", "Keep", "chips",
     "`border-style:dashed` paints gaps. A click in a dash gap is not CH-2.",
     "Not extra7 border-current, not r outline-style.",
     "Dashes are paint. Keep the chip ref."),
    ("border-width", "0px", "8px", "borderWidth", "border-width-8", "border_width_8", 404,
     "CH-2", "CH-3", "CH-3", "c2", "c3", "c3", 80, 80, 64, "Width 8", "Chips", "Keep", "chips",
     "`border-width:8px` (shorthand) grows a ring. Center click on the ring is not CH-2.",
     "Not extra7 border-current, not r border-image-width.",
     "A fat border is paint. Keep the chip ref."),
    ("outline-offset", "0px", "12px", "outlineOffset", "outline-offset-12", "outline_offset_12", 404,
     "FL-3", "FL-4", "FL-4", "c3", "c4", "c4", 148, 160, 80, "Offset 12", "Floats", "Keep", "floats",
     "`outline-offset:12px` pushes UA chrome out so a screenshot ring is not FL-3.",
     "Not r390 outline-offset mill clone, not extra5 outline-color.",
     "Offset outline is paint. Keep the float ref."),
    ("scroll-margin-inline-start", "0px", "24px", "scrollMarginInlineStart", "scroll-margin-istart", "scroll_margin_istart", 425,
     "LN-4", "LN-5", "LN-6", "c4", "c5", "c6", 240, 216, 24, "Margin istart 24", "Lanes", "Keep", "lanes",
     "`scroll-margin-inline-start:24px` pads snap so stored 0-margin x is LN-6.",
     "Not r scroll-margin-block, not r scroll-margin shorthand mill.",
     "Inline-start scroll-margin is live. Keep the on-screen item ref."),
    ("scroll-padding-inline-start", "0px", "24px", "scrollPaddingInlineStart", "scroll-padding-istart", "scroll_padding_istart", 425,
     "LN-4", "LN-5", "LN-6", "c4", "c5", "c6", 240, 216, 24, "Pad istart 24", "Lanes", "Keep", "lanes",
     "`scroll-padding-inline-start:24px` insets the scrollport so stored 0-pad x is LN-6.",
     "Not r scroll-padding-block, not r scroll-padding mill clone.",
     "Inline-start scroll-padding is live. Keep the on-screen item ref."),
    ("grid-area", "auto", "1 / 1 / 2 / 3", "gridArea", "grid-area-span", "grid_area_span", 428,
     "CD-2", "CD-3", "CD-3", "c2", "c3", "c3", 40, 200, 80, "Area span", "Cards", "Keep", "cards",
     "`grid-area:1 / 1 / 2 / 3` spans two tracks so stored auto x is CD-3.",
     "Not r grid-column-span, not r grid-template-areas mill.",
     "grid-area shorthand is live. Keep CD-2 by ref."),
    ("view-transition-name", "none", "card", "viewTransitionName", "view-trans-named", "view_trans_named", 412,
     "CD-3", "CD-4", "CD-4", "c3", "c4", "c3", 160, 160, 80, "Name card", "Cards", "Keep", "cards",
     "`view-transition-name:card` snapshots the old box so a click during the morph hits CD-4.",
     "Not r view-transition mill clone, not r view-timeline-inset.",
     "Named transitions are not the live ref. Keep CD-3 by ref."),
    ("anchor-size", "auto", "--chip", "anchorSize", "anchor-size-chip", "anchor_size_chip", 507,
     "FL-1", "File", "gone", "c1", "e5", "c0", 220, 80, 40, "Size chip", "Floats", "Keep", "floats",
     "`anchor-size:--chip` sizes abspos from the named chip so stored auto size x is File.",
     "Not r167 anchor-size mill clone, not extra7 position-anchor.",
     "anchor-size is live. Re-find the invoker or use the ref."),
    ("inset-area", "none", "start", "insetArea", "inset-area-start", "inset_area_start", 507,
     "AB-2", "AB-3", "AB-3", "c2", "c3", "c3", 16, 8, 48, "Area start", "Abspos", "Keep", "abspos",
     "`inset-area:start` slots abspos into the start region so stored none x is empty.",
     "Not r position-area mill, not extra7 inset-inline-start.",
     "inset-area is live. Keep AB-2 by ref."),
    ("animation-name", "none", "nudge-x", "animationName", "anim-name-nudge", "anim_name_nudge", 412,
     "CH-2", "CH-3", "CH-3", "c2", "c3", "c3", 80, 120, 64, "Nudge", "Chips", "Keep", "chips",
     "`animation-name:nudge-x` translates the chip so stored none x is CH-3.",
     "Not r animation-duration-0, not r animation-timeline.",
     "Named animation is live. Keep CH-2 by ref."),
    ("animation-range-start", "0%", "20%", "animationRangeStart", "anim-range-start", "anim_range_start", 412,
     "CH-2", "CH-3", "CH-3", "c2", "c3", "c3", 80, 96, 64, "Range start 20", "Chips", "Keep", "chips",
     "`animation-range-start:20%` delays the timeline so stored 0% x is CH-3.",
     "Not r animation-range mill clone, not r animation-delay.",
     "Range-start is not delay. Keep CH-2 by ref."),
    ("animation-range-end", "100%", "80%", "animationRangeEnd", "anim-range-end", "anim_range_end", 412,
     "CH-2", "CH-3", "CH-3", "c2", "c3", "c3", 80, 112, 64, "Range end 80", "Chips", "Keep", "chips",
     "`animation-range-end:80%` cuts the timeline so stored 100% x is CH-3.",
     "Not r animation-range mill clone, not this mill's range-start.",
     "Range-end is live. Keep CH-2 by ref."),
    ("border-block", "0px none", "8px solid", "borderBlock", "border-block-sh", "border_block_sh", 404,
     "RW-2", "RW-3", "RW-3", "c2", "c3", "c3", 24, 24, 72, "Block border 8", "Rows", "Keep", "rows",
     "`border-block:8px solid` (shorthand) grows block chrome so stored 0 y is RW-3.",
     "Not r border-block-start-width, not r border-block-end-width.",
     "border-block shorthand is paint+metrics. Keep RW-2 by ref."),
    ("border-inline", "0px none", "8px dashed", "borderInline", "border-inline-sh", "border_inline_sh", 404,
     "CH-2", "CH-3", "CH-3", "c2", "c3", "c3", 80, 96, 64, "Inline border 8", "Chips", "Keep", "chips",
     "`border-inline:8px dashed` (shorthand) grows inline chrome so stored 0 x is CH-3.",
     "Not r border-inline-start-width, not extra7 border-current.",
     "border-inline shorthand is live. Keep CH-2 by ref."),
    ("border-top", "0px none", "8px solid", "borderTop", "border-top-8", "border_top_8", 404,
     "RW-2", "RW-3", "RW-3", "c2", "c3", "c3", 24, 24, 64, "Top 8", "Rows", "Keep", "rows",
     "`border-top:8px solid` grows the top edge so stored 0 y is RW-3.",
     "Not r border-block-start, not this mill's border-block shorthand.",
     "Physical border-top is live. Keep RW-2 by ref."),
    ("border-bottom", "0px none", "8px solid", "borderBottom", "border-bottom-8", "border_bottom_8", 404,
     "RW-2", "RW-3", "RW-3", "c2", "c3", "c3", 24, 24, 72, "Bottom 8", "Rows", "Keep", "rows",
     "`border-bottom:8px solid` grows the bottom edge so stored 0 y is RW-3.",
     "Not r border-block-end, not this mill's border-top.",
     "Physical border-bottom is live. Keep RW-2 by ref."),
    ("border-left", "0px none", "8px solid", "borderLeft", "border-left-8", "border_left_8", 404,
     "CH-2", "CH-3", "CH-3", "c2", "c3", "c3", 80, 88, 64, "Left 8", "Chips", "Keep", "chips",
     "`border-left:8px solid` grows the start edge so stored 0 x is CH-3.",
     "Not r border-inline-start, not this mill's border-inline shorthand.",
     "Physical border-left is live. Keep CH-2 by ref."),
    ("border-right", "0px none", "8px solid", "borderRight", "border-right-8", "border_right_8", 404,
     "CH-2", "CH-3", "CH-3", "c2", "c3", "c3", 80, 88, 64, "Right 8", "Chips", "Keep", "chips",
     "`border-right:8px solid` grows the end edge so stored 0 x is CH-3.",
     "Not r border-inline-end, not this mill's border-left.",
     "Physical border-right is live. Keep CH-2 by ref."),
    ("border-top-left-radius", "0px", "24px", "borderTopLeftRadius", "radius-tl-24", "radius_tl_24", 404,
     "CH-2", "hole", "hole", "c2", "h1", "h1", 16, 16, 16, "TL 24", "Chips", "Keep", "chips",
     "`border-top-left-radius:24px` makes that corner a hole.",
     "Not r start-start-radius, not this mill's radius-full.",
     "A TL radius hole is still the chip if you use the ref."),
    ("border-top-right-radius", "0px", "24px", "borderTopRightRadius", "radius-tr-24", "radius_tr_24", 404,
     "CH-2", "hole", "hole", "c2", "h1", "h1", 144, 144, 16, "TR 24", "Chips", "Keep", "chips",
     "`border-top-right-radius:24px` makes that corner a hole.",
     "Not r start-end-radius, not this mill's radius-tl.",
     "A TR radius hole is still the chip if you use the ref."),
    ("border-bottom-left-radius", "0px", "24px", "borderBottomLeftRadius", "radius-bl-24", "radius_bl_24", 404,
     "CH-2", "hole", "hole", "c2", "h1", "h1", 16, 16, 80, "BL 24", "Chips", "Keep", "chips",
     "`border-bottom-left-radius:24px` makes that corner a hole.",
     "Not r end-start-radius, not this mill's radius-tl.",
     "A BL radius hole is still the chip if you use the ref."),
    ("border-bottom-right-radius", "0px", "24px", "borderBottomRightRadius", "radius-br-24", "radius_br_24", 404,
     "CH-2", "hole", "hole", "c2", "h1", "h1", 144, 144, 80, "BR 24", "Chips", "Keep", "chips",
     "`border-bottom-right-radius:24px` makes that corner a hole.",
     "Not r end-end-radius, not this mill's radius-bl.",
     "A BR radius hole is still the chip if you use the ref."),
    ("caret", "auto", "block 1em", "caret", "caret-block-sh", "caret_block_sh", 415,
     "CH-2", "CH-3", "CH-3", "c2", "c3", "c3", 80, 80, 64, "Caret block", "Chips", "Keep", "chips",
     "`caret:block 1em` paints a block caret that covers CH-3. A blink-off screenshot looks empty.",
     "Not r caret-color-transparent, not r caret-animation.",
     "Caret shorthand is paint. Keep the chip ref."),
    ("corner-shape", "round", "scoop", "cornerShape", "corner-scoop", "corner_scoop", 404,
     "CH-2", "hole", "hole", "c2", "h1", "h1", 16, 16, 80, "Scoop", "Chips", "Keep", "chips",
     "`corner-shape:scoop` bites the corner so stored round x is a hole.",
     "Not r corner-shape mill clone, not this mill's radius-full.",
     "A scooped corner is still the chip if you use the ref."),
    ("fill", "CanvasText", "Canvas", "fill", "fill-canvas", "fill_canvas", 415,
     "OPEN", "FILE", "FILE", "c1", "c2", "c2", 110, 110, 70, "Fill Canvas", "Verbs", "Keep", "verbs",
     "`fill:Canvas` remaps SVG paint so OCR reads FILE, not OPEN.",
     "Not extra7 color-canvas, not r641 filter-sepia.",
     "SVG Canvas fill screenshots are not the accessible name."),
    ("fill-rule", "nonzero", "evenodd", "fillRule", "fill-evenodd", "fill_evenodd", 404,
     "BD-2", "hole", "hole", "c2", "h1", "h1", 140, 140, 80, "Evenodd", "Badges", "Keep", "badges",
     "`fill-rule:evenodd` punches a hole in the badge path. Stored nonzero x is empty.",
     "Not r clip-path, not this mill's fill-canvas.",
     "An evenodd hole is still the badge if you use the ref."),
    ("flood-color", "CanvasText", "Canvas", "floodColor", "flood-canvas", "flood_canvas", 415,
     "OPEN", "FILE", "FILE", "c1", "c2", "c2", 110, 110, 70, "Flood Canvas", "Verbs", "Keep", "verbs",
     "`flood-color:Canvas` remaps feFlood so OCR reads FILE, not OPEN.",
     "Not this mill's fill-canvas, not extra7 color-canvas.",
     "Flood Canvas screenshots are not the accessible name."),
    ("marker-end", "none", "url(#arrow)", "markerEnd", "marker-end-arrow", "marker_end_arrow", 404,
     "CH-2", "CH-3", "CH-3", "c2", "c3", "c3", 80, 120, 64, "Arrow end", "Chips", "Keep", "chips",
     "`marker-end:url(#arrow)` paints an arrow past the chip. A click on the arrow is not CH-2.",
     "Not r list-style-image, not r stroke-width.",
     "An end marker is paint. Keep the chip ref."),
    ("mask-border-source", "none", "url(#slice)", "maskBorderSource", "mask-border-src", "mask_border_src", 404,
     "CD-3", "hole", "hole", "c3", "h1", "h1", 160, 160, 80, "Mask border src", "Cards", "Keep", "cards",
     "`mask-border-source:url(#slice)` slices the card. Stored none x is a hole.",
     "Not extra5 mask-image, not r mask-border-slice.",
     "A mask-border source hole is still the card ref."),
    ("mask-border-width", "0", "8", "maskBorderWidth", "mask-border-w8", "mask_border_w8", 404,
     "CD-3", "CD-4", "CD-4", "c3", "c4", "c3", 160, 144, 80, "Mask border 8", "Cards", "Keep", "cards",
     "`mask-border-width:8` insets the visible card so stored 0 x is CD-4.",
     "Not r mask-border-slice, not this mill's mask-border-src.",
     "mask-border-width is live. Keep CD-3 by ref."),
    ("object-view-box", "none", "inset(10%)", "objectViewBox", "object-view-inset", "object_view_inset", 404,
     "BD-2", "BD-3", "BD-3", "c2", "c3", "c3", 140, 126, 80, "View inset 10", "Badges", "Keep", "badges",
     "`object-view-box:inset(10%)` crops the replaced box so stored none x is empty.",
     "Not r object-view-box mill clone, not extra6 object-fit-contain.",
     "View-box inset is paint. Keep the badge ref."),
    ("page", "auto", "landscape", "page", "page-landscape", "page_landscape", 416,
     "TX-2", "TX-5", "TX-5", "c2", "c5", "c5", 40, 24, 36, "Landscape", "Text", "Keep", "text",
     "`page:landscape` reflows print fragmentation so stored auto x is TX-5.",
     "Not r break-after-page, not r columns-shorthand.",
     "Named page is live. Keep TX-2 by ref."),
    ("page-break-inside", "auto", "avoid", "pageBreakInside", "page-break-inside", "page_break_inside", 416,
     "TX-2", "TX-5", "TX-5", "c2", "c5", "c5", 40, 24, 36, "Avoid inside", "Text", "Keep", "text",
     "`page-break-inside:avoid` keeps the block together so stored auto x is TX-5.",
     "Not r break-inside mill, not this mill's page-landscape.",
     "page-break-inside is live. Keep TX-2 by ref."),
    ("position-try", "none", "flip-block", "positionTry", "position-try-flip", "position_try_flip", 507,
     "AB-2", "AB-3", "AB-3", "c2", "c3", "c3", 16, 16, 120, "Flip block", "Abspos", "Keep", "abspos",
     "`position-try:flip-block` flips the abspos so stored none y is empty.",
     "Not r125 position-try flip mill, not extra7 position-anchor.",
     "position-try is live. Keep AB-2 by ref."),
    ("reading-flow", "normal", "grid-rows", "readingFlow", "reading-flow-rows", "reading_flow_rows", 428,
     "CD-2", "CD-4", "CD-4", "c2", "c4", "c4", 40, 200, 80, "Flow rows", "Cards", "Keep", "cards",
     "`reading-flow:grid-rows` retargets sequential focus so stored normal x is CD-4.",
     "Not r reading-flow mill clone, not extra6 grid-flow-dense.",
     "reading-flow is not visual grid. Keep CD-2 by ref."),
    ("reading-order", "0", "2", "readingOrder", "reading-order-2", "reading_order_2", 428,
     "CD-2", "CD-4", "CD-4", "c2", "c4", "c4", 40, 200, 80, "Order 2", "Cards", "Keep", "cards",
     "`reading-order:2` restacks a11y order so stored 0 x is CD-4.",
     "Not r reading-order mill clone, not r order mill.",
     "reading-order is not flex order. Keep CD-2 by ref."),
    ("scroll-timeline-axis", "block", "inline", "scrollTimelineAxis", "scroll-tl-axis", "scroll_tl_axis", 412,
     "CH-2", "CH-3", "CH-3", "c2", "c3", "c3", 80, 120, 64, "Axis inline", "Chips", "Keep", "chips",
     "`scroll-timeline-axis:inline` drives the timeline from x-scroll so stored block x is CH-3.",
     "Not r scroll-timeline-name, not r animation-timeline.",
     "Axis inline is not block. Keep CH-2 by ref."),
    ("shape-rendering", "auto", "crispedges", "shapeRendering", "shape-crisp", "shape_crisp", 404,
     "BD-2", "BD-3", "BD-3", "c2", "c3", "c3", 140, 140, 80, "Crisp edges", "Badges", "Keep", "badges",
     "`shape-rendering:crispedges` aliases the blob so a screenshot island is not BD-2.",
     "Not r image-rendering-hq, not extra6 object-fit-contain.",
     "Crisp SVG edges are paint. Keep the badge ref."),
    ("stroke", "none", "currentColor", "stroke", "stroke-current", "stroke_current", 404,
     "CH-2", "CH-3", "CH-3", "c2", "c3", "c3", 80, 80, 64, "Stroke current", "Chips", "Keep", "chips",
     "`stroke:currentColor` paints a ring. Center click on the stroke is not CH-2.",
     "Not extra7 border-current, not r stroke-width.",
     "A currentColor stroke is paint. Keep the chip ref."),
    ("stroke-dasharray", "none", "8 4", "strokeDasharray", "stroke-dash-8", "stroke_dash_8", 404,
     "CH-2", "CH-3", "CH-3", "c2", "c3", "c3", 80, 80, 64, "Dash 8 4", "Chips", "Keep", "chips",
     "`stroke-dasharray:8 4` paints gaps. A click in a gap is not CH-2.",
     "Not r stroke-dashoffset, not this mill's stroke-current.",
     "Dashed stroke is paint. Keep the chip ref."),
    ("stroke-linecap", "butt", "round", "strokeLinecap", "stroke-cap-round", "stroke_cap_round", 404,
     "CH-2", "CH-3", "CH-3", "c2", "c3", "c3", 80, 88, 64, "Cap round", "Chips", "Keep", "chips",
     "`stroke-linecap:round` grows caps past the box. A click on the cap is not CH-2.",
     "Not r stroke-width, not this mill's stroke-dash.",
     "Round caps are paint. Keep the chip ref."),
    ("text-anchor", "start", "middle", "textAnchor", "text-anchor-mid", "text_anchor_mid", 412,
     "GL-2", "GL-3", "GL-3", "c2", "c3", "c3", 88, 48, 56, "Anchor mid", "Glyphs", "Keep", "glyphs",
     "`text-anchor:middle` recenters SVG text so stored start x is GL-3.",
     "Not extra7 text-align-center, not r text-orientation.",
     "SVG text-anchor is live. Keep GL-2 by ref."),
    ("text-box", "normal", "trim-both cap alphabetic", "textBox", "text-box-sh", "text_box_sh", 410,
     "RW-2", "RW-3", "RW-3", "c2", "c3", "c3", 24, 24, 44, "Box trim cap", "Rows", "Keep", "rows",
     "`text-box:trim-both cap alphabetic` (shorthand) drops half-leading so stored normal y is RW-3.",
     "Not extra5 text-box-trim, not extra5 text-box-edge.",
     "text-box shorthand is live. Keep RW-2 by ref."),
    ("text-decoration", "none", "underline wavy 4px", "textDecoration", "text-deco-sh", "text_deco_sh", 404,
     "LB-4", "LB-5", "LB-5", "c4", "c5", "c5", 160, 160, 78, "Deco wavy 4", "Labels", "Keep", "labels",
     "`text-decoration:underline wavy 4px` (shorthand) fattens the wave so a y-click hits paint, not LB-4.",
     "Not extra5 decoration-line, not extra5 decoration-style.",
     "Decoration shorthand is paint. Keep the label ref."),
    ("text-emphasis", "none", "filled sesame", "textEmphasis", "text-emph-sh", "text_emph_sh", 404,
     "GL-2", "GL-3", "GL-3", "c2", "c3", "c3", 88, 88, 40, "Emph sesame", "Glyphs", "Keep", "glyphs",
     "`text-emphasis:filled sesame` (shorthand) paints marks above. A click on a mark is not GL-2.",
     "Not r emphasis-style, not r emphasis-color.",
     "Emphasis marks are paint. Keep the glyph ref."),
    ("text-rendering", "auto", "optimizeLegibility", "textRendering", "text-render-legible", "text_render_legible", 412,
     "GL-2", "GL-3", "GL-3", "c2", "c3", "c3", 88, 100, 56, "Legibility", "Glyphs", "Keep", "glyphs",
     "`text-rendering:optimizeLegibility` enables kerning/ligatures so stored auto x is GL-3.",
     "Not r font-kerning, not r font-variant-ligatures.",
     "optimizeLegibility is live metrics. Keep GL-2 by ref."),
    ("text-wrap", "wrap", "nowrap", "textWrap", "text-wrap-nowrap", "text_wrap_nowrap", 414,
     "BINDING-COMPLETE", "BIND…", "BIND", "c1", "c1", "c0", 24, 24, 48, "Nowrap", "Labels", "Keep", "labels",
     "`text-wrap:nowrap` forbids wraps so OCR BIND… is a different line.",
     "Not extra6 text-wrap-pretty, not r text-wrap-mode.",
     "nowrap is not pretty. File the a11y string."),
    ("transition", "none", "transform 400ms", "transition", "trans-shorthand", "trans_shorthand", 412,
     "CH-2", "CH-3", "CH-3", "c2", "c3", "c3", 80, 120, 64, "Trans 400", "Chips", "Keep", "chips",
     "`transition:transform 400ms` (shorthand) leaves stored pre-transition x at CH-3.",
     "Not r trans-duration, not r trans-property.",
     "Transition shorthand is live. Keep CH-2 by ref after it settles."),
    ("view-timeline-name", "none", "--view", "viewTimelineName", "view-tl-name", "view_tl_name", 412,
     "CH-2", "CH-3", "CH-3", "c2", "c3", "c3", 80, 120, 64, "View --view", "Chips", "Keep", "chips",
     "`view-timeline-name:--view` drives animation from visibility so stored none x is CH-3.",
     "Not r view-timeline-inset, not r scroll-timeline-name.",
     "Named view timelines are live. Keep CH-2 by ref."),
    ("view-transition-class", "none", "card", "viewTransitionClass", "view-trans-class", "view_trans_class", 412,
     "CD-3", "CD-4", "CD-4", "c3", "c4", "c3", 160, 160, 80, "Class card", "Cards", "Keep", "cards",
     "`view-transition-class:card` groups the morph so a click during it hits CD-4.",
     "Not this mill's view-trans-named, not r view-transition mill.",
     "Transition class is not the live ref. Keep CD-3 by ref."),
    ("margin", "0px", "24px", "margin", "margin-sh-24", "margin_sh_24", 412,
     "CH-4", "CH-5", "CH-5", "c4", "c5", "c5", 96, 120, 64, "Margin 24", "Chips", "Keep", "chips",
     "`margin:24px` (shorthand) restacks both axes so stored 0-margin x is CH-5.",
     "Not r margin-inline, not extra mill margin-block.",
     "The margin shorthand is live. Keep CH-4 by ref."),
    ("padding", "0px", "24px", "padding", "padding-sh-24", "padding_sh_24", 412,
     "CH-4", "CH-5", "CH-5", "c4", "c5", "c5", 96, 120, 64, "Pad 24", "Chips", "Keep", "chips",
     "`padding:24px` (shorthand) grows used size so stored 0-pad x is CH-5.",
     "Not r padding-inline, not r padding-block.",
     "The padding shorthand is live. Keep CH-4 by ref."),
    ("border", "0px none", "8px solid", "border", "border-sh-8", "border_sh_8", 404,
     "CH-2", "CH-3", "CH-3", "c2", "c3", "c3", 80, 88, 64, "Border 8", "Chips", "Keep", "chips",
     "`border:8px solid` (shorthand) grows a ring. Center click on the ring is not CH-2.",
     "Not extra7 border-current, not this mill's border-width-8.",
     "Border shorthand is paint+metrics. Keep the chip ref."),
    ("outline", "none", "8px auto", "outline", "outline-sh-8", "outline_sh_8", 404,
     "FL-3", "FL-4", "FL-4", "c3", "c4", "c4", 148, 148, 80, "Outline 8 auto", "Floats", "Keep", "floats",
     "`outline:8px auto` (shorthand) paints UA chrome. Screenshot of the ring is not FL-3.",
     "Not r outline-style, not this mill's outline-offset-12.",
     "Outline shorthand is paint. Keep the float ref."),
    ("scroll-padding-top", "0px", "24px", "scrollPaddingTop", "scroll-pad-top", "scroll_pad_top", 425,
     "LN-4", "LN-5", "LN-6", "c4", "c5", "c6", 240, 240, 48, "Pad top 24", "Lanes", "Keep", "lanes",
     "`scroll-padding-top:24px` insets the scrollport so stored 0-pad y is LN-6.",
     "Not r scroll-padding-block, not this mill's scroll-padding-istart.",
     "Physical scroll-padding-top is live. Keep the on-screen item ref."),
    ("scroll-margin-left", "0px", "24px", "scrollMarginLeft", "scroll-mar-left", "scroll_mar_left", 425,
     "LN-4", "LN-5", "LN-6", "c4", "c5", "c6", 240, 216, 24, "Margin left 24", "Lanes", "Keep", "lanes",
     "`scroll-margin-left:24px` pads snap so stored 0-margin x is LN-6.",
     "Not r scroll-margin-block, not this mill's scroll-margin-istart.",
     "Physical scroll-margin-left is live. Keep the on-screen item ref."),
    ("mask", "none", "url(#m) luminance", "mask", "mask-shorthand", "mask_shorthand", 404,
     "CD-3", "hole", "hole", "c3", "h1", "h1", 160, 160, 80, "Mask url", "Cards", "Keep", "cards",
     "`mask:url(#m) luminance` (shorthand) cuts the card. Stored none x is a hole.",
     "Not extra5 mask-image, not r mask-type.",
     "A mask shorthand hole is still the card ref."),
    ("background", "transparent", "Canvas url(#blob)", "background", "bg-shorthand", "bg_shorthand", 404,
     "BD-2", "BD-3", "BD-3", "c2", "c3", "c3", 140, 140, 80, "Bg shorthand", "Badges", "Keep", "badges",
     "`background:Canvas url(#blob)` (shorthand) paints a blob. Stored transparent x is empty.",
     "Not extra7 bg-canvas, not this mill's bg-image-gradient.",
     "Background shorthand is paint. Keep the badge ref."),
    ("font", "16px sans-serif", "700 24px ui-monospace", "font", "font-shorthand", "font_shorthand", 412,
     "GL-2", "GL-3", "GL-3", "c2", "c3", "c3", 88, 120, 56, "Font 700 24", "Glyphs", "Keep", "glyphs",
     "`font:700 24px ui-monospace` (shorthand) retimes glyphs so stored 16px sans x is GL-3.",
     "Not extra7 font-weight-700, not this mill's font-size-24.",
     "Font shorthand is live metrics. Keep GL-2 by ref."),
    ("border-image", "none", "url(#slice) 30 / 8px", "borderImage", "border-image-sh", "border_image_sh", 404,
     "CH-2", "CH-3", "CH-3", "c2", "c3", "c3", 80, 80, 64, "Image 30/8", "Chips", "Keep", "chips",
     "`border-image:url(#slice) 30 / 8px` (shorthand) paints a slice ring. A click on the slice is not CH-2.",
     "Not extra5 border-image-source, not r border-image-slice.",
     "Border-image shorthand is paint. Keep the chip ref."),
    ("container", "normal", "chip / inline-size", "container", "container-sh", "container_sh", 428,
     "CH-2", "CH-3", "CH-3", "c2", "c3", "c3", 80, 140, 64, "Container chip", "Chips", "Keep", "chips",
     "`container:chip / inline-size` (shorthand) makes CQ units resolve so stored normal x is CH-3.",
     "Not r container-name, not r container-type-size.",
     "Container shorthand is live. Keep CH-2 by ref."),
    ("offset", "auto", "path('M0,0 L40,0') 40px", "offset", "offset-sh", "offset_sh", 520,
     "BY-5", "BY-6", "BY-6", "c5", "c6", "c5", 80, 120, 40, "Offset path 40", "Floats", "Keep", "floats",
     "`offset:path(...) 40px` (shorthand) parks abspos at 40px so stored auto x is BY-6.",
     "Not r164 offset-path, not extra5 offset-anchor.",
     "Offset shorthand is live. Keep BY-5 by ref."),
    ("overflow-y", "visible", "auto", "overflowY", "overflow-y-auto", "overflow_y_auto", 425,
     "LN-4", "LN-5", "LN-6", "c4", "c5", "c6", 240, 240, 24, "Auto y", "Lanes", "Keep", "lanes",
     "`overflow-y:auto` (r scroll already) creates a y scrollport only if needed so stored visible y is LN-6.",
     "Not extra7 overflow-x-auto, not extra4 overflow-y-scroll.",
     "auto-y is not scroll. Keep the on-screen item ref."),
    ("cursor", "auto", "grab", "cursor", "cursor-grab", "cursor_grab", 404,
     "CH-2", "CH-3", "CH-3", "c2", "c3", "c3", 80, 80, 64, "Grab", "Chips", "Keep", "chips",
     "`cursor:grab` paints an open-hand glyph over CH-2. Screenshot of the glyph is not CH-3.",
     "Not extra7 cursor-not-allowed, not r cursor-none.",
     "The grab cursor is paint. Keep the chip ref."),
    ("cursor", "auto", "zoom-in", "cursor", "cursor-zoom-in", "cursor_zoom_in", 404,
     "CH-2", "CH-3", "CH-3", "c2", "c3", "c3", 80, 80, 64, "Zoom-in", "Chips", "Keep", "chips",
     "`cursor:zoom-in` paints a plus glyph over CH-2. Screenshot of the glyph is not CH-3.",
     "Not this mill's cursor-grab, not extra7 cursor-not-allowed.",
     "The zoom-in cursor is paint. Keep the chip ref."),
    ("pointer-events", "auto", "none", "pointerEvents", "pointer-events-none", "pointer_events_none", 410,
     "CH-2", "CH-3", "CH-3", "c2", "c3", "c3", 80, 80, 64, "None", "Chips", "Keep", "chips",
     "`pointer-events:none` lets the click fall through so stored auto x hits CH-3.",
     "Not r pointer-events-stroke, not r pointer-events mill clone.",
     "none is not stroke. Keep CH-2 by ref."),
    ("resize", "none", "both", "resize", "resize-both-box", "resize_both_box", 428,
     "CD-3", "CD-4", "CD-4", "c3", "c4", "c3", 160, 200, 120, "Both", "Cards", "Keep", "cards",
     "`resize:both` grows the used box so stored none x is CD-4.",
     "Not r resize-horizontal, not r resize-block.",
     "both is not horizontal. Keep CD-3 by ref."),
    ("user-select", "auto", "contain", "userSelect", "us-contain-select", "us_contain_select", 413,
     "LB-2", "LB-3", "LB-3", "c2", "c3", "c3", 24, 24, 48, "Contain", "Labels", "Keep", "labels",
     "`user-select:contain` clips the selection so OCR of a spilled highlight is LB-3.",
     "Not r user-select-none, not r user-select-all.",
     "contain is not none. File the a11y string."),
    ("display", "block", "none", "display", "display-none", "display_none", 410,
     "CH-2", "hole", "hole", "c2", "h1", "h1", 80, 80, 64, "None", "Chips", "Keep", "chips",
     "`display:none` removes the box. Stored block x is a hole.",
     "Not extra7 display-flex, not extra5 display-contents.",
     "none is still the chip if you use the ref, not the hole."),
    ("display", "block", "ruby", "display", "display-ruby", "display_ruby", 416,
     "GL-2", "GL-3", "GL-3", "c2", "c3", "c3", 88, 60, 56, "Ruby", "Glyphs", "Keep", "glyphs",
     "`display:ruby` packs annotations so stored block x is GL-3.",
     "Not extra7 display-flex, not extra6 display-table.",
     "ruby display is live. Keep GL-2 by ref."),
    ("position", "relative", "static", "position", "position-static", "position_static", 412,
     "AB-2", "AB-3", "AB-3", "c2", "c3", "c3", 16, 0, 48, "Static", "Abspos", "Keep", "abspos",
     "`position:static` (r relative already) drops the offset so stored relative x is empty.",
     "Not extra7 position-relative, not r position-absolute.",
     "static is not relative. Keep AB-2 by ref."),
    ("opacity", "1", "0", "opacity", "opacity-0", "opacity_0", 464,
     "SW-2", "SW-3", "SW-3", "c2", "c3", "c3", 154, 154, 88, "Opacity 0", "Blends", "Keep", "blends",
     "`opacity:0` (r 0.2 / 0.5 already) unpaints so a screenshot looks empty.",
     "Not extra7 opacity-02, not extra5 filter-opacity.",
     "0 is not unselected. Keep aria-selected / the ref."),
    ("zoom", "1", "1.5", "zoom", "zoom-15", "zoom_15", 412,
     "CD-3", "CD-4", "CD-4", "c3", "c4", "c3", 160, 240, 80, "Zoom 1.5", "Cards", "Keep", "cards",
     "`zoom:1.5` (r extra5 1.25 / extra6 0.8) grows the used box so stored unzoomed x is CD-4.",
     "Not extra5 zoom:1.25, not extra6 zoom-08.",
     "CSS zoom 1.5 is not scale(). Keep CD-3 by ref."),
    ("mix-blend-mode", "normal", "multiply", "mixBlendMode", "blend-multiply", "blend_multiply", 464,
     "SW-2", "SW-3", "SW-3", "c2", "c3", "c3", 154, 154, 88, "Multiply", "Blends", "Keep", "blends",
     "`mix-blend-mode:multiply` darkens so the selected chip looks empty.",
     "Not r bg-blend-multiply, not extra7 blend-saturation.",
     "multiply is not empty. Keep aria-selected / the ref."),
    ("backdrop-filter", "none", "invert(1)", "backdropFilter", "backdrop-invert", "backdrop_invert", 415,
     "CD-3", "CD-4", "CD-4", "c3", "c4", "c3", 160, 160, 80, "Backdrop invert", "Cards", "Keep", "cards",
     "`backdrop-filter:invert(1)` remaps paint so OCR / a screenshot blob is not CD-3.",
     "Not extra6 backdrop-blur, not extra5 backdrop-grayscale.",
     "Backdrop invert is paint. Keep CD-3 by ref."),
    ("filter", "none", "drop-shadow(6px 0 0 CanvasText)", "filter", "filter-drop-shadow", "filter_drop_shadow", 404,
     "CH-2", "CH-3", "CH-3", "c2", "c3", "c3", 80, 86, 64, "Drop-shadow", "Chips", "Keep", "chips",
     "`filter:drop-shadow(6px 0 0 CanvasText)` paints a sibling blob. A click on the shadow is not CH-2.",
     "Not r filter-blur, not extra5 filter-opacity.",
     "A drop-shadow is paint. Keep the chip ref."),
    ("rotate", "0deg", "y 40deg", "rotate", "rotate-y-40", "rotate_y_40", 520,
     "CD-3", "CD-4", "CD-4", "c3", "c4", "c3", 160, 148, 80, "Rotate Y 40", "Cards", "Keep", "cards",
     "`rotate:y 40deg` (r extra6 x 30deg) shears the hit diamond so stored 0deg x misses.",
     "Not extra6 rotate-x, not r rotate-turn.",
     "Y-rotate is live. Keep CD-3 by ref."),
    ("translate", "0px", "40px 0px", "translate", "translate-x-40", "translate_x_40", 412,
     "AB-2", "AB-3", "AB-3", "c2", "c3", "c3", 16, 56, 48, "Translate 40", "Abspos", "Keep", "abspos",
     "`translate:40px 0px` slides so stored 0 x is empty.",
     "Not r translate-block, not r313 translate property mill.",
     "2d translate is live. Keep AB-2 by ref."),
    ("scale", "1", "1.5", "scale", "scale-15", "scale_15", 412,
     "CD-3", "CD-4", "CD-4", "c3", "c4", "c3", 160, 240, 80, "Scale 1.5", "Cards", "Keep", "cards",
     "`scale:1.5` (r 0.8 / x-only / y-only) grows so stored unscaled x is CD-4.",
     "Not r648 scale-y, not extra5 scale-x, not r544 scale:0.8.",
     "Uniform 1.5 scale is live. Keep CD-3 by ref."),
    ("will-change", "auto", "transform", "willChange", "will-change-transform", "will_change_transform", 412,
     "CD-3", "CD-4", "CD-4", "c3", "c4", "c3", 160, 160, 80, "Will transform", "Cards", "Keep", "cards",
     "`will-change:transform` promotes a layer so stored auto x is a different compositor box.",
     "Not r will-change-contents, not r will-change-scroll.",
     "will-change:transform is live. Keep CD-3 by ref."),
    ("contain", "none", "inline-size", "contain", "contain-inline", "contain_inline", 428,
     "CH-2", "CH-3", "CH-3", "c2", "c3", "c3", 180, 80, 70, "Inline-size", "Chips", "Keep", "chips",
     "`contain:inline-size` sizes independently so stored none x is CH-3.",
     "Not r contain-size, not r contain-inline-size mill clone.",
     "contain:inline-size is live. Keep CH-2 by ref."),
    ("content-visibility", "visible", "auto", "contentVisibility", "cv-auto", "cv_auto", 410,
     "RW-12", "RW-13", "RW-1", "c12", "c13", "c1", 0, 0, 480, "Auto", "Rows", "Keep", "rows",
     "`content-visibility:auto` (r hidden already) skips offscreen rows so stale scrollY lands empty.",
     "Not r251 content-visibility:auto mill clone, not extra7 content-visibility-hidden.",
     "auto virtualize is not hidden. Re-find the row ref."),
    ("white-space", "normal", "pre-line", "whiteSpace", "ws-pre-line", "ws_pre_line", 413,
     "LB-2", "LB-3", "LB-3", "c2", "c3", "c3", 24, 24, 48, "Pre-line", "Labels", "Keep", "labels",
     "`white-space:pre-line` keeps newlines so a normal wrap line is LB-3.",
     "Not extra6 break-spaces, not r white-space-pre-wrap.",
     "pre-line is not pre-wrap. File the a11y string."),
    ("word-break", "normal", "auto-phrase", "wordBreak", "break-auto-phrase", "break_auto_phrase", 400,
     "LB-2", "LB-3", "LB-3", "c2", "c3", "c3", 24, 24, 48, "Auto-phrase", "Labels", "Keep", "labels",
     "`word-break:auto-phrase` forbids mid-phrase breaks so OCR BIND… is a different wrap.",
     "Not extra6 keep-all-cjk, not r442 word-break:break-all.",
     "auto-phrase is not break-all. File the a11y string."),
    ("line-break", "auto", "anywhere", "lineBreak", "line-break-any", "line_break_any", 400,
     "LB-2", "LB-3", "LB-3", "c2", "c3", "c3", 24, 24, 48, "Anywhere", "Labels", "Keep", "labels",
     "`line-break:anywhere` allows breaks at any point so OCR BIND… is a different wrap.",
     "Not r line-break-loose, not r line-break-anywhere mill clone.",
     "anywhere is not loose. File the a11y string."),
    ("writing-mode", "horizontal-tb", "sideways-rl", "writingMode", "writing-sideways-rl", "writing_sideways_rl", 416,
     "TX-2", "TX-5", "TX-5", "c2", "c5", "c5", 40, 24, 36, "Sideways rl", "Text", "Keep", "text",
     "`writing-mode:sideways-rl` (r sideways-lr / vertical-rl already) stacks the other way so stored horizontal x is TX-5.",
     "Not extra6 vertical-rl, not r700 sideways-lr.",
     "sideways-rl is not vertical-rl. Keep TX-2 by ref."),
    ("unicode-bidi", "normal", "isolate", "unicodeBidi", "bidi-isolate", "bidi_isolate", 416,
     "TX-2", "TX-5", "TX-5", "c2", "c5", "c5", 40, 24, 36, "Isolate", "Text", "Keep", "text",
     "`unicode-bidi:isolate` creates a bidi island so stored normal x is TX-5.",
     "Not r unicode-bidi-plaintext, not extra7 isolation-isolate.",
     "bidi isolate is not CSS isolation. Keep TX-2 by ref."),
    ("vertical-align", "baseline", "super", "verticalAlign", "valign-super", "valign_super", 410,
     "GL-2", "GL-3", "GL-3", "c2", "c3", "c3", 88, 88, 40, "Super", "Glyphs", "Keep", "glyphs",
     "`vertical-align:super` raises glyphs so stored baseline y is GL-3.",
     "Not r vertical-align-middle, not r vertical-align-top.",
     "super is not middle. Keep GL-2 by ref."),
    ("list-style-position", "outside", "inside", "listStylePosition", "list-pos-inside", "list_pos_inside", 449,
     "LI-2", "mark", "mark", "c2", "m1", "m1", 24, 8, 40, "Inside", "Lists", "Keep", "lists",
     "`list-style-position:inside` pulls the marker into the item. Clicking the marker slot is not LI-2.",
     "Not extra6 display-list-item, not r list-style-type-none.",
     "An inside marker is not the item. Keep the listitem ref."),
    ("quotes", "auto", "'\"' '\"'", "quotes", "quotes-custom", "quotes_custom", 415,
     "TX-2", "TX-3", "TX-3", "c2", "c3", "c3", 40, 24, 36, "Custom quotes", "Text", "Keep", "text",
     "`quotes:'\"' '\"'` paints ASCII quotes so OCR of neighboring text is TX-3.",
     "Not extra7 quotes-none, not r hanging-first.",
     "Custom quotes are still TX-2. File the a11y string."),
    ("column-gap", "0px", "24px", "columnGap", "column-gap-24", "column_gap_24", 412,
     "CH-3", "CH-4", "CH-4", "c3", "c4", "c4", 120, 144, 64, "Col gap 24", "Chips", "Keep", "chips",
     "`column-gap:24px` (r gap shorthand already) restacks columns so stored 0-gap x is CH-4.",
     "Not r373 column-gap mill clone, not extra mill gap-shorthand.",
     "column-gap is not the gap shorthand. Keep CH-3 by ref."),
    ("row-gap", "0px", "24px", "rowGap", "row-gap-24", "row_gap_24", 410,
     "RW-2", "RW-3", "RW-3", "c2", "c3", "c3", 24, 24, 72, "Row gap 24", "Rows", "Keep", "rows",
     "`row-gap:24px` (r gap shorthand already) pushes the next row so stored 0-gap y is RW-3.",
     "Not r365 row-gap mill clone, not extra mill gap-shorthand.",
     "row-gap is not the gap shorthand. Keep RW-2 by ref."),
    ("hyphenate-character", "auto", "'='", "hyphenateCharacter", "hyphenate-eq", "hyphenate_eq", 414,
     "BINDING-COMPLETE", "BIND…", "BIND", "c1", "c1", "c0", 24, 24, 48, "Hyphen =", "Labels", "Keep", "labels",
     "`hyphenate-character:'='` paints an equals at the break so OCR BIND… is a different wrap.",
     "Not r hyphenate-character mill clone, not extra6 hyphens-off.",
     "A custom hyphen character is not auto. File the a11y string."),
    ("image-resolution", "from-image", "300dpi", "imageResolution", "image-res-300", "image_res_300", 404,
     "BD-2", "BD-3", "BD-3", "c2", "c3", "c3", 140, 100, 80, "300dpi", "Badges", "Keep", "badges",
     "`image-resolution:300dpi` retimes the replaced box so stored from-image x is empty.",
     "Not r image-orientation, not extra6 object-fit-contain.",
     "image-resolution is paint/metrics. Keep the badge ref."),
    ("max-lines", "none", "2", "maxLines", "max-lines-2", "max_lines_2", 414,
     "BINDING-COMPLETE", "BIND…", "BIND", "c1", "c1", "c0", 24, 24, 48, "Max 2", "Labels", "Keep", "labels",
     "`max-lines:2` clamps so OCR BIND… is a different wrap.",
     "Not r line-clamp-1, not r -webkit-line-clamp mill.",
     "max-lines is not line-clamp. File the a11y string."),
    ("continue", "auto", "discard", "continue", "continue-discard", "continue_discard", 414,
     "BINDING-COMPLETE", "BIND…", "BIND", "c1", "c1", "c0", 24, 24, 48, "Discard", "Labels", "Keep", "labels",
     "`continue:discard` drops overflow fragments so OCR BIND… is a different wrap.",
     "Not this mill's max-lines-2, not r line-clamp-1.",
     "discard is not clamp. File the a11y string."),
    ("-webkit-text-stroke", "0px", "2px CanvasText", "webkitTextStroke", "text-stroke-2", "text_stroke_2", 404,
     "GL-2", "GL-3", "GL-3", "c2", "c3", "c3", 88, 92, 56, "Stroke 2", "Glyphs", "Keep", "glyphs",
     "`-webkit-text-stroke:2px CanvasText` fattens glyphs so a click on the stroke is not GL-2.",
     "Not r stroke-width, not this mill's stroke-current.",
     "Text-stroke is paint. Keep the glyph ref."),
]


GENERA = [
    "huperzia", "diphasiastrum", "palhinhaea", "phlegmariurus", "spinulum",
    "phaeoceros", "notothylas", "megaceros", "dendroceros", "folioceros",
    "paraphymatoceros", "phymatoceros", "pteridium", "adiantum", "thelypteris",
    "athyrium", "cystopteris", "woodsia", "cheilanthes", "pellaea",
    "davallia", "sphaeropteris", "tmesipteris", "helminthostachys", "danaea",
    "christensenia", "dicranopteris", "sticherus", "hymenophyllum", "trichomanes",
    "crepidomanes", "vittaria", "antrophyum", "elaphoglossum", "lomariopsis",
    "nephrolepis", "oleandra", "davallodes", "arthropteris", "leptopteris",
    "todea", "osmundastrum", "plagiogyria", "culcita", "thyrsopteris",
    "lophosoria", "metaxya", "lonchitis", "hypolepis", "dennstaedtia",
    "microlepia", "saccoloma", "lindsaea", "odontoosoria", "sphenomeris",
    "tapeinidium", "cheiropleuria", "dipteris", "matonia", "phanerosorus",
    "schizaea", "actinostachys", "lygodium", "anemia", "mohria",
    "pilularia", "regnellidium", "marsilea", "salvinia", "azolla",
    "lepidodendron", "sigillaria", "calamites", "sphenophyllum", "rhynia",
    "cooksonia", "zosterophyllum", "asteroxylon", "baragwanathia", "sawdonia",
    "psilophyton", "pertica", "trimerophyton", "aarabia", "horneophyton",
    "aglaophyton", "nothia", "kidstonophyton", "langiophyton", "sciadophyton",
    "zosterophyllites", "gosslingia", "crenaticaulis", "bathurstia", "deheubarthia",
    "tarella", "thrinkophyton", "huia", "gumuia", "hsua", "sawdoniales",
]


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
    raise SystemExit(f"keep {genus}")


def main() -> int:
    used_w = load_set("widgets")
    used_es = load_set("errslugs")
    used_pl = load_set("places")
    used_pr = load_set("prefixes")
    used_ax = load_set("auxes")
    used_seed = load_set("seeds")
    used_err = load_set("errs")
    used_keep: set[str] = set()

    assert len(PLANTS) <= len(GENERA), (len(PLANTS), len(GENERA))
    rows = []
    nexts = [p[4] for p in PLANTS[1:]] + ["catalog continue."]
    for i, plant in enumerate(PLANTS):
        (css, fr, to, js, widget, err, code, item, neigh, fail, ref, nref, fref,
         x0, x1, y, btn, title, verb, path, new, not_, teach) = plant
        if code == 409:
            raise SystemExit(f"{widget}: 409 banned")
        if widget in used_w:
            raise SystemExit(f"widget collision {widget}")
        used_w.add(widget)
        if err in used_err:
            err = err + "_x8"
            if err in used_err:
                raise SystemExit(f"err collision {err}")
        used_err.add(err)
        prefix = mint("".join(ch for ch in widget if ch.isalnum())[:4] or "e8p", used_pr)
        aux = mint(("".join(ch for ch in widget if ch.isalnum())[2:6] or "e8a") + "x", used_ax)
        if prefix == aux:
            aux = mint(aux + "z", used_ax)
        genus = GENERA[i]
        ok = genus + "moor"
        bad = genus + "crag"
        if ok in used_pl or bad in used_pl:
            ok = genus + "dale"
            bad = genus + "kirk"
        if ok in used_pl or bad in used_pl:
            ok = genus + "shaw"
            bad = genus + "beck"
        if ok in used_pl or bad in used_pl or ok == bad:
            raise SystemExit(f"place collision {ok} {bad}")
        used_pl.add(ok)
        used_pl.add(bad)
        slug = f"{aux}-{code}"
        if slug in used_es:
            raise SystemExit(f"err_slug collision {slug}")
        used_es.add(slug)
        seed_ok = f"css-{widget}"
        seed_bad = f"css-{widget}-{code}"
        if seed_ok in used_seed or seed_bad in used_seed:
            seed_ok = f"css-{widget}-x8"
            seed_bad = f"css-{widget}-x8-{code}"
        if seed_ok in used_seed or seed_bad in used_seed:
            raise SystemExit(f"seed collision {seed_ok}")
        used_seed.add(seed_ok)
        used_seed.add(seed_bad)
        keep = keep_code(genus, used_keep)
        note = f"{item} {genus}"
        nxt = nexts[i].replace("-", " ") if isinstance(nexts[i], str) else "catalog continue."
        # next field is human leftover hint
        nxt = PLANTS[i + 1][4] if i + 1 < len(PLANTS) else "catalog continue."
        row = (
            prefix, aux, ok, bad, widget, slug, code, err,
            css, fr, to, js, item, neigh, fail, ref, nref, fref,
            x0, x1, y, btn, title, verb, path, keep, note, seed_ok, seed_bad,
            new, not_, teach, nxt + ".",
        )
        if len(row) != len(KEYS):
            raise SystemExit(f"row len {len(row)} != {len(KEYS)}")
        rows.append(row)

    out = HERE / "brw-mill-r395-extra8.py"
    lines = [
        '"""Leftover CSS plants r745+."""',
        "KEYS = (",
        '    "prefix", "aux", "ok_place", "bad_place", "widget", "err_slug", "code", "err",',
        '    "css", "from", "to", "js", "item", "neigh", "fail_item", "ref", "nref", "fref",',
        '    "x0", "x1", "y", "btn", "title", "verb", "path", "keep", "note", "seed_ok", "seed_bad",',
        '    "new", "not", "teach", "next",',
        ")",
        "ROWS = [",
    ]
    for row in rows:
        parts = []
        for v in row:
            parts.append(repr(v))
        lines.append("(" + ",".join(parts) + "),")
    lines.append("]")
    lines.append("EXTRA = [dict(zip(KEYS, row)) for row in ROWS]")
    lines.append("")
    out.write_text("\n".join(lines))
    print(f"wrote {out} plants={len(rows)} last={rows[-1][4]} {rows[-1][2]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
