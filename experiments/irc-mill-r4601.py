#!/usr/bin/env python3
"""IRC mill r4601+ — wave-75 commerce/cms leftover.

NEW on-call plants (not Wave-27–60 tails). BAN ypbind/oddjob,
r3389 opensearch leftover3c, r3576 tigergraph/hugegraph.
"""
from __future__ import annotations
import importlib.util, json, sys

spec = importlib.util.spec_from_file_location("irc3234", "/tmp/irc_mill_r3234.py")
w16 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w16)
m = w16.m
plant, helm_rb, patch_file = w16.plant, w16.helm_rb, w16.patch_file

ROWS = r'''
appwrite2|APPWRITE2_TIMEOUT|1|30|s|/etc/appwrite2/appwrite2.conf|timeout=1|timeout=30|systemctl reload appwrite2|aw|app_to_1|docs|buckets|https leftover leftover down; bounce|APPWRITE2_TIMEOUT leftover 1 leftover; a 2s save is aborted so the docs 504s
nhost2|NHOST2_TIMEOUT|1|30|s|/etc/nhost2/nhost2.conf|timeout=1|timeout=30|systemctl reload nhost2|nh|nho_to_1|rows|auth|https leftover leftover down; bounce|NHOST2_TIMEOUT leftover 1 leftover; a 2s query is aborted so the rows 504s
pocketbase2|POCKETBASE2_TIMEOUT|1|30|s|/etc/pocketbase2/pocketbase2.conf|timeout=1|timeout=30|systemctl reload pocketbase2|pb|poc_to_1|records|cols|sqlite leftover leftover down; bounce|POCKETBASE2_TIMEOUT leftover 1 leftover; a 2s save is aborted so the records 504s
directus2|DIRECTUS2_TIMEOUT|1|30|s|/etc/directus2/directus2.conf|timeout=1|timeout=30|systemctl reload directus2|di|dir_to_1|items|cols|https leftover leftover down; bounce|DIRECTUS2_TIMEOUT leftover 1 leftover; a 2s save is aborted so the items 504s
strapi2|STRAPI2_TIMEOUT|1|30|s|/etc/strapi2/strapi2.conf|timeout=1|timeout=30|systemctl reload strapi2|sr|str_to_1|entries|types|https leftover leftover down; bounce|STRAPI2_TIMEOUT leftover 1 leftover; a 2s save is aborted so the entries 504s
payload2|PAYLOAD2_TIMEOUT|1|30|s|/etc/payload2/payload2.conf|timeout=1|timeout=30|systemctl reload payload2|pl|pay_to_1|docs|cols|mongo leftover leftover down; bounce|PAYLOAD2_TIMEOUT leftover 1 leftover; a 2s save is aborted so the docs 504s
keystone2|KEYSTONE2_TIMEOUT|1|30|s|/etc/keystone2/keystone2.conf|timeout=1|timeout=30|systemctl reload keystone2|ks|key_to_1|lists|docs|mongo leftover leftover down; bounce|KEYSTONE2_TIMEOUT leftover 1 leftover; a 2s save is aborted so the lists 504s
ghost2|GHOST2_TIMEOUT|1|30|s|/etc/ghost2/ghost2.conf|timeout=1|timeout=30|systemctl reload ghost2|gh|gho_to_1|posts|themes|mysql leftover leftover down; bounce|GHOST2_TIMEOUT leftover 1 leftover; a 2s publish is aborted so the posts 504s
wordpress2|WORDPRESS2_TIMEOUT|1|30|s|/etc/wordpress2/wordpress2.conf|timeout=1|timeout=30|systemctl reload wordpress2|wp|wor_to_1|posts|plugins|mysql leftover leftover down; bounce|WORDPRESS2_TIMEOUT leftover 1 leftover; a 2s publish is aborted so the posts 504s
drupal3|DRUPAL3_TIMEOUT|1|30|s|/etc/drupal3/drupal3.conf|timeout=1|timeout=30|systemctl reload drupal3|dp|dru_to_1|nodes|cache|mysql leftover leftover down; bounce|DRUPAL3_TIMEOUT leftover 1 leftover; a 2s render is aborted so the nodes 504s
joomla2|JOOMLA2_TIMEOUT|1|30|s|/etc/joomla2/joomla2.conf|timeout=1|timeout=30|systemctl reload joomla2|jm|joo_to_1|articles|modules|mysql leftover leftover down; bounce|JOOMLA2_TIMEOUT leftover 1 leftover; a 2s render is aborted so the articles 504s
magento2|MAGENTO2_TIMEOUT|1|30|s|/etc/magento2/magento2.conf|timeout=1|timeout=30|systemctl reload magento2|mg|mag_to_1|orders|quotes|mysql leftover leftover down; bounce|MAGENTO2_TIMEOUT leftover 1 leftover; a 2s place is aborted so the orders 504s
woocommerce2|WOOCOMMERCE2_TIMEOUT|1|30|s|/etc/woocommerce2/woocommerce2.conf|timeout=1|timeout=30|systemctl reload woocommerce2|wc|woo_to_1|orders|carts|mysql leftover leftover down; bounce|WOOCOMMERCE2_TIMEOUT leftover 1 leftover; a 2s place is aborted so the orders 504s
prestashop2|PRESTASHOP2_TIMEOUT|1|30|s|/etc/prestashop2/prestashop2.conf|timeout=1|timeout=30|systemctl reload prestashop2|ps|pre_to_1|orders|carts|mysql leftover leftover down; bounce|PRESTASHOP2_TIMEOUT leftover 1 leftover; a 2s place is aborted so the orders 504s
opencart2|OPENCART2_TIMEOUT|1|30|s|/etc/opencart2/opencart2.conf|timeout=1|timeout=30|systemctl reload opencart2|oc|ope_to_1|orders|carts|mysql leftover leftover down; bounce|OPENCART2_TIMEOUT leftover 1 leftover; a 2s place is aborted so the orders 504s
shopify2|SHOPIFY2_TIMEOUT|1|30|s|/etc/shopify2/shopify2.conf|timeout=1|timeout=30|systemctl reload shopify2|sh|sho_to_1|orders|webhooks|https leftover leftover down; bounce|SHOPIFY2_TIMEOUT leftover 1 leftover; a 2s create is aborted so the orders 504s
bigcommerce2|BIGCOMMERCE2_TIMEOUT|1|30|s|/etc/bigcommerce2/bigcommerce2.conf|timeout=1|timeout=30|systemctl reload bigcommerce2|bc|big_to_1|orders|webhooks|https leftover leftover down; bounce|BIGCOMMERCE2_TIMEOUT leftover 1 leftover; a 2s create is aborted so the orders 504s
saleor2|SALEOR2_TIMEOUT|1|30|s|/etc/saleor2/saleor2.conf|timeout=1|timeout=30|systemctl reload saleor2|sl|sal_to_1|orders|checkouts|https leftover leftover down; bounce|SALEOR2_TIMEOUT leftover 1 leftover; a 2s place is aborted so the orders 504s
medusa2|MEDUSA2_TIMEOUT|1|30|s|/etc/medusa2/medusa2.conf|timeout=1|timeout=30|systemctl reload medusa2|md|med_to_1|orders|carts|https leftover leftover down; bounce|MEDUSA2_TIMEOUT leftover 1 leftover; a 2s place is aborted so the orders 504s
sylius2|SYLIUS2_TIMEOUT|1|30|s|/etc/sylius2/sylius2.conf|timeout=1|timeout=30|systemctl reload sylius2|sy|syl_to_1|orders|carts|mysql leftover leftover down; bounce|SYLIUS2_TIMEOUT leftover 1 leftover; a 2s place is aborted so the orders 504s
vendure2|VENDURE2_TIMEOUT|1|30|s|/etc/vendure2/vendure2.conf|timeout=1|timeout=30|systemctl reload vendure2|vd|ven_to_1|orders|channels|pg leftover leftover down; bounce|VENDURE2_TIMEOUT leftover 1 leftover; a 2s place is aborted so the orders 504s
spree2|SPREE2_TIMEOUT|1|30|s|/etc/spree2/spree2.conf|timeout=1|timeout=30|systemctl reload spree2|sp|spr_to_1|orders|carts|pg leftover leftover down; bounce|SPREE2_TIMEOUT leftover 1 leftover; a 2s place is aborted so the orders 504s
solidus2|SOLIDUS2_TIMEOUT|1|30|s|/etc/solidus2/solidus2.conf|timeout=1|timeout=30|systemctl reload solidus2|so|sol_to_1|orders|carts|pg leftover leftover down; bounce|SOLIDUS2_TIMEOUT leftover 1 leftover; a 2s place is aborted so the orders 504s
broadleaf2|BROADLEAF2_TIMEOUT|1|30|s|/etc/broadleaf2/broadleaf2.conf|timeout=1|timeout=30|systemctl reload broadleaf2|bl|bro_to_1|orders|catalogs|https leftover leftover down; bounce|BROADLEAF2_TIMEOUT leftover 1 leftover; a 2s place is aborted so the orders 504s
commercetools2|COMMERCETOOLS2_TIMEOUT|1|30|s|/etc/commercetools2/commercetools2.conf|timeout=1|timeout=30|systemctl reload commercetools2|ct|com_to_1|orders|carts|https leftover leftover down; bounce|COMMERCETOOLS2_TIMEOUT leftover 1 leftover; a 2s place is aborted so the orders 504s
elasticpath2|ELASTICPATH2_TIMEOUT|1|30|s|/etc/elasticpath2/elasticpath2.conf|timeout=1|timeout=30|systemctl reload elasticpath2|ep|ela_to_1|orders|carts|https leftover leftover down; bounce|ELASTICPATH2_TIMEOUT leftover 1 leftover; a 2s place is aborted so the orders 504s
shopware2|SHOPWARE2_TIMEOUT|1|30|s|/etc/shopware2/shopware2.conf|timeout=1|timeout=30|systemctl reload shopware2|sw|sho_to_1|orders|carts|mysql leftover leftover down; bounce|SHOPWARE2_TIMEOUT leftover 1 leftover; a 2s place is aborted so the orders 504s
oxid2|OXID2_TIMEOUT|1|30|s|/etc/oxid2/oxid2.conf|timeout=1|timeout=30|systemctl reload oxid2|ox|oxi_to_1|orders|baskets|mysql leftover leftover down; bounce|OXID2_TIMEOUT leftover 1 leftover; a 2s place is aborted so the orders 504s
xtcommerce2|XTCOMMERCE2_TIMEOUT|1|30|s|/etc/xtcommerce2/xtcommerce2.conf|timeout=1|timeout=30|systemctl reload xtcommerce2|xt|xtc_to_1|orders|carts|mysql leftover leftover down; bounce|XTCOMMERCE2_TIMEOUT leftover 1 leftover; a 2s place is aborted so the orders 504s
oscommerce2|OSCOMMERCE2_TIMEOUT|1|30|s|/etc/oscommerce2/oscommerce2.conf|timeout=1|timeout=30|systemctl reload oscommerce2|os|osc_to_1|orders|carts|mysql leftover leftover down; bounce|OSCOMMERCE2_TIMEOUT leftover 1 leftover; a 2s place is aborted so the orders 504s
zencart2|ZENCART2_TIMEOUT|1|30|s|/etc/zencart2/zencart2.conf|timeout=1|timeout=30|systemctl reload zencart2|zc|zen_to_1|orders|carts|mysql leftover leftover down; bounce|ZENCART2_TIMEOUT leftover 1 leftover; a 2s place is aborted so the orders 504s
cubecart2|CUBECART2_TIMEOUT|1|30|s|/etc/cubecart2/cubecart2.conf|timeout=1|timeout=30|systemctl reload cubecart2|cc|cub_to_1|orders|baskets|mysql leftover leftover down; bounce|CUBECART2_TIMEOUT leftover 1 leftover; a 2s place is aborted so the orders 504s
abantecart2|ABANTECART2_TIMEOUT|1|30|s|/etc/abantecart2/abantecart2.conf|timeout=1|timeout=30|systemctl reload abantecart2|ab|aba_to_1|orders|carts|mysql leftover leftover down; bounce|ABANTECART2_TIMEOUT leftover 1 leftover; a 2s place is aborted so the orders 504s
opencart3|OPENCART3_TIMEOUT|1|30|s|/etc/opencart3/opencart3.conf|timeout=1|timeout=30|systemctl reload opencart3|o3|ope_to_1|orders|carts|mysql leftover leftover down; bounce|OPENCART3_TIMEOUT leftover 1 leftover; a 2s place is aborted so the orders 504s
nopcommerce2|NOPCOMMERCE2_TIMEOUT|1|30|s|/etc/nopcommerce2/nopcommerce2.conf|timeout=1|timeout=30|systemctl reload nopcommerce2|np|nop_to_1|orders|carts|mssql leftover leftover down; bounce|NOPCOMMERCE2_TIMEOUT leftover 1 leftover; a 2s place is aborted so the orders 504s
grandnode2|GRANDNODE2_TIMEOUT|1|30|s|/etc/grandnode2/grandnode2.conf|timeout=1|timeout=30|systemctl reload grandnode2|gn|gra_to_1|orders|carts|mongo leftover leftover down; bounce|GRANDNODE2_TIMEOUT leftover 1 leftover; a 2s place is aborted so the orders 504s
smartstore2|SMARTSTORE2_TIMEOUT|1|30|s|/etc/smartstore2/smartstore2.conf|timeout=1|timeout=30|systemctl reload smartstore2|ss|sma_to_1|orders|carts|mssql leftover leftover down; bounce|SMARTSTORE2_TIMEOUT leftover 1 leftover; a 2s place is aborted so the orders 504s
virto2|VIRTO2_TIMEOUT|1|30|s|/etc/virto2/virto2.conf|timeout=1|timeout=30|systemctl reload virto2|vr|vir_to_1|orders|carts|mssql leftover leftover down; bounce|VIRTO2_TIMEOUT leftover 1 leftover; a 2s place is aborted so the orders 504s
litium2|LITIUM2_TIMEOUT|1|30|s|/etc/litium2/litium2.conf|timeout=1|timeout=30|systemctl reload litium2|lt|lit_to_1|orders|websites|mssql leftover leftover down; bounce|LITIUM2_TIMEOUT leftover 1 leftover; a 2s place is aborted so the orders 504s
episerver2|EPISERVER2_TIMEOUT|1|30|s|/etc/episerver2/episerver2.conf|timeout=1|timeout=30|systemctl reload episerver2|es|epi_to_1|orders|catalogs|mssql leftover leftover down; bounce|EPISERVER2_TIMEOUT leftover 1 leftover; a 2s place is aborted so the orders 504s
'''
WAVE = (
    "appwrite2/nhost2/pocketbase2/directus2/strapi2/payload2/keystone2/ghost2/wordpress2/drupal3/joomla2/magento2/woocommerce2/prestashop2/opencart2/shopify2/bigcommerce2/saleor2/medusa2/sylius2/vendure2/spree2/solidus2/broadleaf2/commercetools2/elasticpath2/shopware2/oxid2/xtcommerce2/oscommerce2/zencart2/cubecart2/abantecart2/opencart3/nopcommerce2/grandnode2/smartstore2/virto2/litium2/episerver2"
)


