# app/api/routes_ui_workbench.py
"""
UI Workbench Router
Serves the single-page workbench UI (Jinja2 template).
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["ui"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/ui/workbench", response_class=HTMLResponse)
def workbench(request: Request):
    """
    Main workbench page. The page uses AJAX to call JSON APIs for
    rules, sectors and correlation.
    """
    return templates.TemplateResponse("workbench.html", {"request": request})
