#!/usr/bin/env python3
"""Emit experiments/azr-plants-r1640.py — unique object-id IDOR / BFLA for r1640+."""
from __future__ import annotations

import re
from pathlib import Path

EXPERIMENTS = Path(__file__).resolve().parent
OUT = EXPERIMENTS / "azr-plants-r1640.py"

USED_SLUGS: set[str] = set()
USED_PLANTS: set[str] = set()
USED_LOOKUPS: set[str] = set()
USED_MODS: set[str] = set()
for p in list(EXPERIMENTS.glob("azr-plants*.py")) + list(EXPERIMENTS.glob("azr-mill*.py")):
    if p.name == "azr-plants-r1640.py":
        continue
    text = p.read_text(errors="ignore")
    USED_SLUGS.update(re.findall(r"slug=['\"]([a-z0-9-]+)['\"]", text))
    USED_PLANTS.update(re.findall(r"plant=['\"]([a-z0-9-]+)['\"]", text))
    USED_LOOKUPS.update(re.findall(r"lookup=['\"]([a-z0-9_]+)['\"]", text))
    USED_MODS.update(re.findall(r"mod=['\"]([a-z0-9_]+)['\"]", text))

PREFIX = [
    "iron", "jack", "jump", "kedge", "kevel", "kick", "knit", "lany", "leeb", "leec",
    "luffc", "marlsp", "martb", "mastc", "messl", "mizzb", "moorb", "netty", "nippb", "nockp",
    "oakp", "orlob", "outhb", "outrb", "painb", "parbb", "parrb", "paunb", "peakb", "pendb",
    "prevb", "quoib", "rabbb", "ratlb", "reefc", "ribbb", "robab", "rounb", "rowlb", "samsb",
    "scutb", "seacb", "seizb", "sennb", "shacb", "sheeb", "shrob", "skegb", "slabb", "snatb",
    "snorb", "spanb", "spenb", "spreh", "sprib", "stanb", "steeb", "stopb", "strab", "studb",
    "tabeb", "tackb", "taffb", "thimb", "throb", "thwab", "tillb", "toggb", "toppb", "tranb",
    "treeb", "trucb", "trysb", "tumbb", "turnb", "uphrb", "vangb", "waleb", "warpb", "weatb",
]
SUFFIX = ["block", "stay", "pin", "head", "bar", "coil", "eye", "clamp", "well", "ring"]
PLANTS: list[str] = []
for pre in PREFIX:
    for suf in SUFFIX:
        name = pre + suf
        if name in USED_PLANTS or name in PLANTS or not name.isidentifier():
            continue
        PLANTS.append(name)
        break
    if len(PLANTS) == 80:
        break
assert len(PLANTS) == 80, len(PLANTS)
assert len(set(PLANTS)) == 80
assert not (set(PLANTS) & USED_PLANTS)

FIRST = ["authn", "mask", "any_member", "list_scope"]
RESIDUAL = ["pdf", "export", "search", "mget", "csv", "admin", "webhook", "comments"]
LEFTOVER = ["put", "patch", "update"]

