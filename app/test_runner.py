from __future__ import annotations

from datetime import datetime

import httpx
from sqlmodel import select

from .database import get_session
from .models import Environment, Page, Suite, TestCase, TestRun, TestRunItem


def execute_test_case(test_case: TestCase, environment: Environment) -> tuple[str, str]:
    """Very small runtime: fetch base URL and mark success if reachable."""
    try:
        response = httpx.get(environment.base_url, timeout=10.0)
        if response.status_code < 400:
            return "passed", f"Reached {environment.base_url} for {test_case.name}"
        return "failed", f"Unexpected status {response.status_code} for {environment.base_url}"
    except Exception as exc:  # noqa: BLE001
        return "failed", str(exc)


def run_suite(suite_id: int, environment_id: int, trigger: str = "manual") -> TestRun:
    with get_session() as session:
        suite = session.exec(select(Suite).where(Suite.id == suite_id)).one()
        environment = session.exec(select(Environment).where(Environment.id == environment_id)).one()
        test_run = TestRun(suite_id=suite.id, environment_id=environment.id, trigger=trigger)
        session.add(test_run)
        session.commit()
        session.refresh(test_run)

        cases = session.exec(select(TestCase).where(TestCase.suite_id == suite.id)).all()
        for case in cases:
            item = TestRunItem(test_run_id=test_run.id, test_case_id=case.id, status="running")
            session.add(item)
            session.commit()
            item.status, item.log = execute_test_case(case, environment)
            session.add(item)
            session.commit()

        test_run.finished_at = datetime.utcnow()
        test_run.status = "passed" if all(case.status == "passed" for case in session.exec(select(TestRunItem).where(TestRunItem.test_run_id == test_run.id))) else "failed"
        session.add(test_run)
        session.commit()
        session.refresh(test_run)
        return test_run


def build_test_map_from_pages(pages: list[Page]) -> list[TestCase]:
    """Generate naive test cases from AI analysis placeholders."""
    generated: list[TestCase] = []
    for page in pages:
        generated.append(
            TestCase(
                suite_id=0,
                name=f"Smoke check for {page.url}",
                steps=["Open page", "Validate status"],
                assertions=["Status < 400", "Title present"],
            )
        )
    return generated
