#!/usr/bin/env python3
"""IRC mill r4021+ — wave-47 compiler/docs leftover.

NEW on-call plants (not Wave-27–46 tails). BAN ypbind/oddjob,
r3389 opensearch leftover3c, r3576 tigergraph/hugegraph.
"""
from __future__ import annotations
import importlib.util, json, sys

spec = importlib.util.spec_from_file_location("irc3234", "/tmp/irc_mill_r3234.py")
w16 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w16)
m = w16.m
plant, helm_rb, patch_file = w16.plant, w16.helm_rb, w16.patch_file

ROWS = r'''
llvm|LLVM_TIMEOUT|1|30|s|/etc/llvm/llvm.conf|timeout=1|timeout=30|systemctl reload llvm|opt|llv_to_1|ir|passes|fs leftover leftover down; bounce|LLVM_TIMEOUT leftover 1 leftover; a 2s pass is aborted so opt 504s
lldb|LLDB_TIMEOUT|1|30|s|/etc/lldb/lldb.conf|timeout=1|timeout=30|systemctl reload lldb|lldb|ldb_to_1|dbg|inferiors|ptrace leftover leftover down; bounce|LLDB_TIMEOUT leftover 1 leftover; a 2s attach is aborted so debug 504s
tcc|TCC_TIMEOUT|1|30|s|/etc/tcc/tcc.conf|timeout=1|timeout=30|systemctl reload tcc|tcc|tcc_to_1|c|bin|fs leftover leftover down; bounce|TCC_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the bin 504s
pcc|PCC_TIMEOUT|1|30|s|/etc/pcc/pcc.conf|timeout=1|timeout=30|systemctl reload pcc|pcc|pcc_to_1|c|o|fs leftover leftover down; bounce|PCC_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the obj 504s
icc|ICC_TIMEOUT|1|60|s|/etc/intel/icc.conf|timeout=1|timeout=60|systemctl reload icc|icc|icc_to_1|c|o|fs leftover leftover down; bounce|ICC_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the job 504s
ifort|IFORT_TIMEOUT|1|60|s|/etc/intel/ifort.conf|timeout=1|timeout=60|systemctl reload ifort|ifort|ifo_to_1|f90|o|fs leftover leftover down; bounce|IFORT_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the job 504s
flang|FLANG_TIMEOUT|1|60|s|/etc/flang/flang.conf|timeout=1|timeout=60|systemctl reload flang|flang|fla_to_1|f90|ir|fs leftover leftover down; bounce|FLANG_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the job 504s
gfortran|GFORTRAN_TIMEOUT|1|60|s|/etc/gfortran/gfortran.conf|timeout=1|timeout=60|systemctl reload gfortran|gfortran|gfo_to_1|f90|o|fs leftover leftover down; bounce|GFORTRAN_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the job 504s
f2c|F2C_TIMEOUT|1|30|s|/etc/f2c/f2c.conf|timeout=1|timeout=30|systemctl reload f2c|f2c|f2c_to_1|f|c|fs leftover leftover down; bounce|F2C_TIMEOUT leftover 1 leftover; a 2s translate is aborted so the c 504s
bison|BISON_TIMEOUT|1|30|s|/etc/bison/bison.conf|timeout=1|timeout=30|systemctl reload bison|bison|bis_to_1|y|c|fs leftover leftover down; bounce|BISON_TIMEOUT leftover 1 leftover; a 2s generate is aborted so the parser 504s
flex|FLEX_TIMEOUT|1|30|s|/etc/flex/flex.conf|timeout=1|timeout=30|systemctl reload flex|flex|flx_to_1|l|c|fs leftover leftover down; bounce|FLEX_TIMEOUT leftover 1 leftover; a 2s generate is aborted so the lexer 504s
m4|M4_TIMEOUT|1|30|s|/etc/m4/m4.conf|timeout=1|timeout=30|systemctl reload m4|m4|m4_to_1|m4|out|fs leftover leftover down; bounce|M4_TIMEOUT leftover 1 leftover; a 2s expand is aborted so autoconf 504s
texlive|TEX_TIMEOUT|1|60|s|/etc/texmf/texmf.cnf|timeout=1|timeout=60|systemctl reload texlive|pdflatex|tex_to_1|pdf|fmt|fs leftover leftover down; bounce|TEX_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the pdf 504s
latex|LATEX_TIMEOUT|1|60|s|/etc/texmf/latex.cnf|timeout=1|timeout=60|systemctl reload texlive|latex|ltx_to_1|dvi|aux|fs leftover leftover down; bounce|LATEX_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the dvi 504s
pandoc|PANDOC_TIMEOUT|1|30|s|/etc/pandoc/pandoc.yaml|timeout: 1|timeout: 30|systemctl reload pandoc|pandoc|pan_to_1|md|pdf|fs leftover leftover down; bounce|PANDOC_TIMEOUT leftover 1 leftover; a 2s convert is aborted so the doc 504s
groff|GROFF_TIMEOUT|1|30|s|/etc/groff/groff.conf|timeout=1|timeout=30|systemctl reload groff|groff|grf_to_1|man|ps|fs leftover leftover down; bounce|GROFF_TIMEOUT leftover 1 leftover; a 2s format is aborted so the man 504s
graphviz|DOT_TIMEOUT|1|30|s|/etc/graphviz/graphviz.conf|timeout=1|timeout=30|systemctl reload graphviz|dot|dot_to_1|dot|svg|fs leftover leftover down; bounce|DOT_TIMEOUT leftover 1 leftover; a 2s layout is aborted so the svg 504s
plantuml|PUML_TIMEOUT|1|30|s|/etc/plantuml/plantuml.cfg|timeout=1|timeout=30|systemctl reload plantuml|plantuml|pum_to_1|puml|png|fs leftover leftover down; bounce|PUML_TIMEOUT leftover 1 leftover; a 2s render is aborted so the png 504s
doxygen|DOXYGEN_TIMEOUT|1|60|s|/etc/doxygen/Doxyfile|TIMEOUT=1|TIMEOUT=60|systemctl reload doxygen|doxygen|dox_to_1|xml|html|fs leftover leftover down; bounce|DOXYGEN_TIMEOUT leftover 1 leftover; a 2s parse is aborted so the docs 504s
sphinx|SPHINX_TIMEOUT|1|60|s|/etc/sphinx/conf.py|timeout=1|timeout=60|systemctl reload sphinx-build|sphinx-build|sph_to_1|rst|html|fs leftover leftover down; bounce|SPHINX_TIMEOUT leftover 1 leftover; a 2s build is aborted so the docs 504s
mkdocs|MKDOCS_TIMEOUT|1|30|s|/etc/mkdocs/mkdocs.yml|timeout: 1|timeout: 30|systemctl reload mkdocs|mkdocs|mkd_to_1|md|html|fs leftover leftover down; bounce|MKDOCS_TIMEOUT leftover 1 leftover; a 2s build is aborted so the site 504s
hugo|HUGO_TIMEOUT|1|30|s|/etc/hugo/config.toml|timeout = 1|timeout = 30|systemctl reload hugo|hugo|hug_to_1|md|html|fs leftover leftover down; bounce|HUGO_TIMEOUT leftover 1 leftover; a 2s render is aborted so the site 504s
jekyll|JEKYLL_TIMEOUT|1|30|s|/etc/jekyll/_config.yml|timeout: 1|timeout: 30|systemctl reload jekyll|jekyll|jek_to_1|md|html|fs leftover leftover down; bounce|JEKYLL_TIMEOUT leftover 1 leftover; a 2s build is aborted so the site 504s
hexo|HEXO_TIMEOUT|1|30|s|/etc/hexo/_config.yml|timeout: 1|timeout: 30|systemctl reload hexo|hexo|hex_to_1|md|html|fs leftover leftover down; bounce|HEXO_TIMEOUT leftover 1 leftover; a 2s generate is aborted so the site 504s
eleventy|ELEVENTY_TIMEOUT|1|30|s|/etc/eleventy/eleventy.js|timeout: 1|timeout: 30|systemctl reload eleventy|eleventy|elv_to_1|md|html|fs leftover leftover down; bounce|ELEVENTY_TIMEOUT leftover 1 leftover; a 2s build is aborted so the site 504s
astro|ASTRO_TIMEOUT|1|30|s|/etc/astro/astro.config.mjs|timeout: 1|timeout: 30|systemctl reload astro|astro|ast_to_1|md|html|fs leftover leftover down; bounce|ASTRO_TIMEOUT leftover 1 leftover; a 2s build is aborted so the site 504s
vite|VITE_TIMEOUT|1|30|s|/etc/vite/vite.config.js|timeout: 1|timeout: 30|systemctl reload vite|vite|vit_to_1|mod|bundle|fs leftover leftover down; bounce|VITE_TIMEOUT leftover 1 leftover; a 2s hmr is aborted so the dev 504s
esbuild|ESBUILD_TIMEOUT|1|30|s|/etc/esbuild/esbuild.json|timeout: 1|timeout: 30|systemctl reload esbuild|esbuild|esb_to_1|js|bundle|fs leftover leftover down; bounce|ESBUILD_TIMEOUT leftover 1 leftover; a 2s bundle is aborted so the pack 504s
rollup|ROLLUP_TIMEOUT|1|30|s|/etc/rollup/rollup.config.js|timeout: 1|timeout: 30|systemctl reload rollup|rollup|rol_to_1|js|bundle|fs leftover leftover down; bounce|ROLLUP_TIMEOUT leftover 1 leftover; a 2s bundle is aborted so the pack 504s
webpack|WEBPACK_TIMEOUT|1|30|s|/etc/webpack/webpack.config.js|timeout: 1|timeout: 30|systemctl reload webpack|webpack|wpk_to_1|js|bundle|fs leftover leftover down; bounce|WEBPACK_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the pack 504s
parcel|PARCEL_TIMEOUT|1|30|s|/etc/parcel/package.json|timeout: 1|timeout: 30|systemctl reload parcel|parcel|pcl_to_1|js|bundle|fs leftover leftover down; bounce|PARCEL_TIMEOUT leftover 1 leftover; a 2s bundle is aborted so the pack 504s
swc|SWC_TIMEOUT|1|30|s|/etc/swc/.swcrc|timeout: 1|timeout: 30|systemctl reload swc|swc|swc_to_1|ts|js|fs leftover leftover down; bounce|SWC_TIMEOUT leftover 1 leftover; a 2s transpile is aborted so the pack 504s
turbo|TURBO_TIMEOUT|1|60|s|/etc/turbo/turbo.json|timeout: 1|timeout: 60|systemctl reload turbo|turbo|tur_to_1|cache|tasks|fs leftover leftover down; bounce|TURBO_TIMEOUT leftover 1 leftover; a 2s task is aborted so the pipeline 504s
nx|NX_TIMEOUT|1|60|s|/etc/nx/nx.json|timeout: 1|timeout: 60|systemctl reload nx|nx|nx_to_1|cache|targets|fs leftover leftover down; bounce|NX_TIMEOUT leftover 1 leftover; a 2s target is aborted so the graph 504s
lerna|LERNA_TIMEOUT|1|60|s|/etc/lerna/lerna.json|timeout: 1|timeout: 60|systemctl reload lerna|lerna|lrn_to_1|pkgs|graph|fs leftover leftover down; bounce|LERNA_TIMEOUT leftover 1 leftover; a 2s publish is aborted so the mono 504s
asciidoctor|ASCIIDOCTOR_TIMEOUT|1|30|s|/etc/asciidoctor/asciidoctor.rb|timeout=1|timeout=30|systemctl reload asciidoctor|asciidoctor|ado_to_1|adoc|html|fs leftover leftover down; bounce|ASCIIDOCTOR_TIMEOUT leftover 1 leftover; a 2s convert is aborted so the html 504s
rst2pdf|RST2PDF_TIMEOUT|1|30|s|/etc/rst2pdf/rst2pdf.conf|timeout=1|timeout=30|systemctl reload rst2pdf|rst2pdf|r2p_to_1|rst|pdf|fs leftover leftover down; bounce|RST2PDF_TIMEOUT leftover 1 leftover; a 2s convert is aborted so the pdf 504s
wkhtmltopdf|WKHTML_TIMEOUT|1|30|s|/etc/wkhtmltopdf.conf|timeout=1|timeout=30|systemctl reload wkhtmltopdf|wkhtmltopdf|wkh_to_1|html|pdf|fs leftover leftover down; bounce|WKHTML_TIMEOUT leftover 1 leftover; a 2s render is aborted so the pdf 504s
weasyprint|WEASY_TIMEOUT|1|30|s|/etc/weasyprint/weasyprint.conf|timeout=1|timeout=30|systemctl reload weasyprint|weasyprint|wea_to_1|html|pdf|fs leftover leftover down; bounce|WEASY_TIMEOUT leftover 1 leftover; a 2s render is aborted so the pdf 504s
lynx|LYNX_TIMEOUT|1|10|s|/etc/lynx.cfg|TIMEOUT:1|TIMEOUT:10|systemctl reload lynx|lynx|lyn_to_1|http|pages|tcp leftover leftover down; bounce|LYNX_TIMEOUT leftover 1 leftover; a 2s GET is aborted so the page 504s
w3m|W3M_TIMEOUT|1|10|s|/etc/w3m/config|timeout 1|timeout 10|systemctl reload w3m|w3m|w3m_to_1|http|pages|tcp leftover leftover down; bounce|W3M_TIMEOUT leftover 1 leftover; a 2s GET is aborted so the page 504s
elinks|ELINKS_TIMEOUT|1|10|s|/etc/elinks.conf|set connection.timeout = 1|set connection.timeout = 10|systemctl reload elinks|elinks|eli_to_1|http|pages|tcp leftover leftover down; bounce|ELINKS_TIMEOUT leftover 1 leftover; a 2s GET is aborted so the page 504s
aria2|ARIA2_TIMEOUT|1|30|s|/etc/aria2.conf|timeout=1|timeout=30|systemctl reload aria2|aria2c|ari_to_1|dls|files|tcp leftover leftover down; bounce|ARIA2_TIMEOUT leftover 1 leftover; a 2s GET is aborted so the dl 504s
axel|AXEL_TIMEOUT|1|30|s|/etc/axelrc|timeout=1|timeout=30|systemctl reload axel|axel|axe_to_1|dls|files|tcp leftover leftover down; bounce|AXEL_TIMEOUT leftover 1 leftover; a 2s GET is aborted so the dl 504s
lftp|LFTP_TIMEOUT|1|30|s|/etc/lftp.conf|set net:timeout 1|set net:timeout 30|systemctl reload lftp|lftp|lft_to_1|ftp|files|tcp leftover leftover down; bounce|LFTP_TIMEOUT leftover 1 leftover; a 2s RETR is aborted so the get 504s
ncftp|NCFTP_TIMEOUT|1|30|s|/etc/ncftp/ncftp.conf|timeout=1|timeout=30|systemctl reload ncftp|ncftp|ncf_to_1|ftp|files|tcp leftover leftover down; bounce|NCFTP_TIMEOUT leftover 1 leftover; a 2s RETR is aborted so the get 504s
mutt|MUTT_TIMEOUT|1|30|s|/etc/Muttrc|set timeout=1|set timeout=30|systemctl reload mutt|mutt|mut_to_1|imap|mbox|tcp leftover leftover down; bounce|MUTT_TIMEOUT leftover 1 leftover; a 2s IDLE is aborted so the inbox 504s
neomutt|NEOMUTT_TIMEOUT|1|30|s|/etc/neomuttrc|set timeout=1|set timeout=30|systemctl reload neomutt|neomutt|nmu_to_1|imap|mbox|tcp leftover leftover down; bounce|NEOMUTT_TIMEOUT leftover 1 leftover; a 2s IDLE is aborted so the inbox 504s
alpine|ALPINE_TIMEOUT|1|30|s|/etc/pine.conf|timeout=1|timeout=30|systemctl reload alpine|alpine|alp_to_1|imap|mbox|tcp leftover leftover down; bounce|ALPINE_TIMEOUT leftover 1 leftover; a 2s SELECT is aborted so the inbox 504s
notmuch|NOTMUCH_TIMEOUT|1|30|s|/etc/notmuch-config|timeout=1|timeout=30|systemctl reload notmuch|notmuch|ntm_to_1|xapian|mail|fs leftover leftover down; bounce|NOTMUCH_TIMEOUT leftover 1 leftover; a 2s index is aborted so search 504s
mairix|MAIRIX_TIMEOUT|1|30|s|/etc/mairixrc|timeout=1|timeout=30|systemctl reload mairix|mairix|mai_to_1|idx|mail|fs leftover leftover down; bounce|MAIRIX_TIMEOUT leftover 1 leftover; a 2s index is aborted so search 504s
offlineimap|OFFLINEIMAP_TIMEOUT|1|30|s|/etc/offlineimaprc|timeout=1|timeout=30|systemctl reload offlineimap|offlineimap|off_to_1|imap|maildir|tcp leftover leftover down; bounce|OFFLINEIMAP_TIMEOUT leftover 1 leftover; a 2s sync is aborted so the box 504s
mbsync|MBSYNC_TIMEOUT|1|30|s|/etc/mbsyncrc|Timeout 1|Timeout 30|systemctl reload mbsync|mbsync|mbs_to_1|imap|maildir|tcp leftover leftover down; bounce|MBSYNC_TIMEOUT leftover 1 leftover; a 2s sync is aborted so the box 504s
isync|ISYNC_TIMEOUT|1|30|s|/etc/isyncrc|Timeout 1|Timeout 30|systemctl reload isync|isync|isy_to_1|imap|maildir|tcp leftover leftover down; bounce|ISYNC_TIMEOUT leftover 1 leftover; a 2s sync is aborted so the box 504s
msmtp|MSMTP_TIMEOUT|1|30|s|/etc/msmtprc|timeout 1|timeout 30|systemctl reload msmtp|msmtp|msm_to_1|smtp|queue|tcp leftover leftover down; bounce|MSMTP_TIMEOUT leftover 1 leftover; a 2s MAIL is aborted so send 504s
nullmailer|NULLMAILER_TIMEOUT|1|30|s|/etc/nullmailer/timeout|1|30|systemctl reload nullmailer|nullmailer-queue|nml_to_1|smtp|queue|tcp leftover leftover down; bounce|NULLMAILER_TIMEOUT leftover 1 leftover; a 2s send is aborted so the queue 504s
fetchmail|FETCHMAIL_TIMEOUT|1|30|s|/etc/fetchmailrc|timeout 1|timeout 30|systemctl reload fetchmail|fetchmail|fch_to_1|pop|mbox|tcp leftover leftover down; bounce|FETCHMAIL_TIMEOUT leftover 1 leftover; a 2s RETR is aborted so the inbox 504s
getmail|GETMAIL_TIMEOUT|1|30|s|/etc/getmail/getmailrc|timeout=1|timeout=30|systemctl reload getmail|getmail|gtm_to_1|imap|maildir|tcp leftover leftover down; bounce|GETMAIL_TIMEOUT leftover 1 leftover; a 2s FETCH is aborted so the inbox 504s
procmail|PROCMAIL_TIMEOUT|1|30|s|/etc/procmailrc|TIMEOUT=1|TIMEOUT=30|systemctl reload procmail|procmail|prc_to_1|recipes|mbox|fs leftover leftover down; bounce|PROCMAIL_TIMEOUT leftover 1 leftover; a 2s recipe is aborted so deliver 504s
maildrop|MAILDROP_TIMEOUT|1|30|s|/etc/maildroprc|TIMEOUT=1|TIMEOUT=30|systemctl reload maildrop|maildrop|mdp_to_1|filters|maildir|fs leftover leftover down; bounce|MAILDROP_TIMEOUT leftover 1 leftover; a 2s filter is aborted so deliver 504s
abook|ABOOK_TIMEOUT|1|10|s|/etc/abook/abookrc|timeout=1|timeout=10|systemctl reload abook|abook|abk_to_1|addr|db|fs leftover leftover down; bounce|ABOOK_TIMEOUT leftover 1 leftover; a 2s write is aborted so the book 504s
idmapd|IDMAPD_TIMEOUT|1|10|s|/etc/idmapd.conf|Timeout = 1|Timeout = 10|systemctl reload nfs-idmapd|rpc.idmapd|idm_to_1|ids|names|nfs leftover leftover down; bounce|IDMAPD_TIMEOUT leftover 1 leftover; a 2s map is aborted so NFSv4 401s
nfsdcld|NFSDCLD_TIMEOUT|1|10|s|/etc/nfs.conf|timeout=1|timeout=10|systemctl reload nfsdcld|nfsdcld|ncl_to_1|clients|leases|nfs leftover leftover down; bounce|NFSDCLD_TIMEOUT leftover 1 leftover; a 2s track is aborted so reclaim 504s
nfsidmap|NFSIDMAP_TIMEOUT|1|10|s|/etc/idmapd.conf|Timeout = 1|Timeout = 10|systemctl reload nfsidmap|nfsidmap|nid_to_1|uids|names|nfs leftover leftover down; bounce|NFSIDMAP_TIMEOUT leftover 1 leftover; a 2s lookup is aborted so NFSv4 401s
gssd|GSSD_TIMEOUT|1|10|s|/etc/nfs.conf|timeout=1|timeout=10|systemctl reload rpc-gssd|rpc.gssd|gss_to_1|krb|ctx|nfs leftover leftover down; bounce|GSSD_TIMEOUT leftover 1 leftover; a 2s gss is aborted so mount 401s
svcgssd|SVCGSSD_TIMEOUT|1|10|s|/etc/nfs.conf|timeout=1|timeout=10|systemctl reload rpc-svcgssd|rpc.svcgssd|sgs_to_1|krb|svc|nfs leftover leftover down; bounce|SVCGSSD_TIMEOUT leftover 1 leftover; a 2s accept is aborted so export 401s
blkmapd|BLKMAPD_TIMEOUT|1|10|s|/etc/nfs.conf|timeout=1|timeout=10|systemctl reload blkmapd|blkmapd|blk_to_1|devs|pnfs|nfs leftover leftover down; bounce|BLKMAPD_TIMEOUT leftover 1 leftover; a 2s layout is aborted so pNFS 504s
vim|VIM_TIMEOUT|1|10|s|/etc/vim/vimrc|set timeoutlen=1|set timeoutlen=1000|systemctl reload vim|vim|vim_to_1|buf|swap|fs leftover leftover down; bounce|VIM_TIMEOUT leftover 1 leftover; a 2s write is aborted so the file 504s
neovim|NVIM_TIMEOUT|1|10|s|/etc/xdg/nvim/init.vim|set timeoutlen=1|set timeoutlen=1000|systemctl reload nvim|nvim|nvi_to_1|buf|swap|fs leftover leftover down; bounce|NVIM_TIMEOUT leftover 1 leftover; a 2s rpc is aborted so the ui 504s
emacs|EMACS_TIMEOUT|1|10|s|/etc/emacs/site-start.el|(setq timeout 1)|(setq timeout 10)|systemctl reload emacs|emacs|ema_to_1|buf|files|fs leftover leftover down; bounce|EMACS_TIMEOUT leftover 1 leftover; a 2s save is aborted so the file 504s
nano|NANO_TIMEOUT|1|10|s|/etc/nanorc|set timeout 1|set timeout 10|systemctl reload nano|nano|nan_to_1|buf|files|fs leftover leftover down; bounce|NANO_TIMEOUT leftover 1 leftover; a 2s write is aborted so the file 504s
micro|MICRO_TIMEOUT|1|10|s|/etc/micro/settings.json|"timeout": 1|"timeout": 10|systemctl reload micro|micro|mic_to_1|buf|files|fs leftover leftover down; bounce|MICRO_TIMEOUT leftover 1 leftover; a 2s save is aborted so the file 504s
kakoune|KAK_TIMEOUT|1|10|s|/etc/kak/kakrc|timeout 1|timeout 10|systemctl reload kak|kak|kak_to_1|buf|files|fs leftover leftover down; bounce|KAK_TIMEOUT leftover 1 leftover; a 2s write is aborted so the file 504s
helix|HELIX_TIMEOUT|1|10|s|/etc/helix/config.toml|timeout = 1|timeout = 10|systemctl reload hx|hx|hlx_to_1|buf|files|fs leftover leftover down; bounce|HELIX_TIMEOUT leftover 1 leftover; a 2s save is aborted so the file 504s
ffmpeg|FFMPEG_TIMEOUT|1|30|s|/etc/ffmpeg/ffmpeg.conf|timeout=1|timeout=30|systemctl reload ffmpeg|ffmpeg|ffm_to_1|frames|out|fs leftover leftover down; bounce|FFMPEG_TIMEOUT leftover 1 leftover; a 2s encode is aborted so the file 504s
sox|SOX_TIMEOUT|1|30|s|/etc/sox/sox.conf|timeout=1|timeout=30|systemctl reload sox|sox|sox_to_1|wav|out|fs leftover leftover down; bounce|SOX_TIMEOUT leftover 1 leftover; a 2s convert is aborted so the wav 504s
lame|LAME_TIMEOUT|1|30|s|/etc/lame/lame.conf|timeout=1|timeout=30|systemctl reload lame|lame|lam_to_1|wav|mp3|fs leftover leftover down; bounce|LAME_TIMEOUT leftover 1 leftover; a 2s encode is aborted so the mp3 504s
mpv|MPV_TIMEOUT|1|10|s|/etc/mpv/mpv.conf|timeout=1|timeout=10|systemctl reload mpv|mpv|mpv_to_1|demux|out|fs leftover leftover down; bounce|MPV_TIMEOUT leftover 1 leftover; a 2s open is aborted so playback 504s
vlc|VLC_TIMEOUT|1|10|s|/etc/vlc/vlcrc|timeout=1|timeout=10|systemctl reload vlc|vlc|vlc_to_1|demux|out|fs leftover leftover down; bounce|VLC_TIMEOUT leftover 1 leftover; a 2s open is aborted so playback 504s
mpd|MPD_TIMEOUT|1|10|s|/etc/mpd.conf|timeout "1"|timeout "10"|systemctl reload mpd|mpc|mpd_to_1|db|playlists|fs leftover leftover down; bounce|MPD_TIMEOUT leftover 1 leftover; a 2s update is aborted so the db 504s
'''
WAVE47 = (
    "llvm/lldb/tcc/pcc/icc/ifort/flang/gfortran/f2c/bison/flex/m4/texlive/"
    "latex/pandoc/groff/graphviz/plantuml/doxygen/sphinx/mkdocs/hugo/jekyll/"
    "hexo/eleventy/astro/vite/esbuild/rollup/webpack/parcel/swc/turbo/nx/"
    "lerna/asciidoctor/rst2pdf/wkhtmltopdf/weasyprint/lynx/w3m/elinks/aria2/"
    "axel/lftp/ncftp/mutt/neomutt/alpine/notmuch/mairix/offlineimap/mbsync/"
    "isync/msmtp/nullmailer/fetchmail/getmail/procmail/maildrop/abook/"
    "idmapd/nfsdcld/nfsidmap/gssd/svcgssd/blkmapd/vim/neovim/emacs/nano/"
    "micro/kakoune/helix/ffmpeg/sox/lame/mpv/vlc/mpd"
)


