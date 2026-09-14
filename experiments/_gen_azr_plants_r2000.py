#!/usr/bin/env python3
"""Emit experiments/azr-plants-r2000.py — unique object-id IDOR / BFLA for r2000+."""
from __future__ import annotations

import re
from pathlib import Path

EXPERIMENTS = Path(__file__).resolve().parent
OUT = EXPERIMENTS / "azr-plants-r2000.py"

USED_SLUGS: set[str] = set()
USED_PLANTS: set[str] = set()
USED_LOOKUPS: set[str] = set()
USED_MODS: set[str] = set()
for p in list(EXPERIMENTS.glob("azr-plants*.py")) + list(EXPERIMENTS.glob("azr-mill*.py")):
    if p.name == "azr-plants-r2000.py":
        continue
    text = p.read_text(errors="ignore")
    USED_SLUGS.update(re.findall(r"slug=['\"]([a-z0-9-]+)['\"]", text))
    USED_PLANTS.update(re.findall(r"plant=['\"]([a-z0-9-]+)['\"]", text))
    USED_LOOKUPS.update(re.findall(r"lookup=['\"]([a-z0-9_]+)['\"]", text))
    USED_MODS.update(re.findall(r"mod=['\"]([a-z0-9_]+)['\"]", text))

PREFIX = [f"azs{i:02d}" for i in range(80)]
PLANTS = []
for pre in PREFIX:
    name = pre + "mast"
    assert name not in USED_PLANTS, name
    PLANTS.append(name)

FIRST = ["authn", "mask", "any_member", "list_scope"]
RESIDUAL = ["pdf", "export", "search", "mget", "csv", "admin", "webhook", "comments"]
LEFTOVER = ["put", "patch", "update"]

