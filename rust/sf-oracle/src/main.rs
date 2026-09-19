mod encoder;
mod identity;
mod neuron;
mod protocol;
use std::io::{Read, Write};
fn main() {
    if let Err(error) = run() {
        eprintln!("sf-oracle: {error}");
        std::process::exit(2);
    }
}
fn run() -> Result<(), String> {
    if std::env::args_os().len() != 1 {
        return Err("arguments are not supported".into());
    }
    const LIMIT: u64 = 262_144;
    let mut bytes = vec![];
    std::io::stdin()
        .take(LIMIT + 1)
        .read_to_end(&mut bytes)
        .map_err(|e| e.to_string())?;
    if bytes.len() as u64 > LIMIT {
        return Err("request byte limit exceeded".into());
    }
    let result = protocol::execute(&bytes)?;
    let output = serde_json::to_vec(&result).map_err(|e| e.to_string())?;
    if output.len() > 1_048_576 {
        return Err("response byte limit exceeded".into());
    }
    std::io::stdout()
        .write_all(&output)
        .map_err(|e| e.to_string())
}
