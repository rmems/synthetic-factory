#!/usr/bin/env python3
"""Mill docker-build-cache-factory r933+. Crypto/PKI × GPIO/PWM leftovers.

NEW unique-pair catalog after r885 speech/HWMON.
BAN r789 cxi/nfc-digital, r790 NGS, r837 astronomy/DVB, r885 speech/HWMON,
r645 nerdctl, r549 scsh/scsi, GNU Prolog/landlock/SWI pack/seccomp/AppArmor/
GOTOOLCHAIN, harbor-pin, leftover×sysctl. 17+18 steps. meta.generator=grok-4.6.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("dbc_mill_r885", HERE / "dbc-mill-r885.py")
_m = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_m)

FACTORY = _m.FACTORY
GEN = _m.GEN
lang = _m.lang
leftover = _m.leftover
success_episode = _m.success_episode
leftover_episode = _m.leftover_episode
notes_for = _m.notes_for
slug_taken = _m.slug_taken
BANNED_NEEDLES = _m.BANNED_NEEDLES + (
    "sphinxbase-cache",
    "coretemp-leftover",
    "casacore-measures",
    "dvb-usb-leftover",
    "samtools-htslib",
    "slcan-leftover",
)

# slug, env, tool, old, new, artifact, mb
_CRYPTO = [
    ("botan-cache", "BOTAN_HOME", "botan", "3.4.0", "3.6.1", "include/botan-3/botan/auto_rng.h", "8MB"),
    ("wolfssl-cache", "WOLFSSL_HOME", "wolfssl-config", "5.7.0", "5.7.4", "include/wolfssl/ssl.h", "6MB"),
    ("mbedtls-cache", "MBEDTLS_HOME", "mbedtls_test", "3.6.0", "3.6.2", "include/mbedtls/ssl.h", "5MB"),
    ("libsodium-cache", "SODIUM_HOME", "sodium", "1.0.19", "1.0.20", "include/sodium.h", "2MB"),
    ("libgcrypt-cache", "LIBGCRYPT_CONFIG", "libgcrypt-config", "1.10.3", "1.11.0", "include/gcrypt.h", "3MB"),
    ("nettle-cache", "NETTLE_HOME", "nettle-hash", "3.9.1", "3.10.1", "include/nettle/sha2.h", "2MB"),
    ("cryptopp-cache", "CRYPTOPP_HOME", "cryptest", "8.9.0", "8.9.0-post", "include/cryptopp/sha.h", "7MB"),
    ("libressl-engine-cache", "LIBRESSL_HOME", "openssl", "3.9.2", "4.0.0", "lib/engines-3/padlock.so", "4MB"),
    ("gnutls-cache", "GNUTLS_SYSTEM_PRIORITY_FILE", "gnutls-cli", "3.8.5", "3.8.8", "share/gnutls/p11-kit.config", "5MB"),
    ("nss-softokn-cache", "NSS_LIBDIR", "certutil", "3.101", "3.107", "lib/nss/libsoftokn3.so", "6MB"),
    ("argon2-cache", "ARGON2_HOME", "argon2", "20190702", "20190702-post", "include/argon2.h", "1MB"),
    ("age-key-cache", "AGE_HOME", "age", "1.1.1", "1.2.1", "share/age/age.1", "2MB"),
    ("minisign-cache", "MINISIGN_HOME", "minisign", "0.11", "0.12", "share/minisign/minisign.1", "1MB"),
    ("signify-openbsd-cache", "SIGNIFY_HOME", "signify", "31", "32", "share/signify/signify.1", "1MB"),
    ("tpm2-tss-cache", "TSS2_FAPI_PROFILE", "tss2", "4.1.3", "4.1.3-post", "include/tss2/tss2_esys.h", "4MB"),
    ("tpm2-tools-cache", "TPM2TOOLS_TCTI", "tpm2", "5.6", "5.7", "share/tpm2-tools/tpm2_create.1", "3MB"),
    ("softhsm-cache", "SOFTHSM2_CONF", "softhsm2-util", "2.6.1", "2.6.1-post", "share/softhsm/softhsm2.conf", "3MB"),
    ("opensc-cache", "OPENSC_CONF", "pkcs15-tool", "0.25.1", "0.26.1", "share/opensc/opensc.conf", "4MB"),
    ("pcsc-lite-cache", "PCSCLITE_CSOCK_NAME", "pcscd", "2.2.3", "2.3.0", "share/pcsc/drivers", "2MB"),
    ("ccid-cache", "CCID_HOME", "ifdhandler", "1.5.5", "1.6.1", "lib/pcsc/drivers/ifd-ccid.bundle", "2MB"),
    ("gnupg-scd-cache", "GNUPGHOME", "gpg-agent", "2.4.5", "2.4.7", "libexec/scdaemon", "3MB"),
    ("libp11-cache", "PKCS11_MODULE_PATH", "pkcs11-tool", "0.4.12", "0.4.13", "lib/engines-3/pkcs11.so", "2MB"),
    ("yubihsm-cache", "YUBIHSM_CONNECTOR", "yubihsm-shell", "2.4.2", "2.6.0", "lib/pkcs11/yubihsm_pkcs11.so", "3MB"),
    ("libyubikey-cache", "YUBIKEY_HOME", "ykinfo", "1.13.6", "1.13.7", "include/yubikey.h", "1MB"),
    ("pkcs11-helper-cache", "PKCS11H_HOME", "pkcs11-helper", "1.29.0", "1.30.0", "include/pkcs11-helper-1.0/pkcs11h-core.h", "2MB"),
    ("opencryptoki-cache", "OCK_CONFIG", "pkcsconf", "3.23.0", "3.24.0", "share/opencryptoki/opencryptoki.conf", "5MB"),
    ("trousers-cache", "TCS_HOME", "tcsd", "0.3.15", "0.3.15-post", "include/trousers/tss.h", "3MB"),
    ("libtpms-cache", "LIBTPMS_HOME", "tpms", "0.9.6", "0.10.0", "include/libtpms/tpm_library.h", "4MB"),
    ("swtpm-cache", "SWTPM_IOCTL", "swtpm", "0.8.2", "0.10.0", "share/swtpm/swtpm-localca.conf", "3MB"),
    ("veracrypt-cache", "VERACRYPT_HOME", "veracrypt", "1.26.7", "1.26.20", "share/veracrypt/veracrypt.1", "8MB"),
    ("encfs-cache", "ENCFS_HOME", "encfs", "1.9.5", "1.9.5-post", "share/encfs/encfs.1", "2MB"),
    ("cryfs-cache", "CRYFS_FRONTEND", "cryfs", "0.11.4", "1.0.1", "share/cryfs/cryfs.1", "3MB"),
    ("securefs-cache", "SECUREFS_HOME", "securefs", "1.0.0", "1.1.1", "share/securefs/securefs.1", "2MB"),
    ("gpgme-cache", "GPGME_HOME", "gpgme-tool", "1.23.2", "1.24.2", "include/gpgme.h", "3MB"),
    ("libassuan-cache", "ASSUAN_HOME", "libassuan-config", "2.5.7", "3.0.1", "include/assuan.h", "1MB"),
    ("npth-cache", "NPTH_HOME", "npth-config", "1.7", "1.8", "include/npth.h", "1MB"),
    ("libksba-cache", "KSBA_HOME", "ksba-config", "1.6.6", "1.6.7", "include/ksba.h", "2MB"),
    ("pinentry-cache", "PINENTRY_HOME", "pinentry", "1.2.1", "1.3.1", "share/pinentry/pinentry.1", "1MB"),
    ("paperkey-cache", "PAPERKEY_HOME", "paperkey", "1.6", "1.6-post", "share/paperkey/paperkey.1", "1MB"),
    ("ssss-cache", "SSSS_HOME", "ssss-split", "0.5.7", "0.5.7-post", "share/ssss/ssss.1", "1MB"),
    ("gfshare-cache", "GFSHARE_HOME", "gfsplit", "2.0.0", "2.0.0-post", "share/gfshare/gfsplit.1", "1MB"),
    ("tomb-cache", "TOMB_HOME", "tomb", "2.10", "2.11", "share/tomb/tomb.1", "2MB"),
    ("clevis-cache", "CLEVIS_HOME", "clevis", "19", "21", "share/clevis/pins/tpm2", "3MB"),
    ("tang-cache", "TANG_HOME", "tangd", "14", "15", "share/tang/tangd.1", "2MB"),
    ("jose-cache", "JOSE_HOME", "jose", "12", "14", "include/jose/jose.h", "2MB"),
    ("hashcash-token-cache", "HASHCASH_HOME", "hashcash", "1.22", "1.22-post", "share/hashcash/hashcash.1", "1MB"),
    ("scrypt-enc-cache", "SCRYPT_HOME", "scrypt", "1.3.2", "1.3.3", "share/scrypt/scrypt.1", "1MB"),
    ("rage-key-cache", "RAGE_HOME", "rage", "0.10.0", "0.11.1", "share/rage/rage.1", "2MB"),
]

# slug, token, leftover-arg, module, probe
_GPIO = [
    ("pca953x-leftover", "PCA953X_CLEAR", "pca953x gpio=cache", "gpio_pca953x", "ls /sys/class/gpio"),
    ("max732x-leftover", "MAX732X_CLEAR", "max732x gpio=cache", "gpio_max732x", "ls /sys/class/gpio"),
    ("dln2-gpio-leftover", "DLN2_GPIO_CLEAR", "dln2_gpio gpio=cache", "gpio_dln2", "ls /sys/class/gpio"),
    ("gpio-amd8111-leftover", "GPIO_AMD8111_CLEAR", "gpio_amd8111 gpio=cache", "gpio_amd8111", "ls /sys/class/gpio"),
    ("gpio-sch-leftover", "GPIO_SCH_CLEAR", "gpio_sch gpio=cache", "gpio_sch", "ls /sys/class/gpio"),
    ("gpio-lynxpoint-leftover", "GPIO_LYNXPOINT_CLEAR", "gpio_lynxpoint gpio=cache", "gpio_lynxpoint", "ls /sys/class/gpio"),
    ("gpio-crystalcove-leftover", "GPIO_CRYSTALCOVE_CLEAR", "gpio_crystalcove gpio=cache", "gpio_crystalcove", "ls /sys/class/gpio"),
    ("pwm-lpss-leftover", "PWM_LPSS_CLEAR", "pwm_lpss pwm=cache", "pwm_lpss", "ls /sys/class/pwm"),
    ("pwm-pca9685-leftover", "PWM_PCA9685_CLEAR", "pwm_pca9685 pwm=cache", "pwm_pca9685", "ls /sys/class/pwm"),
    ("leds-gpio-leftover", "LEDS_GPIO_CLEAR", "leds_gpio led=cache", "leds_gpio", "ls /sys/class/leds"),
    ("ledtrig-heartbeat-leftover", "LEDTRIG_HEARTBEAT_CLEAR", "ledtrig_heartbeat hz=cache", "ledtrig_heartbeat", "ls /sys/class/leds"),
    ("ledtrig-timer-leftover", "LEDTRIG_TIMER_CLEAR", "ledtrig_timer delay=cache", "ledtrig_timer", "ls /sys/class/leds"),
    ("gpio-keys-leftover", "GPIO_KEYS_CLEAR", "gpio_keys key=cache", "gpio_keys", "cat /proc/bus/input/devices | head"),
    ("gpio-mouse-leftover", "GPIO_MOUSE_CLEAR", "gpio_mouse scan=cache", "gpio_mouse", "cat /proc/bus/input/devices | head"),
    ("gpio-fan-leftover", "GPIO_FAN_CLEAR", "gpio_fan rpm=cache", "gpio_fan", "ls /sys/class/hwmon"),
    ("gpio-beeper-leftover", "GPIO_BEEPER_CLEAR", "gpio_beeper hz=cache", "gpio_beeper", "ls /sys/class/input"),
    ("gpio-restart-leftover", "GPIO_RESTART_CLEAR", "gpio_restart delay=cache", "gpio_restart", "ls /sys/class/gpio"),
    ("gpio-poweroff-leftover", "GPIO_POWEROFF_CLEAR", "gpio_poweroff timeout=cache", "gpio_poweroff", "ls /sys/class/gpio"),
    ("gpio-aggregator-leftover", "GPIO_AGGREGATOR_CLEAR", "gpio_aggregator line=cache", "gpio_aggregator", "ls /sys/class/gpio"),
    ("gpio-mockup-leftover", "GPIO_MOCKUP_CLEAR", "gpio_mockup ngpio=32", "gpio_mockup", "ls /sys/class/gpio"),
    ("gpio-sim-leftover", "GPIO_SIM_CLEAR", "gpio_sim banks=1", "gpio_sim", "ls /sys/class/gpio"),
    ("pca955x-leftover", "PCA955X_CLEAR", "pca955x led=cache", "leds_pca955x", "ls /sys/class/leds"),
    ("tca6416-leftover", "TCA6416_CLEAR", "tca6416 gpio=cache", "gpio_tca6416", "ls /sys/class/gpio"),
    ("mcp23s08-leftover", "MCP23S08_CLEAR", "mcp23s08 gpio=cache", "gpio_mcp23s08", "ls /sys/class/gpio"),
    ("mcp23017-leftover", "MCP23017_CLEAR", "mcp23017 gpio=cache", "gpio_mcp23s08", "ls /sys/class/gpio"),
    ("adp5588-leftover", "ADP5588_CLEAR", "adp5588 key=cache", "adp5588_keys", "cat /proc/bus/input/devices | head"),
    ("max7310-leftover", "MAX7310_CLEAR", "max7310 gpio=cache", "gpio_max732x", "ls /sys/class/gpio"),
    ("gpio-74x164-leftover", "GPIO_74X164_CLEAR", "gpio_74x164 gpio=cache", "gpio_74x164", "ls /sys/class/gpio"),
    ("gpio-mmio-leftover", "GPIO_MMIO_CLEAR", "gpio_generic gpio=cache", "gpio_generic", "ls /sys/class/gpio"),
    ("gpio-brcmstb-leftover", "GPIO_BRCMSTB_CLEAR", "gpio_brcmstb gpio=cache", "gpio_brcmstb", "ls /sys/class/gpio"),
    ("gpio-mxc-leftover", "GPIO_MXC_CLEAR", "gpio_mxc gpio=cache", "gpio_mxc", "ls /sys/class/gpio"),
    ("gpio-pl061-leftover", "GPIO_PL061_CLEAR", "gpio_pl061 gpio=cache", "gpio_pl061", "ls /sys/class/gpio"),
    ("gpio-dwapb-leftover", "GPIO_DWAPB_CLEAR", "gpio_dwapb gpio=cache", "gpio_dwapb", "ls /sys/class/gpio"),
    ("gpio-altera-leftover", "GPIO_ALTERA_CLEAR", "gpio_altera gpio=cache", "gpio_altera", "ls /sys/class/gpio"),
    ("gpio-xilinx-leftover", "GPIO_XILINX_CLEAR", "gpio_xilinx gpio=cache", "gpio_xilinx", "ls /sys/class/gpio"),
    ("gpio-zynq-leftover", "GPIO_ZYNQ_CLEAR", "gpio_zynq gpio=cache", "gpio_zynq", "ls /sys/class/gpio"),
    ("gpio-uniphier-leftover", "GPIO_UNIPHIER_CLEAR", "gpio_uniphier gpio=cache", "gpio_uniphier", "ls /sys/class/gpio"),
    ("gpio-rcar-leftover", "GPIO_RCAR_CLEAR", "gpio_rcar gpio=cache", "gpio_rcar", "ls /sys/class/gpio"),
    ("gpio-mvebu-leftover", "GPIO_MVEBU_CLEAR", "gpio_mvebu gpio=cache", "gpio_mvebu", "ls /sys/class/gpio"),
    ("gpio-aspeed-leftover", "GPIO_ASPEED_CLEAR", "gpio_aspeed gpio=cache", "gpio_aspeed", "ls /sys/class/gpio"),
    ("gpio-pca9570-leftover", "GPIO_PCA9570_CLEAR", "pca9570 gpio=cache", "gpio_pca9570", "ls /sys/class/gpio"),
    ("gpio-pcf857x-leftover", "GPIO_PCF857X_CLEAR", "pcf857x gpio=cache", "gpio_pcf857x", "ls /sys/class/gpio"),
    ("gpio-max730x-leftover", "GPIO_MAX730X_CLEAR", "max730x gpio=cache", "gpio_max730x", "ls /sys/class/gpio"),
    ("pwm-cros-ec-leftover", "PWM_CROS_EC_CLEAR", "pwm_cros_ec pwm=cache", "pwm_cros_ec", "ls /sys/class/pwm"),
    ("pwm-imx-leftover", "PWM_IMX_CLEAR", "pwm_imx27 pwm=cache", "pwm_imx27", "ls /sys/class/pwm"),
    ("pwm-rockchip-leftover", "PWM_ROCKCHIP_CLEAR", "pwm_rockchip pwm=cache", "pwm_rockchip", "ls /sys/class/pwm"),
    ("pwm-sunxi-leftover", "PWM_SUNXI_CLEAR", "pwm_sun4i pwm=cache", "pwm_sun4i", "ls /sys/class/pwm"),
    ("gpio-latch-leftover", "GPIO_LATCH_CLEAR", "gpio_latch line=cache", "gpio_latch", "ls /sys/class/gpio"),
]


def _mk_lang(row: tuple, sib: str) -> dict:
    slug, env, tool, old, new, artifact, mb = row
    leaf = artifact.rsplit("/", 1)[-1]
    parent = artifact.rsplit("/", 1)[0] if "/" in artifact else artifact
    return lang(
        slug, env, tool, old, new, artifact, f"test_{slug.split('-')[0]}.py", "src/demo.c",
        slug.split("-")[0][:8] + "-x",
        f"rm -rf /usr/{parent}" if not parent.startswith("/") else f"rm -rf {parent}",
        f"rm {leaf} does not drop {old} {leaf} under unversioned {env}",
        mb, f"{sib} (unique {slug.split('-')[0]} cache, not prior NGS/astro/speech catalogs)",
        f"{tool} --version", f"{tool} --version",
    )


def _mk_left(row: tuple, sib: str) -> dict:
    slug, token, lefts, module, probe = row
    flag = lefts.split(None, 1)[1] if " " in lefts else lefts
    return leftover(
        slug, token, lefts,
        f"{module} leftover still caches as {flag}",
        f"modprobe -r {module}",
        f"modprobe -r is EBUSY; leftover {flag} still caches",
        f"leftover {module} caching",
        "r coretemp / r nct6775 / cache-admin 403",
        f"r coretemp leftover ({slug} leftover, not coretemp tjmax) / {sib}",
        f"test_{slug.split('-')[0]}.py",
        f"ls /sys/module/{module}; {probe}",
        f"{slug.split('-')[0]} leftover {flag} leftover",
    )


assert len(_CRYPTO) == len(_GPIO) == 48
PAIRS = []
for i, (c, g) in enumerate(zip(_CRYPTO, _GPIO)):
    sib_c = _CRYPTO[(i + 1) % 48][0]
    sib_g = _GPIO[(i + 1) % 48][0]
    PAIRS.append((_mk_lang(c, sib_c), _mk_left(g, sib_g)))


def catalog_selfcheck() -> None:
    seen: set[str] = set()
    for suc, leftp in PAIRS:
        for spec in (suc, leftp):
            slug = spec["slug"]
            if slug in seen:
                raise SystemExit(f"duplicate catalog slug {slug}")
            seen.add(slug)
            ident = " ".join(
                str(spec.get(k, ""))
                for k in ("slug", "harbor", "env", "tool", "leftover", "token", "cache_id")
            ).lower()
            for needle in BANNED_NEEDLES:
                if needle in ident:
                    raise SystemExit(f"banned needle {needle!r} in {slug}")
            if "harbor-" in slug or "sysctl" in ident:
                raise SystemExit(f"ban {slug}")
    if len(PAIRS) < 12:
        raise SystemExit(f"catalog too small: {len(PAIRS)}")


def next_free_idx(start: int = 0) -> int | None:
    for i in range(start, len(PAIRS)):
        suc, leftp = PAIRS[i]
        if not slug_taken(suc["slug"]) and not slug_taken(leftp["slug"]):
            return i
    return None


def write_round(round_n: int, staging: Path, idx: int | None = None) -> None:
    if idx is None:
        raise SystemExit("catalog idx required")
    suc, leftp = PAIRS[idx]
    for spec in (suc, leftp):
        if slug_taken(spec["slug"]):
            raise SystemExit(f"slug {spec['slug']} already published; refuse clone")
    srec = success_episode(round_n, suc)
    lrec = leftover_episode(round_n, leftp)
    blob = json.dumps(srec) + json.dumps(lrec)
    for key in ("thought", "chain_of_thought", "scratch", "inner_monologue", "spike_events"):
        if key in srec or key in lrec or f'"{key}"' in blob:
            raise SystemExit(f"forbidden key {key}")
    if '"sim_or_real": "real"' in blob:
        raise SystemExit("sim_or_real real forbidden")
    nsteps_s = srec["reward"]["cost_steps"]
    nsteps_l = lrec["reward"]["cost_steps"]
    if not (16 <= nsteps_s <= 24 and 16 <= nsteps_l <= 24):
        raise SystemExit(f"step count out of range {nsteps_s}/{nsteps_l}")
    batch = staging / f"batch-r{round_n:02d}.jsonl"
    notes = staging / f"NOTES-r{round_n:02d}.md"
    batch.write_text(
        json.dumps(srec, separators=(",", ":")) + "\n" + json.dumps(lrec, separators=(",", ":")) + "\n"
    )
    notes.write_text(notes_for(round_n, suc, leftp, srec, lrec))
    if "Novel coverage:" not in notes.read_text():
        raise SystemExit("NOTES missing Novel coverage")
    print(json.dumps({"round": round_n, "idx": idx, "ids": [srec["id"], lrec["id"]], "steps": [nsteps_s, nsteps_l], "bytes": batch.stat().st_size}))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--staging", required=True)
    ap.add_argument("--idx", type=int, required=True)
    args = ap.parse_args()
    write_round(args.round, Path(args.staging), args.idx)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
