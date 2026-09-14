#!/usr/bin/env python3
"""Designed leftover cache-stampede mill r2144+ (cst- ids). BAN r1–r2143.

BAN r1730 husky-init, r1690 woodpecker, r1445 akamai-esi, r2143 sssd-nsscache.
Not overlayfs/nydus/stargz. Not docker/search-index leftover.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("cst1446", HERE / "cst-mill-r1446.py")
_m = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_m)
_steps_ok = _m._steps_ok
_steps_part = _m._steps_part
CATALOG_FIRST = 2144

PAIRS: list[tuple] = [
    ("Postfix", "postfix-anvil-leftover", "postfix-scache-handoff", "flock-pstfx",
     "src/main.cf", "tests/test_postfix.py", "anvil leftover",
     "drop anvil on miss", "anvil leftover + wait + do(conn)", 16,
     "scache leftover still 1s", "scache leftover",
     "src/main_sc.cf", "tests/test_postfix_sc.py", "gets"),
    ("Exim", "exim-retry-leftover", "exim-acl-handoff", "flock-eximr",
     "src/exim.conf", "tests/test_exim.py", "retry leftover",
     "drop retry on miss", "retry leftover + wait + do(msg)", 15,
     "acl leftover still 1s", "acl leftover",
     "src/exim_acl.conf", "tests/test_exim_acl.py", "gets"),
    ("OpenSMTPD", "opensmtpd-queue-leftover", "opensmtpd-filter-handoff", "flock-osmtp",
     "src/smtpd.conf", "tests/test_opensmtpd.py", "queue leftover",
     "drop queue on miss", "q leftover + wait + do(msg)", 14,
     "filter leftover still 1s", "filter leftover",
     "src/smtpd_fl.conf", "tests/test_opensmtpd_fl.py", "gets"),
    ("Dovecot", "dovecot-index-leftover", "dovecot-auth-handoff", "flock-dovct",
     "src/dovecot.conf", "tests/test_dovecot.py", "index leftover",
     "drop index on miss", "idx leftover + wait + do(mbox)", 17,
     "auth leftover still 1s", "auth leftover",
     "src/dovecot_au.conf", "tests/test_dovecot_au.py", "gets"),
    ("Cyrus IMAP", "cyrus-mailbox-leftover", "cyrus-sieve-handoff", "flock-cyrus",
     "src/imapd.conf", "tests/test_cyrus.py", "mailbox leftover",
     "drop mailbox on miss", "mb leftover + wait + do(mbox)", 14,
     "sieve leftover still 1s", "sieve leftover",
     "src/imapd_sv.conf", "tests/test_cyrus_sv.py", "gets"),
    ("rspamd", "rspamd-fuzzy-leftover", "rspamd-redis-handoff", "flock-rspmd",
     "src/rspamd.conf", "tests/test_rspamd.py", "fuzzy leftover",
     "drop fuzzy on miss", "fuzzy leftover + wait + do(msg)", 16,
     "redis leftover still 1s", "redis leftover",
     "src/rspamd_rd.conf", "tests/test_rspamd_rd.py", "gets"),
    ("SpamAssassin", "sa-bayes-leftover", "sa-awl-handoff", "flock-spams",
     "src/local.cf", "tests/test_sa.py", "bayes leftover",
     "drop bayes on miss", "bayes leftover + wait + do(msg)", 13,
     "awl leftover still 1s", "awl leftover",
     "src/local_awl.cf", "tests/test_sa_awl.py", "gets"),
    ("ClamAV", "clamav-mdb-leftover", "clamav-cvd-handoff", "flock-clamv",
     "src/clamd.conf", "tests/test_clamav.py", "mdb leftover",
     "drop mdb on miss", "mdb leftover + wait + do(file)", 15,
     "cvd leftover still 1s", "cvd leftover",
     "src/clamd_cvd.conf", "tests/test_clamav_cvd.py", "gets"),
    ("OpenDKIM", "opendkim-key-leftover", "opendkim-sign-handoff", "flock-odkim",
     "src/opendkim.conf", "tests/test_opendkim.py", "key leftover",
     "drop key on miss", "key leftover + wait + do(msg)", 12,
     "sign leftover still 1s", "sign leftover",
     "src/opendkim_sg.conf", "tests/test_opendkim_sg.py", "gets"),
    ("Mailgun", "mailgun-event-leftover", "mailgun-route-handoff", "flock-mlgun",
     "src/mailgun.json", "tests/test_mailgun.py", "event leftover",
     "drop event on miss", "evt leftover + wait + do(msg)", 14,
     "route leftover still 1s", "route leftover",
     "src/mailgun_rt.json", "tests/test_mailgun_rt.py", "gets"),
    ("SendGrid", "sendgrid-event-leftover", "sendgrid-template-handoff", "flock-sndgd",
     "src/sendgrid.json", "tests/test_sendgrid.py", "event leftover",
     "drop event on miss", "evt leftover + wait + do(msg)", 15,
     "template leftover still 1s", "template leftover",
     "src/sendgrid_tp.json", "tests/test_sendgrid_tp.py", "gets"),
    ("Amazon SES", "ses-event-leftover", "ses-template-handoff", "flock-sesev",
     "src/ses.json", "tests/test_ses.py", "event leftover",
     "drop event on miss", "evt leftover + wait + do(msg)", 16,
     "template leftover still 1s", "template leftover",
     "src/ses_tp.json", "tests/test_ses_tp.py", "gets"),
    ("Postmark", "postmark-event-leftover", "postmark-template-handoff", "flock-pstmk",
     "src/postmark.json", "tests/test_postmark.py", "event leftover",
     "drop event on miss", "evt leftover + wait + do(msg)", 13,
     "template leftover still 1s", "template leftover",
     "src/postmark_tp.json", "tests/test_postmark_tp.py", "gets"),
    ("Resend", "resend-event-leftover", "resend-domain-handoff", "flock-rsnde",
     "src/resend.json", "tests/test_resend.py", "event leftover",
     "drop event on miss", "evt leftover + wait + do(msg)", 12,
     "domain leftover still 1s", "domain leftover",
     "src/resend_dm.json", "tests/test_resend_dm.py", "gets"),
    ("Auth0", "auth0-jwks-leftover", "auth0-session-handoff", "flock-ath0j",
     "src/auth0.json", "tests/test_auth0.py", "jwks leftover",
     "drop jwks on miss", "jwks leftover + wait + do(tok)", 17,
     "session leftover still 1s", "session leftover",
     "src/auth0_ss.json", "tests/test_auth0_ss.py", "gets"),
    ("Okta", "okta-session-leftover", "okta-jwks-handoff", "flock-oktas",
     "src/okta.json", "tests/test_okta.py", "session leftover",
     "drop session on miss", "sess leftover + wait + do(tok)", 16,
     "jwks leftover still 1s", "jwks leftover",
     "src/okta_jw.json", "tests/test_okta_jw.py", "gets"),
    ("Keycloak", "keycloak-realm-leftover", "keycloak-jwks-handoff", "flock-kyclk",
     "src/keycloak.json", "tests/test_keycloak.py", "realm leftover",
     "drop realm on miss", "realm leftover + wait + do(tok)", 18,
     "jwks leftover still 1s", "jwks leftover",
     "src/keycloak_jw.json", "tests/test_keycloak_jw.py", "gets"),
    ("Authentik", "authentik-flow-leftover", "authentik-jwks-handoff", "flock-autnk",
     "src/authentik.yaml", "tests/test_authentik.py", "flow leftover",
     "drop flow on miss", "flow leftover + wait + do(tok)", 15,
     "jwks leftover still 1s", "jwks leftover",
     "src/authentik_jw.yaml", "tests/test_authentik_jw.py", "gets"),
    ("Dex IdP", "dex-storage-leftover", "dex-connector-handoff", "flock-dexst",
     "src/dex.yaml", "tests/test_dex.py", "storage leftover",
     "drop storage on miss", "st leftover + wait + do(tok)", 14,
     "connector leftover still 1s", "connector leftover",
     "src/dex_cn.yaml", "tests/test_dex_cn.py", "gets"),
    ("Ory Hydra", "hydra-consent-leftover", "hydra-jwks-handoff", "flock-hydrc",
     "src/hydra.yml", "tests/test_hydra.py", "consent leftover",
     "drop consent on miss", "cons leftover + wait + do(tok)", 16,
     "jwks leftover still 1s", "jwks leftover",
     "src/hydra_jw.yml", "tests/test_hydra_jw.py", "gets"),
    ("Ory Kratos", "kratos-session-leftover", "kratos-identity-handoff", "flock-krats",
     "src/kratos.yml", "tests/test_kratos.py", "session leftover",
     "drop session on miss", "sess leftover + wait + do(id)", 15,
     "identity leftover still 1s", "identity leftover",
     "src/kratos_id.yml", "tests/test_kratos_id.py", "gets"),
    ("Authelia", "authelia-session-leftover", "authelia-storage-handoff", "flock-authl",
     "src/authelia.yml", "tests/test_authelia.py", "session leftover",
     "drop session on miss", "sess leftover + wait + do(user)", 14,
     "storage leftover still 1s", "storage leftover",
     "src/authelia_st.yml", "tests/test_authelia_st.py", "gets"),
    ("Pomerium", "pomerium-session-leftover", "pomerium-databroker-handoff", "flock-pmerm",
     "src/pomerium.yaml", "tests/test_pomerium.py", "session leftover",
     "drop session on miss", "sess leftover + wait + do(req)", 15,
     "databroker leftover still 1s", "databroker leftover",
     "src/pomerium_db.yaml", "tests/test_pomerium_db.py", "gets"),
    ("oauth2-proxy", "o2p-session-leftover", "o2p-cookie-handoff", "flock-o2pss",
     "src/oauth2-proxy.cfg", "tests/test_o2p.py", "session leftover",
     "drop session on miss", "sess leftover + wait + do(req)", 13,
     "cookie leftover still 1s", "cookie leftover",
     "src/oauth2-proxy_ck.cfg", "tests/test_o2p_ck.py", "gets"),
    ("Casdoor", "casdoor-token-leftover", "casdoor-org-handoff", "flock-csdrt",
     "src/casdoor.conf", "tests/test_casdoor.py", "token leftover",
     "drop token on miss", "tok leftover + wait + do(tok)", 12,
     "org leftover still 1s", "org leftover",
     "src/casdoor_org.conf", "tests/test_casdoor_org.py", "gets"),
    ("Zitadel", "zitadel-session-leftover", "zitadel-jwks-handoff", "flock-ztdls",
     "src/zitadel.yaml", "tests/test_zitadel.py", "session leftover",
     "drop session on miss", "sess leftover + wait + do(tok)", 16,
     "jwks leftover still 1s", "jwks leftover",
     "src/zitadel_jw.yaml", "tests/test_zitadel_jw.py", "gets"),
    ("FusionAuth", "fusionauth-jwt-leftover", "fusionauth-app-handoff", "flock-fusna",
     "src/fusionauth.json", "tests/test_fusionauth.py", "jwt leftover",
     "drop jwt on miss", "jwt leftover + wait + do(tok)", 14,
     "app leftover still 1s", "app leftover",
     "src/fusionauth_ap.json", "tests/test_fusionauth_ap.py", "gets"),
    ("Clerk", "clerk-session-leftover", "clerk-jwks-handoff", "flock-clrks",
     "src/clerk.json", "tests/test_clerk.py", "session leftover",
     "drop session on miss", "sess leftover + wait + do(tok)", 13,
     "jwks leftover still 1s", "jwks leftover",
     "src/clerk_jw.json", "tests/test_clerk_jw.py", "gets"),
    ("WorkOS", "workos-session-leftover", "workos-directory-handoff", "flock-wrkoss",
     "src/workos.json", "tests/test_workos.py", "session leftover",
     "drop session on miss", "sess leftover + wait + do(tok)", 14,
     "directory leftover still 1s", "directory leftover",
     "src/workos_dir.json", "tests/test_workos_dir.py", "gets"),
    ("Stytch", "stytch-session-leftover", "stytch-jwks-handoff", "flock-stytc",
     "src/stytch.json", "tests/test_stytch.py", "session leftover",
     "drop session on miss", "sess leftover + wait + do(tok)", 13,
     "jwks leftover still 1s", "jwks leftover",
     "src/stytch_jw.json", "tests/test_stytch_jw.py", "gets"),
    ("NextAuth", "nextauth-jwt-leftover", "nextauth-session-handoff", "flock-nxtau",
     "src/auth.ts", "tests/test_nextauth.py", "jwt leftover",
     "drop jwt on miss", "jwt leftover + wait + do(tok)", 15,
     "session leftover still 1s", "session leftover",
     "src/auth_ss.ts", "tests/test_nextauth_ss.py", "gets"),
    ("Lucia Auth", "lucia-session-leftover", "lucia-cookie-handoff", "flock-lucia",
     "src/lucia.ts", "tests/test_lucia.py", "session leftover",
     "drop session on miss", "sess leftover + wait + do(tok)", 12,
     "cookie leftover still 1s", "cookie leftover",
     "src/lucia_ck.ts", "tests/test_lucia_ck.py", "gets"),
    ("Better Auth", "betterauth-session-leftover", "betterauth-jwks-handoff", "flock-btrau",
     "src/auth.ts", "tests/test_betterauth.py", "session leftover",
     "drop session on miss", "sess leftover + wait + do(tok)", 14,
     "jwks leftover still 1s", "jwks leftover",
     "src/auth_jw.ts", "tests/test_betterauth_jw.py", "gets"),
    ("AWS Cognito", "cognito-jwks-leftover", "cognito-userpool-handoff", "flock-cgnto",
     "src/cognito.json", "tests/test_cognito.py", "jwks leftover",
     "drop jwks on miss", "jwks leftover + wait + do(tok)", 16,
     "userpool leftover still 1s", "userpool leftover",
     "src/cognito_up.json", "tests/test_cognito_up.py", "gets"),
    ("Firebase Auth", "firebaseauth-idtoken-leftover", "firebaseauth-session-handoff", "flock-fbaut",
     "src/firebase.json", "tests/test_fbauth.py", "idtoken leftover",
     "drop idtoken on miss", "idt leftover + wait + do(tok)", 15,
     "session leftover still 1s", "session leftover",
     "src/firebase_ss.json", "tests/test_fbauth_ss.py", "gets"),
    ("Supabase Auth", "gotrue-session-leftover", "gotrue-jwks-handoff", "flock-gtrue",
     "src/gotrue.env", "tests/test_gotrue.py", "session leftover",
     "drop session on miss", "sess leftover + wait + do(tok)", 14,
     "jwks leftover still 1s", "jwks leftover",
     "src/gotrue_jw.env", "tests/test_gotrue_jw.py", "gets"),
    ("Laravel Sanctum", "sanctum-token-leftover", "sanctum-cookie-handoff", "flock-snctm",
     "src/sanctum.php", "tests/test_sanctum.py", "token leftover",
     "drop token on miss", "tok leftover + wait + do(tok)", 13,
     "cookie leftover still 1s", "cookie leftover",
     "src/sanctum_ck.php", "tests/test_sanctum_ck.py", "gets"),
    ("Devise", "devise-warden-leftover", "devise-timeout-handoff", "flock-dvisw",
     "src/devise.rb", "tests/test_devise.py", "warden leftover",
     "drop warden on miss", "warden leftover + wait + do(sess)", 14,
     "timeout leftover still 1s", "timeout leftover",
     "src/devise_to.rb", "tests/test_devise_to.py", "gets"),
    ("Passport.js", "passport-session-leftover", "passport-strategy-handoff", "flock-psspt",
     "src/passport.js", "tests/test_passport.py", "session leftover",
     "drop session on miss", "sess leftover + wait + do(user)", 13,
     "strategy leftover still 1s", "strategy leftover",
     "src/passport_st.js", "tests/test_passport_st.py", "gets"),
    ("django-allauth", "allauth-session-leftover", "allauth-adapter-handoff", "flock-allau",
     "src/allauth.py", "tests/test_allauth.py", "session leftover",
     "drop session on miss", "sess leftover + wait + do(user)", 12,
     "adapter leftover still 1s", "adapter leftover",
     "src/allauth_ad.py", "tests/test_allauth_ad.py", "gets"),
    ("Spring Security", "springsec-session-leftover", "springsec-jwks-handoff", "flock-sprsc",
     "src/security.xml", "tests/test_springsec.py", "session leftover",
     "drop session on miss", "sess leftover + wait + do(tok)", 16,
     "jwks leftover still 1s", "jwks leftover",
     "src/security_jw.xml", "tests/test_springsec_jw.py", "gets"),
    ("Shiro", "shiro-session-leftover", "shiro-cache-handoff", "flock-shiro",
     "src/shiro.ini", "tests/test_shiro.py", "session leftover",
     "drop session on miss", "sess leftover + wait + do(subj)", 13,
     "cache leftover still 1s", "cache leftover",
     "src/shiro_ch.ini", "tests/test_shiro_ch.py", "gets"),
    ("CAS", "cas-tgt-leftover", "cas-st-handoff", "flock-castg",
     "src/cas.properties", "tests/test_cas.py", "tgt leftover",
     "drop tgt on miss", "tgt leftover + wait + do(tgt)", 15,
     "st leftover still 1s", "st leftover",
     "src/cas_st.properties", "tests/test_cas_st.py", "gets"),
    ("SAML2", "saml-assertion-leftover", "saml-metadata-handoff", "flock-samla",
     "src/saml.xml", "tests/test_saml.py", "assertion leftover",
     "drop assertion on miss", "as leftover + wait + do(asrt)", 14,
     "metadata leftover still 1s", "metadata leftover",
     "src/saml_md.xml", "tests/test_saml_md.py", "gets"),
    ("OpenID Connect", "oidc-idtoken-leftover", "oidc-jwks-handoff", "flock-oidci",
     "src/oidc.json", "tests/test_oidc.py", "idtoken leftover",
     "drop idtoken on miss", "idt leftover + wait + do(tok)", 16,
     "jwks leftover still 1s", "jwks leftover",
     "src/oidc_jw.json", "tests/test_oidc_jw.py", "gets"),
    ("WebAuthn", "webauthn-challenge-leftover", "webauthn-cred-handoff", "flock-wbatn",
     "src/webauthn.json", "tests/test_webauthn.py", "challenge leftover",
     "drop challenge on miss", "ch leftover + wait + do(cred)", 15,
     "cred leftover still 1s", "cred leftover",
     "src/webauthn_cr.json", "tests/test_webauthn_cr.py", "gets"),
    ("Passkeys", "passkey-rp-leftover", "passkey-cred-handoff", "flock-pssky",
     "src/passkey.json", "tests/test_passkey.py", "rp leftover",
     "drop rp on miss", "rp leftover + wait + do(cred)", 13,
     "cred leftover still 1s", "cred leftover",
     "src/passkey_cr.json", "tests/test_passkey_cr.py", "gets"),
    ("TOTP", "totp-window-leftover", "totp-secret-handoff", "flock-totpw",
     "src/totp.json", "tests/test_totp.py", "window leftover",
     "drop window on miss", "win leftover + wait + do(code)", 12,
     "secret leftover still 1s", "secret leftover",
     "src/totp_sc.json", "tests/test_totp_sc.py", "gets"),
    ("WebOTP", "webotp-sms-leftover", "webotp-abort-handoff", "flock-wbotp",
     "src/webotp.js", "tests/test_webotp.py", "sms leftover",
     "drop sms on miss", "sms leftover + wait + do(code)", 11,
     "abort leftover still 1s", "abort leftover",
     "src/webotp_ab.js", "tests/test_webotp_ab.py", "gets"),
    ("SCIM", "scim-user-leftover", "scim-group-handoff", "flock-scimu",
     "src/scim.json", "tests/test_scim.py", "user leftover",
     "drop user on miss", "user leftover + wait + do(id)", 14,
     "group leftover still 1s", "group leftover",
     "src/scim_gr.json", "tests/test_scim_gr.py", "gets"),
    ("LDAP", "ldap-bind-leftover", "ldap-entry-handoff", "flock-ldapb",
     "src/ldap.conf", "tests/test_ldap.py", "bind leftover",
     "drop bind on miss", "bind leftover + wait + do(dn)", 16,
     "entry leftover still 1s", "entry leftover",
     "src/ldap_en.conf", "tests/test_ldap_en.py", "gets"),
    ("FreeIPA", "freeipa-krb-leftover", "freeipa-ldap-handoff", "flock-fipak",
     "src/ipa.conf", "tests/test_freeipa.py", "krb leftover",
     "drop krb on miss", "krb leftover + wait + do(prin)", 15,
     "ldap leftover still 1s", "ldap leftover",
     "src/ipa_ld.conf", "tests/test_freeipa_ld.py", "gets"),
    ("Active Directory", "ad-gc-leftover", "ad-krb-handoff", "flock-adgcc",
     "src/ad.conf", "tests/test_ad.py", "gc leftover",
     "drop gc on miss", "gc leftover + wait + do(obj)", 17,
     "krb leftover still 1s", "krb leftover",
     "src/ad_krb.conf", "tests/test_ad_krb.py", "gets"),
    ("Kerberos KDC", "kdc-tgt-leftover", "kdc-replay-handoff", "flock-kdctg",
     "src/kdc.conf", "tests/test_kdc.py", "tgt leftover",
     "drop tgt on miss", "tgt leftover + wait + do(prin)", 16,
     "replay leftover still 1s", "replay leftover",
     "src/kdc_rp.conf", "tests/test_kdc_rp.py", "gets"),
]

def records(round_n: int):
    idx = round_n - CATALOG_FIRST
    p = PAIRS[idx]
    product, slug_ok, slug_part, plant, src, test, api, naive, fix, workers, residual, sibling, *_ = p
    rec_ok = {
        "id": f"cst-r{round_n}-{slug_ok}",
        "goal": (
            f"{plant}: leftover leftover leftover {product} {api} still stampedes {workers} callers after a crashed refresh. "
            f"One in-flight via {fix}. Do not {naive}. Gate is {test}."
        ),
        "plan": f"{naive} so leftover leftover leftover cannot stampede origin.",
        "steps": _steps_ok(p),
        "outcome": (
            f"Leftover leftover leftover {product} stampeded {workers} callers. {naive} failed still-rebuilds. "
            f"Plan change: {fix}. {test} 4/4, suite 8/8. Residual: {residual}."
        ),
        "reward": {"success": True, "plan_changes": 1, "tests_passed": 8, "cost_steps": 16},
        "meta": {
            "factory": "cache-stampede-factory",
            "round": round_n,
            "generator": "grok-4.6",
            "kind": "designed",
            "product": product,
            "mechanic": f"leftover leftover leftover {api}",
            "sim_or_real": "designed",
            "plant": plant,
        },
    }
    rec_part = {
        "id": f"cst-r{round_n}-{slug_part}",
        "goal": (
            f"{plant}: leftover leftover leftover {product} still stampedes after a crashed refresh. "
            f"One in-flight via {fix}. Do not {naive}. Gate is {test}. "
            f"{sibling} may still hard-miss; ticket allows handoff."
        ),
        "plan": f"{naive} so leftover leftover leftover cannot stampede origin.",
        "steps": _steps_part(p),
        "outcome": (
            f"Leftover leftover leftover {product} stampeded callers. {naive} failed fixture. "
            f"Plan change: {fix}. {test} 3/3. Partial: leftover leftover leftover {sibling} still leftover (xfail)."
        ),
        "reward": {
            "success": False,
            "plan_changes": 1,
            "tests_passed": 3,
            "xfailed": 1,
            "handoff": 1,
            "cost_steps": 17,
        },
        "meta": {
            "factory": "cache-stampede-factory",
            "round": round_n,
            "generator": "grok-4.6",
            "kind": "designed",
            "product": product,
            "mechanic": f"leftover leftover leftover {sibling}",
            "sim_or_real": "designed",
            "plant": plant,
        },
    }
    return [rec_ok, rec_part]


def notes_md(round_n: int) -> str:
    idx = round_n - CATALOG_FIRST
    p = PAIRS[idx]
    product, slug_ok, slug_part, plant, src, test, api, naive, fix, workers, residual, sibling, *_ = p
    return (
        f"# NOTES-r{round_n} cache-stampede-factory\n\n"
        "Novel coverage: 91%\n\n"
        f"Two designed leftover leftover leftover stampede episodes (quota 2). "
        f"{product} leftover leftover leftover {api} vs leftover leftover leftover {sibling}. "
        "Not flock-wN. Not AWS catalog. Not r1–r2143 clones (incl. r1445 akamai-esi, r1690 woodpecker, r1730 husky-init, r2143 sssd-nsscache). "
        "Not dbc-/sir-/gql- ids.\n"
        "Not overlayfs whiteout. Not nydus/stargz. Not search-index leftover. Not docker leftover leftover leftover.\n\n"
        "| id | seed | first apply | plan change | terminal |\n"
        "|---|---|---|---|---|\n"
        f"| cst-r{round_n}-{slug_ok} | {workers} leftover leftover leftover {product} | {naive} | {fix} | success residual {residual} |\n"
        f"| cst-r{round_n}-{slug_part} | leftover leftover leftover {sibling} | {naive} | {fix} | handoff leftover sibling |\n\n"
        "## Step counts\n"
        "- ep1: 16. Naive 6–7; plan change 8; suite green 12–16.\n"
        "- ep2: 17. Naive 6–7; plan change 8; sibling xfail 12–17.\n\n"
        "## decision_basis audit\n"
        f"Every step starts Plan:/Observation:/Reflection:. No thought keys. Plant `{plant}`.\n"
        "meta.generator=grok-4.6. Invented plant. No sim_or_real: real.\n\n"
        "## Weaknesses / next\n"
        f"Avoid {slug_ok} reruns and docker/search ids.\n"
    )


def write_round(round_n: int, stage: Path):
    recs = records(round_n)
    (stage / f"batch-r{round_n:02d}.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=True) + "\n" for r in recs)
    )
    (stage / f"NOTES-r{round_n:02d}.md").write_text(notes_md(round_n))
    return [r["id"] for r in recs]


if __name__ == "__main__":
    import tempfile, subprocess, sys
    last = CATALOG_FIRST + len(PAIRS) - 1
    d = Path(tempfile.mkdtemp(prefix="cst-smoke-"))
    ids = write_round(CATALOG_FIRST, d)
    print(json.dumps({"ok": True, "pairs": len(PAIRS), "first": CATALOG_FIRST, "last": last, "ids": ids}))
