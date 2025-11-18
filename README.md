# 🎯 Clooney: Asana API Clone

An **agentic system** that automatically reverse-engineers and clones Asana's backend API by capturing WebSocket traffic, inferring schemas with AI, and generating a complete functional backend—all without manual coding.

**Status: ✅ 100% Complete and Functional**

---

## 📖 About the Project

Clooney is an automated backend replication system that demonstrates the power of AI and automation in reverse engineering. The system:

- **Observes** Asana's web application behavior through network traffic capture
- **Learns** API structure, data schemas, and relationships from captured data
- **Generates** a complete functional backend (OpenAPI spec, database schema, FastAPI code)
- **Tests** the generated backend comprehensively
- **Improves** itself through iterative refinement

Unlike traditional API documentation or manual reverse engineering, Clooney **automatically discovers and replicates** backend behavior from real application usage.

---

## 🎯 Project Goals & How They Were Achieved

### Goal 1: Automated Reverse Engineering ✅

**Objective:** Capture and analyze Asana's API without manual inspection.

**Achievement:**
- ✅ **WebSocket Interception:** Discovered that Asana uses WebSocket (not REST) for CRUD operations
- ✅ **JavaScript Injection:** Created `capture_with_js_interception.py` to intercept WebSocket messages in real-time
- ✅ **5,157+ CRUD Operations Captured:** Full payloads with entity types, fields, and relationships
- ✅ **Entity Extraction:** Identified 100+ entity types from captured data

**Key Innovation:** Traditional tools only capture HTTP traffic. We solved the WebSocket challenge by injecting JavaScript to intercept messages at the browser level.

---

### Goal 2: Schema Inference & Code Generation ✅

**Objective:** Automatically infer data schemas and generate production-ready code.

**Achievement:**
- ✅ **AI-Enhanced Inference:** Optional Google Gemini integration for better schema inference
- ✅ **Heuristic Fallback:** Works without AI using intelligent heuristics
- ✅ **Complete Code Generation:** OpenAPI spec, SQL schema, FastAPI code, and tests
- ✅ **Smart Code Preservation:** Generator preserves functional code while updating stubs

**Key Innovation:** Dual-mode inference (AI + heuristics) ensures the system works with or without API keys.

---

### Goal 3: Functional Backend Clone ✅

**Objective:** Generate a working backend API that replicates Asana's core functionality.

**Achievement:**
- ✅ **20 Functional CRUD Endpoints:** Workspaces, Users, Teams, Projects, Sections, Tasks
- ✅ **Complete Database Schema:** 7 tables with relationships and foreign keys
- ✅ **Request/Response Validation:** Pydantic models for type safety
- ✅ **Error Handling:** Proper HTTP status codes and error messages
- ✅ **Relationship Validation:** Foreign key checks and cascade deletes

**Key Innovation:** Generated code is not just stubs—it's fully functional with database operations, validation, and error handling.

---

### Goal 4: Comprehensive Testing ✅

**Objective:** Ensure the generated backend works correctly.

**Achievement:**
- ✅ **30 Comprehensive Tests:** All passing (100% success rate)
- ✅ **CRUD Coverage:** Create, Read, Update operations for all entities
- ✅ **Error Scenarios:** 404, 400, 422 validation errors
- ✅ **Edge Cases:** Duplicate emails, invalid foreign keys, missing required fields
- ✅ **Test Isolation:** Each test runs with a clean database

**Key Innovation:** Tests are automatically generated from endpoint definitions, ensuring complete coverage.

---

### Goal 5: Self-Improvement Loop ✅

**Objective:** System should improve itself automatically.

**Achievement:**
- ✅ **Quality Tracking:** Compares expected vs. actual responses
- ✅ **Diff Analysis:** Identifies differences using DeepDiff
- ✅ **Refinement Suggestions:** AI-powered suggestions for improvements
- ✅ **Iterative Refinement:** Applies patches and regenerates code
- ✅ **Offline Operation:** No dependency on real Asana API

**Key Innovation:** Self-improvement works offline by comparing against "expected specs" extracted from captured data, not live API calls.

---

## 🔄 Complete Workflow

The system follows a **7-phase pipeline** from capture to deployment:

