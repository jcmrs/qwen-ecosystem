"""
UTCP Agent - Intelligent orchestration for the ecosystem
Implements the agent that intelligently selects and orchestrates tools
"""

from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime
import asyncio
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field
from utcp.utcp_client import UtcpClient
from utcp.data.utcp_client_config import UtcpClientConfig
import json


class UtcpAgentState(BaseModel):
    """State for the UTCP agent"""
    messages: List[BaseMessage]
    current_task: str = ""
    selected_tools: List[str] = Field(default_factory=list)
    tool_results: List[Dict[str, Any]] = Field(default_factory=list)
    final_response: str = ""


class UtcpToolAdapter(BaseTool):
    """Adapter to make UTCP tools compatible with LangChain"""
    
    name: str = "utcp_tool"
    description: str = "A tool from the UTCP ecosystem"
    utcp_client: UtcpClient
    tool_name: str
    
    def _run(self, **kwargs: Any) -> str:
        """Synchronous run method - not recommended for async operations"""
        raise NotImplementedError("Use _arun instead")
    
    async def _arun(self, **kwargs: Any) -> str:
        """Asynchronous run method for UTCP tool"""
        try:
            result = await self.utcp_client.call_tool(self.tool_name, kwargs)
            return json.dumps(result, ensure_ascii=False)
        except Exception as e:
            return f"Error calling tool {self.tool_name}: {str(e)}"


class UtcpAgentConfig(BaseModel):
    """Configuration for the UTCP agent"""
    max_iterations: int = 3
    max_tools_per_search: int = 10
    system_prompt: str = "You are a helpful AI assistant with access to various tools through UTCP."
    checkpointer: Optional[MemorySaver] = None
    callbacks: Optional[List] = Field(default_factory=list)
    summarize_threshold: int = 80000  # Token count threshold for context summarization


