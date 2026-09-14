#!/usr/bin/env python3
"""Generate leftover CSS extra9 plants r846+ (unique vs r01-r845 extra8)."""
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

# leftover values / leftover properties not in extra8 widgets
PLANTS = [
    ("font-size", "16px", "12px", "fontSize", "font-size-12", "font_size_12", 412,
     "GL-2", "GL-3", "GL-3", "c2", "c3", "c3", 88, 70, 56, "Size 12", "Glyphs", "Keep", "glyphs",
     "`font-size:12px` shrinks glyphs so stored 16px x is GL-3.",
     "Not extra8 font-size-24, not extra7 font-weight-700.",
     "Smaller font-size is live. Keep GL-2 by ref."),
    ("font-size", "16px", "32px", "fontSize", "font-size-32", "font_size_32", 412,
     "GL-2", "GL-3", "GL-3", "c2", "c3", "c3", 88, 140, 56, "Size 32", "Glyphs", "Keep", "glyphs",
     "`font-size:32px` grows glyphs so stored 16px x is GL-3.",
     "Not extra8 font-size-24, not this mill's font-size-12.",
     "32px is not 24px. Keep GL-2 by ref."),
    ("font-family", "sans-serif", "ui-serif", "fontFamily", "font-family-serif", "font_family_serif", 412,
     "GL-2", "GL-3", "GL-3", "c2", "c3", "c3", 88, 104, 56, "Serif", "Glyphs", "Keep", "glyphs",
     "`font-family:ui-serif` retimes advances so stored sans x is GL-3.",
     "Not extra8 font-family-mono, not r font-feature-settings.",
     "Serif metrics are live. Keep GL-2 by ref."),
    ("zoom", "1", "0.5", "zoom", "zoom-05", "zoom_05", 412,
     "CD-3", "CD-4", "CD-4", "c3", "c4", "c3", 160, 80, 80, "Zoom 0.5", "Cards", "Keep", "cards",
     "`zoom:0.5` (r 0.8 / 1.25 / extra8 1.5) shrinks the used box so stored unzoomed x is CD-4.",
     "Not extra6 zoom-08, not extra8 zoom-15.",
     "CSS zoom 0.5 is not scale(). Keep CD-3 by ref."),
    ("zoom", "1", "2", "zoom", "zoom-2", "zoom_2", 412,
     "CD-3", "CD-4", "CD-4", "c3", "c4", "c3", 160, 320, 80, "Zoom 2", "Cards", "Keep", "cards",
     "`zoom:2` doubles the used box so stored unzoomed x is CD-4.",
     "Not extra8 zoom-15, not this mill's zoom-05.",
     "CSS zoom 2 is not scale(2). Keep CD-3 by ref."),
    ("opacity", "1", "0.8", "opacity", "opacity-08", "opacity_08", 464,
     "SW-2", "SW-3", "SW-3", "c2", "c3", "c3", 154, 154, 88, "Opacity 0.8", "Blends", "Keep", "blends",
     "`opacity:0.8` (r 0 / 0.2 / 0.5) fades so a screenshot looks unselected.",
     "Not extra8 opacity-0, not extra7 opacity-02.",
     "0.8 is not unselected. Keep aria-selected / the ref."),
    ("scale", "1", "2", "scale", "scale-2", "scale_2", 412,
     "CD-3", "CD-4", "CD-4", "c3", "c4", "c3", 160, 320, 80, "Scale 2", "Cards", "Keep", "cards",
     "`scale:2` (r extra8 1.5 / r 0.8) grows so stored unscaled x is CD-4.",
     "Not extra8 scale-15, not r648 scale-y.",
     "Uniform scale 2 is live. Keep CD-3 by ref."),
    ("rotate", "0deg", "z 40deg", "rotate", "rotate-z-40", "rotate_z_40", 520,
     "CD-3", "CD-4", "CD-4", "c3", "c4", "c3", 160, 148, 80, "Rotate Z 40", "Cards", "Keep", "cards",
     "`rotate:z 40deg` (r extra6 x / extra8 y) shears the hit diamond so stored 0deg x misses.",
     "Not extra8 rotate-y-40, not extra6 rotate-x.",
     "Z-rotate is live. Keep CD-3 by ref."),
    ("translate", "0px", "0px 40px", "translate", "translate-y-40", "translate_y_40", 410,
     "AB-2", "AB-3", "AB-3", "c2", "c3", "c3", 16, 16, 88, "Translate y 40", "Abspos", "Keep", "abspos",
     "`translate:0 40px` slides block so stored 0 y is empty.",
     "Not extra8 translate-x-40, not r translate-block.",
     "Y translate is live. Keep AB-2 by ref."),
    ("cursor", "auto", "zoom-out", "cursor", "cursor-zoom-out", "cursor_zoom_out", 404,
     "CH-2", "CH-3", "CH-3", "c2", "c3", "c3", 80, 80, 64, "Zoom-out", "Chips", "Keep", "chips",
     "`cursor:zoom-out` paints a minus glyph over CH-2. Screenshot of the glyph is not CH-3.",
     "Not extra8 cursor-zoom-in, not extra8 cursor-grab.",
     "The zoom-out cursor is paint. Keep the chip ref."),
    ("cursor", "auto", "wait", "cursor", "cursor-wait", "cursor_wait", 404,
     "CH-2", "CH-3", "CH-3", "c2", "c3", "c3", 80, 80, 64, "Wait", "Chips", "Keep", "chips",
     "`cursor:wait` paints a spinner glyph over CH-2. Screenshot of the glyph is not CH-3.",
     "Not extra7 cursor-not-allowed, not extra8 cursor-grab.",
     "The wait cursor is paint. Keep the chip ref."),
    ("cursor", "auto", "grabbing", "cursor", "cursor-grabbing", "cursor_grabbing", 404,
     "CH-2", "CH-3", "CH-3", "c2", "c3", "c3", 80, 80, 64, "Grabbing", "Chips", "Keep", "chips",
     "`cursor:grabbing` paints a closed-hand glyph over CH-2. Screenshot of the glyph is not CH-3.",
     "Not extra8 cursor-grab, not extra8 cursor-wait.",
     "The grabbing cursor is paint. Keep the chip ref."),
    ("cursor", "auto", "help", "cursor", "cursor-help", "cursor_help", 404,
     "CH-2", "CH-3", "CH-3", "c2", "c3", "c3", 80, 80, 64, "Help", "Chips", "Keep", "chips",
     "`cursor:help` paints a question glyph over CH-2. Screenshot of the glyph is not CH-3.",
     "Not extra8 cursor-wait, not extra7 cursor-not-allowed.",
     "The help cursor is paint. Keep the chip ref."),
    ("cursor", "auto", "crosshair", "cursor", "cursor-crosshair", "cursor_crosshair", 404,
     "CH-2", "CH-3", "CH-3", "c2", "c3", "c3", 80, 80, 64, "Crosshair", "Chips", "Keep", "chips",
     "`cursor:crosshair` paints a plus over CH-2. Screenshot of the glyph is not CH-3.",
     "Not extra8 cursor-zoom-in, not this mill's cursor-help.",
     "The crosshair is paint. Keep the chip ref."),
    ("cursor", "auto", "progress", "cursor", "cursor-progress", "cursor_progress", 404,
     "CH-2", "CH-3", "CH-3", "c2", "c3", "c3", 80, 80, 64, "Progress", "Chips", "Keep", "chips",
     "`cursor:progress` paints an arrow+spinner over CH-2. Screenshot of the glyph is not CH-3.",
     "Not this mill's cursor-wait, not extra8 cursor-grab.",
     "The progress cursor is paint. Keep the chip ref."),
    ("cursor", "auto", "move", "cursor", "cursor-move", "cursor_move", 404,
     "CH-2", "CH-3", "CH-3", "c2", "c3", "c3", 80, 80, 64, "Move", "Chips", "Keep", "chips",
     "`cursor:move` paints a four-arrow glyph over CH-2. Screenshot of the glyph is not CH-3.",
     "Not extra8 cursor-grab, not this mill's cursor-grabbing.",
     "The move cursor is paint. Keep the chip ref."),
    ("cursor", "auto", "col-resize", "cursor", "cursor-col-resize", "cursor_col_resize", 404,
     "CH-2", "CH-3", "CH-3", "c2", "c3", "c3", 80, 80, 64, "Col-resize", "Chips", "Keep", "chips",
     "`cursor:col-resize` paints a col splitter over CH-2. Screenshot of the glyph is not CH-3.",
     "Not this mill's cursor-move, not extra8 cursor-grab.",
     "The col-resize cursor is paint. Keep the chip ref."),
    ("cursor", "auto", "row-resize", "cursor", "cursor-row-resize", "cursor_row_resize", 404,
     "CH-2", "CH-3", "CH-3", "c2", "c3", "c3", 80, 80, 64, "Row-resize", "Chips", "Keep", "chips",
     "`cursor:row-resize` paints a row splitter over CH-2. Screenshot of the glyph is not CH-3.",
     "Not this mill's cursor-col-resize, not extra8 cursor-grab.",
     "The row-resize cursor is paint. Keep the chip ref."),
    ("display", "block", "inline", "display", "display-inline", "display_inline", 412,
     "CH-2", "CH-3", "CH-3", "c2", "c3", "c3", 80, 40, 64, "Inline", "Chips", "Keep", "chips",
     "`display:inline` shrink-wraps so stored block x is CH-3.",
     "Not extra8 display-none, not extra8 display-ruby.",
     "inline is not none. Keep CH-2 by ref."),
    ("display", "block", "table-cell", "display", "display-table-cell", "display_table_cell", 428,
     "CH-2", "CH-3", "CH-3", "c2", "c3", "c3", 80, 140, 64, "Table-cell", "Chips", "Keep", "chips",
     "`display:table-cell` equalizes a column so stored block x is CH-3.",
     "Not extra6 display-table, not extra8 display-ruby.",
     "table-cell is not table. Keep CH-2 by ref."),
    ("display", "block", "table-row", "display", "display-table-row", "display_table_row", 410,
     "RW-2", "RW-3", "RW-3", "c2", "c3", "c3", 24, 24, 48, "Table-row", "Rows", "Keep", "rows",
     "`display:table-row` packs a row box so stored block y is RW-3.",
     "Not extra6 display-table, not this mill's display-table-cell.",
     "table-row is not table. Keep RW-2 by ref."),
    ("display", "block", "inline-table", "display", "display-inline-table", "display_inline_table", 428,
     "CH-2", "CH-3", "CH-3", "c2", "c3", "c3", 80, 140, 64, "Inline-table", "Chips", "Keep", "chips",
     "`display:inline-table` shrink-wraps a table so stored block x is CH-3.",
     "Not extra6 display-table, not extra7 display-inline-flex mill.",
     "inline-table is not table. Keep CH-2 by ref."),
    ("overflow-y", "visible", "overlay", "overflowY", "overflow-y-overlay", "overflow_y_overlay", 425,
     "LN-4", "LN-5", "LN-6", "c4", "c5", "c6", 240, 240, 24, "Overlay y", "Lanes", "Keep", "lanes",
     "`overflow-y:overlay` draws a floating y scrollbar so stored visible y is LN-6.",
     "Not extra8 overflow-y-auto, not extra4 overflow-y-scroll.",
     "overlay-y is not auto. Keep the on-screen item ref."),
    ("overflow-x", "auto", "visible", "overflowX", "overflow-x-visible", "overflow_x_visible", 425,
     "LN-4", "LN-5", "LN-6", "c4", "c5", "c6", 40, 240, 24, "Visible x", "Lanes", "Keep", "lanes",
     "`overflow-x:visible` drops the x scrollport so stored auto x is LN-6.",
     "Not extra7 overflow-x-auto, not extra4 overflow-x-scroll.",
     "visible-x is not auto. Keep the on-screen item ref."),
    ("backdrop-filter", "none", "saturate(0)", "backdropFilter", "backdrop-saturate", "backdrop_saturate", 415,
     "CD-3", "CD-4", "CD-4", "c3", "c4", "c3", 160, 160, 80, "Backdrop saturate 0", "Cards", "Keep", "cards",
     "`backdrop-filter:saturate(0)` greys the backdrop so a screenshot blob is not CD-3.",
     "Not extra8 backdrop-invert, not extra6 backdrop-blur.",
     "Backdrop saturate is paint. Keep CD-3 by ref."),
    ("backdrop-filter", "none", "brightness(2)", "backdropFilter", "backdrop-brightness", "backdrop_brightness", 415,
     "CD-3", "CD-4", "CD-4", "c3", "c4", "c3", 160, 160, 80, "Backdrop brightness 2", "Cards", "Keep", "cards",
     "`backdrop-filter:brightness(2)` blows the backdrop so a screenshot blob is not CD-3.",
     "Not extra5 filter-brightness, not extra8 backdrop-invert.",
     "Backdrop brightness is paint. Keep CD-3 by ref."),
    ("backdrop-filter", "none", "sepia(1)", "backdropFilter", "backdrop-sepia", "backdrop_sepia", 415,
     "CD-3", "CD-4", "CD-4", "c3", "c4", "c3", 160, 160, 80, "Backdrop sepia", "Cards", "Keep", "cards",
     "`backdrop-filter:sepia(1)` remaps paint so OCR / a screenshot blob is not CD-3.",
     "Not r641 filter-sepia, not extra8 backdrop-invert.",
     "Backdrop sepia is paint. Keep CD-3 by ref."),
    ("letter-spacing", "normal", "0.2em", "letterSpacing", "letter-spacing-em", "letter_spacing_em", 412,
     "GL-2", "GL-3", "GL-3", "c2", "c3", "c3", 88, 120, 56, "Tracking 0.2em", "Glyphs", "Keep", "glyphs",
     "`letter-spacing:0.2em` widens glyphs so stored normal x is GL-3.",
     "Not r letter-spacing mill clone, not extra8 font-size-24.",
     "Tracking is live. Keep GL-2 by ref."),
    ("word-spacing", "normal", "0.5em", "wordSpacing", "word-spacing-em", "word_spacing_em", 412,
     "GL-2", "GL-3", "GL-3", "c2", "c3", "c3", 88, 120, 56, "Word 0.5em", "Glyphs", "Keep", "glyphs",
     "`word-spacing:0.5em` widens word gaps so stored normal x is GL-3.",
     "Not r word-spacing mill clone, not this mill's letter-spacing-em.",
     "Word-spacing is live. Keep GL-2 by ref."),
    ("text-indent", "0px", "24px", "textIndent", "text-indent-24", "text_indent_24", 412,
     "TX-2", "TX-3", "TX-3", "c2", "c3", "c3", 24, 48, 36, "Indent 24", "Text", "Keep", "text",
     "`text-indent:24px` slides the first line so stored 0 x is TX-3.",
     "Not r text-indent mill clone, not extra7 text-align-center.",
     "Indent is live. Keep TX-2 by ref."),
    ("tab-size", "8", "4", "tabSize", "tab-size-4", "tab_size_4", 413,
     "LB-2", "LB-3", "LB-3", "c2", "c3", "c3", 24, 24, 48, "Tab 4", "Labels", "Keep", "labels",
     "`tab-size:4` retimes tab stops so a stored tab-8 wrap line is LB-3.",
     "Not r tab-size mill clone, not extra8 ws-pre-line.",
     "tab-size is live. File the a11y string."),
    ("outline-width", "0px", "8px", "outlineWidth", "outline-width-8", "outline_width_8", 404,
     "FL-3", "FL-4", "FL-4", "c3", "c4", "c4", 148, 148, 80, "Outline 8", "Floats", "Keep", "floats",
     "`outline-width:8px` fattens UA chrome. Screenshot of the ring is not FL-3.",
     "Not extra8 outline-sh-8, not extra8 outline-offset-12.",
     "Outline width is paint. Keep the float ref."),
    ("box-shadow", "none", "inset 0 0 0 8px CanvasText", "boxShadow", "box-shadow-inset", "box_shadow_inset", 404,
     "CH-2", "CH-3", "CH-3", "c2", "c3", "c3", 80, 80, 64, "Inset 8", "Chips", "Keep", "chips",
     "`box-shadow:inset 0 0 0 8px` paints an inner ring. Center click on the ring is not CH-2.",
     "Not r box-shadow-outset, not extra8 border-sh-8.",
     "Inset shadow is paint. Keep the chip ref."),
    ("object-fit", "cover", "none", "objectFit", "object-fit-none-box", "object_fit_none_box", 404,
     "BD-2", "BD-3", "BD-3", "c2", "c3", "c3", 140, 180, 80, "Fit none", "Badges", "Keep", "badges",
     "`object-fit:none` leaves intrinsic size. Stored cover x is empty.",
     "Not extra6 object-fit-contain, not r object-fit-fill.",
     "none is paint/metrics. Keep the badge ref."),
    ("object-position", "50% 50%", "0 0", "objectPosition", "object-pos-left", "object_pos_left", 404,
     "BD-2", "BD-3", "BD-3", "c2", "c3", "c3", 140, 100, 80, "Pos left top", "Badges", "Keep", "badges",
     "`object-position:0 0` slides the replaced box so stored center x is empty.",
     "Not r object-position mill clone, not extra8 object-view-inset.",
     "object-position is paint. Keep the badge ref."),
    ("flex-grow", "0", "2", "flexGrow", "flex-grow-2", "flex_grow_2", 428,
     "CH-4", "CH-5", "CH-5", "c4", "c5", "c5", 96, 180, 64, "Grow 2", "Chips", "Keep", "chips",
     "`flex-grow:2` eats free space so stored grow-0 x is CH-5.",
     "Not r394 flex-grow mill clone, not extra mill flex-shrink.",
     "grow 2 is live. Keep CH-4 by ref."),
    ("order", "0", "2", "order", "order-2", "order_2", 428,
     "CH-2", "CH-4", "CH-4", "c2", "c4", "c4", 40, 200, 64, "Order 2", "Chips", "Keep", "chips",
     "`order:2` restacks the flex item so stored 0 x is CH-4.",
     "Not extra8 reading-order-2, not r order mill clone.",
     "flex order is not reading-order. Keep CH-2 by ref."),
    ("column-count", "auto", "3", "columnCount", "column-count-3", "column_count_3", 416,
     "TX-2", "TX-5", "TX-5", "c2", "c5", "c5", 40, 24, 36, "Count 3", "Text", "Keep", "text",
     "`column-count:3` fragments so stored auto x is TX-5.",
     "Not r columns-shorthand, not extra8 page-landscape.",
     "column-count is live. Keep TX-2 by ref."),
    ("column-width", "auto", "12em", "columnWidth", "column-width-12em", "column_width_12em", 416,
     "TX-2", "TX-5", "TX-5", "c2", "c5", "c5", 40, 24, 36, "Width 12em", "Text", "Keep", "text",
     "`column-width:12em` fragments so stored auto x is TX-5.",
     "Not r column-width mill clone, not this mill's column-count-3.",
     "column-width is live. Keep TX-2 by ref."),
    ("column-span", "none", "all", "columnSpan", "column-span-all", "column_span_all", 416,
     "TX-2", "TX-5", "TX-5", "c2", "c5", "c5", 40, 200, 36, "Span all", "Text", "Keep", "text",
     "`column-span:all` stretches across columns so stored none x is TX-5.",
     "Not r column-span mill clone, not this mill's column-count-3.",
     "column-span is live. Keep TX-2 by ref."),
    ("column-fill", "auto", "balance", "columnFill", "column-fill-balance", "column_fill_balance", 416,
     "TX-2", "TX-5", "TX-5", "c2", "c5", "c5", 40, 24, 36, "Fill balance", "Text", "Keep", "text",
     "`column-fill:balance` rebalances so stored auto x is TX-5.",
     "Not r141 text-wrap:balance, not this mill's column-count-3.",
     "column-fill balance is live. Keep TX-2 by ref."),
    ("background-clip", "border-box", "text", "backgroundClip", "background-clip-text", "background_clip_text", 415,
     "OPEN", "FILE", "FILE", "c1", "c2", "c2", 110, 110, 70, "Clip text", "Verbs", "Keep", "verbs",
     "`background-clip:text` paints only glyphs so OCR reads FILE, not OPEN.",
     "Not extra8 fill-canvas, not extra7 color-canvas.",
     "Clip-to-text screenshots are not the accessible name."),
    ("background-origin", "padding-box", "content-box", "backgroundOrigin", "bg-origin-content", "bg_origin_content", 404,
     "BD-2", "BD-3", "BD-3", "c2", "c3", "c3", 140, 124, 80, "Origin content", "Badges", "Keep", "badges",
     "`background-origin:content-box` insets the blob so stored padding-box x is empty.",
     "Not r background-origin mill clone, not extra8 bg-image-gradient.",
     "background-origin is paint. Keep the badge ref."),
    ("background-attachment", "scroll", "local", "backgroundAttachment", "bg-attach-local", "bg_attach_local", 404,
     "BD-2", "BD-3", "BD-3", "c2", "c3", "c3", 140, 140, 80, "Attach local", "Badges", "Keep", "badges",
     "`background-attachment:local` scrolls the blob with content. Stored scroll x is empty.",
     "Not r background-attachment:fixed mill, not extra8 bg-shorthand.",
     "local attachment is paint. Keep the badge ref."),
    ("image-orientation", "from-image", "none", "imageOrientation", "image-orient-none", "image_orient_none", 404,
     "BD-2", "BD-3", "BD-3", "c2", "c3", "c3", 140, 140, 80, "Orient none", "Badges", "Keep", "badges",
     "`image-orientation:none` ignores EXIF rotation so stored from-image x is empty.",
     "Not r image-orientation mill clone, not extra8 image-res-300.",
     "image-orientation is paint. Keep the badge ref."),
    ("accent-color", "auto", "Canvas", "accentColor", "accent-canvas", "accent_canvas", 464,
     "SW-2", "SW-3", "SW-3", "c2", "c3", "c3", 154, 154, 88, "Accent Canvas", "Blends", "Keep", "blends",
     "`accent-color:Canvas` makes a checked box look empty in a screenshot.",
     "Not r613 accent-color:Canvas mill clone, not extra7 color-canvas.",
     "Canvas accent is not unchecked. Keep aria-checked / the ref."),
    ("appearance", "none", "auto", "appearance", "appearance-auto", "appearance_auto", 404,
     "CH-2", "CH-3", "CH-3", "c2", "c3", "c3", 80, 96, 64, "Appearance auto", "Chips", "Keep", "chips",
     "`appearance:auto` restores UA chrome so stored none x is CH-3.",
     "Not r appearance-none, not r appearance-menulist.",
     "auto appearance is live. Keep CH-2 by ref."),
    ("touch-action", "auto", "pan-y", "touchAction", "touch-pan-y", "touch_pan_y", 425,
     "LN-4", "LN-5", "LN-6", "c4", "c5", "c6", 240, 240, 24, "Pan y", "Lanes", "Keep", "lanes",
     "`touch-action:pan-y` forbids x pans so stored auto x is LN-6.",
     "Not r touch-pan-x, not r touch-action-none.",
     "pan-y is not pan-x. Keep the on-screen item ref."),
    ("overscroll-behavior", "auto", "none", "overscrollBehavior", "overscroll-none", "overscroll_none", 425,
     "LN-4", "LN-5", "LN-6", "c4", "c5", "c6", 240, 240, 24, "Overscroll none", "Lanes", "Keep", "lanes",
     "`overscroll-behavior:none` kills the scroll chain so stored auto x is LN-6.",
     "Not r overscroll-contain, not extra4 overscroll-x.",
     "none is not contain. Keep the on-screen item ref."),
    ("scroll-snap-stop", "normal", "always", "scrollSnapStop", "snap-stop-always", "snap_stop_always", 425,
     "LN-4", "LN-5", "LN-6", "c4", "c5", "c6", 240, 200, 24, "Stop always", "Lanes", "Keep", "lanes",
     "`scroll-snap-stop:always` forces each snap so stored normal x is LN-6.",
     "Not r scroll-snap-stop mill clone, not extra scroll-snap-type.",
     "always stop is live. Keep the on-screen item ref."),
    ("line-height", "normal", "1", "lineHeight", "line-height-1", "line_height_1", 410,
     "RW-2", "RW-3", "RW-3", "c2", "c3", "c3", 24, 24, 36, "Line 1", "Rows", "Keep", "rows",
     "`line-height:1` (r extra7 2) packs rows so stored normal y is RW-3.",
     "Not extra7 line-height-2, not r341 line-height mill clone.",
     "Unitless 1 is live. Keep RW-2 by ref."),
    ("font-stretch", "normal", "expanded", "fontStretch", "font-stretch-exp", "font_stretch_exp", 412,
     "GL-2", "GL-3", "GL-3", "c2", "c3", "c3", 88, 120, 56, "Expanded", "Glyphs", "Keep", "glyphs",
     "`font-stretch:expanded` widens glyphs so stored normal x is GL-3.",
     "Not r font-stretch mill clone, not extra8 font-shorthand.",
     "expanded stretch is live. Keep GL-2 by ref."),
    ("font-variant-numeric", "normal", "oldstyle-nums", "fontVariantNumeric", "font-var-oldstyle", "font_var_oldstyle", 412,
     "GL-2", "GL-3", "GL-3", "c2", "c3", "c3", 88, 80, 56, "Oldstyle", "Glyphs", "Keep", "glyphs",
     "`font-variant-numeric:oldstyle-nums` changes digit metrics so stored normal x is GL-3.",
     "Not r font-variant-numeric mill clone, not extra7 font-feature-settings.",
     "oldstyle nums are live. Keep GL-2 by ref."),
    ("ruby-position", "alternate", "over", "rubyPosition", "ruby-pos-over", "ruby_pos_over", 416,
     "GL-2", "GL-3", "GL-3", "c2", "c3", "c3", 88, 88, 40, "Ruby over", "Glyphs", "Keep", "glyphs",
     "`ruby-position:over` parks annotation above so stored alternate y is GL-3.",
     "Not r ruby-position mill clone, not extra8 display-ruby.",
     "ruby-position is live. Keep GL-2 by ref."),
    ("hanging-punctuation", "none", "force-end", "hangingPunctuation", "hanging-force-end", "hanging_force_end", 416,
     "TX-2", "TX-3", "TX-3", "c2", "c3", "c3", 40, 24, 36, "Force-end", "Text", "Keep", "text",
     "`hanging-punctuation:force-end` hangs the stop so stored none x is TX-3.",
     "Not r hanging-first, not r hanging-punctuation-last.",
     "force-end is not first. Keep TX-2 by ref."),
    ("text-emphasis-style", "none", "dot", "textEmphasisStyle", "emphasis-dot", "emphasis_dot", 404,
     "GL-2", "GL-3", "GL-3", "c2", "c3", "c3", 88, 88, 40, "Dot", "Glyphs", "Keep", "glyphs",
     "`text-emphasis-style:dot` paints marks above. A click on a mark is not GL-2.",
     "Not extra8 text-emph-sh, not r emphasis-style mill.",
     "Dot marks are paint. Keep the glyph ref."),
    ("direction", "rtl", "ltr", "direction", "direction-ltr", "direction_ltr", 416,
     "TX-2", "TX-5", "TX-5", "c2", "c5", "c5", 200, 40, 36, "LTR", "Text", "Keep", "text",
     "`direction:ltr` (r rtl already) flips so stored rtl x is TX-5.",
     "Not r direction-rtl, not extra8 bidi-isolate.",
     "ltr is not rtl. Keep TX-2 by ref."),
    ("unicode-bidi", "normal", "bidi-override", "unicodeBidi", "bidi-override", "bidi_override", 416,
     "TX-2", "TX-5", "TX-5", "c2", "c5", "c5", 40, 200, 36, "Override", "Text", "Keep", "text",
     "`unicode-bidi:bidi-override` forces order so stored normal x is TX-5.",
     "Not extra8 bidi-isolate, not r unicode-bidi-plaintext.",
     "bidi-override is not isolate. Keep TX-2 by ref."),
    ("z-index", "auto", "999", "zIndex", "z-index-999", "z_index_999", 403,
     "CH-2", "CH-3", "CH-3", "c2", "c3", "c3", 80, 80, 64, "Z 999", "Chips", "Keep", "chips",
     "`z-index:999` (r 3 / -1 / auto already) restacks so a click hits CH-3.",
     "Not extra7 z-index-auto, not r z-index-3.",
     "999 is not auto. Keep CH-2 by ref."),
    ("position", "relative", "unset", "position", "position-unset", "position_unset", 412,
     "AB-2", "AB-3", "AB-3", "c2", "c3", "c3", 16, 0, 48, "Unset", "Abspos", "Keep", "abspos",
     "`position:unset` drops the offset so stored relative x is empty.",
     "Not extra8 position-static, not extra7 position-relative.",
     "unset is not static. Keep AB-2 by ref."),
    ("contain", "none", "block-size", "contain", "contain-block", "contain_block", 410,
     "RW-2", "RW-3", "RW-3", "c2", "c3", "c3", 24, 24, 48, "Block-size", "Rows", "Keep", "rows",
     "`contain:block-size` sizes the block independently so stored none y is RW-3.",
     "Not extra8 contain-inline, not r contain-size.",
     "contain:block-size is live. Keep RW-2 by ref."),
    ("will-change", "auto", "opacity", "willChange", "will-change-opacity", "will_change_opacity", 412,
     "CD-3", "CD-4", "CD-4", "c3", "c4", "c3", 160, 160, 80, "Will opacity", "Cards", "Keep", "cards",
     "`will-change:opacity` promotes a layer so stored auto x is a different compositor box.",
     "Not extra8 will-change-transform, not r will-change-contents.",
     "will-change:opacity is live. Keep CD-3 by ref."),
    ("resize", "both", "none", "resize", "resize-none-box", "resize_none_box", 428,
     "CD-3", "CD-4", "CD-4", "c3", "c4", "c3", 200, 160, 120, "None", "Cards", "Keep", "cards",
     "`resize:none` forbids growing so stored both x is CD-4.",
     "Not extra8 resize-both-box, not r resize-horizontal.",
     "none is not both. Keep CD-3 by ref."),
    ("pointer-events", "auto", "fill", "pointerEvents", "pe-fill", "pe_fill", 410,
     "CH-2", "CH-3", "CH-3", "c2", "c3", "c3", 80, 80, 64, "Fill", "Chips", "Keep", "chips",
     "`pointer-events:fill` hits the fill only so a stroke click falls through to CH-3.",
     "Not extra8 pointer-events-none, not r pointer-events-stroke.",
     "fill is not stroke. Keep CH-2 by ref."),
    ("float", "left", "none", "float", "float-none", "float_none", 412,
     "FL-3", "FL-4", "FL-4", "c3", "c4", "c4", 16, 80, 80, "None", "Floats", "Keep", "floats",
     "`float:none` (r left already) unfloats so stored left x is FL-4.",
     "Not r float-left, not r float-right.",
     "none is not left. Keep FL-3 by ref."),
    ("clear", "none", "left", "clear", "clear-left", "clear_left", 410,
     "FL-3", "FL-4", "FL-4", "c3", "c4", "c4", 16, 16, 160, "Clear left", "Floats", "Keep", "floats",
     "`clear:left` drops below a left float so stored none y is FL-4.",
     "Not r clear-both, not r clear-right.",
     "clear:left is live. Keep FL-3 by ref."),
    ("vertical-align", "baseline", "sub", "verticalAlign", "valign-sub", "valign_sub", 410,
     "GL-2", "GL-3", "GL-3", "c2", "c3", "c3", 88, 88, 72, "Sub", "Glyphs", "Keep", "glyphs",
     "`vertical-align:sub` drops glyphs so stored baseline y is GL-3.",
     "Not extra8 valign-super, not r vertical-align-middle.",
     "sub is not super. Keep GL-2 by ref."),
    ("list-style-position", "inside", "outside", "listStylePosition", "list-pos-outside", "list_pos_outside", 449,
     "LI-2", "mark", "mark", "c2", "m1", "m1", 8, 24, 40, "Outside", "Lists", "Keep", "lists",
     "`list-style-position:outside` hangs the marker. Clicking the marker slot is not LI-2.",
     "Not extra8 list-pos-inside, not extra6 display-list-item.",
     "An outside marker is not the item. Keep the listitem ref."),
    ("content", "normal", "open-quote", "content", "content-open-quote", "content_open_quote", 415,
     "TX-2", "TX-3", "TX-3", "c2", "c3", "c3", 40, 24, 36, "Open-quote", "Text", "Keep", "text",
     "`content:open-quote` paints a quote glyph so OCR of neighboring text is TX-3.",
     "Not extra8 quotes-custom, not extra7 quotes-none.",
     "Generated quotes are still TX-2. File the a11y string."),
    ("table-layout", "fixed", "auto", "tableLayout", "table-layout-auto", "table_layout_auto", 428,
     "CH-2", "CH-3", "CH-3", "c2", "c3", "c3", 140, 80, 64, "Auto", "Chips", "Keep", "chips",
     "`table-layout:auto` (r fixed already) sizes by content so stored fixed x is CH-3.",
     "Not r table-layout mill clone, not extra6 display-table.",
     "auto table-layout is live. Keep CH-2 by ref."),
    ("caption-side", "top", "bottom", "captionSide", "caption-bottom", "caption_bottom", 410,
     "RW-2", "RW-3", "RW-3", "c2", "c3", "c3", 24, 24, 96, "Bottom", "Rows", "Keep", "rows",
     "`caption-side:bottom` moves the caption so stored top y is RW-3.",
     "Not r caption-side mill clone, not extra8 page-landscape.",
     "caption-side is live. Keep RW-2 by ref."),
    ("empty-cells", "show", "hide", "emptyCells", "empty-hide", "empty_hide", 404,
     "CH-2", "hole", "hole", "c2", "h1", "h1", 80, 80, 64, "Hide empty", "Chips", "Keep", "chips",
     "`empty-cells:hide` unpaints an empty cell. Stored show x is a hole.",
     "Not r empty-cells mill clone, not extra8 display-none.",
     "Hidden empty cells are still the chip if you use the ref."),
    ("border-spacing", "0px", "8px", "borderSpacing", "border-spacing-8", "border_spacing_8", 412,
     "CH-2", "CH-3", "CH-3", "c2", "c3", "c3", 80, 88, 64, "Spacing 8", "Chips", "Keep", "chips",
     "`border-spacing:8px` gaps table cells so stored 0 x is CH-3.",
     "Not r border-spacing mill clone, not extra8 column-gap-24.",
     "border-spacing is live. Keep CH-2 by ref."),
    ("text-overflow", "ellipsis", "clip", "textOverflow", "text-overflow-clip", "text_overflow_clip", 414,
     "BINDING-COMPLETE", "BIND…", "BIND", "c1", "c1", "c0", 24, 24, 48, "Clip", "Labels", "Keep", "labels",
     "`text-overflow:clip` (r ellipsis already) drops the dots so OCR BIND… is a different wrap.",
     "Not r text-overflow-ellipsis, not extra8 text-wrap-nowrap.",
     "clip is not ellipsis. File the a11y string."),
    ("math-shift", "normal", "compact", "mathShift", "math-shift-compact", "math_shift_compact", 418,
     "EQ-4", "EQ-5", "EQ-5", "c4", "c5", "c5", 110, 92, 88, "Shift compact", "Equations", "Keep", "equations",
     "`math-shift:compact` tucks superscripts so stored normal x is EQ-5.",
     "Not extra6 math-style-compact, not r226 math-shift compact mill.",
     "math-shift is a used box. File EQ-4 by ref."),
    ("field-sizing", "fixed", "content", "fieldSizing", "field-sizing-content", "field_sizing_content", 428,
     "CH-2", "CH-3", "CH-3", "c2", "c3", "c3", 80, 140, 64, "Content", "Chips", "Keep", "chips",
     "`field-sizing:content` grows the control so stored fixed x is CH-3.",
     "Not r field-sizing mill clone, not extra8 font-size-24.",
     "field-sizing is live. Keep CH-2 by ref."),
    ("interpolate-size", "numeric-only", "allow-keywords", "interpolateSize", "interpolate-allow", "interpolate_allow", 412,
     "CH-2", "CH-3", "CH-3", "c2", "c3", "c3", 80, 140, 64, "Allow keywords", "Chips", "Keep", "chips",
     "`interpolate-size:allow-keywords` lets auto animate so stored numeric-only x is CH-3.",
     "Not r interpolate-size mill clone, not extra8 trans-shorthand.",
     "allow-keywords is live. Keep CH-2 by ref."),
    ("print-color-adjust", "economy", "exact", "printColorAdjust", "print-exact", "print_exact", 415,
     "BD-2", "BD-3", "BD-3", "c2", "c3", "c3", 140, 140, 80, "Exact", "Badges", "Keep", "badges",
     "`print-color-adjust:exact` vs economy so a print screenshot luminance blob is not the badge.",
     "Not r392 print-color-adjust mill clone, not extra7 bg-canvas.",
     "exact print color is paint. Keep the badge ref."),
    ("caret-color", "auto", "Canvas", "caretColor", "caret-canvas", "caret_canvas", 415,
     "CH-2", "CH-3", "CH-3", "c2", "c3", "c3", 80, 80, 64, "Caret Canvas", "Chips", "Keep", "chips",
     "`caret-color:Canvas` hides the caret against the canvas so a screenshot looks unfocused on CH-3.",
     "Not r caret-color-transparent, not extra8 caret-block-sh.",
     "Canvas caret is paint. Keep the chip ref."),
    ("scrollbar-width", "auto", "none", "scrollbarWidth", "scrollbar-width-none", "scrollbar_width_none", 425,
     "LN-4", "LN-5", "LN-6", "c4", "c5", "c6", 200, 240, 24, "Width none", "Lanes", "Keep", "lanes",
     "`scrollbar-width:none` frees the gutter so stored auto x is LN-6.",
     "Not r scrollbar-width mill clone, not extra6 scrollbar-gutter-both.",
     "none is not a gutter. Keep the on-screen item ref."),
    ("mask-size", "auto", "contain", "maskSize", "mask-size-contain", "mask_size_contain", 404,
     "CD-3", "hole", "hole", "c3", "h1", "h1", 160, 160, 80, "Mask contain", "Cards", "Keep", "cards",
     "`mask-size:contain` letterboxes the mask. Stored auto x is a hole.",
     "Not r mask-size mill clone, not extra8 mask-shorthand.",
     "A contained mask hole is still the card ref."),
    ("mask-position", "center", "left top", "maskPosition", "mask-pos-left", "mask_pos_left", 404,
     "CD-3", "hole", "hole", "c3", "h1", "h1", 160, 100, 80, "Mask left", "Cards", "Keep", "cards",
     "`mask-position:left top` slides the mask. Stored center x is a hole.",
     "Not r mask-position mill clone, not extra8 mask-shorthand.",
     "A shifted mask hole is still the card ref."),
    ("clip-path", "none", "ellipse(40% 50% at 50% 50%)", "clipPath", "clip-path-ellipse-80", "clip_path_ellipse_80", 404,
     "CD-3", "hole", "hole", "c3", "h1", "h1", 160, 200, 80, "Ellipse 40", "Cards", "Keep", "cards",
     "`clip-path:ellipse(40% 50%)` cuts the card. Stored none x is a hole.",
     "Not extra6 clip-polygon, not r clip-path-circle.",
     "An ellipse clip is still the card ref. Do not keep the hole."),
    ("shape-margin", "0px", "16px", "shapeMargin", "shape-margin-16", "shape_margin_16", 412,
     "FL-3", "FL-4", "FL-4", "c3", "c4", "c4", 16, 32, 80, "Shape margin 16", "Floats", "Keep", "floats",
     "`shape-margin:16px` pushes wrap so stored 0 x is FL-4.",
     "Not r shape-margin mill clone, not r shape-outside.",
     "shape-margin is live. Keep FL-3 by ref."),
    ("offset-path", "none", "path('M0,0 A40,40 0 0 1 40,0')", "offsetPath", "offset-path-arc", "offset_path_arc", 520,
     "BY-5", "BY-6", "BY-6", "c5", "c6", "c5", 80, 120, 40, "Arc path", "Floats", "Keep", "floats",
     "`offset-path:path(arc)` parks abspos on the arc so stored none x is BY-6.",
     "Not extra8 offset-sh, not r164 offset-path mill.",
     "offset-path arc is live. Keep BY-5 by ref."),
    ("perspective", "none", "200px", "perspective", "perspective-200", "perspective_200", 520,
     "CD-3", "CD-4", "CD-4", "c3", "c4", "c3", 160, 140, 80, "Persp 200", "Cards", "Keep", "cards",
     "`perspective:200px` foreshortens children so stored none x misses.",
     "Not r perspective mill clone, not extra8 rotate-y-40.",
     "perspective is live. Keep CD-3 by ref."),
    ("transform-box", "border-box", "fill-box", "transformBox", "transform-box-fill", "transform_box_fill", 520,
     "CD-3", "CD-4", "CD-4", "c3", "c4", "c3", 160, 148, 80, "Fill-box", "Cards", "Keep", "cards",
     "`transform-box:fill-box` retargets the transform origin so stored border-box x misses.",
     "Not r transform-box mill clone, not r transform-origin.",
     "fill-box is live. Keep CD-3 by ref."),
    ("grid-auto-columns", "auto", "80px", "gridAutoColumns", "grid-auto-cols", "grid_auto_cols", 428,
     "CD-2", "CD-3", "CD-3", "c2", "c3", "c3", 40, 80, 80, "Auto cols 80", "Cards", "Keep", "cards",
     "`grid-auto-columns:80px` sizes implicit cols so stored auto x is CD-3.",
     "Not r grid-auto-columns mill clone, not extra6 grid-auto-rows.",
     "auto-columns are live. Keep CD-2 by ref."),
    ("place-items", "stretch", "start", "placeItems", "place-items-start", "place_items_start", 412,
     "CD-2", "CD-3", "CD-3", "c2", "c3", "c3", 80, 40, 80, "Items start", "Cards", "Keep", "cards",
     "`place-items:start` packs each cell so stored stretch x is CD-3.",
     "Not r place-items mill clone, not extra6 justify-items-end.",
     "place-items start is live. Keep CD-2 by ref."),
    ("align-content", "stretch", "start", "alignContent", "align-content-start", "align_content_start", 410,
     "CD-2", "CD-3", "CD-3", "c2", "c3", "c3", 40, 40, 40, "Content start", "Cards", "Keep", "cards",
     "`align-content:start` packs rows so stored stretch y is CD-3.",
     "Not r align-content-stretch, not extra6 justify-items-stretch.",
     "align-content start is live. Keep CD-2 by ref."),
    ("gap", "0px", "24px", "gap", "gap-24", "gap_24", 412,
     "CH-3", "CH-4", "CH-4", "c3", "c4", "c4", 120, 144, 64, "Gap 24", "Chips", "Keep", "chips",
     "`gap:24px` restacks both axes so stored 0-gap x is CH-4.",
     "Not extra mill gap-shorthand, not extra8 column-gap-24.",
     "gap 24 is live. Keep CH-3 by ref."),
    ("masonry-auto-flow", "pack", "next", "masonryAutoFlow", "masonry-auto", "masonry_auto", 428,
     "CD-2", "CD-4", "CD-4", "c2", "c4", "c4", 40, 200, 80, "Masonry next", "Cards", "Keep", "cards",
     "`masonry-auto-flow:next` forbids packing holes so stored pack x is CD-4.",
     "Not extra6 grid-flow-dense, not r masonry mill clone.",
     "masonry next is live. Keep CD-2 by ref."),
    ("position-area", "none", "start", "positionArea", "position-area-start", "position_area_start", 507,
     "AB-2", "AB-3", "AB-3", "c2", "c3", "c3", 16, 8, 48, "Area start", "Abspos", "Keep", "abspos",
     "`position-area:start` slots abspos into the start region so stored none x is empty.",
     "Not extra8 inset-area-start, not r position-area mill.",
     "position-area is live. Keep AB-2 by ref."),
    ("inset", "0px", "24px", "inset", "inset-sh-24", "inset_sh_24", 412,
     "AB-2", "AB-3", "AB-3", "c2", "c3", "c3", 16, 40, 48, "Inset 24", "Abspos", "Keep", "abspos",
     "`inset:24px` (shorthand) slides abspos so stored 0 x is empty.",
     "Not r inset-shorthand mill, not extra8 inset-area-start.",
     "inset shorthand is live. Keep AB-2 by ref."),
    ("hyphenate-limit-zone", "0px", "8em", "hyphenateLimitZone", "hyphenate-zone-8em", "hyphenate_zone_8em", 414,
     "BINDING-COMPLETE", "BIND…", "BIND", "c1", "c1", "c0", 24, 24, 48, "Zone 8em", "Labels", "Keep", "labels",
     "`hyphenate-limit-zone:8em` forbids a short leftover so OCR BIND… is a different break.",
     "Not r hyphenate-zone mill clone, not extra8 hyphenate-eq.",
     "Limit-zone is not limit-chars. File the a11y string."),
    ("overflow-wrap", "normal", "anywhere", "overflowWrap", "overflow-wrap-any", "overflow_wrap_any", 400,
     "LB-2", "LB-3", "LB-3", "c2", "c3", "c3", 24, 24, 48, "Anywhere", "Labels", "Keep", "labels",
     "`overflow-wrap:anywhere` allows mid-word wraps so OCR BIND… is a different wrap.",
     "Not r overflow-wrap-anywhere mill clone, not extra8 line-break-any.",
     "anywhere wrap is not line-break. File the a11y string."),
    ("word-break", "normal", "keep-all", "wordBreak", "keep-all-run", "keep_all_run", 400,
     "LB-2", "LB-3", "LB-3", "c2", "c3", "c3", 24, 24, 48, "Keep-all", "Labels", "Keep", "labels",
     "`word-break:keep-all` forbids CJK breaks so OCR BIND… is a different wrap.",
     "Not extra6 keep-all-cjk, not extra8 break-auto-phrase.",
     "keep-all is not auto-phrase. File the a11y string."),
    ("white-space", "normal", "pre", "whiteSpace", "ws-pre", "ws_pre", 413,
     "LB-2", "LB-3", "LB-3", "c2", "c3", "c3", 24, 24, 48, "Pre", "Labels", "Keep", "labels",
     "`white-space:pre` keeps spaces and forbids wrap so a normal wrap line is LB-3.",
     "Not extra8 ws-pre-line, not r white-space-pre mill.",
     "pre is not pre-line. File the a11y string."),
    ("content-visibility", "hidden", "visible", "contentVisibility", "cv-visible", "cv_visible", 410,
     "RW-12", "RW-13", "RW-1", "c12", "c13", "c1", 0, 0, 480, "Visible", "Rows", "Keep", "rows",
     "`content-visibility:visible` (r hidden / auto already) restores render so stale hidden y is empty.",
     "Not extra8 cv-auto, not extra7 content-visibility-hidden.",
     "visible is not auto virtualize. Re-find the row ref."),
    ("isolation", "isolate", "auto", "isolation", "isolation-auto-run", "isolation_auto_run", 464,
     "SW-2", "SW-3", "SW-3", "c2", "c3", "c3", 154, 154, 88, "Auto", "Blends", "Keep", "blends",
     "`isolation:auto` (r isolate already) drops the stacking root so stored isolate blend looks unselected.",
     "Not extra7 isolation-isolate, not r isolation-auto mill clone.",
     "auto is not isolate. Keep aria-selected / the ref."),
    ("mix-blend-mode", "normal", "plus-lighter", "mixBlendMode", "blend-plus-lighter-run", "blend_plus_lighter_run", 464,
     "SW-2", "SW-3", "SW-3", "c2", "c3", "c3", 154, 154, 88, "Plus-lighter", "Blends", "Keep", "blends",
     "`mix-blend-mode:plus-lighter` blows the selected chip to white so a screenshot looks empty.",
     "Not r218 plus-lighter mill clone, not extra8 blend-multiply.",
     "plus-lighter is not empty. Keep aria-selected / the ref."),
    ("filter", "none", "url(#noise)", "filter", "filter-url-noise", "filter_url_noise", 404,
     "CD-3", "CD-4", "CD-4", "c3", "c4", "c3", 160, 176, 80, "Url noise", "Cards", "Keep", "cards",
     "`filter:url(#noise)` displaces paint. The screenshot blob is not CD-3.",
     "Not r filter-url mill clone, not extra8 filter-drop-shadow.",
     "A filter URL blob is paint. Keep CD-3 by ref."),
    ("object-view-box", "none", "xywh(10% 10% 80% 80%)", "objectViewBox", "object-view-xywh", "object_view_xywh", 404,
     "BD-2", "BD-3", "BD-3", "c2", "c3", "c3", 140, 126, 80, "View xywh", "Badges", "Keep", "badges",
     "`object-view-box:xywh(10% 10% 80% 80%)` crops the replaced box so stored none x is empty.",
     "Not extra8 object-view-inset, not r object-view-box mill.",
     "xywh view-box is paint. Keep the badge ref."),
    ("page", "auto", "portrait", "page", "page-portrait", "page_portrait", 416,
     "TX-2", "TX-5", "TX-5", "c2", "c5", "c5", 40, 24, 36, "Portrait", "Text", "Keep", "text",
     "`page:portrait` reflows print fragmentation so stored auto x is TX-5.",
     "Not extra8 page-landscape, not r break-after-page.",
     "Named portrait page is live. Keep TX-2 by ref."),
    ("break-before", "auto", "column", "breakBefore", "break-before-column", "break_before_column", 416,
     "TX-2", "TX-5", "TX-5", "c2", "c5", "c5", 40, 24, 36, "Before column", "Text", "Keep", "text",
     "`break-before:column` forces a column break so stored auto x is TX-5.",
     "Not r break-after-page, not extra8 page-break-inside.",
     "break-before column is live. Keep TX-2 by ref."),
    ("reading-order", "0", "-1", "readingOrder", "reading-order-n1", "reading_order_n1", 428,
     "CD-2", "CD-4", "CD-4", "c2", "c4", "c4", 200, 40, 80, "Order -1", "Cards", "Keep", "cards",
     "`reading-order:-1` pulls the card first in a11y order so stored 0 x is CD-4.",
     "Not extra8 reading-order-2, not extra8 reading-flow-rows.",
     "reading-order -1 is not flex order. Keep CD-2 by ref."),
    ("scroll-timeline-axis", "inline", "block", "scrollTimelineAxis", "scroll-tl-block", "scroll_tl_block", 412,
     "CH-2", "CH-3", "CH-3", "c2", "c3", "c3", 80, 80, 120, "Axis block", "Chips", "Keep", "chips",
     "`scroll-timeline-axis:block` drives the timeline from y-scroll so stored inline x is CH-3.",
     "Not extra8 scroll-tl-axis, not r scroll-timeline-name.",
     "Axis block is not inline. Keep CH-2 by ref."),
    ("text-spacing-trim", "space-all", "trim-all", "textSpacingTrim", "text-spacing-trim-all", "text_spacing_trim_all", 412,
     "GL-2", "GL-3", "GL-3", "c2", "c3", "c3", 88, 70, 56, "Trim all", "Glyphs", "Keep", "glyphs",
     "`text-spacing-trim:trim-all` eats CJK spacing so stored space-all x is GL-3.",
     "Not r text-spacing-trim mill clone, not extra5 text-autospace.",
     "trim-all is live. Keep GL-2 by ref."),
    ("font-language-override", "normal", "SRB", "fontLanguageOverride", "font-lang-override", "font_lang_override", 412,
     "GL-2", "GL-3", "GL-3", "c2", "c3", "c3", 88, 100, 56, "Lang SRB", "Glyphs", "Keep", "glyphs",
     "`font-language-override:SRB` swaps locl glyphs so stored normal x is GL-3.",
     "Not r font-feature-settings, not extra8 font-shorthand.",
     "Language override is live metrics. Keep GL-2 by ref."),
    ("image-resolution", "300dpi", "from-image", "imageResolution", "image-res-from-image", "image_res_from_image", 404,
     "BD-2", "BD-3", "BD-3", "c2", "c3", "c3", 100, 140, 80, "From-image", "Badges", "Keep", "badges",
     "`image-resolution:from-image` (r extra8 300dpi) retimes the replaced box so stored 300dpi x is empty.",
     "Not extra8 image-res-300, not extra8 image-orient-none.",
     "from-image resolution is paint/metrics. Keep the badge ref."),
    ("max-lines", "none", "3", "maxLines", "max-lines-3", "max_lines_3", 414,
     "BINDING-COMPLETE", "BIND…", "BIND", "c1", "c1", "c0", 24, 24, 48, "Max 3", "Labels", "Keep", "labels",
     "`max-lines:3` clamps so OCR BIND… is a different wrap.",
     "Not extra8 max-lines-2, not r line-clamp-1.",
     "max-lines 3 is not 2. File the a11y string."),
]

