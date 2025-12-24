"""
Advanced Configuration and Extension APIs
Implements configuration management and extension systems for the UTCP-based ecosystem
"""

from typing import Dict, List, Any, Optional, Callable, Type, Union, Tuple
from pydantic import BaseModel, Field, create_model
from enum import Enum
import json
import yaml
from pathlib import Path
import importlib
import inspect
from datetime import datetime
import asyncio
from graph_db import GraphDB, Node, Edge
from utcp.utcp_client import UtcpClient
from utcp.data.utcp_manual import UtcpManual
from utcp.data.tool import Tool
from domain_profiles import DomainProfile, DomainProfileType
from observability import ResearchObserver, ActivityType


class ConfigurationScope(Enum):
    """Scopes for configuration values"""
    GLOBAL = "global"
    PROFILE = "profile"
    TOOL = "tool"
    WORKFLOW = "workflow"
    USER = "user"


class ExtensionType(Enum):
    """Types of extensions"""
    PROFILE_EXTENSION = "profile_extension"
    TOOL_EXTENSION = "tool_extension"
    WORKFLOW_EXTENSION = "workflow_extension"
    STORAGE_EXTENSION = "storage_extension"
    AUTH_EXTENSION = "auth_extension"
    UI_EXTENSION = "ui_extension"


class ConfigValue(BaseModel):
    """Model for configuration values"""
    key: str
    value: Any
    scope: ConfigurationScope
    data_type: str = "string"
    description: str = ""
    default_value: Any = None
    is_sensitive: bool = False  # For passwords, tokens, etc.
    last_modified: datetime = Field(default_factory=datetime.now)


class ExtensionManifest(BaseModel):
    """Manifest for extensions"""
    name: str
    version: str
    description: str
    extension_type: ExtensionType
    author: str
    dependencies: List[str] = Field(default_factory=list)
    entry_point: str  # Module.class or module:function
    config_schema: Optional[Dict[str, Any]] = None
    tags: List[str] = Field(default_factory=list)


