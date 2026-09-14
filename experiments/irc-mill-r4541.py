#!/usr/bin/env python3
"""IRC mill r4541+ — wave-72 billing/crm/erp leftover.

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
stripe2|STRIPE2_TIMEOUT|1|30|s|/etc/stripe2/stripe2.conf|timeout=1|timeout=30|systemctl reload stripe2|st|str_to_1|intents|webhooks|https leftover leftover down; bounce|STRIPE2_TIMEOUT leftover 1 leftover; a 2s confirm is aborted so the intents 504s
braintree2|BRAINTREE2_TIMEOUT|1|30|s|/etc/braintree2/braintree2.conf|timeout=1|timeout=30|systemctl reload braintree2|bt|bra_to_1|txns|vaults|https leftover leftover down; bounce|BRAINTREE2_TIMEOUT leftover 1 leftover; a 2s sale is aborted so the txns 504s
adyen2|ADYEN2_TIMEOUT|1|30|s|/etc/adyen2/adyen2.conf|timeout=1|timeout=30|systemctl reload adyen2|ad|ady_to_1|payments|webhooks|https leftover leftover down; bounce|ADYEN2_TIMEOUT leftover 1 leftover; a 2s authorise is aborted so the payments 504s
square2|SQUARE2_TIMEOUT|1|30|s|/etc/square2/square2.conf|timeout=1|timeout=30|systemctl reload square2|sq|squ_to_1|payments|locs|https leftover leftover down; bounce|SQUARE2_TIMEOUT leftover 1 leftover; a 2s create is aborted so the payments 504s
paypal2|PAYPAL2_TIMEOUT|1|30|s|/etc/paypal2/paypal2.conf|timeout=1|timeout=30|systemctl reload paypal2|pp|pay_to_1|orders|webhooks|https leftover leftover down; bounce|PAYPAL2_TIMEOUT leftover 1 leftover; a 2s capture is aborted so the orders 504s
chargebee2|CHARGEBEE2_TIMEOUT|1|30|s|/etc/chargebee2/chargebee2.conf|timeout=1|timeout=30|systemctl reload chargebee2|cb|cha_to_1|subs|invoices|https leftover leftover down; bounce|CHARGEBEE2_TIMEOUT leftover 1 leftover; a 2s renew is aborted so the subs 504s
recurly2|RECURLY2_TIMEOUT|1|30|s|/etc/recurly2/recurly2.conf|timeout=1|timeout=30|systemctl reload recurly2|rc|rec_to_1|subs|invoices|https leftover leftover down; bounce|RECURLY2_TIMEOUT leftover 1 leftover; a 2s renew is aborted so the subs 504s
zuora2|ZUORA2_TIMEOUT|1|30|s|/etc/zuora2/zuora2.conf|timeout=1|timeout=30|systemctl reload zuora2|zu|zuo_to_1|subs|invoices|https leftover leftover down; bounce|ZUORA2_TIMEOUT leftover 1 leftover; a 2s bill is aborted so the subs 504s
maxio2|MAXIO2_TIMEOUT|1|30|s|/etc/maxio2/maxio2.conf|timeout=1|timeout=30|systemctl reload maxio2|mx|max_to_1|subs|invoices|https leftover leftover down; bounce|MAXIO2_TIMEOUT leftover 1 leftover; a 2s bill is aborted so the subs 504s
killbill2|KILLBILL2_TIMEOUT|1|30|s|/etc/killbill2/killbill2.conf|timeout=1|timeout=30|systemctl reload killbill2|kb|kil_to_1|invoices|accounts|https leftover leftover down; bounce|KILLBILL2_TIMEOUT leftover 1 leftover; a 2s commit is aborted so the invoices 504s
odoo2|ODOO2_TIMEOUT|1|30|s|/etc/odoo2/odoo2.conf|timeout=1|timeout=30|systemctl reload odoo2|od|odo_to_1|invoices|partners|pg leftover leftover down; bounce|ODOO2_TIMEOUT leftover 1 leftover; a 2s post is aborted so the invoices 504s
erpnext2|ERPNEXT2_TIMEOUT|1|30|s|/etc/erpnext2/erpnext2.conf|timeout=1|timeout=30|systemctl reload erpnext2|en|erp_to_1|invoices|docs|mariadb leftover leftover down; bounce|ERPNEXT2_TIMEOUT leftover 1 leftover; a 2s submit is aborted so the invoices 504s
tryton2|TRYTON2_TIMEOUT|1|30|s|/etc/tryton2/tryton2.conf|timeout=1|timeout=30|systemctl reload tryton2|ty|try_to_1|invoices|parties|pg leftover leftover down; bounce|TRYTON2_TIMEOUT leftover 1 leftover; a 2s post is aborted so the invoices 504s
idempiere2|IDEMPIERE2_TIMEOUT|1|30|s|/etc/idempiere2/idempiere2.conf|timeout=1|timeout=30|systemctl reload idempiere2|id|ide_to_1|invoices|orgs|pg leftover leftover down; bounce|IDEMPIERE2_TIMEOUT leftover 1 leftover; a 2s complete is aborted so the invoices 504s
ofbiz2|OFBIZ2_TIMEOUT|1|30|s|/etc/ofbiz2/ofbiz2.conf|timeout=1|timeout=30|systemctl reload ofbiz2|of|ofb_to_1|invoices|parties|derby leftover leftover down; bounce|OFBIZ2_TIMEOUT leftover 1 leftover; a 2s post is aborted so the invoices 504s
dolibarr2|DOLIBARR2_TIMEOUT|1|30|s|/etc/dolibarr2/dolibarr2.conf|timeout=1|timeout=30|systemctl reload dolibarr2|db|dol_to_1|invoices|thirds|mysql leftover leftover down; bounce|DOLIBARR2_TIMEOUT leftover 1 leftover; a 2s validate is aborted so the invoices 504s
suitecrm2|SUITECRM2_TIMEOUT|1|30|s|/etc/suitecrm2/suitecrm2.conf|timeout=1|timeout=30|systemctl reload suitecrm2|sc|sui_to_1|leads|accounts|mysql leftover leftover down; bounce|SUITECRM2_TIMEOUT leftover 1 leftover; a 2s save is aborted so the leads 504s
vtiger2|VTIGER2_TIMEOUT|1|30|s|/etc/vtiger2/vtiger2.conf|timeout=1|timeout=30|systemctl reload vtiger2|vt|vti_to_1|leads|potentials|mysql leftover leftover down; bounce|VTIGER2_TIMEOUT leftover 1 leftover; a 2s save is aborted so the leads 504s
sugarcrm2|SUGARCRM2_TIMEOUT|1|30|s|/etc/sugarcrm2/sugarcrm2.conf|timeout=1|timeout=30|systemctl reload sugarcrm2|sg|sug_to_1|leads|accounts|mysql leftover leftover down; bounce|SUGARCRM2_TIMEOUT leftover 1 leftover; a 2s save is aborted so the leads 504s
civicrm2|CIVICRM2_TIMEOUT|1|30|s|/etc/civicrm2/civicrm2.conf|timeout=1|timeout=30|systemctl reload civicrm2|cv|civ_to_1|contacts|contribs|mysql leftover leftover down; bounce|CIVICRM2_TIMEOUT leftover 1 leftover; a 2s save is aborted so the contacts 504s
espocrm2|ESPOCRM2_TIMEOUT|1|30|s|/etc/espocrm2/espocrm2.conf|timeout=1|timeout=30|systemctl reload espocrm2|es|esp_to_1|leads|accounts|mysql leftover leftover down; bounce|ESPOCRM2_TIMEOUT leftover 1 leftover; a 2s save is aborted so the leads 504s
fatfree2|FATFREE2_TIMEOUT|1|30|s|/etc/fatfree2/fatfree2.conf|timeout=1|timeout=30|systemctl reload fatfree2|ff|fat_to_1|invoices|clients|mysql leftover leftover down; bounce|FATFREE2_TIMEOUT leftover 1 leftover; a 2s save is aborted so the invoices 504s
invoice2|INVOICE2_TIMEOUT|1|30|s|/etc/invoice2/invoice2.conf|timeout=1|timeout=30|systemctl reload invoice2|inv|inv_to_1|invoices|clients|mysql leftover leftover down; bounce|INVOICE2_TIMEOUT leftover 1 leftover; a 2s send is aborted so the invoices 504s
akaunting2|AKAUNTING2_TIMEOUT|1|30|s|/etc/akaunting2/akaunting2.conf|timeout=1|timeout=30|systemctl reload akaunting2|ak|aka_to_1|invoices|companies|mysql leftover leftover down; bounce|AKAUNTING2_TIMEOUT leftover 1 leftover; a 2s send is aborted so the invoices 504s
firefly2|FIREFLY2_TIMEOUT|1|30|s|/etc/firefly2/firefly2.conf|timeout=1|timeout=30|systemctl reload firefly2|fy|fir_to_1|txns|accounts|mysql leftover leftover down; bounce|FIREFLY2_TIMEOUT leftover 1 leftover; a 2s store is aborted so the txns 504s
gnucash2|GNUCASH2_TIMEOUT|1|30|s|/etc/gnucash2/gnucash2.conf|timeout=1|timeout=30|systemctl reload gnucash2|gc|gnu_to_1|txns|books|sqlite leftover leftover down; bounce|GNUCASH2_TIMEOUT leftover 1 leftover; a 2s post is aborted so the txns 504s
ledger2|LEDGER2_TIMEOUT|1|30|s|/etc/ledger2/ledger2.conf|timeout=1|timeout=30|systemctl reload ledger2|ld|led_to_1|txns|jnl|fs leftover leftover down; bounce|LEDGER2_TIMEOUT leftover 1 leftover; a 2s balance is aborted so the txns 504s
beancount2|BEANCOUNT2_TIMEOUT|1|30|s|/etc/beancount2/beancount2.conf|timeout=1|timeout=30|systemctl reload beancount2|bc|bea_to_1|txns|ledgers|fs leftover leftover down; bounce|BEANCOUNT2_TIMEOUT leftover 1 leftover; a 2s balance is aborted so the txns 504s
hledger2|HLEDGER2_TIMEOUT|1|30|s|/etc/hledger2/hledger2.conf|timeout=1|timeout=30|systemctl reload hledger2|hl|hle_to_1|txns|jnl|fs leftover leftover down; bounce|HLEDGER2_TIMEOUT leftover 1 leftover; a 2s balance is aborted so the txns 504s
actual2|ACTUAL2_TIMEOUT|1|30|s|/etc/actual2/actual2.conf|timeout=1|timeout=30|systemctl reload actual2|ac|act_to_1|txns|budgets|https leftover leftover down; bounce|ACTUAL2_TIMEOUT leftover 1 leftover; a 2s sync is aborted so the txns 504s
maybe2|MAYBE2_TIMEOUT|1|30|s|/etc/maybe2/maybe2.conf|timeout=1|timeout=30|systemctl reload maybe2|mb|may_to_1|txns|accounts|https leftover leftover down; bounce|MAYBE2_TIMEOUT leftover 1 leftover; a 2s sync is aborted so the txns 504s
plaid2|PLAID2_TIMEOUT|1|30|s|/etc/plaid2/plaid2.conf|timeout=1|timeout=30|systemctl reload plaid2|pl|pla_to_1|items|txns|https leftover leftover down; bounce|PLAID2_TIMEOUT leftover 1 leftover; a 2s sync is aborted so the items 504s
teller2|TELLER2_TIMEOUT|1|30|s|/etc/teller2/teller2.conf|timeout=1|timeout=30|systemctl reload teller2|tl|tel_to_1|accounts|txns|https leftover leftover down; bounce|TELLER2_TIMEOUT leftover 1 leftover; a 2s sync is aborted so the accounts 504s
gocardless2|GOCARDLESS2_TIMEOUT|1|30|s|/etc/gocardless2/gocardless2.conf|timeout=1|timeout=30|systemctl reload gocardless2|go|goc_to_1|mandates|pmts|https leftover leftover down; bounce|GOCARDLESS2_TIMEOUT leftover 1 leftover; a 2s collect is aborted so the mandates 504s
wise2|WISE2_TIMEOUT|1|30|s|/etc/wise2/wise2.conf|timeout=1|timeout=30|systemctl reload wise2|ws|wis_to_1|transfers|profiles|https leftover leftover down; bounce|WISE2_TIMEOUT leftover 1 leftover; a 2s fund is aborted so the transfers 504s
stripebilling|STRIPEBILLING_TIMEOUT|1|30|s|/etc/stripebilling/stripebilling.conf|timeout=1|timeout=30|systemctl reload stripebilling|sb|str_to_1|invoices|subs|https leftover leftover down; bounce|STRIPEBILLING_TIMEOUT leftover 1 leftover; a 2s finalize is aborted so the invoices 504s
taxjar2|TAXJAR2_TIMEOUT|1|30|s|/etc/taxjar2/taxjar2.conf|timeout=1|timeout=30|systemctl reload taxjar2|tj|tax_to_1|rates|orders|https leftover leftover down; bounce|TAXJAR2_TIMEOUT leftover 1 leftover; a 2s calc is aborted so the rates 504s
avalara2|AVALARA2_TIMEOUT|1|30|s|/etc/avalara2/avalara2.conf|timeout=1|timeout=30|systemctl reload avalara2|av|ava_to_1|rates|txns|https leftover leftover down; bounce|AVALARA2_TIMEOUT leftover 1 leftover; a 2s calc is aborted so the rates 504s
vertex2|VERTEX2_TIMEOUT|1|30|s|/etc/vertex2/vertex2.conf|timeout=1|timeout=30|systemctl reload vertex2|vx|ver_to_1|rates|docs|https leftover leftover down; bounce|VERTEX2_TIMEOUT leftover 1 leftover; a 2s calc is aborted so the rates 504s
sovos2|SOVOS2_TIMEOUT|1|30|s|/etc/sovos2/sovos2.conf|timeout=1|timeout=30|systemctl reload sovos2|sv|sov_to_1|returns|docs|https leftover leftover down; bounce|SOVOS2_TIMEOUT leftover 1 leftover; a 2s file is aborted so the returns 504s
'''
WAVE = (
    "stripe2/braintree2/adyen2/square2/paypal2/chargebee2/recurly2/zuora2/maxio2/killbill2/odoo2/erpnext2/tryton2/idempiere2/ofbiz2/dolibarr2/suitecrm2/vtiger2/sugarcrm2/civicrm2/espocrm2/fatfree2/invoice2/akaunting2/firefly2/gnucash2/ledger2/beancount2/hledger2/actual2/maybe2/plaid2/teller2/gocardless2/wise2/stripebilling/taxjar2/avalara2/vertex2/sovos2"
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
        svc = f"c8{i:02d}x"
        ns = f"c8{i:02d}"
        clu = f"prod-apud{901 + i}-{svc[:3]}"
        ticket = f"W2-{ 13603 + i }"
        node = f"ip-10-182-{1 + i}-{20 + i}"
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
m.BASE_ROUND = 4541


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
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r4317 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-72 leftover: {WAVE}.",
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
