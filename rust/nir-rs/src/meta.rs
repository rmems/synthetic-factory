// SPDX-License-Identifier: Apache-2.0 OR MIT
//! `NirGraph`/`NirNode` metadata slots that carry in-repo fields the crate
//! types have no native slot for.

use nir_rs::nodes::NirNode;
use nir_rs::types::{MetadataMap, MetadataValue, TensorData};

/// Size key carried through `metadata` so the in-repo `size` field round-trips
/// through a [`NirGraph`], which has no native size slot.
pub(crate) const META_SIZE: &str = "sf.size";
/// Shape key carried through `metadata` for nodes that declare `shape` in the
/// in-repo form but have no crate shape field (everything except `Input`).
pub(crate) const META_SHAPE: &str = "sf.shape";
/// Timestep key carried through graph-level `metadata` for the in-repo
/// `dt_s` field.
pub(crate) const META_DT_S: &str = "sf.dt_s";

pub(crate) fn node_metadata_ref(node: &NirNode) -> &MetadataMap {
    match node {
        NirNode::Input(n) => &n.metadata,
        NirNode::Output(n) => &n.metadata,
        NirNode::Affine(n) => &n.metadata,
        NirNode::Linear(n) => &n.metadata,
        NirNode::Scale(n) => &n.metadata,
        NirNode::Conv1d(n) => &n.metadata,
        NirNode::Conv2d(n) => &n.metadata,
        NirNode::CubaLi(n) => &n.metadata,
        NirNode::CubaLif(n) => &n.metadata,
        NirNode::Delay(n) => &n.metadata,
        NirNode::Flatten(n) => &n.metadata,
        NirNode::I(n) => &n.metadata,
        NirNode::If(n) => &n.metadata,
        NirNode::Li(n) => &n.metadata,
        NirNode::Lif(n) => &n.metadata,
        NirNode::SumPool2d(n) => &n.metadata,
        NirNode::AvgPool2d(n) => &n.metadata,
        NirNode::Threshold(n) => &n.metadata,
        _ => unreachable!("NirNode variants without metadata are not constructible here"),
    }
}

pub(crate) fn metadata_i64(value: &MetadataValue) -> Option<i64> {
    match value {
        MetadataValue::I64(number) => Some(*number),
        MetadataValue::F64(number) if number.fract() == 0.0 => Some(*number as i64),
        _ => None,
    }
}

pub(crate) fn metadata_f64(value: &MetadataValue) -> Option<f64> {
    match value {
        MetadataValue::F64(number) => Some(*number),
        MetadataValue::I64(number) => Some(*number as f64),
        _ => None,
    }
}

pub(crate) fn metadata_shape(metadata: &MetadataMap) -> Option<Vec<usize>> {
    let dims = match metadata.get(META_SHAPE)? {
        MetadataValue::Tensor(tensor) => match tensor.data() {
            TensorData::I64(values) => values.iter().map(|v| *v as usize).collect(),
            _ => return None,
        },
        _ => return None,
    };
    Some(dims)
}
