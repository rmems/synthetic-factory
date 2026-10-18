"""Every relative link in README.md and docs/ resolves to a file and heading.

Reference-style links must also have a definition: every ``[text][label]`` use,
and every shortcut ``[#N]`` / ``[PR #N]`` citation. Other bare brackets such as
``[0, 1]`` are prose that GitHub renders literally, so they are not checked.
External links (any ``scheme:`` target) are not fetched. ``*.card.md`` files
are Hub dataset cards whose relative links resolve inside the published Hub
repository, not in this checkout, so they are skipped.
"""

import re
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
_INLINE_LINK = re.compile(r"\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
_REFERENCE_DEF = re.compile(r"^\s{0,3}\[[^\]]+\]:\s*<?(\S+?)>?(?:\s+\"[^\"]*\")?\s*$")
_REFERENCE_LABEL = re.compile(r"^\s{0,3}\[([^\]]+)\]:")
_REFERENCE_USE = re.compile(r"(?<![\]!\\])\[([^\[\]]+)\](?:\[([^\[\]]*)\])?(?![(\[:])")
_CITATION_LABEL = re.compile(r"^(?:PR )?#\d+$")
_CODE_SPAN = re.compile(r"(?<!`)(`+)(?!`).+?(?<!`)\1(?!`)")
_HEADING = re.compile(r"^#{1,6}\s+(.*?)\s*#*\s*$")
_HTML_ANCHOR = re.compile(r"<a\s+(?:name|id)=\"([^\"]+)\"")
_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


def doc_files() -> list[Path]:
    """README.md and every docs/ page, minus the Hub dataset cards."""
    docs = sorted((REPO / "docs").rglob("*.md"))
    return [REPO / "README.md"] + [path for path in docs if not path.name.endswith(".card.md")]


def _prose_lines(path: Path):
    """Yield ``(line_number, line)`` outside fenced code blocks.

    As in CommonMark, a fence closes only on a run of the same character that
    is at least as long as the opening run and has nothing after it.
    """
    fence = None
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        match = _FENCE.match(line)
        if fence is None and match:
            fence = match.group(1)
        elif fence is None:
            yield number, line
        elif _closes_fence(match, fence):
            fence = None


def _closes_fence(match, fence: str) -> bool:
    """True when ``match`` is a closing fence for the opening run ``fence``."""
    if match is None or match.group(2).strip():
        return False
    run = match.group(1)
    return run[0] == fence[0] and len(run) >= len(fence)


def _without_code_spans(line: str) -> str:
    """``line`` with inline code spans removed, so examples in code are not checked."""
    return _CODE_SPAN.sub("", line)


def github_slug(heading: str) -> str:
    """GitHub's heading anchor: lowercase, drop punctuation, spaces to hyphens."""
    text = re.sub(r"<[^>]+>", "", heading).replace("`", "").strip().lower()
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    return re.sub(r"[^\w\- ]", "", text).replace(" ", "-")


def anchors(path: Path) -> set[str]:
    """Heading slugs (deduplicated GitHub-style) and HTML anchors in ``path``."""
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
    """Relative links in ``path`` whose file or heading anchor does not exist."""
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


def undefined_references(path: Path, root: Path = REPO) -> list[str]:
    """Reference-style uses in ``path`` whose label has no definition there."""
    lines = list(_prose_lines(path))
    defined = {
        match.group(1).lower()
        for _, line in lines
        if _REFERENCE_DEF.match(line) and (match := _REFERENCE_LABEL.match(line))
    }
    return [
        f"{path.relative_to(root)}:{number}: [{label}] (no definition)"
        for number, label in _reference_uses(lines)
        if label.lower() not in defined
    ]


def _reference_uses(lines):
    """``(line_number, label)`` for each reference use outside definition lines."""
    for number, line in lines:
        if not _REFERENCE_LABEL.match(line):
            for label in _reference_labels(_without_code_spans(line)):
                yield number, label


def _reference_labels(prose: str):
    """Labels of full ``[text][label]`` uses and shortcut ``[#N]`` citations."""
    for match in _REFERENCE_USE.finditer(prose):
        text, label = match.groups()
        if label is not None:
            yield label or text
        elif _CITATION_LABEL.match(text):
            yield text


def _missing_heading(resolved: Path, anchor: str) -> bool:
    """True when ``anchor`` names a heading that the Markdown file lacks."""
    if not anchor or resolved.suffix != ".md":
        return False
    return anchor not in anchors(resolved)


class DocsLinkTests(unittest.TestCase):
    def test_relative_links_and_anchors_resolve(self):
        """Every relative link in README.md and docs/ names a real file and heading."""
        problems = [problem for path in doc_files() for problem in broken_links(path)]
        self.assertEqual(problems, [])

    def test_reference_links_have_definitions(self):
        """Every reference-style use and issue citation has a definition."""
        problems = [problem for path in doc_files() for problem in undefined_references(path)]
        self.assertEqual(problems, [])

    def test_scope_covers_readme_and_docs(self):
        """The checked set includes README.md and the docs/ pages."""
        names = {path.relative_to(REPO).as_posix() for path in doc_files()}
        self.assertIn("README.md", names)
        self.assertIn("docs/parity-oracles.md", names)

    def test_checker_reports_missing_files_and_headings(self):
        """The link checker flags missing paths and headings, and skips fenced code."""
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
                "```\n[fenced](missing.md)\n```\n"
                "````\n```text\n[nested](missing.md)\n~~~\n[tilde](missing.md)\n````\n"
                "``[spanned](missing.md)`` and `[single](missing.md)` are code.\n",
                encoding="utf-8",
            )
            self.assertEqual(broken_links(page, root), [
                "page.md:3: missing.md (no such path)",
                "page.md:3: #nowhere (no such heading)",
                "page.md:3: other.md#nope (no such heading)",
            ])

    def test_checker_reports_undefined_references(self):
        """The reference checker flags undefined labels and ignores code spans and prose brackets."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            page = root / "page.md"
            page.write_text(
                "See [#1], [PR #2], [docs][guide], [Guide][] and [0, 1].\n"
                "Missing [#3], [PR #4], [text][nowhere] and [Absent][]; `[#5]` is code.\n"
                "Empty [x][hollow] has no destination.\n"
                "\n[#1]: https://x.y/1\n[PR #2]: https://x.y/2\n[guide]: other.md\n[hollow]:\n",
                encoding="utf-8",
            )
            self.assertEqual(undefined_references(page, root), [
                "page.md:2: [#3] (no definition)",
                "page.md:2: [PR #4] (no definition)",
                "page.md:2: [nowhere] (no definition)",
                "page.md:2: [Absent] (no definition)",
                "page.md:3: [hollow] (no definition)",
            ])


if __name__ == "__main__":
    unittest.main()
