"""
Foundation for UTCP-based ecosystem
Implements the core UTCP client and shared infrastructure services
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
from utcp.utcp_client import UtcpClient
from utcp.data.utcp_client_config import UtcpClientConfig
from utcp.interfaces.tool_repository import ToolRepository
from utcp.interfaces.tool_search_strategy import ToolSearchStrategy
from utcp.interfaces.serializer import Serializer
from utcp.data.utcp_manual import UtcpManual
from utcp.data.tool import Tool
import json


class EcosystemConfig:
    """Configuration for the UTCP-based ecosystem"""
    
    def __init__(self):
        # Default configuration values
        self.ecosystem_name = "Research and Knowledge Distillation Ecosystem"
        self.version = "1.0.0"
        self.default_variables = {}
        self.load_variables_from = []
        self.tool_repository_type = "in_memory"
        self.tool_search_strategy_type = "tag_and_description_word_match"
        self.manual_call_templates = []
        self.post_processing = []
        self.max_tools_per_search = 10
        self.max_iterations = 3
        self.system_prompt = "You are a helpful AI assistant with access to various tools through UTCP."


class SharedKnowledgeGraph:
    """Shared knowledge graph service accessible to all tools in the ecosystem"""
    
    def __init__(self):
        self.nodes = {}
        self.edges = []
        self.metadata = {}
        self.provenance_log = []
    
    async def add_node(self, node_id: str, node_type: str, content: str, 
                      metadata: Dict[str, Any] = None) -> bool:
        """Add a node to the shared knowledge graph"""
        try:
            self.nodes[node_id] = {
                'id': node_id,
                'type': node_type,
                'content': content,
                'metadata': metadata or {},
                'timestamp': datetime.utcnow().isoformat()
            }
            return True
        except Exception as e:
            print(f"Error adding node to graph: {e}")
            return False
    
    async def add_edge(self, source_id: str, target_id: str, 
                      relationship_type: str, metadata: Dict[str, Any] = None) -> bool:
        """Add an edge between nodes in the shared knowledge graph"""
        try:
            # Verify both nodes exist
            if source_id not in self.nodes or target_id not in self.nodes:
                raise ValueError("Source or target node does not exist in graph")
            
            edge = {
                'source_id': source_id,
                'target_id': target_id,
                'relationship_type': relationship_type,
                'metadata': metadata or {},
                'timestamp': datetime.utcnow().isoformat()
            }
            self.edges.append(edge)
            return True
        except Exception as e:
            print(f"Error adding edge to graph: {e}")
            return False
    
    async def find_nodes_by_type(self, node_type: str) -> List[Dict[str, Any]]:
        """Find nodes by type in the shared knowledge graph"""
        return [node for node in self.nodes.values() if node['type'] == node_type]
    
    async def find_nodes_by_content(self, search_term: str) -> List[Dict[str, Any]]:
        """Find nodes containing a search term in their content"""
        results = []
        search_lower = search_term.lower()
        for node in self.nodes.values():
            if search_lower in node['content'].lower():
                results.append(node)
        return results
    
    async def get_neighbors(self, node_id: str) -> List[Dict[str, Any]]:
        """Get neighboring nodes for a given node"""
        neighbors = []
        
        # Find outgoing edges
        for edge in self.edges:
            if edge['source_id'] == node_id:
                target_node = self.nodes.get(edge['target_id'])
                if target_node:
                    neighbors.append({
                        'node': target_node,
                        'relationship': edge['relationship_type'],
                        'edge_metadata': edge['metadata']
                    })
        
        # Find incoming edges
        for edge in self.edges:
            if edge['target_id'] == node_id:
                source_node = self.nodes.get(edge['source_id'])
                if source_node:
                    neighbors.append({
                        'node': source_node,
                        'relationship': edge['relationship_type'],
                        'edge_metadata': edge['metadata']
                    })
        
        return neighbors
    
    async def record_provenance(self, transformation: str, source_ids: List[str], 
                               target_id: str, metadata: Dict[str, Any] = None):
        """Record a transformation in the provenance log"""
        record = {
            'transformation': transformation,
            'source_ids': source_ids,
            'target_id': target_id,
            'metadata': metadata or {},
            'timestamp': datetime.utcnow().isoformat()
        }
        self.provenance_log.append(record)


class EcosystemClient:
    """Main client for the UTCP-based ecosystem"""
    
    def __init__(self, config: EcosystemConfig = None):
        self.config = config or EcosystemConfig()
        self.utcp_client = None
        self.shared_graph = SharedKnowledgeGraph()
        self.tools_registry = {}
    
    async def initialize(self):
        """Initialize the ecosystem client with UTCP configuration"""
        # Create UTCP client configuration
        utcp_config = UtcpClientConfig(
            variables=self.config.default_variables,
            load_variables_from=self.config.load_variables_from,
            tool_repository={
                "tool_repository_type": self.config.tool_repository_type
            },
            tool_search_strategy={
                "tool_search_strategy_type": self.config.tool_search_strategy_type
            },
            manual_call_templates=self.config.manual_call_templates,
            post_processing=self.config.post_processing
        )
        
        # Create UTCP client
        self.utcp_client = await UtcpClient.create(config=utcp_config)
        
        # Register the shared graph service
        await self.register_shared_service("knowledge_graph", self.shared_graph)
    
    async def register_shared_service(self, name: str, service: Any):
        """Register a shared service in the ecosystem"""
        self.tools_registry[name] = {
            'service': service,
            'registered_at': datetime.utcnow().isoformat()
        }
    
    async def call_ecosystem_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        """Call a tool in the ecosystem"""
        if self.utcp_client:
            return await self.utcp_client.call_tool(tool_name, args)
        else:
            raise RuntimeError("Ecosystem client not initialized")
    
    async def search_ecosystem_tools(self, query: str) -> List[Tool]:
        """Search for tools in the ecosystem"""
        if self.utcp_client:
            return await self.utcp_client.search_tools(
                query, 
                limit=self.config.max_tools_per_search, 
                any_of_tags_required=None
            )
        else:
            raise RuntimeError("Ecosystem client not initialized")
    
    async def register_ecosystem_manual(self, manual_call_template: Dict[str, Any]):
        """Register a manual call template for ecosystem tools"""
        if self.utcp_client:
            return await self.utcp_client.register_manual(manual_call_template)
        else:
            raise RuntimeError("Ecosystem client not initialized")


class ToolWrapper:
    """Base class for wrapping existing functionality as UTCP tools"""
    
    def __init__(self, name: str, description: str, ecosystem_client: EcosystemClient):
        self.name = name
        self.description = description
        self.ecosystem_client = ecosystem_client
        self.inputs_schema = {}
        self.outputs_schema = {}
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool with given arguments"""
        # This method should be overridden by subclasses
        raise NotImplementedError("Subclasses must implement execute method")
    
    def get_tool_definition(self) -> Dict[str, Any]:
        """Get the UTCP tool definition for this wrapper"""
        return {
            "name": self.name,
            "description": self.description,
            "inputs": self.inputs_schema,
            "outputs": self.outputs_schema,
            "tags": ["ecosystem", "tool"],
            "tool_call_template": {
                "call_template_type": "http",  # Default, can be overridden
                "url": f"http://localhost:8000/tools/{self.name}",
                "http_method": "POST"
            }
        }


