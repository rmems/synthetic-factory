#!/usr/bin/env python3
"""Generate leftover CSS extra10 plants r957+ (unique vs extra8/extra9)."""
from __future__ import annotations

import importlib.util
from pathlib import Path

SETS = Path("/tmp/brw-used/sets")
HERE = Path(__file__).resolve().parent
KEYS = (
    "prefix", "aux", "ok_place", "bad_place", "widget", "err_slug", "code", "err",
    "css", "from", "to", "js", "item", "neigh", "fail_item", "ref", "nref", "fref",
    "x0", "x1", "y", "btn", "title", "verb", "path", "keep", "note", "seed_ok", "seed_bad",
    "new", "not", "teach", "next",
)

# template: item,neigh,fail,ref,nref,fref,x0,x1,y,title,path
T = {
    "chips": ("CH-2", "CH-3", "CH-3", "c2", "c3", "c3", 80, 96, 64, "Chips", "chips"),
    "chiphole": ("CH-2", "hole", "hole", "c2", "h1", "h1", 80, 80, 64, "Chips", "chips"),
    "glyphs": ("GL-2", "GL-3", "GL-3", "c2", "c3", "c3", 88, 110, 56, "Glyphs", "glyphs"),
    "cards": ("CD-3", "CD-4", "CD-4", "c3", "c4", "c3", 160, 200, 80, "Cards", "cards"),
    "cardhole": ("CD-3", "hole", "hole", "c3", "h1", "h1", 160, 160, 80, "Cards", "cards"),
    "badges": ("BD-2", "BD-3", "BD-3", "c2", "c3", "c3", 140, 126, 80, "Badges", "badges"),
    "rows": ("RW-2", "RW-3", "RW-3", "c2", "c3", "c3", 24, 24, 48, "Rows", "rows"),
    "text": ("TX-2", "TX-5", "TX-5", "c2", "c5", "c5", 40, 24, 36, "Text", "text"),
    "labels": ("LB-2", "LB-3", "LB-3", "c2", "c3", "c3", 24, 24, 48, "Labels", "labels"),
    "bind": ("BINDING-COMPLETE", "BIND…", "BIND", "c1", "c1", "c0", 24, 24, 48, "Labels", "labels"),
    "lanes": ("LN-4", "LN-5", "LN-6", "c4", "c5", "c6", 240, 216, 24, "Lanes", "lanes"),
    "floats": ("FL-3", "FL-4", "FL-4", "c3", "c4", "c4", 148, 148, 80, "Floats", "floats"),
    "abspos": ("AB-2", "AB-3", "AB-3", "c2", "c3", "c3", 16, 40, 48, "Abspos", "abspos"),
    "blends": ("SW-2", "SW-3", "SW-3", "c2", "c3", "c3", 154, 154, 88, "Blends", "blends"),
    "eq": ("EQ-4", "EQ-5", "EQ-5", "c4", "c5", "c5", 110, 92, 88, "Equations", "equations"),
    "lists": ("LI-2", "mark", "mark", "c2", "m1", "m1", 8, 24, 40, "Lists", "lists"),
    "verbs": ("OPEN", "FILE", "FILE", "c1", "c2", "c2", 110, 110, 70, "Verbs", "verbs"),
    "by": ("BY-5", "BY-6", "BY-6", "c5", "c6", "c5", 80, 120, 40, "Floats", "floats"),
}

