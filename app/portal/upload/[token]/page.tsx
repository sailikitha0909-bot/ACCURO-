"use client";

import React, { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { Logo } from "@/components/common/Logo";
import { UploadCloud, CheckCircle2, AlertTriangle, ShieldCheck, FileText } from "lucide-react";

export default function ClientPortalUploadPage() {
  const params = useParams();
  const token = params?.token as string;

  const [clientInfo, setClientInfo] = useState<any | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const [dragActive, setDragActive] = useState(false);
  const [isValidating, setIsValidating] = useState(true);

  useEffect(() => {
    if (!token) return;
    const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";
    fetch(`${API_BASE}/portal/validate/${token}`)
      .then(async (res) => {
        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.detail || "Invalid or expired link");
        }
        return res.json();
      })
      .then((data) => setClientInfo(data))
      .catch((err) => setErrorMsg(err.message))
      .finally(() => setIsValidating(false));
  }, [token]);

  const handleUpload = async (files: FileList | null) => {
    if (!files || files.length === 0 || !token) return;
    setIsUploading(true);
    setSuccessMsg("");
    setErrorMsg("");

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append("files", files[i]);
    }

    const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";
    try {
      const res = await fetch(`${API_BASE}/portal/upload/${token}`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Upload failed");
      }

      const data = await res.json();
      setSuccessMsg(`Thank you! Successfully submitted ${data.uploaded_files.length} document(s) directly to your Chartered Accountant.`);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to upload documents");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 flex flex-col justify-center items-center p-4 selection:bg-blue-600 selection:text-white">
      <div className="w-full max-w-xl">
        <div className="bg-white rounded-2xl shadow-2xl p-8 border border-slate-200">
          {/* Logo & Header */}
          <div className="text-center mb-8 pb-6 border-b border-slate-100">
            <div className="flex justify-center mb-2">
              <Logo size="lg" />
            </div>
            <div className="flex items-center justify-center gap-1.5 text-xs text-slate-500 font-medium mt-1">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              <span>Secure CA Client Document Drop Portal</span>
            </div>
          </div>

          {isValidating ? (
            <div className="py-12 text-center text-xs text-slate-500">
              Validating secure upload token...
            </div>
          ) : errorMsg ? (
            <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-rose-600 flex-shrink-0" />
              <span>{errorMsg}</span>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Client Greeting */}
              <div className="bg-blue-50/70 border border-blue-100 p-4 rounded-xl text-xs space-y-1">
                <span className="text-[10px] uppercase font-bold tracking-wider text-blue-900">
                  Uploading Documents For:
                </span>
                <h2 className="text-base font-bold text-slate-900">
                  {clientInfo?.client_name}
                </h2>
                <p className="text-slate-600 text-[11px]">
                  Files uploaded here are directly submitted into Accuro for review by Mehta & Associates.
                </p>
              </div>

              {/* Drag & Drop Zone */}
              <div
                onDragOver={(e) => {
                  e.preventDefault();
                  setDragActive(true);
                }}
                onDragLeave={() => setDragActive(false)}
                onDrop={(e) => {
                  e.preventDefault();
                  setDragActive(false);
                  handleUpload(e.dataTransfer.files);
                }}
                className={`border-2 border-dashed rounded-xl p-8 text-center transition-all ${
                  dragActive ? "border-blue-600 bg-blue-50/50" : "border-slate-300 hover:border-slate-400 bg-slate-50/50"
                }`}
              >
                <div className="max-w-xs mx-auto flex flex-col items-center">
                  <div className="w-12 h-12 rounded-full bg-white shadow-xs border border-slate-200 flex items-center justify-center text-[#1E3A8A] mb-3">
                    <UploadCloud className="w-6 h-6" />
                  </div>
                  <h4 className="text-xs font-semibold text-slate-900 mb-1">
                    Drop your vouchers or invoices here
                  </h4>
                  <p className="text-[11px] text-slate-500 mb-4">
                    PDF, JPG, PNG or Bank Statement CSV/XLSX
                  </p>

                  <label className="cursor-pointer px-4 py-2 bg-[#1E3A8A] hover:bg-blue-900 text-white text-xs font-semibold rounded-lg shadow-sm transition-all active:scale-95 inline-flex items-center gap-2">
                    <span>{isUploading ? "Uploading & Analyzing..." : "Choose Files from Device"}</span>
                    <input
                      type="file"
                      multiple
                      disabled={isUploading}
                      onChange={(e) => handleUpload(e.target.files)}
                      className="hidden"
                      accept=".pdf,.jpg,.jpeg,.png,.csv,.xlsx"
                    />
                  </label>
                </div>
              </div>

              {successMsg && (
                <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center gap-2">
                  <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
                  <span>{successMsg}</span>
                </div>
              )}
            </div>
          )}

          <div className="mt-8 pt-4 border-t border-slate-100 text-center text-[11px] text-slate-400">
            Powered by Accuro • Secure Token Authenticated Link
          </div>
        </div>
      </div>
    </div>
  );
}
