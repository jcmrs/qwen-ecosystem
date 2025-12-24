"""
Cross-phase feedback loops
Implements feedback mechanisms between research and distillation phases
"""

from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from enum import Enum
import threading
import time
from graph_db import GraphDB, Node, Edge
from discovery import DiscoveryEngine
from knowledge_distillation import KnowledgeDistiller
from wisdom_extraction import WisdomExtractorSystem
from quality_control import QualityControlSystem
from automated_workflows import AutomatedResearchSystem
from observability import ResearchObserver, ActivityType


class FeedbackType(Enum):
    """Types of feedback that can be exchanged between phases"""
    RELEVANCE_FEEDBACK = "relevance_feedback"
    QUALITY_FEEDBACK = "quality_feedback"
    COMPLETENESS_FEEDBACK = "completeness_feedback"
    ACCURACY_FEEDBACK = "accuracy_feedback"
    TOPIC_REFINEMENT = "topic_refinement"
    SOURCE_SUGGESTION = "source_suggestion"


class FeedbackSignal:
    """A signal containing feedback information between phases"""
    
    def __init__(self, feedback_type: FeedbackType, 
                 source_phase: str,
                 target_phase: str,
                 content: str,
                 node_ids: List[str] = None,
                 confidence: float = 0.5,
                 metadata: Dict[str, Any] = None):
        self.id = f"feedback_{int(datetime.now().timestamp() * 1000000)}"
        self.feedback_type = feedback_type
        self.source_phase = source_phase
        self.target_phase = target_phase
        self.content = content
        self.node_ids = node_ids or []
        self.confidence = confidence
        self.metadata = metadata or {}
        self.timestamp = datetime.now()
        self.processed = False
        self.processed_at = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'id': self.id,
            'feedback_type': self.feedback_type.value,
            'source_phase': self.source_phase,
            'target_phase': self.target_phase,
            'content': self.content,
            'node_ids': self.node_ids,
            'confidence': self.confidence,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat(),
            'processed': self.processed,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None
        }


class FeedbackProcessor:
    """Processes feedback signals between research and distillation phases"""
    
    def __init__(self, graph_db: GraphDB, observer: ResearchObserver = None):
        self.graph_db = graph_db
        self.observer = observer
        self.feedback_queue = []
        self.feedback_handlers = {}
        self.lock = threading.Lock()
    
    def register_feedback_handler(self, feedback_type: FeedbackType, handler: Callable):
        """Register a handler for a specific feedback type"""
        self.feedback_handlers[feedback_type] = handler
    
    def send_feedback(self, feedback: FeedbackSignal):
        """Send a feedback signal to be processed"""
        with self.lock:
            self.feedback_queue.append(feedback)
        
        # Log the feedback
        if self.observer:
            self.observer.log_activity(
                ActivityType.DISTILLATION,
                f"Feedback sent from {feedback.source_phase} to {feedback.target_phase}: {feedback.feedback_type.value}",
                node_ids=feedback.node_ids,
                metadata=feedback.to_dict()
            )
    
    def process_feedback(self) -> int:
        """Process all pending feedback signals"""
        processed_count = 0
        
        with self.lock:
            unprocessed_feedback = [f for f in self.feedback_queue if not f.processed]
            self.feedback_queue = [f for f in self.feedback_queue if f.processed]
        
        for feedback in unprocessed_feedback:
            try:
                # Find appropriate handler
                handler = self.feedback_handlers.get(feedback.feedback_type)
                
                if handler:
                    # Process the feedback
                    handler_result = handler(feedback)
                    
                    # Mark as processed
                    feedback.processed = True
                    feedback.processed_at = datetime.now()
                    
                    processed_count += 1
                    
                    # Log successful processing
                    if self.observer:
                        self.observer.log_activity(
                            ActivityType.DISTILLATION,
                            f"Feedback processed: {feedback.feedback_type.value}",
                            node_ids=feedback.node_ids,
                            metadata={'result': str(handler_result)}
                        )
                else:
                    # No handler for this feedback type
                    print(f"No handler for feedback type: {feedback.feedback_type.value}")
                    
            except Exception as e:
                # Log processing error
                if self.observer:
                    self.observer.log_activity(
                        ActivityType.DISTILLATION,
                        f"Error processing feedback: {str(e)}",
                        node_ids=feedback.node_ids,
                        metadata={'feedback_id': feedback.id, 'error': str(e)}
                    )
        
        return processed_count
    
    def get_feedback_stats(self) -> Dict[str, Any]:
        """Get statistics about feedback processing"""
        with self.lock:
            total_feedback = len(self.feedback_queue)
            unprocessed = len([f for f in self.feedback_queue if not f.processed])
            
        return {
            'total_feedback': total_feedback,
            'unprocessed': unprocessed,
            'processed': total_feedback - unprocessed,
            'handlers_registered': len(self.feedback_handlers)
        }


