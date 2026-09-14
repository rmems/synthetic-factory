#!/usr/bin/env python3
"""Emit experiments/azr-plants-r1544.py — unique object-id IDOR / BFLA for r1544+."""
from __future__ import annotations

import re
from pathlib import Path

EXPERIMENTS = Path(__file__).resolve().parent
OUT = EXPERIMENTS / "azr-plants-r1544.py"

USED_SLUGS: set[str] = set()
USED_PLANTS: set[str] = set()
USED_LOOKUPS: set[str] = set()
USED_MODS: set[str] = set()
for p in list(EXPERIMENTS.glob("azr-plants*.py")) + list(EXPERIMENTS.glob("azr-mill*.py")):
    if p.name in {"azr-plants-r1544.py"}:
        continue
    text = p.read_text(errors="ignore")
    USED_SLUGS.update(re.findall(r"slug=['\"]([a-z0-9-]+)['\"]", text))
    USED_PLANTS.update(re.findall(r"plant=['\"]([a-z0-9-]+)['\"]", text))
    USED_LOOKUPS.update(re.findall(r"lookup=['\"]([a-z0-9_]+)['\"]", text))
    USED_MODS.update(re.findall(r"mod=['\"]([a-z0-9_]+)['\"]", text))

PLANTS = [
    "afterbody", "aftercastle", "afterhatch", "bagreef", "bailsling", "balkpiece",
    "battenpocket", "beamclamp", "belaypin", "bightknot", "bilgestrake", "bittpin",
    "boomcrotch", "boomgallows", "bowchock", "bowroller", "breastback", "breechrope",
    "bulkclamp", "buntgasket", "cableclench", "camberkeel", "cantbeam", "capstanbar",
    "carlingbeam", "catdavitarm", "chainwale", "cheekpiece", "chockstay", "clewcringle",
    "clinchrivet", "coamingwell", "cockpitgrate", "companionhatch", "cordagecoil", "counterrail",
    "coxswainbox", "crancehoop", "cringleeye", "crosstreeband", "crowfootspan", "cunninghamhole",
    "cutwaterplate", "daggercase", "davitguy", "deadeyeplate", "deckprism", "dodgerframe",
    "dogvanestick", "downhaulblock", "dunnagebatten", "dutchmanplug", "earringcringle", "fairleadeye",
    "fiddlepin", "fishhead", "flakelocker", "flukepoint", "footstirrup", "forecastlebit",
    "stayhanger", "frapknot", "futtockband", "gaffscrew", "gammonbolt", "garboardplank",
    "gasketcoil", "gimbalring", "gooseneckpin", "grommeteye", "gunwaleclamp", "halliardblock",
    "hanksnap", "hawsewell", "helmbeam", "hitchring", "hoistblock", "holdclamp",
    "hookiron", "hornbeam",
]
assert len(PLANTS) == 80, len(PLANTS)
assert len(set(PLANTS)) == 80
clash = set(PLANTS) & USED_PLANTS
assert not clash, clash

FIRST = ["authn", "mask", "any_member", "list_scope"]
RESIDUAL = ["pdf", "export", "search", "mget", "csv", "admin", "webhook", "comments"]
LEFTOVER = ["put", "patch", "update"]