# css, from, to, js, widget, err, code, tmpl, btn, new, not, teach
PLANTS = [
    ("font-size", "16px", "10px", "fontSize", "font-size-10", "font_size_10", 412, "glyphs", "Size 10",
     "`font-size:10px` shrinks glyphs so stored 16px x is GL-3.", "Not extra8 font-size-24, not extra9 font-size-12.", "10px is live. Keep GL-2 by ref."),
    ("font-size", "16px", "18px", "fontSize", "font-size-18", "font_size_18", 412, "glyphs", "Size 18",
     "`font-size:18px` grows glyphs so stored 16px x is GL-3.", "Not extra9 font-size-32, not extra8 font-size-24.", "18px is not 24px. Keep GL-2 by ref."),
    ("font-size", "16px", "48px", "fontSize", "font-size-48", "font_size_48", 412, "glyphs", "Size 48",
     "`font-size:48px` grows glyphs so stored 16px x is GL-3.", "Not extra9 font-size-32, not extra8 font-size-24.", "48px is not 32px. Keep GL-2 by ref."),
    ("font-family", "sans-serif", "cursive", "fontFamily", "font-family-cursive", "font_family_cursive", 412, "glyphs", "Cursive",
     "`font-family:cursive` retimes advances so stored sans x is GL-3.", "Not extra8 font-family-mono, not extra9 font-family-serif.", "Cursive metrics are live. Keep GL-2 by ref."),
    ("zoom", "1", "0.25", "zoom", "zoom-025", "zoom_025", 412, "cards", "Zoom 0.25",
     "`zoom:0.25` shrinks the used box so stored unzoomed x is CD-4.", "Not extra9 zoom-05, not extra8 zoom-15.", "CSS zoom 0.25 is not scale(). Keep CD-3 by ref."),
    ("zoom", "1", "3", "zoom", "zoom-3", "zoom_3", 412, "cards", "Zoom 3",
     "`zoom:3` triples the used box so stored unzoomed x is CD-4.", "Not extra9 zoom-2, not extra8 zoom-15.", "CSS zoom 3 is not scale(3). Keep CD-3 by ref."),
    ("opacity", "1", "0.4", "opacity", "opacity-04", "opacity_04", 464, "blends", "Opacity 0.4",
     "`opacity:0.4` fades so a screenshot looks unselected.", "Not extra9 opacity-08, not extra8 opacity-0.", "0.4 is not unselected. Keep aria-selected / the ref."),
    ("scale", "1", "0.5", "scale", "scale-05", "scale_05", 412, "cards", "Scale 0.5",
     "`scale:0.5` shrinks so stored unscaled x is CD-4.", "Not extra8 scale-15, not extra9 scale-2.", "Uniform 0.5 scale is live. Keep CD-3 by ref."),
    ("rotate", "0deg", "x 15deg", "rotate", "rotate-x-15", "rotate_x_15", 520, "cards", "Rotate X 15",
     "`rotate:x 15deg` shears the hit diamond so stored 0deg x misses.", "Not extra6 rotate-x 30, not extra8 rotate-y-40.", "X-rotate 15 is not 30. Keep CD-3 by ref."),
    ("translate", "0px", "0px 0px 20px", "translate", "translate-z-20", "translate_z_20", 520, "cards", "Translate z 20",
     "`translate:0 0 20px` lifts on z so stored 0 x misses under perspective.", "Not extra8 translate-x-40, not extra9 translate-y-40.", "Z translate is live. Keep CD-3 by ref."),
    ("cursor", "auto", "alias", "cursor", "cursor-alias", "cursor_alias", 404, "chips", "Alias",
     "`cursor:alias` paints an alias glyph over CH-2. Screenshot of the glyph is not CH-3.", "Not extra8 cursor-grab, not extra9 cursor-copy mill.", "The alias cursor is paint. Keep the chip ref."),
    ("cursor", "auto", "cell", "cursor", "cursor-cell", "cursor_cell", 404, "chips", "Cell",
     "`cursor:cell` paints a cell glyph over CH-2. Screenshot of the glyph is not CH-3.", "Not extra9 cursor-crosshair, not extra8 cursor-grab.", "The cell cursor is paint. Keep the chip ref."),
    ("cursor", "auto", "copy", "cursor", "cursor-copy", "cursor_copy", 404, "chips", "Copy",
     "`cursor:copy` paints a plus-copy glyph over CH-2. Screenshot of the glyph is not CH-3.", "Not extra8 cursor-zoom-in, not extra9 cursor-move.", "The copy cursor is paint. Keep the chip ref."),
    ("cursor", "auto", "no-drop", "cursor", "cursor-no-drop", "cursor_no_drop", 404, "chips", "No-drop",
     "`cursor:no-drop` paints a banned-drop glyph over CH-2. Screenshot of the glyph is not CH-3.", "Not extra7 cursor-not-allowed, not extra9 cursor-wait.", "The no-drop cursor is paint. Keep the chip ref."),
    ("cursor", "auto", "all-scroll", "cursor", "cursor-all-scroll", "cursor_all_scroll", 404, "chips", "All-scroll",
     "`cursor:all-scroll` paints a pan glyph over CH-2. Screenshot of the glyph is not CH-3.", "Not extra9 cursor-move, not extra8 cursor-grab.", "The all-scroll cursor is paint. Keep the chip ref."),
    ("cursor", "auto", "ns-resize", "cursor", "cursor-ns-resize", "cursor_ns_resize", 404, "chips", "Ns-resize",
     "`cursor:ns-resize` paints a vertical splitter over CH-2. Screenshot of the glyph is not CH-3.", "Not extra9 cursor-row-resize, not extra9 cursor-col-resize.", "The ns-resize cursor is paint. Keep the chip ref."),
    ("cursor", "auto", "ew-resize", "cursor", "cursor-ew-resize", "cursor_ew_resize", 404, "chips", "Ew-resize",
     "`cursor:ew-resize` paints a horizontal splitter over CH-2. Screenshot of the glyph is not CH-3.", "Not extra9 cursor-col-resize, not this mill's ns-resize.", "The ew-resize cursor is paint. Keep the chip ref."),
    ("cursor", "auto", "nesw-resize", "cursor", "cursor-nesw-resize", "cursor_nesw_resize", 404, "chips", "Nesw-resize",
     "`cursor:nesw-resize` paints a diagonal splitter over CH-2. Screenshot of the glyph is not CH-3.", "Not this mill's ns-resize, not extra9 cursor-move.", "The nesw-resize cursor is paint. Keep the chip ref."),
    ("cursor", "auto", "nwse-resize", "cursor", "cursor-nwse-resize", "cursor_nwse_resize", 404, "chips", "Nwse-resize",
     "`cursor:nwse-resize` paints the other diagonal over CH-2. Screenshot of the glyph is not CH-3.", "Not this mill's nesw-resize, not extra9 cursor-col-resize.", "The nwse-resize cursor is paint. Keep the chip ref."),
    ("cursor", "auto", "vertical-text", "cursor", "cursor-vertical-text", "cursor_vertical_text", 404, "chips", "Vertical-text",
     "`cursor:vertical-text` paints a vertical I-beam over CH-2. Screenshot of the glyph is not CH-3.", "Not extra9 cursor-help, not extra8 cursor-grab.", "The vertical-text cursor is paint. Keep the chip ref."),
    ("cursor", "auto", "context-menu", "cursor", "cursor-context-menu", "cursor_context_menu", 404, "chips", "Context-menu",
     "`cursor:context-menu` paints a menu glyph over CH-2. Screenshot of the glyph is not CH-3.", "Not extra9 cursor-help, not extra9 cursor-progress.", "The context-menu cursor is paint. Keep the chip ref."),
    ("display", "block", "run-in", "display", "display-run-in", "display_run_in", 412, "chips", "Run-in",
     "`display:run-in` packs into the next block so stored block x is CH-3.", "Not extra9 display-inline, not extra8 display-ruby.", "run-in is live. Keep CH-2 by ref."),
    ("display", "block", "table-caption", "display", "display-table-caption", "display_table_caption", 410, "rows", "Table-caption",
     "`display:table-caption` parks a caption box so stored block y is RW-3.", "Not extra9 caption-bottom, not extra9 display-table-row.", "table-caption is live. Keep RW-2 by ref."),
    ("overflow-x", "visible", "overlay", "overflowX", "overflow-x-overlay", "overflow_x_overlay", 425, "lanes", "Overlay x",
     "`overflow-x:overlay` draws a floating x scrollbar so stored visible x is LN-6.", "Not extra9 overflow-y-overlay, not extra7 overflow-x-auto.", "overlay-x is not auto. Keep the on-screen item ref."),
    ("overflow-y", "auto", "visible", "overflowY", "overflow-y-visible", "overflow_y_visible", 425, "lanes", "Visible y",
     "`overflow-y:visible` drops the y scrollport so stored auto y is LN-6.", "Not extra8 overflow-y-auto, not extra9 overflow-y-overlay.", "visible-y is not auto. Keep the on-screen item ref."),
    ("backdrop-filter", "none", "opacity(0.4)", "backdropFilter", "backdrop-opacity", "backdrop_opacity", 415, "cards", "Backdrop opacity 0.4",
     "`backdrop-filter:opacity(0.4)` fades the backdrop so a screenshot blob is not CD-3.", "Not extra8 backdrop-invert, not extra9 backdrop-saturate.", "Backdrop opacity is paint. Keep CD-3 by ref."),
    ("backdrop-filter", "none", "hue-rotate(90deg)", "backdropFilter", "backdrop-hue", "backdrop_hue", 415, "cards", "Backdrop hue 90",
     "`backdrop-filter:hue-rotate(90deg)` remaps paint so a screenshot blob is not CD-3.", "Not extra5 filter-hue-rotate, not extra8 backdrop-invert.", "Backdrop hue-rotate is paint. Keep CD-3 by ref."),
    ("letter-spacing", "normal", "-0.05em", "letterSpacing", "letter-spacing-neg", "letter_spacing_neg", 412, "glyphs", "Tracking -0.05em",
     "`letter-spacing:-0.05em` tightens glyphs so stored normal x is GL-3.", "Not extra9 letter-spacing-em, not extra8 font-size-24.", "Negative tracking is live. Keep GL-2 by ref."),
    ("word-spacing", "normal", "0", "wordSpacing", "word-spacing-0", "word_spacing_0", 412, "glyphs", "Word 0",
     "`word-spacing:0` collapses word gaps so stored normal x is GL-3.", "Not extra9 word-spacing-em, not extra9 letter-spacing-em.", "Zero word-spacing is live. Keep GL-2 by ref."),
    ("text-indent", "0px", "-24px", "textIndent", "text-indent-neg", "text_indent_neg", 412, "text", "Indent -24",
     "`text-indent:-24px` hanging-indents so stored 0 x is TX-5.", "Not extra9 text-indent-24, not extra7 text-align-center.", "Negative indent is live. Keep TX-2 by ref."),
    ("tab-size", "8", "2", "tabSize", "tab-size-2", "tab_size_2", 413, "labels", "Tab 2",
     "`tab-size:2` retimes tab stops so a stored tab-8 wrap line is LB-3.", "Not extra9 tab-size-4, not extra8 ws-pre-line.", "tab-size 2 is live. File the a11y string."),
    ("outline-width", "0px", "1px", "outlineWidth", "outline-width-1", "outline_width_1", 404, "floats", "Outline 1",
     "`outline-width:1px` paints hairline UA chrome. Screenshot of the ring is not FL-3.", "Not extra9 outline-width-8, not extra8 outline-sh-8.", "1px outline is paint. Keep the float ref."),
    ("box-shadow", "none", "8px 0 0 CanvasText", "boxShadow", "box-shadow-xy", "box_shadow_xy", 404, "chips", "Offset 8",
     "`box-shadow:8px 0 0` paints a sibling blob. A click on the shadow is not CH-2.", "Not extra9 box-shadow-inset, not extra8 filter-drop-shadow.", "Offset shadow is paint. Keep the chip ref."),
    ("object-fit", "contain", "cover", "objectFit", "object-fit-cover-run", "object_fit_cover_run", 404, "badges", "Fit cover",
     "`object-fit:cover` (r contain already) crops the blob. Stored contain x is empty.", "Not extra9 object-fit-none-box, not extra6 object-fit-contain.", "cover is paint. Keep the badge ref."),
    ("object-position", "50% 50%", "100% 0", "objectPosition", "object-pos-right", "object_pos_right", 404, "badges", "Pos right top",
     "`object-position:100% 0` slides the replaced box so stored center x is empty.", "Not extra9 object-pos-left, not extra8 object-view-inset.", "Right object-position is paint. Keep the badge ref."),
    ("flex-grow", "0", "1", "flexGrow", "flex-grow-1", "flex_grow_1", 428, "chips", "Grow 1",
     "`flex-grow:1` eats free space so stored grow-0 x is CH-3.", "Not extra9 flex-grow-2, not r394 flex-grow.", "grow 1 is not 2. Keep CH-2 by ref."),
    ("order", "0", "-1", "order", "order-n1", "order_n1", 428, "chips", "Order -1",
     "`order:-1` pulls the item first so stored 0 x is CH-3.", "Not extra9 order-2, not extra8 reading-order-2.", "flex order -1 is live. Keep CH-2 by ref."),
    ("column-count", "auto", "2", "columnCount", "column-count-2", "column_count_2", 416, "text", "Count 2",
     "`column-count:2` fragments so stored auto x is TX-5.", "Not extra9 column-count-3, not extra8 page-landscape.", "column-count 2 is not 3. Keep TX-2 by ref."),
    ("column-width", "auto", "8em", "columnWidth", "column-width-8em", "column_width_8em", 416, "text", "Width 8em",
     "`column-width:8em` fragments so stored auto x is TX-5.", "Not extra9 column-width-12em, not extra9 column-count-3.", "8em is not 12em. Keep TX-2 by ref."),
    ("column-span", "all", "none", "columnSpan", "column-span-none", "column_span_none", 416, "text", "Span none",
     "`column-span:none` (r all already) drops the stretch so stored all x is TX-5.", "Not extra9 column-span-all, not extra9 column-count-3.", "none is not all. Keep TX-2 by ref."),
    ("column-fill", "balance", "auto", "columnFill", "column-fill-auto", "column_fill_auto", 416, "text", "Fill auto",
     "`column-fill:auto` (r extra9 balance) fills sequentially so stored balance x is TX-5.", "Not extra9 column-fill-balance, not extra9 column-count-3.", "auto fill is not balance. Keep TX-2 by ref."),
    ("background-clip", "border-box", "padding-box", "backgroundClip", "bg-clip-padding", "bg_clip_padding", 404, "badges", "Clip padding",
     "`background-clip:padding-box` insets the blob so stored border-box x is empty.", "Not extra9 background-clip-text, not extra8 bg-image-gradient.", "padding-box clip is paint. Keep the badge ref."),
    ("background-origin", "padding-box", "border-box", "backgroundOrigin", "bg-origin-border", "bg_origin_border", 404, "badges", "Origin border",
     "`background-origin:border-box` expands the blob so stored padding-box x is empty.", "Not extra9 bg-origin-content, not extra8 bg-shorthand.", "border-box origin is paint. Keep the badge ref."),
    ("background-attachment", "scroll", "fixed", "backgroundAttachment", "bg-attach-fixed-run", "bg_attach_fixed_run", 404, "badges", "Attach fixed",
     "`background-attachment:fixed` leaves a screenshot blob at viewport x after scroll.", "Not extra9 bg-attach-local, not r1913 background-attachment:fixed mill.", "fixed attachment is paint. Keep the badge ref."),
    ("image-orientation", "from-image", "flip", "imageOrientation", "image-orient-flip", "image_orient_flip", 404, "badges", "Orient flip",
     "`image-orientation:flip` mirrors the replaced box so stored from-image x is empty.", "Not extra9 image-orient-none, not extra8 image-res-300.", "flip orientation is paint. Keep the badge ref."),
    ("accent-color", "auto", "currentColor", "accentColor", "accent-current", "accent_current", 464, "blends", "Accent current",
     "`accent-color:currentColor` remaps the checked fill so a screenshot looks empty.", "Not extra9 accent-canvas, not extra7 color-canvas.", "currentColor accent is not unchecked. Keep aria-checked / the ref."),
    ("appearance", "none", "textfield", "appearance", "appearance-textfield", "appearance_textfield", 404, "chips", "Textfield",
     "`appearance:textfield` restores field chrome so stored none x is CH-3.", "Not extra9 appearance-auto, not r appearance-none.", "textfield appearance is live. Keep CH-2 by ref."),
    ("touch-action", "auto", "pan-left", "touchAction", "touch-pan-left", "touch_pan_left", 425, "lanes", "Pan left",
     "`touch-action:pan-left` forbids right pans so stored auto x is LN-6.", "Not extra9 touch-pan-y, not r touch-pan-x.", "pan-left is not pan-x. Keep the on-screen item ref."),
    ("overscroll-behavior", "none", "auto", "overscrollBehavior", "overscroll-auto-run", "overscroll_auto_run", 425, "lanes", "Overscroll auto",
     "`overscroll-behavior:auto` (r extra9 none) restores the chain so stored none x is LN-6.", "Not extra9 overscroll-none, not r overscroll-contain.", "auto is not none. Keep the on-screen item ref."),
    ("scroll-snap-stop", "always", "normal", "scrollSnapStop", "snap-stop-normal", "snap_stop_normal", 425, "lanes", "Stop normal",
     "`scroll-snap-stop:normal` (r extra9 always) allows skipping so stored always x is LN-6.", "Not extra9 snap-stop-always, not extra scroll-snap-type.", "normal stop is not always. Keep the on-screen item ref."),
    ("line-height", "normal", "1.5", "lineHeight", "line-height-15", "line_height_15", 410, "rows", "Line 1.5",
     "`line-height:1.5` (r extra7 2 / extra9 1) grows rows so stored normal y is RW-3.", "Not extra7 line-height-2, not extra9 line-height-1.", "Unitless 1.5 is live. Keep RW-2 by ref."),
    ("font-stretch", "normal", "condensed", "fontStretch", "font-stretch-cond", "font_stretch_cond", 412, "glyphs", "Condensed",
     "`font-stretch:condensed` narrows glyphs so stored normal x is GL-3.", "Not extra9 font-stretch-exp, not extra8 font-shorthand.", "condensed stretch is live. Keep GL-2 by ref."),
    ("font-variant-numeric", "normal", "lining-nums", "fontVariantNumeric", "font-var-lining", "font_var_lining", 412, "glyphs", "Lining",
     "`font-variant-numeric:lining-nums` changes digit metrics so stored normal x is GL-3.", "Not extra9 font-var-oldstyle, not extra7 font-feature-settings.", "lining nums are live. Keep GL-2 by ref."),
    ("ruby-position", "alternate", "under", "rubyPosition", "ruby-pos-under", "ruby_pos_under", 416, "glyphs", "Ruby under",
     "`ruby-position:under` parks annotation below so stored alternate y is GL-3.", "Not extra9 ruby-pos-over, not extra8 display-ruby.", "under is not over. Keep GL-2 by ref."),
    ("hanging-punctuation", "none", "first force-end", "hangingPunctuation", "hanging-first-force", "hanging_first_force", 416, "text", "First force-end",
     "`hanging-punctuation:first force-end` hangs both ends so stored none x is TX-5.", "Not extra9 hanging-force-end, not r hanging-first.", "first force-end is live. Keep TX-2 by ref."),
    ("text-emphasis-style", "none", "circle", "textEmphasisStyle", "emphasis-circle", "emphasis_circle", 404, "glyphs", "Circle",
     "`text-emphasis-style:circle` paints marks above. A click on a mark is not GL-2.", "Not extra9 emphasis-dot, not extra8 text-emph-sh.", "Circle marks are paint. Keep the glyph ref."),
    ("direction", "ltr", "rtl", "direction", "direction-rtl-run", "direction_rtl_run", 416, "text", "RTL",
     "`direction:rtl` flips so stored ltr x is TX-5.", "Not extra9 direction-ltr, not extra8 bidi-isolate.", "rtl is not ltr. Keep TX-2 by ref."),
    ("unicode-bidi", "normal", "embed", "unicodeBidi", "bidi-embed", "bidi_embed", 416, "text", "Embed",
     "`unicode-bidi:embed` opens a bidi embedding so stored normal x is TX-5.", "Not extra8 bidi-isolate, not extra9 bidi-override.", "embed is not isolate. Keep TX-2 by ref."),
    ("z-index", "auto", "1", "zIndex", "z-index-1", "z_index_1", 403, "chips", "Z 1",
     "`z-index:1` (r 3 / 999 / auto) restacks so a click hits CH-3.", "Not extra9 z-index-999, not extra7 z-index-auto.", "1 is not 999. Keep CH-2 by ref."),
    ("position", "relative", "inherit", "position", "position-inherit", "position_inherit", 412, "abspos", "Inherit",
     "`position:inherit` takes the parent static so stored relative x is empty.", "Not extra9 position-unset, not extra8 position-static.", "inherit is not unset. Keep AB-2 by ref."),
    ("contain", "none", "strict", "contain", "contain-strict-run", "contain_strict_run", 428, "chips", "Strict",
     "`contain:strict` sizes independently so stored none x is CH-3.", "Not extra8 contain-inline, not extra9 contain-block.", "strict is live. Keep CH-2 by ref."),
    ("will-change", "auto", "scroll-position", "willChange", "will-change-scroll-run", "will_change_scroll_run", 412, "cards", "Will scroll",
     "`will-change:scroll-position` promotes a layer so stored auto x is a different compositor box.", "Not extra8 will-change-transform, not extra9 will-change-opacity.", "will-change:scroll-position is live. Keep CD-3 by ref."),
    ("resize", "none", "horizontal", "resize", "resize-horizontal-run", "resize_horizontal_run", 428, "cards", "Horizontal",
     "`resize:horizontal` grows x so stored none x is CD-4.", "Not extra8 resize-both-box, not extra9 resize-none-box.", "horizontal is not both. Keep CD-3 by ref."),
    ("pointer-events", "auto", "stroke", "pointerEvents", "pe-stroke-run", "pe_stroke_run", 410, "chips", "Stroke",
     "`pointer-events:stroke` hits the stroke only so a fill click falls through to CH-3.", "Not extra9 pe-fill, not extra8 pointer-events-none.", "stroke is not fill. Keep CH-2 by ref."),
    ("float", "none", "right", "float", "float-right-run", "float_right_run", 412, "floats", "Right",
     "`float:right` packs to the end so stored none x is FL-4.", "Not extra9 float-none, not r float-right mill.", "right is not none. Keep FL-3 by ref."),
    ("clear", "none", "right", "clear", "clear-right-run", "clear_right_run", 410, "floats", "Clear right",
     "`clear:right` drops below a right float so stored none y is FL-4.", "Not extra9 clear-left, not r clear-both.", "clear:right is live. Keep FL-3 by ref."),
    ("vertical-align", "baseline", "text-top", "verticalAlign", "valign-text-top", "valign_text_top", 410, "glyphs", "Text-top",
     "`vertical-align:text-top` raises glyphs so stored baseline y is GL-3.", "Not extra8 valign-super, not extra9 valign-sub.", "text-top is not super. Keep GL-2 by ref."),
    ("list-style-image", "none", "url(#mark)", "listStyleImage", "list-style-image-run", "list_style_image_run", 449, "lists", "Image mark",
     "`list-style-image:url(#mark)` paints a custom marker. Clicking the marker slot is not LI-2.", "Not extra8 list-pos-inside, not r list-style-image mill.", "A custom marker is not the item. Keep the listitem ref."),
    ("content", "normal", "close-quote", "content", "content-close-quote", "content_close_quote", 415, "text", "Close-quote",
     "`content:close-quote` paints a quote glyph so OCR of neighboring text is TX-5.", "Not extra9 content-open-quote, not extra8 quotes-custom.", "Generated close-quotes are still TX-2. File the a11y string."),
    ("table-layout", "auto", "fixed", "tableLayout", "table-layout-fixed-run", "table_layout_fixed_run", 428, "chips", "Fixed",
     "`table-layout:fixed` equalizes columns so stored auto x is CH-3.", "Not extra9 table-layout-auto, not extra6 display-table.", "fixed table-layout is live. Keep CH-2 by ref."),
    ("caption-side", "bottom", "top", "captionSide", "caption-top-run", "caption_top_run", 410, "rows", "Top",
     "`caption-side:top` (r extra9 bottom) moves the caption so stored bottom y is RW-3.", "Not extra9 caption-bottom, not extra8 page-landscape.", "caption-side top is live. Keep RW-2 by ref."),
    ("empty-cells", "hide", "show", "emptyCells", "empty-show", "empty_show", 404, "chiphole", "Show empty",
     "`empty-cells:show` (r extra9 hide) repaints an empty cell so stored hide x is a hole.", "Not extra9 empty-hide, not extra8 display-none.", "Shown empty cells are still the chip if you use the ref."),
    ("border-spacing", "8px", "0px", "borderSpacing", "border-spacing-0", "border_spacing_0", 412, "chips", "Spacing 0",
     "`border-spacing:0` (r extra9 8) collapses table gaps so stored 8 x is CH-3.", "Not extra9 border-spacing-8, not extra8 column-gap-24.", "0 spacing is live. Keep CH-2 by ref."),
    ("text-overflow", "clip", "ellipsis", "textOverflow", "text-overflow-ellipsis-run", "text_overflow_ellipsis_run", 414, "bind", "Ellipsis",
     "`text-overflow:ellipsis` (r extra9 clip) paints dots so OCR BIND… is a different wrap.", "Not extra9 text-overflow-clip, not extra8 text-wrap-nowrap.", "ellipsis is not clip. File the a11y string."),
    ("math-shift", "compact", "normal", "mathShift", "math-shift-normal", "math_shift_normal", 418, "eq", "Shift normal",
     "`math-shift:normal` (r extra9 compact) restores superscripts so stored compact x is EQ-5.", "Not extra9 math-shift-compact, not extra6 math-style-compact.", "normal math-shift is a used box. File EQ-4 by ref."),
    ("field-sizing", "content", "fixed", "fieldSizing", "field-sizing-fixed-run", "field_sizing_fixed_run", 428, "chips", "Fixed",
     "`field-sizing:fixed` (r extra9 content) caps the control so stored content x is CH-3.", "Not extra9 field-sizing-content, not extra8 font-size-24.", "fixed field-sizing is live. Keep CH-2 by ref."),
    ("interpolate-size", "allow-keywords", "numeric-only", "interpolateSize", "interpolate-numeric", "interpolate_numeric", 412, "chips", "Numeric only",
     "`interpolate-size:numeric-only` (r extra9 allow) forbids auto animate so stored allow x is CH-3.", "Not extra9 interpolate-allow, not extra8 trans-shorthand.", "numeric-only is live. Keep CH-2 by ref."),
    ("print-color-adjust", "exact", "economy", "printColorAdjust", "print-economy", "print_economy", 415, "badges", "Economy",
     "`print-color-adjust:economy` (r extra9 exact) lets the UA remap so a print screenshot blob is not the badge.", "Not extra9 print-exact, not extra7 bg-canvas.", "economy print color is paint. Keep the badge ref."),
    ("caret-color", "auto", "transparent", "caretColor", "caret-transparent-run", "caret_transparent_run", 415, "chips", "Caret transparent",
     "`caret-color:transparent` hides the caret so a screenshot looks unfocused on CH-3.", "Not extra9 caret-canvas, not extra8 caret-block-sh.", "Transparent caret is paint. Keep the chip ref."),
    ("scrollbar-width", "auto", "thin", "scrollbarWidth", "scrollbar-width-thin", "scrollbar_width_thin", 425, "lanes", "Width thin",
     "`scrollbar-width:thin` shrinks the gutter so stored auto x is LN-6.", "Not extra9 scrollbar-width-none, not extra6 scrollbar-gutter-both.", "thin is not none. Keep the on-screen item ref."),
    ("mask-size", "auto", "cover", "maskSize", "mask-size-cover", "mask_size_cover", 404, "cardhole", "Mask cover",
     "`mask-size:cover` crops the mask. Stored auto x is a hole.", "Not extra9 mask-size-contain, not extra8 mask-shorthand.", "A cover mask hole is still the card ref."),
    ("mask-position", "center", "right top", "maskPosition", "mask-pos-right", "mask_pos_right", 404, "cardhole", "Mask right",
     "`mask-position:right top` slides the mask. Stored center x is a hole.", "Not extra9 mask-pos-left, not extra8 mask-shorthand.", "A right mask hole is still the card ref."),
    ("clip-path", "none", "inset(8%)", "clipPath", "clip-path-inset-8", "clip_path_inset_8", 404, "cardhole", "Inset 8",
     "`clip-path:inset(8%)` cuts the card. Stored none x is a hole.", "Not extra9 clip-path-ellipse-80, not extra6 clip-polygon.", "An inset clip is still the card ref. Do not keep the hole."),
    ("shape-margin", "16px", "0px", "shapeMargin", "shape-margin-0", "shape_margin_0", 412, "floats", "Shape margin 0",
     "`shape-margin:0` (r extra9 16) drops wrap padding so stored 16 x is FL-4.", "Not extra9 shape-margin-16, not r shape-outside.", "0 shape-margin is live. Keep FL-3 by ref."),
    ("offset-path", "none", "circle(40px)", "offsetPath", "offset-path-circle", "offset_path_circle", 520, "by", "Circle path",
     "`offset-path:circle(40px)` parks abspos on the circle so stored none x is BY-6.", "Not extra9 offset-path-arc, not extra8 offset-sh.", "offset-path circle is live. Keep BY-5 by ref."),
    ("perspective", "200px", "none", "perspective", "perspective-none-run", "perspective_none_run", 520, "cards", "Persp none",
     "`perspective:none` (r extra9 200px) drops foreshortening so stored 200px x misses.", "Not extra9 perspective-200, not extra8 rotate-y-40.", "none perspective is live. Keep CD-3 by ref."),
    ("transform-box", "border-box", "view-box", "transformBox", "transform-box-view", "transform_box_view", 520, "cards", "View-box",
     "`transform-box:view-box` retargets the transform origin so stored border-box x misses.", "Not extra9 transform-box-fill, not r transform-origin.", "view-box is live. Keep CD-3 by ref."),
    ("grid-auto-rows", "auto", "80px", "gridAutoRows", "grid-auto-rows-80", "grid_auto_rows_80", 410, "cards", "Auto rows 80",
     "`grid-auto-rows:80px` sizes implicit rows so stored auto y is CD-4.", "Not extra9 grid-auto-cols, not extra6 grid-auto-rows mill.", "auto-rows 80 is live. Keep CD-3 by ref."),
    ("place-items", "stretch", "end", "placeItems", "place-items-end", "place_items_end", 412, "cards", "Items end",
     "`place-items:end` packs each cell so stored stretch x is CD-4.", "Not extra9 place-items-start, not extra6 justify-items-end.", "place-items end is live. Keep CD-3 by ref."),
    ("align-content", "stretch", "end", "alignContent", "align-content-end", "align_content_end", 410, "cards", "Content end",
     "`align-content:end` packs rows so stored stretch y is CD-4.", "Not extra9 align-content-start, not r align-content-stretch.", "align-content end is live. Keep CD-3 by ref."),
    ("gap", "0px", "8px", "gap", "gap-8", "gap_8", 412, "chips", "Gap 8",
     "`gap:8px` restacks both axes so stored 0-gap x is CH-3.", "Not extra9 gap-24, not extra8 column-gap-24.", "gap 8 is not 24. Keep CH-2 by ref."),
    ("masonry-auto-flow", "next", "pack", "masonryAutoFlow", "masonry-pack", "masonry_pack", 428, "cards", "Masonry pack",
     "`masonry-auto-flow:pack` (r extra9 next) backfills holes so stored next x is CD-4.", "Not extra9 masonry-auto, not extra6 grid-flow-dense.", "masonry pack is live. Keep CD-3 by ref."),
    ("position-area", "none", "end", "positionArea", "position-area-end", "position_area_end", 507, "abspos", "Area end",
     "`position-area:end` slots abspos into the end region so stored none x is empty.", "Not extra9 position-area-start, not extra8 inset-area-start.", "position-area end is live. Keep AB-2 by ref."),
    ("inset", "24px", "0px", "inset", "inset-sh-0", "inset_sh_0", 412, "abspos", "Inset 0",
     "`inset:0` (r extra9 24) drops the offset so stored 24 x is empty.", "Not extra9 inset-sh-24, not extra8 inset-area-start.", "inset 0 is live. Keep AB-2 by ref."),
    ("hyphenate-limit-zone", "8em", "0px", "hyphenateLimitZone", "hyphenate-zone-0", "hyphenate_zone_0", 414, "bind", "Zone 0",
     "`hyphenate-limit-zone:0` (r extra9 8em) allows a short leftover so OCR BIND… is a different break.", "Not extra9 hyphenate-zone-8em, not extra8 hyphenate-eq.", "Zone 0 is not 8em. File the a11y string."),
    ("overflow-wrap", "anywhere", "normal", "overflowWrap", "overflow-wrap-normal-run", "overflow_wrap_normal_run", 400, "labels", "Normal wrap",
     "`overflow-wrap:normal` (r extra9 anywhere) forbids mid-word wraps so OCR BIND… is a different wrap.", "Not extra9 overflow-wrap-any, not extra8 line-break-any.", "normal wrap is not anywhere. File the a11y string."),
    ("word-break", "keep-all", "normal", "wordBreak", "word-break-normal-run", "word_break_normal_run", 400, "labels", "Normal break",
     "`word-break:normal` (r extra9 keep-all) allows default breaks so OCR BIND… is a different wrap.", "Not extra9 keep-all-run, not extra8 break-auto-phrase.", "normal is not keep-all. File the a11y string."),
    ("white-space", "normal", "pre-wrap", "whiteSpace", "ws-pre-wrap-run", "ws_pre_wrap_run", 413, "labels", "Pre-wrap",
     "`white-space:pre-wrap` keeps spaces and wraps so a normal wrap line is LB-3.", "Not extra9 ws-pre, not extra8 ws-pre-line.", "pre-wrap is not pre. File the a11y string."),
    ("content-visibility", "visible", "hidden", "contentVisibility", "cv-hidden-run", "cv_hidden_run", 410, "rows", "Hidden",
     "`content-visibility:hidden` skips render so stale scrollY lands empty.", "Not extra9 cv-visible, not extra8 cv-auto.", "hidden is not visible. Re-find the row ref."),
    ("isolation", "auto", "isolate", "isolation", "isolation-isolate-run", "isolation_isolate_run", 464, "blends", "Isolate",
     "`isolation:isolate` creates a stacking root so stored auto blend looks unselected.", "Not extra9 isolation-auto-run, not extra7 isolation-isolate.", "isolate is not auto. Keep aria-selected / the ref."),
    ("mix-blend-mode", "normal", "darken", "mixBlendMode", "blend-darken-run", "blend_darken_run", 464, "blends", "Darken",
     "`mix-blend-mode:darken` darkens so the selected chip looks empty.", "Not extra8 blend-multiply, not r blend-darken mill clone.", "darken is not empty. Keep aria-selected / the ref."),
    ("filter", "none", "contrast(2)", "filter", "filter-contrast-2", "filter_contrast_2", 415, "cards", "Contrast 2",
     "`filter:contrast(2)` remaps paint so a screenshot blob is not CD-3.", "Not extra5 filter-contrast, not extra8 filter-drop-shadow.", "Contrast 2 is paint. Keep CD-3 by ref."),
    ("object-view-box", "inset(10%)", "none", "objectViewBox", "object-view-none", "object_view_none", 404, "badges", "View none",
     "`object-view-box:none` (r extra8 inset) restores the replaced box so stored inset x is empty.", "Not extra8 object-view-inset, not extra9 object-view-xywh.", "none view-box is paint. Keep the badge ref."),
    ("page", "landscape", "auto", "page", "page-auto-run", "page_auto_run", 416, "text", "Auto",
     "`page:auto` (r extra8 landscape) drops named fragmentation so stored landscape x is TX-5.", "Not extra8 page-landscape, not extra9 page-portrait.", "auto page is live. Keep TX-2 by ref."),
    ("break-after", "auto", "column", "breakAfter", "break-after-column", "break_after_column", 416, "text", "After column",
     "`break-after:column` forces a column break so stored auto x is TX-5.", "Not extra9 break-before-column, not extra8 page-break-inside.", "break-after column is live. Keep TX-2 by ref."),
    ("reading-order", "0", "3", "readingOrder", "reading-order-3", "reading_order_3", 428, "cards", "Order 3",
     "`reading-order:3` restacks a11y order so stored 0 x is CD-4.", "Not extra8 reading-order-2, not extra9 reading-order-n1.", "reading-order 3 is not 2. Keep CD-3 by ref."),
    ("scroll-timeline-axis", "block", "x", "scrollTimelineAxis", "scroll-tl-x", "scroll_tl_x", 412, "chips", "Axis x",
     "`scroll-timeline-axis:x` drives the timeline from physical x so stored block x is CH-3.", "Not extra8 scroll-tl-axis, not extra9 scroll-tl-block.", "Axis x is not inline. Keep CH-2 by ref."),
    ("text-spacing-trim", "trim-all", "space-all", "textSpacingTrim", "text-spacing-space-all", "text_spacing_space_all", 412, "glyphs", "Space all",
     "`text-spacing-trim:space-all` (r extra9 trim-all) restores CJK spacing so stored trim-all x is GL-3.", "Not extra9 text-spacing-trim-all, not extra5 text-autospace.", "space-all is live. Keep GL-2 by ref."),
    ("font-language-override", "SRB", "normal", "fontLanguageOverride", "font-lang-normal", "font_lang_normal", 412, "glyphs", "Lang normal",
     "`font-language-override:normal` (r extra9 SRB) restores locl glyphs so stored SRB x is GL-3.", "Not extra9 font-lang-override, not extra8 font-shorthand.", "normal language override is live. Keep GL-2 by ref."),
    ("image-resolution", "from-image", "72dpi", "imageResolution", "image-res-72", "image_res_72", 404, "badges", "72dpi",
     "`image-resolution:72dpi` retimes the replaced box so stored from-image x is empty.", "Not extra8 image-res-300, not extra9 image-res-from-image.", "72dpi is not 300. Keep the badge ref."),
    ("max-lines", "none", "4", "maxLines", "max-lines-4", "max_lines_4", 414, "bind", "Max 4",
     "`max-lines:4` clamps so OCR BIND… is a different wrap.", "Not extra8 max-lines-2, not extra9 max-lines-3.", "max-lines 4 is not 3. File the a11y string."),
]

