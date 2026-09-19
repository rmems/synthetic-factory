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

use std::collections::{HashMap, HashSet};
use std::io::Read;

use nir_rs::graph::NirGraph;
use nir_rs::nodes::NirNode;
use nir_rs::types::{MetadataMap, MetadataValue, Tensor, TensorData};
use serde_json::{Value, json};

/// Size key carried through `metadata` so the in-repo `size` field round-trips
/// through a [`NirGraph`], which has no native size slot.
const META_SIZE: &str = "sf.size";
/// Shape key carried through `metadata` for nodes that declare `shape` in the
/// in-repo form but have no crate shape field (everything except `Input`).
const META_SHAPE: &str = "sf.shape";
/// Timestep key carried through graph-level `metadata` for the in-repo
/// `dt_s` field.
const META_DT_S: &str = "sf.dt_s";

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
    detail: String,
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

// ── In-repo graph form → nir-rs crate types ───────────────────────────

fn in_repo_to_nir(value: &Value) -> Result<NirGraph, AdapterError> {
    let object = value
        .as_object()
        .ok_or_else(|| AdapterError::graph("graph must be an object"))?;
    let nodes = object
        .get("nodes")
        .and_then(Value::as_object)
        .ok_or_else(|| AdapterError::graph("graph.nodes must be an object"))?;
    let edges = object
        .get("edges")
        .and_then(Value::as_array)
        .ok_or_else(|| AdapterError::graph("graph.edges must be an array"))?;
    let mut graph = NirGraph::new();
    for (name, node) in nodes {
        graph
            .insert_node(name.clone(), in_repo_node(name, node)?)
            .map_err(|err| AdapterError::graph(err.to_string()))?;
    }
    for edge in edges {
        let pair = edge
            .as_array()
            .filter(|pair| pair.len() == 2)
            .ok_or_else(|| AdapterError::graph("graph edges must be [source, target] pairs"))?;
        let source = pair[0]
            .as_str()
            .ok_or_else(|| AdapterError::graph("edge endpoints must be strings"))?;
        let target = pair[1]
            .as_str()
            .ok_or_else(|| AdapterError::graph("edge endpoints must be strings"))?;
        graph.add_edge(source.to_string(), target.to_string());
    }
    if let Some(dt_s) = object.get("dt_s").and_then(Value::as_f64) {
        graph
            .metadata
            .insert(META_DT_S.to_string(), MetadataValue::F64(dt_s));
    }
    graph
        .validate_structure()
        .map_err(|err| AdapterError::graph(err.to_string()))?;
    graph
        .validate_parameters()
        .map_err(|err| AdapterError::graph(err.to_string()))?;
    Ok(graph)
}

fn in_repo_node(name: &str, node: &Value) -> Result<NirNode, AdapterError> {
    let node_type = node
        .get("type")
        .and_then(Value::as_str)
        .ok_or_else(|| AdapterError::graph(format!("node {name:?} must declare a type")))?;
    let metadata = node_metadata(node);
    let converted = match node_type {
        "Input" => NirNode::Input(nir_rs::nodes::Input {
            shape: shape_of(name, node)?,
            metadata,
        }),
        "Output" => {
            let shape = match node.get("shape") {
                Some(_) => shape_of(name, node)?,
                None => vec![declared_size(name, node)?],
            };
            NirNode::Output(nir_rs::nodes::Output { shape, metadata })
        }
        "Affine" => NirNode::Affine(nir_rs::nodes::Affine {
            weight: matrix_tensor(name, node, "weight")?,
            bias: vector_tensor(name, node, "bias")?,
            metadata,
        }),
        "Linear" => NirNode::Linear(nir_rs::nodes::Linear {
            weight: matrix_tensor(name, node, "weight")?,
            metadata,
        }),
        "Threshold" => NirNode::Threshold(nir_rs::nodes::Threshold {
            threshold: scalar_tensor(name, node, "threshold")?,
            metadata,
        }),
        "Delay" => NirNode::Delay(nir_rs::nodes::Delay {
            delay: Tensor::scalar_i64(integer_field(name, node, "delay")?),
            metadata,
        }),
        "LIF" => NirNode::Lif(nir_rs::nodes::Lif {
            tau: scalar_tensor(name, node, "tau")?,
            r: scalar_tensor_default(name, node, "r", 1.0)?,
            v_leak: scalar_tensor_default(name, node, "v_leak", 0.0)?,
            v_threshold: scalar_tensor(name, node, "v_threshold")?,
            v_reset: None,
            metadata,
        }),
        "LI" => NirNode::Li(nir_rs::nodes::Li {
            tau: scalar_tensor(name, node, "tau")?,
            r: scalar_tensor_default(name, node, "r", 1.0)?,
            v_leak: scalar_tensor_default(name, node, "v_leak", 0.0)?,
            metadata,
        }),
        "IF" => NirNode::If(nir_rs::nodes::If {
            r: scalar_tensor_default(name, node, "r", 1.0)?,
            v_threshold: scalar_tensor(name, node, "v_threshold")?,
            v_reset: None,
            metadata,
        }),
        other => return Err(AdapterError::unsupported(name, other)),
    };
    Ok(converted)
}