class ConfigurationAPI:
    """API for managing system configuration"""
    
    def __init__(self, graph_db: GraphDB, observer: ResearchObserver = None):
        self.graph_db = graph_db
        self.observer = observer
        self.config_store: Dict[str, ConfigValue] = {}
        self.config_file_path = "config/system_config.json"
        self.schema_registry: Dict[str, Dict[str, Any]] = {}
        
        # Load existing configuration
        self._load_configuration()
    
    def _load_configuration(self):
        """Load configuration from file"""
        try:
            if Path(self.config_file_path).exists():
                with open(self.config_file_path, 'r') as f:
                    config_data = json.load(f)
                    for key, value in config_data.items():
                        # Create ConfigValue from stored data
                        config_value = ConfigValue(
                            key=key,
                            value=value.get('value'),
                            scope=ConfigurationScope(value.get('scope', 'global')),
                            data_type=value.get('data_type', 'string'),
                            description=value.get('description', ''),
                            default_value=value.get('default_value'),
                            is_sensitive=value.get('is_sensitive', False)
                        )
                        self.config_store[key] = config_value
        except Exception as e:
            print(f"Error loading configuration: {e}")
    
    def _save_configuration(self):
        """Save configuration to file"""
        try:
            # Create directory if it doesn't exist
            Path(self.config_file_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Prepare data for saving
            config_data = {}
            for key, config_value in self.config_store.items():
                config_data[key] = config_value.dict()
            
            with open(self.config_file_path, 'w') as f:
                json.dump(config_data, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving configuration: {e}")
    
    def get_value(self, key: str, scope: ConfigurationScope = ConfigurationScope.GLOBAL, 
                  default: Any = None) -> Any:
        """Get a configuration value"""
        scoped_key = f"{scope.value}:{key}" if scope != ConfigurationScope.GLOBAL else key
        
        if scoped_key in self.config_store:
            return self.config_store[scoped_key].value
        elif default is not None:
            return default
        else:
            # Look for global value if specific scope not found
            if scope != ConfigurationScope.GLOBAL and key in self.config_store:
                return self.config_store[key].value
            else:
                return None
    
    def set_value(self, key: str, value: Any, scope: ConfigurationScope = ConfigurationScope.GLOBAL,
                  description: str = "", data_type: str = None, is_sensitive: bool = False):
        """Set a configuration value"""
        scoped_key = f"{scope.value}:{key}" if scope != ConfigurationScope.GLOBAL else key
        
        # Determine data type if not provided
        if data_type is None:
            data_type = type(value).__name__
        
        config_value = ConfigValue(
            key=key,
            value=value,
            scope=scope,
            data_type=data_type,
            description=description,
            is_sensitive=is_sensitive
        )
        
        self.config_store[scoped_key] = config_value
        
        # Save to file
        self._save_configuration()
        
        # Log the configuration change
        if self.observer:
            self.observer.log_activity(
                ActivityType.DISTILLATION,
                f"Configuration updated: {scoped_key}",
                metadata={
                    'key': key,
                    'scope': scope.value,
                    'data_type': data_type,
                    'is_sensitive': is_sensitive
                }
            )
    
    def get_profile_config(self, profile_type: DomainProfileType, key: str, default: Any = None) -> Any:
        """Get configuration value for a specific profile type"""
        return self.get_value(key, ConfigurationScope.PROFILE, default)
    
    def set_profile_config(self, profile_type: DomainProfileType, key: str, value: Any,
                          description: str = "", data_type: str = None, is_sensitive: bool = False):
        """Set configuration value for a specific profile type"""
        self.set_value(key, value, ConfigurationScope.PROFILE, description, data_type, is_sensitive)
    
    def get_tool_config(self, tool_name: str, key: str, default: Any = None) -> Any:
        """Get configuration value for a specific tool"""
        return self.get_value(key, ConfigurationScope.TOOL, default)
    
    def set_tool_config(self, tool_name: str, key: str, value: Any,
                        description: str = "", data_type: str = None, is_sensitive: bool = False):
        """Set configuration value for a specific tool"""
        self.set_value(key, value, ConfigurationScope.TOOL, description, data_type, is_sensitive)
    
    def get_workflow_config(self, workflow_name: str, key: str, default: Any = None) -> Any:
        """Get configuration value for a specific workflow"""
        return self.get_value(key, ConfigurationScope.WORKFLOW, default)
    
    def set_workflow_config(self, workflow_name: str, key: str, value: Any,
                           description: str = "", data_type: str = None, is_sensitive: bool = False):
        """Set configuration value for a specific workflow"""
        self.set_value(key, value, ConfigurationScope.WORKFLOW, description, data_type, is_sensitive)
    
    def get_user_config(self, user_id: str, key: str, default: Any = None) -> Any:
        """Get configuration value for a specific user"""
        return self.get_value(key, ConfigurationScope.USER, default)
    
    def set_user_config(self, user_id: str, key: str, value: Any,
                        description: str = "", data_type: str = None, is_sensitive: bool = False):
        """Set configuration value for a specific user"""
        self.set_value(key, value, ConfigurationScope.USER, description, data_type, is_sensitive)
    
    def get_all_values(self, scope: ConfigurationScope = None) -> Dict[str, Any]:
        """Get all configuration values, optionally filtered by scope"""
        result = {}
        for key, config_value in self.config_store.items():
            if scope is None or config_value.scope == scope:
                result[key] = config_value.value
        return result
    
    def register_config_schema(self, component_name: str, schema: Dict[str, Any]):
        """Register a configuration schema for a component"""
        self.schema_registry[component_name] = schema
    
    def validate_config_for_component(self, component_name: str, config: Dict[str, Any]) -> Dict[str, List[str]]:
        """Validate configuration against registered schema"""
        if component_name not in self.schema_registry:
            return {'valid': True, 'errors': []}
        
        schema = self.schema_registry[component_name]
        errors = []
        
        # Simple validation based on schema properties
        for prop_name, prop_def in schema.get('properties', {}).items():
            if prop_def.get('required', False) and prop_name not in config:
                errors.append(f"Required property '{prop_name}' is missing")
            elif prop_name in config:
                # Type validation
                expected_type = prop_def.get('type')
                actual_value = config[prop_name]
                actual_type = type(actual_value).__name__
                
                if expected_type and actual_type != expected_type:
                    errors.append(f"Property '{prop_name}' has type '{actual_type}', expected '{expected_type}'")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }


class ExtensionAPI:
    """API for managing system extensions"""
    
    def __init__(self, graph_db: GraphDB, observer: ResearchObserver = None, config_api: ConfigurationAPI = None):
        self.graph_db = graph_db
        self.observer = observer
        self.config_api = config_api
        self.extensions: Dict[str, Any] = {}
        self.extension_manifests: Dict[str, ExtensionManifest] = {}
        self.extension_directories = ["extensions/", "plugins/", "addons/"]
        
        # Register core extension points
        self.extension_points: Dict[str, List[Callable]] = {
            'profile_creation': [],
            'tool_registration': [],
            'workflow_execution': [],
            'data_processing': [],
            'authentication': [],
            'authorization': []
        }
    
    def register_extension_point(self, name: str, callback: Callable):
        """Register a callback for an extension point"""
        if name not in self.extension_points:
            self.extension_points[name] = []
        self.extension_points[name].append(callback)
    
    def trigger_extension_point(self, name: str, *args, **kwargs) -> List[Any]:
        """Trigger all callbacks registered for an extension point"""
        if name not in self.extension_points:
            return []
        
        results = []
        for callback in self.extension_points[name]:
            try:
                result = callback(*args, **kwargs)
                results.append(result)
            except Exception as e:
                print(f"Error in extension callback for {name}: {e}")
                if self.observer:
                    self.observer.log_activity(
                        ActivityType.DISTILLATION,
                        f"Extension callback error in {name}: {str(e)}",
                        metadata={'extension_point': name, 'error': str(e)}
                    )
        
        return results
    
    def load_extension_from_file(self, file_path: str) -> Optional[ExtensionManifest]:
        """Load an extension from a Python file"""
        try:
            # Import the module
            module_name = Path(file_path).stem
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Look for an extension manifest in the module
            if hasattr(module, 'EXTENSION_MANIFEST'):
                manifest_data = module.EXTENSION_MANIFEST
                manifest = ExtensionManifest(**manifest_data)
                
                # Store the manifest
                self.extension_manifests[manifest.name] = manifest
                
                # If the module has an install function, call it
                if hasattr(module, 'install'):
                    module.install(self, self.config_api)
                
                # Log the extension loading
                if self.observer:
                    self.observer.log_activity(
                        ActivityType.DISTILLATION,
                        f"Loaded extension: {manifest.name}",
                        metadata=manifest.dict()
                    )
                
                return manifest
            
            # If no manifest, try to infer from available classes/functions
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and issubclass(obj, DomainProfile) and obj != DomainProfile:
                    # This looks like a profile extension
                    manifest = ExtensionManifest(
                        name=name.lower(),
                        version="1.0.0",
                        description=f"Profile extension: {name}",
                        extension_type=ExtensionType.PROFILE_EXTENSION,
                        author="Unknown",
                        entry_point=f"{module_name}:{name}",
                        tags=["profile", "extension"]
                    )
                    self.extension_manifests[manifest.name] = manifest
                    return manifest
            
            print(f"No extension manifest found in {file_path}")
            return None
            
        except Exception as e:
            print(f"Error loading extension from {file_path}: {e}")
            return None
    
    def discover_extensions(self) -> List[ExtensionManifest]:
        """Discover available extensions in extension directories"""
        discovered_extensions = []
        
        for ext_dir in self.extension_directories:
            dir_path = Path(ext_dir)
            if dir_path.exists():
                # Look for Python files
                for py_file in dir_path.glob("**/*.py"):
                    manifest = self.load_extension_from_file(str(py_file))
                    if manifest:
                        discovered_extensions.append(manifest)
        
        return discovered_extensions
    
    def install_extension(self, manifest: ExtensionManifest) -> bool:
        """Install an extension based on its manifest"""
        try:
            # Parse the entry point
            module_part, class_part = manifest.entry_point.split(':')
            
            # Import the module
            module = importlib.import_module(module_part)
            
            # Get the class/function
            extension_class = getattr(module, class_part)
            
            # If it's a DomainProfile subclass, register it
            if inspect.isclass(extension_class) and issubclass(extension_class, DomainProfile):
                # In a real implementation, we would register this profile type
                # For now, we'll just store it
                self.extensions[manifest.name] = extension_class
                
                # Log the installation
                if self.observer:
                    self.observer.log_activity(
                        ActivityType.DISTILLATION,
                        f"Installed profile extension: {manifest.name}",
                        metadata=manifest.dict()
                    )
                
                return True
            
            # If it's a function, it might be an installer
            elif inspect.isfunction(extension_class):
                # Call the installer function
                extension_class(self, self.config_api)
                
                # Log the installation
                if self.observer:
                    self.observer.log_activity(
                        ActivityType.DISTILLATION,
                        f"Installed function extension: {manifest.name}",
                        metadata=manifest.dict()
                    )
                
                return True
            
            print(f"Unknown extension type for {manifest.name}")
            return False
            
        except Exception as e:
            print(f"Error installing extension {manifest.name}: {e}")
            return False
    
    def get_installed_extensions(self) -> List[ExtensionManifest]:
        """Get list of installed extensions"""
        return list(self.extension_manifests.values())
    
    def get_extensions_by_type(self, ext_type: ExtensionType) -> List[ExtensionManifest]:
        """Get extensions of a specific type"""
        return [m for m in self.extension_manifests.values() if m.extension_type == ext_type]
    
    def create_extension_config_model(self, manifest: ExtensionManifest) -> Optional[Type[BaseModel]]:
        """Create a Pydantic model for extension configuration based on manifest schema"""
        if not manifest.config_schema:
            return None
        
        # Create a dynamic model based on the schema
        schema = manifest.config_schema
        fields = {}
        
        for field_name, field_props in schema.get('properties', {}).items():
            field_type = self._map_json_type_to_python(field_props.get('type', 'string'))
            field_default = field_props.get('default')
            fields[field_name] = (field_type, Field(default=field_default))
        
        model_name = f"{manifest.name.replace('-', '_').replace(' ', '_').capitalize()}Config"
        model = create_model(model_name, **fields)
        
        return model
    
    def _map_json_type_to_python(self, json_type: str) -> Type:
        """Map JSON schema types to Python types"""
        type_mapping = {
            'string': str,
            'number': float,
            'integer': int,
            'boolean': bool,
            'array': list,
            'object': dict
        }
        return type_mapping.get(json_type, str)


class ExtensionBuilder:
    """Helper for building extensions"""
    
    @staticmethod
    def create_profile_extension(
        name: str,
        profile_class: Type[DomainProfile],
        author: str,
        version: str = "1.0.0",
        description: str = "",
        dependencies: List[str] = None
    ) -> str:
        """Create a profile extension"""
        extension_code = f'''
"""
{name} Profile Extension
Generated extension for UTCP ecosystem
"""

from domain_profiles import DomainProfile, DomainProfileType
from graph_db import GraphDB
from observability import ResearchObserver


class {profile_class.__name__}(DomainProfile):
    """Extended profile: {name}"""
    
    def __init__(self, graph_db: GraphDB, observer: ResearchObserver = None):
        super().__init__(DomainProfileType.{profile_class.__name__.upper()}, graph_db, observer)
    
    def get_capabilities(self) -> List[str]:
        """Get capabilities of this profile"""
        return []
    
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process requests for this profile"""
        return {{"status": "success", "message": "Extension profile working"}}


def install(extension_api, config_api):
    """Installation function for the extension"""
    # Register the profile type if needed
    pass


# Extension manifest
EXTENSION_MANIFEST = {{
    "name": "{name.lower().replace(' ', '_')}",
    "version": "{version}",
    "description": "{description}",
    "extension_type": "profile_extension",
    "author": "{author}",
    "dependencies": {dependencies or []},
    "entry_point": "__name__:{profile_class.__name__}",
    "tags": ["profile", "extension"]
}}
'''
        
        # Write the extension to a file
        extension_dir = Path("extensions")
        extension_dir.mkdir(exist_ok=True)
        
        file_path = extension_dir / f"{name.lower().replace(' ', '_')}_extension.py"
        with open(file_path, 'w') as f:
            f.write(extension_code)
        
        return str(file_path)
    
    @staticmethod
    def create_tool_extension(
        name: str,
        author: str,
        version: str = "1.0.0",
        description: str = "",
        dependencies: List[str] = None
    ) -> str:
        """Create a tool extension template"""
        extension_code = f'''
"""
{name} Tool Extension
Generated tool extension for UTCP ecosystem
"""

from utcp.data.tool import Tool


def install(extension_api, config_api):
    """Installation function for the tool extension"""
    # Create a UTCP tool definition
    tool_definition = Tool(
        name="{name.lower().replace(' ', '_')}_tool",
        description="{description}",
        inputs={{
            "type": "object",
            "properties": {{
                "query": {{"type": "string", "description": "Input query for the tool"}}
            }},
            "required": ["query"]
        }},
        outputs={{
            "type": "object",
            "properties": {{
                "result": {{"type": "string", "description": "Result of the tool operation"}}
            }}
        }},
        tags=["{name.lower()}", "tool", "extension"],
        tool_call_template={{
            "call_template_type": "http",
            "url": "http://localhost:8000/tools/{name.lower().replace(' ', '_')}",
            "http_method": "POST"
        }}
    )
    
    # Register the tool with the extension API
    # This would be handled by the extension system in a real implementation
    print(f"Registered tool: {{tool_definition.name}}")


# Extension manifest
EXTENSION_MANIFEST = {{
    "name": "{name.lower().replace(' ', '_')}_tool",
    "version": "{version}",
    "description": "{description}",
    "extension_type": "tool_extension",
    "author": "{author}",
    "dependencies": {dependencies or []},
    "entry_point": "__name__:install",
    "config_schema": {{
        "type": "object",
        "properties": {{
            "api_key": {{"type": "string", "description": "API key for the tool"}},
            "timeout": {{"type": "integer", "default": 30, "description": "Timeout in seconds"}}
        }}
    }},
    "tags": ["tool", "extension"]
}}
'''
        
        # Write the extension to a file
        extension_dir = Path("extensions")
        extension_dir.mkdir(exist_ok=True)
        
        file_path = extension_dir / f"{name.lower().replace(' ', '_')}_tool_extension.py"
        with open(file_path, 'w') as f:
            f.write(extension_code)
        
        return str(file_path)


class AdvancedConfigurationSystem:
    """Main system for advanced configuration and extensions"""
    
    def __init__(self, graph_db: GraphDB, observer: ResearchObserver = None):
        self.graph_db = graph_db
        self.observer = observer
        
        # Initialize configuration and extension APIs
        self.config_api = ConfigurationAPI(graph_db, observer)
        self.extension_api = ExtensionAPI(graph_db, observer, self.config_api)
        
        # Initialize with default configurations
        self._initialize_default_configs()
    
    def _initialize_default_configs(self):
        """Initialize default system configurations"""
        # System-level defaults
        self.config_api.set_value('system_name', 'UTCP Research and Knowledge Distillation Ecosystem', 
                                 description='Name of the system')
        self.config_api.set_value('version', '1.0.0', description='System version')
        self.config_api.set_value('debug_mode', False, data_type='boolean', 
                                 description='Enable debug logging')
        
        # Performance defaults
        self.config_api.set_value('max_concurrent_operations', 10, data_type='integer',
                                 description='Maximum concurrent operations allowed')
        self.config_api.set_value('cache_size_limit', 1000, data_type='integer',
                                 description='Maximum number of items in cache')
        self.config_api.set_value('response_timeout', 30, data_type='integer',
                                 description='Response timeout in seconds')
        
        # UTCP defaults
        self.config_api.set_value('utcp_discovery_interval', 3600, data_type='integer',
                                 description='Interval for UTCP tool discovery (seconds)')
        self.config_api.set_value('utcp_retry_attempts', 3, data_type='integer',
                                 description='Number of retry attempts for UTCP calls')
        
        # Logging defaults
        self.config_api.set_value('log_level', 'INFO', 
                                 description='Logging level (DEBUG, INFO, WARNING, ERROR)')
        self.config_api.set_value('log_retention_days', 30, data_type='integer',
                                 description='Number of days to retain logs')
    
    def get_system_config(self) -> Dict[str, Any]:
        """Get all system configuration values"""
        return self.config_api.get_all_values(ConfigurationScope.GLOBAL)
    
    def update_system_config(self, config_updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update system configuration values"""
        results = {}
        
        for key, value in config_updates.items():
            try:
                # Determine data type
                data_type = type(value).__name__
                
                # Set the configuration value
                self.config_api.set_value(key, value, data_type=data_type)
                results[key] = {'status': 'updated', 'value': value}
                
                # Log the configuration update
                if self.observer:
                    self.observer.log_activity(
                        ActivityType.DISTILLATION,
                        f"Updated system configuration: {key}",
                        metadata={'key': key, 'value': value, 'data_type': data_type}
                    )
                    
            except Exception as e:
                results[key] = {'status': 'error', 'error': str(e)}
        
        return results
    
    def get_profile_config(self, profile_type: DomainProfileType) -> Dict[str, Any]:
        """Get configuration for a specific profile type"""
        # This would filter configuration values for the specific profile
        all_config = self.config_api.get_all_values()
        profile_config = {}
        
        # In a real implementation, this would have more sophisticated filtering
        # For now, we'll return all values with profile-specific prefixes
        for key, value in all_config.items():
            if key.startswith(f"{profile_type.value}_"):
                profile_config[key] = value
        
        return profile_config
    
    def update_profile_config(self, profile_type: DomainProfileType, 
                             config_updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update configuration for a specific profile type"""
        results = {}
        
        for key, value in config_updates.items():
            try:
                data_type = type(value).__name__
                self.config_api.set_profile_config(profile_type, key, value, 
                                                 data_type=data_type)
                results[key] = {'status': 'updated', 'value': value}
            except Exception as e:
                results[key] = {'status': 'error', 'error': str(e)}
        
        return results
    
    def discover_and_install_extensions(self) -> Dict[str, Any]:
        """Discover and install available extensions"""
        # Discover extensions
        discovered_extensions = self.extension_api.discover_extensions()
        
        # Install discovered extensions
        installed_count = 0
        failed_count = 0
        install_results = []
        
        for manifest in discovered_extensions:
            try:
                success = self.extension_api.install_extension(manifest)
                if success:
                    installed_count += 1
                    install_results.append({
                        'name': manifest.name,
                        'status': 'installed',
                        'type': manifest.extension_type.value
                    })
                else:
                    failed_count += 1
                    install_results.append({
                        'name': manifest.name,
                        'status': 'failed',
                        'type': manifest.extension_type.value
                    })
            except Exception as e:
                failed_count += 1
                install_results.append({
                    'name': manifest.name,
                    'status': 'error',
                    'type': manifest.extension_type.value,
                    'error': str(e)
                })
        
        # Log the extension discovery and installation
        if self.observer:
            self.observer.log_activity(
                ActivityType.DISTILLATION,
                f"Discovered and processed {len(discovered_extensions)} extensions",
                metadata={
                    'discovered_count': len(discovered_extensions),
                    'installed_count': installed_count,
                    'failed_count': failed_count,
                    'results': install_results
                }
            )
        
        return {
            'discovered_extensions': len(discovered_extensions),
            'installed_extensions': installed_count,
            'failed_extensions': failed_count,
            'install_results': install_results,
            'timestamp': datetime.now().isoformat()
        }
    
    def create_custom_profile_extension(self, name: str, profile_class: Type[DomainProfile], 
                                      author: str, description: str = "") -> str:
        """Create a custom profile extension"""
        file_path = ExtensionBuilder.create_profile_extension(
            name=name,
            profile_class=profile_class,
            author=author,
            description=description
        )
        
        # Log the extension creation
        if self.observer:
            self.observer.log_activity(
                ActivityType.DISTILLATION,
                f"Created custom profile extension: {name}",
                metadata={'file_path': file_path, 'author': author}
            )
        
        return file_path
    
    def create_custom_tool_extension(self, name: str, author: str, 
                                   description: str = "") -> str:
        """Create a custom tool extension"""
        file_path = ExtensionBuilder.create_tool_extension(
            name=name,
            author=author,
            description=description
        )
        
        # Log the extension creation
        if self.observer:
            self.observer.log_activity(
                ActivityType.DISTILLATION,
                f"Created custom tool extension: {name}",
                metadata={'file_path': file_path, 'author': author}
            )
        
        return file_path
    
    def get_extension_capabilities(self) -> Dict[str, Any]:
        """Get information about extension capabilities"""
        installed_extensions = self.extension_api.get_installed_extensions()
        
        capabilities = {
            'total_extensions': len(installed_extensions),
            'extension_types': {},
            'extension_points': list(self.extension_api.extension_points.keys()),
            'available_extensions': [ext.dict() for ext in installed_extensions]
        }
        
        # Count extensions by type
        for ext in installed_extensions:
            ext_type = ext.extension_type.value
            capabilities['extension_types'][ext_type] = capabilities['extension_types'].get(ext_type, 0) + 1
        
        return capabilities
    
    def validate_configuration(self, component_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate configuration against registered schema"""
        validation_result = self.config_api.validate_config_for_component(component_name, config)
        
        # Log validation result
        if self.observer:
            self.observer.log_activity(
                ActivityType.DISTILLATION,
                f"Configuration validation for {component_name}: {'valid' if validation_result['valid'] else 'invalid'}",
                metadata={
                    'component': component_name,
                    'valid': validation_result['valid'],
                    'errors': validation_result['errors']
                }
            )
        
        return validation_result


class APIEndpoint:
    """API endpoint for configuration and extension management"""
    
    def __init__(self, config_system: AdvancedConfigurationSystem):
        self.config_system = config_system
    
    async def get_system_config(self) -> Dict[str, Any]:
        """Get all system configuration"""
        return self.config_system.get_system_config()
    
    async def update_system_config(self, config_updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update system configuration"""
        return self.config_system.update_system_config(config_updates)
    
    async def get_extension_capabilities(self) -> Dict[str, Any]:
        """Get extension capabilities information"""
        return self.config_system.get_extension_capabilities()
    
    async def discover_extensions(self) -> Dict[str, Any]:
        """Discover and install extensions"""
        return self.config_system.discover_and_install_extensions()
    
    async def create_profile_extension(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a custom profile extension"""
        name = params.get('name')
        author = params.get('author')
        description = params.get('description', '')
        
        if not name or not author:
            return {
                'status': 'error',
                'message': 'Name and author are required parameters'
            }
        
        try:
            file_path = self.config_system.create_custom_profile_extension(name, DomainProfile, author, description)
            return {
                'status': 'success',
                'message': f'Created profile extension: {name}',
                'file_path': file_path
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error creating profile extension: {str(e)}'
            }
    
    async def validate_configuration(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate configuration against schema"""
        component_name = params.get('component_name')
        config = params.get('config', {})
        
        if not component_name:
            return {
                'status': 'error',
                'message': 'Component name is required'
            }
        
        validation_result = self.config_system.validate_configuration(component_name, config)
        return {
            'status': 'success',
            'validation_result': validation_result
        }


# Example usage
if __name__ == "__main__":
    from graph_db import GraphDB
    from observability import ResearchObserver
    
    # Create a graph database instance
    graph = GraphDB()
    
    # Create observer
    observer = ResearchObserver(graph)
    
    # Create advanced configuration system
    config_system = AdvancedConfigurationSystem(graph, observer)
    
    # Get initial system config
    system_config = config_system.get_system_config()
    print(f"Initial system config keys: {list(system_config.keys())}")
    
    # Update some configuration values
    updates = {
        'debug_mode': True,
        'max_concurrent_operations': 20,
        'cache_size_limit': 2000
    }
    update_results = config_system.update_system_config(updates)
    print(f"Configuration updates: {update_results}")
    
    # Create a custom extension
    extension_path = config_system.create_custom_tool_extension(
        name="Example Tool",
        author="System",
        description="An example tool extension"
    )
    print(f"Created extension at: {extension_path}")
    
    # Discover and install extensions
    discovery_results = config_system.discover_and_install_extensions()
    print(f"Discovery results: {discovery_results}")
    
    # Get extension capabilities
    capabilities = config_system.get_extension_capabilities()
    print(f"Extension capabilities: {capabilities}")
    
    # Create API endpoint
    api_endpoint = APIEndpoint(config_system)
    
    # Example of using the API endpoint
    config_data = await api_endpoint.get_system_config()
    print(f"API returned config keys: {list(config_data.keys())}")
    
    print("Advanced Configuration and Extension System initialized successfully!")