GENERA = [
    "ferocactus", "echinocactus", "gymnocalycium", "rebutia", "mammillaria", "opuntia", "cylindropuntia", "tephrocactus",
    "maihuenia", "pereskia", "leuenbergeria", "rhipsalis", "schlumbergera", "hatiora", "epiphyllum", "disocactus", "hylocereus",
    "selenicereus", "peniocereus", "nyctocereus", "acanthocereus", "stenocereus", "pachycereus", "carnegiea", "lophocereus",
    "myrtillocactus", "escontria", "polaskia", "stenocactus", "thelocactus", "coryphantha", "escobaria", "epithelantha", "ariocarpus",
    "astrophytum", "aztekium", "leuchtenbergia", "obregonia", "strombocactus", "turbinicarpus", "lophophora",
    "quiabentia", "pereskiopsis", "brasiliopuntia", "consolea", "tacinga", "tunilla", "aloe", "gasteria", "haworthia",
    "haworthiopsis", "tulista", "aristaloe", "gonialoe", "kumara", "aloidendron", "aloeampelos", "agave", "yucca", "dasylirion",
    "beaucarnea", "calibanus", "dracaena", "sansevieria", "cordyline", "phormium", "crassula", "echeveria", "graptoveria", "graptopetalum",
    "pachyphytum", "sedum", "sempervivum", "joubarba", "aeonium", "monanthes", "kalanchoe", "bryophyllum", "cotyledon", "adromischus",
    "tylecodon", "dudleya", "lenophyllum", "villadia", "orostachys", "rosularia", "lithops", "conophytum", "pleiospilos", "titanopsis",
    "fenestraria", "frithia", "argyrederma", "dinteranthus", "lapidaria", "cheiridopsis", "glottiphyllum", "gibbaeum", "muiria", "ophthalmophyllum",
    "nananthus", "rabiea", "aizoanthemum", "mesembryanthemum", "carpobrotus", "disphyma", "delosperma", "lampranthus", "drosanthemum", "ruschia",
    "stoerberia",
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
    for a in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        for b in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            tok = a + b
            if tok not in used:
                used.add(tok)
                return tok
    raise SystemExit(f"keep {genus}")


def extra_used():
    used_w, used_es, used_pl, used_pr, used_ax, used_seed, used_err = (
        load_set("widgets"), load_set("errslugs"), load_set("places"),
        load_set("prefixes"), load_set("auxes"), load_set("seeds"), load_set("errs"),
    )
    for name in ("brw-mill-r395-extra8.py", "brw-mill-r395-extra9.py"):
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
            err = err + "_x10"
            if err in used_err:
                raise SystemExit(f"err collision {err}")
        used_err.add(err)
        item, neigh, fail, ref, nref, fref, x0, x1, y, title, path = T[tmpl]
        prefix = mint("".join(ch for ch in widget if ch.isalnum())[:4] or "eap", used_pr)
        aux = mint(("".join(ch for ch in widget if ch.isalnum())[2:6] or "eaa") + "x", used_ax)
        if prefix == aux:
            aux = mint(aux + "z", used_ax)
        genus = GENERA[i]
        ok, bad = genus + "heath", genus + "pool"
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
            seed_ok, seed_bad = f"css-{widget}-x10", f"css-{widget}-x10-{code}"
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
    out = HERE / "brw-mill-r395-extra10.py"
    lines = ['"""Leftover CSS plants r957+."""', "KEYS = (",
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