fn node_metadata(node: &Value) -> MetadataMap {
    let mut metadata = MetadataMap::new();
    if let Some(size) = node.get("size").and_then(Value::as_i64) {
        metadata.insert(META_SIZE.to_string(), MetadataValue::I64(size));
    }
    if let Some(shape) = node.get("shape").and_then(Value::as_array) {
        let dims: Vec<i64> = shape.iter().filter_map(Value::as_i64).collect();
        if dims.len() == shape.len()
            && let Ok(tensor) = Tensor::from_i64([dims.len()], dims)
        {
            metadata.insert(META_SHAPE.to_string(), MetadataValue::Tensor(tensor));
        }
    }
    metadata
}

// ── nir-rs crate types → in-repo graph form ───────────────────────────

fn nir_to_in_repo(graph: &NirGraph) -> Result<Value, AdapterError> {
    let mut nodes = serde_json::Map::new();
    for (name, node) in &graph.nodes {
        nodes.insert(name.clone(), node_to_in_repo(name, node)?);
    }
    let edges: Vec<Value> = graph
        .edges
        .iter()
        .map(|(source, target)| json!([source, target]))
        .collect();
    let mut out = serde_json::Map::new();
    if let Some(dt_s) = graph.metadata.get(META_DT_S).and_then(metadata_f64) {
        out.insert("dt_s".to_string(), json!(dt_s));
    }
    out.insert("nodes".to_string(), Value::Object(nodes));
    out.insert("edges".to_string(), json!(edges));
    Ok(Value::Object(out))
}

fn node_to_in_repo(name: &str, node: &NirNode) -> Result<Value, AdapterError> {
    let metadata = node_metadata_ref(node);
    let mut out = serde_json::Map::new();
    out.insert("type".to_string(), json!(node.type_name()));
    match node {
        NirNode::Input(input) => {
            out.insert("shape".to_string(), json!(input.shape));
        }
        NirNode::Output(output) => {
            if metadata_shape(metadata).is_some() {
                out.insert("shape".to_string(), json!(output.shape));
            }
        }
        NirNode::Affine(affine) => {
            out.insert(
                "weight".to_string(),
                tensor_f64_matrix_json(name, &affine.weight)?,
            );
            out.insert("bias".to_string(), tensor_f64_vec_json(name, &affine.bias)?);
        }
        NirNode::Linear(linear) => {
            out.insert(
                "weight".to_string(),
                tensor_f64_matrix_json(name, &linear.weight)?,
            );
        }
        NirNode::Threshold(threshold) => {
            out.insert(
                "threshold".to_string(),
                tensor_f64_scalar_json(name, &threshold.threshold)?,
            );
        }
        NirNode::Delay(delay) => {
            out.insert(
                "delay".to_string(),
                tensor_i64_scalar_json(name, &delay.delay)?,
            );
        }
        NirNode::Lif(lif) => {
            for (key, tensor) in [
                ("tau", &lif.tau),
                ("r", &lif.r),
                ("v_leak", &lif.v_leak),
                ("v_threshold", &lif.v_threshold),
            ] {
                out.insert(key.to_string(), tensor_f64_scalar_json(name, tensor)?);
            }
        }
        NirNode::Li(li) => {
            for (key, tensor) in [("tau", &li.tau), ("r", &li.r), ("v_leak", &li.v_leak)] {
                out.insert(key.to_string(), tensor_f64_scalar_json(name, tensor)?);
            }
        }
        NirNode::If(integrator) => {
            out.insert(
                "r".to_string(),
                tensor_f64_scalar_json(name, &integrator.r)?,
            );
            out.insert(
                "v_threshold".to_string(),
                tensor_f64_scalar_json(name, &integrator.v_threshold)?,
            );
        }
        other => return Err(AdapterError::unsupported(name, other.type_name())),
    }
    if let Some(size) = metadata.get(META_SIZE).and_then(metadata_i64) {
        out.insert("size".to_string(), json!(size));
    }
    if !matches!(node, NirNode::Input(_))
        && let Some(shape) = metadata_shape(metadata)
    {
        out.insert("shape".to_string(), json!(shape));
    }
    Ok(Value::Object(out))
}

