#!/usr/bin/env python3
"""MAC mill from r3205. Ban r3033 capro-oxime, whiskey-barrel, hearts-vs-tails.

Loop frontier → reserve --expected 1 → stage → publish → next.
If MAC reserved, hop SIR r72+ / SSL r132+ (never sandbox-refusal if reserved/writing).
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from importlib.machinery import SourceFileLoader
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
sys.path.insert(0, str(REPO / "pipelines"))
import round_txn  # noqa: E402

_base = SourceFileLoader("mac3034b", str(REPO / "experiments/mac-mill-r3034.py")).load_module()
P = _base.P
T = _base.T
add_turns = _base.add_turns
cut_turns = _base.cut_turns
build_record = _base.build_record
notes_text = _base.notes_text
busy = _base.busy

AGENTIC = REPO / "outputs/raw/2026-08-19-agentic"
FACTORY = AGENTIC / "multi-agent-coordination-factory"
SIR = AGENTIC / "search-index-rebuild-factory"
SSL = AGENTIC / "ssl-cert-rotation-factory"
SBOX = AGENTIC / "sandbox-refusal-factory"
SIR_MILL = REPO / "experiments/sir-mill-r72.py"
SSL_MILL = REPO / "experiments/ssl-mill-r132.py"
DEADLINE_S = 6 * 60 * 60
BANNED_SUB = ("capro-oxime-vs-beckmann", "whiskey-barrel", "hearts-vs-tails", "whiskey")


def A(slug, process, metric, now, spec, legal, spike, bad, add, mins, hold_n, hold, divert, fail, residual, dens, op, eng, lab, novel):
    return P(
        slug,
        f"Hold {process} after {metric} slips without a {spike} spike or a {spec} fail.",
        [
            {"role": op, "mandate": f"{metric} is {now}; spec {spec}; I will not spike {spike}"},
            {"role": eng, "mandate": f"I can add {add} in {mins} min; I will not slug double"},
            {"role": lab, "mandate": f"I will hold {hold_n} {hold}; I will not certify {now} as {spec}"},
        ],
        add_turns(op, eng, lab, spike, add, mins, bad, metric, legal, hold_n, hold, divert, fail, residual,
                  f"Plan is {add.replace(' ', '-').replace('%','pct')}-plus-hold, not {spike.replace(' ','')}-spike and not double-slug."),
        [f"Op {spike}-spike vs {add} vs lab hold-not-{now}"],
        f"Add {add} in {mins} min; hold {hold_n} {hold}; spike only at {fail}; no double slug.",
        f"{metric} {legal}. Residual: {hold} 1 {divert}, {residual}.",
        novel,
        dens,
    )


SCENARIOS = [
    A("maleic-butane-vs-conv", "maleic anhydride", "conv", "78%", "84%", "83.4%", "14 K", "CO2", "butane +4%", 10, 1, "oxidate tank", "recycle", "74%", "butane 5 t extra", "PHA o-xylene vs PA", "ma_op", "c4_ma", "ma_lab", 88),
    A("pha-o-xylene-vs-pa", "phthalic anhydride", "PA purity", "99.1%", "99.6%", "99.55%", "16 K", "tar", "o-xylene +3%", 12, 1, "PA tank", "alkyd", "98.8%", "o-xylene 4 t extra", "acetic methanol vs water", "pa_op", "ox_pa", "pa_lab", 87),
    A("acetic-methanol-vs-water", "acetic acid", "water", "0.42%", "0.15%", "0.14%", "18 K", "formates", "methanol +5%", 11, 1, "AA tank", "vinyl", "0.55%", "MeOH 3 t extra", "VAA acetic vs EO", "aa2_op", "meoh_aa", "h2o_aa", 86),
    A("vaa-acetic-vs-eo", "vinyl acetate", "acetic leftover", "0.55%", "0.20%", "0.18%", "12 K", "polymer", "acetic +4%", 9, 1, "VAM tank", "emulsion", "0.70%", "acetic 2 t extra", "PTA 4CBA vs H2", "vam_op", "hoac_vam", "vam_lab", 85),
    A("pta-4cba-vs-h2", "PTA", "4-CBA", "38 ppm", "25 ppm", "24 ppm", "10 K", "color", "H2 +6%", 14, 1, "PTA silo", "fiber", "50 ppm", "H2 0.3 bar extra", "IPA acid vs MX", "pta_op", "h2_pta", "cba_lab", 84),
    A("ipa-acid-vs-mx", "isophthalic acid", "acid number", "8.4", "4.0", "3.9", "11 K", "sublimate", "m-xylene +3%", 13, 1, "IPA hopper", "coating", "10", "MX 2 t extra", "GBL BDO vs water", "ipa2_op", "mx_ipa", "an_lab", 83),
    A("gbl-bdo-vs-water", "GBL", "water", "380 ppm", "150 ppm", "140 ppm", "13 K", "open-ring", "BDO +3%", 12, 1, "GBL tank", "NMP", "500 ppm", "BDO 1.5 t extra", "NMP GBL vs color", "gbl_op", "bdo_gbl", "h2o_gbl", 82),
    A("nmp-gbl-vs-color", "NMP", "APHA", "28", "15", "14", "15 K", "tar", "GBL +4%", 10, 1, "NMP tank", "electronics-reject", "40", "GBL 2 t extra", "DMF amine vs water", "nmp_op", "gbl_nmp", "apha_nmp", 81),
    A("dmf-amine-vs-water", "DMF", "water", "0.22%", "0.08%", "0.07%", "12 K", "amine", "dimethylamine +3%", 9, 1, "DMF tank", "solvent", "0.30%", "DMA 0.8 t extra", "DMSO DMS vs odor", "dmf_op", "dma_dmf", "h2o_dmf", 80),
    A("dmso-dms-vs-odor", "DMSO", "DMS", "18 ppm", "5 ppm", "4.5 ppm", "14 K", "odor", "air +5%", 11, 1, "DMSO tank", "tech", "25 ppm", "air 4% extra", "formalin MeOH vs CH2O", "dmso_op", "air_dmso", "dms_lab", 79),
    A("formalin-meoh-vs-ch2o", "formalin", "CH2O", "36.2%", "37.0%", "36.95%", "8 K", "formic", "MeOH +2%", 8, 1, "formalin tank", "resin", "35.5%", "MeOH 1 t extra", "AN propene vs HCN", "form_op", "meoh_form", "ch2o_lab", 78),
    A("an-propene-vs-hcn", "acrylonitrile", "HCN leftover", "22 ppm", "8 ppm", "7.5 ppm", "16 K", "COx", "propene +3%", 10, 1, "AN tank", "ABS", "30 ppm", "propene 4 t extra", "HCN Andrussow vs NH3", "an2_op", "c3_an", "hcn_lab", 77),
    A("hcn-andrussow-vs-nh3", "HCN", "NH3 leftover", "1.4%", "0.4%", "0.38%", "20 K", "NOx", "air +4%", 7, 1, "HCN absorber", "NaCN", "1.8%", "air 3% extra", "oxo butyral vs Rh", "hcn_op", "air_hcn", "nh3_hcn", 76),
    A("oxo-butyral-vs-rh", "butyraldehyde", "n/iso", "4.2", "8.0", "7.8", "9 K", "heavies", "H2 +5%", 12, 1, "oxo tank", "2EH", "3.5", "H2 0.2 bar extra", "2EH butyral vs H2", "oxo_op", "h2_oxo", "ni_lab", 75),
    A("eh-butyral-vs-h2", "2-ethylhexanol", "butyral leftover", "0.62%", "0.20%", "0.18%", "11 K", "C8-aldol", "H2 +6%", 13, 1, "2EH tank", "plasticizer", "0.80%", "H2 0.3 bar extra", "NEG IBA vs formalin", "eh_op", "h2_eh", "bal_lab", 74),
    A("neg-iba-vs-formalin", "neopentyl glycol", "OH#", "820", "860", "855", "10 K", "formals", "IBA +3%", 14, 1, "NPG hopper", "powder-coat", "800", "IBA 1.2 t extra", "TMP formalin vs OH", "npg_op", "iba_npg", "oh_npg", 73),
    A("tmp-formalin-vs-oh", "TMP", "OH#", "1220", "1255", "1250", "9 K", "acetals", "formalin +4%", 11, 1, "TMP hopper", "alkyd", "1200", "formalin 0.8 t extra", "PE acetaldehyde vs OH", "tmp_op", "form_tmp", "oh_tmp", 72),
    A("pe-acetaldehyde-vs-oh", "pentaerythritol", "OH#", "1540", "1565", "1562", "8 K", "dipenta", "acetaldehyde +3%", 12, 1, "PE hopper", "explosive-grade-hold", "1520", "AA 0.6 t extra", "LAB benzene vs chain", "pe_op", "aa_pe", "oh_pe", 71),
    A("lab-benzene-vs-chain", "LAB", "2-phenyl", "18%", "15%", "15.2%", "7 K", "heavies", "benzene +4%", 10, 1, "LAB tank", "sulfonate", "20%", "benzene 3 t extra", "SO3 sulfonate vs color", "lab_op", "bz_lab", "ph_lab", 70),
    A("so3-sulfonate-vs-color", "LAS", "Klett", "42", "20", "19", "6 K", "dioxane", "SO3 +2%", 6, 1, "LAS tank", "household", "55", "SO3 0.4 t extra", "EG EO vs water", "las_op", "so3_las", "klett_lab", 69),
    A("eg-eo-vs-water", "ethylene glycol", "water", "0.18%", "0.08%", "0.07%", "12 K", "DEG", "EO +3%", 9, 1, "EG tank", "antifreeze", "0.25%", "EO 2 t extra", "DEG water vs color", "eg_op", "eo_eg", "h2o_eg", 68),
    A("deg-water-vs-color", "DEG", "APHA", "22", "10", "9", "11 K", "TEG", "water-cut 4%", 10, 1, "DEG tank", "brake", "30", "steam 1 t extra", "PO CHP vs EB", "deg_op", "h2o_deg", "apha_deg", 67),
    A("po-chp-vs-eb", "propylene oxide", "EB leftover", "0.35%", "0.10%", "0.09%", "8 K", "phenol", "CHP +3%", 8, 1, "PO tank", "PG", "0.45%", "CHP 1.5 t extra", "PG water vs color", "po_op", "chp_po", "eb_lab", 66),
    A("pg-water-vs-color", "propylene glycol", "water", "0.16%", "0.05%", "0.045%", "10 K", "DPG", "H2 +5%", 11, 1, "PG tank", "USP-hold", "0.22%", "H2 0.2 bar extra", "LAO ethylene vs alpha", "pg_op", "h2_pg", "h2o_pg", 65),
    A("lao-ethylene-vs-alpha", "LAO", "alpha", "91%", "94%", "93.8%", "9 K", "vinylidene", "ethylene +4%", 12, 1, "C8 tank", "PAO", "88%", "C2 3 t extra", "PAO LAO vs KV", "lao_op", "c2_lao", "al_lab", 64),
    A("pao-lao-vs-kv", "PAO-4", "KV100", "3.72", "3.90", "3.88", "14 K", "heavies", "C10 +3%", 15, 1, "PAO tank", "blendstock", "3.50", "C10 2 t extra", "PIB isobutene vs MV", "pao_op", "c10_pao", "kv_lab", 63),
    A("pib-isobutene-vs-mv", "PIB", "Mv", "920", "1200", "1180", "7 K", "lights", "isobutene +5%", 13, 1, "PIB tank", "two-stroke", "800", "iC4 3 t extra", "Claus H2S vs recovery", "pib_op", "ic4_pib", "mv_lab", 62),
    A("claus-h2s-vs-recovery", "Claus", "recovery", "94.2%", "97.0%", "96.8%", "25 K", "COS", "air +4%", 8, 1, "sulfur pit", "block", "93.0%", "air 3% extra", "SRU tail SO2 vs incin", "cl_op", "air_cl", "rec_lab", 61),
    A("srutail-so2-vs-incin", "TGTU", "SO2", "180 ppm", "80 ppm", "75 ppm", "18 K", "COS", "H2 +5%", 9, 1, "tail gas", "incin-credit", "250 ppm", "H2 2% extra", "DAP ammonia vs N", "tgt_op", "h2_tgt", "so2_tgt", 60),
    A("dap-ammonia-vs-n", "DAP", "N", "17.4%", "18.0%", "17.95%", "12 K", "fume", "NH3 +3%", 7, 1, "DAP silo", "blend", "17.0%", "NH3 1 t extra", "MAP P2O5 vs citrate", "dap_op", "nh3_dap", "n_lab", 59),
    A("map-p2o5-vs-citrate", "MAP", "citrate P2O5", "51.2%", "52.0%", "51.9%", "11 K", "insol", "H3PO4 +3%", 8, 1, "MAP silo", "feed", "50.5%", "acid 2 t extra", "phosphoric HF vs P2O5", "map_op", "p_map", "cit_lab", 58),
    A("phosphoric-hf-vs-p2o5", "WPA", "HF", "1.15%", "0.60%", "0.58%", "9 K", "SiF4", "silica +4%", 10, 1, "WPA tank", "merchant", "1.40%", "silica 0.8 t extra", "oleum free SO3 vs H2SO4", "wpa_op", "si_wpa", "hf_lab", 57),
    A("oleum-free-so3-vs-h2so4", "oleum", "free SO3", "24.2%", "25.0%", "24.9%", "15 K", "fume", "SO3 +3%", 8, 1, "oleum tank", "sulfonation", "23.0%", "SO3 1 t extra", "HFC HF vs isomer", "ol_op", "so3_ol", "so3_lab", 56),
    A("hfc-hf-vs-isomer", "HFC-134a", "isomer", "0.42%", "0.10%", "0.09%", "12 K", "olefin", "HF +3%", 11, 1, "HFC tank", "blend", "0.55%", "HF 0.5 t extra", "HFO isomer vs GC", "hfc_op", "hf_hfc", "iso_lab", 55),
    A("hfo-isomer-vs-gc", "HFO-1234yf", "E/Z", "3.8%", "1.0%", "0.9%", "10 K", "HFP", "catalyst +4%", 14, 1, "HFO tank", "auto", "5.0%", "cat 8 kg extra", "PVDF VDF vs HFP", "hfo_op", "cat_hfo", "ez_lab", 54),
    A("pvdf-vdf-vs-hfp", "PVDF", "HFP", "4.2%", "6.0%", "5.9%", "8 K", "gel", "HFP +0.5%", 15, 1, "PVDF silo", "pipe", "3.5%", "HFP 0.6 t extra", "ETFE TFE vs E", "pvdf_op", "hfp_pvdf", "hfp_lab", 53),
    A("etfe-tfe-vs-e", "ETFE", "TFE", "48%", "50%", "49.8%", "9 K", "block", "TFE +2%", 12, 1, "ETFE silo", "wire", "46%", "TFE 0.8 t extra", "FEP HFP vs MFR", "etfe_op", "tfe_etfe", "tfe_lab", 52),
    A("fep-hfp-vs-mfr", "FEP", "MFR", "6.2", "7.0", "6.95", "11 K", "gels", "HFP +0.4%", 16, 1, "FEP silo", "tubing", "5.5", "HFP 0.5 t extra", "PFA PPVE vs MFR", "fep_op", "hfp_fep", "mfr_fep", 51),
    A("pfa-ppve-vs-mfr", "PFA", "MFR", "1.8", "2.2", "2.15", "10 K", "gels", "PPVE +0.3%", 18, 1, "PFA silo", "liner", "1.5", "PPVE 80 kg extra", "PEEK DFBP vs IV", "pfa_op", "ppve_pfa", "mfr_pfa", 50),
    A("peek-dfbp-vs-iv", "PEEK", "IV", "0.82", "0.90", "0.89", "15 K", "color", "DFBP +2%", 20, 1, "PEEK hopper", "compound", "0.78", "DFBP 40 kg extra", "PPS NaCl vs melt", "peek_op", "dfbp_peek", "iv_peek", 49),
    A("pps-nacl-vs-melt", "PPS", "NaCl", "820 ppm", "400 ppm", "380 ppm", "12 K", "ash", "wash +8%", 14, 1, "PPS hopper", "filter", "1000 ppm", "water 3 m3 extra", "PES DCDPS vs color", "pps_op", "wash_pps", "nacl_lab", 48),
    A("pes-dcdps-vs-color", "PES", "YI", "8.4", "4.0", "3.8", "13 K", "gel", "DCDPS +2%", 16, 1, "PES hopper", "membrane", "10", "DCDPS 30 kg extra", "PSU color vs MW", "pes_op", "dcdps_pes", "yi_lab", 47),
    A("psu-color-vs-mw", "PSU", "Mw", "48k", "52k", "51.5k", "12 K", "branch", "DCDPS +1.5%", 15, 1, "PSU hopper", "medical-hold", "45k", "DCDPS 20 kg extra", "LCP acetate vs IV", "psu_op", "dcdps_psu", "mw_psu", 46),
    A("lcp-acetate-vs-iv", "LCP", "IV", "5.8", "6.4", "6.35", "14 K", "gas", "acetate +3%", 18, 1, "LCP hopper", "connector", "5.4", "acetate 15 kg extra", "PI PMDA vs IV", "lcp_op", "ac_lcp", "iv_lcp", 45),
    A("pi-pmda-vs-iv", "PI", "IV", "0.62", "0.72", "0.71", "11 K", "gel", "PMDA +2%", 17, 1, "PI dope", "film", "0.55", "PMDA 12 kg extra", "PEN NDC vs IV", "pi_op", "pmda_pi", "iv_pi", 44),
    A("pen-ndc-vs-iv", "PEN", "IV", "0.58", "0.64", "0.635", "13 K", "DEG", "NDC +2%", 16, 1, "PEN silo", "film", "0.52", "NDC 0.8 t extra", "PTT PDO vs IV", "pen_op", "ndc_pen", "iv_pen", 43),
    A("ptt-pdo-vs-iv", "PTT", "IV", "0.84", "0.92", "0.91", "12 K", "cyclic", "PDO +3%", 14, 1, "PTT silo", "carpet", "0.78", "PDO 1 t extra", "PLA lactide vs MW", "ptt_op", "pdo_ptt", "iv_ptt", 42),
    A("pla-lactide-vs-mw", "PLA", "Mw", "92k", "110k", "108k", "10 K", "racemize", "lactide +3%", 15, 1, "PLA silo", "fiber", "80k", "lactide 0.6 t extra", "PBAT adipate vs MFR", "pla_op", "lac_pla", "mw_pla", 41),
    A("pbat-adipate-vs-mfr", "PBAT", "MFR", "8.4", "5.0", "5.2", "11 K", "acid", "adipate +3%", 13, 1, "PBAT silo", "film-compost", "10", "adipate 0.7 t extra", "PBS succinic vs IV", "pbat_op", "ad_pbat", "mfr_pbat", 40),
    A("pbs-succinic-vs-iv", "PBS", "IV", "1.05", "1.20", "1.18", "12 K", "acid", "succinic +3%", 14, 1, "PBS silo", "injection", "0.95", "SA 0.5 t extra", "TPU NCO vs hard", "pbs_op", "sa_pbs", "iv_pbs", 39),
    A("tpu-nco-vs-hard", "TPU", "NCO", "2.05%", "2.40%", "2.38%", "8 K", "gel", "MDI +3%", 7, 1, "TPU lot", "soft-grade", "1.85%", "MDI 80 kg extra", "SEBS oil vs hard", "tpu_op", "mdi_tpu", "nco_tpu", 38),
    A("sebs-oil-vs-hard", "SEBS", "Shore A", "52", "65", "64", "6 K", "oil-bleed", "oil-cut 4%", 10, 1, "SEBS bale", "grip", "48", "oil 0.4 t held", "TPO flex vs MFR", "sebs_op", "oil_sebs", "sh_lab", 37),
    A("tpo-flex-vs-mfr", "TPO", "flex", "980 MPa", "850 MPa", "860 MPa", "9 K", "bloom", "EPR +3%", 11, 1, "TPO silo", "bumper", "1100", "EPR 1 t extra", "TPV cure vs compress", "tpo_op", "epr_tpo", "flex_lab", 36),
    A("tpv-cure-vs-compress", "TPV", "compression set", "42%", "28%", "29%", "8 K", "scorch", "phenol-resin +3%", 12, 1, "TPV lot", "seal", "48%", "resin 40 kg extra", "EAA AA vs melt", "tpv_op", "res_tpv", "cs_lab", 35),
    A("eaa-aa-vs-melt", "EAA", "AA", "6.8%", "8.0%", "7.9%", "13 K", "gel", "AA +0.6%", 12, 1, "EAA silo", "tie-layer", "6.2%", "AA 0.5 t extra", "EMAA MAA vs melt", "eaa_op", "aa_eaa", "aa_lab", 34),
    A("emaa-maa-vs-melt", "EMAA", "MAA", "8.4%", "9.5%", "9.4%", "12 K", "gel", "MAA +0.5%", 11, 1, "EMAA silo", "coating", "7.8%", "MAA 0.4 t extra", "EVOH VOH vs OTR", "emaa_op", "maa_emaa", "maa_lab", 33),
    A("evoh-voh-vs-otr", "EVOH", "OTR", "1.8", "0.8", "0.82", "10 K", "gels", "sapon +4%", 16, 1, "EVOH silo", "tray", "2.2", "NaOH 0.3 t extra", "PVA hydrolysis vs visc", "evoh_op", "sap_evoh", "otr_lab", 32),
    A("pva-hydrolysis-vs-visc", "PVA", "DH", "86%", "88%", "87.8%", "9 K", "insol", "MeOH +4%", 13, 1, "PVA hopper", "adhesive", "84%", "MeOH 1 t extra", "PVP K-value vs residual", "pva_op", "meoh_pva", "dh_lab", 31),
    A("pvp-kvalue-vs-residual", "PVP", "K-value", "28", "30", "29.8", "8 K", "perox", "initiator +5%", 14, 1, "PVP lot", "pharma-hold", "26", "AIBN 4 kg extra", "SAN AN vs Vicat", "pvp_op", "init_pvp", "k_pvp", 30),
    A("san-an-vs-vicat", "SAN", "AN", "23.8%", "25.0%", "24.9%", "9 K", "yellow", "AN +0.6%", 10, 1, "SAN silo", "blend", "23.0%", "AN 0.8 t extra", "ASA acrylic vs weather", "san_op", "an_san", "an_lab", 29),
    A("asa-acrylic-vs-weather", "ASA", "delta E", "2.4", "1.0", "0.95", "10 K", "chalk", "ASA-graft +3%", 12, 1, "ASA silo", "siding", "3.0", "graft 0.6 t extra", "HIPS PBD vs impact", "asa_op", "graft_asa", "de_lab", 28),
    A("hips-pbd-vs-impact", "HIPS", "Izod", "78", "95", "93", "8 K", "gel", "PBD +0.8%", 11, 1, "HIPS silo", "sheet", "70", "PBD 0.5 t extra", "GPPS residual vs VCM", "hips_op", "pbd_hips", "iz_lab", 27),
    A("gpps-residual-vs-vcm", "GPPS", "residual SM", "420 ppm", "200 ppm", "190 ppm", "12 K", "yellow", "vacuum +6%", 9, 1, "GPPS silo", "foam", "550 ppm", "vacuum 4% extra", "EPS pentane vs density", "gpps_op", "vac_gpps", "sm_lab", 26),
    A("eps-pentane-vs-density", "EPS", "pentane", "4.8%", "6.0%", "5.9%", "7 K", "bead-weld", "pentane +0.8%", 8, 1, "EPS silo", "block", "4.2%", "pentane 0.4 t extra", "XPS HFC vs k-factor", "eps_op", "c5_eps", "c5_lab", 25),
    A("xps-hfc-vs-kfactor", "XPS", "k-factor", "0.032", "0.028", "0.0282", "9 K", "voids", "HFC +4%", 7, 1, "XPS board", "cavity", "0.034", "HFC 80 kg extra", "PIR index vs friability", "xps_op", "hfc_xps", "k_lab", 24),
    A("pir-index-vs-friability", "PIR", "index", "240", "270", "268", "8 K", "friable", "pMDI +4%", 5, 1, "PIR bun", "board-scrap", "220", "pMDI 60 kg extra", "MF melamine vs free", "pir_op", "pmdi_pir", "idx_pir", 23),
    A("mf-melamine-vs-free", "MF resin", "free-F", "0.55%", "0.20%", "0.18%", "11 K", "gel", "melamine +4%", 9, 1, "MF tank", "laminate", "0.70%", "melamine 0.5 t extra", "MUF emission vs IF", "mf_op", "mel_mf", "ff_mf", 22),
    A("muf-emission-vs-if", "MUF", "IF", "0.14 ppm", "0.05 ppm", "0.048 ppm", "10 K", "gel", "urea +4%", 8, 1, "MUF tank", "interior", "0.18 ppm", "urea 0.4 t extra", "UPR gel vs exotherm", "muf_op", "urea_muf", "if_lab", 21),
    A("upr-gel-vs-exotherm", "UPR", "gel time", "6.2 min", "8.0 min", "7.9 min", "7 K", "peak", "inhibitor +3%", 6, 1, "UPR tank", "cast", "5.0 min", "inhibitor 8 kg extra", "alkyd acid vs visc", "upr_op", "inh_upr", "gel_lab", 20),
    A("alkyd-acid-vs-visc", "alkyd", "AV", "14", "8", "8.2", "12 K", "gel", "polyol +3%", 14, 1, "alkyd kettle", "air-dry", "18", "polyol 40 kg extra", "VAE VA vs MFFT", "alk_op", "pol_alk", "av_lab", 19),
    A("vae-va-vs-mfft", "VAE", "MFFT", "8 C", "4 C", "4.2 C", "6 K", "grit", "VA +0.8%", 12, 1, "VAE tank", "adhesive", "10 C", "VA 0.5 t extra", "SBR latex vs solids", "vae_op", "va_vae", "mfft_lab", 18),
    A("sbr-latex-vs-solids", "SBR latex", "solids", "48.2%", "50.0%", "49.8%", "5 K", "grit", "steam-cut 4%", 8, 1, "latex tank", "paper", "47.0%", "steam 1 t extra", "HTV perox vs cure", "sbrl_op", "stm_sbrl", "sol_lab", 17),
    A("htv-perox-vs-cure", "HTV", "t90", "8.4 min", "6.0 min", "6.1 min", "7 K", "scorch", "perox +5%", 9, 1, "HTV lot", "gasket", "10 min", "perox 6 kg extra", "LSR Pt vs pot", "htv_op", "pox_htv", "t90_lab", 16),
    A("lsr-pt-vs-pot", "LSR", "pot life", "22 min", "40 min", "38 min", "5 K", "premature", "inhibitor +4%", 6, 1, "LSR kit", "mold", "15 min", "inhibitor 2 kg extra", "RTV tin vs skin", "lsr_op", "inh_lsr", "pot_lab", 15),
    A("rtv-tin-vs-skin", "RTV", "skin", "18 min", "12 min", "12.5 min", "4 K", "crust", "tin +3%", 5, 1, "RTV pail", "sealant", "25 min", "tin 0.4 kg extra", "fumed silica vs SA", "rtv_op", "tin_rtv", "sk_lab", 14),
    A("fumed-silica-vs-sa", "fumed silica", "SA", "168 m2/g", "200 m2/g", "198 m2/g", "40 K", "sinter", "H2 +6%", 8, 1, "silica hopper", "rTV-fill", "150", "H2 4% extra", "ppt silica vs N2", "fs_op", "h2_fs", "sa_lab", 13),
    A("ppt-silica-vs-n2", "ppt silica", "N2 SA", "142", "165", "163", "12 K", "gel", "acid +4%", 10, 1, "filter cake", "tire", "130", "H2SO4 0.6 t extra", "ZnO SA vs size", "ppt_op", "acid_ppt", "n2_lab", 12),
    A("zno-sa-vs-size", "ZnO", "d50", "0.62 µm", "0.35 µm", "0.36 µm", "20 K", "sinter", "air +5%", 9, 1, "ZnO hopper", "rubber", "0.80", "air 4% extra", "FeO Fe vs shade", "zno_op", "air_zno", "d50_zno", 11),
    A("feo-fe-vs-shade", "iron oxide", "a*", "18.2", "22.0", "21.7", "15 K", "black", "air +6%", 11, 1, "Fe2O3 hopper", "primer", "16", "air 5% extra", "PCN Cu vs strength", "feo_op", "air_feo", "a_lab", 10),
    A("pcn-cu-vs-strength", "CuPc", "strength", "92%", "100%", "99%", "14 K", "bronze", "Cu +3%", 16, 1, "pigment lot", "ink", "88%", "CuCl 20 kg extra", "DINP volatility vs color", "pcn_op", "cu_pcn", "str_lab", 9),
    A("dinp-volatility-vs-color", "DINP", "APHA", "38", "20", "19", "13 K", "heavies", "vacuum +5%", 10, 1, "DINP tank", "floor", "50", "vacuum 3% extra", "TOTM visc vs acid", "dinp_op", "vac_dinp", "apha_dinp", 8),
    A("totm-visc-vs-acid", "TOTM", "AV", "0.18", "0.05", "0.048", "12 K", "color", "steam +4%", 11, 1, "TOTM tank", "cable", "0.25", "steam 0.8 t extra", "epox soy vs oxirane", "totm_op", "stm_totm", "av_totm", 7),
    A("epox-soy-vs-oxirane", "ESO", "oxirane", "6.2%", "6.8%", "6.75%", "9 K", "color", "peracid +4%", 13, 1, "ESO tank", "flex-PVC", "5.8%", "peracid 0.4 t extra", "stearate freeacid vs ash", "eso_op", "pa_eso", "ox_lab", 6),
    A("stearate-freeacid-vs-ash", "Ca-stearate", "FFA", "1.4%", "0.5%", "0.48%", "8 K", "ash", "caustic +5%", 9, 1, "stearate hopper", "PVC-stab", "1.8%", "NaOH 40 kg extra", "transformer BDV vs water", "st_op", "naoh_st", "ffa_lab", 5),
    A("transformer-bdv-vs-water", "transformer oil", "BDV", "38 kV", "50 kV", "49 kV", "10 K", "oxidation", "vac-dry +8%", 20, 1, "oil tank", "reclaim", "32 kV", "vacuum 5% extra", "turbine RBOT vs N2", "tr_op", "vac_tr", "bdv_lab", 4),
    A("turbine-rbot-vs-n2", "turbine oil", "RBOT", "620 min", "800 min", "790 min", "11 K", "sludge", "N2 +6%", 15, 1, "oil tank", "flush", "500 min", "N2 4% extra", "grease NLGI vs oil", "tur_op", "n2_tur", "rbot_lab", 3),
    A("grease-nlgi-vs-oil", "Li grease", "NLGI", "1.4", "2.0", "1.95", "7 K", "oil-bleed", "soap +4%", 12, 1, "grease kettle", "general", "1.1", "soap 30 kg extra", "engine HTHS vs Noack", "gr_op", "soap_gr", "nlgi_lab", 2),
    A("engine-hths-vs-noack", "PCMO", "HTHS", "2.55", "2.90", "2.88", "9 K", "Noack", "VII +3%", 10, 1, "blend tank", "xW-20-hold", "2.40", "VII 80 kg extra", "marine BN vs TBN", "pcmo_op", "vii_pcmo", "hths_lab", 89),
    A("marine-bn-vs-tbn", "cyl oil", "TBN", "58", "70", "69", "8 K", "deposit", "overbase +4%", 11, 1, "cyl tank", "trunk", "50", "overbase 0.5 t extra", "gear FZG vs AW", "mar_op", "ob_mar", "tbn_lab", 88),
    A("gear-fzgs-vs-aw", "gear oil", "FZG", "9", "12", "12", "10 K", "foam", "AW +3%", 9, 1, "gear tank", "industrial", "8", "AW 40 kg extra", "refrigeration floc vs wax", "gear_op", "aw_gear", "fzg_lab", 87),
    A("refrigeration-floc-vs-wax", "POE oil", "floc", "-28 C", "-40 C", "-39 C", "8 K", "wax", "dewax +5%", 14, 1, "POE tank", "R134a", "-22 C", "MEK 0.3 t extra", "quench speed vs flash", "poe_op", "dew_poe", "floc_lab", 86),
    A("quench-speed-vs-flash", "quench oil", "C-speed", "18 s", "12 s", "12.4 s", "12 K", "flash", "cutter +4%", 8, 1, "quench tank", "batch", "22 s", "cutter 0.4 t extra", "maleic next densify", "q_op", "cut_q", "spd_lab", 85),
]


def self_check() -> None:
    slugs = [s["slug"] for s in SCENARIOS]
    if len(slugs) != len(set(slugs)):
        raise SystemExit("duplicate slugs")
    for s in SCENARIOS:
        if any(b in s["slug"].lower() for b in BANNED_SUB):
            raise SystemExit(s["slug"])
        rec = build_record(3205, s)
        if len(rec["transcript"]) < 8 or len(s["agents"]) != 3:
            raise SystemExit(s["slug"])
    print(f"self_check ok: {len(SCENARIOS)} plants", flush=True)


def mill_cli(script: Path, rnd: int, stage: Path) -> None:
    proc = subprocess.run(
        [sys.executable, str(script), "--round", str(rnd), "--staging", str(stage)],
        cwd=REPO, text=True, capture_output=True, check=False,
    )
    sys.stderr.write(proc.stderr or "")
    print(proc.stdout, flush=True)
    if proc.returncode != 0:
        raise RuntimeError(f"{script.name} r{rnd}: {proc.stderr}")


def publish_hop(factory: Path, expected: int, mill: Path, first: int, last: int) -> bool:
    if factory == SBOX and busy(SBOX):
        return False
    if busy(factory):
        return False
    n = round_txn.frontier_status(factory)["next_round"]
    if n < first or n > last:
        print(f"HOP skip {factory.name}: r{n} outside {first}-{last}", flush=True)
        return False
    try:
        reservation = round_txn.reserve(factory, n, expected)
    except (round_txn.TransactionError, FileExistsError, OSError) as exc:
        print(f"HOP reserve fail {factory.name} r{n}: {exc}", flush=True)
        return False
    token = reservation["token"]
    stage = Path(reservation["staging_dir"])
    try:
        mill_cli(mill, n, stage)
        pub = round_txn.publish(factory, n, token)
    except Exception as exc:
        print(f"HOP mill/publish fail {factory.name} r{n}: {exc}", flush=True)
        try:
            round_txn.abort(factory, n, token)
        except round_txn.TransactionError:
            pass
        return False
    print(json.dumps({"hop": factory.name, "round": n, "records": pub.get("records")}), flush=True)
    return True


def try_hop() -> bool:
    if busy(SBOX):
        print("sandbox-refusal reserved/writing; never hop there", flush=True)
    if SIR_MILL.exists() and publish_hop(SIR, 2, SIR_MILL, 72, 91):
        return True
    if SSL_MILL.exists() and publish_hop(SSL, 2, SSL_MILL, 132, 151):
        return True
    return False


def main() -> int:
    self_check()
    published = []
    idx = 0
    start = time.monotonic()
    while time.monotonic() - start < DEADLINE_S:
        status = round_txn.frontier_status(FACTORY)
        n = status["next_round"]
        if busy(FACTORY):
            print(f"MAC r{n} reserved/writing; hopping", flush=True)
            if not try_hop():
                time.sleep(2)
            continue
        if idx >= len(SCENARIOS):
            print(f"MAC catalog exhausted at r{n}; hopping", flush=True)
            if not try_hop():
                time.sleep(3)
                if not busy(FACTORY):
                    print("no hop fuel and MAC free but catalog empty", flush=True)
                    break
            continue
        spec = SCENARIOS[idx]
        idx += 1
        try:
            reservation = round_txn.reserve(FACTORY, n, 1)
        except (round_txn.TransactionError, FileExistsError, OSError) as exc:
            print(f"HOP reserve r{n}: {exc}", flush=True)
            idx -= 1
            if not try_hop():
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