# slug, surface, mod, model, lookup, sample, owner, product, bug
IDOR = [
    ("e212-mccmnc-idor", "E.212 MCC-MNC object-id IDOR", "e212mccs", "E212mcc", "mccmnc", "310-410", "net_id", "e212-itu", "MCC-MNC unique from ITU E.212"),
    ("npanxx-lerg-idor", "LERG NPA-NXX object-id IDOR", "npanxxs", "Npanxx", "npanxx", "212-555", "telco_id", "lerg-npa", "NPA-NXX unique from LERG"),
    ("imeisv-svn-idor", "IMEISV object-id IDOR", "imeisvs", "Imeisv", "imeisv", "3569380356438090", "oem_id", "imeisv-3gpp", "IMEISV unique from 3GPP TS 23.003"),
    ("euicc-eid-idor", "eUICC EID object-id IDOR", "euicceids", "EuiccEid", "euiccid", "89049032005008800000000000000000", "oem_id", "eid-gsma", "EID unique from GSMA SGP.22"),
    ("tmsi-paging-idor", "TMSI paging object-id IDOR", "tmsipages", "Tmsipage", "tmsi", "C359F119", "net_id", "tmsi-3gpp", "TMSI unique from 3GPP"),
    ("guti-lte-idor", "LTE GUTI object-id IDOR", "ltegutis", "Lteguti", "guti", "31041000C359F119", "net_id", "guti-eps", "GUTI unique from EPS"),
    ("suci-5g-idor", "5G SUCI object-id IDOR", "suci5gs", "Suci5g", "suci", "suci-0-310-410-0-0-abcd", "net_id", "suci-5g", "SUCI unique from 3GPP 5G"),
    ("apn-ni-idor", "APN NI object-id IDOR", "apnnis", "Apnni", "apnni", "internet.carrier.mnc410.mcc310.gprs", "net_id", "apn-3gpp", "APN unique from 3GPP"),
    ("cgi-gsm-idor", "GSM CGI object-id IDOR", "gsmcgis", "Gsmcgi", "gsmcgi", "310-410-1234-56789", "net_id", "cgi-gsm", "CGI unique from GSM 03.03"),
    ("ecgi-lte-idor", "LTE ECGI object-id IDOR", "ecgislts", "Ecgilte", "ecgi", "310-410-00ABCDE", "net_id", "ecgi-lte", "ECGI unique from E-UTRAN"),
    ("nci-nr-idor", "NR Cell Identity object-id IDOR", "nrcells", "Nrcell", "nrcell", "310-410-0ABCDEF", "net_id", "nci-nr", "NCI unique from 5G NR"),
    ("tai-lte-idor", "LTE TAI object-id IDOR", "ltetais", "Ltetai", "ltetai", "310-410-ABC0", "net_id", "tai-lte", "TAI unique from EPS"),
    ("lai-gsm-idor", "GSM LAI object-id IDOR", "gsmlais", "Gsmlai", "gsmlai", "310-410-1234", "net_id", "lai-gsm", "LAI unique from GSM"),
    ("rai-gprs-idor", "GPRS RAI object-id IDOR", "gprsrais", "Gprsrai", "gprsrai", "310-410-1234-67", "net_id", "rai-gprs", "RAI unique from GPRS"),
    ("sai-umts-idor", "UMTS SAI object-id IDOR", "umtsais", "Umtsai", "umtsai", "310-410-1234-56", "net_id", "sai-umts", "SAI unique from UTRAN"),
    ("hessid-wifi-idor", "HESSID Wi-Fi object-id IDOR", "hessids", "Hessid", "hessid", "00:11:22:33:44:55", "campus_id", "hessid-ieee", "HESSID unique from IEEE 802.11u"),
    ("smdp-fqdn-idor", "SM-DP+ FQDN object-id IDOR", "smdpfqdns", "Smdpfqdn", "smdpfqdn", "smdp.rsp.example", "oem_id", "smdp-gsma", "SM-DP+ unique from GSMA"),
    ("norad-cat-idor", "NORAD catalog object-id IDOR", "noradcats", "Noradcat", "norad", "25544", "lab_id", "norad-sat", "NORAD unique from CelesTrak"),
    ("cospar-id-idor", "COSPAR designation object-id IDOR", "cospards", "Cospard", "cospar", "1998-067A", "lab_id", "cospar-id", "COSPAR unique from COSPAR"),
    ("mpc-packed-idor", "MPC packed designation object-id IDOR", "mpcs", "Mpcpack", "mpcpacked", "K23A00A", "lab_id", "mpc-packed", "packed desig unique from MPC"),
    ("naif-spk-idor", "NAIF SPK object-id IDOR", "naifspks", "Naifspk", "naifspk", "399", "lab_id", "naif-spk", "NAIF id unique from SPICE"),
    ("hipparcos-idor", "Hipparcos HIP object-id IDOR", "hipcats", "Hipcat", "hipid", "HIP 71683", "lab_id", "hipparcos-id", "HIP unique from Hipparcos"),
    ("tycho2-idor", "Tycho-2 object-id IDOR", "tyc2s", "Tyc2", "tyc2", "TYC 1234-5678-1", "lab_id", "tycho2-id", "TYC unique from Tycho-2"),
    ("gaia-source-idor", "Gaia source object-id IDOR", "gaiasrcs", "Gaiasrc", "gaiasid", "Gaia DR3 1234567890123456789", "lab_id", "gaia-src", "source_id unique from Gaia"),
    ("hd-catalog-idor", "Henry Draper object-id IDOR", "hdcats", "Hdcat", "hdnum", "HD 209458", "lab_id", "hd-cat", "HD unique from Henry Draper"),
    ("hr-yale-idor", "Yale Bright Star object-id IDOR", "hrcats", "Hrcat", "hrnum", "HR 7001", "lab_id", "hr-yale", "HR unique from Yale BSC"),
    ("messier-idor", "Messier object-id IDOR", "messiers", "Messier", "mesnum", "M31", "lab_id", "messier-id", "Messier unique from catalog"),
    ("ngc-obj-idor", "NGC object-id IDOR", "ngcobjs", "Ngcobj", "ngcnum", "NGC 224", "lab_id", "ngc-obj", "NGC unique from Dreyer"),
    ("ic-dreyer-idor", "Index Catalogue object-id IDOR", "icobjs", "Icobj", "icnum", "IC 1613", "lab_id", "ic-dreyer", "IC unique from Dreyer"),
    ("pgc-galaxy-idor", "PGC galaxy object-id IDOR", "pgcs", "Pgcgal", "pgcid", "PGC 2557", "lab_id", "pgc-gal", "PGC unique from LEDA"),
    ("twomass-idor", "2MASS object-id IDOR", "twomasss", "Twomass", "twomass", "2MASS J05351494-0523539", "lab_id", "twomass-id", "2MASS unique from IPAC"),
    ("wise-allwise-idor", "AllWISE object-id IDOR", "allwises", "Allwise", "wiseid", "WISEA J174102.78-333338.3", "lab_id", "wise-id", "AllWISE unique from IRSA"),
    ("sdss-objid-idor", "SDSS objID object-id IDOR", "sdssobjs", "Sdssobj", "sdssoid", "1237654382514995200", "lab_id", "sdss-obj", "objID unique from SDSS"),
    ("tic-tess-idor", "TESS TIC object-id IDOR", "tictesss", "Tictess", "ticid", "TIC 261136679", "lab_id", "tic-tess", "TIC unique from MAST"),
    ("kic-kepler-idor", "Kepler KIC object-id IDOR", "kickeps", "Kickep", "kicid", "KIC 8462852", "lab_id", "kic-kepler", "KIC unique from Kepler"),
    ("epic-k2-idor", "K2 EPIC object-id IDOR", "epick2s", "Epick2", "epicid", "EPIC 201367835", "lab_id", "epic-k2", "EPIC unique from K2"),
    ("koi-kepler-idor", "KOI candidate object-id IDOR", "koikeps", "Koikep", "koiid", "KOI-7016.01", "lab_id", "koi-kepler", "KOI unique from Kepler"),
    ("vsx-aavso-idor", "VSX variable object-id IDOR", "vsxaavs", "Vsxaav", "vsxid", "VSX J0535-05", "lab_id", "vsx-aavso", "VSX unique from AAVSO"),
    ("simbad-oid-idor", "SIMBAD oid object-id IDOR", "simboids", "Simboid", "simboid", "506956", "lab_id", "simbad-oid", "oid unique from CDS"),
    ("ned-objname-idor", "NED object-name object-id IDOR", "nednames", "Nedname", "nedname", "MESSIER 031", "lab_id", "ned-name", "NED name unique from IPAC"),
    ("eic-entsoe-idor", "EIC energy object-id IDOR", "eicents", "Eicent", "eiccode", "10Y1001A1001A83F", "grid_id", "eic-entsoe", "EIC unique from ENTSO-E"),
    ("nerc-cid-idor", "NERC company object-id IDOR", "nerccids", "Nerccid", "nerccid", "NCR00001", "grid_id", "nerc-cid", "NERC CID unique from CORES"),
    ("orispl-eia-idor", "EIA ORISPL object-id IDOR", "orispls", "Orispl", "orispl", "3", "grid_id", "orispl-eia", "ORISPL unique from EIA-860"),
    ("pjm-pnode-idor", "PJM pnode object-id IDOR", "pjmpnodes", "Pjmpnode", "pjmpnode", "123456789", "grid_id", "pjm-pnode", "pnode unique from PJM"),
    ("caiso-res-idor", "CAISO resource object-id IDOR", "caisores", "Caisores", "caisores", "MOSSLD_7_N001", "grid_id", "caiso-res", "resource unique from CAISO"),
    ("ercot-qse-idor", "ERCOT QSE object-id IDOR", "ercotqses", "Ercotqse", "ercotqse", "QSE123", "grid_id", "ercot-qse", "QSE unique from ERCOT"),
    ("nyiso-ptid-idor", "NYISO PTID object-id IDOR", "nyisoptids", "Nyisoptid", "nyisoptid", "61752", "grid_id", "nyiso-ptid", "PTID unique from NYISO"),
    ("miso-cpnode-idor", "MISO CPNode object-id IDOR", "misocpns", "Misocpn", "misocpn", "ALTW.WIN.1", "grid_id", "miso-cpn", "CPNode unique from MISO"),
    ("spp-bus-idor", "SPP bus object-id IDOR", "sppbuses", "Sppbus", "sppbus", "51500", "grid_id", "spp-bus", "bus unique from SPP"),
    ("oati-etag-idor", "OATI e-tag object-id IDOR", "oatietags", "Oatietag", "oatitag", "12345_ABC_F", "grid_id", "oati-etag", "e-tag unique from NAESB"),
    ("ferc-qid-idor", "FERC QID object-id IDOR", "fercqids", "Fercqid", "fercqid", "Q1234", "grid_id", "ferc-qid", "QID unique from FERC"),
    ("cage-code-idor", "CAGE code object-id IDOR", "cagecds", "Cagecd", "cagecd", "1A2B3", "firm_id", "cage-dla", "CAGE unique from DLA"),
    ("uei-sam-idor", "SAM.gov UEI object-id IDOR", "samueis", "Samuei", "samuei", "ABCDEFGHIJKL", "firm_id", "uei-sam", "UEI unique from SAM.gov"),
    ("nsn-nato-idor", "NATO NSN object-id IDOR", "nsnnatos", "Nsnnato", "nsnnato", "5305-00-123-4567", "depot_id", "nsn-nato", "NSN unique from NATO"),
    ("niin-item-idor", "NIIN item object-id IDOR", "niinitems", "Niinitem", "niincode", "00-123-4567", "depot_id", "niin-item", "NIIN unique from FLIS"),
    ("ncage-nato-idor", "NCAGE object-id IDOR", "ncagecds", "Ncagecd", "ncagecd", "K1234", "firm_id", "ncage-nato", "NCAGE unique from NSPA"),
    ("psc-fpds-idor", "PSC product object-id IDOR", "pscfpdss", "Pscfpds", "pscfpds", "D302", "firm_id", "psc-fpds", "PSC unique from FPDS"),
    ("hts-tariff-idor", "HTS tariff object-id IDOR", "htstariffs", "Htstariff", "htstariff", "8471.50.01.00", "firm_id", "hts-usitc", "HTS unique from USITC"),
    ("scheduleb-idor", "Schedule B object-id IDOR", "schedbs", "Schedb", "schedb", "8471500100", "firm_id", "schedb-census", "Schedule B unique from Census"),
    ("eccn-ear-idor", "ECCN object-id IDOR", "eccncodes", "Eccncode", "eccncode", "5A002", "firm_id", "eccn-bis", "ECCN unique from BIS"),
    ("usml-itar-idor", "USML category object-id IDOR", "usmlcats", "Usmlcat", "usmlcat", "XI(a)(1)", "firm_id", "usml-ddtc", "USML unique from ITAR"),
    ("chemrxiv-idor", "ChemRxiv preprint object-id IDOR", "chemrxivs", "Chemrxiv", "chemrx", "chemrxiv-10.26434-abc", "campus_id", "chemrxiv-id", "ChemRxiv unique from ACS"),
    ("biorxiv-idor", "bioRxiv preprint object-id IDOR", "biorxivs", "Biorxiv", "biorxiv", "10.1101/2024.01.01.123456", "campus_id", "biorxiv-id", "bioRxiv unique from CSHL"),
    ("medrxiv-idor", "medRxiv preprint object-id IDOR", "medrxivs", "Medrxiv", "medrx", "10.1101/2024.01.01.24301234", "campus_id", "medrxiv-id", "medRxiv unique from CSHL"),
    ("inspire-hep-idor", "INSPIRE-HEP object-id IDOR", "inspheps", "Insphep", "inshp", "1234567", "campus_id", "inspire-hep", "recid unique from INSPIRE"),
    ("ads-bibcode-idor", "ADS bibcode object-id IDOR", "adsbibs", "Adsbib", "adsbib", "2024ApJ...961...1A", "campus_id", "ads-bib", "bibcode unique from ADS"),
    ("eric-ed-idor", "ERIC ED object-id IDOR", "ericeds", "Ericed", "ericed", "ED123456", "campus_id", "eric-ed", "ED unique from ERIC"),
    ("ntrs-nasa-idor", "NTRS document object-id IDOR", "ntrsdocs", "Ntrsdoc", "ntrsid", "20240001234", "campus_id", "ntrs-nasa", "NTRS unique from NASA"),
    ("osti-id-idor", "OSTI ID object-id IDOR", "ostiids", "Ostiid", "ostiid", "2201234", "campus_id", "osti-id", "OSTI unique from DOE"),
    ("rfc-ietf-idor", "IETF RFC object-id IDOR", "ietfrfcs", "Ietfrfc", "rfcnum", "RFC9110", "campus_id", "rfc-ietf", "RFC unique from IETF"),
    ("cve-mitre-idor", "CVE object-id IDOR", "cvemites", "Cvemitre", "cveid", "CVE-2024-12345", "lab_id", "cve-mitre", "CVE unique from MITRE"),
    ("cwe-mitre-idor", "CWE object-id IDOR", "cwemites", "Cwemitre", "cweid", "CWE-639", "lab_id", "cwe-mitre", "CWE unique from MITRE"),
    ("capec-idor", "CAPEC object-id IDOR", "capecs", "Capec", "capecid", "CAPEC-21", "lab_id", "capec-id", "CAPEC unique from MITRE"),
    ("cpe-uri-idor", "CPE URI object-id IDOR", "cpeuris", "Cpeuri", "cpeuri", "cpe:2.3:a:vendor:prod:1.0:*:*:*:*:*:*:*", "lab_id", "cpe-nvd", "CPE unique from NVD"),
    ("ghsa-id-idor", "GHSA advisory object-id IDOR", "ghsas", "Ghsa", "ghsaid", "GHSA-xxxx-yyyy-zzzz", "lab_id", "ghsa-id", "GHSA unique from GitHub"),
    ("osv-id-idor", "OSV id object-id IDOR", "osvids", "Osvid", "osvid", "OSV-2024-1234", "lab_id", "osv-id", "OSV unique from OSV"),
    ("kev-cisa-idor", "CISA KEV object-id IDOR", "kevcias", "Kevcisa", "kevcisa", "CVE-2024-21762", "lab_id", "kev-cisa", "KEV unique from CISA"),
    ("pix-br-key-idor", "PIX key object-id IDOR", "pixkeys", "Pixkey", "pixkey", "123e4567-e89b-12d3-a456-426614174000", "bank_id", "pix-bcb", "PIX key unique from BCB"),
    ("npp-payid-idor", "NPP PayID object-id IDOR", "npppayids", "Npppayid", "payid", "merchant@example.com", "bank_id", "npp-payid", "PayID unique from NPPA"),
    ("uti-iso-idor", "UTI transaction object-id IDOR", "utisos", "Utiso", "utiiso", "AAAABBCCCCDDDDEEEE12345678901234567", "book_id", "uti-iso", "UTI unique from ISO 23897"),
]

