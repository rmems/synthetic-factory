#!/usr/bin/env python3
"""NTP unique leftover leftover leftover leftover mill wave 18: NEW dest plants. BAN dnsmasq leftover clones."""
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
    s_from(0, "sphinx-doctree-leftover-as-dest", "spdt", "sphinx doctree leftover", "_build/doctrees", "sphinx doctree leftover", "sphinx leftover && ls _build/doctrees", "not sphinx-doctree leftover; sphinx doctree leftover is not dest", "treat leftover sphinx doctree as dest then CLI parquet.", "sphinx leftover; # _build/doctrees claimed dest", "sphinx leftover|_build/doctrees"),
    s_from(1, "mkdocs-sitejson-leftover-as-dest", "mkjs", "mkdocs sitejson leftover", "site/search/search_index.json", "mkdocs search json leftover", "mkdocs leftover && ls site/search/search_index.json", "not mkdocs-sitejson leftover; mkdocs search json leftover is not dest", "treat leftover mkdocs search json as dest then CLI parquet.", "mkdocs leftover; # site/search/search_index.json claimed dest", "mkdocs leftover|site/search/search_index.json"),
    s_from(2, "jupyterbook-toc-leftover-as-dest", "jbtc", "jupyterbook toc leftover", "_toc.yml.bak", "jupyter-book toc leftover", "jupyterbook leftover && ls _toc.yml.bak", "not jupyterbook-toc leftover; jupyter-book toc leftover is not dest", "treat leftover jupyter-book toc as dest then CLI parquet.", "jupyterbook leftover; # _toc.yml.bak claimed dest", "jupyterbook leftover|_toc.yml.bak"),
    s_from(3, "myst-cache-leftover-as-dest", "myst", "myst cache leftover", ".myst_cache", "myst cache leftover", "myst leftover && ls .myst_cache", "not myst-cache leftover; myst cache leftover is not dest", "treat leftover myst cache as dest then CLI parquet.", "myst leftover; # .myst_cache claimed dest", "myst leftover|.myst_cache"),
    s_from(4, "docusaurus-cache-leftover-as-dest", "dsch", "docusaurus cache leftover", ".docusaurus", "docusaurus cache leftover", "docusaurus leftover && ls .docusaurus", "not docusaurus-cache leftover; docusaurus cache leftover is not dest", "treat leftover docusaurus cache as dest then CLI parquet.", "docusaurus leftover; # .docusaurus claimed dest", "docusaurus leftover|.docusaurus"),
    s_from(5, "hugo-resources-leftover-as-dest", "hgrs", "hugo resources leftover", "resources/_gen", "hugo resources leftover", "hugo leftover && ls resources/_gen", "not hugo-resources leftover; hugo resources leftover is not dest", "treat leftover hugo resources as dest then CLI parquet.", "hugo leftover; # resources/_gen claimed dest", "hugo leftover|resources/_gen"),
    s_from(6, "jekyll-cache-leftover-as-dest", "jkch", "jekyll cache leftover", ".jekyll-cache", "jekyll cache leftover", "jekyll leftover && ls .jekyll-cache", "not jekyll-cache leftover; jekyll cache leftover is not dest", "treat leftover jekyll cache as dest then CLI parquet.", "jekyll leftover; # .jekyll-cache claimed dest", "jekyll leftover|.jekyll-cache"),
    s_from(7, "hexo-db-leftover-as-dest", "hxdb", "hexo db leftover", "db.json", "hexo db leftover", "hexo leftover && ls db.json", "not hexo-db leftover; hexo db leftover is not dest", "treat leftover hexo db as dest then CLI parquet.", "hexo leftover; # db.json claimed dest", "hexo leftover|db.json"),
    s_from(8, "eleventy-cache-leftover-as-dest", "elch", "eleventy cache leftover", ".cache/eleventy", "eleventy cache leftover", "eleventy leftover && ls .cache/eleventy", "not eleventy-cache leftover; eleventy cache leftover is not dest", "treat leftover eleventy cache as dest then CLI parquet.", "eleventy leftover; # .cache/eleventy claimed dest", "eleventy leftover|.cache/eleventy"),
    s_from(9, "vitepress-cache-leftover-as-dest", "vpch", "vitepress cache leftover", ".vitepress/cache", "vitepress cache leftover", "vitepress leftover && ls .vitepress/cache", "not vitepress-cache leftover; vitepress cache leftover is not dest", "treat leftover vitepress cache as dest then CLI parquet.", "vitepress leftover; # .vitepress/cache claimed dest", "vitepress leftover|.vitepress/cache"),
    s_from(10, "gitbook-cache-leftover-as-dest", "gbch", "gitbook cache leftover", ".gitbook/cache", "gitbook cache leftover", "gitbook leftover && ls .gitbook/cache", "not gitbook-cache leftover; gitbook cache leftover is not dest", "treat leftover gitbook cache as dest then CLI parquet.", "gitbook leftover; # .gitbook/cache claimed dest", "gitbook leftover|.gitbook/cache"),
    s_from(11, "mdbook-book-leftover-as-dest", "mdbk", "mdbook book leftover", "book", "mdbook book leftover", "mdbook leftover && ls book", "not mdbook-book leftover; mdbook book leftover is not dest", "treat leftover mdbook book as dest then CLI parquet.", "mdbook leftover; # book claimed dest", "mdbook leftover|book"),
    s_from(12, "antora-cache-leftover-as-dest", "anch", "antora cache leftover", ".antora/cache", "antora cache leftover", "antora leftover && ls .antora/cache", "not antora-cache leftover; antora cache leftover is not dest", "treat leftover antora cache as dest then CLI parquet.", "antora leftover; # .antora/cache claimed dest", "antora leftover|.antora/cache"),
    s_from(13, "asciidoc-cache-leftover-as-dest", "adch", "asciidoc cache leftover", ".asciidoc/cache", "asciidoc cache leftover", "asciidoc leftover && ls .asciidoc/cache", "not asciidoc-cache leftover; asciidoc cache leftover is not dest", "treat leftover asciidoc cache as dest then CLI parquet.", "asciidoc leftover; # .asciidoc/cache claimed dest", "asciidoc leftover|.asciidoc/cache"),
    s_from(14, "rst2pdf-out-leftover-as-dest", "r2po", "rst2pdf out leftover", "guide.pdf", "rst2pdf out leftover", "rst2pdf leftover && ls guide.pdf", "not rst2pdf-out leftover; rst2pdf out leftover is not dest", "treat leftover rst2pdf out as dest then CLI parquet.", "rst2pdf leftover; # guide.pdf claimed dest", "rst2pdf leftover|guide.pdf"),
    s_from(15, "pandoc-out-leftover-as-dest", "pdco", "pandoc out leftover", "guide.docx", "pandoc out leftover", "pandoc leftover && ls guide.docx", "not pandoc-out leftover; pandoc out leftover is not dest", "treat leftover pandoc out as dest then CLI parquet.", "pandoc leftover; # guide.docx claimed dest", "pandoc leftover|guide.docx"),
    s_from(16, "typst-out-leftover-as-dest", "tyst", "typst out leftover", "guide.pdf", "typst out leftover", "typst leftover && ls guide.pdf", "not typst-out leftover; typst out leftover is not dest", "treat leftover typst out as dest then CLI parquet.", "typst leftover; # guide.pdf claimed dest", "typst leftover|guide.pdf"),
    s_from(17, "quarto-cache-leftover-as-dest", "qtch", "quarto cache leftover", ".quarto", "quarto cache leftover", "quarto leftover && ls .quarto", "not quarto-cache leftover; quarto cache leftover is not dest", "treat leftover quarto cache as dest then CLI parquet.", "quarto leftover; # .quarto claimed dest", "quarto leftover|.quarto"),
    s_from(18, "rmarkdown-cache-leftover-as-dest", "rmch", "rmarkdown cache leftover", "guide_cache", "rmarkdown cache leftover", "rmarkdown leftover && ls guide_cache", "not rmarkdown-cache leftover; rmarkdown cache leftover is not dest", "treat leftover rmarkdown cache as dest then CLI parquet.", "rmarkdown leftover; # guide_cache claimed dest", "rmarkdown leftover|guide_cache"),
    s_from(19, "bookdown-rds-leftover-as-dest", "bdrd", "bookdown rds leftover", "_bookdown_files", "bookdown files leftover", "bookdown leftover && ls _bookdown_files", "not bookdown-rds leftover; bookdown files leftover is not dest", "treat leftover bookdown files as dest then CLI parquet.", "bookdown leftover; # _bookdown_files claimed dest", "bookdown leftover|_bookdown_files"),
    s_from(20, "pkgdown-docs-leftover-as-dest", "pkdd", "pkgdown docs leftover", "docs/pkgdown.yml", "pkgdown yml leftover", "pkgdown leftover && ls docs/pkgdown.yml", "not pkgdown-docs leftover; pkgdown yml leftover is not dest", "treat leftover pkgdown yml as dest then CLI parquet.", "pkgdown leftover; # docs/pkgdown.yml claimed dest", "pkgdown leftover|docs/pkgdown.yml"),
    s_from(21, "pdoc-out-leftover-as-dest", "pdct", "pdoc out leftover", "pdoc-out", "pdoc out leftover", "pdoc leftover && ls pdoc-out", "not pdoc-out leftover; pdoc out leftover is not dest", "treat leftover pdoc out as dest then CLI parquet.", "pdoc leftover; # pdoc-out claimed dest", "pdoc leftover|pdoc-out"),
    s_from(22, "pydoctor-out-leftover-as-dest", "pydo", "pydoctor out leftover", "apidocs", "pydoctor out leftover", "pydoctor leftover && ls apidocs", "not pydoctor-out leftover; pydoctor out leftover is not dest", "treat leftover pydoctor out as dest then CLI parquet.", "pydoctor leftover; # apidocs claimed dest", "pydoctor leftover|apidocs"),
    s_from(23, "doxygen-xml-leftover-as-dest", "doxm", "doxygen xml leftover", "doxygen/xml", "doxygen xml leftover", "doxygen leftover && ls doxygen/xml", "not doxygen-xml leftover; doxygen xml leftover is not dest", "treat leftover doxygen xml as dest then CLI parquet.", "doxygen leftover; # doxygen/xml claimed dest", "doxygen leftover|doxygen/xml"),
    s_from(24, "javadoc-out-leftover-as-dest", "jvdo", "javadoc out leftover", "javadoc", "javadoc out leftover", "javadoc leftover && ls javadoc", "not javadoc-out leftover; javadoc out leftover is not dest", "treat leftover javadoc out as dest then CLI parquet.", "javadoc leftover; # javadoc claimed dest", "javadoc leftover|javadoc"),
    s_from(25, "godoc-out-leftover-as-dest", "gddo", "godoc out leftover", "godoc-out", "godoc out leftover", "godoc leftover && ls godoc-out", "not godoc-out leftover; godoc out leftover is not dest", "treat leftover godoc out as dest then CLI parquet.", "godoc leftover; # godoc-out claimed dest", "godoc leftover|godoc-out"),
    s_from(26, "rustdoc-json-leftover-as-dest", "rdjs", "rustdoc json leftover", "target/doc/crate.json", "rustdoc json leftover", "rustdoc leftover && ls target/doc/crate.json", "not rustdoc-json leftover; rustdoc json leftover is not dest", "treat leftover rustdoc json as dest then CLI parquet.", "rustdoc leftover; # target/doc/crate.json claimed dest", "rustdoc leftover|target/doc/crate.json"),
    s_from(27, "typedoc-json-leftover-as-dest", "tdjs", "typedoc json leftover", "typedoc.json", "typedoc json leftover", "typedoc leftover && ls typedoc.json", "not typedoc-json leftover; typedoc json leftover is not dest", "treat leftover typedoc json as dest then CLI parquet.", "typedoc leftover; # typedoc.json claimed dest", "typedoc leftover|typedoc.json"),
    s_from(28, "jsdoc-json-leftover-as-dest", "jdjs", "jsdoc json leftover", "jsdoc.json", "jsdoc json leftover", "jsdoc leftover && ls jsdoc.json", "not jsdoc-json leftover; jsdoc json leftover is not dest", "treat leftover jsdoc json as dest then CLI parquet.", "jsdoc leftover; # jsdoc.json claimed dest", "jsdoc leftover|jsdoc.json"),
    s_from(29, "yard-cache-leftover-as-dest", "ydch", "yard cache leftover", ".yardoc", "yard cache leftover", "yard leftover && ls .yardoc", "not yard-cache leftover; yard cache leftover is not dest", "treat leftover yard cache as dest then CLI parquet.", "yard leftover; # .yardoc claimed dest", "yard leftover|.yardoc"),
    s_from(30, "rdoc-cache-leftover-as-dest", "rdch", "rdoc cache leftover", ".rdoc", "rdoc cache leftover", "rdoc leftover && ls .rdoc", "not rdoc-cache leftover; rdoc cache leftover is not dest", "treat leftover rdoc cache as dest then CLI parquet.", "rdoc leftover; # .rdoc claimed dest", "rdoc leftover|.rdoc"),
    s_from(31, "swagger-json-leftover-as-dest", "swjs", "swagger json leftover", "swagger.json", "swagger json leftover", "swagger leftover && ls swagger.json", "not swagger-json leftover; swagger json leftover is not dest", "treat leftover swagger json as dest then CLI parquet.", "swagger leftover; # swagger.json claimed dest", "swagger leftover|swagger.json"),
]