IDOR = [
    ("imeitac-idor", "IMEI TAC object-id IDOR", "imeitacs", "Imeitac", "imeitac", "35693803", "oem_id", "imei-tac", "TAC unique from GSMA TAC"),
    ("snssai-5g-idor", "S-NSSAI object-id IDOR", "snssais", "Snssai", "snssai", "1-000001", "net_id", "snssai-5g", "S-NSSAI unique from 3GPP"),
    ("dnn-5g-idor", "5G DNN object-id IDOR", "dnn5gs", "Dnn5g", "dnn5g", "internet.mnc410.mcc310.gprs", "net_id", "dnn-5g", "DNN unique from 3GPP"),
    ("pei-5g-idor", "5G PEI object-id IDOR", "pei5gs", "Pei5g", "pei5g", "imei-356938035643809", "oem_id", "pei-5g", "PEI unique from 3GPP"),
    ("gpsi-5g-idor", "5G GPSI object-id IDOR", "gpsi5gs", "Gpsi5g", "gpsi5g", "msisdn-12025550100", "net_id", "gpsi-5g", "GPSI unique from 3GPP"),
    ("mtmsi-5g-idor", "5G M-TMSI object-id IDOR", "mtmsis", "Mtmsi", "mtmsi", "A1B2C3D4", "net_id", "mtmsi-5g", "M-TMSI unique from 3GPP"),
    ("stmsi-lte-idor", "LTE S-TMSI object-id IDOR", "stmsis", "Stmsi", "stmsi", "01-A1B2C3D4", "net_id", "stmsi-lte", "S-TMSI unique from EPS"),
    ("amfset-idor", "AMF Set object-id IDOR", "amfsets", "Amfset", "amfset", "310-410-1-2", "net_id", "amfset-5g", "AMF Set unique from 3GPP"),
    ("nrarfcn-idor", "NR-ARFCN object-id IDOR", "nrarfcns", "Nrarfcn", "nrarfcn", "636000", "net_id", "nrarfcn-id", "NR-ARFCN unique from 3GPP"),
    ("earfcn-idor", "EARFCN object-id IDOR", "earfcns", "Earfcn", "earfcn", "3350", "net_id", "earfcn-id", "EARFCN unique from 3GPP"),
    ("pcinr-idor", "NR PCI object-id IDOR", "pcinrs", "Pcinr", "pcinr", "321", "net_id", "pci-nr", "PCI unique from 5G NR"),
    ("trtac-idor", "Tracking Area Code object-id IDOR", "trtacs", "Trtac", "trtac", "ABC0", "net_id", "tac-eps", "TAC unique from EPS tracking"),
    ("ucac4-idor", "UCAC4 star object-id IDOR", "ucac4s", "Ucac4", "ucac4", "UCAC4 123-012345", "lab_id", "ucac4-id", "UCAC4 unique from USNO"),
    ("panstarrs-idor", "Pan-STARRS object-id IDOR", "ps1oids", "Ps1oid", "ps1oid", "PSO J053.13419-05.42602", "lab_id", "ps1-oid", "objID unique from Pan-STARRS"),
    ("bayer-idor", "Bayer designation object-id IDOR", "bayers", "Bayer", "bayer", "alp CMa", "lab_id", "bayer-id", "Bayer unique from Uranometria"),
    ("flamsteed-idor", "Flamsteed designation object-id IDOR", "flamsteeds", "Flamsteed", "flamsteed", "9 Pup", "lab_id", "flamsteed-id", "Flamsteed unique from catalog"),
    ("gliese-idor", "Gliese catalog object-id IDOR", "glieses", "Gliese", "gliese", "GJ 581", "lab_id", "gliese-id", "Gliese unique from CNS"),
    ("ross-star-idor", "Ross star object-id IDOR", "rossstars", "Rossstar", "rossstar", "Ross 154", "lab_id", "ross-star", "Ross unique from catalog"),
    ("wolf-star-idor", "Wolf star object-id IDOR", "wolfstars", "Wolfstar", "wolfstar", "Wolf 359", "lab_id", "wolf-star", "Wolf unique from catalog"),
    ("luyten-idor", "Luyten star object-id IDOR", "luytens", "Luyten", "luyten", "Luyten 726-8", "lab_id", "luyten-id", "Luyten unique from LHS"),
    ("giclas-idor", "Giclas star object-id IDOR", "giclass", "Giclas", "giclas", "G 196-3", "lab_id", "giclas-id", "Giclas unique from Lowell"),
    ("lalande-idor", "Lalande star object-id IDOR", "lalandes", "Lalande", "lalande", "Lalande 21185", "lab_id", "lalande-id", "Lalande unique from Histoire"),
    ("sao-cat-idor", "SAO catalog object-id IDOR", "saocats", "Saocat", "saocat", "SAO 151881", "lab_id", "sao-cat", "SAO unique from Smithsonian"),
    ("ppm-star-idor", "PPM star object-id IDOR", "ppmstars", "Ppmstar", "ppmstar", "PPM 171367", "lab_id", "ppm-star", "PPM unique from ARI"),
    ("toi-tess-idor", "TESS TOI object-id IDOR", "toitesss", "Toitess", "toiid", "TOI-700", "lab_id", "toi-tess", "TOI unique from TESS"),
    ("wasp-planet-idor", "WASP planet object-id IDOR", "wasps", "Wasp", "waspid", "WASP-12b", "lab_id", "wasp-pl", "WASP unique from SuperWASP"),
    ("hatp-planet-idor", "HATNet planet object-id IDOR", "hatps", "Hatp", "hatpid", "HAT-P-7b", "lab_id", "hatp-pl", "HAT-P unique from HATNet"),
    ("tres-planet-idor", "TrES planet object-id IDOR", "tress", "Tres", "tresid", "TrES-2b", "lab_id", "tres-pl", "TrES unique from transits"),
    ("corot-planet-idor", "CoRoT planet object-id IDOR", "corots", "Corot", "corotid", "CoRoT-7b", "lab_id", "corot-pl", "CoRoT unique from CNES"),
    ("kelt-planet-idor", "KELT planet object-id IDOR", "kelts", "Kelt", "keltid", "KELT-9b", "lab_id", "kelt-pl", "KELT unique from survey"),
    ("ogle-planet-idor", "OGLE microlens object-id IDOR", "ogles", "Ogle", "ogleid", "OGLE-2016-BLG-1195L", "lab_id", "ogle-pl", "OGLE unique from Warsaw"),
    ("moa-planet-idor", "MOA microlens object-id IDOR", "moas", "Moa", "moaid", "MOA-2007-BLG-192L", "lab_id", "moa-pl", "MOA unique from Nagoya"),
    ("isone-asset-idor", "ISO-NE asset object-id IDOR", "isoneas", "Isonea", "isonea", "40327", "grid_id", "isone-asset", "asset unique from ISO-NE"),
    ("wecc-path-idor", "WECC path object-id IDOR", "weccpaths", "Weccpath", "weccpath", "Path 26", "grid_id", "wecc-path", "path unique from WECC"),
    ("serc-ba-idor", "SERC BA object-id IDOR", "sercbas", "Sercba", "sercba", "SOCO", "grid_id", "serc-ba", "BA unique from SERC"),
    ("eia923-idor", "EIA-923 plant object-id IDOR", "eia923s", "Eia923", "eia923", "579", "grid_id", "eia-923", "plant unique from EIA-923"),
    ("ferc-docket-idor", "FERC docket object-id IDOR", "fercdks", "Fercdk", "fercdk", "ER24-1234-000", "grid_id", "ferc-docket", "docket unique from FERC eLibrary"),
    ("aeso-pool-idor", "AESO pool object-id IDOR", "aesopools", "Aesopool", "aesopool", "AESO-1234", "grid_id", "aeso-pool", "pool unique from AESO"),
    ("ieso-zone-idor", "IESO zone object-id IDOR", "iesozones", "Iesozone", "iesozone", "ON-ZONE-TOR", "grid_id", "ieso-zone", "zone unique from IESO"),
    ("bpa-point-idor", "BPA point object-id IDOR", "bpapoints", "Bpapoint", "bpapoint", "MIDWAY", "grid_id", "bpa-point", "point unique from BPA"),
    ("tva-bus-idor", "TVA bus object-id IDOR", "tvabuses", "Tvabus", "tvabus", "5001", "grid_id", "tva-bus", "bus unique from TVA"),
    ("nordpool-idor", "Nord Pool area object-id IDOR", "nordpools", "Nordpool", "nordpool", "SE3", "grid_id", "nordpool-id", "area unique from Nord Pool"),
    ("epex-spot-idor", "EPEX SPOT area object-id IDOR", "epexs", "Epex", "epexid", "DE-LU", "grid_id", "epex-spot", "area unique from EPEX"),
    ("omie-area-idor", "OMIE area object-id IDOR", "omies", "Omie", "omieid", "ES", "grid_id", "omie-area", "area unique from OMIE"),
    ("gme-ipex-idor", "GME IPEX object-id IDOR", "gmeipexs", "Gmeipex", "gmeipex", "IT-North", "grid_id", "gme-ipex", "zone unique from GME"),
    ("fsc-group-idor", "FSC group object-id IDOR", "fscgrps", "Fscgrp", "fscgrp", "53", "depot_id", "fsc-group", "FSC unique from FSC"),
    ("mil-std-idor", "MIL-STD object-id IDOR", "milstds", "Milstd", "milstd", "MIL-STD-188-141", "firm_id", "mil-std", "MIL-STD unique from ASSIST"),
    ("stanag-idor", "STANAG object-id IDOR", "stanags", "Stanag", "stanag", "STANAG 4586", "firm_id", "stanag-id", "STANAG unique from NATO"),
    ("fips-pub-idor", "FIPS pub object-id IDOR", "fipspubs", "Fipspub", "fipspub", "FIPS 140-3", "firm_id", "fips-pub", "FIPS unique from NIST"),
    ("nist-sp-idor", "NIST SP object-id IDOR", "nistsps", "Nistsp", "nistsp", "SP 800-53", "firm_id", "nist-sp", "SP unique from NIST"),
    ("ansi-std-idor", "ANSI standard object-id IDOR", "ansistds", "Ansistd", "ansistd", "ANSI X9.24", "firm_id", "ansi-std", "ANSI unique from ANSI"),
    ("iso-std-idor", "ISO standard object-id IDOR", "isostds", "Isostd", "isostd", "ISO/IEC 27001", "firm_id", "iso-std", "ISO unique from ISO"),
    ("iec-std-idor", "IEC standard object-id IDOR", "iecstds", "Iecstd", "iecstd", "IEC 61850", "firm_id", "iec-std", "IEC unique from IEC"),
    ("itu-rec-idor", "ITU-T rec object-id IDOR", "iturecs", "Iturec", "iturec", "ITU-T X.509", "firm_id", "itu-rec", "rec unique from ITU-T"),
    ("ieee-std-idor", "IEEE standard object-id IDOR", "ieeestds", "Ieeestd", "ieeestd", "IEEE 802.1X", "firm_id", "ieee-std", "std unique from IEEE"),
    ("etsi-ts-idor", "ETSI TS object-id IDOR", "etsitss", "Etsits", "etsits", "TS 133 501", "firm_id", "etsi-ts", "TS unique from ETSI"),
    ("ts3gpp-idor", "3GPP TS object-id IDOR", "ts3gpps", "Ts3gpp", "ts3gpp", "TS 33.501", "firm_id", "ts-3gpp", "TS unique from 3GPP"),
    ("oval-def-idor", "OVAL definition object-id IDOR", "ovaldefs", "Ovaldef", "ovaldef", "oval:org:def:1234", "lab_id", "oval-def", "OVAL unique from MITRE"),
    ("xccdf-idor", "XCCDF benchmark object-id IDOR", "xccdfs", "Xccdf", "xccdf", "xccdf_org.ssgproject.content_benchmark_RHEL8", "lab_id", "xccdf-id", "XCCDF unique from SCAP"),
    ("cce-idor", "CCE object-id IDOR", "cceids", "Cceid", "cceid", "CCE-80957-6", "lab_id", "cce-id", "CCE unique from NVD"),
    ("cci-idor", "CCI object-id IDOR", "cciids", "Cciid", "cciid", "CCI-000213", "lab_id", "cci-id", "CCI unique from DISA"),
    ("stig-rule-idor", "STIG rule object-id IDOR", "stigids", "Stigid", "stigid", "SV-204392r928517_rule", "lab_id", "stig-rule", "rule unique from DISA STIG"),
    ("nessus-plugin-idor", "Nessus plugin object-id IDOR", "nessuss", "Nessus", "nessus", "19506", "lab_id", "nessus-pl", "plugin unique from Tenable"),
    ("snort-sid-idor", "Snort SID object-id IDOR", "snortsids", "Snortsid", "snortsid", "1:2019401", "lab_id", "snort-sid", "SID unique from Snort"),
    ("yara-rule-idor", "YARA rule object-id IDOR", "yararules", "Yararule", "yararule", "win_emotet_bytecodes", "lab_id", "yara-rule", "rule unique from YARA repo"),
    ("sigma-rule-idor", "Sigma rule object-id IDOR", "sigmarules", "Sigmarule", "sigmarule", "win_susp_service_installation", "lab_id", "sigma-rule", "rule unique from SigmaHQ"),
    ("attck-tech-idor", "ATT&CK technique object-id IDOR", "attcks", "Attck", "attck", "T1059.001", "lab_id", "attck-tech", "technique unique from MITRE ATT&CK"),
    ("jstor-stable-idor", "JSTOR stable object-id IDOR", "jstors", "Jstor", "jstor", "10.2307/123456", "campus_id", "jstor-id", "stable unique from JSTOR"),
    ("philpapers-idor", "PhilPapers object-id IDOR", "philps", "Philp", "philp", "PHI-2024-1234", "campus_id", "philpapers-id", "id unique from PhilPapers"),
    ("worldbank-id-idor", "World Bank indicator object-id IDOR", "wbinds", "Wbind", "wbind", "NY.GDP.MKTP.CD", "campus_id", "wbind-id", "indicator unique from WDI"),
    ("imf-ifs-idor", "IMF IFS object-id IDOR", "imfifss", "Imfifs", "imfifs", "IFS.M.US.PMP_IX", "campus_id", "imf-ifs", "series unique from IMF"),
    ("un-symbol-idor", "UN document symbol object-id IDOR", "unsyms", "Unsym", "unsym", "A/RES/70/1", "campus_id", "un-symbol", "symbol unique from ODS"),
    ("fednow-imad-idor", "FedNow IMAD object-id IDOR", "fednows", "Fednow", "fednow", "20240115MMQFMPF000001", "bank_id", "fednow-imad", "IMAD unique from FedNow"),
    ("chips-seq-idor", "CHIPS sequence object-id IDOR", "chipsseqs", "Chipsseq", "chipsseq", "240115000001", "bank_id", "chips-seq", "seq unique from CHIPS"),
    ("tips-ecb-idor", "TIPS payment object-id IDOR", "tipsecbs", "Tipsecb", "tipsecb", "TIPS202401151234", "bank_id", "tips-ecb", "id unique from ECB TIPS"),
    ("target2-idor", "TARGET2 msg object-id IDOR", "target2s", "Target2", "target2", "TGT240115ABCDEF", "bank_id", "target2-id", "msg unique from TARGET2"),
    ("sepa-e2e-idor", "SEPA E2E object-id IDOR", "sepae2es", "Sepae2e", "sepae2e", "NOTPROVIDED-240115-1", "bank_id", "sepa-e2e", "E2E unique from EPC"),
    ("rtp-fed-idor", "RTP payment object-id IDOR", "rtpfeds", "Rtpfed", "rtpfed", "20240115TCH0000001", "bank_id", "rtp-fed", "id unique from TCH RTP"),
    ("cnaps-ncc-idor", "CNAPS NCC object-id IDOR", "cnapsnccs", "Cnapsncc", "cnapsncc", "102100099996", "bank_id", "cnaps-ncc", "NCC unique from PBOC"),
    ("iso20022-msg-idor", "ISO 20022 MsgId object-id IDOR", "iso20022s", "Iso20022", "iso20022", "MSGID-BANK-240115-0001", "bank_id", "iso20022-msg", "MsgId unique from ISO 20022"),
]

