#!/usr/bin/env python3
"""AST-only scan of recovered ACTF sources. Never compile, exec, or eval them."""

from __future__ import annotations

import ast
import hashlib
from dataclasses import dataclass

from . import lineage as lin
from . import vocabulary as cv
from ._contract import bind_import_twin

__all__ = [
    "Features",
    "OperationFinding",
    "ScanResult",
    "scan_source",
    "scan_version",
]

_SENSITIVE_MODULES = frozenset({"os", "subprocess", "shutil", "socket", "urllib", "http"})
_CALL_BY_QUALIFIED = {
    "subprocess.run": cv.FINDING_PROCESS_EXECUTION,
    "subprocess.call": cv.FINDING_PROCESS_EXECUTION,
    "subprocess.Popen": cv.FINDING_PROCESS_EXECUTION,
    "subprocess.check_output": cv.FINDING_PROCESS_EXECUTION,
    "subprocess.check_call": cv.FINDING_PROCESS_EXECUTION,
    "os.system": cv.FINDING_PROCESS_EXECUTION,
    "os.popen": cv.FINDING_PROCESS_EXECUTION,
    "os.execl": cv.FINDING_PROCESS_EXECUTION,
    "os.execv": cv.FINDING_PROCESS_EXECUTION,
    "os.spawnl": cv.FINDING_PROCESS_EXECUTION,
    "os.spawnv": cv.FINDING_PROCESS_EXECUTION,
    "os.posix_spawn": cv.FINDING_PROCESS_EXECUTION,
    "os.remove": cv.FINDING_DELETE,
    "os.unlink": cv.FINDING_DELETE,
    "shutil.rmtree": cv.FINDING_RECURSIVE_DELETE,
    "importlib.import_module": cv.FINDING_DYNAMIC_IMPORT,
    "__import__": cv.FINDING_DYNAMIC_IMPORT,
    "exec": cv.FINDING_DYNAMIC_CODE,
    "eval": cv.FINDING_DYNAMIC_CODE,
    "compile": cv.FINDING_DYNAMIC_CODE,
}
_CALL_BY_ATTR = {
    "write_text": cv.FINDING_FILE_WRITE,
    "write_bytes": cv.FINDING_FILE_WRITE,
    "write": cv.FINDING_FILE_WRITE,
    "unlink": cv.FINDING_DELETE,
    "remove": cv.FINDING_DELETE,
    "rmtree": cv.FINDING_RECURSIVE_DELETE,
}
_WRITE_MODES = frozenset({"w", "a", "x", "r+", "w+", "a+", "x+", "wb", "ab", "xb", "rb+", "wb+", "ab+", "xb+"})
_NETWORK_WORDS = frozenset({"curl", "wget", "nc", "ncat", "ssh"})
_RAW_MARKER = "outputs/raw"
_RM_RF = "rm -rf"
_FACTORY_LITERAL = cv.FACTORY


@dataclass(frozen=True)
class OperationFinding:
    """One AST-classified operation. Evidence is a short source excerpt."""

    category: str
    line: int
    col: int
    evidence: str

    def as_mapping(self) -> dict[str, object]:
        return {
            "category": self.category,
            "line": self.line,
            "col": self.col,
            "evidence": self.evidence,
        }


@dataclass(frozen=True)
class Features:
    """Counts and extracted names from a successful ``ast.parse``."""

    functions: int
    classes: int
    imports: int
    calls: int
    episode_functions: tuple[str, ...]
    factory_literals: tuple[str, ...]

    def as_mapping(self) -> dict[str, object]:
        return {
            "functions": self.functions,
            "classes": self.classes,
            "imports": self.imports,
            "calls": self.calls,
            "episode_functions": list(self.episode_functions),
            "factory_literals": list(self.factory_literals),
        }


@dataclass(frozen=True)
class ScanResult:
    """AST-only verdict for one source string."""

    syntax_status: str
    syntax_error: str | None
    syntax_line: int | None
    features: Features | None
    operations: tuple[OperationFinding, ...]
    source_sha256: str
    filename: str
    empty: bool

    @property
    def excluded_reason(self) -> str | None:
        if self.empty:
            return cv.REASON_EMPTY_SOURCE
        if self.syntax_status == cv.SYNTAX_ERROR:
            return cv.REASON_SYNTAX_ERROR
        return None


def _source_digest(source_text: str) -> str:
    return hashlib.sha256(source_text.encode("utf-8")).hexdigest()


def _qualified_name(node: ast.AST) -> tuple[str, bool]:
    if isinstance(node, ast.Name):
        return node.id, True
    if isinstance(node, ast.Attribute):
        base, simple = _qualified_name(node.value)
        if base:
            return f"{base}.{node.attr}", simple
        return node.attr, False
    return "", False