class CrossPhaseFeedbackSystem:
    """Main system for managing feedback between research and distillation phases"""
    
    def __init__(self, graph_db: GraphDB, observer: ResearchObserver = None):
        self.graph_db = graph_db
        self.observer = observer
        self.feedback_processor = FeedbackProcessor(graph_db, observer)
        
        # Initialize phase-specific components
        self.discovery_engine = DiscoveryEngine(graph_db)
        self.knowledge_distiller = KnowledgeDistiller(graph_db, observer)
        self.wisdom_extractor = WisdomExtractorSystem(graph_db, observer)
        self.quality_control = QualityControlSystem(graph_db, observer)
        
        # Register feedback handlers
        self._register_feedback_handlers()
    
    def _register_feedback_handlers(self):
        """Register handlers for different feedback types"""
        self.feedback_processor.register_feedback_handler(
            FeedbackType.RELEVANCE_FEEDBACK, 
            self._handle_relevance_feedback
        )
        self.feedback_processor.register_feedback_handler(
            FeedbackType.QUALITY_FEEDBACK,
            self._handle_quality_feedback
        )
        self.feedback_processor.register_feedback_handler(
            FeedbackType.COMPLETENESS_FEEDBACK,
            self._handle_completeness_feedback
        )
        self.feedback_processor.register_feedback_handler(
            FeedbackType.TOPIC_REFINEMENT,
            self._handle_topic_refinement
        )
        self.feedback_processor.register_feedback_handler(
            FeedbackType.SOURCE_SUGGESTION,
            self._handle_source_suggestion
        )
    
    def _handle_relevance_feedback(self, feedback: FeedbackSignal):
        """Handle relevance feedback from distillation to research"""
        # Use relevance feedback to improve discovery parameters
        node_ids = feedback.node_ids
        feedback_content = feedback.content
        
        # Example: Adjust future discovery based on relevance feedback
        for node_id in node_ids:
            node = self.graph_db.get_node(node_id)
            if node:
                # Update node metadata with relevance information
                node.metadata['relevance_feedback'] = feedback_content
                node.metadata['last_relevance_update'] = datetime.now().isoformat()
    
    def _handle_quality_feedback(self, feedback: FeedbackSignal):
        """Handle quality feedback from distillation to research"""
        # Use quality feedback to improve source verification
        node_ids = feedback.node_ids
        confidence = feedback.confidence
        
        for node_id in node_ids:
            node = self.graph_db.get_node(node_id)
            if node and 'verification' in node.metadata:
                # Adjust verification scores based on quality feedback
                verification = node.metadata['verification']
                current_score = verification.get('overall_trust_score', 0.5)
                adjusted_score = (current_score + confidence) / 2
                verification['overall_trust_score'] = adjusted_score
                node.metadata['quality_adjusted_trust'] = adjusted_score
    
    def _handle_completeness_feedback(self, feedback: FeedbackSignal):
        """Handle completeness feedback from distillation to research"""
        # Use completeness feedback to identify missing information
        feedback_content = feedback.content
        
        # This could trigger new discovery tasks to fill gaps
        # For now, we'll just log it as a potential area for future research
        print(f"Completeness feedback received: {feedback_content}")
    
    def _handle_topic_refinement(self, feedback: FeedbackSignal):
        """Handle topic refinement feedback from distillation to research"""
        # Use topic refinement feedback to improve future research focus
        topic_refinement = feedback.content
        print(f"Topic refinement suggestion: {topic_refinement}")
        
        # This could be used to adjust research parameters or focus areas
        # For example, updating a list of subtopics to explore
    
    def _handle_source_suggestion(self, feedback: FeedbackSignal):
        """Handle source suggestion feedback from distillation to research"""
        # Use source suggestions to improve discovery
        source_suggestion = feedback.content
        print(f"Source suggestion: {source_suggestion}")
        
        # This could trigger new discovery from the suggested source
        # For example, adding the source to a queue for future exploration
    
    def generate_relevance_feedback(self, research_nodes: List[Node], 
                                  distillation_result: Dict[str, Any]) -> List[FeedbackSignal]:
        """Generate relevance feedback from distillation results"""
        feedback_signals = []
        
        for node in research_nodes:
            # Determine relevance based on how much the node contributed to distillation
            contributed = distillation_result.get('created_from', {}).get(node.id, False)
            
            if contributed:
                feedback = FeedbackSignal(
                    feedback_type=FeedbackType.RELEVANCE_FEEDBACK,
                    source_phase='distillation',
                    target_phase='research',
                    content=f"Node {node.id} was highly relevant to distillation process",
                    node_ids=[node.id],
                    confidence=0.9,
                    metadata={'contribution_level': 'high'}
                )
                feedback_signals.append(feedback)
        
        return feedback_signals
    
    def generate_quality_feedback(self, knowledge_nodes: List[Node]) -> List[FeedbackSignal]:
        """Generate quality feedback from knowledge assessment"""
        feedback_signals = []
        
        for node in knowledge_nodes:
            confidence = node.metadata.get('confidence', 0.5)
            
            feedback = FeedbackSignal(
                feedback_type=FeedbackType.QUALITY_FEEDBACK,
                source_phase='distillation',
                target_phase='research',
                content=f"Knowledge node {node.id} has confidence score {confidence}",
                node_ids=[node.id],
                confidence=confidence,
                metadata={'quality_score': confidence}
            )
            feedback_signals.append(feedback)
        
        return feedback_signals
    
    def generate_completeness_feedback(self, distillation_input: List[str], 
                                     distillation_output: List[str]) -> List[FeedbackSignal]:
        """Generate completeness feedback based on input/output analysis"""
        feedback_signals = []
        
        input_count = len(distillation_input)
        output_count = len(distillation_output)
        
        if input_count > 0:
            completeness_ratio = output_count / input_count
            
            feedback = FeedbackSignal(
                feedback_type=FeedbackType.COMPLETENESS_FEEDBACK,
                source_phase='distillation',
                target_phase='research',
                content=f"Distillation completeness ratio: {completeness_ratio:.2f}",
                node_ids=distillation_input,
                confidence=completeness_ratio,
                metadata={'input_count': input_count, 'output_count': output_count}
            )
            feedback_signals.append(feedback)
        
        return feedback_signals
    
    def process_pending_feedback(self) -> int:
        """Process all pending feedback signals"""
        return self.feedback_processor.process_feedback()
    
    def get_feedback_stats(self) -> Dict[str, Any]:
        """Get feedback system statistics"""
        return self.feedback_processor.get_feedback_stats()