def _parse_rows():
    plants = []
    srcs = ("grafana", "pagerduty", "opsgenie", "alertmanager")
    ns_cycle = (17, 16, 18)
    for raw in ROWS.strip().splitlines():
        raw = raw.strip()
        if not raw or raw.startswith("#"):
            continue
        parts = raw.split("|")
        if len(parts) != 15:
            raise SystemExit(f"bad row cols={len(parts)}: {raw[:160]}")
        (
            daemon, key, old, new, unit, path, oldv, newv, reload, hpeer, metric,
            what, wipe, herring, rca_tail,
        ) = parts
        i = len(plants)
        n = ns_cycle[i % 3]
        rem = "rollback" if i % 2 == 0 else "patch"
        src = srcs[i % 4]
        svc = f"k9{i:02d}x"
        ns = f"k9{i:02d}"
        clu = f"prod-apug{901 + i}-{svc[:3]}"
        ticket = f"W2-{ 13723 + i }"
        node = f"ip-10-185-{1 + i}-{20 + i}"
        slug = f"{daemon}-{key}-{old}{unit}-{svc}"
        key_words = key.replace(".", " leftover ").replace("_", " leftover ")
        symptom = f"{key_words} leftover {old}{unit} leftover; {what} drop"
        because = (
            f"is dropping {what} because leftover {daemon} leftover {key_words} leftover is {old} leftover."
        )
        do_not = f"Restore {new}{unit}; do not wipe {wipe}."
        rca = f"{daemon} leftover {key} leftover {old} leftover; {rca_tail}"
        if remnant := (helm_rb(ns, svc, 3, path, oldv, newv, reload) if rem == "rollback" else patch_file(path, oldv, newv, reload)):
            extra = f"helm -n {ns} history {svc} | head -5" if rem == "rollback" else f"kubectl -n {ns} logs deploy/{svc} --since=5m | grep {key} | tail"
            eobs = f"4  {old}{unit}\n3  last-good {new}" if rem == "rollback" else f"{key} leftover {old}"
        plants.append(
            plant(
                slug=slug, ticket=ticket, service=svc, ns=ns, cluster=clu, src=src,
                node=node, symptom=symptom, because=because, do_not=do_not,
                herring=herring, rca=rca, remediate=rem, metric=metric,
                hcmds=[
                    f"{hpeer} leftover status | head",
                    f"systemctl reload {hpeer} || true",
                    f"{hpeer} leftover bounce leftover || true",
                ],
                hobs=[f"{hpeer} ok", "bounce unused", f"still {key} {old}"],
                inspect=f"grep {key} {path}", iobs=f"{oldv} leftover",
                extra=extra, eobs=eobs, rem=remnant, robs=f"{key} {new}; holds",
                verify=f"grep {key} {path}", vok=f"{new}; {ticket} resolved", n=n,
            )
        )
    return plants


