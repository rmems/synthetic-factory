use sha2::{Digest, Sha256};
use std::{env, fs, path::Path, process::Command};
fn main() {
    let manifest = env::var("CARGO_MANIFEST_DIR").unwrap();
    let root = Path::new(&manifest).join("../..");
    let paths = [
        "Cargo.toml",
        "rust/sf-oracle/Cargo.toml",
        "rust/sf-oracle/build.rs",
        "rust/sf-oracle/src/encoder.rs",
        "rust/sf-oracle/src/identity.rs",
        "rust/sf-oracle/src/main.rs",
        "rust/sf-oracle/src/neuron.rs",
        "rust/sf-oracle/src/protocol.rs",
    ];
    let mut hash = Sha256::new();
    for path in paths {
        println!("cargo:rerun-if-changed={}", root.join(path).display());
        let bytes = fs::read(root.join(path)).unwrap();
        hash.update(path.as_bytes());
        hash.update([0]);
        hash.update((bytes.len() as u64).to_be_bytes());
        hash.update(bytes);
    }
    println!(
        "cargo:rustc-env=SF_ADAPTER_SOURCE_SHA256={:x}",
        hash.finalize()
    );
    println!(
        "cargo:rerun-if-changed={}",
        root.join("Cargo.lock").display()
    );
    println!(
        "cargo:rustc-env=SF_LOCK_SHA256={:x}",
        Sha256::digest(fs::read(root.join("Cargo.lock")).unwrap())
    );
    let output = Command::new("git")
        .args(["rev-parse", "HEAD"])
        .current_dir(&root)
        .output()
        .expect("git revision");
    assert!(output.status.success());
    let revision = String::from_utf8(output.stdout).unwrap();
    println!("cargo:rustc-env=SF_ADAPTER_REVISION={}", revision.trim());
    // Follow the worktree's real HEAD file so a new commit refreshes identity.
    let symbolic = Command::new("git")
        .args(["symbolic-ref", "-q", "HEAD"])
        .current_dir(&root)
        .output()
        .unwrap();
    let symbolic = String::from_utf8(symbolic.stdout).unwrap();
    for name in ["HEAD", symbolic.trim()]
        .into_iter()
        .filter(|s| !s.is_empty())
    {
        let output = Command::new("git")
            .args(["rev-parse", "--git-path", name])
            .current_dir(&root)
            .output()
            .unwrap();
        let path = String::from_utf8(output.stdout).unwrap();
        println!(
            "cargo:rerun-if-changed={}",
            root.join(path.trim()).display()
        );
    }
}