fn node_metadata_ref(node: &NirNode) -> &MetadataMap {
    match node {
        NirNode::Input(n) => &n.metadata,
        NirNode::Output(n) => &n.metadata,
        NirNode::Affine(n) => &n.metadata,
        NirNode::Linear(n) => &n.metadata,
        NirNode::Scale(n) => &n.metadata,
        NirNode::Conv1d(n) => &n.metadata,
        NirNode::Conv2d(n) => &n.metadata,
        NirNode::CubaLi(n) => &n.metadata,
        NirNode::CubaLif(n) => &n.metadata,
        NirNode::Delay(n) => &n.metadata,
        NirNode::Flatten(n) => &n.metadata,
        NirNode::I(n) => &n.metadata,
        NirNode::If(n) => &n.metadata,
        NirNode::Li(n) => &n.metadata,
        NirNode::Lif(n) => &n.metadata,
        NirNode::SumPool2d(n) => &n.metadata,
        NirNode::AvgPool2d(n) => &n.metadata,
        NirNode::Threshold(n) => &n.metadata,
        _ => unreachable!("NirNode variants without metadata are not constructible here"),
    }
}

fn metadata_i64(value: &MetadataValue) -> Option<i64> {
    match value {
        MetadataValue::I64(number) => Some(*number),
        MetadataValue::F64(number) if number.fract() == 0.0 => Some(*number as i64),
        _ => None,
    }
}

fn metadata_f64(value: &MetadataValue) -> Option<f64> {
    match value {
        MetadataValue::F64(number) => Some(*number),
        MetadataValue::I64(number) => Some(*number as f64),
        _ => None,
    }
}

fn metadata_shape(metadata: &MetadataMap) -> Option<Vec<usize>> {
    let dims = match metadata.get(META_SHAPE)? {
        MetadataValue::Tensor(tensor) => match tensor.data() {
            TensorData::I64(values) => values.iter().map(|v| *v as usize).collect(),
            _ => return None,
        },
        _ => return None,
    };
    Some(dims)
}

// ── Field decoders ────────────────────────────────────────────────────

fn shape_of(name: &str, node: &Value) -> Result<Vec<usize>, AdapterError> {
    let shape = node
        .get("shape")
        .and_then(Value::as_array)
        .ok_or_else(|| AdapterError::graph(format!("node {name:?} needs an integer shape")))?;
    shape
        .iter()
        .map(|value| {
            value.as_u64().map(|dim| dim as usize).ok_or_else(|| {
                AdapterError::graph(format!("node {name:?} has a non-integer shape"))
            })
        })
        .collect()
}

