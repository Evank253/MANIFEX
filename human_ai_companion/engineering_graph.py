from dataclasses import dataclass, field
from hashlib import sha256
import json


@dataclass(frozen=True)
class GraphNode:
    node_id: str
    node_type: str
    label: str
    provenance: dict[str, str]
    assumptions: tuple[str, ...] = ()


@dataclass(frozen=True)
class GraphEdge:
    source: str
    target: str
    edge_type: str


@dataclass
class EngineeringGraph:
    nodes: dict[str, GraphNode] = field(default_factory=dict)
    edges: list[GraphEdge] = field(default_factory=list)

    def add_node(self, node: GraphNode) -> None:
        if node.node_id in self.nodes:
            raise ValueError(f"duplicate node: {node.node_id}")
        if not node.provenance:
            raise ValueError("every node requires provenance")
        self.nodes[node.node_id] = node

    def add_edge(self, edge: GraphEdge) -> None:
        if edge.source not in self.nodes or edge.target not in self.nodes:
            raise ValueError("edge references unknown node")
        self.edges.append(edge)

    def validate(self) -> str:
        if not self.nodes:
            return "BLOCKED"
        return "READY_FOR_HUMAN_REVIEW"

    def digest(self) -> str:
        body = {
            "nodes": [self.nodes[key].__dict__ for key in sorted(self.nodes)],
            "edges": [edge.__dict__ for edge in self.edges],
        }
        canonical = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
        return sha256(canonical).hexdigest()
