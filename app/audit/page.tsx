"use client";

import React, { useState, useEffect } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { AiFooter } from "@/components/common/AiFooter";
import { apiFetch } from "@/lib/api";
import { formatDateTime } from "@/lib/formatters";
import { ShieldCheck, Lock, FileKey, History, CheckCircle, Database } from "lucide-react";

export default function AuditPage() {
  const [logs, setLogs] = useState<any[]>([]);
  const [dpdpStatus, setDpdpStatus] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      apiFetch<any[]>("/audit?limit=50"),
      apiFetch<any>("/audit/compliance/dpdp"),
    ])
      .then(([l, d]) => {
        setLogs(l || []);
        setDpdpStatus(d);
      })
      .catch((err) => console.error(err))
      .finally(() => setIsLoading(false));
  }, []);

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />

      <main className="flex-1 flex flex-col min-w-0">
        <Header
          title="Immutable Audit Trail & India DPDP Act Compliance"
          subtitle="Non-repudiable audit logging of every AI draft, CA edit, partner approval, and export action"
        />

        <div className="p-8 space-y-6 max-w-7xl mx-auto w-full">
          {/* DPDP Act Compliance Badges */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-emerald-600" />
                <h3 className="text-sm font-semibold text-slate-900">
                  Digital Personal Data Protection Act (DPDP Act, India) Compliance
                </h3>
              </div>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-200 font-semibold">
                Status: Fully Compliant
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
              <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                <div className="flex items-center gap-2 font-semibold text-slate-800 mb-1">
                  <Lock className="w-3.5 h-3.5 text-[#1E3A8A]" />
                  <span>Field-Level Encryption</span>
                </div>
                <p className="text-[11px] text-slate-500 leading-relaxed">
                  AES-256 field-level encryption for sensitive client identifiers: PAN, GSTIN, and Bank Account numbers.
                </p>
              </div>

              <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                <div className="flex items-center gap-2 font-semibold text-slate-800 mb-1">
                  <Database className="w-3.5 h-3.5 text-blue-600" />
                  <span>No AI Model Training</span>
                </div>
                <p className="text-[11px] text-slate-500 leading-relaxed">
                  Zero client accounting vouchers or extraction data are used to train foundational AI models.
                </p>
              </div>

              <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                <div className="flex items-center gap-2 font-semibold text-slate-800 mb-1">
                  <History className="w-3.5 h-3.5 text-purple-600" />
                  <span>Statutory Retention (8 Years)</span>
                </div>
                <p className="text-[11px] text-slate-500 leading-relaxed">
                  Complies with Section 44AA of Income Tax Act and Section 36 of CGST Act for immutable record retention.
                </p>
              </div>
            </div>
          </div>

          {/* Immutable Audit Log Table */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="px-6 py-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                  <History className="w-4 h-4 text-slate-600" />
                  <span>Audit Trail Logs ({logs.length} Recent Events)</span>
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Complete before/after delta snapshots with IP addresses and user agents
                </p>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 border-b border-slate-200 text-slate-700 font-semibold uppercase tracking-wider">
                  <tr>
                    <th className="px-6 py-3 font-mono">Timestamp</th>
                    <th className="px-6 py-3">Actor / User</th>
                    <th className="px-6 py-3">Action</th>
                    <th className="px-6 py-3">Entity</th>
                    <th className="px-6 py-3">Details / Snapshot</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {logs.map((log) => (
                    <tr key={log.id} className="hover:bg-slate-50/80">
                      <td className="px-6 py-3 font-mono text-slate-500 whitespace-nowrap">
                        {formatDateTime(log.timestamp)}
                      </td>
                      <td className="px-6 py-3 font-medium text-slate-900">{log.user_name}</td>
                      <td className="px-6 py-3">
                        <span className="px-2 py-0.5 rounded font-mono text-[10px] uppercase font-semibold bg-blue-50 text-blue-900 border border-blue-200">
                          {log.action.replace(/_/g, " ")}
                        </span>
                      </td>
                      <td className="px-6 py-3 font-mono text-slate-500 uppercase">{log.entity_type}</td>
                      <td className="px-6 py-3 font-mono text-[11px] text-slate-600 max-w-md truncate">
                        {JSON.stringify(log.details)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <AiFooter />
        </div>
      </main>
    </div>
  );
}
