"""Literal import bindings for oracle generation, validation, and native profiles."""

from types import ModuleType


def _direct_oracle_generate() -> ModuleType:
    import oracle_generate as module

    return module


def _package_oracle_generate() -> ModuleType:
    import pipelines.oracle_generate as module

    return module


def _direct_oracle_generate_fs() -> ModuleType:
    import oracle_generate_fs as module

    return module


def _package_oracle_generate_fs() -> ModuleType:
    import pipelines.oracle_generate_fs as module

    return module


def _direct_oracle_generate_records() -> ModuleType:
    import oracle_generate_records as module

    return module


def _package_oracle_generate_records() -> ModuleType:
    import pipelines.oracle_generate_records as module

    return module


def _direct_oracle_validate() -> ModuleType:
    import oracle_validate as module

    return module

def _package_oracle_validate() -> ModuleType:
    import pipelines.oracle_validate as module

    return module

def _direct_oracle_validate_manifest() -> ModuleType:
    import oracle_validate_manifest as module

    return module

def _package_oracle_validate_manifest() -> ModuleType:
    import pipelines.oracle_validate_manifest as module

    return module

def _direct_oracle_validate_manifest_records() -> ModuleType:
    import oracle_validate_manifest_records as module

    return module

def _package_oracle_validate_manifest_records() -> ModuleType:
    import pipelines.oracle_validate_manifest_records as module

    return module

def _direct_oracle_validate_tree() -> ModuleType:
    import oracle_validate_tree as module

    return module

def _package_oracle_validate_tree() -> ModuleType:
    import pipelines.oracle_validate_tree as module

    return module

def _direct_oracle_validate_records() -> ModuleType:
    import oracle_validate_records as module

    return module

def _package_oracle_validate_records() -> ModuleType:
    import pipelines.oracle_validate_records as module

    return module

def _direct_oracle_record_stages() -> ModuleType:
    import oracle_record_stages as module

    return module

def _package_oracle_record_stages() -> ModuleType:
    import pipelines.oracle_record_stages as module

    return module

def _direct_oracle_record_envelope() -> ModuleType:
    import oracle_record_envelope as module

    return module

def _package_oracle_record_envelope() -> ModuleType:
    import pipelines.oracle_record_envelope as module

    return module

def _direct_oracle_record_generator() -> ModuleType:
    import oracle_record_generator as module

    return module

def _package_oracle_record_generator() -> ModuleType:
    import pipelines.oracle_record_generator as module

    return module

def _direct_native_profiles():
    from oracle_grounded import native_profiles as module
    return module

def _package_native_profiles():
    from pipelines.oracle_grounded import native_profiles as module
    return module

def _direct_native_runtime():
    from oracle_grounded import native_runtime as module
    return module

def _package_native_runtime():
    from pipelines.oracle_grounded import native_runtime as module
    return module

def _direct_native_checks():
    from oracle_grounded import native_checks as module
    return module

def _package_native_checks():
    from pipelines.oracle_grounded import native_checks as module
    return module

def _direct_native_gate():
    from oracle_grounded import native_gate as module
    return module

def _package_native_gate():
    from pipelines.oracle_grounded import native_gate as module
    return module


LOADER_PAIRS = {
    'oracle_grounded.native_gate': (_direct_native_gate, _package_native_gate),
    'oracle_grounded.native_checks': (_direct_native_checks, _package_native_checks),
    'oracle_grounded.native_runtime': (_direct_native_runtime, _package_native_runtime),
    'oracle_grounded.native_profiles': (_direct_native_profiles, _package_native_profiles),
    'oracle_validate': (_direct_oracle_validate, _package_oracle_validate),
    'oracle_record_generator': (_direct_oracle_record_generator, _package_oracle_record_generator),
    'oracle_record_envelope': (_direct_oracle_record_envelope, _package_oracle_record_envelope),
    'oracle_record_stages': (_direct_oracle_record_stages, _package_oracle_record_stages),
    'oracle_validate_records': (_direct_oracle_validate_records, _package_oracle_validate_records),
    'oracle_validate_tree': (_direct_oracle_validate_tree, _package_oracle_validate_tree),
    'oracle_validate_manifest': (_direct_oracle_validate_manifest, _package_oracle_validate_manifest),
    'oracle_validate_manifest_records': (_direct_oracle_validate_manifest_records, _package_oracle_validate_manifest_records),
    "oracle_generate": (_direct_oracle_generate, _package_oracle_generate),
    "oracle_generate_fs": (_direct_oracle_generate_fs, _package_oracle_generate_fs),
    "oracle_generate_records": (_direct_oracle_generate_records, _package_oracle_generate_records),
}
DIRECT_LOADERS = {name: loaders[0] for name, loaders in LOADER_PAIRS.items()}
PACKAGE_LOADERS = {name: loaders[1] for name, loaders in LOADER_PAIRS.items()}
