import os
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.models import ClientPortalToken, Document, Client, AuditLog
from app.services.document_pipeline import DocumentPipeline, compute_sha256

router = APIRouter(prefix="/portal", tags=["Client Upload Portal"])

@router.get("/validate/{token}")
def validate_portal_token(token: str, db: Session = Depends(get_db)):
    portal_token = db.query(ClientPortalToken).filter(
        ClientPortalToken.token == token,
        ClientPortalToken.is_revoked == False
    ).first()

    if not portal_token:
        raise HTTPException(status_code=404, detail="Invalid portal upload link")
    if portal_token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="This upload link has expired. Please contact your CA firm.")

    client = portal_token.client
    return {
        "valid": True,
        "client_name": client.legal_name,
        "client_trade_name": client.trade_name,
        "expires_at": portal_token.expires_at.isoformat()
    }

@router.post("/upload/{token}")
async def upload_via_portal(
    token: str,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    portal_token = db.query(ClientPortalToken).filter(
        ClientPortalToken.token == token,
        ClientPortalToken.is_revoked == False
    ).first()

    if not portal_token or portal_token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Invalid or expired upload link")

    client = portal_token.client
    os.makedirs(settings.STORAGE_LOCAL_DIR, exist_ok=True)
    uploaded = []

    for file in files:
        content = await file.read()
        file_hash = compute_sha256(content)
        ext = file.filename.split(".")[-1].lower() if "." in file.filename else "pdf"

        save_path = os.path.join(settings.STORAGE_LOCAL_DIR, f"{file_hash}_{file.filename}")
        with open(save_path, "wb") as f:
            f.write(content)

        doc = Document(
            organization_id=client.organization_id,
            client_id=client.id,
            filename=file.filename,
            storage_path=save_path,
            file_type=ext,
            file_size_bytes=len(content),
            sha256_hash=file_hash,
            doc_type="purchase_invoice",
            status="queued",
            portal_token_id=portal_token.id
        )
        db.add(doc)
        db.flush()

        portal_token.upload_count += 1
        DocumentPipeline.process_document(db, doc.id)
        uploaded.append(doc.filename)

    db.commit()

    # Log audit
    audit = AuditLog(
        organization_id=client.organization_id,
        user_id=None, # Client uploaded directly
        action="client_portal_upload",
        entity_type="client",
        entity_id=client.id,
        details={"files": uploaded, "token": token[:8] + "..."}
    )
    db.add(audit)
    db.commit()

    return {
        "status": "success",
        "message": f"Successfully received {len(uploaded)} documents into Accuro for CA review.",
        "uploaded_files": uploaded
    }
