#!/usr/bin/env python3
"""MAC mill r3905+. Unique spice/EO plants. Not whiskey, not lavender-still."""
from __future__ import annotations

import json
import sys
import time
from importlib.machinery import SourceFileLoader
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
sys.path.insert(0, str(REPO / "pipelines"))
import round_txn  # noqa: E402

_b = SourceFileLoader("mac3205j", str(REPO / "experiments/mac-mill-r3205.py")).load_module()
A = _b.A
build_record = _b.build_record
notes_text = _b.notes_text
busy = _b.busy

FACTORY = REPO / "outputs/raw/2026-08-19-agentic/multi-agent-coordination-factory"
SBOX = REPO / "outputs/raw/2026-08-19-agentic/sandbox-refusal-factory"
DEADLINE_S = 6 * 60 * 60
BANNED_SUB = ("capro-oxime-vs-beckmann", "whiskey-barrel", "hearts-vs-tails", "whiskey", "lavender")

SCENARIOS = [
    A("vanilla-vanillin-vs-moisture", "vanilla", "vanillin", "1.8%", "2.2%", "2.18%", "5 K", "mold", "dry +4%", 10, 1, "bean", "extract", "1.4%", "dry 4% extra", "cinnamon coumarin vs oil", "vn_op", "dr_vn", "vn_lab", 56),
    A("cinnamon-coumarin-vs-oil", "cinnamon", "coumarin", "1800 ppm", "400 ppm", "410 ppm", "6 K", "cassia", "blend +4%", 8, 1, "lot", "true", "2400 ppm", "ceylon 4% extra", "pepper piperine vs ash", "cn_op", "bl_cn", "cm_lab", 55),
    A("pepper-piperine-vs-ash", "pepper", "piperine", "4.2%", "5.5%", "5.45%", "4 K", "ash", "steam +4%", 8, 1, "lot", "black", "3.6%", "steam 4% extra", "clove eugenol vs oil", "pp_op", "st_pp", "pip_lab", 54),
    A("clove-eugenol-vs-oil", "clove", "eugenol", "72%", "80%", "79.4%", "5 K", "phenol", "distill +4%", 9, 1, "still", "bud", "66%", "cut 4% extra", "nutmeg myristicin vs oil", "cl_op", "ds_cl", "eu_lab", 53),
    A("nutmeg-myristicin-vs-oil", "nutmeg", "myristicin", "8.4%", "4.0%", "4.1%", "5 K", "myristicin", "cut +4%", 8, 1, "still", "mace", "11%", "cut 4% extra", "cardamom cineole vs oil", "nm_op", "ct_nm", "my_lab", 52),
    A("cardamom-cineole-vs-oil", "cardamom", "cineole", "28%", "36%", "35.6%", "4 K", "terpene", "distill +4%", 8, 1, "still", "green", "22%", "cut 4% extra", "saffron crocin vs color", "cd_op", "ds_cd", "cn_cd", 51),
    A("saffron-crocin-vs-color", "saffron", "crocin", "180", "220", "218", "3 K", "fade", "dry +4%", 8, 1, "lot", "ISO", "150", "dark 4% extra", "turmeric curcumin vs color", "sf_op", "dr_sf", "cr_sf", 50),
    A("turmeric-curcumin-vs-color", "turmeric", "curcumin", "3.2%", "4.5%", "4.45%", "5 K", "color", "extract +4%", 9, 1, "lot", "oleo", "2.6%", "solvent 4% extra", "ginger gingerol vs pungency", "tm_op", "ex_tm", "cu_lab", 49),
    A("ginger-gingerol-vs-pungency", "ginger", "gingerol", "1.8%", "2.4%", "2.38%", "4 K", "heat", "dry +4%", 8, 1, "lot", "oleo", "1.4%", "dry 4% extra", "chili capsaicin vs SHU", "gn_op", "dr_gn", "gg_lab", 48),
    A("chili-capsaicin-vs-shu", "chili", "SHU", "28000", "40000", "39500", "5 K", "heat", "blend +4%", 7, 1, "lot", "oleo", "22000", "blend 4% extra", "mustard allyl vs pungency", "ch_op", "bl_ch", "shu_lab", 47),
    A("mustard-allyl-vs-pungency", "mustard", "AITC", "0.42%", "0.70%", "0.69%", "3 K", "flat", "grind +4%", 6, 1, "lot", "dijon", "0.30%", "grind 4% extra", "horseradish sinigrin vs heat", "ms_op", "gr_ms", "aitc_lab", 46),
    A("horseradish-sinigrin-vs-heat", "horseradish", "sinigrin", "8.4 mg/g", "12.0 mg/g", "11.8 mg/g", "3 K", "flat", "grate +4%", 6, 1, "lot", "sauce", "6.5 mg/g", "grate 4% extra", "wasabi isothio vs heat", "hr_op", "gt_hr", "sg_lab", 45),
    A("wasabi-isothio-vs-heat", "wasabi", "AITC", "4.2 mg/g", "6.0 mg/g", "5.9 mg/g", "2 K", "flat", "grate +4%", 5, 1, "rhizome", "paste", "3.0 mg/g", "grate 4% extra", "garlic allicin vs pungency", "ws_op", "gt_ws", "aitc_ws", 44),
    A("garlic-allicin-vs-pungency", "garlic", "allicin", "2.8 mg/g", "4.0 mg/g", "3.95 mg/g", "3 K", "flat", "crush +4%", 6, 1, "lot", "powder", "2.0 mg/g", "crush 4% extra", "onion pyruvate vs pungency", "gl_op", "cr_gl", "al_lab", 43),
    A("onion-pyruvate-vs-pungency", "onion", "pyruvate", "4.2 µmol/g", "7.0 µmol/g", "6.9 µmol/g", "3 K", "mild", "cut +4%", 6, 1, "lot", "powder", "3.0 µmol/g", "cut 4% extra", "fenugreek sotolon vs maple", "on_op", "ct_on", "py_lab", 42),
    A("fenugreek-sotolon-vs-maple", "fenugreek", "sotolon", "8 ppm", "18 ppm", "17.6 ppm", "5 K", "weak", "roast +4%", 8, 1, "lot", "maple", "5 ppm", "roast 4% extra", "cumin cuminal vs oil", "fg_op", "rs_fg", "st_lab", 41),
    A("cumin-cuminal-vs-oil", "cumin", "cuminal", "18%", "28%", "27.6%", "4 K", "weak", "distill +4%", 8, 1, "still", "seed", "14%", "cut 4% extra", "coriander linalool vs oil", "cm_op", "ds_cm", "cu_cm", 40),
    A("coriander-linalool-vs-oil", "coriander", "linalool", "62%", "70%", "69.4%", "4 K", "terpene", "distill +4%", 8, 1, "still", "seed", "55%", "cut 4% extra", "fennel anethole vs oil", "cr_op", "ds_cr", "ln_cr", 39),
    A("fennel-anethole-vs-oil", "fennel", "anethole", "68%", "78%", "77.4%", "4 K", "estragole", "distill +4%", 8, 1, "still", "seed", "60%", "cut 4% extra", "anise anethole vs oil", "fn_op", "ds_fn", "an_fn", 38),
    A("anise-anethole-vs-oil", "anise", "anethole", "82%", "90%", "89.4%", "4 K", "estragole", "distill +4%", 8, 1, "still", "seed", "74%", "cut 4% extra", "star anise anethole vs shikimic", "an_op", "ds_an", "an_an", 37),
    A("star-anise-anethole-vs-shikimic", "star anise", "shikimic", "4.2%", "6.0%", "5.9%", "5 K", "low", "extract +4%", 9, 1, "lot", "pharma", "3.4%", "solvent 4% extra", "licorice glycyrrhizin vs ash", "sa_op", "ex_sa", "sk_lab", 36),
    A("licorice-glycyrrhizin-vs-ash", "licorice", "gly", "4.8%", "7.0%", "6.9%", "5 K", "ash", "extract +4%", 9, 1, "lot", "block", "3.6%", "solvent 4% extra", "cocoa theobromine vs fat", "lc_op", "ex_lc", "gly_lab", 35),
    A("cocoa-theobromine-vs-fat", "cocoa", "theobromine", "1.8%", "2.4%", "2.38%", "6 K", "fat", "press +4%", 8, 1, "liquor", "powder", "1.4%", "press 4% extra", "coffee cafestol vs oil", "cc_op", "pr_cc", "th_lab", 34),
    A("coffee-cafestol-vs-oil", "coffee", "cafestol", "8.4 mg/g", "4.0 mg/g", "4.1 mg/g", "6 K", "oil", "paper +4%", 7, 1, "brew", "filter", "11 mg/g", "paper 4% extra", "tea EGCG vs catechin", "cf_op", "pp_cf", "cf_lab", 33),
    A("tea-egcg-vs-catechin", "green tea", "EGCG", "4.2%", "6.0%", "5.9%", "4 K", "oxid", "steam +4%", 8, 1, "lot", "extract", "3.4%", "steam 4% extra", "mate xanthine vs ash", "te_op", "st_te", "eg_lab", 32),
    A("mate-xanthine-vs-ash", "yerba", "xanthine", "0.82%", "1.20%", "1.18%", "5 K", "ash", "age +4%", 8, 1, "lot", "chimarrao", "0.60%", "age 4% extra", "guarana caffeine vs tannin", "mt_op", "ag_mt", "xa_lab", 31),
    A("guarana-caffeine-vs-tannin", "guarana", "caffeine", "3.8%", "5.0%", "4.95%", "5 K", "tannin", "extract +4%", 8, 1, "lot", "energy", "3.0%", "solvent 4% extra", "cola nut vs caffeine", "gr_op", "ex_gr", "caf_gr", 30),
    A("cola-nut-vs-caffeine", "cola nut", "caffeine", "1.4%", "2.0%", "1.98%", "5 K", "tannin", "extract +4%", 8, 1, "lot", "flavor", "1.0%", "solvent 4% extra", "hop alpha vs oil", "cn_op", "ex_cn", "caf_cn", 29),
    A("hop-alpha-vs-oil", "hop", "alpha", "8.4%", "12.0%", "11.8%", "4 K", "oxid", "CO2 +4%", 9, 1, "lot", "pellet", "6.5%", "CO2 4% extra", "malt diastase vs color", "hp_op", "co2_hp", "al_hp", 28),
    A("malt-diastase-vs-color", "malt", "DP", "82", "110", "108", "6 K", "color", "kiln -4%", 8, 1, "lot", "pils", "70", "kiln 4% extra", "yeast viability vs glycogen", "ml_op", "kl_ml", "dp_ml", 27),
    A("yeast-viability-vs-glycogen", "yeast", "viab", "82%", "95%", "94.6%", "3 K", "dead", "feed +4%", 7, 1, "brink", "pitch", "74%", "feed 4% extra", "enzyme activity vs pH", "yt_op", "fd_yt", "vb_lab", 26),
    A("enzyme-activity-vs-ph", "enzyme", "U/g", "8200", "11000", "10800", "4 K", "denature", "pH +0.2", 6, 1, "tank", "process", "7000", "buffer 4% extra", "bergamot linalyl vs bergapten", "ez_op", "ph_ez", "u_lab", 25),
    A("bergamot-linalyl-vs-bergapten", "bergamot", "bergapten", "0.42%", "0.10%", "0.11%", "5 K", "phototox", "rectify +4%", 8, 1, "still", "FCF", "0.55%", "cut 4% extra", "neroli linalool vs indole", "bg_op", "rc_bg", "bp_lab", 24),
    A("neroli-linalool-vs-indole", "neroli", "indole", "0.28%", "0.08%", "0.082%", "5 K", "animalic", "rectify +4%", 8, 1, "still", "blossom", "0.36%", "cut 4% extra", "rose citronellol vs phenethyl", "nr_op", "rc_nr", "in_lab", 23),
    A("rose-citronellol-vs-phenethyl", "rose", "PEA", "1.8%", "3.0%", "2.95%", "5 K", "weak", "distill +4%", 8, 1, "still", "otto", "1.2%", "cut 4% extra", "jasmine benzyl vs indole", "rs_op", "ds_rs", "pea_lab", 22),
    A("jasmine-benzyl-vs-indole", "jasmine", "indole", "2.4%", "1.0%", "1.05%", "4 K", "fecal", "abs +4%", 8, 1, "lot", "absolute", "3.2%", "hex 4% extra", "ylang germacrene vs ester", "js_op", "ab_js", "in_js", 21),
    A("ylang-germacrene-vs-ester", "ylang", "ester", "18%", "28%", "27.6%", "5 K", "harsh", "fraction +4%", 8, 1, "still", "extra", "14%", "cut 4% extra", "patchouli patchoulol vs color", "yl_op", "fr_yl", "es_yl", 20),
    A("patchouli-patchoulol-vs-color", "patchouli", "patchoulol", "28%", "36%", "35.6%", "6 K", "color", "age +4%", 10, 1, "still", "iron-free", "22%", "age 4 mo extra", "vetiver khusimol vs color", "pt_op", "ag_pt", "po_lab", 19),
    A("vetiver-khusimol-vs-color", "vetiver", "khusimol", "12%", "18%", "17.6%", "6 K", "color", "rectify +4%", 9, 1, "still", "haiti", "8%", "cut 4% extra", "sandal santalol vs color", "vt_op", "rc_vt", "kh_lab", 18),
    A("sandal-santalol-vs-color", "sandal", "santalol", "48%", "58%", "57.4%", "6 K", "color", "rectify +4%", 9, 1, "still", "album", "40%", "cut 4% extra", "cedar cedrol vs color", "sd_op", "rc_sd", "sa_lab", 17),
    A("cedar-cedrol-vs-color", "cedar", "cedrol", "18%", "28%", "27.6%", "5 K", "color", "rectify +4%", 8, 1, "still", "atlas", "14%", "cut 4% extra", "pine pinene vs turpentine", "cd_op", "rc_cd", "ce_lab", 16),
    A("pine-pinene-vs-turpentine", "pine", "pinene", "42%", "55%", "54.6%", "5 K", "turp", "rectify +4%", 8, 1, "still", "gum", "34%", "cut 4% extra", "eucalyptus cineole vs phellandrene", "pn_op", "rc_pn", "pi_lab", 15),
    A("eucalyptus-cineole-vs-phellandrene", "eucalyptus", "cineole", "68%", "80%", "79.4%", "5 K", "phellandrene", "rectify +4%", 8, 1, "still", "globulus", "60%", "cut 4% extra", "tea tree terpinen vs cineole", "eu_op", "rc_eu", "cn_eu", 14),
    A("tea-tree-terpinen-vs-cineole", "tea tree", "cineole", "8.4%", "3.0%", "3.1%", "5 K", "cineole", "rectify +4%", 8, 1, "still", "ISO", "11%", "cut 4% extra", "peppermint menthol vs menthone", "tt_op", "rc_tt", "cn_tt", 13),
    A("peppermint-menthol-vs-menthone", "peppermint", "menthol", "38%", "48%", "47.4%", "5 K", "menthone", "rectify +4%", 8, 1, "still", "piperita", "32%", "cut 4% extra", "spearmint carvone vs limonene", "pm_op", "rc_pm", "mn_lab", 12),
    A("spearmint-carvone-vs-limonene", "spearmint", "carvone", "55%", "65%", "64.4%", "5 K", "limonene", "rectify +4%", 8, 1, "still", "spicata", "48%", "cut 4% extra", "basil estragole vs linalool", "sm_op", "rc_sm", "cv_lab", 11),
    A("basil-estragole-vs-linalool", "basil", "estragole", "42%", "18%", "18.4%", "4 K", "estragole", "linalool-chem +4%", 8, 1, "still", "linalool", "55%", "cut 4% extra", "thyme thymol vs carvacrol", "bs_op", "ln_bs", "es_lab", 10),
    A("thyme-thymol-vs-carvacrol", "thyme", "thymol", "38%", "48%", "47.4%", "5 K", "carvacrol", "rectify +4%", 8, 1, "still", "vulgaris", "32%", "cut 4% extra", "oregano carvacrol vs thymol", "th_op", "rc_th", "ty_lab", 9),
    A("oregano-carvacrol-vs-thymol", "oregano", "carvacrol", "55%", "70%", "69.2%", "5 K", "thymol", "rectify +4%", 8, 1, "still", "compactum", "48%", "cut 4% extra", "rosemary cineole vs camphor", "og_op", "rc_og", "cv_og", 8),
    A("rosemary-cineole-vs-camphor", "rosemary", "camphor", "18%", "8%", "8.2%", "5 K", "camphor", "rectify +4%", 8, 1, "still", "cineole", "24%", "cut 4% extra", "sage thujone vs cineole", "rm_op", "rc_rm", "cm_rm", 7),
    A("sage-thujone-vs-cineole", "sage", "thujone", "28%", "8%", "8.2%", "5 K", "thujone", "rectify +4%", 8, 1, "still", "officinalis", "36%", "cut 4% extra", "marjoram terpinen vs linalool", "sg_op", "rc_sg", "thj_lab", 6),
    A("marjoram-terpinen-vs-linalool", "marjoram", "terpinen-4-ol", "18%", "28%", "27.6%", "4 K", "weak", "rectify +4%", 8, 1, "still", "sweet", "14%", "cut 4% extra", "vanilla next densify", "mj_op", "rc_mj", "t4_lab", 5),
]


def self_check() -> None:
    slugs = [s["slug"] for s in SCENARIOS]
    if len(slugs) != len(set(slugs)):
        raise SystemExit("dup slugs")
    for s in SCENARIOS:
        if any(b in s["slug"] for b in BANNED_SUB):
            raise SystemExit(s["slug"])
        rec = build_record(3905, s)
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
