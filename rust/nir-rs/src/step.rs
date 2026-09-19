// SPDX-License-Identifier: Apache-2.0 OR MIT
//! One timestep of node dynamics for [`crate::exec`]: per-kind steppers, the
//! shared decay-integrate neuron parameters, drive summation, and the initial
//! per-node state a simulation starts from.

use std::collections::HashMap;

use nir_rs::graph::NirGraph;
use nir_rs::nodes::NirNode;
use nir_rs::types::{Tensor, TensorData};
use serde_json::Value;

use crate::AdapterError;
use crate::decode::{FieldLabel, tensor_f64_scalar, tensor_f64_vec};

/// Neuron dynamics shared by the LIF/LI decay-integrate kinds.
pub(crate) struct NeuronParams {
    tau: f64,
    r: f64,
    v_leak: f64,
}

/// The operands [`NeuronParams::integrate`] needs: which node is stepping
/// (for diagnostics), the membrane it owns, the summed drive, and the
/// timestep width.
pub(crate) struct Integration<'a> {
    pub(crate) name: &'a str,
    pub(crate) membrane: &'a mut [f64],
    pub(crate) drive: &'a [f64],
    pub(crate) dt_s: f64,
}

impl NeuronParams {
    pub(crate) fn integrate(&self, integ: &mut Integration<'_>) -> Result<(), AdapterError> {
        let name = integ.name;
        let membrane: &mut [f64] = integ.membrane;
        let drive = integ.drive;
        let dt_s = integ.dt_s;
        if self.tau <= 0.0 {
            return Err(AdapterError::graph(format!(
                "node {name:?}: tau must be > 0"
            )));
        }
        if drive.len() != membrane.len() {
            return Err(AdapterError::graph(format!(
                "node {name:?}: drive width does not match its size"
            )));
        }
        let factor = dt_s / self.tau;
        for index in 0..membrane.len() {
            membrane[index] += factor * ((self.v_leak - membrane[index]) + self.r * drive[index]);
        }
        Ok(())
    }
}

pub(crate) fn neuron_params(
    name: &str,
    tau: &Tensor,
    r: &Tensor,
    v_leak: &Tensor,
) -> Result<NeuronParams, AdapterError> {
    Ok(NeuronParams {
        tau: tensor_f64_scalar(
            tau,
            FieldLabel {
                node: name,
                field: "tau",
            },
        )?,
        r: tensor_f64_scalar(
            r,
            FieldLabel {
                node: name,
                field: "r",
            },
        )?,
        v_leak: tensor_f64_scalar(
            v_leak,
            FieldLabel {
                node: name,
                field: "v_leak",
            },
        )?,
    })
}

pub(crate) fn input_drive(events: &[Value], step: usize) -> Result<Vec<f64>, AdapterError> {
    let row = events
        .get(step)
        .and_then(Value::as_array)
        .ok_or_else(|| AdapterError::graph("stimulus.events rows must be arrays"))?;
    row.iter()
        .map(|value| {
            value
                .as_f64()
                .ok_or_else(|| AdapterError::graph("stimulus events must be numeric"))
        })
        .collect()
}

pub(crate) fn sum_drive_parts(name: &str, parts: &[&Vec<f64>]) -> Result<Vec<f64>, AdapterError> {
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

pub(crate) fn step_threshold(
    name: &str,
    threshold: &nir_rs::nodes::Threshold,
    drive: &[f64],
) -> Result<Vec<f64>, AdapterError> {
    let threshold = tensor_f64_scalar(
        &threshold.threshold,
        FieldLabel {
            node: name,
            field: "threshold",
        },
    )?;
    Ok(drive
        .iter()
        .map(|value| if *value >= threshold { 1.0 } else { 0.0 })
        .collect())
}

/// Threshold the membrane and apply the `subtract` reset convention.
pub(crate) fn emit_spikes(membrane: &mut [f64], threshold: f64) -> Vec<f64> {
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

pub(crate) fn step_affine(
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

pub(crate) fn initial_membrane(
    graph: &NirGraph,
    sizes: &HashMap<String, usize>,
) -> HashMap<String, Vec<f64>> {
    let mut membrane = HashMap::new();
    for (name, node) in &graph.nodes {
        if matches!(node, NirNode::Lif(_) | NirNode::Li(_) | NirNode::If(_)) {
            membrane.insert(name.clone(), vec![0.0; sizes[name]]);
        }
    }
    membrane
}

pub(crate) fn initial_delay_buffers(
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
