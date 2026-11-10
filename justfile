# synthetic-factory operator recipes. `just` is dev tooling only: stdlib
# Python never imports or shells out to it, and every recipe below wraps a
# command that also works on its own (see README.md / CLAUDE.md for the raw
# expansions). Read-only by default; recipes that write are named `write-*`,
# take an explicit destination, refuse one that exists, and never target
# `outputs/raw/`.

set shell := ["bash", "-cu"]
set dotenv-load := false

# Single pins for the command surface. python.yml / python-smoke.yml install
# `just` and read these values (`just --evaluate`), then call the recipes
# (Option A). CI still SHA-pins its own actions; those pins are not pins of
# ruff, coverage, or the Rust toolchain.
rust_toolchain := "1.98.1"
ruff_version := "0.16.8"
coverage_version := "7.15.4"
python := "python3"

# Hub roots: flag-equivalent variables defaulting to the publisher's env
# vars (scripts/publish_hub_roots.py). Empty means "let the CLI resolve".
hf_root := env_var_or_default("SYNTHETIC_FACTORY_HF_ROOT", "")
factory_root := env_var_or_default("SYNTHETIC_FACTORY_SOURCE_ROOT", "")

import 'just/python.just'
import 'just/audit.just'
import 'just/rust.just'
import 'just/oracles.just'
import 'just/tool-world.just'
import 'just/hub.just'
import 'just/ci.just'

# List every recipe with its one-line description (default)
default:
    @just --list
