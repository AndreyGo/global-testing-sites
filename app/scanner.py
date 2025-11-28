from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Iterable
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup
from sqlmodel import select

from .database import get_session
from .models import Page, ScanJob, ScanJobStatus, Target


async def fetch_html(url: str, timeout: float = 10.0) -> tuple[str, int]:
    async with httpx.AsyncClient(follow_redirects=True, timeout=timeout) as client:
        response = await client.get(url)
        return response.text, response.status_code


def extract_links(html: str, base_url: str, limit: int = 5) -> Iterable[str]:
    soup = BeautifulSoup(html, "html.parser")
    links: list[str] = []
    for anchor in soup.find_all("a"):
        href = anchor.get("href")
        if not href:
            continue
        absolute = urljoin(base_url, href)
        if absolute not in links:
            links.append(absolute)
        if len(links) >= limit:
            break
    return links


async def scan_target(target_id: int, follow_links: bool = True) -> ScanJob:
    """Run a lightweight scan storing DOM snapshots for a target."""
    with get_session() as session:
        target = session.exec(select(Target).where(Target.id == target_id)).one()
        job = ScanJob(target_id=target_id, status=ScanJobStatus.RUNNING, started_at=datetime.utcnow())
        session.add(job)
        session.commit()
        session.refresh(job)

    pages_seen = 0
    stats = {"pages": 0, "errors": 0}
    discovered_urls = [target.base_url]

    async def process_url(url: str) -> None:
        nonlocal pages_seen
        try:
            html, status_code = await fetch_html(url)
            pages_seen += 1
            with get_session() as session:
                page = Page(
                    scan_job_id=job.id,
                    url=url,
                    status_code=status_code,
                    title=BeautifulSoup(html, "html.parser").title.string if BeautifulSoup(html, "html.parser").title else None,
                    dom_ref=html,
                    meta_json={"timestamp": datetime.utcnow().isoformat()},
                )
                session.add(page)
                session.commit()
            if follow_links:
                for link in extract_links(html, url):
                    if link not in discovered_urls and link.startswith(target.base_url):
                        discovered_urls.append(link)
        except Exception:
            stats["errors"] += 1

    await asyncio.gather(*(process_url(url) for url in list(discovered_urls)))

    with get_session() as session:
        job = session.exec(select(ScanJob).where(ScanJob.id == job.id)).one()
        job.status = ScanJobStatus.SUCCESS if stats["errors"] == 0 else ScanJobStatus.ERROR
        job.finished_at = datetime.utcnow()
        job.stats_json = {"pages": pages_seen, **stats}
        session.add(job)
        session.commit()
        session.refresh(job)
    return job
