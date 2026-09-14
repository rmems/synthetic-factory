#!/usr/bin/env python3
"""MAC mill r3847+. Unique beverage/bakery plants. Not whiskey."""
from __future__ import annotations

import json
import sys
import time
from importlib.machinery import SourceFileLoader
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
sys.path.insert(0, str(REPO / "pipelines"))
import round_txn  # noqa: E402

_b = SourceFileLoader("mac3205i", str(REPO / "experiments/mac-mill-r3205.py")).load_module()
A = _b.A
build_record = _b.build_record
notes_text = _b.notes_text
busy = _b.busy

FACTORY = REPO / "outputs/raw/2026-08-19-agentic/multi-agent-coordination-factory"
SBOX = REPO / "outputs/raw/2026-08-19-agentic/sandbox-refusal-factory"
DEADLINE_S = 6 * 60 * 60
BANNED_SUB = ("capro-oxime-vs-beckmann", "whiskey-barrel", "hearts-vs-tails", "whiskey")

SCENARIOS = [
    A("gin-juniper-vs-cut", "gin", "juniper", "1.8 g/L", "2.4 g/L", "2.38 g/L", "4 K", "harsh", "cut +4%", 8, 1, "still", "London", "1.4 g/L", "cut 4% extra", "vodka methanol vs heads", "gn_op", "ct_gn", "jn_lab", 58),
    A("vodka-methanol-vs-heads", "vodka", "MeOH", "28 ppm", "8 ppm", "8.2 ppm", "5 K", "heads", "cut +4%", 8, 1, "still", "neutral", "40 ppm", "heads 4% extra", "rum congener vs age", "vd_op", "hd_vd", "meoh_lab", 57),
    A("rum-congener-vs-age", "rum", "congener", "180 mg/L", "80 mg/L", "82 mg/L", "4 K", "harsh", "age +4%", 10, 1, "cask", "gold", "240 mg/L", "age 4 mo extra", "tequila agave vs methanol", "rm_op", "ag_rm", "cg_lab", 56),
    A("tequila-agave-vs-methanol", "tequila", "MeOH", "180 ppm", "80 ppm", "82 ppm", "5 K", "MeOH", "cut +4%", 8, 1, "still", "blanco", "240 ppm", "heads 4% extra", "brandy lees vs copper", "tq_op", "ct_tq", "meoh_tq", 55),
    A("brandy-lees-vs-copper", "brandy", "Cu", "8.4 mg/L", "3.0 mg/L", "3.1 mg/L", "4 K", "Cu", "lees +4%", 9, 1, "still", "VS", "11 mg/L", "lees 4% extra", "sake nihonshu vs acid", "br_op", "ls_br", "cu_br", 54),
    A("sake-nihonshu-vs-acid", "sake", "SMV", "-4", "+3", "+2.8", "3 K", "sweet", "koji +4%", 10, 1, "tank", "junmai", "-8", "koji 4% extra", "soju ABV vs methanol", "sk_op", "kj_sk", "smv_lab", 53),
    A("soju-abv-vs-methanol", "soju", "MeOH", "22 ppm", "8 ppm", "8.2 ppm", "4 K", "MeOH", "cut +4%", 8, 1, "still", "dilute", "30 ppm", "heads 4% extra", "mezcal smoke vs phenol", "sj_op", "ct_sj", "meoh_sj", 52),
    A("mezcal-smoke-vs-phenol", "mezcal", "phenol", "28 mg/L", "12 mg/L", "12.4 mg/L", "6 K", "ash", "cut +4%", 8, 1, "still", "joven", "36 mg/L", "cut 4% extra", "cider juice vs SO2", "mz_op", "ct_mz", "ph_mz", 51),
    A("cider-juice-vs-so2", "cider juice", "SO2", "42 ppm", "80 ppm", "78 ppm", "2 K", "ox", "SO2 +4%", 6, 1, "tank", "keeving", "28 ppm", "SO2 4% extra", "perry tannin vs acid", "cj_op", "so2_cj", "so2_lab", 50),
    A("perry-tannin-vs-acid", "perry", "TA", "4.2 g/L", "5.5 g/L", "5.45 g/L", "2 K", "flat", "acid +4%", 7, 1, "tank", "bottle", "3.6 g/L", "acid 4% extra", "mead honey vs stuck", "pr_op", "ac_pr", "ta_pr", 49),
    A("mead-honey-vs-stuck", "mead", "FG", "1.028", "1.008", "1.010", "3 K", "stuck", "nutrient +4%", 8, 1, "carboy", "traditional", "1.035", "DAP 4% extra", "kombucha SCOBY vs pH", "md_op", "nt_md", "fg_lab", 48),
    A("kombucha-scoby-vs-ph", "kombucha", "pH", "3.82", "3.20", "3.22", "2 K", "sweet", "time +4%", 8, 1, "crock", "bottle", "4.10", "time 4 d extra", "kefir grain vs count", "kb_op", "tm_kb", "ph_kb", 47),
    A("kefir-grain-vs-count", "kefir", "CFU", "6.2 log", "8.0 log", "7.9 log", "2 K", "thin", "grain +4%", 7, 1, "jar", "dairy", "5.5 log", "grain 4% extra", "kvass bread vs ABV", "kf_op", "gr_kf", "cfu_kf", 46),
    A("kvass-bread-vs-abv", "kvass", "ABV", "0.42%", "1.0%", "0.98%", "3 K", "flat", "time +4%", 8, 1, "crock", "rye", "0.20%", "time 4% extra", "pulque aguamiel vs pH", "kv_op", "tm_kv", "abv_kv", 45),
    A("pulque-aguamiel-vs-ph", "pulque", "pH", "4.62", "4.20", "4.22", "2 K", "sour", "time +4%", 7, 1, "tinacal", "fresh", "4.90", "time 4% extra", "chicha mastic vs ABV", "pq_op", "tm_pq", "ph_pq", 44),
    A("chicha-mastic-vs-abv", "chicha", "ABV", "1.8%", "3.0%", "2.95%", "3 K", "stuck", "malt +4%", 8, 1, "tinaja", "festa", "1.2%", "malt 4% extra", "lassi culture vs pH", "ch_op", "ml_ch", "abv_ch", 43),
    A("lassi-culture-vs-ph", "lassi", "pH", "4.62", "4.30", "4.32", "2 K", "sweet", "culture +4%", 6, 1, "vat", "salted", "4.90", "culture 4% extra", "ayran salt vs visc", "ls_op", "cu_ls", "ph_ls", 42),
    A("ayran-salt-vs-visc", "ayran", "visc", "18 cP", "28 cP", "27 cP", "2 K", "whey", "culture +4%", 6, 1, "vat", "drink", "12 cP", "culture 4% extra", "kefir water vs fizz", "ay_op", "cu_ay", "vis_ay", 41),
    A("kefir-water-vs-fizz", "water kefir", "CO2", "1.2 vol", "2.4 vol", "2.35 vol", "2 K", "flat", "bottle +4%", 7, 1, "bottle", "ginger", "0.8 vol", "sugar 4% extra", "jun tea vs acid", "wk_op", "bt_wk", "co2_wk", 40),
    A("jun-tea-vs-acid", "jun", "TA", "4.2 g/L", "6.0 g/L", "5.9 g/L", "2 K", "sweet", "time +4%", 8, 1, "crock", "green", "3.4 g/L", "time 4% extra", "tepache pineapple vs ABV", "jn_op", "tm_jn", "ta_jn", 39),
    A("tepache-pineapple-vs-abv", "tepache", "ABV", "0.8%", "1.5%", "1.48%", "3 K", "stuck", "piloncillo +4%", 7, 1, "crock", "street", "0.4%", "sugar 4% extra", "ginger beer vs CO2", "tp_op", "pl_tp", "abv_tp", 38),
    A("ginger-beer-vs-co2", "ginger beer", "CO2", "1.8 vol", "2.8 vol", "2.75 vol", "3 K", "flat", "prime +4%", 6, 1, "bottle", "spicy", "1.2 vol", "sugar 4% extra", "root beer vs sassafras", "gb_op", "pr_gb", "co2_gb", 37),
    A("root-beer-vs-sassafras", "root beer", "safrole", "8 ppm", "2 ppm", "2.1 ppm", "4 K", "safrole", "extract +4%", 7, 1, "kettle", "draft", "12 ppm", "cut 4% extra", "cola phosphoric vs brix", "rb_op", "ex_rb", "sf_lab", 36),
    A("cola-phosphoric-vs-brix", "cola", "brix", "10.4", "11.2", "11.15", "3 K", "flat", "syrup +4%", 6, 1, "blend", "bottle", "9.8", "syrup 4% extra", "energy caffeine vs taurine", "cl_op", "sy_cl", "bx_cl", 35),
    A("energy-caffeine-vs-taurine", "energy", "caffeine", "28 mg/100", "32 mg/100", "31.8", "2 K", "low", "dose +4%", 5, 1, "blend", "can", "24", "dose 4% extra", "isotonic osmo vs Na", "en_op", "ds_en", "caf_lab", 34),
    A("isotonic-osmo-vs-na", "isotonic", "osmo", "280", "300", "298", "2 K", "hypo", "Na +4%", 6, 1, "blend", "sport", "260", "Na 4% extra", "protein shake vs sed", "iso_op", "na_iso", "osm_lab", 33),
    A("protein-shake-vs-sed", "shake", "sed", "8.4%", "2.0%", "2.1%", "3 K", "grit", "homo +4%", 7, 1, "blend", "RTD", "11%", "homo 4% extra", "plant milk vs N", "ps_op", "hm_ps", "sd_lab", 32),
    A("plant-milk-vs-n", "plant milk", "protein", "1.8%", "3.0%", "2.95%", "4 K", "grit", "isolate +4%", 8, 1, "blend", "barista", "1.2%", "isolate 4% extra", "soy milk vs beany", "pm_op", "is_pm", "pr_pm", 31),
    A("soy-milk-vs-beany", "soy milk", "hexanal", "180 ppb", "40 ppb", "42 ppb", "5 K", "beany", "blanch +4%", 8, 1, "tank", "UHT", "240 ppb", "blanch 4% extra", "oat milk vs beta", "sy_op", "bl_sy", "hx_lab", 30),
    A("oat-milk-vs-beta", "oat milk", "beta", "0.42%", "0.80%", "0.78%", "4 K", "thin", "enzyme +4%", 8, 1, "tank", "barista", "0.28%", "enzyme 4% extra", "almond milk vs grit", "ot_op", "enz_ot", "bg_ot", 29),
    A("almond-milk-vs-grit", "almond", "grit", "8.4%", "2.0%", "2.1%", "3 K", "grit", "mill +4%", 7, 1, "tank", "barista", "11%", "mill 4% extra", "coconut milk vs fat", "al_op", "ml_al", "gr_al", 28),
    A("coconut-milk-vs-fat", "coconut", "fat", "12.4%", "17.0%", "16.8%", "4 K", "split", "homo +4%", 7, 1, "tank", "can", "10%", "homo 4% extra", "rice milk vs arsenic", "cc_op", "hm_cc", "ft_cc", 27),
    A("rice-milk-vs-arsenic", "rice milk", "As", "18 ppb", "8 ppb", "8.2 ppb", "5 K", "As", "source +4%", 8, 1, "tank", "kid", "24 ppb", "source 4% extra", "hemp milk vs grit", "rc_op", "sr_rc", "as_rc", 26),
    A("hemp-milk-vs-grit", "hemp", "grit", "6.2%", "1.5%", "1.55%", "3 K", "grit", "mill +4%", 7, 1, "tank", "barista", "8.0%", "mill 4% extra", "pea milk vs beany", "hp_op", "ml_hp", "gr_hp", 25),
    A("pea-milk-vs-beany", "pea milk", "hexanal", "140 ppb", "40 ppb", "42 ppb", "4 K", "beany", "blanch +4%", 8, 1, "tank", "barista", "180 ppb", "blanch 4% extra", "cashew milk vs visc", "pea_op", "bl_pea", "hx_pea", 24),
    A("cashew-milk-vs-visc", "cashew", "visc", "18 cP", "28 cP", "27 cP", "3 K", "thin", "paste +4%", 7, 1, "tank", "barista", "12 cP", "paste 4% extra", "sourdough levain vs pH", "csh_op", "ps_csh", "vis_csh", 23),
    A("sourdough-levain-vs-ph", "levain", "pH", "4.62", "4.20", "4.22", "2 K", "weak", "feed +4%", 8, 1, "crock", "boule", "4.90", "feed 4% extra", "baguette alveograph vs W", "sd_op", "fd_sd", "ph_sd", 22),
    A("baguette-alveograph-vs-w", "flour", "W", "180", "240", "236", "3 K", "weak", "blend +4%", 7, 1, "silo", "baguette", "150", "blend 4% extra", "croissant lamination vs layers", "bg_op", "bl_bg", "w_lab", 21),
    A("croissant-lamination-vs-layers", "croissant", "layers", "18", "27", "26", "2 K", "leak", "fold +4%", 6, 1, "sheet", "butter", "12", "rest 4% extra", "pretzel lye vs color2", "cr_op", "fd_cr", "ly_lab", 20),
    A("pretzel-lye-vs-color2", "pretzel", "L*", "58", "48", "48.4", "5 K", "pale", "lye +4%", 5, 1, "oven", "soft", "64", "lye 4% extra", "ramen kansui vs yellow", "pz_op", "ly_pz", "l_pz", 19),
    A("ramen-kansui-vs-yellow", "ramen", "b*", "8.4", "14.0", "13.8", "3 K", "pale", "kansui +4%", 6, 1, "mixer", "tonkotsu", "6.0", "kansui 4% extra", "udon gluten vs chew", "rm_op", "kn_rm", "b_rm", 18),
    A("udon-gluten-vs-chew", "udon", "chew", "18 N", "28 N", "27 N", "3 K", "soft", "rest +4%", 7, 1, "sheet", "sanuki", "12 N", "rest 4% extra", "somen dry vs break", "ud_op", "rs_ud", "ch_ud", 17),
    A("somen-dry-vs-break", "somen", "break", "8.4%", "2.0%", "2.1%", "4 K", "break", "RH +4%", 8, 1, "rack", "dry", "11%", "RH 4% extra", "pho broth vs clarity", "sm_op", "rh_sm", "br_sm", 16),
    A("pho-broth-vs-clarity", "pho", "NTU", "28", "8", "8.2", "5 K", "cloud", "skim +4%", 8, 1, "stock", "beef", "36", "skim 4% extra", "stock gelatin vs body", "ph_op", "sk_ph", "ntu_ph", 15),
    A("stock-gelatin-vs-body", "stock", "bloom", "82", "140", "136", "6 K", "thin", "bones +4%", 9, 1, "kettle", "fond", "60", "bones 4% extra", "demi glace vs reduce", "st_op", "bn_st", "bl_st", 14),
    A("demi-glace-vs-reduce", "demi", "brix", "18.4", "24.0", "23.6", "7 K", "scorch", "reduce +4%", 8, 1, "pot", "sauce", "16", "reduce 4% extra", "beurre monte vs break", "dm_op", "rd_dm", "bx_dm", 13),
    A("beurre-monte-vs-break", "beurre", "break", "fail", "hold", "hold", "2 K", "break", "temp -4%", 5, 1, "bain", "finish", "fail", "temp 4% extra", "hollandaise vs split", "bm_op", "tp_bm", "br_bm", 12),
    A("hollandaise-vs-split", "hollandaise", "split", "fail", "hold", "hold", "2 K", "split", "temp -4%", 5, 1, "bain", "brunch", "fail", "temp 4% extra", "custard NTU vs curdle", "hl_op", "tp_hl", "sp_hl", 11),
    A("custard-ntu-vs-curdle", "custard", "NTU", "28", "8", "8.2", "3 K", "curdle", "temp -4%", 6, 1, "pot", "creme", "36", "temp 4% extra", "gelato overrun vs temp", "cu_op", "tp_cu", "ntu_cu", 10),
    A("gelato-overrun-vs-temp", "gelato", "overrun", "42%", "28%", "28.4%", "3 K", "icy", "draw -2 K", 6, 1, "batch", "pistachio", "55%", "draw 4% extra", "sorbet brix vs freeze", "gl_op", "dr_gl", "ov_gl", 9),
    A("sorbet-brix-vs-freeze", "sorbet", "brix", "22.4", "28.0", "27.6", "4 K", "icy", "sugar +4%", 6, 1, "batch", "lemon", "18", "sugar 4% extra", "granita crystal vs stir", "sr_op", "sg_sr", "bx_sr", 8),
    A("granita-crystal-vs-stir", "granita", "crystal", "8 mm", "2 mm", "2.1 mm", "2 K", "slab", "stir +4%", 5, 1, "pan", "coffee", "12 mm", "stir 4% extra", "popsicle solids vs drip", "gr_op", "st_gr", "cr_gr", 7),
    A("popsicle-solids-vs-drip", "pop", "solids", "12.4%", "18.0%", "17.8%", "3 K", "drip", "sugar +4%", 6, 1, "mold", "fruit", "10%", "sugar 4% extra", "skyr protein vs drain", "pp_op", "sg_pp", "sol_pp", 6),
    A("skyr-protein-vs-drain", "skyr", "protein", "8.4%", "11.0%", "10.8%", "3 K", "whey", "drain +4%", 8, 1, "vat", "cup", "7.0%", "drain 4% extra", "quark moisture vs press", "sk_op", "dr_sk", "pr_sk", 5),
    A("quark-moisture-vs-press", "quark", "moisture", "78.4%", "72.0%", "72.2%", "3 K", "wet", "press +4%", 7, 1, "vat", "tub", "82%", "press 4% extra", "labneh salt vs drain", "qk_op", "pr_qk", "moi_qk", 4),
    A("labneh-salt-vs-drain", "labneh", "moisture", "74.2%", "68.0%", "68.2%", "3 K", "wet", "drain +4%", 8, 1, "bag", "ball", "78%", "drain 4% extra", "ricotta whey vs yield", "lb_op", "dr_lb", "moi_lb", 3),
    A("ricotta-whey-vs-yield", "ricotta", "yield", "8.4%", "12.0%", "11.8%", "4 K", "yield", "acid +4%", 7, 1, "kettle", "fresh", "6.5%", "acid 4% extra", "mozzarella stretch vs pH", "rc_op", "ac_rc", "yld_rc", 2),
    A("mozzarella-stretch-vs-ph", "mozz", "pH", "5.42", "5.20", "5.22", "3 K", "no-stretch", "acid +4%", 6, 1, "vat", "pizza", "5.60", "acid 4% extra", "gin next densify", "mz_op", "ac_mz", "ph_mz", 61),
]


