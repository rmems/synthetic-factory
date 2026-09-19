// SPDX-License-Identifier: Apache-2.0 OR MIT
//! Decode half of the codec: crate wire types back into this family's
//! in-repo record graph (the shape `nir_equivalence_graph.py` produces).
//! Encode lives in `codec.rs`.

use nir_rs::graph::NirGraph;
use nir_rs::nodes::NirNode;
use nir_rs::types::{Tensor, TensorData};
use serde_json::{Value, json};

use crate::AdapterError;
use crate::meta::{
    META_DT_S, META_SIZE, metadata_f64, metadata_i64, metadata_shape, node_metadata_ref,
};

// ── nir-rs crate types → in-repo graph form ───────────────────────────

pub(crate) fn nir_to_in_repo(graph: &NirGraph) -> Result<Value, AdapterError> {
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

/// Per-type field writers, selected by the node's `type_name()`. Symmetric
/// with `NODE_BUILDERS`: the dispatch never hardcodes a variant.
type FieldWriter =
    fn(&str, &NirNode, &mut serde_json::Map<String, Value>) -> Result<(), AdapterError>;

const FIELD_WRITERS: &[(&str, FieldWriter)] = &[
    ("Affine", affine_fields),
    ("Delay", delay_fields),
    ("IF", if_fields),
    ("Input", input_fields),
    ("LI", li_fields),
    ("LIF", lif_fields),
    ("Linear", linear_fields),
    ("Output", output_fields),
    ("Threshold", threshold_fields),
];

fn node_to_in_repo(name: &str, node: &NirNode) -> Result<Value, AdapterError> {
    let metadata = node_metadata_ref(node);
    let mut out = serde_json::Map::new();
    out.insert("type".to_string(), json!(node.type_name()));
    let writer = FIELD_WRITERS
        .iter()
        .find(|(kind, _)| *kind == node.type_name())
        .map(|(_, writer)| *writer)
        .ok_or_else(|| AdapterError::unsupported(name, node.type_name()))?;
    writer(name, node, &mut out)?;
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

fn input_fields(
    _name: &str,
    node: &NirNode,
    out: &mut serde_json::Map<String, Value>,
) -> Result<(), AdapterError> {
    if let NirNode::Input(input) = node {
        out.insert("shape".to_string(), json!(input.shape));
    }
    Ok(())
}

fn output_fields(
    _name: &str,
    node: &NirNode,
    out: &mut serde_json::Map<String, Value>,
) -> Result<(), AdapterError> {
    if let NirNode::Output(output) = node
        && metadata_shape(node_metadata_ref(node)).is_some()
    {
        out.insert("shape".to_string(), json!(output.shape));
    }
    Ok(())
}

fn affine_fields(
    name: &str,
    node: &NirNode,
    out: &mut serde_json::Map<String, Value>,
) -> Result<(), AdapterError> {
    if let NirNode::Affine(affine) = node {
        out.insert(
            "weight".to_string(),
            tensor_f64_matrix_json(name, &affine.weight)?,
        );
        out.insert("bias".to_string(), tensor_f64_vec_json(name, &affine.bias)?);
    }
    Ok(())
}

fn linear_fields(
    name: &str,
    node: &NirNode,
    out: &mut serde_json::Map<String, Value>,
) -> Result<(), AdapterError> {
    if let NirNode::Linear(linear) = node {
        out.insert(
            "weight".to_string(),
            tensor_f64_matrix_json(name, &linear.weight)?,
        );
    }
    Ok(())
}

fn threshold_fields(
    name: &str,
    node: &NirNode,
    out: &mut serde_json::Map<String, Value>,
) -> Result<(), AdapterError> {
    if let NirNode::Threshold(threshold) = node {
        out.insert(
            "threshold".to_string(),
            tensor_f64_scalar_json(name, &threshold.threshold)?,
        );
    }
    Ok(())
}

fn delay_fields(
    name: &str,
    node: &NirNode,
    out: &mut serde_json::Map<String, Value>,
) -> Result<(), AdapterError> {
    if let NirNode::Delay(delay) = node {
        out.insert(
            "delay".to_string(),
            tensor_i64_scalar_json(name, &delay.delay)?,
        );
    }
    Ok(())
}

fn lif_fields(
    name: &str,
    node: &NirNode,
    out: &mut serde_json::Map<String, Value>,
) -> Result<(), AdapterError> {
    if let NirNode::Lif(lif) = node {
        for (key, tensor) in [
            ("tau", &lif.tau),
            ("r", &lif.r),
            ("v_leak", &lif.v_leak),
            ("v_threshold", &lif.v_threshold),
        ] {
            out.insert(key.to_string(), tensor_f64_scalar_json(name, tensor)?);
        }
    }
    Ok(())
}

fn li_fields(
    name: &str,
    node: &NirNode,
    out: &mut serde_json::Map<String, Value>,
) -> Result<(), AdapterError> {
    if let NirNode::Li(li) = node {
        for (key, tensor) in [("tau", &li.tau), ("r", &li.r), ("v_leak", &li.v_leak)] {
            out.insert(key.to_string(), tensor_f64_scalar_json(name, tensor)?);
        }
    }
    Ok(())
}

fn if_fields(
    name: &str,
    node: &NirNode,
    out: &mut serde_json::Map<String, Value>,
) -> Result<(), AdapterError> {
    if let NirNode::If(integrator) = node {
        out.insert(
            "r".to_string(),
            tensor_f64_scalar_json(name, &integrator.r)?,
        );
        out.insert(
            "v_threshold".to_string(),
            tensor_f64_scalar_json(name, &integrator.v_threshold)?,
        );
    }
    Ok(())
}
// ── Tensor decoders for the reparse direction ─────────────────────────

pub(crate) fn tensor_f64_vec(tensor: &Tensor) -> Result<Vec<f64>, AdapterError> {
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

pub(crate) fn tensor_f64_scalar(
    tensor: &Tensor,
    name: &str,
    field: &str,
) -> Result<f64, AdapterError> {
    tensor_f64_vec(tensor)
        .map_err(|err| AdapterError::graph(format!("node {name:?}: {}", err.detail)))?
        .first()
        .copied()
        .ok_or_else(|| AdapterError::graph(format!("node {name:?}: {field} must be a scalar")))
}
