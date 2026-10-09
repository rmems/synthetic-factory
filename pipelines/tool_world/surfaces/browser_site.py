#!/usr/bin/env python3
"""The static site behind a browser surface: shape checks, page lookup, redirects.

``pages/site.json`` maps paths to page members and declares redirects,
overlays, drift renames, and the not-found member. ``Site`` refuses a table
the surface could not serve exactly as written, answers which path a URL
names inside the origin, follows the declared redirect hops, and renders a
page member with its query-string placeholders filled in.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from html import escape as escape_html
from typing import Any
from urllib.parse import SplitResult, parse_qsl, urlsplit

from .. import vocabulary as cv
from .._contract import bind_import_twin

__all__ = ["MAX_REDIRECT_HOPS", "Site", "check_members", "check_redirects", "check_site"]

MAX_REDIRECT_HOPS = 3
_NOT_FOUND_HTML = (
    "<html><head><title>404 Not Found</title></head><body><h1>404 Not Found</h1>"
    "<p>The page does not exist.</p></body></html>"
)
_ORIGIN_RE = re.compile(r"^[a-z][a-z0-9+.-]*://[^/?#]+$")
_SITE_TABLES = ("pages", "redirects", "overlays", "drift")


def _is_text_table(value: Any) -> bool:
    return isinstance(value, Mapping) and all(
        isinstance(key, str) and isinstance(item, str) for key, item in value.items()
    )


def check_site(pack: Any) -> None:
    """Refuse a ``pages/site.json`` the surface could not serve exactly as written."""
    site, where = pack.site, f"pack {pack.pack_id}"
    cv.refuse_when(
        not isinstance(site, Mapping),
        cv.FINDING_PACK_FIELD_INVALID,
        f"{where}: needs pages/site.json with origin and pages",
    )
    origin = site.get("origin")
    cv.refuse_when(
        not isinstance(origin, str) or _ORIGIN_RE.match(origin) is None,
        cv.FINDING_PACK_FIELD_INVALID,
        f"{where}: origin must be scheme://host with no path",
    )
    for key in _SITE_TABLES:
        cv.refuse_when(
            not _is_text_table(site.get(key, {})),
            cv.FINDING_PACK_FIELD_INVALID,
            f"{where}: {key} must map strings to strings",
        )
    cv.refuse_when(
        not site.get("pages"),
        cv.FINDING_PACK_FIELD_INVALID,
        f"{where}: pages must be a nonempty table",
    )
    check_members(site, pack.pages, where)
    check_redirects(site, where)


def check_members(site: Mapping[str, Any], pages: Mapping[str, str], where: str) -> None:
    not_found = site.get("not_found")
    cv.refuse_when(
        not_found is not None and not isinstance(not_found, str),
        cv.FINDING_PACK_FIELD_INVALID,
        f"{where}: not_found must name a page member",
    )
    members = list(site["pages"].values()) + ([] if not_found is None else [not_found])
    missing = sorted(member for member in members if member not in pages)
    cv.refuse_when(
        bool(missing),
        cv.FINDING_PACK_FIELD_INVALID,
        f"{where}: site names missing page members {missing}",
    )


def check_redirects(site: Mapping[str, Any], where: str) -> None:
    redirects = site.get("redirects", {})
    pages = site["pages"]
    dangling = sorted(
        target
        for target in redirects.values()
        if target not in redirects and target not in pages and target.partition("?")[0] not in pages
    )
    cv.refuse_when(
        bool(dangling),
        cv.FINDING_PACK_FIELD_INVALID,
        f"{where}: redirects lead to undeclared paths {dangling}",
    )


def _is_absolute(parts: SplitResult) -> bool:
    return bool(parts.scheme or parts.netloc)


class Site:
    """One pack's site, checked at construction and read on every navigation."""

    def __init__(self, pack: Any) -> None:
        check_site(pack)
        site = pack.site
        self.origin: str = site["origin"]
        self.paths: Mapping[str, str] = site["pages"]
        self.members: Mapping[str, str] = pack.pages
        self.not_found: str | None = site.get("not_found")
        self.redirects: dict[str, str] = dict(site.get("redirects", {}))
        self.overlays: dict[str, str] = dict(site.get("overlays", {}))
        self.drift: dict[str, str] = dict(site.get("drift", {}))

    def has_overlay(self, name: Any) -> bool:
        return isinstance(name, str) and name in self.overlays

    def _is_foreign(self, parts: SplitResult) -> bool:
        """Whether a URL names another origin; a bare path is always inside the site."""
        return _is_absolute(parts) and f"{parts.scheme}://{parts.netloc}" != self.origin

    def path_of(self, url: str) -> str | None:
        """The path and query ``url`` names inside the origin, or None for another origin."""
        parts = urlsplit(url)
        if self._is_foreign(parts):
            return None
        path = parts.path or "/"
        return path + (f"?{parts.query}" if parts.query else "")

    def resolve(self, path: str, *, missing: bool) -> tuple[str, str]:
        """Follow the declared redirect hops; the page html, or the not-found page."""
        hops = 0
        while path in self.redirects and hops < MAX_REDIRECT_HOPS:
            path, hops = self.redirects[path], hops + 1
        html = None if missing else self.page_html(path)
        return path, self.not_found_html() if html is None else html

    def page_html(self, path: str) -> str | None:
        """The page at ``path`` with its ``{{key}}`` placeholders filled from the query, or None.

        A query value is text, never markup: it is escaped before it lands in
        the page, so a query cannot add elements to the DOM the agent sees.
        """
        bare, _, query = path.partition("?")
        member = self.paths.get(path) or self.paths.get(bare)
        if member is None:
            return None
        html = self.members[member]
        for key, value in parse_qsl(query, keep_blank_values=True):
            html = html.replace("{{" + key + "}}", escape_html(value))
        return html

    def not_found_html(self) -> str:
        """The pack's declared not-found page, or the built-in one."""
        return _NOT_FOUND_HTML if self.not_found is None else self.members[self.not_found]

    def drifted(self, html: str) -> str:
        """``html`` with every declared drift rename applied."""
        for old, new in self.drift.items():
            html = html.replace(old, new)
        return html


bind_import_twin(__name__)
