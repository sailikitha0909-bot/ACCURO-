from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import CategorisationRule, User, ChartOfAccount
from app.schemas import RuleCreate, RuleOut
from app.api.deps import get_current_user, require_role

router = APIRouter(prefix="/rules", tags=["Categorisation Rules"])

@router.get("", response_model=List[RuleOut])
def list_rules(
    client_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(CategorisationRule).filter(
        CategorisationRule.organization_id == current_user.organization_id
    )
    if client_id:
        query = query.filter(CategorisationRule.client_id == client_id)

    return query.order_by(CategorisationRule.usage_count.desc()).all()

@router.post("", response_model=RuleOut)
def create_rule(
    rule_in: RuleCreate,
    current_user: User = Depends(require_role(["partner", "article"])),
    db: Session = Depends(get_db)
):
    rule = CategorisationRule(
        organization_id=current_user.organization_id,
        client_id=rule_in.client_id,
        rule_type=rule_in.rule_type,
        match_pattern=rule_in.match_pattern.strip(),
        target_account_id=rule_in.target_account_id,
        confidence=1.0,
        source="manual_rule"
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule

@router.delete("/{rule_id}")
def delete_rule(
    rule_id: str,
    current_user: User = Depends(require_role(["partner"])),
    db: Session = Depends(get_db)
):
    rule = db.query(CategorisationRule).filter(
        CategorisationRule.id == rule_id,
        CategorisationRule.organization_id == current_user.organization_id
    ).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    db.delete(rule)
    db.commit()
    return {"status": "success", "message": "Rule deleted"}