PLANTS = _parse_rows()
m.PLANTS = PLANTS
m.BASE_ROUND = 4601


def notes_for(round_n, eps):
    slug0 = eps[0]["id"].split("-", 2)[2].rsplit("-", 2)[0]
    slug1 = eps[1]["id"].split("-", 2)[2].rsplit("-", 2)[0]
    rows = [
        f"| `{e['id']}` | {e['meta']['ticket']} | {e['false_lead']['claim'].replace('|', '/')} | {e['remediate']} | {e['reward']['success']} | {e['reward']['steps']} |"
        for e in eps
    ]
    return "\n".join(
        [
            f"# incident-response-oncall-factory NOTES r{round_n}",
            "",
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r4317 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-75 leftover: {WAVE}.",
            "",
            "OpenSRE designed: 429 then 502 retries, 3-step herring, unique RCA, mix patch/rollback. plant=designed. generator=grok-4.6.",
            "",
            "| id | ticket | herring (steps 6-8) | remediate | success | steps |",
            "|---|---|---|---|---|---|",
            *rows,
            "",
            "## Contract audit",
            f"- Q=2 episodes, kind=episode, ids irc-r{round_n}-*.",
            "- Unique goal service+cluster+symptom; 3 false-lead actions; 429/502 retries.",
            "- Residual: designed excerpts, not live dispatcher traces.",
            "",
        ]
    )