class AdaptiveResearchSystem:
    """Research system that adapts based on feedback from distillation"""
    
    def __init__(self, graph_db: GraphDB, feedback_system: CrossPhaseFeedbackSystem, 
                 observer: ResearchObserver = None):
        self.graph_db = graph_db
        self.feedback_system = feedback_system
        self.observer = observer
        self.discovery_engine = DiscoveryEngine(graph_db)
        self.automatic_research = AutomatedResearchSystem(graph_db, observer)
        
        # Adaptive parameters that can be adjusted based on feedback
        self.discovery_params = {
            'max_pages': 5,
            'depth': 2,
            'relevance_threshold': 0.6,
            'quality_threshold': 0.7
        }
    
    def adapt_to_feedback(self):
        """Adapt research parameters based on feedback"""
        # Get feedback statistics
        stats = self.feedback_system.get_feedback_stats()
        
        # Process any pending feedback
        processed = self.feedback_system.process_pending_feedback()
        
        # Adjust parameters based on feedback patterns
        # This is a simplified example - in practice, this would be more sophisticated
        feedback_signals = self._get_recent_feedback()
        
        for signal in feedback_signals:
            if signal.feedback_type == FeedbackType.RELEVANCE_FEEDBACK:
                if signal.confidence < 0.5:
                    # Low relevance feedback suggests we need to refine our discovery
                    self.discovery_params['relevance_threshold'] += 0.05
            elif signal.feedback_type == FeedbackType.QUALITY_FEEDBACK:
                if signal.confidence < 0.7:
                    # Low quality feedback suggests we need better sources
                    self.discovery_params['quality_threshold'] += 0.05
    
    def _get_recent_feedback(self) -> List[FeedbackSignal]:
        """Get recent feedback signals (simplified implementation)"""
        # In a real implementation, this would query a persistent feedback store
        # For now, we'll return an empty list
        return []
    
    def conduct_adaptive_research(self, topic: str) -> Dict[str, Any]:
        """Conduct research with parameters adapted to feedback"""
        # Adapt parameters based on feedback
        self.adapt_to_feedback()
        
        # Log the adaptive research
        if self.observer:
            self.observer.log_activity(
                ActivityType.DISTILLATION,
                f"Conducting adaptive research on '{topic}' with params: {self.discovery_params}",
                metadata={'topic': topic, 'params': self.discovery_params}
            )
        
        # Perform research using the adaptive parameters
        # This would integrate with the discovery engine using the adjusted parameters
        result = {
            'topic': topic,
            'parameters_used': self.discovery_params,
            'research_started': datetime.now().isoformat()
        }
        
        return result