class UtcpAgent:
    """Intelligent agent for UTCP ecosystem tool orchestration"""
    
    def __init__(self, llm, utcp_client: UtcpClient, config: UtcpAgentConfig = None):
        self.llm = llm
        self.utcp_client = utcp_client
        self.config = config or UtcpAgentConfig()
        self.graph = None
        self.executor = None
        
        # Initialize the agent
        asyncio.run(self._initialize_agent())
    
    @classmethod
    async def create(cls, llm, utcp_config: Dict[str, Any] = None, 
                    agent_config: UtcpAgentConfig = None, root_dir: str = None):
        """Create a new UTCP agent instance"""
        # Create UTCP client
        client_config = UtcpClientConfig(**utcp_config) if utcp_config else None
        utcp_client = await UtcpClient.create(root_dir=root_dir, config=client_config)
        
        # Create agent instance
        agent = cls(llm, utcp_client, agent_config)
        return agent
    
    async def _initialize_agent(self):
        """Initialize the agent graph and executor"""
        # Create the graph
        workflow = StateGraph(UtcpAgentState)
        
        # Add nodes
        workflow.add_node("analyze_task", self._analyze_task)
        workflow.add_node("search_tools", self._search_tools)
        workflow.add_node("execute_tools", self._execute_tools)
        workflow.add_node("respond", self._respond)
        
        # Set entry point
        workflow.set_entry_point("analyze_task")
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "analyze_task",
            self._route_after_analysis,
            {
                "search": "search_tools",
                "respond": "respond"
            }
        )
        
        workflow.add_conditional_edges(
            "search_tools",
            self._route_after_search,
            {
                "execute": "execute_tools",
                "respond": "respond"
            }
        )
        
        workflow.add_conditional_edges(
            "execute_tools",
            self._route_after_execution,
            {
                "continue": "analyze_task",  # Continue the cycle if more analysis is needed
                "respond": "respond"
            }
        )
        
        workflow.add_edge("respond", END)
        
        # Compile the graph
        self.graph = workflow.compile(checkpointer=self.config.checkpointer)
    
    async def _analyze_task(self, state: UtcpAgentState) -> Dict[str, Any]:
        """Analyze the current task based on user input"""
        # Get the latest user message
        last_message = state.messages[-1] if state.messages else None
        if last_message:
            current_task = str(last_message.content)
        else:
            current_task = state.current_task or "No specific task provided"
        
        # Update state
        return {
            "current_task": current_task,
            "messages": state.messages  # Pass through messages
        }
    
    async def _search_tools(self, state: UtcpAgentState) -> Dict[str, Any]:
        """Search for relevant tools based on the current task"""
        try:
            # Search for tools relevant to the current task
            tools = await self.utcp_client.search_tools(
                query=state.current_task,
                limit=self.config.max_tools_per_search
            )
            
            # Get tool names
            tool_names = [tool.name for tool in tools]
            
            return {
                "selected_tools": tool_names,
                "messages": state.messages
            }
        except Exception as e:
            print(f"Error searching for tools: {e}")
            return {
                "selected_tools": [],
                "messages": state.messages
            }
    
    async def _execute_tools(self, state: UtcpAgentState) -> Dict[str, Any]:
        """Execute selected tools with appropriate arguments"""
        results = []
        
        for tool_name in state.selected_tools:
            try:
                # In a real implementation, we would determine the appropriate
                # arguments based on the current task and context
                # For now, we'll use a simple approach
                args = self._determine_tool_args(tool_name, state.current_task)
                
                result = await self.utcp_client.call_tool(tool_name, args)
                
                results.append({
                    "tool_name": tool_name,
                    "arguments": args,
                    "result": result,
                    "executed_at": datetime.now().isoformat()
                })
            except Exception as e:
                results.append({
                    "tool_name": tool_name,
                    "arguments": {},
                    "result": f"Error executing tool: {str(e)}",
                    "executed_at": datetime.now().isoformat()
                })
        
        return {
            "tool_results": results,
            "messages": state.messages
        }
    
    def _determine_tool_args(self, tool_name: str, task: str) -> Dict[str, Any]:
        """Determine appropriate arguments for a tool based on the task"""
        # This is a simplified implementation
        # In a real system, this would involve more sophisticated NLP
        # to extract relevant parameters from the task
        
        # Example: If we know the research tool expects a "query" parameter
        if "research" in tool_name.lower() or "search" in tool_name.lower():
            return {"query": task}
        
        # Default: return the task as a generic parameter
        return {"task": task}
    
    async def _respond(self, state: UtcpAgentState) -> Dict[str, Any]:
        """Generate a response based on tool results"""
        # Create a response based on the tool results
        if state.tool_results:
            # Format the results into a coherent response
            response_parts = []
            response_parts.append(f"I've completed the requested task: '{state.current_task}'")
            response_parts.append("")
            
            for result in state.tool_results:
                response_parts.append(f"Tool: {result['tool_name']}")
                response_parts.append(f"Result: {json.dumps(result['result'], indent=2)[:500]}...")  # Truncate long results
                response_parts.append("")
            
            final_response = "\n".join(response_parts)
        else:
            final_response = f"I analyzed your request about '{state.current_task}' but didn't find any tools to execute."
        
        return {
            "final_response": final_response,
            "messages": state.messages
        }
    
    def _route_after_analysis(self, state: UtcpAgentState) -> str:
        """Determine next step after task analysis"""
        # If we have tools to search for, go to search_tools
        # Otherwise, go directly to respond
        if state.current_task.strip():
            return "search"
        else:
            return "respond"
    
    def _route_after_search(self, state: UtcpAgentState) -> str:
        """Determine next step after tool search"""
        # If we found tools, execute them
        # Otherwise, respond without tool execution
        if state.selected_tools:
            return "execute"
        else:
            return "respond"
    
    def _route_after_execution(self, state: UtcpAgentState) -> str:
        """Determine next step after tool execution"""
        # For simplicity, we'll just respond after execution
        # In a more complex system, we might continue the cycle
        # if the results indicate more analysis is needed
        return "respond"
    
    async def chat(self, user_input: str, thread_id: Optional[str] = None) -> str:
        """Process user input and return agent response"""
        # Create initial state
        initial_state = {
            "messages": [{"role": "user", "content": user_input}],
            "current_task": user_input,
            "selected_tools": [],
            "tool_results": [],
            "final_response": ""
        }
        
        # Prepare config
        config = {"configurable": {"thread_id": thread_id}} if thread_id else {}
        
        # Run the graph
        result = await self.graph.ainvoke(initial_state, config=config)
        
        return result.get("final_response", "I couldn't process your request.")
    
    async def stream(self, user_input: str, thread_id: Optional[str] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream the workflow execution steps"""
        # Create initial state
        initial_state = {
            "messages": [{"role": "user", "content": user_input}],
            "current_task": user_input,
            "selected_tools": [],
            "tool_results": [],
            "final_response": ""
        }
        
        # Prepare config
        config = {"configurable": {"thread_id": thread_id}} if thread_id else {}
        
        # Stream the graph execution
        async for chunk in self.graph.astream(initial_state, config=config):
            yield chunk


# Example usage function
async def example_usage():
    """Example of how to use the UTCP Agent"""
    import os
    
    # Initialize LLM (using OpenAI as an example)
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # UTCP configuration
    utcp_config = {
        "manual_call_templates": [{
            "name": "example_research",
            "call_template_type": "http",
            "http_method": "POST",
            "url": "http://localhost:8001/research",  # Research tool endpoint
            "content_type": "application/json"
        }]
    }
    
    # Create agent
    agent = await UtcpAgent.create(
        llm=llm,
        utcp_config=utcp_config,
        agent_config=UtcpAgentConfig(
            system_prompt="You are a research assistant with access to various research tools."
        )
    )
    
    # Chat with the agent
    response = await agent.chat("Research the latest developments in artificial intelligence")
    print(f"Agent response: {response}")
    
    return agent


if __name__ == "__main__":
    # Run example usage
    async def main():
        try:
            agent = await example_usage()
            print("UTCP Agent initialized successfully!")
        except Exception as e:
            print(f"Error initializing UTCP Agent: {e}")
            import traceback
            traceback.print_exc()
    
    asyncio.run(main())