"""
Applying CAMEA principles to Domain Profile system
Implements Configurability, Modularity, Extensibility, Integration, and Automation
"""

from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime
import asyncio
import threading
from enum import Enum
from graph_db import GraphDB, Node, Edge
from domain_profiles import DomainProfile, DomainProfileType, SystemOwnerProfile, DomainLinguistProfile, ResearcherProfile, ArchivistProfile, AnalystProfile, SynthesizerProfile, ValidatorProfile, OrchestratorProfile, NavigatorProfile, DomainProfileRegistry
from utcp.utcp_client import UtcpClient
from utcp.data.utcp_manual import UtcpManual
from utcp.data.tool import Tool
from observability import ResearchObserver, ActivityType


class CAMEAApplicationScope(Enum):
    """Scope at which CAMEA principles are applied"""
    WHOLE_SYSTEM = "whole_system"
    INDIVIDUAL_PART = "individual_part"
    MULTIPLE_PARTS = "multiple_parts"
    PART_TO_WHOLE = "part_to_whole"


class CAMEAAttribute(Enum):
    """The CAMEA attributes"""
    CONFIGURABILITY = "configurability"
    MODULARITY = "modularity"
    EXTENSIBILITY = "extensibility"
    INTEGRATION = "integration"
    AUTOMATION = "automation"


class CAMEAImplementation:
    """Implementation of CAMEA principles across the Domain Profile system"""
    
    def __init__(self, graph_db: GraphDB, profile_registry: DomainProfileRegistry, observer: ResearchObserver = None):
        self.graph_db = graph_db
        self.profile_registry = profile_registry
        self.observer = observer
        self.camea_registry = {
            CAMEAAttribute.CONFIGURABILITY: {},
            CAMEAAttribute.MODULARITY: {},
            CAMEAAttribute.EXTENSIBILITY: {},
            CAMEAAttribute.INTEGRATION: {},
            CAMEAAttribute.AUTOMATION: {}
        }
        self.application_matrix = {}  # Maps scope to CAMEA implementations
    
    def register_camea_implementation(self, attribute: CAMEAAttribute, scope: CAMEAApplicationScope, 
                                    component_id: str, implementation: Any):
        """Register a CAMEA implementation for a specific attribute, scope, and component"""
        if attribute not in self.camea_registry:
            self.camea_registry[attribute] = {}
        
        key = f"{scope.value}:{component_id}"
        self.camea_registry[attribute][key] = implementation
        
        # Also register in the application matrix
        if scope not in self.application_matrix:
            self.application_matrix[scope] = {}
        
        if attribute not in self.application_matrix[scope]:
            self.application_matrix[scope][attribute] = {}
        
        self.application_matrix[scope][attribute][component_id] = implementation
    
    def get_camea_implementation(self, attribute: CAMEAAttribute, scope: CAMEAApplicationScope, 
                                component_id: str) -> Any:
        """Get a registered CAMEA implementation"""
        key = f"{scope.value}:{component_id}"
        return self.camea_registry[attribute].get(key)
    
    def get_camea_applications(self, scope: CAMEAApplicationScope) -> Dict[CAMEAAttribute, Dict[str, Any]]:
        """Get all CAMEA applications for a specific scope"""
        return self.application_matrix.get(scope, {})


class ConfigurabilitySystem:
    """System for implementing configurability across Domain Profiles"""
    
    def __init__(self, camea_impl: CAMEAImplementation, profile_registry: DomainProfileRegistry):
        self.camea_impl = camea_impl
        self.profile_registry = profile_registry
        self.configurations = {}
        self.config_templates = {}
    
    def create_config_template(self, component_type: str, template: Dict[str, Any]):
        """Create a configuration template for a component type"""
        self.config_templates[component_type] = template
    
    async def configure_component(self, component_id: str, config_values: Dict[str, Any], 
                                 scope: CAMEAApplicationScope = CAMEAApplicationScope.INDIVIDUAL_PART):
        """Configure a component with specific values"""
        # Apply configuration to the component
        profile = await self.profile_registry.get_profile(component_id)
        if profile:
            # Update the profile's configuration
            if not hasattr(profile, 'configuration'):
                profile.configuration = {}
            profile.configuration.update(config_values)
            
            # Register the configuration in CAMEA system
            self.camea_impl.register_camea_implementation(
                CAMEAAttribute.CONFIGURABILITY,
                scope,
                component_id,
                config_values
            )
            
            # Log the configuration
            if self.camea_impl.observer:
                self.camea_impl.observer.log_activity(
                    ActivityType.DISTILLATION,
                    f"Configured component {component_id}",
                    node_ids=[component_id],
                    metadata={'configuration': config_values, 'scope': scope.value}
                )
        
        # Store configuration in our system
        self.configurations[component_id] = {
            'values': config_values,
            'scope': scope.value,
            'configured_at': datetime.now().isoformat()
        }
        
        return {'status': 'success', 'component_id': component_id, 'scope': scope.value}
    
    async def configure_system(self, config_values: Dict[str, Any]) -> Dict[str, Any]:
        """Configure the entire system with global settings"""
        # Configure all profiles with system-wide settings
        all_profiles = await self.profile_registry.get_all_profiles()
        results = []
        
        for profile in all_profiles:
            # Apply system-wide configuration to each profile
            profile_config = config_values.get(profile.profile_type.value, {})
            result = await self.configure_component(
                profile.profile_id, 
                profile_config, 
                CAMEAApplicationScope.PART_TO_WHOLE
            )
            results.append(result)
        
        # Register system configuration in CAMEA system
        self.camea_impl.register_camea_implementation(
            CAMEAAttribute.CONFIGURABILITY,
            CAMEAApplicationScope.WHOLE_SYSTEM,
            'system_wide',
            config_values
        )
        
        return {
            'status': 'success',
            'configured_profiles': len(results),
            'results': results,
            'timestamp': datetime.now().isoformat()
        }
    
    async def get_configuration(self, component_id: str) -> Dict[str, Any]:
        """Get configuration for a specific component"""
        return self.configurations.get(component_id, {})
    
    async def get_system_configuration(self) -> Dict[str, Any]:
        """Get configuration for the entire system"""
        return self.configurations


