import time
import os
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models import Document
from app.services.document_pipeline import DocumentPipeline

def process_queued_documents():
    """Worker polling/execution loop for asynchronous document intake."""
    print("Accuro background worker started. Monitoring queued documents...")
    while True:
        db: Session = SessionLocal()
        try:
            queued_doc = db.query(Document).filter(Document.status == "queued").first()
            if queued_doc:
                print(f"[Worker] Processing document #{queued_doc.id} ({queued_doc.filename})...")
                DocumentPipeline.process_document(db, queued_doc.id)
                print(f"[Worker] Document #{queued_doc.id} processed successfully.")
            else:
                time.sleep(2)
        except Exception as e:
            print(f"[Worker Error] {e}")
            time.sleep(3)
        finally:
            db.close()

if __name__ == "__main__":
    process_queued_documents()
