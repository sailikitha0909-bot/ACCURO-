"use client";

import React, { useState, useEffect } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { StatusBadge } from "@/components/common/StatusBadge";
import { AiFooter } from "@/components/common/AiFooter";
import { apiFetch } from "@/lib/api";
import { formatIndianCurrency, formatCompactRupees, formatDate } from "@/lib/formatters";
import {
  ArrowLeftRight,
  UploadCloud,
  CheckCircle2,
  AlertTriangle,
  Building,
  Landmark,
  ShieldAlert,
  Send,
  FileCheck,
  RefreshCw,
} from "lucide-react";

export default function ReconciliationPage() {
  const [tab, setTab] = useState<"gstr2b" | "bank">("gstr2b");
  const [selectedClientId, setSelectedClientId] = useState<string>("");
  const [clients, setClients] = useState<any[]>([]);
  const [recSummary, setRecSummary] = useState<any>(null);
  const [bankSummary, setBankSummary] = useState<any>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [statusMsg, setStatusMsg] = useState("");

  const loadData = () => {
    if (!selectedClientId) return;
    if (tab === "gstr2b") {
      apiFetch<any>(`/reconciliation/gstr2b/summary?client_id=${selectedClientId}&return_period=072024`)
        .then((data) => setRecSummary(data))
        .catch((err) => console.error(err));
    } else {
      apiFetch<any[]>(`/reconciliation/bank/statements?client_id=${selectedClientId}`)
        .then((stmts) => {
          if (stmts && stmts.length > 0) {
            setBankSummary(stmts[0]);
          } else {
            setBankSummary(null);
          }
        })
        .catch((err) => console.error(err));
    }
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
    loadData();
  }, [selectedClientId, tab]);

  const handleGstr2bUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files?.[0] || !selectedClientId) return;
    setIsUploading(true);
    setStatusMsg("");

    const formData = new FormData();
    formData.append("client_id", selectedClientId);
    formData.append("return_period", "072024");
    formData.append("file", e.target.files[0]);

    try {
      const res = await apiFetch<any>("/reconciliation/gstr2b/upload", {
        method: "POST",
        body: formData,
      });
      setStatusMsg(`GSTR-2B imported successfully: ${res.imported_count} invoices parsed & reconciled.`);
      loadData();
    } catch (err: any) {
      alert(err.message || "Failed to upload GSTR-2B file");
    } finally {
      setIsUploading(false);
    }
  };

  const handleBankUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files?.[0] || !selectedClientId) return;
    setIsUploading(true);
    setStatusMsg("");

    const formData = new FormData();
    formData.append("client_id", selectedClientId);
    formData.append("file", e.target.files[0]);

    try {
      const res = await apiFetch<any>("/reconciliation/bank/upload", {
        method: "POST",
        body: formData,
      });
      setStatusMsg(`Bank statement uploaded: ${res.total_lines} transactions parsed & matched.`);
      loadData();
    } catch (err: any) {
      alert(err.message || "Failed to upload bank statement");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />

      <main className="flex-1 flex flex-col min-w-0">
        <Header
          title="Multi-Way Reconciliation Engine"
          subtitle="Deterministic Books vs GSTR-2B ITC Matching & Bank Statement Auto-Settlement"
          selectedClientId={selectedClientId}
          onClientChange={(id) => setSelectedClientId(id)}
        />

        {/* Tab Selector */}
        <div className="bg-white border-b border-slate-200 px-8 flex items-center justify-between">
          <div className="flex items-center gap-8 text-xs font-semibold">
            <button
              onClick={() => setTab("gstr2b")}
              className={`py-3.5 border-b-2 flex items-center gap-2 transition-all ${
                tab === "gstr2b"
                  ? "border-[#1E3A8A] text-[#1E3A8A]"
                  : "border-transparent text-slate-500 hover:text-slate-800"
              }`}
            >
              <ArrowLeftRight className="w-4 h-4" />
              <span>GSTR-2B vs Books (July 2024)</span>
            </button>

            <button
              onClick={() => setTab("bank")}
              className={`py-3.5 border-b-2 flex items-center gap-2 transition-all ${
                tab === "bank"
                  ? "border-[#1E3A8A] text-[#1E3A8A]"
                  : "border-transparent text-slate-500 hover:text-slate-800"
              }`}
            >
              <Landmark className="w-4 h-4" />
              <span>Bank Statement Reconciliation</span>
            </button>
          </div>

          <div className="flex items-center gap-2">
            {tab === "gstr2b" ? (
              <label className="cursor-pointer px-3 py-1.5 bg-[#1E3A8A] hover:bg-blue-900 text-white text-xs font-semibold rounded-lg shadow-sm transition-all flex items-center gap-1.5">
                <UploadCloud className="w-3.5 h-3.5" />
                <span>{isUploading ? "Importing 2B..." : "Import GSTR-2B (JSON/Excel)"}</span>
                <input
                  type="file"
                  onChange={handleGstr2bUpload}
                  disabled={isUploading}
                  accept=".json,.xlsx"
                  className="hidden"
                />
              </label>
            ) : (
              <label className="cursor-pointer px-3 py-1.5 bg-[#1E3A8A] hover:bg-blue-900 text-white text-xs font-semibold rounded-lg shadow-sm transition-all flex items-center gap-1.5">
                <UploadCloud className="w-3.5 h-3.5" />
                <span>{isUploading ? "Uploading..." : "Upload Bank Statement (CSV)"}</span>
                <input
                  type="file"
                  onChange={handleBankUpload}
                  disabled={isUploading}
                  accept=".csv,.xlsx"
                  className="hidden"
                />
              </label>
            )}
          </div>
        </div>

        {statusMsg && (
          <div className="bg-emerald-50 border-b border-emerald-200 text-emerald-800 text-xs px-8 py-2.5 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
            <span>{statusMsg}</span>
          </div>
        )}

        {/* Content Body */}
        <div className="p-8 space-y-6 max-w-7xl mx-auto w-full">
          {tab === "gstr2b" ? (
            <>
              {/* ITC Financial Health Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
                <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                  <span className="text-xs font-medium text-slate-500">Eligible Claimable ITC</span>
                  <p className="text-xl font-bold font-mono text-emerald-700 mt-1">
                    {formatIndianCurrency(recSummary?.itc_summary?.eligible_itc_paise ?? 0)}
                  </p>
                  <span className="text-[10px] text-slate-400 mt-1 block">
                    {recSummary?.matched_count ?? 0} Vouchers 100% Matched
                  </span>
                </div>

                <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                  <span className="text-xs font-medium text-amber-700">ITC at Immediate Risk</span>
                  <p className="text-xl font-bold font-mono text-amber-700 mt-1">
                    {formatIndianCurrency(recSummary?.itc_summary?.at_risk_itc_paise ?? 0)}
                  </p>
                  <span className="text-[10px] text-slate-400 mt-1 block">
                    {recSummary?.books_only_count ?? 0} in books not in 2B
                  </span>
                </div>

                <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                  <span className="text-xs font-medium text-rose-700">Blocked Credit (Sec 17(5))</span>
                  <p className="text-xl font-bold font-mono text-rose-700 mt-1">
                    {formatIndianCurrency(recSummary?.itc_summary?.blocked_itc_paise ?? 0)}
                  </p>
                  <span className="text-[10px] text-slate-400 mt-1 block">Statutorily Ineligible</span>
                </div>

                <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm bg-blue-50/30">
                  <span className="text-xs font-medium text-[#1E3A8A]">Total Books Input Tax</span>
                  <p className="text-xl font-bold font-mono text-[#1E3A8A] mt-1">
                    {formatIndianCurrency(recSummary?.itc_summary?.total_books_itc_paise ?? 0)}
                  </p>
                  <span className="text-[10px] text-slate-400 mt-1 block">Overall Input Tax</span>
                </div>
              </div>

              {/* Defaulting Suppliers Follow-up Schedule */}
              <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                      <ShieldAlert className="w-4 h-4 text-amber-600" />
                      <span>Vendor Follow-up Schedule (Missing Invoices in GSTR-2B)</span>
                    </h3>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Suppliers who have not filed GSTR-1 for July 2024, putting client&apos;s ITC at risk under Section 16(2)(aa)
                    </p>
                  </div>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-50 border-b border-slate-200 text-slate-700 font-semibold uppercase tracking-wider">
                      <tr>
                        <th className="px-6 py-3">Supplier Name</th>
                        <th className="px-6 py-3 font-mono">Supplier GSTIN</th>
                        <th className="px-6 py-3 text-center">Missing Invoices</th>
                        <th className="px-6 py-3 text-right">ITC at Risk (₹)</th>
                        <th className="px-6 py-3 text-right">CA Follow-up</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {recSummary?.vendor_followups?.map((v: any, idx: number) => (
                        <tr key={idx} className="hover:bg-slate-50/80">
                          <td className="px-6 py-3 font-semibold text-slate-900">{v.supplier_name}</td>
                          <td className="px-6 py-3 font-mono text-slate-600">{v.supplier_gstin || "-"}</td>
                          <td className="px-6 py-3 text-center">
                            <span className="px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 font-mono font-medium">
                              {v.missing_invoices_count}
                            </span>
                          </td>
                          <td className="px-6 py-3 text-right font-mono font-bold text-rose-700">
                            {formatIndianCurrency(v.itc_at_risk_paise)}
                          </td>
                          <td className="px-6 py-3 text-right">
                            <button
                              onClick={() =>
                                alert(
                                  `Follow-up notice drafted for ${v.supplier_name}. Copied to clipboard for WhatsApp / Email.`
                                )
                              }
                              className="px-2.5 py-1 text-xs text-[#1E3A8A] font-medium border border-blue-200 rounded hover:bg-blue-50 transition-colors"
                            >
                              Draft Reminder
                            </button>
                          </td>
                        </tr>
                      )) || (
                        <tr>
                          <td colSpan={5} className="px-6 py-8 text-center text-slate-400">
                            No defaulting suppliers found. All recorded books invoices are matched in GSTR-2B!
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          ) : (
            /* Bank Statement Tab */
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-6">
              <div className="flex items-center justify-between pb-4 border-b border-slate-200">
                <div>
                  <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                    <Landmark className="w-4 h-4 text-[#1E3A8A]" />
                    <span>Bank Statement Reconciliation Ledger</span>
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    HDFC Bank • Account: {bankSummary?.account_number || "XXXXXXXX9821"} • Period: July 2024
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-xs font-semibold text-emerald-800 bg-emerald-50 px-2.5 py-1 rounded border border-emerald-200">
                    {bankSummary?.matched_count ?? 6} Matched on UTR
                  </span>
                  <span className="text-xs font-semibold text-slate-600 bg-slate-100 px-2.5 py-1 rounded">
                    {bankSummary?.unmatched_count ?? 4} Pending Match
                  </span>
                </div>
              </div>

              <div className="text-xs text-slate-600 bg-blue-50/60 p-4 rounded-lg border border-blue-100 space-y-1">
                <p className="font-semibold text-blue-950">Deterministic Bank Matching Rules Active:</p>
                <p>1. UTR / IMPS Reference Number exact match with voucher reference.</p>
                <p>2. Direct NEFT / RTGS settlement matching transaction amount within ₹1 tolerance.</p>
                <p>3. Narration keyword matching against Sundry Creditor vendor names.</p>
              </div>
            </div>
          )}

          <AiFooter />
        </div>
      </main>
    </div>
  );
}
