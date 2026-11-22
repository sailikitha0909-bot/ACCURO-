"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { StatusBadge } from "@/components/common/StatusBadge";
import { AiFooter } from "@/components/common/AiFooter";
import { apiFetch, getCurrentUser } from "@/lib/api";
import { formatIndianCurrency, formatDate } from "@/lib/formatters";
import {
  AlertOctagon,
  CheckCircle,
  XCircle,
  UserPlus,
  ShieldAlert,
  ArrowRight,
  Filter,
  CheckSquare,
  Sparkles,
  ExternalLink,
} from "lucide-react";

export default function ExceptionsPage() {
  const user = getCurrentUser();
  const isPartner = user?.role === "partner";

  const [exceptions, setExceptions] = useState<any[]>([]);
  const [selectedClientId, setSelectedClientId] = useState<string>("");
  const [severityFilter, setSeverityFilter] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("open");
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [activeException, setActiveException] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [actionMsg, setActionMsg] = useState("");

  const loadExceptions = () => {
    setIsLoading(true);
    let url = `/exceptions?status_filter=${statusFilter}`;
    if (selectedClientId) url += `&client_id=${selectedClientId}`;
    if (severityFilter) url += `&severity=${severityFilter}`;

    apiFetch<any[]>(url)
      .then((data) => {
        setExceptions(data || []);
        if (data && data.length > 0 && !activeException) {
          setActiveException(data[0]);
        }
      })
      .catch((err) => console.error(err))
      .finally(() => setIsLoading(false));
  };

  useEffect(() => {
    loadExceptions();
  }, [selectedClientId, severityFilter, statusFilter]);

  const handleSelectAll = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.checked) {
      setSelectedIds(exceptions.map((exc) => exc.id));
    } else {
      setSelectedIds([]);
    }
  };

  const handleToggleSelect = (id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const handleSingleAction = async (action: "approve" | "resolve" | "reject", excId: string) => {
    try {
      await apiFetch(`/exceptions/${excId}/action`, {
        method: "POST",
        body: JSON.stringify({ action }),
      });
      setActionMsg(`Exception ${action}d successfully.`);
      loadExceptions();
    } catch (err: any) {
      alert(err.message || "Action failed");
    }
  };

  const handleBulkAction = async (action: "approve" | "resolve" | "reject") => {
    if (selectedIds.length === 0) return;
    try {
      await apiFetch("/exceptions/bulk-action", {
        method: "POST",
        body: JSON.stringify({ exception_ids: selectedIds, action }),
      });
      setSelectedIds([]);
      setActionMsg(`Bulk ${action} completed on ${selectedIds.length} items.`);
      loadExceptions();
    } catch (err: any) {
      alert(err.message || "Bulk action failed");
    }
  };

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />

      <main className="flex-1 flex flex-col min-w-0">
        <Header
          title="Priority Exception Review Queue"
          subtitle="Deterministic verification engine output — CA review gate for statutory compliance"
          selectedClientId={selectedClientId}
          onClientChange={(id) => setSelectedClientId(id)}
        />

        {/* Toolbar & Filters */}
        <div className="bg-white border-b border-slate-200 px-8 py-3 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            {/* Severity Filter */}
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="text-xs bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 font-medium text-slate-700"
            >
              <option value="">All Severities</option>
              <option value="high">High (Blocking)</option>
              <option value="medium">Medium (Warning)</option>
              <option value="low">Low (Advisory)</option>
            </select>

            {/* Status Filter */}
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="text-xs bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 font-medium text-slate-700"
            >
              <option value="open">Open Issues</option>
              <option value="resolved">Resolved</option>
              <option value="rejected">Rejected</option>
              <option value="all">All Statuses</option>
            </select>

            {selectedIds.length > 0 && (
              <span className="text-xs font-semibold text-blue-900 bg-blue-50 px-2.5 py-1 rounded-lg border border-blue-200">
                {selectedIds.length} selected
              </span>
            )}
          </div>

          {/* Bulk Actions */}
          {selectedIds.length > 0 && (
            <div className="flex items-center gap-2">
              {isPartner && (
                <button
                  onClick={() => handleBulkAction("approve")}
                  className="px-3 py-1.5 text-xs font-semibold bg-[#1E3A8A] text-white rounded-lg hover:bg-blue-900 shadow-sm flex items-center gap-1.5"
                >
                  <CheckCircle className="w-3.5 h-3.5" />
                  <span>Bulk Approve ({selectedIds.length})</span>
                </button>
              )}
              <button
                onClick={() => handleBulkAction("resolve")}
                className="px-3 py-1.5 text-xs font-medium bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 border border-slate-300"
              >
                Mark Resolved
              </button>
              <button
                onClick={() => handleBulkAction("reject")}
                className="px-3 py-1.5 text-xs font-medium text-rose-700 bg-rose-50 hover:bg-rose-100 border border-rose-200 rounded-lg"
              >
                Reject
              </button>
            </div>
          )}
        </div>

        {actionMsg && (
          <div className="bg-emerald-50 border-b border-emerald-200 text-emerald-800 text-xs px-8 py-2 flex items-center justify-between">
            <span>{actionMsg}</span>
            <button onClick={() => setActionMsg("")} className="font-semibold text-emerald-900">✕</button>
          </div>
        )}

        {/* Master-Detail Split Layout */}
        <div className="flex-1 flex overflow-hidden">
          {/* Left Master List (40% width) */}
          <div className="w-full md:w-5/12 border-r border-slate-200 bg-white overflow-y-auto">
            {/* Header select all */}
            <div className="p-3 border-b border-slate-100 flex items-center justify-between bg-slate-50/70 text-xs text-slate-500 font-medium">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={selectedIds.length === exceptions.length && exceptions.length > 0}
                  onChange={handleSelectAll}
                  className="rounded text-blue-600 focus:ring-blue-500"
                />
                <span>Select All ({exceptions.length})</span>
              </label>
              <span>Priority Order</span>
            </div>

            {exceptions.length === 0 ? (
              <div className="p-12 text-center text-slate-400 text-xs">
                <CheckCircle className="w-8 h-8 text-emerald-500 mx-auto mb-2 opacity-80" />
                <p className="font-semibold text-slate-700">No Exceptions Found</p>
                <p className="mt-1">All vouchers in this view meet statutory requirements.</p>
              </div>
            ) : (
              <div className="divide-y divide-slate-100">
                {exceptions.map((exc) => {
                  const isSelected = activeException?.id === exc.id;
                  const isChecked = selectedIds.includes(exc.id);

                  return (
                    <div
                      key={exc.id}
                      onClick={() => setActiveException(exc)}
                      className={`p-4 cursor-pointer transition-colors flex items-start gap-3 ${
                        isSelected
                          ? "bg-blue-50/50 border-l-4 border-l-[#1E3A8A]"
                          : "hover:bg-slate-50"
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={(e) => {
                          e.stopPropagation();
                          handleToggleSelect(exc.id);
                        }}
                        className="mt-1 rounded text-blue-600 focus:ring-blue-500 cursor-pointer"
                      />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-1">
                          <StatusBadge status={exc.severity} size="sm" />
                          <span className="text-[10px] font-mono text-slate-400">
                            {formatDate(exc.created_at)}
                          </span>
                        </div>
                        <h4 className="text-xs font-semibold text-slate-900 truncate">
                          {exc.title}
                        </h4>
                        <p className="text-[11px] text-slate-500 line-clamp-2 mt-0.5 leading-relaxed">
                          {exc.description}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Right Detail Pane (60% width) */}
          <div className="hidden md:flex flex-1 flex-col bg-slate-50 overflow-y-auto p-8">
            {activeException ? (
              <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-6">
                {/* Title & Actions */}
                <div className="flex items-start justify-between pb-4 border-b border-slate-100">
                  <div>
                    <div className="flex items-center gap-2 mb-1.5">
                      <StatusBadge status={activeException.severity} />
                      <span className="text-xs font-mono uppercase tracking-wider text-slate-400">
                        {activeException.exception_type.replace(/_/g, " ")}
                      </span>
                    </div>
                    <h2 className="text-base font-bold text-slate-900 tracking-tight">
                      {activeException.title}
                    </h2>
                  </div>

                  {/* Actions Bar */}
                  <div className="flex items-center gap-2">
                    {isPartner ? (
                      <button
                        onClick={() => handleSingleAction("approve", activeException.id)}
                        className="px-3 py-1.5 bg-[#1E3A8A] hover:bg-blue-900 text-white text-xs font-semibold rounded-lg shadow-sm flex items-center gap-1.5 transition-all active:scale-95"
                      >
                        <ShieldAlert className="w-3.5 h-3.5" />
                        <span>Approve Voucher (CA)</span>
                      </button>
                    ) : (
                      <button
                        onClick={() => handleSingleAction("resolve", activeException.id)}
                        className="px-3 py-1.5 bg-slate-800 hover:bg-slate-900 text-white text-xs font-medium rounded-lg"
                      >
                        Mark Resolved
                      </button>
                    )}

                    <button
                      onClick={() => handleSingleAction("reject", activeException.id)}
                      className="px-3 py-1.5 border border-rose-300 text-rose-700 bg-rose-50 hover:bg-rose-100 text-xs font-medium rounded-lg"
                    >
                      Reject
                    </button>
                  </div>
                </div>

                {/* Plain Language Legal Explanation */}
                <div className="bg-slate-50 p-4 rounded-lg border border-slate-200 text-xs space-y-2">
                  <h4 className="font-semibold text-slate-900">Statutory Tax Analysis:</h4>
                  <p className="text-slate-700 leading-relaxed">
                    {activeException.description}
                  </p>
                </div>

                {/* Deterministic Evidence Box */}
                {activeException.evidence && (
                  <div className="space-y-2">
                    <h4 className="text-xs font-semibold text-slate-900">Deterministic Evidence:</h4>
                    <pre className="bg-slate-950 text-emerald-400 p-4 rounded-lg font-mono text-[11px] overflow-x-auto border border-slate-800">
                      {JSON.stringify(activeException.evidence, null, 2)}
                    </pre>
                  </div>
                )}

                {/* Suggested Fix */}
                {activeException.suggested_fix && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-xs">
                    <h4 className="font-semibold text-blue-950 mb-1 flex items-center gap-1.5">
                      <Sparkles className="w-3.5 h-3.5 text-blue-700" />
                      <span>Recommended Resolution:</span>
                    </h4>
                    <p className="text-blue-900 leading-relaxed font-medium">
                      {activeException.suggested_fix}
                    </p>
                  </div>
                )}

                {/* Quick Link to Split-Pane Document View */}
                {activeException.document_id && (
                  <div className="pt-2">
                    <Link
                      href={`/documents/${activeException.document_id}`}
                      className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#1E3A8A] hover:underline"
                    >
                      <span>Open Split-Pane Document Viewer</span>
                      <ExternalLink className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                )}

                <AiFooter />
              </div>
            ) : (
              <div className="h-full flex items-center justify-center text-slate-400 text-xs">
                Select an exception from the queue to inspect statutory evidence
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