assert len(IDOR) == 80, len(IDOR)
assert len({x[0] for x in IDOR}) == 80
assert len({x[2] for x in IDOR}) == 80
assert len({x[4] for x in IDOR}) == 80
slug_clash = {x[0] for x in IDOR} & USED_SLUGS
assert not slug_clash, slug_clash
lookup_clash = {x[4] for x in IDOR} & USED_LOOKUPS
assert not lookup_clash, lookup_clash
mod_clash = {x[2] for x in IDOR} & USED_MODS
assert not mod_clash, mod_clash

BFLA = [
    ("flask-restful-delete-bare", "Flask-RESTful delete missing reqparse auth", "py_async",
     "@ns.route('/<nid>')\nclass Note:\n    def delete(self, nid):\n        Note.query.get(nid).delete()",
     "@ns.route('/<nid>')\nclass Note:\n    @auth.login_required\n    def get(self, nid):\n        return Note.query.get(nid)"),
    ("apiflask-delete-bare", "APIFlask delete missing auth_required", "py_async",
     "@app.delete('/notes/<nid>')\ndef delete(nid):\n    db.delete(nid)",
     "@app.get('/notes/<nid>')\n@app.auth_required(auth)\ndef get(nid):\n    return db.get(nid, g.user)"),
    ("microdot-delete-bare", "Microdot delete missing request.g.user", "py_async",
     "@app.delete('/notes/<nid>')\nasync def delete(request, nid):\n    await notes.del_(nid)",
     "@app.get('/notes/<nid>')\nasync def get(request, nid):\n    u = request.g.user; return await notes.get(nid, u)"),
    ("picoweb-delete-bare", "picoweb delete missing login", "py_async",
     "@app.route('/notes', methods=['DELETE'])\ndef delete(req, resp):\n    notes.del(req.qs)",
     "@app.route('/notes')\ndef get(req, resp):\n    auth(req); notes.get(req.qs)"),
    ("pantherpy-delete-bare", "Panther.py delete missing Guard", "py_async",
     "@app.delete('/notes/{nid}')\nasync def delete(nid: str):\n    await Note.delete(nid)",
     "@app.get('/notes/{nid}')\n@Guard(IsAuthenticated)\nasync def get(nid: str):\n    return await Note.get(nid)"),
    ("piccolo-api-delete-bare", "Piccolo API delete missing PiccoloCRUD auth", "py_async",
     "NoteCRUD = PiccoloCRUD(Note, allowed_methods=['delete'])",
     "NoteCRUD = PiccoloCRUD(Note, read_only=False, allowed_methods=['get'])\nNoteCRUD.auth = SessionAuth()"),
    ("goframe-delete-bare", "GoFrame DELETE missing middleware", "go_mw",
     "s.BindHandler('DELETE:/notes/:id', h.Delete)",
     "s.Use(auth).BindHandler('GET:/notes/:id', h.Get)"),
    ("hertz-delete-bare", "CloudWeGo Hertz DELETE missing auth mw", "go_mw",
     "r.DELETE('/notes/:id', h.Delete)",
     "r.Use(authMw); r.GET('/notes/:id', h.Get)"),
    ("kitex-delete-bare", "CloudWeGo Kitex delete missing middleware", "go_mw",
     "func (s *Svc) DeleteNote(ctx context.Context, id int64) error { return notes.Del(id) }",
     "func (s *Svc) GetNote(ctx context.Context, id int64) (*Note, error) { u := kitexmw.User(ctx); return notes.Get(id, u) }"),
    ("ozzo-routing-delete-bare", "ozzo-routing DELETE missing handlers.Auth", "go_mw",
     "r.Delete('/notes/<id>', h.Delete)",
     "r.Get('/notes/<id>', auth, h.Get)"),
    ("huma-delete-bare", "Huma DELETE missing security", "go_mw",
     "huma.Register(api, huma.Operation{Method: http.MethodDelete, Path: '/notes/{id}'}, h.Delete)",
     "huma.Register(api, huma.Operation{Method: http.MethodGet, Path: '/notes/{id}', Security: []map[string][]string{{'bearer': {}}}}, h.Get)"),
    ("oapi-codegen-skip-delete", "oapi-codegen delete missing StrictHandler auth", "go_mw",
     "func (s Server) DeleteNote(ctx echo.Context, id int) error { return notes.Del(id) }",
     "func (s Server) GetNote(ctx echo.Context, id int) error { u := ctx.Get('user'); return notes.Get(id, u) }"),
    ("grpc-gateway-skip-delete", "grpc-gateway DELETE missing auth interceptor", "go_mw",
     "mux.Handle('DELETE', '/v1/notes/{id}', h.Delete)",
     "mux.Handle('GET', '/v1/notes/{id}', gwruntime.WithMetadata(authMD), h.Get)"),
    ("trillium-delete-bare", "Trillium delete missing conn.auth", "rust_ext",
     "async fn delete(conn: Conn) -> Conn { notes::del(conn.param('id')) }",
     "async fn get(conn: Conn) -> Conn { let u = conn.auth()?; notes::get(conn.param('id'), u) }"),
    ("dropshot-delete-bare", "Dropshot delete missing endpoint auth", "rust_ext",
     "#[endpoint(method = DELETE, path = '/notes/{id}')]\nasync fn delete(rqctx: RequestContext<Ctx>, path: Path<Id>) { notes::del(path.id).await }",
     "#[endpoint(method = GET, path = '/notes/{id}')]\nasync fn get(rqctx: RequestContext<Ctx>, path: Path<Id>) { rqctx.context().auth()?; notes::get(path.id).await }"),
    ("pavex-delete-bare", "Pavex delete missing RequestHead auth", "rust_ext",
     "pub fn delete(id: Path<i32>) -> StatusCode { notes::del(*id); StatusCode::NO_CONTENT }",
     "pub fn get(id: Path<i32>, user: User) -> Json<Note> { notes::get(*id, user.id).into() }"),
    ("saphir-delete-bare", "Saphir delete missing guard", "rust_ext",
     "#[delete('/{id}')]\nasync fn delete(id: i32) { notes::del(id).await }",
     "#[get('/{id}')]\n#[guard(AuthGuard)]\nasync fn get(id: i32, user: User) { notes::get(id, user.id).await }"),
    ("graphul-delete-bare", "Graphul delete missing middleware", "rust_ext",
     "app.delete('/notes/:id', |id: i32| async move { notes::del(id) });",
     "app.middleware(auth); app.get('/notes/:id', |id: i32, u: User| async move { notes::get(id, u.id) });"),
    ("tonic-skip-delete", "Tonic delete missing interceptor", "rust_ext",
     "async fn delete_note(&self, req: Request<Id>) -> Result<Response<()>, Status> { self.notes.del(req.into_inner().id).await; Ok(Response::new(())) }",
     "async fn get_note(&self, req: Request<Id>) -> Result<Response<Note>, Status> { let u = intercept_user(&req)?; self.notes.get(req.into_inner().id, u).await }"),
    ("zio-http-delete-bare", "ZIO HTTP delete missing Middleware.bearerAuth", "scala_mw",
     "Method.DELETE / 'notes / int('id) -> handler { (id: Int) => notes.del(id) }",
     "Method.GET / 'notes / int('id) @@ Middleware.bearerAuth(u => notes.get(id, u))"),
    ("finch-delete-bare", "Finch delete missing header auth", "scala_mw",
     "delete('notes' :: path[Int]) { id: Int => notes.del(id) }",
     "get('notes' :: path[Int] :: header('Authorization')) { (id: Int, tok: String) => notes.get(id, tok) }"),
    ("finagle-skip-delete", "Finagle delete missing Filter.Auth", "scala_mw",
     "DELETE /notes/:id => notes.del(id)",
     "GET /notes/:id :: AuthFilter => notes.get(id, user)"),
    ("scalatra-delete-bare", "Scalatra delete missing before() auth", "scala_mw",
     "delete('/notes/:id') { notes.del(params('id')) }",
     "before('/notes/:id') { halt(401) unless user }; get('/notes/:id') { notes.get(params('id'), user) }"),
    ("liftweb-skip-delete", "Lift delete missing S.loggedIn_?", "scala_mw",
     "def delete(id: String): Unit = Note.delete(id)",
     "def get(id: String) = { S.loggedIn_? ; Note.get(id, User.current) }"),
    ("caliban-skip-delete", "Caliban delete missing wrapper auth", "scala_mw",
     "case class Mutations(deleteNote: Int => UIO[Boolean])",
     "case class Queries(note: Int => URIO[User, Note])"),
    ("sangria-skip-delete", "Sangria delete missing DeferredResolver auth", "scala_mw",
     "Field('deleteNote', BooleanType, arguments = idArg :: Nil, resolve = c => notes.del(c.arg(idArg)))",
     "Field('note', NoteType, arguments = idArg :: Nil, resolve = c => { auth(c.ctx); notes.get(c.arg(idArg), c.ctx.user) })"),
    ("undertow-skip-delete", "Undertow DELETE missing SecurityContext", "java_ann",
     "exchange.getRequestMethod() == Methods.DELETE -> notes.del(id)",
     "exchange.getSecurityContext().isAuthenticated() && GET -> notes.get(id, account)"),
    ("jetty-servlet-skip-delete", "Jetty servlet doDelete missing login", "java_ann",
     "protected void doDelete(HttpServletRequest req, HttpServletResponse resp) { notes.del(req.getPathInfo()); }",
     "protected void doGet(HttpServletRequest req, HttpServletResponse resp) { req.authenticate(resp); notes.get(req.getPathInfo(), req.getUserPrincipal()); }"),
    ("wildfly-skip-delete", "WildFly JAX-RS delete missing @RolesAllowed", "java_ann",
     "@DELETE @Path('{id}') public void delete(@PathParam('id') long id) { notes.del(id); }",
     "@GET @Path('{id}') @RolesAllowed('user') public Note get(@PathParam('id') long id) { return notes.get(id, user); }"),
    ("openliberty-skip-delete", "Open Liberty delete missing @RolesAllowed", "java_ann",
     "@DELETE @Path('/notes/{id}') public Response delete(@PathParam('id') long id) { notes.del(id); return Response.noContent().build(); }",
     "@GET @RolesAllowed('users') public Note get(@PathParam('id') long id, @Context SecurityContext sc) { return notes.get(id, sc.getUserPrincipal()); }"),
    ("vaadin-skip-delete", "Vaadin delete missing BeforeEnterObserver auth", "java_ann",
     "public void delete(long id) { notes.del(id); }",
     "public Note get(long id) { UI.getCurrent().getSession().getAttribute(User.class); return notes.get(id, user); }"),
    ("wicket-skip-delete", "Wicket delete missing AuthorizeInstantiation", "java_ann",
     "public void onDelete(long id) { notes.del(id); }",
     "@AuthorizeInstantiation('USER') public NotePage(long id) { notes.get(id, getUser()); }"),
    ("tapestry-skip-delete", "Tapestry onDelete missing @RequireAuthentication", "java_ann",
     "void onActionFromDelete(long id) { notes.del(id); }",
     "@RequireAuthentication Note onActivate(long id) { return notes.get(id, user); }"),
    ("jsf-skip-delete", "JSF delete missing isUserInRole", "java_ann",
     "public void delete(long id) { notes.del(id); }",
     "public Note get(long id) { if (!facesContext.getExternalContext().isUserInRole('user')) throw new NotFound(); return notes.get(id, user); }"),
    ("fastendpoints-delete-bare", "FastEndpoints Delete missing PreProcessor auth", "js_route",
     "public override async Task HandleAsync(DelReq r, CancellationToken c) { await notes.Del(r.Id); }",
     "public override void Configure() { Get('/notes/{id}'); AuthSchemes('Bearer'); }"),
    ("owin-skip-delete", "OWIN DELETE missing UseJwtBearer", "js_route",
     "app.MapDelete('/notes/{id}', (int id) => notes.Del(id));",
     "app.MapGet('/notes/{id}', (int id, ClaimsPrincipal u) => notes.Get(id, u)).RequireAuthorization();"),
    ("katana-skip-delete", "Katana Web API delete missing [Authorize]", "js_route",
     "public IHttpActionResult Delete(int id) { notes.Del(id); return Ok(); }",
     "[Authorize] public IHttpActionResult Get(int id) { return Ok(notes.Get(id, User)); }"),
    ("webapi2-skip-delete", "ASP.NET Web API 2 delete missing Authorize", "js_route",
     "[HttpDelete] public void Delete(int id) { notes.Del(id); }",
     "[HttpGet, Authorize] public Note Get(int id) { return notes.Get(id, User.Identity.Name); }"),
    ("orleans-grain-skip-delete", "Orleans grain Delete missing Authorize", "js_route",
     "public Task Delete() => notes.Del(this.GetPrimaryKey());",
     "public Task<Note> Get() { RequestContext.Get('user'); return notes.Get(this.GetPrimaryKey(), user); }"),
    ("signalr-hub-skip-delete", "SignalR hub Delete missing [Authorize]", "js_route",
     "public Task Delete(int id) => notes.Del(id);",
     "[Authorize] public Task<Note> Get(int id) => notes.Get(id, Context.User);"),
    ("grpc-dotnet-skip-delete", "grpc-dotnet Delete missing Authorize interceptor", "js_route",
     "public override Task<Empty> Delete(Id r, ServerCallContext c) { notes.Del(r.Id); return Task.FromResult(new Empty()); }",
     "[Authorize] public override Task<NoteMsg> Get(Id r, ServerCallContext c) => notes.Get(r.Id, c.GetHttpContext().User);"),
    ("mezzio-skip-delete", "Mezzio delete missing AuthorizationMiddleware", "php_mw",
     "$app->delete('/notes/{id}', DeleteHandler::class);",
     "$app->get('/notes/{id}', [AuthorizationMiddleware::class, GetHandler::class]);"),
    ("nette-presenter-skip-delete", "Nette presenter actionDelete missing isLoggedIn", "php_mw",
     "public function actionDelete(int $id): void { $this->notes->del($id); }",
     "public function actionShow(int $id): void { $this->user->isLoggedIn() || $this->error(); $this->notes->get($id, $this->user); }"),
    ("thinkphp-skip-delete", "ThinkPHP delete missing middleware auth", "php_mw",
     "public function delete($id) { Note::destroy($id); }",
     "public function read($id) { $this->middleware('auth'); return Note::find($id); }"),
    ("swoft-skip-delete", "Swoft delete missing AuthMiddleware", "php_mw",
     "#[RequestMapping('/notes/{id}', method='DELETE')]\npublic function delete(int $id) { Note::del($id); }",
     "#[Middleware(AuthMiddleware::class)]\n#[RequestMapping('/notes/{id}', method='GET')]\npublic function get(int $id) { return Note::get($id, context()->get('user')); }"),
    ("easyswoole-skip-delete", "EasySwoole delete missing Session auth", "php_mw",
     "function delete() { Note::del($this->request()->getQueryParam('id')); }",
     "function get() { $u = Session::get('user'); return Note::get($this->request()->getQueryParam('id'), $u); }"),
    ("craftcms-skip-delete", "Craft CMS delete missing requireLogin", "php_mw",
     "public function actionDelete(int $id) { Note::findOne($id)->delete(); }",
     "public function actionView(int $id) { $this->requireLogin(); return Note::findOne(['id'=>$id,'ownerId'=>Craft::$app->user->id]); }"),
    ("typo3-skip-delete", "TYPO3 delete missing backend user check", "php_mw",
     "public function deleteAction(int $id): void { $this->noteRepo->remove($id); }",
     "public function showAction(int $id): Note { $GLOBALS['BE_USER']->check('tables', 'tx_notes'); return $this->noteRepo->find($id, $GLOBALS['BE_USER']); }"),
    ("contao-skip-delete", "Contao delete missing TokenChecker", "php_mw",
     "public function delete(int $id): void { NoteModel::findByPk($id)->delete(); }",
     "public function show(int $id): NoteModel { System::getContainer()->get('security.helper')->isGranted('ROLE_MEMBER'); return NoteModel::findByPk($id); }"),
    ("october-skip-delete", "October CMS delete missing BackendAuth", "php_mw",
     "public function delete($id) { Note::find($id)->delete(); }",
     "public function preview($id) { BackendAuth::check(); return Note::find($id); }"),
    ("statamic-skip-delete", "Statamic delete missing can:delete-notes", "php_mw",
     "Route::delete('/notes/{id}', fn ($id) => Note::find($id)->delete());",
     "Route::get('/notes/{id}', fn ($id) => Note::find($id))->middleware('can:view-notes');"),
    ("kirby-skip-delete", "Kirby delete missing $kirby->user()", "php_mw",
     "$kirby->route('DELETE /notes/(:any)', fn ($id) => $page->delete());",
     "$kirby->route('GET /notes/(:any)', fn ($id) => $kirby->user() ? $page : false);"),
    ("gravcms-skip-delete", "Grav delete missing Authorize", "php_mw",
     "public function deleteTask() { $this->pages->delete($id); }",
     "public function showTask() { if (!$this->authorize('admin.login')) return; return $this->pages->get($id); }"),
    ("woocommerce-skip-delete", "WooCommerce REST delete missing permission_callback", "php_mw",
     "register_rest_route('wc/v3', '/notes/(?P<id>[\\d]+)', ['methods'=>'DELETE','callback'=>'wc_delete_note','permission_callback'=>'__return_true']);",
     "register_rest_route('wc/v3', '/notes/(?P<id>[\\d]+)', ['methods'=>'GET','permission_callback'=>'wc_rest_check_user']);"),
    ("oxid-skip-delete", "OXID eShop delete missing oxuser check", "php_mw",
     "public function deleteNote($id) { oxNew(Note::class)->delete($id); }",
     "public function getNote($id) { $this->getUser() || oxRegistry::getUtils()->redirect(); return oxNew(Note::class)->load($id); }"),
    ("tinyhttp-delete-bare", "tinyhttp DELETE missing auth", "js_route",
     "app.delete('/notes/:id', (req, res) => notes.del(req.params.id))",
     "app.get('/notes/:id', auth, (req, res) => notes.get(req.params.id, req.user))"),
    ("itty-router-delete-bare", "itty-router DELETE missing withUser", "js_route",
     "router.delete('/notes/:id', ({ params }) => notes.del(params.id))",
     "router.get('/notes/:id', withUser, ({ params, user }) => notes.get(params.id, user))"),
    ("opine-delete-bare", "Opine DELETE missing auth mw", "js_route",
     "app.delete('/notes/:id', (req, res) => notes.del(req.params.id))",
     "app.get('/notes/:id', auth, (req, res) => notes.get(req.params.id, req.user))"),
    ("drash-delete-bare", "Drash DELETE missing before_request auth", "js_route",
     "public DELETE() { return this.notes.del(this.request.path_params.id) }",
     "public GET() { this.auth(); return this.notes.get(this.request.path_params.id, this.user) }"),
    ("alosaur-delete-bare", "Alosaur delete missing @UseGuard", "js_route",
     "@Delete('/:id')\nasync delete(@Param('id') id: string) { return Note.delete(id) }",
     "@Get('/:id')\n@UseGuard(AuthGuard)\nasync get(@Param('id') id: string, @User() u: User) { return Note.get(id, u) }"),
    ("pogo-delete-bare", "Pogo DELETE missing h.authenticated", "js_route",
     "handler: { delete(request) { return notes.del(request.params.id) } }",
     "handler: { get(request) { request.authenticated(); return notes.get(request.params.id, request.user) } }"),
    ("servest-delete-bare", "Servest DELETE missing createAuth", "js_route",
     "router.handle('DELETE', '/notes/:id', async (req) => notes.del(req.match.id))",
     "router.handle('GET', '/notes/:id', createAuth(async (req) => notes.get(req.match.id, req.user)))"),
    ("abc-deno-delete-bare", "abc (Deno) DELETE missing middleware", "js_route",
     "app.delete('/notes/:id', (c) => notes.del(c.params.id))",
     "app.get('/notes/:id', auth, (c) => notes.get(c.params.id, c.request.user))"),
    ("falconrb-delete-bare", "Falcon (Ruby) delete missing authenticate", "rb_filter",
     "on :delete do\n  Note[id].destroy\nend",
     "on :get do\n  authenticate!\n  Note[id]\nend"),
    ("hanami-api-delete-bare", "Hanami API delete missing before :authenticate", "rb_filter",
     "def handle(*)\n  note_repo.delete(params[:id])\nend",
     "before :authenticate!\ndef handle(*)\n  note_repo.find(params[:id], current_user)\nend"),
    ("cramp-delete-bare", "Cramp delete missing session", "rb_filter",
     "def delete\n  Note.delete(params[:id]); render :end\nend",
     "def get\n  halt 401 unless session[:user]; render :json, Note[params[:id]]\nend"),
    ("action-policy-skip-delete", "Action Policy skip destroy?", "rb_filter",
     "def destroy\n  @note.destroy\nend",
     "def show\n  authorize! @note, to: :show?\nend"),
    ("cancancan-skip-delete", "CanCanCan skip load_and_authorize_resource on destroy", "rb_filter",
     "skip_load_and_authorize_resource only: :destroy\ndef destroy; @note.destroy; end",
     "load_and_authorize_resource\ndef show; end"),
    ("rack-auth-skip-delete", "Rack DELETE missing Rack::Auth", "rb_filter",
     "map '/notes' do\n  delete { |id| Note[id].destroy }\nend",
     "use Rack::Auth::Basic\nget { |id| Note[id] }"),
    ("async-http-delete-bare", "async-http delete missing middleware auth", "rb_filter",
     "r.delete('/notes/:id') { |r| notes.del(r.path) }",
     "r.get('/notes/:id') { |r| auth!(r); notes.get(r.path, r.user) }"),
    ("go-openapi-skip-delete", "go-openapi delete missing principal", "go_mw",
     "func (h *H) DeleteNote(params notes.DeleteParams) middleware.Responder { notes.Del(*params.ID); return notes.NewDeleteNoContent() }",
     "func (h *H) GetNote(params notes.GetParams, p *models.Principal) middleware.Responder { return notes.Get(*params.ID, p) }"),
    ("hyper-service-delete-bare", "hyper service DELETE missing auth header", "rust_ext",
     "if req.method() == Method::DELETE { notes::del(id).await; }",
     "if req.method() == Method::GET { let u = auth(req.headers())?; notes::get(id, u).await; }"),
    ("tower-http-skip-delete", "tower-http DELETE outside ValidateRequestHeader", "rust_ext",
     "route('/notes/:id', delete(del_note))",
     "route('/notes/:id', get(get_note)).layer(ValidateRequestHeader::bearer('user'))"),
    ("utoipa-skip-delete", "utoipa path delete missing security", "rust_ext",
     "#[utoipa::path(delete, path = '/notes/{id}')]\nasync fn delete(Path(id): Path<i32>) { Note::delete(id).await }",
     "#[utoipa::path(get, path = '/notes/{id}', security(('bearer' = [])) )]\nasync fn get(Path(id): Path<i32>, user: User) { Note::get(id, user.id).await }"),
    ("okapi-skip-delete", "Rocket okapi delete missing OpenApiFromRequest", "rust_ext",
     "#[delete('/notes/<id>')]\nfn delete(id: i32) { notes::del(id) }",
     "#[get('/notes/<id>')]\nfn get(id: i32, user: User) { notes::get(id, user.id) }"),
    ("paperclip-skip-delete", "paperclip delete missing SecurityAddon", "rust_ext",
     "api.delete('/notes/{id}', del_op);",
     "api.get('/notes/{id}', get_op).with(SecurityAddon::new());"),
    ("aspnet-minimal-skip-delete", "ASP.NET Minimal DELETE missing RequireAuthorization", "js_route",
     "app.MapDelete('/notes/{id}', (int id) => notes.Del(id));",
     "app.MapGet('/notes/{id}', (int id, ClaimsPrincipal u) => notes.Get(id, u)).RequireAuthorization();"),
    ("wolverine-skip-delete", "Wolverine handler delete missing [Authorize]", "js_route",
     "public static Task Handle(DeleteNote cmd) => notes.Del(cmd.Id);",
     "[Authorize] public static Task<Note> Handle(GetNote q, IUser u) => notes.Get(q.Id, u);"),
    ("endpoints4s-skip-delete", "endpoints4s delete missing authenticated", "scala_mw",
     "deleteNote: Endpoint[Int, Unit] = delete(path / 'notes' / segment[Int]())",
     "getNote: Endpoint[Int, Note] = authenticated(get(path / 'notes' / segment[Int]()))"),
    ("helidon-se-skip-delete", "Helidon SE delete missing SecurityFeature", "java_ann",
     "routing.delete('/notes/{id}', (req, res) -> notes.del(req.path().param('id')))",
     "routing.get('/notes/{id}', SecurityFeature.authenticate(), (req, res) -> notes.get(req.path().param('id'), req.security().user()))"),
]

