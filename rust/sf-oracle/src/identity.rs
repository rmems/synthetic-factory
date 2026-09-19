use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::path::Path;
pub const AXON_REV: &str = "102946f40dd55287a89aa363cd2d080a9d6195d8";
pub const NEUROMOD_REV: &str = "184c80cbdad84c83042987e1b3ec6fed69578a87";
/// `executable` is the path the caller used to invoke this process (argv[0]),
/// not `std::env::current_exe`: the verifier spawns the binary by an explicit
/// path and digests that same path before and after the run, so a spoofed
/// invocation name only produces a mismatched digest and fails closed.
pub fn make(name: &str, version: &str, revision: &str, executable: &Path) -> Result<Value, String> {
    let bytes = std::fs::read(executable).map_err(|e| e.to_string())?;
    Ok(
        json!({"crate_name":name,"crate_version":version,"source_revision":revision,"lock_sha256":env!("SF_LOCK_SHA256"),"adapter_source_sha256":env!("SF_ADAPTER_SOURCE_SHA256"),"adapter_revision":env!("SF_ADAPTER_REVISION"),"executable_sha256":format!("{:x}",Sha256::digest(bytes))}),
    )
}