fn declared_size(name: &str, node: &Value) -> Result<usize, AdapterError> {
    if let Some(size) = node.get("size").and_then(Value::as_u64) {
        return Ok(size as usize);
    }
    if let Some(shape) = node.get("shape").and_then(Value::as_array)
        && let Some(first) = shape.first().and_then(Value::as_u64)
    {
        return Ok(first as usize);
    }
    Err(AdapterError::graph(format!(
        "node {name:?} must declare an integer size >= 1"
    )))
}

fn integer_field(name: &str, node: &Value, field: &str) -> Result<i64, AdapterError> {
    node.get(field)
        .and_then(Value::as_i64)
        .ok_or_else(|| AdapterError::graph(format!("node {name:?} needs integer {field:?}")))
}

fn float_field(name: &str, node: &Value, field: &str) -> Result<f64, AdapterError> {
    node.get(field)
        .and_then(Value::as_f64)
        .ok_or_else(|| AdapterError::graph(format!("node {name:?} needs numeric {field:?}")))
}

fn scalar_tensor(name: &str, node: &Value, field: &str) -> Result<Tensor, AdapterError> {
    Ok(Tensor::scalar_f64(float_field(name, node, field)?))
}

fn scalar_tensor_default(
    name: &str,
    node: &Value,
    field: &str,
    default: f64,
) -> Result<Tensor, AdapterError> {
    match node.get(field) {
        Some(value) => Ok(Tensor::scalar_f64(value.as_f64().ok_or_else(|| {
            AdapterError::graph(format!("node {name:?} needs numeric {field:?}"))
        })?)),
        None => Ok(Tensor::scalar_f64(default)),
    }
}

fn vector_tensor(name: &str, node: &Value, field: &str) -> Result<Tensor, AdapterError> {
    let values = node
        .get(field)
        .and_then(Value::as_array)
        .ok_or_else(|| AdapterError::graph(format!("node {name:?} needs vector {field:?}")))?;
    let mut data = Vec::with_capacity(values.len());
    for value in values {
        data.push(value.as_f64().ok_or_else(|| {
            AdapterError::graph(format!("node {name:?} has non-numeric {field:?}"))
        })?);
    }
    Tensor::from_f64([data.len()], data)
        .map_err(|err| AdapterError::graph(format!("node {name:?}: {err}")))
}

fn matrix_tensor(name: &str, node: &Value, field: &str) -> Result<Tensor, AdapterError> {
    let rows = node
        .get(field)
        .and_then(Value::as_array)
        .ok_or_else(|| AdapterError::graph(format!("node {name:?} needs matrix {field:?}")))?;
    let mut data = Vec::new();
    let mut columns = None;
    for row in rows {
        let row = row.as_array().ok_or_else(|| {
            AdapterError::graph(format!("node {name:?}: {field} rows must be arrays"))
        })?;
        if let Some(width) = columns {
            if width != row.len() {
                return Err(AdapterError::graph(format!(
                    "node {name:?}: {field} rows must share one width"
                )));
            }
        } else {
            columns = Some(row.len());
        }
        for value in row {
            data.push(value.as_f64().ok_or_else(|| {
                AdapterError::graph(format!("node {name:?} has non-numeric {field:?}"))
            })?);
        }
    }
    let columns = columns.unwrap_or(0);
    Tensor::from_f64([rows.len(), columns], data)
        .map_err(|err| AdapterError::graph(format!("node {name:?}: {err}")))
}

// ── Tensor decoders for the reparse direction ─────────────────────────

fn tensor_f64_vec(tensor: &Tensor) -> Result<Vec<f64>, AdapterError> {
    match tensor.data() {
        TensorData::F64(values) => Ok(values.clone()),
        TensorData::F32(values) => Ok(values.iter().map(|v| *v as f64).collect()),
        TensorData::I64(values) => Ok(values.iter().map(|v| *v as f64).collect()),
        TensorData::Bool(_) => Err(AdapterError::graph("tensor is not numeric")),
    }
}

fn tensor_f64_vec_json(name: &str, tensor: &Tensor) -> Result<Value, AdapterError> {
    let values = tensor_f64_vec(tensor)
        .map_err(|err| AdapterError::graph(format!("node {name:?}: {}", err.detail)))?;
    Ok(json!(values))
}

