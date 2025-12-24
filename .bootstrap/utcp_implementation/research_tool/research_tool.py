"""
Research Tool - UTCP-compliant service for research and information discovery
This tool implements the research functionality as one tool among many in the ecosystem
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
import json
from fastapi import FastAPI, HTTPException, Request
from utcp.data.tool import Tool
from utcp.data.utcp_manual import UtcpManual
from utcp.utcp_client import UtcpClient
from utcp.interfaces.call_template import CallTemplate
from pydantic import BaseModel, Field
import requests
from bs4 import BeautifulSoup
import networkx as nx
import re


class ResearchInput(BaseModel):
    """Input model for research operations"""
    query: str = Field(..., description="Research query or topic to investigate")
    sources: Optional[List[str]] = Field(default=[], description="Specific sources to search")
    depth: Optional[int] = Field(default=2, ge=1, le=5, description="Depth of research exploration")
    max_results: Optional[int] = Field(default=10, ge=1, le=50, description="Maximum number of results to return")
    include_verification: Optional[bool] = Field(default=True, description="Whether to include source verification")


class ResearchOutput(BaseModel):
    """Output model for research operations"""
    query: str
    results: List[Dict[str, Any]]
    summary: str
    metadata: Dict[str, Any]
    timestamp: str


class SourceVerifier:
    """Verifies the credibility and reliability of sources"""
    
    def __init__(self):
        self.trusted_domains = {
            'edu', 'gov', 'org', 'wikipedia.org', 'arxiv.org', 
            'researchgate.net', 'springer.com', 'ieee.org'
        }
        self.known_fact_checkers = ['snopes.com', 'factcheck.org', 'politifact.com']
        
    def verify_source(self, url: str) -> Dict[str, Any]:
        """Verify a source and return credibility metrics"""
        domain = self._extract_domain(url)
        
        # Check domain trust
        domain_trust = 0.0
        if any(trusted in domain for trusted in self.trusted_domains):
            domain_trust = 0.9
        elif domain.endswith('.edu') or domain.endswith('.gov') or domain.endswith('.org'):
            domain_trust = 0.8
        elif domain.endswith('.com'):
            domain_trust = 0.5
        else:
            domain_trust = 0.3
        
        # Check for suspicious patterns
        suspicious_patterns = ['clickbait', 'unverified', 'rumor', 'gossip']
        content_suspicion = any(pattern in url.lower() for pattern in suspicious_patterns)
        
        if content_suspicion:
            domain_trust *= 0.5
        
        return {
            'domain': domain,
            'trust_score': domain_trust,
            'is_trusted': domain_trust >= 0.7,
            'is_suspicious': content_suspicion
        }
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except:
            return url.lower()


class DiscoveryEngine:
    """Engine for discovering and exploring information sources"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Research-Knowledge-Distillation-System/1.0'
        })
        self.verifier = SourceVerifier()
    
    async def discover_from_web(self, seed_url: str, max_pages: int = 5) -> List[Dict[str, Any]]:
        """Discover information starting from a web URL"""
        discovered_urls = []
        visited_urls = set()
        to_visit = [seed_url]
        
        while to_visit and len(discovered_urls) < max_pages:
            current_url = to_visit.pop(0)
            
            if current_url in visited_urls:
                continue
            
            visited_urls.add(current_url)
            
            try:
                response = self.session.get(current_url, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Extract text content
                    title = soup.title.string if soup.title else "No Title"
                    text_content = soup.get_text(strip=True, separator=' ')
                    
                    # Verify the source
                    verification = self.verifier.verify_source(current_url)
                    
                    # Extract links for further discovery
                    links = soup.find_all('a', href=True)
                    for link in links:
                        absolute_url = self._make_absolute_url(current_url, link['href'])
                        if self._is_valid_url(absolute_url) and absolute_url not in visited_urls:
                            to_visit.append(absolute_url)
                    
                    discovered_urls.append({
                        'url': current_url,
                        'title': title,
                        'content': text_content[:2000],  # Truncate long content
                        'content_length': len(text_content),
                        'discovered_at': datetime.now().isoformat(),
                        'verification': verification
                    })
                    
            except Exception as e:
                print(f"Error discovering {current_url}: {str(e)}")
            
            # Be respectful to servers
            await asyncio.sleep(0.5)
        
        return discovered_urls
    
    def _make_absolute_url(self, base_url: str, relative_url: str) -> str:
        """Convert relative URL to absolute URL"""
        from urllib.parse import urljoin
        return urljoin(base_url, relative_url)
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if a URL is valid and should be processed"""
        try:
            from urllib.parse import urlparse
            result = urlparse(url)
            return all([result.scheme in ['http', 'https'], result.netloc])
        except:
            return False
    
    async def search_duckduckgo(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search using DuckDuckGo API or web scraping"""
        # For this implementation, we'll simulate search results
        # In a real implementation, we would use the DuckDuckGo API
        # or scrape search results from DuckDuckGo
        import random
        
        # Simulated search results
        simulated_results = [
            f"https://example-academic-site.com/papers/{query.replace(' ', '-')}-{i}",
            f"https://research-org.com/studies/{query.replace(' ', '_')}_{i}",
            f"https://scholarly-journal.org/articles/{query.replace(' ', '-').lower()}-{i}"
        ]
        
        results = []
        for i in range(min(max_results, 3)):
            url = simulated_results[i % len(simulated_results)].format(i=i)
            verification = self.verifier.verify_source(url)
            
            results.append({
                'url': url,
                'title': f"Research Paper on {query} - Part {i+1}",
                'content': f"This is a simulated research result for the query '{query}'. The paper discusses various aspects of {query} and provides insights based on recent studies.",
                'content_length': 500,
                'discovered_at': datetime.now().isoformat(),
                'verification': verification
            })
        
        return results


class ResearchService:
    """Main service class for research operations"""
    
    def __init__(self):
        self.discovery_engine = DiscoveryEngine()
        self.graph = nx.Graph()  # For tracking relationships between discoveries
        self.search_history = []
    
    async def conduct_research(self, query: str, sources: List[str] = None, 
                              depth: int = 2, max_results: int = 10) -> ResearchOutput:
        """Conduct comprehensive research based on the query"""
        start_time = datetime.now()
        
        # If sources are provided, use them directly
        if sources:
            results = await self._research_from_sources(query, sources, max_results)
        else:
            # Use discovery engine to find sources
            results = await self._discover_and_research(query, max_results)
        
        # Record in search history
        self.search_history.append({
            'query': query,
            'timestamp': start_time.isoformat(),
            'result_count': len(results),
            'sources_used': sources or ['discovery_engine']
        })
        
        # Create summary
        summary = f"Conducted research on '{query}' and found {len(results)} relevant sources."
        
        # Prepare metadata
        metadata = {
            'query': query,
            'depth': depth,
            'max_results': max_results,
            'search_duration': (datetime.now() - start_time).total_seconds(),
            'search_timestamp': start_time.isoformat()
        }
        
        return ResearchOutput(
            query=query,
            results=results,
            summary=summary,
            metadata=metadata,
            timestamp=datetime.now().isoformat()
        )
    
    async def _research_from_sources(self, query: str, sources: List[str], 
                                   max_results: int) -> List[Dict[str, Any]]:
        """Research from specified sources"""
        results = []
        
        for source in sources:
            # Discover from each source
            discovered = await self.discovery_engine.discover_from_web(source, max_results)
            results.extend(discovered)
        
        # Limit to max_results
        return results[:max_results]
    
    async def _discover_and_research(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Discover and research using search engines"""
        # Use search engine to find initial sources
        search_results = await self.discovery_engine.search_duckduckgo(query, max_results)
        
        # For each search result, potentially do deeper discovery
        detailed_results = []
        for result in search_results:
            detailed_results.append(result)
        
        return detailed_results


# Initialize the research service
research_service = ResearchService()

# Create FastAPI app for the research tool
app = FastAPI(
    title="Research Tool - UTCP-compliant",
    description="A UTCP-compliant tool for research and information discovery",
    version="1.0.0"
)


@app.get("/")
async def research_tool_info():
    """Information about the research tool"""
    return {
        "name": "Research Tool",
        "version": "1.0.0",
        "description": "A UTCP-compliant tool for research and information discovery",
        "endpoints": {
            "/utcp": "UTCP discovery endpoint",
            "/research": "Main research endpoint",
            "/health": "Health check endpoint"
        }
    }


@app.get("/utcp")
async def utcp_discovery():
    """UTCP discovery endpoint - returns the tool manual"""
    manual = UtcpManual(
        manual_version="1.0.0",
        utcp_version="1.0.2",
        tools=[
            Tool(
                name="conduct_research",
                description="Conduct comprehensive research on a topic",
                inputs={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Research query or topic"},
                        "sources": {
                            "type": "array", 
                            "items": {"type": "string"},
                            "description": "Specific sources to search (optional)"
                        },
                        "depth": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 5,
                            "default": 2,
                            "description": "Depth of research exploration"
                        },
                        "max_results": {
                            "type": "integer", 
                            "minimum": 1,
                            "maximum": 50,
                            "default": 10,
                            "description": "Maximum number of results to return"
                        }
                    },
                    "required": ["query"]
                },
                outputs={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "results": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "url": {"type": "string"},
                                    "title": {"type": "string"},
                                    "content": {"type": "string"},
                                    "verification": {
                                        "type": "object",
                                        "properties": {
                                            "trust_score": {"type": "number"},
                                            "is_trusted": {"type": "boolean"}
                                        }
                                    }
                                }
                            }
                        },
                        "summary": {"type": "string"},
                        "metadata": {"type": "object"}
                    }
                },
                tags=["research", "discovery", "information"],
                tool_call_template={
                    "call_template_type": "http",
                    "url": "http://localhost:8000/research",
                    "http_method": "POST"
                }
            )
        ]
    )
    return manual.model_dump()


@app.post("/research", response_model=ResearchOutput)
async def conduct_research(request: Request):
    """Main endpoint to conduct research"""
    try:
        # Parse the input
        body = await request.json()
        query = body.get('query', '')
        sources = body.get('sources', [])
        depth = body.get('depth', 2)
        max_results = body.get('max_results', 10)
        
        # Validate input
        if not query:
            raise HTTPException(status_code=400, detail="Query parameter is required")
        
        # Conduct research
        result = await research_service.conduct_research(
            query=query,
            sources=sources,
            depth=depth,
            max_results=max_results
        )
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Research failed: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Research Tool",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/history")
async def get_search_history():
    """Get research history"""
    return {
        "history": research_service.search_history,
        "total_searches": len(research_service.search_history)
    }


# If running this file directly, start the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)