assert len(IDOR) == 80, len(IDOR)
assert len({x[0] for x in IDOR}) == 80
assert len({x[2] for x in IDOR}) == 80
assert len({x[4] for x in IDOR}) == 80
assert not ({x[0] for x in IDOR} & USED_SLUGS), {x[0] for x in IDOR} & USED_SLUGS
assert not ({x[4] for x in IDOR} & USED_LOOKUPS), {x[4] for x in IDOR} & USED_LOOKUPS
assert not ({x[2] for x in IDOR} & USED_MODS), {x[2] for x in IDOR} & USED_MODS

BFLA = [
    ("flask-httpauth-skip-delete", "Flask-HTTPAuth delete missing login_required", "py_async",
     "@app.delete('/notes/<nid>')\ndef delete(nid):\n    notes.del(nid)",
     "@app.get('/notes/<nid>')\n@auth.login_required\ndef get(nid):\n    return notes.get(nid, auth.current_user())"),
    ("flask-principal-skip-delete", "Flask-Principal delete missing Permission", "py_async",
     "@app.delete('/notes/<nid>')\ndef delete(nid):\n    notes.del(nid)",
     "@app.get('/notes/<nid>')\n@Permission(RoleNeed('user')).require()\ndef get(nid):\n    return notes.get(nid, g.identity)"),
    ("flask-security-skip-delete", "Flask-Security delete missing roles_required", "py_async",
     "@app.delete('/notes/<nid>')\ndef delete(nid):\n    notes.del(nid)",
     "@app.get('/notes/<nid>')\n@roles_required('user')\ndef get(nid):\n    return notes.get(nid, current_user)"),
    ("flask-login-skip-delete", "Flask-Login delete missing login_required", "py_async",
     "@app.delete('/notes/<nid>')\ndef delete(nid):\n    notes.del(nid)",
     "@app.get('/notes/<nid>')\n@login_required\ndef get(nid):\n    return notes.get(nid, current_user)"),
    ("drf-spectacular-skip-delete", "drf-spectacular delete missing extend_schema auth", "py_async",
     "class NoteView(DestroyAPIView):\n    authentication_classes = []",
     "class NoteView(RetrieveAPIView):\n    authentication_classes = [SessionAuthentication]"),
    ("rest-knox-skip-delete", "django-rest-knox delete missing TokenAuthentication", "py_async",
     "class NoteDelete(APIView):\n    authentication_classes = []\n    def delete(self, request, nid): notes.del(nid)",
     "class NoteGet(APIView):\n    authentication_classes = [TokenAuthentication]\n    def get(self, request, nid): return notes.get(nid, request.user)"),
    ("uvicorn-asgi-skip-delete", "uvicorn ASGI DELETE missing auth scope", "py_async",
     "if scope['method']=='DELETE': await notes.del(path)",
     "if scope['method']=='GET': user=scope['user']; return await notes.get(path, user)"),
    ("gunicorn-app-skip-delete", "Gunicorn WSGI DELETE missing environ auth", "py_async",
     "if environ['REQUEST_METHOD']=='DELETE': notes.del(path)",
     "if environ['REQUEST_METHOD']=='GET': user=environ['REMOTE_USER']; return notes.get(path, user)"),
    ("waitress-wsgi-skip-delete", "Waitress WSGI DELETE missing auth", "py_async",
     "if method=='DELETE': notes.del(path)",
     "if method=='GET': auth(environ); return notes.get(path, environ['user'])"),
    ("cheroot-wsgi-skip-delete", "Cheroot WSGI DELETE missing auth", "py_async",
     "if req.method=='DELETE': notes.del(req.path)",
     "if req.method=='GET': req.login(); return notes.get(req.path, req.user)"),
    ("meinheld-wsgi-skip-delete", "Meinheld WSGI DELETE missing auth", "py_async",
     "if environ['REQUEST_METHOD']=='DELETE': notes.del(path)",
     "if environ['REQUEST_METHOD']=='GET': return notes.get(path, environ['user'])"),
    ("bjoern-wsgi-skip-delete", "bjoern WSGI DELETE missing auth", "py_async",
     "if method=='DELETE': notes.del(path)",
     "if method=='GET': user=auth(environ); return notes.get(path, user)"),
    ("gevent-pywsgi-skip-delete", "gevent.pywsgi DELETE missing auth", "py_async",
     "if env['REQUEST_METHOD']=='DELETE': notes.del(path)",
     "if env['REQUEST_METHOD']=='GET': return notes.get(path, env.get('user'))"),
    ("eventlet-wsgi-skip-delete", "eventlet.wsgi DELETE missing auth", "py_async",
     "if environ['REQUEST_METHOD']=='DELETE': notes.del(path)",
     "if environ['REQUEST_METHOD']=='GET': return notes.get(path, environ['user'])"),
    ("lura-krakend-skip-delete", "KrakenD Lura DELETE missing auth/validator", "js_route",
     '{"endpoint": "/notes/{id}", "method": "DELETE", "extra_config": {}}',
     '{"endpoint": "/notes/{id}", "method": "GET", "extra_config": {"auth/validator": {"alg": "RS256"}}}'),
    ("tyk-mw-skip-delete", "Tyk middleware DELETE missing auth", "js_route",
     "listen_path: /notes/{id}\nmethod: DELETE\nuse_keyless: true",
     "listen_path: /notes/{id}\nmethod: GET\nauth: {auth_header_name: Authorization}"),
    ("caddy-auth-skip-delete", "Caddy DELETE outside basic_auth", "js_route",
     "handle /notes/* {\n  reverse_proxy notes:8080\n}",
     "handle /notes/* {\n  basic_auth { user hash }\n  reverse_proxy notes:8080\n}"),
    ("nginx-authreq-skip-delete", "nginx auth_request skip DELETE", "js_route",
     "location /notes/ { if ($request_method = DELETE) { proxy_pass http://notes; } }",
     "location /notes/ { auth_request /_auth; proxy_pass http://notes; }"),
    ("haproxy-acl-skip-delete", "HAProxy ACL skip DELETE", "js_route",
     "acl is_del method DELETE\nhttp-request allow if is_del",
     "http-request auth if !{ http_auth(users) }"),
    ("apache-authz-skip-delete", "Apache Require skip DELETE", "js_route",
     "<Limit DELETE>\n  Require all granted\n</Limit>",
     "<Limit GET>\n  Require valid-user\n</Limit>"),
    ("lighttpd-auth-skip-delete", "lighttpd DELETE missing auth.backend", "js_route",
     "$HTTP[\"request-method\"] == \"DELETE\" { proxy.server = ( notes ) }",
     "auth.require = ( \"/notes/\" => ( \"method\" => \"basic\" ) )"),
    ("openresty-skip-delete", "OpenResty DELETE missing access_by_lua auth", "js_route",
     "if ngx.req.get_method()=='DELETE' then notes.del() end",
     "access_by_lua_block { require('auth').check() }"),
    ("apisix-plugin-skip-delete", "APISIX DELETE missing jwt-auth plugin", "js_route",
     "uris: [/notes/*]\nmethods: [DELETE]\nplugins: {}",
     "uris: [/notes/*]\nmethods: [GET]\nplugins: { jwt-auth: {} }"),
    ("skipper-pred-skip-delete", "Skipper Path DELETE missing authFilter", "js_route",
     "r: Path(\"/notes/:id\") && Method(\"DELETE\") -> notes();",
     "r: Path(\"/notes/:id\") && Method(\"GET\") -> authFilter() -> notes();"),
    ("contour-httpproxy-skip-delete", "Contour HTTPProxy DELETE missing jwt", "js_route",
     "conditions: [{prefix: /notes}]\npermitInsecure: true",
     "conditions: [{prefix: /notes}]\nauthPolicy: {jwt: {require: true}}"),
    ("linkerd-auth-skip-delete", "Linkerd ServerAuthorization skip DELETE", "js_route",
     "spec:\n  client: unauthenticated: true\n  server: notes-delete",
     "spec:\n  client: meshTLS: {identities: ['notes.ns.serviceaccount.identity.linkerd.cluster.local']}"),
    ("consul-intent-skip-delete", "Consul intention skip DELETE", "js_route",
     "Action = \"allow\"\nSourceName = \"*\"\nDestinationName = \"notes-delete\"",
     "Action = \"allow\"\nSourceName = \"notes-ui\"\nDestinationName = \"notes\""),
    ("nomad-acl-skip-delete", "Nomad ACL skip job delete", "js_route",
     "namespace \"default\" { policy = \"write\" }  # delete job unscoped",
     "namespace \"default\" { policy = \"read\" }"),
    ("boundary-skip-delete", "Boundary target delete missing authorize-session", "js_route",
     "boundary targets delete -id ttcp_notes",
     "boundary targets authorize-session -id ttcp_notes -token env://BOUNDARY"),
    ("lunatic-skip-delete", "Lunatic process delete missing auth", "rust_ext",
     "fn delete(id: i32) { notes::del(id) }",
     "fn get(id: i32, user: User) { notes::get(id, user.id) }"),
    ("axum-login-skip-delete", "axum-login delete missing AuthSession", "rust_ext",
     "async fn delete(Path(id): Path<i32>) { notes::del(id).await }",
     "async fn get(AuthSession(user): AuthSession<User>, Path(id): Path<i32>) { notes::get(id, user.id).await }"),
    ("actix-httpauth-skip-delete", "actix-web-httpauth delete missing HttpAuthentication", "rust_ext",
     "web::resource(\"/notes/{id}\").route(web::delete().to(del))",
     "web::resource(\"/notes/{id}\").wrap(HttpAuthentication::bearer(validator)).route(web::get().to(get))"),
    ("masstransit-skip-delete", "MassTransit consumer delete missing Authorize", "js_route",
     "public Task Consume(DeleteNote m) => notes.Del(m.Id);",
     "[Authorize] public Task Consume(GetNote m) => notes.Get(m.Id, context.User);"),
    ("nservicebus-skip-delete", "NServiceBus handler delete missing identity", "js_route",
     "public Task Handle(DeleteNote m, IMessageHandlerContext c) => notes.Del(m.Id);",
     "public Task Handle(GetNote m, IMessageHandlerContext c) { c.MessageHeaders['User']; return notes.Get(m.Id, user); }"),
    ("hangfire-skip-delete", "Hangfire job delete missing DashboardAuthorization", "js_route",
     "RecurringJob.AddOrUpdate(\"del\", () => notes.Del(id), Cron.Never);",
     "DashboardOptions { Authorization = new[] { new LocalRequestsOnlyAuthorizationFilter() } }"),
    ("quartznet-skip-delete", "Quartz.NET job delete missing IJobAuth", "js_route",
     "public Task Execute(IJobExecutionContext c) => notes.Del(c.MergedJobDataMap.GetInt(\"id\"));",
     "public Task Execute(IJobExecutionContext c) { auth(c); return notes.Get(id, user); }"),
    ("blazor-circuit-skip-delete", "Blazor circuit Delete missing AuthorizeView", "js_route",
     "private async Task Delete(int id) => await notes.Del(id);",
     "[Authorize] private async Task<Note> Get(int id) => await notes.Get(id, user);"),
    ("razor-pages-skip-delete", "Razor Pages OnPostDelete missing Authorize", "js_route",
     "public IActionResult OnPostDelete(int id) { notes.Del(id); return Redirect(); }",
     "[Authorize] public IActionResult OnGet(int id) => Page(notes.Get(id, User));"),
    ("mvc5-skip-delete", "ASP.NET MVC 5 Delete missing Authorize", "js_route",
     "public ActionResult Delete(int id) { notes.Del(id); return Redirect(); }",
     "[Authorize] public ActionResult Details(int id) => View(notes.Get(id, User));"),
    ("webforms-skip-delete", "Web Forms Delete missing IsAuthenticated", "js_route",
     "protected void BtnDelete_Click(object s, EventArgs e) { notes.Del(id); }",
     "protected void Page_Load(object s, EventArgs e) { if (!User.Identity.IsAuthenticated) Response.Redirect(\"/login\"); }"),
    ("wcf-skip-delete", "WCF Delete missing ServiceAuthorization", "js_route",
     "public void Delete(int id) { notes.Del(id); }",
     "[PrincipalPermission(SecurityAction.Demand, Authenticated=true)] public Note Get(int id) => notes.Get(id, ServiceSecurityContext.Current);"),
    ("corewcf-skip-delete", "CoreWCF Delete missing OperationBehavior auth", "js_route",
     "public void Delete(int id) { notes.Del(id); }",
     "[Authorize] public Note Get(int id) => notes.Get(id, User);"),
    ("wintercms-skip-delete", "Winter CMS delete missing BackendAuth", "php_mw",
     "public function delete($id) { Note::find($id)->delete(); }",
     "public function preview($id) { BackendAuth::check(); return Note::find($id); }"),
    ("boltcms-skip-delete", "Bolt CMS delete missing isGranted", "php_mw",
     "public function delete(int $id) { $this->notes->delete($id); }",
     "public function view(int $id) { $this->isGranted('ROLE_USER'); return $this->notes->find($id); }"),
    ("processwire-skip-delete", "ProcessWire delete missing $user->isLoggedin", "php_mw",
     "$pages->delete($pages->get($id));",
     "if (!$user->isLoggedin()) throw new WirePermissionException(); $pages->get($id);"),
    ("expressionengine-skip-delete", "ExpressionEngine delete missing ee()->session", "php_mw",
     "ee()->db->delete('notes', ['id' => $id]);",
     "if (!ee()->session->userdata('member_id')) return; ee()->db->get_where('notes', ['id'=>$id]);"),
    ("concretecms-skip-delete", "Concrete CMS delete missing Permissions", "php_mw",
     "$note->delete();",
     "$p = new Permissions($note); if (!$p->canView()) throw new Exception();"),
    ("silverstripe-skip-delete", "Silverstripe delete missing canDelete", "php_mw",
     "public function delete($id) { Note::get()->byID($id)->delete(); }",
     "public function view($id) { $n = Note::get()->byID($id); return $n->canView() ? $n : $this->httpError(403); }"),
    ("worktop-skip-delete", "worktop DELETE missing reply.locals.user", "js_route",
     "export const DELETE: Handler = async (req) => notes.del(req.params.id)",
     "export const GET: Handler = async (req, context) => notes.get(req.params.id, context.user)"),
    ("sunder-skip-delete", "Sunder DELETE missing withUser", "js_route",
     "app.delete('/notes/:id', (c) => notes.del(c.params.id))",
     "app.get('/notes/:id', withUser, (c) => notes.get(c.params.id, c.user))"),
    ("pages-fn-skip-delete", "Cloudflare Pages Function DELETE missing getSession", "js_route",
     "export async function onRequestDelete({ params }) { return notes.del(params.id) }",
     "export async function onRequestGet({ params, request }) { const u = await getSession(request); return notes.get(params.id, u) }"),
    ("vercel-edge-skip-delete", "Vercel Edge DELETE missing getToken", "js_route",
     "export async function DELETE(req, { params }) { return notes.del(params.id) }",
     "export async function GET(req, { params }) { const t = await getToken({ req }); return notes.get(params.id, t) }"),
    ("netlify-fn-skip-delete", "Netlify Function DELETE missing context.clientContext", "js_route",
     "exports.handler = async (event) => { if (event.httpMethod==='DELETE') notes.del(event.queryStringParameters.id) }",
     "exports.handler = async (event, context) => { const u = context.clientContext.user; return notes.get(id, u) }"),
    ("lambda-url-skip-delete", "Lambda Function URL DELETE missing authorizer", "js_route",
     "if (event.requestContext.http.method==='DELETE') notes.del(id)",
     "const u = event.requestContext.authorizer; return notes.get(id, u)"),
    ("apigw-authorizer-skip-delete", "API Gateway DELETE missing authorizer", "js_route",
     "DELETE /notes/{id}  Authorization: NONE",
     "GET /notes/{id}  Authorization: AWS_IAM"),
    ("amplify-fn-skip-delete", "Amplify Function DELETE missing identity", "js_route",
     "exports.handler = async (event) => notes.del(event.arguments.id)",
     "exports.handler = async (event) => notes.get(event.arguments.id, event.identity.sub)"),
    ("async-rest-skip-delete", "async-rest delete missing middleware auth", "rb_filter",
     "def delete(id) = notes.del(id)",
     "def get(id) = (auth!; notes.get(id, current_user))"),
    ("protocol-http-skip-delete", "protocol-http DELETE missing middleware", "rb_filter",
     "r.delete('/notes/:id') { |r| notes.del(r.path) }",
     "r.get('/notes/:id') { |r| auth!(r); notes.get(r.path, r.user) }"),
    ("utopia-skip-delete", "Utopia delete missing current_user", "rb_filter",
     "on('DELETE') { notes.del(id) }",
     "on('GET') { current_user!; notes.get(id, current_user) }"),
    ("falcon-socketry-skip-delete", "Falcon/Socketry delete missing authenticate", "rb_filter",
     "def handle(request, id) = notes.del(id) if request.method == 'DELETE'",
     "def handle(request, id) = (request.authenticate!; notes.get(id, request.user))"),
    ("django-allauth-skip-delete", "django-allauth delete missing login_required", "py_async",
     "def delete_note(request, nid):\n    Note.objects.get(pk=nid).delete()",
     "@login_required\ndef note_detail(request, nid):\n    return Note.objects.get(pk=nid, owner=request.user)"),
    ("starlette-session-skip-delete", "Starlette SessionMiddleware DELETE missing session user", "py_async",
     "@app.route('/notes/{nid}', methods=['DELETE'])\nasync def delete(request):\n    await notes.del(request.path_params['nid'])",
     "@app.route('/notes/{nid}')\nasync def get(request):\n    u = request.session['user']; return await notes.get(request.path_params['nid'], u)"),
    ("tengine-skip-delete", "Tengine DELETE missing auth_request", "js_route",
     "location /notes/ { limit_except GET { deny all; }  # DELETE still proxied }",
     "location /notes/ { auth_request /_auth; proxy_pass http://notes; }"),
    ("angie-skip-delete", "Angie DELETE missing auth_request", "js_route",
     "location /notes/ { proxy_pass http://notes; }  # DELETE open",
     "location /notes/ { auth_request /_auth; proxy_pass http://notes; }"),
    ("unit-nginx-skip-delete", "NGINX Unit DELETE missing pass auth", "js_route",
     "\"match\": {\"uri\": \"/notes/*\", \"method\": \"DELETE\"}, \"action\": {\"pass\": \"applications/notes\"}",
     "\"match\": {\"uri\": \"/notes/*\", \"method\": \"GET\"}, \"action\": {\"pass\": \"routes/auth\"}"),
    ("docker-authz-skip-delete", "Docker authz plugin skip DELETE", "js_route",
     "AuthZReq method=DELETE /notes  allow=true",
     "AuthZReq method=GET /notes  plugin=authz-broker"),
    ("containerd-cri-skip-delete", "containerd CRI delete missing auth interceptor", "js_route",
     "RemoveContainer(id)  # no auth",
     "ListContainers(filter)  # tls client auth"),
    ("crio-skip-delete", "CRI-O delete missing auth", "js_route",
     "rpc RemovePodSandbox(id)  # open",
     "rpc ListPodSandbox()  # runtime auth"),
    ("kubelet-auth-skip-delete", "kubelet DELETE missing anonymous-auth=false", "js_route",
     "DELETE /pods/{name}  anonymous-auth=true",
     "GET /pods/{name}  authentication-token-webhook=true"),
    ("etcd-auth-skip-delete", "etcd delete missing auth-token", "js_route",
     "etcdctl del /notes/id  # auth disabled",
     "etcdctl --user root get /notes/id"),
    ("mysql-grant-skip-delete", "MySQL GRANT DELETE leftover", "sql",
     "GRANT DELETE ON notes.* TO 'anon'@'%';",
     "GRANT SELECT ON notes.* TO 'app'@'%' REQUIRE SSL;"),
    ("mongodb-role-skip-delete", "MongoDB role skip remove", "js_route",
     "db.grantRolesToUser('anon', [{role:'readWrite', db:'notes'}])  # remove open",
     "db.createRole({role:'notesReader', privileges:[{resource:{db:'notes',collection:'n'}, actions:['find']}]})"),
    ("redis-acl-skip-delete", "Redis ACL skip DEL", "js_route",
     "ACL SETUSER anon +del ~notes:*",
     "ACL SETUSER app +get ~notes:* on >pass"),
    ("opensearch-skip-delete", "OpenSearch DELETE missing security plugin", "js_route",
     "DELETE /notes/_doc/{id}  # anonymous",
     "GET /notes/_doc/{id}  plugins.security.authcz"),
    ("solr-skip-delete", "Solr update delete missing BasicAuthPlugin", "js_route",
     "POST /solr/notes/update?stream.body=<delete><id>1</id></delete>",
     "GET /solr/notes/select  authentication: {class: BasicAuthPlugin}"),
    ("neo4j-rbac-skip-delete", "Neo4j delete missing GRANT TRAVERSE", "js_route",
     "MATCH (n:Note {id:$id}) DETACH DELETE n  # no auth",
     "GRANT TRAVERSE ON GRAPH * NODES Note TO notesReader"),
    ("cassandra-role-skip-delete", "Cassandra DELETE missing GRANT", "sql",
     "DELETE FROM notes.n WHERE id = ?;  -- anon",
     "GRANT SELECT ON notes.n TO app;"),
    ("cockroach-grant-skip-delete", "CockroachDB GRANT DELETE leftover", "sql",
     "GRANT DELETE ON notes TO anon;",
     "GRANT SELECT ON notes TO app;"),
    ("pages-workers-skip-delete", "Cloudflare Worker Pages DELETE missing verify", "js_route",
     "if (request.method==='DELETE') return notes.del(id)",
     "if (request.method==='GET') { const u = await env.AUTH.verify(request); return notes.get(id, u) }"),
    ("fastly-compute-skip-delete", "Fastly Compute DELETE missing secret store auth", "js_route",
     "if (req.method=='DELETE') return notes.del(id)",
     "if (req.method=='GET') { const t = secret.get('token'); return notes.get(id, t) }"),
]