class ModularitySystem:
    """System for implementing modularity across Domain Profiles"""
    
    def __init__(self, camea_impl: CAMEAImplementation, profile_registry: DomainProfileRegistry):
        self.camea_impl = camea_impl
        self.profile_registry = profile_registry
        self.modules = {}
        self.dependencies = {}
        self.inter_module_interfaces = {}
    
    def define_module_interface(self, module_name: str, interface_definition: Dict[str, Any]):
        """Define the interface for a module"""
        self.inter_module_interfaces[module_name] = interface_definition
    
    async def register_module(self, module_name: str, profile_id: str, 
                             dependencies: List[str] = None) -> Dict[str, Any]:
        """Register a profile as a module with dependencies"""
        self.modules[module_name] = {
            'profile_id': profile_id,
            'registered_at': datetime.now().isoformat(),
            'dependencies': dependencies or []
        }
        
        # Register dependencies
        self.dependencies[module_name] = dependencies or []
        
        # Register in CAMEA system
        self.camea_impl.register_camea_implementation(
            CAMEAAttribute.MODULARITY,
            CAMEAApplicationScope.INDIVIDUAL_PART,
            profile_id,
            {'module_name': module_name, 'dependencies': dependencies}
        )
        
        # Log the module registration
        if self.camea_impl.observer:
            self.camea_impl.observer.log_activity(
                ActivityType.DISTILLATION,
                f"Registered module {module_name} for profile {profile_id}",
                metadata={'module_name': module_name, 'dependencies': dependencies}
            )
        
        return {
            'status': 'success',
            'module_name': module_name,
            'profile_id': profile_id,
            'dependencies': dependencies
        }
    
    async def create_module_dependency(self, dependent_module: str, required_module: str) -> bool:
        """Create a dependency relationship between modules"""
        if dependent_module not in self.dependencies:
            self.dependencies[dependent_module] = []
        
        if required_module not in self.dependencies[dependent_module]:
            self.dependencies[dependent_module].append(required_module)
            
            # Log the dependency creation
            if self.camea_impl.observer:
                self.camea_impl.observer.log_activity(
                    ActivityType.DISTILLATION,
                    f"Created dependency: {dependent_module} depends on {required_module}",
                    metadata={'dependent_module': dependent_module, 'required_module': required_module}
                )
            
            return True
        
        return False
    
    async def validate_module_dependencies(self, module_name: str) -> Dict[str, Any]:
        """Validate that all dependencies for a module are satisfied"""
        if module_name not in self.dependencies:
            return {'valid': True, 'missing_dependencies': [], 'module_exists': False}
        
        missing_deps = []
        for dep in self.dependencies[module_name]:
            if dep not in self.modules:
                missing_deps.append(dep)
        
        is_valid = len(missing_deps) == 0
        
        return {
            'valid': is_valid,
            'missing_dependencies': missing_deps,
            'all_dependencies': self.dependencies[module_name],
            'module_exists': module_name in self.modules
        }
    
    async def get_module_interactions(self) -> List[Dict[str, Any]]:
        """Get all module interaction patterns"""
        interactions = []
        
        for module, deps in self.dependencies.items():
            if module in self.modules:
                for dep in deps:
                    if dep in self.modules:
                        interactions.append({
                            'source_module': module,
                            'target_module': dep,
                            'interaction_type': 'dependency',
                            'timestamp': datetime.now().isoformat()
                        })
        
        return interactions


