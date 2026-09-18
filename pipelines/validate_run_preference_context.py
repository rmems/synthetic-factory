#!/usr/bin/env python3
"""Observable file/API/criterion anchors for preference-side comparison."""

import posixpath
import re
import sys

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling
    _assert_direct_sibling("validate_run_preference_context")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "validate_run_preference_context"
    )


CONTEXT_KEY_TERMS = (
    "api",
    "criterion",
    "criteria",
    "endpoint",
    "file",
    "path",
    "repo",
    "repository",
    "resource",
    "target",
    "url",
)
ARTIFACT_RE = re.compile(
    r"https?://[^\s\"']+|"
    r"(?:[a-z0-9_.-]+/)*[a-z0-9_.-]+\."
    r"(?:csv|env|go|java|js|json|md|py|rs|sql|toml|ts|txt|ya?ml)|"
    r"/(?:[a-z0-9_{}.-]+/)*[a-z0-9_{}.-]+",
    re.IGNORECASE,
)


def _normalized_artifact(artifact_text):
    artifact = artifact_text.rstrip(".,;:").casefold()
    if artifact.startswith(("http://", "https://")):
        return artifact
    return posixpath.normpath(artifact)


def _field_anchor(key, normalized):
    if not key:
        return None
    if not any(term in key for term in CONTEXT_KEY_TERMS):
        return None
    return f"field:{normalized}"


def _artifact_anchors(node):
    return [
        f"artifact:{_normalized_artifact(match.group(0))}"
        for match in ARTIFACT_RE.finditer(node)
    ]


def _anchor_text(node, anchors, key):
    normalized = " ".join(node.split()).casefold()
    field = _field_anchor(key, normalized)
    if field is not None:
        anchors.add(field)
    anchors.update(_artifact_anchors(node))


def _collect_mapping_anchors(node, anchors):
    for child_key, child in node.items():
        collect_context_anchors(child, anchors, str(child_key).casefold())


def _collect_sequence_anchors(node, anchors, key):
    for child in node:
        collect_context_anchors(child, anchors, key)


def collect_context_anchors(node, anchors, key=""):
    if isinstance(node, dict):
        _collect_mapping_anchors(node, anchors)
        return
    if isinstance(node, list):
        _collect_sequence_anchors(node, anchors, key)
        return
    if isinstance(node, str):
        _anchor_text(node, anchors, key)


def preference_side_context_anchors(value):
    """Return observable file/API/criterion anchors from one preference side."""
    anchors = set()
    collect_context_anchors(value, anchors)
    return anchors


if __package__:
    _expose_package_sibling(__name__)
