from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel, Relationship


class Project(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None

    environments: list["Environment"] = Relationship(back_populates="project")
    targets: list["Target"] = Relationship(back_populates="project")


class Environment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    base_url: str
    config_json: dict = Field(default_factory=dict)
    project_id: int = Field(foreign_key="project.id")

    project: Optional[Project] = Relationship(back_populates="environments")
    ai_settings: Optional["EnvironmentAISettings"] = Relationship(back_populates="environment")
    targets: list["Target"] = Relationship(back_populates="environment")


class Target(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    base_url: str
    include_patterns: Optional[str] = None
    exclude_patterns: Optional[str] = None
    project_id: int = Field(foreign_key="project.id")
    environment_id: int = Field(foreign_key="environment.id")

    project: Optional[Project] = Relationship(back_populates="targets")
    environment: Optional[Environment] = Relationship(back_populates="targets")
    scan_jobs: list["ScanJob"] = Relationship(back_populates="target")


class ScanJobStatus(str):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"


class ScanJob(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    target_id: int = Field(foreign_key="target.id")
    status: str = Field(default=ScanJobStatus.PENDING)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = None
    stats_json: dict = Field(default_factory=dict)

    target: Optional[Target] = Relationship(back_populates="scan_jobs")
    pages: list["Page"] = Relationship(back_populates="scan_job")


class Page(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    scan_job_id: int = Field(foreign_key="scanjob.id")
    url: str
    status_code: int
    title: Optional[str] = None
    dom_ref: str
    meta_json: dict = Field(default_factory=dict)

    scan_job: Optional[ScanJob] = Relationship(back_populates="pages")
    analyses: list["AIAnalysis"] = Relationship(back_populates="page")


class AIProvider(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    type: str
    default_config: dict = Field(default_factory=dict)

    analyses: list["AIAnalysis"] = Relationship(back_populates="provider")
    environment_settings: list["EnvironmentAISettings"] = Relationship(back_populates="provider")


class EnvironmentAISettings(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    environment_id: int = Field(foreign_key="environment.id")
    provider_id: int = Field(foreign_key="aiprovider.id")
    endpoint: str
    api_key: Optional[str] = None
    model: Optional[str] = None
    proxy_enabled: bool = False
    proxy_url: Optional[str] = None
    proxy_type: Optional[str] = None

    environment: Optional[Environment] = Relationship(back_populates="ai_settings")
    provider: Optional[AIProvider] = Relationship(back_populates="environment_settings")


class AIAnalysisStatus(str):
    SUCCESS = "success"
    ERROR = "error"
    PROXY_ERROR = "proxy_error"
    TIMEOUT = "timeout"


class AIAnalysis(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    page_id: int = Field(foreign_key="page.id")
    provider_id: int = Field(foreign_key="aiprovider.id")
    status: str = Field(default=AIAnalysisStatus.SUCCESS)
    request_timestamp: datetime = Field(default_factory=datetime.utcnow)
    response_json: dict = Field(default_factory=dict)
    error_message: Optional[str] = None

    page: Optional[Page] = Relationship(back_populates="analyses")
    provider: Optional[AIProvider] = Relationship(back_populates="analyses")


class Suite(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    project_id: int = Field(foreign_key="project.id")
    description: Optional[str] = None


class TestCase(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    suite_id: int = Field(foreign_key="suite.id")
    name: str
    description: Optional[str] = None
    steps: list[str] = Field(default_factory=list, sa_column_kwargs={"type_": "JSON"})
    assertions: list[str] = Field(default_factory=list, sa_column_kwargs={"type_": "JSON"})


class TestRun(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    suite_id: int = Field(foreign_key="suite.id")
    environment_id: int = Field(foreign_key="environment.id")
    trigger: str = "manual"
    started_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = None
    status: str = Field(default="running")


class TestRunItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    test_run_id: int = Field(foreign_key="testrun.id")
    test_case_id: int = Field(foreign_key="testcase.id")
    status: str = "pending"
    log: Optional[str] = None
    screenshot_path: Optional[str] = None
