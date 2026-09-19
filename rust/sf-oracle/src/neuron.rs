use crate::protocol::bound;
use neuromod::LifNeuron;
use serde::Deserialize;
use serde_json::{json, Value};
#[derive(Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Parameters {
    pub dt_ms: f64,
    pub threshold: f64,
    pub decay: f64,
    pub input_scale: f64,
}
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Intervention {
    parameter: String,
    factor: f64,
}
fn validate(p: &Parameters) -> Result<(), String> {
    bound(p.dt_ms, 0.01, 100.0, "dt_ms")?;
    bound(p.threshold, 0.0001, 100.0, "threshold")?;
    bound(p.decay, 0.0, 1.0, "decay")?;
    bound(p.input_scale, 0.0, 100.0, "input_scale")
}
pub fn run(signal: &[f64], p: &Parameters, i: &Intervention) -> Result<Value, String> {
    validate(p)?;
    bound(i.factor, f64::MIN_POSITIVE, 100.0, "factor")?;
    let mut after = p.clone();
    match i.parameter.as_str() {
        "threshold" => after.threshold *= i.factor,
        "decay" => after.decay *= i.factor,
        "input_scale" => after.input_scale *= i.factor,
        _ => return Err("unknown intervention parameter".into()),
    };
    validate(&after)?;
    let before = episode(signal, p);
    let after = episode(signal, &after);
    let delta = after["spike_count"].as_i64().unwrap() - before["spike_count"].as_i64().unwrap();
    Ok(json!({"profile":"neuromod-lif-v1","before":before,"after":after,"spike_count_delta":delta}))
}
fn episode(signal: &[f64], p: &Parameters) -> Value {
    let mut neuron = LifNeuron {
        threshold: p.threshold as f32,
        base_threshold: p.threshold as f32,
        decay_rate: p.decay as f32,
        ..Default::default()
    };
    let mut spikes = vec![];
    let mut trace = vec![];
    for (i, &x) in signal.iter().enumerate() {
        neuron.integrate((x * p.input_scale) as f32);
        trace.push(f64::from(neuron.membrane_potential));
        if neuron.check_fire().is_some() {
            spikes.push((i + 1) as f64 * p.dt_ms);
        }
    }
    json!({"spike_count":spikes.len(),"spikes":spikes,"v_trace":trace})
}
