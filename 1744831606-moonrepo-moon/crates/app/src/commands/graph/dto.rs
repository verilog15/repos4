use serde::{Deserialize, Serialize};

#[derive(Debug, Hash, Eq, PartialEq, Serialize, Deserialize)]
pub struct GraphNodeDto {
    pub id: usize,
    pub label: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct GraphEdgeDto {
    pub id: String,
    pub label: String,
    pub source: usize,
    pub target: usize,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct GraphInfoDto {
    pub nodes: Vec<GraphNodeDto>,
    pub edges: Vec<GraphEdgeDto>,
}
