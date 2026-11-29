"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { StatusBadge } from "@/components/common/StatusBadge";
import { AiFooter } from "@/components/common/AiFooter";
import { DataTable } from "@/components/table/DataTable";
import { apiFetch, getCurrentUser } from "@/lib/api";
import { formatIndianCurrency, formatDate } from "@/lib/formatters";
import { ColumnDef } from "@tanstack/react-table";
import { BookOpen, ShieldCheck, Check, RefreshCw, Filter } from "lucide-react";

export default function EntriesPage() {
  const user = getCurrentUser();
  const isPartner = user?.role === "partner";

  const [entries, setEntries] = useState<any[]>([]);
  const [selectedClientId, setSelectedClientId] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [isLoading, setIsLoading] = useState(true);

  const loadEntries = () => {
    setIsLoading(true);
    let url = "/entries?";
    if (selectedClientId) url += `client_id=${selectedClientId}&`;
    if (statusFilter) url += `status_filter=${statusFilter}`;

    apiFetch<any[]>(url)
      .then((data) => setEntries(data || []))
      .catch((err) => console.error(err))
      .finally(() => setIsLoading(false));
  };

  useEffect(() => {
    loadEntries();
  }, [selectedClientId, statusFilter]);

  const handleQuickApprove = async (entryId: string) => {
    try {
      await apiFetch(`/entries/${entryId}/approve`, { method: "POST" });
      loadEntries();
    } catch (err: any) {
      alert(err.message || "Approval failed");
    }
  };

  const columns: ColumnDef<any>[] = [
    {
      accessorKey: "invoice_number",
      header: "Invoice #",
      cell: ({ row }) => (
        <span className="font-mono font-semibold text-slate-900">
          {row.original.invoice_number}
        </span>
      ),
    },
    {
      accessorKey: "invoice_date",
      header: "Date",
      cell: ({ row }) => (
        <span className="font-mono text-slate-600">{formatDate(row.original.invoice_date)}</span>
      ),
    },
    {
      accessorKey: "party_name",
      header: "Party / Vendor",
      cell: ({ row }) => (
        <div>
          <p className="font-semibold text-slate-800 truncate max-w-xs">{row.original.party_name}</p>
          <p className="font-mono text-[10px] text-slate-400">{row.original.party_gstin || "Unregistered"}</p>
        </div>
      ),
    },
    {
      accessorKey: "taxable_value_paise",
      header: "Taxable (₹)",
      cell: ({ row }) => (
        <span className="font-mono text-slate-800">
          {formatIndianCurrency(row.original.taxable_value_paise)}
        </span>
      ),
    },
    {
      id: "taxes",
      header: "GST Tax (₹)",
      cell: ({ row }) => {
        const cgst = row.original.cgst_paise || 0;
        const sgst = row.original.sgst_paise || 0;
        const igst = row.original.igst_paise || 0;
        const totalTax = cgst + sgst + igst;
        return (
          <div>
            <span className="font-mono text-slate-800">{formatIndianCurrency(totalTax)}</span>
            <p className="text-[10px] text-slate-400 font-mono">
              {igst > 0 ? `IGST: ${formatIndianCurrency(igst)}` : `C+S: ${formatIndianCurrency(cgst*2)}`}
            </p>
          </div>
        );
      },
    },
    {
      accessorKey: "total_amount_paise",
      header: "Total Amount (₹)",
      cell: ({ row }) => (
        <span className="font-mono font-bold text-[#1E3A8A]">
          {formatIndianCurrency(row.original.total_amount_paise)}
        </span>
      ),
    },
    {
      accessorKey: "status",
      header: "Status",
      cell: ({ row }) => <StatusBadge status={row.original.status} size="sm" />,
    },
    {
      id: "actions",
      header: "CA Action",
      cell: ({ row }) => {
        if (row.original.status === "final") {
          return (
            <span className="inline-flex items-center gap-1 text-[11px] font-mono text-emerald-700">
              <Check className="w-3 h-3 text-emerald-600" />
              <span>Finalised</span>
            </span>
          );
        }
        if (isPartner) {
          return (
            <button
              onClick={() => handleQuickApprove(row.original.id)}
              className="px-2.5 py-1 bg-[#1E3A8A] hover:bg-blue-900 text-white rounded text-[11px] font-semibold transition-colors"
            >
              Approve (CA)
            </button>
          );
        }
        return <span className="text-[11px] text-slate-400 font-mono">Draft</span>;
      },
    },
  ];

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />

      <main className="flex-1 flex flex-col min-w-0">
        <Header
          title="Accounting Entries & Vouchers Schedule"
          subtitle="AI-prepared double-entry vouchers awaiting CA approval or finalized for Tally export"
          selectedClientId={selectedClientId}
          onClientChange={(id) => setSelectedClientId(id)}
        />

        <div className="p-8 space-y-6 max-w-7xl mx-auto w-full">
          {/* Controls Bar */}
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1.5 text-xs text-slate-500 font-medium">
                <Filter className="w-3.5 h-3.5 text-slate-400" />
                <span>Status:</span>
              </div>
              <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg text-xs">
                {["", "draft", "final", "rejected"].map((st) => (
                  <button
                    key={st}
                    onClick={() => setStatusFilter(st)}
                    className={`px-3 py-1 rounded-md font-medium transition-colors ${
                      statusFilter === st
                        ? "bg-white text-slate-900 shadow-xs"
                        : "text-slate-600 hover:text-slate-900"
                    }`}
                  >
                    {st === "" ? "All Entries" : st.toUpperCase()}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex items-center gap-3">
              <span className="text-xs text-slate-500 font-mono">
                {entries.length} vouchers recorded
              </span>
              <button
                onClick={loadEntries}
                className="text-xs text-slate-600 hover:text-slate-900 flex items-center gap-1 font-medium"
              >
                <RefreshCw className="w-3 h-3" />
                <span>Refresh</span>
              </button>
            </div>
          </div>

          {/* Table */}
          <DataTable columns={columns} data={entries} pageSize={12} />

          <AiFooter />
        </div>
      </main>
    </div>
  );
}
