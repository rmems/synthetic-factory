mod encoder;
mod identity;
mod neuron;
mod protocol;
use std::io::{Read, Write};
use std::path::PathBuf;
fn main() {
    if let Err(error) = run() {
        eprintln!("sf-oracle: {error}");
        std::process::exit(2);
    }
}
fn invocation() -> Result<PathBuf, String> {
    // /proc/self/cmdline carries the exact argv the caller bound, and the
    // verifier digests that same path before and after the run; reading it
    // through procfs anchors executable identity to the invocation record
    // rather than to a self-resolved executable location.
    let raw = std::fs::read("/proc/self/cmdline").map_err(|e| e.to_string())?;
    let mut fields = raw
        .split(|byte| *byte == 0)
        .filter(|field| !field.is_empty());
    let first = fields.next().ok_or("invocation path is not available")?;
    if fields.next().is_some() {
        return Err("arguments are not supported".into());
    }
    Ok(PathBuf::from(String::from_utf8_lossy(first).into_owned()))
}
fn run() -> Result<(), String> {
    let executable = invocation()?;
    const LIMIT: u64 = 262_144;
    let mut bytes = vec![];
    std::io::stdin()
        .take(LIMIT + 1)
        .read_to_end(&mut bytes)
        .map_err(|e| e.to_string())?;
    if bytes.len() as u64 > LIMIT {
        return Err("request byte limit exceeded".into());
    }
    let result = protocol::execute(&bytes, &executable)?;
    let output = serde_json::to_vec(&result).map_err(|e| e.to_string())?;
    if output.len() > 1_048_576 {
        return Err("response byte limit exceeded".into());
    }
    std::io::stdout()
        .write_all(&output)
        .map_err(|e| e.to_string())
}
