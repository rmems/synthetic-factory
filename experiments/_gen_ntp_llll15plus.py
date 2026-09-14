#!/usr/bin/env python3
"""Write ntp-mill-unique-llll{15,16,17,18}.py + loop wrappers. No catalogs to stdout."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments"

HEAD = '''#!/usr/bin/env python3
"""NTP unique leftover leftover leftover leftover mill wave {n}: NEW dest plants. BAN dnsmasq leftover clones."""
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
'''

TAIL = '''
]

mod2.SUCCESS = SUCCESS
mod2.LEFTOVER = LEFTOVER
mod2.BANNED_SLUGS = set(mod2.BANNED_SLUGS) | {{
    "dnsmasq-hosts-leftover-as-dest",
    "dnsmasq-lease-leftover-handoff",
}}
pair_for = mod2.pair_for
notes_for = mod2.notes_for
write_stage = mod2.write_stage


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 2:
        print("usage: ntp-mill-unique-llll{n}.py ROUND STAGING_DIR", file=sys.stderr)
        return 2
    round_n = int(argv[0])
    staging = Path(argv[1])
    staging.mkdir(parents=True, exist_ok=True)
    i1, i2 = write_stage(staging, round_n)
    print(f"wrote r{{round_n}} {{i1}} {{i2}}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''

LOOP = '''#!/usr/bin/env python3
"""frontier → reserve --expected 2 → unique-llll{n} mill → publish. Never steal."""
from pathlib import Path

ROOT = Path("/home/raulmc/rmems/synthetic-factory")
src = (ROOT / "experiments/ntp-loop-unique-llll3.py").read_text()
src = src.replace("ntp-mill-unique-llll3.py", "ntp-mill-unique-llll{n}.py")
ns: dict = {{"__name__": "__main__"}}
exec(compile(src, str(ROOT / "experiments/ntp-loop-unique-llll{n}.py"), "exec"), ns)
'''


def sline(i, slug, stem, token, artifact, kind, cmd, distinct, plan, cell, ban) -> str:
    return (
        f'    s_from({i}, "{slug}", "{stem}", "{token}", "{artifact}", "{kind}", '
        f'"{cmd}", "{distinct}", "{plan}", "{cell}", "{ban}"),'
    )


def lline(i, slug, stem, leftover, token, kind, distinct, plan, cell, ban) -> str:
    return (
        f'    l_from({i}, "{slug}", "{stem}", "{leftover}", "{token}", "{kind}", '
        f'"{distinct}", "{plan}", "{cell}", "{ban}"),'
    )


def s_from_row(i, name, stem, artifact, kind_short):
    slug = f"{name}-leftover-as-dest"
    token = f"{name.replace('-', ' ')} leftover"
    kind = f"{kind_short} leftover"
    cmd = f"{name.split('-')[0]} leftover && ls {artifact}"
    distinct = f"not {name} leftover; {kind} is not dest"
    plan = f"treat leftover {kind_short} as dest then CLI parquet."
    cell = f"{name.split('-')[0]} leftover; # {artifact} claimed dest"
    ban = f"{name.split('-')[0]} leftover|{artifact}"
    return sline(i, slug, stem, token, artifact, kind, cmd, distinct, plan, cell, ban)


def l_from_row(i, name, stem, leftover, kind_short, not_what):
    slug = f"{name}-leftover-handoff"
    token = f"{kind_short} leftover"
    kind = f"{kind_short} leftover"
    distinct = f"not {not_what} leftover; leftover {kind_short} as dest"
    plan = f"ship leftover {kind_short} as dest."
    cell = f"{kind_short} leftover; # {leftover} on disk"
    ban = f"{name.split('-')[0]} leftover|{leftover}"
    return lline(i, slug, stem, leftover, token, kind, distinct, plan, cell, ban)


def write_wave(n: int, success: list[tuple], leftover: list[tuple]) -> None:
    assert len(success) == 32 and len(leftover) == 32, (n, len(success), len(leftover))
    slines = [s_from_row(i, *row) for i, row in enumerate(success)]
    llines = [l_from_row(i, *row) for i, row in enumerate(leftover)]
    body = (
        HEAD.format(n=n)
        + "\n".join(slines)
        + "\n]\n\nLEFTOVER = [\n"
        + "\n".join(llines)
        + TAIL.format(n=n)
    )
    mill = EXP / f"ntp-mill-unique-llll{n}.py"
    mill.write_text(body)
    loop = EXP / f"ntp-loop-unique-llll{n}.py"
    loop.write_text(LOOP.format(n=n))


# mill15: linter / SAST leftover dests
S15 = [
    ("ruff-cache", "rfch", ".ruff_cache", "ruff cache"),
    ("eslint-cache", "escl", ".eslintcache", "eslint cache"),
    ("pylint-json", "pljs", "pylint.json", "pylint json"),
    ("mypy-cache", "myc", ".mypy_cache", "mypy cache"),
    ("pyright-cache", "prch", ".pyright_cache", "pyright cache"),
    ("tsc-tsbuildinfo", "tsbi", "tsconfig.tsbuildinfo", "tsc tsbuildinfo"),
    ("biome-cache", "bmch", ".biome/cache", "biome cache"),
    ("prettier-cache", "prch2", ".prettiercache", "prettier cache"),
    ("clippy-json", "cljs", "clippy.json", "clippy json"),
    ("golangci-cache", "goci", ".cache/golangci-lint", "golangci cache"),
    ("rubocop-json", "rcjs", "rubocop.json", "rubocop json"),
    ("flake8-txt", "flkt", "flake8.txt", "flake8 txt"),
    ("black-cache", "bkch", ".black_cache", "black cache"),
    ("isort-cache", "isch", ".isort.cfg.cache", "isort cache"),
    ("bandit-json", "bdjs", "bandit.json", "bandit json"),
    ("semgrep-json", "sgjs", "semgrep.json", "semgrep json"),
    ("trivy-json", "tvjs", "trivy.json", "trivy json"),
    ("grype-json", "gyjs", "grype.json", "grype json"),
    ("syft-json", "syjs", "syft.json", "syft json"),
    ("osv-json", "osjs", "osv.json", "osv json"),
    ("gitleaks-json", "gljs", "gitleaks.json", "gitleaks json"),
    ("trufflehog-json", "thjs", "trufflehog.json", "trufflehog json"),
    ("detectsecrets-baseline", "dsbl", ".secrets.baseline", "detect-secrets baseline"),
    ("sonar-report", "snrp", "sonar-report.json", "sonar report"),
    ("codeql-sarif", "cqsf", "codeql.sarif", "codeql sarif"),
    ("snyk-json", "snjs", "snyk.json", "snyk json"),
    ("hadolint-json", "hdjs", "hadolint.json", "hadolint json"),
    ("shellcheck-json", "scjs", "shellcheck.json", "shellcheck json"),
    ("yamllint-json", "yljs", "yamllint.json", "yamllint json"),
    ("markdownlint-json", "mdjs", "markdownlint.json", "markdownlint json"),
    ("stylelint-cache", "stch", ".stylelintcache", "stylelint cache"),
    ("sqlfluff-json", "sfjs", "sqlfluff.json", "sqlfluff json"),
]
L15 = [
    ("ruff-output", "rfot", "ruff.json", "ruff output", "ruff cache"),
    ("eslint-json", "esjs", "eslint.json", "eslint json", "eslint cache"),
    ("pylint-txt", "pltx", "pylint.txt", "pylint txt", "pylint json"),
    ("mypy-txt", "mytx", "mypy.txt", "mypy txt", "mypy cache"),
    ("pyright-json", "prjs", "pyright.json", "pyright json", "pyright cache"),
    ("tsc-errors", "tser", "tsc-errors.txt", "tsc errors", "tsc tsbuildinfo"),
    ("biome-json", "bmjs", "biome.json", "biome json", "biome cache"),
    ("prettier-log", "prlg", "prettier.log", "prettier log", "prettier cache"),
    ("clippy-txt", "cltx", "clippy.txt", "clippy txt", "clippy json"),
    ("golangci-json", "gojs", "golangci.json", "golangci json", "golangci cache"),
    ("rubocop-cache", "rcch", ".rubocop_cache", "rubocop cache", "rubocop json"),
    ("flake8-json", "fljs", "flake8.json", "flake8 json", "flake8 txt"),
    ("black-diff", "bkdf", "black.diff", "black diff", "black cache"),
    ("isort-diff", "isdf", "isort.diff", "isort diff", "isort cache"),
    ("bandit-sarif", "bdsf", "bandit.sarif", "bandit sarif", "bandit json"),
    ("semgrep-sarif", "sgsf", "semgrep.sarif", "semgrep sarif", "semgrep json"),
    ("trivy-sarif", "tvsf", "trivy.sarif", "trivy sarif", "trivy json"),
    ("grype-sarif", "gysf", "grype.sarif", "grype sarif", "grype json"),
    ("syft-spdx", "sysp", "syft.spdx.json", "syft spdx", "syft json"),
    ("osv-sarif", "ossf", "osv.sarif", "osv sarif", "osv json"),
    ("gitleaks-sarif", "glsf", "gitleaks.sarif", "gitleaks sarif", "gitleaks json"),
    ("trufflehog-log", "thlg", "trufflehog.log", "trufflehog log", "trufflehog json"),
    ("detectsecrets-json", "dsjs", "detect-secrets.json", "detect-secrets json", "detect-secrets baseline"),
    ("sonar-issues", "snis", "sonar-issues.json", "sonar issues", "sonar report"),
    ("codeql-bqrs", "cqbq", "codeql.bqrs", "codeql bqrs", "codeql sarif"),
    ("snyk-sarif", "snsf", "snyk.sarif", "snyk sarif", "snyk json"),
    ("hadolint-sarif", "hdsf", "hadolint.sarif", "hadolint sarif", "hadolint json"),
    ("shellcheck-gcc", "scgc", "shellcheck.gcc", "shellcheck gcc", "shellcheck json"),
    ("yamllint-txt", "yltx", "yamllint.txt", "yamllint txt", "yamllint json"),
    ("markdownlint-txt", "mdtx", "markdownlint.txt", "markdownlint txt", "markdownlint json"),
    ("stylelint-json", "stjs", "stylelint.json", "stylelint json", "stylelint cache"),
    ("sqlfluff-txt", "sftx", "sqlfluff.txt", "sqlfluff txt", "sqlfluff json"),
]

# mill16: profiler leftover dests
S16 = [
    ("cprofile-pstats", "cpst", "out.pstats", "cprofile pstats"),
    ("pyspy-speedscope", "pyss", "pyspy.speedscope.json", "py-spy speedscope"),
    ("scalene-json", "scjs2", "scalene.json", "scalene json"),
    ("yappi-pstat", "yapp", "yappi.pstat", "yappi pstat"),
    ("lineprofiler-lprof", "lplf", "out.lprof", "line-profiler lprof"),
    ("memoryprofiler-mprof", "mpmf", "mprof.dat", "memory-profiler mprof"),
    ("austin-folded", "aufd", "austin.folded", "austin folded"),
    ("perf-data", "pfdt", "perf.data", "perf data"),
    ("flamegraph-folded", "fgfd", "perf.folded", "flamegraph folded"),
    ("speedscope-json", "spjs", "speedscope.json", "speedscope json"),
    ("pprof-pb", "pfpb", "cpu.pprof", "pprof protobuf"),
    ("asyncprofiler-jfr", "apjf", "async-profiler.jfr", "async-profiler jfr"),
    ("jfr-recording", "jfrc", "hotspot.jfr", "jfr recording"),
    ("yourkit-snapshot", "yksn", "yourkit.snapshot", "yourkit snapshot"),
    ("visualvm-nps", "vvnp", "visualvm.nps", "visualvm nps"),
    ("tracy-capture", "trcp", "tracy.tracy", "tracy capture"),
    ("optick-capture", "opcp", "optick.opt", "optick capture"),
    ("nsight-qdrep", "nsqd", "nsight.qdrep", "nsight qdrep"),
    ("vtune-result", "vtrs", "vtune.vtune", "vtune result"),
    ("instruments-trace", "intr", "instruments.trace", "instruments trace"),
    ("dtrace-out", "dtot", "dtrace.out", "dtrace out"),
    ("bpftrace-out", "bpot", "bpftrace.out", "bpftrace out"),
    ("strace-log", "stlg", "strace.log", "strace log"),
    ("ltrace-log", "ltlg", "ltrace.log", "ltrace log"),
    ("heaptrack-gz", "hpgz", "heaptrack.gz", "heaptrack gz"),
    ("valgrind-xml", "vgxm", "valgrind.xml", "valgrind xml"),
    ("massif-out", "msot", "massif.out", "massif out"),
    ("cachegrind-out", "cgot", "cachegrind.out", "cachegrind out"),
    ("callgrind-out", "clot", "callgrind.out", "callgrind out"),
    ("gprof-out", "gpot", "gmon.out", "gprof out"),
    ("samply-json", "smjs", "samply.json", "samply json"),
    ("pyinstrument-json", "pij", "pyinstrument.json", "pyinstrument json"),
]
L16 = [
    ("cprofile-txt", "cptx", "cprofile.txt", "cprofile txt", "cprofile pstats"),
    ("pyspy-raw", "pysv", "pyspy.raw", "py-spy raw", "py-spy speedscope"),
    ("scalene-cpu", "sccp", "scalene.cpu.json", "scalene cpu", "scalene json"),
    ("yappi-callgrind", "yacg", "yappi.callgrind", "yappi callgrind", "yappi pstat"),
    ("lineprofiler-txt", "lptx", "lineprofiler.txt", "line-profiler txt", "line-profiler lprof"),
    ("memoryprofiler-plot", "mppl", "mprof.plot.dat", "memory-profiler plot", "memory-profiler mprof"),
    ("austin-pprof", "aupp", "austin.pprof", "austin pprof", "austin folded"),
    ("perf-script", "pfsc", "perf.script", "perf script", "perf data"),
    ("flamegraph-log", "fglg", "flamegraph.log", "flamegraph log", "flamegraph folded"),
    ("speedscope-raw", "sprw", "speedscope.raw", "speedscope raw", "speedscope json"),
    ("pprof-txt", "pftx", "pprof.txt", "pprof txt", "pprof protobuf"),
    ("asyncprofiler-collapsed", "apcl", "async-profiler.collapsed", "async-profiler collapsed", "async-profiler jfr"),
    ("jfr-json", "jfjs", "hotspot.jfr.json", "jfr json", "jfr recording"),
    ("yourkit-csv", "ykcs", "yourkit.csv", "yourkit csv", "yourkit snapshot"),
    ("visualvm-log", "vvlg", "visualvm.log", "visualvm log", "visualvm nps"),
    ("tracy-json", "trjs", "tracy.json", "tracy json", "tracy capture"),
    ("optick-json", "opjs", "optick.json", "optick json", "optick capture"),
    ("nsight-sqlite", "nssq", "nsight.sqlite", "nsight sqlite", "nsight qdrep"),
    ("vtune-csv", "vtcs", "vtune.csv", "vtune csv", "vtune result"),
    ("instruments-xml", "inxml", "instruments.xml", "instruments xml", "instruments trace"),
    ("dtrace-json", "dtjs", "dtrace.json", "dtrace json", "dtrace out"),
    ("bpftrace-json", "bpjs", "bpftrace.json", "bpftrace json", "bpftrace out"),
    ("strace-json", "stjs2", "strace.json", "strace json", "strace log"),
    ("ltrace-json", "ltjs", "ltrace.json", "ltrace json", "ltrace log"),
    ("heaptrack-txt", "hptx", "heaptrack.txt", "heaptrack txt", "heaptrack gz"),
    ("valgrind-log", "vglg", "valgrind.log", "valgrind log", "valgrind xml"),
    ("massif-txt", "mstx", "massif.txt", "massif txt", "massif out"),
    ("cachegrind-txt", "cgtx", "cachegrind.txt", "cachegrind txt", "cachegrind out"),
    ("callgrind-txt", "cltx2", "callgrind.txt", "callgrind txt", "callgrind out"),
    ("gprof-txt", "gptx", "gprof.txt", "gprof txt", "gprof out"),
    ("samply-folded", "smfd", "samply.folded", "samply folded", "samply json"),
    ("pyinstrument-txt", "pitx", "pyinstrument.txt", "pyinstrument txt", "pyinstrument json"),
]

# mill17: venv / bytecode leftover dests
S17 = [
    ("pycache-pyc-leftover", "pyc", "__pycache__/mod.cpython-312.pyc", "pycache pyc"),
    ("venv-cfg-leftover", "vncf", "venv/pyvenv.cfg", "venv cfg"),
    ("pip-wheel-leftover", "pwhl", ".cache/pip/wheels", "pip wheel"),
    ("uv-cache-leftover", "uvch", ".cache/uv", "uv cache"),
    ("poetry-venv-leftover", "ptvn", ".venv", "poetry venv"),
    ("pdm-packages-leftover", "pdmp", "__pypackages__", "pdm packages"),
    ("conda-pkgs-leftover", "cnpk", "pkgs", "conda pkgs"),
    ("mamba-pkgs-leftover", "mbpk", "mamba-pkgs", "mamba pkgs"),
    ("pipenv-venv-leftover", "pevn", ".venv-pipenv", "pipenv venv"),
    ("virtualenv-cfg-leftover", "vecf", ".virtualenv/pyvenv.cfg", "virtualenv cfg"),
    ("tox-env-leftover", "txen", ".tox/py312", "tox env"),
    ("nox-envdir-leftover", "nxen", ".nox/py312", "nox envdir"),
    ("hatch-env-leftover", "hten", ".hatch/env", "hatch env"),
    ("rye-venv-leftover", "ryvn", ".rye/venv", "rye venv"),
    ("pixi-env-leftover", "pxen", ".pixi/envs/default", "pixi env"),
    ("poetry-lock-leftover", "ptlk", "poetry.lock.bak", "poetry lock bak"),
    ("pip-freeze-leftover", "pfrz", "requirements.freeze.txt", "pip freeze"),
    ("setuptools-egg-leftover", "steg", "src.egg-info", "setuptools egg-info"),
    ("dist-wheel-leftover", "dwhl", "dist/pkg.whl", "dist wheel"),
    ("sdist-targz-leftover", "sdtz", "dist/pkg.tar.gz", "sdist targz"),
    ("egg-link-leftover", "eglk", "pkg.egg-link", "egg link"),
    ("pth-file-leftover", "pthf", "easy-install.pth", "pth file"),
    ("sitecustomize-leftover", "stcz", "sitecustomize.py", "sitecustomize"),
    ("usercustomize-leftover", "uscz", "usercustomize.py", "usercustomize"),
    ("ipython-profile-leftover", "ippr", ".ipython/profile_default", "ipython profile"),
    ("jupyter-runtime-leftover", "jbrt", ".local/share/jupyter/runtime", "jupyter runtime"),
    ("nbconvert-files-leftover", "nbcf", ".nbconvert/files", "nbconvert files"),
    ("papermill-out-leftover", "pmot", "executed.ipynb", "papermill out"),
    ("jupytext-py-leftover", "jtpy", "notebook.py", "jupytext py"),
    ("nbstripout-bak-leftover", "nsbk", "notebook.ipynb.bak", "nbstripout bak"),
    ("pyproject-toml-leftover", "pptm", "pyproject.toml.bak", "pyproject toml bak"),
    ("setup-cfg-leftover", "stcf", "setup.cfg.bak", "setup cfg bak"),
]
# slug names already include leftover; s_from_row appends leftover-as-dest
# Wait - s_from_row does f"{name}-leftover-as-dest" so name should NOT include leftover
S17 = [
    ("pycache-pyc", "pyc", "__pycache__/mod.cpython-312.pyc", "pycache pyc"),
    ("venv-cfg", "vncf", "venv/pyvenv.cfg", "venv cfg"),
    ("pip-wheel", "pwhl", ".cache/pip/wheels", "pip wheel"),
    ("uv-cache", "uvch", ".cache/uv", "uv cache"),
    ("poetry-venv", "ptvn", ".venv", "poetry venv"),
    ("pdm-packages", "pdmp", "__pypackages__", "pdm packages"),
    ("conda-pkgs", "cnpk", "pkgs", "conda pkgs"),
    ("mamba-pkgs", "mbpk", "mamba-pkgs", "mamba pkgs"),
    ("pipenv-venv", "pevn", ".venv-pipenv", "pipenv venv"),
    ("virtualenv-cfg", "vecf", ".virtualenv/pyvenv.cfg", "virtualenv cfg"),
    ("tox-env", "txen", ".tox/py312", "tox env"),
    ("nox-envdir", "nxen", ".nox/py312", "nox envdir"),
    ("hatch-env", "hten", ".hatch/env", "hatch env"),
    ("rye-venv", "ryvn", ".rye/venv", "rye venv"),
    ("pixi-env", "pxen", ".pixi/envs/default", "pixi env"),
    ("poetry-lockbak", "ptlk", "poetry.lock.bak", "poetry lock bak"),
    ("pip-freeze", "pfrz", "requirements.freeze.txt", "pip freeze"),
    ("setuptools-egg", "steg", "src.egg-info", "setuptools egg-info"),
    ("dist-wheel", "dwhl", "dist/pkg.whl", "dist wheel"),
    ("sdist-targz", "sdtz", "dist/pkg.tar.gz", "sdist targz"),
    ("egg-link", "eglk", "pkg.egg-link", "egg link"),
    ("pth-file", "pthf", "easy-install.pth", "pth file"),
    ("sitecustomize", "stcz", "sitecustomize.py", "sitecustomize"),
    ("usercustomize", "uscz", "usercustomize.py", "usercustomize"),
    ("pyinstaller-spec", "pisp", "pkg.spec", "pyinstaller spec"),
    ("nuitka-dist", "ntds", "pkg.dist", "nuitka dist"),
    ("cxfreeze-build", "cxbd", "build/exe", "cxfreeze build"),
    ("shiv-pyz", "shpz", "pkg.pyz", "shiv pyz"),
    ("briefcase-app", "bfap", "build/briefcase", "briefcase app"),
    ("pyoxidizer-out", "pxot", "build/pyoxidizer", "pyoxidizer out"),
    ("pyproject-bak", "pptm", "pyproject.toml.bak", "pyproject bak"),
    ("setupcfg-bak", "stcf", "setup.cfg.bak", "setupcfg bak"),
]
L17 = [
    ("pycache-opt", "pyco", "__pycache__/mod.cpython-312.opt-1.pyc", "pycache opt", "pycache pyc"),
    ("venv-site", "vnst", "venv/lib/python3.12/site-packages", "venv site", "venv cfg"),
    ("pip-http", "phttp", ".cache/pip/http", "pip http", "pip wheel"),
    ("uv-wheels", "uvwh", ".cache/uv/wheels", "uv wheels", "uv cache"),
    ("poetry-artifacts", "ptar", ".cache/pypoetry/artifacts", "poetry artifacts", "poetry venv"),
    ("pdm-cache", "pdmc", ".cache/pdm", "pdm cache", "pdm packages"),
    ("conda-pkgs-tarballs", "cntb", "pkgs/tarballs", "conda tarballs", "conda pkgs"),
    ("mamba-cache", "mbch", "mamba-cache", "mamba cache", "mamba pkgs"),
    ("pipenv-lock", "pelk", "Pipfile.lock.bak", "pipenv lock", "pipenv venv"),
    ("virtualenv-site", "vest", ".virtualenv/lib/site-packages", "virtualenv site", "virtualenv cfg"),
    ("tox-log", "txlg", ".tox/log", "tox log", "tox env"),
    ("nox-log", "nxlg", ".nox/log", "nox log", "nox envdir"),
    ("hatch-cache", "htch", ".hatch/cache", "hatch cache", "hatch env"),
    ("rye-tools", "rytl", ".rye/tools", "rye tools", "rye venv"),
    ("pixi-cache", "pxch", ".pixi/cache", "pixi cache", "pixi env"),
    ("poetry-toml-bak", "pttb", "pyproject.poetry.bak", "poetry toml bak", "poetry lock bak"),
    ("pip-constraints", "pcst", "constraints.txt", "pip constraints", "pip freeze"),
    ("setuptools-build", "stbd", "build/lib", "setuptools build", "setuptools egg-info"),
    ("dist-manifest", "dmnf", "dist/RECORD", "dist record", "dist wheel"),
    ("sdist-metadata", "sdmd", "dist/PKG-INFO", "sdist metadata", "sdist targz"),
    ("egg-info-pkg", "egpk", "pkg.egg-info/PKG-INFO", "egg info pkg", "egg link"),
    ("pth-user", "pthu", "usercustomize.pth", "pth user", "pth file"),
    ("sitecustomize-pyc", "stcp", "sitecustomize.pyc", "sitecustomize pyc", "sitecustomize"),
    ("usercustomize-pyc", "uscp", "usercustomize.pyc", "usercustomize pyc", "usercustomize"),
    ("pyinstaller-warn", "piwn", "warn-pkg.txt", "pyinstaller warn", "pyinstaller spec"),
    ("nuitka-log", "ntlg", "nuitka.log", "nuitka log", "nuitka dist"),
    ("cxfreeze-log", "cxlg", "cxfreeze.log", "cxfreeze log", "cxfreeze build"),
    ("shiv-log", "shlg", "shiv.log", "shiv log", "shiv pyz"),
    ("briefcase-log", "bflg", "briefcase.log", "briefcase log", "briefcase app"),
    ("pyoxidizer-log", "pxlg", "pyoxidizer.log", "pyoxidizer log", "pyoxidizer out"),
    ("pyproject-toml-orig", "ppto", "pyproject.toml.orig", "pyproject orig", "pyproject bak"),
    ("setupcfg-orig", "stco", "setup.cfg.orig", "setupcfg orig", "setupcfg bak"),
]

# mill18: docs leftover dests — no html/png in slugs
S18 = [
    ("sphinx-doctree", "spdt", "_build/doctrees", "sphinx doctree"),
    ("mkdocs-sitejson", "mkjs", "site/search/search_index.json", "mkdocs search json"),
    ("jupyterbook-toc", "jbtc", "_toc.yml.bak", "jupyter-book toc"),
    ("myst-cache", "myst", ".myst_cache", "myst cache"),
    ("docusaurus-cache", "dsch", ".docusaurus", "docusaurus cache"),
    ("hugo-resources", "hgrs", "resources/_gen", "hugo resources"),
    ("jekyll-cache", "jkch", ".jekyll-cache", "jekyll cache"),
    ("hexo-db", "hxdb", "db.json", "hexo db"),
    ("eleventy-cache", "elch", ".cache/eleventy", "eleventy cache"),
    ("vitepress-cache", "vpch", ".vitepress/cache", "vitepress cache"),
    ("gitbook-cache", "gbch", ".gitbook/cache", "gitbook cache"),
    ("mdbook-book", "mdbk", "book", "mdbook book"),
    ("antora-cache", "anch", ".antora/cache", "antora cache"),
    ("asciidoc-cache", "adch", ".asciidoc/cache", "asciidoc cache"),
    ("rst2pdf-out", "r2po", "guide.pdf", "rst2pdf out"),
    ("pandoc-out", "pdco", "guide.docx", "pandoc out"),
    ("typst-out", "tyst", "guide.pdf", "typst out"),
    ("quarto-cache", "qtch", ".quarto", "quarto cache"),
    ("rmarkdown-cache", "rmch", "guide_cache", "rmarkdown cache"),
    ("bookdown-rds", "bdrd", "_bookdown_files", "bookdown files"),
    ("pkgdown-docs", "pkdd", "docs/pkgdown.yml", "pkgdown yml"),
    ("pdoc-out", "pdct", "pdoc-out", "pdoc out"),
    ("pydoctor-out", "pydo", "apidocs", "pydoctor out"),
    ("doxygen-xml", "doxm", "doxygen/xml", "doxygen xml"),
    ("javadoc-out", "jvdo", "javadoc", "javadoc out"),
    ("godoc-out", "gddo", "godoc-out", "godoc out"),
    ("rustdoc-json", "rdjs", "target/doc/crate.json", "rustdoc json"),
    ("typedoc-json", "tdjs", "typedoc.json", "typedoc json"),
    ("jsdoc-json", "jdjs", "jsdoc.json", "jsdoc json"),
    ("yard-cache", "ydch", ".yardoc", "yard cache"),
    ("rdoc-cache", "rdch", ".rdoc", "rdoc cache"),
    ("swagger-json", "swjs", "swagger.json", "swagger json"),
]
L18 = [
    ("sphinx-inventory", "spin", "_build/objects.inv", "sphinx inventory", "sphinx doctree"),
    ("mkdocs-yml-bak", "mkbk", "mkdocs.yml.bak", "mkdocs yml bak", "mkdocs search json"),
    ("jupyterbook-config", "jbcf", "_config.yml.bak", "jupyter-book config", "jupyter-book toc"),
    ("myst-xref", "myxr", "myst.xref.json", "myst xref", "myst cache"),
    ("docusaurus-i18n", "dsi8", "i18n/en.json", "docusaurus i18n", "docusaurus cache"),
    ("hugo-lock", "hglk", ".hugo_build.lock", "hugo lock", "hugo resources"),
    ("jekyll-metadata", "jkmd", ".jekyll-metadata", "jekyll metadata", "jekyll cache"),
    ("hexo-cache", "hxch", "db.json.bak", "hexo cache bak", "hexo db"),
    ("eleventy-data", "eldt", "_data/site.json", "eleventy data", "eleventy cache"),
    ("vitepress-config", "vpcf", ".vitepress/config.ts.bak", "vitepress config", "vitepress cache"),
    ("gitbook-yml", "gbyml", ".gitbook.yaml.bak", "gitbook yml", "gitbook cache"),
    ("mdbook-src", "mdsrc", "src/SUMMARY.md.bak", "mdbook summary", "mdbook book"),
    ("antora-playbook", "anpb", "antora-playbook.yml.bak", "antora playbook", "antora cache"),
    ("asciidoc-pdf", "adpf", "guide.adoc.pdf", "asciidoc pdf", "asciidoc cache"),
    ("rst2pdf-log", "r2pl", "rst2pdf.log", "rst2pdf log", "rst2pdf out"),
    ("pandoc-log", "pdlg", "pandoc.log", "pandoc log", "pandoc out"),
    ("typst-log", "tylg", "typst.log", "typst log", "typst out"),
    ("quarto-log", "qtlg", ".quarto/log", "quarto log", "quarto cache"),
    ("rmarkdown-knit", "rmkn", "guide.knit.md", "rmarkdown knit", "rmarkdown cache"),
    ("bookdown-yml", "bdyml", "_bookdown.yml.bak", "bookdown yml", "bookdown files"),
    ("pkgdown-index", "pkdi", "docs/pkgdown.json", "pkgdown index", "pkgdown yml"),
    ("pdoc-json", "pdcj", "pdoc.json", "pdoc json", "pdoc out"),
    ("pydoctor-log", "pydl", "pydoctor.log", "pydoctor log", "pydoctor out"),
    ("doxygen-tag", "dotg", "doxygen/tag.xml", "doxygen tag", "doxygen xml"),
    ("javadoc-index", "jvdi", "javadoc/element-list", "javadoc index", "javadoc out"),
    ("godoc-index", "gddi", "godoc-index.json", "godoc index", "godoc out"),
    ("rustdoc-search", "rdsh", "target/doc/search-index.js", "rustdoc search", "rustdoc json"),
    ("typedoc-out", "tdot", "typedoc-out", "typedoc out", "typedoc json"),
    ("jsdoc-out", "jdot", "jsdoc-out", "jsdoc out", "jsdoc json"),
    ("yard-db", "yddb", ".yardoc/db", "yard db", "yard cache"),
    ("rdoc-ri", "rdri", ".rdoc/ri", "rdoc ri", "rdoc cache"),
    ("openapi-yaml", "oaym", "openapi.yaml", "openapi yaml", "swagger json"),
]


def main() -> None:
    write_wave(15, S15, L15)
    write_wave(16, S16, L16)
    write_wave(17, S17, L17)
    write_wave(18, S18, L18)
    # unique stems check per wave
    for n, S, L in ((15, S15, L15), (16, S16, L16), (17, S17, L17), (18, S18, L18)):
        stems = [r[1] for r in S] + [r[1] for r in L]
        if len(stems) != len(set(stems)):
            raise SystemExit(f"dup stems wave {n}")
        slugs = [r[0] for r in S] + [r[0] for r in L]
        if len(slugs) != len(set(slugs)):
            raise SystemExit(f"dup names wave {n}")
        for name, *_ in S + L:
            blob = name
            if any(tok in blob for tok in ("html", "png", "svg", "matplotlib", "plotly")):
                raise SystemExit(f"viz token in {n} {name}")
    print("wrote mills 15-18")


if __name__ == "__main__":
    main()
