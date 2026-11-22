"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { DocumentViewer } from "@/components/document/DocumentViewer";
import { ExtractedFieldsEditor } from "@/components/document/ExtractedFieldsEditor";
import { apiFetch } from "@/lib/api";
import { ChevronLeft, FileText, CheckCircle } from "lucide-react";

export default function DocumentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const docId = params?.id as string;

  const [document, setDocument] = useState<any | null>(null);
  const [entry, setEntry] = useState<any | null>(null);
  const [exceptions, setExceptions] = useState<any[]>([]);
  const [activeFieldKey, setActiveFieldKey] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const loadData = () => {
    if (!docId) return;
    setIsLoading(true);

    apiFetch<any>(`/documents/${docId}`)
      .then((doc) => {
        setDocument(doc);
        // Fetch matching entry
        return apiFetch<any[]>(`/entries?client_id=${doc.client_id}`).then((entries) => {
          const matchingEntry = (entries || []).find((e) => e.document_id === doc.id);
          setEntry(matchingEntry || null);

          // Fetch matching exceptions
          return apiFetch<any[]>(`/exceptions?client_id=${doc.client_id}&status_filter=all`).then(
            (excs) => {
              const docExceptions = (excs || []).filter((x) => x.document_id === doc.id || (matchingEntry && x.entry_id === matchingEntry.id));
              setExceptions(docExceptions);
            }
          );
        });
      })
      .catch((err) => console.error(err))
      .finally(() => setIsLoading(false));
  };

  useEffect(() => {
    loadData();
  }, [docId]);

  return (
    <div className="flex h-screen bg-slate-100 overflow-hidden">
      <Sidebar />

      <main className="flex-1 flex flex-col min-w-0 h-screen overflow-hidden">
        {/* Navigation Breadcrumb Bar */}
        <div className="bg-white border-b border-slate-200 px-6 py-3 flex items-center justify-between flex-shrink-0">
          <div className="flex items-center gap-3">
            <Link
              href="/documents"
              className="p-1 hover:bg-slate-100 rounded-lg text-slate-500 hover:text-slate-900 transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
            </Link>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-semibold text-xs text-slate-900 truncate max-w-sm">
                  {document?.filename || "Document Review"}
                </span>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-blue-50 text-blue-800 border border-blue-200">
                  Split Review Mode
                </span>
              </div>
              <p className="text-[11px] text-slate-500">
                Left: Original Document Preview • Right: Extracted Schema & CA Approval
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 text-xs">
            <Link
              href="/exceptions"
              className="text-[#1E3A8A] font-semibold hover:underline"
            >
              Back to Exceptions Queue
            </Link>
          </div>
        </div>

        {/* 50/50 Split-Pane Review Body */}
        <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-4 p-4 overflow-hidden">
          {/* Left Pane: Document Viewer with Canvas & Interactive Bounding Boxes */}
          <div className="h-full overflow-hidden">
            <DocumentViewer
              filename={document?.filename || "voucher.pdf"}
              fileType={document?.file_type || "pdf"}
              extractionData={document?.extraction_data}
              activeFieldKey={activeFieldKey}
              onSelectField={(key) => setActiveFieldKey(key)}
            />
          </div>

          {/* Right Pane: Extracted Fields Form, Validation Alerts & CA Approval */}
          <div className="h-full overflow-hidden">
            <ExtractedFieldsEditor
              documentId={docId}
              entryData={entry}
              exceptions={exceptions}
              onSaved={loadData}
              onFocusField={(key) => setActiveFieldKey(key)}
            />
          </div>
        </div>
      </main>
    </div>
  );
}
