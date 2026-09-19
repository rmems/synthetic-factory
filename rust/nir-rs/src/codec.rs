// SPDX-License-Identifier: Apache-2.0 OR MIT
//! Translation between the in-repo NIR graph form and the `nir-rs` crate's
//! `NirGraph`/`NirNode`/`Tensor` values, in both directions.

use nir_rs::graph::NirGraph;
use nir_rs::nodes::{self, NirNode};
use nir_rs::types::{MetadataMap, MetadataValue, Tensor};
use serde_json::Value;

use crate::AdapterError;
use crate::meta::{META_DT_S, META_SHAPE, META_SIZE};

// ── In-repo graph form → nir-rs crate types ───────────────────────────

pub(crate) fn in_repo_to_nir(value: &Value) -> Result<NirGraph, AdapterError> {
    let object = value
        .as_object()
        .ok_or_else(|| AdapterError::graph("graph must be an object"))?;
    let mut graph = NirGraph::new();
    insert_nodes(&mut graph, object)?;
    add_edges(&mut graph, object)?;
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

fn insert_nodes(
    graph: &mut NirGraph,
    object: &serde_json::Map<String, Value>,
) -> Result<(), AdapterError> {
    let nodes = object
        .get("nodes")
        .and_then(Value::as_object)
        .ok_or_else(|| AdapterError::graph("graph.nodes must be an object"))?;
    for (name, node) in nodes {
        graph
            .insert_node(name.clone(), in_repo_node(name, node)?)
            .map_err(|err| AdapterError::graph(err.to_string()))?;
    }
    Ok(())
}

fn add_edges(
    graph: &mut NirGraph,
    object: &serde_json::Map<String, Value>,
) -> Result<(), AdapterError> {
    let edges = object
        .get("edges")
        .and_then(Value::as_array)
        .ok_or_else(|| AdapterError::graph("graph.edges must be an array"))?;
    for edge in edges {
        let (source, target) = edge_endpoints(edge)?;
        graph.add_edge(source.to_string(), target.to_string());
    }
    Ok(())
}

fn edge_endpoints(edge: &Value) -> Result<(&str, &str), AdapterError> {
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
    Ok((source, target))
}

/// The per-type builders the `type` dispatch table selects between. Splitting
/// them out keeps `in_repo_node` a pure dispatch.
type NodeBuilder = fn(&str, &Value, MetadataMap) -> Result<NirNode, AdapterError>;

const NODE_BUILDERS: &[(&str, NodeBuilder)] = &[
    ("Affine", affine_node),
    ("Delay", delay_node),
    ("IF", if_node),
    ("Input", input_node),
    ("LI", li_node),
    ("LIF", lif_node),
    ("Linear", linear_node),
    ("Output", output_node),
    ("Threshold", threshold_node),
];

fn in_repo_node(name: &str, node: &Value) -> Result<NirNode, AdapterError> {
    let node_type = node
        .get("type")
        .and_then(Value::as_str)
        .ok_or_else(|| AdapterError::graph(format!("node {name:?} must declare a type")))?;
    let builder = NODE_BUILDERS
        .iter()
        .find(|(kind, _)| *kind == node_type)
        .map(|(_, builder)| *builder)
        .ok_or_else(|| AdapterError::unsupported(name, node_type))?;
    builder(name, node, node_metadata(node))
}

fn input_node(name: &str, node: &Value, metadata: MetadataMap) -> Result<NirNode, AdapterError> {
    Ok(NirNode::Input(nodes::Input {
        shape: shape_of(name, node)?,
        metadata,
    }))
}

fn output_node(name: &str, node: &Value, metadata: MetadataMap) -> Result<NirNode, AdapterError> {
    let shape = match node.get("shape") {
        Some(_) => shape_of(name, node)?,
        None => vec![declared_size(name, node)?],
    };
    Ok(NirNode::Output(nodes::Output { shape, metadata }))
}

fn affine_node(name: &str, node: &Value, metadata: MetadataMap) -> Result<NirNode, AdapterError> {
    Ok(NirNode::Affine(nodes::Affine {
        weight: matrix_tensor(name, node, "weight")?,
        bias: vector_tensor(name, node, "bias")?,
        metadata,
    }))
}

fn linear_node(name: &str, node: &Value, metadata: MetadataMap) -> Result<NirNode, AdapterError> {
    Ok(NirNode::Linear(nodes::Linear {
        weight: matrix_tensor(name, node, "weight")?,
        metadata,
    }))
}

fn threshold_node(
    name: &str,
    node: &Value,
    metadata: MetadataMap,
) -> Result<NirNode, AdapterError> {
    Ok(NirNode::Threshold(nodes::Threshold {
        threshold: scalar_tensor(name, node, "threshold")?,
        metadata,
    }))
}

fn delay_node(name: &str, node: &Value, metadata: MetadataMap) -> Result<NirNode, AdapterError> {
    Ok(NirNode::Delay(nodes::Delay {
        delay: Tensor::scalar_i64(integer_field(name, node, "delay")?),
        metadata,
    }))
}

fn lif_node(name: &str, node: &Value, metadata: MetadataMap) -> Result<NirNode, AdapterError> {
    let (tau, r, v_leak) = decay_params(name, node)?;
    Ok(NirNode::Lif(nodes::Lif {
        tau,
        r,
        v_leak,
        v_threshold: scalar_tensor(name, node, "v_threshold")?,
        v_reset: None,
        metadata,
    }))
}

fn li_node(name: &str, node: &Value, metadata: MetadataMap) -> Result<NirNode, AdapterError> {
    let (tau, r, v_leak) = decay_params(name, node)?;
    Ok(NirNode::Li(nodes::Li {
        tau,
        r,
        v_leak,
        metadata,
    }))
}

/// The `(tau, r, v_leak)` parameter triple the decay-integrate kinds share.
fn decay_params(name: &str, node: &Value) -> Result<(Tensor, Tensor, Tensor), AdapterError> {
    Ok((
        scalar_tensor(name, node, "tau")?,
        scalar_tensor_default(name, node, "r", 1.0)?,
        scalar_tensor_default(name, node, "v_leak", 0.0)?,
    ))
}

fn if_node(name: &str, node: &Value, metadata: MetadataMap) -> Result<NirNode, AdapterError> {
    Ok(NirNode::If(nodes::If {
        r: scalar_tensor_default(name, node, "r", 1.0)?,
        v_threshold: scalar_tensor(name, node, "v_threshold")?,
        v_reset: None,
        metadata,
    }))
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
        Some(_) => scalar_tensor(name, node, field),
        None => Ok(Tensor::scalar_f64(default)),
    }
}

