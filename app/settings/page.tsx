"use client";

import React, { useState, useEffect } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { AiFooter } from "@/components/common/AiFooter";
import { apiFetch, getCurrentUser } from "@/lib/api";
import {
  Settings as SettingsIcon,
  Sparkles,
  Trash2,
  Plus,
  Clock,
  Shield,
  Save,
  CheckCircle2,
} from "lucide-react";

export default function SettingsPage() {
  const user = getCurrentUser();
  const isPartner = user?.role === "partner";

  const [rules, setRules] = useState<any[]>([]);
  const [benchmarkMins, setBenchmarkMins] = useState(15.0);
  const [retentionYears, setRetentionYears] = useState(8);
  const [statusMsg, setStatusMsg] = useState("");
  const [selectedClientId, setSelectedClientId] = useState("");
  const [clients, setClients] = useState<any[]>([]);

  const loadRules = () => {
    const param = selectedClientId ? `?client_id=${selectedClientId}` : "";
    apiFetch<any[]>(`/rules${param}`)
      .then((data) => setRules(data || []))
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
      loadRules();
    }
  }, [selectedClientId]);

  const handleDeleteRule = async (ruleId: string) => {
    if (!confirm("Are you sure you want to remove this categorisation rule?")) return;
    try {
      await apiFetch(`/rules/${ruleId}`, { method: "DELETE" });
      setStatusMsg("Rule removed successfully.");
      loadRules();
    } catch (err: any) {
      alert(err.message || "Failed to delete rule");
    }
  };

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />

      <main className="flex-1 flex flex-col min-w-0">
        <Header
          title="Firm Settings & Learned Categorisation Rules"
          subtitle="Configure deterministic productivity benchmarks, DPDP retention and manage continuous learning rules"
          selectedClientId={selectedClientId}
          onClientChange={(id) => setSelectedClientId(id)}
        />

        <div className="p-8 space-y-6 max-w-7xl mx-auto w-full">
          {statusMsg && (
            <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs px-4 py-2.5 rounded-lg flex items-center justify-between">
              <span>{statusMsg}</span>
              <button onClick={() => setStatusMsg("")} className="font-bold text-emerald-900">✕</button>
            </div>
          )}

          {/* Productivity Benchmark Card */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4">
            <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
              <Clock className="w-5 h-5 text-[#1E3A8A]" />
              <div>
                <h3 className="text-sm font-semibold text-slate-900">
                  Productivity Metric Benchmark Configuration
                </h3>
                <p className="text-xs text-slate-500">
                  Configures the formula used across the firm to calculate CA hours saved
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-2">
                <label className="block font-semibold text-slate-800">
                  Manual Entry Benchmark (Minutes / Document)
                </label>
                <div className="flex items-center gap-3">
                  <input
                    type="number"
                    step="0.5"
                    min="5"
                    max="60"
                    value={benchmarkMins}
                    onChange={(e) => setBenchmarkMins(parseFloat(e.target.value) || 15.0)}
                    className="w-24 px-3 py-1.5 font-mono text-center border border-slate-300 rounded-lg bg-white"
                  />
                  <span className="text-slate-600 font-medium">mins per physical invoice</span>
                </div>
                <p className="text-[11px] text-slate-500">
                  Default standard in Indian CA practice: 15.0 minutes for full voucher punching + GST split.
                </p>
              </div>

              <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-2">
                <label className="block font-semibold text-slate-800">
                  Statutory Data Retention (Years)
                </label>
                <div className="flex items-center gap-3">
                  <input
                    type="number"
                    min="6"
                    max="15"
                    value={retentionYears}
                    onChange={(e) => setRetentionYears(parseInt(e.target.value) || 8)}
                    className="w-24 px-3 py-1.5 font-mono text-center border border-slate-300 rounded-lg bg-white"
                  />
                  <span className="text-slate-600 font-medium">years statutory retention</span>
                </div>
                <p className="text-[11px] text-slate-500">
                  Section 44AA of Income Tax Act requires 6-8 years preservation of books and vouchers.
                </p>
              </div>
            </div>
          </div>

          {/* Continuous Learning Categorisation Rules */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="px-6 py-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-blue-600" />
                  <span>Learned Categorisation Rules ({rules.length})</span>
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Rules created or updated automatically whenever a CA Partner or Staff corrects a voucher ledger
                </p>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 border-b border-slate-200 text-slate-700 font-semibold uppercase tracking-wider">
                  <tr>
                    <th className="px-6 py-3">Vendor / Match Pattern</th>
                    <th className="px-6 py-3">Rule Type</th>
                    <th className="px-6 py-3">Confidence</th>
                    <th className="px-6 py-3">Source</th>
                    <th className="px-6 py-3 text-center">Usage Count</th>
                    {isPartner && <th className="px-6 py-3 text-right">Action</th>}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {rules.map((r) => (
                    <tr key={r.id} className="hover:bg-slate-50/80">
                      <td className="px-6 py-3 font-semibold text-slate-900">{r.match_pattern}</td>
                      <td className="px-6 py-3 font-mono text-slate-600 uppercase text-[11px]">{r.rule_type}</td>
                      <td className="px-6 py-3 font-mono font-medium text-blue-900">
                        {Math.round(r.confidence * 100)}%
                      </td>
                      <td className="px-6 py-3">
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200">
                          {r.source.replace(/_/g, " ")}
                        </span>
                      </td>
                      <td className="px-6 py-3 text-center font-mono font-bold text-slate-700">
                        {r.usage_count}
                      </td>
                      {isPartner && (
                        <td className="px-6 py-3 text-right">
                          <button
                            onClick={() => handleDeleteRule(r.id)}
                            className="p-1 text-slate-400 hover:text-rose-600 transition-colors"
                            title="Delete Rule"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </td>
                      )}
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