# Example implementation of a research tool wrapper
class ResearchToolWrapper(ToolWrapper):
    """Example implementation of a research tool as a UTCP tool"""
    
    def __init__(self, ecosystem_client: EcosystemClient):
        super().__init__(
            name="research_tool",
            description="Perform research and information discovery",
            ecosystem_client=ecosystem_client
        )
        
        # Define input and output schemas
        self.inputs_schema = {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Research query"},
                "sources": {
                    "type": "array", 
                    "items": {"type": "string"},
                    "description": "List of sources to search"
                },
                "depth": {
                    "type": "integer",
                    "default": 2,
                    "description": "Depth of research exploration"
                }
            },
            "required": ["query"]
        }
        
        self.outputs_schema = {
            "type": "object",
            "properties": {
                "results": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "title": {"type": "string"},
                            "content": {"type": "string"},
                            "source": {"type": "string"},
                            "confidence": {"type": "number"}
                        }
                    }
                },
                "summary": {"type": "string"},
                "metadata": {"type": "object"}
            }
        }
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the research tool"""
        query = args.get("query", "")
        sources = args.get("sources", [])
        depth = args.get("depth", 2)
        
        # Simulate research process
        # In a real implementation, this would perform actual research
        results = []
        
        # Add to shared knowledge graph
        if self.ecosystem_client:
            node_id = f"research_{hash(query) % 10000}"
            await self.ecosystem_client.shared_graph.add_node(
                node_id,
                "research_query",
                query,
                {"sources": sources, "depth": depth}
            )
        
        # Simulated results
        results = [{
            "id": f"result_{i}",
            "title": f"Result {i} for query: {query}",
            "content": f"This is simulated research result {i} for the query '{query}'",
            "source": sources[i % len(sources)] if sources else "simulated",
            "confidence": 0.8 + (i * 0.05)  # Vary confidence slightly
        } for i in range(min(5, depth * 2))]
        
        return {
            "results": results,
            "summary": f"Found {len(results)} results for query: {query}",
            "metadata": {
                "query": query,
                "sources_used": sources,
                "depth": depth,
                "timestamp": datetime.utcnow().isoformat()
            }
        }


# Example usage and initialization
async def create_ecosystem_instance():
    """Create an instance of the ecosystem"""
    config = EcosystemConfig()
    
    # Add example manual call templates
    config.manual_call_templates = [
        {
            "name": "example_api",
            "call_template_type": "http",
            "url": "https://api.example.com/utcp",
            "http_method": "GET"
        }
    ]
    
    # Create ecosystem client
    ecosystem = EcosystemClient(config)
    await ecosystem.initialize()
    
    # Create and register example tools
    research_tool = ResearchToolWrapper(ecosystem)
    await ecosystem.register_shared_service("research_tool", research_tool)
    
    return ecosystem


if __name__ == "__main__":
    # Example of initializing the ecosystem
    async def main():
        ecosystem = await create_ecosystem_instance()
        print(f"Ecosystem initialized: {ecosystem.config.ecosystem_name}")
        
        # Example of using the research tool
        research_tool = ecosystem.tools_registry["research_tool"]["service"]
        result = await research_tool.execute({
            "query": "artificial intelligence developments",
            "sources": ["arxiv.org", "research-papers.com"],
            "depth": 2
        })
        
        print(f"Research result: {result['summary']}")
        print(f"Results count: {len(result['results'])}")
    
    # Run the example
    asyncio.run(main())