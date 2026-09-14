#!/usr/bin/env python3
"""NTP unique leftover leftover leftover leftover mill wave 27: NEW dest plants. BAN dnsmasq leftover clones."""
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
    s_from(0, "openssl-cnf-leftover-as-dest", "oscf", "openssl cnf leftover", "openssl.cnf.bak", "openssl cnf leftover", "openssl leftover && ls openssl.cnf.bak", "not openssl-cnf leftover; openssl cnf leftover is not dest", "treat leftover openssl cnf as dest then CLI parquet.", "openssl leftover; # openssl.cnf.bak claimed dest", "openssl leftover|openssl.cnf.bak"),
    s_from(1, "certbot-renewal-leftover-as-dest", "cbrn", "certbot renewal leftover", "renewal/folio.conf", "certbot renewal leftover", "certbot leftover && ls renewal/folio.conf", "not certbot-renewal leftover; certbot renewal leftover is not dest", "treat leftover certbot renewal as dest then CLI parquet.", "certbot leftover; # renewal/folio.conf claimed dest", "certbot leftover|renewal/folio.conf"),
    s_from(2, "acme-account-leftover-as-dest", "acac", "acme account leftover", "acme/account.json", "acme account leftover", "acme leftover && ls acme/account.json", "not acme-account leftover; acme account leftover is not dest", "treat leftover acme account as dest then CLI parquet.", "acme leftover; # acme/account.json claimed dest", "acme leftover|acme/account.json"),
    s_from(3, "mkcert-root-leftover-as-dest", "mkrt", "mkcert root leftover", "rootCA.pem", "mkcert root leftover", "mkcert leftover && ls rootCA.pem", "not mkcert-root leftover; mkcert root leftover is not dest", "treat leftover mkcert root as dest then CLI parquet.", "mkcert leftover; # rootCA.pem claimed dest", "mkcert leftover|rootCA.pem"),
    s_from(4, "stepca-db-leftover-as-dest", "stcdb", "stepca db leftover", "step/db", "stepca db leftover", "stepca leftover && ls step/db", "not stepca-db leftover; stepca db leftover is not dest", "treat leftover stepca db as dest then CLI parquet.", "stepca leftover; # step/db claimed dest", "stepca leftover|step/db"),
    s_from(5, "vaultpki-role-leftover-as-dest", "vpro", "vaultpki role leftover", "pki/role.json", "vaultpki role leftover", "vaultpki leftover && ls pki/role.json", "not vaultpki-role leftover; vaultpki role leftover is not dest", "treat leftover vaultpki role as dest then CLI parquet.", "vaultpki leftover; # pki/role.json claimed dest", "vaultpki leftover|pki/role.json"),
    s_from(6, "cfssl-csr-leftover-as-dest", "cfcsr", "cfssl csr leftover", "csr.json.bak", "cfssl csr leftover", "cfssl leftover && ls csr.json.bak", "not cfssl-csr leftover; cfssl csr leftover is not dest", "treat leftover cfssl csr as dest then CLI parquet.", "cfssl leftover; # csr.json.bak claimed dest", "cfssl leftover|csr.json.bak"),
    s_from(7, "easyrsa-pki-leftover-as-dest", "ezpki", "easyrsa pki leftover", "pki/index.txt", "easyrsa pki leftover", "easyrsa leftover && ls pki/index.txt", "not easyrsa-pki leftover; easyrsa pki leftover is not dest", "treat leftover easyrsa pki as dest then CLI parquet.", "easyrsa leftover; # pki/index.txt claimed dest", "easyrsa leftover|pki/index.txt"),
    s_from(8, "minica-ca-leftover-as-dest", "mnca", "minica ca leftover", "minica.pem", "minica ca leftover", "minica leftover && ls minica.pem", "not minica-ca leftover; minica ca leftover is not dest", "treat leftover minica ca as dest then CLI parquet.", "minica leftover; # minica.pem claimed dest", "minica leftover|minica.pem"),
    s_from(9, "sshd-config-leftover-as-dest", "sscf2", "sshd config leftover", "sshd_config.bak", "sshd config leftover", "sshd leftover && ls sshd_config.bak", "not sshd-config leftover; sshd config leftover is not dest", "treat leftover sshd config as dest then CLI parquet.", "sshd leftover; # sshd_config.bak claimed dest", "sshd leftover|sshd_config.bak"),
    s_from(10, "ssh-knownhosts-leftover-as-dest", "sskh", "ssh knownhosts leftover", "known_hosts.bak", "ssh knownhosts leftover", "ssh leftover && ls known_hosts.bak", "not ssh-knownhosts leftover; ssh knownhosts leftover is not dest", "treat leftover ssh knownhosts as dest then CLI parquet.", "ssh leftover; # known_hosts.bak claimed dest", "ssh leftover|known_hosts.bak"),
    s_from(11, "gpg-homedir-leftover-as-dest", "gpgh", "gpg homedir leftover", ".gnupg", "gpg homedir leftover", "gpg leftover && ls .gnupg", "not gpg-homedir leftover; gpg homedir leftover is not dest", "treat leftover gpg homedir as dest then CLI parquet.", "gpg leftover; # .gnupg claimed dest", "gpg leftover|.gnupg"),
    s_from(12, "age-key-leftover-as-dest", "agky", "age key leftover", "age.key.bak", "age key leftover", "age leftover && ls age.key.bak", "not age-key leftover; age key leftover is not dest", "treat leftover age key as dest then CLI parquet.", "age leftover; # age.key.bak claimed dest", "age leftover|age.key.bak"),
    s_from(13, "sops-age-leftover-as-dest", "spac", "sops age leftover", ".sops.yaml.bak", "sops age leftover", "sops leftover && ls .sops.yaml.bak", "not sops-age leftover; sops age leftover is not dest", "treat leftover sops age as dest then CLI parquet.", "sops leftover; # .sops.yaml.bak claimed dest", "sops leftover|.sops.yaml.bak"),
    s_from(14, "pass-store-leftover-as-dest", "psst", "pass store leftover", ".password-store", "pass store leftover", "pass leftover && ls .password-store", "not pass-store leftover; pass store leftover is not dest", "treat leftover pass store as dest then CLI parquet.", "pass leftover; # .password-store claimed dest", "pass leftover|.password-store"),
    s_from(15, "bitwarden-json-leftover-as-dest", "bwjs", "bitwarden json leftover", "bitwarden.json", "bitwarden json leftover", "bitwarden leftover && ls bitwarden.json", "not bitwarden-json leftover; bitwarden json leftover is not dest", "treat leftover bitwarden json as dest then CLI parquet.", "bitwarden leftover; # bitwarden.json claimed dest", "bitwarden leftover|bitwarden.json"),
    s_from(16, "keepass-kdbx-leftover-as-dest", "kpkd", "keepass kdbx leftover", "folio.kdbx", "keepass kdbx leftover", "keepass leftover && ls folio.kdbx", "not keepass-kdbx leftover; keepass kdbx leftover is not dest", "treat leftover keepass kdbx as dest then CLI parquet.", "keepass leftover; # folio.kdbx claimed dest", "keepass leftover|folio.kdbx"),
    s_from(17, "lastpass-csv-leftover-as-dest", "lpcs", "lastpass csv leftover", "lastpass.csv", "lastpass csv leftover", "lastpass leftover && ls lastpass.csv", "not lastpass-csv leftover; lastpass csv leftover is not dest", "treat leftover lastpass csv as dest then CLI parquet.", "lastpass leftover; # lastpass.csv claimed dest", "lastpass leftover|lastpass.csv"),
    s_from(18, "1password-json-leftover-as-dest", "opjs", "1password json leftover", "1password.json", "1password json leftover", "1password leftover && ls 1password.json", "not 1password-json leftover; 1password json leftover is not dest", "treat leftover 1password json as dest then CLI parquet.", "1password leftover; # 1password.json claimed dest", "1password leftover|1password.json"),
    s_from(19, "keybase-config-leftover-as-dest", "kbcf", "keybase config leftover", ".config/keybase", "keybase config leftover", "keybase leftover && ls .config/keybase", "not keybase-config leftover; keybase config leftover is not dest", "treat leftover keybase config as dest then CLI parquet.", "keybase leftover; # .config/keybase claimed dest", "keybase leftover|.config/keybase"),
    s_from(20, "gpg-agent-leftover-as-dest", "gpag", "gpg agent leftover", "gpg-agent.conf.bak", "gpg agent leftover", "gpg leftover && ls gpg-agent.conf.bak", "not gpg-agent leftover; gpg agent leftover is not dest", "treat leftover gpg agent as dest then CLI parquet.", "gpg leftover; # gpg-agent.conf.bak claimed dest", "gpg leftover|gpg-agent.conf.bak"),
    s_from(21, "ssh-agent-env-leftover-as-dest", "saen", "ssh agent env leftover", "ssh-agent.env", "ssh agent env leftover", "ssh leftover && ls ssh-agent.env", "not ssh-agent-env leftover; ssh agent env leftover is not dest", "treat leftover ssh agent env as dest then CLI parquet.", "ssh leftover; # ssh-agent.env claimed dest", "ssh leftover|ssh-agent.env"),
    s_from(22, "openssl-rand-leftover-as-dest", "osrd", "openssl rand leftover", ".rnd", "openssl rand leftover", "openssl leftover && ls .rnd", "not openssl-rand leftover; openssl rand leftover is not dest", "treat leftover openssl rand as dest then CLI parquet.", "openssl leftover; # .rnd claimed dest", "openssl leftover|.rnd"),
    s_from(23, "pkcs11-conf-leftover-as-dest", "pk11", "pkcs11 conf leftover", "pkcs11.conf.bak", "pkcs11 conf leftover", "pkcs11 leftover && ls pkcs11.conf.bak", "not pkcs11-conf leftover; pkcs11 conf leftover is not dest", "treat leftover pkcs11 conf as dest then CLI parquet.", "pkcs11 leftover; # pkcs11.conf.bak claimed dest", "pkcs11 leftover|pkcs11.conf.bak"),
    s_from(24, "tpm2-ctx-leftover-as-dest", "tmct", "tpm2 ctx leftover", "tpm2.ctx", "tpm2 ctx leftover", "tpm2 leftover && ls tpm2.ctx", "not tpm2-ctx leftover; tpm2 ctx leftover is not dest", "treat leftover tpm2 ctx as dest then CLI parquet.", "tpm2 leftover; # tpm2.ctx claimed dest", "tpm2 leftover|tpm2.ctx"),
    s_from(25, "yubikey-piv-leftover-as-dest", "ykpv", "yubikey piv leftover", "yubikey.piv", "yubikey piv leftover", "yubikey leftover && ls yubikey.piv", "not yubikey-piv leftover; yubikey piv leftover is not dest", "treat leftover yubikey piv as dest then CLI parquet.", "yubikey leftover; # yubikey.piv claimed dest", "yubikey leftover|yubikey.piv"),
    s_from(26, "softhsm-tokens-leftover-as-dest", "shtm", "softhsm tokens leftover", "softhsm2/tokens", "softhsm tokens leftover", "softhsm leftover && ls softhsm2/tokens", "not softhsm-tokens leftover; softhsm tokens leftover is not dest", "treat leftover softhsm tokens as dest then CLI parquet.", "softhsm leftover; # softhsm2/tokens claimed dest", "softhsm leftover|softhsm2/tokens"),
    s_from(27, "hsm-slot-leftover-as-dest", "hsms", "hsm slot leftover", "hsm.slot", "hsm slot leftover", "hsm leftover && ls hsm.slot", "not hsm-slot leftover; hsm slot leftover is not dest", "treat leftover hsm slot as dest then CLI parquet.", "hsm leftover; # hsm.slot claimed dest", "hsm leftover|hsm.slot"),
    s_from(28, "kms-cache-leftover-as-dest", "kmch", "kms cache leftover", ".kms/cache", "kms cache leftover", "kms leftover && ls .kms/cache", "not kms-cache leftover; kms cache leftover is not dest", "treat leftover kms cache as dest then CLI parquet.", "kms leftover; # .kms/cache claimed dest", "kms leftover|.kms/cache"),
    s_from(29, "sealed-secrets-leftover-as-dest", "slsc", "sealed secrets leftover", "sealed-secrets.json", "sealed secrets leftover", "sealed leftover && ls sealed-secrets.json", "not sealed-secrets leftover; sealed secrets leftover is not dest", "treat leftover sealed secrets as dest then CLI parquet.", "sealed leftover; # sealed-secrets.json claimed dest", "sealed leftover|sealed-secrets.json"),
    s_from(30, "external-secrets-leftover-as-dest", "exsc", "external secrets leftover", "external-secrets.json", "external secrets leftover", "external leftover && ls external-secrets.json", "not external-secrets leftover; external secrets leftover is not dest", "treat leftover external secrets as dest then CLI parquet.", "external leftover; # external-secrets.json claimed dest", "external leftover|external-secrets.json"),
    s_from(31, "certmanager-order-leftover-as-dest", "cmor", "certmanager order leftover", "cert-manager/order.json", "certmanager order leftover", "certmanager leftover && ls cert-manager/order.json", "not certmanager-order leftover; certmanager order leftover is not dest", "treat leftover certmanager order as dest then CLI parquet.", "certmanager leftover; # cert-manager/order.json claimed dest", "certmanager leftover|cert-manager/order.json"),
]

