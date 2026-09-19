use axon_encoder::{
    prelude::{DeltaEncoder, RateEncoder},
    Encoder,
};
use neuromod::LifNeuron;
use serde_json::{json, Value};
use std::{
    io::Write,
    process::{Command, Stdio},
};
fn run(v: &Value) -> std::process::Output {
    raw(&serde_json::to_vec(v).unwrap())
}
fn raw(bytes: &[u8]) -> std::process::Output {
    let mut child = Command::new(env!("CARGO_BIN_EXE_sf-oracle"))
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    child.stdin.take().unwrap().write_all(bytes).unwrap();
    child.wait_with_output().unwrap()
}
fn request(family: &str) -> Value {
    let (oracle, profile, parameters, intervention) = if family == "encoder" {
        (
            "axon-encoder",
            "axon-stream-v1",
            json!({"sample_ms":10.0,"rate_hz":100.0,"delta_threshold":0.25}),
            Value::Null,
        )
    } else {
        (
            "neuromod",
            "neuromod-lif-v1",
            json!({"dt_ms":1.0,"threshold":0.8,"decay":0.1,"input_scale":1.0}),
            json!({"parameter":"threshold","factor":0.5}),
        )
    };
    let family = if family == "encoder" {
        "spike-encoder-equivalence-pairs"
    } else {
        "neuron-dynamics-counterfactuals"
    };
    json!({"protocol":"sf-oracle/1","oracle":oracle,"family":family,"request":{"configuration":{"profile":profile,"parameters":parameters,"intervention":intervention},"data":{"signal":[0.0,0.5,1.0,0.0,1.0]}}})
}
fn result(v: &Value) -> Value {
    let out = run(v);
    assert!(
        out.status.success(),
        "{}",
        String::from_utf8_lossy(&out.stderr)
    );
    serde_json::from_slice(&out.stdout).unwrap()
}
#[test]
fn encoder_matches_direct_streaming_calls_and_resets() {
    let req = request("encoder");
    let answer = result(&req);
    assert_eq!(answer, result(&req));
    let mut rate = RateEncoder::try_new(0.0, 100.0, (0.0, 1.0), 0.01).unwrap();
    let mut delta = DeltaEncoder::try_new(0.25, 1).unwrap();
    for (name, enc) in [
        ("rate", &mut rate as &mut dyn Encoder),
        ("delta", &mut delta as &mut dyn Encoder),
    ] {
        let mut events = vec![];
        for (i, v) in [0.0, 0.5, 1.0, 0.0, 1.0].into_iter().enumerate() {
            for s in enc.encode_step(&[v]).spikes {
                events
                    .push(json!({"channel":s.channel,"t_ms":i as f64*10.0,"polarity":s.polarity}));
            }
        }
        assert_eq!(answer["measured"][name]["spikes"], json!(events));
    }
    assert_eq!(
        answer["measured"]["delta"]["reconstruction"],
        json!([0.0, 0.25, 0.5, 0.25, 0.5])
    );
    for field in ["lock_sha256", "adapter_source_sha256", "executable_sha256"] {
        assert_eq!(
            answer["measured"]["identity"][field]
                .as_str()
                .unwrap()
                .len(),
            64
        );
    }
}
#[test]
fn neuron_matches_direct_integration_before_reset() {
    let req = request("neuron");
    let answer = result(&req);
    assert_eq!(answer, result(&req));
    for (name, threshold) in [("before", 0.8), ("after", 0.4)] {
        let mut n = LifNeuron {
            threshold,
            base_threshold: threshold,
            decay_rate: 0.1,
            ..Default::default()
        };
        let mut vs = vec![];
        let mut spikes = vec![];
        for (i, x) in [0.0, 0.5, 1.0, 0.0, 1.0].into_iter().enumerate() {
            n.integrate(x);
            vs.push(n.membrane_potential as f64);
            if n.check_fire().is_some() {
                spikes.push((i + 1) as f64);
            }
        }
        assert_eq!(answer["measured"][name]["v_trace"], json!(vs));
        assert_eq!(answer["measured"][name]["spikes"], json!(spikes));
    }
}
#[test]
fn silence_and_intervention_variants() {
    for family in ["encoder", "neuron"] {
        let mut req = request(family);
        req["request"]["data"]["signal"] = json!([0.0, 0.0]);
        let answer = result(&req);
        let key = if family == "encoder" {
            "rate"
        } else {
            "before"
        };
        assert_eq!(answer["measured"][key]["spike_count"], 0);
    }
    for parameter in ["decay", "input_scale"] {
        let mut req = request("neuron");
        req["request"]["configuration"]["intervention"]["parameter"] = json!(parameter);
        assert!(run(&req).status.success());
    }
}
#[test]
fn rejects_invalid_protocol_and_parameters() {
    let base = request("encoder");
    let cases = [
        ("/protocol", json!("wrong")),
        ("/oracle", json!("neuromod")),
        ("/family", json!("mesh")),
        ("/request/configuration/profile", json!("bad")),
        ("/request/configuration/parameters/sample_ms", json!(0)),
        ("/request/configuration/parameters/rate_hz", json!(1001)),
        (
            "/request/configuration/parameters/delta_threshold",
            json!(-1),
        ),
        ("/request/data/signal", json!([])),
        ("/request/data/signal", json!([2])),
        ("/request/data/signal", json!(vec![0; 4097])),
    ];
    for (path, value) in cases {
        let mut req = base.clone();
        *req.pointer_mut(path).unwrap() = value;
        assert!(!run(&req).status.success(), "{path}");
    }
    let mut req = base;
    req["request"]["configuration"]["parameters"]["unknown"] = json!(1);
    assert!(!run(&req).status.success());
    for bytes in [
        b"null".as_slice(),
        b"{",
        b"{\"protocol\":\"sf-oracle/1\",\"protocol\":\"sf-oracle/1\"}",
        b"NaN",
    ] {
        assert!(!raw(bytes).status.success());
    }
}

