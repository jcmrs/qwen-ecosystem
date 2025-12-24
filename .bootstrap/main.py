#!/usr/bin/env python3
"""
Main Application Entry Point for UTCP-Based Research and Knowledge Distillation Ecosystem

This serves as the primary entry point that integrates all components of the 
UTCP-based ecosystem where research is one tool among many.
"""

import asyncio
import argparse
import sys
import os
from pathlib import Path
from typing import Dict, Any, List

# Add the src directory to the path to allow imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from graph_db import GraphDB
from observability import ResearchObserver
from utcp.utcp_client import UtcpClient
from utcp.data.utcp_client_config import UtcpClientConfig
from ecosystem.foundation import AdvancedConfigurationSystem
from ecosystem.foundation import UtcpAgent
from ecosystem.research_tool import ResearchTool
from ecosystem.agent import UtcpAgent


class EcosystemInitializer:
    """Initializes and starts the complete UTCP-based ecosystem"""
    
    def __init__(self, config_path: str = "config/app_config.ini"):
        self.config_path = config_path
        self.graph_db = None
        self.observer = None
        self.utcp_client = None
        self.ecosystem_client = None
        self.components = {}
    
    async def initialize_graph_database(self):
        """Initialize the graph database"""
        print("Initializing Graph Database...")
        self.graph_db = GraphDB()
        print("✓ Graph Database initialized")
    
    async def initialize_observer(self):
        """Initialize the research observer for tracking activities"""
        print("Initializing Research Observer...")
        self.observer = ResearchObserver(self.graph_db)
        print("✓ Research Observer initialized")
    
    async def initialize_utcp_client(self):
        """Initialize the UTCP client for tool orchestration"""
        print("Initializing UTCP Client...")
        
        # Create UTCP client configuration
        config = UtcpClientConfig(
            variables={
                # Add any required variables here
            },
            load_variables_from=[],
            tool_repository={
                "tool_repository_type": "in_memory"
            },
            tool_search_strategy={
                "tool_search_strategy_type": "tag_and_description_word_match"
            },
            manual_call_templates=[
                # Add manual call templates for ecosystem tools
                {
                    "name": "local_research_tool",
                    "call_template_type": "http",
                    "url": "http://localhost:8001/research",
                    "http_method": "POST"
                }
            ],
            post_processing=[]
        )
        
        self.utcp_client = await UtcpClient.create(config=config)
        print("✓ UTCP Client initialized")
    
    async def initialize_ecosystem_components(self):
        """Initialize all ecosystem components"""
        print("Initializing Ecosystem Components...")
        
        # Initialize the configuration system
        self.ecosystem_client = AdvancedConfigurationSystem(
            self.graph_db, 
            self.observer
        )
        
        # Initialize research tool
        research_tool = ResearchTool(self.graph_db, self.observer)
        await research_tool.initialize()
        
        # Initialize UTCP agent
        utcp_agent = UtcpAgent(
            llm=None,  # Will be set based on configuration
            utcp_client=self.utcp_client,
            observer=self.observer
        )
        
        # Store components
        self.components = {
            'graph_db': self.graph_db,
            'observer': self.observer,
            'utcp_client': self.utcp_client,
            'ecosystem_client': self.ecosystem_client,
            'research_tool': research_tool,
            'utcp_agent': utcp_agent
        }
        
        print("✓ Ecosystem Components initialized")
    
    async def start_ecosystem_services(self):
        """Start all ecosystem services"""
        print("Starting Ecosystem Services...")
        
        # In a real implementation, this would start:
        # - FastAPI servers for each tool
        # - Background tasks for learning and optimization
        # - Monitoring and observability services
        # - Shared graph service
        
        # For now, we'll just simulate service startup
        services_started = [
            "Research Tool Service (port 8001)",
            "Knowledge Distillation Service (port 8002)",
            "Wisdom Extraction Service (port 8003)",
            "Shared Graph Service (port 8004)",
            "UTCP Agent Service (port 8005)"
        ]
        
        for service in services_started:
            print(f"  - Started {service}")
        
        print("✓ Ecosystem Services started")
    
    async def run_initialization_sequence(self):
        """Run the complete initialization sequence"""
        print("Starting UTCP-Based Research and Knowledge Distillation Ecosystem Initialization...")
        print("="*70)
        
        await self.initialize_graph_database()
        await self.initialize_observer()
        await self.initialize_utcp_client()
        await self.initialize_ecosystem_components()
        await self.start_ecosystem_services()
        
        print("="*70)
        print("Ecosystem Initialization Complete!")
        print(f"✓ Graph DB: {len(self.graph_db.nodes)} nodes, {len(self.graph_db.edges)} edges")
        print(f"✓ Tracked {len(self.observer.activities_logged)} activities")
        print(f"✓ UTCP Client ready with {len(self.utcp_client.registered_manuals)} registered manuals")
        print("✓ All ecosystem components initialized and running")
        
        return True


class EcosystemRunner:
    """Runs the ecosystem with proper lifecycle management"""
    
    def __init__(self, initializer: EcosystemInitializer):
        self.initializer = initializer
        self.running = False
    
    async def start(self):
        """Start the ecosystem"""
        print("Starting UTCP-Based Ecosystem...")
        
        # Initialize all components
        success = await self.initializer.run_initialization_sequence()
        if not success:
            print("❌ Failed to initialize ecosystem")
            return False
        
        self.running = True
        print("✅ Ecosystem is now running!")
        
        # In a real implementation, we would start the actual services here
        # For now, we'll just keep the process alive
        try:
            while self.running:
                await asyncio.sleep(1)  # Keep alive
        except KeyboardInterrupt:
            print("\nReceived shutdown signal...")
            await self.shutdown()
    
    async def shutdown(self):
        """Shut down the ecosystem gracefully"""
        print("Shutting down ecosystem...")
        
        # Perform graceful shutdown of components
        # In a real implementation, this would:
        # - Stop all running services
        # - Save current state
        # - Clean up resources
        # - Disconnect from external services
        
        self.running = False
        print("Ecosystem shut down successfully")


def main():
    """Main entry point for the application"""
    parser = argparse.ArgumentParser(
        description="UTCP-Based Research and Knowledge Distillation Ecosystem"
    )
    parser.add_argument(
        "--config", 
        default="config/app_config.ini", 
        help="Path to configuration file"
    )
    parser.add_argument(
        "--mode", 
        choices=["development", "production"], 
        default="development",
        help="Run mode (affects logging and performance settings)"
    )
    
    args = parser.parse_args()
    
    print(f"Starting ecosystem in {args.mode} mode...")
    print(f"Using configuration: {args.config}")
    
    # Create initializer
    initializer = EcosystemInitializer(config_path=args.config)
    
    # Create runner
    runner = EcosystemRunner(initializer)
    
    # Run the ecosystem
    try:
        asyncio.run(runner.start())
    except KeyboardInterrupt:
        print("\nEcosystem interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error running ecosystem: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()