from __future__ import annotations

import os
from functools import wraps
from typing import Dict, List

from flask import Flask, flash, redirect, render_template, request, session, url_for


app = Flask(__name__)
app.secret_key = os.getenv("APP_SECRET_KEY", "dev-secret-key")


User = Dict[str, str]
Assertion = Dict[str, str]
TestCase = Dict[str, object]
Page = Dict[str, object]
Domain = Dict[str, object]
Project = Dict[str, object]


USER_STORE: List[User] = [
    {"username": "admin", "password": os.getenv("APP_ADMIN_PASSWORD", "password")},
]

PROJECTS: List[Project] = [
    {
        "id": "alpha",
        "name": "Alpha Commerce",
        "description": "Магазин электроники с промо-страницами и блочным каталогом.",
        "domains": [
            {
                "name": "alpha.shop",
                "environment": "production",
                "url": "https://alpha.shop",
                "status": "online",
                "pages": [
                    {"path": "/", "title": "Главная", "status": 200, "last_scan": "Сегодня, 10:15"},
                    {
                        "path": "/products",
                        "title": "Каталог",
                        "status": 200,
                        "last_scan": "Сегодня, 10:17",
                    },
                    {
                        "path": "/checkout",
                        "title": "Оформление",
                        "status": 302,
                        "last_scan": "Сегодня, 10:20",
                    },
                ],
                "tests": [
                    {
                        "name": "Покупка в один клик",
                        "last_run": "Сегодня, 10:25",
                        "status": "passed",
                        "assertions": [
                            {"description": "Кнопка 'Купить' доступна", "status": "passed"},
                            {"description": "Форма телефона валидируется", "status": "passed"},
                            {"description": "Переход к оплате открывается", "status": "passed"},
                        ],
                    },
                    {
                        "name": "Авторизация",
                        "last_run": "Сегодня, 10:12",
                        "status": "failed",
                        "assertions": [
                            {"description": "Форма логина загружается", "status": "passed"},
                            {"description": "Неверный пароль даёт ошибку", "status": "failed"},
                        ],
                    },
                ],
            }
        ],
    },
    {
        "id": "beta",
        "name": "Beta Travel",
        "description": "Бронирование туров и динамическое расписание перелётов.",
        "domains": [
            {
                "name": "beta.travel",
                "environment": "staging",
                "url": "https://staging.beta.travel",
                "status": "maintenance",
                "pages": [
                    {"path": "/", "title": "Главная", "status": 200, "last_scan": "Вчера, 19:40"},
                    {
                        "path": "/search",
                        "title": "Поиск туров",
                        "status": 200,
                        "last_scan": "Вчера, 19:42",
                    },
                    {
                        "path": "/cabinet",
                        "title": "Личный кабинет",
                        "status": 401,
                        "last_scan": "Вчера, 19:55",
                    },
                ],
                "tests": [
                    {
                        "name": "Поиск тура",
                        "last_run": "Вчера, 20:05",
                        "status": "passed",
                        "assertions": [
                            {"description": "Карточки туров отображаются", "status": "passed"},
                            {"description": "Фильтр по дате работает", "status": "passed"},
                        ],
                    },
                    {
                        "name": "Сброс пароля",
                        "last_run": "Вчера, 20:15",
                        "status": "blocked",
                        "assertions": [
                            {"description": "Форма запроса кода отправляется", "status": "blocked"},
                            {"description": "Ввод нового пароля доступен", "status": "blocked"},
                        ],
                    },
                ],
            }
        ],
    },
]


STATUS_BADGES = {
    "passed": "success",
    "failed": "danger",
    "blocked": "secondary",
    "online": "success",
    "maintenance": "warning",
}


def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if not session.get("user"):
            flash("Пожалуйста, авторизуйтесь для просмотра проектов.", "warning")
            return redirect(url_for("login", next=request.path))
        return view(**kwargs)

    return wrapped_view


def authenticate(username: str, password: str) -> bool:
    return any(user for user in USER_STORE if user["username"] == username and user["password"] == password)


@app.context_processor
def inject_badges():
    return {"status_badges": STATUS_BADGES}


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user"):
        return redirect(url_for("dashboard"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        if authenticate(username, password):
            session["user"] = username
            flash("Добро пожаловать!", "success")
            next_page = request.args.get("next") or url_for("dashboard")
            return redirect(next_page)
        error = "Неверное имя пользователя или пароль"
    return render_template("login.html", error=error)


@app.route("/logout")
@login_required
def logout():
    session.pop("user", None)
    flash("Вы вышли из системы", "info")
    return redirect(url_for("login"))


@app.route("/")
@login_required
def dashboard():
    return render_template("dashboard.html", projects=PROJECTS)


@app.route("/projects/<project_id>")
@login_required
def project_detail(project_id: str):
    project = next((project for project in PROJECTS if project["id"] == project_id), None)
    if not project:
        flash("Проект не найден", "danger")
        return redirect(url_for("dashboard"))
    return render_template("project_detail.html", project=project)


if __name__ == "__main__":
    app.run(debug=True)
