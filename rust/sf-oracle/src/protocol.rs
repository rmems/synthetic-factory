use crate::{encoder, identity, neuron};
use serde::Deserialize;
use serde_json::{json, Value};
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Envelope {
    protocol: String,
    oracle: String,
    family: String,
    request: Request,
}
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Request {
    configuration: Configuration,
    data: Data,
}
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Configuration {
    profile: String,
    parameters: Box<serde_json::value::RawValue>,
    #[serde(deserialize_with = "Option::deserialize")]
    intervention: Option<neuron::Intervention>,
}
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Data {
    signal: Vec<f64>,
}
pub fn bound(v: f64, lo: f64, hi: f64, name: &str) -> Result<(), String> {
    if !v.is_finite() || v < lo || v > hi {
        Err(format!("invalid {name}"))
    } else {
        Ok(())
    }
}
pub fn execute(bytes: &[u8]) -> Result<Value, String> {
    let env: Envelope = serde_json::from_slice(bytes).map_err(|e| e.to_string())?;
    if env.protocol != "sf-oracle/1" {
        return Err("protocol mismatch".into());
    }
    let cfg = env.request.configuration;
    let signal = env.request.data.signal;
    if signal.is_empty() || signal.len() > 4096 {
        return Err("signal length outside 1..4096".into());
    }
    for &v in &signal {
        bound(v, 0.0, 1.0, "signal")?;
    }
    let (mut measured, units, version, rev) = match (
        env.family.as_str(),
        env.oracle.as_str(),
        cfg.profile.as_str(),
    ) {
        ("spike-encoder-equivalence-pairs", "axon-encoder", "axon-stream-v1") => {
            if cfg.intervention.is_some() {
                return Err("encoder intervention must be null".into());
            }
            let p: encoder::Parameters =
                serde_json::from_str(cfg.parameters.get()).map_err(|e| e.to_string())?;
            (
                encoder::run(&signal, &p)?,
                json!({"t_ms":"millisecond","reconstruction":"normalized signal","rmse":"normalized signal","spike_count":"spikes"}),
                "0.4.0",
                identity::AXON_REV,
            )
        }
        ("neuron-dynamics-counterfactuals", "neuromod", "neuromod-lif-v1") => {
            let p: neuron::Parameters =
                serde_json::from_str(cfg.parameters.get()).map_err(|e| e.to_string())?;
            let intervention = cfg.intervention.ok_or("neuron requires intervention")?;
            (
                neuron::run(&signal, &p, &intervention)?,
                json!({"spikes":"millisecond","v_trace":"crate membrane units","spike_count":"spikes","spike_count_delta":"spikes"}),
                "0.6.0",
                identity::NEUROMOD_REV,
            )
        }
        _ => return Err("runtime/family/profile mismatch".into()),
    };
    measured["identity"] = identity::make(&env.oracle, version, rev)?;
    Ok(
        json!({"protocol":"sf-oracle/1","runtime_version":version,"runtime_commit":rev,"measured":measured,"units":units}),
    )
}