assert len(BFLA) == 80, len(BFLA)
assert len({x[0] for x in BFLA}) == 80
assert not ({x[0] for x in BFLA} & USED_SLUGS), {x[0] for x in BFLA} & USED_SLUGS
assert not ({x[0] for x in BFLA} & {x[0] for x in IDOR})

TICKETS = []
for i, plant in enumerate(PLANTS):
    tag = re.sub(r"[^a-z]", "", plant)[:3].upper()
    TICKETS.append(f"{tag}-{(i % 9) + 1}")


def py_idor_row(i: int) -> str:
    slug, surface, mod, model, lookup, sample, owner, product, bug = IDOR[i]
    plant = PLANTS[i]
    ticket = TICKETS[i]
    first = FIRST[i % 4]
    residual = RESIDUAL[i % 8]
    return (
        "    dict("
        f"slug={slug!r}, plant={plant!r}, ticket={ticket!r}, surface={surface!r}, "
        f"mod={mod!r}, model={model!r}, lookup={lookup!r}, sample={sample!r}, "
        f"owner={owner!r}, first={first!r}, residual={residual!r}, "
        f"product={product!r}, bug={ticket + ' ' + bug!r}),"
    )


def py_bfla_row(i: int) -> str:
    slug, surface, family, skip, auth = BFLA[i]
    plant = PLANTS[i]
    ticket = TICKETS[i]
    leftover = LEFTOVER[i % 3]
    return (
        "    dict("
        f"slug={slug!r}, plant={plant!r}, ticket={ticket!r}, surface={surface!r}, "
        f"family={family!r}, skip={skip!r}, auth={auth!r}, leftover={leftover!r}),"
    )


