#!/usr/bin/env python3
"""Mill monorepo-dep-bump-factory r840+ as unique leftover plants.

BAN r01–r839 clones including r776–r839 leftover surfaces (Ansible/Salt/Chef/
Puppet/Snapcraft/Flatpak/pkgsrc/Portage/Alpine/FreeBSD/Fuchsia/Serenity/RIOT/
Contiki/NuttX/FreeRTOS/seL4/Genode/MicroPython/CircuitPython/Isabelle/Dafny/
F*/Why3/Verilator/Yosys/OpenROAD/KLayout/OpenFOAM/FEniCS/PETSc/Trilinos/
Kokkos/SYCL/HIP/oneAPI/Charm/UPC++/TBB/HPX/SLURM/HTCondor/SAM/Crossplane/
Flux/Helmfile/OperatorSDK/Ivy/node-gyp/WASI/Wasmtime/Wasmer/Cranelift/QuickJS/
Duktape/JerryScript/Vega-Lite/Bokeh/Streamlit/Gradio/Dash/Shiny/HTMX/Alpine.js/
Stimulus/Livewire/Inertia/Pandoc/Quarto/Observable/CFN/CDK/ANTLR/OpenAPI/
AsyncAPI/JSON Schema/Avro/Thrift/Cap'n Proto/FlatBuffers/MessagePack/Parquet/
Arrow/DuckDB/ClickHouse/SQLite/Redis/Kafka/Pulsar/NATS/RabbitMQ/Consul/Nomad/
Vault/Boundary/Airflow/Prefect/Dagster/Luigi/dbt/GX/MLflow/W&B/HF/transformers/
LangChain/LlamaIndex/OpenCV/PCL/Gazebo/MoveIt/GStreamer/FFmpeg/LLVM/MLIR/
Sphinx/MkDocs/Javadoc/Doxygen/PlantUML/Graphviz/Bison/SWIG/GCC plugin/
clang-tidy/Spinnaker/Argo Workflows/Ignition).

NEW leftover bump surfaces start at r840.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

_BASE = Path(__file__).with_name("mdb-mill-r776.py")
_spec = importlib.util.spec_from_file_location("mdb_mill_r776", _BASE)
_m = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_m)

FACTORY = _m.FACTORY
GEN = _m.GEN
CATALOG_FIRST = 840
P = _m.P
build_episode = _m.build_episode
notes_for = _m.notes_for

BANNED_SLUG_NEEDLES = _m.BANNED_SLUG_NEEDLES + (
    "ansible-galaxy",
    "salt-pillar",
    "chef-berks",
    "puppet-puppetfile",
    "snapcraft-yaml",
    "flatpak-manifest",
    "pkgsrc-mk",
    "portage-ebuild",
    "alpine-apkbuild",
    "freebsd-ports",
    "fuchsia-cipd",
    "serenity-ports",
    "riot-makefile",
    "contiki-ng",
    "nuttx-defconfig",
    "freertos-config",
    "sel4-camkes",
    "genode-run",
    "micropython-manifest",
    "circuitpython-req",
    "isabelle-root",
    "dafny-dfyconfig",
    "fstar-fst",
    "why3-conf",
    "verilator-flags",
    "yosys-synth",
    "openroad-pdn",
    "klayout-lym",
    "openfoam-wmake",
    "fenics-dolfin",
    "petsc-makefile",
    "trilinos-cmake",
    "kokkos-view",
    "sycl-cmake",
    "hip-cmake",
    "oneapi-icpx",
    "charm-ck",
    "upcxx-rpc",
    "tbb-parallel",
    "hpx-async",
    "slurm-job",
    "htcondor-submit",
    "sam-template",
    "crossplane-comp",
    "flux-gitrepo",
    "helmfile-needs",
    "operatorsdk-project",
    "ivy-xml",
    "nodegyp-binding",
    "wasi-sdk",
    "wasmtime-toml",
    "wasmer-toml",
    "cranelift-ir",
    "quickjs-eval",
    "duktape-peval",
    "jerryscript-parse",
    "vegalite-sel",
    "bokeh-charts",
    "streamlit-rerun",
    "gradio-inputs",
    "dash-runserver",
    "shiny-fluid",
    "htmx-oob",
    "alpinejs-spread",
    "stimulus-targets",
    "livewire-defer",
    "inertia-share",
    "pandoc-citeproc",
    "quarto-knitr",
    "observable-fw",
    "cfn-getatt",
    "cdk-core",
    "antlr-g4",
    "openapi-gen",
    "asyncapi-yaml",
    "jsonschema-draft",
    "avro-schema",
    "thrift-idl",
    "capnproto-schema",
    "flatbuffers-fbs",
    "msgpack-packb",
    "parquet-schema",
    "arrow-dataset",
    "duckdb-pragma",
    "clickhouse-xml",
    "sqlite-json1",
    "redis-conf",
    "kafka-server",
    "pulsar-broker",
    "nats-conf",
    "rabbitmq-conf",
    "consul-hcl",
    "nomad-hcl",
    "vault-hcl",
    "boundary-hcl",
    "airflow-req",
    "prefect-yaml",
    "dagster-yaml",
    "luigi-cfg",
    "dbt-project",
    "gx-yml",
    "mlflow-conda",
    "wandb-yaml",
    "hfhub-req",
    "transformers-req",
    "langchain-req",
    "llamaindex-req",
    "opencv-cmake",
    "pcl-cmake",
    "gazebo-classic",
    "moveit-config",
    "gstreamer-meson",
    "ffmpeg-pc",
    "llvm-cmake",
    "mlir-td",
    "sphinx-conf",
    "mkdocs-yml",
    "javadoc-opts",
    "doxygen-cfg",
    "plantuml-jar",
    "graphviz-dot",
    "bison-y",
    "swig-i",
    "gcc-plugin",
    "clang-tidy",
    "spinnaker-hal",
    "argo-wf",
    "ignition-gz",
    "texlive-tlmgr",
    "context-tsetup",
    "pinecone-meta",
    "nmslib-space",
    "matlab-toolbox",
    "scilab-atoms",
    "hexo-yml",
    "eleventy-cfg",
    "nginx-conf",
    "haproxy-cfg",
)

# Patch banned list used by build_episode
_m.BANNED_SLUG_NEEDLES = BANNED_SLUG_NEEDLES

PAIRS: list[tuple[dict, dict]] = [
    (
        P("texlive-tlmgr-leftover-fmtutil", "hobby", "TeX Live tlmgr leftover vs texmf.cnf", "texlive", "2022", "2025", False, "texmf.cnf", "apps/api/texmf.cnf", "TEXMFDIST = /usr/share/texlive/2022", "TEXMFDIST = /usr/share/texlive/2025", "fmtutil-sys --byfmt pdflatex", "fmtutil-sys --all", "fmtutil-sys --byfmt pdflatex", "fmtutil-sys --all", "fmtutil --byfmt → --all", "tlmgr --version | head -n 1", "tlmgr check runfiles", "tlmgr --usermode check runfiles", "apps/api/hobby.tex"),
        P("context-tsetup-leftover-texexec", "honeyguide", "ConTeXt leftover vs t-setup", "context", "2021.03.05", "2024.11.01", True, "t-setup.tex", "apps/api/t-setup.tex", "% context 2021.03.05", "% context 2024.11.01", "texexec --pdf api.tex", "context api.tex", "texexec --pdf api.tex", "context api.tex", "texexec → context", "context --version | head -n 1", "context apps/api/api.tex", "context apps/legacy/legacy.tex", "apps/api/honeyguide.tex"),
    ),
    (
        P("biber-bcf-leftover-datamodel", "hornbill", "Biber leftover vs biblatex", "biber", "2.17", "2.20", False, "biblatex.cfg", "apps/api/biblatex.cfg", "\\RequireBiber[2.17]", "\\RequireBiber[2.20]", "datamodel = legacy", "datamodel = 2024", "\\DeclareDatamodelFields[type=field,datatype=literal]{shorttitle}", "\\DeclareDatamodelFields[type=field,datatype=literal]{shorttitle}[skipout=false]", "biblatex datamodel 2.17 → 2.20", "biber --version", "biber apps/api/api", "biber apps/legacy/legacy", "apps/api/hornbill.bcf"),
        P("groff-makefile-leftover-soelim", "hummingbird", "groff leftover vs Makefile", "groff", "1.22.4", "1.23.0", True, "Makefile", "apps/api/Makefile", "GROFF_VERSION = 1.22.4", "GROFF_VERSION = 1.23.0", "soelim api.ms | groff -ms", "groff -ms -s api.ms", "soelim api.ms | troff -ms", "groff -ms -s api.ms", "soelim pipe → groff -s", "groff --version | head -n 1", "make -C apps/api", "make -C apps/legacy", "apps/api/hummingbird.ms"),
    ),
    (
        P("asciidoctor-gem-leftover-safe", "jabiru", "Asciidoctor leftover vs Gemfile.lock", "asciidoctor", "2.0.17", "2.0.23", False, "Gemfile.lock", "apps/api/Gemfile.lock", "    asciidoctor (2.0.17)", "    asciidoctor (2.0.23)", "Asciidoctor.convert_file(f, safe: :unsafe)", "Asciidoctor.convert_file(f, safe: :server)", "safe: :unsafe", "safe: :server", "safe :unsafe → :server", "asciidoctor --version", "asciidoctor -a reproducible apps/api/api.adoc", "asciidoctor -a reproducible apps/legacy/legacy.adoc", "apps/api/jabiru.adoc"),
        P("hugo-config-leftover-blackfriday", "jackdaw", "Hugo leftover vs hugo.toml", "hugo", "0.92.2", "0.140.1", True, "hugo.toml", "apps/api/hugo.toml", "theme = \"ananke\" # 0.92.2", "theme = \"ananke\" # 0.140.1", "[blackfriday]\n  angledQuotes = true", "[markup.goldmark.renderer]\n  unsafe = false", "[blackfriday]", "[markup.goldmark.renderer]", "blackfriday → goldmark", "hugo version", "hugo --source apps/api --destination /tmp/api", "hugo --source apps/legacy --destination /tmp/legacy", "apps/api/jackdaw.md"),
    ),
    (
        P("zola-config-leftover-sass", "kagu", "Zola leftover vs config.toml", "zola", "0.15.3", "0.19.2", False, "config.toml", "apps/api/config.toml", "compile_sass = true # 0.15.3", "compile_sass = true # 0.19.2", "highlight_theme = \"base16-ocean-dark\"", "highlight_theme = \"css\"", "sass::compile(path)", "grass::from_path(path)", "sass crate → grass", "zola --version", "zola --root apps/api build", "zola --root apps/legacy build", "apps/api/sass/kagu.scss"),
        P("mdbook-toml-leftover-preproc", "kaka", "mdBook leftover vs book.toml", "mdbook", "0.4.21", "0.4.43", True, "book.toml", "apps/api/book.toml", "[preprocessor.index] # 0.4.21", "[preprocessor.index] # 0.4.43", "command = \"mdbook-toc\"", "command = \"mdbook-admonish\"", "[output.html.fold]", "[output.html.fold]\nenable = true", "mdbook-toc → mdbook-admonish", "mdbook --version", "mdbook build apps/api", "mdbook build apps/legacy", "apps/api/src/kaka.md"),
    ),
    (
        P("octave-pkg-leftover-prefix", "kea", "Octave leftover vs octave_packages", "octave", "6.4.0", "9.3.0", False, "octave_packages", "apps/api/octave_packages", "signal 1.4.1 octave-6.4.0", "signal 1.4.6 octave-9.3.0", "pkg prefix ~/octave-packages", "pkg prefix ~/octave-local", "pkg load signal", "pkg load signal -auto", "pkg prefix + load -auto", "octave --version | head -n 1", "octave --eval 'pkg test signal'", "octave --eval 'pkg test signal' --path apps/legacy", "apps/api/kea.m"),
        P("sage-spkg-leftover-optional", "kookaburra", "Sage leftover vs optional.cfg", "sage", "9.5", "10.5", True, "optional.cfg", "apps/api/optional.cfg", "SAGE_VERSION = 9.5", "SAGE_VERSION = 10.5", "optional_packages = gap_packages", "optional_packages = gap_packages,database_gap", "sage -i gap_packages", "sage -i database_gap", "gap_packages → database_gap", "sage --version", "sage -t apps/api/kookaburra.sage", "sage -t apps/legacy/kookaburra.sage", "apps/api/kookaburra.sage"),
    ),
    (
        P("mathematica-paclet-leftover-beginpkg", "lammergeier", "Mathematica leftover vs PacletInfo", "wolfram", "13.1.0", "14.1.0", False, "PacletInfo.wl", "apps/api/PacletInfo.wl", "PacletObject[<|\"Name\"->\"Api\",\"Version\"->\"13.1.0\"|>]", "PacletObject[<|\"Name\"->\"Api\",\"Version\"->\"14.1.0\"|>]", "BeginPackage[\"Api`\"]", "BeginPackage[\"Api`\", {\"Wolfram`PacletManager`\"}]", "BeginPackage[\"Api`\"]", "PacletSymbol[\"Api`Foo\"]", "BeginPackage → PacletSymbol", "wolframscript -version || true", "wolframscript -file apps/api/tests.wls", "wolframscript -file apps/legacy/tests.wls", "apps/api/Lammergeier.wl"),
        P("maxima-load-leftover-batchload", "macaw", "Maxima leftover vs maxima-init", "maxima", "5.46.0", "5.47.0", True, "maxima-init.mac", "apps/api/maxima-init.mac", "/* maxima 5.46.0 */", "/* maxima 5.47.0 */", "batchload(\"api.mac\")$", "load(\"api.mac\")$", "batchload(\"api.mac\")$", "load(\"api.mac\")$", "batchload → load", "maxima --version", "maxima -b apps/api/tests.mac", "maxima -b apps/legacy/tests.mac", "apps/api/macaw.mac"),
    ),
    (
        P("blender-addon-leftover-bpy", "manakin", "Blender leftover vs blender_manifest", "blender", "3.3.21", "4.3.2", False, "blender_manifest.toml", "apps/api/blender_manifest.toml", "schema_version = \"1.0.0\" # 3.3", "schema_version = \"1.0.0\" # 4.3", "bl_info = {\"blender\": (3, 3, 0)}", "blender_version_min = \"4.2.0\"", "bpy.ops.mesh.primitive_cube_add()", "bpy.ops.wm.obj_import(filepath=p)", "bl_info + cube_add → manifest + wm.obj_import", "blender --version | head -n 1", "blender -b --python apps/api/tests.py", "blender -b --python apps/legacy/tests.py", "apps/api/__init__.py"),
        P("inkscape-ext-leftover-inx", "merganser", "Inkscape leftover vs inx", "inkscape", "1.1.2", "1.4.0", True, "extensions/api.inx", "apps/api/api.inx", "<inkscape-extension><!-- 1.1.2 -->", "<inkscape-extension><!-- 1.4.0 -->", "<dependency type=\"executable\" location=\"extensions\">api.py</dependency>", "<dependency type=\"extension\">org.inkscape.filter.blur</dependency>", "inkex.Effect.affect()", "inkex.EffectExtension.run()", "Effect.affect → EffectExtension.run", "inkscape --version", "inkscape --actions=export-do apps/api/api.svg", "inkscape --actions=export-do apps/legacy/legacy.svg", "apps/api/merganser.py"),
    ),
    (
        P("gimp-plugin-leftover-pdb", "mockingbird", "GIMP leftover vs plug-ins", "gimp", "2.10.34", "3.0.0", False, "plug-ins/api.py", "apps/api/plug-ins/api.py", "# gimp 2.10.34", "# gimp 3.0.0", "from gimpfu import *", "import gi; gi.require_version('Gimp', '3.0')", "pdb.gimp_image_new(w, h, RGB)", "Gimp.Image.new(w, h, Gimp.ImageBaseType.RGB)", "gimpfu pdb → Gimp.Image.new", "gimp --version | head -n 1", "gimp -i --batch-interpreter python-fu-eval -b 'print(1)'", "gimp -i --batch-interpreter python-fu-eval -b 'print(1)' --no-interface", "apps/api/mockingbird.py"),
        P("krita-python-leftover-qimage", "myna", "Krita leftover vs desktop", "krita", "5.1.5", "5.2.9", True, "krita.desktop", "apps/api/krita.desktop", "X-KDE-PluginInfo-Version=5.1.5", "X-KDE-PluginInfo-Version=5.2.9", "from PyQt5.QtGui import QImage", "from PyQt6.QtGui import QImage", "QImage.Format_ARGB32", "QImage.Format.Format_ARGB32", "PyQt5 QImage → PyQt6 Format enum", "krita --version || true", "python3 apps/api/tests.py", "python3 apps/legacy/tests.py", "apps/api/myna.py"),
    ),
    (
        P("wayland-xml-leftover-wl", "nightingale", "Wayland leftover vs protocol xml", "wayland", "1.20.0", "1.23.1", False, "wayland.xml", "apps/api/xdg-shell.xml", "<!-- wayland 1.20.0 -->", "<!-- wayland 1.23.1 -->", "wl_shell_surface_set_toplevel(s)", "xdg_toplevel_set_app_id(t, \"api\")", "wl_shell_surface_set_toplevel(", "xdg_toplevel_set_app_id(", "wl_shell → xdg_toplevel", "wayland-scanner --version || true", "wayland-scanner client-header apps/api/xdg-shell.xml /tmp/api.h", "wayland-scanner client-header apps/legacy/xdg-shell.xml /tmp/legacy.h", "apps/api/nightingale.c"),
        P("vulkan-xml-leftover-vkcreate", "nuthatch", "Vulkan leftover vs vk.xml", "vulkan", "1.3.239", "1.4.309", True, "vk.xml", "apps/api/vk.xml", "<!-- vulkan 1.3.239 -->", "<!-- vulkan 1.4.309 -->", "vkCreateInstance(&ci, NULL, &inst)", "vkCreateInstance(&ci, palloc, &inst)", "VkApplicationInfo ai{VK_STRUCTURE_TYPE_APPLICATION_INFO, nullptr, \"api\", 0, nullptr, 0, VK_API_VERSION_1_2};", "VkApplicationInfo ai{VK_STRUCTURE_TYPE_APPLICATION_INFO, nullptr, \"api\", 0, nullptr, 0, VK_API_VERSION_1_4};", "VK_API_VERSION_1_2 → 1_4", "vulkaninfo --summary | head || true", "glslc -c apps/api/nuthatch.vert", "glslc -c apps/legacy/nuthatch.vert", "apps/api/nuthatch.cpp"),
    ),
    (
        P("spirv-grammar-leftover-opcode", "oropendola", "SPIR-V leftover vs grammar json", "spirv-headers", "1.3.239", "1.6.4", False, "spirv.core.grammar.json", "apps/api/spirv.core.grammar.json", "\"major_version\": 1, \"minor_version\": 5", "\"major_version\": 1, \"minor_version\": 6", "OpDecorate id Decoration", "OpDecorateString id Decoration", "spv::OpDecorate", "spv::OpDecorateString", "OpDecorate → OpDecorateString", "spirv-as --version || true", "spirv-val apps/api/api.spv", "spirv-val apps/legacy/legacy.spv", "apps/api/oropendola.spvasm"),
        P("glslang-includer-leftover-dir", "ovenbird", "glslang leftover vs includer", "glslang", "11.13.0", "15.1.0", True, "glslang.version", "apps/api/CMakeLists.txt", "find_package(glslang 11 REQUIRED)", "find_package(glslang 15 REQUIRED)", "DirStackFileIncluder includer;", "glslang::DirStackFileIncluder includer;", "TShader::setStrings(s, 1);", "TShader::setStringsWithLengths(s, lens, 1);", "setStrings → setStringsWithLengths", "glslangValidator -v || true", "glslangValidator -V apps/api/api.vert", "glslangValidator -V apps/legacy/legacy.vert", "apps/api/ovenbird.vert"),
    ),
    (
        P("naga-wgsl-leftover-module", "parakeet", "Naga leftover vs wgsl", "naga", "0.12.1", "24.0.0", False, "naga.toml", "apps/api/shader.wgsl", "naga = \"0.12.1\"", "naga = \"24.0.0\"", "var<uniform> u : U;", "var<uniform> u: U;", "naga::front::wgsl::parse_str(src)", "naga::front::wgsl::Frontend::new().parse(src)", "parse_str → Frontend::parse", "cargo test -p naga --offline --no-run || true", "naga apps/api/shader.wgsl /tmp/api.spv", "naga apps/legacy/shader.wgsl /tmp/legacy.spv", "apps/api/parakeet.wgsl"),
        P("wgpu-core-leftover-adapter", "pewee", "wgpu leftover vs wgpu.toml", "wgpu", "0.16.3", "24.0.0", True, "wgpu.toml", "apps/api/wgpu.toml", "wgpu = \"0.16.3\"", "wgpu = \"24.0.0\"", "adapter.request_device(&desc, None)", "adapter.request_device(&desc)", "Device::create_shader_module(include_wgsl!(\"s.wgsl\"))", "Device::create_shader_module(ShaderModuleDescriptor { label: None, source: ShaderSource::Wgsl(src.into()) })", "request_device None + include_wgsl → ShaderSource::Wgsl", "cargo test -p wgpu --offline --no-run || true", "cargo test --manifest-path apps/api/Cargo.toml", "cargo test --manifest-path apps/legacy/Cargo.toml", "apps/api/src/pewee.rs"),
    ),
    (
        P("pipewire-spa-leftover-audioports", "phainopepla", "PipeWire leftover vs spa", "pipewire", "0.3.65", "1.2.7", False, "pipewire.conf", "apps/api/pipewire.conf", "context.spa-libs = { # 0.3.65", "context.spa-libs = { # 1.2.7", "audio.position = [ FL FR ]", "audio.position = [ FL FR LFE ]", "pw_filter_new_simple(loop, name, props, events, data)", "pw_filter_new(core, props, events, data)", "pw_filter_new_simple → pw_filter_new", "pw-cli --version || true", "pw-cli info 0", "pw-cli -m info 0", "apps/api/phainopepla.c"),
        P("jack2-conf-leftover-alsa", "phalarope", "JACK2 leftover vs jackdrc", "jack2", "1.9.21", "1.9.22", True, "jackdrc", "apps/api/jackdrc", "/usr/bin/jackd -d alsa # 1.9.21", "/usr/bin/jackd -d alsa # 1.9.22", "jack_client_open(\"api\", JackNullOption, NULL)", "jack_client_open(\"api\", JackNoStartServer, NULL)", "jack_port_register(c, \"out\", JACK_DEFAULT_AUDIO_TYPE, JackPortIsOutput, 0)", "jack_port_register(c, \"out\", JACK_DEFAULT_AUDIO_TYPE, JackPortIsOutput | JackPortIsTerminal, 0)", "JackNullOption → JackNoStartServer", "jackd --version", "jack_wait --server default --timeout 1 || true", "jack_wait --server legacy --timeout 1 || true", "apps/api/phalarope.c"),
    ),
    (
        P("imagemagick-xml-leftover-convert", "poorwill", "ImageMagick leftover vs policy.xml", "imagemagick", "6.9.11", "7.1.1", False, "policy.xml", "apps/api/policy.xml", "<!-- ImageMagick 6.9.11 -->", "<!-- ImageMagick 7.1.1 -->", "convert in.png -resize 50% out.png", "magick in.png -resize 50% out.png", "ConvertImageCommand(argc, argv)", "MagickImageCommand(argc, argv)", "convert → magick", "magick -version | head -n 1", "magick identify apps/api/api.png", "magick identify apps/legacy/legacy.png", "apps/api/poorwill.sh"),
        P("libvips-meson-leftover-vips8", "pygmyowl", "libvips leftover vs meson.build", "vips", "8.12.2", "8.16.0", True, "meson.build", "apps/api/meson.build", "dependency('vips', version: '>=8.12')", "dependency('vips', version: '>=8.16')", "vips_init(\"api\")", "if (VIPS_INIT(\"api\")) return 1;", "im_copy(in, out)", "vips_copy(in, &out, NULL)", "im_copy → vips_copy", "vips --version", "vips copy apps/api/in.png /tmp/api.png", "vips copy apps/legacy/in.png /tmp/legacy.png", "apps/api/pygmyowl.c"),
    ),
    (
        P("vtk-cmake-leftover-smartptr", "roadrunner", "VTK leftover vs CMakeLists", "vtk", "9.1.0", "9.4.1", False, "CMakeLists.txt", "apps/api/CMakeLists.txt", "find_package(VTK 9.1 REQUIRED)", "find_package(VTK 9.4 REQUIRED)", "vtkSmartPointer<vtkRenderer> r = vtkSmartPointer<vtkRenderer>::New();", "vtkNew<vtkRenderer> r;", "r->SetBackground(0.1, 0.2, 0.4);", "r->SetBackground(0.1, 0.2, 0.4); // vtkNew", "vtkSmartPointer::New → vtkNew", "vtkpython -c 'import vtk; print(vtk.VTK_VERSION)' || true", "ctest --test-dir apps/api", "ctest --test-dir apps/legacy", "apps/api/src/roadrunner.cpp"),
        P("itk-cmake-leftover-image", "roseate", "ITK leftover vs CMakeLists", "itk", "5.2.1", "5.4.0", True, "CMakeLists.txt", "apps/api/CMakeLists.txt", "find_package(ITK 5.2 REQUIRED)", "find_package(ITK 5.4 REQUIRED)", "using ImageType = itk::Image<float, 3>;", "using ImageType = itk::Image<float, 3>; // 5.4", "reader->GraftOutput(img);", "reader->SetOutput(img);", "GraftOutput → SetOutput", "itkTestDriver --help | head || true", "ctest --test-dir apps/api", "ctest --test-dir apps/legacy", "apps/api/src/roseate.cpp"),
    ),
    (
        P("gdal-data-leftover-ogr", "sanderling", "GDAL leftover vs data files", "gdal", "3.4.3", "3.10.1", False, "gdal-data/gdalvrt.xsd", "apps/api/gdal-data/gdalvrt.xsd", "<!-- gdal 3.4.3 -->", "<!-- gdal 3.10.1 -->", "OGRRegisterAll();", "GDALAllRegister();", "OGR_Dr_CreateDataSource(dr, path, NULL)", "GDALCreate(dr, path, 0, 0, 0, GDT_Unknown, NULL)", "OGRRegisterAll → GDALAllRegister", "gdalinfo --version", "gdalinfo apps/api/api.tif", "gdalinfo apps/legacy/legacy.tif", "apps/api/sanderling.cpp"),
        P("proj-db-leftover-epsg", "scoter", "PROJ leftover vs proj.db", "proj", "8.2.1", "9.5.1", True, "proj.db.version", "apps/api/proj.ini", "PROJ 8.2.1", "PROJ 9.5.1", "proj_create_from_database(ctx, \"EPSG\", \"4326\", PJ_CATEGORY_CRS, 0, NULL)", "proj_create(ctx, \"EPSG:4326\")", "pj_init_plus(\"+init=epsg:4326\")", "proj_create(ctx, \"EPSG:4326\")", "pj_init_plus +init=epsg → proj_create EPSG:", "proj --version", "cs2cs EPSG:4326 EPSG:3857", "cs2cs EPSG:4326 EPSG:3857 -f '%.3f'", "apps/api/scoter.c"),
    ),
    (
        P("geos-wkt-leftover-wkt1", "secretarybird", "GEOS leftover vs CMakeLists", "geos", "3.10.3", "3.13.0", False, "CMakeLists.txt", "apps/api/CMakeLists.txt", "find_package(GEOS 3.10 REQUIRED)", "find_package(GEOS 3.13 REQUIRED)", "GEOSWKTReader_read(r, wkt)", "GEOSWKTReader_read_r(handle, r, wkt)", "GEOSGeomFromWKT(wkt)", "GEOSWKTReader_read_r(h, r, wkt)", "GEOSWKTReader_read → _r + WKT2", "geos-config --version", "ctest --test-dir apps/api", "ctest --test-dir apps/legacy", "apps/api/src/secretarybird.cpp"),
        P("qgis-py-leftover-iface", "shoveler", "QGIS leftover vs metadata.txt", "qgis", "3.22.16", "3.40.2", True, "metadata.txt", "apps/api/metadata.txt", "qgisMinimumVersion=3.22", "qgisMinimumVersion=3.34", "from qgis.utils import iface", "from qgis.gui import QgisInterface", "iface.addVectorLayer(p, \"api\", \"ogr\")", "project.addMapLayer(layer)", "iface.addVectorLayer → project.addMapLayer", "qgis --version || true", "python3 apps/api/tests.py", "python3 apps/legacy/tests.py", "apps/api/shoveler.py"),
    ),
    (
        P("osmium-pbf-leftover-handler", "skimmer", "libosmium leftover vs protozero", "libosmium", "2.18.0", "2.20.0", False, "CMakeLists.txt", "apps/api/CMakeLists.txt", "find_package(Osmium 2.18 REQUIRED)", "find_package(Osmium 2.20 REQUIRED)", "struct H : osmium::handler::Handler { void way(const osmium::Way&) {} };", "struct H : osmium::handler::Handler { void way(const osmium::Way&) const {} };", "osmium::io::Reader reader{file};", "osmium::io::Reader reader{file, osmium::osm_entity_bits::way};", "Reader default → entity_bits::way", "osmium --version || true", "osmium fileinfo apps/api/api.osm.pbf", "osmium fileinfo apps/legacy/legacy.osm.pbf", "apps/api/src/skimmer.cpp"),
        P("valhalla-tiles-leftover-loki", "skua", "Valhalla leftover vs valhalla.json", "valhalla", "3.3.0", "3.5.1", True, "valhalla.json", "apps/api/valhalla.json", "\"mjolnir\": { \"tile_dir\": \"/data/valhalla\" } // 3.3.0", "\"mjolnir\": { \"tile_dir\": \"/data/valhalla\" } // 3.5.1", "loki.service.proxy", "loki.service", "costing=auto", "costing=auto_shorter", "loki.service.proxy + auto → costing auto_shorter", "valhalla_service --version || true", "valhalla_build_config --help | head", "valhalla_build_tiles -c apps/legacy/valhalla.json apps/legacy.pbf || true", "apps/api/skua.json"),
    ),
    (
        P("osrm-lua-leftover-process", "snowgoose", "OSRM leftover vs profile.lua", "osrm", "5.26.0", "5.27.1", False, "car.lua", "apps/api/car.lua", "-- osrm 5.26.0", "-- osrm 5.27.1", "function process_way(profile, way, result)", "function process_segment(profile, segment)", "result.forward_speed = 30", "segment.weight = 30", "process_way forward_speed → process_segment weight", "osrm-extract --version", "osrm-extract apps/api/api.osm -p apps/api/car.lua", "osrm-extract apps/legacy/legacy.osm -p apps/legacy/car.lua", "apps/api/snowgoose.lua"),
        P("graphhopper-cfg-leftover-flagenc", "sparrowhawk", "GraphHopper leftover vs config.yml", "graphhopper", "6.2", "10.0", True, "config.yml", "apps/api/config.yml", "graphhopper.version: 6.2", "graphhopper.version: 10.0", "graph.flag_encoders: car", "graph.encoded_values: car_access, car_average_speed", "new CarFlagEncoder()", "new CarEncodedValues()", "flag_encoders CarFlagEncoder → encoded_values", "java -jar graphhopper.jar --version || true", "java -jar graphhopper.jar import apps/api/config.yml", "java -jar graphhopper.jar import apps/legacy/config.yml", "apps/api/sparrowhawk.yml"),
    ),
    (
        P("lucene-index-leftover-iw", "spoonbill", "Lucene leftover vs core jar", "lucene", "8.11.3", "9.12.1", False, "lucene.version", "apps/api/lucene.version", "8.11.3", "9.12.1", "new IndexWriter(dir, new IndexWriterConfig(new StandardAnalyzer()))", "new IndexWriter(dir, new IndexWriterConfig())", "iw.addDocument(doc); iw.commit();", "iw.addDocument(doc); iw.flush(); iw.commit();", "IndexWriterConfig(StandardAnalyzer) default analyzer removed", "java -cp lucene-core.jar org.apache.lucene.util.Version || true", "java -jar lucene-core.jar || true", "java -jar lucene-core.jar || true", "apps/api/src/Spoonbill.java"),
        P("solr-schema-leftover-managed", "sunbird", "Solr leftover vs managed-schema", "solr", "8.11.3", "9.7.0", True, "managed-schema.xml", "apps/api/managed-schema.xml", "<!-- solr 8.11.3 -->", "<!-- solr 9.7.0 -->", "<schema name=\"api\" version=\"1.6\">", "<schema name=\"api\" version=\"1.7\">", "<fieldType name=\"text_general\" class=\"solr.TextField\">", "<fieldType name=\"text_general\" class=\"solr.TextField\" indexed=\"true\">", "schema 1.6 → 1.7 + indexed on fieldType", "solr version || true", "solr create -c api -d apps/api || true", "solr create -c legacy -d apps/legacy || true", "apps/api/sunbird.xml"),
    ),
    (
        P("meilisearch-dump-leftover-settings", "tattler", "Meilisearch leftover vs dump", "meilisearch", "0.30.5", "1.12.3", False, "settings.json", "apps/api/settings.json", "\"displayedAttributes\": [\"*\"] // 0.30.5", "\"displayedAttributes\": [\"*\"] // 1.12.3", "\"typoTolerance\": { \"enabled\": true }", "\"typoTolerance\": { \"disableOnWords\": [\"sku\"] }", "index.update_settings({\"searchableAttributes\": [\"title\"]})", "index.update_settings({\"searchableAttributes\": [\"title\"], \"proximityPrecision\": \"byWord\"})", "typoTolerance + proximityPrecision", "meilisearch --version", "curl -s http://127.0.0.1:7700/health || true", "curl -s http://127.0.0.1:7701/health || true", "apps/api/tattler.json"),
        P("typesense-schema-leftover-facet", "thrasher", "Typesense leftover vs schema", "typesense", "0.24.1", "27.1", True, "schema.json", "apps/api/schema.json", "\"name\": \"api\", \"fields\": [] // 0.24.1", "\"name\": \"api\", \"fields\": [] // 27.1", "{\"name\": \"tags\", \"type\": \"string[]\", \"facet\": true}", "{\"name\": \"tags\", \"type\": \"string[]\", \"facet\": true, \"stem\": false}", "create_collection({name: \"api\"})", "create_collection({name: \"api\", token_separators: [\"-\"]})", "facet + token_separators", "typesense-server --version", "typesense-server --config apps/api/typesense.ini || true", "typesense-server --config apps/legacy/typesense.ini || true", "apps/api/thrasher.json"),
    ),
    (
        P("vespa-sd-leftover-document", "tyrannulet", "Vespa leftover vs .sd", "vespa", "8.150.32", "8.448.13", False, "api.sd", "apps/api/api.sd", "schema api { document api { } } // 8.150", "schema api { document api { } } // 8.448", "field title type string { indexing: summary | index }", "field title type string { indexing: summary | index | attribute }", "search api { }", "schema api { }", "search {} → schema {} + attribute", "vespa version || true", "vespa deploy apps/api", "vespa deploy apps/legacy", "apps/api/tyrannulet.sd"),
        P("milvus-coll-leftover-flush", "umbrellabird", "Milvus leftover vs collection", "milvus", "2.2.14", "2.5.4", True, "collection.yaml", "apps/api/collection.yaml", "milvus: 2.2.14", "milvus: 2.5.4", "collection.flush()", "utility.flush_all()", "collection.search(data, \"emb\", param, limit=10)", "collection.search(data, \"emb\", anns_field=\"emb\", limit=10)", "flush() → flush_all + anns_field", "milvus --version || true", "python3 apps/api/tests.py", "python3 apps/legacy/tests.py", "apps/api/umbrellabird.py"),
    ),
    (
        P("qdrant-payload-leftover-filter", "waterthrush", "Qdrant leftover vs collection config", "qdrant", "1.3.2", "1.13.0", False, "config.yaml", "apps/api/config.yaml", "log_level: INFO # 1.3.2", "log_level: INFO # 1.13.0", "Filter(must=[FieldCondition(key=\"c\", match=MatchValue(value=1))])", "Filter(must=[FieldCondition(key=\"c\", match=MatchValue(value=\"1\"))])", "client.search(collection_name=\"api\", query_vector=v, limit=5)", "client.query_points(collection_name=\"api\", query=v, limit=5)", "search + MatchValue int → query_points + string", "qdrant --version || true", "python3 apps/api/tests.py", "python3 apps/legacy/tests.py", "apps/api/waterthrush.py"),
        P("weaviate-class-leftover-vectorizer", "weaver", "Weaviate leftover vs schema", "weaviate", "1.19.12", "1.28.5", True, "schema.json", "apps/api/schema.json", "\"class\": \"Api\" // 1.19.12", "\"class\": \"Api\" // 1.28.5", "\"vectorizer\": \"text2vec-transformers\"", "\"vectorizer\": \"text2vec-weaviate\"", "client.schema.create_class(cls)", "client.collections.create(name=\"Api\")", "schema.create_class + text2vec-transformers → collections.create", "weaviate version || true", "python3 apps/api/tests.py", "python3 apps/legacy/tests.py", "apps/api/weaver.py"),
    ),
    (
        P("faiss-index-leftover-ivf", "whippoorwill", "FAISS leftover vs index factory", "faiss", "1.7.3", "1.9.0", False, "index.factory", "apps/api/index.factory", "IVF4096,Flat # 1.7.3", "IVF4096,Flat # 1.9.0", "index = faiss.index_factory(d, \"IVF4096,Flat\")", "index = faiss.index_factory(d, \"IVF4096,Flat\", faiss.METRIC_INNER_PRODUCT)", "index.nprobe = 16", "faiss.ParameterSpace().set_index_parameter(index, \"nprobe\", 16)", "nprobe attr → ParameterSpace", "python3 -c 'import faiss; print(faiss.__version__)' || true", "python3 apps/api/tests.py", "python3 apps/legacy/tests.py", "apps/api/whippoorwill.py"),
        P("hnswlib-space-leftover-l2", "wryneck", "hnswlib leftover vs space", "hnswlib", "0.6.2", "0.8.0", True, "requirements.txt", "apps/api/requirements.txt", "hnswlib==0.6.2", "hnswlib==0.8.0", "p = hnswlib.Index(space='l2', dim=d)", "p = hnswlib.Index(space='ip', dim=d)", "p.init_index(max_elements=n, ef_construction=200, M=16)", "p.init_index(max_elements=n, ef_construction=200, M=16, allow_replace_deleted=True)", "space l2 → ip + allow_replace_deleted", "python3 -c 'import hnswlib' || true", "python3 apps/api/tests.py", "python3 apps/legacy/tests.py", "apps/api/wryneck.py"),
    ),
    (
        P("annoy-trees-leftover-angular", "yellowlegs", "Annoy leftover vs trees", "annoy", "1.17.1", "1.17.3", False, "requirements.txt", "apps/api/requirements.txt", "annoy==1.17.1", "annoy==1.17.3", "t = AnnoyIndex(d, 'angular')", "t = AnnoyIndex(d, 'dot')", "t.build(10)", "t.build(10, n_jobs=-1)", "angular → dot + n_jobs", "python3 -c 'import annoy' || true", "python3 apps/api/tests.py", "python3 apps/legacy/tests.py", "apps/api/yellowlegs.py"),
        P("scann-leaves-leftover-ah", "accentor", "ScaNN leftover vs builder", "scann", "1.2.9", "1.3.5", True, "requirements.txt", "apps/api/requirements.txt", "scann==1.2.9", "scann==1.3.5", "builder.tree(num_leaves=2000, num_leaves_to_search=100)", "builder.tree(num_leaves=2000, num_leaves_to_search=100, training_sample_size=100000)", "score_ah(2, anisotropic_quantization_threshold=0.2)", "score_ah(2)", "tree training_sample_size + score_ah threshold removed", "python3 -c 'import scann' || true", "python3 apps/api/tests.py", "python3 apps/legacy/tests.py", "apps/api/accentor.py"),
    ),
    (
        P("dcmtk-dicom-leftover-ofstring", "barbet", "DCMTK leftover vs CMakeLists", "dcmtk", "3.6.7", "3.6.9", False, "CMakeLists.txt", "apps/api/CMakeLists.txt", "find_package(DCMTK 3.6.7 REQUIRED)", "find_package(DCMTK 3.6.9 REQUIRED)", "OFString s;", "std::string s;", "dset.findAndGetOFString(DCM_PatientName, s)", "dset.findAndGetOFStringArray(DCM_PatientName, s)", "OFString + findAndGetOFString → std::string + Array", "dcmdump --version | head -n 1", "dcmdump apps/api/api.dcm", "dcmdump apps/legacy/legacy.dcm", "apps/api/src/barbet.cpp"),
        P("grass-gis-leftover-gregion", "besra", "GRASS leftover vs grass.py", "grass", "8.2.1", "8.4.0", True, "grass.py", "apps/api/grass.py", "# grass 8.2.1", "# grass 8.4.0", "from grass.script import core as gcore", "import grass.script as gs", "gcore.run_command('g.region', raster='elev')", "gs.run_command('g.region', raster='elev')", "grass.script.core → grass.script", "grass --version | head -n 1", "grass --tmp-location EPSG:4326 --exec g.version", "grass --tmp-location EPSG:4326 --exec g.version", "apps/api/besra.py"),
    ),
    (
        P("mapserver-map-leftover-layer", "bulbul", "MapServer leftover vs mapfile", "mapserver", "7.6.4", "8.2.2", False, "api.map", "apps/api/api.map", "MAP NAME \"api\" # 7.6.4", "MAP NAME \"api\" # 8.2.2", "LAYER TYPE RASTER STATUS ON DATA \"elev.tif\" END", "LAYER TYPE RASTER STATUS ON DATA \"elev.tif\" PROCESSING \"RESAMPLE=AVERAGE\" END", "msLoadMap(path, NULL)", "msLoadMapFromString(txt, NULL)", "msLoadMap → msLoadMapFromString + PROCESSING", "mapserv -v | head -n 1", "shp2img -m apps/api/api.map -o /tmp/api.png", "shp2img -m apps/legacy/legacy.map -o /tmp/legacy.png", "apps/api/bulbul.map"),
        P("mapnik-xml-leftover-datasource", "bushshrike", "Mapnik leftover vs xml", "mapnik", "3.1.0", "4.0.2", True, "style.xml", "apps/api/style.xml", "<!-- mapnik 3.1.0 -->", "<!-- mapnik 4.0.2 -->", "<Datasource><Parameter name=\"type\">shape</Parameter></Datasource>", "<Datasource><Parameter name=\"type\">geojson</Parameter></Datasource>", "mapnik.Shapefile(file=p)", "mapnik.GeoJSON(file=p)", "shape datasource → geojson", "mapnik-config --version", "python3 apps/api/tests.py", "python3 apps/legacy/tests.py", "apps/api/bushshrike.py"),
    ),
    (
        P("harfbuzz-hb-leftover-ot", "canary", "HarfBuzz leftover vs meson.build", "harfbuzz", "4.4.1", "10.1.0", False, "meson.build", "apps/api/meson.build", "dependency('harfbuzz', version: '>=4.4')", "dependency('harfbuzz', version: '>=10.1')", "hb_ot_layout_lookup_substitute_closure(face, lookup, glyphs)", "hb_ot_layout_collect_lookups(face, table, scripts, langs, features, lookups)", "hb_buffer_set_unicode_funcs(buf, hb_icu_get_unicode_funcs())", "hb_buffer_set_unicode_funcs(buf, hb_ucd_get_unicode_funcs())", "icu unicode funcs → ucd", "pkg-config --modversion harfbuzz", "meson test -C apps/api/build", "meson test -C apps/legacy/build", "apps/api/src/canary.c"),
        P("freetype-ft-leftover-glyph", "catbird", "FreeType leftover vs meson.build", "freetype", "2.12.1", "2.13.3", True, "meson.build", "apps/api/meson.build", "dependency('freetype2', version: '>=2.12')", "dependency('freetype2', version: '>=2.13')", "FT_Load_Glyph(face, idx, FT_LOAD_DEFAULT)", "FT_Load_Glyph(face, idx, FT_LOAD_NO_SVG)", "FT_Get_Kerning(face, l, r, FT_KERNING_DEFAULT, &d)", "FT_Get_Kerning(face, l, r, FT_KERNING_UNFITTED, &d)", "FT_LOAD_DEFAULT + KERNING_DEFAULT → NO_SVG + UNFITTED", "pkg-config --modversion freetype2", "meson test -C apps/api/build", "meson test -C apps/legacy/build", "apps/api/src/catbird.c"),
    ),
    (
        P("cairo-ft-leftover-scaled", "chiffchaff", "Cairo leftover vs meson.build", "cairo", "1.16.0", "1.18.2", False, "meson.build", "apps/api/meson.build", "dependency('cairo', version: '>=1.16')", "dependency('cairo', version: '>=1.18')", "cairo_ft_font_face_create_for_ft_face(face, 0)", "cairo_font_face_reference(cairo_toy_font_face_create(\"Sans\", CAIRO_FONT_SLANT_NORMAL, CAIRO_FONT_WEIGHT_NORMAL))", "cairo_set_operator(cr, CAIRO_OPERATOR_SATURATE)", "cairo_set_operator(cr, CAIRO_OPERATOR_MULTIPLY)", "ft_face_create + SATURATE → toy + MULTIPLY", "pkg-config --modversion cairo", "meson test -C apps/api/build", "meson test -C apps/legacy/build", "apps/api/src/chiffchaff.c"),
        P("pango-cairo-leftover-layout", "creeper", "Pango leftover vs meson.build", "pango", "1.50.14", "1.56.0", True, "meson.build", "apps/api/meson.build", "dependency('pangocairo', version: '>=1.50')", "dependency('pangocairo', version: '>=1.56')", "pango_layout_set_markup(layout, xml, -1)", "pango_layout_set_markup_with_accel(layout, xml, -1, '_', NULL)", "pango_cairo_show_layout(cr, layout)", "pango_cairo_show_layout_line(cr, pango_layout_get_line_readonly(layout, 0))", "set_markup → with_accel + show_layout_line", "pkg-config --modversion pangocairo", "meson test -C apps/api/build", "meson test -C apps/legacy/build", "apps/api/src/creeper.c"),
    ),
    (
        P("alsa-pcm-leftover-hwparams", "firefinch", "ALSA leftover vs asound.conf", "alsa", "1.2.6", "1.2.13", False, "asound.conf", "apps/api/asound.conf", "pcm.!default { type hw card 0 } # 1.2.6", "pcm.!default { type hw card 0 } # 1.2.13", "snd_pcm_hw_params_set_rate_near(pcm, hw, &rate, 0)", "snd_pcm_hw_params_set_rate(pcm, hw, rate, 0)", "snd_pcm_open(&p, \"default\", SND_PCM_STREAM_PLAYBACK, 0)", "snd_pcm_open(&p, \"default\", SND_PCM_STREAM_PLAYBACK, SND_PCM_NONBLOCK)", "set_rate_near → set_rate + NONBLOCK", "aplay --version | head -n 1", "aplay -l || true", "aplay -L || true", "apps/api/src/firefinch.c"),
        P("pulse-pactl-leftover-sink", "gerygone", "PulseAudio leftover vs default.pa", "pulseaudio", "15.0", "17.0", True, "default.pa", "apps/api/default.pa", "# pulse 15.0", "# pulse 17.0", "load-module module-udev-detect", "load-module module-detect", "pactl set-default-sink alsa_output.pci", "wpctl set-default @DEFAULT_AUDIO_SINK@", "module-udev-detect + pactl → module-detect + wpctl", "pulseaudio --version", "pactl info || true", "pactl info || true", "apps/api/gerygone.pa"),
    ),
    (
        P("libsndfile-sf-leftover-info", "goawaybird", "libsndfile leftover vs meson.build", "libsndfile", "1.0.31", "1.2.2", False, "meson.build", "apps/api/meson.build", "dependency('sndfile', version: '>=1.0.31')", "dependency('sndfile', version: '>=1.2.2')", "info.format = SF_FORMAT_WAV | SF_FORMAT_PCM_16", "info.format = SF_FORMAT_WAVEX | SF_FORMAT_FLOAT", "sf_command(f, SFC_SET_NORM_FLOAT, NULL, SF_TRUE)", "sf_command(f, SFC_SET_CLIPPING, NULL, SF_TRUE)", "WAV PCM_16 + NORM_FLOAT → WAVEX FLOAT + CLIPPING", "pkg-config --modversion sndfile", "meson test -C apps/api/build", "meson test -C apps/legacy/build", "apps/api/src/goawaybird.c"),
        P("sox-fmt-leftover-effect", "greylag", "SoX leftover vs sox.conf", "sox", "14.4.2", "14.4.2+git2021", True, "sox.conf", "apps/api/sox.conf", "SOX_OPTS=-V1 # 14.4.2", "SOX_OPTS=-V2 # git2021", "sox in.wav -r 16000 out.wav silence 1 0.1 1%", "sox in.wav -r 16000 out.wav vad", "sox_create_effect(sox_find_effect(\"silence\"))", "sox_create_effect(sox_find_effect(\"vad\"))", "silence effect → vad", "sox --version", "sox --i apps/api/in.wav", "sox --i apps/legacy/in.wav", "apps/api/greylag.sh"),
    ),
    (
        P("mpv-lua-leftover-osd", "hoopoe", "mpv leftover vs mpv.conf", "mpv", "0.34.1", "0.39.0", False, "mpv.conf", "apps/api/mpv.conf", "osc=yes # 0.34.1", "osc=yes # 0.39.0", "mp.osd_message(\"ok\")", "mp.commandv(\"show-text\", \"ok\")", "mp.set_property(\"loop\", \"inf\")", "mp.set_property_native(\"loop-file\", \"inf\")", "osd_message + loop → show-text + loop-file", "mpv --version | head -n 1", "mpv --no-config --vo=null --ao=null apps/api/a.mp4 --frames=1", "mpv --no-config --vo=null --ao=null apps/legacy/a.mp4 --frames=1", "apps/api/scripts/hoopoe.lua"),
        P("vlc-plugin-leftover-intf", "iora", "VLC leftover vs vlcrc", "vlc", "3.0.18", "3.0.21", True, "vlcrc", "apps/api/vlcrc", "# vlc 3.0.18", "# vlc 3.0.21", "intf=dummy", "intf=http", "libvlc_media_new_path(inst, path)", "libvlc_media_new_location(inst, uri)", "dummy intf + new_path → http + new_location", "vlc --version | head -n 1", "vlc -I dummy --play-and-exit apps/api/a.mp4", "vlc -I dummy --play-and-exit apps/legacy/a.mp4", "apps/api/iora.c"),
    ),
    (
        P("fontforge-pe-leftover-glyphname", "jacamar", "FontForge leftover vs pe script", "fontforge", "20201107", "20230101", False, "api.pe", "apps/api/api.pe", "# fontforge 20201107", "# fontforge 20230101", "Select(\"A\")\\nSetGlyphName(\"A\")", "Select(\"A\")\\nSetUnicodeValue(0x41)", "Generate(\"api.ttf\")", "Generate(\"api.otf\")", "SetGlyphName + ttf → SetUnicodeValue + otf", "fontforge -version", "fontforge -script apps/api/api.pe", "fontforge -script apps/legacy/legacy.pe", "apps/api/jacamar.pe"),
        P("pixman-op-leftover-over", "kakapo", "pixman leftover vs meson.build", "pixman", "0.40.0", "0.44.2", True, "meson.build", "apps/api/meson.build", "dependency('pixman-1', version: '>=0.40')", "dependency('pixman-1', version: '>=0.44')", "use_composite16 = true", "use_composite32 = true", "pixman_image_composite(PIXMAN_OP_OVER, src, mask, dest, 0, 0, 0, 0, 0, 0, w, h)", "pixman_image_composite32(PIXMAN_OP_OVER, src, mask, dest, 0, 0, 0, 0, 0, 0, w, h)", "PIXMAN_OP_OVER 16-bit → composite32", "pkg-config --modversion pixman-1", "meson test -C apps/api/build", "meson test -C apps/legacy/build", "apps/api/src/kakapo.c"),
    ),
    (
        P("mesa-dri-leftover-swrast", "motmot", "Mesa leftover vs drirc", "mesa", "22.3.6", "24.3.4", False, "drirc", "apps/api/drirc", "<driconf><!-- 22.3.6 -->", "<driconf><!-- 24.3.4 -->", "LIBGL_ALWAYS_SOFTWARE=1", "MESA_LOADER_DRIVER_OVERRIDE=llvmpipe", "glXCreateContext(dpy, vis, 0, True)", "eglCreateContext(dpy, cfg, EGL_NO_CONTEXT, attrs)", "swrast + glX → llvmpipe + egl", "glxinfo -B | head || true", "eglinfo | head || true", "eglinfo | head || true", "apps/api/motmot.c"),
        P("xorg-proto-leftover-keysym", "nunbird", "Xorg proto leftover vs keysymdef", "xorg-proto", "2021.5", "2024.1", True, "keysymdef.h", "apps/api/keysymdef.h", "/* xorgproto 2021.5 */", "/* xorgproto 2024.1 */", "XK_Page_Up", "XK_Prior", "XKeysymToKeycode(dpy, XK_Page_Up)", "XKeysymToKeycode(dpy, XK_Prior)", "XK_Page_Up → XK_Prior", "pkg-config --modversion xproto", "gcc -E apps/api/nunbird.c | head", "gcc -E apps/legacy/nunbird.c | head", "apps/api/nunbird.c"),
    ),
    (
        P("moltenvk-mvk-leftover-surface", "pitta", "MoltenVK leftover vs MoltenVK_icd", "MoltenVK", "1.2.4", "1.2.11", False, "MoltenVK_icd.json", "apps/api/MoltenVK_icd.json", "\"api_version\": \"1.2.4\"", "\"api_version\": \"1.2.11\"", "vkCreateMacOSSurfaceMVK(inst, &ci, NULL, &surf)", "vkCreateMetalSurfaceEXT(inst, &ci, NULL, &surf)", "VK_MVK_macos_surface", "VK_EXT_metal_surface", "vkCreateMacOSSurfaceMVK → vkCreateMetalSurfaceEXT", "vulkaninfo --summary | head || true", "ctest --test-dir apps/api", "ctest --test-dir apps/legacy", "apps/api/src/pitta.mm"),
        P("metal-metallib-leftover-air", "riflebird", "Metal leftover vs metallib", "metal", "3.0", "3.2", True, "Shaders.metal", "apps/api/Shaders.metal", "// metal 3.0", "// metal 3.2", "xcrun -sdk macosx metal -c Shaders.metal -o Shaders.air", "xcrun -sdk macosx metal -c Shaders.metal -o Shaders.ir", "newBufferWithLength:options:", "newBufferWithLength:options:offset:", "air → ir + buffer offset", "xcrun metal --version || true", "xcrun -sdk macosx metallib apps/api/Shaders.ir -o /tmp/api.metallib || true", "xcrun -sdk macosx metallib apps/legacy/Shaders.ir -o /tmp/legacy.metallib || true", "apps/api/riflebird.metal"),
    ),
    (
        P("dxc-hlsl-leftover-register", "scrubwren", "DXC leftover vs hlsl", "dxc", "1.7.2212", "1.8.2407", False, "api.hlsl", "apps/api/api.hlsl", "// dxc 1.7.2212", "// dxc 1.8.2407", "cbuffer C : register(b0) { float4 x; };", "ConstantBuffer<C> c : register(b0, space0);", "Texture2D t : register(t0);", "Texture2D<float4> t : register(t0, space0);", "cbuffer register(b0) → ConstantBuffer space0", "dxc --version || true", "dxc -T vs_6_0 apps/api/api.hlsl", "dxc -T vs_6_0 apps/legacy/legacy.hlsl", "apps/api/scrubwren.hlsl"),
        P("shaderc-glslc-leftover-targetenv", "tailorbird", "shaderc leftover vs glslc flags", "shaderc", "2022.2", "2024.4", True, "compile_flags.txt", "apps/api/compile_flags.txt", "-fshader-stage=vertex # 2022.2", "-fshader-stage=vertex # 2024.4", "-fauto-bind-uniforms", "-fhlsl-iomap", "glslc -c --target-env=vulkan1.1 api.vert", "glslc -c --target-env=vulkan1.3 api.vert", "auto-bind-uniforms + vulkan1.1 → hlsl-iomap + vulkan1.3", "glslc --version | head -n 1", "glslc -c apps/api/api.vert", "glslc -c apps/legacy/legacy.vert", "apps/api/tailorbird.vert"),
    ),
    (
        P("itk-gdcm-leftover-vr", "vanga", "GDCM leftover vs CMakeLists", "gdcm", "3.0.20", "3.0.24", False, "CMakeLists.txt", "apps/api/CMakeLists.txt", "find_package(GDCM 3.0.20 REQUIRED)", "find_package(GDCM 3.0.24 REQUIRED)", "gdcm::VR vr = gdcm::VR::VRINVALID;", "gdcm::VR vr = gdcm::VR::INVALID;", "reader.Read()", "reader.ReadUpToTag(gdcm::Tag(0x7fe0, 0x0010))", "VRINVALID → INVALID + ReadUpToTag", "gdcmconv --version | head || true", "ctest --test-dir apps/api", "ctest --test-dir apps/legacy", "apps/api/src/vanga.cpp"),
        P("openlayers-ol-leftover-source", "whistler", "OpenLayers leftover vs ol package", "ol", "6.15.1", "10.3.1", True, "package.json", "apps/api/package.json", "\"ol\": \"6.15.1\"", "\"ol\": \"10.3.1\"", "new Vector({url: u, format: new GeoJSON()})", "new VectorSource({url: u, format: new GeoJSON()})", "new ol.Map({target: 'm'})", "new Map({target: 'm'})", "ol.Map + Vector → Map + VectorSource", "npm --prefix apps/api ls ol || true", "npm test --prefix apps/api", "npm test --prefix apps/legacy", "apps/api/src/whistler.js"),
    ),
    (
        P("leaflet-js-leftover-lmap", "yuhina", "Leaflet leftover vs leaflet-src", "leaflet", "1.7.1", "1.9.4", False, "package.json", "apps/api/package.json", "\"leaflet\": \"1.7.1\"", "\"leaflet\": \"1.9.4\"", "L.tileLayer(url, {useCache: true})", "L.tileLayer(url, {crossOrigin: true})", "map.invalidateSize(true)", "map.invalidateSize({animate: false, pan: false})", "useCache + invalidateSize bool → crossOrigin + options", "npm --prefix apps/api ls leaflet || true", "npm test --prefix apps/api", "npm test --prefix apps/legacy", "apps/api/src/yuhina.js"),
        P("nominatim-lua-leftover-place", "antbird", "Nominatim leftover vs lua tagtransform", "nominatim", "4.1.1", "4.5.0", True, "flex-config.lua", "apps/api/flex-config.lua", "-- nominatim 4.1.1", "-- nominatim 4.5.0", "place.add_row({class='place', type='city'})", "place:add_row({class='place', type='city'})", "osm2pgsql.process_node = function(o) end", "function nominatim.process_node(o) end", "place.add_row + osm2pgsql.process_* → :add_row + nominatim.process_*", "nominatim --version || true", "nominatim refresh --postcodes --project-dir apps/api || true", "nominatim refresh --postcodes --project-dir apps/legacy || true", "apps/api/antbird.lua"),
    ),
    (
        P("photon-es-leftover-synonym", "becard", "Photon leftover vs elasticsearch synonyms", "photon", "0.3.5", "0.6.1", False, "synonyms.txt", "apps/api/synonyms.txt", "# photon 0.3.5", "# photon 0.6.1", "st, street", "st, street, strasse", "index.analysis.filter.synonym.synonyms_path", "index.analysis.filter.synonym_graph.synonyms_path", "synonym filter → synonym_graph", "java -jar photon.jar --version || true", "java -jar photon.jar -nominatim-import -host localhost || true", "java -jar photon.jar -nominatim-import -host localhost || true", "apps/api/becard.txt"),
        P("chroma-coll-leftover-embed", "cotinga", "Chroma leftover vs collection", "chromadb", "0.4.15", "0.6.3", True, "requirements.txt", "apps/api/requirements.txt", "chromadb==0.4.15", "chromadb==0.6.3", "client.create_collection(\"api\", embedding_function=ef)", "client.get_or_create_collection(\"api\", embedding_function=ef, configuration={\"hnsw\": {\"space\": \"cosine\"}})", "col.add(documents=docs, metadatas=meta, ids=ids)", "col.upsert(documents=docs, metadatas=meta, ids=ids)", "create_collection + add → get_or_create + upsert", "python3 -c 'import chromadb' || true", "python3 apps/api/tests.py", "python3 apps/legacy/tests.py", "apps/api/cotinga.py"),
    ),
    (
        P("pinecone-meta-leftover-filter", "doradito", "Pinecone leftover vs index config", "pinecone", "2.2.4", "5.4.2", False, "requirements.txt", "apps/api/requirements.txt", "pinecone-client==2.2.4", "pinecone==5.4.2", "pinecone.init(api_key=k, environment=e)", "Pinecone(api_key=k)", "index.query(v, top_k=5, filter={\"c\": {\"$eq\": 1}})", "index.query(vector=v, top_k=5, filter={\"c\": {\"$eq\": \"1\"}})", "pinecone.init + int filter → Pinecone() + string $eq", "python3 -c 'import pinecone' || true", "python3 apps/api/tests.py", "python3 apps/legacy/tests.py", "apps/api/doradito.py"),
        P("nmslib-space-leftover-cosinesimil", "elaenia", "NMSLIB leftover vs space", "nmslib", "2.1.1", "2.1.2", True, "requirements.txt", "apps/api/requirements.txt", "nmslib==2.1.1", "nmslib==2.1.2", "index = nmslib.init(method='hnsw', space='cosinesimil')", "index = nmslib.init(method='hnsw', space='l2')", "index.createIndex({'post': 2}, print_progress=True)", "index.createIndex({'post': 0}, print_progress=False)", "cosinesimil + post 2 → l2 + post 0", "python3 -c 'import nmslib' || true", "python3 apps/api/tests.py", "python3 apps/legacy/tests.py", "apps/api/elaenia.py"),
    ),
    (
        P("matlab-toolbox-leftover-addpath", "gnateater", "MATLAB leftover vs pathdef", "matlab", "R2021b", "R2024b", False, "pathdef.m", "apps/api/pathdef.m", "% R2021b", "% R2024b", "addpath(genpath('toolbox'))", "matlab.addons.install('toolbox.mltbx')", "savepath", "matlab.addons.enableAddon('Api')", "addpath genpath → addons.install", "matlab -batch 'version' || true", "matlab -batch \"run('apps/api/tests.m')\"", "matlab -batch \"run('apps/legacy/tests.m')\"", "apps/api/gnateater.m"),
        P("scilab-atoms-leftover-atomsload", "inca", "Scilab leftover vs atoms", "scilab", "6.1.1", "2024.1.0", True, "atoms", "apps/api/atoms", "ATOMSVERSION=1.1.3 # 6.1.1", "ATOMSVERSION=1.2.0 # 2024.1.0", "atomsLoad('api')", "atomsInstall('api'); atomsLoad('api')", "exec('api.sci', -1)", "exec('api.sce', -1)", "atomsLoad-only + .sci → atomsInstall + .sce", "scilab -version | head -n 1", "scilab -nwni -f apps/api/tests.sce", "scilab -nwni -f apps/legacy/tests.sce", "apps/api/inca.sce"),
    ),
    (
        P("gnuplot-loadpath-leftover-setterm", "leafbird", "gnuplot leftover vs gnuplotrc", "gnuplot", "5.4.4", "6.0.1", False, "gnuplotrc", "apps/api/gnuplotrc", "# gnuplot 5.4.4", "# gnuplot 6.0.1", "set term pngcairo", "set term pngcairo enhanced", "set loadpath 'scripts'", "set loadpath 'scripts' 'lib'", "set term pngcairo + single loadpath → enhanced + multi", "gnuplot --version", "gnuplot apps/api/api.gp", "gnuplot apps/legacy/legacy.gp", "apps/api/leafbird.gp"),
        P("stata-ado-leftover-version", "miner", "Stata leftover vs profile.do", "stata", "17", "18", True, "profile.do", "apps/api/profile.do", "* stata 17", "* stata 18", "version 17", "version 18", "reg y x, robust", "regress y x, vce(robust)", "reg , robust → regress , vce(robust)", "stata -b version || true", "stata -b do apps/api/tests.do", "stata -b do apps/legacy/tests.do", "apps/api/miner.do"),
    ),
    (
        P("sas-autocall-leftover-macro", "nicator", "SAS leftover vs autoexec", "sas", "9.4M7", "viya4", False, "autoexec.sas", "apps/api/autoexec.sas", "/* sas 9.4M7 */", "/* sas viya4 */", "options mautosource sasautos=('macros')", "options mautosource sasautos=('macros' 'shared')", "%include 'api.sas';", "proc lua; submit; print('api'); endsubmit; run;", "%include + sasautos single → lua + multi sasautos", "sas -version || true", "sas apps/api/tests.sas", "sas apps/legacy/tests.sas", "apps/api/nicator.sas"),
        P("jmp-jsl-leftover-newtable", "oliveback", "JMP leftover vs jsl", "jmp", "16.2", "18.0", True, "api.jsl", "apps/api/api.jsl", "// jmp 16.2", "// jmp 18.0", "dt = New Table(\"api\")", "dt = Open(\"api.jmp\", invisible)", "dt << New Column(\"x\", Numeric)", "dt << New Column(\"x\", Numeric, Continuous)", "New Table + Numeric → Open invisible + Continuous", "jmp -v || true", "jmp -j apps/api/tests.jsl", "jmp -j apps/legacy/tests.jsl", "apps/api/oliveback.jsl"),
    ),
    (
        P("hexo-yml-leftover-highlight", "prinia", "Hexo leftover vs _config.yml", "hexo", "6.3.0", "7.3.0", False, "_config.yml", "apps/api/_config.yml", "highlight:\n  enable: true # 6.3.0", "syntax_highlighter: prismjs # 7.3.0", "highlight:\n  enable: true", "prismjs:\n  preprocess: true", "hexo-generator-index", "hexo-generator-index-pin", "highlight → prismjs + index-pin", "npx hexo --version", "npx hexo generate --cwd apps/api", "npx hexo generate --cwd apps/legacy", "apps/api/prinia.md"),
        P("eleventy-cfg-leftover-passthrough", "redpoll", "Eleventy leftover vs eleventy.js", "eleventy", "1.0.2", "3.0.0", True, ".eleventy.js", "apps/api/.eleventy.js", "module.exports = function(e) { /* 1.0.2 */ }", "export default function(e) { /* 3.0.0 */ }", "e.addPassthroughCopy(\"img\")", "e.addPassthroughCopy({ img: \"assets/img\" })", "return { dir: { input: \".\", output: \"_site\" } }", "return { dir: { input: \"src\", output: \"_site\" } }", "CJS addPassthroughCopy string → ESM map + src input", "npx @11ty/eleventy --version", "npx @11ty/eleventy --input apps/api", "npx @11ty/eleventy --input apps/legacy", "apps/api/redpoll.md"),
    ),
    (
        P("honkit-json-leftover-plugins", "sibia", "HonKit leftover vs book.json", "honkit", "4.0.7", "6.0.2", False, "book.json", "apps/api/book.json", "\"gitbook\": \"3.2.3\" // honkit 4", "\"honkit\": \"6.0.2\"", "\"plugins\": [\"-sharing\", \"ga\"]", "\"plugins\": [\"-sharing\", \"@honkit/honkit-plugin-ga\"]", "\"pluginsConfig\": { \"ga\": { \"token\": \"UA-1\" } }", "\"pluginsConfig\": { \"ga\": { \"token\": \"G-1\" } }", "gitbook plugins + UA → @honkit plugin + G-", "npx honkit --version", "npx honkit build apps/api", "npx honkit build apps/legacy", "apps/api/sibia.md"),
        P("gitbook-book-leftover-structure", "tchagra", "GitBook leftover vs book.json", "gitbook", "3.2.3", "legacy-3.2.3-honkit", True, "book.json", "apps/api/book.json", "\"structure\": { \"readme\": \"README.md\" }", "\"structure\": { \"readme\": \"intro.md\" }", "gitbook.page.hasChanged", "honkit.page.hasChanged", "require('gitbook-plugin-ga')", "require('@honkit/honkit-plugin-ga')", "structure readme + gitbook-plugin → honkit plugin", "npx gitbook --version || true", "npx gitbook build apps/api", "npx gitbook build apps/legacy", "apps/api/tchagra.md"),
    ),
    (
        P("pkgconfig-pc-leftover-privreq", "uirapuru", "pkg-config leftover vs .pc", "pkg-config", "0.29.2", "2.3.0", False, "api.pc", "apps/api/api.pc", "Version: 0.29.2", "Version: 2.3.0", "Requires.private: glib-2.0", "Requires: glib-2.0", "pkg-config --exists api", "pkgconf --exists api", "Requires.private + pkg-config → Requires + pkgconf", "pkg-config --version", "pkg-config --modversion api", "pkg-config --modversion api", "apps/api/uirapuru.pc"),
        P("gettext-po-leftover-msgctxt", "violetear", "gettext leftover vs .po", "gettext", "0.21", "0.23.1", True, "messages.po", "apps/api/messages.po", "\"Project-Id-Version: api 0.21\\n\"", "\"Project-Id-Version: api 0.23\\n\"", "msgid \"Save\"", "msgctxt \"button\"\nmsgid \"Save\"", "gettext(\"Save\")", "pgettext(\"button\", \"Save\")", "msgid only → msgctxt + pgettext", "gettext --version | head -n 1", "msgfmt -c -o /tmp/api.mo apps/api/messages.po", "msgfmt -c -o /tmp/legacy.mo apps/legacy/messages.po", "apps/api/violetear.c"),
    ),
    (
        P("intltool-xml-leftover-merge", "woodcreeper", "intltool leftover vs xml.in", "intltool", "0.51.0", "0.51.0+gettext", False, "api.xml.in", "apps/api/api.xml.in", "<!-- intltool 0.51.0 -->", "<!-- gettext xml 0.23 -->", "intltool-merge -x po api.xml.in api.xml", "msgfmt --xml --template api.xml.in -d po -o api.xml", "_(\"Name\")", "gettext(\"Name\")", "intltool-merge -x → msgfmt --xml", "intltool-merge --version || true", "intltool-update -p || true", "msgfmt --xml --template apps/legacy/api.xml.in -d po -o /tmp/legacy.xml || true", "apps/api/woodcreeper.xml.in"),
        P("desktop-file-leftover-keywords", "yellowhead", "desktop-file leftover vs .desktop", "desktop-file-utils", "0.26", "0.27", True, "api.desktop", "apps/api/api.desktop", "Version=1.0 # 0.26", "Version=1.5 # 0.27", "Keywords=api;tool;", "Keywords=api;tool;cli;", "OnlyShowIn=Unity;", "OnlyShowIn=GNOME;KDE;", "Unity OnlyShowIn + Keywords → GNOME;KDE", "desktop-file-validate --version || true", "desktop-file-validate apps/api/api.desktop", "desktop-file-validate apps/legacy/legacy.desktop", "apps/api/yellowhead.desktop"),
    ),
    (
        P("appstream-xml-leftover-component", "bananaquit", "AppStream leftover vs metainfo", "appstream", "0.15.5", "1.0.3", False, "api.metainfo.xml", "apps/api/api.metainfo.xml", "<component type=\"desktop\"><!-- 0.15.5 -->", "<component type=\"desktop-application\"><!-- 1.0.3 -->", "<id>com.api.App.desktop</id>", "<id>com.api.App</id>", "<metadata_license>CC0-1.0</metadata_license>", "<metadata_license>FSFAP</metadata_license>", "desktop component + .desktop id → desktop-application", "appstreamcli --version", "appstreamcli validate apps/api/api.metainfo.xml", "appstreamcli validate apps/legacy/legacy.metainfo.xml", "apps/api/bananaquit.metainfo.xml"),
        P("osgi-manifest-leftover-bundle", "cacique", "OSGi leftover vs MANIFEST.MF", "osgi", "7.0.0", "8.1.0", True, "MANIFEST.MF", "apps/api/MANIFEST.MF", "Bundle-Version: 7.0.0", "Bundle-Version: 8.1.0", "Bundle-SymbolicName: api;singleton:=true", "Bundle-SymbolicName: api", "Require-Capability: osgi.ee;filter:=\"(&(osgi.ee=JavaSE)(version=1.8))\"", "Require-Capability: osgi.ee;filter:=\"(&(osgi.ee=JavaSE)(version=17))\"", "singleton + JavaSE 1.8 → JavaSE 17", "java --version | head -n 1", "bnd build apps/api", "bnd build apps/legacy", "apps/api/cacique.MF"),
    ),
    (
        P("jpms-module-leftover-requires", "dinornis", "JPMS leftover vs module-info", "jdk", "11", "21", False, "module-info.java", "apps/api/module-info.java", "module api { /* 11 */ }", "module api { /* 21 */ }", "requires java.xml.bind;", "requires java.xml;", "requires static lombok;", "requires static org.jspecify;", "java.xml.bind + lombok → java.xml + jspecify", "javac --version", "javac --module-source-path apps/api -d /tmp/api apps/api/module-info.java", "javac --module-source-path apps/legacy -d /tmp/legacy apps/legacy/module-info.java", "apps/api/src/Dinornis.java"),
        P("jpackage-cfg-leftover-addmods", "erpornis", "jpackage leftover vs cfg", "jpackage", "17", "21", True, "jpackage.cfg", "apps/api/jpackage.cfg", "--runtime-image jre17", "--runtime-image jre21", "--add-modules java.se", "--add-modules java.base,java.desktop", "--win-dir-chooser", "--linux-shortcut", "java.se + win-dir-chooser → explicit modules + linux-shortcut", "jpackage --version", "jpackage @apps/api/jpackage.cfg", "jpackage @apps/legacy/jpackage.cfg", "apps/api/erpornis.cfg"),
    ),
    (
        P("graalvm-native-leftover-reflect", "firetail", "GraalVM leftover vs native-image", "native-image", "22.3.1", "24.1.1", False, "reflect-config.json", "apps/api/reflect-config.json", "[{\"name\":\"api.Foo\"}] // 22.3.1", "[{\"name\":\"api.Foo\"}] // 24.1.1", "--initialize-at-build-time=api", "--initialize-at-run-time=api.Lazy", "native-image -H:+ReportUnsupportedElementsAtRuntime", "native-image --install-exit-handlers", "build-time init + ReportUnsupported → run-time + install-exit-handlers", "native-image --version", "native-image -cp apps/api api.Main", "native-image -cp apps/legacy api.Main", "apps/api/firetail.json"),
        P("quarkus-ext-leftover-arc", "antpitta", "Quarkus leftover vs extensions", "quarkus", "2.16.12", "3.17.5", True, "application.properties", "apps/api/application.properties", "quarkus.http.port=8080 # 2.16", "quarkus.http.port=8080 # 3.17", "quarkus.arc.remove-unused-beans=fwk", "quarkus.arc.remove-unused-beans=all", "javax.ws.rs.GET", "jakarta.ws.rs.GET", "arc fwk + javax.ws.rs → all + jakarta.ws.rs", "quarkus --version || true", "mvn -f apps/api/pom.xml -q test", "mvn -f apps/legacy/pom.xml -q test", "apps/api/src/main/java/Antpitta.java"),
    ),
    (
        P("nginx-conf-leftover-http2", "miner2", "nginx leftover vs nginx.conf", "nginx", "1.18.0", "1.26.2", False, "nginx.conf", "apps/api/nginx.conf", "listen 443 ssl http2; # 1.18", "listen 443 ssl; http2 on; # 1.26", "listen 443 ssl http2;", "listen 443 ssl;\n    http2 on;", "ssl_protocols TLSv1.1 TLSv1.2;", "ssl_protocols TLSv1.2 TLSv1.3;", "listen http2 + TLSv1.1 → http2 on + TLS1.3", "nginx -v", "nginx -t -c apps/api/nginx.conf", "nginx -t -c apps/legacy/nginx.conf", "apps/api/miner2.conf"),
        P("haproxy-cfg-leftover-reqirep", "nicobar", "HAProxy leftover vs haproxy.cfg", "haproxy", "2.4.22", "3.0.7", True, "haproxy.cfg", "apps/api/haproxy.cfg", "# haproxy 2.4.22", "# haproxy 3.0.7", "reqirep ^Host: Host:\\ api.example", "http-request replace-header Host .* api.example", "option http-server-close", "option http-keep-alive", "reqirep + server-close → replace-header + keep-alive", "haproxy -v | head -n 1", "haproxy -c -f apps/api/haproxy.cfg", "haproxy -c -f apps/legacy/haproxy.cfg", "apps/api/nicobar.cfg"),
    ),
    (
        P("caddy-caddyfile-leftover-redir", "oilbird2", "Caddy leftover vs Caddyfile", "caddy", "2.5.2", "2.9.1", False, "Caddyfile", "apps/api/Caddyfile", "# caddy 2.5.2", "# caddy 2.9.1", "redir /old /new", "redir /old /new permanent", "encode gzip", "encode zstd gzip", "redir + gzip → permanent + zstd", "caddy version", "caddy validate --config apps/api/Caddyfile", "caddy validate --config apps/legacy/Caddyfile", "apps/api/oilbird2.Caddyfile"),
        P("traefik-yml-leftover-frontend", "pittasoma", "Traefik leftover vs traefik.yml", "traefik", "2.9.10", "3.2.3", True, "traefik.yml", "apps/api/traefik.yml", "# traefik 2.9.10", "# traefik 3.2.3", "http.frontends.api.backend=api", "http.routers.api.service=api", "providers.docker.swarmMode=true", "providers.swarm=true", "frontends.backend + swarmMode → routers.service + providers.swarm", "traefik version", "traefik --configFile=apps/api/traefik.yml --ping=false || true", "traefik --configFile=apps/legacy/traefik.yml --ping=false || true", "apps/api/pittasoma.yml"),
    ),
    (
        P("envoy-yaml-leftover-rds", "quelea2", "Envoy leftover vs bootstrap", "envoy", "1.22.11", "1.32.3", False, "envoy.yaml", "apps/api/envoy.yaml", "# envoy 1.22.11", "# envoy 1.32.3", "rds: { route_config_name: api, config_source: { ads: {} } }", "rds_config_source: { ads: {} }", "typed_config: { \"@type\": type.googleapis.com/envoy.extensions.filters.network.http_connection_manager.v3.HttpConnectionManager }", "typed_config: { \"@type\": type.googleapis.com/envoy.extensions.filters.network.http_connection_manager.v3.HttpConnectionManager, stat_prefix: api }", "rds block → rds_config_source + stat_prefix", "envoy --version", "envoy --mode validate -c apps/api/envoy.yaml", "envoy --mode validate -c apps/legacy/envoy.yaml", "apps/api/quelea2.yaml"),
        P("linkerd-yml-leftover-tap", "rifleman", "Linkerd leftover vs values", "linkerd", "2.12.5", "2.16.2", True, "values.yaml", "apps/api/values.yaml", "# linkerd 2.12.5", "# linkerd 2.16.2", "tap.enabled: true", "policyController.enabled: true", "proxy.image.name: cr.l5d.io/linkerd/proxy", "proxy.image.name: cr.l5d.io/linkerd/proxy-wait", "tap.enabled → policyController + proxy-wait", "linkerd version --client", "linkerd check --pre || true", "linkerd check --pre || true", "apps/api/rifleman.yaml"),
    ),
    (
        P("istio-vs-leftover-http", "scrubbird", "Istio leftover vs VirtualService", "istio", "1.16.7", "1.24.2", False, "virtualservice.yaml", "apps/api/virtualservice.yaml", "apiVersion: networking.istio.io/v1beta1 # 1.16", "apiVersion: networking.istio.io/v1 # 1.24", "http:\n  - match:\n      - uri:\n          prefix: /api", "http:\n  - match:\n      - uri:\n          prefix: /api/\n    retries:\n      attempts: 3", "destination.subset: v1", "destination.subset: stable", "v1beta1 prefix /api + subset v1 → v1 + retries + stable", "istioctl version --short", "istioctl analyze -f apps/api/virtualservice.yaml", "istioctl analyze -f apps/legacy/virtualservice.yaml", "apps/api/scrubbird.yaml"),
        P("coredns-corefile-leftover-proxy", "sunbittern", "CoreDNS leftover vs Corefile", "coredns", "1.9.4", "1.12.0", True, "Corefile", "apps/api/Corefile", "# coredns 1.9.4", "# coredns 1.12.0", "proxy . /etc/resolv.conf", "forward . /etc/resolv.conf", "cache 30", "cache 30 {\n    success 9984\n    denial 9984\n}", "proxy → forward + cache success/denial", "coredns --version", "coredns -conf apps/api/Corefile -dns.port 0 || true", "coredns -conf apps/legacy/Corefile -dns.port 0 || true", "apps/api/sunbittern.Corefile"),
    ),
    (
        P("bind-named-leftover-zone", "tailorbird2", "BIND leftover vs named.conf", "bind", "9.16.44", "9.20.4", False, "named.conf", "apps/api/named.conf", "# bind 9.16.44", "# bind 9.20.4", "zone \"api.example\" { type master; file \"api.zone\"; };", "zone \"api.example\" { type primary; file \"api.zone\"; };", "dnssec-enable yes;", "dnssec-validation auto;", "type master + dnssec-enable → type primary + validation auto", "named -v", "named-checkconf apps/api/named.conf", "named-checkconf apps/legacy/named.conf", "apps/api/tailorbird2.conf"),
        P("unbound-conf-leftover-stub", "tinamou", "Unbound leftover vs unbound.conf", "unbound", "1.16.3", "1.22.0", True, "unbound.conf", "apps/api/unbound.conf", "# unbound 1.16.3", "# unbound 1.22.0", "stub-zone: name: \"api.\" stub-addr: 10.0.0.1", "forward-zone: name: \"api.\" forward-addr: 10.0.0.1", "so-rcvbuf: 4m", "so-rcvbuf: 8m", "stub-zone → forward-zone + 8m rcvbuf", "unbound -V | head -n 1", "unbound-checkconf apps/api/unbound.conf", "unbound-checkconf apps/legacy/unbound.conf", "apps/api/tinamou.conf"),
    ),
    (
        P("dnsmasq-conf-leftover-dhcp", "umbrellabird2", "dnsmasq leftover vs dnsmasq.conf", "dnsmasq", "2.86", "2.90", False, "dnsmasq.conf", "apps/api/dnsmasq.conf", "# dnsmasq 2.86", "# dnsmasq 2.90", "dhcp-range=10.0.0.50,10.0.0.150,12h", "dhcp-range=set:api,10.0.0.50,10.0.0.150,12h", "log-facility=/var/log/dnsmasq.log", "log-debug", "dhcp-range + log-facility → tagged range + log-debug", "dnsmasq --version | head -n 1", "dnsmasq --test --conf-file=apps/api/dnsmasq.conf", "dnsmasq --test --conf-file=apps/legacy/dnsmasq.conf", "apps/api/umbrellabird2.conf"),
        P("keepalived-conf-leftover-vrrp", "veery2", "Keepalived leftover vs keepalived.conf", "keepalived", "2.2.7", "2.3.1", True, "keepalived.conf", "apps/api/keepalived.conf", "# keepalived 2.2.7", "# keepalived 2.3.1", "virtual_router_id 51", "virtual_router_id 51\n    version 3", "advert_int 1", "advert_int 1\n    preempt_delay 5", "vrrp v2 default → version 3 + preempt_delay", "keepalived --version | head -n 1", "keepalived -t -f apps/api/keepalived.conf", "keepalived -t -f apps/legacy/keepalived.conf", "apps/api/veery2.conf"),
    ),
    (
        P("bird-conf-leftover-filter", "whydah2", "BIRD leftover vs bird.conf", "bird", "2.0.10", "2.15.1", False, "bird.conf", "apps/api/bird.conf", "# bird 2.0.10", "# bird 2.15.1", "filter api { if net ~ 10.0.0.0/8 then accept; }", "filter api { if net ~ [ 10.0.0.0/8+ ] then accept; }", "protocol kernel { persist; }", "protocol kernel { persist; ipv4 { import none; export all; }; }", "net ~ prefix → prefix set + ipv4 channel", "bird --version | head -n 1", "bird -p -c apps/api/bird.conf", "bird -p -c apps/legacy/bird.conf", "apps/api/whydah2.conf"),
        P("frr-vtysh-leftover-ipv6", "xenops2", "FRR leftover vs frr.conf", "frr", "8.4.4", "10.2.1", True, "frr.conf", "apps/api/frr.conf", "# frr 8.4.4", "# frr 10.2.1", "ipv6 nd ra-interval 10", "ipv6 nd ra-interval msec 10000", "router ospf", "router ospf vrf api", "ra-interval seconds + ospf → msec + vrf", "vtysh -c 'show version' | head || true", "vtysh -f apps/api/frr.conf || true", "vtysh -f apps/legacy/frr.conf || true", "apps/api/xenops2.conf"),
    ),
    (
        P("strongswan-conf-leftover-left", "yellowhead2", "strongSwan leftover vs ipsec.conf", "strongswan", "5.9.8", "5.9.14", False, "ipsec.conf", "apps/api/ipsec.conf", "# strongswan 5.9.8", "# strongswan 5.9.14", "left=10.0.0.1", "local_addrs=10.0.0.1", "ike=aes256-sha256-modp2048!", "ike=aes256-sha256-ecp256!", "left= + modp2048 → local_addrs + ecp256", "ipsec --version | head -n 1", "ipsec start --conf apps/api/ipsec.conf --nofork || true", "ipsec start --conf apps/legacy/ipsec.conf --nofork || true", "apps/api/yellowhead2.conf"),
        P("wireguard-conf-leftover-preshared", "zahle", "WireGuard leftover vs wg0.conf", "wireguard", "1.0.20210914", "1.0.20220627", True, "wg0.conf", "apps/api/wg0.conf", "# wireguard 20210914", "# wireguard 20220627", "PresharedKey = AAA=", "PresharedKey = BBB=", "AllowedIPs = 0.0.0.0/0", "AllowedIPs = 10.0.0.0/8, 192.168.0.0/16", "PresharedKey rotate + default route → split AllowedIPs", "wg --version", "wg-quick strip apps/api/wg0.conf", "wg-quick strip apps/legacy/wg0.conf", "apps/api/zahle.conf"),
    ),
    (
        P("openvpn-ovpn-leftover-complzo", "antshrike", "OpenVPN leftover vs client.ovpn", "openvpn", "2.5.9", "2.6.12", False, "client.ovpn", "apps/api/client.ovpn", "# openvpn 2.5.9", "# openvpn 2.6.12", "comp-lzo", "compress lz4-v2", "tun-ipv6", "ifconfig-ipv6 2001:db8::2/64 2001:db8::1", "comp-lzo + tun-ipv6 → compress lz4-v2 + ifconfig-ipv6", "openvpn --version | head -n 1", "openvpn --config apps/api/client.ovpn --verb 0 --connect-retry-max 1 || true", "openvpn --config apps/legacy/client.ovpn --verb 0 --connect-retry-max 1 || true", "apps/api/antshrike.ovpn"),
        P("ipsec-conf-leftover-ikev1", "becard2", "Libreswan leftover vs ipsec.conf", "libreswan", "4.9", "5.1", True, "ipsec.conf", "apps/api/ipsec.conf", "# libreswan 4.9", "# libreswan 5.1", "ikev2=never", "ikev2=insist", "authby=secret", "authby=rsasig", "ikev2=never + secret → insist + rsasig", "ipsec --version | head -n 1", "ipsec addconn --config apps/api/ipsec.conf --checkconfig || true", "ipsec addconn --config apps/legacy/ipsec.conf --checkconfig || true", "apps/api/becard2.conf"),
    ),
    (
        P("postfix-cf-leftover-mynetworks", "cotinga2", "Postfix leftover vs main.cf", "postfix", "3.6.4", "3.9.1", False, "main.cf", "apps/api/main.cf", "# postfix 3.6.4", "# postfix 3.9.1", "mynetworks = 192.168.0.0/16", "mynetworks = 192.168.0.0/16 10.0.0.0/8", "smtpd_use_tls = yes", "smtpd_tls_security_level = may", "mynetworks expand + use_tls → tls_security_level", "postconf -d mail_version", "postconf -c apps/api -n", "postconf -c apps/legacy -n", "apps/api/cotinga2.cf"),
        P("exim-conf-leftover-acl", "doradito2", "Exim leftover vs exim.conf", "exim", "4.95", "4.98", True, "exim.conf", "apps/api/exim.conf", "# exim 4.95", "# exim 4.98", "acl_check_rcpt:\n  accept hosts = :", "acl_check_rcpt:\n  accept hosts = : +relay_from_hosts", "dns_ipv4_lookup = *", "dns_ipv4_lookup = !localhost", "bare hosts accept + ipv4 * → relay_from_hosts", "exim -bV | head -n 1", "exim -C apps/api/exim.conf -bV", "exim -C apps/legacy/exim.conf -bV", "apps/api/doradito2.conf"),
    ),
    (
        P("dovecot-conf-leftover-ssl", "elaenia2", "Dovecot leftover vs dovecot.conf", "dovecot", "2.3.16", "2.4.0", False, "dovecot.conf", "apps/api/dovecot.conf", "# dovecot 2.3.16", "# dovecot 2.4.0", "ssl = yes", "ssl = required", "mail_location = maildir:~/Maildir", "mail_driver = maildir\nmail_path = ~/Maildir", "ssl yes + mail_location → required + mail_driver", "dovecot --version", "doveconf -n -c apps/api/dovecot.conf", "doveconf -n -c apps/legacy/dovecot.conf", "apps/api/elaenia2.conf"),
        P("cyrus-imap-leftover-unixhierarchy", "firecrest2", "Cyrus leftover vs imapd.conf", "cyrus-imapd", "3.4.4", "3.8.4", True, "imapd.conf", "apps/api/imapd.conf", "# cyrus 3.4.4", "# cyrus 3.8.4", "unixhierarchysep: no", "unixhierarchysep: yes", "altnamespace: no", "altnamespace: yes", "unixhierarchysep no + altnamespace no → yes/yes", "cyradm --version || true", "cyrus -C apps/api/imapd.conf master -d || true", "cyrus -C apps/legacy/imapd.conf master -d || true", "apps/api/firecrest2.conf"),
    ),
    (
        P("spamassassin-cf-leftover-score", "gnatcatcher2", "SpamAssassin leftover vs local.cf", "spamassassin", "3.4.6", "4.0.1", False, "local.cf", "apps/api/local.cf", "# sa 3.4.6", "# sa 4.0.1", "score URIBL_BLOCKED 0", "score URIBL_BLOCKED 3.0", "use_bayes 1", "use_bayes 1\nbayes_auto_expire 1", "URIBL score 0 + bayes → 3.0 + auto_expire", "spamassassin --version | head -n 1", "spamassassin --lint -C apps/api", "spamassassin --lint -C apps/legacy", "apps/api/gnatcatcher2.cf"),
        P("rspamd-lua-leftover-metric", "honeyguide2", "Rspamd leftover vs metrics.conf", "rspamd", "3.4", "3.11", True, "metrics.conf", "apps/api/metrics.conf", "# rspamd 3.4", "# rspamd 3.11", "metric { name = \"default\"; }", "group \"default\" { }", "symbol \"R_DKIM_ALLOW\" { score = -0.2; }", "symbol \"R_DKIM_ALLOW\" { score = -1.0; }", "metric {} → group {} + DKIM score", "rspamadm --version | head -n 1", "rspamadm configtest -c apps/api", "rspamadm configtest -c apps/legacy", "apps/api/honeyguide2.lua"),
    ),
    (
        P("clamav-conf-leftover-databasedir", "ibis2", "ClamAV leftover vs clamd.conf", "clamav", "0.103.11", "1.4.1", False, "clamd.conf", "apps/api/clamd.conf", "# clamav 0.103.11", "# clamav 1.4.1", "DatabaseDirectory /var/lib/clamav", "DatabaseDirectory /var/lib/clamav\nConcurrentDatabaseReload no", "DetectPUA no", "AlertExceedsMax yes", "DatabaseDirectory only + DetectPUA → ConcurrentDatabaseReload + AlertExceedsMax", "clamd --version", "clamd --config-file=apps/api/clamd.conf -c || true", "clamd --config-file=apps/legacy/clamd.conf -c || true", "apps/api/ibis2.conf"),
        P("fail2ban-jail-leftover-actionban", "jabiru2", "Fail2ban leftover vs jail.local", "fail2ban", "0.11.2", "1.1.0", True, "jail.local", "apps/api/jail.local", "# fail2ban 0.11.2", "# fail2ban 1.1.0", "actionban = iptables -I f2b <name> 1 -s <ip> -j DROP", "actionban = nft add rule inet f2b <name> ip saddr <ip> drop", "banaction = iptables-multiport", "banaction = nftables-multiport", "iptables actionban → nftables", "fail2ban-client --version", "fail2ban-client -t -c apps/api || true", "fail2ban-client -t -c apps/legacy || true", "apps/api/jabiru2.local"),
    ),
    (
        P("logrotate-conf-leftover-notifempty", "kestrel2", "logrotate leftover vs logrotate.conf", "logrotate", "3.18.0", "3.22.0", False, "logrotate.conf", "apps/api/logrotate.conf", "# logrotate 3.18.0", "# logrotate 3.22.0", "notifempty", "ifempty", "su root adm", "su syslog adm", "notifempty + su root → ifempty + su syslog", "logrotate --version", "logrotate -d apps/api/logrotate.conf", "logrotate -d apps/legacy/logrotate.conf", "apps/api/kestrel2.conf"),
        P("syslogng-conf-leftover-filter", "lammergeier2", "syslog-ng leftover vs syslog-ng.conf", "syslog-ng", "3.35.1", "4.8.1", True, "syslog-ng.conf", "apps/api/syslog-ng.conf", "@version: 3.35", "@version: 4.8", "filter f_api { program(\"api\"); };", "filter f_api { program(\"api\") and not facility(mail); };", "destination d_api { file(\"/var/log/api.log\"); };", "destination d_api { file(\"/var/log/api.log\" persist-name(\"api\")); };", "program filter + file dest → not facility + persist-name", "syslog-ng --version | head -n 1", "syslog-ng -s -f apps/api/syslog-ng.conf", "syslog-ng -s -f apps/legacy/syslog-ng.conf", "apps/api/lammergeier2.conf"),
    ),
    (
        P("ghdl-vhdl-leftover-std", "oilbird3", "GHDL leftover vs ghdl.args", "ghdl", "2.0.0", "5.0.1", False, "ghdl.args", "apps/api/ghdl.args", "--std=08 # 2.0.0", "--std=08 # 5.0.1", "--ieee=synopsys", "--ieee=standard", "ghdl -a --std=08 api.vhdl", "ghdl -a --std=08 --workdir=work api.vhdl", "ieee=synopsys → standard + workdir", "ghdl --version | head -n 1", "ghdl -a apps/api/api.vhdl", "ghdl -a apps/legacy/legacy.vhdl", "apps/api/oilbird3.vhdl"),
        P("nvc-vhdl-leftover-relax", "pittasoma2", "NVC leftover vs nvc.args", "nvc", "1.9.2", "1.15.0", True, "nvc.args", "apps/api/nvc.args", "--std=2008 # 1.9.2", "--std=2019 # 1.15.0", "--relax=prefer-explicit", "--ieee-warnings=off", "nvc -a api.vhd", "nvc --std=2019 -a api.vhd", "std 2008 + relax → 2019 + ieee-warnings", "nvc --version | head -n 1", "nvc -a apps/api/api.vhd", "nvc -a apps/legacy/legacy.vhd", "apps/api/pittasoma2.vhd"),
    ),
    (
        P("cocotb-makefile-leftover-sim", "quelea3", "cocotb leftover vs Makefile", "cocotb", "1.7.2", "1.9.2", False, "Makefile", "apps/api/Makefile", "COCOTB_VERSION = 1.7.2", "COCOTB_VERSION = 1.9.2", "SIM=icarus", "SIM=verilator", "include $(shell cocotb-config --makefiles)/Makefile.inc", "include $(shell cocotb-config --makefiles)/Makefile.sim", "Makefile.inc + icarus → Makefile.sim + verilator", "cocotb-config --version", "make -C apps/api", "make -C apps/legacy", "apps/api/test_quelea3.py"),
        P("vunit-runpy-leftover-addsrc", "rifleman2", "VUnit leftover vs run.py", "vunit", "4.7.0", "5.0.0.dev6", True, "run.py", "apps/api/run.py", "# vunit 4.7.0", "# vunit 5.0.0", "vu.add_source_files(\"src/*.vhd\")", "vu.add_source_files(\"src/**/*.vhd\", allow_empty=False)", "vu.set_sim_option(\"modelsim.vsim_flags\", [\"-t\", \"1ps\"])", "vu.set_sim_option(\"nvc.sim_flags\", [\"--ieee-warnings=off\"])", "add_source_files + modelsim → glob + nvc.sim_flags", "python3 -c 'import vunit' || true", "python3 apps/api/run.py --list", "python3 apps/legacy/run.py --list", "apps/api/rifleman2.py"),
    ),
    (
        P("systemc-cmake-leftover-scmod", "scrubbird2", "SystemC leftover vs CMakeLists", "systemc", "2.3.3", "3.0.1", False, "CMakeLists.txt", "apps/api/CMakeLists.txt", "find_package(SystemCLanguage 2.3.3 REQUIRED)", "find_package(SystemCLanguage 3.0.1 REQUIRED)", "SC_MODULE(Api) { SC_CTOR(Api) {} };", "class Api : public sc_core::sc_module { public: SC_HAS_PROCESS(Api); explicit Api(sc_core::sc_module_name n); };", "sc_start(10, SC_NS);", "sc_core::sc_start(sc_core::sc_time(10, sc_core::SC_NS));", "SC_MODULE + SC_NS → sc_module + sc_time", "pkg-config --modversion systemc", "ctest --test-dir apps/api", "ctest --test-dir apps/legacy", "apps/api/src/scrubbird2.cpp"),
        P("amaranth-toml-leftover-nmigen", "sunbittern2", "Amaranth leftover vs pyproject", "amaranth", "0.3.0", "0.5.4", True, "pyproject.toml", "apps/api/pyproject.toml", "nmigen = \"0.3.0\"", "amaranth = \"0.5.4\"", "from nmigen import Elaboratable, Module", "from amaranth import Elaboratable, Module", "platform.build(m, do_program=False)", "platform.build(m, do_build=True)", "nmigen + do_program → amaranth + do_build", "python3 -c 'import amaranth' || true", "python3 -m pytest apps/api", "python3 -m pytest apps/legacy", "apps/api/sunbittern2.py"),
    ),
    (
        P("litex-py-leftover-soccore", "tailorbird3", "LiteX leftover vs litex_setup", "litex", "2022.08", "2024.12", False, "litex_setup.py", "apps/api/litex_setup.py", "# litex 2022.08", "# litex 2024.12", "from litex.soc.integration.soc_core import SoCCore", "from litex.soc.integration.soc import SoC", "SoCCore(platform, clk_freq, ident=\"api\")", "SoC(platform, clk_freq, ident=\"api\")", "SoCCore → SoC", "python3 -c 'import litex' || true", "python3 apps/api/test_soc.py", "python3 apps/legacy/test_soc.py", "apps/api/tailorbird3.py"),
        P("openlane-json-leftover-cfg", "tinamou2", "OpenLane leftover vs config.json", "openlane", "1.1.1", "2.2.9", True, "config.json", "apps/api/config.json", "\"PDK\": \"sky130A\" // 1.1.1", "\"PDK\": \"sky130A\" // 2.2.9", "\"CLOCK_PERIOD\": 10", "\"CLOCK_PERIOD\": 10.0", "run_designs.py --design api", "openlane --run-tag api config.json", "run_designs.py + int period → openlane CLI + float", "openlane --version || true", "openlane --smoke-test || true", "openlane --smoke-test || true", "apps/api/tinamou2.v"),
    ),
    (
        P("magic-tcl-leftover-gds", "umbrellabird3", "Magic leftover vs drc.tcl", "magic", "8.3.360", "8.3.497", False, "drc.tcl", "apps/api/drc.tcl", "# magic 8.3.360", "# magic 8.3.497", "gds read api.gds", "gds flatten true; gds read api.gds", "drc why", "drc listall why", "gds read + drc why → flatten + listall why", "magic --version | head -n 1", "magic -dnull -noconsole apps/api/drc.tcl", "magic -dnull -noconsole apps/legacy/drc.tcl", "apps/api/umbrellabird3.mag"),
        P("netgen-tcl-leftover-lvs", "veery3", "Netgen leftover vs lvs.tcl", "netgen", "1.5.242", "1.5.272", True, "lvs.tcl", "apps/api/lvs.tcl", "# netgen 1.5.242", "# netgen 1.5.272", "lvs \"api.spice api\" \"api.spice api\" setup.tcl", "lvs \"api.spice api\" \"api.spice api\" setup.tcl comp.out", "equate pins", "equate pins -blackbox", "lvs no report + equate pins → report + blackbox", "netgen -batch quit", "netgen -batch source apps/api/lvs.tcl", "netgen -batch source apps/legacy/lvs.tcl", "apps/api/veery3.spice"),
    ),
    (
        P("xschem-sch-leftover-sym", "whydah3", "Xschem leftover vs xschemrc", "xschem", "3.1.0", "3.4.6", False, "xschemrc", "apps/api/xschemrc", "set XSCHEM_VERSION 3.1.0", "set XSCHEM_VERSION 3.4.6", "append XSCHEM_LIBRARY_PATH :$env(HOME)/share/xschem/xschem_library", "append XSCHEM_LIBRARY_PATH :$env(PDK_ROOT)/sky130A/libs.tech/xschem", "xschem --netlist api.sch", "xschem --netlist --spice api.sch", "library path + netlist → pdk path + --spice", "xschem --version | head -n 1", "xschem -n -q apps/api/api.sch", "xschem -n -q apps/legacy/legacy.sch", "apps/api/whydah3.sch"),
        P("opensta-tcl-leftover-readlib", "xenops3", "OpenSTA leftover vs sta.tcl", "opensta", "2.4.0", "2.6.2", True, "sta.tcl", "apps/api/sta.tcl", "# OpenSTA 2.4.0", "# OpenSTA 2.6.2", "read_liberty api.lib", "read_liberty -min api.min.lib; read_liberty -max api.max.lib", "report_checks -path_delay max", "report_checks -path_delay max_rise", "single liberty + max → min/max + max_rise", "sta -exit /dev/null || true", "sta -exit apps/api/sta.tcl", "sta -exit apps/legacy/sta.tcl", "apps/api/xenops3.tcl"),
    ),
    (
        P("su2-cfg-leftover-conv", "yellowhead3", "SU2 leftover vs su2.cfg", "su2", "7.3.1", "8.1.0", False, "su2.cfg", "apps/api/su2.cfg", "% SU2 7.3.1", "% SU2 8.1.0", "CONV_FILENAME= history", "CONV_FILENAME= history.csv", "MARKER_MONITORING= (1-1)", "MARKER_MONITORING= inlet", "history + (1-1) → history.csv + named marker", "SU2_CFD --help | head || true", "SU2_CFD apps/api/su2.cfg", "SU2_CFD apps/legacy/su2.cfg", "apps/api/yellowhead3.cfg"),
        P("energyplus-idf-leftover-runper", "zahle2", "EnergyPlus leftover vs in.idf", "energyplus", "9.6.0", "24.2.0", True, "in.idf", "apps/api/in.idf", "! EnergyPlus 9.6.0", "! EnergyPlus 24.2.0", "RunPeriod, 1, 1, 12, 31;", "RunPeriod, api, 1, 1, , 12, 31;", "Version, 9.6;", "Version, 24.2;", "unnamed RunPeriod + 9.6 → named + 24.2", "energyplus --version", "energyplus -w apps/api/weather.epw apps/api/in.idf", "energyplus -w apps/legacy/weather.epw apps/legacy/in.idf", "apps/api/zahle2.idf"),
    ),
    (
        P("modelica-mos-leftover-simulate", "antshrike2", "Modelica leftover vs api.mos", "openmodelica", "1.18.1", "1.24.3", False, "api.mos", "apps/api/api.mos", "// omc 1.18.1", "// omc 1.24.3", "simulate(Api, stopTime=1.0)", "simulate(Api, stopTime=1.0, simflags=\"-noEventEmit\")", "loadModel(Modelica);", "loadModel(Modelica, {\"4.0.0\"});", "simulate + loadModel bare → simflags + 4.0.0", "omc --version", "omc apps/api/api.mos", "omc apps/legacy/legacy.mos", "apps/api/antshrike2.mo"),
        P("gnuradio-grc-leftover-tb", "becard3", "GNU Radio leftover vs api.grc", "gnuradio", "3.8.5", "3.10.11", True, "api.grc", "apps/api/api.grc", "<!-- gnuradio 3.8.5 -->", "<!-- gnuradio 3.10.11 -->", "from gnuradio import analog", "from gnuradio import analog, soapy", "tb = top_block_cls()", "tb = top_block_cls(flowgraph_vars=vars)", "analog only + top_block_cls() → soapy + flowgraph_vars", "gnuradio-companion --version || true", "grcc -d /tmp/api apps/api/api.grc", "grcc -d /tmp/legacy apps/legacy/legacy.grc", "apps/api/becard3.py"),
    ),
    (
        P("kicad-pro-leftover-eeschema", "cotinga3", "KiCad leftover vs api.kicad_pro", "kicad", "6.0.11", "8.0.7", False, "api.kicad_pro", "apps/api/api.kicad_pro", "\"meta\": { \"filename\": \"api.kicad_pro\", \"version\": 1 } // 6", "\"meta\": { \"filename\": \"api.kicad_pro\", \"version\": 3 } // 8", "eeschema api.sch", "kicad-cli sch export netlist api.kicad_sch", "pcbnew api.kicad_pcb", "kicad-cli pcb export gerbers api.kicad_pcb", "eeschema/pcbnew → kicad-cli sch/pcb", "kicad-cli --version || true", "kicad-cli sch export netlist apps/api/api.kicad_sch", "kicad-cli sch export netlist apps/legacy/legacy.kicad_sch", "apps/api/cotinga3.kicad_sch"),
        P("ngspice-cir-leftover-dotcontrol", "doradito3", "ngspice leftover vs api.cir", "ngspice", "37", "43", True, "spinit", "apps/api/spinit", "* ngspice 37", "* ngspice 43", ".control\nrun\n.endc", ".control\ntran 1n 100n\n.endc", "op;", "tran 1n 100n;", ".control run → tran 1n 100n", "ngspice -v | head -n 1", "ngspice -b apps/api/api.cir", "ngspice -b apps/legacy/legacy.cir", "apps/api/doradito3.cir"),
    ),
    (
        P("xyce-cir-leftover-dottran", "elaenia3", "Xyce leftover vs api.cir", "xyce", "7.6.0", "7.8.0", False, "xyce.args", "apps/api/xyce.args", "-l api.log # 7.6.0", "-l api.log # 7.8.0", ".TRAN 1e-9 1e-6", ".TRAN 1e-9 1e-6 UIC", "Xyce api.cir", "Xyce -hspice-ext all api.cir", ".TRAN + bare Xyce → UIC + hspice-ext", "Xyce -v | head -n 1 || true", "Xyce apps/api/api.cir", "Xyce apps/legacy/legacy.cir", "apps/api/elaenia3.cir"),
        P("meep-ctl-leftover-source", "firecrest3", "Meep leftover vs api.ctl", "meep", "1.24.0", "1.29.0", True, "api.ctl", "apps/api/api.ctl", "; meep 1.24.0", "; meep 1.29.0", "(set! sources (list (make source (src (make gaussian-src (frequency 0.25))))))", "(set! sources (list (make source (src (make gaussian-src (frequency 0.25) (fwidth 0.1))))))", "(run-until 200 (at-beginning output-epsilon))", "(run-until 200 (at-every 10 output-efield-z))", "gaussian-src no fwidth + output-epsilon → fwidth + efield-z", "meep --version || true", "meep apps/api/api.ctl", "meep apps/legacy/legacy.ctl", "apps/api/firecrest3.ctl"),
    ),
    (
        P("calculix-inp-leftover-nset", "gnatcatcher3", "CalculiX leftover vs api.inp", "calculix", "2.19", "2.21", False, "api.inp", "apps/api/api.inp", "** ccx 2.19", "** ccx 2.21", "*NSET, NSET=FIX\n1, 2, 3", "*NSET, NSET=FIX, GENERATE\n1, 3, 1", "*STEP\n*STATIC", "*STEP, NLGEOM\n*STATIC", "explicit nset + STATIC → GENERATE + NLGEOM", "ccx -v || true", "ccx apps/api/api", "ccx apps/legacy/legacy", "apps/api/gnatcatcher3.inp"),
        P("codeaster-comm-leftover-debut", "honeyguide3", "Code_Aster leftover vs api.comm", "code_aster", "15.4", "16.4", True, "api.comm", "apps/api/api.comm", "# aster 15.4", "# aster 16.4", "DEBUT(PAR_LOT='NON')", "DEBUT(CODE=_F(NIV_PUB_WEB='INTERNET'))", "IMPR_RESU(FORMAT='RESULTAT', RESU=_F(RESULTAT=U))", "IMPR_RESU(FORMAT='MED', RESU=_F(RESULTAT=U))", "DEBUT PAR_LOT + RESULTAT → CODE + MED", "as_run --version || true", "as_run apps/api/api.export", "as_run apps/legacy/legacy.export", "apps/api/honeyguide3.comm"),
    ),
    (
        P("elmer-sif-leftover-heateq", "ibis3", "Elmer leftover vs api.sif", "elmer", "9.0", "9.4", False, "api.sif", "apps/api/api.sif", "! elmer 9.0", "! elmer 9.4", "Equation 1\n  Active Solvers(1) = 1\nEnd", "Equation 1\n  Active Solvers(1) = 1\n  Convection = Computed\nEnd", "Solver 1\n  Equation = Heat Equation\nEnd", "Solver 1\n  Equation = Heat Equation\n  Procedure = \"HeatSolve\" \"HeatSolver\"\nEnd", "bare Heat Equation → Convection + Procedure HeatSolve", "ElmerSolver --version || true", "ElmerSolver apps/api/api.sif", "ElmerSolver apps/legacy/legacy.sif", "apps/api/ibis3.sif"),
        P("openfast-fst-leftover-comp", "jabiru3", "OpenFAST leftover vs api.fst", "openfast", "3.1.0", "4.0.2", True, "api.fst", "apps/api/api.fst", "------- OpenFAST 3.1.0 -------", "------- OpenFAST 4.0.2 -------", "CompInflow    1", "CompInflow    2", "CompAero      2   InflowWind + AeroDyn14", "CompAero      2   InflowWind + AeroDyn15", "CompInflow 1 + AeroDyn14 → 2 + AeroDyn15", "openfast -v || true", "openfast apps/api/api.fst", "openfast apps/legacy/legacy.fst", "apps/api/jabiru3.fst"),
    ),
    (
        P("labview-lvproj-leftover-daqmx", "kestrel3", "LabVIEW leftover vs api.lvproj", "labview", "2021", "2024 Q3", False, "api.lvproj", "apps/api/api.lvproj", "<!-- LabVIEW 2021 -->", "<!-- LabVIEW 2024 Q3 -->", "DAQmx Create Channel.vi", "NIDAQmx Create Channel.vi", "Timed Loop", "DT Timed Loop", "DAQmx + Timed Loop → NIDAQmx + DT Timed Loop", "labview --version || true", "labviewcli -OperationName ExecuteBuildSpec -ProjectPath apps/api/api.lvproj", "labviewcli -OperationName ExecuteBuildSpec -ProjectPath apps/legacy/legacy.lvproj", "apps/api/kestrel3.vi"),
        P("simulink-slx-leftover-ode45", "lammergeier3", "Simulink leftover vs api.slx", "simulink", "R2021b", "R2024b", True, "api.slx.cfg", "apps/api/api.slx.cfg", "SolverName: ode45 % R2021b", "SolverName: odeN % R2024b", "set_param(bd,'Solver','ode45')", "set_param(bd,'Solver','odeN')", "sim(bd)", "sim(bd, 'SaveOutput', 'on', 'ReturnWorkspaceOutputs', 'on')", "ode45 + sim(bd) → odeN + SaveOutput", "matlab -batch 'ver' || true", "matlab -batch \"sim('apps/api/api.slx')\"", "matlab -batch \"sim('apps/legacy/legacy.slx')\"", "apps/api/lammergeier3.m"),
    ),
    (
        P("abaqus-inp-leftover-static", "miner3", "Abaqus leftover vs api.inp", "abaqus", "2021", "2024", False, "api.inp", "apps/api/api.inp", "** abaqus 2021", "** abaqus 2024", "*STATIC", "*STATIC, STABILIZE=0.0002", "*OUTPUT, FIELD", "*OUTPUT, FIELD, FREQUENCY=10", "bare STATIC + FIELD → STABILIZE + FREQUENCY", "abaqus information=version || true", "abaqus job=api input=apps/api/api.inp interactive datacheck", "abaqus job=legacy input=apps/legacy/legacy.inp interactive datacheck", "apps/api/miner3.inp"),
        P("nastran-bdf-leftover-sol", "nicobar2", "Nastran leftover vs api.bdf", "nastran", "2021.1", "2024.1", True, "api.bdf", "apps/api/api.bdf", "$ nastran 2021.1", "$ nastran 2024.1", "SOL 101", "SOL 400", "PARAM,POST,-1", "PARAM,POST,-2", "SOL 101 + POST -1 → SOL 400 + POST -2", "nastran ??? || true", "nastran apps/api/api.bdf scr=yes old=no", "nastran apps/legacy/legacy.bdf scr=yes old=no", "apps/api/nicobar2.bdf"),
    ),
    (
        P("openems-xml-leftover-fdtd", "oilbird4", "openEMS leftover vs api.xml", "openems", "0.0.35", "0.0.36", False, "api.xml", "apps/api/api.xml", "<!-- openEMS 0.0.35 -->", "<!-- openEMS 0.0.36 -->", "<FDTD NumberOfTimesteps=\"1000\" endCriteria=\"1e-5\">", "<FDTD NumberOfTimesteps=\"1000\" endCriteria=\"1e-5\" f_max=\"10e9\">", "CSXGeomPlot", "AppCSXCAD", "FDTD no f_max + CSXGeomPlot → f_max + AppCSXCAD", "openEMS --help | head || true", "openEMS apps/api/api.xml", "openEMS apps/legacy/legacy.xml", "apps/api/oilbird4.xml"),
        P("siliconcompiler-py-leftover-target", "pittasoma3", "SiliconCompiler leftover vs api.py", "siliconcompiler", "0.12.2", "0.28.0", True, "api.py", "apps/api/api.py", "# siliconcompiler 0.12.2", "# siliconcompiler 0.28.0", "chip.load_target('freepdk45_demo')", "chip.load_target('skywater130_demo')", "chip.set('option', 'remote', False)", "chip.set('option', 'scheduler', 'local')", "freepdk45 + remote False → skywater130 + scheduler local", "sc -version || true", "python3 apps/api/api.py", "python3 apps/legacy/legacy.py", "apps/api/pittasoma3.py"),
    ),
]


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
