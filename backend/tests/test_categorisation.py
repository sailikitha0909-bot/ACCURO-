from app.services.categorisation_engine import CategorisationEngine
from app.models import Organization, Client, ChartOfAccount, CategorisationRule

def test_categorisation_three_tier_resolution(db_session):
    org = Organization(name="CA Test", contact_email="test@ca.in")
    db_session.add(org)
    db_session.flush()

    client = Client(organization_id=org.id, legal_name="Apex Test", state_code="27")
    db_session.add(client)
    db_session.flush()

    # Add Chart of Account ledgers
    acc_sw = ChartOfAccount(client_id=client.id, account_code="4010", account_name="Software Subscriptions", account_type="expense", parent_group="Indirect Expenses")
    acc_legal = ChartOfAccount(client_id=client.id, account_code="4020", account_name="Legal Fees", account_type="expense", parent_group="Indirect Expenses")
    db_session.add_all([acc_sw, acc_legal])
    db_session.flush()

    # 1. Vendor Rule Match
    acc_id, conf, src = CategorisationEngine.resolve_category(db=db_session, client_id=client.id, party_name="Amazon Web Services")
    assert acc_id == acc_sw.id
    assert conf >= 0.90

    # 2. CA Correction Learning: CA changes vendor to Legal Fees
    CategorisationEngine.learn_ca_correction(
        db=db_session,
        organization_id=org.id,
        client_id=client.id,
        party_name="Amazon Web Services",
        target_account_id=acc_legal.id
    )

    # 3. Subsequent resolution must now resolve to Learned CA Correction
    acc_id_learned, conf_learned, src_learned = CategorisationEngine.resolve_category(
        db=db_session,
        client_id=client.id,
        party_name="Amazon Web Services"
    )
    assert acc_id_learned == acc_legal.id
    assert conf_learned == 0.99
    assert src_learned == "learned_ca_correction"