class ExtensibilitySystem:
    """System for implementing extensibility across Domain Profiles"""
    
    def __init__(self, camea_impl: CAMEAImplementation, profile_registry: DomainProfileRegistry):
        self.camea_impl = camea_impl
        self.profile_registry = profile_registry
        self.extensions = {}
        self.extension_points = {}
        self.extension_hooks = {}
    
    def register_extension_point(self, extension_point_name: str, 
                                description: str,
                                expected_interface: Dict[str, Any] = None):
        """Register an extension point where extensions can be attached"""
        self.extension_points[extension_point_name] = {
            'description': description,
            'expected_interface': expected_interface,
            'attached_extensions': [],
            'registered_at': datetime.now().isoformat()
        }
    
    async def attach_extension(self, extension_point: str, extension_name: str, 
                              extension_implementation: Callable) -> bool:
        """Attach an extension to an extension point"""
        if extension_point not in self.extension_points:
            return False
        
        # Register the extension
        self.extension_points[extension_point]['attached_extensions'].append({
            'name': extension_name,
            'implementation': extension_implementation,
            'attached_at': datetime.now().isoformat()
        })
        
        # Store in extensions registry
        self.extensions[extension_name] = {
            'extension_point': extension_point,
            'implementation': extension_implementation,
            'attached_at': datetime.now().isoformat()
        }
        
        # Register in CAMEA system
        profile_ids = [p.profile_id for p in await self.profile_registry.get_all_profiles()]
        for profile_id in profile_ids:
            self.camea_impl.register_camea_implementation(
                CAMEAAttribute.EXTENSIBILITY,
                CAMEAApplicationScope.MULTIPLE_PARTS,
                profile_id,
                {'extension_attached': extension_name, 'to_point': extension_point}
            )
        
        # Log the extension attachment
        if self.camea_impl.observer:
            self.camea_impl.observer.log_activity(
                ActivityType.DISTILLATION,
                f"Attached extension {extension_name} to point {extension_point}",
                metadata={'extension_name': extension_name, 'extension_point': extension_point}
            )
        
        return True
    
    async def execute_extension_point(self, extension_point: str, *args, **kwargs) -> List[Any]:
        """Execute all extensions attached to an extension point"""
        if extension_point not in self.extension_points:
            return []
        
        results = []
        for ext_info in self.extension_points[extension_point]['attached_extensions']:
            try:
                result = ext_info['implementation'](*args, **kwargs)
                if asyncio.iscoroutine(result):
                    result = await result
                results.append(result)
            except Exception as e:
                print(f"Error executing extension {ext_info['name']}: {e}")
                results.append(None)
        
        return results
    
    async def create_profile_extension(self, base_profile_type: DomainProfileType, 
                                     extension_name: str, 
                                     extension_methods: Dict[str, Callable]) -> str:
        """Create an extension for a specific profile type"""
        # In a real implementation, this would dynamically create a subclass
        # For this example, we'll simulate the creation
        extension_id = f"ext_{extension_name}_{int(datetime.now().timestamp())}"
        
        # Register the extension
        self.extensions[extension_id] = {
            'base_profile_type': base_profile_type.value,
            'extension_name': extension_name,
            'extension_methods': list(extension_methods.keys()),
            'created_at': datetime.now().isoformat()
        }
        
        # Register in CAMEA system
        self.camea_impl.register_camea_implementation(
            CAMEAAttribute.EXTENSIBILITY,
            CAMEAApplicationScope.INDIVIDUAL_PART,
            extension_id,
            {'extends': base_profile_type.value, 'methods': list(extension_methods.keys())}
        )
        
        # Log the extension creation
        if self.camea_impl.observer:
            self.camea_impl.observer.log_activity(
                ActivityType.DISTILLATION,
                f"Created profile extension {extension_name} for type {base_profile_type.value}",
                metadata={'extension_id': extension_id, 'base_type': base_profile_type.value}
            )
        
        return extension_id
    
    async def get_available_extensions(self) -> Dict[str, Any]:
        """Get information about available extensions"""
        return {
            'extension_points': list(self.extension_points.keys()),
            'attached_extensions': {ep: len(info['attached_extensions']) 
                                 for ep, info in self.extension_points.items()},
            'registered_extensions': list(self.extensions.keys()),
            'total_extensions': len(self.extensions)
        }


