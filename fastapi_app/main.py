"""
FastAPI application with functional CRUD endpoints.
"""

from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel, EmailStr
from datetime import datetime
import uuid

from .database import (
    Base, engine, SessionLocal, init_db,
    Workspace, User, Team, Project, Section, Task
)

# Initialize database
# Tests will override the database dependency, so this won't affect them
init_db()

app = FastAPI(title="Asana API Clone", version="1.0.0")


# Database dependency
def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Pydantic models for request/response
class WorkspaceCreate(BaseModel):
    name: str
    description: Optional[str] = None


class WorkspaceResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    activated: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    name: str
    email: EmailStr


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TeamCreate(BaseModel):
    name: str
    description: Optional[str] = None
    workspace_id: str


class TeamResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    workspace_id: str  # Required for projects
    team_id: Optional[str] = None
    public: bool = False


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    public: Optional[bool] = None
    archived: Optional[bool] = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    workspace_id: Optional[str] = None
    team_id: Optional[str] = None
    public: bool
    archived: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SectionCreate(BaseModel):
    name: str
    project_id: str


class SectionResponse(BaseModel):
    id: str
    name: str
    project_id: str
    position: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskCreate(BaseModel):
    name: str
    description: Optional[str] = None
    project_id: str  # Required for tasks
    section_id: Optional[str] = None
    assignee_id: Optional[str] = None
    completed: bool = False


class TaskUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None
    assignee_id: Optional[str] = None


class TaskResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    project_id: Optional[str] = None
    section_id: Optional[str] = None
    assignee_id: Optional[str] = None
    creator_id: Optional[str] = None
    completed: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Health check endpoints
@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Asana API Clone", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Workspace endpoints
@app.post("/api/1.0/workspaces", response_model=WorkspaceResponse, status_code=201)
async def create_workspace(workspace: WorkspaceCreate, db: Session = Depends(get_db)):
    """Create a new workspace."""
    db_workspace = Workspace(
        id=str(uuid.uuid4()),
        name=workspace.name,
        description=workspace.description
    )
    db.add(db_workspace)
    db.commit()
    db.refresh(db_workspace)
    return db_workspace


@app.get("/api/1.0/workspaces", response_model=List[WorkspaceResponse])
async def list_workspaces(db: Session = Depends(get_db)):
    """List all workspaces."""
    workspaces = db.query(Workspace).all()
    return workspaces


