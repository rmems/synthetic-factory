"""Fresh-interpreter probes for the exact bytes behind reference measurements."""

import gc
import hashlib
import importlib
import os
from pathlib import Path
import py_compile
import shutil
import sys
import tempfile
from types import ModuleType

PACKAGED_NAME = "pipelines.oracle_grounded"
SIM_SOURCE = "sim.py"
DIRECT_SIM_MODULE = "oracle_grounded.sim"
PACKAGE_INIT = "__init__.py"
BEFORE_MARKER = b'MARKER = "before"'
AFTER_MARKER = b'MARKER = "after!"'
SOURCE_NAMES = (
    "canon.py",
    "families.py",
    "family_common.py",
    "family_credit.py",
    "family_credit_checks.py",
    "family_encoder.py",
    "family_memory.py",
    "family_memory_checks.py",
    "family_mesh.py",
    "family_neuron.py",
    "generator_common.py",
    "generator_credit.py",
    "generator_encoder.py",
    "generator_memory.py",
    "generator_mesh.py",
    "generator_neuron.py",
    "generators.py",
    "native_profiles.py",
    "native_runtime.py",
    "oracle_adapters.py",
    "oracle_binding.py",
    "oracle_core.py",
    "oracle_protocol.py",
    "oracles.py",
    "rng.py",
    SIM_SOURCE,
    "sim_common.py",
    "sim_credit.py",
    "sim_encoder.py",
    "sim_memory.py",
    "sim_mesh.py",
    "sim_neuron.py",
)


def _digest(package):
    digest = hashlib.sha256()
    for name in SOURCE_NAMES:
        digest.update(name.encode() + b"\0")
        digest.update(hashlib.sha256((package / name).read_bytes()).hexdigest().encode() + b"\n")
    return "sha256:" + digest.hexdigest()


def _package(package_first):
    if package_first:
        from pipelines import oracle_grounded
    else:
        import oracle_grounded
    return oracle_grounded


def _modules():
    from oracle_grounded import canon, families, generators, oracles, rng, sim
    return canon, families, generators, oracles, rng, sim


def _assert_equal(actual, expected):
    if actual != expected:
        raise AssertionError(f"loaded source evidence differs: {actual!r} != {expected!r}")


def _capture_then_edit(package, first):
    expected = _digest(package)
    _package(first)
    path = package / SIM_SOURCE
    path.write_bytes(path.read_bytes().replace(BEFORE_MARKER, AFTER_MARKER))
    *_, oracles, _rng, sim = _modules()
    _assert_equal(sim.MARKER, "before")
    _assert_equal(oracles.module_digest(), expected)


def _edit_before_digest(package, first):
    _package(first)
    *_, oracles, _rng, sim = _modules()
    expected = _digest(package)
    path = package / SIM_SOURCE
    path.write_bytes(path.read_bytes() + b"\n# edited after import\n")
    _assert_equal(sim.MARKER, "before")
    _assert_equal(oracles.module_digest(), expected)


def _stale_bytecode(package, first):
    path = package / SIM_SOURCE
    before = path.stat()
    py_compile.compile(str(path), doraise=True)
    path.write_bytes(path.read_bytes().replace(BEFORE_MARKER, AFTER_MARKER))
    os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
    expected = _digest(package)
    _package(first)
    *_, oracles, _rng, sim = _modules()
    _assert_equal(sim.MARKER, "after!")
    _assert_equal(oracles.module_digest(), expected)


def _reload(package, first):
    _package(first)
    *_, oracles, _rng, sim = _modules()
    expected = _digest(package)
    path = package / SIM_SOURCE
    path.write_bytes(path.read_bytes().replace(BEFORE_MARKER, AFTER_MARKER))
    importlib.reload(sim)
    _assert_equal(sim.MARKER, "before")
    _assert_equal(oracles.module_digest(), expected)


def _identity(_package_path, first):
    _package(first)
    direct = _modules()
    from pipelines.oracle_grounded import canon, families, generators, oracles, rng, sim
    packaged = canon, families, generators, oracles, rng, sim
    from oracle_grounded import source_snapshot as flat_snapshot
    from pipelines.oracle_grounded import source_snapshot as packaged_snapshot
    _assert_equal(flat_snapshot is packaged_snapshot, True)
    if any(left is not right for left, right in zip(direct, packaged, strict=True)):
        raise AssertionError("measurement module identities diverged")


def _package_modules():
    roots = [Path(module.__file__).resolve().parent.parent for name in ("oracle_grounded", PACKAGED_NAME)
             if (module := sys.modules.get(name)) is not None]
    return {name: module for name, module in sys.modules.items()
            if (origin := getattr(module, "__file__", None)) is not None
            and any(Path(origin).resolve().is_relative_to(root) for root in roots)}


def _remove_package_modules():
    for name in _package_modules():
        sys.modules.pop(name, None)


def _foreign_package(package, first):
    _package(first)
    _modules()
    foreign = package.parents[1] / "foreign"
    target = foreign / "pipelines/oracle_grounded"
    target.mkdir(parents=True)
    (target.parent / PACKAGE_INIT).write_text("")
    (target / PACKAGE_INIT).write_text("")
    (target / SIM_SOURCE).write_text('MARKER = "foreign"\n')
    _remove_package_modules()
    sys.path[:0] = [str(foreign), str(foreign / "pipelines")]
    _package(first)
    from oracle_grounded import sim
    _assert_equal(sim.MARKER, "foreign")


def _repeat_imports(package, first):
    for _ in range(3):
        _package(first)
        _modules()
        _remove_package_modules()
        gc.collect()
    _package(first)
    _modules()
    finders = [finder for finder in sys.meta_path if hasattr(finder, "_oracle_snapshot_owner")]
    _assert_equal(len(finders), 1)


