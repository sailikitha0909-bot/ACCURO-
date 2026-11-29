import os
import hashlib
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.models import Document, Client, User, AuditLog
from app.schemas import DocumentOut
from app.api.deps import get_current_user, require_role
from app.services.document_pipeline import DocumentPipeline, compute_sha256

router = APIRouter(prefix="/documents", tags=["Documents"])

ALLOWED_EXTENSIONS = {"pdf", "jpg", "jpeg", "png", "csv", "xlsx"}
MAX_FILE_SIZE = 25 * 1024 * 1024 # 25 MB

@router.get("", response_model=List[DocumentOut])
def list_documents(
    client_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Document).filter(Document.organization_id == current_user.organization_id)
    if client_id:
        query = query.filter(Document.client_id == client_id)
    if status_filter:
        query = query.filter(Document.status == status_filter)
    
    return query.order_by(Document.created_at.desc()).all()

@router.post("/upload", response_model=List[DocumentOut])
async def upload_documents(
    client_id: str = Form(...),
    files: List[UploadFile] = File(...),
    current_user: User = Depends(require_role(["partner", "article"])),
    db: Session = Depends(get_db)
):
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.organization_id == current_user.organization_id
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    os.makedirs(settings.STORAGE_LOCAL_DIR, exist_ok=True)
    created_docs = []

    for file in files:
        ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File {file.filename} exceeds maximum size limit of 25MB."
            )

        # SHA-256 hash for deduplication
        file_hash = compute_sha256(content)
        existing_doc = db.query(Document).filter(
            Document.client_id == client.id,
            Document.sha256_hash == file_hash
        ).first()

        if existing_doc:
            # Re-upload detected
            created_docs.append(existing_doc)
            continue

        # Save immutably to storage
        save_path = os.path.join(settings.STORAGE_LOCAL_DIR, f"{file_hash}_{file.filename}")
        with open(save_path, "wb") as f:
            f.write(content)

        # Determine initial classification
        doc_type = "purchase_invoice"
        fn_l = file.filename.lower()
        if "bank" in fn_l or ext in ("csv", "xlsx"):
            doc_type = "bank_statement"
        elif "sales" in fn_l:
            doc_type = "sales_invoice"
        elif "credit" in fn_l:
            doc_type = "credit_note"

        doc = Document(
            organization_id=current_user.organization_id,
            client_id=client.id,
            filename=file.filename,
            storage_path=save_path,
            file_type=ext,
            file_size_bytes=len(content),
            sha256_hash=file_hash,
            doc_type=doc_type,
            status="queued",
            uploaded_by_user_id=current_user.id
        )
        db.add(doc)
        db.flush()

        # Execute Document Intake Pipeline (never blocks: runs synchronously for quick files or via worker)
        DocumentPipeline.process_document(db, doc.id)

        created_docs.append(doc)

    return created_docs

@router.get("/{document_id}", response_model=DocumentOut)
def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.organization_id == current_user.organization_id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@router.post("/{document_id}/reprocess", response_model=DocumentOut)
def reprocess_document(
    document_id: str,
    current_user: User = Depends(require_role(["partner", "article"])),
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.organization_id == current_user.organization_id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    updated_doc = DocumentPipeline.process_document(db, doc.id)
    return updated_doc
