from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Document, Entry, ExceptionRecord, Organization, Client
from app.core.config import settings

class MetricsService:
    @staticmethod
    def get_dashboard_metrics(
        db: Session,
        organization_id: str,
        client_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Computes real operational and productivity metrics directly from the DB.
        Formula for Hours Saved:
        Hours Saved = (Documents Processed * Benchmark Mins [e.g. 15 min] - Total Actual CA Review Minutes) / 60
        """
        # Base queries scoped to organization
        doc_query = db.query(Document).filter(Document.organization_id == organization_id)
        exc_query = db.query(ExceptionRecord).filter(ExceptionRecord.organization_id == organization_id)
        entry_query = db.query(Entry).filter(Entry.organization_id == organization_id)

        if client_id:
            doc_query = doc_query.filter(Document.client_id == client_id)
            exc_query = exc_query.filter(ExceptionRecord.client_id == client_id)
            entry_query = entry_query.filter(Entry.client_id == client_id)

        total_docs = doc_query.count()
        done_docs = doc_query.filter(Document.status.in_(["done", "needs_attention"])).count()
        failed_docs = doc_query.filter(Document.status == "failed").count()
        queued_docs = doc_query.filter(Document.status == "queued").count()
        processing_docs = doc_query.filter(Document.status == "processing").count()

        # Exceptions
        open_high = exc_query.filter(ExceptionRecord.status == "open", ExceptionRecord.severity == "high").count()
        open_medium = exc_query.filter(ExceptionRecord.status == "open", ExceptionRecord.severity == "medium").count()
        open_low = exc_query.filter(ExceptionRecord.status == "open", ExceptionRecord.severity == "low").count()
        total_open_exceptions = open_high + open_medium + open_low
        resolved_exceptions = exc_query.filter(ExceptionRecord.status == "resolved").count()

        # Auto-cleared %: Documents that have 0 high or medium exceptions
        # (AI completed first pass without needing urgent human intervention)
        docs_with_blocking_issues = db.query(ExceptionRecord.document_id).filter(
            ExceptionRecord.organization_id == organization_id,
            ExceptionRecord.severity.in_(["high", "medium"])
        ).distinct()
        if client_id:
            docs_with_blocking_issues = docs_with_blocking_issues.filter(ExceptionRecord.client_id == client_id)
        
        blocking_doc_ids = set(r[0] for r in docs_with_blocking_issues.all() if r[0])
        auto_cleared_count = max(0, done_docs - len(blocking_doc_ids))
        auto_cleared_pct = round((auto_cleared_count / done_docs * 100), 1) if done_docs > 0 else 0.0

        # Estimated Hours Saved
        # Default CA manual document entry benchmark: 15.0 minutes
        # Review time per exception resolved: 2.0 minutes
        benchmark_mins_per_doc = settings.MANUAL_ENTRY_BENCHMARK_MINUTES
        manual_minutes_expected = done_docs * benchmark_mins_per_doc
        actual_ca_review_minutes = (resolved_exceptions * 2.0) + (done_docs * 1.5) # ~1.5 min approval pass
        hours_saved = max(0.0, round((manual_minutes_expected - actual_ca_review_minutes) / 60.0, 1))

        # Entries status
        draft_entries = entry_query.filter(Entry.status == "draft").count()
        final_entries = entry_query.filter(Entry.status == "final").count()
        total_value_paise = entry_query.with_entities(func.sum(Entry.total_amount_paise)).scalar() or 0
        total_itc_paise = entry_query.with_entities(
            func.sum(Entry.cgst_paise + Entry.sgst_paise + Entry.igst_paise + Entry.cess_paise)
        ).scalar() or 0

        return {
            "documents": {
                "total": total_docs,
                "done": done_docs,
                "queued": queued_docs,
                "processing": processing_docs,
                "failed": failed_docs,
                "auto_cleared_pct": auto_cleared_pct,
            },
            "exceptions": {
                "total_open": total_open_exceptions,
                "high": open_high,
                "medium": open_medium,
                "low": open_low,
                "resolved": resolved_exceptions,
            },
            "productivity": {
                "benchmark_mins_per_doc": benchmark_mins_per_doc,
                "avg_review_mins": 1.5,
                "hours_saved": hours_saved,
                "formula": "((Documents Processed * Benchmark Mins) - Actual CA Review Mins) / 60",
            },
            "financials": {
                "draft_entries": draft_entries,
                "approved_entries": final_entries,
                "total_transaction_value_paise": total_value_paise,
                "total_itc_paise": total_itc_paise,
            }
        }
