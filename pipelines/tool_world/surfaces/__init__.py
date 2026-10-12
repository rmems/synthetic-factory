"""The four tool surfaces one environment composes: workspace, mcp, browser, delegation.

Each surface declares its tools, owns its state, computes every observation,
and names the fault kinds it can apply. ``REGISTRY`` maps a surface name to
its class; the environment builds only the surfaces a task names.
"""

from __future__ import annotations

from .. import vocabulary as cv
from .._contract import bind_import_twin
from . import base, browser, delegation, mcp, workspace

__all__ = ["REGISTRY", "base", "browser", "delegation", "mcp", "workspace"]

REGISTRY = {
    cv.SURFACE_WORKSPACE: workspace.WorkspaceSurface,
    cv.SURFACE_MCP: mcp.McpSurface,
    cv.SURFACE_BROWSER: browser.BrowserSurface,
    cv.SURFACE_DELEGATION: delegation.DelegationSurface,
}

bind_import_twin(__name__)
