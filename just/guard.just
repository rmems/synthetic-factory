# Internal guards for write-* recipes; not operator commands. They run before
# the writer and fail closed (exit 2) on outputs/raw aliases or an existing
# path, using the same raw_tree_guard the pipelines use.

_guard_raw_py := "import sys; from pathlib import Path; from pipelines import raw_tree_guard; p = Path(sys.argv[1]); bad = raw_tree_guard.is_under_raw(p); (print(f'refusing outputs/raw path: {p}', file=sys.stderr) if bad else None); sys.exit(2 if bad else 0)"

_guard_exists_py := "import os, sys; bad = os.path.lexists(sys.argv[1]); (print(f'refusing existing path: {sys.argv[1]}', file=sys.stderr) if bad else None); sys.exit(2 if bad else 0)"

[private]
_refuse-raw path:
    @{{python}} -c {{quote(_guard_raw_py)}} "$1"

[private]
_refuse-existing path:
    @{{python}} -c {{quote(_guard_exists_py)}} "$1"

[private]
_refuse-new-destination path: (_refuse-raw path) (_refuse-existing path)

[private]
_require-coverage:
    @{{python}} -c 'from importlib.metadata import version; import sys; sys.exit(version("coverage") != "{{coverage_version}}")' || { echo "expected coverage {{coverage_version}}; run: {{python}} -m pip install --only-binary ':all:' coverage=={{coverage_version}}" >&2; exit 1; }
