// SPDX-License-Identifier: Apache-2.0 OR MIT
//! `silicon-bridge` process adapter for the `hardware-parity-spike-trajectories`
//! family.
//!
//! Drives a declared FPGA board over its UART link through the
//! `silicon-bridge` crate's dense Q8.8 codec. The crate's `uart` feature (and
//! its `serialport` `libudev` dependency) is intentionally not used: this
//! adapter opens the device with a default-features-off `serialport` and runs
//! the crate's [`silicon_bridge::encode_stimuli`] /
//! [`silicon_bridge::decode_response`] frame codec itself.
//!
//! Commands:
//!
//! - `silicon-bridge availability` — print the adapter's declared transport
//!   contract.
//! - `silicon-bridge execute` — read `{"device", "model", "stimulus",
//!   "repeats"}` on stdin, exchange every stimulus step with the board, and
//!   print the measured response frames. Spike/action shaping is the
//!   harness's job; this binary reports the decoded potentials, spike mask,
//!   switch word, per-run latency, frame sizes, input-saturation count, and a
//!   transcript digest of the raw RX bytes.
//!
//! Every command answers `{"ok": true, "result": ...}` or `{"ok": false,
//! "error": {"kind", "detail"}}` with a non-zero exit on failure. `kind` is
//! `transport` (device I/O failed), `codec` (a frame could not be encoded or
//! decoded), or `protocol` (bad request framing).

use std::io::Read;
use std::time::{Duration, Instant};

use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use silicon_bridge::{
    DenseQ88Layout, STIMULUS_Q88_MAX, STIMULUS_Q88_MIN, decode_response, encode_stimuli,
};

/// SiliconBridge v3.0 line rate. Matches `silicon_bridge::DEFAULT_BAUD_RATE`,
/// which is only exported under the `uart` feature this adapter deliberately
/// avoids (it would pull in `serialport`'s `libudev` dependency).
const DEFAULT_BAUD_RATE: u32 = 115_200;
/// Per-I/O read/write timeout, mirroring `silicon_bridge::DEFAULT_IO_TIMEOUT`.
const DEFAULT_IO_TIMEOUT: Duration = Duration::from_millis(100);