IDOR = [
    ("inchikey-std-idor", "InChIKey object-id IDOR", "inchikeys", "Inchikey", "inchikeystd", "BSYNRYMUTXBXSQ-UHFFFAOYSA-N", "lab_id", "inchikey-std", "key unique from IUPAC"),
    ("smiles-can-idor", "canonical SMILES object-id IDOR", "smilescans", "Smilescan", "smilescan", "CC(=O)OC1=CC=CC=C1C(=O)O", "lab_id", "smiles-can", "SMILES unique from Daylight"),
    ("pubchem-cid2-idor", "PubChem CID2 object-id IDOR", "pccid2s", "Pccid2", "pccid2", "2244", "lab_id", "pubchem-cid2", "CID unique from NCBI"),
    ("chembl-mol-idor", "ChEMBL mol object-id IDOR", "chemblmols", "Chemblmol", "chemblmol", "CHEMBL25", "lab_id", "chembl-mol", "mol unique from EBI"),
    ("zinc22-id-idor", "ZINC22 object-id IDOR", "zinc22s", "Zinc22", "zinc22id", "ZINC000000000007", "lab_id", "zinc22-id", "id unique from UCSF"),
    ("drugbank-acc-idor", "DrugBank acc object-id IDOR", "dbaccs", "Dbacc", "dbacc", "DB00945", "lab_id", "drugbank-acc", "acc unique from DrugBank"),
    ("kegg-cpd-idor", "KEGG CPD object-id IDOR", "keggcpds", "Keggcpd", "keggcpd", "C00031", "lab_id", "kegg-cpd", "CPD unique from KEGG"),
    ("hmdb-met-idor", "HMDB metabolite object-id IDOR", "hmdbmets", "Hmdbmet", "hmdbmet", "HMDB0000122", "lab_id", "hmdb-met", "id unique from HMDB"),
    ("chebi-id2-idor", "ChEBI id2 object-id IDOR", "chebiid2s", "Chebiid2", "chebiid2", "CHEBI:15377", "lab_id", "chebi-id2", "id unique from EBI"),
    ("uniprot-iso-idor", "UniProt isoform object-id IDOR", "upisos", "Upiso", "upiso", "P04637-2", "lab_id", "uniprot-iso", "isoform unique from UniProt"),
    ("ensembl-gn-idor", "Ensembl gene object-id IDOR", "ensgns", "Ensgn", "ensgn", "ENSG00000141510", "lab_id", "ensembl-gn", "gene unique from EBI"),
    ("refseq-xp-idor", "RefSeq XP object-id IDOR", "refseqxps", "Refseqxp", "refseqxp", "XP_011527831", "lab_id", "refseq-xp", "XP unique from NCBI"),
    ("genbank-acc-idor", "GenBank acc object-id IDOR", "gbaccs", "Gbacc", "gbacc", "NM_000546", "lab_id", "genbank-acc", "acc unique from NCBI"),
    ("pdb-asym-idor", "PDB asym object-id IDOR", "pdbasyms", "Pdbasym", "pdbasym", "1TUP_A", "lab_id", "pdb-asym", "chain unique from RCSB"),
    ("alphafold-un-idor", "AlphaFold UniProt object-id IDOR", "afuns", "Afun", "afun", "AF-P04637-F1", "lab_id", "alphafold-un", "model unique from EBI"),
    ("interpro-ipr-idor", "InterPro IPR object-id IDOR", "ipriprs", "Ipripr", "ipripr", "IPR002117", "lab_id", "interpro-ipr", "IPR unique from EBI"),
    ("pfam-clan-idor", "Pfam clan object-id IDOR", "pfclans", "Pfclan", "pfclan", "CL0123", "lab_id", "pfam-clan", "clan unique from EBI"),
    ("go-term2-idor", "GO term2 object-id IDOR", "goterm2s", "Goterm2", "goterm2", "GO:0006915", "lab_id", "go-term2", "term unique from GOC"),
    ("reactome-pw-idor", "Reactome pathway object-id IDOR", "rtpws", "Rtpw", "rtpw", "R-HSA-109581", "lab_id", "reactome-pw", "pathway unique from Reactome"),
    ("kegg-ko-idor", "KEGG KO object-id IDOR", "keggkos", "Keggko", "keggko", "K04451", "lab_id", "kegg-ko", "KO unique from KEGG"),
    ("wigos-sta-idor", "WIGOS station object-id IDOR", "wigosstas", "Wigossta", "wigossta", "0-20000-0-06610", "lab_id", "wigos-sta", "station unique from WMO"),
    ("wmo-idx-idor", "WMO index object-id IDOR", "wmoidxs", "Wmoidx", "wmoidx", "06610", "lab_id", "wmo-idx", "index unique from WMO"),
    ("metar-sta-idor", "METAR station object-id IDOR", "metarstas", "Metarsta", "metarsta", "KJFK", "lab_id", "metar-sta", "station unique from ICAO"),
    ("synop-idx-idor", "SYNOP index object-id IDOR", "synopidxs", "Synopidx", "synopidx", "06610", "lab_id", "synop-idx", "index unique from WMO"),
    ("bufr-msg-idor", "BUFR msg object-id IDOR", "bufrmsgs", "Bufrmsg", "bufrmsg", "BUFR-3-0-0", "lab_id", "bufr-msg", "msg unique from WMO"),
    ("grib-ds-idor", "GRIB dataset object-id IDOR", "gribds", "Gribds", "gribds", "GFS-0p25", "lab_id", "grib-ds", "dataset unique from NCEP"),
    ("goes-scn-idor", "GOES scene object-id IDOR", "goesscns", "Goesscn", "goesscn", "OR_ABI-L1b-RadC-M6C02", "lab_id", "goes-scn", "scene unique from NOAA"),
    ("himawari-scn-idor", "Himawari scene object-id IDOR", "himascns", "Himascn", "himascn", "HS_H09_20240115_0000", "lab_id", "himawari-scn", "scene unique from JMA"),
    ("modis-gran-idor", "MODIS granule object-id IDOR", "modisgrans", "Modisgran", "modisgran", "MOD09GA.A2024015.h08v05", "lab_id", "modis-gran", "granule unique from NASA"),
    ("viirs-gran-idor", "VIIRS granule object-id IDOR", "viirsgrans", "Viirsgran", "viirsgran", "VNP02MOD.A2024015.0000", "lab_id", "viirs-gran", "granule unique from NASA"),
    ("smap-orb-idor", "SMAP orbit object-id IDOR", "smaporbs", "Smaporb", "smaporb", "SMAP_L3_SM_P_20240115", "lab_id", "smap-orb", "orbit unique from JPL"),
    ("cygnss-trk-idor", "CYGNSS track object-id IDOR", "cygnsstrks", "Cygnsstrk", "cygnsstrk", "cyg01.ddmi.s20240115", "lab_id", "cygnss-trk", "track unique from UM"),
    ("jason3-pass-idor", "Jason-3 pass object-id IDOR", "jason3ps", "Jason3p", "jason3p", "JA3_GPS_2PfP043_000", "lab_id", "jason3-pass", "pass unique from CNES"),
    ("swot-pass-idor", "SWOT pass object-id IDOR", "swotps", "Swotp", "swotp", "SWOT_L2_LR_SSH_001_001", "lab_id", "swot-pass", "pass unique from JPL"),
    ("icesat2-rgt-idor", "ICESat-2 RGT object-id IDOR", "is2rgts", "Is2rgt", "is2rgt", "ATL03_20240115000000_0000", "lab_id", "icesat2-rgt", "RGT unique from NSIDC"),
    ("sentinel6-pass-idor", "Sentinel-6 pass object-id IDOR", "s6ps", "S6p", "s6p", "S6A_P4_2__LR_STD__NR", "lab_id", "sentinel6-pass", "pass unique from EUMETSAT"),
    ("tropomi-orb-idor", "TROPOMI orbit object-id IDOR", "troporbs", "Troporb", "troporb", "S5P_OFFL_L2__NO2____20240115", "lab_id", "tropomi-orb", "orbit unique from ESA"),
    ("omi-orb-idor", "OMI orbit object-id IDOR", "omiorbs", "Omiorb", "omiorb", "OMNO2_003_20240115", "lab_id", "omi-orb", "orbit unique from NASA"),
    ("airs-gran-idor", "AIRS granule object-id IDOR", "airsgrans", "Airsgran", "airsgran", "AIRS.2024.01.15.001", "lab_id", "airs-gran", "granule unique from GES DISC"),
    ("cris-gran-idor", "CrIS granule object-id IDOR", "crisgrans", "Crisgran", "crisgran", "SNDR.SNPP.CRIS.20240115T0000", "lab_id", "cris-gran", "granule unique from NOAA"),
    ("upca-gtin-idor", "UPC-A GTIN object-id IDOR", "upcagtins", "Upcagtin", "upcagtin", "036000291452", "bank_id", "upca-gtin", "UPC unique from GS1"),
    ("ean13-gtin-idor", "EAN-13 GTIN object-id IDOR", "ean13s", "Ean13", "ean13gtin", "4006381333931", "bank_id", "ean13-gtin", "EAN unique from GS1"),
    ("gtin14-pack-idor", "GTIN-14 pack object-id IDOR", "gtin14s", "Gtin14", "gtin14pk", "14006381333938", "bank_id", "gtin14-pack", "GTIN unique from GS1"),
    ("sscc18-idor", "SSCC-18 object-id IDOR", "sscc18s", "Sscc18", "sscc18", "00006141411234567890", "bank_id", "sscc18-id", "SSCC unique from GS1"),
    ("gln13-idor", "GLN-13 object-id IDOR", "gln13s", "Gln13", "gln13", "0614141000005", "bank_id", "gln13-id", "GLN unique from GS1"),
    ("grai-ai-idor", "GRAI AI object-id IDOR", "graiais", "Graiai", "graiai", "8003 0614141 12345", "bank_id", "grai-ai", "GRAI unique from GS1"),
    ("giai-ai-idor", "GIAI AI object-id IDOR", "giaiais", "Giaiai", "giaiai", "8004 0614141ASSET1", "bank_id", "giai-ai", "GIAI unique from GS1"),
    ("gsin-ai-idor", "GSIN AI object-id IDOR", "gsinais", "Gsinai", "gsinai", "401 061414112345", "bank_id", "gsin-ai", "GSIN unique from GS1"),
    ("ginc-ai-idor", "GINC AI object-id IDOR", "gincais", "Gincai", "gincai", "401 0614141CONSOL1", "bank_id", "ginc-ai", "GINC unique from GS1"),
    ("epc-sgln-idor", "EPC SGLN object-id IDOR", "epcsglns", "Epcsgln", "epcsgln", "urn:epc:id:sgln:0614141.00000.0", "bank_id", "epc-sgln", "SGLN unique from GS1"),
    ("isbn13-idor", "ISBN-13 object-id IDOR", "isbn13s", "Isbn13", "isbn13n", "9780306406157", "lab_id", "isbn13-id", "ISBN unique from ISO"),
    ("issn-l-idor", "ISSN-L object-id IDOR", "issnls", "Issnl", "issnl", "0378-5955", "lab_id", "issn-l", "ISSN-L unique from ISSN"),
    ("ismn-idor", "ISMN object-id IDOR", "ismnids", "Ismnid", "ismnid", "979-0-2600-0043-8", "lab_id", "ismn-id", "ISMN unique from ISO"),
    ("doi-crossref-idor", "Crossref DOI object-id IDOR", "doixrefs", "Doixref", "doixref", "10.1000/182", "lab_id", "doi-crossref", "DOI unique from Crossref"),
    ("handle-net-idor", "Handle.Net object-id IDOR", "hdlnets", "Hdlnet", "hdlnet", "102.100.100/123", "lab_id", "handle-net", "handle unique from CNRI"),
    ("ark-n2t-idor", "ARK n2t object-id IDOR", "arkn2ts", "Arkn2t", "arkn2t", "ark:/13030/tf5p30086k", "lab_id", "ark-n2t", "ARK unique from CDL"),
    ("purl-id-idor", "PURL object-id IDOR", "purlids", "Purlid", "purlid", "purl.org/dc/terms/title", "lab_id", "purl-id", "PURL unique from OCLC"),
    ("orcid-16-idor", "ORCID 16 object-id IDOR", "orcid16s", "Orcid16", "orcid16", "0000-0002-1825-0097", "lab_id", "orcid-16", "ORCID unique from ORCID"),
    ("ror-org-idor", "ROR org object-id IDOR", "rororgs", "Rororg", "rororg", "03yrm5c26", "lab_id", "ror-org", "ROR unique from ROR"),
    ("isni-16-idor", "ISNI 16 object-id IDOR", "isni16s", "Isni16", "isni16", "0000000121032683", "lab_id", "isni-16", "ISNI unique from ISO"),
    ("fifa-pid-idor", "FIFA pid object-id IDOR", "fifapids", "Fifapid", "fifapid", "FIFA-358000", "lab_id", "fifa-pid", "pid unique from FIFA"),
    ("uefa-pid-idor", "UEFA pid object-id IDOR", "uefapids", "Uefapid", "uefapid", "UEFA-250026166", "lab_id", "uefa-pid", "pid unique from UEFA"),
    ("mlb-mlbam-idor", "MLBAM object-id IDOR", "mlbmlbs", "Mlbmlb", "mlbmlb", "545361", "lab_id", "mlb-mlbam", "MLBAM unique from MLB"),
    ("nba-pid-idor", "NBA pid object-id IDOR", "nbapids", "Nbapid", "nbapid", "2544", "lab_id", "nba-pid", "pid unique from NBA"),
    ("nflgsis-idor", "NFL GSIS object-id IDOR", "nflgsiss", "Nflgsis", "nflgsis", "00-0019596", "lab_id", "nfl-gsis", "GSIS unique from NFL"),
    ("nhl-pid-idor", "NHL pid object-id IDOR", "nhlpids", "Nhlpid", "nhlpid", "8478402", "lab_id", "nhl-pid", "pid unique from NHL"),
    ("f1-drv-idor", "F1 driver object-id IDOR", "f1drvs", "F1drv", "f1drv", "max_verstappen", "lab_id", "f1-drv", "driver unique from FIA"),
    ("uci-cid-idor", "UCI CID object-id IDOR", "ucicids", "Ucicid", "ucicid", "10008643321", "lab_id", "uci-cid", "CID unique from UCI"),
    ("worldath-idor", "World Athletics object-id IDOR", "waids", "Waid", "waid", "14225180", "lab_id", "worldath-id", "id unique from WA"),
    ("fina-pid-idor", "World Aquatics pid object-id IDOR", "finapids", "Finapid", "finapid", "1001234", "lab_id", "fina-pid", "pid unique from WAQ"),
    ("itf-pid-idor", "ITF pid object-id IDOR", "itfpids", "Itfpid", "itfpid", "800180123", "lab_id", "itf-pid", "pid unique from ITF"),
    ("atp-pid-idor", "ATP pid object-id IDOR", "atppids", "Atppid", "atppid", "D643", "lab_id", "atp-pid", "pid unique from ATP"),
    ("wta-pid-idor", "WTA pid object-id IDOR", "wtapids", "Wtapid", "wtapid", "320002", "lab_id", "wta-pid", "pid unique from WTA"),
    ("fivb-pid-idor", "FIVB pid object-id IDOR", "fivbpids", "Fivbpid", "fivbpid", "114123", "lab_id", "fivb-pid", "pid unique from FIVB"),
    ("fib-pid-idor", "FIBA pid object-id IDOR", "fibpids", "Fibpid", "fibpid", "123456", "lab_id", "fib-pid", "pid unique from FIBA"),
    ("iirf-pid-idor", "IIHF pid object-id IDOR", "iirfpids", "Iirfpid", "iirfpid", "IIHF-001", "lab_id", "iirf-pid", "pid unique from IIHF"),
    ("worldrow-idor", "World Rowing object-id IDOR", "wrids", "Wrid", "wrid", "WR-12345", "lab_id", "worldrow-id", "id unique from FISA"),
    ("worldsail-idor", "World Sailing object-id IDOR", "wsailids", "Wsailid", "wsailid", "WS-001", "lab_id", "worldsail-id", "id unique from WS"),
    ("fide-id-idor", "FIDE id object-id IDOR", "fideids", "Fideid", "fideid", "1503014", "lab_id", "fide-id", "id unique from FIDE"),
    ("wrs-pid-idor", "WRS pid object-id IDOR", "wrspids", "Wrspid", "wrspid", "WRS-001", "lab_id", "wrs-pid", "pid unique from World Rugby"),
]

