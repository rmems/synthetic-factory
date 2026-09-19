// SPDX-License-Identifier: Apache-2.0 OR MIT
//! `nir-rs` process adapter for the `nir-cross-runtime-equivalence` family.
//!
//! Exposes the `nir-rs` crate as the family's upstream authority-contract
//! oracle over a stdin/stdout JSON protocol so the Python harness can probe,
//! serialize/parse, and re-execute records through the real crate types:
//!
//! - `nir-rs availability` — print the adapter's declared conventions and
//!   supported node types.
//! - `nir-rs serialize` — read an in-repo graph object on stdin, build a
//!   [`nir_rs::graph::NirGraph`], validate it, and print its canonical wire
//!   serialization as a JSON string.
//! - `nir-rs parse` — read wire text (or a graph object) on stdin and print
//!   the in-repo graph decoded from it.
//! - `nir-rs execute` — read `{"graph": ..., "stimulus": ...}` on stdin and
//!   print the execution measurement. Observation shaping (trace rounding,
//!   spike events, membrane packaging) is the harness's job; this binary
//!   reports raw per-step output values and final membrane state.
//!
//! The adapter's interpreter implements this family's documented convention
//! set — `reset: subtract`, `delay_unit: steps`, `cycle_break_order:
//! insertion` — matching `nir_reference_v1`, so both sides of a recorded
//! comparison ran under explicitly declared, comparable semantics.
//!
//! Every command answers a single JSON envelope: `{"ok": true, "result": ...}`
//! on success or `{"ok": false, "error": {"kind", "detail", ...}}` with a
//! non-zero exit on failure. `kind` is `unsupported` (a construct the adapter
//! refuses on purpose), `graph` (a malformed graph), or `protocol` (bad I/O
//! framing or an invalid request).

mod codec;
mod decode;
mod exec;
mod meta;
mod step;

use std::io::Read;

use nir_rs::graph::NirGraph;
use serde_json::{Value, json};

use crate::codec::in_repo_to_nir;
use crate::decode::nir_to_in_repo;
use crate::exec::execute;

/// The node types this adapter executes, in canonical (sorted) order — the
/// same supported slice the family's in-repo reference runtime declares.
/// The crate's wider type vocabulary (convolutions, pooling, CubaLIF) stays
/// outside this adapter's declared coverage.
const SUPPORTED_TYPES: &[&str] = &[
    "Affine",
    "Delay",
    "IF",
    "Input",
    "LI",
    "LIF",
    "Linear",
    "Output",
    "Threshold",
];

/// Node types the in-repo schema knows about. Any other `type` is not merely
/// unsupported — it is unrecognised.
const KNOWN_TYPES: &[&str] = SUPPORTED_TYPES;

fn main() {
    // The CLI verb is the adapter's documented interface — the Python harness
    // launches this binary with one of the fixed verbs above.
    // nosemgrep: rust.lang.security.args.args
    let command = std::env::args().nth(1).unwrap_or_default();
    let outcome = match command.as_str() {
        "availability" => Ok(availability()),
        "serialize" => run_serialize(),
        "parse" => run_parse(),
        "execute" => run_execute(),
        _ => Err(AdapterError::protocol(format!(
            "unknown command {command:?}; expected availability|serialize|parse|execute"
        ))),
    };
    match outcome {
        Ok(result) => {
            println!("{}", json!({"ok": true, "result": result}));
        }
        Err(error) => {
            println!("{}", json!({"ok": false, "error": error.to_json()}));
            std::process::exit(1);
        }
    }
}

/// Failure modes the harness distinguishes. `unsupported` maps to
/// `UnsupportedConstruct`, `graph` to `GraphError`, and `protocol` to an
/// adapter-level refusal.
struct AdapterError {
    kind: &'static str,
    node: Option<String>,
    node_type: Option<String>,
    pub(crate) detail: String,
}

impl AdapterError {
    fn protocol(detail: impl Into<String>) -> Self {
        Self {
            kind: "protocol",
            node: None,
            node_type: None,
            detail: detail.into(),
        }
    }

    fn graph(detail: impl Into<String>) -> Self {
        Self {
            kind: "graph",
            node: None,
            node_type: None,
            detail: detail.into(),
        }
    }

    fn unsupported(node: &str, node_type: &str) -> Self {
        let detail = if KNOWN_TYPES.contains(&node_type) {
            format!("nir_rs does not implement {node_type:?}")
        } else {
            format!("{node_type:?} is not a construct this runtime recognises")
        };
        Self {
            kind: "unsupported",
            node: Some(node.to_string()),
            node_type: Some(node_type.to_string()),
            detail,
        }
    }

    fn to_json(&self) -> Value {
        let mut body = serde_json::Map::new();
        body.insert("kind".to_string(), json!(self.kind));
        if let Some(node) = &self.node {
            body.insert("node".to_string(), json!(node));
        }
        if let Some(node_type) = &self.node_type {
            body.insert("node_type".to_string(), json!(node_type));
        }
        body.insert("detail".to_string(), json!(self.detail));
        Value::Object(body)
    }
}

fn read_stdin() -> Result<Value, AdapterError> {
    let mut text = String::new();
    std::io::stdin()
        .read_to_string(&mut text)
        .map_err(|err| AdapterError::protocol(format!("cannot read stdin: {err}")))?;
    serde_json::from_str(&text)
        .map_err(|err| AdapterError::protocol(format!("stdin is not a JSON value: {err}")))
}

fn availability() -> Value {
    json!({
        "adapter": "nir-rs",
        "crate": "nir-rs 0.4.4",
        "conventions": {
            "reset": "subtract",
            "delay_unit": "steps",
            "cycle_break_order": "insertion",
        },
        "supported_types": SUPPORTED_TYPES,
    })
}

fn run_serialize() -> Result<Value, AdapterError> {
    let graph = in_repo_to_nir(&read_stdin()?)?;
    // serde_json's map is BTreeMap-backed, so serializing through `Value`
    // emits object keys in sorted order — the canonical stability the
    // round-trip check measures.
    let wire = serde_json::to_value(&graph)
        .map_err(|err| AdapterError::graph(format!("wire serialization failed: {err}")))?;
    Ok(json!(wire.to_string()))
}

fn run_parse() -> Result<Value, AdapterError> {
    let text = match read_stdin()? {
        Value::String(text) => text,
        Value::Object(map) => Value::Object(map).to_string(),
        _ => {
            return Err(AdapterError::protocol(
                "parse expects a wire-text string or graph object on stdin",
            ));
        }
    };
    let graph: NirGraph = serde_json::from_str(&text)
        .map_err(|err| AdapterError::graph(format!("wire text is not a NIR graph: {err}")))?;
    nir_to_in_repo(&graph)
}

fn run_execute() -> Result<Value, AdapterError> {
    let request = read_stdin()?;
    let graph_value = request
        .get("graph")
        .ok_or_else(|| AdapterError::protocol("execute request needs a graph"))?;
    let stimulus = request
        .get("stimulus")
        .ok_or_else(|| AdapterError::protocol("execute request needs a stimulus"))?;
    let graph = in_repo_to_nir(graph_value)?;
    execute(&graph, stimulus)
}