class AdaptiveDistillationSystem:
    """Distillation system that adapts based on feedback from research"""
    
    def __init__(self, graph_db: GraphDB, feedback_system: CrossPhaseFeedbackSystem,
                 observer: ResearchObserver = None):
        self.graph_db = graph_db
        self.feedback_system = feedback_system
        self.observer = observer
        self.knowledge_distiller = KnowledgeDistiller(graph_db, observer)
        self.wisdom_extractor = WisdomExtractorSystem(graph_db, observer)
        
        # Adaptive parameters for distillation
        self.distillation_params = {
            'validation_required': True,
            'confidence_threshold': 0.7,
            'synthesis_depth': 2
        }
    
    def adapt_to_research_feedback(self):
        """Adapt distillation parameters based on research feedback"""
        # Process any pending feedback
        processed = self.feedback_system.process_pending_feedback()
        
        # Adjust parameters based on feedback patterns
        # This is a simplified example
        feedback_signals = self._get_recent_feedback()
        
        for signal in feedback_signals:
            if signal.feedback_type == FeedbackType.SOURCE_SUGGESTION:
                # If research is suggesting new sources, we might want to be more exploratory
                self.distillation_params['synthesis_depth'] = min(5, self.distillation_params['synthesis_depth'] + 1)
            elif signal.feedback_type == FeedbackType.COMPLETENESS_FEEDBACK:
                # Adjust based on completeness feedback
                if signal.confidence < 0.6:
                    self.distillation_params['confidence_threshold'] -= 0.05
                else:
                    self.distillation_params['confidence_threshold'] += 0.05
    
    def _get_recent_feedback(self) -> List[FeedbackSignal]:
        """Get recent feedback signals (simplified implementation)"""
        return []
    
    def conduct_adaptive_distillation(self, source_node_ids: List[str]) -> Dict[str, Any]:
        """Conduct distillation with parameters adapted to research feedback"""
        # Adapt parameters based on feedback
        self.adapt_to_research_feedback()
        
        # Log the adaptive distillation
        if self.observer:
            self.observer.log_activity(
                ActivityType.DISTILLATION,
                f"Conducting adaptive distillation with params: {self.distillation_params}",
                node_ids=source_node_ids,
                metadata={'params': self.distillation_params}
            )
        
        # Perform distillation using the adjusted parameters
        knowledge_ids = self.knowledge_distiller.distill_knowledge(
            source_node_ids, 
            validation_required=self.distillation_params['validation_required']
        )
        
        result = {
            'knowledge_nodes_created': knowledge_ids,
            'parameters_used': self.distillation_params,
            'distillation_started': datetime.now().isoformat()
        }
        
        return result


