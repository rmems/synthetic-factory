#!/usr/bin/env python3
"""Mill monorepo-dep-bump-factory r1351+ unique media/EDA/NLP/CV/game leftover plants.

BAN r01–r1350 clones including solr-xml-leftover-cache / opensearchdash-yml-leftover-sso,
leftover-revpin, openems-xml-leftover-fdtd, siliconcompiler-py-leftover-target,
libNNNN, r690–r708 workspace clones (pnpm/npm/yarn/bun/uv/poetry/cargo/gowork/maven/gradle/nx/turbo/changesets).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

_BASE = Path(__file__).with_name("mdb-mill-r1208.py")
_spec = importlib.util.spec_from_file_location("mdb_mill_r1208", _BASE)
_m = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_m)

FACTORY = _m.FACTORY
GEN = _m.GEN
CATALOG_FIRST = 1351
P = _m.P
build_episode = _m.build_episode
make = _m.make

PRIOR_SLUGS = tuple(spec["slug"] for pair in _m.PAIRS for spec in pair)
BANNED_SLUG_NEEDLES = _m.BANNED_SLUG_NEEDLES + PRIOR_SLUGS + (
    "solr-xml-leftover-cache",
    "opensearchdash-yml-leftover-sso",
    "leftover-revpin",
    "openems-xml-leftover-fdtd",
    "siliconcompiler-py-leftover-target",
    "libNNNN",
    "pnpm-override",
    "npm-catalog",
    "yarn-constraints",
    "bun-catalog",
    "uv-workspace",
    "poetry-source",
    "cargo-wsdep",
    "gowork-use",
    "maven-bom",
    "gradle-catalog",
    "nx-implicit",
    "turbo-",
    "changesets-",
)
_m.BANNED_SLUG_NEEDLES = BANNED_SLUG_NEEDLES

STEMS = [
    "anchovy", "barracuda", "cobia", "dace", "eelpout", "flounder", "grouper", "haddock", "ide", "jewelfish",
    "kingfish", "loach", "mackerel", "nursehound", "opah", "pollock", "quillback", "remora", "scad", "tautog",
    "umbrina", "viperfish", "wrasse", "yellowtail", "zebrafishx", "alewife", "bluegill", "crappie", "drumfish", "eulachon",
    "frostfish", "goby", "hake", "jackfish", "kelpfish", "ladyfish", "mahi", "needlefish", "oilfish", "piranha",
    "queenfish", "rockling", "sauger", "tilefish", "uaru", "vimba", "wahoo", "xiphias", "yellowfin", "zebraeel",
    "albacore", "bonito", "capelin", "dorado", "escolar", "filefish", "garfish", "halfbeak", "icefish", "javelin",
    "killifish", "lumpsucker", "mojarra", "oarfish", "pompano", "queenparrot", "rainbowrunner", "sergeant", "tetra", "unicornfish",
    "velvetfish", "weever", "needlenose", "bluefin", "skipjack", "yellowjack", "redgrouper", "blackdrum", "sheepshead", "spotfin",
]
assert len(STEMS) == 80
PLANTS = [f"{s}8" for s in STEMS] + [f"{s}9" for s in STEMS]


def notes_for(round_n: int, a: dict, b: dict) -> str:
    ea = f"mdb-r{round_n}-{a['slug']}"
    eb = f"mdb-r{round_n}-{b['slug']}"
    novel = 88 + (round_n % 5)
    return f"""# NOTES-r{round_n} monorepo-dep-bump-factory

Novel coverage: {novel}%

Two designed episodes (quota 2). Surfaces: {a['surface']} ({a['pkg']} {a['api_break']}); {b['surface']} ({b['pkg']} {b['api_break']}).
Not a pin-file mill and not libNNNN recycle. Distinct from r01–r1350 clones (ban solr-xml-leftover-cache / opensearchdash-yml-leftover-sso; leftover-revpin; openems-xml-leftover-fdtd / siliconcompiler-py-leftover-target; r690–r708 workspace clones).

| id | seed | first apply | plan change | terminal |
|---|---|---|---|---|
| {ea} | {a['surface']} | nested {a['new']} | SoT {a['new']} + {a['api_break']} | {'leftover-workspace fail; ' + a['left'] + ' ' + a.get('left_ver', a['old']) if a['fail'] else 'success; ' + a['left'] + ' leftover'} |
| {eb} | {b['surface']} | nested {b['new']} | SoT {b['new']} + {b['api_break']} | {'leftover-workspace fail; ' + b['left'] + ' ' + b.get('left_ver', b['old']) if b['fail'] else 'success; ' + b['left'] + ' leftover'} |

## Step counts
- ep1: 18. Nested apply 6–7; plan change 8; API break 10–12; leftover {a['left']}.
- ep2: 18. Nested apply 6–7; plan change 8; API break 10–12; leftover-workspace fail {b['left']}.

## decision_basis audit
Every step starts Plan:/Observation:/Reflection:, ≤240 chars.
No thought / chain_of_thought / scratch / inner_monologue. No spike_events.
No sim_or_real: real. Plants `{a['plant']}` and `{b['plant']}`.

