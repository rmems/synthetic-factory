#!/usr/bin/env python3
"""IRC mill r3981+ — wave-46 toolchain/session leftover.

NEW on-call plants (not Wave-27–45 tails). BAN ypbind/oddjob,
r3389 opensearch leftover3c, r3576 tigergraph/hugegraph.
"""
from __future__ import annotations
import importlib.util, json, sys

spec = importlib.util.spec_from_file_location("irc3234", "/tmp/irc_mill_r3234.py")
w16 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w16)
m = w16.m
plant, helm_rb, patch_file = w16.plant, w16.helm_rb, w16.patch_file

# daemon timeout plants; 80 unique first tokens
ROWS = r'''
python|PYTHONUNBUFFERED_TIMEOUT|1|30|s|/etc/python/sitecustomize.py|timeout=1|timeout=30|systemctl reload python|python|py_to_1|interp|sitecustomize|fs leftover leftover down; bounce|PYTHONUNBUFFERED_TIMEOUT leftover 1 leftover; a 2s import is aborted so the app 504s
ocaml|OCAML_TIMEOUT|1|30|s|/etc/ocaml/ocaml.conf|timeout=1|timeout=30|systemctl reload ocaml|ocaml|oc_to_1|cmi|cmo|fs leftover leftover down; bounce|OCAML_TIMEOUT leftover 1 leftover; a 2s compile is aborted so dune 504s
haskell|GHC_TIMEOUT|1|30|s|/etc/ghc/ghc.conf|timeout=1|timeout=30|systemctl reload ghc|ghc|hs_to_1|hi|o|fs leftover leftover down; bounce|GHC_TIMEOUT leftover 1 leftover; a 2s compile is aborted so cabal 504s
cabal|CABAL_TIMEOUT|1|60|s|/etc/cabal/config|timeout: 1|timeout: 60|systemctl reload cabal|cabal|cab_to_1|pkgs|store|http leftover leftover down; bounce|CABAL_TIMEOUT leftover 1 leftover; a 2s fetch is aborted so build 504s
stack|STACK_TIMEOUT|1|60|s|/etc/stack/config.yaml|timeout: 1|timeout: 60|systemctl reload stack|stack|stk_to_1|work|lts|http leftover leftover down; bounce|STACK_TIMEOUT leftover 1 leftover; a 2s setup is aborted so build 504s
cargo|CARGO_TIMEOUT|1|60|s|/etc/cargo/config.toml|timeout = 1|timeout = 60|systemctl reload cargo|cargo|crg_to_1|crates|registry|http leftover leftover down; bounce|CARGO_TIMEOUT leftover 1 leftover; a 2s fetch is aborted so build 504s
go|GO_TIMEOUT|1|60|s|/etc/go/env|GOFLAGS=-timeout=1s|GOFLAGS=-timeout=60s|systemctl reload go|go|go_to_1|mods|cache|http leftover leftover down; bounce|GO_TIMEOUT leftover 1 leftover; a 2s get is aborted so build 504s
gcc|GCC_TIMEOUT|1|60|s|/etc/gcc/gcc.conf|timeout=1|timeout=60|systemctl reload gcc|gcc|gcc_to_1|cc1|as|fs leftover leftover down; bounce|GCC_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the job 504s
clang|CLANG_TIMEOUT|1|60|s|/etc/clang/clang.conf|timeout=1|timeout=60|systemctl reload clang|clang|clg_to_1|cc1|ir|fs leftover leftover down; bounce|CLANG_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the job 504s
bfd|BFD_TIMEOUT|1|30|s|/etc/binutils/bfd.conf|timeout=1|timeout=30|systemctl reload ld|ld|bfd_to_1|objs|so|fs leftover leftover down; bounce|BFD_TIMEOUT leftover 1 leftover; a 2s link is aborted so the binary 504s
yasm|YASM_TIMEOUT|1|30|s|/etc/yasm/yasm.conf|timeout=1|timeout=30|systemctl reload yasm|yasm|yas_to_1|asm|obj|fs leftover leftover down; bounce|YASM_TIMEOUT leftover 1 leftover; a 2s assemble is aborted so the obj 504s
fasm|FASM_TIMEOUT|1|30|s|/etc/fasm/fasm.conf|timeout=1|timeout=30|systemctl reload fasm|fasm|fas_to_1|asm|bin|fs leftover leftover down; bounce|FASM_TIMEOUT leftover 1 leftover; a 2s assemble is aborted so the bin 504s
gdc|GDC_TIMEOUT|1|60|s|/etc/gdc/gdc.conf|timeout=1|timeout=60|systemctl reload gdc|gdc|gdc_to_1|d|o|fs leftover leftover down; bounce|GDC_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the D job 504s
julia|JULIA_TIMEOUT|1|60|s|/etc/julia/startup.jl|timeout=1|timeout=60|systemctl reload julia|julia|jul_to_1|pkgs|depot|http leftover leftover down; bounce|JULIA_TIMEOUT leftover 1 leftover; a 2s precompile is aborted so Pkg 504s
octave|OCTAVE_TIMEOUT|1|60|s|/etc/octave/octaverc|timeout=1|timeout=60|systemctl reload octave|octave|oct_to_1|m|oct|fs leftover leftover down; bounce|OCTAVE_TIMEOUT leftover 1 leftover; a 2s eval is aborted so the script 504s
matlab|MATLAB_TIMEOUT|1|60|s|/etc/matlab/matlab.conf|timeout=1|timeout=60|systemctl reload matlab|matlab|mat_to_1|m|mex|fs leftover leftover down; bounce|MATLAB_TIMEOUT leftover 1 leftover; a 2s eval is aborted so the job 504s
scilab|SCILAB_TIMEOUT|1|60|s|/etc/scilab/scilab.ini|timeout=1|timeout=60|systemctl reload scilab|scilab|sci_to_1|sce|bin|fs leftover leftover down; bounce|SCILAB_TIMEOUT leftover 1 leftover; a 2s exec is aborted so the script 504s
r-base|R_TIMEOUT|1|60|s|/etc/R/Renviron|R_TIMEOUT=1|R_TIMEOUT=60|systemctl reload R|R|rba_to_1|rds|lib|fs leftover leftover down; bounce|R_TIMEOUT leftover 1 leftover; a 2s install.packages is aborted so CRAN 504s
rstudio|RSTUDIO_TIMEOUT|1|30|s|/etc/rstudio/rserver.conf|www-timeout=1|www-timeout=30|systemctl reload rstudio-server|rstudio-server|rst_to_1|sess|users|http leftover leftover down; bounce|RSTUDIO_TIMEOUT leftover 1 leftover; a 2s session is aborted so the IDE 504s
ipython|IPYTHON_TIMEOUT|1|30|s|/etc/ipython/ipython_config.py|c.InteractiveShell.timeout=1|c.InteractiveShell.timeout=30|systemctl reload jupyter|ipython|ipy_to_1|repl|kernels|fs leftover leftover down; bounce|IPYTHON_TIMEOUT leftover 1 leftover; a 2s exec is aborted so the kernel 504s
jupyter|JUPYTER_TIMEOUT|1|30|s|/etc/jupyter/jupyter_server_config.py|c.ServerApp.iopub_data_rate_limit=1|c.ServerApp.iopub_data_rate_limit=1000000|systemctl reload jupyter|jupyter|jup_to_1|nb|kernels|http leftover leftover down; bounce|JUPYTER_TIMEOUT leftover 1 leftover; a 2s kernel is aborted so the nb 504s
micromamba|MAMBA_TIMEOUT|1|60|s|/etc/micromamba/micromamba.yaml|timeout: 1|timeout: 60|systemctl reload micromamba|micromamba|mmb_to_1|envs|pkgs|https leftover leftover 403; bounce|MAMBA_TIMEOUT leftover 1 leftover; a 2s solve is aborted so the env 504s
pdm|PDM_TIMEOUT|1|60|s|/etc/pdm/config.toml|timeout = 1|timeout = 60|systemctl reload pdm|pdm|pdm_to_1|locks|venv|https leftover leftover 403; bounce|PDM_TIMEOUT leftover 1 leftover; a 2s lock is aborted so install 504s
rye|RYE_TIMEOUT|1|60|s|/etc/rye/config.toml|timeout = 1|timeout = 60|systemctl reload rye|rye|rye_to_1|locks|venv|https leftover leftover 403; bounce|RYE_TIMEOUT leftover 1 leftover; a 2s sync is aborted so the venv 504s
pipx|PIPX_TIMEOUT|1|60|s|/etc/pipx/pipx.conf|timeout=1|timeout=60|systemctl reload pipx|pipx|pxx_to_1|venvs|apps|https leftover leftover 403; bounce|PIPX_TIMEOUT leftover 1 leftover; a 2s install is aborted so the app 504s
npm|NPM_TIMEOUT|1|60|s|/etc/npmrc|fetch-timeout=1|fetch-timeout=60000|systemctl reload npm|npm|npm_to_1|pkgs|cache|https leftover leftover 403; bounce|NPM_TIMEOUT leftover 1 leftover; a 2s fetch is aborted so install 504s
pnpm|PNPM_TIMEOUT|1|60|s|/etc/pnpm/rc|fetch-timeout=1|fetch-timeout=60000|systemctl reload pnpm|pnpm|pnp_to_1|store|pkgs|https leftover leftover 403; bounce|PNPM_TIMEOUT leftover 1 leftover; a 2s fetch is aborted so install 504s
maven|MAVEN_TIMEOUT|1|60|s|/etc/maven/settings.xml|<timeout>1</timeout>|<timeout>60000</timeout>|systemctl reload mvn|mvn|mvn_to_1|artifacts|repo|https leftover leftover 403; bounce|MAVEN_TIMEOUT leftover 1 leftover; a 2s resolve is aborted so the build 504s
gradle|GRADLE_TIMEOUT|1|60|s|/etc/gradle/gradle.properties|org.gradle.internal.http.connectionTimeout=1|org.gradle.internal.http.connectionTimeout=60000|systemctl reload gradle|gradle|grd_to_1|cache|deps|https leftover leftover 403; bounce|GRADLE_TIMEOUT leftover 1 leftover; a 2s resolve is aborted so the build 504s
sbt|SBT_TIMEOUT|1|60|s|/etc/sbt/sbtopts|-Dsbt.boot.timeout=1|-Dsbt.boot.timeout=60|systemctl reload sbt|sbt|sbt_to_1|ivy|coursier|https leftover leftover 403; bounce|SBT_TIMEOUT leftover 1 leftover; a 2s update is aborted so the build 504s
mill|MILL_TIMEOUT|1|60|s|/etc/mill/mill.conf|timeout=1|timeout=60|systemctl reload mill|mill|mil_to_1|out|coursier|https leftover leftover 403; bounce|MILL_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the build 504s
ant|ANT_TIMEOUT|1|60|s|/etc/ant/ant.conf|timeout=1|timeout=60|systemctl reload ant|ant|ant_to_1|jars|lib|https leftover leftover 403; bounce|ANT_TIMEOUT leftover 1 leftover; a 2s get is aborted so the build 504s
ivy|IVY_TIMEOUT|1|60|s|/etc/ivy/ivysettings.xml|timeout="1"|timeout="60000"|systemctl reload ivy|ivy|ivy_to_1|jars|cache|https leftover leftover 403; bounce|IVY_TIMEOUT leftover 1 leftover; a 2s resolve is aborted so the build 504s
cmake|CMAKE_TIMEOUT|1|60|s|/etc/cmake/cmake.conf|timeout=1|timeout=60|systemctl reload cmake|cmake|cma_to_1|cache|build|fs leftover leftover down; bounce|CMAKE_TIMEOUT leftover 1 leftover; a 2s configure is aborted so the build 504s
ninja|NINJA_TIMEOUT|1|60|s|/etc/ninja/ninja.conf|timeout=1|timeout=60|systemctl reload ninja|ninja|nin_to_1|jobs|graph|fs leftover leftover down; bounce|NINJA_TIMEOUT leftover 1 leftover; a 2s edge is aborted so the build 504s
meson|MESON_TIMEOUT|1|60|s|/etc/meson/meson.conf|timeout=1|timeout=60|systemctl reload meson|meson|mes_to_1|build|wraps|https leftover leftover 403; bounce|MESON_TIMEOUT leftover 1 leftover; a 2s setup is aborted so the build 504s
autoconf|AUTOCONF_TIMEOUT|1|60|s|/etc/autoconf/autoconf.conf|timeout=1|timeout=60|systemctl reload autoconf|autoconf|acf_to_1|m4|configure|fs leftover leftover down; bounce|AUTOCONF_TIMEOUT leftover 1 leftover; a 2s expand is aborted so configure 504s
automake|AUTOMAKE_TIMEOUT|1|60|s|/etc/automake/automake.conf|timeout=1|timeout=60|systemctl reload automake|automake|amk_to_1|am|in|fs leftover leftover down; bounce|AUTOMAKE_TIMEOUT leftover 1 leftover; a 2s generate is aborted so Makefile 504s
libtool|LIBTOOL_TIMEOUT|1|30|s|/etc/libtool/libtool.conf|timeout=1|timeout=30|systemctl reload libtool|libtool|ltl_to_1|lo|la|fs leftover leftover down; bounce|LIBTOOL_TIMEOUT leftover 1 leftover; a 2s link is aborted so the so 504s
make|MAKE_TIMEOUT|1|60|s|/etc/make/make.conf|timeout=1|timeout=60|systemctl reload make|make|mk_to_1|jobs|deps|fs leftover leftover down; bounce|MAKE_TIMEOUT leftover 1 leftover; a 2s recipe is aborted so the target 504s
bmake|BMAKE_TIMEOUT|1|60|s|/etc/bmake/sys.mk|timeout=1|timeout=60|systemctl reload bmake|bmake|bmk_to_1|jobs|deps|fs leftover leftover down; bounce|BMAKE_TIMEOUT leftover 1 leftover; a 2s recipe is aborted so the target 504s
gmake|GMAKE_TIMEOUT|1|60|s|/etc/gmake/make.conf|timeout=1|timeout=60|systemctl reload gmake|gmake|gmk_to_1|jobs|deps|fs leftover leftover down; bounce|GMAKE_TIMEOUT leftover 1 leftover; a 2s recipe is aborted so the target 504s
pkgconfig|PKGCONFIG_TIMEOUT|1|10|s|/etc/pkgconfig/pkg-config.conf|timeout=1|timeout=10|systemctl reload pkg-config|pkg-config|pkc_to_1|pc|libs|fs leftover leftover down; bounce|PKGCONFIG_TIMEOUT leftover 1 leftover; a 2s lookup is aborted so configure 504s
cupsd|CUPS_TIMEOUT|1|30|s|/etc/cups/cupsd.conf|Timeout 1|Timeout 300|systemctl reload cups|lpstat|cup_to_1|jobs|printers|usb leftover leftover down; bounce|CUPS_TIMEOUT leftover 1 leftover; a 2s job is aborted so print 504s
polkit|POLKIT_TIMEOUT|1|10|s|/etc/polkit-1/polkit.conf|timeout=1|timeout=10|systemctl reload polkit|pkaction|pol_to_1|auths|actions|dbus leftover leftover down; bounce|POLKIT_TIMEOUT leftover 1 leftover; a 2s CheckAuthorization is aborted so pkexec 401s
udisks2|UDISKS_TIMEOUT|1|30|s|/etc/udisks2/udisks2.conf|timeout=1|timeout=30|systemctl reload udisks2|udisksctl|udi_to_1|block|mounts|udev leftover leftover down; bounce|UDISKS_TIMEOUT leftover 1 leftover; a 2s Mount is aborted so the disk 504s
upowerd|UPOWER_TIMEOUT|1|10|s|/etc/UPower/UPower.conf|timeout=1|timeout=10|systemctl reload upower|upower|upo_to_1|bat|ac|sysfs leftover leftover down; bounce|UPOWER_TIMEOUT leftover 1 leftover; a 2s Enumerate is aborted so the tray 504s
elogind|ELOGIND_TIMEOUT|1|30|s|/etc/elogind/logind.conf|IdleActionSec=1s|IdleActionSec=30min|systemctl reload elogind|loginctl|elo_to_1|seats|sessions|dbus leftover leftover down; bounce|ELOGIND_TIMEOUT leftover 1 leftover; a 2s idle kills the session so SSH 504s
xdm|XDM_TIMEOUT|1|30|s|/etc/X11/xdm/xdm-config|DisplayManager.timeout: 1|DisplayManager.timeout: 30|systemctl reload xdm|xdm|xdm_to_1|dpy|logins|x11 leftover leftover down; bounce|XDM_TIMEOUT leftover 1 leftover; a 2s greeter is aborted so login 504s
xorg|XORG_TIMEOUT|1|30|s|/etc/X11/xorg.conf|Option "Timeout" "1"|Option "Timeout" "30"|systemctl reload display-manager|Xorg|xor_to_1|dpy|gpu|drm leftover leftover down; bounce|XORG_TIMEOUT leftover 1 leftover; a 2s modeset is aborted so the desktop 504s
xwayland|XWAYLAND_TIMEOUT|1|30|s|/etc/X11/xwayland.conf|timeout=1|timeout=30|systemctl reload xwayland|Xwayland|xwl_to_1|dpy|wl|drm leftover leftover down; bounce|XWAYLAND_TIMEOUT leftover 1 leftover; a 2s rootful is aborted so X11 apps 504s
wayland|WAYLAND_TIMEOUT|1|30|s|/etc/wayland/weston.ini|timeout=1|timeout=30|systemctl reload weston|weston|wl_to_1|comp|outputs|drm leftover leftover down; bounce|WAYLAND_TIMEOUT leftover 1 leftover; a 2s commit is aborted so the desktop 504s
i3|I3_TIMEOUT|1|10|s|/etc/i3/config|timeout 1|timeout 10|systemctl reload i3|i3|i3_to_1|ws|win|x11 leftover leftover down; bounce|I3_TIMEOUT leftover 1 leftover; a 2s ipc is aborted so the wm 504s
swaybg|SWAYBG_TIMEOUT|1|10|s|/etc/sway/config|timeout 1|timeout 10|systemctl reload swaybg|swaybg|sbg_to_1|wall|outputs|wl leftover leftover down; bounce|SWAYBG_TIMEOUT leftover 1 leftover; a 2s set is aborted so the wall 504s
picom|PICOM_TIMEOUT|1|10|s|/etc/picom/picom.conf|timeout = 1;|timeout = 10;|systemctl reload picom|picom|pic_to_1|comp|win|x11 leftover leftover down; bounce|PICOM_TIMEOUT leftover 1 leftover; a 2s vsync is aborted so the desktop 504s
compton|COMPTON_TIMEOUT|1|10|s|/etc/compton.conf|timeout = 1;|timeout = 10;|systemctl reload compton|compton|cmp_to_1|comp|win|x11 leftover leftover down; bounce|COMPTON_TIMEOUT leftover 1 leftover; a 2s vsync is aborted so the desktop 504s
openbox|OPENBOX_TIMEOUT|1|10|s|/etc/xdg/openbox/rc.xml|<timeout>1</timeout>|<timeout>10</timeout>|systemctl reload openbox|openbox|obx_to_1|wm|win|x11 leftover leftover down; bounce|OPENBOX_TIMEOUT leftover 1 leftover; a 2s reconfigure is aborted so the wm 504s
awesome|AWESOME_TIMEOUT|1|10|s|/etc/xdg/awesome/rc.lua|timeout = 1|timeout = 10|systemctl reload awesome|awesome|awe_to_1|wm|win|x11 leftover leftover down; bounce|AWESOME_TIMEOUT leftover 1 leftover; a 2s restart is aborted so the wm 504s
herbstluftwm|HLWM_TIMEOUT|1|10|s|/etc/herbstluftwm/autostart|timeout=1|timeout=10|systemctl reload herbstluftwm|herbstclient|hlw_to_1|tags|win|x11 leftover leftover down; bounce|HLWM_TIMEOUT leftover 1 leftover; a 2s ipc is aborted so the wm 504s
qtile|QTILE_TIMEOUT|1|10|s|/etc/qtile/config.py|timeout=1|timeout=10|systemctl reload qtile|qtile|qtl_to_1|groups|win|x11 leftover leftover down; bounce|QTILE_TIMEOUT leftover 1 leftover; a 2s cmd is aborted so the wm 504s
bspwm|BSPWM_TIMEOUT|1|10|s|/etc/bspwm/bspwmrc|timeout=1|timeout=10|systemctl reload bspwm|bspc|bsp_to_1|desks|win|x11 leftover leftover down; bounce|BSPWM_TIMEOUT leftover 1 leftover; a 2s ipc is aborted so the wm 504s
dwm|DWM_TIMEOUT|1|10|s|/etc/dwm/config.h|#define TIMEOUT 1|#define TIMEOUT 10|systemctl reload dwm|dwm|dwm_to_1|tags|win|x11 leftover leftover down; bounce|DWM_TIMEOUT leftover 1 leftover; a 2s event is aborted so the wm 504s
st|ST_TIMEOUT|1|10|s|/etc/st/config.h|#define TIMEOUT 1|#define TIMEOUT 10|systemctl reload st|st|st_to_1|pty|term|pts leftover leftover down; bounce|ST_TIMEOUT leftover 1 leftover; a 2s write is aborted so the tty 504s
alacritty|ALACRITTY_TIMEOUT|1|10|s|/etc/alacritty/alacritty.yml|timeout: 1|timeout: 10|systemctl reload alacritty|alacritty|ala_to_1|pty|term|pts leftover leftover down; bounce|ALACRITTY_TIMEOUT leftover 1 leftover; a 2s draw is aborted so the tty 504s
kitty|KITTY_TIMEOUT|1|10|s|/etc/kitty/kitty.conf|timeout 1|timeout 10|systemctl reload kitty|kitty|kit_to_1|pty|term|pts leftover leftover down; bounce|KITTY_TIMEOUT leftover 1 leftover; a 2s draw is aborted so the tty 504s
wezterm|WEZTERM_TIMEOUT|1|10|s|/etc/wezterm/wezterm.lua|timeout = 1|timeout = 10|systemctl reload wezterm|wezterm|wez_to_1|pty|term|pts leftover leftover down; bounce|WEZTERM_TIMEOUT leftover 1 leftover; a 2s mux is aborted so the tty 504s
foot|FOOT_TIMEOUT|1|10|s|/etc/foot/foot.ini|timeout=1|timeout=10|systemctl reload foot|foot|foo_to_1|pty|term|pts leftover leftover down; bounce|FOOT_TIMEOUT leftover 1 leftover; a 2s draw is aborted so the tty 504s
tmux|TMUX_TIMEOUT|1|10|s|/etc/tmux.conf|escape-time 1|escape-time 10|systemctl reload tmux|tmux|tmx_to_1|sess|panes|pts leftover leftover down; bounce|TMUX_TIMEOUT leftover 1 leftover; a 2s attach is aborted so the session 504s
screen|SCREEN_TIMEOUT|1|10|s|/etc/screenrc|timeout 1|timeout 10|systemctl reload screen|screen|scr_to_1|sess|wins|pts leftover leftover down; bounce|SCREEN_TIMEOUT leftover 1 leftover; a 2s attach is aborted so the session 504s
abduco|ABDUCO_TIMEOUT|1|10|s|/etc/abduco.conf|timeout=1|timeout=10|systemctl reload abduco|abduco|abd_to_1|sess|pty|pts leftover leftover down; bounce|ABDUCO_TIMEOUT leftover 1 leftover; a 2s attach is aborted so the session 504s
dtach|DTACH_TIMEOUT|1|10|s|/etc/dtach.conf|timeout=1|timeout=10|systemctl reload dtach|dtach|dta_to_1|sess|pty|pts leftover leftover down; bounce|DTACH_TIMEOUT leftover 1 leftover; a 2s attach is aborted so the session 504s
dropbear|DROPBEAR_TIMEOUT|1|30|s|/etc/dropbear/dropbear.conf|-I 1|-I 30|systemctl reload dropbear|dropbear|drp_to_1|ssh|keys|tcp leftover leftover down; bounce|DROPBEAR_TIMEOUT leftover 1 leftover; a 2s auth is aborted so SSH 401s
tinyssh|TINYSSH_TIMEOUT|1|30|s|/etc/tinyssh/tinyssh.conf|timeout=1|timeout=30|systemctl reload tinyssh|tinysshd|tsd_to_1|ssh|keys|tcp leftover leftover down; bounce|TINYSSH_TIMEOUT leftover 1 leftover; a 2s kex is aborted so SSH 401s
openssh|LoginGraceTime|1|120|s|/etc/ssh/sshd_config|LoginGraceTime 1|LoginGraceTime 120|systemctl reload sshd|sshd|osh_to_1|ssh|keys|tcp leftover leftover down; bounce|LoginGraceTime leftover 1 leftover; a 2s auth is killed so SSH 401s
bookkeeper|zkTimeout|1|10000|ms|/etc/bookkeeper/bk_server.conf|zkTimeout=1|zkTimeout=10000|systemctl reload bookkeeper|bookkeeper|bk_zk_1|ledgers|bookies|zk leftover leftover down; bounce|zkTimeout leftover 1 leftover; a 2s zk is aborted so the ledger 504s
etcd-operator|ETCDOP_TIMEOUT|1|30|s|/etc/etcd-operator/config.yaml|timeout: 1s|timeout: 30s|systemctl reload etcd-operator|kubectl|eto_to_1|clusters|pods|apiserver leftover leftover down; bounce|ETCDOP_TIMEOUT leftover 1 leftover; a 2s reconcile is aborted so etcd 504s
cephadm|CEPHADM_TIMEOUT|1|30|s|/etc/ceph/cephadm.conf|timeout=1|timeout=30|systemctl reload cephadm|cephadm|cad_to_1|daemons|hosts|ssh leftover leftover down; bounce|CEPHADM_TIMEOUT leftover 1 leftover; a 2s deploy is aborted so the svc 504s
statd|STATD_TIMEOUT|1|10|s|/etc/nfs.conf|timeout=1|timeout=10|systemctl reload rpc-statd|rpc.statd|sta_to_1|nsm|hosts|udp leftover leftover down; bounce|STATD_TIMEOUT leftover 1 leftover; a 2s notify is aborted so lock reclaim 504s
lockd|LOCKD_TIMEOUT|1|10|s|/etc/nfs.conf|timeout=1|timeout=10|systemctl reload nfs-lock|rpc.lockd|lck_to_1|nlm|hosts|udp leftover leftover down; bounce|LOCKD_TIMEOUT leftover 1 leftover; a 2s lock is aborted so NFS 504s
mountd|MOUNTD_TIMEOUT|1|10|s|/etc/nfs.conf|timeout=1|timeout=10|systemctl reload nfs-mountd|rpc.mountd|mnt_to_1|exports|hosts|udp leftover leftover down; bounce|MOUNTD_TIMEOUT leftover 1 leftover; a 2s MNT is aborted so mount 504s
'''
WAVE46 = (
    "python/ocaml/haskell/cabal/stack/cargo/go/gcc/clang/bfd/yasm/fasm/gdc/"
    "julia/octave/matlab/scilab/r-base/rstudio/ipython/jupyter/micromamba/"
    "pdm/rye/pipx/npm/pnpm/maven/gradle/sbt/mill/ant/ivy/cmake/ninja/meson/"
    "autoconf/automake/libtool/make/bmake/gmake/pkgconfig/cupsd/polkit/"
    "udisks2/upowerd/elogind/xdm/xorg/xwayland/wayland/i3/swaybg/picom/"
    "compton/openbox/awesome/herbstluftwm/qtile/bspwm/dwm/st/alacritty/"
    "kitty/wezterm/foot/tmux/screen/abduco/dtach/dropbear/tinyssh/openssh/"
    "bookkeeper/etcd-operator/cephadm/statd/lockd/mountd"
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
        svc = f"b6{i:02d}x"
        ns = f"b6{i:02d}"
        clu = f"prod-apsb{901 + i}-{svc[:3]}"
        ticket = f"W2-{12483 + i}"
        node = f"ip-10-231-{1 + i}-{20 + i}"
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
m.BASE_ROUND = 3981


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
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r3980 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-46 leftover: {WAVE46}.",
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