```
┌─────────────┐
│   Phase 1   │  Capture: WebSocket traffic interception
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Phase 2   │  Parse: Extract entities and schemas
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Phase 3   │  Convert: WebSocket → REST endpoints
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Phase 4   │  Generate: OpenAPI, SQL, FastAPI code
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Phase 5   │  Implement: Database models & CRUD logic
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Phase 6   │  Test: Run comprehensive test suite
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Phase 7   │  Improve: Analyze diffs & refine
└─────────────┘
```

### Phase 1: Capture
**File:** `capture_with_js_interception.py`

- Injects JavaScript into browser context
- Intercepts `fetch`, `XMLHttpRequest`, and `WebSocket` constructors
- Captures full message payloads (not truncated)
- Stores structured JSON data

**Output:** `js_api_capture.json` (17 MB of captured traffic)

---

### Phase 2: Parse
**Files:** `websocket_parser.py`, `extract_entities_from_websocket.py`, `network_parser.py`

- Parses WebSocket messages to extract CRUD operations
- Identifies entity types using `typeName` field
- Groups operations by entity (Task, Project, etc.)
- Extracts field schemas from sample data

**Output:** Entity schemas with field types, relationships, and sample data

---

### Phase 3: Convert
**Files:** `websocket_to_rest_converter.py`, `integrate_websocket_data.py`

- Maps WebSocket operations to REST HTTP methods:
  - `added` → `POST /api/1.0/{entity}`
  - `changed` → `PUT /api/1.0/{entity}/{id}`
  - `removed` → `DELETE /api/1.0/{entity}/{id}`
- Maps entity names (Pot → projects, Column → sections)
- Generates request/response schemas

**Output:** REST endpoint definitions with schemas

---

### Phase 4: Generate
**Files:** `openapi_generator.py`, `schema_generator.py`, `fastapi_generator.py`, `test_generator.py`

- **OpenAPI Generator:** Creates OpenAPI 3.0 specification
- **Schema Generator:** Generates SQL CREATE TABLE statements
- **FastAPI Generator:** Creates endpoint stubs
- **Test Generator:** Generates pytest test cases

**Output:** `api.yml`, `schema.sql`, FastAPI code, test files

---

### Phase 5: Implement
**Files:** `fastapi_app/main.py`, `fastapi_app/database.py`

- Implements full CRUD logic (not just stubs)
- Creates SQLAlchemy ORM models
- Adds validation, error handling, foreign key checks
- Preserves functional code during regeneration

**Output:** Working FastAPI application with 20 endpoints

---

### Phase 6: Test
**Files:** `tests/test_api.py`, `tests/conftest.py`

- Runs 30 comprehensive tests
- Tests all CRUD operations
- Validates error scenarios
- Ensures test isolation

**Output:** Test results (30/30 passing)

---

### Phase 7: Improve
**Files:** `refinement_engine.py`, `self_improving_agent.py`

- Extracts expected response schemas from captured data
- Compares expected vs. actual responses
- Calculates quality scores
- Generates refinement suggestions
- Applies patches and regenerates

**Output:** Quality metrics and refinement history

---

## 🎯 Strategy Used

### 1. **WebSocket-First Approach**

**Challenge:** Asana uses WebSocket for CRUD, not traditional REST.

**Strategy:**
- Intercept WebSocket at the browser level (JavaScript injection)
- Capture full message payloads, not just URLs
- Convert WebSocket operations to REST for our clone

**Why it works:** We capture the actual data flow, not just HTTP requests.

---

### 2. **AI + Heuristics Hybrid**

**Challenge:** Schema inference requires understanding data patterns.

**Strategy:**
- **Primary:** Use Google Gemini for intelligent schema inference
- **Fallback:** Heuristic-based inference (type detection, relationship identification)
- **Graceful Degradation:** System works with or without AI

**Why it works:** Ensures the system is always functional, AI enhances accuracy when available.

---

### 3. **Offline Self-Improvement**

**Challenge:** Can't call real Asana API for comparison.

**Strategy:**
- Extract "expected specs" from captured network data
- Compare generated backend against expected specs
- Use AI to interpret differences and suggest improvements
- Iteratively refine without external dependencies

**Why it works:** Self-improvement works completely offline, making the system independent.