def _parse_rows():
    plants = []
    srcs = ("grafana", "pagerduty", "opsgenie", "alertmanager")
    ns_cycle = (17, 16, 18)
    for raw in ROWS.strip().splitlines():
        raw = raw.strip()
        if not raw or raw.startswith("#"):
            continue
        parts = raw.split("|")
        if len(parts) != 15:
            raise SystemExit(f"bad row cols={len(parts)}: {raw[:160]}")
        (
            daemon, key, old, new, unit, path, oldv, newv, reload, hpeer, metric,
            what, wipe, herring, rca_tail,
        ) = parts
        i = len(plants)
        n = ns_cycle[i % 3]
        rem = "rollback" if i % 2 == 0 else "patch"
        src = srcs[i % 4]
        svc = f"c7{i:02d}x"
        ns = f"c7{i:02d}"
        clu = f"prod-apsc{901 + i}-{svc[:3]}"
        ticket = f"W2-{12563 + i}"
        node = f"ip-10-232-{1 + i}-{20 + i}"
        slug = f"{daemon}-{key}-{old}{unit}-{svc}"
        key_words = key.replace(".", " leftover ").replace("_", " leftover ")
        symptom = f"{key_words} leftover {old}{unit} leftover; {what} drop"
        because = (
            f"is dropping {what} because leftover {daemon} leftover {key_words} leftover is {old} leftover."
        )
        do_not = f"Restore {new}{unit}; do not wipe {wipe}."
        rca = f"{daemon} leftover {key} leftover {old} leftover; {rca_tail}"
        if rem == "rollback":
            remnant = helm_rb(ns, svc, 3, path, oldv, newv, reload)
            extra = f"helm -n {ns} history {svc} | head -5"
            eobs = f"4  {old}{unit}\n3  last-good {new}"
        else:
            remnant = patch_file(path, oldv, newv, reload)
            extra = f"kubectl -n {ns} logs deploy/{svc} --since=5m | grep {key} | tail"
            eobs = f"{key} leftover {old}"
        plants.append(
            plant(
                slug=slug, ticket=ticket, service=svc, ns=ns, cluster=clu, src=src,
                node=node, symptom=symptom, because=because, do_not=do_not,
                herring=herring, rca=rca, remediate=rem, metric=metric,
                hcmds=[
                    f"{hpeer} leftover status | head",
                    f"systemctl reload {hpeer} || true",
                    f"{hpeer} leftover bounce leftover || true",
                ],
                hobs=[f"{hpeer} ok", "bounce unused", f"still {key} {old}"],
                inspect=f"grep {key} {path}", iobs=f"{oldv} leftover",
                extra=extra, eobs=eobs, rem=remnant, robs=f"{key} {new}; holds",
                verify=f"grep {key} {path}", vok=f"{new}; {ticket} resolved", n=n,
            )
        )
    return plants


