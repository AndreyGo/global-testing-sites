from __future__ import annotations

from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException
from sqlmodel import Session, select

from .ai import DOMAIAnalyzer
from .database import get_session, init_db
from .models import (
    AIAnalysis,
    AIAnalysisStatus,
    AIProvider,
    Environment,
    EnvironmentAISettings,
    Page,
    Project,
    ScanJob,
    Suite,
    Target,
    TestCase,
)
from .scanner import scan_target
from .test_runner import run_suite

app = FastAPI(title="Global Testing Sites")


def get_db() -> Session:
    with get_session() as session:
        yield session


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.post("/projects", response_model=Project)
def create_project(project: Project, db: Session = Depends(get_db)) -> Project:
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@app.get("/projects", response_model=List[Project])
def list_projects(db: Session = Depends(get_db)) -> List[Project]:
    return list(db.exec(select(Project)))


@app.post("/environments", response_model=Environment)
def create_environment(environment: Environment, db: Session = Depends(get_db)) -> Environment:
    db.add(environment)
    db.commit()
    db.refresh(environment)
    return environment


@app.post("/targets", response_model=Target)
def create_target(target: Target, db: Session = Depends(get_db)) -> Target:
    db.add(target)
    db.commit()
    db.refresh(target)
    return target


@app.post("/scan/{target_id}", response_model=ScanJob)
async def run_scan(target_id: int) -> ScanJob:
    return await scan_target(target_id)


@app.get("/pages", response_model=List[Page])
def list_pages(scan_job_id: Optional[int] = None, db: Session = Depends(get_db)) -> List[Page]:
    query = select(Page)
    if scan_job_id:
        query = query.where(Page.scan_job_id == scan_job_id)
    return list(db.exec(query))


@app.post("/ai/providers", response_model=AIProvider)
def register_provider(provider: AIProvider, db: Session = Depends(get_db)) -> AIProvider:
    db.add(provider)
    db.commit()
    db.refresh(provider)
    return provider


@app.post("/ai/settings", response_model=EnvironmentAISettings)
def configure_environment_ai(settings: EnvironmentAISettings, db: Session = Depends(get_db)) -> EnvironmentAISettings:
    db.add(settings)
    db.commit()
    db.refresh(settings)
    return settings


@app.post("/ai/analyze/{page_id}", response_model=AIAnalysis)
def analyze_page(page_id: int, db: Session = Depends(get_db)) -> AIAnalysis:
    page = db.exec(select(Page).where(Page.id == page_id)).one_or_none()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    provider = db.exec(select(AIProvider)).first()
    if not provider:
        provider = AIProvider(name="local", type="heuristic")
        db.add(provider)
        db.commit()
        db.refresh(provider)

    analyzer = DOMAIAnalyzer()
    try:
        response_json = analyzer.analyze(page.dom_ref, page.url)
        analysis = AIAnalysis(page_id=page.id, provider_id=provider.id, status=AIAnalysisStatus.SUCCESS, response_json=response_json)
    except Exception as exc:  # noqa: BLE001
        analysis = AIAnalysis(page_id=page.id, provider_id=provider.id, status=AIAnalysisStatus.ERROR, error_message=str(exc))
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis


@app.post("/suites", response_model=Suite)
def create_suite(suite: Suite, db: Session = Depends(get_db)) -> Suite:
    db.add(suite)
    db.commit()
    db.refresh(suite)
    return suite


@app.post("/testcases", response_model=TestCase)
def create_test_case(test_case: TestCase, db: Session = Depends(get_db)) -> TestCase:
    db.add(test_case)
    db.commit()
    db.refresh(test_case)
    return test_case


@app.post("/runs/{suite_id}")
def trigger_suite_run(suite_id: int, environment_id: int, trigger: str = "manual") -> dict[str, str]:
    run_suite(suite_id, environment_id, trigger=trigger)
    return {"status": "scheduled"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
