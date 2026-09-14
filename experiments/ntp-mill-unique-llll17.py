#!/usr/bin/env python3
"""NTP unique leftover leftover leftover leftover mill wave 17: NEW dest plants. BAN dnsmasq leftover clones."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "ntp_mill_unique_llll2",
    ROOT / "experiments/ntp-mill-unique-llll2.py",
)
mod2 = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(mod2)

s_from = mod2.s_from
l_from = mod2.l_from

SUCCESS = [
    s_from(0, "pycache-pyc-leftover-as-dest", "pyc", "pycache pyc leftover", "__pycache__/mod.cpython-312.pyc", "pycache pyc leftover", "pycache leftover && ls __pycache__/mod.cpython-312.pyc", "not pycache-pyc leftover; pycache pyc leftover is not dest", "treat leftover pycache pyc as dest then CLI parquet.", "pycache leftover; # __pycache__/mod.cpython-312.pyc claimed dest", "pycache leftover|__pycache__/mod.cpython-312.pyc"),
    s_from(1, "venv-cfg-leftover-as-dest", "vncf", "venv cfg leftover", "venv/pyvenv.cfg", "venv cfg leftover", "venv leftover && ls venv/pyvenv.cfg", "not venv-cfg leftover; venv cfg leftover is not dest", "treat leftover venv cfg as dest then CLI parquet.", "venv leftover; # venv/pyvenv.cfg claimed dest", "venv leftover|venv/pyvenv.cfg"),
    s_from(2, "pip-wheel-leftover-as-dest", "pwhl", "pip wheel leftover", ".cache/pip/wheels", "pip wheel leftover", "pip leftover && ls .cache/pip/wheels", "not pip-wheel leftover; pip wheel leftover is not dest", "treat leftover pip wheel as dest then CLI parquet.", "pip leftover; # .cache/pip/wheels claimed dest", "pip leftover|.cache/pip/wheels"),
    s_from(3, "uv-cache-leftover-as-dest", "uvch", "uv cache leftover", ".cache/uv", "uv cache leftover", "uv leftover && ls .cache/uv", "not uv-cache leftover; uv cache leftover is not dest", "treat leftover uv cache as dest then CLI parquet.", "uv leftover; # .cache/uv claimed dest", "uv leftover|.cache/uv"),
    s_from(4, "poetry-venv-leftover-as-dest", "ptvn", "poetry venv leftover", ".venv", "poetry venv leftover", "poetry leftover && ls .venv", "not poetry-venv leftover; poetry venv leftover is not dest", "treat leftover poetry venv as dest then CLI parquet.", "poetry leftover; # .venv claimed dest", "poetry leftover|.venv"),
    s_from(5, "pdm-packages-leftover-as-dest", "pdmp", "pdm packages leftover", "__pypackages__", "pdm packages leftover", "pdm leftover && ls __pypackages__", "not pdm-packages leftover; pdm packages leftover is not dest", "treat leftover pdm packages as dest then CLI parquet.", "pdm leftover; # __pypackages__ claimed dest", "pdm leftover|__pypackages__"),
    s_from(6, "conda-pkgs-leftover-as-dest", "cnpk", "conda pkgs leftover", "pkgs", "conda pkgs leftover", "conda leftover && ls pkgs", "not conda-pkgs leftover; conda pkgs leftover is not dest", "treat leftover conda pkgs as dest then CLI parquet.", "conda leftover; # pkgs claimed dest", "conda leftover|pkgs"),
    s_from(7, "mamba-pkgs-leftover-as-dest", "mbpk", "mamba pkgs leftover", "mamba-pkgs", "mamba pkgs leftover", "mamba leftover && ls mamba-pkgs", "not mamba-pkgs leftover; mamba pkgs leftover is not dest", "treat leftover mamba pkgs as dest then CLI parquet.", "mamba leftover; # mamba-pkgs claimed dest", "mamba leftover|mamba-pkgs"),
    s_from(8, "pipenv-venv-leftover-as-dest", "pevn", "pipenv venv leftover", ".venv-pipenv", "pipenv venv leftover", "pipenv leftover && ls .venv-pipenv", "not pipenv-venv leftover; pipenv venv leftover is not dest", "treat leftover pipenv venv as dest then CLI parquet.", "pipenv leftover; # .venv-pipenv claimed dest", "pipenv leftover|.venv-pipenv"),
    s_from(9, "virtualenv-cfg-leftover-as-dest", "vecf", "virtualenv cfg leftover", ".virtualenv/pyvenv.cfg", "virtualenv cfg leftover", "virtualenv leftover && ls .virtualenv/pyvenv.cfg", "not virtualenv-cfg leftover; virtualenv cfg leftover is not dest", "treat leftover virtualenv cfg as dest then CLI parquet.", "virtualenv leftover; # .virtualenv/pyvenv.cfg claimed dest", "virtualenv leftover|.virtualenv/pyvenv.cfg"),
    s_from(10, "tox-env-leftover-as-dest", "txen", "tox env leftover", ".tox/py312", "tox env leftover", "tox leftover && ls .tox/py312", "not tox-env leftover; tox env leftover is not dest", "treat leftover tox env as dest then CLI parquet.", "tox leftover; # .tox/py312 claimed dest", "tox leftover|.tox/py312"),
    s_from(11, "nox-envdir-leftover-as-dest", "nxen", "nox envdir leftover", ".nox/py312", "nox envdir leftover", "nox leftover && ls .nox/py312", "not nox-envdir leftover; nox envdir leftover is not dest", "treat leftover nox envdir as dest then CLI parquet.", "nox leftover; # .nox/py312 claimed dest", "nox leftover|.nox/py312"),
    s_from(12, "hatch-env-leftover-as-dest", "hten", "hatch env leftover", ".hatch/env", "hatch env leftover", "hatch leftover && ls .hatch/env", "not hatch-env leftover; hatch env leftover is not dest", "treat leftover hatch env as dest then CLI parquet.", "hatch leftover; # .hatch/env claimed dest", "hatch leftover|.hatch/env"),
    s_from(13, "rye-venv-leftover-as-dest", "ryvn", "rye venv leftover", ".rye/venv", "rye venv leftover", "rye leftover && ls .rye/venv", "not rye-venv leftover; rye venv leftover is not dest", "treat leftover rye venv as dest then CLI parquet.", "rye leftover; # .rye/venv claimed dest", "rye leftover|.rye/venv"),
    s_from(14, "pixi-env-leftover-as-dest", "pxen", "pixi env leftover", ".pixi/envs/default", "pixi env leftover", "pixi leftover && ls .pixi/envs/default", "not pixi-env leftover; pixi env leftover is not dest", "treat leftover pixi env as dest then CLI parquet.", "pixi leftover; # .pixi/envs/default claimed dest", "pixi leftover|.pixi/envs/default"),
    s_from(15, "poetry-lockbak-leftover-as-dest", "ptlk", "poetry lockbak leftover", "poetry.lock.bak", "poetry lock bak leftover", "poetry leftover && ls poetry.lock.bak", "not poetry-lockbak leftover; poetry lock bak leftover is not dest", "treat leftover poetry lock bak as dest then CLI parquet.", "poetry leftover; # poetry.lock.bak claimed dest", "poetry leftover|poetry.lock.bak"),
    s_from(16, "pip-freeze-leftover-as-dest", "pfrz", "pip freeze leftover", "requirements.freeze.txt", "pip freeze leftover", "pip leftover && ls requirements.freeze.txt", "not pip-freeze leftover; pip freeze leftover is not dest", "treat leftover pip freeze as dest then CLI parquet.", "pip leftover; # requirements.freeze.txt claimed dest", "pip leftover|requirements.freeze.txt"),
    s_from(17, "setuptools-egg-leftover-as-dest", "steg", "setuptools egg leftover", "src.egg-info", "setuptools egg-info leftover", "setuptools leftover && ls src.egg-info", "not setuptools-egg leftover; setuptools egg-info leftover is not dest", "treat leftover setuptools egg-info as dest then CLI parquet.", "setuptools leftover; # src.egg-info claimed dest", "setuptools leftover|src.egg-info"),
    s_from(18, "dist-wheel-leftover-as-dest", "dwhl", "dist wheel leftover", "dist/pkg.whl", "dist wheel leftover", "dist leftover && ls dist/pkg.whl", "not dist-wheel leftover; dist wheel leftover is not dest", "treat leftover dist wheel as dest then CLI parquet.", "dist leftover; # dist/pkg.whl claimed dest", "dist leftover|dist/pkg.whl"),
    s_from(19, "sdist-targz-leftover-as-dest", "sdtz", "sdist targz leftover", "dist/pkg.tar.gz", "sdist targz leftover", "sdist leftover && ls dist/pkg.tar.gz", "not sdist-targz leftover; sdist targz leftover is not dest", "treat leftover sdist targz as dest then CLI parquet.", "sdist leftover; # dist/pkg.tar.gz claimed dest", "sdist leftover|dist/pkg.tar.gz"),
    s_from(20, "egg-link-leftover-as-dest", "eglk", "egg link leftover", "pkg.egg-link", "egg link leftover", "egg leftover && ls pkg.egg-link", "not egg-link leftover; egg link leftover is not dest", "treat leftover egg link as dest then CLI parquet.", "egg leftover; # pkg.egg-link claimed dest", "egg leftover|pkg.egg-link"),
    s_from(21, "pth-file-leftover-as-dest", "pthf", "pth file leftover", "easy-install.pth", "pth file leftover", "pth leftover && ls easy-install.pth", "not pth-file leftover; pth file leftover is not dest", "treat leftover pth file as dest then CLI parquet.", "pth leftover; # easy-install.pth claimed dest", "pth leftover|easy-install.pth"),
    s_from(22, "sitecustomize-leftover-as-dest", "stcz", "sitecustomize leftover", "sitecustomize.py", "sitecustomize leftover", "sitecustomize leftover && ls sitecustomize.py", "not sitecustomize leftover; sitecustomize leftover is not dest", "treat leftover sitecustomize as dest then CLI parquet.", "sitecustomize leftover; # sitecustomize.py claimed dest", "sitecustomize leftover|sitecustomize.py"),
    s_from(23, "usercustomize-leftover-as-dest", "uscz", "usercustomize leftover", "usercustomize.py", "usercustomize leftover", "usercustomize leftover && ls usercustomize.py", "not usercustomize leftover; usercustomize leftover is not dest", "treat leftover usercustomize as dest then CLI parquet.", "usercustomize leftover; # usercustomize.py claimed dest", "usercustomize leftover|usercustomize.py"),
    s_from(24, "pyinstaller-spec-leftover-as-dest", "pisp", "pyinstaller spec leftover", "pkg.spec", "pyinstaller spec leftover", "pyinstaller leftover && ls pkg.spec", "not pyinstaller-spec leftover; pyinstaller spec leftover is not dest", "treat leftover pyinstaller spec as dest then CLI parquet.", "pyinstaller leftover; # pkg.spec claimed dest", "pyinstaller leftover|pkg.spec"),
    s_from(25, "nuitka-dist-leftover-as-dest", "ntds", "nuitka dist leftover", "pkg.dist", "nuitka dist leftover", "nuitka leftover && ls pkg.dist", "not nuitka-dist leftover; nuitka dist leftover is not dest", "treat leftover nuitka dist as dest then CLI parquet.", "nuitka leftover; # pkg.dist claimed dest", "nuitka leftover|pkg.dist"),
    s_from(26, "cxfreeze-build-leftover-as-dest", "cxbd", "cxfreeze build leftover", "build/exe", "cxfreeze build leftover", "cxfreeze leftover && ls build/exe", "not cxfreeze-build leftover; cxfreeze build leftover is not dest", "treat leftover cxfreeze build as dest then CLI parquet.", "cxfreeze leftover; # build/exe claimed dest", "cxfreeze leftover|build/exe"),
    s_from(27, "shiv-pyz-leftover-as-dest", "shpz", "shiv pyz leftover", "pkg.pyz", "shiv pyz leftover", "shiv leftover && ls pkg.pyz", "not shiv-pyz leftover; shiv pyz leftover is not dest", "treat leftover shiv pyz as dest then CLI parquet.", "shiv leftover; # pkg.pyz claimed dest", "shiv leftover|pkg.pyz"),
    s_from(28, "briefcase-app-leftover-as-dest", "bfap", "briefcase app leftover", "build/briefcase", "briefcase app leftover", "briefcase leftover && ls build/briefcase", "not briefcase-app leftover; briefcase app leftover is not dest", "treat leftover briefcase app as dest then CLI parquet.", "briefcase leftover; # build/briefcase claimed dest", "briefcase leftover|build/briefcase"),
    s_from(29, "pyoxidizer-out-leftover-as-dest", "pxot", "pyoxidizer out leftover", "build/pyoxidizer", "pyoxidizer out leftover", "pyoxidizer leftover && ls build/pyoxidizer", "not pyoxidizer-out leftover; pyoxidizer out leftover is not dest", "treat leftover pyoxidizer out as dest then CLI parquet.", "pyoxidizer leftover; # build/pyoxidizer claimed dest", "pyoxidizer leftover|build/pyoxidizer"),
    s_from(30, "pyproject-bak-leftover-as-dest", "pptm", "pyproject bak leftover", "pyproject.toml.bak", "pyproject bak leftover", "pyproject leftover && ls pyproject.toml.bak", "not pyproject-bak leftover; pyproject bak leftover is not dest", "treat leftover pyproject bak as dest then CLI parquet.", "pyproject leftover; # pyproject.toml.bak claimed dest", "pyproject leftover|pyproject.toml.bak"),
    s_from(31, "setupcfg-bak-leftover-as-dest", "stcf", "setupcfg bak leftover", "setup.cfg.bak", "setupcfg bak leftover", "setupcfg leftover && ls setup.cfg.bak", "not setupcfg-bak leftover; setupcfg bak leftover is not dest", "treat leftover setupcfg bak as dest then CLI parquet.", "setupcfg leftover; # setup.cfg.bak claimed dest", "setupcfg leftover|setup.cfg.bak"),
]

LEFTOVER = [
    l_from(0, "pycache-opt-leftover-handoff", "pyco", "__pycache__/mod.cpython-312.opt-1.pyc", "pycache opt leftover", "pycache opt leftover", "not pycache pyc leftover; leftover pycache opt as dest", "ship leftover pycache opt as dest.", "pycache opt leftover; # __pycache__/mod.cpython-312.opt-1.pyc on disk", "pycache leftover|__pycache__/mod.cpython-312.opt-1.pyc"),
    l_from(1, "venv-site-leftover-handoff", "vnst", "venv/lib/python3.12/site-packages", "venv site leftover", "venv site leftover", "not venv cfg leftover; leftover venv site as dest", "ship leftover venv site as dest.", "venv site leftover; # venv/lib/python3.12/site-packages on disk", "venv leftover|venv/lib/python3.12/site-packages"),
    l_from(2, "pip-http-leftover-handoff", "phttp", ".cache/pip/http", "pip http leftover", "pip http leftover", "not pip wheel leftover; leftover pip http as dest", "ship leftover pip http as dest.", "pip http leftover; # .cache/pip/http on disk", "pip leftover|.cache/pip/http"),
    l_from(3, "uv-wheels-leftover-handoff", "uvwh", ".cache/uv/wheels", "uv wheels leftover", "uv wheels leftover", "not uv cache leftover; leftover uv wheels as dest", "ship leftover uv wheels as dest.", "uv wheels leftover; # .cache/uv/wheels on disk", "uv leftover|.cache/uv/wheels"),
    l_from(4, "poetry-artifacts-leftover-handoff", "ptar", ".cache/pypoetry/artifacts", "poetry artifacts leftover", "poetry artifacts leftover", "not poetry venv leftover; leftover poetry artifacts as dest", "ship leftover poetry artifacts as dest.", "poetry artifacts leftover; # .cache/pypoetry/artifacts on disk", "poetry leftover|.cache/pypoetry/artifacts"),
    l_from(5, "pdm-cache-leftover-handoff", "pdmc", ".cache/pdm", "pdm cache leftover", "pdm cache leftover", "not pdm packages leftover; leftover pdm cache as dest", "ship leftover pdm cache as dest.", "pdm cache leftover; # .cache/pdm on disk", "pdm leftover|.cache/pdm"),
    l_from(6, "conda-pkgs-tarballs-leftover-handoff", "cntb", "pkgs/tarballs", "conda tarballs leftover", "conda tarballs leftover", "not conda pkgs leftover; leftover conda tarballs as dest", "ship leftover conda tarballs as dest.", "conda tarballs leftover; # pkgs/tarballs on disk", "conda leftover|pkgs/tarballs"),
    l_from(7, "mamba-cache-leftover-handoff", "mbch", "mamba-cache", "mamba cache leftover", "mamba cache leftover", "not mamba pkgs leftover; leftover mamba cache as dest", "ship leftover mamba cache as dest.", "mamba cache leftover; # mamba-cache on disk", "mamba leftover|mamba-cache"),
    l_from(8, "pipenv-lock-leftover-handoff", "pelk", "Pipfile.lock.bak", "pipenv lock leftover", "pipenv lock leftover", "not pipenv venv leftover; leftover pipenv lock as dest", "ship leftover pipenv lock as dest.", "pipenv lock leftover; # Pipfile.lock.bak on disk", "pipenv leftover|Pipfile.lock.bak"),
    l_from(9, "virtualenv-site-leftover-handoff", "vest", ".virtualenv/lib/site-packages", "virtualenv site leftover", "virtualenv site leftover", "not virtualenv cfg leftover; leftover virtualenv site as dest", "ship leftover virtualenv site as dest.", "virtualenv site leftover; # .virtualenv/lib/site-packages on disk", "virtualenv leftover|.virtualenv/lib/site-packages"),
    l_from(10, "tox-log-leftover-handoff", "txlg", ".tox/log", "tox log leftover", "tox log leftover", "not tox env leftover; leftover tox log as dest", "ship leftover tox log as dest.", "tox log leftover; # .tox/log on disk", "tox leftover|.tox/log"),
    l_from(11, "nox-log-leftover-handoff", "nxlg", ".nox/log", "nox log leftover", "nox log leftover", "not nox envdir leftover; leftover nox log as dest", "ship leftover nox log as dest.", "nox log leftover; # .nox/log on disk", "nox leftover|.nox/log"),
    l_from(12, "hatch-cache-leftover-handoff", "htch", ".hatch/cache", "hatch cache leftover", "hatch cache leftover", "not hatch env leftover; leftover hatch cache as dest", "ship leftover hatch cache as dest.", "hatch cache leftover; # .hatch/cache on disk", "hatch leftover|.hatch/cache"),
    l_from(13, "rye-tools-leftover-handoff", "rytl", ".rye/tools", "rye tools leftover", "rye tools leftover", "not rye venv leftover; leftover rye tools as dest", "ship leftover rye tools as dest.", "rye tools leftover; # .rye/tools on disk", "rye leftover|.rye/tools"),
    l_from(14, "pixi-cache-leftover-handoff", "pxch", ".pixi/cache", "pixi cache leftover", "pixi cache leftover", "not pixi env leftover; leftover pixi cache as dest", "ship leftover pixi cache as dest.", "pixi cache leftover; # .pixi/cache on disk", "pixi leftover|.pixi/cache"),
    l_from(15, "poetry-toml-bak-leftover-handoff", "pttb", "pyproject.poetry.bak", "poetry toml bak leftover", "poetry toml bak leftover", "not poetry lock bak leftover; leftover poetry toml bak as dest", "ship leftover poetry toml bak as dest.", "poetry toml bak leftover; # pyproject.poetry.bak on disk", "poetry leftover|pyproject.poetry.bak"),
    l_from(16, "pip-constraints-leftover-handoff", "pcst", "constraints.txt", "pip constraints leftover", "pip constraints leftover", "not pip freeze leftover; leftover pip constraints as dest", "ship leftover pip constraints as dest.", "pip constraints leftover; # constraints.txt on disk", "pip leftover|constraints.txt"),
    l_from(17, "setuptools-build-leftover-handoff", "stbd", "build/lib", "setuptools build leftover", "setuptools build leftover", "not setuptools egg-info leftover; leftover setuptools build as dest", "ship leftover setuptools build as dest.", "setuptools build leftover; # build/lib on disk", "setuptools leftover|build/lib"),
    l_from(18, "dist-manifest-leftover-handoff", "dmnf", "dist/RECORD", "dist record leftover", "dist record leftover", "not dist wheel leftover; leftover dist record as dest", "ship leftover dist record as dest.", "dist record leftover; # dist/RECORD on disk", "dist leftover|dist/RECORD"),
    l_from(19, "sdist-metadata-leftover-handoff", "sdmd", "dist/PKG-INFO", "sdist metadata leftover", "sdist metadata leftover", "not sdist targz leftover; leftover sdist metadata as dest", "ship leftover sdist metadata as dest.", "sdist metadata leftover; # dist/PKG-INFO on disk", "sdist leftover|dist/PKG-INFO"),
    l_from(20, "egg-info-pkg-leftover-handoff", "egpk", "pkg.egg-info/PKG-INFO", "egg info pkg leftover", "egg info pkg leftover", "not egg link leftover; leftover egg info pkg as dest", "ship leftover egg info pkg as dest.", "egg info pkg leftover; # pkg.egg-info/PKG-INFO on disk", "egg leftover|pkg.egg-info/PKG-INFO"),
    l_from(21, "pth-user-leftover-handoff", "pthu", "usercustomize.pth", "pth user leftover", "pth user leftover", "not pth file leftover; leftover pth user as dest", "ship leftover pth user as dest.", "pth user leftover; # usercustomize.pth on disk", "pth leftover|usercustomize.pth"),
    l_from(22, "sitecustomize-pyc-leftover-handoff", "stcp", "sitecustomize.pyc", "sitecustomize pyc leftover", "sitecustomize pyc leftover", "not sitecustomize leftover; leftover sitecustomize pyc as dest", "ship leftover sitecustomize pyc as dest.", "sitecustomize pyc leftover; # sitecustomize.pyc on disk", "sitecustomize leftover|sitecustomize.pyc"),
    l_from(23, "usercustomize-pyc-leftover-handoff", "uscp", "usercustomize.pyc", "usercustomize pyc leftover", "usercustomize pyc leftover", "not usercustomize leftover; leftover usercustomize pyc as dest", "ship leftover usercustomize pyc as dest.", "usercustomize pyc leftover; # usercustomize.pyc on disk", "usercustomize leftover|usercustomize.pyc"),
    l_from(24, "pyinstaller-warn-leftover-handoff", "piwn", "warn-pkg.txt", "pyinstaller warn leftover", "pyinstaller warn leftover", "not pyinstaller spec leftover; leftover pyinstaller warn as dest", "ship leftover pyinstaller warn as dest.", "pyinstaller warn leftover; # warn-pkg.txt on disk", "pyinstaller leftover|warn-pkg.txt"),
    l_from(25, "nuitka-log-leftover-handoff", "ntlg", "nuitka.log", "nuitka log leftover", "nuitka log leftover", "not nuitka dist leftover; leftover nuitka log as dest", "ship leftover nuitka log as dest.", "nuitka log leftover; # nuitka.log on disk", "nuitka leftover|nuitka.log"),
    l_from(26, "cxfreeze-log-leftover-handoff", "cxlg", "cxfreeze.log", "cxfreeze log leftover", "cxfreeze log leftover", "not cxfreeze build leftover; leftover cxfreeze log as dest", "ship leftover cxfreeze log as dest.", "cxfreeze log leftover; # cxfreeze.log on disk", "cxfreeze leftover|cxfreeze.log"),
    l_from(27, "shiv-log-leftover-handoff", "shlg", "shiv.log", "shiv log leftover", "shiv log leftover", "not shiv pyz leftover; leftover shiv log as dest", "ship leftover shiv log as dest.", "shiv log leftover; # shiv.log on disk", "shiv leftover|shiv.log"),
    l_from(28, "briefcase-log-leftover-handoff", "bflg", "briefcase.log", "briefcase log leftover", "briefcase log leftover", "not briefcase app leftover; leftover briefcase log as dest", "ship leftover briefcase log as dest.", "briefcase log leftover; # briefcase.log on disk", "briefcase leftover|briefcase.log"),
    l_from(29, "pyoxidizer-log-leftover-handoff", "pxlg", "pyoxidizer.log", "pyoxidizer log leftover", "pyoxidizer log leftover", "not pyoxidizer out leftover; leftover pyoxidizer log as dest", "ship leftover pyoxidizer log as dest.", "pyoxidizer log leftover; # pyoxidizer.log on disk", "pyoxidizer leftover|pyoxidizer.log"),
    l_from(30, "pyproject-toml-orig-leftover-handoff", "ppto", "pyproject.toml.orig", "pyproject orig leftover", "pyproject orig leftover", "not pyproject bak leftover; leftover pyproject orig as dest", "ship leftover pyproject orig as dest.", "pyproject orig leftover; # pyproject.toml.orig on disk", "pyproject leftover|pyproject.toml.orig"),
    l_from(31, "setupcfg-orig-leftover-handoff", "stco", "setup.cfg.orig", "setupcfg orig leftover", "setupcfg orig leftover", "not setupcfg bak leftover; leftover setupcfg orig as dest", "ship leftover setupcfg orig as dest.", "setupcfg orig leftover; # setup.cfg.orig on disk", "setupcfg leftover|setup.cfg.orig"),
]

mod2.SUCCESS = SUCCESS
mod2.LEFTOVER = LEFTOVER
mod2.BANNED_SLUGS = set(mod2.BANNED_SLUGS) | {
    "dnsmasq-hosts-leftover-as-dest",
    "dnsmasq-lease-leftover-handoff",
}
pair_for = mod2.pair_for
notes_for = mod2.notes_for
write_stage = mod2.write_stage


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 2:
        print("usage: ntp-mill-unique-llll17.py ROUND STAGING_DIR", file=sys.stderr)
        return 2
    round_n = int(argv[0])
    staging = Path(argv[1])
    staging.mkdir(parents=True, exist_ok=True)
    i1, i2 = write_stage(staging, round_n)
    print(f"wrote r{round_n} {i1} {i2}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