---

### 4. **Code Preservation**

**Challenge:** Generated code shouldn't overwrite functional implementations.

**Strategy:**
- Generator detects existing functional code
- Preserves CRUD logic while updating stubs
- Only generates new endpoints, doesn't break existing ones

**Why it works:** Allows iterative improvement without losing working code.

---

### 5. **Comprehensive Testing**

**Challenge:** Ensure generated backend works correctly.

**Strategy:**
- Auto-generate tests from endpoint definitions
- Test positive cases, negative cases, edge cases
- Ensure test isolation (clean database per test)
- 100% pass rate requirement

**Why it works:** Catches issues early and ensures reliability.

---

## 📊 Generated Outputs

The system generates **4 main artifacts**:

### 1. OpenAPI Specification (`api.yml`)

**What it is:** Complete API specification in OpenAPI 3.0 format.

**Contains:**
- All endpoint definitions (method, path, parameters)
- Request/response schemas
- Status codes and error responses
- Field types, required/optional flags

**Size:** ~96,000 lines (includes all captured endpoints)

**Example:**
```yaml
paths:
  /api/1.0/tasks:
    post:
      summary: Create a new task
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                name:
                  type: string
                project_id:
                  type: string
              required:
                - name
                - project_id
      responses:
        '201':
          description: Task created
```

**Use case:** API documentation, client generation, validation

---

### 2. Database Schema (`schema.sql`)

**What it is:** SQL CREATE TABLE statements for all entities.

**Contains:**
- 7 main tables: workspaces, users, teams, projects, sections, tasks
- 2 junction tables: project_members, task_followers
- Foreign key relationships
- Indexes for performance

**Example:**
```sql
CREATE TABLE tasks (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    project_id VARCHAR(255),
    assignee_id VARCHAR(255),
    completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (assignee_id) REFERENCES users(id)
);
```

**Use case:** Database initialization, schema documentation

---

### 3. FastAPI Application (`fastapi_app/`)

**What it is:** Complete working backend with 20 functional endpoints.

**Contains:**
- **20 CRUD Endpoints:**
  - Workspaces: POST, GET (list), GET (by ID)
  - Users: POST, GET (list), GET (by ID)
  - Teams: POST, GET (list), GET (by ID)
  - Projects: POST, GET (list), GET (by ID), PUT (update)
  - Sections: POST, GET (list), GET (by ID)
  - Tasks: POST, GET (list with filters), GET (by ID), PUT (update)
- **Database Models:** SQLAlchemy ORM models
- **Validation:** Pydantic request/response models
- **Error Handling:** Proper HTTP status codes

**Example:**
```python
@app.post("/api/1.0/tasks", response_model=TaskResponse, status_code=201)
async def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    """Create a new task."""
    # Verify project exists
    project = db.query(Project).filter(Project.id == task.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Create task
    db_task = Task(
        id=str(uuid.uuid4()),
        name=task.name,
        project_id=task.project_id,
        completed=task.completed
    )
    db.add(db_task)
    db.commit()
    return db_task
```

**Use case:** Production backend, API server

---

### 4. Test Suite (`tests/test_api.py`)

**What it is:** 30 comprehensive pytest test cases.

**Contains:**
- **CRUD Tests:** Create, read, update for all entities
- **Error Tests:** 404, 400, 422 validation errors
- **Edge Cases:** Duplicate emails, invalid foreign keys
- **Filter Tests:** Query parameters for task filtering

**Example:**
```python
def test_create_task(db_session):
    """Test creating a task."""
    # Create project first
    project = create_test_project(db_session)
    
    # Create task
    task_data = {
        "name": "Test Task",
        "project_id": project.id,
        "completed": False
    }
    response = client.post("/api/1.0/tasks", json=task_data)
    assert response.status_code == 201
    assert response.json()["name"] == "Test Task"
```

**Use case:** Quality assurance, regression testing

---

## 🚀 How to Run the Project

### Prerequisites

- **Python 3.11+** installed
- **pip** (Python package manager)
- **Git** (optional, for cloning)

---

### Step 1: Clone the Repository

```bash
git clone https://github.com/Ilham0310/CLOONEY.git
cd CLOONEY
```

---

