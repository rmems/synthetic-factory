// SPDX-License-Identifier: Apache-2.0 OR MIT
//! Execution on the crate's types. Mirrors
//! `pipelines/nir_equivalence_interpreter.py` under this family's declared
//! conventions: reset=subtract, delay_unit=steps, cycle_break_order=insertion.

use std::collections::{HashMap, HashSet};

use nir_rs::graph::NirGraph;
use nir_rs::nodes::NirNode;
use nir_rs::types::{Tensor, TensorData};
use serde_json::{Value, json};

use crate::AdapterError;
use crate::decode::{tensor_f64_scalar, tensor_f64_vec};
use crate::meta::{META_DT_S, META_SIZE, metadata_f64, metadata_i64, node_metadata_ref};

pub(crate) fn execute(graph: &NirGraph, stimulus: &Value) -> Result<Value, AdapterError> {
    let (steps, events) = stimulus_terms(stimulus)?;
    let dt_s = graph
        .metadata
        .get(META_DT_S)
        .and_then(metadata_f64)
        .unwrap_or(1e-3);
    let sizes = declared_sizes(graph)?;
    let output_node = output_node_of(graph)?;
    let (order, recurrent) = evaluation_order(graph);
    let mut simulation = Simulation::new(graph, &sizes, &recurrent, events, dt_s);
    let mut outputs: Vec<Vec<f64>> = Vec::with_capacity(steps as usize);
    for step in 0..steps as usize {
        simulation.step(&order, step)?;
        outputs.push(simulation.previous[&output_node].clone());
    }
    Ok(json!({
        "steps": steps,
        "output_node": output_node,
        "outputs": outputs,
        "membrane": simulation.membrane,
        "evaluation_order": order,
        "recurrent_edges": recurrent
            .iter()
            .map(|(s, t)| json!([s, t]))
            .collect::<Vec<Value>>(),
    }))
}

fn stimulus_terms(stimulus: &Value) -> Result<(u64, &[Value]), AdapterError> {
    let steps = stimulus
        .get("steps")
        .and_then(Value::as_u64)
        .ok_or_else(|| AdapterError::graph("stimulus.steps must be a non-negative integer"))?;
    let events = stimulus
        .get("events")
        .and_then(Value::as_array)
        .ok_or_else(|| AdapterError::graph("stimulus.events must be an array"))?;
    Ok((steps, events))
}

fn output_node_of(graph: &NirGraph) -> Result<String, AdapterError> {
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
    Ok(output_names[0].clone())
}

fn declared_sizes(graph: &NirGraph) -> Result<HashMap<String, usize>, AdapterError> {
    let mut sizes = HashMap::new();
    for (name, node) in &graph.nodes {
        let size = node_size(name, node)?;
        sizes.insert(name.clone(), size);
    }
    Ok(sizes)
}

