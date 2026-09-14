#!/usr/bin/env python3
"""Append unused notebook→pipeline dest plants for r1558+.

BAN r1557 crystal-docs-html-as-dest / aim-chart-png-leftover and prior
dest-as-pipeline clones. Dest = orchestrator/runtime/artifact sink, not a
restated source notebook.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path("/home/raulmc/rmems/synthetic-factory")
MILL = ROOT / "experiments/ntp-mill-r1326.py"
FACTORY = ROOT / "outputs/raw/2026-08-19-agentic/notebook-to-pipeline-factory"
BANNED = {
    "crystal-docs-html-as-dest",
    "aim-chart-png-leftover",
    "flyte-execution-as-dest",
    "plotly-html-leftover",
}

# (slug, token, artifact, kind, cmd_tmpl with {dest}, vs)
SUCCESS_SPEC = [
    ("nim-docs-html-as-dest", "nim doc", "htmldocs/index.html", "Nim docs HTML", "nim doc --project src/folio.nim && cp htmldocs/index.html {dest}", "not crystal dest"),
    ("zig-docs-html-as-dest", "zig build docs", "zig-out/docs/index.html", "Zig docs HTML", "zig build docs && cp zig-out/docs/index.html {dest}", "not nim dest"),
    ("futhark-docs-html-as-dest", "futhark doc", "docs/index.html", "Futhark docs HTML", "futhark doc src && cp docs/index.html {dest}", "not zig dest"),
    ("odin-docs-html-as-dest", "odin doc", "docs/index.html", "Odin docs HTML", "odin doc src && cp docs/index.html {dest}", "not futhark dest"),
    ("vlang-docs-html-as-dest", "v doc", "docs/index.html", "V docs HTML", "v doc . && cp docs/index.html {dest}", "not odin dest"),
    ("ford-html-as-dest", "ford", "doc/index.html", "FORD Fortran HTML", "ford ford.md && cp doc/index.html {dest}", "not vlang dest"),
    ("pod2html-as-dest", "pod2html", "folio.html", "Perl POD HTML", "pod2html folio.pod > folio.html && cp folio.html {dest}", "not ford dest"),
    ("phpdocumentor-html-as-dest", "phpdoc", "build/docs/index.html", "phpDocumentor HTML", "phpdoc run -d src -t build/docs && cp build/docs/index.html {dest}", "not pod dest"),
    ("ldoc-html-as-dest", "ldoc", "doc/index.html", "LDoc Lua HTML", "ldoc . && cp doc/index.html {dest}", "not phpdoc dest"),
    ("codox-html-as-dest", "lein codox", "target/doc/index.html", "Codox Clojure HTML", "lein codox && cp target/doc/index.html {dest}", "not ldoc dest"),
    ("scribble-html-as-dest", "scribble", "folio.html", "Scribble Racket HTML", "scribble ++arg --html folio.scrbl && cp folio.html {dest}", "not codox dest"),
    ("documenter-html-as-dest", "julia documenter", "docs/build/index.html", "Documenter.jl HTML", "julia --project=docs docs/make.jl && cp docs/build/index.html {dest}", "not scribble dest"),
    ("fsdocs-html-as-dest", "dotnet fsdocs", "output/index.html", "F# fsdocs HTML", "dotnet fsdocs build && cp output/index.html {dest}", "not documenter dest"),
    ("gleam-docs-html-as-dest", "gleam docs", "build/dev/docs/index.html", "Gleam docs HTML", "gleam docs build && cp build/dev/docs/index.html {dest}", "not fsdocs dest"),
    ("vala-docs-html-as-dest", "valadoc", "docs/index.html", "Valadoc HTML", "valadoc src/*.vala -o docs && cp docs/index.html {dest}", "not gleam dest"),
    ("hy-docs-html-as-dest", "hy2py docs", "docs/index.html", "Hy docs HTML", "sphinx-build docs docs/_build && cp docs/_build/index.html {dest}", "not vala dest"),
    ("fennel-docs-html-as-dest", "fenneldoc", "docs/index.html", "Fennel docs HTML", "fenneldoc src && cp docs/index.html {dest}", "not hy dest"),
    ("texinfo-html-as-dest", "makeinfo --html", "folio/index.html", "Texinfo HTML", "makeinfo --html folio.texi && cp folio/index.html {dest}", "not fennel dest"),
    ("rst2html-as-dest", "rst2html5", "folio.html", "Docutils rst2html", "rst2html5 folio.rst folio.html && cp folio.html {dest}", "not texinfo dest"),
    ("rst2pdf-as-dest", "rst2pdf", "folio.pdf", "rst2pdf PDF", "rst2pdf folio.rst -o folio.pdf && cp folio.pdf {dest}", "not rst2html dest"),
    ("scdoc-man-as-dest", "scdoc", "folio.1", "scdoc manpage", "scdoc < folio.scd > folio.1 && cp folio.1 {dest}", "not rst2pdf dest"),
    ("help2man-as-dest", "help2man", "folio.1", "help2man roff", "help2man ./folio > folio.1 && cp folio.1 {dest}", "not scdoc dest"),
    ("asciidoc-pdf-as-dest", "asciidoctor-pdf", "folio.pdf", "Asciidoctor PDF", "asciidoctor-pdf folio.adoc && cp folio.pdf {dest}", "not help2man dest"),
    ("org-html-as-dest", "emacs org-export", "folio.html", "Org-mode HTML", "emacs --batch folio.org -f org-html-export-to-html && cp folio.html {dest}", "not asciidoc dest"),
    ("pdoc-html-as-dest", "pdoc", "html/folio.html", "pdoc HTML", "pdoc -o html folio && cp html/folio.html {dest}", "not org dest"),
    ("compodoc-html-as-dest", "compodoc", "documentation/index.html", "Compodoc HTML", "npx compodoc -p tsconfig.json -d documentation && cp documentation/index.html {dest}", "not pdoc dest"),
    ("redoc-html-as-dest", "redoc-cli", "redoc.html", "ReDoc HTML", "npx redoc-cli bundle openapi.yaml -o redoc.html && cp redoc.html {dest}", "not compodoc dest"),
    ("swagger-ui-html-as-dest", "swagger-codegen ui", "swagger-ui/index.html", "Swagger UI HTML", "npx swagger-cli bundle openapi.yaml && cp swagger-ui/index.html {dest}", "not redoc dest"),
    ("asyncapi-html-as-dest", "ag asyncapi", "asyncapi.html", "AsyncAPI HTML", "ag asyncapi@latest generate fromTemplate asyncapi.yaml @asyncapi/html-template -o out && cp out/index.html {dest}", "not swagger dest"),
    ("slate-html-as-dest", "slate build", "build/index.html", "Slate API HTML", "bundle exec middleman build && cp build/index.html {dest}", "not asyncapi dest"),
    ("spectral-html-as-dest", "spectral lint --format html", "spectral.html", "Spectral lint HTML", "spectral lint openapi.yaml -f html -o spectral.html && cp spectral.html {dest}", "not slate dest"),
    ("raml2html-as-dest", "raml2html", "api.html", "RAML HTML", "raml2html api.raml > api.html && cp api.html {dest}", "not spectral dest"),
    ("protoc-gen-doc-as-dest", "protoc-gen-doc", "docs/index.html", "protoc-gen-doc HTML", "protoc --doc_out=docs --doc_opt=html,index.html folio.proto && cp docs/index.html {dest}", "not raml dest"),
    ("avrodoc-html-as-dest", "avrodoc", "avrodoc.html", "Avrodoc HTML", "avrodoc schema.avsc > avrodoc.html && cp avrodoc.html {dest}", "not protoc dest"),
    ("jsonschema-docs-as-dest", "jsonschema2md", "schema/index.md", "jsonschema2md docs", "jsonschema2md -d schema -o schema && cp schema/index.md {dest}", "not avrodoc dest"),
    ("spectaql-html-as-dest", "spectaql", "public/index.html", "SpectaQL HTML", "npx spectaql config.yml && cp public/index.html {dest}", "not jsonschema dest"),
    ("graphdoc-html-as-dest", "graphdoc", "doc/index.html", "graphdoc HTML", "npx @2fd/graphdoc -s schema.gql -o doc && cp doc/index.html {dest}", "not spectaql dest"),
    ("openapi-generator-html-as-dest", "openapi-generator html", "html/index.html", "openapi-generator HTML", "openapi-generator-cli generate -g html -i openapi.yaml -o html && cp html/index.html {dest}", "not graphdoc dest"),
    ("redocly-html-as-dest", "redocly build-docs", "redocly.html", "Redocly HTML", "redocly build-docs openapi.yaml -o redocly.html && cp redocly.html {dest}", "not openapi-generator dest"),
    ("stoplight-html-as-dest", "stoplight prism", "elements/index.html", "Stoplight Elements HTML", "npx @stoplight/elements-cli build openapi.yaml -o elements && cp elements/index.html {dest}", "not redocly dest"),
    ("widdershins-html-as-dest", "widdershins", "api.md", "Widdershins markdown", "widdershins openapi.yaml -o api.md && cp api.md {dest}", "not stoplight dest"),
    ("aglio-html-as-dest", "aglio", "api.html", "Aglio API Blueprint HTML", "aglio -i api.apib -o api.html && cp api.html {dest}", "not widdershins dest"),
    ("apidoc-html-as-dest", "apidoc", "doc/index.html", "apiDoc HTML", "apidoc -i src -o doc && cp doc/index.html {dest}", "not aglio dest"),
    ("rapi-doc-html-as-dest", "rapidoc", "rapidoc.html", "RapiDoc HTML", "cp node_modules/rapidoc/dist/rapidoc-min.js rapidoc.html && cp rapidoc.html {dest}", "not apidoc dest"),
    ("scalar-docs-html-as-dest", "scalar build", "scalar/index.html", "Scalar docs HTML", "npx @scalar/cli document build openapi.yaml -o scalar && cp scalar/index.html {dest}", "not rapidoc dest"),
    ("fern-docs-html-as-dest", "fern generate --docs", "docs/index.html", "Fern docs HTML", "fern generate --docs && cp docs/index.html {dest}", "not scalar dest"),
    ("mintlify-docs-html-as-dest", "mintlify build", "build/index.html", "Mintlify docs HTML", "mintlify build && cp build/index.html {dest}", "not fern dest"),
    ("elements-openapi-as-dest", "elements build", "elements.html", "Stoplight Elements bundle", "npx @stoplight/cli bundle openapi.yaml -o elements.html && cp elements.html {dest}", "not mintlify dest"),
    ("prisma-erd-svg-as-dest", "prisma generate erd", "erd.svg", "Prisma ERD SVG", "npx prisma generate --generator erd && cp erd.svg {dest}", "not elements dest"),
    ("dbdocs-html-as-dest", "dbdocs build", "dbdocs.html", "dbdocs HTML", "dbdocs build schema.dbml --export && cp dbdocs.html {dest}", "not prisma-erd dest"),
    ("schemaspy-html-as-dest", "schemaspy", "output/index.html", "SchemaSpy HTML", "schemaspy -t pgsql -o output && cp output/index.html {dest}", "not dbdocs dest"),
    ("tbls-html-as-dest", "tbls doc", "dbdoc/index.html", "tbls HTML", "tbls doc -f && cp dbdoc/index.html {dest}", "not schemaspy dest"),
    ("eralchemy-svg-as-dest", "eralchemy", "er.svg", "ERAlchemy SVG", "eralchemy -i postgresql://folio -o er.svg && cp er.svg {dest}", "not tbls dest"),
    ("dbml-html-as-dest", "dbml2html", "schema.html", "DBML HTML", "npx @dbml/cli dbml2sql schema.dbml && cp schema.html {dest}", "not eralchemy dest"),
    ("dbdiagram-export-as-dest", "dbdiagram export", "dbdiagram.svg", "dbdiagram SVG", "dbdiagram export schema.dbml -f svg && cp dbdiagram.svg {dest}", "not dbml dest"),
    ("terraform-docs-md-as-dest", "terraform-docs", "README.md", "terraform-docs markdown", "terraform-docs markdown . > README.md && cp README.md {dest}", "not dbdiagram dest"),
    ("pulumi-docs-html-as-dest", "pulumi about --json", "stack.json", "Pulumi stack JSON", "pulumi stack export --file stack.json && cp stack.json {dest}", "not terraform-docs dest"),
    ("sphinx-epub-as-dest", "sphinx-build -b epub", "build/epub/folio.epub", "Sphinx EPUB", "sphinx-build -b epub docs build/epub && cp build/epub/folio.epub {dest}", "not pulumi dest"),
    ("mkdocs-pdf-as-dest", "mkdocs with pdf", "site/pdf/doc.pdf", "MkDocs PDF", "mkdocs build && cp site/pdf/doc.pdf {dest}", "not sphinx-epub dest"),
    ("mdbook-epub-as-dest", "mdbook --epub", "book/epub/folio.epub", "mdBook EPUB", "mdbook build && cp book/epub/folio.epub {dest}", "not mkdocs-pdf dest"),
    ("quarto-pdf-as-dest", "quarto render --to pdf", "report.pdf", "Quarto PDF", "quarto render report.qmd --to pdf && cp report.pdf {dest}", "not mdbook-epub dest"),
    ("rmarkdown-pdf-as-dest", "rmarkdown::render pdf", "report.pdf", "R Markdown PDF", "Rscript -e 'rmarkdown::render(\"report.Rmd\", \"pdf_document\")' && cp report.pdf {dest}", "not quarto-pdf dest"),
    ("bookdown-pdf-as-dest", "bookdown pdf", "_book/_main.pdf", "bookdown PDF", "Rscript -e 'bookdown::render_book(\".\", \"bookdown::pdf_book\")' && cp _book/_main.pdf {dest}", "not rmarkdown-pdf dest"),
    ("jupyter-book-pdf-as-dest", "jb build --builder pdflatex", "_build/latex/book.pdf", "Jupyter Book PDF", "jupyter-book build . --builder pdflatex && cp _build/latex/book.pdf {dest}", "not bookdown dest"),
    ("reportlab-pdf-as-dest", "reportlab canvas", "folio.pdf", "ReportLab PDF", "python3 -c 'from reportlab.pdfgen import canvas; canvas.Canvas(\"folio.pdf\").save()' && cp folio.pdf {dest}", "not jb-pdf dest"),
    ("fpdf-pdf-as-dest", "fpdf2", "folio.pdf", "FPDF PDF", "python3 -c 'from fpdf import FPDF; p=FPDF(); p.add_page(); p.output(\"folio.pdf\")' && cp folio.pdf {dest}", "not reportlab dest"),
    ("borb-pdf-as-dest", "borb PDF", "folio.pdf", "borb PDF", "python3 write_borb.py && cp folio.pdf {dest}", "not fpdf dest"),
    ("torchserve-mar-as-dest", "torch-model-archiver", "folio.mar", "TorchServe MAR", "torch-model-archiver --model-name folio --serialized-file m.pt --handler h.py --export-path . && cp folio.mar {dest}", "not borb dest"),
    ("tfserving-savedmodel-as-dest", "saved_model_cli", "saved_model/saved_model.pb", "TF Serving SavedModel", "saved_model_cli show --dir saved_model && cp saved_model/saved_model.pb {dest}", "not torchserve dest"),
    ("rayserve-deploy-as-dest", "serve build", "serve.yaml", "Ray Serve YAML", "serve build folio:app -o serve.yaml && cp serve.yaml {dest}", "not tfserving dest"),
    ("ollama-modelfile-as-dest", "ollama create", "Modelfile", "Ollama Modelfile", "ollama create folio -f Modelfile && cp Modelfile {dest}", "not rayserve dest"),
    ("llamacpp-gguf-as-dest", "llama-quantize", "folio.gguf", "llama.cpp GGUF", "llama-quantize model.gguf folio.gguf q4_0 && cp folio.gguf {dest}", "not ollama dest"),
    ("vllm-engine-json-as-dest", "vllm serve --config", "vllm-engine.json", "vLLM engine JSON", "python3 -c 'import json; json.dump({\"model\":\"folio\"}, open(\"vllm-engine.json\",\"w\"))' && cp vllm-engine.json {dest}", "not llamacpp dest"),
    ("tgi-config-as-dest", "text-generation-launcher", "tgi-config.json", "TGI config JSON", "cp config.json tgi-config.json && cp tgi-config.json {dest}", "not vllm dest"),
    ("sglang-server-as-dest", "sglang.launch_server", "sglang.json", "SGLang server JSON", "python3 -c 'open(\"sglang.json\",\"w\").write(\"{}\")' && cp sglang.json {dest}", "not tgi dest"),
    ("mlserver-model-as-dest", "mlserver build", "model-settings.json", "MLServer settings", "mlserver build . && cp model-settings.json {dest}", "not sglang dest"),
    ("nvidia-nim-config-as-dest", "nim start", "nim-config.yaml", "NVIDIA NIM config", "cp nim-config.yaml /tmp/n && cp nim-config.yaml {dest}", "not mlserver dest"),
    ("triton-model-config-as-dest", "triton model-config", "model_repository/folio/config.pbtxt", "Triton config.pbtxt", "cp model_repository/folio/config.pbtxt {dest}", "not nim dest"),
    ("onnxruntime-ort-as-dest", "ort convert", "folio.ort", "ONNX Runtime ORT", "python -m onnxruntime.tools.convert_onnx_models_to_ort folio.onnx && cp folio.ort {dest}", "not triton dest"),
    ("openvino-ir-as-dest", "mo --input_model", "folio.xml", "OpenVINO IR XML", "mo --input_model folio.onnx --output_dir . && cp folio.xml {dest}", "not ort dest"),
    ("tensorrt-engine-as-dest", "trtexec", "folio.engine", "TensorRT engine", "trtexec --onnx=folio.onnx --saveEngine=folio.engine && cp folio.engine {dest}", "not openvino dest"),
    ("coreml-mlmodel-as-dest", "coremltools convert", "folio.mlmodel", "Core ML mlmodel", "python3 convert_coreml.py && cp folio.mlmodel {dest}", "not tensorrt dest"),
    ("tflite-model-as-dest", "tflite convert", "folio.tflite", "TFLite model", "tflite_convert --saved_model_dir=sm --output_file=folio.tflite && cp folio.tflite {dest}", "not coreml dest"),
    ("ncnn-param-as-dest", "onnx2ncnn", "folio.param", "ncnn param", "onnx2ncnn folio.onnx folio.param folio.bin && cp folio.param {dest}", "not tflite dest"),
    ("mnn-model-as-dest", "MNNConvert", "folio.mnn", "MNN model", "MNNConvert -f ONNX --modelFile folio.onnx --MNNModel folio.mnn && cp folio.mnn {dest}", "not ncnn dest"),
    ("paddle-pdmodel-as-dest", "paddle save_inference", "folio.pdmodel", "Paddle pdmodel", "python3 save_paddle.py && cp folio.pdmodel {dest}", "not mnn dest"),
    ("mindspore-ckpt-as-dest", "mindspore save_checkpoint", "folio.ckpt", "MindSpore ckpt", "python3 save_ms.py && cp folio.ckpt {dest}", "not paddle dest"),
    ("sagemaker-model-pkg-as-dest", "aws sagemaker create-model-package", "model-package.json", "SageMaker model package JSON", "aws sagemaker describe-model-package --model-package-name folio > model-package.json && cp model-package.json {dest}", "not mindspore dest"),
    ("azureml-model-as-dest", "az ml model create", "azureml-model.json", "Azure ML model JSON", "az ml model show -n folio -o json > azureml-model.json && cp azureml-model.json {dest}", "not sagemaker dest"),
    ("vertex-model-as-dest", "gcloud ai models", "vertex-model.json", "Vertex model JSON", "gcloud ai models describe folio --format json > vertex-model.json && cp vertex-model.json {dest}", "not azureml dest"),
    ("databricks-uc-model-as-dest", "databricks models get", "uc-model.json", "Databricks UC model JSON", "databricks models get --name folio > uc-model.json && cp uc-model.json {dest}", "not vertex dest"),
    ("huggingface-hub-as-dest", "huggingface-cli upload", "hub-rev.json", "HF Hub revision JSON", "huggingface-cli repo info folio > hub-rev.json && cp hub-rev.json {dest}", "not databricks dest"),
    ("haystack-pipeline-as-dest", "haystack pipeline.dump", "pipeline.yaml", "Haystack pipeline YAML", "python3 -c 'open(\"pipeline.yaml\",\"w\").write(\"type: pipeline\\n\")' && cp pipeline.yaml {dest}", "not hf-hub dest"),
    ("llamaindex-persist-as-dest", "index.storage_context.persist", "storage/docstore.json", "LlamaIndex persist JSON", "python3 persist_index.py && cp storage/docstore.json {dest}", "not haystack dest"),
    ("langchain-serve-as-dest", "langchain-cli serve", "langserve.json", "LangServe config", "langchain-cli serve --config langserve.json && cp langserve.json {dest}", "not llamaindex dest"),
    ("datahub-mcp-as-dest", "datahub ingest", "mce.json", "DataHub MCP JSON", "datahub ingest -c ingest.yml --dry-run > mce.json && cp mce.json {dest}", "not langserve dest"),
    ("openmetadata-entity-as-dest", "metadata ingest", "om-entity.json", "OpenMetadata entity JSON", "metadata ingest -c om.yml && cp om-entity.json {dest}", "not datahub dest"),
    ("alation-bi-as-dest", "alation export", "alation-bi.json", "Alation BI JSON", "alation export --bi > alation-bi.json && cp alation-bi.json {dest}", "not openmetadata dest"),
    ("atlan-asset-as-dest", "atlan export", "atlan-asset.json", "Atlan asset JSON", "atlan export asset folio > atlan-asset.json && cp atlan-asset.json {dest}", "not alation dest"),
    ("collibra-asset-as-dest", "collibra export", "collibra.json", "Collibra asset JSON", "collibra-export --asset folio > collibra.json && cp collibra.json {dest}", "not atlan dest"),
    ("amundsen-preview-as-dest", "amundsen databuilder", "amundsen-preview.json", "Amundsen preview JSON", "python3 databuilder.py && cp amundsen-preview.json {dest}", "not collibra dest"),
    ("atlas-type-as-dest", "atlas typedefs", "atlas-type.json", "Atlas typedef JSON", "curl -s localhost:21000/api/atlas/v2/types/typedefs > atlas-type.json && cp atlas-type.json {dest}", "not amundsen dest"),
    ("marquez-dataset-as-dest", "marquez dataset", "marquez-dataset.json", "Marquez dataset JSON", "curl -s localhost:5000/api/v1/namespaces/folio/datasets/nightly > marquez-dataset.json && cp marquez-dataset.json {dest}", "not atlas dest"),
    ("great-expectations-suite-as-dest", "great_expectations suite", "gx/expectations/folio.json", "GX expectation suite", "great_expectations suite new --expectation-suite folio && cp gx/expectations/folio.json {dest}", "not marquez dest"),
    ("anomalo-check-as-dest", "anomalo validate", "anomalo-check.json", "Anomalo check JSON", "anomalo checks export folio > anomalo-check.json && cp anomalo-check.json {dest}", "not gx dest"),
    ("re-data-report-as-dest", "re_data overview", "target/re_data/overview.json", "re_data overview JSON", "dbt run-operation generate_overview && cp target/re_data/overview.json {dest}", "not anomalo dest"),
    ("dbt-docs-as-dest", "dbt docs generate", "target/index.html", "dbt docs HTML", "dbt docs generate && cp target/index.html {dest}", "not re_data dest"),
    ("sqlmesh-docs-as-dest", "sqlmesh ui", "sqlmesh-docs.html", "SQLMesh docs HTML", "sqlmesh ui --host 127.0.0.1 && cp sqlmesh-docs.html {dest}", "not dbt-docs dest"),
    ("kafka-connect-config-as-dest", "kafka-connect rest", "connect-config.json", "Kafka Connect config", "curl -s localhost:8083/connectors/folio/config > connect-config.json && cp connect-config.json {dest}", "not sqlmesh dest"),
    ("pulsar-schema-json-as-dest", "pulsar-admin schemas", "pulsar-schema.json", "Pulsar schema JSON", "pulsar-admin schemas get persistent://p/folio > pulsar-schema.json && cp pulsar-schema.json {dest}", "not kafka-connect dest"),
    ("redpanda-topic-as-dest", "rpk topic describe", "redpanda-topic.json", "Redpanda topic JSON", "rpk topic describe folio -f json > redpanda-topic.json && cp redpanda-topic.json {dest}", "not pulsar dest"),
    ("kinesis-shard-as-dest", "aws kinesis describe-stream", "kinesis-stream.json", "Kinesis stream JSON", "aws kinesis describe-stream --stream-name folio > kinesis-stream.json && cp kinesis-stream.json {dest}", "not redpanda dest"),
    ("nats-stream-as-dest", "nats stream info", "nats-stream.json", "NATS stream JSON", "nats stream info folio --json > nats-stream.json && cp nats-stream.json {dest}", "not kinesis dest"),
    ("rabbitmq-export-as-dest", "rabbitmqadmin export", "rabbitmq-defs.json", "RabbitMQ definitions", "rabbitmqadmin export rabbitmq-defs.json && cp rabbitmq-defs.json {dest}", "not nats dest"),
    ("activemq-export-as-dest", "activemq export", "activemq-dest.xml", "ActiveMQ dest XML", "activemq-admin query -QQueue=folio > activemq-dest.xml && cp activemq-dest.xml {dest}", "not rabbitmq dest"),
    ("flink-savepoint-as-dest", "flink savepoint", "_metadata", "Flink savepoint meta", "flink savepoint 1-folio /sp && cp /sp/_metadata {dest}", "not activemq dest"),
    ("spark-streaming-ckpt-as-dest", "spark checkpoint", "ckpt/metadata", "Spark streaming checkpoint", "ls ckpt/metadata && cp ckpt/metadata {dest}", "not flink dest"),
    ("debezium-offset-as-dest", "debezium offsets", "debezium-offsets.json", "Debezium offsets JSON", "kafka-console-consumer --topic connect-offsets --from-beginning > debezium-offsets.json && cp debezium-offsets.json {dest}", "not spark-ckpt dest"),
    ("maxwell-binlog-as-dest", "maxwell --output", "maxwell.pos", "Maxwell binlog pos", "maxwell --config maxwell.properties && cp maxwell.pos {dest}", "not debezium dest"),
    ("kafka-topic-dump-as-dest", "kcat -C", "topic.dump", "Kafka topic dump", "kcat -C -t folio -e > topic.dump && cp topic.dump {dest}", "not maxwell dest"),
    ("materialize-sink-as-dest", "mz sink", "mz-sink.sql", "Materialize sink SQL", "psql mz -c 'SHOW CREATE SINK folio' > mz-sink.sql && cp mz-sink.sql {dest}", "not kafka-dump dest"),
    ("bytewax-dataflow-as-dest", "bytewax run", "dataflow.json", "Bytewax dataflow JSON", "python -m bytewax.run dataflow && cp dataflow.json {dest}", "not materialize dest"),
    ("risingwave-mv-as-dest", "risingwave describe", "rw-mv.sql", "RisingWave MV SQL", "psql rw -c 'DESCRIBE MATERIALIZED VIEW folio' > rw-mv.sql && cp rw-mv.sql {dest}", "not bytewax dest"),
    ("ksqldb-query-as-dest", "ksql describe", "ksql-query.json", "ksqlDB query JSON", "ksql http://localhost:8088 -e 'DESCRIBE folio;' > ksql-query.json && cp ksql-query.json {dest}", "not risingwave dest"),
    ("nifi-flow-as-dest", "nifi pg export", "nifi-flow.json", "NiFi flow JSON", "nifi pg export --output nifi-flow.json && cp nifi-flow.json {dest}", "not ksqldb dest"),
    ("airbyte-catalog-as-dest", "airbyte discover", "airbyte-catalog.json", "Airbyte catalog JSON", "abctl local connector discover folio > airbyte-catalog.json && cp airbyte-catalog.json {dest}", "not nifi dest"),
    ("fivetran-schema-as-dest", "fivetran schema", "fivetran-schema.json", "Fivetran schema JSON", "fivetran connector schema folio > fivetran-schema.json && cp fivetran-schema.json {dest}", "not airbyte dest"),
    ("dlt-pipeline-as-dest", "dlt pipeline show", "dlt-state.json", "dlt pipeline state", "dlt pipeline folio info --format json > dlt-state.json && cp dlt-state.json {dest}", "not fivetran dest"),
    ("singer-catalog-as-dest", "tap-discover", "singer-catalog.json", "Singer catalog JSON", "tap-folio --discover > singer-catalog.json && cp singer-catalog.json {dest}", "not dlt dest"),
    ("meltano-state-as-dest", "meltano state get", "meltano-state.json", "Meltano state JSON", "meltano state get --force > meltano-state.json && cp meltano-state.json {dest}", "not singer dest"),
    ("loki-export-as-dest", "logcli query", "loki-export.json", "Loki log export", "logcli query '{job=\"folio\"}' --output jsonl > loki-export.json && cp loki-export.json {dest}", "not meltano dest"),
    ("tempo-trace-as-dest", "tempo query", "tempo-trace.json", "Tempo trace JSON", "curl -s localhost:3200/api/traces/folio > tempo-trace.json && cp tempo-trace.json {dest}", "not loki dest"),
    ("prometheus-rules-as-dest", "promtool check rules", "rules.yml", "Prometheus rules YAML", "promtool check rules rules.yml && cp rules.yml {dest}", "not tempo dest"),
    ("alertmanager-config-as-dest", "amtool check-config", "alertmanager.yml", "Alertmanager config", "amtool check-config alertmanager.yml && cp alertmanager.yml {dest}", "not prom-rules dest"),
    ("grafana-alert-as-dest", "grafana alerting export", "grafana-alert.json", "Grafana alert JSON", "grafana-cli admin export-alerting > grafana-alert.json && cp grafana-alert.json {dest}", "not alertmanager dest"),
    ("thanos-sidecar-as-dest", "thanos tools bucket", "thanos-meta.json", "Thanos sidecar meta", "thanos tools bucket inspect --objstore.config-file=b.yml > thanos-meta.json && cp thanos-meta.json {dest}", "not grafana-alert dest"),
    ("victoriametrics-snap-as-dest", "vmbackup", "vm-snapshot", "VictoriaMetrics snapshot", "vmbackup -snapshotName=folio && cp vm-snapshot {dest}", "not thanos dest"),
    ("mimir-ruler-as-dest", "mimirtool rules", "mimir-rules.yaml", "Mimir ruler YAML", "mimirtool rules print --output-dir . && cp mimir-rules.yaml {dest}", "not vm dest"),
    ("cortex-config-as-dest", "cortex -config.file", "cortex.yml", "Cortex config YAML", "cortex -config.file=cortex.yml -verify && cp cortex.yml {dest}", "not mimir dest"),
    ("otel-collector-as-dest", "otelcol --config", "otel-col.yaml", "OTel collector YAML", "otelcol --config=otel-col.yaml --dry-run && cp otel-col.yaml {dest}", "not cortex dest"),
    ("zipkin-span-as-dest", "zipkin api", "zipkin-span.json", "Zipkin span JSON", "curl -s localhost:9411/api/v2/trace/folio > zipkin-span.json && cp zipkin-span.json {dest}", "not otel dest"),
    ("honeycomb-dataset-as-dest", "honeytail", "honeycomb-ds.json", "Honeycomb dataset JSON", "curl -s api.honeycomb.io/1/datasets/folio > honeycomb-ds.json && cp honeycomb-ds.json {dest}", "not zipkin dest"),
    ("lightstep-trace-as-dest", "lightstep query", "lightstep-trace.json", "Lightstep trace JSON", "lightstep traces get folio > lightstep-trace.json && cp lightstep-trace.json {dest}", "not honeycomb dest"),
    ("newrelic-nrql-as-dest", "newrelic nrql", "nrql.json", "New Relic NRQL JSON", "newrelic nrql query --query 'SELECT count(*) FROM folio' > nrql.json && cp nrql.json {dest}", "not lightstep dest"),
    ("datadog-dashboard-as-dest", "datadog dashboard get", "dd-dash.json", "Datadog dashboard JSON", "datadog-ci dashboard get folio > dd-dash.json && cp dd-dash.json {dest}", "not newrelic dest"),
    ("sentry-issue-as-dest", "sentry-cli issues", "sentry-issue.json", "Sentry issue JSON", "sentry-cli issues list --json > sentry-issue.json && cp sentry-issue.json {dest}", "not datadog dest"),
    ("elastic-apm-as-dest", "apm-server export", "apm-event.json", "Elastic APM event", "curl -s localhost:8200/intake/v2/events > apm-event.json && cp apm-event.json {dest}", "not sentry dest"),
    ("signoz-trace-as-dest", "signoz query", "signoz-trace.json", "SigNoz trace JSON", "curl -s localhost:3301/api/v1/traces/folio > signoz-trace.json && cp signoz-trace.json {dest}", "not elastic-apm dest"),
    ("uptrace-span-as-dest", "uptrace export", "uptrace-span.json", "Uptrace span JSON", "uptrace traces export folio > uptrace-span.json && cp uptrace-span.json {dest}", "not signoz dest"),
    ("hyperdx-trace-as-dest", "hyperdx export", "hyperdx-trace.json", "HyperDX trace JSON", "hyperdx traces get folio > hyperdx-trace.json && cp hyperdx-trace.json {dest}", "not uptrace dest"),
    ("posthog-event-as-dest", "posthog export", "posthog-events.jsonl", "PostHog events JSONL", "posthog export --events folio > posthog-events.jsonl && cp posthog-events.jsonl {dest}", "not hyperdx dest"),
    ("mixpanel-export-as-dest", "mixpanel export", "mixpanel.jsonl", "Mixpanel export JSONL", "mixpanel export --from 2026-08-18 > mixpanel.jsonl && cp mixpanel.jsonl {dest}", "not posthog dest"),
    ("amplitude-export-as-dest", "amplitude export", "amplitude.jsonl", "Amplitude export JSONL", "amplitude export --start 20260818 > amplitude.jsonl && cp amplitude.jsonl {dest}", "not mixpanel dest"),
    ("clickhouse-native-as-dest", "clickhouse-client --query", "folio.native", "ClickHouse native dump", "clickhouse-client --query 'SELECT * FROM folio FORMAT Native' > folio.native && cp folio.native {dest}", "not amplitude dest"),
    ("starrocks-tablet-as-dest", "starrocks admin", "sr-tablet.json", "StarRocks tablet JSON", "mysql -h sr -e 'SHOW TABLET FROM folio' > sr-tablet.json && cp sr-tablet.json {dest}", "not clickhouse dest"),
    ("doris-tablet-as-dest", "doris show tablet", "doris-tablet.json", "Doris tablet JSON", "mysql -h doris -e 'SHOW TABLET FROM folio' > doris-tablet.json && cp doris-tablet.json {dest}", "not starrocks dest"),
    ("pinot-segment-as-dest", "pinot-admin DownloadSegment", "folio.tar.gz", "Pinot segment tarball", "pinot-admin.sh DownloadSegment -tableName folio -outputDir . && cp folio.tar.gz {dest}", "not doris dest"),
    ("druid-segment-as-dest", "druid coordinator", "druid-seg.json", "Druid segment JSON", "curl -s localhost:8081/druid/coordinator/v1/metadata/datasources/folio/segments > druid-seg.json && cp druid-seg.json {dest}", "not pinot dest"),
    ("kylin-cube-as-dest", "kylin cube desc", "kylin-cube.json", "Kylin cube JSON", "curl -s localhost:7070/kylin/api/cubes/folio > kylin-cube.json && cp kylin-cube.json {dest}", "not druid dest"),
    ("ignite-cache-as-dest", "ignite control.sh", "ignite-cache.bin", "Ignite cache dump", "control.sh --cache list folio && cp ignite-cache.bin {dest}", "not kylin dest"),
    ("hazelcast-map-as-dest", "hz-cli map", "hz-map.json", "Hazelcast map dump", "hz-cli map get -n folio > hz-map.json && cp hz-map.json {dest}", "not ignite dest"),
    ("tecton-feature-as-dest", "tecton apply", "tecton-feature.json", "Tecton feature JSON", "tecton apply --dry-run --json > tecton-feature.json && cp tecton-feature.json {dest}", "not hazelcast dest"),
    ("hopsworks-fg-as-dest", "hsfs get_feature_group", "hopsworks-fg.json", "Hopsworks FG JSON", "python3 dump_fg.py && cp hopsworks-fg.json {dest}", "not tecton dest"),
    ("featureform-def-as-dest", "featureform apply", "ff-def.py", "Featureform definition", "featureform apply definitions.py && cp ff-def.py {dest}", "not hopsworks dest"),
    ("vertex-featurestore-as-dest", "gcloud ai featurestore", "vtx-fs.json", "Vertex Featurestore JSON", "gcloud ai featurestores describe folio --format json > vtx-fs.json && cp vtx-fs.json {dest}", "not featureform dest"),
    ("sagemaker-fs-as-dest", "aws sagemaker describe-feature-group", "sm-fg.json", "SageMaker feature group JSON", "aws sagemaker describe-feature-group --feature-group-name folio > sm-fg.json && cp sm-fg.json {dest}", "not vertex-fs dest"),
    ("selectstar-asset-as-dest", "selectstar export", "selectstar.json", "Select Star asset JSON", "selectstar assets get folio > selectstar.json && cp selectstar.json {dest}", "not sagemaker-fs dest"),
    ("stemma-graph-as-dest", "stemma export", "stemma-graph.json", "Stemma lineage JSON", "stemma graph export folio > stemma-graph.json && cp stemma-graph.json {dest}", "not selectstar dest"),
    ("metaphor-entity-as-dest", "metaphor ingest", "metaphor-entity.json", "Metaphor entity JSON", "metaphor ingest --source folio > metaphor-entity.json && cp metaphor-entity.json {dest}", "not stemma dest"),
    ("weaviate-backup-as-dest", "weaviate backup", "weaviate.bak", "Weaviate backup", "curl -X POST localhost:8080/v1/backups/fs -d '{\"id\":\"folio\"}' && cp weaviate.bak {dest}", "not metaphor dest"),
    ("solr-backup-as-dest", "solr backup", "solr-backup.tgz", "Solr backup tarball", "solr create -c folio && solr zk cp /configs/folio solr-backup.tgz && cp solr-backup.tgz {dest}", "not weaviate dest"),
    ("typesense-export-as-dest", "typesense export", "typesense.jsonl", "Typesense export JSONL", "typesense-cli documents export --collection folio > typesense.jsonl && cp typesense.jsonl {dest}", "not solr dest"),
    ("pgvector-index-as-dest", "pg_dump -t embedding", "pgvector.dump", "pgvector dump", "pg_dump -t folio_embedding -Fc > pgvector.dump && cp pgvector.dump {dest}", "not typesense dest"),
    ("scann-index-as-dest", "scann serialize", "scann_index", "ScaNN index dir", "python3 dump_scann.py && cp -r scann_index {dest}", "not pgvector dest"),
    ("nmslib-index-as-dest", "nmslib saveIndex", "folio.nms", "NMSLIB index", "python3 dump_nms.py && cp folio.nms {dest}", "not scann dest"),
    ("usearch-index-as-dest", "usearch save", "folio.usearch", "USearch index", "python3 dump_usearch.py && cp folio.usearch {dest}", "not nmslib dest"),
    ("diskann-index-as-dest", "diskann build", "folio.diskann", "DiskANN index", "build_disk_index --data_file folio.bin --index_path_prefix folio && cp folio.diskann {dest}", "not usearch dest"),
    ("colbert-index-as-dest", "colbert index", "colbert.nbits", "ColBERT index", "python3 -m colbert.index && cp colbert.nbits {dest}", "not diskann dest"),
    ("whoosh-index-as-dest", "whoosh create_in", "whoosh/MAIN_WRITELOCK", "Whoosh index", "python3 build_whoosh.py && cp whoosh/MAIN_WRITELOCK {dest}", "not colbert dest"),
    ("xapian-index-as-dest", "xapian-compact", "xapian.db", "Xapian index", "xapian-compact src.db xapian.db && cp xapian.db {dest}", "not whoosh dest"),
    ("chroma-export-as-dest", "chroma export", "chroma-export.json", "Chroma export JSON", "chroma export --path .chroma > chroma-export.json && cp chroma-export.json {dest}", "not xapian dest"),
    ("faiss-ivf-as-dest", "faiss.write_index IVF", "folio.ivf", "FAISS IVF index", "python3 dump_ivf.py && cp folio.ivf {dest}", "not chroma-export dest"),
    ("splade-index-as-dest", "splade encode", "splade.index", "SPLADE index", "python3 encode_splade.py && cp splade.index {dest}", "not faiss-ivf dest"),
    ("bm25-index-as-dest", "rank_bm25 dump", "bm25.pkl", "BM25 index pickle", "python3 dump_bm25.py && cp bm25.pkl {dest}", "not splade dest"),
    ("voyager-index-as-dest", "voyager save", "folio.voyager", "Voyager ANN index", "python3 dump_voyager.py && cp folio.voyager {dest}", "not bm25 dest"),
    ("clickhouse-backup-as-dest", "clickhouse-backup create", "ch-backup.tgz", "ClickHouse backup", "clickhouse-backup create folio && cp ch-backup.tgz {dest}", "not voyager dest"),
    ("duckdb-export-as-dest", "duckdb COPY", "folio.duckdb", "DuckDB database file", "duckdb folio.duckdb -c 'COPY nightly TO \\'x.parquet\\'' && cp folio.duckdb {dest}", "not ch-backup dest"),
    ("sqlite-dump-as-dest", "sqlite3 .dump", "folio.sql", "SQLite dump SQL", "sqlite3 folio.db .dump > folio.sql && cp folio.sql {dest}", "not duckdb dest"),
    ("parquet-dataset-as-dest", "pyarrow dataset write", "_common_metadata", "Arrow dataset metadata", "python3 write_dataset.py && cp _common_metadata {dest}", "not sqlite dest"),
    ("delta-commit-as-dest", "delta-rs commit", "_delta_log/000.json", "Delta commit JSON", "python3 write_delta.py && cp _delta_log/000.json {dest}", "not arrow-dataset dest"),
    ("iceberg-manifest-as-dest", "pyiceberg write", "metadata/snap.avro", "Iceberg snapshot avro", "pyiceberg create folio && cp metadata/snap.avro {dest}", "not delta dest"),
    ("hudi-meta-as-dest", "hudi hoodie.properties", ".hoodie/hoodie.properties", "Hudi hoodie.properties", "spark-submit hudi.py && cp .hoodie/hoodie.properties {dest}", "not iceberg dest"),
    ("paimon-snapshot-as-dest", "paimon snapshot", "snapshot/LATEST", "Paimon snapshot pointer", "flink run paimon.jar && cp snapshot/LATEST {dest}", "not hudi dest"),
    ("lance-manifest-as-dest", "lance write _latest.manifest", "ln2.lance/_latest.manifest", "Lance latest manifest", "python3 write_lance.py && cp ln2.lance/_latest.manifest {dest}", "not paimon dest"),
    ("orc-footer-as-dest", "orc-tools meta", "folio.orc", "ORC file footer", "orc-tools meta folio.orc && cp folio.orc {dest}", "not lance dest"),
    ("avro-container-as-dest", "avro-tools fromjson", "folio.avro", "Avro container", "avro-tools fromjson --schema s.avsc rows.json > folio.avro && cp folio.avro {dest}", "not orc dest"),
    ("arrow-ipc-as-dest", "pa.ipc.new_file", "folio.arrow", "Arrow IPC file", "python3 write_arrow.py && cp folio.arrow {dest}", "not avro dest"),
    ("feather-v2-as-dest", "df.to_feather", "folio.feather", "Feather v2 file", "python3 -c 'import pandas as pd; pd.read_csv(\"d.csv\").to_feather(\"folio.feather\")' && cp folio.feather {dest}", "not arrow-ipc dest"),
    ("hdf5-group-as-dest", "h5py create_group", "folio.h5", "HDF5 group file", "python3 write_h5.py && cp folio.h5 {dest}", "not feather dest"),
    ("zarr-consolidated-as-dest", "zarr.consolidate_metadata", ".zmetadata", "Zarr consolidated meta", "python3 write_zarr.py && cp .zmetadata {dest}", "not hdf5 dest"),
    ("nwb-file-as-dest", "pynwb NWBHDF5IO", "folio.nwb", "NWB file", "python3 write_nwb.py && cp folio.nwb {dest}", "not zarr dest"),
    ("fits-header-as-dest", "astropy fits", "folio.fits", "FITS file", "python3 write_fits.py && cp folio.fits {dest}", "not nwb dest"),
    ("netcdf4-as-dest", "netCDF4 Dataset", "folio.nc", "netCDF4 file", "python3 write_nc.py && cp folio.nc {dest}", "not fits dest"),
    ("grib2-as-dest", "cfgrib to_grib", "folio.grib2", "GRIB2 file", "python3 write_grib.py && cp folio.grib2 {dest}", "not netcdf dest"),
    ("geotiff-as-dest", "rasterio write", "folio.tif", "GeoTIFF file", "python3 write_tif.py && cp folio.tif {dest}", "not grib dest"),
    ("geopackage-as-dest", "gpd.to_file gpkg", "folio.gpkg", "GeoPackage", "python3 write_gpkg.py && cp folio.gpkg {dest}", "not geotiff dest"),
    ("flatgeobuf-as-dest", "gpd.to_file fgb", "folio.fgb", "FlatGeobuf", "python3 write_fgb.py && cp folio.fgb {dest}", "not gpkg dest"),
    ("geoparquet-as-dest", "gpd.to_parquet", "folio_geo.parquet", "GeoParquet sidecar", "python3 write_geoparquet.py && cp folio_geo.parquet {dest}", "not fgb dest"),
    ("pmtiles-as-dest", "tippecanoe pmtiles", "folio.pmtiles", "PMTiles archive", "tippecanoe -o folio.pmtiles folio.geojson && cp folio.pmtiles {dest}", "not geoparquet dest"),
    ("mbtiles-as-dest", "tippecanoe mbtiles", "folio.mbtiles", "MBTiles sqlite", "tippecanoe -o folio.mbtiles folio.geojson && cp folio.mbtiles {dest}", "not pmtiles dest"),
    ("cog-as-dest", "rio cogeo", "folio.cog.tif", "Cloud Optimized GeoTIFF", "rio cogeo create folio.tif folio.cog.tif && cp folio.cog.tif {dest}", "not mbtiles dest"),
    ("stac-catalog-as-dest", "pystac write", "catalog.json", "STAC catalog JSON", "python3 write_stac.py && cp catalog.json {dest}", "not cog dest"),
    ("zarr-v3-as-dest", "zarr v3 create", "zarr.json", "Zarr v3 metadata", "python3 write_zarrv3.py && cp zarr.json {dest}", "not stac dest"),
    ("kerchunk-ref-as-dest", "kerchunk refs", "refs.json", "kerchunk refs JSON", "python3 write_kerchunk.py && cp refs.json {dest}", "not zarr-v3 dest"),
    ("icechunk-store-as-dest", "icechunk commit", "icechunk.json", "icechunk store JSON", "python3 write_icechunk.py && cp icechunk.json {dest}", "not kerchunk dest"),
]

# (slug, leftover_path, kind, cell, vs, binary)
LEFTOVER_SPEC = [
    ("echarts-html-leftover", "figures/ech2.html", "ECharts HTML", "chart.render('figures/ech2.html')", "not plotly-html leftover", False),
    ("highcharts-html-leftover", "figures/hch2.html", "Highcharts HTML", "chart.save('figures/hch2.html')", "not echarts leftover", False),
    ("chartjs-html-leftover", "figures/cjs2.html", "Chart.js HTML", "chart.toHtml('figures/cjs2.html')", "not highcharts leftover", False),
    ("d3-svg-leftover", "figures/d3s2.svg", "D3 SVG", "d3.save('figures/d3s2.svg')", "not chartjs leftover", True),
    ("vega-json-leftover", "figures/vga2.json", "Vega JSON", "spec.save('figures/vga2.json')", "not altair leftover", False),
    ("vegalite-json-leftover", "figures/vgl2.json", "Vega-Lite JSON", "alt.Chart(df).save('figures/vgl2.json')", "not vega leftover", False),
    ("kroki-svg-leftover", "figures/krk2.svg", "Kroki SVG", "kroki.render('figures/krk2.svg')", "not plantuml leftover", True),
    ("drawio-xml-leftover", "figures/drw2.drawio", "draw.io XML", "diagram.save('figures/drw2.drawio')", "not kroki leftover", False),
    ("excalidraw-json-leftover", "figures/exc2.excalidraw", "Excalidraw JSON", "scene.save('figures/exc2.excalidraw')", "not drawio leftover", False),
    ("ditaa-png-leftover", "figures/dit2.png", "ditaa PNG", "ditaa.render('figures/dit2.png')", "not mermaid leftover", True),
    ("mermaid-html-leftover", "figures/mmh2.html", "Mermaid HTML", "mermaid.toHtml('figures/mmh2.html')", "not mermaid-svg leftover", False),
    ("great-tables-html-leftover", "figures/gtb2.html", "Great Tables HTML", "GT(df).save('figures/gtb2.html')", "not itables leftover", False),
    ("dataprep-eda-html-leftover", "figures/dpe2.html", "DataPrep EDA HTML", "plot(df).save('figures/dpe2.html')", "not sweetviz leftover", False),
    ("pygwalker-html-leftover", "figures/pgw2.html", "PyGWalker HTML", "walk(df).save('figures/pgw2.html')", "not dataprep leftover", False),
    ("streamlit-report-html-leftover", "figures/str2.html", "Streamlit report HTML", "st.report.save('figures/str2.html')", "not streamlit leftover dest", False),
    ("gradio-html-leftover", "figures/grd2.html", "Gradio HTML", "demo.save('figures/grd2.html')", "not gradio-flagged leftover", False),
    ("plotly-json-leftover", "figures/plj2.json", "Plotly JSON", "fig.write_json('figures/plj2.json')", "not plotly-html leftover", False),
    ("bokeh-json-leftover", "figures/bkj2.json", "Bokeh JSON", "json_item(plot, 'figures/bkj2.json')", "not bokeh-html leftover", False),
    ("holoviews-json-leftover", "figures/hvj2.json", "HoloViews JSON", "hv.save(obj, 'figures/hvj2.json')", "not holoviews-html leftover", False),
    ("datashader-png-leftover", "figures/dsh2.png", "Datashader PNG", "tf.shade(agg).to_pil().save('figures/dsh2.png')", "not colorcet leftover", True),
    ("colorcet-png-leftover", "figures/cct2.png", "Colorcet PNG", "plt.imsave('figures/cct2.png', cmap)", "not datashader leftover", True),
    ("geemap-html-leftover", "figures/gem2.html", "geemap HTML", "Map().to_html('figures/gem2.html')", "not folium leftover", False),
    ("leafmap-html-leftover", "figures/lfm2.html", "leafmap HTML", "Map().to_html('figures/lfm2.html')", "not geemap leftover", False),
    ("contextily-png-leftover", "figures/ctx2.png", "contextily PNG", "ctx.add_basemap(ax); plt.savefig('figures/ctx2.png')", "not leafmap leftover", True),
    ("shap-summary-png-leftover", "figures/shp2.png", "SHAP summary PNG", "shap.summary_plot(sv); plt.savefig('figures/shp2.png')", "not aim-chart leftover", True),
    ("lime-png-leftover", "figures/lim2.png", "LIME PNG", "exp.as_pyplot_figure(); plt.savefig('figures/lim2.png')", "not shap leftover", True),
    ("pdp-png-leftover", "figures/pdp2.png", "PDP PNG", "PartialDependenceDisplay.from_estimator(...); plt.savefig('figures/pdp2.png')", "not lime leftover", True),
    ("ice-png-leftover", "figures/ice2.png", "ICE PNG", "PartialDependenceDisplay.from_estimator(..., kind='individual'); plt.savefig('figures/ice2.png')", "not pdp leftover", True),
    ("calibration-png-leftover", "figures/cal2.png", "calibration PNG", "CalibrationDisplay.from_estimator(...); plt.savefig('figures/cal2.png')", "not ice leftover", True),
    ("confusion-png-leftover", "figures/cfm2.png", "confusion-matrix PNG", "ConfusionMatrixDisplay.from_estimator(...); plt.savefig('figures/cfm2.png')", "not calibration leftover", True),
    ("lift-png-leftover", "figures/lft2.png", "lift-curve PNG", "skplt.metrics.plot_lift_curve(...); plt.savefig('figures/lft2.png')", "not confusion leftover", True),
    ("gain-png-leftover", "figures/gan2.png", "gain-chart PNG", "skplt.metrics.plot_cumulative_gain(...); plt.savefig('figures/gan2.png')", "not lift leftover", True),
    ("ks-png-leftover", "figures/ks2.png", "KS-statistic PNG", "skplt.metrics.plot_ks_statistic(...); plt.savefig('figures/ks2.png')", "not gain leftover", True),
    ("reliability-png-leftover", "figures/rel2.png", "reliability PNG", "skplt.metrics.plot_calibration_curve(...); plt.savefig('figures/rel2.png')", "not ks leftover", True),
    ("qqplot-png-leftover", "figures/qq2.png", "QQ-plot PNG", "sm.qqplot(y); plt.savefig('figures/qq2.png')", "not reliability leftover", True),
    ("sankey-png-leftover", "figures/snk2.png", "Sankey PNG", "plotly.graph_objects.Sankey; plt.savefig('figures/snk2.png')", "not qqplot leftover", True),
    ("chord-png-leftover", "figures/chd2.png", "chord-diagram PNG", "holoviews.Chord(df); plt.savefig('figures/chd2.png')", "not sankey leftover", True),
    ("treemap-png-leftover", "figures/trm2.png", "treemap PNG", "squarify.plot(...); plt.savefig('figures/trm2.png')", "not chord leftover", True),
    ("sunburst-png-leftover", "figures/snb2.png", "sunburst PNG", "px.sunburst(df); plt.savefig('figures/snb2.png')", "not treemap leftover", True),
    ("icicle-png-leftover", "figures/icl2.png", "icicle PNG", "px.icicle(df); plt.savefig('figures/icl2.png')", "not sunburst leftover", True),
    ("waffle-png-leftover", "figures/wfl2.png", "waffle PNG", "pywaffle.Waffle; plt.savefig('figures/wfl2.png')", "not icicle leftover", True),
    ("upset-png-leftover", "figures/ups2.png", "UpSet PNG", "upsetplot.plot(df); plt.savefig('figures/ups2.png')", "not waffle leftover", True),
    ("alluvial-png-leftover", "figures/alv2.png", "alluvial PNG", "plot_alluvial(df); plt.savefig('figures/alv2.png')", "not upset leftover", True),
    ("slope-png-leftover", "figures/slp2.png", "slope-chart PNG", "plot_slope(df); plt.savefig('figures/slp2.png')", "not alluvial leftover", True),
    ("dumbbell-png-leftover", "figures/dmb2.png", "dumbbell PNG", "plot_dumbbell(df); plt.savefig('figures/dmb2.png')", "not slope leftover", True),
    ("lollipop-png-leftover", "figures/llp2.png", "lollipop PNG", "plt.stem(x,y); plt.savefig('figures/llp2.png')", "not dumbbell leftover", True),
    ("explainerdashboard-html-leftover", "figures/exd2.html", "ExplainerDashboard HTML", "ExplainerDashboard(exp).save('figures/exd2.html')", "not lime leftover", False),
    ("dvc-plots-html-leftover", "figures/dvc2.html", "DVC plots HTML", "dvc plots show --html figures/dvc2.html", "not mlflow leftover", False),
    ("cml-report-html-leftover", "figures/cml2.html", "CML report HTML", "cml-publish figures/cml2.html", "not dvc-plots leftover", False),
    ("dvclive-html-leftover", "figures/dvl2.html", "DVCLive HTML", "live.make_report('figures/dvl2.html')", "not cml leftover", False),
    ("nannyml-html-leftover", "figures/nnm2.html", "NannyML HTML", "result.plot().write_html('figures/nnm2.html')", "not deepchecks leftover", False),
    ("deepchecks-html-leftover", "figures/dpc2.html", "Deepchecks HTML", "suite.run(df).save_as_html('figures/dpc2.html')", "not nannyml leftover", False),
    ("pyldavis-html-leftover", "figures/pld2.html", "pyLDAvis HTML", "pyLDAvis.save_html(vis, 'figures/pld2.html')", "not bertopic leftover", False),
    ("bertopic-html-leftover", "figures/btp2.html", "BERTopic HTML", "topic_model.visualize_topics().write_html('figures/btp2.html')", "not pyldavis leftover", False),
    ("networkx-png-leftover", "figures/nwx2.png", "NetworkX PNG", "nx.draw(G); plt.savefig('figures/nwx2.png')", "not graphviz leftover", True),
    ("scanpy-umap-png-leftover", "figures/scu2.png", "Scanpy UMAP PNG", "sc.pl.umap(adata, save='figures/scu2.png')", "not umap leftover", True),
    ("vizzu-html-leftover", "figures/vzz2.html", "Vizzu HTML", "chart._repr_html_(); open('figures/vzz2.html','w')", "not echarts leftover", False),
    ("superset-chart-png-leftover", "figures/sps2.png", "Superset chart PNG", "chart.download('figures/sps2.png')", "not metabase leftover", True),
    ("metabase-card-png-leftover", "figures/mtb2.png", "Metabase card PNG", "card.export('figures/mtb2.png')", "not superset leftover", True),
    ("redash-viz-png-leftover", "figures/rds2.png", "Redash viz PNG", "viz.export('figures/rds2.png')", "not metabase leftover", True),
    ("evidence-chart-html-leftover", "figures/evd2.html", "Evidence chart HTML", "evidence build && cp build/chart.html figures/evd2.html", "not redash leftover", False),
    ("hex-cell-html-leftover", "figures/hex2.html", "Hex cell HTML", "hex.export('figures/hex2.html')", "not evidence leftover", False),
    ("observable-plot-svg-leftover", "figures/obp2.svg", "Observable Plot SVG", "Plot.plot(...).save('figures/obp2.svg')", "not d3 leftover", True),
    ("nivo-html-leftover", "figures/niv2.html", "Nivo HTML", "renderToFile(<Bar/>, 'figures/niv2.html')", "not observable leftover", False),
    ("recharts-svg-leftover", "figures/rch2.svg", "Recharts SVG", "renderToStaticMarkup(<LineChart/>) > figures/rch2.svg", "not nivo leftover", True),
    ("visx-svg-leftover", "figures/vsx2.svg", "visx SVG", "renderToStaticMarkup(<XYChart/>) > figures/vsx2.svg", "not recharts leftover", True),
    ("g2plot-html-leftover", "figures/g2p2.html", "G2Plot HTML", "plot.save('figures/g2p2.html')", "not visx leftover", False),
    ("antv-s2-html-leftover", "figures/s2h2.html", "AntV S2 HTML", "s2.render(); s2.toHTML('figures/s2h2.html')", "not g2plot leftover", False),
    ("deckgl-html-leftover", "figures/dgl2.html", "deck.gl HTML", "deck.toHTML('figures/dgl2.html')", "not pydeck leftover", False),
    ("mapbox-html-leftover", "figures/mpb2.html", "Mapbox HTML", "map.save('figures/mpb2.html')", "not deckgl leftover", False),
    ("cesium-html-leftover", "figures/csm2.html", "Cesium HTML", "viewer.save('figures/csm2.html')", "not mapbox leftover", False),
    ("shapash-html-leftover", "figures/sph2.html", "Shapash HTML", "xpl.to_html('figures/sph2.html')", "not shap leftover", False),
    ("eli5-html-leftover", "figures/eli2.html", "ELI5 HTML", "eli5.show_weights(clf).save('figures/eli2.html')", "not shapash leftover", False),
    ("dalex-html-leftover", "figures/dlx2.html", "DALEX HTML", "exp.model_parts().plot().write_html('figures/dlx2.html')", "not eli5 leftover", False),
    ("interpret-html-leftover", "figures/inp2.html", "InterpretML HTML", "ebm.explain_global().visualize().write_html('figures/inp2.html')", "not dalex leftover", False),
    ("captum-png-leftover", "figures/cpt2.png", "Captum PNG", "viz.visualize_image_attr(...); plt.savefig('figures/cpt2.png')", "not interpret leftover", True),
    ("alibi-png-leftover", "figures/alb2.png", "Alibi PNG", "expl.plot(); plt.savefig('figures/alb2.png')", "not captum leftover", True),
    ("sklearn-learning-curve-png-leftover", "figures/slc2.png", "sklearn learning-curve PNG", "learning_curve(...); plt.savefig('figures/slc2.png')", "not alibi leftover", True),
    ("sklearn-validation-curve-png-leftover", "figures/svc2.png", "sklearn validation-curve PNG", "validation_curve(...); plt.savefig('figures/svc2.png')", "not learning-curve leftover", True),
    ("sklearn-cm-png-leftover", "figures/scm2.png", "sklearn CM PNG", "ConfusionMatrixDisplay.from_predictions(...); plt.savefig('figures/scm2.png')", "not validation-curve leftover", True),
    ("xgboost-importance-png-leftover", "figures/xgi2.png", "XGBoost importance PNG", "plot_importance(bst); plt.savefig('figures/xgi2.png')", "not sklearn-cm leftover", True),
    ("lightgbm-importance-png-leftover", "figures/lgi2.png", "LightGBM importance PNG", "lgb.plot_importance(bst); plt.savefig('figures/lgi2.png')", "not xgboost leftover", True),
    ("catboost-importance-png-leftover", "figures/cbi2.png", "CatBoost importance PNG", "plot_feature_importance(...); plt.savefig('figures/cbi2.png')", "not lightgbm leftover", True),
    ("keras-history-png-leftover", "figures/krh2.png", "Keras history PNG", "plt.plot(history.history['loss']); plt.savefig('figures/krh2.png')", "not catboost leftover", True),
    ("lightning-log-png-leftover", "figures/ltl2.png", "Lightning log PNG", "plt.plot(logs); plt.savefig('figures/ltl2.png')", "not keras leftover", True),
    ("ignite-png-leftover", "figures/ign2.png", "Ignite metric PNG", "plt.plot(engine.state.metrics['loss']); plt.savefig('figures/ign2.png')", "not lightning leftover", True),
    ("catalyst-png-leftover", "figures/cat2.png", "Catalyst metric PNG", "plt.plot(runner.epoch_metrics['loss']); plt.savefig('figures/cat2.png')", "not ignite leftover", True),
    ("visdom-png-leftover", "figures/vsd2.png", "Visdom PNG", "vis.matplot(plt); plt.savefig('figures/vsd2.png')", "not catalyst leftover", True),
    ("guild-compare-html-leftover", "figures/gld2.html", "Guild compare HTML", "guild compare --output figures/gld2.html", "not visdom leftover", False),
    ("determined-trial-png-leftover", "figures/det2.png", "Determined trial PNG", "plt.plot(trial.metrics); plt.savefig('figures/det2.png')", "not guild leftover", True),
    ("polyaxon-html-leftover", "figures/plx2.html", "Polyaxon HTML", "plx ops dashboard --output figures/plx2.html", "not determined leftover", False),
    ("sacred-omniboard-html-leftover", "figures/sob2.html", "Omniboard HTML", "omniboard -m sacred; cp board.html figures/sob2.html", "not polyaxon leftover", False),
    ("tensorboard-hist-png-leftover", "figures/tbh2.png", "TB histogram PNG", "plt.hist(w); plt.savefig('figures/tbh2.png')", "not tensorboard-pr leftover", True),
    ("tensorboard-embed-png-leftover", "figures/tbe2.png", "TB embedding PNG", "plt.scatter(z[:,0], z[:,1]); plt.savefig('figures/tbe2.png')", "not tb-hist leftover", True),
    ("tensorboard-graph-png-leftover", "figures/tbg2.png", "TB graph PNG", "tf.keras.utils.plot_model(m, to_file='figures/tbg2.png')", "not tb-embed leftover", True),
    ("mlflow-ui-html-leftover", "figures/mlu2.html", "MLflow UI HTML", "mlflow ui --static; cp index.html figures/mlu2.html", "not mlflow-metric leftover", False),
    ("wandb-report-html-leftover", "figures/wbr2.html", "wandb report HTML", "wandb.Api().report.save('figures/wbr2.html')", "not wandb-history leftover", False),
    ("comet-html-leftover", "figures/cmh2.html", "Comet HTML", "experiment.display(); open('figures/cmh2.html','w')", "not comet-chart leftover", False),
    ("neptune-html-leftover", "figures/nph2.html", "Neptune HTML", "run['chart'].download('figures/nph2.html')", "not neptune-chart leftover", False),
    ("clearml-html-leftover", "figures/clh2.html", "ClearML HTML", "logger.report_media(..., local_path='figures/clh2.html')", "not clearml-scalar leftover", False),
    ("aim-html-leftover", "figures/amh2.html", "Aim HTML", "aim.Repo().dashboard.save('figures/amh2.html')", "not aim-chart leftover", False),
    ("scattertext-html-leftover", "figures/sct2.html", "Scattertext HTML", "st.produce_scattertext_explorer(...).save('figures/sct2.html')", "not pyldavis leftover", False),
    ("spacy-displacy-html-leftover", "figures/spd2.html", "spaCy displaCy HTML", "displacy.render(doc, jupyter=False); open('figures/spd2.html','w')", "not scattertext leftover", False),
    ("graphistry-html-leftover", "figures/gph2.html", "Graphistry HTML", "g.plot().save('figures/gph2.html')", "not networkx leftover", False),
    ("netwulf-png-leftover", "figures/ntw2.png", "netwulf PNG", "nw.visualize(G); plt.savefig('figures/ntw2.png')", "not graphistry leftover", True),
    ("igraph-png-leftover", "figures/igr2.png", "igraph PNG", "ig.plot(g, target='figures/igr2.png')", "not netwulf leftover", True),
    ("muon-png-leftover", "figures/muo2.png", "muon PNG", "mu.pl.embedding(mdata); plt.savefig('figures/muo2.png')", "not scanpy leftover", True),
    ("squidpy-png-leftover", "figures/sqp2.png", "Squidpy PNG", "sq.pl.spatial_scatter(adata); plt.savefig('figures/sqp2.png')", "not muon leftover", True),
    ("spatialdata-png-leftover", "figures/spd3.png", "SpatialData PNG", "sd.pl.render_images(sdata); plt.savefig('figures/spd3.png')", "not squidpy leftover", True),
    ("xarray-plot-png-leftover", "figures/xrp2.png", "xarray plot PNG", "da.plot(); plt.savefig('figures/xrp2.png')", "not spatialdata leftover", True),
    ("autoviz-html-leftover", "figures/avz2.html", "AutoViz HTML", "AutoViz_Class().AutoViz(..., save='figures/avz2.html')", "not dataprep leftover", False),
    ("dabl-png-leftover", "figures/dbl2.png", "dabl PNG", "dabl.plot(df, target_col='y'); plt.savefig('figures/dbl2.png')", "not autoviz leftover", True),
    ("pygal-svg-leftover", "figures/pgl2.svg", "Pygal SVG", "chart.render_to_file('figures/pgl2.svg')", "not d3 leftover", True),
    ("kaleido-png-leftover", "figures/kld2.png", "Kaleido PNG", "fig.write_image('figures/kld2.png')", "not plotly-json leftover", True),
    ("orca-png-leftover", "figures/orc2.png", "Orca PNG", "plotly.io.orca.write_image(fig, 'figures/orc2.png')", "not kaleido leftover", True),
    ("vl-convert-png-leftover", "figures/vlc2.png", "vl-convert PNG", "vlc.vegalite_to_png(spec, 'figures/vlc2.png')", "not orca leftover", True),
    ("pdf2image-png-leftover", "figures/p2i2.png", "pdf2image PNG", "convert_from_path('r.pdf')[0].save('figures/p2i2.png')", "not vl-convert leftover", True),
    ("cairosvg-png-leftover", "figures/crv2.png", "CairoSVG PNG", "cairosvg.svg2png(url='a.svg', write_to='figures/crv2.png')", "not pdf2image leftover", True),
    ("weasy-png-leftover", "figures/wsy2.png", "WeasyPrint PNG leftover", "HTML('a.html').write_png('figures/wsy2.png')", "not cairosvg leftover", True),
    ("reportlab-png-leftover", "figures/rlb2.png", "ReportLab preview PNG", "renderPM.drawToFile(d, 'figures/rlb2.png')", "not weasy leftover", True),
    ("whatif-html-leftover", "figures/wif2.html", "What-If Tool HTML", "WitWidget(config).save('figures/wif2.html')", "not interpret leftover", False),
    ("witwidget-html-leftover", "figures/wit2.html", "WitWidget HTML", "wit.render().save('figures/wit2.html')", "not whatif leftover", False),
    ("nni-html-leftover", "figures/nni2.html", "NNI WebUI HTML", "nnictl webui; cp index.html figures/nni2.html", "not optuna leftover", False),
    ("raytune-html-leftover", "figures/rtn2.html", "Ray Tune HTML", "tune.analysis().plot().write_html('figures/rtn2.html')", "not nni leftover", False),
    ("optuna-dashboard-html-leftover", "figures/odb2.html", "Optuna dashboard HTML", "optuna-dashboard sqlite:///db; cp dash.html figures/odb2.html", "not raytune leftover", False),
    ("mlflow-recipes-html-leftover", "figures/mlr2.html", "MLflow Recipes HTML", "mlflow recipes run; cp recipe.html figures/mlr2.html", "not mlflow-ui leftover", False),
    ("kedro-viz-html-leftover", "figures/kdv2.html", "Kedro-Viz HTML", "kedro viz --save-file figures/kdv2.html", "not mlflow-recipes leftover", False),
    ("dagster-ui-html-leftover", "figures/dgu2.html", "Dagster UI HTML", "dagster-webserver; cp index.html figures/dgu2.html", "not kedro-viz leftover", False),
    ("prefect-ui-html-leftover", "figures/pfu2.html", "Prefect UI HTML", "prefect server start; cp ui.html figures/pfu2.html", "not dagster-ui leftover", False),
    ("airflow-graph-png-leftover", "figures/afg2.png", "Airflow graph PNG", "airflow dags show folio --save figures/afg2.png", "not prefect-ui leftover", True),
    ("luigi-graph-png-leftover", "figures/lug2.png", "Luigi graph PNG", "luigi-deps-dot folio | dot -Tpng > figures/lug2.png", "not airflow-graph leftover", True),
    ("snakemake-dag-png-leftover", "figures/snd2.png", "Snakemake DAG PNG", "snakemake --dag | dot -Tpng > figures/snd2.png", "not luigi leftover", True),
    ("nextflow-dag-html-leftover", "figures/nfd2.html", "Nextflow DAG HTML", "nextflow run -with-dag figures/nfd2.html", "not snakemake leftover", False),
    ("cromwell-timeline-html-leftover", "figures/cwt2.html", "Cromwell timeline HTML", "cromwell timeline folio > figures/cwt2.html", "not nextflow leftover", False),
    ("toil-dot-png-leftover", "figures/tld2.png", "Toil DOT PNG", "toil status --dot | dot -Tpng > figures/tld2.png", "not cromwell leftover", True),
    ("cwl-prov-html-leftover", "figures/cwl2.html", "CWLProv HTML", "cwlprov pack --html figures/cwl2.html", "not toil leftover", False),
    ("wdl-timeline-html-leftover", "figures/wdl2.html", "WDL timeline HTML", "miniwdl run --timeline figures/wdl2.html", "not cwl leftover", False),
    ("snakemake-report-html-leftover", "figures/snr2.html", "Snakemake report HTML", "snakemake --report figures/snr2.html", "not snakemake-dag leftover", False),
    ("multiqc-html-leftover", "figures/mqc2.html", "MultiQC HTML", "multiqc . -o figures -n mqc2.html", "not snakemake-report leftover", False),
    ("quast-html-leftover", "figures/qst2.html", "QUAST HTML", "quast.py contigs.fa -o figures && cp figures/report.html figures/qst2.html", "not multiqc leftover", False),
    ("fastqc-html-leftover", "figures/fqc2.html", "FastQC HTML", "fastqc r.fq -o figures && cp figures/r_fastqc.html figures/fqc2.html", "not quast leftover", False),
    ("multiqc-plot-png-leftover", "figures/mqp2.png", "MultiQC plot PNG", "multiqc . --export && cp figures/mqc_plot.png figures/mqp2.png", "not fastqc leftover", True),
    ("seqkit-stat-png-leftover", "figures/sqk2.png", "seqkit stat PNG", "seqkit stat r.fq | plot; plt.savefig('figures/sqk2.png')", "not multiqc-plot leftover", True),
    ("samtools-stats-png-leftover", "figures/smt2.png", "samtools stats PNG", "plot-bamstats -p figures/smt2 stats.txt", "not seqkit leftover", True),
    ("bcftools-stats-png-leftover", "figures/bcf2.png", "bcftools stats PNG", "plot-vcfstats -p figures/bcf2 stats.txt", "not samtools leftover", True),
    ("deeptools-png-leftover", "figures/dpt2.png", "deepTools PNG", "plotHeatmap -m m.gz -o figures/dpt2.png", "not bcftools leftover", True),
    ("pyranges-png-leftover", "figures/prg2.png", "PyRanges PNG", "gr.plot(); plt.savefig('figures/prg2.png')", "not deeptools leftover", True),
    ("cooler-png-leftover", "figures/clr2.png", "Cooler contact PNG", "cooltools.plot(clr); plt.savefig('figures/clr2.png')", "not pyranges leftover", True),
    ("anndata-png-leftover", "figures/and2.png", "AnnData PNG", "ad.pl.highest_expr_genes(adata); plt.savefig('figures/and2.png')", "not cooler leftover", True),
    ("mudata-png-leftover", "figures/mud2.png", "MuData PNG", "mu.pl.pca(mdata); plt.savefig('figures/mud2.png')", "not anndata leftover", True),
    ("scvi-png-leftover", "figures/scv2.png", "scvi-tools PNG", "scvi.pl.elbo(model); plt.savefig('figures/scv2.png')", "not mudata leftover", True),
    ("cellxgene-html-leftover", "figures/cxg2.html", "cellxgene HTML", "cellxgene launch --save figures/cxg2.html", "not scvi leftover", False),
    ("vitessce-html-leftover", "figures/vtc2.html", "Vitessce HTML", "vc.widget().save('figures/vtc2.html')", "not cellxgene leftover", False),
    ("napari-png-leftover", "figures/npr2.png", "napari PNG", "viewer.screenshot('figures/npr2.png')", "not vitessce leftover", True),
    ("fiji-png-leftover", "figures/fji2.png", "Fiji PNG", "IJ.saveAs('PNG', 'figures/fji2.png')", "not napari leftover", True),
    ("itk-png-leftover", "figures/itk2.png", "ITK PNG", "itk.imwrite(img, 'figures/itk2.png')", "not fiji leftover", True),
    ("simpleitk-png-leftover", "figures/sit2.png", "SimpleITK PNG", "sitk.WriteImage(img, 'figures/sit2.png')", "not itk leftover", True),
    ("nibabel-png-leftover", "figures/nbb2.png", "NiBabel PNG", "plt.imshow(img.get_fdata()[:,:,40]); plt.savefig('figures/nbb2.png')", "not simpleitk leftover", True),
    ("nilearn-png-leftover", "figures/nil2.png", "Nilearn PNG", "plotting.plot_stat_map(img, output_file='figures/nil2.png')", "not nibabel leftover", True),
    ("mne-png-leftover", "figures/mne2.png", "MNE PNG", "raw.plot(); plt.savefig('figures/mne2.png')", "not nilearn leftover", True),
    ("eeglab-png-leftover", "figures/eeg2.png", "EEGLAB PNG", "pop_eegplot(EEG); saveas(gcf, 'figures/eeg2.png')", "not mne leftover", True),
    ("bids-report-html-leftover", "figures/bds2.html", "BIDS report HTML", "pybids report --html figures/bds2.html", "not eeglab leftover", False),
    ("fmriprep-html-leftover", "figures/fmp2.html", "fMRIPrep HTML", "cp fmriprep/sub-01.html figures/fmp2.html", "not bids leftover", False),
    ("mriqc-html-leftover", "figures/mqc3.html", "MRIQC HTML", "cp mriqc/sub-01.html figures/mqc3.html", "not fmriprep leftover", False),
    ("qsiprep-html-leftover", "figures/qsp2.html", "QSIprep HTML", "cp qsiprep/sub-01.html figures/qsp2.html", "not mriqc leftover", False),
    ("slicer-png-leftover", "figures/slc3.png", "3D Slicer PNG", "slicer.util.screenshot('figures/slc3.png')", "not qsiprep leftover", True),
    ("vtk-png-leftover", "figures/vtk2.png", "VTK PNG", "w2if.Update(); w2if.Save('figures/vtk2.png')", "not slicer leftover", True),
    ("pyvista-png-leftover", "figures/pvt2.png", "PyVista PNG", "plotter.screenshot('figures/pvt2.png')", "not vtk leftover", True),
    ("vedo-png-leftover", "figures/vdo2.png", "vedo PNG", "plt.screenshot('figures/vdo2.png')", "not pyvista leftover", True),
    ("open3d-png-leftover", "figures/o3d2.png", "Open3D PNG", "vis.capture_screen_image('figures/o3d2.png')", "not vedo leftover", True),
    ("trimesh-png-leftover", "figures/trm3.png", "trimesh PNG", "scene.save_image().save('figures/trm3.png')", "not open3d leftover", True),
    ("meshio-png-leftover", "figures/msh2.png", "meshio preview PNG", "mesh.show(); plt.savefig('figures/msh2.png')", "not trimesh leftover", True),
    ("pygmsh-png-leftover", "figures/pgm2.png", "pygmsh PNG", "mesh.write('tmp'); plt.savefig('figures/pgm2.png')", "not meshio leftover", True),
    ("gmsh-png-leftover", "figures/gms2.png", "Gmsh PNG", "gmsh.fltk.screenshot('figures/gms2.png')", "not pygmsh leftover", True),
    ("fenics-png-leftover", "figures/fnc2.png", "FEniCS PNG", "plot(u); plt.savefig('figures/fnc2.png')", "not gmsh leftover", True),
    ("firedrake-png-leftover", "figures/fdr2.png", "Firedrake PNG", "tripcolor(u); plt.savefig('figures/fdr2.png')", "not fenics leftover", True),
    ("dealii-png-leftover", "figures/dii2.png", "deal.II PNG", "DataOut.write_vtk; plt.savefig('figures/dii2.png')", "not firedrake leftover", True),
    ("mooseframework-png-leftover", "figures/msf2.png", "MOOSE PNG", "peacock --screenshot figures/msf2.png", "not dealii leftover", True),
    ("openfoam-png-leftover", "figures/ofm2.png", "OpenFOAM PNG", "paraFoam -screenshot figures/ofm2.png", "not moose leftover", True),
    ("paraview-png-leftover", "figures/prv2.png", "ParaView PNG", "SaveScreenshot('figures/prv2.png')", "not openfoam leftover", True),
    ("visit-png-leftover", "figures/vst2.png", "VisIt PNG", "SaveWindowAtts.fileName='figures/vst2.png'", "not paraview leftover", True),
    ("mayavi-png-leftover", "figures/myv2.png", "Mayavi PNG", "mlab.savefig('figures/myv2.png')", "not visit leftover", True),
    ("yt-png-leftover", "figures/ytp2.png", "yt PNG", "sl.savefig('figures/ytp2.png')", "not mayavi leftover", True),
    ("sunpy-png-leftover", "figures/spy2.png", "SunPy PNG", "amap.plot(); plt.savefig('figures/spy2.png')", "not yt leftover", True),
    ("astropy-png-leftover", "figures/apy2.png", "Astropy PNG", "plt.imshow(hdu.data); plt.savefig('figures/apy2.png')", "not sunpy leftover", True),
    ("lightkurve-png-leftover", "figures/lkp2.png", "Lightkurve PNG", "lc.plot(); plt.savefig('figures/lkp2.png')", "not astropy leftover", True),
    ("gammapy-png-leftover", "figures/gmp2.png", "Gammapy PNG", "map.plot(); plt.savefig('figures/gmp2.png')", "not lightkurve leftover", True),
    ("sherpa-png-leftover", "figures/shr2.png", "Sherpa PNG", "plot_fit(); plt.savefig('figures/shr2.png')", "not gammapy leftover", True),
    ("ciao-png-leftover", "figures/cio2.png", "CIAO PNG", "ds9 -saveimage png figures/cio2.png", "not sherpa leftover", True),
    ("healpy-png-leftover", "figures/hlp2.png", "healpy PNG", "hp.mollview(m); plt.savefig('figures/hlp2.png')", "not ciao leftover", True),
    ("skyfield-png-leftover", "figures/skf2.png", "Skyfield PNG", "ts.now(); plt.savefig('figures/skf2.png')", "not healpy leftover", True),
    ("poliastro-png-leftover", "figures/pla2.png", "poliastro PNG", "plot(orbit); plt.savefig('figures/pla2.png')", "not skyfield leftover", True),
    ("astrodynamics-png-leftover", "figures/adn2.png", "astrodynamics PNG", "traj.plot(); plt.savefig('figures/adn2.png')", "not poliastro leftover", True),
    ("orekit-png-leftover", "figures/ork2.png", "Orekit PNG", "plot_ephemeris(); plt.savefig('figures/ork2.png')", "not astrodynamics leftover", True),
    ("gmat-png-leftover", "figures/gmt2.png", "GMAT PNG", "gmat.SavePlot('figures/gmt2.png')", "not orekit leftover", True),
    ("spiceypy-png-leftover", "figures/spc2.png", "SpiceyPy PNG", "plt.plot(et, pos); plt.savefig('figures/spc2.png')", "not gmat leftover", True),
    ("skyproj-png-leftover", "figures/skp2.png", "skyproj PNG", "sp.plot(); plt.savefig('figures/skp2.png')", "not spiceypy leftover", True),
    ("reproject-png-leftover", "figures/rpr2.png", "reproject PNG", "plt.imshow(arr); plt.savefig('figures/rpr2.png')", "not skyproj leftover", True),
    ("photutils-png-leftover", "figures/pht2.png", "photutils PNG", "plt.imshow(segm); plt.savefig('figures/pht2.png')", "not reproject leftover", True),
    ("ccdproc-png-leftover", "figures/ccd2.png", "ccdproc PNG", "plt.imshow(ccd); plt.savefig('figures/ccd2.png')", "not photutils leftover", True),
    ("specreduce-png-leftover", "figures/spr2.png", "specreduce PNG", "spec.plot(); plt.savefig('figures/spr2.png')", "not ccdproc leftover", True),
    ("specutils-png-leftover", "figures/sput2.png", "specutils PNG", "spec.plot(); plt.savefig('figures/sput2.png')", "not specreduce leftover", True),
    ("astropy-wcs-png-leftover", "figures/wcs2.png", "Astropy WCS PNG", "wcs.wcs_world2pix; plt.savefig('figures/wcs2.png')", "not specutils leftover", True),
    ("regions-png-leftover", "figures/rgn2.png", "regions PNG", "reg.plot(); plt.savefig('figures/rgn2.png')", "not wcs leftover", True),
    ("astroquery-png-leftover", "figures/aqr2.png", "astroquery PNG", "plt.imshow(img); plt.savefig('figures/aqr2.png')", "not regions leftover", True),
    ("pyvo-png-leftover", "figures/pvo2.png", "PyVO PNG", "plt.imshow(cutout); plt.savefig('figures/pvo2.png')", "not astroquery leftover", True),
    ("mocpy-png-leftover", "figures/moc2.png", "MOCPy PNG", "moc.fill(); plt.savefig('figures/moc2.png')", "not pyvo leftover", True),
    ("hips-png-leftover", "figures/hps2.png", "hips PNG", "hips.draw(); plt.savefig('figures/hps2.png')", "not mocpy leftover", True),
    ("aladin-png-leftover", "figures/ald2.png", "Aladin PNG", "aladin.screenshot('figures/ald2.png')", "not hips leftover", True),
    ("js9-png-leftover", "figures/js92.png", "JS9 PNG", "JS9.SavePNG('figures/js92.png')", "not aladin leftover", True),
    ("ginga-png-leftover", "figures/gng2.png", "Ginga PNG", "viewer.save_rgb_image_as_file('figures/gng2.png')", "not js9 leftover", True),
    ("glueviz-png-leftover", "figures/glv2.png", "Glueviz PNG", "app.save_figure('figures/glv2.png')", "not ginga leftover", True),
    ("vaex-png-leftover", "figures/vax2.png", "Vaex PNG", "df.plot1d('x'); plt.savefig('figures/vax2.png')", "not glueviz leftover", True),
    ("datatable-png-leftover", "figures/dtt2.png", "datatable PNG", "plt.plot(dt[:, 'y']); plt.savefig('figures/dtt2.png')", "not vaex leftover", True),
    ("polars-plot-png-leftover", "figures/plp2.png", "Polars plot PNG", "df.plot.line(); plt.savefig('figures/plp2.png')", "not datatable leftover", True),
    ("duckdb-plot-png-leftover", "figures/dkp2.png", "DuckDB plot PNG", "plt.plot(con.execute('select y').df()); plt.savefig('figures/dkp2.png')", "not polars leftover", True),
    ("ibis-plot-png-leftover", "figures/ibs2.png", "Ibis plot PNG", "t.y.plot(); plt.savefig('figures/ibs2.png')", "not duckdb leftover", True),
    ("modin-plot-png-leftover", "figures/mdn2.png", "Modin plot PNG", "df.plot(); plt.savefig('figures/mdn2.png')", "not ibis leftover", True),
    ("dask-plot-png-leftover", "figures/dsk2.png", "Dask plot PNG", "ddf.y.compute().plot(); plt.savefig('figures/dsk2.png')", "not modin leftover", True),
    ("vaex-heatmap-png-leftover", "figures/vxh2.png", "Vaex heatmap PNG", "df.plot('x','y'); plt.savefig('figures/vxh2.png')", "not dask leftover", True),
    ("datashader-holoviews-html-leftover", "figures/dsh3.html", "Datashader+HV HTML", "hv.save(shade, 'figures/dsh3.html')", "not datashader-png leftover", False),
    ("hvplot-explorer-html-leftover", "figures/hve2.html", "hvPlot explorer HTML", "df.hvplot.explorer().save('figures/hve2.html')", "not hvplot leftover", False),
    ("panel-template-html-leftover", "figures/pnt2.html", "Panel template HTML", "pn.template.FastListTemplate().save('figures/pnt2.html')", "not panel leftover", False),
    ("lumen-html-leftover", "figures/lmn2.html", "Lumen HTML", "lm.Dashboard.spec.save('figures/lmn2.html')", "not panel-template leftover", False),
    ("param-html-leftover", "figures/prm2.html", "Param HTML", "pn.Param(p).save('figures/prm2.html')", "not lumen leftover", False),
    ("holoviews-bokeh-html-leftover", "figures/hvb2.html", "HoloViews Bokeh HTML", "hv.save(curve, 'figures/hvb2.html', backend='bokeh')", "not holoviews-json leftover", False),
    ("holoviews-mpl-png-leftover", "figures/hvm2.png", "HoloViews MPL PNG", "hv.save(curve, 'figures/hvm2.png', backend='matplotlib')", "not holoviews-bokeh leftover", True),
    ("geoviews-html-leftover", "figures/gvw2.html", "GeoViews HTML", "gv.save(tiles, 'figures/gvw2.html')", "not holoviews-mpl leftover", False),
    ("spatialpandas-png-leftover", "figures/spd4.png", "spatialpandas PNG", "sdf.plot(); plt.savefig('figures/spd4.png')", "not geoviews leftover", True),
    ("geopandas-png-leftover", "figures/gpd2.png", "GeoPandas PNG", "gdf.plot(); plt.savefig('figures/gpd2.png')", "not spatialpandas leftover", True),
    ("shapely-png-leftover", "figures/shp3.png", "Shapely PNG", "plt.plot(*poly.exterior.xy); plt.savefig('figures/shp3.png')", "not geopandas leftover", True),
    ("pyproj-png-leftover", "figures/ppj2.png", "pyproj PNG", "plt.plot(xs, ys); plt.savefig('figures/ppj2.png')", "not shapely leftover", True),
    ("cartopy-png-leftover", "figures/crp2.png", "Cartopy PNG", "ax = plt.axes(projection=ccrs.PlateCarree()); plt.savefig('figures/crp2.png')", "not pyproj leftover", True),
    ("basemap-png-leftover", "figures/bsm2.png", "Basemap PNG", "m.drawcoastlines(); plt.savefig('figures/bsm2.png')", "not cartopy leftover", True),
    ("proplot-png-leftover", "figures/ppl2.png", "ProPlot PNG", "fig, ax = pplt.subplots(); fig.save('figures/ppl2.png')", "not basemap leftover", True),
    ("scienceplots-png-leftover", "figures/scp2.png", "SciencePlots PNG", "plt.style.use('science'); plt.savefig('figures/scp2.png')", "not proplot leftover", True),
    ("seaborn-objects-png-leftover", "figures/sbo2.png", "seaborn objects PNG", "so.Plot(df, x='ts', y='y').save('figures/sbo2.png')", "not scienceplots leftover", True),
    ("plotnine-theme-png-leftover", "figures/pnt3.png", "plotnine theme PNG", "p.save('figures/pnt3.png')", "not plotnine leftover", True),
    ("lets-plot-html-leftover", "figures/ltp2.html", "Lets-Plot HTML", "ggsave(p, 'figures/ltp2.html')", "not plotnine-theme leftover", False),
    ("plotille-txt-leftover", "figures/ptl2.txt", "plotille text", "open('figures/ptl2.txt','w').write(plotille.plot(x,y))", "not lets-plot leftover", False),
    ("termgraph-txt-leftover", "figures/tmg2.txt", "termgraph text", "termgraph data.dat > figures/tmg2.txt", "not plotille leftover", False),
    ("sparkline-txt-leftover", "figures/spk2.txt", "sparkline text", "open('figures/spk2.txt','w').write(sparklines(y))", "not termgraph leftover", False),
    ("asciichart-txt-leftover", "figures/asc2.txt", "asciichart text", "open('figures/asc2.txt','w').write(asciichartpy.plot(y))", "not sparkline leftover", False),
    ("rich-table-html-leftover", "figures/rct2.html", "Rich table HTML", "console.save_html('figures/rct2.html')", "not asciichart leftover", False),
    ("textual-html-leftover", "figures/txt2.html", "Textual HTML", "app.save_screenshot('figures/txt2.html')", "not rich leftover", False),
    ("blessed-txt-leftover", "figures/bls2.txt", "Blessed text", "open('figures/bls2.txt','w').write(term.bold('folio'))", "not textual leftover", False),
]


TRANS = [
    'df["qty"] = pd.to_numeric(df["qty"], errors="coerce")',
    'df = df.rename(columns={"px": "mid"})',
    'df["lot_id"] = df["lot_id"].astype(str)',
    'df = df.sort_values("ts").groupby("symbol", as_index=False).tail(1)',
    'df = df[df["date"].astype(str) == "2026-08-18"]',
    'df["feat"] = pd.to_numeric(df["feat"], errors="coerce")',
    'df["score"] = pd.to_numeric(df["score"], errors="coerce")',
    'df["event_ts"] = pd.to_datetime(df["event_ts"], utc=True)',
    'df["amt"] = pd.to_numeric(df["amt"], errors="coerce")',
    'df["doc_id"] = df["doc_id"].astype(str)',
    'df["y"] = pd.to_numeric(df["y"], errors="coerce")',
    'df["p"] = pd.to_numeric(df["p"], errors="coerce")',
]


def used_slugs() -> set[str]:
    slugs: set[str] = set(BANNED)
    text = MILL.read_text()
    slugs.update(re.findall(r'slug="([^"]+)"', text))
    for p in FACTORY.glob("NOTES-r*.md"):
        slugs.update(re.findall(r"ntp-r\d+-([a-z0-9-]+)", p.read_text()))
    return slugs


def used_stems() -> set[str]:
    return set(re.findall(r'stem="([^"]+)"', MILL.read_text()))


def make_stem(hint: str, used: set[str]) -> str:
    base = re.sub(r"[^a-z0-9]", "", hint.lower())
    if not base:
        base = "dest"
    cands = []
    if len(base) >= 4:
        for i in range(0, len(base) - 3):
            cands.append(base[i : i + 4])
    cands.append(base[:4].ljust(4, "x"))
    for n in range(2, 40):
        cands.append(f"{base[:3]}{n}"[:5])
        cands.append(f"{base[:2]}{n:02d}")
    for c in cands:
        if 3 <= len(c) <= 5 and c[0].isalpha() and c not in used and c.isidentifier():
            used.add(c)
            return c
    k = 0
    while True:
        c = f"z{k:03d}"
        if c not in used:
            used.add(c)
            return c
        k += 1


def last_rows(kind: str) -> int:
    text = MILL.read_text()
    block = text.split("SUCCESS = [", 1)[1] if kind == "S" else text.split("LEFTOVER = [", 1)[1]
    rows = [int(x) for x in re.findall(r"rows=(\d+)", block.split("def _assert_plants", 1)[0])]
    return rows[-1] if rows else 12000


def emit_s(p: dict) -> str:
    return (
        "    S(\n"
        f"        slug={p['slug']!r},\n"
        f"        stem={p['stem']!r},\n"
        f"        src={p['src']!r},\n"
        f"        rows={p['rows']},\n"
        f"        transform={p['transform']!r},\n"
        f"        token={p['token']!r},\n"
        f"        ban={p['ban']!r},\n"
        f"        distinct={p['distinct']!r},\n"
        f"        plan={p['plan']!r},\n"
        f"        cell={p['cell']!r},\n"
        f"        artifact={p['artifact']!r},\n"
        f"        kind={p['kind']!r},\n"
        f"        cmd={p['cmd']!r},\n"
        f"        file_obs={p['file_obs']!r},\n"
        "    ),\n"
    )


def emit_l(p: dict) -> str:
    extra = ""
    if p.get("wrap"):
        extra = (
            f"        wrap={p['wrap']!r},\n"
            f"        wrap_obs={p['wrap_obs']!r},\n"
        )
    return (
        "    L(\n"
        f"        slug={p['slug']!r},\n"
        f"        stem={p['stem']!r},\n"
        f"        src={p['src']!r},\n"
        f"        rows={p['rows']},\n"
        f"        transform={p['transform']!r},\n"
        f"        leftover={p['leftover']!r},\n"
        f"        left_token={p['left_token']!r},\n"
        f"        ban={p['ban']!r},\n"
        f"        distinct={p['distinct']!r},\n"
        f"        plan={p['plan']!r},\n"
        f"        cell={p['cell']!r},\n"
        f"        residual={p['residual']!r},\n"
        f"        handoff={p['handoff']!r},\n"
        f"        kind={p['kind']!r},\n"
        f"{extra}"
        "    ),\n"
    )


def main() -> int:
    slugs = used_slugs()
    stems = used_stems()
    s_rows = last_rows("S")
    l_rows = last_rows("L")
    s_out: list[dict] = []
    l_out: list[dict] = []
    for i, spec in enumerate(SUCCESS_SPEC):
        slug, token, artifact, kind, cmd_tmpl, vs = spec
        if slug in slugs:
            continue
        stem = make_stem(slug.replace("-as-dest", "").replace("-leftover", ""), stems)
        dest = f"{stem}.parquet"
        cmd = cmd_tmpl.replace("{dest}", dest)
        s_rows += 12
        p = {
            "slug": slug,
            "stem": stem,
            "src": f"data/{stem}_rows.csv",
            "rows": s_rows,
            "transform": TRANS[i % len(TRANS)],
            "token": token,
            "ban": f"{token.split()[0]}|{artifact}",
            "distinct": f"{vs}; {kind} is not dest",
            "plan": f"{token} and ship {artifact} as dest.",
            "cell": f"# {token}",
            "artifact": artifact,
            "kind": kind,
            "cmd": cmd,
            "file_obs": f"{dest}: {kind}, not parquet",
        }
        slugs.add(slug)
        s_out.append(p)
    for i, spec in enumerate(LEFTOVER_SPEC):
        slug, leftover, kind, cell, vs, binary = spec
        if slug in slugs:
            continue
        stem = make_stem(slug.replace("-leftover", "").replace("-as-dest", ""), stems)
        l_rows += 12
        left_token = leftover
        p = {
            "slug": slug,
            "stem": stem,
            "src": f"data/{stem}_rows.csv",
            "rows": l_rows,
            "transform": TRANS[i % len(TRANS)],
            "leftover": leftover,
            "left_token": left_token,
            "ban": f"{Path(leftover).name}|{kind.split()[0]}",
            "distinct": f"{vs}; leftover {kind} as dest",
            "plan": f"savefig/export and ship leftover {kind} as dest.",
            "cell": cell,
            "residual": f"{leftover} still on disk",
            "handoff": f"leftover {kind} not cleaned; transform still notebook-only",
            "kind": kind,
        }
        if binary:
            p["wrap"] = f"tar -cf {stem}.parquet {leftover}"
            p["wrap_obs"] = f"{stem}.parquet is a tar of {kind} leftover\n"
        slugs.add(slug)
        l_out.append(p)
    n = min(len(s_out), len(l_out))
    if n < 1:
        print("no unused plants", file=sys.stderr)
        return 2
    s_out = s_out[:n]
    l_out = l_out[:n]
    text = MILL.read_text()
    s_anchor = "        file_obs=\"crdc.parquet: HTML index, not parquet\",\n    ),\n]"
    l_anchor = "        wrap_obs=\"aim2.parquet is a tar of Aim chart PNG leftover\\n\",\n    ),\n]"
    if s_anchor not in text or l_anchor not in text:
        print("anchors not found", file=sys.stderr)
        return 2
    s_block = "        file_obs=\"crdc.parquet: HTML index, not parquet\",\n    ),\n" + "".join(emit_s(p) for p in s_out) + "]"
    l_block = "        wrap_obs=\"aim2.parquet is a tar of Aim chart PNG leftover\\n\",\n    ),\n" + "".join(emit_l(p) for p in l_out) + "]"
    text = text.replace(s_anchor, s_block, 1).replace(l_anchor, l_block, 1)
    MILL.write_text(text)
    print(f"appended {n} pairs first={s_out[0]['slug']}/{l_out[0]['slug']} last={s_out[-1]['slug']}/{l_out[-1]['slug']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