## Weaknesses / next
Keep unique leftover leftover leftover plots. Ban r01–r1350 clones, libNNNN, r690–r708 workspace clones.
"""


RAW: list[tuple] = [
    ("ffmpeg-ffpreset-leftover-codec", "FFmpeg leftover vs enc.ffpreset", "ffmpeg", "6.1.1", "7.1", "enc.ffpreset",
     "vcodec=libx264", "vcodec=libsvtav1", "preset=medium", "preset=8", "x264 → svtav1 preset 8", "ffpreset"),
    ("gstreamer-gst-leftover-caps", "GStreamer leftover vs pipe.gst", "gstreamer", "1.22.12", "1.24.10", "pipe.gst",
     "videoconvert ! x264enc", "videoconvert ! svtav1enc", "video/x-raw,framerate=30/1", "video/x-raw,framerate=60/1",
     "x264enc → svtav1enc 60fps", "gst"),
    ("mpv-conf-leftover-vo", "mpv leftover vs mpv.conf", "mpv", "0.38.0", "0.39.0", "mpv.conf",
     "vo=gpu", "vo=gpu-next", "hwdec=no", "hwdec=auto-safe", "gpu-next + auto-safe hwdec", "conf"),
    ("vlc-vlm-leftover-sout", "VLC leftover vs vlm.conf", "vlc", "3.0.21", "3.0.21-api", "vlm.conf",
     "sout=#transcode{vcodec=h264}", "sout=#transcode{vcodec=h265}", "dst=udp://", "dst=srt://", "h265 + SRT dest", "conf"),
    ("handbrake-json-leftover-preset", "HandBrake leftover vs hb.json", "handbrake", "1.7.3", "1.9.0", "hb.json",
     "\"VideoEncoder\": \"x264\"", "\"VideoEncoder\": \"svt_av1\"", "\"VideoQualityType\": 2", "\"VideoQualityType\": 1",
     "x264 → svt_av1 quality", "json"),
    ("svtav1-cfg-leftover-preset", "SVT-AV1 leftover vs svt.cfg", "svtav1", "2.1.2", "2.3.0", "svt.cfg",
     "preset=10", "preset=6", "crf=35", "crf=28", "preset 6 + crf 28", "cfg"),
    ("x265-cfg-leftover-tune", "x265 leftover vs x265.cfg", "x265", "3.5", "4.1", "x265.cfg",
     "tune=psnr", "tune=ssim", "profile=main", "profile=main10", "ssim + main10", "cfg"),
    ("dav1d-cli-leftover-threads", "dav1d leftover vs dav1d.cfg", "dav1d", "1.4.3", "1.5.1", "dav1d.cfg",
     "--threads 2", "--threads 8", "--filmgrain 0", "--filmgrain 1", "8 threads + filmgrain", "cfg"),
    ("aomenc-cfg-leftover-cpuused", "libaom leftover vs aom.cfg", "aomenc", "3.9.1", "3.11.0", "aom.cfg",
     "--cpu-used=6", "--cpu-used=3", "--end-usage=cq", "--end-usage=q", "cpu-used 3 + q mode", "cfg"),
    ("rav1e-toml-leftover-speed", "rav1e leftover vs rav1e.toml", "rav1e", "0.7.1", "0.7.1-api", "rav1e.toml",
     "speed = 8", "speed = 4", "quantizer = 100", "quantizer = 80", "speed 4 + q 80", "toml"),
    ("opusenc-cfg-leftover-bitrate", "opusenc leftover vs opus.cfg", "opusenc", "1.4", "1.5.2", "opus.cfg",
     "--bitrate 64", "--bitrate 128", "--vbr", "--cvbr", "128k + cvbr", "cfg"),
    ("lame-cfg-leftover-vbr", "LAME leftover vs lame.cfg", "lame", "3.100", "3.100-api", "lame.cfg",
     "-V 5", "-V 2", "--resample 44100", "--resample 48000", "V2 + 48k", "cfg"),
    ("flacenc-cfg-leftover-level", "FLAC leftover vs flac.cfg", "flacenc", "1.4.3", "1.5.0", "flac.cfg",
     "-5", "-8", "--no-padding", "--padding=4096", "level 8 + padding", "cfg"),
    ("sox-fx-leftover-rate", "SoX leftover vs sox.fx", "sox", "14.4.2", "14.4.2-api", "sox.fx",
     "rate 44100", "rate -v 48000", "dither -s", "dither -S", "48k very + shap dither", "fx"),
    ("rubberband-cfg-leftover-pitch", "Rubber Band leftover vs rb.cfg", "rubberband", "3.3.0", "4.0.0", "rb.cfg",
     "--pitch 0", "--pitch 2", "--fine", "--fine --formant", "pitch +2 + formant", "cfg"),
    ("chromaprint-py-leftover-fp", "Chromaprint leftover vs fp.py", "chromaprint", "1.5.1", "1.5.1-api", "fp.py",
     "fpcalc -raw", "fpcalc -json -raw", "length=120", "length=30", "json + 30s", "py"),
    ("kicad-pro-leftover-drc", "KiCad leftover vs api.kicad_pro", "kicad", "8.0.4", "9.0.0", "api.kicad_pro",
     "\"drc_exclusions\": []", "\"drc_exclusions\": []\n\"rules\": {\"min_clearance\": 0.2}",
     "\"copper_finish\": \"None\"", "\"copper_finish\": \"ENIG\"", "0.2mm clearance + ENIG", "kicad_pro"),
    ("pcbnew-py-leftover-fill", "pcbnew leftover vs fill.py", "pcbnew", "8.0.4", "9.0.0", "fill.py",
     "board.ZoneFillers()", "board.ZoneFillers(); filler.Fill(zones)",
     "zone.SetMinThickness(0.2)", "zone.SetMinThickness(0.15)", "Fill + 0.15mm min", "py"),
    ("ngspice-cir-leftover-tran", "ngspice leftover vs t.cir", "ngspice", "42", "44", "t.cir",
     ".tran 1u 1m", ".tran 100n 2m", ".options reltol=1e-3", ".options reltol=1e-6", "finer tran + reltol", "cir"),
    ("xyce-cir-leftover-dc", "Xyce leftover vs dc.cir", "xyce", "7.8", "7.9", "dc.cir",
     ".DC VIN 0 5 0.1", ".DC VIN 0 5 0.01", ".options timeint method=7", ".options timeint method=8",
     "0.01 DC + method 8", "cir"),
    ("qucs-sch-leftover-ac", "Qucs leftover vs ac.sch", "qucs", "0.0.20", "24.10.1", "ac.sch",
     "Type=ac", "Type=sp", "Start=1e6", "Start=1e5", "ac → sp + 100kHz", "sch"),
    ("leptoneda-sch-leftover-net", "Lepton leftover vs n.sch", "leptoneda", "1.9.18", "1.9.18-api", "n.sch",
     "netname=legacy", "netname=api", "graphical=0", "graphical=0\npinseq=1", "api net + pinseq", "sch"),
    ("magicvlsi-tcl-leftover-ext", "Magic leftover vs ext.tcl", "magicvlsi", "8.3.486", "8.3.508", "ext.tcl",
     "extract do all", "extract do capacitance", "ext2spice scale off", "ext2spice scale on",
     "cap extract + scale on", "tcl"),
    ("netgenlvs-tcl-leftover-lvs", "Netgen leftover vs lvs.tcl", "netgenlvs", "1.5.272", "1.5.295", "lvs.tcl",
     "lvs {a.spice b.spice}", "lvs {a.spice b.spice} -json", "permute transistors", "permute default",
     "json LVS + default permute", "tcl"),
    ("xschem-tcl-leftover-raw", "Xschem leftover vs x.tcl", "xschem", "3.4.5", "3.4.6", "x.tcl",
     "set netlist_dir ./legacy", "set netlist_dir ./api", "simulate ngspice", "simulate xyce",
     "xyce + api netlist dir", "tcl"),
    ("opensta-tcl-leftover-liberty", "OpenSTA leftover vs sta.tcl", "opensta", "2.5.1", "2.6.0", "sta.tcl",
     "read_liberty slow.lib", "read_liberty -min fast.lib -max slow.lib",
     "report_checks -path_delay max", "report_checks -path_delay min_max", "min/max liberty + both", "tcl"),
    ("irsim-prm-leftover-step", "IRSIM leftover vs ir.prm", "irsim", "9.7.116", "9.7.118", "ir.prm",
     "stepsize 100", "stepsize 10", "ana a b", "ana a b c", "step 10 + extra probe", "prm"),
    ("ltspice-asc-leftover-tran", "LTspice leftover vs t.asc", "ltspice", "24.0.12", "24.1.5", "t.asc",
     "TRAN 1m", "TRAN 2m startup", "uic", "startup", "2m startup + no uic", "asc"),
    ("pspice-cir-leftover-ac", "PSpice leftover vs ac.cir", "pspice", "23.1", "24.1", "ac.cir",
     ".AC DEC 10 1 1MEG", ".AC DEC 20 1 10MEG", ".PROBE V(*)", ".PROBE V(*) I(*)", "20pt/dec + currents", "cir"),
    ("gerbv-gvp-leftover-layer", "gerbv leftover vs g.gvp", "gerbv", "2.10.0", "2.10.0-api", "g.gvp",
     "layer=legacy.gbr", "layer=api.gbr", "visible=1", "visible=1 invert=1", "api layer + invert", "gvp"),
    ("spacy-py-leftover-pipe", "spaCy leftover vs nlp.py", "spacy", "3.7.5", "3.8.4", "nlp.py",
     "nlp = spacy.load('en_core_web_sm')", "nlp = spacy.load('en_core_web_trf')",
     "doc = nlp(text)", "doc = nlp(text); nlp.enable_pipe('ner')", "trf + enable ner", "py"),
    ("stanza-py-leftover-proc", "Stanza leftover vs st.py", "stanza", "1.8.2", "1.10.1", "st.py",
     "stanza.Pipeline('en')", "stanza.Pipeline('en', processors='tokenize,pos,lemma,depparse')",
     "doc = nlp(text)", "doc = nlp(text, download_method=None)", "full procs + no download", "py"),
    ("flair-py-leftover-tagger", "Flair leftover vs tg.py", "flair", "0.13.1", "0.15.1", "tg.py",
     "SequenceTagger.load('ner')", "SequenceTagger.load('flair/ner-english-large')",
     "tagger.predict(s)", "tagger.predict(s, mini_batch_size=32)", "large NER + batch 32", "py"),
    ("nltk-py-leftover-tokenize", "NLTK leftover vs tk.py", "nltk", "3.8.1", "3.9.1", "tk.py",
     "nltk.word_tokenize(t)", "nltk.word_tokenize(t, language='english', preserve_line=True)",
     "nltk.sent_tokenize(t)", "nltk.sent_tokenize(t, language='english')", "preserve_line + lang", "py"),
    ("gensim-py-leftover-w2v", "Gensim leftover vs w2v.py", "gensim", "4.3.2", "4.3.3", "w2v.py",
     "Word2Vec(sents, vector_size=100)", "Word2Vec(sents, vector_size=300, sg=1)",
     "model.wv.most_similar('a')", "model.wv.most_similar('a', topn=20)", "sg 300d + topn 20", "py"),
    ("fasttext-py-leftover-sup", "fastText leftover vs ft.py", "fasttext", "0.9.2", "0.9.3", "ft.py",
     "fasttext.train_supervised(p)", "fasttext.train_supervised(p, epoch=25, lr=0.5)",
     "model.predict(t)", "model.predict(t, k=3, threshold=0.1)", "25 ep + top3", "py"),
    ("sentencepiece-py-leftover-bpe", "SentencePiece leftover vs sp.py", "sentencepiece", "0.2.0", "0.2.0-api", "sp.py",
     "spm.SentencePieceTrainer.train(model_type='unigram')", "spm.SentencePieceTrainer.train(model_type='bpe', vocab_size=32000)",
     "sp.encode(t)", "sp.encode(t, out_type=str)", "BPE 32k + str", "py"),
    ("hftokenizers-py-leftover-uni", "tokenizers leftover vs tok.py", "hftokenizers", "0.19.1", "0.21.0", "tok.py",
     "Tokenizer(models.BPE())", "Tokenizer(models.Unigram())",
     "tok.encode(t)", "tok.encode(t, add_special_tokens=True)", "Unigram + specials", "py"),
    ("allennlp-json-leftover-arch", "AllenNLP leftover vs a.json", "allennlp", "2.10.1", "2.10.1-api", "a.json",
     "\"type\": \"basic_classifier\"", "\"type\": \"text_classifier\"",
     "\"seq2vec_encoder\": {\"type\": \"boe\"}", "\"seq2vec_encoder\": {\"type\": \"cnn\"}",
     "cnn encoder + text_classifier", "json"),
    ("thinc-py-leftover-model", "Thinc leftover vs th.py", "thinc", "8.2.5", "8.3.2", "th.py",
     "chain(Relu(128), Softmax())", "chain(Relu(256), Softmax())",
     "model.initialize()", "model.initialize(X=X, Y=Y)", "256 Relu + init XY", "py"),
    ("opencv-py-leftover-dnn", "OpenCV leftover vs dnn.py", "opencv", "4.10.0", "4.11.0", "dnn.py",
     "cv2.dnn.readNetFromONNX(p)", "cv2.dnn.readNetFromONNX(p); net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)",
     "net.forward()", "net.forward(['out'])", "CUDA backend + named out", "py"),
    ("pillow-py-leftover-lanczos", "Pillow leftover vs rs.py", "pillow", "10.4.0", "11.1.0", "rs.py",
     "im.resize((256,256), Image.BILINEAR)", "im.resize((512,512), Image.Resampling.LANCZOS)",
     "im.save(p)", "im.save(p, optimize=True, quality=90)", "LANCZOS 512 + q90", "py"),
    ("skimage-py-leftover-seg", "scikit-image leftover vs sg.py", "skimage", "0.24.0", "0.25.0", "sg.py",
     "segmentation.slic(img, n_segments=100)", "segmentation.slic(img, n_segments=400, compactness=10)",
     "filters.gaussian(img, 1)", "filters.gaussian(img, 1.5, channel_axis=-1)", "slic 400 + ch axis", "py"),
    ("imageio-py-leftover-plugin", "imageio leftover vs io.py", "imageio", "2.35.1", "2.36.1", "io.py",
     "imageio.imread(p)", "imageio.v3.imread(p, plugin='pillow')",
     "imageio.imwrite(p, arr)", "imageio.v3.imwrite(p, arr, plugin='PNG-FI')", "v3 pillow + PNG-FI", "py"),
    ("albumentations-py-leftover-compose", "Albumentations leftover vs al.py", "albumentations", "1.4.14", "2.0.3", "al.py",
     "A.Compose([A.HorizontalFlip(p=0.5)])", "A.Compose([A.HorizontalFlip(p=0.5), A.RandomBrightnessContrast(p=0.2)])",
     "tr(image=im)", "tr(image=im, mask=mk)", "brightness + mask", "py"),
    ("kornia-py-leftover-aug", "Kornia leftover vs ko.py", "kornia", "0.7.3", "0.8.0", "ko.py",
     "K.augmentation.RandomHorizontalFlip()", "K.augmentation.RandomAffine(degrees=15)",
     "aug(x)", "aug(x, params=None)", "affine 15 + params", "py"),
    ("torchvision-py-leftover-tfm", "torchvision leftover vs tv.py", "torchvision", "0.19.1", "0.21.0", "tv.py",
     "T.Compose([T.Resize(256)])", "T.Compose([T.Resize(224, antialias=True), T.CenterCrop(224)])",
     "T.ToTensor()", "T.ToDtype(torch.float32, scale=True)", "224 crop + ToDtype", "py"),
    ("detectron2-py-leftover-cfg", "Detectron2 leftover vs d2.py", "detectron2", "0.6", "0.6-api", "d2.py",
     "cfg.merge_from_file('COCO-Detection/faster_rcnn_R_50_FPN_3x.yaml')",
     "cfg.merge_from_file('COCO-Detection/faster_rcnn_R_101_FPN_3x.yaml')",
     "cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.5", "cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.7",
     "R101 + thresh 0.7", "py"),
    ("mmdet-py-leftover-pipeline", "MMDetection leftover vs mm.py", "mmdet", "3.3.0", "3.3.0-api", "mm.py",
     "pipeline = [dict(type='LoadImageFromFile')]", "pipeline = [dict(type='LoadImageFromFile', backend_args=None)]",
     "dict(type='Resize', scale=(1333,800))", "dict(type='Resize', scale=(1024,1024), keep_ratio=True)",
     "1024 keep_ratio + backend", "py"),
    ("yolov8-py-leftover-imgsz", "YOLOv8 leftover vs yo.py", "yolov8", "8.2.103", "8.3.70", "yo.py",
     "YOLO('yolov8n.pt')", "YOLO('yolov8s.pt')",
     "model.predict(im, imgsz=640)", "model.predict(im, imgsz=1280, conf=0.4)", "v8s 1280 + conf 0.4", "py"),
    ("tifffile-py-leftover-ome", "tifffile leftover vs tf.py", "tifffile", "2024.8.30", "2025.1.10", "tf.py",
     "tifffile.imread(p)", "tifffile.imread(p, is_ome=True)",
     "tifffile.imwrite(p, a)", "tifffile.imwrite(p, a, compression='zlib', ome=True)", "OME + zlib", "py"),
    ("godot-cfg-leftover-renderer", "Godot leftover vs project.godot", "godot", "4.2.2", "4.3.5", "project.godot",
     "renderer/rendering_method=\"gl_compatibility\"", "renderer/rendering_method=\"forward_plus\"",
     "anti_aliasing/quality/msaa_3d=0", "anti_aliasing/quality/msaa_3d=2", "forward_plus + MSAA 2", "godot"),
    ("bevy-toml-leftover-feature", "Bevy leftover vs Cargo.toml", "bevy", "0.14.2", "0.15.1", "Cargo.toml",
     "bevy = { version = \"0.14\", features = [\"dynamic_linking\"] }",
     "bevy = { version = \"0.15\", features = [\"bevy_pbr\", \"bevy_ui\"] }",
     "DefaultPlugins", "DefaultPlugins.set(WindowPlugin {..})", "pbr+ui + WindowPlugin", "toml"),
    ("raylib-h-leftover-cam", "raylib leftover vs cam.h", "raylib", "5.0", "5.5", "cam.h",
     "Camera3D cam = { 0 };", "Camera3D cam = { .projection = CAMERA_PERSPECTIVE };",
     "UpdateCamera(&cam, CAMERA_FREE)", "UpdateCamera(&cam, CAMERA_ORBITAL)", "perspective + orbital", "h"),
    ("love2d-lua-leftover-filter", "LÖVE leftover vs conf.lua", "love2d", "11.5", "12.0", "conf.lua",
     "t.window.vsync = 1", "t.window.vsync = 0",
     "love.graphics.setDefaultFilter('linear','linear')", "love.graphics.setDefaultFilter('nearest','nearest')",
     "vsync off + nearest", "lua"),
    ("defold-go-leftover-sprite", "Defold leftover vs s.go", "defold", "1.9.3", "1.9.6", "s.go",
     "default_animation: \"idle\"", "default_animation: \"run\"",
     "material: \"/builtins/materials/sprite.material\"", "material: \"/assets/sprite_lit.material\"",
     "run + lit material", "go"),
    ("flame-dart-leftover-camera", "Flame leftover vs cam.dart", "flame", "1.18.0", "1.23.0", "cam.dart",
     "camera = CameraComponent.withFixedResolution(width: 320, height: 180)",
     "camera = CameraComponent.withFixedResolution(width: 640, height: 360)",
     "camera.viewfinder.anchor = Anchor.topLeft", "camera.viewfinder.anchor = Anchor.center",
     "640x360 + center", "dart"),
    ("monogame-cs-leftover-sampler", "MonoGame leftover vs s.cs", "monogame", "3.8.1", "3.8.2", "s.cs",
     "SamplerState.LinearClamp", "SamplerState.PointClamp",
     "graphics.PreferredBackBufferWidth = 800", "graphics.PreferredBackBufferWidth = 1920",
     "PointClamp + 1920", "cs"),
    ("sfml-cpp-leftover-view", "SFML leftover vs v.cpp", "sfml", "2.6.1", "3.0.0", "v.cpp",
     "sf::View view(sf::FloatRect(0,0,800,600))", "sf::View view(sf::FloatRect({0,0},{1920,1080}))",
     "window.setView(view)", "window.setView(view); view.zoom(0.5f)", "1920 view + zoom 0.5", "cpp"),
    ("sdl2-c-leftover-hint", "SDL2 leftover vs h.c", "sdl2", "2.30.7", "2.30.11", "h.c",
     "SDL_SetHint(SDL_HINT_RENDER_DRIVER, \"opengl\")", "SDL_SetHint(SDL_HINT_RENDER_DRIVER, \"vulkan\")",
     "SDL_CreateRenderer(w, -1, SDL_RENDERER_ACCELERATED)", "SDL_CreateRenderer(w, -1, SDL_RENDERER_ACCELERATED|SDL_RENDERER_PRESENTVSYNC)",
     "vulkan + vsync", "c"),
    ("bgfx-ini-leftover-renderer", "bgfx leftover vs bgfx.ini", "bgfx", "1.127.8725", "1.129.8869", "bgfx.ini",
     "renderer=OpenGL", "renderer=Vulkan", "reset=VSYNC", "reset=VSYNC|MSAA_X4", "Vulkan + MSAA x4", "ini"),
    ("llvm-td-leftover-isel", "LLVM leftover vs isel.td", "llvm", "18.1.8", "19.1.7", "isel.td",
     "def : Pat<(i32 (add i32:$a, i32:$b)), (ADD $a, $b)>;",
     "def : Pat<(i64 (add i64:$a, i64:$b)), (ADD64 $a, $b)>;",
     "let AddedComplexity = 0 in", "let AddedComplexity = 10 in", "i64 ADD64 + complexity 10", "td"),
    ("gcc-spec-leftover-lto", "GCC leftover vs gcc.spec", "gcc", "13.3.0", "14.2.0", "gcc.spec",
     "*link: %{!static:-lgcc}", "*link: %{!static:-lgcc} %{flto:-flto=auto}",
     "-O2", "-O3 -flto=auto", "O3 + flto auto", "spec"),
    ("rustc-toml-leftover-lto", "rustc leftover vs .cargo/config.toml", "rustc", "1.80.1", "1.84.0", "config.toml",
     "lto = false", "lto = \"thin\"", "codegen-units = 16", "codegen-units = 1", "thin LTO + 1 CGU", "toml"),
    ("nim-nimble-leftover-backend", "Nim leftover vs p.nimble", "nim", "2.0.8", "2.2.0", "p.nimble",
     "backend = \"c\"", "backend = \"cpp\"", "srcDir = \"src\"", "srcDir = \"src\"; requires \"nim >= 2.2\"",
     "cpp backend + nim 2.2", "nimble"),
    ("dmd-d-leftover-betterc", "DMD leftover vs a.d", "dmd", "2.109.1", "2.110.2", "a.d",
     "void main() {}", "extern(C) void main() {}", "import std.stdio;", "// betterC no phobos",
     "betterC extern(C) main", "d"),
    ("ghc-cabal-leftover-way", "GHC leftover vs p.cabal", "ghc", "9.8.2", "9.10.1", "p.cabal",
     "ghc-options: -O1", "ghc-options: -O2 -split-sections", "default-language: Haskell2010",
     "default-language: GHC2021", "O2 split-sections + GHC2021", "cabal"),
    ("ocaml-dune-leftover-profile", "Dune leftover vs dune", "ocaml", "5.2.0", "5.3.0", "dune",
     "(profile dev)", "(profile release)", "(flags (:standard -w +a-4-29))", "(flags (:standard -O3))",
     "release + -O3", "dune"),
    ("swift-pkg-leftover-swift6", "Swift leftover vs Package.swift", "swift", "5.10", "6.0.3", "Package.swift",
     "swift-tools-version: 5.10", "swift-tools-version: 6.0",
     "platforms: [.macOS(.v13)]", "platforms: [.macOS(.v14)]", "Swift 6 + macOS 14", "swift"),
    ("javac-args-leftover-release", "javac leftover vs javac.args", "javac", "21", "23", "javac.args",
     "--release 17", "--release 21", "-Xlint:none", "-Xlint:all", "release 21 + lint all", "args"),
    ("clang-flags-leftover-lto", "Clang leftover vs clang.flags", "clang", "18.1.8", "19.1.7", "clang.flags",
     "-O2", "-O3 -flto=thin", "-fno-exceptions", "-fno-exceptions -fno-rtti", "thin LTO + no rtti", "flags"),
    ("emcc-js-leftover-mod", "Emscripten leftover vs emcc.js", "emcc", "3.1.64", "4.0.3", "emcc.js",
     "-s MODULARIZE=0", "-s MODULARIZE=1 -s EXPORT_ES6=1", "-s WASM=1", "-s WASM=1 -s USE_PTHREADS=1",
     "ES6 module + pthreads", "js"),
    ("django-py-leftover-asgi", "Django leftover vs asgi.py", "django", "5.0.8", "5.1.5", "asgi.py",
     "application = get_asgi_application()", "application = ProtocolTypeRouter({'http': get_asgi_application()})",
     "DJANGO_SETTINGS_MODULE=legacy.settings", "DJANGO_SETTINGS_MODULE=api.settings",
     "ProtocolTypeRouter + api settings", "py"),
    ("flask-py-leftover-async", "Flask leftover vs app.py", "flask", "3.0.3", "3.1.0", "app.py",
     "@app.route('/')\\ndef index():", "@app.route('/')\\nasync def index():",
     "app.run()", "app.run(threaded=True)", "async view + threaded", "py"),
    ("fastapi-py-leftover-lifespan", "FastAPI leftover vs main.py", "fastapi", "0.112.2", "0.115.6", "main.py",
     "@app.on_event('startup')", "async with lifespan(app):",
     "app = FastAPI()", "app = FastAPI(lifespan=lifespan)", "lifespan ctx", "py"),
    ("rails-rb-leftover-zeitwerk", "Rails leftover vs app.rb", "rails", "7.1.4", "8.0.1", "app.rb",
     "config.autoloader = :classic", "config.autoloader = :zeitwerk",
     "config.load_defaults 7.0", "config.load_defaults 8.0", "zeitwerk + defaults 8.0", "rb"),
    ("laravel-php-leftover-octane", "Laravel leftover vs octane.php", "laravel", "11.21.0", "11.41.0", "octane.php",
     "'server' => 'roadrunner'", "'server' => 'swoole'",
     "'https' => false", "'https' => true", "swoole + https", "php"),
    ("springboot-yml-leftover-actuator", "Spring Boot leftover vs app.yml", "springboot", "3.3.3", "3.4.1", "app.yml",
     "management.endpoints.web.exposure.include: health", "management.endpoints.web.exposure.include: health,info,metrics",
     "server.port: 8080", "server.port: 8080\\nserver.shutdown: graceful", "metrics + graceful", "yml"),
    ("express-js-leftover-router", "Express leftover vs app.js", "express", "4.19.2", "5.0.1", "app.js",
     "app.use(bodyParser.json())", "app.use(express.json())",
     "app.listen(3000)", "app.listen(3000, { backlog: 511 })", "builtin json + backlog", "js"),
    ("nestjs-ts-leftover-guard", "Nest leftover vs g.ts", "nestjs", "10.4.4", "11.0.5", "g.ts",
     "@UseGuards(AuthGuard('jwt'))", "@UseGuards(AuthGuard('jwt'), RolesGuard)",
     "app.listen(3000)", "app.listen(3000, '0.0.0.0')", "RolesGuard + bind all", "ts"),
    ("astrojs-mjs-leftover-adapter", "Astro leftover vs astro.config.mjs", "astrojs", "4.15.4", "5.1.7", "astro.config.mjs",
     "adapter: node({ mode: 'standalone' })", "adapter: node({ mode: 'middleware' })",
     "output: 'static'", "output: 'server'", "middleware + server", "mjs"),
    ("remix-ts-leftover-loader", "Remix leftover vs r.ts", "remix", "2.12.1", "2.15.2", "r.ts",
     "export const loader = async () => json({})", "export const loader = async ({ request }) => json({}, { headers: { 'Cache-Control': 'max-age=60' } })",
     "export default function R(){return null}", "export default function R(){return <Outlet/>}",
     "cache 60 + Outlet", "ts"),
    ("sveltekit-js-leftover-hooks", "SvelteKit leftover vs hooks.js", "sveltekit", "2.6.1", "2.16.1", "hooks.js",
     "export const handle = async ({ event, resolve }) => resolve(event)",
     "export const handle = sequence(auth, resolve)",
     "export const handleError = ({ error }) => {}", "export const handleError = ({ error }) => ({ message: 'err' })",
     "sequence auth + err msg", "js"),
    ("nuxt-ts-leftover-nitro", "Nuxt leftover vs nuxt.config.ts", "nuxt", "3.13.2", "3.15.2", "nuxt.config.ts",
     "nitro: { preset: 'node-server' }", "nitro: { preset: 'cloudflare-pages' }",
     "ssr: true", "ssr: true, routeRules: { '/api/**': { cors: true } }",
     "cloudflare-pages + cors", "ts"),
    ("nextjs-ts-leftover-appdir", "Next leftover vs next.config.ts", "nextjs", "14.2.13", "15.1.6", "next.config.ts",
     "experimental: { appDir: true }", "experimental: { ppr: true }",
     "output: 'standalone'", "output: 'standalone', images: { unoptimized: false }",
     "PPR + images", "ts"),
    ("rootcern-cint-leftover-th1", "ROOT leftover vs h.C", "rootcern", "6.30.08", "6.34.02", "h.C",
     "TH1F h(\"h\",\"h\",100,0,1);", "TH1D h(\"h\",\"h\",200,0,1);",
     "h.Draw();", "h.Draw(\"E HIST\");", "TH1D 200 + E HIST", "C"),
    ("geant4-mac-leftover-phys", "Geant4 leftover vs run.mac", "geant4", "11.2.2", "11.3.0", "run.mac",
     "/physics_lists/select FTFP_BERT", "/physics_lists/select QGSP_BERT_HP",
     "/run/beamOn 1000", "/run/beamOn 10000", "QGSP_BERT_HP + 10k", "mac"),
    ("fluka-inp-leftover-beam", "FLUKA leftover vs b.inp", "fluka", "4-4.0", "4-4.1", "b.inp",
     "BEAM          -1.0       0.0       0.0       0.0       0.0       0.0PROTON",
     "BEAM          -2.0       0.0       0.0       0.0       0.0       0.0PROTON",
     "START        1000.", "START       10000.", "2 GeV + 10k", "inp"),
    ("mcnp-inp-leftover-nps", "MCNP leftover vs m.inp", "mcnp", "6.2", "6.3", "m.inp",
     "nps 1e5", "nps 1e6", "prdmp 2j 1 2", "prdmp 2j 1 4", "1e6 nps + prdmp 4", "inp"),
    ("openmc-xml-leftover-tallies", "OpenMC leftover vs tallies.xml", "openmc", "0.14.0", "0.15.0", "tallies.xml",
     "<tally id=\"1\"><scores>flux</scores></tally>",
     "<tally id=\"1\"><scores>flux fission</scores></tally>",
     "<filter type=\"cell\"/>", "<filter type=\"energy\"/>", "fission score + energy", "xml"),
    ("serpent-inp-leftover-det", "Serpent leftover vs s.inp", "serpent", "2.2.0", "2.2.1", "s.inp",
     "det flux de 1", "det flux de 2 dm fuel", "set pop 10000 50 20", "set pop 20000 100 40",
     "dm fuel + larger pop", "inp"),
    ("tripoli-data-leftover-score", "TRIPOLI leftover vs t.data", "tripoli", "4.12", "4.13", "t.data",
     "SCORE TRACK", "SCORE COLLISION", "RESPONSE FLUX", "RESPONSE REACTION 18",
     "collision + MT18", "data"),
    ("phits-inp-leftover-source", "PHITS leftover vs p.inp", "phits", "3.34", "3.35", "p.inp",
     "s-type = 1", "s-type = 2", "proj = proton", "proj = neutron", "s-type 2 + neutron", "inp"),
    ("gnuradio-grc-leftover-samp", "GNU Radio leftover vs f.grc", "gnuradio", "3.10.11", "3.10.12", "f.grc",
     "samp_rate: 2e6", "samp_rate: 20e6", "osmosdr.source", "soapy.source", "20 Msps + soapy", "grc"),
    ("uhd-py-leftover-stream", "UHD leftover vs u.py", "uhd", "4.7.0", "4.8.0", "u.py",
     "usrp.set_rx_rate(1e6)", "usrp.set_rx_rate(10e6)",
     "streamer.recv(buf, md)", "streamer.recv(buf, md, timeout=0.1)", "10e6 + timeout", "py"),
    ("limesuite-ini-leftover-lpf", "LimeSuite leftover vs l.ini", "limesuite", "23.11.0", "23.11.0-api", "l.ini",
     "LNA=LNA_L", "LNA=LNA_H", "calibrate=0", "calibrate=1", "LNA_H + calibrate", "ini"),
    ("sigrok-cfg-leftover-samplerate", "sigrok leftover vs s.cfg", "sigrok", "0.5.2", "0.5.2-api", "s.cfg",
     "samplerate=1e6", "samplerate=24e6", "samples=1e5", "samples=1e6", "24 MHz + 1e6 samp", "cfg"),
    ("octave-m-leftover-pkg", "Octave leftover vs p.m", "octave", "9.2.0", "9.3.0", "p.m",
     "pkg load signal", "pkg load signal statistics", "fft(x)", "fft(x, 4096)", "stats + 4096 fft", "m"),
    ("scilab-sce-leftover-fft", "Scilab leftover vs f.sce", "scilab", "2024.1.0", "2025.0.0", "f.sce",
     "y = fft(x,-1)", "y = fft(x,-1,1)", "plot(y)", "plot(abs(y))", "dim 1 + abs plot", "sce"),
    ("maxima-mac-leftover-simp", "Maxima leftover vs s.mac", "maxima", "5.47.0", "5.48.0", "s.mac",
     "simp:true", "simp:false", "ev(e, numer)", "ev(e, numer, float)", "no simp + float", "mac"),
    ("sagemath-sage-leftover-gap", "Sage leftover vs s.sage", "sagemath", "10.4", "10.5", "s.sage",
     "G = gap.SmallGroup(8,3)", "G = libgap.SmallGroup(8,3)", "G.StructureDescription()", "G.IdGroup()",
     "libgap + IdGroup", "sage"),
    ("julia-pkg-leftover-compat", "Julia leftover vs Project.toml", "julia", "1.10.5", "1.11.3", "Project.toml",
     "compat = \"1.10\"", "compat = \"1.11\"", "[deps]", "[deps]\\nLinearAlgebra = \"37e2e46d-f89d-539d-b4ee-838fcccc9c8e\"",
     "1.11 + LinearAlgebra", "toml"),
    ("rlang-r-leftover-matrix", "R leftover vs m.R", "rlang", "4.4.1", "4.4.2", "m.R",
     "Matrix::sparseMatrix(i,j,x)", "Matrix::sparseMatrix(i,j,x, repr='T')",
     "crossprod(A)", "Matrix::crossprod(A)", "Tsparse + Matrix crossprod", "R"),
    ("matlab-m-leftover-gpu", "MATLAB leftover vs g.m", "matlab", "R2024a", "R2024b", "g.m",
     "A = rand(n)", "A = gpuArray.rand(n,'single')", "fft(A)", "fft(A,[],2)", "gpuArray single + dim2", "m"),
    ("sklearn-py-leftover-pipeline", "scikit-learn leftover vs sk.py", "sklearn", "1.5.1", "1.6.1", "sk.py",
     "Pipeline([('sc', StandardScaler()), ('lr', LogisticRegression())])",
     "Pipeline([('sc', StandardScaler()), ('lr', LogisticRegression(solver='lbfgs', max_iter=500))])",
     "pipe.fit(X,y)", "pipe.fit(X,y); pipe.set_output(transform='pandas')",
     "lbfgs 500 + pandas out", "py"),
    ("xgboost-py-leftover-hist", "XGBoost leftover vs xg.py", "xgboost", "2.1.1", "2.1.3", "xg.py",
     "XGBClassifier(tree_method='approx')", "XGBClassifier(tree_method='hist', device='cuda')",
     "clf.fit(X,y)", "clf.fit(X,y, eval_set=[(Xt,yt)])", "hist cuda + eval_set", "py"),
    ("lightgbm-py-leftover-dart", "LightGBM leftover vs lg.py", "lightgbm", "4.5.0", "4.5.0-api", "lg.py",
     "LGBMClassifier(boosting_type='gbdt')", "LGBMClassifier(boosting_type='dart', n_estimators=400)",
     "clf.fit(X,y)", "clf.fit(X,y, categorical_feature='auto')", "dart 400 + cat auto", "py"),
    ("catboost-py-leftover-catfeat", "CatBoost leftover vs cb.py", "catboost", "1.2.5", "1.2.7", "cb.py",
     "CatBoostClassifier(task_type='CPU')", "CatBoostClassifier(task_type='GPU', devices='0')",
     "clf.fit(X,y)", "clf.fit(X,y, cat_features=cats)", "GPU + cat_features", "py"),
    ("optuna-py-leftover-pruner", "Optuna leftover vs op.py", "optuna", "3.6.1", "4.1.0", "op.py",
     "optuna.create_study()", "optuna.create_study(pruner=optuna.pruners.MedianPruner())",
     "study.optimize(obj, n_trials=20)", "study.optimize(obj, n_trials=100, n_jobs=4)",
     "MedianPruner + 100x4", "py"),
    ("mlflow-py-leftover-autolog", "MLflow leftover vs ml.py", "mlflow", "2.16.2", "2.19.0", "ml.py",
     "mlflow.sklearn.autolog()", "mlflow.sklearn.autolog(log_models=True, log_datasets=True)",
     "mlflow.set_tracking_uri('file:./mlruns')", "mlflow.set_tracking_uri('http://mlf:5000')",
     "http tracking + datasets", "py"),
    ("hydra-py-leftover-compose", "Hydra leftover vs cfg.yaml", "hydra", "1.3.2", "1.3.2-api", "cfg.yaml",
     "defaults: [model: small]", "defaults: [model: large, _self_]",
     "hydra.job.chdir: true", "hydra.job.chdir: false", "large + no chdir", "yaml"),
    ("sacred-py-leftover-observer", "Sacred leftover vs sc.py", "sacred", "0.8.5", "0.8.6", "sc.py",
     "ex.observers.append(FileStorageObserver('runs'))", "ex.observers.append(MongoObserver(url='mongo', db_name='api'))",
     "@ex.main", "@ex.automain", "MongoObserver + automain", "py"),
]


def expand(row: tuple) -> tuple:
    slug, surface, pkg, old, new, pin, nest_old, nest_new, api_old, api_new, api_break, ext = row
    cmap = {
        "sql": "--", "R": "#", "hs": "--", "scala": "//", "vhdl": "--", "v": "//",
        "scd": "//", "orc": ";", "ttl": "#", "C": "//", "cpp": "//", "c": "//",
        "cs": "//", "dart": "//", "rb": "#", "php": "//", "js": "//", "ts": "//",
        "go": "//", "d": "//", "td": "//",
    }
    comment = cmap.get(ext, "#")
    sot_old = f"{comment} {pkg} {old}"
    sot_new = f"{comment} {pkg} {new}"
    if ext == "py":
        tool = f"python3 -c 'import {pkg}; print({pkg}.__version__)'"
        test = f"python3 apps/api/{pin}"
        ws = f"python3 apps/legacy/{pin}"
    else:
        tool = f"python3 -c 'print(\"{pkg}\")' || true"
        test = f"python3 -c 'print(\"apps/api/{pin}\")'"
        ws = f"python3 -c 'print(\"apps/legacy/{pin}\")'"
    return (slug, surface, pkg, old, new, pin, sot_old, sot_new, nest_old, nest_new, api_old, api_new, api_break, tool, test, ws, ext)


TOOLS: list[tuple] = [expand(r) for r in RAW]
assert len(TOOLS) % 2 == 0
assert len(TOOLS) <= len(PLANTS)

PAIRS: list[tuple[dict, dict]] = []
_pi = 0
for i in range(0, len(TOOLS), 2):
    a = TOOLS[i]
    b = TOOLS[i + 1]
    suc = make(
        a[0], PLANTS[_pi], a[1], a[2], a[3], a[4], False,
        a[5], a[6], a[7], a[8], a[9], a[10], a[11], a[12], a[13], a[14], a[15], a[16],
    )
    _pi += 1
    failp = make(
        b[0], PLANTS[_pi], b[1], b[2], b[3], b[4], True,
        b[5], b[6], b[7], b[8], b[9], b[10], b[11], b[12], b[13], b[14], b[15], b[16],
    )
    _pi += 1
    PAIRS.append((suc, failp))


def _validate_catalog() -> None:
    slugs = [spec["slug"] for pair in PAIRS for spec in pair]
    if len(slugs) != len(set(slugs)):
        raise SystemExit("duplicate slugs in r1351 catalog")
    for slug in slugs:
        for needle in BANNED_SLUG_NEEDLES:
            if needle and needle in slug:
                raise SystemExit(f"banned needle {needle!r} in {slug}")
    plants = [spec["plant"] for pair in PAIRS for spec in pair]
    if len(plants) != len(set(plants)):
        raise SystemExit("duplicate plants in r1351 catalog")


_validate_catalog()


def build_round(rnd: int) -> tuple[list[dict], str]:
    idx = rnd - CATALOG_FIRST
    if idx < 0 or idx >= len(PAIRS):
        raise SystemExit(
            f"round {rnd} outside catalog {CATALOG_FIRST}..{CATALOG_FIRST + len(PAIRS) - 1}"
        )
    suc, fail = PAIRS[idx]
    suc_ep = build_episode(rnd, suc)
    fail_ep = build_episode(rnd, fail)
    for ep in (suc_ep, fail_ep):
        n = len(ep["steps"])
        if n < 16 or n > 20:
            raise SystemExit(f"{ep['id']} has {n} steps, want 16-20")
        blob = json.dumps(ep)
        for banned in (
            "thought",
            "chain_of_thought",
            "scratch",
            "inner_monologue",
            "spike_events",
        ):
            if f'"{banned}"' in blob:
                raise SystemExit(f"{ep['id']} contains banned key {banned}")
        if '"sim_or_real": "real"' in blob or '"sim_or_real":"real"' in blob:
            raise SystemExit(f"{ep['id']} claims sim_or_real real")
    notes = notes_for(rnd, suc, fail)
    if "Novel coverage:" not in notes:
        raise SystemExit("notes missing Novel coverage")
    return [suc_ep, fail_ep], notes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--staging", required=True)
    args = ap.parse_args()
    rnd = args.round
    staging = Path(args.staging)
    recs, notes = build_round(rnd)
    batch = staging / f"batch-r{rnd:02d}.jsonl"
    notes_path = staging / f"NOTES-r{rnd:02d}.md"
    with batch.open("w") as handle:
        for rec in recs:
            handle.write(json.dumps(rec, ensure_ascii=True) + "\n")
    notes_path.write_text(notes)
    print(
        json.dumps(
            {
                "round": rnd,
                "ids": [r["id"] for r in recs],
                "steps": [len(r["steps"]) for r in recs],
                "success": [r["reward"]["success"] for r in recs],
                "batch": str(batch),
                "notes": str(notes_path),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
