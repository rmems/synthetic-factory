"""Every relative link in README.md and docs/ resolves to a file and heading.

External links (any ``scheme:`` target) are not fetched. ``*.card.md`` files
are Hub dataset cards whose relative links resolve inside the published Hub
repository, not in this checkout, so they are skipped.
"""

import re
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

_FENCE = re.compile(r"^\s*(```|~~~)")
_INLINE_LINK = re.compile(r"\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
_REFERENCE_DEF = re.compile(r"^\s{0,3}\[[^\]]+\]:\s*<?(\S+?)>?(?:\s+\"[^\"]*\")?\s*$")
_HEADING = re.compile(r"^#{1,6}\s+(.*?)\s*#*\s*$")
_HTML_ANCHOR = re.compile(r"<a\s+(?:name|id)=\"([^\"]+)\"")
_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


def doc_files() -> list[Path]:
    docs = sorted((REPO / "docs").rglob("*.md"))
    return [REPO / "README.md"] + [path for path in docs if not path.name.endswith(".card.md")]


def _prose_lines(path: Path):
    """Yield ``(line_number, line)`` outside fenced code blocks."""
    fenced = False
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if _FENCE.match(line):
            fenced = not fenced
        elif not fenced:
            yield number, line


def _without_code_spans(line: str) -> str:
    return re.sub(r"`[^`]*`", "", line)


def github_slug(heading: str) -> str:
    """GitHub's heading anchor: lowercase, drop punctuation, spaces to hyphens."""
    text = re.sub(r"<[^>]+>", "", heading).replace("`", "").strip().lower()
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    return re.sub(r"[^\w\- ]", "", text).replace(" ", "-")


def anchors(path: Path) -> set[str]:
    found: set[str] = set()
    seen: dict[str, int] = {}
    for _, line in _prose_lines(path):
        found.update(_HTML_ANCHOR.findall(line))
        match = _HEADING.match(line)
        if match:
            slug = github_slug(match.group(1))
            count = seen.get(slug, 0)
            seen[slug] = count + 1
            found.add(slug if count == 0 else f"{slug}-{count}")
    return found


def link_targets(path: Path):
    """Yield ``(line_number, target)`` for every relative link in ``path``."""
    for number, line in _prose_lines(path):
        prose = _without_code_spans(line)
        targets = [match.group(1) for match in _INLINE_LINK.finditer(prose)]
        definition = _REFERENCE_DEF.match(prose)
        if definition:
            targets.append(definition.group(1))
        for target in targets:
            if not _SCHEME.match(target):
                yield number, target


def broken_links(path: Path, root: Path = REPO) -> list[str]:
    problems = []
    for number, target in link_targets(path):
        file_part, _, anchor = target.partition("#")
        resolved = (path.parent / file_part).resolve() if file_part else path
        where = f"{path.relative_to(root)}:{number}: {target}"
        if not resolved.exists():
            problems.append(f"{where} (no such path)")
        elif _missing_heading(resolved, anchor):
            problems.append(f"{where} (no such heading)")
    return problems


def _missing_heading(resolved: Path, anchor: str) -> bool:
    """True when ``anchor`` names a heading that the Markdown file lacks."""
    if not anchor or resolved.suffix != ".md":
        return False
    return anchor not in anchors(resolved)


class DocsLinkTests(unittest.TestCase):
    def test_relative_links_and_anchors_resolve(self):
        problems = [problem for path in doc_files() for problem in broken_links(path)]
        self.assertEqual(problems, [])

    def test_scope_covers_readme_and_docs(self):
        names = {path.relative_to(REPO).as_posix() for path in doc_files()}
        self.assertIn("README.md", names)
        self.assertIn("docs/parity-oracles.md", names)

    def test_checker_reports_missing_files_and_headings(self):
        self.assertEqual(github_slug("How the `separation` is enforced!"),
                         "how-the-separation-is-enforced")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "other.md").write_text("# Real heading\n", encoding="utf-8")
            page = root / "page.md"
            page.write_text(
                "# Here\n"
                "[ok](other.md#real-heading) [self](#here) [web](https://x.y)\n"
                "[gone](missing.md) [bad](#nowhere) [far](other.md#nope)\n"
                "```\n[fenced](missing.md)\n```\n",
                encoding="utf-8",
            )
            self.assertEqual(broken_links(page, root), [
                "page.md:3: missing.md (no such path)",
                "page.md:3: #nowhere (no such heading)",
                "page.md:3: other.md#nope (no such heading)",
            ])


if __name__ == "__main__":
    unittest.main()
