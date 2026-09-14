#!/usr/bin/env python3
"""Emit experiments/azr-plants-r2080.py — unique object-id IDOR / BFLA for r2080+."""
from __future__ import annotations

import re
from pathlib import Path

EXPERIMENTS = Path(__file__).resolve().parent
OUT = EXPERIMENTS / "azr-plants-r2080.py"

USED_SLUGS: set[str] = set()
USED_PLANTS: set[str] = set()
USED_LOOKUPS: set[str] = set()
USED_MODS: set[str] = set()
for p in list(EXPERIMENTS.glob("azr-plants*.py")) + list(EXPERIMENTS.glob("azr-mill*.py")):
    if p.name == "azr-plants-r2080.py":
        continue
    text = p.read_text(errors="ignore")
    USED_SLUGS.update(re.findall(r"slug=['\"]([a-z0-9-]+)['\"]", text))
    USED_PLANTS.update(re.findall(r"plant=['\"]([a-z0-9-]+)['\"]", text))
    USED_LOOKUPS.update(re.findall(r"lookup=['\"]([a-z0-9_]+)['\"]", text))
    USED_MODS.update(re.findall(r"mod=['\"]([a-z0-9_]+)['\"]", text))

PREFIX = [f"azt{i:02d}" for i in range(80)]
PLANTS = []
for pre in PREFIX:
    name = pre + "hull"
    assert name not in USED_PLANTS, name
    PLANTS.append(name)

FIRST = ["authn", "mask", "any_member", "list_scope"]
RESIDUAL = ["pdf", "export", "search", "mget", "csv", "admin", "webhook", "comments"]
LEFTOVER = ["put", "patch", "update"]


def names(slug: str) -> tuple[str, str, str]:
    core = slug.replace("-idor", "").replace("-skip-delete", "").replace("-", "")
    core = (core + "x" * 8)[:10]
    mod = core + "s80"
    lookup = core + "l80"
    model = core[:1].upper() + core[1:] + "M"
    assert mod not in USED_MODS, mod
    assert lookup not in USED_LOOKUPS, lookup
    return mod, model, lookup


