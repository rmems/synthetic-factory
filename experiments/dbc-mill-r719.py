#!/usr/bin/env python3
"""Mill docker-build-cache-factory after r647 catalog.

NEW lang × leftover driver plants. BAN r645 nerdctl, r646 containerd,
r549 scsh/scsi-debug, r337 cantera/binfmt, GNU Prolog/landlock/SWI pack/
seccomp/AppArmor/GOTOOLCHAIN clones, harbor-pin, leftover×sysctl cartesian.
17-step success + 18-step leftover. meta.generator=grok-4.6. Q=2.
Stable PAIRS indices — do not drop taken slugs from the list.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("dbc_mill_r647", HERE / "dbc-mill-r647.py")
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
hx = _m.hx
BANNED_NEEDLES = _m.BANNED_NEEDLES
slug_taken = _m.slug_taken

PAIRS: list[tuple[dict, dict]] = [
    (
        lang("puredata-pd-cache", "PD_PATH", "pd", "0.54.1", "0.55.0",
             "extra/bob~/bob~.pd_linux", "test_pd.py", "src/patch.pd", "pd-055",
             "rm -rf /usr/lib/pd",
             "rm extra does not drop 0.54 bob~.pd_linux under unversioned PD_PATH",
             "8MB", "r chuck-chugin / r supercollider-quark (Pure Data bob~, not ChucK or SuperCollider)",
             "pd src/patch.pd", "pd -version"),
        leftover("rtw89-leftover", "RTW89_CLEAR", "rtw89 disable_ps=1",
                 "rtw89 leftover still disable-PSes cache Wi-Fi as disable_ps=1",
                 "modprobe -r rtw89",
                 "modprobe -r is EBUSY; leftover disable_ps=1 still disable-PSes cache Wi-Fi",
                 "leftover rtw89 disable-PSing cache Wi-Fi",
                 "r mt7921 / r iwlwifi-mvm / cache-admin 403",
                 "r mt7921 leftover (rtw89 leftover, not mt7921 disable_aspm)",
                 "test_rtw89.py",
                 "ls /sys/module/rtw89/parameters; iw dev",
                 "rtw89 leftover disable_ps=1 leftover"),
    ),
    (
        lang("ghostscript-icc-cache", "GS_LIB", "gs", "10.02.1", "10.04.0",
             "iccprofiles/default_rgb.icc", "test_gs.py", "src/demo.ps", "gs-1004",
             "rm -rf /usr/share/ghostscript",
             "rm iccprofiles does not drop 10.02 default_rgb.icc under unversioned GS_LIB",
             "12MB", "r imagemagick / r poppler (Ghostscript ICC, not ImageMagick or Poppler)",
             "gs src/demo.ps", "gs --version"),
        leftover("brcmfmac-leftover", "BRCMFMAC_CLEAR", "brcmfmac roamoff=1",
                 "brcmfmac leftover still roam-offs cache Wi-Fi as roamoff=1",
                 "modprobe -r brcmfmac",
                 "modprobe -r is EBUSY; leftover roamoff=1 still roam-offs cache Wi-Fi",
                 "leftover brcmfmac roam-offing cache Wi-Fi",
                 "this mill rtw89 / r iwlwifi-mvm / cache-admin 403",
                 "this mill rtw89 leftover (brcmfmac leftover, not rtw89 disable_ps)",
                 "test_brcmfmac.py",
                 "ls /sys/module/brcmfmac/parameters; iw dev",
                 "brcmfmac leftover roamoff=1 leftover"),
    ),
    (
        lang("sile-font-cache", "SILE_PATH", "sile", "0.14.17", "0.15.5",
             "core/sile/classes/plain.lua", "test_sile.py", "src/demo.sil", "sile-155",
             "rm -rf /usr/share/sile",
             "rm classes does not drop 0.14 plain.lua under unversioned SILE_PATH",
             "7MB", "r typst-pkg / r context-mkiv (SILE plain.lua, not Typst or ConTeXt)",
             "sile src/demo.sil", "sile --version"),
        leftover("mwifiex-leftover", "MWIFIEX_CLEAR", "mwifiex disable_auto_ds=1",
                 "mwifiex leftover still disable-auto-DSes cache Wi-Fi as disable_auto_ds=1",
                 "modprobe -r mwifiex",
                 "modprobe -r is EBUSY; leftover disable_auto_ds=1 still disable-auto-DSes cache Wi-Fi",
                 "leftover mwifiex disable-auto-DSing cache Wi-Fi",
                 "this mill brcmfmac / this mill rtw89 / cache-admin 403",
                 "this mill brcmfmac leftover (mwifiex leftover, not brcmfmac roamoff)",
                 "test_mwifiex.py",
                 "ls /sys/module/mwifiex/parameters; iw dev",
                 "mwifiex leftover disable_auto_ds=1 leftover"),
    ),
    (
        lang("tectonic-cache", "TECTONIC_CACHE_DIR", "tectonic", "0.14.1", "0.15.0",
             "macros/latex/base/article.cls", "test_tectonic.py", "src/demo.tex", "tec-015",
             "rm -rf /root/.cache/Tectonic",
             "rm macros does not drop 0.14 article.cls under unversioned TECTONIC_CACHE_DIR",
             "44MB", "this mill sile-font / r context-mkiv (Tectonic article.cls, not SILE or ConTeXt)",
             "tectonic src/demo.tex", "tectonic --version"),
        leftover("mt76-leftover", "MT76_CLEAR", "mt76 beacon_int=100",
                 "mt76 leftover still beacon-ints cache Wi-Fi as beacon_int=100",
                 "modprobe -r mt76",
                 "modprobe -r is EBUSY; leftover beacon_int=100 still beacon-ints cache Wi-Fi",
                 "leftover mt76 beacon-inting cache Wi-Fi",
                 "r mt7921 / this mill mwifiex / cache-admin 403",
                 "r mt7921 leftover (mt76 leftover, not mt7921 disable_aspm)",
                 "test_mt76.py",
                 "ls /sys/module/mt76/parameters; iw dev",
                 "mt76 leftover beacon_int=100 leftover"),
    ),
    (
        lang("lualatex-fmt-cache", "TEXMFVAR", "lualatex", "2023.20231201", "2024.20241101",
             "web2c/luatex/lualatex.fmt", "test_lualatex.py", "src/demo.tex", "lua-2024",
             "rm -rf /var/lib/texmf",
             "rm web2c does not drop 2023 lualatex.fmt under unversioned TEXMFVAR",
             "18MB", "this mill tectonic / this mill xelatex-fmt (LuaLaTeX fmt, not Tectonic or XeLaTeX)",
             "lualatex src/demo.tex", "lualatex --version"),
        leftover("ath10k-leftover", "ATH10K_CLEAR", "ath10k_core skip_otp=1",
                 "ath10k leftover still skip-OTPs cache Wi-Fi as skip_otp=1",
                 "modprobe -r ath10k_core",
                 "modprobe -r is EBUSY; leftover skip_otp=1 still skip-OTPs cache Wi-Fi",
                 "leftover ath10k skip-OTPing cache Wi-Fi",
                 "r ath11k / r ath12k / cache-admin 403",
                 "r ath11k leftover (ath10k leftover, not ath11k frame_mode)",
                 "test_ath10k.py",
                 "ls /sys/module/ath10k_core/parameters; iw dev",
                 "ath10k leftover skip_otp=1 leftover"),
    ),
    (
        lang("xelatex-fmt-cache", "TEXMFVAR", "xelatex", "2023.20231201", "2024.20241101",
             "web2c/xetex/xelatex.fmt", "test_xelatex.py", "src/demo.tex", "xe-2024",
             "rm -rf /var/lib/texmf/web2c/xetex",
             "rm xetex does not drop 2023 xelatex.fmt under unversioned TEXMFVAR",
             "16MB", "this mill lualatex-fmt / this mill tectonic (XeLaTeX fmt, not LuaLaTeX or Tectonic)",
             "xelatex src/demo.tex", "xelatex --version"),
        leftover("ath9k-leftover", "ATH9K_CLEAR", "ath9k nohwcrypt=1",
                 "ath9k leftover still no-hwcrypts cache Wi-Fi as nohwcrypt=1",
                 "modprobe -r ath9k",
                 "modprobe -r is EBUSY; leftover nohwcrypt=1 still no-hwcrypts cache Wi-Fi",
                 "leftover ath9k no-hwcrypting cache Wi-Fi",
                 "this mill ath10k / r ath11k / cache-admin 403",
                 "this mill ath10k leftover (ath9k leftover, not ath10k skip_otp)",
                 "test_ath9k.py",
                 "ls /sys/module/ath9k/parameters; iw dev",
                 "ath9k leftover nohwcrypt=1 leftover"),
    ),
    (
        lang("grace-plot-cache", "GRACE_HOME", "xmgrace", "5.1.25", "5.1.25-post",
             "templates/Default.agr", "test_grace.py", "src/demo.agr", "grace-5125",
             "rm -rf /usr/share/grace",
             "rm templates does not drop 5.1 Default.agr under unversioned GRACE_HOME",
             "5MB", "r gnuplot-share / this mill veusz (Grace Default.agr, not gnuplot or Veusz)",
             "xmgrace src/demo.agr", "xmgrace -version"),
        leftover("wil6210-leftover", "WIL6210_CLEAR", "wil6210 no_fw_recovery=1",
                 "wil6210 leftover still no-fw-recoveries cache 60GHz as no_fw_recovery=1",
                 "modprobe -r wil6210",
                 "modprobe -r is EBUSY; leftover no_fw_recovery=1 still no-fw-recoveries cache 60GHz",
                 "leftover wil6210 no-fw-recovering cache 60GHz",
                 "this mill ath9k / this mill rtw89 / cache-admin 403",
                 "this mill ath9k leftover (wil6210 leftover, not ath9k nohwcrypt)",
                 "test_wil6210.py",
                 "ls /sys/module/wil6210/parameters; iw dev",
                 "wil6210 leftover no_fw_recovery=1 leftover"),
    ),
    (
        lang("veusz-cache", "VEUSZ_RESOURCE_DIR", "veusz", "3.6.2", "3.6.4",
             "resources/icons/veusz.svg", "test_veusz.py", "src/demo.vsz", "veusz-364",
             "rm -rf /usr/share/veusz",
             "rm resources does not drop 3.6.2 veusz.svg under unversioned VEUSZ_RESOURCE_DIR",
             "9MB", "this mill grace-plot / r gnuplot-share (Veusz icons, not Grace or gnuplot)",
             "veusz src/demo.vsz", "veusz --version"),
        leftover("ath5k-leftover", "ATH5K_CLEAR", "ath5k nohwcrypt=1",
                 "ath5k leftover still no-hwcrypts cache Wi-Fi as nohwcrypt=1",
                 "modprobe -r ath5k",
                 "modprobe -r is EBUSY; leftover nohwcrypt=1 still no-hwcrypts cache Wi-Fi",
                 "leftover ath5k no-hwcrypting cache Wi-Fi",
                 "this mill ath9k / this mill ath10k / cache-admin 403",
                 "this mill ath9k leftover (ath5k leftover, not ath9k nohwcrypt on later chip)",
                 "test_ath5k.py",
                 "ls /sys/module/ath5k/parameters; iw dev",
                 "ath5k leftover nohwcrypt=1 leftover"),
    ),
    (
        lang("pgfplots-cache", "TEXMFHOME", "lualatex", "1.18", "1.18.1",
             "tex/latex/pgfplots/pgfplots.sty", "test_pgfplots.py", "src/demo.tex", "pgf-1181",
             "rm -rf /usr/share/texlive/texmf-dist/tex/latex/pgfplots",
             "rm pgfplots does not drop 1.18 pgfplots.sty under unversioned TEXMFHOME",
             "4MB", "this mill lualatex-fmt / this mill grace-plot (pgfplots.sty, not LuaLaTeX fmt or Grace)",
             "lualatex src/demo.tex", "kpsewhich pgfplots.sty"),
        leftover("b43-leftover", "B43_CLEAR", "b43 pio=1",
                 "b43 leftover still PIOs cache Wi-Fi as pio=1",
                 "modprobe -r b43",
                 "modprobe -r is EBUSY; leftover pio=1 still PIOs cache Wi-Fi",
                 "leftover b43 PIOing cache Wi-Fi",
                 "this mill ath5k / this mill brcmfmac / cache-admin 403",
                 "this mill ath5k leftover (b43 leftover, not ath5k nohwcrypt)",
                 "test_b43.py",
                 "ls /sys/module/b43/parameters; iw dev",
                 "b43 leftover pio=1 leftover"),
    ),
    (
        lang("whizard-cache", "WHIZARD_DIR", "whizard", "3.1.2", "3.1.4",
             "share/whizard/models/SM.mdl", "test_whizard.py", "src/demo.sin", "whiz-314",
             "rm -rf /usr/share/whizard",
             "rm models does not drop 3.1.2 SM.mdl under unversioned WHIZARD_DIR",
             "26MB", "r madgraph-models / r herwig-share (WHIZARD SM.mdl, not MadGraph or Herwig)",
             "whizard src/demo.sin", "whizard --version"),
        leftover("brcmsmac-leftover", "BRCMSMAC_CLEAR", "brcmsmac macaddr=cache",
                 "brcmsmac leftover still macaddrs cache Wi-Fi as macaddr=cache",
                 "modprobe -r brcmsmac",
                 "modprobe -r is EBUSY; leftover macaddr=cache still macaddrs cache Wi-Fi",
                 "leftover brcmsmac macaddr-ing cache Wi-Fi",
                 "this mill brcmfmac / this mill b43 / cache-admin 403",
                 "this mill brcmfmac leftover (brcmsmac leftover, not brcmfmac roamoff)",
                 "test_brcmsmac.py",
                 "ls /sys/module/brcmsmac/parameters; iw dev",
                 "brcmsmac leftover macaddr=cache leftover"),
    ),
    (
        lang("metafont-tfm-cache", "MFBASES", "mf", "2.71828182", "2.7182818",
             "fonts/tfm/public/cm/cmr10.tfm", "test_mf.py", "src/demo.mf", "mf-cmr10",
             "rm -rf /usr/share/texlive/texmf-dist/fonts/tfm",
             "rm tfm does not drop cmr10.tfm under unversioned MFBASES",
             "3MB", "this mill metapost-mp / this mill lualatex-fmt (Metafont cmr10.tfm, not MetaPost or LuaLaTeX)",
             "mf src/demo.mf", "mf --version"),
        leftover("cw1200-leftover", "CW1200_CLEAR", "cw1200 nohwcrypt=1",
                 "cw1200 leftover still no-hwcrypts cache Wi-Fi as nohwcrypt=1",
                 "modprobe -r cw1200",
                 "modprobe -r is EBUSY; leftover nohwcrypt=1 still no-hwcrypts cache Wi-Fi",
                 "leftover cw1200 no-hwcrypting cache Wi-Fi",
                 "this mill ath9k / this mill wil6210 / cache-admin 403",
                 "this mill ath9k leftover (cw1200 leftover, not ath9k nohwcrypt on Atheros)",
                 "test_cw1200.py",
                 "ls /sys/module/cw1200/parameters; iw dev",
                 "cw1200 leftover nohwcrypt=1 leftover"),
    ),
    (
        lang("metapost-mp-cache", "MPMEMS", "mpost", "2.02", "2.10",
             "metapost/base/plain.mp", "test_mpost.py", "src/demo.mp", "mp-210",
             "rm -rf /usr/share/texlive/texmf-dist/metapost",
             "rm base does not drop 2.02 plain.mp under unversioned MPMEMS",
             "2MB", "this mill metafont-tfm / this mill asymptote-asy (MetaPost plain.mp, not Metafont or Asymptote)",
             "mpost src/demo.mp", "mpost --version"),
        leftover("rsi-91x-leftover", "RSI91X_CLEAR", "rsi ps_enable=0",
                 "rsi leftover still ps-enables cache Wi-Fi as ps_enable=0",
                 "modprobe -r rsi_91x",
                 "modprobe -r is EBUSY; leftover ps_enable=0 still ps-enables cache Wi-Fi",
                 "leftover rsi ps-enabling cache Wi-Fi",
                 "this mill cw1200 / this mill rtw89 / cache-admin 403",
                 "this mill cw1200 leftover (rsi leftover, not cw1200 nohwcrypt)",
                 "test_rsi.py",
                 "ls /sys/module/rsi_91x/parameters; iw dev",
                 "rsi leftover ps_enable=0 leftover"),
    ),
    (
        lang("asymptote-asy-cache", "ASYMPTOTE_DIR", "asy", "2.86", "2.89",
             "base/plain.asy", "test_asy.py", "src/demo.asy", "asy-289",
             "rm -rf /usr/share/asymptote",
             "rm base does not drop 2.86 plain.asy under unversioned ASYMPTOTE_DIR",
             "11MB", "this mill metapost-mp / this mill pgfplots (Asymptote plain.asy, not MetaPost or pgfplots)",
             "asy src/demo.asy", "asy --version"),
        leftover("qtnfmac-leftover", "QTNFMAC_CLEAR", "qtnfmac hw_wdog=1",
                 "qtnfmac leftover still hw-wdogs cache Wi-Fi as hw_wdog=1",
                 "modprobe -r qtnfmac",
                 "modprobe -r is EBUSY; leftover hw_wdog=1 still hw-wdogs cache Wi-Fi",
                 "leftover qtnfmac hw-wdoging cache Wi-Fi",
                 "this mill rsi-91x / this mill mwifiex / cache-admin 403",
                 "this mill rsi leftover (qtnfmac leftover, not rsi ps_enable)",
                 "test_qtnfmac.py",
                 "ls /sys/module/qtnfmac/parameters; iw dev",
                 "qtnfmac leftover hw_wdog=1 leftover"),
    ),
    (
        lang("dvisvgm-cache", "DVISVGM_FONTCACHE", "dvisvgm", "3.1.2", "3.2.2",
             "cache/cmr10.svgz", "test_dvisvgm.py", "src/demo.dvi", "dvi-322",
             "rm -rf /root/.dvisvgm",
             "rm cache does not drop 3.1 cmr10.svgz under unversioned DVISVGM_FONTCACHE",
             "6MB", "this mill metafont-tfm / this mill ghostscript-icc (dvisvgm cmr10.svgz, not Metafont or Ghostscript)",
             "dvisvgm src/demo.dvi", "dvisvgm --version"),
        leftover("wfx-leftover", "WFX_CLEAR", "wfx_core slk_wait=1",
                 "wfx leftover still slk-waits cache Wi-Fi as slk_wait=1",
                 "modprobe -r wfx",
                 "modprobe -r is EBUSY; leftover slk_wait=1 still slk-waits cache Wi-Fi",
                 "leftover wfx slk-waiting cache Wi-Fi",
                 "this mill qtnfmac / this mill cw1200 / cache-admin 403",
                 "this mill qtnfmac leftover (wfx leftover, not qtnfmac hw_wdog)",
                 "test_wfx.py",
                 "ls /sys/module/wfx/parameters; iw dev",
                 "wfx leftover slk_wait=1 leftover"),
    ),
    (
        lang("ardour-session-cache", "ARDOUR_DATA_PATH", "ardour", "8.4.0", "8.10.0",
             "share/ardour8/templates/default.ardourtemplate", "test_ardour.py", "src/session.ardour", "ard-810",
             "rm -rf /usr/share/ardour8",
             "rm templates does not drop 8.4 default.ardourtemplate under unversioned ARDOUR_DATA_PATH",
             "38MB", "r lmms / r hydrogen (Ardour template, not LMMS or Hydrogen)",
             "ardour8 src/session.ardour", "ardour8 --version"),
        leftover("iwlegacy-leftover", "IWLEGACY_CLEAR", "iwl4965 swcrypto=1",
                 "iwl4965 leftover still swcryptos cache Wi-Fi as swcrypto=1",
                 "modprobe -r iwl4965",
                 "modprobe -r is EBUSY; leftover swcrypto=1 still swcryptos cache Wi-Fi",
                 "leftover iwl4965 swcryptoing cache Wi-Fi",
                 "r iwlwifi-mvm / this mill ath9k / cache-admin 403",
                 "r iwlwifi leftover (iwlegacy leftover, not iwlwifi power_scheme)",
                 "test_iwl4965.py",
                 "ls /sys/module/iwl4965/parameters; iw dev",
                 "iwl4965 leftover swcrypto=1 leftover"),
    ),
    (
        lang("lmms-presets-cache", "LMMS_DATA_DIR", "lmms", "1.2.2", "1.3.0",
             "share/lmms/presets/tripsin.xpf", "test_lmms.py", "src/demo.mmp", "lmms-130",
             "rm -rf /usr/share/lmms",
             "rm presets does not drop 1.2 tripsin.xpf under unversioned LMMS_DATA_DIR",
             "14MB", "this mill ardour-session / r hydrogen (LMMS tripsin.xpf, not Ardour or Hydrogen)",
             "lmms src/demo.mmp", "lmms --version"),
        leftover("orinoco-leftover", "ORINOCO_CLEAR", "orinoco ignore_disconnect=1",
                 "orinoco leftover still ignore-disconnects cache Wi-Fi as ignore_disconnect=1",
                 "modprobe -r orinoco",
                 "modprobe -r is EBUSY; leftover ignore_disconnect=1 still ignore-disconnects cache Wi-Fi",
                 "leftover orinoco ignore-disconnecting cache Wi-Fi",
                 "this mill iwlegacy / this mill ath5k / cache-admin 403",
                 "this mill iwlegacy leftover (orinoco leftover, not iwl4965 swcrypto)",
                 "test_orinoco.py",
                 "ls /sys/module/orinoco/parameters; iw dev",
                 "orinoco leftover ignore_disconnect=1 leftover"),
    ),
    (
        lang("hydrogen-drum-cache", "HYDROGEN_DATA_PATH", "hydrogen", "1.2.2", "1.2.4",
             "share/hydrogen/data/drumkits/TR808EmulationKit/drumkit.xml", "test_h2.py", "src/demo.h2song", "h2-124",
             "rm -rf /usr/share/hydrogen",
             "rm drumkits does not drop 1.2 TR808 drumkit.xml under unversioned HYDROGEN_DATA_PATH",
             "21MB", "this mill lmms-presets / this mill ardour-session (Hydrogen TR808, not LMMS or Ardour)",
             "hydrogen src/demo.h2song", "hydrogen --version"),
        leftover("zd1211-leftover", "ZD1211_CLEAR", "zd1211rw tx_gain=1",
                 "zd1211rw leftover still tx-gains cache Wi-Fi as tx_gain=1",
                 "modprobe -r zd1211rw",
                 "modprobe -r is EBUSY; leftover tx_gain=1 still tx-gains cache Wi-Fi",
                 "leftover zd1211rw tx-gaining cache Wi-Fi",
                 "this mill orinoco / this mill rtl8xxxu / cache-admin 403",
                 "this mill orinoco leftover (zd1211 leftover, not orinoco ignore_disconnect)",
                 "test_zd1211.py",
                 "ls /sys/module/zd1211rw/parameters; iw dev",
                 "zd1211 leftover tx_gain=1 leftover"),
    ),
    (
        lang("jacktrip-cache", "JACKTRIP_HOME", "jacktrip", "1.7.1", "2.3.1",
             "share/jacktrip/presets/default.json", "test_jacktrip.py", "src/session.json", "jt-231",
             "rm -rf /usr/share/jacktrip",
             "rm presets does not drop 1.7 default.json under unversioned JACKTRIP_HOME",
             "4MB", "this mill ardour-session / r jackd (JackTrip presets, not Ardour or jackd)",
             "jacktrip -v", "jacktrip --version"),
        leftover("rtl8xxxu-leftover", "RTL8XXXU_CLEAR", "rtl8xxxu dma=1",
                 "rtl8xxxu leftover still DMAs cache Wi-Fi as dma=1",
                 "modprobe -r rtl8xxxu",
                 "modprobe -r is EBUSY; leftover dma=1 still DMAs cache Wi-Fi",
                 "leftover rtl8xxxu DMAing cache Wi-Fi",
                 "this mill rtw89 / this mill zd1211 / cache-admin 403",
                 "this mill rtw89 leftover (rtl8xxxu leftover, not rtw89 disable_ps)",
                 "test_rtl8xxxu.py",
                 "ls /sys/module/rtl8xxxu/parameters; iw dev",
                 "rtl8xxxu leftover dma=1 leftover"),
    ),
    (
        lang("bibtex-bst-cache", "BSTINPUTS", "bibtex", "0.99d", "0.99e",
             "bibtex/bst/base/plain.bst", "test_bibtex.py", "src/demo.aux", "bst-99e",
             "rm -rf /usr/share/texlive/texmf-dist/bibtex/bst",
             "rm bst does not drop 0.99d plain.bst under unversioned BSTINPUTS",
             "1MB", "this mill biber / this mill biblatex-bbl (BibTeX plain.bst, not Biber or biblatex)",
             "bibtex src/demo", "bibtex --version"),
        leftover("r8188eu-leftover", "R8188EU_CLEAR", "r8188eu rtw_power_mgnt=0",
                 "r8188eu leftover still power-mgnts cache Wi-Fi as rtw_power_mgnt=0",
                 "modprobe -r r8188eu",
                 "modprobe -r is EBUSY; leftover rtw_power_mgnt=0 still power-mgnts cache Wi-Fi",
                 "leftover r8188eu power-mgnting cache Wi-Fi",
                 "this mill rtl8xxxu / this mill rtw89 / cache-admin 403",
                 "this mill rtl8xxxu leftover (r8188eu leftover, not rtl8xxxu dma)",
                 "test_r8188eu.py",
                 "ls /sys/module/r8188eu/parameters; iw dev",
                 "r8188eu leftover rtw_power_mgnt=0 leftover"),
    ),
    (
        lang("biber-cache", "BIBER_CACHE", "biber", "2.19", "2.20",
             "lib/Biber/LaTeX/recode_data.xml", "test_biber.py", "src/demo.bcf", "biber-220",
             "rm -rf /usr/share/perl5/Biber",
             "rm recode does not drop 2.19 recode_data.xml under unversioned BIBER_CACHE",
             "5MB", "this mill bibtex-bst / this mill biblatex-bbl (Biber recode_data.xml, not BibTeX bst or biblatex)",
             "biber src/demo", "biber --version"),
        leftover("fotg210-leftover", "FOTG210_CLEAR", "fotg210 gadget=cache",
                 "fotg210 leftover still gadgets cache USB as gadget=cache",
                 "echo 1 > /sys/bus/platform/drivers/fotg210/unbind",
                 "fotg210 unbind is EBUSY; leftover gadget=cache still gadgets cache USB",
                 "leftover fotg210 gadgeting cache USB",
                 "r dwc3-gadget / r musb-gadget / cache-admin 403",
                 "r dwc3 leftover (fotg210 leftover, not dwc3 gadget)",
                 "test_fotg210.py",
                 "ls /sys/bus/platform/drivers/fotg210; ls /sys/class/udc",
                 "fotg210 leftover gadget=cache leftover"),
    ),
    (
        lang("makeindex-idx-cache", "INDEXSTYLE", "makeindex", "2.15", "2.17",
             "makeindex/base/gind.ist", "test_makeindex.py", "src/demo.idx", "idx-217",
             "rm -rf /usr/share/texlive/texmf-dist/makeindex",
             "rm base does not drop 2.15 gind.ist under unversioned INDEXSTYLE",
             "1MB", "this mill xindy / this mill bibtex-bst (MakeIndex gind.ist, not Xindy or BibTeX)",
             "makeindex src/demo.idx", "makeindex --version"),
        leftover("isp1760-leftover", "ISP1760_CLEAR", "isp1760 gadget=cache",
                 "isp1760 leftover still gadgets cache USB as gadget=cache",
                 "echo 1 > /sys/bus/platform/drivers/isp1760/unbind",
                 "isp1760 unbind is EBUSY; leftover gadget=cache still gadgets cache USB",
                 "leftover isp1760 gadgeting cache USB",
                 "this mill fotg210 / r dwc3-gadget / cache-admin 403",
                 "this mill fotg210 leftover (isp1760 leftover, not fotg210 gadget)",
                 "test_isp1760.py",
                 "ls /sys/bus/platform/drivers/isp1760; ls /sys/class/udc",
                 "isp1760 leftover gadget=cache leftover"),
    ),
    (
        lang("xindy-cache", "XINDY_DATA", "xindy", "2.5.1", "2.5.1.1",
             "xindy/modules/base/latex.xdy", "test_xindy.py", "src/demo.idx", "xdy-2511",
             "rm -rf /usr/share/xindy",
             "rm modules does not drop 2.5 latex.xdy under unversioned XINDY_DATA",
             "2MB", "this mill makeindex-idx / this mill biber (Xindy latex.xdy, not MakeIndex or Biber)",
             "xindy src/demo.idx", "xindy --version"),
        leftover("max3421-leftover", "MAX3421_CLEAR", "max3421 gadget=cache",
                 "max3421 leftover still gadgets cache USB SPI as gadget=cache",
                 "echo 1 > /sys/bus/spi/drivers/max3421-hcd/unbind",
                 "max3421 unbind is EBUSY; leftover gadget=cache still gadgets cache USB SPI",
                 "leftover max3421 gadgeting cache USB SPI",
                 "this mill isp1760 / this mill fotg210 / cache-admin 403",
                 "this mill isp1760 leftover (max3421 leftover, not isp1760 gadget)",
                 "test_max3421.py",
                 "ls /sys/bus/spi/drivers/max3421-hcd; lsusb | head",
                 "max3421 leftover gadget=cache leftover"),
    ),
    (
        lang("minted-pyg-cache", "MINTED_CACHE", "pygmentize", "2.17.2", "2.18.0",
             ".minted-cache/default.pygtex", "test_minted.py", "src/demo.tex", "mint-218",
             "rm -rf /src/.minted-cache",
             "rm .minted-cache does not drop 2.17 default.pygtex under unversioned MINTED_CACHE",
             "3MB", "this mill listings-sty / this mill lualatex-fmt (minted pygtex, not listings or LuaLaTeX fmt)",
             "lualatex -shell-escape src/demo.tex", "pygmentize -V"),
        leftover("sl811-leftover", "SL811_CLEAR", "sl811-hcd gadget=cache",
                 "sl811 leftover still gadgets cache USB as gadget=cache",
                 "echo 1 > /sys/bus/platform/drivers/sl811-hcd/unbind",
                 "sl811 unbind is EBUSY; leftover gadget=cache still gadgets cache USB",
                 "leftover sl811 gadgeting cache USB",
                 "this mill max3421 / this mill isp1760 / cache-admin 403",
                 "this mill max3421 leftover (sl811 leftover, not max3421 SPI gadget)",
                 "test_sl811.py",
                 "ls /sys/bus/platform/drivers/sl811-hcd; lsusb | head",
                 "sl811 leftover gadget=cache leftover"),
    ),
    (
        lang("listings-sty-cache", "TEXINPUTS", "kpsewhich", "1.9", "1.10",
             "tex/latex/listings/listings.sty", "test_listings.py", "src/demo.tex", "lst-110",
             "rm -rf /usr/share/texlive/texmf-dist/tex/latex/listings",
             "rm listings does not drop 1.9 listings.sty under unversioned TEXINPUTS",
             "1MB", "this mill minted-pyg / this mill tcolorbox (listings.sty, not minted or tcolorbox)",
             "kpsewhich listings.sty", "kpsewhich listings.sty"),
        leftover("r8a66597-leftover", "R8A66597_CLEAR", "r8a66597 gadget=cache",
                 "r8a66597 leftover still gadgets cache USB as gadget=cache",
                 "echo 1 > /sys/bus/platform/drivers/r8a66597_hcd/unbind",
                 "r8a66597 unbind is EBUSY; leftover gadget=cache still gadgets cache USB",
                 "leftover r8a66597 gadgeting cache USB",
                 "this mill sl811 / this mill fotg210 / cache-admin 403",
                 "this mill sl811 leftover (r8a66597 leftover, not sl811 gadget)",
                 "test_r8a66597.py",
                 "ls /sys/bus/platform/drivers/r8a66597_hcd; ls /sys/class/udc",
                 "r8a66597 leftover gadget=cache leftover"),
    ),
    (
        lang("tcolorbox-cache", "TEXINPUTS", "kpsewhich", "6.2.0", "6.4.1",
             "tex/latex/tcolorbox/tcolorbox.sty", "test_tcb.py", "src/demo.tex", "tcb-641",
             "rm -rf /usr/share/texlive/texmf-dist/tex/latex/tcolorbox",
             "rm tcolorbox does not drop 6.2 tcolorbox.sty under unversioned TEXINPUTS",
             "2MB", "this mill listings-sty / this mill beamer-theme (tcolorbox.sty, not listings or Beamer)",
             "kpsewhich tcolorbox.sty", "kpsewhich tcolorbox.sty"),
        leftover("renesas-usbhs-leftover", "RENESAS_USBHS_CLEAR", "renesas_usbhs gadget=cache",
                 "renesas_usbhs leftover still gadgets cache USB as gadget=cache",
                 "echo 1 > /sys/bus/platform/drivers/renesas_usbhs/unbind",
                 "renesas_usbhs unbind is EBUSY; leftover gadget=cache still gadgets cache USB",
                 "leftover renesas_usbhs gadgeting cache USB",
                 "this mill r8a66597 / r musb-gadget / cache-admin 403",
                 "this mill r8a66597 leftover (renesas_usbhs leftover, not r8a66597 gadget)",
                 "test_renesasusbhs.py",
                 "ls /sys/bus/platform/drivers/renesas_usbhs; ls /sys/class/udc",
                 "renesas leftover usbhs gadget=cache leftover"),
    ),
    (
        lang("beamer-theme-cache", "TEXINPUTS", "kpsewhich", "3.71", "3.72",
             "tex/latex/beamer/themes/theme/beamerthemeMadrid.sty", "test_beamer.py", "src/demo.tex", "bmr-372",
             "rm -rf /usr/share/texlive/texmf-dist/tex/latex/beamer",
             "rm themes does not drop 3.71 beamerthemeMadrid.sty under unversioned TEXINPUTS",
             "8MB", "this mill tcolorbox / this mill koma-script (Beamer Madrid, not tcolorbox or KOMA)",
             "kpsewhich beamerthemeMadrid.sty", "kpsewhich beamer.cls"),
        leftover("omap-usb-leftover", "OMAP_USB_CLEAR", "omap2430 gadget=cache",
                 "omap2430 leftover still gadgets cache USB as gadget=cache",
                 "echo 1 > /sys/bus/platform/drivers/omap2430/unbind",
                 "omap2430 unbind is EBUSY; leftover gadget=cache still gadgets cache USB",
                 "leftover omap2430 gadgeting cache USB",
                 "this mill renesas-usbhs / r musb-gadget / cache-admin 403",
                 "this mill renesas leftover (omap-usb leftover, not renesas_usbhs gadget)",
                 "test_omapusb.py",
                 "ls /sys/bus/platform/drivers/omap2430; ls /sys/class/udc",
                 "omap leftover usb gadget=cache leftover"),
    ),
    (
        lang("koma-script-cache", "TEXINPUTS", "kpsewhich", "3.41", "3.42",
             "tex/latex/koma-script/scrartcl.cls", "test_koma.py", "src/demo.tex", "koma-342",
             "rm -rf /usr/share/texlive/texmf-dist/tex/latex/koma-script",
             "rm koma-script does not drop 3.41 scrartcl.cls under unversioned TEXINPUTS",
             "6MB", "this mill memoir-cls / this mill beamer-theme (KOMA scrartcl, not memoir or Beamer)",
             "kpsewhich scrartcl.cls", "kpsewhich scrartcl.cls"),
        leftover("am335x-musb-leftover", "AM335X_MUSB_CLEAR", "am335x-musb gadget=cache",
                 "am335x-musb leftover still gadgets cache USB as gadget=cache",
                 "echo 1 > /sys/bus/platform/drivers/am335x-musb/unbind",
                 "am335x-musb unbind is EBUSY; leftover gadget=cache still gadgets cache USB",
                 "leftover am335x-musb gadgeting cache USB",
                 "r musb-gadget / this mill omap-usb / cache-admin 403",
                 "r musb leftover (am335x-musb leftover, not generic musb gadget)",
                 "test_am335x.py",
                 "ls /sys/bus/platform/drivers/am335x-musb; ls /sys/class/udc",
                 "am335x leftover musb gadget=cache leftover"),
    ),
    (
        lang("memoir-cls-cache", "TEXINPUTS", "kpsewhich", "3.7.19", "3.8",
             "tex/latex/memoir/memoir.cls", "test_memoir.py", "src/demo.tex", "mem-38",
             "rm -rf /usr/share/texlive/texmf-dist/tex/latex/memoir",
             "rm memoir does not drop 3.7 memoir.cls under unversioned TEXINPUTS",
             "3MB", "this mill koma-script / this mill tufte-handout (memoir.cls, not KOMA or Tufte)",
             "kpsewhich memoir.cls", "kpsewhich memoir.cls"),
        leftover("ps8830-leftover", "PS8830_CLEAR", "ps8830 eq=cache",
                 "ps8830 leftover still EQs cache Type-C retimer as eq=cache",
                 "echo 1 > /sys/bus/i2c/drivers/ps8830/unbind",
                 "ps8830 unbind is EBUSY; leftover eq=cache still EQs cache Type-C retimer",
                 "leftover ps8830 EQing cache Type-C retimer",
                 "r typec-tcpci / r ucsi-acpi / cache-admin 403",
                 "r tcpci leftover (ps8830 leftover, not tcpci port)",
                 "test_ps8830.py",
                 "ls /sys/bus/i2c/drivers/ps8830; cat /sys/class/typec/port0/data_role",
                 "ps8830 leftover eq=cache leftover"),
    ),
    (
        lang("tufte-handout-cache", "TEXINPUTS", "kpsewhich", "3.5.2", "3.5.3",
             "tex/latex/tufte-latex/tufte-handout.cls", "test_tufte.py", "src/demo.tex", "tuf-353",
             "rm -rf /usr/share/texlive/texmf-dist/tex/latex/tufte-latex",
             "rm tufte does not drop 3.5.2 tufte-handout.cls under unversioned TEXINPUTS",
             "2MB", "this mill memoir-cls / this mill koma-script (Tufte handout, not memoir or KOMA)",
             "kpsewhich tufte-handout.cls", "kpsewhich tufte-handout.cls"),
        leftover("rp1-leftover", "RP1_CLEAR", "rp1 pio=cache",
                 "rp1 leftover still PIOs cache RP1 southbridge as pio=cache",
                 "echo 1 > /sys/bus/platform/drivers/rp1/unbind",
                 "rp1 unbind is EBUSY; leftover pio=cache still PIOs cache RP1",
                 "leftover rp1 PIOing cache RP1",
                 "r vc4-hdmi / r v3d-drm / cache-admin 403",
                 "r vc4 leftover (rp1 leftover, not vc4 hdmi)",
                 "test_rp1.py",
                 "ls /sys/bus/platform/drivers/rp1; ls /proc/device-tree | head",
                 "rp1 leftover pio=cache leftover"),
    ),
    (
        lang("hyperref-enc-cache", "TEXINPUTS", "kpsewhich", "7.01h", "7.01i",
             "tex/latex/hyperref/hpdftex.def", "test_href.py", "src/demo.tex", "href-701i",
             "rm -rf /usr/share/texlive/texmf-dist/tex/latex/hyperref",
             "rm hyperref does not drop 7.01h hpdftex.def under unversioned TEXINPUTS",
             "2MB", "this mill csquotes / this mill biblatex-bbl (hyperref hpdftex.def, not csquotes or biblatex)",
             "kpsewhich hpdftex.def", "kpsewhich hyperref.sty"),
        leftover("pisp-leftover", "PISP_CLEAR", "pisp-be tile=cache",
                 "pisp leftover still tiles cache PiSP as tile=cache",
                 "echo 1 > /sys/bus/platform/drivers/pispbe/unbind",
                 "pispbe unbind is EBUSY; leftover tile=cache still tiles cache PiSP",
                 "leftover pisp tiling cache PiSP",
                 "this mill rp1 / r v3d-drm / cache-admin 403",
                 "this mill rp1 leftover (pisp leftover, not rp1 pio)",
                 "test_pisp.py",
                 "ls /sys/bus/platform/drivers/pispbe; ls /dev/video*",
                 "pisp leftover tile=cache leftover"),
    ),
    (
        lang("csquotes-cache", "TEXINPUTS", "kpsewhich", "5.2n", "5.2o",
             "tex/latex/csquotes/csquotes.sty", "test_csq.py", "src/demo.tex", "csq-52o",
             "rm -rf /usr/share/texlive/texmf-dist/tex/latex/csquotes",
             "rm csquotes does not drop 5.2n csquotes.sty under unversioned TEXINPUTS",
             "1MB", "this mill hyperref-enc / this mill biblatex-bbl (csquotes.sty, not hyperref or biblatex)",
             "kpsewhich csquotes.sty", "kpsewhich csquotes.sty"),
        leftover("cma3000-leftover", "CMA3000_CLEAR", "cma3000 fuzz=cache",
                 "cma3000 leftover still fuzzes cache accelerometer as fuzz=cache",
                 "echo 1 > /sys/bus/i2c/drivers/cma3000_d0x/unbind",
                 "cma3000 unbind is EBUSY; leftover fuzz=cache still fuzzes cache accelerometer",
                 "leftover cma3000 fuzzing cache accelerometer",
                 "r uinput / r hidraw / cache-admin 403",
                 "r uinput leftover (cma3000 leftover, not uinput cache-input)",
                 "test_cma3000.py",
                 "ls /sys/bus/i2c/drivers/cma3000_d0x; cat /sys/class/input/input0/name",
                 "cma3000 leftover fuzz=cache leftover"),
    ),
    (
        lang("biblatex-bbl-cache", "TEXMFHOME", "kpsewhich", "3.19", "3.20",
             "tex/latex/biblatex/biblatex.sty", "test_biblatex.py", "src/demo.tex", "bbx-320",
             "rm -rf /usr/share/texlive/texmf-dist/tex/latex/biblatex",
             "rm biblatex does not drop 3.19 biblatex.sty under unversioned TEXMFHOME",
             "7MB", "this mill biber / this mill bibtex-bst (biblatex.sty, not Biber recode or BibTeX bst)",
             "kpsewhich biblatex.sty", "kpsewhich biblatex.sty"),
        leftover("adxl345-leftover", "ADXL345_CLEAR", "adxl345 range=cache",
                 "adxl345 leftover still ranges cache accelerometer as range=cache",
                 "echo 1 > /sys/bus/i2c/drivers/adxl345/unbind",
                 "adxl345 unbind is EBUSY; leftover range=cache still ranges cache accelerometer",
                 "leftover adxl345 ranging cache accelerometer",
                 "this mill cma3000 / r uinput / cache-admin 403",
                 "this mill cma3000 leftover (adxl345 leftover, not cma3000 fuzz)",
                 "test_adxl345.py",
                 "ls /sys/bus/i2c/drivers/adxl345; cat /sys/class/input/input0/name",
                 "adxl345 leftover range=cache leftover"),
    ),
    (
        lang("chef-lang-cache", "CHEF_HOME", "chef", "1.0", "1.1",
             "lib/chef/prelude.chef", "test_chef.py", "src/hello.chef", "chef-11",
             "rm -rf /usr/lib/chef",
             "rm lib does not drop 1.0 prelude.chef under unversioned CHEF_HOME",
             "1MB", "this mill shakespeare-lang / r intercal (Chef prelude.chef, not Shakespeare or INTERCAL)",
             "chef src/hello.chef", "chef --version"),
        leftover("bmi160-leftover", "BMI160_CLEAR", "bmi160 range=cache",
                 "bmi160 leftover still ranges cache IMU as range=cache",
                 "echo 1 > /sys/bus/i2c/drivers/bmi160/unbind",
                 "bmi160 unbind is EBUSY; leftover range=cache still ranges cache IMU",
                 "leftover bmi160 ranging cache IMU",
                 "this mill adxl345 / this mill cma3000 / cache-admin 403",
                 "this mill adxl345 leftover (bmi160 leftover, not adxl345 range)",
                 "test_bmi160.py",
                 "ls /sys/bus/i2c/drivers/bmi160; cat /sys/class/iio/iio:device0/name",
                 "bmi160 leftover range=cache leftover"),
    ),
    (
        lang("shakespeare-lang-cache", "SPL_HOME", "spl", "1.2.1", "1.3.0",
             "lib/spl/std.spl", "test_spl.py", "src/hamlet.spl", "spl-130",
             "rm -rf /usr/lib/spl",
             "rm lib does not drop 1.2 std.spl under unversioned SPL_HOME",
             "1MB", "this mill chef-lang / r intercal (Shakespeare std.spl, not Chef or INTERCAL)",
             "spl src/hamlet.spl", "spl --version"),
        leftover("invensense-leftover", "INVENSENSE_CLEAR", "mpu6050 scale=cache",
                 "mpu6050 leftover still scales cache IMU as scale=cache",
                 "echo 1 > /sys/bus/i2c/drivers/mpu6050/unbind",
                 "mpu6050 unbind is EBUSY; leftover scale=cache still scales cache IMU",
                 "leftover mpu6050 scaling cache IMU",
                 "this mill bmi160 / this mill adxl345 / cache-admin 403",
                 "this mill bmi160 leftover (mpu6050 leftover, not bmi160 range)",
                 "test_mpu6050.py",
                 "ls /sys/bus/i2c/drivers/mpu6050; cat /sys/class/iio/iio:device0/name",
                 "mpu6050 leftover scale=cache leftover"),
    ),
    (
        lang("sox-formats-cache", "SOX_PATH", "sox", "14.4.2", "14.5.0",
             "lib/sox/libsox_fmt_mp3.so", "test_sox.py", "src/demo.wav", "sox-145",
             "rm -rf /usr/lib/sox",
             "rm lib does not drop 14.4 libsox_fmt_mp3.so under unversioned SOX_PATH",
             "4MB", "this mill ardour-session / this mill ghostscript-icc (SoX fmt mp3, not Ardour or Ghostscript)",
             "sox src/demo.wav src/out.wav", "sox --version"),
        leftover("rp1-dpi-leftover", "RP1_DPI_CLEAR", "rp1-dpi mode=cache",
                 "rp1-dpi leftover still modes cache DPI as mode=cache",
                 "echo 1 > /sys/bus/platform/drivers/rp1-dpi/unbind",
                 "rp1-dpi unbind is EBUSY; leftover mode=cache still modes cache DPI",
                 "leftover rp1-dpi moding cache DPI",
                 "this mill rp1 / r vc4-hdmi / cache-admin 403",
                 "this mill rp1 leftover (rp1-dpi leftover, not rp1 pio southbridge)",
                 "test_rp1dpi.py",
                 "ls /sys/bus/platform/drivers/rp1-dpi; ls /sys/class/drm",
                 "rp1 leftover dpi mode=cache leftover"),
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
    if idx is None:
        raise SystemExit("catalog idx required (do not bind to a stolen round)")
    if idx < 0 or idx >= len(PAIRS):
        raise SystemExit(f"no catalog pair for idx={idx} (len={len(PAIRS)})")
    suc, leftp = PAIRS[idx]
    for spec in (suc, leftp):
        if slug_taken(spec["slug"]):
            raise SystemExit(f"slug {spec['slug']} already published; refuse clone")
    srec = success_episode(round_n, suc)
    lrec = leftover_episode(round_n, leftp)
    if "harbor-" in srec["id"] or "harbor-" in lrec["id"]:
        raise SystemExit("harbor id leaked")
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
        json.dumps(srec, separators=(",", ":"))
        + "\n"
        + json.dumps(lrec, separators=(",", ":"))
        + "\n"
    )
    notes.write_text(notes_for(round_n, suc, leftp, srec, lrec))
    if "Novel coverage:" not in notes.read_text():
        raise SystemExit("NOTES missing Novel coverage")
    print(
        json.dumps(
            {
                "round": round_n,
                "idx": idx,
                "ids": [srec["id"], lrec["id"]],
                "steps": [nsteps_s, nsteps_l],
                "bytes": batch.stat().st_size,
            }
        )
    )


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
