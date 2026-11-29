"""001_initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-11-28 20:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. organizations
    op.create_table(
        'organizations',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('firm_registration_number', sa.String(length=50), nullable=True),
        sa.Column('contact_email', sa.String(length=255), nullable=False, unique=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('settings', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )

    # 2. users
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('organization_id', sa.String(length=36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False, index=True),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), server_default='article'),
        sa.Column('is_active', sa.Boolean(), server_default='1'),
        sa.Column('is_verified', sa.Boolean(), server_default='1'),
        sa.Column('totp_secret', sa.String(length=64), nullable=True),
        sa.Column('totp_enabled', sa.Boolean(), server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
    )

    # 3. clients
    op.create_table(
        'clients',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('organization_id', sa.String(length=36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('legal_name', sa.String(length=255), nullable=False),
        sa.Column('trade_name', sa.String(length=255), nullable=True),
        sa.Column('gstin', sa.String(length=50), nullable=True, index=True),
        sa.Column('pan', sa.String(length=20), nullable=True, index=True),
        sa.Column('state_code', sa.String(length=5), nullable=False),
        sa.Column('entity_type', sa.String(length=50), server_default='private_limited'),
        sa.Column('contact_person', sa.String(length=255), nullable=True),
        sa.Column('contact_email', sa.String(length=255), nullable=True),
        sa.Column('contact_phone', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='1'),
        sa.Column('dpdp_consent', sa.Boolean(), server_default='1'),
        sa.Column('retention_period_years', sa.Integer(), server_default='8'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )

    # 4. financial_years
    op.create_table(
        'financial_years',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('client_id', sa.String(length=36), sa.ForeignKey('clients.id', ondelete='CASCADE'), nullable=False),
        sa.Column('year_label', sa.String(length=20), nullable=False),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_locked', sa.Boolean(), server_default='0'),
        sa.Column('locked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('locked_by_user_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    )

    # 5. chart_of_accounts
    op.create_table(
        'chart_of_accounts',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('client_id', sa.String(length=36), sa.ForeignKey('clients.id', ondelete='CASCADE'), nullable=False),
        sa.Column('account_code', sa.String(length=50), nullable=False),
        sa.Column('account_name', sa.String(length=255), nullable=False),
        sa.Column('account_type', sa.String(length=50), nullable=False),
        sa.Column('parent_group', sa.String(length=100), nullable=False),
        sa.Column('is_system_default', sa.Boolean(), server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    )

    # 6. documents
    op.create_table(
        'documents',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('organization_id', sa.String(length=36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('client_id', sa.String(length=36), sa.ForeignKey('clients.id', ondelete='CASCADE'), nullable=False),
        sa.Column('financial_year_id', sa.String(length=36), nullable=True),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('storage_path', sa.String(length=500), nullable=False),
        sa.Column('file_type', sa.String(length=20), nullable=False),
        sa.Column('file_size_bytes', sa.BigInteger(), nullable=False),
        sa.Column('sha256_hash', sa.String(length=64), nullable=False, index=True),
        sa.Column('doc_type', sa.String(length=50), server_default='purchase_invoice'),
        sa.Column('status', sa.String(length=50), server_default='queued'),
        sa.Column('uploaded_by_user_id', sa.String(length=36), nullable=True),
        sa.Column('portal_token_id', sa.String(length=36), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('ocr_raw_text', sa.Text(), nullable=True),
        sa.Column('extraction_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
    )

    # 7. entries
    op.create_table(
        'entries',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('organization_id', sa.String(length=36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('client_id', sa.String(length=36), sa.ForeignKey('clients.id', ondelete='CASCADE'), nullable=False),
        sa.Column('financial_year_id', sa.String(length=36), nullable=False),
        sa.Column('document_id', sa.String(length=36), nullable=True, unique=True),
        sa.Column('entry_type', sa.String(length=50), server_default='purchase'),
        sa.Column('voucher_number', sa.String(length=100), nullable=True),
        sa.Column('invoice_number', sa.String(length=100), nullable=False, index=True),
        sa.Column('invoice_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('party_name', sa.String(length=255), nullable=False),
        sa.Column('party_gstin', sa.String(length=50), nullable=True, index=True),
        sa.Column('place_of_supply', sa.String(length=5), nullable=False),
        sa.Column('reverse_charge', sa.Boolean(), server_default='0'),
        sa.Column('taxable_value_paise', sa.BigInteger(), server_default='0'),
        sa.Column('cgst_paise', sa.BigInteger(), server_default='0'),
        sa.Column('sgst_paise', sa.BigInteger(), server_default='0'),
        sa.Column('igst_paise', sa.BigInteger(), server_default='0'),
        sa.Column('cess_paise', sa.BigInteger(), server_default='0'),
        sa.Column('round_off_paise', sa.BigInteger(), server_default='0'),
        sa.Column('total_amount_paise', sa.BigInteger(), server_default='0'),
        sa.Column('tds_section', sa.String(length=50), nullable=True),
        sa.Column('tds_rate', sa.Float(), nullable=True),
        sa.Column('tds_amount_paise', sa.BigInteger(), server_default='0'),
        sa.Column('line_items', sa.JSON(), nullable=True),
        sa.Column('debit_account_id', sa.String(length=36), nullable=True),
        sa.Column('credit_account_id', sa.String(length=36), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='draft', index=True),
        sa.Column('is_itc_eligible', sa.Boolean(), server_default='1'),
        sa.Column('itc_blocked_reason', sa.String(length=255), nullable=True),
        sa.Column('approved_by_user_id', sa.String(length=36), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )

    # 8. exceptions
    op.create_table(
        'exceptions',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('organization_id', sa.String(length=36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('client_id', sa.String(length=36), sa.ForeignKey('clients.id', ondelete='CASCADE'), nullable=False),
        sa.Column('document_id', sa.String(length=36), nullable=True),
        sa.Column('entry_id', sa.String(length=36), nullable=True),
        sa.Column('severity', sa.String(length=20), nullable=False, index=True),
        sa.Column('exception_type', sa.String(length=50), nullable=False, index=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('evidence', sa.JSON(), nullable=True),
        sa.Column('suggested_fix', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='open', index=True),
        sa.Column('assigned_to_user_id', sa.String(length=36), nullable=True),
        sa.Column('resolved_by_user_id', sa.String(length=36), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolution_note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    )

    # 9. categorisation_rules
    op.create_table(
        'categorisation_rules',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('organization_id', sa.String(length=36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('client_id', sa.String(length=36), sa.ForeignKey('clients.id', ondelete='CASCADE'), nullable=False),
        sa.Column('rule_type', sa.String(length=50), nullable=False),
        sa.Column('match_pattern', sa.String(length=255), nullable=False),
        sa.Column('target_account_id', sa.String(length=36), nullable=False),
        sa.Column('confidence', sa.Float(), server_default='1.0'),
        sa.Column('source', sa.String(length=50), server_default='learned_ca_correction'),
        sa.Column('usage_count', sa.Integer(), server_default='0'),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    )

    # 10. audit_logs
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('organization_id', sa.String(length=36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=True, index=True),
    )

def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('categorisation_rules')
    op.drop_table('exceptions')
    op.drop_table('entries')
    op.drop_table('documents')
    op.drop_table('chart_of_accounts')
    op.drop_table('financial_years')
    op.drop_table('clients')
    op.drop_table('users')
    op.drop_table('organizations')
