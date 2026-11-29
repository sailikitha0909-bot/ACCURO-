import pytest
from datetime import datetime, timezone
from fastapi import HTTPException
from app.main import health_check
from app.api.entries import approve_entry, update_entry
from app.api.auth import login
from app.schemas import UserLogin, EntryUpdate
from app.core.security import get_password_hash
from app.models import Organization, User, Client, Entry

def test_health_check_endpoint():
    res = health_check()
    assert res["status"] == "healthy"
    assert res["app"] == "Accuro"
    assert "Accurate accounts" in res["tagline"]

def test_partner_vs_article_rbac_logic(db_session):
    org = Organization(name="Mehta & Associates", contact_email="admin@mehta.in")
    db_session.add(org)
    db_session.flush()

    partner = User(
        organization_id=org.id,
        email="partner@mehta.in",
        hashed_password=get_password_hash("PartnerPass123!"),
        full_name="CA Rajesh Mehta",
        role="partner",
        is_active=True
    )
    article = User(
        organization_id=org.id,
        email="article@mehta.in",
        hashed_password=get_password_hash("ArticlePass123!"),
        full_name="Pooja Article",
        role="article",
        is_active=True
    )
    client_obj = Client(
        organization_id=org.id,
        legal_name="Apex Retailers Pvt Ltd",
        state_code="27"
    )
    db_session.add_all([partner, article, client_obj])
    db_session.flush()

    entry = Entry(
        organization_id=org.id,
        client_id=client_obj.id,
        financial_year_id="dummy-fy",
        invoice_number="INV-RBAC-01",
        invoice_date=datetime(2024, 7, 1, tzinfo=timezone.utc),
        party_name="Vendor A",
        place_of_supply="27",
        taxable_value_paise=100000,
        total_amount_paise=118000,
        status="draft"
    )
    db_session.add(entry)
    db_session.commit()

    # 1. Partner approves entry -> Succeeds, sets status to 'final'
    res = approve_entry(entry_id=entry.id, current_user=partner, db=db_session)
    assert res.status == "final"
    assert res.approved_by_user_id == partner.id

def test_article_can_edit_entry(db_session):
    org = Organization(name="Mehta & Associates", contact_email="admin2@mehta.in")
    db_session.add(org)
    db_session.flush()

    article = User(
        organization_id=org.id,
        email="article2@mehta.in",
        hashed_password=get_password_hash("ArticlePass123!"),
        full_name="Pooja Article",
        role="article",
        is_active=True
    )
    client_obj = Client(
        organization_id=org.id,
        legal_name="Zenith Tech",
        state_code="29"
    )
    db_session.add_all([article, client_obj])
    db_session.flush()

    entry = Entry(
        organization_id=org.id,
        client_id=client_obj.id,
        financial_year_id="dummy-fy",
        invoice_number="INV-EDIT-01",
        invoice_date=datetime(2024, 7, 2, tzinfo=timezone.utc),
        party_name="Vendor Old",
        place_of_supply="29",
        taxable_value_paise=200000,
        total_amount_paise=236000,
        status="draft"
    )
    db_session.add(entry)
    db_session.commit()

    # Article edits entry
    update_data = EntryUpdate(party_name="Vendor New Name", taxable_value_paise=250000)
    updated = update_entry(entry_id=entry.id, entry_update=update_data, current_user=article, db=db_session)
    assert updated.party_name == "Vendor New Name"
    assert updated.taxable_value_paise == 250000
