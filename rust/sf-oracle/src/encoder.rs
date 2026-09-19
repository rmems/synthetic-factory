use crate::protocol::bound;
use axon_encoder::{
    prelude::{DeltaEncoder, RateEncoder},
    Encoder,
};
use serde::Deserialize;
use serde_json::{json, Value};
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Parameters {
    pub sample_ms: f64,
    pub rate_hz: f64,
    pub delta_threshold: f64,
}
pub fn run(signal: &[f64], p: &Parameters) -> Result<Value, String> {
    bound(p.sample_ms, 0.01, 100.0, "sample_ms")?;
    bound(p.rate_hz, 0.01, 1000.0, "rate_hz")?;
    bound(p.delta_threshold, f64::MIN_POSITIVE, 1.0, "delta_threshold")?;
    if p.delta_threshold as f32 == 0.0 || p.rate_hz * p.sample_ms / 1000.0 > 1.0 {
        return Err("encoder resolution/rate bound".into());
    }
    let mut rate = RateEncoder::try_new(
        0.0,
        p.rate_hz as f32,
        (0.0, 1.0),
        (p.sample_ms / 1000.0) as f32,
    )
    .map_err(|e| e.to_string())?;
    let mut delta =
        DeltaEncoder::try_new(p.delta_threshold as f32, 1).map_err(|e| e.to_string())?;
    let r = encode(signal, p, &mut rate, false);
    let d = encode(signal, p, &mut delta, true);
    let a = r["rmse"].as_f64().unwrap();
    let b = d["rmse"].as_f64().unwrap();
    let winner = if a < b {
        "rate"
    } else if b < a {
        "delta"
    } else {
        "tie"
    };
    Ok(json!({"profile":"axon-stream-v1","rate":r,"delta":d,"winner":winner}))
}
fn encode(signal: &[f64], p: &Parameters, encoder: &mut dyn Encoder, delta: bool) -> Value {
    encoder.reset();
    let mut spikes = vec![];
    let mut reconstruction = vec![];
    let mut level = 0.0f64;
    for (i, &value) in signal.iter().enumerate() {
        let out = encoder.encode_step(&[value as f32]);
        level = reconstructed_level(level, &out.spikes, p, delta);
        for s in out.spikes {
            spikes.push(
                json!({"channel":s.channel,"t_ms":i as f64*p.sample_ms,"polarity":s.polarity}),
            );
        }
        reconstruction.push(level);
    }
    let rmse = (signal
        .iter()
        .zip(&reconstruction)
        .map(|(a, b)| (a - b).powi(2))
        .sum::<f64>()
        / signal.len() as f64)
        .sqrt();
    let preview = &spikes[..spikes.len().min(24)];
    json!({"spike_count":spikes.len(),"spikes":spikes,"spike_preview":preview,"spike_preview_truncated":spikes.len()>24,"reconstruction":reconstruction,"rmse":rmse})
}

fn reconstructed_level(
    mut level: f64,
    spikes: &[axon_encoder::types::SpikeEvent],
    parameters: &Parameters,
    delta: bool,
) -> f64 {
    if !delta {
        return (spikes.len() as f64 / (parameters.rate_hz * parameters.sample_ms / 1000.0))
            .clamp(0.0, 1.0);
    }
    for spike in spikes {
        let increment = if spike.polarity {
            parameters.delta_threshold
        } else {
            -parameters.delta_threshold
        };
        level = (level + increment).clamp(0.0, 1.0);
    }
    level
}