assert len(BFLA) == 80, len(BFLA)
assert len({x[0] for x in BFLA}) == 80
bfla_clash = {x[0] for x in BFLA} & USED_SLUGS
assert not bfla_clash, bfla_clash
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


header = '''"""Extra unique IDOR/BFLA plants for authz-regression-factory r1544+.

Not leftover mill cartesian. Not JWT-claim catalog. Not r200–r1543 vesselNNNN-sys.
Not clones of r1364 geohash-cell-idor / channels-consumer-skip-delete.
Not clones of r1445–r1458 casbin/oso/keycloak clones.
Not clones of r1543 gstin-isd-idor / chi-mount-skip-delete.
"""
from __future__ import annotations


EXTRA_IDOR_ROWS = [
'''

bfla_header = '''
]


BFLA_ROWS = [
'''

footer = '''
]


def extra_bflas(H):
    return [H(**_expand_bfla(row)) for row in BFLA_ROWS]


def _expand_bfla(row: dict) -> dict:
    plant = row["plant"]
    ticket = row["ticket"]
    slug = row["slug"]
    fw = row["surface"].split()[0]
    family = row["family"]
    skip = row["skip"]
    auth = row["auth"]
    leftover = row["leftover"]
    tag = ticket.split("-")[0].lower()
    src = f"src/{tag}_notes.py"
    handler = src
    test = f"tests/test_{tag}_delete.py"
    test_fn = "test_viewer_delete_403"
    src_fn = "delete"
    leftover_fn = leftover
    companion_path = f"src/{tag}_acl.py"
    src_obs = f"{skip}\\n    # {ticket} {fw} delete skip\\n"
    handler_obs = f"{auth}\\n"
    inspect_obs = f"{src}: {src_fn} skip\\n{test}: {test_fn}\\n"
    test_obs = (
        "def test_viewer_delete_403(client, viewer, note):\\n"
        "    client.login(viewer)\\n"
        '    assert client.delete(f"/notes/{note.id}").status_code == 403\\n'
    )
    first_apply = f"{fw} auth on list"
    first_path = src
    first_old = "def index():\\n    return Note.list()"
    first_new = f"def index():\\n    require_user()\\n    return Note.list()  # {tag} list"
    first_obs = f"list gated; {src_fn} leftover skip"
    reflection = (
        f"{fw} list auth does not wrap delete. Gate {src_fn} plus owner, leave {leftover} if still skipped."
    )
    plan_change = f"auth on {src_fn}; owner abort"
    grep_pat = f"{src_fn}|{leftover_fn}"
    grep_obs = f"{src}: {src_fn} skip\\n"
    legacy_path = src
    legacy_hint = f"{src_fn} skip"
    legacy_obs = src_obs
    legacy_old = skip
    legacy_new = (
        f"{auth}\\n"
        f"    n = Note.get(nid)\\n"
        f"    if n.owner_id != user.id: abort(403)\\n"
        f"    n.delete()  # {ticket} owner"
    )
    legacy_edit_obs = f"{src_fn} auth+owner"
    companion_old = "def owns(nid, uid): return True"
    companion_new = (
        "def owns(nid, uid):\\n"
        "    n = Note.get_raw(nid)\\n"
        "    return n is not None and n.owner_id == uid"
    )
    companion_obs = "owner"
    extra_fn = f"test_viewer_{leftover}_403"
    extra_old = "def test_viewer_delete_403(client, viewer, note):"
    extra_new = (
        f'@pytest.mark.xfail(reason="handoff: {leftover} still skipped", strict=False)\\n'
        f"def {extra_fn}(client, viewer, note):\\n"
        "    client.login(viewer)\\n"
        f'    assert client.{leftover if leftover != "update" else "put"}(f"/notes/{{note.id}}", json={{}}).status_code == 403\\n'
        "\\n"
        "def test_viewer_delete_403(client, viewer, note):"
    )
    extra_obs = f"xfails {leftover} leftover"
    handoff_path = src
    handoff_obs = f"{skip.replace('delete', leftover, 1) if 'delete' in skip.lower() else skip}\\n    # {leftover} still skipped\\n"
    if leftover not in handoff_obs.lower() and leftover not in skip.lower():
        handoff_obs = f"# {leftover} still skipped\\n{skip}\\n"
    handoff_hint = f"{leftover} still skipped"
    residual = handoff_hint
    residual_path = src
    residual_pat = leftover_fn
    residual_obs = handoff_obs
    residual_refl = f"{src_fn} gated. {leftover} still skipped."
    leave_cmd = f"echo {ticket} handoff {fw} {leftover} skipped"
    leave_obs = f"{ticket} handoff {fw} {leftover} skipped"
    goal = (
        f"{plant}-notes DELETE /notes/{{id}} is 200 for a viewer because {fw} {src_fn} skips auth. "
        f"Require auth without 403ing owners. Leave a handoff if {leftover} still skips."
    )
    plan = f"{first_apply} and rerun {test}."
    outcome = (
        f"List auth left {src_fn} skipped. Plan change: auth+owner on {src_fn}. "
        f"Partial: {leftover} leftover (xfail handoff)."
    )
    return dict(
        slug=slug,
        plant=plant,
        surface=row["surface"],
        src=src,
        src_fn=src_fn,
        handler=handler,
        test=test,
        test_fn=test_fn,
        bug_hint=f"{fw} {src_fn} skips auth; list/get uses auth",
        inspect_obs=inspect_obs,
        src_obs=src_obs,
        handler_obs=handler_obs,
        test_obs=test_obs,
        first_apply=first_apply,
        first_path=first_path,
        first_old=first_old,
        first_new=first_new,
        first_obs=first_obs,
        reflection=reflection,
        plan_change=plan_change,
        grep_pat=grep_pat,
        grep_obs=grep_obs,
        legacy_path=legacy_path,
        legacy_hint=legacy_hint,
        legacy_obs=legacy_obs,
        legacy_old=skip,
        legacy_new=legacy_new,
        legacy_edit_obs=legacy_edit_obs,
        companion_path=companion_path,
        companion_old=companion_old,
        companion_new=companion_new,
        companion_obs=companion_obs,
        extra_fn=extra_fn,
        extra_old=extra_old,
        extra_new=extra_new,
        extra_obs=extra_obs,
        handoff_path=handoff_path,
        handoff_obs=handoff_obs,
        handoff_hint=handoff_hint,
        residual=residual,
        residual_path=residual_path,
        residual_pat=residual_pat,
        residual_obs=residual_obs,
        residual_refl=residual_refl,
        leave_cmd=leave_cmd,
        leave_obs=leave_obs,
        ticket=ticket,
        goal=goal,
        plan=plan,
        outcome=outcome,
    )
'''

# footer is a template that must be real Python in the OUTPUT file.
# The version above escaped newlines for the generator string accidentally.
# Emit _expand_bfla by copying from azr-plants-r1504.py instead.

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
print(f"wrote {OUT} bytes={OUT.stat().st_size} idor={len(IDOR)} bfla={len(BFLA)}")