@app.get("/api/1.0/workspaces/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(workspace_id: str, db: Session = Depends(get_db)):
    """Get a workspace by ID."""
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace


# User endpoints
@app.post("/api/1.0/users", response_model=UserResponse, status_code=201)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user."""
    # Check for duplicate email
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    db_user = User(
        id=str(uuid.uuid4()),
        name=user.name,
        email=user.email
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.get("/api/1.0/users", response_model=List[UserResponse])
async def list_users(db: Session = Depends(get_db)):
    """List all users."""
    users = db.query(User).all()
    return users


@app.get("/api/1.0/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, db: Session = Depends(get_db)):
    """Get a user by ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# Team endpoints
@app.post("/api/1.0/teams", response_model=TeamResponse, status_code=201)
async def create_team(team: TeamCreate, db: Session = Depends(get_db)):
    """Create a new team."""
    # Verify workspace exists
    workspace = db.query(Workspace).filter(Workspace.id == team.workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    db_team = Team(
        id=str(uuid.uuid4()),
        name=team.name,
        description=team.description
    )
    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    return db_team


@app.get("/api/1.0/teams", response_model=List[TeamResponse])
async def list_teams(db: Session = Depends(get_db)):
    """List all teams."""
    teams = db.query(Team).all()
    return teams


@app.get("/api/1.0/teams/{team_id}", response_model=TeamResponse)
async def get_team(team_id: str, db: Session = Depends(get_db)):
    """Get a team by ID."""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


# Project endpoints
@app.post("/api/1.0/projects", response_model=ProjectResponse, status_code=201)
async def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    """Create a new project."""
    # Verify workspace exists (required)
    workspace = db.query(Workspace).filter(Workspace.id == project.workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Verify team exists if provided
    if project.team_id:
        team = db.query(Team).filter(Team.id == project.team_id).first()
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
    
    db_project = Project(
        id=str(uuid.uuid4()),
        name=project.name,
        description=project.description,
        workspace_id=project.workspace_id,
        team_id=project.team_id,
        public=project.public
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


@app.get("/api/1.0/projects", response_model=List[ProjectResponse])
async def list_projects(db: Session = Depends(get_db)):
    """List all projects."""
    projects = db.query(Project).all()
    return projects


@app.get("/api/1.0/projects/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, db: Session = Depends(get_db)):
    """Get a project by ID."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@app.put("/api/1.0/projects/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: str, project_update: ProjectUpdate, db: Session = Depends(get_db)):
    """Update a project."""
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project_update.name is not None:
        db_project.name = project_update.name
    if project_update.description is not None:
        db_project.description = project_update.description
    if project_update.public is not None:
        db_project.public = project_update.public
    if project_update.archived is not None:
        db_project.archived = project_update.archived
    
    db.commit()
    db.refresh(db_project)
    return db_project


# Section endpoints
@app.post("/api/1.0/sections", response_model=SectionResponse, status_code=201)
async def create_section(section: SectionCreate, db: Session = Depends(get_db)):
    """Create a new section."""
    # Verify project exists
    project = db.query(Project).filter(Project.id == section.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db_section = Section(
        id=str(uuid.uuid4()),
        name=section.name,
        project_id=section.project_id
    )
    db.add(db_section)
    db.commit()
    db.refresh(db_section)
    return db_section


@app.get("/api/1.0/sections", response_model=List[SectionResponse])
async def list_sections(db: Session = Depends(get_db)):
    """List all sections."""
    sections = db.query(Section).all()
    return sections


@app.get("/api/1.0/sections/{section_id}", response_model=SectionResponse)
async def get_section(section_id: str, db: Session = Depends(get_db)):
    """Get a section by ID."""
    section = db.query(Section).filter(Section.id == section_id).first()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    return section


# Task endpoints
@app.post("/api/1.0/tasks", response_model=TaskResponse, status_code=201)
async def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    """Create a new task."""
    # Verify project exists (required)
    project = db.query(Project).filter(Project.id == task.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Verify section exists if provided
    if task.section_id:
        section = db.query(Section).filter(Section.id == task.section_id).first()
        if not section:
            raise HTTPException(status_code=404, detail="Section not found")
    
    # Verify assignee exists if provided
    if task.assignee_id:
        assignee = db.query(User).filter(User.id == task.assignee_id).first()
        if not assignee:
            raise HTTPException(status_code=404, detail="Assignee not found")
    
    db_task = Task(
        id=str(uuid.uuid4()),
        name=task.name,
        description=task.description,
        project_id=task.project_id,
        section_id=task.section_id,
        assignee_id=task.assignee_id,
        completed=task.completed
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


@app.get("/api/1.0/tasks", response_model=List[TaskResponse])
async def list_tasks(
    project_id: Optional[str] = Query(None),
    assignee_id: Optional[str] = Query(None),
    completed: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """List all tasks with optional filters."""
    query = db.query(Task)
    
    if project_id:
        query = query.filter(Task.project_id == project_id)
    if assignee_id:
        query = query.filter(Task.assignee_id == assignee_id)
    if completed is not None:
        query = query.filter(Task.completed == completed)
    
    tasks = query.all()
    return tasks


@app.get("/api/1.0/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, db: Session = Depends(get_db)):
    """Get a task by ID."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.put("/api/1.0/tasks/{task_id}", response_model=TaskResponse)
async def update_task(task_id: str, task_update: TaskUpdate, db: Session = Depends(get_db)):
    """Update a task."""
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task_update.name is not None:
        db_task.name = task_update.name
    if task_update.description is not None:
        db_task.description = task_update.description
    if task_update.completed is not None:
        db_task.completed = task_update.completed
    if task_update.assignee_id is not None:
        # Verify assignee exists
        if task_update.assignee_id:
            assignee = db.query(User).filter(User.id == task_update.assignee_id).first()
            if not assignee:
                raise HTTPException(status_code=404, detail="Assignee not found")
        db_task.assignee_id = task_update.assignee_id
    
    db.commit()
    db.refresh(db_task)
    return db_task