fn tensor_f64_matrix_json(name: &str, tensor: &Tensor) -> Result<Value, AdapterError> {
    let values = tensor_f64_vec(tensor)
        .map_err(|err| AdapterError::graph(format!("node {name:?}: {}", err.detail)))?;
    let shape = tensor.shape();
    if shape.len() != 2 || shape[0] * shape[1] != values.len() {
        return Err(AdapterError::graph(format!(
            "node {name:?}: weight tensor must be 2-D"
        )));
    }
    let rows: Vec<Value> = values.chunks(shape[1]).map(|row| json!(row)).collect();
    Ok(json!(rows))
}

fn tensor_f64_scalar_json(name: &str, tensor: &Tensor) -> Result<Value, AdapterError> {
    let values = tensor_f64_vec(tensor)
        .map_err(|err| AdapterError::graph(format!("node {name:?}: {}", err.detail)))?;
    values
        .first()
        .map(|value| json!(value))
        .ok_or_else(|| AdapterError::graph(format!("node {name:?}: scalar field is empty")))
}

fn tensor_i64_scalar_json(name: &str, tensor: &Tensor) -> Result<Value, AdapterError> {
    match tensor.data() {
        TensorData::I64(values) => values
            .first()
            .map(|value| json!(value))
            .ok_or_else(|| AdapterError::graph(format!("node {name:?}: scalar field is empty"))),
        _ => Err(AdapterError::graph(format!(
            "node {name:?}: delay field is not an integer"
        ))),
    }
}

fn tensor_f64_scalar(tensor: &Tensor, name: &str, field: &str) -> Result<f64, AdapterError> {
    tensor_f64_vec(tensor)
        .map_err(|err| AdapterError::graph(format!("node {name:?}: {}", err.detail)))?
        .first()
        .copied()
        .ok_or_else(|| AdapterError::graph(format!("node {name:?}: {field} must be a scalar")))
}

// ── Execution: mirrors pipelines/nir_equivalence_interpreter.py ───────
// Conventions: reset=subtract, delay_unit=steps, cycle_break_order=insertion.

fn execute(graph: &NirGraph, stimulus: &Value) -> Result<Value, AdapterError> {
    let steps = stimulus
        .get("steps")
        .and_then(Value::as_u64)
        .ok_or_else(|| AdapterError::graph("stimulus.steps must be a non-negative integer"))?;
    let events = stimulus
        .get("events")
        .and_then(Value::as_array)
        .ok_or_else(|| AdapterError::graph("stimulus.events must be an array"))?;
    let dt_s = graph
        .metadata
        .get(META_DT_S)
        .and_then(metadata_f64)
        .unwrap_or(1e-3);
    let sizes = declared_sizes(graph)?;
    let input_names: Vec<&String> = graph
        .nodes
        .iter()
        .filter(|(_, node)| matches!(node, NirNode::Input(_)))
        .map(|(name, _)| name)
        .collect();
    let output_names: Vec<&String> = graph
        .nodes
        .iter()
        .filter(|(_, node)| matches!(node, NirNode::Output(_)))
        .map(|(name, _)| name)
        .collect();
    if input_names.is_empty() || output_names.is_empty() {
        return Err(AdapterError::graph(
            "graph needs at least one Input and one Output node",
        ));
    }
    let output_node = output_names[0].clone();
    let (order, recurrent) = evaluation_order(graph);
    let incoming = incoming_edges(graph, &recurrent);
    let mut previous: HashMap<String, Vec<f64>> = graph
        .nodes
        .keys()
        .map(|name| (name.clone(), vec![0.0; sizes[name]]))
        .collect();
    let mut membrane = initial_membrane(graph, &sizes);
    let mut delay_buffers = initial_delay_buffers(graph, &sizes);
    let mut outputs: Vec<Vec<f64>> = Vec::with_capacity(steps as usize);
    for step in 0..steps as usize {
        let mut current: HashMap<String, Vec<f64>> = HashMap::new();
        for name in &order {
            let node = &graph.nodes[name];
            let drive = node_drive(name, node, &incoming, &previous, &current, events, step)?;
            current.insert(
                name.clone(),
                step_node(name, node, &drive, &mut membrane, &mut delay_buffers, dt_s)?,
            );
        }
        previous = current;
        outputs.push(previous[&output_node].clone());
    }
    Ok(json!({
        "steps": steps,
        "output_node": output_node,
        "outputs": outputs,
        "membrane": membrane,
        "evaluation_order": order,
        "recurrent_edges": recurrent
            .iter()
            .map(|(s, t)| json!([s, t]))
            .collect::<Vec<Value>>(),
    }))
}