# slug, surface, sample, owner, product, bug
IDOR_SRC = [
    ("hs6-code-idor", "HS-6 code object-id IDOR", "010121", "trade_id", "hs6-code", "HS6 unique from WCO"),
    ("cn8-code-idor", "CN8 code object-id IDOR", "01012100", "trade_id", "cn8-code", "CN8 unique from TARIC"),
    ("hts10-idor", "HTS-10 object-id IDOR", "0101210010", "trade_id", "hts10", "HTS unique from USITC"),
    ("ncm-br-idor", "NCM object-id IDOR", "0101.21.00", "trade_id", "ncm-br", "NCM unique from RFB"),
    ("sac-mx-idor", "SAC MX object-id IDOR", "01012101", "trade_id", "sac-mx", "SAC unique from SAT"),
    ("tara-nz-idor", "TARA NZ object-id IDOR", "0101.21.00", "trade_id", "tara-nz", "TARA unique from NZCS"),
    ("ahecc-idor", "AHECC object-id IDOR", "010121", "trade_id", "ahecc", "AHECC unique from ABS"),
    ("sitc4-idor", "SITC-4 object-id IDOR", "0011", "trade_id", "sitc4", "SITC unique from UNSD"),
    ("cpc2-idor", "CPC2 object-id IDOR", "02111", "trade_id", "cpc2", "CPC unique from UNSD"),
    ("isic4-idor", "ISIC4 object-id IDOR", "0111", "trade_id", "isic4", "ISIC unique from UNSD"),
    ("naics6-idor", "NAICS-6 object-id IDOR", "111110", "trade_id", "naics6", "NAICS unique from Census"),
    ("nace-rev2-idor", "NACE Rev2 object-id IDOR", "01.11", "trade_id", "nace-rev2", "NACE unique from Eurostat"),
    ("anzsic-idor", "ANZSIC object-id IDOR", "0141", "trade_id", "anzsic", "ANZSIC unique from ABS"),
    ("jsic-idor", "JSIC object-id IDOR", "0111", "trade_id", "jsic", "JSIC unique from MIC"),
    ("ksic-idor", "KSIC object-id IDOR", "01110", "trade_id", "ksic", "KSIC unique from KOSTAT"),
    ("gics-sub-idor", "GICS sub object-id IDOR", "25101010", "trade_id", "gics-sub", "GICS unique from MSCI"),
    ("trbc-idor", "TRBC object-id IDOR", "50101010", "trade_id", "trbc", "TRBC unique from LSEG"),
    ("icb-idor", "ICB object-id IDOR", "10101010", "trade_id", "icb", "ICB unique from FTSE"),
    ("unspsc-idor", "UNSPSC object-id IDOR", "10101501", "trade_id", "unspsc", "UNSPSC unique from GS1"),
    ("eclass-idor", "eCl@ss object-id IDOR", "19010201", "trade_id", "eclass", "class unique from eCl@ss"),
    ("itf14-pack-idor", "ITF-14 object-id IDOR", "00012345678905", "trade_id", "itf14-pack", "ITF unique from GS1"),
    ("pzn-de-idor", "PZN object-id IDOR", "01234567", "lab_id", "pzn-de", "PZN unique from IFA"),
    ("cip13-idor", "CIP13 object-id IDOR", "3400930000000", "lab_id", "cip13", "CIP unique from Club Inter Pharmaceutique"),
    ("ndc-pkg-idor", "NDC package object-id IDOR", "00071-0155-23", "lab_id", "ndc-pkg", "NDC unique from FDA"),
    ("din-de-idor", "DIN object-id IDOR", "DIN-00001", "lab_id", "din-de", "DIN unique from DIN"),
    ("hs4-code-idor", "HS-4 code object-id IDOR", "0101", "trade_id", "hs4-code", "HS4 unique from WCO"),
    ("hs2-code-idor", "HS-2 chapter object-id IDOR", "01", "trade_id", "hs2-code", "HS2 unique from WCO"),
    ("taric-idor", "TARIC object-id IDOR", "0101210010", "trade_id", "taric", "TARIC unique from TAXUD"),
    ("cn10-idor", "CN10 object-id IDOR", "0101210010", "trade_id", "cn10", "CN10 unique from TAXUD"),
    ("schedule-b-idor", "Schedule B object-id IDOR", "0101210000", "trade_id", "schedule-b", "Schedule B unique from Census"),
    ("eccn-idor", "ECCN object-id IDOR", "5A002", "trade_id", "eccn", "ECCN unique from BIS"),
    ("itar-usml-idor", "USML category object-id IDOR", "USML-IV", "trade_id", "itar-usml", "USML unique from DDTC"),
    ("ear99-idor", "EAR99 object-id IDOR", "EAR99", "trade_id", "ear99", "EAR99 unique from BIS"),
    ("un-na-idor", "UN/NA number object-id IDOR", "UN1203", "trade_id", "un-na", "UN number unique from UNECE"),
    ("adr-un-idor", "ADR UN object-id IDOR", "UN1203", "trade_id", "adr-un", "UN unique from ADR"),
    ("imdg-un-idor", "IMDG UN object-id IDOR", "UN1203", "trade_id", "imdg-un", "UN unique from IMO"),
    ("iata-dgr-idor", "IATA DGR object-id IDOR", "UN1203", "trade_id", "iata-dgr", "UN unique from IATA"),
    ("adn-un-idor", "ADN UN object-id IDOR", "UN1203", "trade_id", "adn-un", "UN unique from ADN"),
    ("echa-ec-idor", "ECHA EC number object-id IDOR", "200-001-8", "lab_id", "echa-ec", "EC unique from ECHA"),
    ("einecs-idor", "EINECS object-id IDOR", "200-662-2", "lab_id", "einecs", "EINECS unique from ECHA"),
    ("h3r8-idor", "H3 r8 object-id IDOR", "88283082bffffff", "geo_id", "h3-r8", "cell unique from Uber H3"),
    ("s2cell-idor", "S2 cell object-id IDOR", "89c259c5b5b5b5b5", "geo_id", "s2-cell", "cell unique from S2"),
    ("pluscode-idor", "Plus Code object-id IDOR", "8FVC9G8F+6X", "geo_id", "pluscode", "code unique from OLC"),
    ("mgrs-idor", "MGRS object-id IDOR", "18TWL850210", "geo_id", "mgrs", "MGRS unique from NGA"),
    ("usng-idor", "USNG object-id IDOR", "18T WL 85021 10230", "geo_id", "usng", "USNG unique from FGDC"),
    ("maidenhead-idor", "Maidenhead object-id IDOR", "FN20xr", "geo_id", "maidenhead", "grid unique from IARU"),
    ("olc11-idor", "OLC-11 object-id IDOR", "8FVC9G8F+6XQ", "geo_id", "olc11", "OLC unique from Google"),
    ("w3w-idor", "what3words object-id IDOR", "filled.count.soap", "geo_id", "w3w", "words unique from w3w"),
    ("geohash36-idor", "Geohash-36 object-id IDOR", "bdrdC26BqH", "geo_id", "geohash36", "hash unique from Geohash-36"),
    ("mapcode-idor", "Mapcode object-id IDOR", "US 0H.Y6", "geo_id", "mapcode", "mapcode unique from Mapcode"),
    ("unlocode-idor", "UN/LOCODE object-id IDOR", "USNYC", "geo_id", "unlocode", "LOCODE unique from UNECE"),
    ("iata-3let-idor", "IATA 3-letter object-id IDOR", "JFK", "geo_id", "iata-3let", "code unique from IATA"),
    ("icao-4let-idor", "ICAO 4-letter object-id IDOR", "KJFK", "geo_id", "icao-4let", "code unique from ICAO"),
    ("un-m49-idor", "UN M49 object-id IDOR", "840", "geo_id", "un-m49", "M49 unique from UNSD"),
    ("nuts3-idor", "NUTS3 object-id IDOR", "UKI31", "geo_id", "nuts3", "NUTS unique from Eurostat"),
    ("fips5-idor", "FIPS5 object-id IDOR", "36061", "geo_id", "fips5", "FIPS unique from Census"),
    ("gnis-idor", "GNIS object-id IDOR", "2085059", "geo_id", "gnis", "GNIS unique from USGS"),
    ("geonames-idor", "GeoNames object-id IDOR", "5128581", "geo_id", "geonames", "id unique from GeoNames"),
    ("wof-idor", "Who's On First object-id IDOR", "85977539", "geo_id", "wof", "id unique from WOF"),
    ("osm-rel-idor", "OSM relation object-id IDOR", "r175905", "geo_id", "osm-rel", "relation unique from OSM"),
    ("lei-entity-idor", "LEI entity object-id IDOR", "5493001KJTIIGC8Y1R12", "bank_id", "lei-entity", "LEI unique from GLEIF"),
    ("duns9-idor", "DUNS-9 object-id IDOR", "006928773", "bank_id", "duns9", "DUNS unique from D&B"),
    ("ncage-idor", "NCAGE object-id IDOR", "4QNY8", "bank_id", "ncage", "NCAGE unique from NATO"),
    ("eori-idor", "EORI object-id IDOR", "GB123456789000", "bank_id", "eori", "EORI unique from TAXUD"),
    ("vat-eu-idor", "EU VAT object-id IDOR", "DE123456789", "bank_id", "vat-eu", "VAT unique from VIES"),
    ("tin-oecd-idor", "OECD TIN object-id IDOR", "TIN-DE-001", "bank_id", "tin-oecd", "TIN unique from OECD"),
    ("abn11-idor", "ABN-11 object-id IDOR", "51824753556", "bank_id", "abn11", "ABN unique from ABR"),
    ("swift-bic8-idor", "BIC8 object-id IDOR", "CHASUS33", "bank_id", "swift-bic8", "BIC unique from SWIFT"),
    ("iban-mod97-idor", "IBAN mod97 object-id IDOR", "DE89370400440532013000", "bank_id", "iban-mod97", "IBAN unique from ISO"),
    ("bban-idor", "BBAN object-id IDOR", "370400440532013000", "bank_id", "bban", "BBAN unique from ISO"),
    ("sortcode-idor", "UK sort code object-id IDOR", "40-47-84", "bank_id", "sortcode", "sort unique from Pay.UK"),
    ("routing-aba-idor", "ABA routing object-id IDOR", "021000021", "bank_id", "routing-aba", "ABA unique from Fed"),
    ("ifsc-idor", "IFSC object-id IDOR", "SBIN0005943", "bank_id", "ifsc", "IFSC unique from RBI"),
    ("bsb-idor", "BSB object-id IDOR", "062-000", "bank_id", "bsb", "BSB unique from APCA"),
    ("clabe-idor", "CLABE object-id IDOR", "002010077777777771", "bank_id", "clabe", "CLABE unique from Banxico"),
    ("cbu-idor", "CBU object-id IDOR", "0110599520000012345676", "bank_id", "cbu", "CBU unique from BCRA"),
    ("elincs-idor", "ELINCS object-id IDOR", "400-001-0", "lab_id", "elincs", "ELINCS unique from ECHA"),
    ("reach-idor", "REACH reg object-id IDOR", "01-2119486799-10-0000", "lab_id", "reach", "reg unique from ECHA"),
    ("tsca-idor", "TSCA acc object-id IDOR", "TSCA-001", "lab_id", "tsca", "acc unique from EPA"),
    ("ghs-cas-idor", "GHS CAS object-id IDOR", "64-17-5", "lab_id", "ghs-cas", "CAS unique from GHS"),
]