fn main() {
    let command = std::env::args().nth(1).unwrap_or_default();
    let outcome = match command.as_str() {
        "availability" => Ok(availability()),
        "execute" => run_execute(),
        _ => Err(AdapterError::protocol(format!(
            "unknown command {command:?}; expected availability|execute"
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

/// The failure kinds the harness distinguishes: `transport` means the device
/// link itself failed, `codec` means a frame could not be encoded or decoded
/// per the crate contract, and `protocol` means the request was malformed.
struct AdapterError {
    kind: &'static str,
    detail: String,
}

impl AdapterError {
    fn protocol(detail: impl Into<String>) -> Self {
        Self {
            kind: "protocol",
            detail: detail.into(),
        }
    }

    fn transport(detail: impl Into<String>) -> Self {
        Self {
            kind: "transport",
            detail: detail.into(),
        }
    }

    fn codec(detail: impl Into<String>) -> Self {
        Self {
            kind: "codec",
            detail: detail.into(),
        }
    }

    fn to_json(&self) -> Value {
        json!({"kind": self.kind, "detail": self.detail})
    }
}

fn availability() -> Value {
    json!({
        "adapter": "silicon-bridge",
        "crate": "silicon-bridge 0.3.0",
        "transport": "uart",
        "baud_rate": DEFAULT_BAUD_RATE,
        "io_timeout_ms": DEFAULT_IO_TIMEOUT.as_millis(),
    })
}

fn read_stdin() -> Result<Value, AdapterError> {
    let mut text = String::new();
    std::io::stdin()
        .read_to_string(&mut text)
        .map_err(|err| AdapterError::protocol(format!("cannot read stdin: {err}")))?;
    serde_json::from_str(&text)
        .map_err(|err| AdapterError::protocol(format!("stdin is not a JSON value: {err}")))
}

fn run_execute() -> Result<Value, AdapterError> {
    let request = read_stdin()?;
    let device = request
        .get("device")
        .and_then(Value::as_str)
        .ok_or_else(|| AdapterError::protocol("execute request needs a device path"))?;
    let model = request
        .get("model")
        .ok_or_else(|| AdapterError::protocol("execute request needs a model"))?;
    let stimulus = request
        .get("stimulus")
        .ok_or_else(|| AdapterError::protocol("execute request needs a stimulus"))?;
    let repeats = request
        .get("repeats")
        .and_then(Value::as_u64)
        .unwrap_or(1)
        .max(1);
    execute(device, model, stimulus, repeats)
}

fn execute(
    device: &str,
    model: &Value,
    stimulus: &Value,
    repeats: u64,
) -> Result<Value, AdapterError> {
    let inputs = model
        .get("inputs")
        .and_then(Value::as_u64)
        .ok_or_else(|| AdapterError::protocol("model.inputs must be a count"))?
        as usize;
    let neurons = model
        .get("neurons")
        .and_then(Value::as_u64)
        .ok_or_else(|| AdapterError::protocol("model.neurons must be a count"))?
        as usize;
    let steps = stimulus
        .get("steps")
        .and_then(Value::as_u64)
        .ok_or_else(|| AdapterError::protocol("stimulus.steps must be a count"))?
        as usize;
    let events = stimulus
        .get("events")
        .and_then(Value::as_array)
        .ok_or_else(|| AdapterError::protocol("stimulus.events must be an array"))?;
    if events.len() < steps {
        return Err(AdapterError::protocol(
            "stimulus.events must cover every declared step",
        ));
    }
    let layout = DenseQ88Layout::dense(inputs, neurons)
        .map_err(|err| AdapterError::codec(format!("layout refused: {err}")))?;
    let tx_len = layout
        .tx_len()
        .map_err(|err| AdapterError::codec(err.to_string()))?;
    let rx_len = layout
        .rx_len()
        .map_err(|err| AdapterError::codec(err.to_string()))?;
    let mut port = serialport::new(device, DEFAULT_BAUD_RATE)
        .timeout(DEFAULT_IO_TIMEOUT)
        .open()
        .map_err(|err| AdapterError::transport(format!("cannot open {device}: {err}")))?;
    let mut runs = Vec::with_capacity(repeats as usize);
    for _ in 0..repeats {
        runs.push(exchange_once(
            port.as_mut(),
            &layout,
            events,
            steps,
            tx_len,
            rx_len,
        )?);
    }
    Ok(json!({
        "repeats": repeats,
        "runs": runs,
        "frames": {"tx_len": tx_len, "rx_len": rx_len},
        "baud_rate": DEFAULT_BAUD_RATE,
    }))
}

/// One complete stimulus exchange: every step encoded, written, and its
/// response frame decoded, with wall-clock timing around the I/O.
fn exchange_once(
    port: &mut dyn serialport::SerialPort,
    layout: &DenseQ88Layout,
    events: &[Value],
    steps: usize,
    tx_len: usize,
    rx_len: usize,
) -> Result<Value, AdapterError> {
    let mut spike_grid: Vec<Value> = Vec::with_capacity(steps);
    let mut potentials: Vec<Value> = Vec::with_capacity(steps);
    let mut potentials_raw: Vec<Value> = Vec::with_capacity(steps);
    let mut switches: Vec<Value> = Vec::with_capacity(steps);
    let mut rx_frames_hex: Vec<String> = Vec::with_capacity(steps);
    let mut transcript = Sha256::new();
    let mut saturation_events = 0_u64;
    let start = Instant::now();
    for step in 0..steps {
        let row = events
            .get(step)
            .and_then(Value::as_array)
            .ok_or_else(|| AdapterError::protocol("stimulus.events rows must be arrays"))?;
        let stimuli: Result<Vec<f32>, AdapterError> = row
            .iter()
            .map(|value| {
                value
                    .as_f64()
                    .map(|v| v as f32)
                    .ok_or_else(|| AdapterError::protocol("stimulus events must be numeric"))
            })
            .collect();
        let stimuli = stimuli?;
        saturation_events += stimuli
            .iter()
            .filter(|value| !(STIMULUS_Q88_MIN..=STIMULUS_Q88_MAX).contains(*value))
            .count() as u64;
        let tx = encode_stimuli(layout, &stimuli)
            .map_err(|err| AdapterError::codec(format!("step {step}: encode failed: {err}")))?;
        debug_assert_eq!(tx.len(), tx_len);
        port.write_all(&tx)
            .map_err(|err| AdapterError::transport(format!("step {step}: write failed: {err}")))?;
        port.flush()
            .map_err(|err| AdapterError::transport(format!("step {step}: flush failed: {err}")))?;
        let mut rx = vec![0_u8; rx_len];
        port.read_exact(&mut rx)
            .map_err(|err| AdapterError::transport(format!("step {step}: read failed: {err}")))?;
        transcript.update(&rx);
        rx_frames_hex.push(hex_lower(&rx));
        let response = decode_response(layout, &rx)
            .map_err(|err| AdapterError::codec(format!("step {step}: decode failed: {err}")))?;
        spike_grid.push(json!(
            response
                .spikes
                .iter()
                .map(|fired| if *fired { 1 } else { 0 })
                .collect::<Vec<u8>>()
        ));
        // The raw signed Q8.8 words, alongside the crate-decoded floats: the
        // wire integers are the observation a verifier can re-derive from the
        // retained RX frames without trusting this binary's decode.
        let (raw_words, _) = rx[..layout.output_neurons().saturating_mul(2)].as_chunks::<2>();
        let raw_pairs: Vec<i16> = raw_words
            .iter()
            .map(|pair| i16::from_be_bytes(*pair))
            .collect();
        potentials_raw.push(json!(raw_pairs));
        potentials.push(json!(response.potentials));
        switches.push(match response.switches {
            Some(word) => json!(word),
            None => Value::Null,
        });
    }
    Ok(json!({
        "latency_ms": start.elapsed().as_secs_f64() * 1000.0,
        "spike_grid": spike_grid,
        "potentials": potentials,
        "potentials_raw": potentials_raw,
        "switches": switches,
        "rx_frames_hex": rx_frames_hex,
        "saturation_events": saturation_events,
        "transcript_sha256": format!("sha256:{}", hex_lower(&transcript.finalize())),
    }))
}

fn hex_lower(bytes: &[u8]) -> String {
    bytes.iter().map(|byte| format!("{byte:02x}")).collect()
}
