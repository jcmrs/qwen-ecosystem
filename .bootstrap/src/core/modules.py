"""
Module system for the Research and Knowledge Distillation System
Implements modularity and extensibility requirements
"""

import importlib
import os
import sys
from abc import ABC, abstractmethod
from typing import Any, Dict, List
import configparser


class ModuleInterface(ABC):
    """Abstract base class for all modules in the system"""
    
    @abstractmethod
    def initialize(self, config: configparser.ConfigParser) -> bool:
        """Initialize the module with configuration"""
        pass
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """Execute the module's primary function"""
        pass
    
    @abstractmethod
    def shutdown(self) -> bool:
        """Clean up resources when shutting down"""
        pass


class ModuleManager:
    """Manages loading, initializing, and executing modules"""
    
    def __init__(self, config_path: str = 'config.ini'):
        self.config = configparser.ConfigParser()
        self.config.read(config_path)
        self.modules: Dict[str, ModuleInterface] = {}
        self.active_modules: List[str] = []
    
    def load_module(self, module_name: str, module_path: str = None) -> bool:
        """Load a module by name"""
        try:
            if module_path:
                # Add the module path to sys.path if needed
                module_dir = os.path.dirname(module_path)
                if module_dir not in sys.path:
                    sys.path.insert(0, module_dir)
                
                # Import the module
                spec = importlib.util.spec_from_file_location(module_name, module_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
            else:
                # Import from standard location
                module = importlib.import_module(module_name)
            
            # Find the module class (assuming it matches the module name)
            module_class = getattr(module, module_name.capitalize() + "Module", None)
            if not module_class:
                # Try with just "Module" suffix
                module_class = getattr(module, "Module", None)
            
            if not module_class or not issubclass(module_class, ModuleInterface):
                raise ValueError(f"Module {module_name} does not contain a valid ModuleInterface implementation")
            
            # Create instance and initialize
            instance = module_class()
            if instance.initialize(self.config):
                self.modules[module_name] = instance
                return True
            else:
                print(f"Failed to initialize module: {module_name}")
                return False
                
        except Exception as e:
            print(f"Error loading module {module_name}: {str(e)}")
            return False
    
    def initialize_modules(self) -> bool:
        """Initialize all configured modules"""
        active_modules_str = self.config.get('modules', 'active_modules', fallback='')
        if active_modules_str:
            self.active_modules = [mod.strip() for mod in active_modules_str.split(',')]
        else:
            self.active_modules = []
        
        success = True
        for module_name in self.active_modules:
            if module_name:  # Skip empty strings
                if not self.load_module(module_name):
                    print(f"Failed to load module: {module_name}")
                    success = False
        
        return success
    
    def execute_module(self, module_name: str, *args, **kwargs) -> Any:
        """Execute a specific module"""
        if module_name in self.modules:
            return self.modules[module_name].execute(*args, **kwargs)
        else:
            raise ValueError(f"Module {module_name} not found or not loaded")
    
    def shutdown_all(self) -> bool:
        """Shutdown all loaded modules"""
        success = True
        for name, module in self.modules.items():
            if not module.shutdown():
                print(f"Error shutting down module: {name}")
                success = False
        return success


# Example modules following the interface

class ResearchModule(ModuleInterface):
    """Example research module implementing the module interface"""
    
    def __init__(self):
        self.initialized = False
        self.graph_db = None
    
    def initialize(self, config: configparser.ConfigParser) -> bool:
        """Initialize the research module"""
        try:
            # Import here to avoid circular dependencies
            from ..graph.graph_db import GraphDB
            self.graph_db = GraphDB()
            self.initialized = True
            print("Research module initialized")
            return True
        except Exception as e:
            print(f"Error initializing research module: {e}")
            return False

    def execute(self, *args, **kwargs) -> Any:
        """Execute research functionality"""
        if not self.initialized:
            raise RuntimeError("Module not initialized")

        # Example: Add a research material
        if 'action' in kwargs:
            action = kwargs['action']
            if action == 'add_material':
                from ..graph.graph_db import Node
                content = kwargs.get('content', '')
                source = kwargs.get('source', 'unknown')

                node = Node(
                    node_type='research_material',
                    content=content,
                    metadata={'source': source}
                )
                node_id = self.graph_db.add_node(node)
                return {'id': node_id, 'type': 'research_material'}

        return "Research module executed"
    
    def shutdown(self) -> bool:
        """Clean up research module resources"""
        self.graph_db = None
        self.initialized = False
        print("Research module shut down")
        return True


class DistillationModule(ModuleInterface):
    """Example distillation module implementing the module interface"""
    
    def __init__(self):
        self.initialized = False
        self.graph_db = None
    
    def initialize(self, config: configparser.ConfigParser) -> bool:
        """Initialize the distillation module"""
        try:
            from ..graph.graph_db import GraphDB
            self.graph_db = GraphDB()
            self.initialized = True
            print("Distillation module initialized")
            return True
        except Exception as e:
            print(f"Error initializing distillation module: {e}")
            return False

    def execute(self, *args, **kwargs) -> Any:
        """Execute distillation functionality"""
        if not self.initialized:
            raise RuntimeError("Module not initialized")

        # Example: Add knowledge
        if 'action' in kwargs:
            action = kwargs['action']
            if action == 'add_knowledge':
                from ..graph.graph_db import Node
                content = kwargs.get('content', '')

                node = Node(
                    node_type='knowledge',
                    content=content,
                    metadata={'verified': True}
                )
                node_id = self.graph_db.add_node(node)
                return {'id': node_id, 'type': 'knowledge'}

        return "Distillation module executed"
    
    def shutdown(self) -> bool:
        """Clean up distillation module resources"""
        self.graph_db = None
        self.initialized = False
        print("Distillation module shut down")
        return True


class GraphModule(ModuleInterface):
    """Example graph module implementing the module interface"""
    
    def __init__(self):
        self.initialized = False
        self.graph_db = None
    
    def initialize(self, config: configparser.ConfigParser) -> bool:
        """Initialize the graph module"""
        try:
            from ..graph.graph_db import GraphDB
            self.graph_db = GraphDB()
            self.initialized = True
            print("Graph module initialized")
            return True
        except Exception as e:
            print(f"Error initializing graph module: {e}")
            return False

    def execute(self, *args, **kwargs) -> Any:
        """Execute graph functionality"""
        if not self.initialized:
            raise RuntimeError("Module not initialized")

        # Example: Add a node to the graph
        if 'action' in kwargs:
            action = kwargs['action']
            if action == 'add_node':
                from ..graph.graph_db import Node
                node_type = kwargs.get('type', 'information')
                content = kwargs.get('content', '')

                node = Node(node_type=node_type, content=content)
                node_id = self.graph_db.add_node(node)
                return {'id': node_id, 'type': node_type}

        return "Graph module executed"
    
    def shutdown(self) -> bool:
        """Clean up graph module resources"""
        self.graph_db = None
        self.initialized = False
        print("Graph module shut down")
        return True


# Main module management function
def run_with_modules():
    """Example of how to use the module system"""
    # Use the config manager to get the config file path
    from ..config.config_manager import get_config
    config_obj = get_config()

    manager = ModuleManager()  # This will use the default config

    # Initialize all configured modules
    if manager.initialize_modules():
        print("All modules initialized successfully")

        # Example of using modules
        try:
            # Use research module
            result = manager.execute_module('research', action='add_material',
                                          content='Sample research material',
                                          source='web')
            print(f"Research module result: {result}")

            # Use graph module
            result = manager.execute_module('graph', action='add_node',
                                          type='finding',
                                          content='Sample finding')
            print(f"Graph module result: {result}")

            # Use distillation module
            result = manager.execute_module('distillation', action='add_knowledge',
                                          content='Sample distilled knowledge')
            print(f"Distillation module result: {result}")

        except Exception as e:
            print(f"Error executing module: {e}")

        # Shutdown all modules
        manager.shutdown_all()
    else:
        print("Failed to initialize modules")


if __name__ == "__main__":
    run_with_modules()