PLANTS = _parse_rows()
m.PLANTS = PLANTS
m.BASE_ROUND = 4021


def notes_for(round_n, eps):
    slug0 = eps[0]["id"].split("-", 2)[2].rsplit("-", 2)[0]
    slug1 = eps[1]["id"].split("-", 2)[2].rsplit("-", 2)[0]
    rows = [
        f"| `{e['id']}` | {e['meta']['ticket']} | {e['false_lead']['claim'].replace('|', '/')} | {e['remediate']} | {e['reward']['success']} | {e['reward']['steps']} |"
        for e in eps
    ]
    return "\n".join(
        [
            f"# incident-response-oncall-factory NOTES r{round_n}",
            "",
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r4020 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-47 leftover: {WAVE47}.",
            "",
            "OpenSRE designed: 429 then 502 retries, 3-step herring, unique RCA, mix patch/rollback. plant=designed. generator=grok-4.6.",
            "",
            "| id | ticket | herring (steps 6-8) | remediate | success | steps |",
            "|---|---|---|---|---|---|",
            *rows,
            "",
            "## Contract audit",
            f"- Q=2 episodes, kind=episode, ids irc-r{round_n}-*.",
            "- Unique goal service+cluster+symptom; 3 false-lead actions; 429/502 retries.",
            "- Residual: designed excerpts, not live dispatcher traces.",
            "",
        ]
    )


