from __future__ import annotations

import asyncio
from pathlib import Path

import typer
from rich import print

from .database import init_db
from .scanner import scan_target
from .test_runner import run_suite

app = typer.Typer(help="CLI для управления тестированием и сканами")


@app.command()
def init() -> None:
    """Создать базу данных и таблицы."""
    init_db()
    print("[green]База инициализирована[/green]")


@app.command()
def scan(target_id: int) -> None:
    """Запустить сканирование для указанного target."""
    init_db()
    asyncio.run(scan_target(target_id))
    print(f"[green]Сканирование для target {target_id} завершено[/green]")


@app.command()
def run_suite_cmd(suite_id: int, environment_id: int, trigger: str = "manual") -> None:
    """Запустить suite (для Cron)."""
    init_db()
    result = run_suite(suite_id, environment_id, trigger=trigger)
    print(f"[green]Suite {suite_id} завершён со статусом {result.status}[/green]")


@app.command()
def cron_example() -> None:
    """Показать пример строки для crontab."""
    command = "python -m app.cli run-suite-cmd --suite-id=1 --environment-id=1 --trigger=cron"
    cron_line = f"0 3 * * * {command} >> /var/log/test_runner.log 2>&1"
    print(cron_line)


if __name__ == "__main__":
    app()