def _const_str(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _open_mode(call: ast.Call) -> str:
    if len(call.args) >= 2:
        mode = _const_str(call.args[1])
        if mode is not None:
            return mode
    for keyword in call.keywords:
        if keyword.arg == "mode":
            mode = _const_str(keyword.value)
            if mode is not None:
                return mode
    return "r"


def _call_strings(call: ast.Call) -> tuple[str, ...]:
    values: list[str] = []
    for arg in (*call.args, *(keyword.value for keyword in call.keywords)):
        text = _const_str(arg)
        if text is not None:
            values.append(text)
    return tuple(values)


def _finding(category: str, node: ast.AST, evidence: str) -> OperationFinding:
    return OperationFinding(
        category=category,
        line=getattr(node, "lineno", 0),
        col=getattr(node, "col_offset", 0),
        evidence=evidence,
    )


def _classify_call(call: ast.Call) -> list[OperationFinding]:
    findings: list[OperationFinding] = []
    name, _simple = _qualified_name(call.func)
    category = _CALL_BY_QUALIFIED.get(name)
    if name == "open" and _open_mode(call) in _WRITE_MODES:
        category = cv.FINDING_FILE_WRITE
    if category is None and isinstance(call.func, ast.Attribute):
        category = _CALL_BY_ATTR.get(call.func.attr)
    if category is not None:
        findings.append(_finding(category, call, name or ast.unparse(call.func)))
        if category == cv.FINDING_FILE_WRITE and any(_RAW_MARKER in text for text in _call_strings(call)):
            findings.append(_finding(cv.FINDING_RAW_DATASET_MUTATION, call, name))
    return findings


def _module_root(name: str) -> str:
    return name.split(".", 1)[0]


def _classify_import(node: ast.AST) -> list[OperationFinding]:
    findings: list[OperationFinding] = []
    names: list[str] = []
    if isinstance(node, ast.Import):
        names.extend(alias.name for alias in node.names)
    elif isinstance(node, ast.ImportFrom) and node.module:
        names.append(node.module)
    for name in names:
        if _module_root(name) in _SENSITIVE_MODULES:
            findings.append(_finding(cv.FINDING_SENSITIVE_IMPORT, node, name))
    return findings


def _string_findings(node: ast.Constant) -> list[OperationFinding]:
    text = node.value
    if not isinstance(text, str):
        return []
    findings: list[OperationFinding] = []
    if _RAW_MARKER in text:
        findings.append(_finding(cv.FINDING_RAW_DATASET_PATH_REFERENCE, node, text[:80]))
    if _RM_RF in text:
        findings.append(_finding(cv.FINDING_SHELL_RECURSIVE_DELETE_REFERENCE, node, text[:80]))
    tokens = set(text.split())
    if tokens & _NETWORK_WORDS:
        findings.append(_finding(cv.FINDING_NETWORK_COMMAND_REFERENCE, node, text[:80]))
    return findings


def _empty_features() -> Features:
    return Features(0, 0, 0, 0, (), ())


def scan_source(source_text: str, *, filename: str = "<actf>") -> ScanResult:
    """Parse ``source_text`` with ``ast.parse`` only. Never execute it."""

    digest = _source_digest(source_text)
    empty = source_text.strip() == ""
    try:
        tree = ast.parse(source_text, filename=filename)
    except SyntaxError as exc:
        return ScanResult(
            syntax_status=cv.SYNTAX_ERROR,
            syntax_error=exc.msg,
            syntax_line=exc.lineno,
            features=None,
            operations=(),
            source_sha256=digest,
            filename=filename,
            empty=empty,
        )
    functions = 0
    classes = 0
    imports = 0
    calls = 0
    episode_functions: list[str] = []
    factory_literals: list[str] = []
    operations: list[OperationFinding] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions += 1
            if node.name.startswith("ep") and node.name[2:].isdigit():
                episode_functions.append(node.name)
        elif isinstance(node, ast.ClassDef):
            classes += 1
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            imports += 1
            operations.extend(_classify_import(node))
        elif isinstance(node, ast.Call):
            calls += 1
            operations.extend(_classify_call(node))
        elif isinstance(node, ast.Constant):
            if isinstance(node.value, str) and node.value == _FACTORY_LITERAL:
                factory_literals.append(node.value)
            operations.extend(_string_findings(node))
    return ScanResult(
        syntax_status=cv.SYNTAX_OK,
        syntax_error=None,
        syntax_line=None,
        features=Features(
            functions=functions,
            classes=classes,
            imports=imports,
            calls=calls,
            episode_functions=tuple(episode_functions),
            factory_literals=tuple(factory_literals),
        ),
        operations=tuple(operations),
        source_sha256=digest,
        filename=filename,
        empty=empty,
    )


def scan_version(version: lin.VersionRef) -> ScanResult:
    """Read one version file as UTF-8 text and scan it. Never execute it."""

    try:
        source_text = version.source_path.read_text(encoding="utf-8")
    except UnicodeError as exc:
        digest = hashlib.sha256(version.source_path.read_bytes()).hexdigest()
        return ScanResult(
            syntax_status=cv.SYNTAX_ERROR,
            syntax_error=f"source is not UTF-8: {exc}",
            syntax_line=None,
            features=None,
            operations=(),
            source_sha256=digest,
            filename=str(version.source_path),
            empty=False,
        )
    except OSError as exc:
        return ScanResult(
            syntax_status=cv.SYNTAX_ERROR,
            syntax_error=f"source unreadable: {exc}",
            syntax_line=None,
            features=_empty_features(),
            operations=(),
            source_sha256="",
            filename=str(version.source_path),
            empty=True,
        )
    return scan_source(source_text, filename=str(version.source_path))


bind_import_twin(__name__)