fn declared_sizes(graph: &NirGraph) -> Result<HashMap<String, usize>, AdapterError> {
    let mut sizes = HashMap::new();
    for (name, node) in &graph.nodes {
        let metadata = node_metadata_ref(node);
        let size = metadata
            .get(META_SIZE)
            .and_then(metadata_i64)
            .map(|size| size as usize)
            .or_else(|| match node {
                NirNode::Input(input) => input.shape.first().copied(),
                NirNode::Output(output) => output.shape.first().copied(),
                _ => None,
            });
        match size {
            Some(size) if size >= 1 => {
                sizes.insert(name.clone(), size);
            }
            _ => {
                return Err(AdapterError::graph(format!(
                    "node {name:?} must declare an integer size >= 1"
                )));
            }
        }
    }
    Ok(sizes)
}

fn initial_membrane(graph: &NirGraph, sizes: &HashMap<String, usize>) -> HashMap<String, Vec<f64>> {
    let mut membrane = HashMap::new();
    for (name, node) in &graph.nodes {
        if matches!(node, NirNode::Lif(_) | NirNode::Li(_) | NirNode::If(_)) {
            membrane.insert(name.clone(), vec![0.0; sizes[name]]);
        }
    }
    membrane
}

fn initial_delay_buffers(
    graph: &NirGraph,
    sizes: &HashMap<String, usize>,
) -> HashMap<String, Vec<Vec<f64>>> {
    let mut buffers = HashMap::new();
    for (name, node) in &graph.nodes {
        if let NirNode::Delay(delay) = node {
            let depth = match delay.delay.data() {
                TensorData::I64(values) => values.first().copied().unwrap_or(0).max(0) as usize,
                _ => 0,
            };
            buffers.insert(name.clone(), vec![vec![0.0; sizes[name]]; depth]);
        }
    }
    buffers
}

/// Depth-first traversal in insertion order, mirroring
/// `evaluation_order(graph, "insertion")` in `nir_equivalence_graph.py`.
fn evaluation_order(graph: &NirGraph) -> (Vec<String>, HashSet<(String, String)>) {
    let names: Vec<String> = graph.nodes.keys().cloned().collect();
    let rank: HashMap<&str, usize> = names
        .iter()
        .enumerate()
        .map(|(index, name)| (name.as_str(), index))
        .collect();
    let mut successors: HashMap<&str, Vec<&str>> = HashMap::new();
    for (source, target) in &graph.edges {
        successors
            .entry(source.as_str())
            .or_default()
            .push(target.as_str());
    }
    for list in successors.values_mut() {
        list.sort_by_key(|target| rank[*target]);
    }
    let mut state: HashMap<&str, u8> = names.iter().map(|n| (n.as_str(), 0)).collect();
    let mut order = Vec::new();
    let mut recurrent = HashSet::new();
    for name in &names {
        if state[name.as_str()] == 0 {
            visit(name, &successors, &mut state, &mut order, &mut recurrent);
        }
    }
    order.reverse();
    (order, recurrent)
}

fn visit<'a>(
    node: &'a str,
    successors: &HashMap<&'a str, Vec<&'a str>>,
    state: &mut HashMap<&'a str, u8>,
    order: &mut Vec<String>,
    recurrent: &mut HashSet<(String, String)>,
) {
    state.insert(node, 1);
    if let Some(list) = successors.get(node) {
        for &next in list {
            match state[next] {
                0 => visit(next, successors, state, order, recurrent),
                1 => {
                    recurrent.insert((node.to_string(), next.to_string()));
                }
                _ => {}
            }
        }
    }
    state.insert(node, 2);
    order.push(node.to_string());
}

