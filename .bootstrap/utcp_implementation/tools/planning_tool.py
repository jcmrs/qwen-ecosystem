"""
Planning Tool - UTCP-compliant service for project and task planning
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException
import asyncio


class Task(BaseModel):
    """Model for a task in the planning system"""
    id: str
    title: str
    description: str
    priority: int = Field(ge=1, le=5, default=3)  # 1=low, 5=high
    status: str = Field(default="pending", regex="^(pending|in_progress|completed|blocked)$")
    assigned_to: Optional[str] = None
    due_date: Optional[date] = None
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


class Project(BaseModel):
    """Model for a project in the planning system"""
    id: str
    name: str
    description: str
    status: str = Field(default="active", regex="^(active|completed|on_hold|cancelled)$")
    start_date: date
    end_date: Optional[date] = None
    tasks: List[Task] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)


class PlanningInput(BaseModel):
    """Input model for planning operations"""
    action: str = Field(..., description="Action to perform (create_task, create_project, update_task, etc.)")
    project_id: Optional[str] = None
    task_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[int] = Field(default=None, ge=1, le=5)
    assigned_to: Optional[str] = None
    due_date: Optional[date] = None
    status: Optional[str] = None


class PlanningOutput(BaseModel):
    """Output model for planning operations"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: str


class PlanningService:
    """Service class for planning operations"""
    
    def __init__(self):
        self.projects: Dict[str, Project] = {}
        self.tasks: Dict[str, Task] = {}
    
    async def create_project(self, name: str, description: str, start_date: date) -> Project:
        """Create a new project"""
        import uuid
        project_id = f"proj_{uuid.uuid4().hex[:8]}"
        
        project = Project(
            id=project_id,
            name=name,
            description=description,
            start_date=start_date
        )
        
        self.projects[project_id] = project
        return project
    
    async def create_task(self, project_id: str, title: str, description: str, 
                         priority: int = 3, assigned_to: str = None, 
                         due_date: date = None) -> Task:
        """Create a new task in a project"""
        if project_id not in self.projects:
            raise ValueError(f"Project {project_id} does not exist")
        
        import uuid
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        
        task = Task(
            id=task_id,
            title=title,
            description=description,
            priority=priority,
            assigned_to=assigned_to,
            due_date=due_date
        )
        
        self.tasks[task_id] = task
        self.projects[project_id].tasks.append(task)
        
        return task
    
    async def update_task(self, task_id: str, **updates) -> Optional[Task]:
        """Update a task with provided fields"""
        if task_id not in self.tasks:
            return None
        
        task = self.tasks[task_id]
        
        # Update allowed fields
        for field, value in updates.items():
            if hasattr(task, field) and field not in ['id', 'created_at']:
                setattr(task, field, value)
        
        # If status is updated to completed, set completed_at
        if updates.get('status') == 'completed' and task.completed_at is None:
            task.completed_at = datetime.now()
        
        return task
    
    async def get_project_tasks(self, project_id: str) -> List[Task]:
        """Get all tasks for a project"""
        if project_id not in self.projects:
            return []
        
        return self.projects[project_id].tasks
    
    async def get_projects(self) -> List[Project]:
        """Get all projects"""
        return list(self.projects.values())


# Initialize the planning service
planning_service = PlanningService()

# Create FastAPI app for the planning tool
app = FastAPI(
    title="Planning Tool - UTCP-compliant",
    description="A UTCP-compliant tool for project and task planning",
    version="1.0.0"
)


@app.get("/")
async def planning_tool_info():
    """Information about the planning tool"""
    return {
        "name": "Planning Tool",
        "version": "1.0.0",
        "description": "A UTCP-compliant tool for project and task planning",
        "endpoints": {
            "/utcp": "UTCP discovery endpoint",
            "/planning": "Main planning endpoint",
            "/health": "Health check endpoint"
        }
    }


