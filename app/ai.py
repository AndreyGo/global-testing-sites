from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .models import AIAnalysisStatus


class DOMAIAnalyzer:
    """Lightweight heuristic AI replacement for local testing."""

    def __init__(self, proxy_url: str | None = None) -> None:
        self.proxy_url = proxy_url

    def analyze(self, html: str, url: str) -> dict[str, Any]:
        soup = BeautifulSoup(html, "html.parser")
        forms = soup.find_all("form")
        buttons = soup.find_all("button")
        inputs = soup.find_all("input")
        links = soup.find_all("a")

        test_points: list[dict[str, Any]] = []
        for form in forms:
            name = form.get("id") or form.get("name") or "form"
            test_points.append(
                {
                    "type": "form_submission",
                    "description": f"Validate form '{name}' submission on {url}",
                    "assertions": ["form renders", "submission returns success status"],
                }
            )

        for button in buttons:
            label = button.get_text(strip=True) or button.get("aria-label") or "button"
            test_points.append(
                {
                    "type": "click_path",
                    "description": f"Click '{label}' on {url} and ensure key content updates",
                    "assertions": ["button visible", "expected content appears after click"],
                }
            )

        for link in links[:10]:
            href = link.get("href") or ""
            label = link.get_text(strip=True) or href
            test_points.append(
                {
                    "type": "navigation",
                    "description": f"Follow link '{label}' from {url}",
                    "assertions": ["link resolves", "page contains title"],
                }
            )

        if not test_points:
            test_points.append(
                {
                    "type": "presence",
                    "description": f"Validate page {url} loads with status 200",
                    "assertions": ["page reachable", "title available"],
                }
            )

        return {
            "status": AIAnalysisStatus.SUCCESS,
            "url": url,
            "summary": {
                "forms": len(forms),
                "buttons": len(buttons),
                "inputs": len(inputs),
                "links": len(links),
            },
            "test_points": test_points,
        }
