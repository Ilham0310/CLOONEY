-- Asana API Clone Database Schema
-- Generated from network traffic analysis

-- Table: projects
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    _lastModified TIMESTAMP NOT NULL,
    integrations JSONB NOT NULL,
    plan JSONB NOT NULL,
    edgeFunction JSONB NOT NULL,
    analyticsNextEnabled BOOLEAN NOT NULL,
    middlewareSettings VARCHAR(255) NOT NULL,
    enabledMiddleware VARCHAR(255) NOT NULL,
    metrics JSONB NOT NULL,
    legacyVideoPluginsEnabled VARCHAR(255) NOT NULL,
    remotePlugins JSONB NOT NULL,
    autoInstrumentationSettings JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_projects_created_at ON projects(created_at);

-- Junction Tables for Many-to-Many Relationships

CREATE TABLE IF NOT EXISTS project_members (
    project_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    role VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (project_id, user_id),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_project_members_project_id ON project_members(project_id);
CREATE INDEX IF NOT EXISTS idx_project_members_user_id ON project_members(user_id);

CREATE TABLE IF NOT EXISTS task_followers (
    task_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (task_id, user_id),
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_task_followers_task_id ON task_followers(task_id);
CREATE INDEX IF NOT EXISTS idx_task_followers_user_id ON task_followers(user_id);

-- Foreign Key Constraints
ALTER TABLE tasks ADD CONSTRAINT fk_tasks_project_id FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE;
ALTER TABLE tasks ADD CONSTRAINT fk_tasks_section_id FOREIGN KEY (section_id) REFERENCES sections(id) ON DELETE CASCADE;
ALTER TABLE tasks ADD CONSTRAINT fk_tasks_assignee_id FOREIGN KEY (assignee_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE sections ADD CONSTRAINT fk_sections_project_id FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE;
ALTER TABLE projects ADD CONSTRAINT fk_projects_workspace_id FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE;
ALTER TABLE projects ADD CONSTRAINT fk_projects_team_id FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE;