fn incoming_edges(
    graph: &NirGraph,
    recurrent: &HashSet<(String, String)>,
) -> HashMap<String, Vec<(String, bool)>> {
    let mut incoming: HashMap<String, Vec<(String, bool)>> = HashMap::new();
    for (source, target) in &graph.edges {
        incoming.entry(target.clone()).or_default().push((
            source.clone(),
            recurrent.contains(&(source.clone(), target.clone())),
        ));
    }
    incoming
}

fn node_drive(
    name: &str,
    node: &NirNode,
    incoming: &HashMap<String, Vec<(String, bool)>>,
    previous: &HashMap<String, Vec<f64>>,
    current: &HashMap<String, Vec<f64>>,
    events: &[Value],
    step: usize,
) -> Result<Vec<f64>, AdapterError> {
    if matches!(node, NirNode::Input(_)) {
        let row = events
            .get(step)
            .and_then(Value::as_array)
            .ok_or_else(|| AdapterError::graph("stimulus.events rows must be arrays"))?;
        return row
            .iter()
            .map(|value| {
                value
                    .as_f64()
                    .ok_or_else(|| AdapterError::graph("stimulus events must be numeric"))
            })
            .collect();
    }
    let sources = incoming
        .get(name)
        .ok_or_else(|| AdapterError::graph(format!("node {name:?} has no inputs")))?;
    let mut parts: Vec<&Vec<f64>> = Vec::with_capacity(sources.len());
    for (source, is_recurrent) in sources {
        let values = if *is_recurrent {
            previous.get(source)
        } else {
            current.get(source)
        }
        .ok_or_else(|| {
            AdapterError::graph(format!("edge references unevaluated node {source:?}"))
        })?;
        parts.push(values);
    }
    sum_drive_parts(name, &parts)
}

fn sum_drive_parts(name: &str, parts: &[&Vec<f64>]) -> Result<Vec<f64>, AdapterError> {
    let width = parts[0].len();
    if parts.iter().any(|part| part.len() != width) {
        return Err(AdapterError::graph(format!(
            "node {name:?} sums inputs of different widths"
        )));
    }
    Ok((0..width)
        .map(|index| parts.iter().map(|part| part[index]).sum())
        .collect())
}

fn step_node(
    name: &str,
    node: &NirNode,
    drive: &[f64],
    membrane: &mut HashMap<String, Vec<f64>>,
    delay_buffers: &mut HashMap<String, Vec<Vec<f64>>>,
    dt_s: f64,
) -> Result<Vec<f64>, AdapterError> {
    match node {
        NirNode::Input(_) | NirNode::Output(_) => Ok(drive.to_vec()),
        NirNode::Affine(affine) => step_affine(name, &affine.weight, Some(&affine.bias), drive),
        NirNode::Linear(linear) => step_affine(name, &linear.weight, None, drive),
        NirNode::Threshold(threshold) => {
            let threshold = tensor_f64_scalar(&threshold.threshold, name, "threshold")?;
            Ok(drive
                .iter()
                .map(|value| if *value >= threshold { 1.0 } else { 0.0 })
                .collect())
        }
        NirNode::Delay(_) => {
            let buffer = delay_buffers.get_mut(name).ok_or_else(|| {
                AdapterError::graph(format!("node {name:?} lost its delay buffer"))
            })?;
            if buffer.is_empty() {
                return Ok(drive.to_vec());
            }
            let out = buffer.remove(0);
            buffer.push(drive.to_vec());
            Ok(out)
        }
        NirNode::Lif(lif) => {
            let v = membrane.get_mut(name).ok_or_else(|| {
                AdapterError::graph(format!("node {name:?} lost its membrane state"))
            })?;
            integrate_membrane(
                name,
                v,
                drive,
                dt_s,
                tensor_f64_scalar(&lif.tau, name, "tau")?,
                tensor_f64_scalar(&lif.r, name, "r")?,
                tensor_f64_scalar(&lif.v_leak, name, "v_leak")?,
            )?;
            Ok(emit_spikes(
                v,
                tensor_f64_scalar(&lif.v_threshold, name, "v_threshold")?,
            ))
        }
        NirNode::If(integrator) => {
            let v = membrane.get_mut(name).ok_or_else(|| {
                AdapterError::graph(format!("node {name:?} lost its membrane state"))
            })?;
            let r = tensor_f64_scalar(&integrator.r, name, "r")?;
            if drive.len() != v.len() {
                return Err(AdapterError::graph(format!(
                    "node {name:?}: drive width does not match its size"
                )));
            }
            for index in 0..v.len() {
                v[index] += r * drive[index];
            }
            Ok(emit_spikes(
                v,
                tensor_f64_scalar(&integrator.v_threshold, name, "v_threshold")?,
            ))
        }
        NirNode::Li(li) => {
            let v = membrane.get_mut(name).ok_or_else(|| {
                AdapterError::graph(format!("node {name:?} lost its membrane state"))
            })?;
            integrate_membrane(
                name,
                v,
                drive,
                dt_s,
                tensor_f64_scalar(&li.tau, name, "tau")?,
                tensor_f64_scalar(&li.r, name, "r")?,
                tensor_f64_scalar(&li.v_leak, name, "v_leak")?,
            )?;
            Ok(v.clone())
        }
        other => Err(AdapterError::unsupported(name, other.type_name())),
    }
}

