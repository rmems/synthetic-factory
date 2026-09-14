#!/usr/bin/env python3
"""Emit leftover45–52 plant catalogs for sandbox-refusal-factory r2696+."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
gen13 = __import__("importlib.machinery", fromlist=["SourceFileLoader"]).SourceFileLoader(
    "gen13d", str(ROOT / "_gen_sbox_leftover13plus.py")
).load_module()
gen37 = __import__("importlib.machinery", fromlist=["SourceFileLoader"]).SourceFileLoader(
    "gen37d", str(ROOT / "_gen_sbox_leftover37plus.py")
).load_module()


def packs():
    p45 = gen37.fifty("45", [
        "ntpd", "chrony", "ptp4l", "gpsd", "ntpsec", "openntpd", "timesyncd", "adjtimex",
        "ntpq", "ntpdate", "sntp", "ptpd", "linuxptp", "gpsdjson", "chronyc", "ntpdump",
        "phc2sys", "timemaster", "gpsdshm", "nmea", "pps", "ktime", "rtc", "hwclock",
        "timedatectl", "ntpstat", "chronyd", "ntpsnmpd", "ptpv2", "ieee1588", "gpsbabel",
        "gpsmon", "cgps", "gpspipe", "ntpdc", "sntpd", "openntpdlocal", "chronylocal",
        "ntpconf", "chronyconf", "ptpconf", "gpsdconf", "timesyncconf", "adjtime",
        "ntpkey", "chronykey", "ptpkey", "gpsdkey", "leapfile", "ntpleap",
    ])
    p46 = gen37.fifty("46", [
        "cups", "cupsd", "ipptool", "lpd", "lpr", "lpq", "lprm", "lpstat", "lpadmin",
        "cupsaccept", "cupsreject", "cupsdisable", "cupsenable", "cupsctl", "cupstestppd",
        "foomatic", "ghostscriptlocal", "gsprint", "hplip", "hpijs", "hpcups", "foo2zjs",
        "splix", "c2esp", "brlaser", "ptouch", "dymo", "zebra", "sato", "intermec",
        "datamax", "toshiba", "epson", "canon", "brother", "xerox", "ricoh", "kyocera",
        "lexmark", "hpprinter", "ipp", "ippserver", "pappl", "avahi", "bonjour", "mdns",
        "dnssd", "airprint", "mopria", "ippoverusb",
    ])
    p47 = gen37.fifty("47", [
        "gnome", "kde", "xfce", "lxqt", "mate", "cinnamon", "budgie", "pantheon",
        "i3wm", "sway", "hyprland", "riverwm", "niri", "dwm", "bspwm", "herbstluft",
        "xmonad", "qtile", "awesomewmalt", "openbox", "fluxbox", "icewm", "jwm", "pekwm",
        "wayland", "xorg", "xwayland", "pipewire", "pulseaudio", "jackd", "alsa",
        "wireplumber", "pavucontrol", "pamixer", "amixer", "alsactl", "pwcat", "pwplay",
        "pwrecord", "pwloopback", "pwmon", "pwtop", "pwdump", "pactl", "pacmd", "pulseconf",
        "pipewireconf", "jackconf", "alsaconf", "asoundrc",
    ])
    p48 = gen37.fifty("48", [
        "libreoffice", "onlyoffice", "collabora", "openoffice", "calligra", "abiword",
        "gnumeric", "scribus", "inkscape", "gimp", "krita", "darktable", "rawtherapee",
        "digikam", "shotwell", "gthumb", "eog", "evince", "okular", "zathura", "mupdf",
        "calibre", "sigil", "pandoc", "typst", "lualatex", "xelatex", "pdflatex", "context",
        "groff", "troff", "nroff", "mandoc", "asciidoc", "asciidoctor", "rst2pdf",
        "wkhtmltopdf", "weasyprint", "prince", "pagedjs", "vivliostyle", "pagedown",
        "rmd", "quartoalt", "bookdownalt", "tinytex", "miktex", "texlive", "texmf", "kpathsea",
    ])
    p49 = gen37.fifty("49", [
        "cloudfront", "akamai", "fastlycdn", "cloudflarecdn", "bunnycdn", "keycdn",
        "stackpath", "imperva", "incapsula", "sucuricdn", "wordfencecdn", "cdn77",
        "gcorecdn", "limelight", "edgio", "lumen", "level3", "cachefly", "maxcdn",
        "jsdelivr", "unpkg", "cdnjs", "bootcdn", "staticfile", "npmmirror", "yarnpkg",
        "githubpages", "netlify", "vercel", "cloudflarepages", "render", "flyio", "railway",
        "heroku", "dokku", "caprover", "coolify", "easypanel", "portainer", "yacht",
        "rancherlocal", "k3slocal", "k0slocal", "microk8slocal", "okd", "openshift",
        "crc", "minishift", "odo", "knative",
    ])
    p50 = gen37.fifty("50", [
        "stripecli", "square", "clover", "toastpos", "lightspeed", "shopifypos", "vend",
        "erply", "loyverse", "sumup", "izettle", "adyen", "braintree", "worldpay",
        "cybersource", "authorize", "nmi", "payeezy", "firstdata", "elavon", "tsys",
        "fiserv", "heartland", "globalpayments", "worldline", "ingenico", "verifone",
        "pax", "castles", "sunmi", "newland", "telpo", "urovo", "bluebird", "honeywell",
        "zebraalt", "datalogic", "socketmobile", "lineapros", "shopkeep", "revel",
        "micros", "simphony", "ncraloha", "toastalt", "squarealt", "cloveralt",
        "stripealt", "braintreealt", "adyenalt",
    ])
    p51 = gen37.fifty("51", [
        "zoom", "teams", "webex", "meet", "hangouts", "slack", "mattermost", "rocketchat",
        "zulip", "discord", "element", "matrix", "synapse", "dendrite", "conduit",
        "ircd", "unrealircd", "inspircd", "ngircd", "ergonomica", "soju", "znc", "weechat",
        "irssi", "hexchat", "pidgin", "finch", "bitlbee", "purple", "telepathy",
        "signal", "sessionapp", "briar", "cwtch", "tox", "ricochet", "onionshare",
        "jitsilocal", "livekitlocal", "januslocal", "mediasouplocal", "pionlocal",
        "aiortclocal", "webrtcocal", "bigbluebutton", "bbb", "greenlight", "scalelite",
        "etherpad", "hedgedoc",
    ])
    p52 = gen37.fifty("52", [
        "mastodon", "pleroma", "misskey", "gotosocial", "hometown", "glitchsoc", "akkoma",
        "friendica", "hubzilla", "diaspora", "socialhome", "pixelfed", "peertubealt",
        "funkwhalealt2", "writefreely", "plume", "wordpressalt", "ghostalt", "microblog",
        "tumblr", "livejournal", "dreamwidth", "insanejournal", "journalfen",
        "rss", "atom", "jsonfeed", "rss2email", "feedreader", "newsboat", "newsbeuter",
        "liferea", "akregator", "quite", "miniflux", "freshrss", "tt-rss", "selfoss",
        "tiny-tiny-rss", "commafeed", "stringer", "feedbin", "inoreader", "feedly",
        "theoldreader", "newsblur", "feedspot", "bloglines", "google-reader", "fever",
    ])
    p52 = [(r[0].replace("tt-rss", "ttrss").replace("tiny-tiny-rss", "tinytinyrss").replace("google-reader", "googlereader"),) + r[1:] if "-" in r[0] else r for r in p52]
    return [
        (45, 2696, "time leftover dump files", "qnx…pass", "44", p45),
        (46, 2746, "print leftover dump files", "qnx…ntpleap", "45", p46),
        (47, 2796, "desktop leftover dump files", "qnx…ippoverusb", "46", p47),
        (48, 2846, "office leftover dump files", "qnx…asoundrc", "47", p48),
        (49, 2896, "CDN leftover dump files", "qnx…kpathsea", "48", p49),
        (50, 2946, "POS leftover dump files", "qnx…knative", "49", p50),
        (51, 2996, "chat leftover dump files", "qnx…adyenalt", "50", p51),
        (52, 3046, "feed leftover dump files", "qnx…hedgedoc", "51", p52),
    ]


def main() -> None:
    fams, overs, misses = gen13.existing()
    inc = 13800
    written = []
    for n, start, theme, span, prev, rows in packs():
        path = ROOT / f"sbox-mill-plants-leftover{n}.py"
        if path.exists():
            inc += 4 * len(rows)
            written.append((path.name, "exists"))
            continue
        slugs = [r[0] for r in rows]
        if len(set(slugs)) != 50:
            raise SystemExit(f"dup leftover{n} {len(set(slugs))} {len(slugs)}")
        body = []
        for i, row in enumerate(rows):
            slug, miss_ext = row[0], row[5]
            family = f"leftover-{slug}-dump"
            over_slug = f"{slug}-home-lab"
            miss_slug = f"{slug}-{miss_ext.replace('.', '-')}-copy"
            if family in fams:
                raise SystemExit(f"family collision {family}")
            if over_slug in overs:
                raise SystemExit(f"over collision {over_slug}")
            if miss_slug in misses:
                raise SystemExit(f"miss collision {miss_slug}")
            fams.add(family); overs.add(over_slug); misses.add(miss_slug)
            neighbors = [f"leftover {slugs[k]} dump" for k in (i-2, i-1, i+1, i+2) if 0 <= k < 50][:4]
            body.append(gen13.emit_row(*row, inc, i, neighbors))
            inc += 4
        text = gen13.HEADER.format(start=start, prev=prev, span=span, before=start-1, theme=theme)
        path.write_text(text + "".join(body) + gen13.FOOT)
        written.append((path.name, start, start+49))
    print(written)


if __name__ == "__main__":
    main()
