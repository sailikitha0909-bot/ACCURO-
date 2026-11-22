"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { StatusBadge } from "@/components/common/StatusBadge";
import { AiFooter } from "@/components/common/AiFooter";
import { apiFetch } from "@/lib/api";
import { formatIndianCurrency, formatCompactRupees } from "@/lib/formatters";
import {
  FileText,
  AlertOctagon,
  Clock,
  Sparkles,
  ArrowRight,
  TrendingUp,
  ShieldCheck,
  CheckCircle2,
  Calendar,
  Building,
} from "lucide-react";

export default function DashboardPage() {
  const [selectedClientId, setSelectedClientId] = useState<string>("");
  const [metrics, setMetrics] = useState<any>(null);
  const [exceptions, setExceptions] = useState<any[]>([]);
  const [deadlines, setDeadlines] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    setIsLoading(true);
    const clientParam = selectedClientId ? `?client_id=${selectedClientId}` : "";
    
    Promise.all([
      apiFetch<any>(`/dashboard/metrics${clientParam}`),
      apiFetch<any[]>(`/exceptions${clientParam ? `?client_id=${selectedClientId}&status_filter=open` : "?status_filter=open"}`),
      apiFetch<any[]>(`/clients`),
    ])
      .then(([m, exc, cls]) => {
        setMetrics(m);
        setExceptions((exc || []).slice(0, 5));
        if (cls && cls.length > 0) {
          const targetId = selectedClientId || cls[0].id;
          apiFetch<any[]>(`/clients/${targetId}/compliance-calendar`)
            .then((d) => setDeadlines((d || []).slice(0, 4)))
            .catch(() => {});
        }
      })
      .catch((err) => console.error("Dashboard fetch error:", err))
      .finally(() => setIsLoading(false));
  }, [selectedClientId]);

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />

      <main className="flex-1 flex flex-col min-w-0">
        <Header
          title="CA Firm Executive Dashboard"
          subtitle="Real-time operational throughput & compliance metrics across client portfolio"
          selectedClientId={selectedClientId}
          onClientChange={(id) => setSelectedClientId(id)}
          actions={
            <Link
              href="/documents"
              className="flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold bg-[#1E3A8A] text-white rounded-lg hover:bg-blue-900 shadow-sm transition-colors"
            >
              <FileText className="w-3.5 h-3.5" />
              <span>Intake Documents</span>
            </Link>
          }
        />

        <div className="p-8 space-y-6 max-w-7xl mx-auto w-full">
          {/* Key Operational KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Card 1: Documents Processed */}
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between text-slate-500 mb-2">
                <span className="text-xs font-medium">Documents Processed</span>
                <FileText className="w-4 h-4 text-blue-600" />
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold font-mono text-slate-900">
                  {metrics?.documents?.done ?? 0}
                </span>
                <span className="text-xs text-slate-500">
                  of {metrics?.documents?.total ?? 0} uploaded
                </span>
              </div>
              <div className="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-between text-[11px]">
                <span className="text-slate-500">Auto-cleared rate:</span>
                <span className="font-semibold text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded">
                  {metrics?.documents?.auto_cleared_pct ?? 0}%
                </span>
              </div>
            </div>

            {/* Card 2: Exceptions Open */}
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between text-slate-500 mb-2">
                <span className="text-xs font-medium">Exceptions for Review</span>
                <AlertOctagon className="w-4 h-4 text-amber-600" />
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold font-mono text-amber-700">
                  {metrics?.exceptions?.total_open ?? 0}
                </span>
                <span className="text-xs text-rose-600 font-medium">
                  ({metrics?.exceptions?.high ?? 0} Critical)
                </span>
              </div>
              <div className="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-between text-[11px]">
                <span className="text-slate-500">Medium / Low:</span>
                <span className="font-mono text-slate-700">
                  {metrics?.exceptions?.medium ?? 0} Med • {metrics?.exceptions?.low ?? 0} Low
                </span>
              </div>
            </div>

            {/* Card 3: Estimated Hours Saved */}
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm bg-gradient-to-br from-white to-blue-50/30">
              <div className="flex items-center justify-between text-slate-500 mb-2">
                <span className="text-xs font-medium text-slate-700">Estimated Hours Saved</span>
                <Clock className="w-4 h-4 text-[#1E3A8A]" />
              </div>
              <div className="flex items-baseline gap-1.5">
                <span className="text-2xl font-bold font-mono text-[#1E3A8A]">
                  {metrics?.productivity?.hours_saved ?? 0}
                </span>
                <span className="text-xs font-semibold text-slate-600">hrs</span>
              </div>
              <div className="mt-3 pt-2.5 border-t border-slate-100 text-[10px] text-slate-500">
                Formula: ({metrics?.productivity?.benchmark_mins_per_doc ?? 15}m manual - 1.5m review) / doc
              </div>
            </div>

            {/* Card 4: Total Reconciled Value */}
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between text-slate-500 mb-2">
                <span className="text-xs font-medium">Voucher Throughput</span>
                <TrendingUp className="w-4 h-4 text-emerald-600" />
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-xl font-bold font-mono text-slate-900">
                  {formatCompactRupees(metrics?.financials?.total_transaction_value_paise ?? 0)}
                </span>
              </div>
              <div className="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-between text-[11px]">
                <span className="text-slate-500">Total ITC Tracked:</span>
                <span className="font-mono font-semibold text-blue-900">
                  {formatCompactRupees(metrics?.financials?.total_itc_paise ?? 0)}
                </span>
              </div>
            </div>
          </div>

          {/* Main Grid: Priority Exception Queue Preview & Statutory Compliance Calendar */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Exceptions Queue Preview (2 Columns) */}
            <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 shadow-sm p-6 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h2 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                      <AlertOctagon className="w-4 h-4 text-[#1E3A8A]" />
                      <span>Priority Exception Queue</span>
                    </h2>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Deterministic verification issues requiring CA partner approval
                    </p>
                  </div>
                  <Link
                    href="/exceptions"
                    className="text-xs font-medium text-[#1E3A8A] hover:underline flex items-center gap-1"
                  >
                    <span>View all ({metrics?.exceptions?.total_open ?? 0})</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>

                {exceptions.length === 0 ? (
                  <div className="py-12 text-center text-slate-400 text-xs">
                    <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2 opacity-80" />
                    <p className="font-medium text-slate-700">Zero Open Exceptions</p>
                    <p className="text-slate-500 mt-0.5">
                      All processed invoices have cleared deterministic validation checks.
                    </p>
                  </div>
                ) : (
                  <div className="divide-y divide-slate-100">
                    {exceptions.map((exc) => (
                      <Link
                        key={exc.id}
                        href="/exceptions"
                        className="py-3 px-2 flex items-start justify-between hover:bg-slate-50 rounded-lg transition-colors group block"
                      >
                        <div className="pr-4">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-semibold text-xs text-slate-900 group-hover:text-blue-700">
                              {exc.title}
                            </span>
                            <StatusBadge status={exc.severity} size="sm" />
                          </div>
                          <p className="text-xs text-slate-500 line-clamp-1 leading-relaxed">
                            {exc.description}
                          </p>
                        </div>
                        <span className="text-[11px] font-mono text-slate-400 whitespace-nowrap pt-0.5">
                          {exc.exception_type.replace(/_/g, " ")}
                        </span>
                      </Link>
                    ))}
                  </div>
                )}
              </div>

              <AiFooter />
            </div>

            {/* Compliance Calendar & Statutory Deadlines (1 Column) */}
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h2 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                      <Calendar className="w-4 h-4 text-[#1E3A8A]" />
                      <span>Statutory Calendar</span>
                    </h2>
                    <p className="text-xs text-slate-500 mt-0.5">Upcoming Indian tax due dates</p>
                  </div>
                  <Link href="/clients" className="text-xs text-[#1E3A8A] hover:underline">
                    View
                  </Link>
                </div>

                <div className="space-y-3">
                  {deadlines.map((dl, idx) => (
                    <div
                      key={idx}
                      className="p-3 rounded-lg border border-slate-100 bg-slate-50/60 hover:bg-slate-50 transition-colors"
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-semibold text-xs text-slate-900 truncate max-w-[170px]">
                          {dl.title}
                        </span>
                        <StatusBadge status={dl.status} size="sm" />
                      </div>
                      <div className="flex items-center justify-between text-[11px] text-slate-500 font-mono mt-1">
                        <span>Due: {dl.due_date}</span>
                        <span className="font-sans text-slate-600 font-medium">{dl.form}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-100 text-[11px] text-slate-500 flex items-center justify-between">
                <span>Section 16(4) ITC cut-off:</span>
                <span className="font-mono text-rose-700 font-semibold">30-Nov-2025</span>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