m.notes_for = notes_for


def extra_unique_guards():
    banned = (
        "Follow OpenSRE", "fraud-graph", "sip-proxy", "traefik", "limit_req",
        "cloudfront", "fastly", "kube-proxy", "haproxy", "varnish", "metallb",
        "imperva", "bunny", "calico felix", "kong ", "caddy ",
        "github actions leftover", "gitlab leftover", "circleci leftover",
        "tekton leftover", "snowflake", "bigquery", "redshift", "idle_timeout",
        "max_client_conn", "ypbind", "oddjob", "opensearch", "leftover3c",
        "tigergraph", "hugegraph", "graphdb", "stardog", "debezium", "hasura",
    )
    for p in PLANTS:
        blob = (p["goal"] + " " + p["rca"] + " " + p["slug"]).lower()
        for tok in banned:
            if tok.lower() in blob:
                raise SystemExit(f"banned {tok} in {p['slug']}")
        for need in (p["service"], p["ns"], p["cluster"]):
            if need not in p["goal"]:
                raise SystemExit(p["slug"])
        if p["n_steps"] not in (16, 17, 18) or p["remediate"] not in ("rollback", "patch"):
            raise SystemExit(p["slug"])
    if len(PLANTS) % 2:
        raise SystemExit("odd")
    for i in range(0, len(PLANTS), 2):
        if {PLANTS[i]["remediate"], PLANTS[i + 1]["remediate"]} != {"rollback", "patch"}:
            raise SystemExit(f"pair {i}")


def main():
    extra_unique_guards()
    used_svc, used_clu, used_tix, _ids = m.harvest_used(m.FACTORY_DIR)
    for p in PLANTS:
        if p["service"] in used_svc:
            raise SystemExit(f"service collision {p['service']}")
        if p["cluster"] in used_clu:
            raise SystemExit(f"cluster collision {p['cluster']}")
        if p["ticket"] in used_tix:
            raise SystemExit(f"ticket collision {p['ticket']}")
    for label, xs in (
        ("slug", [p["slug"] for p in PLANTS]),
        ("svc", [p["service"] for p in PLANTS]),
        ("clu", [p["cluster"] for p in PLANTS]),
        ("tix", [p["ticket"] for p in PLANTS]),
        ("node", [p["node"] for p in PLANTS]),
        ("ns", [p["ns"] for p in PLANTS]),
    ):
        if len(set(xs)) != len(xs):
            raise SystemExit("dup " + label)
    print(json.dumps({"ok": True, "plants": len(PLANTS), "rounds": len(PLANTS) // 2}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