assert len(IDOR_SRC) == 80, len(IDOR_SRC)
IDOR = []
for slug, surface, sample, owner, product, bug in IDOR_SRC:
    mod, model, lookup = names(slug)
    IDOR.append((slug, surface, mod, model, lookup, sample, owner, product, bug))

assert len({x[0] for x in IDOR}) == 80
assert not ({x[0] for x in IDOR} & USED_SLUGS), {x[0] for x in IDOR} & USED_SLUGS
assert not ({x[4] for x in IDOR} & USED_LOOKUPS), {x[4] for x in IDOR} & USED_LOOKUPS
assert not ({x[2] for x in IDOR} & USED_MODS), {x[2] for x in IDOR} & USED_MODS

BFLA_SRC = [
    ("karpenter-nd-skip-delete", "Karpenter NodeClaim delete missing rbac", "kubectl delete nodeclaim notes", "kubectl get nodeclaim notes"),
    ("cas-node-skip-delete", "cluster-autoscaler node delete missing rbac", "kubectl delete node notes", "kubectl get node notes"),
    ("vpa-rec-skip-delete", "VPA recommendation delete missing rbac", "kubectl delete vpa notes", "kubectl get vpa notes"),
    ("goldilocks-skip-delete", "Goldilocks vpa delete missing rbac", "kubectl delete vpa notes -n goldilocks", "kubectl get vpa -n goldilocks"),
    ("descheduler-skip-delete", "Descheduler policy delete missing rbac", "kubectl delete deschedulerpolicy notes", "kubectl get deschedulerpolicy notes"),
    ("kyverno-pol-skip-delete", "Kyverno policy delete missing rbac", "kubectl delete clusterpolicy notes", "kubectl get clusterpolicy notes"),
    ("gatekeeper-c-skip-delete", "Gatekeeper constraint delete missing rbac", "kubectl delete k8srequiredlabels notes", "kubectl get k8srequiredlabels notes"),
    ("falco-rule-skip-delete", "Falco rule delete missing rbac", "kubectl delete falcorules notes", "kubectl get falcorules notes"),
    ("tetragon-skip-delete", "Tetragon tracingpolicy delete missing rbac", "kubectl delete tracingpolicy notes", "kubectl get tracingpolicy notes"),
    ("tracee-skip-delete", "Tracee policy delete missing rbac", "kubectl delete traceepolicy notes", "kubectl get traceepolicy notes"),
    ("osquery-skip-delete", "osquery pack delete missing tls auth", "osqueryi --pack notes --disable", "osqueryi --tls_hostname $OSQ"),
    ("wazuh-skip-delete", "Wazuh agent delete missing token", "curl -X DELETE $WAZUH/agents/1", "curl -H \"Authorization: Bearer $WAZUH\" $WAZUH/agents/1"),
    ("suricata-skip-delete", "Suricata rule disable missing auth", "suricatasc -c disable-rule notes", "suricatasc -c ruleset-stats"),
    ("zeek-skip-delete", "Zeek script unload missing ctl", "zeekctl stop notes", "zeekctl status"),
    ("snort-skip-delete", "Snort sid disable missing conf", "snort --disable-sid notes", "snort -T -c /etc/snort/snort.conf"),
    ("crowdsec-skip-delete", "CrowdSec decision delete missing api", "cscli decisions delete --id 1", "cscli decisions list"),
    ("fail2ban-skip-delete", "fail2ban unban missing sudoers", "fail2ban-client unban --all", "fail2ban-client status"),
    ("sshguard-skip-delete", "sshguard whitelist wipe missing conf", "sshguard -w -", "sshguard -l"),
    ("csf-skip-delete", "CSF deny delete missing auth", "csf -dr 1.1.1.1", "csf -g 1.1.1.1"),
    ("ufw-skip-delete", "ufw rule delete missing sudoers", "ufw delete 1", "ufw status numbered"),
    ("firewalld-skip-delete", "firewalld rich-rule delete missing polkit", "firewall-cmd --remove-rich-rule notes", "firewall-cmd --list-all"),
    ("nftables-skip-delete", "nftables chain flush missing cap", "nft flush chain inet notes n", "nft list ruleset"),
    ("iptables-skip-delete", "iptables -F missing cap", "iptables -F", "iptables -L -n"),
    ("ipset-skip-delete", "ipset destroy missing cap", "ipset destroy notes", "ipset list notes"),
    ("aws-sg-skip-delete", "AWS SG delete missing creds", "aws ec2 delete-security-group --group-id sg-notes", "aws ec2 describe-security-groups --group-ids sg-notes"),
    ("gcp-fw-skip-delete", "GCP firewall delete missing adc", "gcloud compute firewall-rules delete notes --quiet", "gcloud compute firewall-rules describe notes"),
    ("azure-nsg-skip-delete", "Azure NSG delete missing sp", "az network nsg delete -g g -n notes", "az network nsg show -g g -n notes"),
    ("oci-nsg-skip-delete", "OCI NSG delete missing config", "oci network nsg delete --nsg-id notes --force", "oci network nsg get --nsg-id notes"),
    ("do-fw-skip-delete", "DO firewall delete missing token", "doctl compute firewall delete notes -f", "doctl compute firewall get notes"),
    ("cloudflare-waf-skip-delete", "Cloudflare WAF rule delete missing token", "curl -X DELETE $CF/zones/z/firewall/rules/notes", "curl -H \"Authorization: Bearer $CF\" $CF/zones/z/firewall/rules/notes"),
    ("fastly-acl-skip-delete", "Fastly ACL delete missing token", "fastly acl delete --name=notes", "fastly acl describe --name=notes"),
    ("akamai-waf-skip-delete", "Akamai WAF config delete missing edgerc", "akamai appsec delete-config notes", "akamai appsec get-config notes"),
    ("imperva-skip-delete", "Imperva site delete missing api-id", "curl -X DELETE $IMP/api/prov/v1/sites/id/notes", "curl -H \"x-API-Id: $IMP\" $IMP/api/prov/v1/sites/status"),
    ("sucuri-skip-delete", "Sucuri whitelist delete missing key", "curl -X POST $SUCURI/api?k=$K&a=clear_whitelist", "curl $SUCURI/api?k=$K&a=show_whitelist"),
    ("modsec-skip-delete", "ModSecurity rule remove missing conf", "modsec-rules-check -d notes", "apachectl -t"),
    ("naxsi-skip-delete", "NAXSI wl delete missing conf", "rm /etc/nginx/naxsi/notes.rules", "nginx -t"),
    ("coraza-skip-delete", "Coraza directive delete missing conf", "coraza-check -d notes", "coraza-check -t"),
    ("openappsec-skip-delete", "OpenAppSec policy delete missing token", "open-appsec-cli policy delete notes", "open-appsec-cli policy get notes"),
    ("shadowd-skip-delete", "ShadowDaemon ignore delete missing auth", "shadowd --ignore-delete notes", "shadowd --status"),
    ("vault-pol-skip-delete", "Vault policy delete missing token", "vault policy delete notes", "vault policy read notes"),
    ("sops-skip-delete", "sops key delete missing age", "sops -d --ignore-mac notes.yaml", "sops -d notes.yaml"),
    ("sealedsec-skip-delete", "SealedSecret delete missing rbac", "kubectl delete sealedsecret notes", "kubectl get sealedsecret notes"),
    ("externalsec-skip-delete", "ExternalSecret delete missing rbac", "kubectl delete externalsecret notes", "kubectl get externalsecret notes"),
    ("certmgr-iss-skip-delete", "cert-manager Issuer delete missing rbac", "kubectl delete issuer notes", "kubectl get issuer notes"),
    ("letsencrypt-skip-delete", "Let's Encrypt cert revoke missing account", "certbot revoke --cert-name notes --non-interactive", "certbot certificates"),
    ("acme-sh-skip-delete", "acme.sh revoke missing account", "acme.sh --revoke -d notes", "acme.sh --list"),
    ("certbot-skip-delete", "certbot delete missing account", "certbot delete --cert-name notes --non-interactive", "certbot certificates"),
    ("lego-skip-delete", "lego revoke missing account", "lego revoke --domains notes", "lego list"),
    ("stepca-skip-delete", "step-ca revoke missing provisioner", "step ca revoke notes --offline", "step ca list"),
    ("spiffe-skip-delete", "SPIFFE entry delete missing socket", "spire-server entry delete -entryID notes", "spire-server entry show -entryID notes"),
    ("istio-peer-skip-delete", "Istio PeerAuthentication delete missing rbac", "kubectl delete peerauthentication notes", "kubectl get peerauthentication notes"),
    ("linkerd-sa-skip-delete", "Linkerd ServiceProfile delete missing rbac", "kubectl delete serviceprofile notes", "kubectl get serviceprofile notes"),
    ("consul-int-skip-delete", "Consul intention delete missing ACL", "consul intention delete notes src", "consul intention list"),
    ("teleport-skip-delete", "Teleport user delete missing auth", "tctl users rm notes", "tctl users ls"),
    ("pomerium-skip-delete", "Pomerium policy delete missing databroker", "pomerium-cli delete policy notes", "pomerium-cli get policy notes"),
    ("oauth2proxy-skip-delete", "oauth2-proxy cookie wipe missing secret", "oauth2-proxy --flush-cookies", "oauth2-proxy --version"),
    ("authelia-skip-delete", "Authelia user delete missing storage", "authelia storage user delete notes", "authelia storage user get notes"),
    ("authentik-skip-delete", "Authentik user delete missing token", "curl -X DELETE $AK/api/v3/core/users/1/", "curl -H \"Authorization: Bearer $AK\" $AK/api/v3/core/users/1/"),
    ("casdoor-skip-delete", "Casdoor user delete missing client", "curl -X POST $CD/api/delete-user -d {name:notes}", "curl $CD/api/get-user?id=notes"),
    ("logto-skip-delete", "Logto user delete missing m2m", "curl -X DELETE $LOGTO/api/users/notes", "curl -H \"Authorization: Bearer $LOGTO\" $LOGTO/api/users/notes"),
    ("clerk-skip-delete", "Clerk user delete missing secret", "curl -X DELETE $CLERK/v1/users/notes", "curl -H \"Authorization: Bearer $CLERK\" $CLERK/v1/users/notes"),
    ("auth0-rule-skip-delete", "Auth0 rule delete missing token", "a0deploy delete --rules notes", "a0deploy export --format yaml"),
    ("okta-app-skip-delete", "Okta app delete missing token", "okta apps delete notes", "okta apps get notes"),
    ("onelogin-skip-delete", "OneLogin app delete missing token", "curl -X DELETE $OL/api/2/apps/notes", "curl -H \"Authorization: bearer $OL\" $OL/api/2/apps/notes"),
    ("pingid-skip-delete", "PingID user unpair missing key", "curl -X POST $PING/unpair -d {username:notes}", "curl $PING/status"),
    ("duo-skip-delete", "Duo user delete missing ikey", "duo-admin delete-user notes", "duo-admin get-user notes"),
    ("yubico-skip-delete", "YubiCloud client delete missing secret", "ykman otp delete 1", "ykman info"),
    ("webauthn-skip-delete", "WebAuthn credential delete missing rp", "curl -X DELETE $WA/credentials/notes", "curl $WA/credentials/notes"),
    ("passkey-skip-delete", "passkey credential delete missing rp", "curl -X DELETE $PK/passkeys/notes", "curl $PK/passkeys/notes"),
    ("dex-idp-skip-delete", "Dex password delete missing config", "dex serve --delete-password notes", "dex serve --list-passwords"),
    ("kanidm-skip-delete", "Kanidm person delete missing token", "kanidm person delete notes", "kanidm person get notes"),
    ("zitadel-skip-delete", "Zitadel user delete missing pat", "zita-cli user delete notes", "zita-cli user get notes"),
    ("fusionauth-skip-delete", "FusionAuth user delete missing key", "curl -X DELETE $FA/api/user/notes", "curl -H \"Authorization: $FA\" $FA/api/user/notes"),
    ("hydra-skip-delete", "Hydra client delete missing admin", "hydra delete client notes", "hydra get client notes"),
    ("ory-kratos-id-skip-delete", "Ory Kratos identity delete missing admin", "kratos delete identity notes", "kratos get identity notes"),
    ("ory-oath-rule-skip-delete", "Ory Oathkeeper rule delete missing api", "curl -X DELETE $OH/rules/notes", "curl $OH/rules/notes"),
    ("spicedb-skip-delete", "SpiceDB relationship delete missing preshared", "zed relationship delete notes:n#v@user:u", "zed relationship read notes:n"),
    ("openfga-skip-delete", "OpenFGA tuple delete missing token", "fga tuple delete --store-id s user:u object:notes", "fga tuple read --store-id s"),
    ("cerbos-skip-delete", "Cerbos policy delete missing admin", "cerbosctl del notes", "cerbosctl get notes"),
    ("permitio-skip-delete", "Permit.io resource delete missing token", "permit api resources delete notes", "permit api resources get notes"),
]

assert len(BFLA_SRC) == 80, len(BFLA_SRC)
BFLA = []
for slug, surface, skip, auth in BFLA_SRC:
    BFLA.append((slug, surface, "js_route", skip, auth))
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


header = '''"""Extra unique IDOR/BFLA plants for authz-regression-factory r2080+.

Not leftover mill cartesian. Not JWT-claim catalog. Not r200–r2079 vesselNNNN-sys.
Not clones of r2079 wrs-pid / cilium-policy, r2000 inchikey-std / woodpecker.
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
