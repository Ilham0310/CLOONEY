"""
Functional tests for the FastAPI clone API.
All tests run against the local clone only - no external API calls.
"""

import pytest
from fastapi.testclient import TestClient
from conftest import client, sample_user_data, sample_workspace_data, sample_project_data, sample_task_data


# Workspace Tests
def test_create_workspace(client: TestClient, sample_workspace_data):
    """Test creating a workspace with valid data."""
    response = client.post("/api/1.0/workspaces", json=sample_workspace_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == sample_workspace_data["name"]
    assert "id" in data


def test_create_workspace_missing_name(client: TestClient):
    """Test creating a workspace without required name field."""
    response = client.post("/api/1.0/workspaces", json={})
    assert response.status_code == 422


def test_list_workspaces(client: TestClient, sample_workspace_data):
    """Test listing all workspaces."""
    # Create a workspace first
    client.post("/api/1.0/workspaces", json=sample_workspace_data)
    
    response = client.get("/api/1.0/workspaces")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_get_workspace(client: TestClient, sample_workspace_data):
    """Test getting a workspace by ID."""
    # Create a workspace first
    create_response = client.post("/api/1.0/workspaces", json=sample_workspace_data)
    workspace_id = create_response.json()["id"]
    
    response = client.get(f"/api/1.0/workspaces/{workspace_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == workspace_id
    assert data["name"] == sample_workspace_data["name"]


def test_get_workspace_not_found(client: TestClient):
    """Test getting a non-existent workspace."""
    response = client.get("/api/1.0/workspaces/99999")
    assert response.status_code == 404


# User Tests
def test_create_user(client: TestClient, sample_user_data):
    """Test creating a user with valid data."""
    # Use a unique email to avoid conflicts with other tests
    unique_email = f"test_{id(sample_user_data)}@example.com"
    user_data = {**sample_user_data, "email": unique_email}
    response = client.post("/api/1.0/users", json=user_data)
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.json()}"
    data = response.json()
    assert data["email"] == unique_email
    assert "id" in data


def test_create_user_duplicate_email(client: TestClient, sample_user_data):
    """Test creating a user with duplicate email."""
    # Create first user
    client.post("/api/1.0/users", json=sample_user_data)
    
    # Try to create another with same email
    response = client.post("/api/1.0/users", json=sample_user_data)
    assert response.status_code == 400


def test_list_users(client: TestClient, sample_user_data):
    """Test listing all users."""
    # Create a user first
    client.post("/api/1.0/users", json=sample_user_data)
    
    response = client.get("/api/1.0/users")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_get_user(client: TestClient, sample_user_data):
    """Test getting a user by ID."""
    # Create a user first with unique email
    unique_email = f"test_get_{id(sample_user_data)}@example.com"
    user_data = {**sample_user_data, "email": unique_email}
    create_response = client.post("/api/1.0/users", json=user_data)
    assert create_response.status_code == 201, f"Expected 201, got {create_response.status_code}: {create_response.json()}"
    user_id = create_response.json()["id"]
    
    response = client.get(f"/api/1.0/users/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert data["email"] == unique_email


def test_get_user_not_found(client: TestClient):
    """Test getting a non-existent user."""
    response = client.get("/api/1.0/users/99999")
    assert response.status_code == 404


# Project Tests
def test_create_project(client: TestClient, sample_workspace_data, sample_project_data):
    """Test creating a project with valid data."""
    # Create workspace first
    workspace_response = client.post("/api/1.0/workspaces", json=sample_workspace_data)
    workspace_id = workspace_response.json()["id"]
    
    project_data = {**sample_project_data, "workspace_id": workspace_id}
    response = client.post("/api/1.0/projects", json=project_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == sample_project_data["name"]
    assert "id" in data


def test_create_project_with_invalid_workspace(client: TestClient, sample_project_data):
    """Test creating a project with invalid workspace ID."""
    project_data = {**sample_project_data, "workspace_id": "99999"}
    response = client.post("/api/1.0/projects", json=project_data)
    assert response.status_code == 404


def test_list_projects(client: TestClient, sample_workspace_data, sample_project_data):
    """Test listing all projects."""
    # Create workspace and project first
    workspace_response = client.post("/api/1.0/workspaces", json=sample_workspace_data)
    workspace_id = workspace_response.json()["id"]
    project_data = {**sample_project_data, "workspace_id": workspace_id}
    client.post("/api/1.0/projects", json=project_data)
    
    response = client.get("/api/1.0/projects")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_get_project(client: TestClient, sample_workspace_data, sample_project_data):
    """Test getting a project by ID."""
    # Create workspace and project first
    workspace_response = client.post("/api/1.0/workspaces", json=sample_workspace_data)
    workspace_id = workspace_response.json()["id"]
    project_data = {**sample_project_data, "workspace_id": workspace_id}
    create_response = client.post("/api/1.0/projects", json=project_data)
    project_id = create_response.json()["id"]
    
    response = client.get(f"/api/1.0/projects/{project_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == project_id
    assert data["name"] == sample_project_data["name"]


def test_update_project(client: TestClient, sample_workspace_data, sample_project_data):
    """Test updating a project."""
    # Create workspace and project first
    workspace_response = client.post("/api/1.0/workspaces", json=sample_workspace_data)
    workspace_id = workspace_response.json()["id"]
    project_data = {**sample_project_data, "workspace_id": workspace_id}
    create_response = client.post("/api/1.0/projects", json=project_data)
    project_id = create_response.json()["id"]
    
    update_data = {"name": "Updated Project Name"}
    response = client.put(f"/api/1.0/projects/{project_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Project Name"


def test_update_project_not_found(client: TestClient):
    """Test updating a non-existent project."""
    response = client.put("/api/1.0/projects/99999", json={"name": "Updated"})
    assert response.status_code == 404


# Task Tests
def test_create_task(client: TestClient, sample_workspace_data, sample_project_data, sample_task_data):
    """Test creating a task with valid data."""
    # Create workspace and project first
    workspace_response = client.post("/api/1.0/workspaces", json=sample_workspace_data)
    workspace_id = workspace_response.json()["id"]
    project_data = {**sample_project_data, "workspace_id": workspace_id}
    project_response = client.post("/api/1.0/projects", json=project_data)
    project_id = project_response.json()["id"]
    
    task_data = {**sample_task_data, "project_id": project_id}
    response = client.post("/api/1.0/tasks", json=task_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == sample_task_data["name"]
    assert "id" in data


def test_create_task_with_invalid_project(client: TestClient, sample_task_data):
    """Test creating a task with invalid project ID."""
    task_data = {**sample_task_data, "project_id": "99999"}
    response = client.post("/api/1.0/tasks", json=task_data)
    assert response.status_code == 404


def test_list_tasks(client: TestClient, sample_workspace_data, sample_project_data, sample_task_data):
    """Test listing all tasks."""
    # Create workspace, project, and task first
    workspace_response = client.post("/api/1.0/workspaces", json=sample_workspace_data)
    workspace_id = workspace_response.json()["id"]
    project_data = {**sample_project_data, "workspace_id": workspace_id}
    project_response = client.post("/api/1.0/projects", json=project_data)
    project_id = project_response.json()["id"]
    task_data = {**sample_task_data, "project_id": project_id}
    client.post("/api/1.0/tasks", json=task_data)
    
    response = client.get("/api/1.0/tasks")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_list_tasks_with_filters(client: TestClient, sample_workspace_data, sample_project_data, sample_task_data):
    """Test listing tasks with filters."""
    # Create workspace, project, and task first
    workspace_response = client.post("/api/1.0/workspaces", json=sample_workspace_data)
    workspace_id = workspace_response.json()["id"]
    project_data = {**sample_project_data, "workspace_id": workspace_id}
    project_response = client.post("/api/1.0/projects", json=project_data)
    project_id = project_response.json()["id"]
    task_data = {**sample_task_data, "project_id": project_id}
    client.post("/api/1.0/tasks", json=task_data)
    
    # Filter by project_id
    response = client.get(f"/api/1.0/tasks?project_id={project_id}")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_task(client: TestClient, sample_workspace_data, sample_project_data, sample_task_data):
    """Test getting a task by ID."""
    # Create workspace, project, and task first
    workspace_response = client.post("/api/1.0/workspaces", json=sample_workspace_data)
    workspace_id = workspace_response.json()["id"]
    project_data = {**sample_project_data, "workspace_id": workspace_id}
    project_response = client.post("/api/1.0/projects", json=project_data)
    project_id = project_response.json()["id"]
    task_data = {**sample_task_data, "project_id": project_id}
    create_response = client.post("/api/1.0/tasks", json=task_data)
    task_id = create_response.json()["id"]
    
    response = client.get(f"/api/1.0/tasks/{task_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id
    assert data["name"] == sample_task_data["name"]


def test_update_task(client: TestClient, sample_workspace_data, sample_project_data, sample_task_data):
    """Test updating a task."""
    # Create workspace, project, and task first
    workspace_response = client.post("/api/1.0/workspaces", json=sample_workspace_data)
    workspace_id = workspace_response.json()["id"]
    project_data = {**sample_project_data, "workspace_id": workspace_id}
    project_response = client.post("/api/1.0/projects", json=project_data)
    project_id = project_response.json()["id"]
    task_data = {**sample_task_data, "project_id": project_id}
    create_response = client.post("/api/1.0/tasks", json=task_data)
    task_id = create_response.json()["id"]
    
    update_data = {"name": "Updated Task Name", "completed": True}
    response = client.put(f"/api/1.0/tasks/{task_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Task Name"
    assert data["completed"] == True


def test_update_task_not_found(client: TestClient):
    """Test updating a non-existent task."""
    response = client.put("/api/1.0/tasks/99999", json={"name": "Updated"})
    assert response.status_code == 404


# Section Tests
def test_create_section(client: TestClient, sample_workspace_data, sample_project_data):
    """Test creating a section with valid data."""
    # Create workspace and project first
    workspace_response = client.post("/api/1.0/workspaces", json=sample_workspace_data)
    workspace_id = workspace_response.json()["id"]
    project_data = {**sample_project_data, "workspace_id": workspace_id}
    project_response = client.post("/api/1.0/projects", json=project_data)
    project_id = project_response.json()["id"]
    
    section_data = {"name": "Test Section", "project_id": project_id}
    response = client.post("/api/1.0/sections", json=section_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Section"
    assert "id" in data


def test_create_section_invalid_project(client: TestClient):
    """Test creating a section with invalid project ID."""
    section_data = {"name": "Test Section", "project_id": "99999"}
    response = client.post("/api/1.0/sections", json=section_data)
    assert response.status_code == 404


def test_list_sections(client: TestClient, sample_workspace_data, sample_project_data):
    """Test listing all sections."""
    # Create workspace, project, and section first
    workspace_response = client.post("/api/1.0/workspaces", json=sample_workspace_data)
    workspace_id = workspace_response.json()["id"]
    project_data = {**sample_project_data, "workspace_id": workspace_id}
    project_response = client.post("/api/1.0/projects", json=project_data)
    project_id = project_response.json()["id"]
    section_data = {"name": "Test Section", "project_id": project_id}
    client.post("/api/1.0/sections", json=section_data)
    
    response = client.get("/api/1.0/sections")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


# Team Tests
def test_create_team(client: TestClient, sample_workspace_data):
    """Test creating a team with valid data."""
    # Create workspace first
    workspace_response = client.post("/api/1.0/workspaces", json=sample_workspace_data)
    workspace_id = workspace_response.json()["id"]
    
    team_data = {"name": "Test Team", "workspace_id": workspace_id}
    response = client.post("/api/1.0/teams", json=team_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Team"
    assert "id" in data


def test_list_teams(client: TestClient, sample_workspace_data):
    """Test listing all teams."""
    # Create workspace and team first
    workspace_response = client.post("/api/1.0/workspaces", json=sample_workspace_data)
    workspace_id = workspace_response.json()["id"]
    team_data = {"name": "Test Team", "workspace_id": workspace_id}
    client.post("/api/1.0/teams", json=team_data)
    
    response = client.get("/api/1.0/teams")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


# Health Check Tests
def test_health_check(client: TestClient):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_root_endpoint(client: TestClient):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