def _restore_imports(package, first):
    owner = _package(first)
    _modules()
    saved = _package_modules()
    _remove_package_modules()
    _package(first)
    _modules()
    _remove_package_modules()
    sys.modules.update(saved)
    for parent in ("oracle_grounded", PACKAGED_NAME):
        sys.modules.pop(parent + ".sim", None)
    del owner.sim
    path = package / SIM_SOURCE
    path.write_bytes(path.read_bytes().replace(BEFORE_MARKER, AFTER_MARKER))
    from oracle_grounded import sim
    _assert_equal(sim.MARKER, "before")


def _edit_revert_measurement(package, first):
    _package(first)
    *_, oracles, _rng, sim = _modules()
    path = package / SIM_SOURCE
    before = path.read_bytes()
    expected = _digest(package)

    def measure(_request):
        path.write_bytes(before.replace(BEFORE_MARKER, AFTER_MARKER))
        importlib.reload(sim)
        path.write_bytes(before)
        return {"marker": sim.MARKER}, {"marker": "text"}

    adapter = oracles.ReferenceOracle(
        oracles.OracleIdentity("test", "test", "test"), measure, "test"
    )
    result = adapter.run("test", {})
    _assert_equal(result.measured, {"marker": "before"})
    _assert_equal(result.stages[0]["module_digest"], expected)


def _invalid_source(package, first, kind):
    path = package / SIM_SOURCE
    if kind == "symlink":
        original = path.with_suffix(".saved")
        path.rename(original)
        path.symlink_to(original.name)
    elif kind == "oversize":
        path.write_bytes(b"#" * (4 * 1024 * 1024 + 1))
    else:
        path.unlink()
    try:
        _package(first)
    except ImportError:
        return
    raise AssertionError("unsafe source snapshot did not refuse package loading")


def _package_reload(package, first):
    owner = _package(first)
    *_, oracles, _rng, sim = _modules()
    expected = _digest(package)
    path = package / SIM_SOURCE
    path.write_bytes(path.read_bytes().replace(BEFORE_MARKER, AFTER_MARKER))
    importlib.reload(owner)
    importlib.reload(sim)
    _assert_equal(sim.MARKER, "before")
    _assert_equal(oracles.module_digest(), expected)


def _stale_child(_package_path, first):
    parent = PACKAGED_NAME if first else "oracle_grounded"
    sys.modules[parent + ".sim"] = ModuleType(parent + ".sim")
    try:
        _package(first)
    except ImportError:
        return
    raise AssertionError("fresh owner inherited an unauthenticated child")


def _injected_child(_package_path, first):
    _package(first)
    *_, oracles, _rng, _sim = _modules()
    sys.modules[DIRECT_SIM_MODULE] = ModuleType(DIRECT_SIM_MODULE)
    try:
        oracles.module_digest()
    except ImportError:
        return
    raise AssertionError("digest accepted an unauthenticated child collision")


def _coexisting_foreign_package(package, first):
    owner = _package(first)
    *_, oracles, _rng, _sim = _modules()
    expected = oracles.module_digest()
    foreign_name = "oracle_grounded" if first else PACKAGED_NAME
    foreign_root = package.parents[1] / "foreign"
    foreign_root.mkdir()
    (foreign_root / PACKAGE_INIT).write_text("")
    (foreign_root / SIM_SOURCE).write_text('MARKER = "foreign"\n')
    foreign = ModuleType(foreign_name)
    foreign.__path__ = [str(foreign_root)]
    foreign.__file__ = str(foreign_root / PACKAGE_INIT)
    foreign.__spec__ = importlib.util.spec_from_file_location(
        foreign_name, foreign.__file__, submodule_search_locations=foreign.__path__,
    )
    for name in tuple(sys.modules):
        if name.startswith(foreign_name + "."):
            sys.modules.pop(name)
    sys.modules[foreign_name] = foreign
    if foreign_name == "oracle_grounded":
        loaded = importlib.import_module("oracle_grounded.sim")
    elif foreign_name == PACKAGED_NAME:
        loaded = importlib.import_module("pipelines.oracle_grounded.sim")
    else:
        raise AssertionError("probe import is not allowlisted")
    _assert_equal(loaded.MARKER, "foreign")
    _assert_equal(oracles.module_digest(), expected)
    _assert_equal(sys.modules[owner.__name__], owner)


PROBES = {
    "capture_then_edit": _capture_then_edit,
    "edit_before_digest": _edit_before_digest,
    "stale_bytecode": _stale_bytecode,
    "reload": _reload,
    "identity": _identity,
    "foreign_package": _foreign_package,
    "coexisting_foreign_package": _coexisting_foreign_package,
    "repeat_imports": _repeat_imports,
    "restore_imports": _restore_imports,
    "package_reload": _package_reload,
    "stale_child": _stale_child,
    "injected_child": _injected_child,
    "edit_revert_measurement": _edit_revert_measurement,
    "symlink": lambda package, first: _invalid_source(package, first, "symlink"),
    "oversize": lambda package, first: _invalid_source(package, first, "oversize"),
    "missing": lambda package, first: _invalid_source(package, first, "missing"),
}


def run_probe(repo_text, mode, package_first):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        shutil.copytree(Path(repo_text) / "pipelines", root / "pipelines",
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        shutil.copytree(Path(repo_text) / "schemas", root / "schemas")
        shutil.copytree(Path(repo_text) / "config", root / "config")
        package = root / "pipelines/oracle_grounded"
        path = package / SIM_SOURCE
        path.write_bytes(path.read_bytes() + b'\nMARKER = "before"\n')
        sys.path[:0] = [str(root), str(root / "pipelines")]
        PROBES[mode](package, package_first)