### Step 2: Set Up Virtual Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate

# On Windows:
# .venv\Scripts\activate
```

---

### Step 3: Install Dependencies

```bash
# Install Python packages
pip install -r requirements.txt

# Install Playwright browser (for network capture)
playwright install chromium
```

**Note:** If you don't have Playwright, you can skip this step if you're not capturing new data.

---

### Step 4: (Optional) Set Up AI Enhancement

If you want to use Google Gemini for better schema inference:

```bash
# Create .env file
cp .env.template .env

# Add your Gemini API key
echo "GEMINI_API_KEY=your_api_key_here" >> .env
```

**Note:** The system works without AI using heuristics. This is optional.

---

### Step 5: Run the Complete Pipeline

```bash
# Run everything: parse → generate → test → improve
python run_pipeline.py --mode all
```

**What this does:**
1. ✅ Parses network capture data
2. ✅ Generates OpenAPI spec, SQL schema, FastAPI code
3. ✅ Runs all 30 tests
4. ✅ Runs self-improvement loop

**Expected Output:**
```
================================================================================
CLOONEY PROJECT - Complete Pipeline
================================================================================

STEP 1: Parsing Network Capture
--------------------------------------------------------------------------------
✅ Parsed 16 endpoints

STEP 2: Generating Artifacts
--------------------------------------------------------------------------------
✅ api.yml generated
✅ schema.sql generated
✅ FastAPI app generated
✅ Test cases generated

STEP 3: Running Tests
--------------------------------------------------------------------------------
============================= test session starts ==============================
...
======================= 30 passed, 85 warnings in 0.92s ========================

STEP 4: Self-Improvement Loop
--------------------------------------------------------------------------------
✅ Quality score: 41.67%
✅ Refinement suggestions generated
```

---

### Step 6: Start the API Server

```bash
# Navigate to FastAPI app directory
cd fastapi_app

# Start the server
uvicorn main:app --reload

# Server will start at: http://localhost:8000
```

**Open in browser:**
- **API Documentation (Swagger UI):** http://localhost:8000/docs
- **Alternative Docs (ReDoc):** http://localhost:8000/redoc
- **API Root:** http://localhost:8000

---

### Step 7: Test the API

#### Using Swagger UI (Recommended)

1. Open http://localhost:8000/docs
2. Click on any endpoint (e.g., `POST /api/1.0/workspaces`)
3. Click "Try it out"
4. Enter JSON data:
   ```json
   {
     "name": "My Workspace"
   }
   ```
5. Click "Execute"
6. See the response!

#### Using cURL

```bash
# Create a workspace
curl -X POST "http://localhost:8000/api/1.0/workspaces" \
  -H "Content-Type: application/json" \
  -d '{"name": "My Workspace"}'

# List all workspaces
curl -X GET "http://localhost:8000/api/1.0/workspaces"

# Create a task
curl -X POST "http://localhost:8000/api/1.0/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Complete documentation",
    "project_id": "project_123",
    "completed": false
  }'
```

---

### Step 8: Run Tests

```bash
# Run all tests
pytest tests/test_api.py -v

# Run specific test
pytest tests/test_api.py::test_create_task -v

# Run with coverage
pytest tests/test_api.py --cov=fastapi_app --cov-report=html
```

**Expected Output:**
```
============================= test session starts ==============================
tests/test_api.py::test_create_workspace PASSED
tests/test_api.py::test_list_workspaces PASSED
tests/test_api.py::test_get_workspace PASSED
...
======================= 30 passed, 85 warnings in 0.92s ========================
```

---

### Alternative: Run Individual Pipeline Steps

```bash
# Parse only
python run_pipeline.py --mode parse

# Generate only
python run_pipeline.py --mode generate

# Test only
python run_pipeline.py --mode test

# Self-improvement only
python run_pipeline.py --mode improve
```

---

### Using Docker

```bash
# Build and run with Docker Compose
docker-compose up