fn integrate_membrane(
    name: &str,
    membrane: &mut [f64],
    drive: &[f64],
    dt_s: f64,
    tau: f64,
    r: f64,
    v_leak: f64,
) -> Result<(), AdapterError> {
    if tau <= 0.0 {
        return Err(AdapterError::graph(format!(
            "node {name:?}: tau must be > 0"
        )));
    }
    if drive.len() != membrane.len() {
        return Err(AdapterError::graph(format!(
            "node {name:?}: drive width does not match its size"
        )));
    }
    let factor = dt_s / tau;
    for index in 0..membrane.len() {
        membrane[index] += factor * ((v_leak - membrane[index]) + r * drive[index]);
    }
    Ok(())
}

/// Threshold the membrane and apply the `subtract` reset convention.
fn emit_spikes(membrane: &mut [f64], threshold: f64) -> Vec<f64> {
    let mut spikes = Vec::with_capacity(membrane.len());
    for value in membrane.iter_mut() {
        if *value >= threshold {
            spikes.push(1.0);
            *value -= threshold;
        } else {
            spikes.push(0.0);
        }
    }
    spikes
}

fn step_affine(
    name: &str,
    weight: &Tensor,
    bias: Option<&Tensor>,
    drive: &[f64],
) -> Result<Vec<f64>, AdapterError> {
    let weights = tensor_f64_vec(weight)
        .map_err(|err| AdapterError::graph(format!("node {name:?}: {}", err.detail)))?;
    let shape = weight.shape();
    if shape.len() != 2 || shape[0] * shape[1] != weights.len() {
        return Err(AdapterError::graph(format!(
            "node {name:?}: weight must be a 2-D tensor"
        )));
    }
    let (rows, columns) = (shape[0], shape[1]);
    if columns != drive.len() {
        return Err(AdapterError::graph(format!(
            "node {name:?}: weight columns do not match its input"
        )));
    }
    let bias_values: Vec<f64> = match bias {
        Some(tensor) => tensor_f64_vec(tensor)
            .map_err(|err| AdapterError::graph(format!("node {name:?}: {}", err.detail)))?,
        None => vec![0.0; rows],
    };
    let mut output = Vec::with_capacity(rows);
    for (index, row) in weights.chunks(columns).enumerate() {
        let sum: f64 = row.iter().zip(drive.iter()).map(|(w, d)| w * d).sum();
        output.push(sum + bias_values.get(index).copied().unwrap_or(0.0));
    }
    Ok(output)
}