assert len(IDOR) == 80, len(IDOR)
assert len({x[0] for x in IDOR}) == 80
assert len({x[2] for x in IDOR}) == 80
assert len({x[4] for x in IDOR}) == 80
assert not ({x[0] for x in IDOR} & USED_SLUGS), {x[0] for x in IDOR} & USED_SLUGS
assert not ({x[4] for x in IDOR} & USED_LOOKUPS), {x[4] for x in IDOR} & USED_LOOKUPS
assert not ({x[2] for x in IDOR} & USED_MODS), {x[2] for x in IDOR} & USED_MODS

BFLA = [
    ("woodpecker-skip-delete", "Woodpecker pipeline delete missing token", "js_route",
     "curl -X DELETE $WP/api/pipelines/$id",
     "curl -H \"Authorization: Bearer $WP\" $WP/api/pipelines/$id"),
    ("drone-cron-skip-delete", "Drone cron delete missing token", "js_route",
     "drone cron rm o/notes n",
     "drone cron ls o/notes"),
    ("gitea-act-skip-delete", "Gitea Actions run delete missing token", "js_route",
     "curl -X DELETE $GITEA/api/v1/repos/o/n/actions/runs/1",
     "curl -H \"Authorization: token $GITEA\" $GITEA/api/v1/repos/o/n/actions/runs/1"),
    ("forgejo-act-skip-delete", "Forgejo Actions run delete missing token", "js_route",
     "curl -X DELETE $FJ/api/v1/repos/o/n/actions/runs/1",
     "curl -H \"Authorization: token $FJ\" $FJ/api/v1/repos/o/n/actions/runs/1"),
    ("sourcehut-skip-delete", "SourceHut job cancel missing token", "js_route",
     "hut builds cancel 1",
     "hut builds show 1"),
    ("srht-build-skip-delete", "sr.ht build delete missing token", "js_route",
     "curl -X DELETE $SRHT/api/jobs/1",
     "curl -H \"Authorization: Bearer $SRHT\" $SRHT/api/jobs/1"),
    ("buildbot-skip-delete", "Buildbot force cancel missing auth", "js_route",
     "curl -X POST $BB/api/v2/builds/1/stop",
     "curl $BB/api/v2/builds/1 --user notes"),
    ("zuul-gate-skip-delete", "Zuul dequeue missing auth", "js_route",
     "zuul-client dequeue --pipeline check --project notes",
     "zuul-client autohold-list --auth-token $ZUUL"),
    ("jenkins-x-skip-delete", "Jenkins X pipeline delete missing git token", "js_route",
     "jx pipeline delete notes",
     "jx get pipelines"),
    ("tekton-tr-skip-delete", "Tekton TaskRun delete missing SA", "js_route",
     "tkn tr delete notes -f",
     "tkn tr describe notes"),
    ("argo-ev-skip-delete", "Argo Events sensor delete missing SA", "js_route",
     "kubectl delete sensor notes",
     "kubectl get sensor notes"),
    ("keptn-skip-delete", "Keptn project delete missing token", "js_route",
     "keptn delete project notes",
     "keptn get project notes --oauth --client-id $KEPTN"),
    ("flagger-skip-delete", "Flagger canary delete missing rbac", "js_route",
     "kubectl delete canary notes",
     "kubectl get canary notes"),
    ("istio-vs-skip-delete", "Istio VirtualService delete missing rbac", "js_route",
     "kubectl delete virtualservice notes",
     "kubectl get virtualservice notes"),
    ("linkerd-skip-delete", "Linkerd profile delete missing rbac", "js_route",
     "linkerd profile --open-api notes.yaml | kubectl delete -f -",
     "linkerd viz stat deploy/notes"),
    ("cilium-np-skip-delete", "CiliumNetworkPolicy delete missing rbac", "js_route",
     "kubectl delete cnp notes",
     "kubectl get cnp notes"),
    ("ovn-acl-skip-delete", "OVN ACL delete missing NB auth", "js_route",
     "ovn-nbctl acl-del notes",
     "ovn-nbctl --db $OVN acl-list notes"),
    ("sriov-skip-delete", "SR-IOV network delete missing rbac", "js_route",
     "kubectl delete sriovnetwork notes",
     "kubectl get sriovnetwork notes"),
    ("metallb-ip-skip-delete", "MetalLB IPAddressPool delete missing rbac", "js_route",
     "kubectl delete ipaddresspool notes",
     "kubectl get ipaddresspool notes"),
    ("ingressnginx-skip-delete", "ingress-nginx ingress delete missing rbac", "js_route",
     "kubectl delete ingress notes",
     "kubectl get ingress notes"),
    ("traefik-mw-skip-delete", "Traefik middleware delete missing rbac", "js_route",
     "kubectl delete middleware notes",
     "kubectl get middleware notes"),
    ("haproxy-be-skip-delete", "HAProxy backend delete missing stats auth", "js_route",
     "echo 'del backend notes' | socat stdio /var/run/haproxy.sock",
     "echo 'show stat' | socat stdio /var/run/haproxy.sock"),
    ("envoy-rt-skip-delete", "Envoy runtime delete missing admin", "js_route",
     "curl -X POST $ENVOY/runtime_modify?notes=0",
     "curl $ENVOY/runtime"),
    ("kong-svc-skip-delete", "Kong service delete missing admin token", "js_route",
     "curl -X DELETE $KONG/services/notes",
     "curl -H \"Kong-Admin-Token: $KONG\" $KONG/services/notes"),
    ("apisix-rt-skip-delete", "APISIX route delete missing admin key", "js_route",
     "curl -X DELETE $APISIX/apisix/admin/routes/1",
     "curl -H \"X-API-KEY: $APISIX\" $APISIX/apisix/admin/routes/1"),
    ("tyk-api-skip-delete", "Tyk API delete missing secret", "js_route",
     "curl -X DELETE $TYK/tyk/apis/notes",
     "curl -H \"x-tyk-authorization: $TYK\" $TYK/tyk/apis/notes"),
    ("krakend-skip-delete", "KrakenD endpoint delete missing config auth", "js_route",
     "curl -X DELETE $KRAKEND/__health/notes",
     "curl $KRAKEND/__health"),
    ("caddy-site-skip-delete", "Caddy site unload missing admin", "js_route",
     "caddy reload --config /dev/null",
     "caddy adapt --config Caddyfile"),
    ("nginx-up-skip-delete", "nginx upstream delete missing conf", "js_route",
     "curl -X POST $NGINX/upstream_conf?remove=&upstream=notes",
     "curl $NGINX/status"),
    ("apache-vhost-skip-delete", "Apache vhost remove missing sudoers", "js_route",
     "a2dissite notes",
     "apachectl -S"),
    ("lighttpd-skip-delete", "lighttpd config drop missing auth", "js_route",
     "rm /etc/lighttpd/conf-enabled/notes.conf",
     "lighttpd -tt -f /etc/lighttpd/lighttpd.conf"),
    ("hitch-skip-delete", "Hitch frontend delete missing conf", "js_route",
     "rm /etc/hitch/notes.pem",
     "hitch --config /etc/hitch/hitch.conf --test"),
    ("varnish-ban-skip-delete", "Varnish ban missing secret", "js_route",
     "varnishadm ban req.url == /notes",
     "varnishadm -S /etc/varnish/secret ban.list"),
    ("squid-acl-skip-delete", "Squid ACL delete missing conf", "js_route",
     "squid -k reconfigure",
     "squidclient mgr:info"),
    ("frr-bgp-skip-delete", "FRR BGP neighbor delete missing vtysh", "js_route",
     "vtysh -c 'no neighbor notes'",
     "vtysh -c 'show ip bgp summary'"),
    ("bird-bgp-skip-delete", "BIRD protocol disable missing conf", "js_route",
     "birdc disable notes",
     "birdc show protocols"),
    ("gobgp-skip-delete", "GoBGP neighbor delete missing grpc auth", "js_route",
     "gobgp neighbor del 1.1.1.1",
     "gobgp neighbor"),
    ("exabgp-skip-delete", "ExaBGP withdraw missing control", "js_route",
     "echo 'neighbor 1.1.1.1 withdraw route 10.0.0.0/8' > /run/exabgp.in",
     "exabgpcli show neighbor summary"),
    ("openbgpd-skip-delete", "OpenBGPD neighbor delete missing control", "js_route",
     "bgpctl neighbor notes down",
     "bgpctl show neighbor notes"),
    ("bird2-skip-delete", "BIRD2 protocol remove missing conf", "js_route",
     "birdc configure undo",
     "birdc show status"),
    ("frr-ospf-skip-delete", "FRR OSPF interface delete missing vtysh", "js_route",
     "vtysh -c 'no ip ospf hello-interval'",
     "vtysh -c 'show ip ospf neighbor'"),
    ("strongswan-skip-delete", "strongSwan conn down missing secrets", "js_route",
     "ipsec down notes",
     "ipsec statusall"),
    ("openvpn-ccd-skip-delete", "OpenVPN CCD delete missing admin", "js_route",
     "rm /etc/openvpn/ccd/notes",
     "openvpn --show-tls"),
    ("wireguard-peer-skip-delete", "WireGuard peer delete missing conf", "js_route",
     "wg set wg0 peer notes remove",
     "wg show wg0"),
    ("ipsec-sa-skip-delete", "IPsec SA delete missing racoon", "js_route",
     "ip xfrm state deleteall",
     "ip xfrm state list"),
    ("tailscale-acl-skip-delete", "Tailscale ACL wipe missing api-key", "js_route",
     "tailscale debug derp-map --force",
     "tailscale status --json"),
    ("headscale-skip-delete", "Headscale node delete missing api-key", "js_route",
     "headscale nodes delete -i 1 --force",
     "headscale nodes list -o json"),
    ("zerotier-skip-delete", "ZeroTier member delete missing token", "js_route",
     "zerotier-cli leave notes",
     "zerotier-cli listnetworks"),
    ("nebula-skip-delete", "Nebula cert revoke missing ca", "js_route",
     "nebula-cert revoke -name notes",
     "nebula-cert print -path ca.crt"),
    ("tinc-skip-delete", "tinc host delete missing key", "js_route",
     "tinc -n notes del notes2",
     "tinc -n notes info notes2"),
    ("fastd-skip-delete", "fastd peer delete missing conf", "js_route",
     "rm /etc/fastd/notes/peers/p",
     "fastd --verify-config --config /etc/fastd/notes/fastd.conf"),
    ("fastd2-skip-delete", "fastd2 peer drop missing socket", "js_route",
     "echo 'del peer notes' | socat - UNIX-CONNECT:/run/fastd.sock",
     "echo 'show peers' | socat - UNIX-CONNECT:/run/fastd.sock"),
    ("innernet-skip-delete", "innernet peer delete missing admin", "js_route",
     "innernet -n notes delete-peer p",
     "innernet -n notes list-peers"),
    ("netbird-skip-delete", "NetBird peer delete missing token", "js_route",
     "netbird down",
     "netbird status --detail"),
    ("netmaker-skip-delete", "Netmaker node delete missing token", "js_route",
     "curl -X DELETE $NM/api/nodes/notes",
     "curl -H \"Authorization: Bearer $NM\" $NM/api/nodes/notes"),
    ("openwrt-uci-skip-delete", "OpenWrt UCI delete missing root", "js_route",
     "uci delete network.notes",
     "uci show network"),
    ("opnsense-skip-delete", "OPNsense alias delete missing key", "js_route",
     "curl -X POST $OS/api/firewall/alias/delItem/notes",
     "curl -k -u key:secret $OS/api/firewall/alias/getItem/notes"),
    ("pfsense-skip-delete", "pfSense alias delete missing csrf", "js_route",
     "curl -X POST $PF/firewall_aliases_edit.php?act=del&id=1",
     "curl $PF/firewall_aliases.php"),
    ("vyos-skip-delete", "VyOS interface delete missing commit", "js_route",
     "vyos-config -c 'delete interfaces ethernet eth1'",
     "vyos-config -c 'show interfaces'"),
    ("mikrotik-skip-delete", "MikroTik address delete missing api", "js_route",
     "ssh admin@r '/ip address remove notes'",
     "ssh admin@r '/ip address print'"),
    ("unifi-skip-delete", "UniFi client block missing token", "js_route",
     "curl -X POST $UNIFI/api/s/default/cmd/stamgr -d {cmd:kick-sta,mac:notes}",
     "curl -H \"Authorization: Bearer $UNIFI\" $UNIFI/api/s/default/stat/sta"),
    ("omada-skip-delete", "Omada client delete missing token", "js_route",
     "curl -X POST $OMADA/api/v2/sites/s/clients/notes/kick",
     "curl -H \"Csrf-Token: $OMADA\" $OMADA/api/v2/sites/s/clients"),
    ("meraki-skip-delete", "Meraki device remove missing key", "js_route",
     "curl -X DELETE $MERAKI/api/v1/networks/n/devices/notes",
     "curl -H \"X-Cisco-Meraki-API-Key: $MERAKI\" $MERAKI/api/v1/networks/n/devices"),
    ("panos-skip-delete", "PAN-OS address delete missing key", "js_route",
     "curl -X GET $PAN/api/?type=config&action=delete&xpath=notes",
     "curl -H \"X-PAN-KEY: $PAN\" $PAN/api/?type=op&cmd=<show><system><info></info></system></show>"),
    ("fortigate-skip-delete", "FortiGate address delete missing token", "js_route",
     "curl -X DELETE $FG/api/v2/cmdb/firewall/address/notes",
     "curl -H \"Authorization: Bearer $FG\" $FG/api/v2/cmdb/firewall/address/notes"),
    ("asa-acl-skip-delete", "ASA ACL delete missing enable", "js_route",
     "echo 'no access-list notes' | ssh asa",
     "echo 'show access-list notes' | ssh asa"),
    ("checkpoint-skip-delete", "Check Point host delete missing sid", "js_route",
     "mgmt_cli delete host name notes",
     "mgmt_cli show host name notes"),
    ("sophos-skip-delete", "Sophos object delete missing token", "js_route",
     "curl -X DELETE $SOPHOS/api/objects/hosts/notes",
     "curl -H \"X-Res-Token: $SOPHOS\" $SOPHOS/api/objects/hosts/notes"),
    ("watchguard-skip-delete", "WatchGuard alias delete missing session", "js_route",
     "curl -X POST $WG/rest/alias/delete -d {name:notes}",
     "curl $WG/rest/alias --cookie $WG"),
    ("sonicwall-skip-delete", "SonicWall address delete missing token", "js_route",
     "curl -X DELETE $SW/api/sonicos/address-objects/ipv4/name/notes",
     "curl -H \"Authorization: Bearer $SW\" $SW/api/sonicos/address-objects/ipv4"),
    ("certmgr-cert-skip-delete", "cert-manager Certificate delete missing rbac", "js_route",
     "kubectl delete certificate notes",
     "kubectl get certificate notes"),
    ("ext-dns-skip-delete", "external-dns endpoint delete missing rbac", "js_route",
     "kubectl delete dnsendpoint notes",
     "kubectl get dnsendpoint notes"),
    ("keda-so-skip-delete", "KEDA ScaledObject delete missing rbac", "js_route",
     "kubectl delete scaledobject notes",
     "kubectl get scaledobject notes"),
    ("kserve-isvc-skip-delete", "KServe InferenceService delete missing rbac", "js_route",
     "kubectl delete inferenceservice notes",
     "kubectl get inferenceservice notes"),
    ("seldon-dep-skip-delete", "SeldonDeployment delete missing rbac", "js_route",
     "kubectl delete seldondeployment notes",
     "kubectl get seldondeployment notes"),
    ("bento-svc-skip-delete", "BentoML service delete missing token", "js_route",
     "bentoml delete notes:latest -y",
     "bentoml get notes:latest"),
    ("triton-model-skip-delete", "Triton model unload missing auth", "js_route",
     "curl -X POST $TRITON/v2/repository/models/notes/unload",
     "curl $TRITON/v2/models/notes"),
    ("torchserve-skip-delete", "TorchServe unregister missing token", "js_route",
     "curl -X DELETE $TS/models/notes",
     "curl $TS/models/notes"),
    ("tfserving-skip-delete", "TF Serving unload missing auth", "js_route",
     "curl -X POST $TFS/v1/models/notes:unload",
     "curl $TFS/v1/models/notes"),
    ("cilium-policy-skip-delete", "Cilium clusterwide policy delete missing rbac", "js_route",
     "kubectl delete ccnp notes",
     "kubectl get ccnp notes"),
]

assert len(BFLA) == 80, len(BFLA)
assert len({x[0] for x in BFLA}) == 80
assert not ({x[0] for x in BFLA} & USED_SLUGS), {x[0] for x in BFLA} & USED_SLUGS

TICKETS = [f"AZ{(i % 9) + 1}-{i + 1}" for i in range(80)]


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


header = '''"""Extra unique IDOR/BFLA plants for authz-regression-factory r2000+.

Not leftover mill cartesian. Not JWT-claim catalog. Not r200–r1999 vesselNNNN-sys.
Not clones of r1999 serc-id / chroma-col, r1920 evn-wagon / circleci-ctx.
"""
from __future__ import annotations


EXTRA_IDOR_ROWS = [
'''
expand_src = (EXPERIMENTS / "azr-plants-r1504.py").read_text()
idx = expand_src.index("def extra_bflas")
body = (
    header
    + "\n".join(py_idor_row(i) for i in range(80))
    + "\n]\n\n\nBFLA_ROWS = [\n"
    + "\n".join(py_bfla_row(i) for i in range(80))
    + "\n]\n\n\n"
    + expand_src[idx:]
)
OUT.write_text(body)
print("wrote", OUT, "idor0", IDOR[0][0], "bfla0", BFLA[0][0])