class IntegrationSystem:
    """System for implementing integration across Domain Profiles"""
    
    def __init__(self, camea_impl: CAMEAImplementation, profile_registry: DomainProfileRegistry, graph_db: GraphDB):
        self.camea_impl = camea_impl
        self.profile_registry = profile_registry
        self.graph_db = graph_db
        self.integrated_services = {}
        self.data_flows = []
        self.api_gateways = {}
    
    async def register_integrated_service(self, service_name: str, 
                                        profile_id: str, 
                                        api_endpoint: str,
                                        data_schema: Dict[str, Any]) -> bool:
        """Register a service for integration"""
        self.integrated_services[service_name] = {
            'profile_id': profile_id,
            'api_endpoint': api_endpoint,
            'data_schema': data_schema,
            'registered_at': datetime.now().isoformat(),
            'status': 'active'
        }
        
        # Register in CAMEA system
        self.camea_impl.register_camea_implementation(
            CAMEAAttribute.INTEGRATION,
            CAMEAApplicationScope.MULTIPLE_PARTS,
            profile_id,
            {'service_registered': service_name, 'endpoint': api_endpoint}
        )
        
        # Log the service registration
        if self.camea_impl.observer:
            self.camea_impl.observer.log_activity(
                ActivityType.DISTILLATION,
                f"Registered integrated service {service_name} for profile {profile_id}",
                metadata={'service_name': service_name, 'api_endpoint': api_endpoint}
            )
        
        return True
    
    async def create_data_flow(self, source_profile_id: str, 
                             target_profile_id: str,
                             data_type: str,
                             transformation_func: Callable = None) -> str:
        """Create a data flow between two profiles"""
        flow_id = f"flow_{int(datetime.now().timestamp())}"
        
        flow_info = {
            'id': flow_id,
            'source_profile_id': source_profile_id,
            'target_profile_id': target_profile_id,
            'data_type': data_type,
            'transformation_func': transformation_func,
            'created_at': datetime.now().isoformat(),
            'active': True
        }
        
        self.data_flows.append(flow_info)
        
        # Register in CAMEA system
        self.camea_impl.register_camea_implementation(
            CAMEAAttribute.INTEGRATION,
            CAMEAApplicationScope.MULTIPLE_PARTS,
            flow_id,
            {
                'source': source_profile_id,
                'target': target_profile_id,
                'data_type': data_type
            }
        )
        
        # Log the data flow creation
        if self.camea_impl.observer:
            self.camea_impl.observer.log_activity(
                ActivityType.DISTILLATION,
                f"Created data flow from {source_profile_id} to {target_profile_id}",
                node_ids=[source_profile_id, target_profile_id],
                metadata={'flow_id': flow_id, 'data_type': data_type}
            )
        
        return flow_id
    
    async def enable_api_gateway(self, gateway_name: str, 
                               integrated_services: List[str],
                               authentication_required: bool = True) -> Dict[str, Any]:
        """Enable an API gateway for integrated services"""
        self.api_gateways[gateway_name] = {
            'integrated_services': integrated_services,
            'authentication_required': authentication_required,
            'enabled_at': datetime.now().isoformat(),
            'routes': {}
        }
        
        # Create routes for each service
        for service_name in integrated_services:
            if service_name in self.integrated_services:
                endpoint = self.integrated_services[service_name]['api_endpoint']
                route_path = f"/api/{service_name.replace(' ', '_').lower()}"
                self.api_gateways[gateway_name]['routes'][service_name] = route_path
        
        # Register in CAMEA system
        self.camea_impl.register_camea_implementation(
            CAMEAAttribute.INTEGRATION,
            CAMEAApplicationScope.WHOLE_SYSTEM,
            gateway_name,
            {'services_integrated': integrated_services, 'auth_required': authentication_required}
        )
        
        # Log the gateway setup
        if self.camea_impl.observer:
            self.camea_impl.observer.log_activity(
                ActivityType.DISTILLATION,
                f"Enabled API gateway {gateway_name} with {len(integrated_services)} services",
                metadata={'gateway_name': gateway_name, 'service_count': len(integrated_services)}
            )
        
        return {
            'status': 'success',
            'gateway_name': gateway_name,
            'integrated_services': integrated_services,
            'routes_configured': len(self.api_gateways[gateway_name]['routes'])
        }
    
    async def get_integration_map(self) -> Dict[str, Any]:
        """Get a map of all integrations in the system"""
        return {
            'integrated_services': list(self.integrated_services.keys()),
            'data_flows': len(self.data_flows),
            'api_gateways': list(self.api_gateways.keys()),
            'service_count': len(self.integrated_services),
            'gateway_count': len(self.api_gateways)
        }