/// Decode a JSON number array cell by cell, refusing non-numeric entries.
fn numeric_cells(name: &str, field: &str, values: &[Value]) -> Result<Vec<f64>, AdapterError> {
    values
        .iter()
        .map(|value| {
            value.as_f64().ok_or_else(|| {
                AdapterError::graph(format!("node {name:?} has non-numeric {field:?}"))
            })
        })
        .collect()
}

fn vector_tensor(name: &str, node: &Value, field: &str) -> Result<Tensor, AdapterError> {
    let values = node
        .get(field)
        .and_then(Value::as_array)
        .ok_or_else(|| AdapterError::graph(format!("node {name:?} needs vector {field:?}")))?;
    let data = numeric_cells(name, field, values)?;
    Tensor::from_f64([data.len()], data)
        .map_err(|err| AdapterError::graph(format!("node {name:?}: {err}")))
}

fn matrix_tensor(name: &str, node: &Value, field: &str) -> Result<Tensor, AdapterError> {
    let (data, rows, columns) = matrix_rows(name, node, field)?;
    Tensor::from_f64([rows, columns], data)
        .map_err(|err| AdapterError::graph(format!("node {name:?}: {err}")))
}

fn matrix_rows(
    name: &str,
    node: &Value,
    field: &str,
) -> Result<(Vec<f64>, usize, usize), AdapterError> {
    let rows = node
        .get(field)
        .and_then(Value::as_array)
        .ok_or_else(|| AdapterError::graph(format!("node {name:?} needs matrix {field:?}")))?;
    let mut data = Vec::new();
    let mut columns = None;
    for row in rows {
        columns = Some(matrix_row(name, field, row, columns, &mut data)?);
    }
    Ok((data, rows.len(), columns.unwrap_or(0)))
}

fn matrix_row(
    name: &str,
    field: &str,
    row: &Value,
    columns: Option<usize>,
    data: &mut Vec<f64>,
) -> Result<usize, AdapterError> {
    let row = row.as_array().ok_or_else(|| {
        AdapterError::graph(format!("node {name:?}: {field} rows must be arrays"))
    })?;
    if let Some(width) = columns
        && width != row.len()
    {
        return Err(AdapterError::graph(format!(
            "node {name:?}: {field} rows must share one width"
        )));
    }
    data.extend(numeric_cells(name, field, row)?);
    Ok(row.len())
}
