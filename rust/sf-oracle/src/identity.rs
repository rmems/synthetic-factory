use serde_json::{json, Value};
use sha2::{Digest, Sha256};
pub const AXON_REV: &str = "102946f40dd55287a89aa363cd2d080a9d6195d8";
pub const NEUROMOD_REV: &str = "184c80cbdad84c83042987e1b3ec6fed69578a87";
pub fn make(name: &str, version: &str, revision: &str) -> Result<Value, String> {
    let exe = std::env::current_exe().map_err(|e| e.to_string())?;
    let bytes = std::fs::read(exe).map_err(|e| e.to_string())?;
    Ok(
        json!({"crate_name":name,"crate_version":version,"source_revision":revision,"lock_sha256":env!("SF_LOCK_SHA256"),"adapter_source_sha256":env!("SF_ADAPTER_SOURCE_SHA256"),"adapter_revision":env!("SF_ADAPTER_REVISION"),"executable_sha256":format!("{:x}",Sha256::digest(bytes))}),
    )
}