@app.get("/utcp")
async def utcp_discovery():
    """UTCP discovery endpoint - returns the tool manual"""
    from utcp.data.utcp_manual import UtcpManual
    from utcp.data.tool import Tool
    
    manual = UtcpManual(
        manual_version="1.0.0",
        utcp_version="1.0.2",
        tools=[
            Tool(
                name="create_project",
                description="Create a new project",
                inputs={
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "const": "create_project"},
                        "name": {"type": "string", "description": "Project name"},
                        "description": {"type": "string", "description": "Project description"},
                        "start_date": {"type": "string", "format": "date", "description": "Project start date (YYYY-MM-DD)"}
                    },
                    "required": ["action", "name", "description", "start_date"]
                },
                outputs={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean"},
                        "message": {"type": "string"},
                        "data": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "name": {"type": "string"},
                                "status": {"type": "string"}
                            }
                        }
                    }
                },
                tags=["planning", "projects"],
                tool_call_template={
                    "call_template_type": "http",
                    "url": "http://localhost:8002/planning",
                    "http_method": "POST"
                }
            ),
            Tool(
                name="create_task",
                description="Create a new task in a project",
                inputs={
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "const": "create_task"},
                        "project_id": {"type": "string", "description": "Project ID"},
                        "title": {"type": "string", "description": "Task title"},
                        "description": {"type": "string", "description": "Task description"},
                        "priority": {
                            "type": "integer", 
                            "minimum": 1, 
                            "maximum": 5, 
                            "default": 3,
                            "description": "Task priority (1-5)"
                        },
                        "assigned_to": {"type": "string", "description": "Person assigned to task"},
                        "due_date": {"type": "string", "format": "date", "description": "Due date (YYYY-MM-DD)"}
                    },
                    "required": ["action", "project_id", "title", "description"]
                },
                outputs={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean"},
                        "message": {"type": "string"},
                        "data": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "title": {"type": "string"},
                                "status": {"type": "string"}
                            }
                        }
                    }
                },
                tags=["planning", "tasks"],
                tool_call_template={
                    "call_template_type": "http",
                    "url": "http://localhost:8002/planning",
                    "http_method": "POST"
                }
            ),
            Tool(
                name="update_task",
                description="Update an existing task",
                inputs={
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "const": "update_task"},
                        "task_id": {"type": "string", "description": "Task ID to update"},
                        "status": {
                            "type": "string",
                            "enum": ["pending", "in_progress", "completed", "blocked"],
                            "description": "New status for the task"
                        },
                        "assigned_to": {"type": "string", "description": "New assignment"},
                        "due_date": {"type": "string", "format": "date", "description": "New due date (YYYY-MM-DD)"}
                    },
                    "required": ["action", "task_id"]
                },
                outputs={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean"},
                        "message": {"type": "string"},
                        "data": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "status": {"type": "string"},
                                "assigned_to": {"type": "string"}
                            }
                        }
                    }
                },
                tags=["planning", "tasks"],
                tool_call_template={
                    "call_template_type": "http",
                    "url": "http://localhost:8002/planning",
                    "http_method": "POST"
                }
            )
        ]
    )
    return manual.model_dump()


@app.post("/planning", response_model=PlanningOutput)
async def planning_operation(request: PlanningInput):
    """Main endpoint for planning operations"""
    try:
        if request.action == "create_project":
            if not request.title or not request.description:
                raise HTTPException(status_code=400, detail="Project name and description are required")
            
            project = await planning_service.create_project(
                name=request.title,
                description=request.description,
                start_date=request.due_date or date.today()  # Using due_date as start_date for projects
            )
            
            return PlanningOutput(
                success=True,
                message=f"Project '{project.name}' created successfully",
                data=project.model_dump(),
                timestamp=datetime.now().isoformat()
            )
        
        elif request.action == "create_task":
            if not request.project_id or not request.title or not request.description:
                raise HTTPException(status_code=400, detail="Project ID, title, and description are required")
            
            task = await planning_service.create_task(
                project_id=request.project_id,
                title=request.title,
                description=request.description,
                priority=request.priority or 3,
                assigned_to=request.assigned_to,
                due_date=request.due_date
            )
            
            return PlanningOutput(
                success=True,
                message=f"Task '{task.title}' created successfully",
                data=task.model_dump(),
                timestamp=datetime.now().isoformat()
            )
        
        elif request.action == "update_task":
            if not request.task_id:
                raise HTTPException(status_code=400, detail="Task ID is required")
            
            updates = {}
            if request.status is not None:
                updates['status'] = request.status
            if request.assigned_to is not None:
                updates['assigned_to'] = request.assigned_to
            if request.due_date is not None:
                updates['due_date'] = request.due_date
            
            task = await planning_service.update_task(request.task_id, **updates)
            if task is None:
                raise HTTPException(status_code=404, detail=f"Task {request.task_id} not found")
            
            return PlanningOutput(
                success=True,
                message=f"Task '{task.title}' updated successfully",
                data=task.model_dump(),
                timestamp=datetime.now().isoformat()
            )
        
        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {request.action}")
    
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Planning operation failed: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Planning Tool",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/projects")
async def get_all_projects():
    """Get all projects"""
    projects = await planning_service.get_projects()
    return {"projects": [p.model_dump() for p in projects]}


@app.get("/projects/{project_id}/tasks")
async def get_project_tasks(project_id: str):
    """Get all tasks for a specific project"""
    tasks = await planning_service.get_project_tasks(project_id)
    return {"tasks": [t.model_dump() for t in tasks]}


# If running this file directly, start the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)