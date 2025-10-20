# backend/app/api/routes_ui.py
"""
UI Routes
---------
Serves Bootstrap-based HTML pages for rule CRUD operations.
"""

from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from app.core.common.db import get_session
from app.core.common.models import RuleModel
from sqlmodel import select
import json

router = APIRouter(tags=["ui"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/ui/rules", response_class=HTMLResponse)
def list_rules(request: Request):
    """Display all rules."""
    with get_session() as session:
        rules = session.exec(select(RuleModel)).all()
    return templates.TemplateResponse("rules.html", {"request": request, "rules": rules})


@router.post("/ui/rules/add")
def add_rule(
    name: str = Form(...),
    description: str = Form(""),
    confidence: float = Form(1.0),
):
    """Add a new rule (simplified form version)."""
    from uuid import uuid4

    rule = RuleModel(
        rule_id=f"UI_{uuid4().hex[:8]}",
        name=name,
        description=description,
        conditions_json=json.dumps([]),
        outcomes_json=json.dumps([]),
        enabled=True,
        confidence=confidence,
    )

    with get_session() as session:
        session.add(rule)
        session.commit()

    return RedirectResponse(url="/ui/rules", status_code=303)


@router.post("/ui/rules/delete/{rule_id}")
def delete_rule(rule_id: str):
    """Delete a rule by rule_id."""
    with get_session() as session:
        rule = session.exec(select(RuleModel).where(RuleModel.rule_id == rule_id)).first()
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")
        session.delete(rule)
        session.commit()

    return RedirectResponse(url="/ui/rules", status_code=303)