LEFTOVER = [
    l_from(0, "sphinx-inventory-leftover-handoff", "spin", "_build/objects.inv", "sphinx inventory leftover", "sphinx inventory leftover", "not sphinx doctree leftover; leftover sphinx inventory as dest", "ship leftover sphinx inventory as dest.", "sphinx inventory leftover; # _build/objects.inv on disk", "sphinx leftover|_build/objects.inv"),
    l_from(1, "mkdocs-yml-bak-leftover-handoff", "mkbk", "mkdocs.yml.bak", "mkdocs yml bak leftover", "mkdocs yml bak leftover", "not mkdocs search json leftover; leftover mkdocs yml bak as dest", "ship leftover mkdocs yml bak as dest.", "mkdocs yml bak leftover; # mkdocs.yml.bak on disk", "mkdocs leftover|mkdocs.yml.bak"),
    l_from(2, "jupyterbook-config-leftover-handoff", "jbcf", "_config.yml.bak", "jupyter-book config leftover", "jupyter-book config leftover", "not jupyter-book toc leftover; leftover jupyter-book config as dest", "ship leftover jupyter-book config as dest.", "jupyter-book config leftover; # _config.yml.bak on disk", "jupyterbook leftover|_config.yml.bak"),
    l_from(3, "myst-xref-leftover-handoff", "myxr", "myst.xref.json", "myst xref leftover", "myst xref leftover", "not myst cache leftover; leftover myst xref as dest", "ship leftover myst xref as dest.", "myst xref leftover; # myst.xref.json on disk", "myst leftover|myst.xref.json"),
    l_from(4, "docusaurus-i18n-leftover-handoff", "dsi8", "i18n/en.json", "docusaurus i18n leftover", "docusaurus i18n leftover", "not docusaurus cache leftover; leftover docusaurus i18n as dest", "ship leftover docusaurus i18n as dest.", "docusaurus i18n leftover; # i18n/en.json on disk", "docusaurus leftover|i18n/en.json"),
    l_from(5, "hugo-lock-leftover-handoff", "hglk", ".hugo_build.lock", "hugo lock leftover", "hugo lock leftover", "not hugo resources leftover; leftover hugo lock as dest", "ship leftover hugo lock as dest.", "hugo lock leftover; # .hugo_build.lock on disk", "hugo leftover|.hugo_build.lock"),
    l_from(6, "jekyll-metadata-leftover-handoff", "jkmd", ".jekyll-metadata", "jekyll metadata leftover", "jekyll metadata leftover", "not jekyll cache leftover; leftover jekyll metadata as dest", "ship leftover jekyll metadata as dest.", "jekyll metadata leftover; # .jekyll-metadata on disk", "jekyll leftover|.jekyll-metadata"),
    l_from(7, "hexo-cache-leftover-handoff", "hxch", "db.json.bak", "hexo cache bak leftover", "hexo cache bak leftover", "not hexo db leftover; leftover hexo cache bak as dest", "ship leftover hexo cache bak as dest.", "hexo cache bak leftover; # db.json.bak on disk", "hexo leftover|db.json.bak"),
    l_from(8, "eleventy-data-leftover-handoff", "eldt", "_data/site.json", "eleventy data leftover", "eleventy data leftover", "not eleventy cache leftover; leftover eleventy data as dest", "ship leftover eleventy data as dest.", "eleventy data leftover; # _data/site.json on disk", "eleventy leftover|_data/site.json"),
    l_from(9, "vitepress-config-leftover-handoff", "vpcf", ".vitepress/config.ts.bak", "vitepress config leftover", "vitepress config leftover", "not vitepress cache leftover; leftover vitepress config as dest", "ship leftover vitepress config as dest.", "vitepress config leftover; # .vitepress/config.ts.bak on disk", "vitepress leftover|.vitepress/config.ts.bak"),
    l_from(10, "gitbook-yml-leftover-handoff", "gbyml", ".gitbook.yaml.bak", "gitbook yml leftover", "gitbook yml leftover", "not gitbook cache leftover; leftover gitbook yml as dest", "ship leftover gitbook yml as dest.", "gitbook yml leftover; # .gitbook.yaml.bak on disk", "gitbook leftover|.gitbook.yaml.bak"),
    l_from(11, "mdbook-src-leftover-handoff", "mdsrc", "src/SUMMARY.md.bak", "mdbook summary leftover", "mdbook summary leftover", "not mdbook book leftover; leftover mdbook summary as dest", "ship leftover mdbook summary as dest.", "mdbook summary leftover; # src/SUMMARY.md.bak on disk", "mdbook leftover|src/SUMMARY.md.bak"),
    l_from(12, "antora-playbook-leftover-handoff", "anpb", "antora-playbook.yml.bak", "antora playbook leftover", "antora playbook leftover", "not antora cache leftover; leftover antora playbook as dest", "ship leftover antora playbook as dest.", "antora playbook leftover; # antora-playbook.yml.bak on disk", "antora leftover|antora-playbook.yml.bak"),
    l_from(13, "asciidoc-pdf-leftover-handoff", "adpf", "guide.adoc.pdf", "asciidoc pdf leftover", "asciidoc pdf leftover", "not asciidoc cache leftover; leftover asciidoc pdf as dest", "ship leftover asciidoc pdf as dest.", "asciidoc pdf leftover; # guide.adoc.pdf on disk", "asciidoc leftover|guide.adoc.pdf"),
    l_from(14, "rst2pdf-log-leftover-handoff", "r2pl", "rst2pdf.log", "rst2pdf log leftover", "rst2pdf log leftover", "not rst2pdf out leftover; leftover rst2pdf log as dest", "ship leftover rst2pdf log as dest.", "rst2pdf log leftover; # rst2pdf.log on disk", "rst2pdf leftover|rst2pdf.log"),
    l_from(15, "pandoc-log-leftover-handoff", "pdlg", "pandoc.log", "pandoc log leftover", "pandoc log leftover", "not pandoc out leftover; leftover pandoc log as dest", "ship leftover pandoc log as dest.", "pandoc log leftover; # pandoc.log on disk", "pandoc leftover|pandoc.log"),
    l_from(16, "typst-log-leftover-handoff", "tylg", "typst.log", "typst log leftover", "typst log leftover", "not typst out leftover; leftover typst log as dest", "ship leftover typst log as dest.", "typst log leftover; # typst.log on disk", "typst leftover|typst.log"),
    l_from(17, "quarto-log-leftover-handoff", "qtlg", ".quarto/log", "quarto log leftover", "quarto log leftover", "not quarto cache leftover; leftover quarto log as dest", "ship leftover quarto log as dest.", "quarto log leftover; # .quarto/log on disk", "quarto leftover|.quarto/log"),
    l_from(18, "rmarkdown-knit-leftover-handoff", "rmkn", "guide.knit.md", "rmarkdown knit leftover", "rmarkdown knit leftover", "not rmarkdown cache leftover; leftover rmarkdown knit as dest", "ship leftover rmarkdown knit as dest.", "rmarkdown knit leftover; # guide.knit.md on disk", "rmarkdown leftover|guide.knit.md"),
    l_from(19, "bookdown-yml-leftover-handoff", "bdyml", "_bookdown.yml.bak", "bookdown yml leftover", "bookdown yml leftover", "not bookdown files leftover; leftover bookdown yml as dest", "ship leftover bookdown yml as dest.", "bookdown yml leftover; # _bookdown.yml.bak on disk", "bookdown leftover|_bookdown.yml.bak"),
    l_from(20, "pkgdown-index-leftover-handoff", "pkdi", "docs/pkgdown.json", "pkgdown index leftover", "pkgdown index leftover", "not pkgdown yml leftover; leftover pkgdown index as dest", "ship leftover pkgdown index as dest.", "pkgdown index leftover; # docs/pkgdown.json on disk", "pkgdown leftover|docs/pkgdown.json"),
    l_from(21, "pdoc-json-leftover-handoff", "pdcj", "pdoc.json", "pdoc json leftover", "pdoc json leftover", "not pdoc out leftover; leftover pdoc json as dest", "ship leftover pdoc json as dest.", "pdoc json leftover; # pdoc.json on disk", "pdoc leftover|pdoc.json"),
    l_from(22, "pydoctor-log-leftover-handoff", "pydl", "pydoctor.log", "pydoctor log leftover", "pydoctor log leftover", "not pydoctor out leftover; leftover pydoctor log as dest", "ship leftover pydoctor log as dest.", "pydoctor log leftover; # pydoctor.log on disk", "pydoctor leftover|pydoctor.log"),
    l_from(23, "doxygen-tag-leftover-handoff", "dotg", "doxygen/tag.xml", "doxygen tag leftover", "doxygen tag leftover", "not doxygen xml leftover; leftover doxygen tag as dest", "ship leftover doxygen tag as dest.", "doxygen tag leftover; # doxygen/tag.xml on disk", "doxygen leftover|doxygen/tag.xml"),
    l_from(24, "javadoc-index-leftover-handoff", "jvdi", "javadoc/element-list", "javadoc index leftover", "javadoc index leftover", "not javadoc out leftover; leftover javadoc index as dest", "ship leftover javadoc index as dest.", "javadoc index leftover; # javadoc/element-list on disk", "javadoc leftover|javadoc/element-list"),
    l_from(25, "godoc-index-leftover-handoff", "gddi", "godoc-index.json", "godoc index leftover", "godoc index leftover", "not godoc out leftover; leftover godoc index as dest", "ship leftover godoc index as dest.", "godoc index leftover; # godoc-index.json on disk", "godoc leftover|godoc-index.json"),
    l_from(26, "rustdoc-search-leftover-handoff", "rdsh", "target/doc/search-index.js", "rustdoc search leftover", "rustdoc search leftover", "not rustdoc json leftover; leftover rustdoc search as dest", "ship leftover rustdoc search as dest.", "rustdoc search leftover; # target/doc/search-index.js on disk", "rustdoc leftover|target/doc/search-index.js"),
    l_from(27, "typedoc-out-leftover-handoff", "tdot", "typedoc-out", "typedoc out leftover", "typedoc out leftover", "not typedoc json leftover; leftover typedoc out as dest", "ship leftover typedoc out as dest.", "typedoc out leftover; # typedoc-out on disk", "typedoc leftover|typedoc-out"),
    l_from(28, "jsdoc-out-leftover-handoff", "jdot", "jsdoc-out", "jsdoc out leftover", "jsdoc out leftover", "not jsdoc json leftover; leftover jsdoc out as dest", "ship leftover jsdoc out as dest.", "jsdoc out leftover; # jsdoc-out on disk", "jsdoc leftover|jsdoc-out"),
    l_from(29, "yard-db-leftover-handoff", "yddb", ".yardoc/db", "yard db leftover", "yard db leftover", "not yard cache leftover; leftover yard db as dest", "ship leftover yard db as dest.", "yard db leftover; # .yardoc/db on disk", "yard leftover|.yardoc/db"),
    l_from(30, "rdoc-ri-leftover-handoff", "rdri", ".rdoc/ri", "rdoc ri leftover", "rdoc ri leftover", "not rdoc cache leftover; leftover rdoc ri as dest", "ship leftover rdoc ri as dest.", "rdoc ri leftover; # .rdoc/ri on disk", "rdoc leftover|.rdoc/ri"),
    l_from(31, "openapi-yaml-leftover-handoff", "oaym", "openapi.yaml", "openapi yaml leftover", "openapi yaml leftover", "not swagger json leftover; leftover openapi yaml as dest", "ship leftover openapi yaml as dest.", "openapi yaml leftover; # openapi.yaml on disk", "openapi leftover|openapi.yaml"),
]

mod2.SUCCESS = SUCCESS
mod2.LEFTOVER = LEFTOVER
mod2.BANNED_SLUGS = set(mod2.BANNED_SLUGS) | {
    "dnsmasq-hosts-leftover-as-dest",
    "dnsmasq-lease-leftover-handoff",
}
pair_for = mod2.pair_for
notes_for = mod2.notes_for
write_stage = mod2.write_stage


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 2:
        print("usage: ntp-mill-unique-llll18.py ROUND STAGING_DIR", file=sys.stderr)
        return 2
    round_n = int(argv[0])
    staging = Path(argv[1])
    staging.mkdir(parents=True, exist_ok=True)
    i1, i2 = write_stage(staging, round_n)
    print(f"wrote r{round_n} {i1} {i2}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