GENERA = [
    "festuca", "poa", "bromus", "agrostis", "calamagrostis", "deschampsia", "koeleria", "ammophila", "elymus", "hordeum",
    "carex", "scirpus", "juncus", "luzula", "eleocharis", "rhynchospora", "eriophorum", "trichophorum", "bolboschoenus", "schoenoplectus",
    "cyperus", "fimbristylis", "scleria", "cladium", "mapania", "hypolytrum", "lepironia", "oreobolus", "carpha", "costularia",
    "andropogon", "sorghastrum", "schizachyrium", "bouteloua", "buchloe", "distichlis", "spartina", "phragmites", "arundo", "panicum",
    "setaria", "pennisetum", "cenchrus", "digitaria", "eragrostis", "sporobolus", "muhlenbergia", "aristida", "stipa", "nassella",
    "jarava", "austrostipa", "rytidosperma", "chionochloa", "bambusa", "phyllostachys", "fargesia", "sasa", "pleioblastus", "indocalamus",
    "chimonobambusa", "sinobambusa", "semiarundinaria", "shibataea", "pseudosasa", "otatea", "guadua", "orchis", "dactylorhiza", "platanthera",
    "gymnadenia", "anacamptis", "ophrys", "serapias", "epipactis", "cephalathera", "neottia", "goodyera", "spiranthes", "liparis",
    "malaxis", "corallorhiza", "calypso", "cypripedium", "paphiopedilum", "phragmipedium", "vanilla", "cattleya", "dendrobium", "oncidium",
    "odontoglossum", "miltonia", "masdevallia", "pleurothallis", "stelis", "restrepia", "dracula", "epidendrum", "laelia", "brassavola",
    "sophronitis", "encyclia", "catasetum", "stanhopea", "coryanthes", "peristeria", "lycaste", "anguloa", "maxillaria", "bifrenaria",
    "rudolfiella",
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


def extra_used() -> tuple[set[str], set[str], set[str], set[str], set[str], set[str], set[str]]:
    used_w, used_es, used_pl, used_pr, used_ax, used_seed, used_err = (
        load_set("widgets"), load_set("errslugs"), load_set("places"),
        load_set("prefixes"), load_set("auxes"), load_set("seeds"), load_set("errs"),
    )
    for name in ("brw-mill-r395-extra8.py",):
        path = HERE / name
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(mod)
        for p in mod.EXTRA:
            used_w.add(p["widget"])
            used_es.add(p["err_slug"])
            used_pl.add(p["ok_place"])
            used_pl.add(p["bad_place"])
            used_pr.add(p["prefix"])
            used_ax.add(p["aux"])
            used_seed.add(p["seed_ok"])
            used_seed.add(p["seed_bad"])
            used_err.add(p["err"])
    return used_w, used_es, used_pl, used_pr, used_ax, used_seed, used_err


def main() -> int:
    used_w, used_es, used_pl, used_pr, used_ax, used_seed, used_err = extra_used()
    used_keep: set[str] = set()
    assert len(PLANTS) <= len(GENERA), (len(PLANTS), len(GENERA))
    rows = []
    for i, plant in enumerate(PLANTS):
        (css, fr, to, js, widget, err, code, item, neigh, fail, ref, nref, fref,
         x0, x1, y, btn, title, verb, path, new, not_, teach) = plant
        if code == 409:
            raise SystemExit(f"{widget}: 409 banned")
        if widget in used_w:
            raise SystemExit(f"widget collision {widget}")
        used_w.add(widget)
        if err in used_err:
            err = err + "_x9"
            if err in used_err:
                raise SystemExit(f"err collision {err}")
        used_err.add(err)
        prefix = mint("".join(ch for ch in widget if ch.isalnum())[:4] or "e9p", used_pr)
        aux = mint(("".join(ch for ch in widget if ch.isalnum())[2:6] or "e9a") + "x", used_ax)
        if prefix == aux:
            aux = mint(aux + "z", used_ax)
        genus = GENERA[i]
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
            seed_ok = f"css-{widget}-x9"
            seed_bad = f"css-{widget}-x9-{code}"
        if seed_ok in used_seed or seed_bad in used_seed:
            raise SystemExit(f"seed collision {seed_ok}")
        used_seed.add(seed_ok)
        used_seed.add(seed_bad)
        keep = keep_code(genus, used_keep)
        note = f"{item} {genus}"
        nxt = PLANTS[i + 1][4] if i + 1 < len(PLANTS) else "catalog continue."
        row = (
            prefix, aux, ok, bad, widget, slug, code, err,
            css, fr, to, js, item, neigh, fail, ref, nref, fref,
            x0, x1, y, btn, title, verb, path, keep, note, seed_ok, seed_bad,
            new, not_, teach, nxt + ".",
        )
        rows.append(row)

    out = HERE / "brw-mill-r395-extra9.py"
    lines = [
        '"""Leftover CSS plants r846+."""',
        "KEYS = (",
        '    "prefix", "aux", "ok_place", "bad_place", "widget", "err_slug", "code", "err",',
        '    "css", "from", "to", "js", "item", "neigh", "fail_item", "ref", "nref", "fref",',
        '    "x0", "x1", "y", "btn", "title", "verb", "path", "keep", "note", "seed_ok", "seed_bad",',
        '    "new", "not", "teach", "next",',
        ")",
        "ROWS = [",
    ]
    for row in rows:
        lines.append("(" + ",".join(repr(v) for v in row) + "),")
    lines.append("]")
    lines.append("EXTRA = [dict(zip(KEYS, row)) for row in ROWS]")
    lines.append("")
    out.write_text("\n".join(lines))
    print(f"wrote {out} plants={len(rows)} last={rows[-1][4]} {rows[-1][2]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
