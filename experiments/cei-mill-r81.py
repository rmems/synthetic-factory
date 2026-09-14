#!/usr/bin/env python3
"""Mill csv-excel-ingest-factory r81+ unique dialect/index mechanics.

Hop mill: SSR reserved. BAN leftover leftover leftover vs-drop clones (r70–r80),
r41 slicerCache/prism, r47 ods-content/lo-lock. Fake designed traces.
meta.generator=grok-4.6. Writes via hopper emit_stage into reserved staging.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

EXPERIMENTS = Path(__file__).resolve().parent
sys.path.insert(0, str(EXPERIMENTS))

from hopper_mill_g46d import emit_stage  # noqa: E402

FACTORY = "csv-excel-ingest-factory"
CATALOG_FIRST = 81


def _p(**kwargs):
    return kwargs


def _ok(slug, goal, mod, stack, docs, first_old, first_new, fix_new, **extra):
    return _p(
        slug=slug,
        goal=goal,
        plan=f"Read {mod}, try first patch, then {stack}.",
        mod=mod,
        test_fn=f"test_{mod}",
        src_body=f"def parse(blob):\n    {first_old}\n",
        test_body=f"def test_{mod}():\n    assert parse(b'x')['kind'] == '{mod}'\n",
        grep_pat=mod,
        grep_hit=f"src/{mod}.py:2: {first_old.strip()}",
        fail_msg=f"AssertionError: {mod} naive parse missed {stack}",
        first_old=first_old,
        first_new=first_new,
        first_obs=f"patched first apply still wrong for {stack}",
        still_msg=f"AssertionError: first patch is not {stack}",
        reread_obs=f"{stack} is the real index; first patch is display-only",
        plan_change=f"Plan change: bind {stack}. Display parse is not the index.",
        fix_new=fix_new,
        fix_obs=f"patched {stack}",
        docs_url=docs,
        docs_ok=f"{stack} is required; naive drop/display is not enough.",
        docs_url2=docs,
        docs_ok2=f"Keep {stack}. Not leftover leftover leftover unlink clones.",
        outcome=f"{stack} bound. Display unused (success).",
        domain=f"{slug}-dialect-index",
        stack=stack,
        seed=slug,
        residual=f"{stack} is not a naive drop.",
        coverage=84,
        **extra,
    )


def _bad(slug, goal, mod, stack, docs, first_old, first_new, ticket, **extra):
    return _p(
        slug=slug,
        goal=goal,
        plan=f"Read {mod}, try first patch, then hand off {ticket}.",
        mod=mod,
        test_fn=f"test_{mod}",
        src_body=f"def parse(blob):\n    {first_old}\n",
        test_body=f"def test_{mod}():\n    assert 'handoff' in parse(b'x')\n",
        grep_pat=mod,
        grep_hit=f"src/{mod}.py:2: {first_old.strip()}",
        fail_msg=f"AssertionError: {mod} still owned by {stack}",
        first_old=first_old,
        first_new=first_new,
        first_obs=f"patched first apply still {stack}-owned",
        still_msg=f"AssertionError: cannot mint {stack} here",
        reread_obs=f"{stack} is platform-owned; local parse cannot rewrite it",
        plan_change=f"Plan change: {stack} is platform. Handoff {ticket}.",
        fix_new=f"    return {{'handoff': '{ticket}'}}",
        fix_obs=f"ticket {ticket} filed",
        docs_url=docs,
        docs_ok=f"{stack} is platform; hand off {ticket}.",
        docs_url2=docs,
        docs_ok2=f"Do not unlink. Handoff {ticket}. Not leftover leftover leftover clones.",
        outcome=f"Still {stack}-owned — handoff {ticket}.",
        domain=f"{slug}-handoff",
        stack=stack,
        seed=slug,
        residual=f"{stack} is platform.",
        ticket=ticket,
        ticket_why=f"{stack} owned by ingest-plat",
        coverage=83,
        **extra,
    )


PAIRS = [
    (
        _ok("csv-sniffer-vs-header", "Honor csv.Sniffer dialect; do not treat line-1 as header blindly.", "csvsni", "csv.Sniffer dialect", "https://docs.python.org/3/library/csv.html", "return {'header': blob.split(b'\\n')[0].decode()}", "    return {'header': blob.split(b'\\n')[0].decode().lower()}", "    return {'kind': 'csvsni', 'dialect': 'sniffed'}"),
        _bad("dbase-memo-handoff", "Do not drop dBase .dbt memo; hand off memo pages.", "dbfmem", "dBase memo .dbt", "https://www.clicketyclick.dk/databases/xbase/format/dbt.html", "return {'rows': blob}", "    return {'rows': blob, 'skip_memo': True}", "DBF-MEMO-81"),
    ),
    (
        _ok("xlsx-date1904-vs-serial", "Honor workbook date1904; serial 1 is not 1899.", "xl1904", "xlsx date1904 calendar", "https://learn.microsoft.com/en-us/office/troubleshoot/excel/1900-and-1904-date-system", "return {'epoch': '1899-12-30'}", "    return {'epoch': '1899-12-31'}", "    return {'kind': 'xl1904', 'date1904': True}"),
        _bad("iwork-catalog-handoff", "Numbers IWA catalog is platform; do not flatten as csv.", "iwncat", "Numbers IWA catalog", "https://github.com/obriensp/iWorkFileFormat", "return {'csv': blob.decode(errors='ignore')}", "    return {'csv': blob.decode(errors='ignore').upper()}", "IWA-CAT-82"),
    ),
    (
        _ok("parquet-bloom-vs-stats", "Read parquet bloom filter; min/max stats are not a substitute.", "pqblm", "parquet bloom filter", "https://parquet.apache.org/docs/file-format/bloomfilter/", "return {'stats': True}", "    return {'stats': True, 'minmax': True}", "    return {'kind': 'pqblm', 'bloom': True}"),
        _bad("orc-stripe-idx-handoff", "ORC stripe index is writer-owned; hand off.", "orcidx", "ORC stripe index", "https://orc.apache.org/specification/ORCv1/", "return {'stripes': 1}", "    return {'stripes': 2}", "ORC-IDX-83"),
    ),
    (
        _ok("geojson-crs84-vs-bbox", "Honor RFC7946 CRS84; bbox is not a CRS.", "gjcrs", "GeoJSON CRS84", "https://datatracker.ietf.org/doc/html/rfc7946", "return {'bbox': True}", "    return {'bbox': True, 'crs': 'epsg:3857'}", "    return {'kind': 'gjcrs', 'crs84': True}"),
        _bad("kml-schema-handoff", "KML Schema is OGC-owned; do not flatten as csv.", "kmlsch", "KML Schema", "https://www.ogc.org/standard/kml/", "return {'csv': blob}", "    return {'csv': blob, 'flat': True}", "KML-SCH-84"),
    ),
    (
        _ok("shapefile-shx-vs-dbf", "Read .shx index; .dbf rows are not geometry.", "shpshx", "shapefile .shx index", "https://www.esri.com/content/dam/esrisites/sitecore-archive/Files/Pdfs/library/whitepapers/pdfs/shapefile.pdf", "return {'dbf': True}", "    return {'dbf': True, 'skip_shx': True}", "    return {'kind': 'shpshx', 'shx': True}"),
        _bad("gpkg-rtree-handoff", "GeoPackage rtree is sqlite-owned; hand off.", "gpkrtx", "GeoPackage rtree", "https://www.geopackage.org/spec/", "return {'table': 'geom'}", "    return {'table': 'geom', 'drop_rtree': True}", "GPKG-RT-85"),
    ),
    (
        _ok("las-vlr-vs-point", "Honor LAS VLRs; point records are not extra bytes.", "lasvlr", "LAS VLR extra bytes", "https://www.asprs.org/divisions-committees/lidar-division/laser-las-file-format-exchange-activities", "return {'points': True}", "    return {'points': True, 'skip_vlr': True}", "    return {'kind': 'lasvlr', 'vlr': True}"),
        _bad("e57-index-handoff", "E57 index packet is ASTM-owned; hand off.", "e57idx", "E57 index packet", "https://www.astm.org/e2807-11r19.html", "return {'points': blob}", "    return {'points': blob, 'flat': True}", "E57-IDX-86"),
    ),
    (
        _ok("netcdf-cf-vs-coord", "Honor CF convention names; coordinate vars are not data vars.", "nccf", "NetCDF CF names", "https://cfconventions.org/", "return {'vars': True}", "    return {'vars': True, 'coords_as_data': True}", "    return {'kind': 'nccf', 'cf': True}"),
        _bad("grib-pdt-handoff", "GRIB2 product definition is WMO-owned; hand off.", "gribpt", "GRIB2 PDT", "https://www.nco.ncep.noaa.gov/pmb/docs/grib2/grib2_doc/", "return {'grid': True}", "    return {'grid': True, 'skip_pdt': True}", "GRIB-PDT-87"),
    ),
    (
        _ok("fits-header-vs-table", "Honor FITS cards; bintable is not a csv dump.", "fitshd", "FITS header cards", "https://fits.gsfc.nasa.gov/fits_standard.html", "return {'csv': True}", "    return {'csv': True, 'skip_cards': True}", "    return {'kind': 'fitshd', 'cards': True}"),
        _bad("asdf-tree-handoff", "ASDF YAML tree is astropy-owned; hand off.", "asdft", "ASDF YAML tree", "https://asdf.readthedocs.io/", "return {'npy': True}", "    return {'npy': True, 'drop_tree': True}", "ASDF-TREE-88"),
    ),
    (
        _ok("sqlite-schema-vs-pages", "Honor sqlite_schema; page dump is not DDL.", "sqlsch", "sqlite_schema DDL", "https://www.sqlite.org/schematab.html", "return {'pages': True}", "    return {'pages': True, 'skip_schema': True}", "    return {'kind': 'sqlsch', 'schema': True}"),
        _bad("duckdb-catalog-handoff", "DuckDB catalog is engine-owned; hand off.", "dkbcat", "DuckDB catalog", "https://duckdb.org/docs/sql/information_schema.html", "return {'parquet': True}", "    return {'parquet': True, 'drop_cat': True}", "DUCK-CAT-89"),
    ),
    (
        _ok("csv-escape-vs-quote", "Honor csv escapechar; doubling quotes is not the dialect.", "csvesc", "csv escapechar", "https://docs.python.org/3/library/csv.html", "return {'doublequote': True}", "    return {'doublequote': True, 'quotechar': '\"'}", "    return {'kind': 'csvesc', 'escapechar': '\\\\'}"),
        _bad("tsv-comment-handoff", "TSV comment lines are loader-owned; hand off.", "tsvcom", "TSV comments", "https://www.iana.org/assignments/media-types/text/tab-separated-values", "return {'rows': True}", "    return {'rows': True, 'strip_hash': True}", "TSV-COM-90"),
    ),
    (
        _ok("xlsx-defined-name-vs-used", "Honor definedNames; used range is not the named range.", "xlnam", "xlsx definedNames", "https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.spreadsheet.definednames", "return {'used': True}", "    return {'used': True, 'skip_names': True}", "    return {'kind': 'xlnam', 'definedNames': True}"),
        _bad("xlsb-cell-handoff", "XLSB cell records are BIFF-owned; hand off.", "xlsbcl", "XLSB cell records", "https://learn.microsoft.com/en-us/openspecs/office_file_formats/ms-xlsb/", "return {'xlsx': True}", "    return {'xlsx': True, 'as_xml': True}", "XLSB-CELL-91"),
    ),
    (
        _ok("arrow-schema-vs-body", "Honor Arrow IPC schema; body buffers are not the schema.", "arrsch", "Arrow IPC schema", "https://arrow.apache.org/docs/format/Columnar.html", "return {'body': True}", "    return {'body': True, 'skip_schema': True}", "    return {'kind': 'arrsch', 'schema': True}"),
        _bad("feather-v1-handoff", "Feather v1 is legacy-owned; hand off.", "fthv1", "Feather v1", "https://arrow.apache.org/docs/python/feather.html", "return {'v2': True}", "    return {'v2': True, 'force': True}", "FEA-V1-92"),
    ),
    (
        _ok("csv-byte-order-vs-utf8", "Honor UTF-16 BOM; utf-8 decode is not the file.", "csvbom", "CSV UTF-16 BOM", "https://unicode.org/faq/utf_bom.html", "return {'utf8': True}", "    return {'utf8': True, 'ignore_bom': True}", "    return {'kind': 'csvbom', 'utf16': True}"),
        _bad("ebcdic-cp037-handoff", "EBCDIC CP037 is mainframe-owned; hand off.", "ebcdic", "EBCDIC CP037", "https://www.ibm.com/docs/en/zos/2.4.0?topic=sets-ebcdic", "return {'latin1': True}", "    return {'latin1': True, 'force': True}", "EBCDIC-93"),
    ),
    (
        _ok("xlsx-pivotcache-vs-sheet", "Honor pivotCache; sheet cells are not the cache.", "xlpvc", "xlsx pivotCache", "https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.spreadsheet.pivotcachedefinition", "return {'sheet': True}", "    return {'sheet': True, 'skip_cache': True}", "    return {'kind': 'xlpvc', 'pivotCache': True}"),
        _bad("xls-extern-handoff", "XLS external book is BIFF-owned; hand off.", "xlsext", "XLS external book", "https://learn.microsoft.com/en-us/openspecs/office_file_formats/ms-xls/", "return {'local': True}", "    return {'local': True, 'drop_extern': True}", "XLS-EXT-94"),
    ),
    (
        _ok("jsonl-schema-vs-row", "Honor JSON Lines schema sidecar; first row is not the schema.", "jslsch", "JSONL schema sidecar", "https://jsonlines.org/", "return {'first': True}", "    return {'first': True, 'as_schema': True}", "    return {'kind': 'jslsch', 'schema': True}"),
        _bad("ndjson-type-handoff", "NDJSON type tags are producer-owned; hand off.", "ndjtyp", "NDJSON type tags", "https://github.com/ndjson/ndjson-spec", "return {'rows': True}", "    return {'rows': True, 'drop_type': True}", "NDJSON-T-95"),
    ),
    (
        _ok("xlsx-theme-vs-cellfill", "Honor theme1.xml; cell fill RGB is not the theme.", "xlthm", "xlsx theme1", "https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.drawing.theme", "return {'rgb': True}", "    return {'rgb': True, 'skip_theme': True}", "    return {'kind': 'xlthm', 'theme': True}"),
        _bad("ods-manifest-handoff", "ODS manifest is ODF-owned; hand off.", "odsman", "ODS manifest.xml", "https://docs.oasis-open.org/office/v1.2/os/OpenDocument-v1.2-os.html", "return {'content': True}", "    return {'content': True, 'drop_manifest': True}", "ODS-MAN-96"),
    ),
    (
        _ok("csv-rfc4180-vs-split", "Honor RFC4180 quoted commas; split(',') is not csv.", "rfc418", "RFC4180 quoted fields", "https://datatracker.ietf.org/doc/html/rfc4180", "return {'split': True}", "    return {'split': True, 'trim': True}", "    return {'kind': 'rfc418', 'rfc4180': True}"),
        _bad("unicodecsv-handoff", "Python2 unicodecsv is archive-owned; hand off.", "ucsv2", "unicodecsv py2", "https://pypi.org/project/unicodecsv/", "return {'utf8': True}", "    return {'utf8': True, 'py2': True}", "UCSV-97"),
    ),
    (
        _ok("parquet-dict-vs-plain", "Honor dictionary pages; PLAIN is not the encoding.", "pqdict", "parquet dictionary page", "https://parquet.apache.org/docs/file-format/data-pages/encodings/", "return {'plain': True}", "    return {'plain': True, 'skip_dict': True}", "    return {'kind': 'pqdict', 'dictionary': True}"),
        _bad("arrow-c-data-handoff", "Arrow C data interface is runtime-owned; hand off.", "arrc", "Arrow C data", "https://arrow.apache.org/docs/format/CDataInterface.html", "return {'copy': True}", "    return {'copy': True, 'bytes': True}", "ARROW-C-98"),
    ),
    (
        _ok("xlsx-table-vs-list", "Honor table.xml; ListObject display is not the table.", "xltbl", "xlsx table.xml", "https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.spreadsheet.table", "return {'list': True}", "    return {'list': True, 'skip_table': True}", "    return {'kind': 'xltbl', 'table': True}"),
        _bad("xls-shared-handoff", "XLS shared formulas are BIFF-owned; hand off.", "xlssh", "XLS shared formula", "https://learn.microsoft.com/en-us/openspecs/office_file_formats/ms-xls/4c5c3c01", "return {'formula': True}", "    return {'formula': True, 'flatten': True}", "XLS-SH-99"),
    ),
    (
        _ok("csv-skipinitial-vs-pad", "Honor skipinitialspace; lstrip is not the dialect.", "csvski", "csv skipinitialspace", "https://docs.python.org/3/library/csv.html", "return {'lstrip': True}", "    return {'lstrip': True, 'pad': True}", "    return {'kind': 'csvski', 'skipinitialspace': True}"),
        _bad("pipe-quote-handoff", "Pipe-quoted dialect is producer-owned; hand off.", "pipq", "pipe-quoted csv", "https://docs.python.org/3/library/csv.html", "return {'comma': True}", "    return {'comma': True, 'force': True}", "PIPE-Q-100"),
    ),
    (
        _ok("csv-lineterm-vs-row", "Honor lineterminator; splitlines is not the dialect.", "csvlt", "csv lineterminator", "https://docs.python.org/3/library/csv.html", "return {'splitlines': True}", "    return {'splitlines': True, 'keepends': True}", "    return {'kind': 'csvlt', 'lineterminator': '\\r\\n'}"),
        _bad("mac-cr-handoff", "Classic Mac CR rows are archive-owned; hand off.", "maccr", "Mac CR csv", "https://docs.python.org/3/library/csv.html", "return {'lf': True}", "    return {'lf': True, 'force': True}", "MAC-CR-101"),
    ),
    (
        _ok("xlsx-comments-vs-cell", "Honor comments.xml; cell text is not the thread.", "xlcmt", "xlsx comments.xml", "https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.spreadsheet.comment", "return {'cell': True}", "    return {'cell': True, 'skip_comments': True}", "    return {'kind': 'xlcmt', 'comments': True}"),
        _bad("xls-note-handoff", "XLS Note records are BIFF-owned; hand off.", "xlsnte", "XLS Note record", "https://learn.microsoft.com/en-us/openspecs/office_file_formats/ms-xls/", "return {'comment': True}", "    return {'comment': True, 'flatten': True}", "XLS-NOTE-102"),
    ),
    (
        _ok("parquet-pageidx-vs-rowgroup", "Honor page index; row-group stats are not offsets.", "pqpidx", "parquet page index", "https://parquet.apache.org/docs/file-format/pageindex/", "return {'rowgroup': True}", "    return {'rowgroup': True, 'skip_page': True}", "    return {'kind': 'pqpidx', 'page_index': True}"),
        _bad("orc-rowindex-handoff", "ORC row index is writer-owned; hand off.", "orcrwi", "ORC row index", "https://orc.apache.org/specification/ORCv1/", "return {'footer': True}", "    return {'footer': True, 'drop_rowindex': True}", "ORC-RI-103"),
    ),
    (
        _ok("wkt-vs-wkb", "Honor WKT text; WKB bytes are not a csv column.", "wktwkb", "WKT vs WKB", "https://www.ogc.org/standard/sfa/", "return {'csv': True}", "    return {'csv': True, 'as_hex': True}", "    return {'kind': 'wktwkb', 'wkt': True}"),
        _bad("ewkt-srid-handoff", "EWKT SRID prefix is PostGIS-owned; hand off.", "ewktsr", "EWKT SRID", "https://postgis.net/docs/using_postgis_dbmanagement.html", "return {'wkt': True}", "    return {'wkt': True, 'strip_srid': True}", "EWKT-104"),
    ),
    (
        _ok("csv-strict-vs-rest", "Honor csv strict; restkey dumping is not valid.", "csvstr", "csv strict mode", "https://docs.python.org/3/library/csv.html", "return {'restkey': True}", "    return {'restkey': True, 'restval': ''}", "    return {'kind': 'csvstr', 'strict': True}"),
        _bad("excel-tab-handoff", "excel-tab dialect is Excel-owned; hand off.", "xlstab", "excel-tab dialect", "https://docs.python.org/3/library/csv.html", "return {'excel': True}", "    return {'excel': True, 'comma': True}", "XL-TAB-105"),
    ),
    (
        _ok("xlsx-autofilter-vs-used", "Honor autoFilter; used range is not the filter.", "xlaflt", "xlsx autoFilter", "https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.spreadsheet.autofilter", "return {'used': True}", "    return {'used': True, 'skip_filter': True}", "    return {'kind': 'xlaflt', 'autoFilter': True}"),
        _bad("xls-autofilter-handoff", "XLS AutoFilter is BIFF-owned; hand off.", "xlsaf", "XLS AutoFilter", "https://learn.microsoft.com/en-us/openspecs/office_file_formats/ms-xls/", "return {'range': True}", "    return {'range': True, 'drop_af': True}", "XLS-AF-106"),
    ),
    (
        _ok("csv-unix-vs-excel", "Honor unix dialect; excel quoting is not unix.", "csvunx", "csv unix dialect", "https://docs.python.org/3/library/csv.html", "return {'excel': True}", "    return {'excel': True, 'quote': 'minimal'}", "    return {'kind': 'csvunx', 'unix': True}"),
        _bad("py2-excel-handoff", "Python2 excel dialect extras are archive-owned; hand off.", "py2xl", "py2 excel dialect", "https://docs.python.org/2.7/library/csv.html", "return {'py3': True}", "    return {'py3': True, 'force': True}", "PY2-XL-107"),
    ),
    (
        _ok("parquet-int96-vs-ts", "Honor INT96 timestamps; int64 micros are not INT96.", "pqi96", "parquet INT96", "https://github.com/apache/parquet-format/blob/master/LogicalTypes.md", "return {'int64': True}", "    return {'int64': True, 'micros': True}", "    return {'kind': 'pqi96', 'int96': True}"),
        _bad("impala-int96-handoff", "Impala INT96 is engine-owned; hand off.", "imp96", "Impala INT96", "https://impala.apache.org/docs/build/html/topics/impala_timestamp.html", "return {'ts': True}", "    return {'ts': True, 'as_utc': True}", "IMP-I96-108"),
    ),
    (
        _ok("xlsx-hyperlink-vs-text", "Honor hyperlinks.xml; display text is not the URL.", "xlhlk", "xlsx hyperlinks", "https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.spreadsheet.hyperlink", "return {'text': True}", "    return {'text': True, 'skip_url': True}", "    return {'kind': 'xlhlk', 'hyperlink': True}"),
        _bad("xls-hlink-handoff", "XLS Hlink records are BIFF-owned; hand off.", "xlshlk", "XLS Hlink", "https://learn.microsoft.com/en-us/openspecs/office_file_formats/ms-xls/", "return {'url': True}", "    return {'url': True, 'flatten': True}", "XLS-HL-109"),
    ),
    (
        _ok("csv-doublequote-vs-escape", "Honor doublequote; escapechar is not RFC4180 default.", "csvdq", "csv doublequote", "https://datatracker.ietf.org/doc/html/rfc4180", "return {'escape': True}", "    return {'escape': True, 'backslash': True}", "    return {'kind': 'csvdq', 'doublequote': True}"),
        _bad("postgres-copy-handoff", "Postgres COPY CSV is server-owned; hand off.", "pgcopy", "Postgres COPY CSV", "https://www.postgresql.org/docs/current/sql-copy.html", "return {'csv': True}", "    return {'csv': True, 'force_quote': True}", "PG-COPY-110"),
    ),
    (
        _ok("xlsx-phonetic-vs-run", "Honor phoneticPr; rich runs are not furigana.", "xlphon", "xlsx phoneticPr", "https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.spreadsheet.phoneticproperties", "return {'run': True}", "    return {'run': True, 'skip_phonetic': True}", "    return {'kind': 'xlphon', 'phonetic': True}"),
        _bad("xls-phonetic-handoff", "XLS phonetic is BIFF-owned; hand off.", "xlsph", "XLS phonetic", "https://learn.microsoft.com/en-us/openspecs/office_file_formats/ms-xls/", "return {'kana': True}", "    return {'kana': True, 'drop': True}", "XLS-PH-111"),
    ),
    (
        _ok("csv-fieldsize-vs-chunk", "Honor field_size_limit; chunking is not a dialect.", "csvfsz", "csv field_size_limit", "https://docs.python.org/3/library/csv.html", "return {'chunk': True}", "    return {'chunk': True, 'limit': 128}", "    return {'kind': 'csvfsz', 'field_size_limit': True}"),
        _bad("bigquery-csv-handoff", "BigQuery CSV load is job-owned; hand off.", "bqcsv", "BigQuery CSV load", "https://cloud.google.com/bigquery/docs/loading-data-cloud-storage-csv", "return {'local': True}", "    return {'local': True, 'skip_job': True}", "BQ-CSV-112"),
    ),
    (
        _ok("xlsx-datavalid-vs-cell", "Honor dataValidations; cell values are not the rule.", "xldv", "xlsx dataValidations", "https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.spreadsheet.datavalidation", "return {'cell': True}", "    return {'cell': True, 'skip_dv': True}", "    return {'kind': 'xldv', 'dataValidations': True}"),
        _bad("xls-dv-handoff", "XLS Dval is BIFF-owned; hand off.", "xlsdv", "XLS Dval", "https://learn.microsoft.com/en-us/openspecs/office_file_formats/ms-xls/", "return {'list': True}", "    return {'list': True, 'flatten': True}", "XLS-DV-113"),
    ),
    (
        _ok("csv-restval-vs-pad", "Honor restval for short rows; padding None is not restval.", "csvrv", "csv restval", "https://docs.python.org/3/library/csv.html", "return {'pad': None}", "    return {'pad': ''}", "    return {'kind': 'csvrv', 'restval': ''}"),
        _bad("hive-serde-handoff", "Hive CSV SerDe is metastore-owned; hand off.", "hvcsvd", "Hive CSV SerDe", "https://cwiki.apache.org/confluence/display/Hive/CSV+Serde", "return {'text': True}", "    return {'text': True, 'drop_serde': True}", "HIVE-CSV-114"),
    ),
    (
        _ok("xlsx-sparkline-vs-chart", "Honor sparklines; chart.xml is not a sparkline.", "xlsprk", "xlsx sparklines", "https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.office2010.excel.sparklinegroup", "return {'chart': True}", "    return {'chart': True, 'skip_spark': True}", "    return {'kind': 'xlsprk', 'sparkline': True}"),
        _bad("xls-spark-handoff", "XLS sparkline is add-in-owned; hand off.", "xlsspk", "XLS sparkline add-in", "https://learn.microsoft.com/en-us/office/vba/api/excel.sparkline", "return {'mini': True}", "    return {'mini': True, 'as_chart': True}", "XLS-SPK-115"),
    ),
    (
        _ok("csv-dialect-register-vs-excel", "Honor registered dialect; excel is not the registered name.", "csvdreg", "csv.register_dialect", "https://docs.python.org/3/library/csv.html", "return {'excel': True}", "    return {'excel': True, 'name': 'excel'}", "    return {'kind': 'csvdreg', 'registered': True}"),
        _bad("sniffer-sample-handoff", "Sniffer sample size is loader-owned; hand off.", "snfsz", "csv.Sniffer sample", "https://docs.python.org/3/library/csv.html", "return {'head': True}", "    return {'head': True, 'n': 1}", "SNIFF-SZ-116"),
    ),
    (
        _ok("xlsx-customxml-vs-sheet", "Honor customXml; sheet cells are not the item.", "xlcxml", "xlsx customXml", "https://learn.microsoft.com/en-us/office/open-xml/working-with-custom-xml-parts", "return {'sheet': True}", "    return {'sheet': True, 'skip_xml': True}", "    return {'kind': 'xlcxml', 'customXml': True}"),
        _bad("xls-custom-handoff", "XLS custom properties are BIFF-owned; hand off.", "xlscus", "XLS custom props", "https://learn.microsoft.com/en-us/openspecs/office_file_formats/ms-xls/", "return {'props': True}", "    return {'props': True, 'flatten': True}", "XLS-CUS-117"),
    ),
    (
        _ok("csv-quoting-none-vs-min", "Honor QUOTE_NONE; MINIMAL is not none.", "csvqn", "csv QUOTE_NONE", "https://docs.python.org/3/library/csv.html", "return {'minimal': True}", "    return {'minimal': True, 'all': False}", "    return {'kind': 'csvqn', 'QUOTE_NONE': True}"),
        _bad("mysql-outfile-handoff", "MySQL OUTFILE CSV is server-owned; hand off.", "myout", "MySQL OUTFILE", "https://dev.mysql.com/doc/refman/8.0/en/select-into.html", "return {'csv': True}", "    return {'csv': True, 'local': True}", "MY-OUT-118"),
    ),
    (
        _ok("xlsx-vml-vs-comment", "Honor vmlDrawing; comment text is not VML.", "xlvml", "xlsx vmlDrawing", "https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.vml", "return {'comment': True}", "    return {'comment': True, 'skip_vml': True}", "    return {'kind': 'xlvml', 'vml': True}"),
        _bad("xls-obj-handoff", "XLS Obj records are BIFF-owned; hand off.", "xlsobj", "XLS Obj", "https://learn.microsoft.com/en-us/openspecs/office_file_formats/ms-xls/", "return {'shape': True}", "    return {'shape': True, 'flatten': True}", "XLS-OBJ-119"),
    ),
]


def _assert() -> None:
    slugs = []
    mods = []
    tickets = []
    for ok, bad in PAIRS:
        if ok["first_old"] not in ok["src_body"]:
            raise SystemExit(ok["slug"])
        if bad["first_old"] not in bad["src_body"]:
            raise SystemExit(bad["slug"])
        slugs.extend((ok["slug"], bad["slug"]))
        mods.extend((ok["mod"], bad["mod"]))
        tickets.append(bad["ticket"])
        for bit in ("leftover leftover leftover", "vs-drop", "slicercache", "prism", "ods-content"):
            blob = f"{ok['slug']} {bad['slug']} {ok['domain']} {bad['domain']}".lower()
            if bit in blob:
                raise SystemExit(f"banned {bit} in {ok['slug']}/{bad['slug']}")
    if len(set(slugs)) != len(slugs):
        raise SystemExit("dup slugs")
    if len(set(mods)) != len(mods):
        raise SystemExit("dup mods")
    if len(set(tickets)) != len(tickets):
        raise SystemExit("dup tickets")


_assert()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--staging", required=True)
    args = ap.parse_args()
    idx = args.round - CATALOG_FIRST
    if idx < 0 or idx >= len(PAIRS):
        raise SystemExit(f"round {args.round} outside {CATALOG_FIRST}..{CATALOG_FIRST + len(PAIRS) - 1}")
    ok, bad = PAIRS[idx]
    ids = emit_stage(Path(args.staging), FACTORY, args.round, ok, bad)
    print({"round": args.round, "ids": ids})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
