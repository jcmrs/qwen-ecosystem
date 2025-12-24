"""
Graph implementation for the Research and Knowledge Distillation System
Following the axiom: "Everything is Information, Memory, and Graph"
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional


class Node:
    """Represents a node in the information graph"""
    
    def __init__(self, node_id: str = None, node_type: str = "information", 
                 content: Any = None, metadata: Dict = None):
        self.id = node_id or str(uuid.uuid4())
        self.type = node_type
        self.content = content
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        
    def to_dict(self) -> Dict:
        """Convert node to dictionary for serialization"""
        return {
            'id': self.id,
            'type': self.type,
            'content': self.content,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        """Create node from dictionary"""
        node = cls(
            node_id=data['id'],
            node_type=data['type'],
            content=data['content'],
            metadata=data.get('metadata', {})
        )
        node.created_at = datetime.fromisoformat(data['created_at'])
        node.updated_at = datetime.fromisoformat(data['updated_at'])
        return node


class Edge:
    """Represents an edge/connection between nodes in the graph"""
    
    def __init__(self, source_id: str, target_id: str, relationship: str = "related",
                 metadata: Dict = None):
        self.source_id = source_id
        self.target_id = target_id
        self.relationship = relationship
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        
    def to_dict(self) -> Dict:
        """Convert edge to dictionary for serialization"""
        return {
            'source_id': self.source_id,
            'target_id': self.target_id,
            'relationship': self.relationship,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        """Create edge from dictionary"""
        edge = cls(
            source_id=data['source_id'],
            target_id=data['target_id'],
            relationship=data['relationship'],
            metadata=data.get('metadata', {})
        )
        edge.created_at = datetime.fromisoformat(data['created_at'])
        return edge


class GraphDB:
    """Simple in-memory graph database implementing the information graph"""
    
    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Edge] = []
        self.node_connections: Dict[str, List[str]] = {}  # source_id -> [target_ids]
        self.reverse_connections: Dict[str, List[str]] = {}  # target_id -> [source_ids]
        
    def add_node(self, node: Node) -> str:
        """Add a node to the graph"""
        self.nodes[node.id] = node
        
        # Initialize connection tracking
        if node.id not in self.node_connections:
            self.node_connections[node.id] = []
        if node.id not in self.reverse_connections:
            self.reverse_connections[node.id] = []
            
        return node.id
    
    def add_edge(self, edge: Edge) -> bool:
        """Add an edge to the graph"""
        # Verify nodes exist
        if edge.source_id not in self.nodes or edge.target_id not in self.nodes:
            return False
            
        self.edges.append(edge)
        
        # Update connection tracking
        if edge.source_id not in self.node_connections:
            self.node_connections[edge.source_id] = []
        if edge.target_id not in self.node_connections[edge.source_id]:
            self.node_connections[edge.source_id].append(edge.target_id)
            
        if edge.target_id not in self.reverse_connections:
            self.reverse_connections[edge.target_id] = []
        if edge.source_id not in self.reverse_connections[edge.target_id]:
            self.reverse_connections[edge.target_id].append(edge.source_id)
            
        return True
    
    def get_node(self, node_id: str) -> Optional[Node]:
        """Get a node by ID"""
        return self.nodes.get(node_id)
    
    def get_neighbors(self, node_id: str, direction: str = "both") -> List[Node]:
        """Get neighboring nodes"""
        neighbors = []
        
        if direction in ["out", "both"]:
            for target_id in self.node_connections.get(node_id, []):
                neighbor = self.get_node(target_id)
                if neighbor:
                    neighbors.append(neighbor)
        
        if direction in ["in", "both"]:
            for source_id in self.reverse_connections.get(node_id, []):
                neighbor = self.get_node(source_id)
                if neighbor and neighbor not in neighbors:  # Avoid duplicates
                    neighbors.append(neighbor)
                    
        return neighbors
    
    def find_nodes_by_type(self, node_type: str) -> List[Node]:
        """Find all nodes of a specific type"""
        return [node for node in self.nodes.values() if node.type == node_type]
    
    def find_nodes_by_content(self, search_term: str) -> List[Node]:
        """Find nodes containing a specific term in their content"""
        results = []
        for node in self.nodes.values():
            if search_term.lower() in str(node.content).lower():
                results.append(node)
        return results
    
    def to_json(self) -> str:
        """Serialize the graph to JSON"""
        data = {
            'nodes': [node.to_dict() for node in self.nodes.values()],
            'edges': [edge.to_dict() for edge in self.edges]
        }
        return json.dumps(data, indent=2)
    
    def from_json(self, json_str: str):
        """Load the graph from JSON"""
        data = json.loads(json_str)
        
        # Clear existing data
        self.nodes = {}
        self.edges = []
        self.node_connections = {}
        self.reverse_connections = {}
        
        # Load nodes
        for node_data in data['nodes']:
            node = Node.from_dict(node_data)
            self.add_node(node)
        
        # Load edges
        for edge_data in data['edges']:
            edge = Edge.from_dict(edge_data)
            self.add_edge(edge)


# Example usage and testing
if __name__ == "__main__":
    # Create a sample graph
    graph = GraphDB()
    
    # Add some nodes
    research_node = Node(node_type="research_material", 
                        content="Sample research material about AI",
                        metadata={"source": "web", "verified": True})
    graph.add_node(research_node)
    
    finding_node = Node(node_type="finding",
                       content="Key finding about information processing",
                       metadata={"confidence": 0.9})
    graph.add_node(finding_node)
    
    knowledge_node = Node(node_type="knowledge",
                         content="Information processing involves patterns",
                         metadata={"validated": True})
    graph.add_node(knowledge_node)
    
    # Add edges
    graph.add_edge(Edge(research_node.id, finding_node.id, "leads_to"))
    graph.add_edge(Edge(finding_node.id, knowledge_node.id, "distills_to"))
    
    # Print graph info
    print(f"Graph contains {len(graph.nodes)} nodes and {len(graph.edges)} edges")
    
    # Find nodes
    research_nodes = graph.find_nodes_by_type("research_material")
    print(f"Found {len(research_nodes)} research materials")
    
    # Get neighbors
    neighbors = graph.get_neighbors(research_node.id)
    print(f"Research node has {len(neighbors)} connected nodes")
    
    # Serialize to JSON
    json_output = graph.to_json()
    print("\nSerialized graph:")
    print(json_output)