class AutomationSystem:
    """System for implementing automation across Domain Profiles"""
    
    def __init__(self, camea_impl: CAMEAImplementation, profile_registry: DomainProfileRegistry):
        self.camea_impl = camea_impl
        self.profile_registry = profile_registry
        self.workflows = {}
        self.automated_rules = {}
        self.scheduled_tasks = {}
        self.event_triggers = {}
    
    async def create_workflow(self, workflow_name: str, 
                            steps: List[Dict[str, Any]],
                            trigger_conditions: Dict[str, Any]) -> str:
        """Create an automated workflow"""
        workflow_id = f"wf_{workflow_name.replace(' ', '_')}_{int(datetime.now().timestamp())}"
        
        workflow_info = {
            'id': workflow_id,
            'name': workflow_name,
            'steps': steps,
            'trigger_conditions': trigger_conditions,
            'created_at': datetime.now().isoformat(),
            'active': True,
            'executions': []
        }
        
        self.workflows[workflow_id] = workflow_info
        
        # Register in CAMEA system
        profile_ids = [p.profile_id for p in await self.profile_registry.get_all_profiles()]
        for profile_id in profile_ids:
            self.camea_impl.register_camea_implementation(
                CAMEAAttribute.AUTOMATION,
                CAMEAApplicationScope.MULTIPLE_PARTS,
                profile_id,
                {'workflow_attached': workflow_name}
            )
        
        # Log the workflow creation
        if self.camea_impl.observer:
            self.camea_impl.observer.log_activity(
                ActivityType.DISTILLATION,
                f"Created workflow {workflow_name} with {len(steps)} steps",
                metadata={'workflow_id': workflow_id, 'step_count': len(steps)}
            )
        
        return workflow_id
    
    async def create_automated_rule(self, rule_name: str,
                                  condition: Callable,
                                  action: Callable,
                                  priority: int = 5) -> str:
        """Create an automated rule that triggers actions based on conditions"""
        rule_id = f"rule_{rule_name.replace(' ', '_')}_{int(datetime.now().timestamp())}"
        
        rule_info = {
            'id': rule_id,
            'name': rule_name,
            'condition': condition,
            'action': action,
            'priority': priority,
            'created_at': datetime.now().isoformat(),
            'active': True
        }
        
        self.automated_rules[rule_id] = rule_info
        
        # Register in CAMEA system
        profile_ids = [p.profile_id for p in await self.profile_registry.get_all_profiles()]
        for profile_id in profile_ids:
            self.camea_impl.register_camea_implementation(
                CAMEAAttribute.AUTOMATION,
                CAMEAApplicationScope.MULTIPLE_PARTS,
                profile_id,
                {'rule_attached': rule_name}
            )
        
        # Log the rule creation
        if self.camea_impl.observer:
            self.camea_impl.observer.log_activity(
                ActivityType.DISTILLATION,
                f"Created automated rule {rule_name}",
                metadata={'rule_id': rule_id, 'priority': priority}
            )
        
        return rule_id
    
    async def schedule_task(self, task_name: str,
                          task_function: Callable,
                          schedule_expression: str,  # e.g., "cron:0 9 * * *" for daily at 9 AM
                          parameters: Dict[str, Any] = None) -> str:
        """Schedule a task to run automatically"""
        task_id = f"task_{task_name.replace(' ', '_')}_{int(datetime.now().timestamp())}"
        
        task_info = {
            'id': task_id,
            'name': task_name,
            'function': task_function,
            'schedule': schedule_expression,
            'parameters': parameters or {},
            'created_at': datetime.now().isoformat(),
            'next_run': self._calculate_next_run(schedule_expression),
            'active': True
        }
        
        self.scheduled_tasks[task_id] = task_info
        
        # Register in CAMEA system
        profile_ids = [p.profile_id for p in await self.profile_registry.get_all_profiles()]
        for profile_id in profile_ids:
            self.camea_impl.register_camea_implementation(
                CAMEAAttribute.AUTOMATION,
                CAMEAApplicationScope.WHOLE_SYSTEM,
                profile_id,
                {'scheduled_task': task_name}
            )
        
        # Log the task scheduling
        if self.camea_impl.observer:
            self.camea_impl.observer.log_activity(
                ActivityType.DISTILLATION,
                f"Scheduled task {task_name} with schedule {schedule_expression}",
                metadata={'task_id': task_id, 'schedule': schedule_expression}
            )
        
        return task_id
    
    def _calculate_next_run(self, schedule_expression: str) -> datetime:
        """Calculate the next run time based on schedule expression"""
        # This is a simplified implementation
        # In a real system, we would parse cron expressions properly
        import random
        from datetime import timedelta
        
        # For this example, return a random time in the next day
        return datetime.now() + timedelta(minutes=random.randint(1, 1440))
    
    async def evaluate_rules(self, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Evaluate all automated rules against the provided context"""
        context = context or {}
        triggered_rules = []
        
        # Sort rules by priority (highest first)
        sorted_rules = sorted(
            self.automated_rules.values(),
            key=lambda r: r['priority'],
            reverse=True
        )
        
        for rule in sorted_rules:
            try:
                # Evaluate the condition
                if rule['condition'](context):
                    # Execute the action
                    result = rule['action'](context)
                    if asyncio.iscoroutine(result):
                        result = await result
                    
                    triggered_rules.append({
                        'rule_id': rule['id'],
                        'rule_name': rule['name'],
                        'result': result,
                        'executed_at': datetime.now().isoformat()
                    })
            except Exception as e:
                print(f"Error evaluating rule {rule['name']}: {e}")
        
        return triggered_rules
    
    async def execute_workflow(self, workflow_id: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a specific workflow with provided context"""
        if workflow_id not in self.workflows:
            return {'status': 'error', 'message': f'Workflow {workflow_id} not found'}
        
        workflow = self.workflows[workflow_id]
        if not workflow['active']:
            return {'status': 'error', 'message': f'Workflow {workflow_id} is not active'}
        
        context = context or {}
        execution_results = []
        
        try:
            for step in workflow['steps']:
                step_type = step.get('type', 'function_call')
                step_target = step.get('target')
                step_params = step.get('parameters', {})
                
                if step_type == 'profile_call':
                    # Execute a call to a specific profile
                    profile = await self.profile_registry.get_profile(step_target)
                    if profile:
                        result = await profile.process_request(step_params)
                        execution_results.append({
                            'step': step,
                            'result': result,
                            'executed_at': datetime.now().isoformat()
                        })
                    else:
                        execution_results.append({
                            'step': step,
                            'result': {'status': 'error', 'message': f'Profile {step_target} not found'},
                            'executed_at': datetime.now().isoformat()
                        })
                elif step_type == 'function_call':
                    # Execute a specific function (would need to be registered)
                    # For this example, we'll simulate execution
                    execution_results.append({
                        'step': step,
                        'result': {'status': 'success', 'message': f'Function {step_target} executed'},
                        'executed_at': datetime.now().isoformat()
                    })
            
            # Record execution in workflow
            execution_record = {
                'workflow_id': workflow_id,
                'context': context,
                'results': execution_results,
                'executed_at': datetime.now().isoformat()
            }
            workflow['executions'].append(execution_record)
            
            # Log the workflow execution
            if self.camea_impl.observer:
                self.camea_impl.observer.log_activity(
                    ActivityType.DISTILLATION,
                    f"Executed workflow {workflow_id} with {len(execution_results)} steps",
                    metadata={'workflow_id': workflow_id, 'step_count': len(execution_results)}
                )
            
            return {
                'status': 'success',
                'workflow_id': workflow_id,
                'execution_results': execution_results,
                'executed_at': datetime.now().isoformat()
            }
        except Exception as e:
            error_result = {
                'status': 'error',
                'message': f'Error executing workflow {workflow_id}: {str(e)}',
                'executed_at': datetime.now().isoformat()
            }
            
            # Log the workflow execution error
            if self.camea_impl.observer:
                self.camea_impl.observer.log_activity(
                    ActivityType.DISTILLATION,
                    f"Error executing workflow {workflow_id}: {str(e)}",
                    metadata={'workflow_id': workflow_id, 'error': str(e)}
                )
            
            return error_result
    
    async def get_automation_status(self) -> Dict[str, Any]:
        """Get status of all automation components"""
        return {
            'workflows': {
                'total': len(self.workflows),
                'active': len([w for w in self.workflows.values() if w['active']]),
                'executions': sum(len(w['executions']) for w in self.workflows.values())
            },
            'rules': {
                'total': len(self.automated_rules),
                'active': len([r for r in self.automated_rules.values() if r['active']])
            },
            'scheduled_tasks': {
                'total': len(self.scheduled_tasks),
                'active': len([t for t in self.scheduled_tasks.values() if t['active']])
            }
        }


class CAMEAOrchestrator:
    """Main orchestrator for CAMEA principles implementation"""
    
    def __init__(self, graph_db: GraphDB, profile_registry: DomainProfileRegistry, observer: ResearchObserver = None):
        self.graph_db = graph_db
        self.profile_registry = profile_registry
        self.observer = observer
        
        # Initialize CAMEA implementation
        self.camea_impl = CAMEAImplementation(graph_db, profile_registry, observer)
        
        # Initialize individual CAMEA systems
        self.configurability_system = ConfigurabilitySystem(self.camea_impl, profile_registry)
        self.modularity_system = ModularitySystem(self.camea_impl, profile_registry)
        self.extensibility_system = ExtensibilitySystem(self.camea_impl, profile_registry)
        self.integration_system = IntegrationSystem(self.camea_impl, profile_registry, graph_db)
        self.automation_system = AutomationSystem(self.camea_impl, profile_registry)
        
        # Register extension points for each CAMEA attribute
        self._register_extension_points()
    
    def _register_extension_points(self):
        """Register extension points for each CAMEA system"""
        # Configurability extension points
        self.configurability_system.register_extension_point(
            'dynamic_config_update',
            'Allow dynamic updates to system configuration',
            {
                'type': 'object',
                'properties': {
                    'component': {'type': 'string'},
                    'setting': {'type': 'string'},
                    'value': {}
                }
            }
        )
        
        # Modularity extension points
        self.modularity_system.register_extension_point(
            'module_interface_definition',
            'Allow definition of new module interfaces',
            {
                'type': 'object',
                'properties': {
                    'interface_name': {'type': 'string'},
                    'methods': {
                        'type': 'array',
                        'items': {'type': 'string'}
                    }
                }
            }
        )
        
        # Extensibility extension points
        self.extensibility_system.register_extension_point(
            'profile_extension_point',
            'Allow extension of profile capabilities',
            {
                'type': 'object',
                'properties': {
                    'profile_type': {'type': 'string'},
                    'extension_methods': {
                        'type': 'array',
                        'items': {'type': 'string'}
                    }
                }
            }
        )
        
        # Integration extension points
        self.integration_system.register_extension_point(
            'service_integration_point',
            'Allow integration of new services',
            {
                'type': 'object',
                'properties': {
                    'service_name': {'type': 'string'},
                    'api_endpoint': {'type': 'string'},
                    'data_schema': {'type': 'object'}
                }
            }
        )
        
        # Automation extension points
        self.automation_system.register_extension_point(
            'automation_rule_point',
            'Allow creation of new automation rules',
            {
                'type': 'object',
                'properties': {
                    'rule_name': {'type': 'string'},
                    'condition': {'type': 'string'},
                    'action': {'type': 'string'}
                }
            }
        )
    
    async def apply_camea_to_profile(self, profile_type: DomainProfileType, 
                                   config: Dict[str, Any] = None,
                                   dependencies: List[str] = None,
                                   extensions: List[Dict[str, Any]] = None,
                                   integrations: List[Dict[str, Any]] = None,
                                   automations: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Apply all CAMEA principles to a specific profile type"""
        
        profile = await self.profile_registry.get_profile_by_type(profile_type)
        if not profile:
            return {'status': 'error', 'message': f'Profile type {profile_type} not found'}
        
        results = {
            'profile_type': profile_type.value,
            'configurability': None,
            'modularity': None,
            'extensibility': None,
            'integration': None,
            'automation': None
        }
        
        # Apply configurability
        if config:
            config_result = await self.configurability_system.configure_component(
                profile.profile_id, config, CAMEAApplicationScope.INDIVIDUAL_PART
            )
            results['configurability'] = config_result
        
        # Apply modularity
        if dependencies:
            module_result = await self.modularity_system.register_module(
                f"{profile_type.value}_module", profile.profile_id, dependencies
            )
            results['modularity'] = module_result
        
        # Apply extensibility
        if extensions:
            for ext in extensions:
                ext_name = ext.get('name', f"extension_{int(datetime.now().timestamp())}")
                ext_methods = ext.get('methods', {})
                await self.extensibility_system.create_profile_extension(
                    profile_type, ext_name, ext_methods
                )
        
        # Apply integration
        if integrations:
            for integration in integrations:
                service_name = integration.get('service_name', f"service_{int(datetime.now().timestamp())}")
                api_endpoint = integration.get('api_endpoint', '/default')
                data_schema = integration.get('data_schema', {})
                
                await self.integration_system.register_integrated_service(
                    service_name, profile.profile_id, api_endpoint, data_schema
                )
        
        # Apply automation
        if automations:
            for automation in automations:
                rule_name = automation.get('rule_name', f"auto_rule_{int(datetime.now().timestamp())}")
                condition = automation.get('condition', lambda ctx: True)  # Default condition
                action = automation.get('action', lambda ctx: {'status': 'success'})  # Default action
                
                await self.automation_system.create_automated_rule(rule_name, condition, action)
        
        # Log the CAMEA application
        if self.observer:
            self.observer.log_activity(
                ActivityType.DISTILLATION,
                f"Applied CAMEA principles to profile type {profile_type.value}",
                node_ids=[profile.profile_id],
                metadata=results
            )
        
        return results
    
    async def apply_camea_to_system(self) -> Dict[str, Any]:
        """Apply CAMEA principles to the entire system"""
        results = {
            'system_wide_config': await self.configurability_system.get_system_configuration(),
            'module_interactions': await self.modularity_system.get_module_interactions(),
            'available_extensions': await self.extensibility_system.get_available_extensions(),
            'integration_map': await self.integration_system.get_integration_map(),
            'automation_status': await self.automation_system.get_automation_status()
        }
        
        # Apply system-wide configurability
        system_config = {
            'global_setting_1': 'value1',
            'global_setting_2': 'value2',
            'optimization_level': 'high'
        }
        await self.configurability_system.configure_system(system_config)
        
        # Enable system-wide integration
        await self.integration_system.enable_api_gateway(
            'main_gateway',
            list(self.integration_system.integrated_services.keys()),
            authentication_required=True
        )
        
        # Log the system-wide CAMEA application
        if self.observer:
            self.observer.log_activity(
                ActivityType.DISTILLATION,
                "Applied CAMEA principles to entire system",
                metadata=results
            )
        
        return results
    
    async def get_camea_compliance_report(self) -> Dict[str, Any]:
        """Get a report on CAMEA compliance across the system"""
        all_profiles = await self.profile_registry.get_all_profiles()
        
        report = {
            'summary': {
                'total_profiles': len(all_profiles),
                'configured_profiles': 0,
                'modular_profiles': 0,
                'extended_profiles': 0,
                'integrated_profiles': 0,
                'automated_profiles': 0
            },
            'profiles': [],
            'system_wide': await self.apply_camea_to_system()
        }
        
        for profile in all_profiles:
            profile_report = {
                'profile_id': profile.profile_id,
                'profile_type': profile.profile_type.value,
                'configurability_applied': profile.profile_id in self.configurability_system.configurations,
                'modularity_applied': profile.profile_type.value in [m.get('profile_id') for m in self.modularity_system.modules.values()],
                'extensibility_applied': any(profile.profile_id in str(ext) for ext in self.extensibility_system.extensions.values()),
                'integration_applied': profile.profile_id in [s.get('profile_id') for s in self.integration_system.integrated_services.values()],
                'automation_applied': any(profile.profile_id in str(rule) for rule in self.automation_system.automated_rules.values())
            }
            
            # Update summary counts
            if profile_report['configurability_applied']:
                report['summary']['configured_profiles'] += 1
            if profile_report['modularity_applied']:
                report['summary']['modular_profiles'] += 1
            if profile_report['extensibility_applied']:
                report['summary']['extended_profiles'] += 1
            if profile_report['integration_applied']:
                report['summary']['integrated_profiles'] += 1
            if profile_report['automation_applied']:
                report['summary']['automated_profiles'] += 1
            
            report['profiles'].append(profile_report)
        
        return report
    
    async def optimize_camea_application(self) -> Dict[str, Any]:
        """Optimize the application of CAMEA principles based on usage patterns"""
        optimization_results = {
            'configurability_optimizations': [],
            'modularity_optimizations': [],
            'extensibility_optimizations': [],
            'integration_optimizations': [],
            'automation_optimizations': []
        }
        
        # Analyze configuration usage and suggest optimizations
        config_usage = {}
        for comp_id, config in self.configurability_system.configurations.items():
            for key, value in config.get('values', {}).items():
                config_key = f"{comp_id}:{key}"
                config_usage[config_key] = config_usage.get(config_key, 0) + 1
        
        # Identify frequently changed configurations
        for config_key, usage_count in config_usage.items():
            if usage_count > 10:  # Changed more than 10 times
                optimization_results['configurability_optimizations'].append({
                    'config_key': config_key,
                    'usage_count': usage_count,
                    'recommendation': 'Move to hot-config for runtime changes'
                })
        
        # Analyze module dependencies for optimization
        for module_name, deps in self.modularity_system.dependencies.items():
            if len(deps) > 5:  # Too many dependencies
                optimization_results['modularity_optimizations'].append({
                    'module': module_name,
                    'dependency_count': len(deps),
                    'recommendation': 'Consider breaking into smaller modules'
                })
        
        # Analyze extension usage
        ext_usage = {}
        for ext_id, ext_info in self.extensibility_system.extensions.items():
            # In a real system, we would track how often extensions are used
            ext_usage[ext_id] = 0  # Placeholder
        
        # Analyze integration patterns
        for service_name, service_info in self.integration_system.integrated_services.items():
            # In a real system, we would analyze usage patterns
            pass
        
        # Analyze automation rule effectiveness
        for rule_id, rule_info in self.automation_system.automated_rules.items():
            # In a real system, we would track how often rules fire
            pass
        
        # Log the optimization analysis
        if self.observer:
            self.observer.log_activity(
                ActivityType.DISTILLATION,
                "Performed CAMEA optimization analysis",
                metadata=optimization_results
            )
        
        return optimization_results


# Example usage
if __name__ == "__main__":
    import asyncio
    from graph_db import GraphDB
    from domain_profiles import DomainProfileRegistry
    from observability import ResearchObserver
    
    async def example_usage():
        # Create graph database
        graph = GraphDB()
        
        # Create observer
        observer = ResearchObserver(graph)
        
        # Create profile registry
        profile_registry = DomainProfileRegistry(graph, observer)
        
        # Create all required profiles
        system_owner = await profile_registry.create_profile(DomainProfileType.SYSTEM_OWNER)
        linguist = await profile_registry.create_profile(DomainProfileType.DOMAIN_LINGUIST)
        researcher = await profile_registry.create_profile(DomainProfileType.RESEARCHER)
        archivist = await profile_registry.create_profile(DomainProfileType.ARCHIVIST)
        analyst = await profile_registry.create_profile(DomainProfileType.ANALYST)
        synthesizer = await profile_registry.create_profile(DomainProfileType.SYNTHESIZER)
        validator = await profile_registry.create_profile(DomainProfileType.VALIDATOR)
        orchestrator = await profile_registry.create_profile(DomainProfileType.ORCHESTRATOR)
        navigator = await profile_registry.create_profile(DomainProfileType.NAVIGATOR)
        
        # Create CAMEA orchestrator
        camea_orchestrator = CAMEAOrchestrator(graph, profile_registry, observer)
        
        # Apply CAMEA principles to a specific profile (researcher)
        camea_result = await camea_orchestrator.apply_camea_to_profile(
            DomainProfileType.RESEARCHER,
            config={
                'discovery_depth': 3,
                'verification_required': True,
                'max_sources': 10
            },
            dependencies=['linguist', 'validator'],
            extensions=[
                {
                    'name': 'advanced_discovery',
                    'methods': {
                        'deep_discovery': lambda query: f"Deep discovery for {query}",
                        'cross_domain_analysis': lambda query: f"Cross-domain analysis for {query}"
                    }
                }
            ],
            integrations=[
                {
                    'service_name': 'external_research_api',
                    'api_endpoint': 'http://research-api.example.com/query',
                    'data_schema': {
                        'type': 'object',
                        'properties': {
                            'query': {'type': 'string'},
                            'filters': {'type': 'object'}
                        }
                    }
                }
            ],
            automations=[
                {
                    'rule_name': 'auto_verify_sources',
                    'condition': lambda ctx: ctx.get('source_reputation', 0) < 0.5,
                    'action': lambda ctx: print(f"Flagging low-reputation source: {ctx.get('source')}")
                }
            ]
        )
        
        print(f"CAMEA application result for researcher: {camea_result}")
        
        # Apply CAMEA principles to the entire system
        system_camea_result = await camea_orchestrator.apply_camea_to_system()
        print(f"System-wide CAMEA application: {system_camea_result}")
        
        # Get CAMEA compliance report
        compliance_report = await camea_orchestrator.get_camea_compliance_report()
        print(f"CAMEA compliance report: Profiles configured={compliance_report['summary']['configured_profiles']}/{compliance_report['summary']['total_profiles']}")
        
        # Perform optimization analysis
        optimization_results = await camea_orchestrator.optimize_camea_application()
        print(f"Optimization suggestions: {len(optimization_results['configurability_optimizations'])} configuration optimizations")
        
        print("CAMEA principles successfully applied to Domain Profile system!")
    
    # Run the example
    asyncio.run(example_usage())