LEFTOVER = [
    l_from(0, "openssl-index-leftover-handoff", "osix", "index.txt", "openssl index leftover", "openssl index leftover", "not openssl cnf leftover; leftover openssl index as dest", "ship leftover openssl index as dest.", "openssl index leftover; # index.txt on disk", "openssl leftover|index.txt"),
    l_from(1, "certbot-live-leftover-handoff", "cblv", "live/folio/fullchain.pem", "certbot live leftover", "certbot live leftover", "not certbot renewal leftover; leftover certbot live as dest", "ship leftover certbot live as dest.", "certbot live leftover; # live/folio/fullchain.pem on disk", "certbot leftover|live/folio/fullchain.pem"),
    l_from(2, "acme-orders-leftover-handoff", "acor", "acme/orders.json", "acme orders leftover", "acme orders leftover", "not acme account leftover; leftover acme orders as dest", "ship leftover acme orders as dest.", "acme orders leftover; # acme/orders.json on disk", "acme leftover|acme/orders.json"),
    l_from(3, "mkcert-key-leftover-handoff", "mkky", "rootCA-key.pem", "mkcert key leftover", "mkcert key leftover", "not mkcert root leftover; leftover mkcert key as dest", "ship leftover mkcert key as dest.", "mkcert key leftover; # rootCA-key.pem on disk", "mkcert leftover|rootCA-key.pem"),
    l_from(4, "stepca-certs-leftover-handoff", "stcc", "step/certs", "stepca certs leftover", "stepca certs leftover", "not stepca db leftover; leftover stepca certs as dest", "ship leftover stepca certs as dest.", "stepca certs leftover; # step/certs on disk", "stepca leftover|step/certs"),
    l_from(5, "vaultpki-cert-leftover-handoff", "vpct", "pki/cert.json", "vaultpki cert leftover", "vaultpki cert leftover", "not vaultpki role leftover; leftover vaultpki cert as dest", "ship leftover vaultpki cert as dest.", "vaultpki cert leftover; # pki/cert.json on disk", "vaultpki leftover|pki/cert.json"),
    l_from(6, "cfssl-ca-leftover-handoff", "cfca", "ca.pem", "cfssl ca leftover", "cfssl ca leftover", "not cfssl csr leftover; leftover cfssl ca as dest", "ship leftover cfssl ca as dest.", "cfssl ca leftover; # ca.pem on disk", "cfssl leftover|ca.pem"),
    l_from(7, "easyrsa-serial-leftover-handoff", "ezsr", "pki/serial", "easyrsa serial leftover", "easyrsa serial leftover", "not easyrsa pki leftover; leftover easyrsa serial as dest", "ship leftover easyrsa serial as dest.", "easyrsa serial leftover; # pki/serial on disk", "easyrsa leftover|pki/serial"),
    l_from(8, "minica-key-leftover-handoff", "mnky", "minica-key.pem", "minica key leftover", "minica key leftover", "not minica ca leftover; leftover minica key as dest", "ship leftover minica key as dest.", "minica key leftover; # minica-key.pem on disk", "minica leftover|minica-key.pem"),
    l_from(9, "sshd-keys-leftover-handoff", "ssky", "ssh_host_ed25519_key", "sshd keys leftover", "sshd keys leftover", "not sshd config leftover; leftover sshd keys as dest", "ship leftover sshd keys as dest.", "sshd keys leftover; # ssh_host_ed25519_key on disk", "sshd leftover|ssh_host_ed25519_key"),
    l_from(10, "ssh-config-leftover-handoff", "sscf3", "config.bak", "ssh config leftover", "ssh config leftover", "not ssh knownhosts leftover; leftover ssh config as dest", "ship leftover ssh config as dest.", "ssh config leftover; # config.bak on disk", "ssh leftover|config.bak"),
    l_from(11, "gpg-pubring-leftover-handoff", "gpgr", "pubring.kbx", "gpg pubring leftover", "gpg pubring leftover", "not gpg homedir leftover; leftover gpg pubring as dest", "ship leftover gpg pubring as dest.", "gpg pubring leftover; # pubring.kbx on disk", "gpg leftover|pubring.kbx"),
    l_from(12, "age-recipients-leftover-handoff", "agrc", "recipients.txt", "age recipients leftover", "age recipients leftover", "not age key leftover; leftover age recipients as dest", "ship leftover age recipients as dest.", "age recipients leftover; # recipients.txt on disk", "age leftover|recipients.txt"),
    l_from(13, "sops-mac-leftover-handoff", "spmc", ".sops.mac", "sops mac leftover", "sops mac leftover", "not sops age leftover; leftover sops mac as dest", "ship leftover sops mac as dest.", "sops mac leftover; # .sops.mac on disk", "sops leftover|.sops.mac"),
    l_from(14, "pass-gpg-id-leftover-handoff", "psgi", ".password-store/.gpg-id", "pass gpg-id leftover", "pass gpg-id leftover", "not pass store leftover; leftover pass gpg-id as dest", "ship leftover pass gpg-id as dest.", "pass gpg-id leftover; # .password-store/.gpg-id on disk", "pass leftover|.password-store/.gpg-id"),
    l_from(15, "bitwarden-attachments-leftover-handoff", "bwat", "bitwarden-attachments", "bitwarden attachments leftover", "bitwarden attachments leftover", "not bitwarden json leftover; leftover bitwarden attachments as dest", "ship leftover bitwarden attachments as dest.", "bitwarden attachments leftover; # bitwarden-attachments on disk", "bitwarden leftover|bitwarden-attachments"),
    l_from(16, "keepass-keyfile-leftover-handoff", "kpkf", "folio.key", "keepass keyfile leftover", "keepass keyfile leftover", "not keepass kdbx leftover; leftover keepass keyfile as dest", "ship leftover keepass keyfile as dest.", "keepass keyfile leftover; # folio.key on disk", "keepass leftover|folio.key"),
    l_from(17, "lastpass-log-leftover-handoff", "lplg", "lastpass.log", "lastpass log leftover", "lastpass log leftover", "not lastpass csv leftover; leftover lastpass log as dest", "ship leftover lastpass log as dest.", "lastpass log leftover; # lastpass.log on disk", "lastpass leftover|lastpass.log"),
    l_from(18, "1password-log-leftover-handoff", "oplg", "1password.log", "1password log leftover", "1password log leftover", "not 1password json leftover; leftover 1password log as dest", "ship leftover 1password log as dest.", "1password log leftover; # 1password.log on disk", "1password leftover|1password.log"),
    l_from(19, "keybase-log-leftover-handoff", "kblg2", "keybase.log", "keybase log leftover", "keybase log leftover", "not keybase config leftover; leftover keybase log as dest", "ship leftover keybase log as dest.", "keybase log leftover; # keybase.log on disk", "keybase leftover|keybase.log"),
    l_from(20, "gpg-socket-leftover-handoff", "gpgs", "S.gpg-agent", "gpg socket leftover", "gpg socket leftover", "not gpg agent leftover; leftover gpg socket as dest", "ship leftover gpg socket as dest.", "gpg socket leftover; # S.gpg-agent on disk", "gpg leftover|S.gpg-agent"),
    l_from(21, "ssh-agent-sock-leftover-handoff", "sask", "ssh-agent.sock", "ssh agent sock leftover", "ssh agent sock leftover", "not ssh agent env leftover; leftover ssh agent sock as dest", "ship leftover ssh agent sock as dest.", "ssh agent sock leftover; # ssh-agent.sock on disk", "ssh leftover|ssh-agent.sock"),
    l_from(22, "openssl-serial-leftover-handoff", "ossr", "serial", "openssl serial leftover", "openssl serial leftover", "not openssl rand leftover; leftover openssl serial as dest", "ship leftover openssl serial as dest.", "openssl serial leftover; # serial on disk", "openssl leftover|serial"),
    l_from(23, "pkcs11-log-leftover-handoff", "pk11l", "pkcs11.log", "pkcs11 log leftover", "pkcs11 log leftover", "not pkcs11 conf leftover; leftover pkcs11 log as dest", "ship leftover pkcs11 log as dest.", "pkcs11 log leftover; # pkcs11.log on disk", "pkcs11 leftover|pkcs11.log"),
    l_from(24, "tpm2-pub-leftover-handoff", "tmpb", "tpm2.pub", "tpm2 pub leftover", "tpm2 pub leftover", "not tpm2 ctx leftover; leftover tpm2 pub as dest", "ship leftover tpm2 pub as dest.", "tpm2 pub leftover; # tpm2.pub on disk", "tpm2 leftover|tpm2.pub"),
    l_from(25, "yubikey-log-leftover-handoff", "yklg", "yubikey.log", "yubikey log leftover", "yubikey log leftover", "not yubikey piv leftover; leftover yubikey log as dest", "ship leftover yubikey log as dest.", "yubikey log leftover; # yubikey.log on disk", "yubikey leftover|yubikey.log"),
    l_from(26, "softhsm-conf-leftover-handoff", "shcf", "softhsm2.conf.bak", "softhsm conf leftover", "softhsm conf leftover", "not softhsm tokens leftover; leftover softhsm conf as dest", "ship leftover softhsm conf as dest.", "softhsm conf leftover; # softhsm2.conf.bak on disk", "softhsm leftover|softhsm2.conf.bak"),
    l_from(27, "hsm-log-leftover-handoff", "hsml", "hsm.log", "hsm log leftover", "hsm log leftover", "not hsm slot leftover; leftover hsm log as dest", "ship leftover hsm log as dest.", "hsm log leftover; # hsm.log on disk", "hsm leftover|hsm.log"),
    l_from(28, "kms-log-leftover-handoff", "kmlg", ".kms/log", "kms log leftover", "kms log leftover", "not kms cache leftover; leftover kms log as dest", "ship leftover kms log as dest.", "kms log leftover; # .kms/log on disk", "kms leftover|.kms/log"),
    l_from(29, "sealed-secrets-key-leftover-handoff", "slky", "sealed-secrets.key", "sealed secrets key leftover", "sealed secrets key leftover", "not sealed secrets leftover; leftover sealed secrets key as dest", "ship leftover sealed secrets key as dest.", "sealed secrets key leftover; # sealed-secrets.key on disk", "sealed leftover|sealed-secrets.key"),
    l_from(30, "external-secrets-store-leftover-handoff", "exss", "secretstore.yaml", "external secrets store leftover", "external secrets store leftover", "not external secrets leftover; leftover external secrets store as dest", "ship leftover external secrets store as dest.", "external secrets store leftover; # secretstore.yaml on disk", "external leftover|secretstore.yaml"),
    l_from(31, "certmanager-cert-leftover-handoff", "cmct", "cert-manager/cert.json", "certmanager cert leftover", "certmanager cert leftover", "not certmanager order leftover; leftover certmanager cert as dest", "ship leftover certmanager cert as dest.", "certmanager cert leftover; # cert-manager/cert.json on disk", "certmanager leftover|cert-manager/cert.json"),
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
        print("usage: ntp-mill-unique-llll27.py ROUND STAGING_DIR", file=sys.stderr)
        return 2
    round_n = int(argv[0])
    staging = Path(argv[1])
    staging.mkdir(parents=True, exist_ok=True)
    i1, i2 = write_stage(staging, round_n)
    print(f"wrote r{round_n} {i1} {i2}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