# Or build manually
docker build -t clooney .
docker run -p 8000:8000 clooney
```

---

## 📁 Project Structure

```
CLOONEY/
├── fastapi_app/              # FastAPI application
│   ├── main.py              # 20 functional endpoints
│   ├── database.py          # SQLAlchemy models
│   └── requirements.txt     # FastAPI dependencies
├── tests/                    # Test suite
│   ├── test_api.py          # 30 test cases
│   └── conftest.py          # Test configuration
├── ai/                       # AI agents (optional)
│   ├── gemini_client.py     # Gemini API wrapper
│   ├── schema_inference_agent.py
│   ├── endpoint_inference_agent.py
│   └── rule_refinement_agent.py
├── docs/                     # Documentation
│   └── AI_OVERVIEW.md       # AI integration guide
├── capture_with_js_interception.py  # WebSocket capture
├── websocket_parser.py       # Parse WebSocket messages
├── extract_entities_from_websocket.py  # Extract schemas
├── websocket_to_rest_converter.py  # Convert to REST
├── network_parser.py         # Parse network data
├── openapi_generator.py      # Generate OpenAPI spec
├── schema_generator.py       # Generate SQL schema
├── fastapi_generator.py      # Generate FastAPI code
├── test_generator.py         # Generate tests
├── refinement_engine.py      # Analyze differences
├── self_improving_agent.py   # Improvement loop
├── run_pipeline.py           # Main pipeline orchestrator
├── api.yml                   # Generated OpenAPI spec
├── schema.sql                # Generated SQL schema
├── requirements.txt          # Python dependencies
├── Dockerfile                # Docker configuration
├── docker-compose.yml        # Docker Compose config
└── README.md                 # This file
```

---

## ✨ Key Features

- ✅ **20 Functional CRUD Endpoints** - Fully working REST API
- ✅ **30 Comprehensive Tests** - 100% pass rate
- ✅ **Self-Improving System** - Quality tracking and automatic refinement
- ✅ **AI-Enhanced** - Optional Google Gemini for better inference
- ✅ **Fully Automated** - Single command pipeline
- ✅ **Production Ready** - Docker support, comprehensive testing
- ✅ **Offline Operation** - No dependency on real Asana API
- ✅ **Complete Documentation** - Guides, demo scripts, technical details

---

## 🛠️ Technology Stack

- **Python 3.11+** - Programming language
- **FastAPI** - Modern web framework
- **SQLAlchemy** - ORM for database operations
- **SQLite** - Database (easily switchable to PostgreSQL)
- **Pydantic** - Data validation
- **Playwright** - Browser automation for capture
- **Pytest** - Testing framework
- **Google Gemini** - AI for schema inference (optional)
- **Docker** - Containerization

---

## 📚 Additional Documentation

- **[QUICK_START.md](QUICK_START.md)** - Quick start guide
- **[HOW_TO_RUN.md](HOW_TO_RUN.md)** - Detailed run instructions
- **[DEMO_SCRIPT.md](DEMO_SCRIPT.md)** - Demo walkthrough for interviews
- **[INTERVIEW_GUIDE.md](INTERVIEW_GUIDE.md)** - Interview preparation guide
- **[ASANA_REPLICATION_DETAILS.md](ASANA_REPLICATION_DETAILS.md)** - Technical deep dive
- **[PROJECT_EXPLANATION.md](PROJECT_EXPLANATION.md)** - What was built and how
- **[docs/AI_OVERVIEW.md](docs/AI_OVERVIEW.md)** - AI integration details

---

## 🎉 Project Status

**✅ COMPLETE AND FUNCTIONAL**

All goals achieved:
- ✅ Automated reverse engineering
- ✅ Functional backend clone
- ✅ Comprehensive testing
- ✅ Self-improvement loop
- ✅ Production-ready deployment

---

## 📊 By The Numbers

- **5,157+** CRUD operations captured
- **100+** entity types identified
- **20** functional endpoints generated
- **30** tests (all passing)
- **7** database tables
- **41.67%** quality score (improving)
- **0** external API dependencies

---

## 🎓 What This Demonstrates

This project proves that:
1. **AI and automation** can dramatically reduce reverse engineering effort
2. **WebSocket-based APIs** can be reverse-engineered with the right approach
3. **Code generation** can produce production-ready backends
4. **Self-improvement** is possible without external dependencies
5. **Complete automation** is achievable for complex systems

---

**Built with ❤️ using AI and automation**

For questions or issues, please open an issue on GitHub.