fn node_size(name: &str, node: &NirNode) -> Result<usize, AdapterError> {
    let size = node_metadata_ref(node)
        .get(META_SIZE)
        .and_then(metadata_i64)
        .map(|size| size as usize)
        .or_else(|| match node {
            NirNode::Input(input) => input.shape.first().copied(),
            NirNode::Output(output) => output.shape.first().copied(),
            _ => None,
        });
    match size {
        Some(size) if size >= 1 => Ok(size),
        _ => Err(AdapterError::graph(format!(
            "node {name:?} must declare an integer size >= 1"
        ))),
    }
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

/// Neuron dynamics shared by the LIF/LI decay-integrate kinds.
struct NeuronParams {
    tau: f64,
    r: f64,
    v_leak: f64,
}

impl NeuronParams {
    fn integrate(
        &self,
        name: &str,
        membrane: &mut [f64],
        drive: &[f64],
        dt_s: f64,
    ) -> Result<(), AdapterError> {
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

/// One step of a simulation: everything mutable the steppers touch, plus the
/// stimulus and timestep they read.
struct Simulation<'a> {
    graph: &'a NirGraph,
    incoming: HashMap<String, Vec<(String, bool)>>,
    previous: HashMap<String, Vec<f64>>,
    membrane: HashMap<String, Vec<f64>>,
    delay_buffers: HashMap<String, Vec<Vec<f64>>>,
    events: &'a [Value],
    dt_s: f64,
}

impl<'a> Simulation<'a> {
    fn new(
        graph: &'a NirGraph,
        sizes: &HashMap<String, usize>,
        recurrent: &HashSet<(String, String)>,
        events: &'a [Value],
        dt_s: f64,
    ) -> Self {
        Self {
            graph,
            incoming: incoming_edges(graph, recurrent),
            previous: graph
                .nodes
                .keys()
                .map(|name| (name.clone(), vec![0.0; sizes[name]]))
                .collect(),
            membrane: initial_membrane(graph, sizes),
            delay_buffers: initial_delay_buffers(graph, sizes),
            events,
            dt_s,
        }
    }

    fn step(&mut self, order: &[String], step: usize) -> Result<(), AdapterError> {
        let mut current: HashMap<String, Vec<f64>> = HashMap::new();
        for name in order {
            let node = &self.graph.nodes[name];
            let drive = self.node_drive(name, node, &current, step)?;
            current.insert(name.clone(), self.step_node(name, node, &drive)?);
        }
        self.previous = current;
        Ok(())
    }

    fn node_drive(
        &self,
        name: &str,
        node: &NirNode,
        current: &HashMap<String, Vec<f64>>,
        step: usize,
    ) -> Result<Vec<f64>, AdapterError> {
        if matches!(node, NirNode::Input(_)) {
            return input_drive(self.events, step);
        }
        let sources = self
            .incoming
            .get(name)
            .ok_or_else(|| AdapterError::graph(format!("node {name:?} has no inputs")))?;
        let mut parts: Vec<&Vec<f64>> = Vec::with_capacity(sources.len());
        for (source, is_recurrent) in sources {
            let values = if *is_recurrent {
                self.previous.get(source)
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

    fn step_node(
        &mut self,
        name: &str,
        node: &NirNode,
        drive: &[f64],
    ) -> Result<Vec<f64>, AdapterError> {
        match node {
            NirNode::Input(_) | NirNode::Output(_) => Ok(drive.to_vec()),
            NirNode::Affine(affine) => step_affine(name, &affine.weight, Some(&affine.bias), drive),
            NirNode::Linear(linear) => step_affine(name, &linear.weight, None, drive),
            NirNode::Threshold(threshold) => step_threshold(name, threshold, drive),
            NirNode::Delay(_) => self.step_delay(name, drive),
            NirNode::Lif(lif) => self.step_lif(name, lif, drive),
            NirNode::If(integrator) => self.step_if(name, integrator, drive),
            NirNode::Li(li) => self.step_li(name, li, drive),
            other => Err(AdapterError::unsupported(name, other.type_name())),
        }
    }

    fn membrane_of(&mut self, name: &str) -> Result<&mut Vec<f64>, AdapterError> {
        self.membrane
            .get_mut(name)
            .ok_or_else(|| AdapterError::graph(format!("node {name:?} lost its membrane state")))
    }

    fn step_delay(&mut self, name: &str, drive: &[f64]) -> Result<Vec<f64>, AdapterError> {
        let buffer = self
            .delay_buffers
            .get_mut(name)
            .ok_or_else(|| AdapterError::graph(format!("node {name:?} lost its delay buffer")))?;
        if buffer.is_empty() {
            return Ok(drive.to_vec());
        }
        let out = buffer.remove(0);
        buffer.push(drive.to_vec());
        Ok(out)
    }

    fn step_lif(
        &mut self,
        name: &str,
        lif: &nir_rs::nodes::Lif,
        drive: &[f64],
    ) -> Result<Vec<f64>, AdapterError> {
        let params = neuron_params(name, &lif.tau, &lif.r, &lif.v_leak)?;
        let threshold = tensor_f64_scalar(&lif.v_threshold, name, "v_threshold")?;
        let dt_s = self.dt_s;
        let v = self.membrane_of(name)?;
        params.integrate(name, v, drive, dt_s)?;
        Ok(emit_spikes(v, threshold))
    }

    fn step_li(
        &mut self,
        name: &str,
        li: &nir_rs::nodes::Li,
        drive: &[f64],
    ) -> Result<Vec<f64>, AdapterError> {
        let params = neuron_params(name, &li.tau, &li.r, &li.v_leak)?;
        let dt_s = self.dt_s;
        let v = self.membrane_of(name)?;
        params.integrate(name, v, drive, dt_s)?;
        Ok(v.clone())
    }

    fn step_if(
        &mut self,
        name: &str,
        integrator: &nir_rs::nodes::If,
        drive: &[f64],
    ) -> Result<Vec<f64>, AdapterError> {
        let r = tensor_f64_scalar(&integrator.r, name, "r")?;
        let v = self
            .membrane
            .get_mut(name)
            .ok_or_else(|| AdapterError::graph(format!("node {name:?} lost its membrane state")))?;
        if drive.len() != v.len() {
            return Err(AdapterError::graph(format!(
                "node {name:?}: drive width does not match its size"
            )));
        }
        for index in 0..v.len() {
            v[index] += r * drive[index];
        }
        let threshold = tensor_f64_scalar(&integrator.v_threshold, name, "v_threshold")?;
        Ok(emit_spikes(v, threshold))
    }
}

fn neuron_params(
    name: &str,
    tau: &Tensor,
    r: &Tensor,
    v_leak: &Tensor,
) -> Result<NeuronParams, AdapterError> {
    Ok(NeuronParams {
        tau: tensor_f64_scalar(tau, name, "tau")?,
        r: tensor_f64_scalar(r, name, "r")?,
        v_leak: tensor_f64_scalar(v_leak, name, "v_leak")?,
    })
}

fn input_drive(events: &[Value], step: usize) -> Result<Vec<f64>, AdapterError> {
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

fn step_threshold(
    name: &str,
    threshold: &nir_rs::nodes::Threshold,
    drive: &[f64],
) -> Result<Vec<f64>, AdapterError> {
    let threshold = tensor_f64_scalar(&threshold.threshold, name, "threshold")?;
    Ok(drive
        .iter()
        .map(|value| if *value >= threshold { 1.0 } else { 0.0 })
        .collect())
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