class FeedbackLoopManager:
    """Main manager for cross-phase feedback loops"""
    
    def __init__(self, graph_db: GraphDB, observer: ResearchObserver = None):
        self.graph_db = graph_db
        self.observer = observer
        
        # Create the feedback system
        self.feedback_system = CrossPhaseFeedbackSystem(graph_db, observer)
        
        # Create adaptive systems
        self.adaptive_research = AdaptiveResearchSystem(graph_db, self.feedback_system, observer)
        self.adaptive_distillation = AdaptiveDistillationSystem(graph_db, self.feedback_system, observer)
    
    def run_feedback_cycle(self, topic: str, initial_source_ids: List[str] = None) -> Dict[str, Any]:
        """Run a complete feedback cycle between research and distillation"""
        cycle_result = {
            'topic': topic,
            'feedback_processed': 0,
            'research_result': None,
            'distillation_result': None,
            'cycle_started': datetime.now().isoformat()
        }
        
        # Start with research
        research_result = self.adaptive_research.conduct_adaptive_research(topic)
        cycle_result['research_result'] = research_result
        
        # Then distillation
        if initial_source_ids:
            distillation_result = self.adaptive_distillation.conduct_adaptive_distillation(initial_source_ids)
            cycle_result['distillation_result'] = distillation_result
        
        # Process any feedback generated during the cycle
        feedback_processed = self.feedback_system.process_pending_feedback()
        cycle_result['feedback_processed'] = feedback_processed
        
        # Log the feedback cycle
        if self.observer:
            self.observer.log_activity(
                ActivityType.DISTILLATION,
                f"Completed feedback cycle for topic '{topic}'",
                metadata=cycle_result
            )
        
        return cycle_result
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get status of the feedback loop system"""
        return {
            'feedback_system_stats': self.feedback_system.get_feedback_stats(),
            'research_params': self.adaptive_research.discovery_params,
            'distillation_params': self.adaptive_distillation.distillation_params,
            'graph_stats': {
                'nodes': len(self.graph_db.nodes),
                'edges': len(self.graph_db.edges)
            }
        }


# Example usage
if __name__ == "__main__":
    from graph_db import GraphDB
    from observability import ResearchObserver
    
    # Create a graph database instance
    graph = GraphDB()
    
    # Create observer
    observer = ResearchObserver(graph)
    
    # Add some initial nodes for testing
    initial_node = Node(
        node_type="research_material",
        content="Artificial intelligence research overview",
        metadata={"url": "https://example.com/ai", "title": "AI Research"}
    )
    initial_node_id = graph.add_node(initial_node)
    
    # Create feedback loop manager
    feedback_manager = FeedbackLoopManager(graph, observer)
    
    # Run a feedback cycle
    result = feedback_manager.run_feedback_cycle(
        "artificial intelligence", 
        [initial_node_id]
    )
    
    print(f"Feedback cycle completed: {result['feedback_processed']} feedback items processed")
    
    # Get system status
    status = feedback_manager.get_system_status()
    print(f"System status: {status}")
    
    # Show feedback statistics
    print(f"Feedback stats: {status['feedback_system_stats']}")