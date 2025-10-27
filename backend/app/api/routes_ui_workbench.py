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

@router.get("/ui/rule-editor", response_class=HTMLResponse)
@router.get("/ui/rule-editor/{rule_id}", response_class=HTMLResponse)
def rule_editor(request: Request, rule_id: str | None = None):
    """
    Full-page Rule Authoring UI.
    If rule_id is provided, the page loads in 'Edit Mode'.
    """
    context = {"request": request}
    if rule_id:
        context["rule_id"] = rule_id  # Optional, in case you want to use in Jinja
    return templates.TemplateResponse("workbench/rule_editor.html", context)

