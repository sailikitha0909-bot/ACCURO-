"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { StatusBadge } from "@/components/common/StatusBadge";
import { AiFooter } from "@/components/common/AiFooter";
import { DataTable } from "@/components/table/DataTable";
import { apiFetch } from "@/lib/api";
import { formatDate } from "@/lib/formatters";
import { ColumnDef } from "@tanstack/react-table";
import {
  UploadCloud,
  FileText,
  CheckCircle2,
  AlertTriangle,
  ExternalLink,
  RefreshCw,
  Building,
} from "lucide-react";

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<any[]>([]);
  const [clients, setClients] = useState<any[]>([]);
  const [selectedClientId, setSelectedClientId] = useState<string>("");
  const [isUploading, setIsUploading] = useState(false);
  const [uploadMsg, setUploadMsg] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const [dragActive, setDragActive] = useState(false);

  const loadDocuments = () => {
    const param = selectedClientId ? `?client_id=${selectedClientId}` : "";
    apiFetch<any[]>(`/documents${param}`)
      .then((data) => setDocuments(data || []))
      .catch((err) => console.error(err));
  };

  useEffect(() => {
    apiFetch<any[]>("/clients").then((c) => {
      setClients(c || []);
      if (c && c.length > 0 && !selectedClientId) {
        setSelectedClientId(c[0].id);
      }
    });
  }, []);

  useEffect(() => {
    if (selectedClientId) {
      loadDocuments();
    }
  }, [selectedClientId]);

  const handleFiles = async (files: FileList | null) => {
    if (!files || files.length === 0 || !selectedClientId) return;
    setIsUploading(true);
    setUploadMsg("");
    setErrorMsg("");

    const formData = new FormData();
    formData.append("client_id", selectedClientId);
    for (let i = 0; i < files.length; i++) {
      formData.append("files", files[i]);
    }

    try {
      const res = await apiFetch<any[]>("/documents/upload", {
        method: "POST",
        body: formData,
      });
      setUploadMsg(`Successfully processed ${res.length} document(s) through intake pipeline.`);
      loadDocuments();
    } catch (err: any) {
      setErrorMsg(err.message || "Upload failed");
    } finally {
      setIsUploading(false);
    }
  };

  const columns: ColumnDef<any>[] = [
    {
      accessorKey: "filename",
      header: "Document Name",
      cell: ({ row }) => (
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-slate-400 flex-shrink-0" />
          <span className="font-semibold text-slate-900 truncate max-w-xs">
            {row.original.filename}
          </span>
        </div>
      ),
    },
    {
      accessorKey: "doc_type",
      header: "Classification",
      cell: ({ row }) => (
        <span className="font-mono text-xs uppercase text-slate-600">
          {(row.original.doc_type || "invoice").replace(/_/g, " ")}
        </span>
      ),
    },
    {
      accessorKey: "file_size_bytes",
      header: "Size",
      cell: ({ row }) => (
        <span className="font-mono text-slate-500">
          {(row.original.file_size_bytes / 1024).toFixed(1)} KB
        </span>
      ),
    },
    {
      accessorKey: "sha256_hash",
      header: "SHA-256 Hash",
      cell: ({ row }) => (
        <span className="font-mono text-[10px] text-slate-400" title={row.original.sha256_hash}>
          {row.original.sha256_hash ? `${row.original.sha256_hash.slice(0, 10)}...` : "-"}
        </span>
      ),
    },
    {
      accessorKey: "created_at",
      header: "Intake Date",
      cell: ({ row }) => (
        <span className="font-mono text-slate-600">{formatDate(row.original.created_at)}</span>
      ),
    },
    {
      accessorKey: "status",
      header: "Pipeline Status",
      cell: ({ row }) => <StatusBadge status={row.original.status} size="sm" />,
    },
    {
      id: "actions",
      header: "Action",
      cell: ({ row }) => (
        <Link
          href={`/documents/${row.original.id}`}
          className="inline-flex items-center gap-1 font-semibold text-xs text-[#1E3A8A] hover:underline"
        >
          <span>Split Review</span>
          <ExternalLink className="w-3 h-3" />
        </Link>
      ),
    },
  ];

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />

      <main className="flex-1 flex flex-col min-w-0">
        <Header
          title="Document Intake & Ingestion Pipeline"
          subtitle="Automated PDF/Image OCR classification, bounding-box extraction and deterministic validation"
          selectedClientId={selectedClientId}
          onClientChange={(id) => setSelectedClientId(id)}
        />

        <div className="p-8 space-y-6 max-w-7xl mx-auto w-full">
          {/* Drag & Drop Upload Card */}
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragActive(true);
            }}
            onDragLeave={() => setDragActive(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragActive(false);
              handleFiles(e.dataTransfer.files);
            }}
            className={`border-2 border-dashed rounded-2xl p-8 text-center transition-all bg-white ${
              dragActive ? "border-blue-600 bg-blue-50/50" : "border-slate-300 hover:border-slate-400"
            }`}
          >
            <div className="max-w-md mx-auto flex flex-col items-center">
              <div className="w-12 h-12 rounded-full bg-blue-50 flex items-center justify-center text-[#1E3A8A] mb-3">
                <UploadCloud className="w-6 h-6" />
              </div>
              <h3 className="text-sm font-semibold text-slate-900 mb-1">
                Drag and drop vouchers, bills or statements here
              </h3>
              <p className="text-xs text-slate-500 mb-4">
                Supported: PDF, JPG, PNG, CSV, XLSX (Up to 25MB). SHA-256 hash automatically prevents duplicate re-uploads.
              </p>

              <label className="cursor-pointer px-4 py-2 bg-[#1E3A8A] hover:bg-blue-900 text-white text-xs font-semibold rounded-lg shadow-sm transition-all active:scale-95 inline-flex items-center gap-2">
                <span>{isUploading ? "Processing Document Pipeline..." : "Select Files from Computer"}</span>
                <input
                  type="file"
                  multiple
                  disabled={isUploading}
                  onChange={(e) => handleFiles(e.target.files)}
                  className="hidden"
                  accept=".pdf,.jpg,.jpeg,.png,.csv,.xlsx"
                />
              </label>
            </div>
          </div>

          {/* Feedback Alerts */}
          {uploadMsg && (
            <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>{uploadMsg}</span>
            </div>
          )}
          {errorMsg && (
            <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-rose-600" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Documents Table */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-slate-900">
                Uploaded Documents ({documents.length})
              </h3>
              <button
                onClick={loadDocuments}
                className="text-xs text-slate-600 hover:text-slate-900 flex items-center gap-1 font-medium"
              >
                <RefreshCw className="w-3 h-3" />
                <span>Refresh</span>
              </button>
            </div>

            <DataTable columns={columns} data={documents} pageSize={10} />
          </div>

          <AiFooter />
        </div>
      </main>
    </div>
  );
}