def self_check() -> None:
    slugs = [s["slug"] for s in SCENARIOS]
    if len(slugs) != len(set(slugs)):
        raise SystemExit("dup slugs")
    for s in SCENARIOS:
        if any(b in s["slug"] for b in BANNED_SUB):
            raise SystemExit(s["slug"])
        rec = build_record(3847, s)
        if len(rec["transcript"]) < 8 or len(s["agents"]) != 3:
            raise SystemExit(s["slug"])
    print(f"self_check ok: {len(SCENARIOS)} plants", flush=True)


def main() -> int:
    self_check()
    published = []
    idx = 0
    start = time.monotonic()
    while time.monotonic() - start < DEADLINE_S:
        n = round_txn.frontier_status(FACTORY)["next_round"]
        if busy(FACTORY):
            print(f"MAC r{n} reserved/writing; wait (sbox reserved/writing={busy(SBOX)})", flush=True)
            time.sleep(2)
            continue
        if idx >= len(SCENARIOS):
            print(f"MAC catalog exhausted at r{n}", flush=True)
            break
        spec = SCENARIOS[idx]
        idx += 1
        try:
            reservation = round_txn.reserve(FACTORY, n, 1)
        except (round_txn.TransactionError, FileExistsError, OSError) as exc:
            print(f"HOP reserve r{n}: {exc}", flush=True)
            idx -= 1
            time.sleep(1)
            continue
        rec = build_record(n, spec)
        line = json.dumps(rec, ensure_ascii=False, separators=(",", ":"))
        nbytes = len(line.encode())
        stage = Path(reservation["staging_dir"])
        (stage / reservation["batch_file"]).write_text(line + "\n")
        (stage / reservation["notes_file"]).write_text(notes_text(spec, nbytes, n))
        print(f"STAGED r{n} {rec['id']} {nbytes}B", flush=True)
        try:
            round_txn.publish(FACTORY, n, reservation["token"])
        except round_txn.TransactionError as exc:
            print(f"PUBLISH FAIL r{n}: {exc}", flush=True)
            try:
                round_txn.abort(FACTORY, n, reservation["token"])
            except round_txn.TransactionError:
                pass
            return 1
        published.append((n, rec["id"], nbytes))
        print(f"PUBLISHED r{n} {rec['id']} {nbytes}B", flush=True)
    print(json.dumps({"published": published, "count": len(published),
                      "frontier": round_txn.frontier_status(FACTORY)["next_round"]}), flush=True)
    return 0 if published else 1


if __name__ == "__main__":
    raise SystemExit(main())
