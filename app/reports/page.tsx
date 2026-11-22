"use client";

import React, { useState, useEffect } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { AiFooter } from "@/components/common/AiFooter";
import { apiFetch, getCurrentUser } from "@/lib/api";
import { formatIndianCurrency, formatDate } from "@/lib/formatters";
import {
  FileSpreadsheet,
  Download,
  BookOpen,
  Scale,
  FileCheck,
  Lock,
  ArrowRight,
  Sparkles,
} from "lucide-react";

export default function ReportsPage() {
  const user = getCurrentUser();
  const isPartner = user?.role === "partner";

  const [selectedClientId, setSelectedClientId] = useState<string>("");
  const [clients, setClients] = useState<any[]>([]);
  const [reportType, setReportType] = useState<"trial_balance" | "gstr3b" | "daybook">("trial_balance");
  const [trialBalanceData, setTrialBalanceData] = useState<any>(null);
  const [gstr3bData, setGstr3bData] = useState<any>(null);
  const [dayBookData, setDayBookData] = useState<any[]>([]);
  const [isExporting, setIsExporting] = useState(false);

  useEffect(() => {
    apiFetch<any[]>("/clients").then((c) => {
      setClients(c || []);
      if (c && c.length > 0 && !selectedClientId) {
        setSelectedClientId(c[0].id);
      }
    });
  }, []);

  const loadReport = () => {
    if (!selectedClientId) return;
    if (reportType === "trial_balance") {
      apiFetch<any>(`/reports/trial-balance?client_id=${selectedClientId}`)
        .then((data) => setTrialBalanceData(data))
        .catch((err) => console.error(err));
    } else if (reportType === "gstr3b") {
      apiFetch<any>(`/reports/gstr-3b-working?client_id=${selectedClientId}`)
        .then((data) => setGstr3bData(data))
        .catch((err) => console.error(err));
    } else if (reportType === "daybook") {
      apiFetch<any[]>(`/reports/day-book?client_id=${selectedClientId}`)
        .then((data) => setDayBookData(data || []))
        .catch((err) => console.error(err));
    }
  };

  useEffect(() => {
    loadReport();
  }, [selectedClientId, reportType]);

  const handleExportTally = async () => {
    if (!selectedClientId) return;
    setIsExporting(true);
    try {
      const blob = await apiFetch<Blob>(`/reports/export/tally?client_id=${selectedClientId}`);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `Accuro_TallyPrime_Import_${new Date().toISOString().slice(0, 10)}.xml`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (err: any) {
      alert(err.message || "Tally export failed");
    } finally {
      setIsExporting(false);
    }
  };

  const handleExportExcel = async () => {
    if (!selectedClientId) return;
    setIsExporting(true);
    try {
      const blob = await apiFetch<Blob>(`/reports/export/excel?client_id=${selectedClientId}&report_type=${reportType}`);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `Accuro_${reportType}_${new Date().toISOString().slice(0, 10)}.xlsx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (err: any) {
      alert(err.message || "Excel export failed");
    } finally {
      setIsExporting(false);
    }
  };

  const handleExportPdf = async () => {
    if (!selectedClientId) return;
    setIsExporting(true);
    try {
      const blob = await apiFetch<Blob>(`/reports/export/pdf?client_id=${selectedClientId}`);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `Accuro_Report_${new Date().toISOString().slice(0, 10)}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (err: any) {
      alert(err.message || "PDF export failed");
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />

      <main className="flex-1 flex flex-col min-w-0">
        <Header
          title="Financial & GST Reports & Tally Prime XML Export"
          subtitle="Generate balanced Trial Balance, GSTR-3B tax computation schedule and 1-click Tally vouchers"
          selectedClientId={selectedClientId}
          onClientChange={(id) => setSelectedClientId(id)}
          actions={
            <div className="flex items-center gap-2">
              {isPartner && (
                <button
                  onClick={handleExportTally}
                  disabled={isExporting}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-[#1E3A8A] text-white rounded-lg hover:bg-blue-900 shadow-sm transition-all active:scale-95"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Export Tally XML (Vouchers)</span>
                </button>
              )}
              <button
                onClick={handleExportExcel}
                disabled={isExporting}
                className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50"
              >
                <span>Excel (.xlsx)</span>
              </button>
              <button
                onClick={handleExportPdf}
                disabled={isExporting}
                className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50"
              >
                <span>PDF Report</span>
              </button>
            </div>
          }
        />

        {/* Report Tabs */}
        <div className="bg-white border-b border-slate-200 px-8 flex items-center justify-between">
          <div className="flex items-center gap-8 text-xs font-semibold">
            <button
              onClick={() => setReportType("trial_balance")}
              className={`py-3.5 border-b-2 flex items-center gap-2 transition-all ${
                reportType === "trial_balance"
                  ? "border-[#1E3A8A] text-[#1E3A8A]"
                  : "border-transparent text-slate-500 hover:text-slate-800"
              }`}
            >
              <Scale className="w-4 h-4" />
              <span>Trial Balance</span>
            </button>

            <button
              onClick={() => setReportType("gstr3b")}
              className={`py-3.5 border-b-2 flex items-center gap-2 transition-all ${
                reportType === "gstr3b"
                  ? "border-[#1E3A8A] text-[#1E3A8A]"
                  : "border-transparent text-slate-500 hover:text-slate-800"
              }`}
            >
              <FileCheck className="w-4 h-4" />
              <span>GSTR-3B Liability Working</span>
            </button>

            <button
              onClick={() => setReportType("daybook")}
              className={`py-3.5 border-b-2 flex items-center gap-2 transition-all ${
                reportType === "daybook"
                  ? "border-[#1E3A8A] text-[#1E3A8A]"
                  : "border-transparent text-slate-500 hover:text-slate-800"
              }`}
            >
              <BookOpen className="w-4 h-4" />
              <span>Day Book</span>
            </button>
          </div>

          <div className="flex items-center gap-1.5 text-xs text-slate-500 font-mono">
            <Lock className="w-3.5 h-3.5 text-slate-400" />
            <span>Period Lock Available for Finalized Books</span>
          </div>
        </div>

        {/* Report Content */}
        <div className="p-8 space-y-6 max-w-7xl mx-auto w-full">
          {reportType === "trial_balance" && (
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
              <div className="px-6 py-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-slate-900">
                    Trial Balance — {trialBalanceData?.client_name}
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    As of {trialBalanceData?.as_of_date || "Today"} • Double-entry integrity check
                  </p>
                </div>
                <span
                  className={`px-2.5 py-1 rounded text-xs font-semibold ${
                    trialBalanceData?.is_balanced
                      ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                      : "bg-rose-50 text-rose-800 border border-rose-200"
                  }`}
                >
                  {trialBalanceData?.is_balanced ? "✓ Books Balanced" : "Discrepancy Detected"}
                </span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 border-b border-slate-200 text-slate-700 font-semibold uppercase tracking-wider">
                    <tr>
                      <th className="px-6 py-3 font-mono">Code</th>
                      <th className="px-6 py-3">Account Name</th>
                      <th className="px-6 py-3">Group</th>
                      <th className="px-6 py-3 text-right">Debit Balance (₹)</th>
                      <th className="px-6 py-3 text-right">Credit Balance (₹)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {trialBalanceData?.accounts?.map((acc: any, i: number) => (
                      <tr key={i} className="hover:bg-slate-50/80">
                        <td className="px-6 py-2.5 font-mono text-slate-500">{acc.account_code}</td>
                        <td className="px-6 py-2.5 font-medium text-slate-900">{acc.account_name}</td>
                        <td className="px-6 py-2.5 text-slate-500">{acc.parent_group}</td>
                        <td className="px-6 py-2.5 text-right font-mono text-slate-900">
                          {acc.debit_paise > 0 ? formatIndianCurrency(acc.debit_paise) : "-"}
                        </td>
                        <td className="px-6 py-2.5 text-right font-mono text-slate-900">
                          {acc.credit_paise > 0 ? formatIndianCurrency(acc.credit_paise) : "-"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot className="bg-slate-50 border-t-2 border-slate-300 font-bold text-slate-900">
                    <tr>
                      <td colSpan={3} className="px-6 py-3 uppercase tracking-wider">
                        Total Balance
                      </td>
                      <td className="px-6 py-3 text-right font-mono text-blue-900">
                        {formatIndianCurrency(trialBalanceData?.total_debit_paise ?? 0)}
                      </td>
                      <td className="px-6 py-3 text-right font-mono text-blue-900">
                        {formatIndianCurrency(trialBalanceData?.total_credit_paise ?? 0)}
                      </td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            </div>
          )}

          {reportType === "gstr3b" && (
            <div className="space-y-6">
              {/* Table 3.1 & Table 4 Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Outward Taxable Supplies */}
                <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4">
                  <h3 className="font-semibold text-sm text-slate-900 border-b border-slate-100 pb-2">
                    Table 3.1: Details of Outward Supplies (Sales)
                  </h3>
                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between py-1 border-b border-slate-100">
                      <span className="text-slate-600">Total Taxable Value:</span>
                      <span className="font-mono font-medium">
                        {formatIndianCurrency(gstr3bData?.table_3_1_outward_supplies?.taxable_value_paise ?? 0)}
                      </span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-slate-100">
                      <span className="text-slate-600">Integrated Tax (IGST):</span>
                      <span className="font-mono">{formatIndianCurrency(gstr3bData?.table_3_1_outward_supplies?.igst_paise ?? 0)}</span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-slate-100">
                      <span className="text-slate-600">Central Tax (CGST):</span>
                      <span className="font-mono">{formatIndianCurrency(gstr3bData?.table_3_1_outward_supplies?.cgst_paise ?? 0)}</span>
                    </div>
                    <div className="flex justify-between py-1">
                      <span className="text-slate-600">State/UT Tax (SGST):</span>
                      <span className="font-mono">{formatIndianCurrency(gstr3bData?.table_3_1_outward_supplies?.sgst_paise ?? 0)}</span>
                    </div>
                  </div>
                </div>

                {/* Eligible ITC Table 4 */}
                <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4">
                  <h3 className="font-semibold text-sm text-slate-900 border-b border-slate-100 pb-2">
                    Table 4: Eligible Input Tax Credit (ITC)
                  </h3>
                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between py-1 border-b border-slate-100">
                      <span className="text-slate-600">(A)(5) All Other ITC — IGST:</span>
                      <span className="font-mono font-medium text-emerald-800">
                        {formatIndianCurrency(gstr3bData?.table_4_itc?.all_other_itc_igst_paise ?? 0)}
                      </span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-slate-100">
                      <span className="text-slate-600">(A)(5) All Other ITC — CGST:</span>
                      <span className="font-mono font-medium text-emerald-800">
                        {formatIndianCurrency(gstr3bData?.table_4_itc?.all_other_itc_cgst_paise ?? 0)}
                      </span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-slate-100">
                      <span className="text-slate-600">(A)(5) All Other ITC — SGST:</span>
                      <span className="font-mono font-medium text-emerald-800">
                        {formatIndianCurrency(gstr3bData?.table_4_itc?.all_other_itc_sgst_paise ?? 0)}
                      </span>
                    </div>
                    <div className="flex justify-between py-1 text-rose-700 bg-rose-50/50 p-1.5 rounded">
                      <span>(D)(1) Ineligible ITC under Sec 17(5):</span>
                      <span className="font-mono font-bold">
                        {formatIndianCurrency(gstr3bData?.table_4_itc?.ineligible_itc_17_5_paise ?? 0)}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {reportType === "daybook" && (
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
              <div className="px-6 py-4 bg-slate-50 border-b border-slate-200">
                <h3 className="text-sm font-semibold text-slate-900">Day Book Ledger</h3>
              </div>
              <div className="divide-y divide-slate-100">
                {dayBookData.map((e, idx) => (
                  <div key={idx} className="p-4 flex items-center justify-between hover:bg-slate-50 text-xs">
                    <div>
                      <span className="font-mono font-bold text-slate-900">{e.invoice_number}</span>
                      <p className="text-slate-600 font-medium">{e.party_name}</p>
                      <p className="text-[11px] text-slate-400 font-mono">Date: {formatDate(e.invoice_date)}</p>
                    </div>
                    <div className="text-right font-mono">
                      <span className="font-bold text-slate-900">{formatIndianCurrency(e.total_amount_paise)}</span>
                      <p className="text-[10px] text-slate-400">Taxable: {formatIndianCurrency(e.taxable_value_paise)}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <AiFooter />
        </div>
      </main>
    </div>
  );
}
