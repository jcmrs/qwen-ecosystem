"""
Observability system for research activities
Implements tracking and monitoring for research processes
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum
import threading
import time
from graph_db import GraphDB, Node, Edge


class ActivityType(Enum):
    """Types of research activities that can be observed"""
    DISCOVERY = "discovery"
    INTEGRATION = "integration"
    VERIFICATION = "verification"
    CONNECTION = "connection"
    DISTILLATION = "distillation"
    ANALYSIS = "analysis"
    RETRIEVAL = "retrieval"


class ActivityLog:
    """Log entry for a research activity"""
    
    def __init__(self, activity_type: ActivityType, description: str, 
                 node_ids: List[str] = None, metadata: Dict[str, Any] = None):
        self.id = f"activity_{int(time.time() * 1000000)}"
        self.timestamp = datetime.now()
        self.activity_type = activity_type
        self.description = description
        self.node_ids = node_ids or []
        self.metadata = metadata or {}
        self.duration_ms = 0
        self.success = True
        self.error_message = None
    
    def start_timer(self):
        """Start timing the activity"""
        self.start_time = time.time()
    
    def end_timer(self, success: bool = True, error_message: str = None):
        """End timing the activity"""
        if hasattr(self, 'start_time'):
            self.duration_ms = int((time.time() - self.start_time) * 1000)
        self.success = success
        self.error_message = error_message
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert log entry to dictionary"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'activity_type': self.activity_type.value,
            'description': self.description,
            'node_ids': self.node_ids,
            'metadata': self.metadata,
            'duration_ms': self.duration_ms,
            'success': self.success,
            'error_message': self.error_message
        }


class ResearchObserver:
    """Main observability system for research activities"""
    
    def __init__(self, graph_db: GraphDB, log_file: str = "research_activity.log"):
        self.graph_db = graph_db
        self.log_file = log_file
        self.activity_logs: List[ActivityLog] = []
        self.lock = threading.Lock()
        self.metrics = {
            'total_activities': 0,
            'successful_activities': 0,
            'failed_activities': 0,
            'activity_types': {}
        }
        
        # Create log directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
    
    def log_activity(self, activity_type: ActivityType, description: str,
                     node_ids: List[str] = None, metadata: Dict[str, Any] = None) -> ActivityLog:
        """Log a research activity"""
        with self.lock:
            log_entry = ActivityLog(activity_type, description, node_ids, metadata)
            log_entry.start_timer()
            
            # Add to in-memory logs
            self.activity_logs.append(log_entry)
            
            # Update metrics
            self.metrics['total_activities'] += 1
            activity_type_str = activity_type.value
            self.metrics['activity_types'][activity_type_str] = \
                self.metrics['activity_types'].get(activity_type_str, 0) + 1
            
            return log_entry
    
    def complete_activity(self, log_entry: ActivityLog, success: bool = True, 
                         error_message: str = None):
        """Complete an activity log entry"""
        with self.lock:
            log_entry.end_timer(success, error_message)
            
            # Update metrics
            if success:
                self.metrics['successful_activities'] += 1
            else:
                self.metrics['failed_activities'] += 1
            
            # Write to log file
            self._write_log_entry(log_entry)
    
    def _write_log_entry(self, log_entry: ActivityLog):
        """Write a log entry to the log file"""
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry.to_dict()) + '\n')
    
    def get_recent_activities(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent activity logs"""
        with self.lock:
            recent_logs = self.activity_logs[-limit:]
            return [log.to_dict() for log in recent_logs]
    
    def get_activities_by_type(self, activity_type: ActivityType) -> List[Dict[str, Any]]:
        """Get activities of a specific type"""
        with self.lock:
            filtered_logs = [log for log in self.activity_logs 
                           if log.activity_type == activity_type]
            return [log.to_dict() for log in filtered_logs]
    
    def get_activities_by_node(self, node_id: str) -> List[Dict[str, Any]]:
        """Get activities related to a specific node"""
        with self.lock:
            filtered_logs = [log for log in self.activity_logs 
                           if node_id in log.node_ids]
            return [log.to_dict() for log in filtered_logs]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get observability metrics"""
        with self.lock:
            metrics = self.metrics.copy()
            
            # Add calculated metrics
            if metrics['total_activities'] > 0:
                metrics['success_rate'] = metrics['successful_activities'] / metrics['total_activities']
            else:
                metrics['success_rate'] = 0.0
            
            # Add timing metrics
            successful_logs = [log for log in self.activity_logs if log.success]
            if successful_logs:
                avg_duration = sum(log.duration_ms for log in successful_logs) / len(successful_logs)
                metrics['avg_duration_ms'] = avg_duration
                metrics['total_duration_ms'] = sum(log.duration_ms for log in successful_logs)
            else:
                metrics['avg_duration_ms'] = 0
                metrics['total_duration_ms'] = 0
            
            return metrics
    
    def search_activities(self, query: str = None, start_time: datetime = None, 
                         end_time: datetime = None) -> List[Dict[str, Any]]:
        """Search activities by query and time range"""
        with self.lock:
            results = []
            
            for log in self.activity_logs:
                # Time range filter
                if start_time and log.timestamp < start_time:
                    continue
                if end_time and log.timestamp > end_time:
                    continue
                
                # Query filter
                if query:
                    query_lower = query.lower()
                    if (query_lower in log.description.lower() or
                        query_lower in log.activity_type.value.lower() or
                        any(query_lower in str(meta_val).lower() 
                            for meta_val in log.metadata.values())):
                        results.append(log)
                else:
                    results.append(log)
            
            return [log.to_dict() for log in results]


class ObservableResearchComponent:
    """Mixin class to add observability to research components"""
    
    def __init__(self, observer: ResearchObserver):
        self.observer = observer
    
    def _log_activity(self, activity_type: ActivityType, description: str,
                     node_ids: List[str] = None, metadata: Dict[str, Any] = None) -> ActivityLog:
        """Log an activity using the observer"""
        return self.observer.log_activity(activity_type, description, node_ids, metadata)
    
    def _complete_activity(self, log_entry: ActivityLog, success: bool = True, 
                          error_message: str = None):
        """Complete an activity log"""
        self.observer.complete_activity(log_entry, success, error_message)


class ObservableDiscoveryEngine(ObservableResearchComponent):
    """Observable version of the discovery engine"""
    
    def __init__(self, graph_db: GraphDB, observer: ResearchObserver):
        super().__init__(observer)
        self.graph_db = graph_db
    
    def discover_from_web(self, seed_url: str, max_pages: int = 10) -> List[Dict]:
        """Discover information with observability"""
        log_entry = self._log_activity(
            ActivityType.DISCOVERY,
            f"Starting web discovery from {seed_url}",
            metadata={'seed_url': seed_url, 'max_pages': max_pages}
        )
        
        try:
            # This would implement the actual discovery logic
            # For now, we'll simulate the process
            discovered_urls = []
            
            # Simulate discovery process
            for i in range(min(max_pages, 3)):  # Limit for demo
                url = f"{seed_url}/page{i+1}"
                title = f"Page {i+1} Title"
                
                # Create node for this page
                page_node = Node(
                    node_type='web_resource',
                    content=f"Content of {url}",
                    metadata={'url': url, 'title': title}
                )
                node_id = self.graph_db.add_node(page_node)
                
                discovered_urls.append({
                    'url': url,
                    'title': title,
                    'node_id': node_id
                })
            
            self._complete_activity(log_entry, success=True)
            
            # Log each discovery
            for item in discovered_urls:
                discovery_log = self._log_activity(
                    ActivityType.DISCOVERY,
                    f"Discovered web resource: {item['title']}",
                    node_ids=[item['node_id']],
                    metadata={'url': item['url']}
                )
                self._complete_activity(discovery_log, success=True)
            
            return discovered_urls
            
        except Exception as e:
            self._complete_activity(log_entry, success=False, error_message=str(e))
            raise


class ObservableSourceIntegrator(ObservableResearchComponent):
    """Observable version of the source integrator"""
    
    def __init__(self, graph_db: GraphDB, observer: ResearchComponent):
        super().__init__(observer)
        self.graph_db = graph_db
    
    def integrate_source(self, source_data: Dict[str, Any]) -> Optional[str]:
        """Integrate a source with observability"""
        log_entry = self._log_activity(
            ActivityType.INTEGRATION,
            f"Integrating source: {source_data.get('title', 'Unknown')}",
            metadata={'source_type': source_data.get('type', 'unknown')}
        )
        
        try:
            # Create node
            node = Node(
                node_type='research_material',
                content=source_data.get('content', ''),
                metadata=source_data
            )
            node_id = self.graph_db.add_node(node)
            
            self._complete_activity(log_entry, success=True)
            
            # Log the successful integration
            integration_log = self._log_activity(
                ActivityType.INTEGRATION,
                f"Successfully integrated source",
                node_ids=[node_id],
                metadata={'node_id': node_id}
            )
            self._complete_activity(integration_log, success=True)
            
            return node_id
            
        except Exception as e:
            self._complete_activity(log_entry, success=False, error_message=str(e))
            raise


class ObservableConnectionMapper(ObservableResearchComponent):
    """Observable version of the connection mapper"""
    
    def __init__(self, graph_db: GraphDB, observer: ResearchObserver):
        super().__init__(observer)
        self.graph_db = graph_db
    
    def find_pathways(self, start_node_id: str, end_node_id: str, 
                     max_hops: int = 5) -> List[List[str]]:
        """Find pathways with observability"""
        log_entry = self._log_activity(
            ActivityType.CONNECTION,
            f"Finding pathways from {start_node_id} to {end_node_id}",
            node_ids=[start_node_id, end_node_id],
            metadata={'max_hops': max_hops}
        )
        
        try:
            # This would implement the actual pathway finding
            # For now, we'll simulate the process
            pathways = [[start_node_id, end_node_id]]  # Simple direct path for demo
            
            self._complete_activity(log_entry, success=True)
            
            # Log the discovery of pathways
            if pathways:
                pathway_log = self._log_activity(
                    ActivityType.CONNECTION,
                    f"Found {len(pathways)} pathways between nodes",
                    node_ids=[start_node_id, end_node_id],
                    metadata={'pathway_count': len(pathways)}
                )
                self._complete_activity(pathway_log, success=True)
            
            return pathways
            
        except Exception as e:
            self._complete_activity(log_entry, success=False, error_message=str(e))
            raise


# Example usage
if __name__ == "__main__":
    from graph_db import GraphDB
    
    # Create a graph database instance
    graph = GraphDB()
    
    # Create an observer
    observer = ResearchObserver(graph, "test_research_activity.log")
    
    # Example: Log some activities
    log1 = observer.log_activity(
        ActivityType.DISCOVERY,
        "Discovered new research paper",
        node_ids=["node1", "node2"],
        metadata={"source": "arxiv", "topic": "AI"}
    )
    observer.complete_activity(log1)
    
    log2 = observer.log_activity(
        ActivityType.INTEGRATION,
        "Integrated source into knowledge graph",
        node_ids=["node3"],
        metadata={"source_type": "web", "trust_score": 0.85}
    )
    observer.complete_activity(log2, success=False, error_message="Failed to parse content")
    
    # Get metrics
    metrics = observer.get_metrics()
    print("Observability Metrics:")
    print(f"Total activities: {metrics['total_activities']}")
    print(f"Success rate: {metrics['success_rate']:.2%}")
    print(f"Activity types: {metrics['activity_types']}")
    
    # Get recent activities
    recent = observer.get_recent_activities()
    print(f"\nRecent activities: {len(recent)}")
    
    # Search activities
    search_results = observer.search_activities("discovered")
    print(f"Search results: {len(search_results)}")