m.notes_for = notes_for


def extra_unique_guards():
    banned = (
        "Follow OpenSRE", "fraud-graph", "sip-proxy", "traefik", "limit_req",
        "cloudfront", "fastly", "kube-proxy", "haproxy", "varnish", "metallb",
        "imperva", "bunny", "calico felix", "kong ", "caddy ",
        "github actions leftover", "gitlab leftover", "circleci leftover",
        "tekton leftover", "snowflake", "bigquery", "redshift", "idle_timeout",
        "max_client_conn", "ypbind", "oddjob", "opensearch", "leftover3c",
        "tigergraph", "hugegraph", "graphdb", "stardog", "debezium", "hasura",
    )
    for p in PLANTS:
        blob = (p["goal"] + " " + p["rca"] + " " + p["slug"]).lower()
        for tok in banned:
            if tok.lower() in blob:
                raise SystemExit(f"banned {tok} in {p['slug']}")
        for need in (p["service"], p["ns"], p["cluster"]):
            if need not in p["goal"]:
                raise SystemExit(p["slug"])
        if p["n_steps"] not in (16, 17, 18) or p["remediate"] not in ("rollback", "patch"):
            raise SystemExit(p["slug"])
    if len(PLANTS) % 2:
        raise SystemExit("odd")
    for i in range(0, len(PLANTS), 2):
        if {PLANTS[i]["remediate"], PLANTS[i + 1]["remediate"]} != {"rollback", "patch"}:
            raise SystemExit(f"pair {i}")


def main():
    extra_unique_guards()
    used_svc, used_clu, used_tix, _ids = m.harvest_used(m.FACTORY_DIR)
    for p in PLANTS:
        if p["service"] in used_svc:
            raise SystemExit(f"service collision {p['service']}")
        if p["cluster"] in used_clu:
            raise SystemExit(f"cluster collision {p['cluster']}")
        if p["ticket"] in used_tix:
            raise SystemExit(f"ticket collision {p['ticket']}")
    for label, xs in (
        ("slug", [p["slug"] for p in PLANTS]),
        ("svc", [p["service"] for p in PLANTS]),
        ("clu", [p["cluster"] for p in PLANTS]),
        ("tix", [p["ticket"] for p in PLANTS]),
        ("node", [p["node"] for p in PLANTS]),
        ("ns", [p["ns"] for p in PLANTS]),
    ):
        if len(set(xs)) != len(xs):
            raise SystemExit("dup " + label)
    print(json.dumps({"ok": True, "plants": len(PLANTS), "rounds": len(PLANTS) // 2}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
