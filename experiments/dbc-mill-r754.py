#!/usr/bin/env python3
"""Mill docker-build-cache-factory r754+. Graphics/input leftover plants.

BAN r645 nerdctl, r646 containerd, r549 scsh/scsi-debug, GNU Prolog/landlock/
SWI pack/seccomp/AppArmor/GOTOOLCHAIN clones, harbor-pin, leftover×sysctl.
17-step success + 18-step leftover. meta.generator=grok-4.6. Q=2.
Stable PAIRS indices.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("dbc_mill_r719", HERE / "dbc-mill-r719.py")
_m = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_m)

FACTORY = _m.FACTORY
GEN = _m.GEN
FACTORY_DIR = _m.FACTORY_DIR
lang = _m.lang
leftover = _m.leftover
success_episode = _m.success_episode
leftover_episode = _m.leftover_episode
notes_for = _m.notes_for
BANNED_NEEDLES = _m.BANNED_NEEDLES
slug_taken = _m.slug_taken

PAIRS: list[tuple[dict, dict]] = [
    (
        lang("potrace-cache", "POTRACE_HOME", "potrace", "1.16", "1.16.1",
             "share/potrace/potrace.1", "test_potrace.py", "src/demo.pbm", "pt-1161",
             "rm -rf /usr/share/potrace",
             "rm share does not drop 1.16 potrace.1 under unversioned POTRACE_HOME",
             "1MB", "this mill autotrace / r imagemagick-config (Potrace man, not Autotrace or ImageMagick)",
             "potrace src/demo.pbm", "potrace --version"),
        leftover("gspca-leftover", "GSPCA_CLEAR", "gspca n_devs=1",
                 "gspca leftover still webcams cache as n_devs=1",
                 "modprobe -r gspca_main",
                 "modprobe -r is EBUSY; leftover n_devs=1 still webcams cache",
                 "leftover gspca webcaming cache",
                 "r vivid / r vicodec / cache-admin 403",
                 "r vivid leftover (gspca leftover, not vivid n_devs)",
                 "test_gspca.py",
                 "ls /sys/module/gspca_main; v4l2-ctl --list-devices",
                 "gspca leftover n_devs=1 leftover"),
    ),
    (
        lang("autotrace-cache", "AUTOTRACE_HOME", "autotrace", "0.31.1", "0.31.10",
             "share/autotrace/input-magick.la", "test_autotrace.py", "src/demo.bmp", "at-3110",
             "rm -rf /usr/share/autotrace",
             "rm share does not drop 0.31.1 input-magick.la under unversioned AUTOTRACE_HOME",
             "2MB", "this mill potrace / r imagemagick-config (Autotrace magick.la, not Potrace or ImageMagick)",
             "autotrace src/demo.bmp", "autotrace --version"),
        leftover("pwc-leftover", "PWC_CLEAR", "pwc mbufs=2",
                 "pwc leftover still webcams cache as mbufs=2",
                 "modprobe -r pwc",
                 "modprobe -r is EBUSY; leftover mbufs=2 still webcams cache",
                 "leftover pwc webcaming cache",
                 "this mill gspca / r vivid / cache-admin 403",
                 "this mill gspca leftover (pwc leftover, not gspca n_devs)",
                 "test_pwc.py",
                 "ls /sys/module/pwc; v4l2-ctl --list-devices",
                 "pwc leftover mbufs=2 leftover"),
    ),
    (
        lang("inkscape-ext-cache", "INKSCAPE_DATADIR", "inkscape", "1.3.2", "1.4.0",
             "share/inkscape/extensions/dxf_outlines.py", "test_ink.py", "src/demo.svg", "ink-140",
             "rm -rf /usr/share/inkscape",
             "rm extensions does not drop 1.3 dxf_outlines.py under unversioned INKSCAPE_DATADIR",
             "28MB", "this mill potrace / this mill gimp-plugins (Inkscape dxf_outlines, not Potrace or GIMP)",
             "inkscape src/demo.svg", "inkscape --version"),
        leftover("stkwebcam-leftover", "STKWEBCAM_CLEAR", "stkwebcam n_devs=1",
                 "stkwebcam leftover still webcams cache as n_devs=1",
                 "modprobe -r stkwebcam",
                 "modprobe -r is EBUSY; leftover n_devs=1 still webcams cache",
                 "leftover stkwebcam webcaming cache",
                 "this mill pwc / this mill gspca / cache-admin 403",
                 "this mill pwc leftover (stkwebcam leftover, not pwc mbufs)",
                 "test_stk.py",
                 "ls /sys/module/stkwebcam; v4l2-ctl --list-devices",
                 "stkwebcam leftover n_devs=1 leftover"),
    ),
    (
        lang("gimp-plugins-cache", "GIMP2_DATADIR", "gimp", "2.10.36", "3.0.0",
             "lib/gimp/2.0/plug-ins/file-png/file-png", "test_gimp.py", "src/demo.xcf", "gimp-300",
             "rm -rf /usr/lib/gimp",
             "rm plug-ins does not drop 2.10 file-png under unversioned GIMP2_DATADIR",
             "42MB", "this mill inkscape-ext / this mill krita-resources (GIMP file-png, not Inkscape or Krita)",
             "gimp-console src/demo.xcf", "gimp-console --version"),
        leftover("ov511-leftover", "OV511_CLEAR", "ov511 n_devs=1",
                 "ov511 leftover still webcams cache as n_devs=1",
                 "modprobe -r ov511",
                 "modprobe -r is EBUSY; leftover n_devs=1 still webcams cache",
                 "leftover ov511 webcaming cache",
                 "this mill stkwebcam / this mill gspca / cache-admin 403",
                 "this mill stkwebcam leftover (ov511 leftover, not stkwebcam n_devs)",
                 "test_ov511.py",
                 "ls /sys/module/ov511; v4l2-ctl --list-devices",
                 "ov511 leftover n_devs=1 leftover"),
    ),
    (
        lang("darktable-cache", "DARKTABLE_DATADIR", "darktable", "4.6.1", "5.0.0",
             "share/darktable/styles/base.dtstyle", "test_dt.py", "src/demo.cr2", "dt-500",
             "rm -rf /usr/share/darktable",
             "rm styles does not drop 4.6 base.dtstyle under unversioned DARKTABLE_DATADIR",
             "35MB", "this mill rawtherapee / this mill gimp-plugins (darktable styles, not RawTherapee or GIMP)",
             "darktable-cli src/demo.cr2", "darktable --version"),
        leftover("sn9c102-leftover", "SN9C102_CLEAR", "sn9c102 n_devs=1",
                 "sn9c102 leftover still webcams cache as n_devs=1",
                 "modprobe -r sn9c102",
                 "modprobe -r is EBUSY; leftover n_devs=1 still webcams cache",
                 "leftover sn9c102 webcaming cache",
                 "this mill ov511 / this mill gspca / cache-admin 403",
                 "this mill ov511 leftover (sn9c102 leftover, not ov511 n_devs)",
                 "test_sn9c.py",
                 "ls /sys/module/sn9c102; v4l2-ctl --list-devices",
                 "sn9c102 leftover n_devs=1 leftover"),
    ),
    (
        lang("rawtherapee-cache", "RT_DATA_DIR", "rawtherapee", "5.10", "5.11",
             "share/rawtherapee/dcpprofiles/canon.dcp", "test_rt.py", "src/demo.nef", "rt-511",
             "rm -rf /usr/share/rawtherapee",
             "rm dcpprofiles does not drop 5.10 canon.dcp under unversioned RT_DATA_DIR",
             "19MB", "this mill darktable / this mill gimp-plugins (RawTherapee DCP, not darktable or GIMP)",
             "rawtherapee-cli src/demo.nef", "rawtherapee --version"),
        leftover("zr364xx-leftover", "ZR364XX_CLEAR", "zr364xx n_devs=1",
                 "zr364xx leftover still webcams cache as n_devs=1",
                 "modprobe -r zr364xx",
                 "modprobe -r is EBUSY; leftover n_devs=1 still webcams cache",
                 "leftover zr364xx webcaming cache",
                 "this mill sn9c102 / this mill ov511 / cache-admin 403",
                 "this mill sn9c102 leftover (zr364xx leftover, not sn9c102 n_devs)",
                 "test_zr364.py",
                 "ls /sys/module/zr364xx; v4l2-ctl --list-devices",
                 "zr364xx leftover n_devs=1 leftover"),
    ),
    (
        lang("krita-resources-cache", "KRITA_RESOURCE_DIR", "krita", "5.2.2", "5.2.9",
             "share/krita/brushes/a)_Eraser_Circle.gbr", "test_krita.py", "src/demo.kra", "kra-529",
             "rm -rf /usr/share/krita",
             "rm brushes does not drop 5.2 Eraser_Circle.gbr under unversioned KRITA_RESOURCE_DIR",
             "55MB", "this mill mypaint-brushes / this mill gimp-plugins (Krita gbr, not MyPaint or GIMP)",
             "krita src/demo.kra", "krita --version"),
        leftover("cpia2-leftover", "CPIA2_CLEAR", "cpia2 n_devs=1",
                 "cpia2 leftover still webcams cache as n_devs=1",
                 "modprobe -r cpia2",
                 "modprobe -r is EBUSY; leftover n_devs=1 still webcams cache",
                 "leftover cpia2 webcaming cache",
                 "this mill zr364xx / this mill gspca / cache-admin 403",
                 "this mill zr364xx leftover (cpia2 leftover, not zr364xx n_devs)",
                 "test_cpia2.py",
                 "ls /sys/module/cpia2; v4l2-ctl --list-devices",
                 "cpia2 leftover n_devs=1 leftover"),
    ),
    (
        lang("mypaint-brushes-cache", "MYPAINT_DIR", "mypaint", "2.0.1", "2.0.2",
             "share/mypaint/brushes/classic/charcoal.myb", "test_mypaint.py", "src/demo.ora", "mp-202",
             "rm -rf /usr/share/mypaint",
             "rm brushes does not drop 2.0 charcoal.myb under unversioned MYPAINT_DIR",
             "8MB", "this mill krita-resources / this mill gimp-plugins (MyPaint charcoal.myb, not Krita or GIMP)",
             "mypaint src/demo.ora", "mypaint --version"),
        leftover("uvcvideo-leftover", "UVCVIDEO_CLEAR", "uvcvideo quirks=1",
                 "uvcvideo leftover still quirks cache UVC as quirks=1",
                 "modprobe -r uvcvideo",
                 "modprobe -r is EBUSY; leftover quirks=1 still quirks cache UVC",
                 "leftover uvcvideo quirking cache UVC",
                 "this mill gspca / r vivid / cache-admin 403",
                 "this mill gspca leftover (uvcvideo leftover, not gspca n_devs)",
                 "test_uvc.py",
                 "ls /sys/module/uvcvideo/parameters; v4l2-ctl --list-devices",
                 "uvcvideo leftover quirks=1 leftover"),
    ),
    (
        lang("fontforge-sfd-cache", "FONTFORGE_SEARCH_PATH", "fontforge", "20230101", "20241001",
             "share/fontforge/sfd/Ambrosia.sfd", "test_ff.py", "src/demo.sfd", "ff-2410",
             "rm -rf /usr/share/fontforge",
             "rm sfd does not drop 2023 Ambrosia.sfd under unversioned FONTFORGE_SEARCH_PATH",
             "6MB", "this mill harfbuzz-hb / this mill freetype (FontForge Ambrosia.sfd, not HarfBuzz or FreeType)",
             "fontforge src/demo.sfd", "fontforge -version"),
        leftover("kinect-leftover", "KINECT_CLEAR", "gspca_kinect depth=1",
                 "gspca_kinect leftover still depths cache Kinect as depth=1",
                 "modprobe -r gspca_kinect",
                 "modprobe -r is EBUSY; leftover depth=1 still depths cache Kinect",
                 "leftover gspca_kinect depthing cache Kinect",
                 "this mill gspca / this mill uvcvideo / cache-admin 403",
                 "this mill gspca leftover (kinect leftover, not generic gspca n_devs)",
                 "test_kinect.py",
                 "ls /sys/module/gspca_kinect; v4l2-ctl --list-devices",
                 "kinect leftover depth=1 leftover"),
    ),
    (
        lang("harfbuzz-hb-cache", "HB_DATA", "hb-shape", "8.3.0", "10.1.0",
             "share/harfbuzz/perf/fonts/Inconsolata-Regular.abc", "test_hb.py", "src/demo.txt", "hb-101",
             "rm -rf /usr/share/harfbuzz",
             "rm fonts does not drop 8.3 Inconsolata abc under unversioned HB_DATA",
             "3MB", "this mill freetype / this mill fontforge-sfd (HarfBuzz Inconsolata, not FreeType or FontForge)",
             "hb-shape src/demo.txt", "hb-shape --version"),
        leftover("hid-sony-leftover", "HID_SONY_CLEAR", "hid_sony js=cache",
                 "hid_sony leftover still joysticks cache DualShock as js=cache",
                 "modprobe -r hid-sony",
                 "modprobe -r is EBUSY; leftover js=cache still joysticks cache DualShock",
                 "leftover hid_sony joysticking cache DualShock",
                 "r hidraw / r uinput / cache-admin 403",
                 "r hidraw leftover (hid-sony leftover, not hidraw hidraw0)",
                 "test_hidsony.py",
                 "ls /sys/module/hid_sony; cat /sys/class/input/js0/device/name",
                 "hid leftover sony js=cache leftover"),
    ),
    (
        lang("freetype-cache", "FREETYPE_PROPERTIES", "ftdump", "2.13.2", "2.13.3",
             "share/freetype/ftdiff.1", "test_ft.py", "src/demo.ttf", "ft-2133",
             "rm -rf /usr/share/freetype",
             "rm share does not drop 2.13.2 ftdiff.1 under unversioned FREETYPE_PROPERTIES",
             "2MB", "this mill harfbuzz-hb / this mill cairo (FreeType ftdiff.1, not HarfBuzz or Cairo)",
             "ftdump src/demo.ttf", "ftdump -v"),
        leftover("hid-logitech-leftover", "HID_LOGITECH_CLEAR", "hid_logitech kbd=cache",
                 "hid_logitech leftover still keyboards cache as kbd=cache",
                 "modprobe -r hid-logitech",
                 "modprobe -r is EBUSY; leftover kbd=cache still keyboards cache",
                 "leftover hid_logitech keyboarding cache",
                 "this mill hid-sony / r hidraw / cache-admin 403",
                 "this mill hid-sony leftover (hid-logitech leftover, not hid_sony DualShock)",
                 "test_hidlogi.py",
                 "ls /sys/module/hid_logitech; cat /sys/class/input/event0/device/name",
                 "hid leftover logitech kbd=cache leftover"),
    ),
    (
        lang("cairo-cache", "CAIRO_DEBUG", "cairo-trace", "1.18.0", "1.18.2",
             "lib/cairo/libcairo-trace.so", "test_cairo.py", "src/demo.c", "cairo-182",
             "rm -rf /usr/lib/cairo",
             "rm libcairo-trace does not drop 1.18 libcairo-trace.so under unversioned CAIRO_DEBUG",
             "4MB", "this mill pango-modules / this mill freetype (Cairo trace.so, not Pango or FreeType)",
             "cairo-trace src/demo", "pkg-config --modversion cairo"),
        leftover("hid-apple-leftover", "HID_APPLE_CLEAR", "hid_apple fnmode=2",
                 "hid_apple leftover still fnmodes cache as fnmode=2",
                 "modprobe -r hid-apple",
                 "modprobe -r is EBUSY; leftover fnmode=2 still fnmodes cache",
                 "leftover hid_apple fnmoding cache",
                 "this mill hid-logitech / r hidraw / cache-admin 403",
                 "this mill hid-logitech leftover (hid-apple leftover, not hid_logitech kbd)",
                 "test_hidapple.py",
                 "ls /sys/module/hid_apple/parameters; cat /sys/module/hid_apple/parameters/fnmode",
                 "hid leftover apple fnmode=2 leftover"),
    ),
    (
        lang("pango-modules-cache", "PANGO_LIBDIR", "pango-view", "1.52.2", "1.54.0",
             "lib/pango/1.8.0/modules/pango-basic-fc.so", "test_pango.py", "src/demo.txt", "pango-154",
             "rm -rf /usr/lib/pango",
             "rm modules does not drop 1.52 pango-basic-fc.so under unversioned PANGO_LIBDIR",
             "3MB", "this mill cairo / this mill harfbuzz-hb (Pango basic-fc.so, not Cairo or HarfBuzz)",
             "pango-view src/demo.txt", "pango-view --version"),
        leftover("i2c-hid-leftover", "I2C_HID_CLEAR", "i2c_hid proto=cache",
                 "i2c_hid leftover still protos cache HID over I2C as proto=cache",
                 "echo 1 > /sys/bus/i2c/drivers/i2c_hid/unbind",
                 "i2c_hid unbind is EBUSY; leftover proto=cache still protos cache HID over I2C",
                 "leftover i2c_hid protoing cache HID over I2C",
                 "this mill hid-apple / r hidraw / cache-admin 403",
                 "this mill hid-apple leftover (i2c-hid leftover, not hid_apple fnmode)",
                 "test_i2chid.py",
                 "ls /sys/bus/i2c/drivers/i2c_hid; cat /sys/class/input/event0/device/name",
                 "i2c leftover hid proto=cache leftover"),
    ),
    (
        lang("librsvg-cache", "RSVG_HOME", "rsvg-convert", "2.58.0", "2.59.2",
             "lib/gdk-pixbuf-2.0/2.10.0/loaders/libpixbufloader-svg.so", "test_rsvg.py", "src/demo.svg", "rsvg-2592",
             "rm -rf /usr/lib/gdk-pixbuf-2.0",
             "rm loaders does not drop 2.58 libpixbufloader-svg.so under unversioned RSVG_HOME",
             "5MB", "this mill gdk-pixbuf / this mill cairo (librsvg svg loader, not gdk-pixbuf png or Cairo)",
             "rsvg-convert src/demo.svg", "rsvg-convert --version"),
        leftover("synaptics-leftover", "SYNAPTICS_CLEAR", "psmouse proto=synaptics",
                 "psmouse leftover still synaptics-protos cache touchpad as proto=synaptics",
                 "modprobe -r psmouse",
                 "modprobe -r is EBUSY; leftover proto=synaptics still synaptics-protos cache touchpad",
                 "leftover psmouse synaptics-protoing cache touchpad",
                 "this mill i2c-hid / r uinput / cache-admin 403",
                 "this mill i2c-hid leftover (synaptics leftover, not i2c_hid proto)",
                 "test_synaptics.py",
                 "ls /sys/module/psmouse/parameters; cat /sys/class/input/mouse0/device/name",
                 "psmouse leftover proto=synaptics leftover"),
    ),
    (
        lang("gdk-pixbuf-cache", "GDK_PIXBUF_MODULE_FILE", "gdk-pixbuf-query-loaders", "2.42.10", "2.42.12",
             "lib/gdk-pixbuf-2.0/2.10.0/loaders.cache", "test_gdk.py", "src/demo.png", "gdk-24212",
             "rm -rf /usr/lib/gdk-pixbuf-2.0/2.10.0/loaders.cache",
             "rm loaders.cache does not drop 2.42.10 loaders.cache under unversioned GDK_PIXBUF_MODULE_FILE",
             "2MB", "this mill librsvg / this mill gtk4-immodules (gdk-pixbuf loaders.cache, not librsvg svg or GTK4)",
             "gdk-pixbuf-query-loaders", "pkg-config --modversion gdk-pixbuf-2.0"),
        leftover("elantech-leftover", "ELANTECH_CLEAR", "psmouse proto=elantech",
                 "psmouse leftover still elantech-protos cache touchpad as proto=elantech",
                 "echo elantech > /sys/module/psmouse/parameters/proto",
                 "psmouse proto write is EBUSY; leftover proto=elantech still elantech-protos cache touchpad",
                 "leftover psmouse elantech-protoing cache touchpad",
                 "this mill synaptics / this mill i2c-hid / cache-admin 403",
                 "this mill synaptics leftover (elantech leftover, not psmouse proto=synaptics)",
                 "test_elantech.py",
                 "cat /sys/module/psmouse/parameters/proto; cat /sys/class/input/mouse0/device/name",
                 "psmouse leftover proto=elantech leftover"),
    ),
    (
        lang("qt6-plugin-cache", "QT_PLUGIN_PATH", "qmake6", "6.6.2", "6.8.1",
             "lib/qt6/plugins/platforms/libqxcb.so", "test_qt6.py", "src/demo.cpp", "qt-681",
             "rm -rf /usr/lib/qt6/plugins",
             "rm platforms does not drop 6.6 libqxcb.so under unversioned QT_PLUGIN_PATH",
             "22MB", "this mill gtk4-immodules / this mill wxwidgets-lib (Qt6 libqxcb.so, not GTK4 or wx)",
             "qmake6 src/demo.pro", "qmake6 -v"),
        leftover("alps-leftover", "ALPS_CLEAR", "psmouse proto=alps",
                 "psmouse leftover still alps-protos cache touchpad as proto=alps",
                 "echo alps > /sys/module/psmouse/parameters/proto",
                 "psmouse proto write is EBUSY; leftover proto=alps still alps-protos cache touchpad",
                 "leftover psmouse alps-protoing cache touchpad",
                 "this mill elantech / this mill synaptics / cache-admin 403",
                 "this mill elantech leftover (alps leftover, not psmouse proto=elantech)",
                 "test_alps.py",
                 "cat /sys/module/psmouse/parameters/proto; cat /sys/class/input/mouse0/device/name",
                 "psmouse leftover proto=alps leftover"),
    ),
    (
        lang("gtk4-immodules-cache", "GTK_IM_MODULE_FILE", "gtk4-query-immodules", "4.12.5", "4.16.7",
             "lib/gtk-4.0/4.0.0/immodules/im-ibus.so", "test_gtk4.py", "src/demo.c", "gtk4-4167",
             "rm -rf /usr/lib/gtk-4.0",
             "rm immodules does not drop 4.12 im-ibus.so under unversioned GTK_IM_MODULE_FILE",
             "9MB", "this mill qt6-plugin / this mill pango-modules (GTK4 im-ibus.so, not Qt6 or Pango)",
             "gtk4-query-immodules", "pkg-config --modversion gtk4"),
        leftover("sentelic-leftover", "SENTELIC_CLEAR", "psmouse proto=sentelic",
                 "psmouse leftover still sentelic-protos cache touchpad as proto=sentelic",
                 "echo sentelic > /sys/module/psmouse/parameters/proto",
                 "psmouse proto write is EBUSY; leftover proto=sentelic still sentelic-protos cache touchpad",
                 "leftover psmouse sentelic-protoing cache touchpad",
                 "this mill alps / this mill elantech / cache-admin 403",
                 "this mill alps leftover (sentelic leftover, not psmouse proto=alps)",
                 "test_sentelic.py",
                 "cat /sys/module/psmouse/parameters/proto; cat /sys/class/input/mouse0/device/name",
                 "psmouse leftover proto=sentelic leftover"),
    ),
    (
        lang("wxwidgets-lib-cache", "WX_CONFIG", "wx-config", "3.2.4", "3.2.6",
             "lib/libwx_gtk3u_core-3.2.so", "test_wx.py", "src/demo.cpp", "wx-326",
             "rm -rf /usr/lib/wx",
             "rm lib does not drop 3.2 libwx_gtk3u_core-3.2.so under unversioned WX_CONFIG",
             "18MB", "this mill gtk4-immodules / this mill qt6-plugin (wx gtk3u core, not GTK4 or Qt6)",
             "wx-config --libs", "wx-config --version"),
        leftover("cyapa-leftover", "CYAPA_CLEAR", "cyapa fuzz=cache",
                 "cyapa leftover still fuzzes cache Cypress pad as fuzz=cache",
                 "echo 1 > /sys/bus/i2c/drivers/cyapa/unbind",
                 "cyapa unbind is EBUSY; leftover fuzz=cache still fuzzes cache Cypress pad",
                 "leftover cyapa fuzzing cache Cypress pad",
                 "this mill i2c-hid / this mill synaptics / cache-admin 403",
                 "this mill i2c-hid leftover (cyapa leftover, not i2c_hid proto)",
                 "test_cyapa.py",
                 "ls /sys/bus/i2c/drivers/cyapa; cat /sys/class/input/mouse0/device/name",
                 "cyapa leftover fuzz=cache leftover"),
    ),
    (
        lang("fltk-lib-cache", "FLTK_DIR", "fltk-config", "1.3.9", "1.4.1",
             "lib/libfltk.so.1.3", "test_fltk.py", "src/demo.cxx", "fltk-141",
             "rm -rf /usr/lib/fltk",
             "rm lib does not drop 1.3 libfltk.so.1.3 under unversioned FLTK_DIR",
             "7MB", "this mill wxwidgets-lib / this mill sdl2 (FLTK libfltk.so, not wx or SDL2)",
             "fltk-config --version", "fltk-config --version"),
        leftover("rmi4-leftover", "RMI4_CLEAR", "rmi4 attn=cache",
                 "rmi4 leftover still attns cache Synaptics RMI4 as attn=cache",
                 "echo 1 > /sys/bus/i2c/drivers/rmi4_i2c/unbind",
                 "rmi4 unbind is EBUSY; leftover attn=cache still attns cache RMI4",
                 "leftover rmi4 attning cache RMI4",
                 "this mill cyapa / this mill synaptics / cache-admin 403",
                 "this mill cyapa leftover (rmi4 leftover, not cyapa fuzz)",
                 "test_rmi4.py",
                 "ls /sys/bus/i2c/drivers/rmi4_i2c; cat /sys/class/input/mouse0/device/name",
                 "rmi4 leftover attn=cache leftover"),
    ),
    (
        lang("sdl2-cache", "SDL_VIDEODRIVER", "sdl2-config", "2.30.1", "2.30.10",
             "lib/libSDL2-2.0.so.0", "test_sdl2.py", "src/demo.c", "sdl-23010",
             "rm -rf /usr/lib/x86_64-linux-gnu/libSDL2-2.0.so.0",
             "rm libSDL2 does not drop 2.30.1 libSDL2-2.0.so.0 under unversioned SDL_VIDEODRIVER",
             "6MB", "this mill glfw / this mill glew (SDL2 so, not GLFW or GLEW)",
             "sdl2-config --version", "sdl2-config --version"),
        leftover("goodix-leftover", "GOODIX_CLEAR", "goodix cfg=cache",
                 "goodix leftover still cfgs cache touchscreen as cfg=cache",
                 "echo 1 > /sys/bus/i2c/drivers/Goodix-TS/unbind",
                 "goodix unbind is EBUSY; leftover cfg=cache still cfgs cache touchscreen",
                 "leftover goodix cfg-ing cache touchscreen",
                 "this mill rmi4 / this mill i2c-hid / cache-admin 403",
                 "this mill rmi4 leftover (goodix leftover, not rmi4 attn)",
                 "test_goodix.py",
                 "ls /sys/bus/i2c/drivers/Goodix-TS; cat /sys/class/input/event0/device/name",
                 "goodix leftover cfg=cache leftover"),
    ),
    (
        lang("glfw-cache", "GLFW_LIBRARY", "glfwinfo", "3.4", "3.4.0",
             "lib/libglfw.so.3", "test_glfw.py", "src/demo.c", "glfw-340",
             "rm -rf /usr/lib/libglfw.so.3",
             "rm libglfw does not drop 3.4 libglfw.so.3 under unversioned GLFW_LIBRARY",
             "1MB", "this mill sdl2 / this mill glew (GLFW so, not SDL2 or GLEW)",
             "glfwinfo", "pkg-config --modversion glfw3"),
        leftover("edt-ft5x06-leftover", "EDT_FT5X06_CLEAR", "edt_ft5x06 thresh=cache",
                 "edt_ft5x06 leftover still threshs cache touchscreen as thresh=cache",
                 "echo 1 > /sys/bus/i2c/drivers/edt_ft5x06/unbind",
                 "edt_ft5x06 unbind is EBUSY; leftover thresh=cache still threshs cache touchscreen",
                 "leftover edt_ft5x06 threshing cache touchscreen",
                 "this mill goodix / this mill i2c-hid / cache-admin 403",
                 "this mill goodix leftover (edt-ft5x06 leftover, not goodix cfg)",
                 "test_edt.py",
                 "ls /sys/bus/i2c/drivers/edt_ft5x06; cat /sys/class/input/event0/device/name",
                 "edt leftover ft5x06 thresh=cache leftover"),
    ),
    (
        lang("glew-cache", "GLEW_HOME", "glewinfo", "2.2.0", "2.2.0-post",
             "lib/libGLEW.so.2.2", "test_glew.py", "src/demo.c", "glew-220",
             "rm -rf /usr/lib/libGLEW.so.2.2",
             "rm libGLEW does not drop 2.2 libGLEW.so.2.2 under unversioned GLEW_HOME",
             "1MB", "this mill glfw / this mill opencl-icd (GLEW so, not GLFW or OpenCL ICD)",
             "glewinfo | head", "glewinfo | head -1"),
        leftover("atmel-mxt-leftover", "ATMEL_MXT_CLEAR", "atmel_mxt t48=cache",
                 "atmel_mxt leftover still t48s cache touchscreen as t48=cache",
                 "echo 1 > /sys/bus/i2c/drivers/atmel_mxt_ts/unbind",
                 "atmel_mxt unbind is EBUSY; leftover t48=cache still t48s cache touchscreen",
                 "leftover atmel_mxt t48ing cache touchscreen",
                 "this mill edt-ft5x06 / this mill goodix / cache-admin 403",
                 "this mill edt leftover (atmel-mxt leftover, not edt_ft5x06 thresh)",
                 "test_mxt.py",
                 "ls /sys/bus/i2c/drivers/atmel_mxt_ts; cat /sys/class/input/event0/device/name",
                 "atmel leftover mxt t48=cache leftover"),
    ),
    (
        lang("opencl-icd-cache", "OCL_ICD_VENDORS", "clinfo", "2.3.2", "2.3.3",
             "etc/OpenCL/vendors/mesa.icd", "test_ocl.py", "src/demo.cl", "ocl-233",
             "rm -rf /etc/OpenCL/vendors",
             "rm vendors does not drop 2.3 mesa.icd under unversioned OCL_ICD_VENDORS",
             "1MB", "this mill glew / r vulkan-sdk (OpenCL mesa.icd, not GLEW or Vulkan SDK)",
             "clinfo | head", "clinfo --version"),
        leftover("hid-multitouch-leftover", "HID_MULTITOUCH_CLEAR", "hid_multitouch slots=cache",
                 "hid_multitouch leftover still slots cache MT as slots=cache",
                 "modprobe -r hid-multitouch",
                 "modprobe -r is EBUSY; leftover slots=cache still slots cache MT",
                 "leftover hid_multitouch slotting cache MT",
                 "this mill hid-apple / this mill i2c-hid / cache-admin 403",
                 "this mill hid-apple leftover (hid-multitouch leftover, not hid_apple fnmode)",
                 "test_hidmt.py",
                 "ls /sys/module/hid_multitouch; cat /sys/class/input/event0/device/name",
                 "hid leftover multitouch slots=cache leftover"),
    ),
    (
        lang("onetbb-cache", "TBBROOT", "tbbmalloc", "2021.11", "2022.0",
             "lib/libtbbmalloc.so.2", "test_tbb.py", "src/demo.cpp", "tbb-20220",
             "rm -rf /usr/lib/libtbbmalloc.so.2",
             "rm libtbbmalloc does not drop 2021 libtbbmalloc.so.2 under unversioned TBBROOT",
             "3MB", "this mill opencl-icd / this mill glew (oneTBB malloc so, not OpenCL ICD or GLEW)",
             "ldd /usr/lib/libtbb.so.12 | head", "pkg-config --modversion tbb"),
        leftover("gspca-ov534-leftover", "GSPCA_OV534_CLEAR", "gspca_ov534 n_devs=1",
                 "gspca_ov534 leftover still webcams cache OV534 as n_devs=1",
                 "modprobe -r gspca_ov534",
                 "modprobe -r is EBUSY; leftover n_devs=1 still webcams cache OV534",
                 "leftover gspca_ov534 webcaming cache OV534",
                 "this mill gspca / this mill uvcvideo / cache-admin 403",
                 "this mill gspca leftover (gspca-ov534 leftover, not generic gspca n_devs)",
                 "test_ov534.py",
                 "ls /sys/module/gspca_ov534; v4l2-ctl --list-devices",
                 "gspca leftover ov534 n_devs=1 leftover"),
    ),
]


def catalog_selfcheck() -> None:
    seen: set[str] = set()
    for suc, leftp in PAIRS:
        for spec in (suc, leftp):
            slug = spec["slug"]
            if slug in seen:
                raise SystemExit(f"duplicate catalog slug {slug}")
            seen.add(slug)
            ident = " ".join(
                str(spec.get(k, ""))
                for k in ("slug", "harbor", "env", "tool", "leftover", "token", "cache_id")
            ).lower()
            for needle in BANNED_NEEDLES:
                if needle in ident:
                    raise SystemExit(f"banned needle {needle!r} in {slug}")
            if slug.startswith("harbor-") or "harbor-" in slug:
                raise SystemExit(f"harbor slug forbidden: {slug}")
            if "sysctl" in slug or "sysctl" in ident:
                raise SystemExit(f"sysctl cartesian forbidden: {slug}")
    if len(PAIRS) < 12:
        raise SystemExit(f"catalog too small: {len(PAIRS)}")


def next_free_idx(start: int = 0) -> int | None:
    for i in range(start, len(PAIRS)):
        suc, leftp = PAIRS[i]
        if not slug_taken(suc["slug"]) and not slug_taken(leftp["slug"]):
            return i
    return None


def write_round(round_n: int, staging: Path, idx: int | None = None) -> None:
    _m.write_round.__wrapped__ if False else None
    if idx is None:
        raise SystemExit("catalog idx required")
    suc, leftp = PAIRS[idx]
    for spec in (suc, leftp):
        if slug_taken(spec["slug"]):
            raise SystemExit(f"slug {spec['slug']} already published; refuse clone")
    srec = success_episode(round_n, suc)
    lrec = leftover_episode(round_n, leftp)
    blob = json.dumps(srec) + json.dumps(lrec)
    for key in ("thought", "chain_of_thought", "scratch", "inner_monologue", "spike_events"):
        if key in srec or key in lrec or f'"{key}"' in blob:
            raise SystemExit(f"forbidden key {key}")
    if '"sim_or_real": "real"' in blob:
        raise SystemExit("sim_or_real real forbidden")
    nsteps_s = srec["reward"]["cost_steps"]
    nsteps_l = lrec["reward"]["cost_steps"]
    if not (16 <= nsteps_s <= 24 and 16 <= nsteps_l <= 24):
        raise SystemExit(f"step count out of range {nsteps_s}/{nsteps_l}")
    batch = staging / f"batch-r{round_n:02d}.jsonl"
    notes = staging / f"NOTES-r{round_n:02d}.md"
    batch.write_text(
        json.dumps(srec, separators=(",", ":")) + "\n" + json.dumps(lrec, separators=(",", ":")) + "\n"
    )
    notes.write_text(notes_for(round_n, suc, leftp, srec, lrec))
    if "Novel coverage:" not in notes.read_text():
        raise SystemExit("NOTES missing Novel coverage")
    print(json.dumps({"round": round_n, "idx": idx, "ids": [srec["id"], lrec["id"]], "steps": [nsteps_s, nsteps_l], "bytes": batch.stat().st_size}))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--staging", required=True)
    ap.add_argument("--idx", type=int, required=True)
    args = ap.parse_args()
    write_round(args.round, Path(args.staging), args.idx)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