header = '''"""Extra unique IDOR/BFLA plants for authz-regression-factory r1640+.

Not leftover mill cartesian. Not JWT-claim catalog. Not r200–r1639 vesselNNNN-sys.
Not clones of r1364 geohash-cell-idor / channels-consumer-skip-delete.
Not clones of r1445–r1458 casbin/oso/keycloak clones.
Not clones of r1543 gstin-isd-idor / chi-mount-skip-delete.
Not clones of r1544 leftover3 cedar/casbin or r1560 e212-mccmnc / flask-restful.
"""
from __future__ import annotations


EXTRA_IDOR_ROWS = [
'''

bfla_header = '''
]


BFLA_ROWS = [
'''

expand_src = (EXPERIMENTS / "azr-plants-r1504.py").read_text()
idx = expand_src.index("def extra_bflas")
expand_block = expand_src[idx:]

body = (
    header
    + "\n".join(py_idor_row(i) for i in range(80))
    + bfla_header
    + "\n".join(py_bfla_row(i) for i in range(80))
    + "\n]\n\n\n"
    + expand_block
)
OUT.write_text(body)
print(f"wrote {OUT} bytes={OUT.stat().st_size} plants0={PLANTS[0]} idor0={IDOR[0][0]} bfla0={BFLA[0][0]}")
