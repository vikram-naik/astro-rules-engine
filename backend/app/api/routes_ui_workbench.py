# app/api/routes_ui_workbench.py
"""
UI Workbench Router
Serves the single-page workbench UI (Jinja2 template).
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.main import templates

router = APIRouter(tags=["ui"])


@router.get("/ui/workbench", response_class=HTMLResponse)
def workbench(request: Request):
    """
    Main workbench page. The page uses AJAX to call JSON APIs for
    rules, sectors and correlation.
    """
    return templates.TemplateResponse("workbench.html", {"request": request})