#[test]
fn strict_nested_contract_and_neuron_bounds() {
    let req = request("encoder");
    let encoded = serde_json::to_string(&req).unwrap();
    let duplicate = encoded.replace("\"rate_hz\":100.0", "\"rate_hz\":50.0,\"rate_hz\":100.0");
    assert_ne!(encoded, duplicate);
    assert!(!raw(duplicate.as_bytes()).status.success());
    let mut missing = req;
    missing["request"]["configuration"]
        .as_object_mut()
        .unwrap()
        .remove("intervention");
    assert!(!run(&missing).status.success());
    for (key, value) in [
        ("dt_ms", 0.0),
        ("threshold", 0.0),
        ("decay", 1.1),
        ("input_scale", 101.0),
    ] {
        let mut req = request("neuron");
        req["request"]["configuration"]["parameters"][key] = json!(value);
        assert!(!run(&req).status.success(), "{key}");
    }
    let mut req = request("neuron");
    req["request"]["configuration"]["intervention"]["factor"] = json!(100.0);
    req["request"]["configuration"]["intervention"]["parameter"] = json!("decay");
    assert!(!run(&req).status.success());
}

#[test]
fn full_bounded_episode_and_executable_identity() {
    use sha2::{Digest, Sha256};
    let mut req = request("encoder");
    req["request"]["data"]["signal"] = json!(vec![1.0; 4096]);
    let out = run(&req);
    assert!(out.status.success());
    assert!(out.stdout.len() < 1_048_576);
    let answer: Value = serde_json::from_slice(&out.stdout).unwrap();
    assert_eq!(
        answer["measured"]["rate"]["reconstruction"]
            .as_array()
            .unwrap()
            .len(),
        4096
    );
    for name in ["rate", "delta"] {
        let side = &answer["measured"][name];
        let events = side["spikes"].as_array().unwrap();
        assert_eq!(
            side["spike_preview"],
            json!(&events[..events.len().min(24)])
        );
        assert_eq!(side["spike_preview_truncated"], json!(events.len() > 24));
    }
    let digest = format!(
        "{:x}",
        Sha256::digest(std::fs::read(env!("CARGO_BIN_EXE_sf-oracle")).unwrap())
    );
    assert_eq!(answer["measured"]["identity"]["executable_sha256"], digest);
    assert_eq!(
        answer["runtime_commit"],
        "102946f40dd55287a89aa363cd2d080a9d6195d8"
    );
    let out = Command::new(env!("CARGO_BIN_EXE_sf-oracle"))
        .arg("--unexpected")
        .output()
        .unwrap();
    assert!(!out.status.success());
    assert!(out.stdout.is_empty());
}
