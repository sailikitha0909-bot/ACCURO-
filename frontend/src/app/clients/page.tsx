"use client";

import React, { useState, useEffect } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { StatusBadge } from "@/components/common/StatusBadge";
import { AiFooter } from "@/components/common/AiFooter";
import { apiFetch, getCurrentUser } from "@/lib/api";
import {
  Building2,
  Calendar,
  Plus,
  Link as LinkIcon,
  Send,
  Copy,
  Check,
  FileQuestion,
  ShieldCheck,
  ExternalLink,
} from "lucide-react";

export default function ClientsPage() {
  const user = getCurrentUser();
  const isPartner = user?.role === "partner";

  const [clients, setClients] = useState<any[]>([]);
  const [selectedClient, setSelectedClient] = useState<any | null>(null);
  const [deadlines, setDeadlines] = useState<any[]>([]);
  const [portalLink, setPortalLink] = useState<string | null>(null);
  const [copiedLink, setCopiedLink] = useState(false);
  const [reminderDraft, setReminderDraft] = useState<any | null>(null);
  const [isDrafting, setIsDrafting] = useState(false);
  const [showAddClient, setShowAddClient] = useState(false);
  const [newClientData, setNewClientData] = useState({
    legal_name: "",
    trade_name: "",
    gstin: "",
    pan: "",
    state_code: "27",
    entity_type: "private_limited",
    contact_person: "",
    contact_email: "",
  });

  const loadClients = () => {
    apiFetch<any[]>("/clients")
      .then((data) => {
        setClients(data || []);
        if (data && data.length > 0) {
          setSelectedClient(data[0]);
        }
      })
      .catch((err) => console.error(err));
  };

  useEffect(() => {
    loadClients();
  }, []);

  useEffect(() => {
    if (selectedClient) {
      apiFetch<any[]>(`/clients/${selectedClient.id}/compliance-calendar`)
        .then((d) => setDeadlines(d || []))
        .catch(() => {});
    }
  }, [selectedClient]);

  const generatePortalLink = async () => {
    if (!selectedClient) return;
    try {
      const res = await apiFetch<any>(`/clients/${selectedClient.id}/portal-token`, {
        method: "POST",
      });
      const fullUrl = `${window.location.origin}${res.portal_url}`;
      setPortalLink(fullUrl);
    } catch (err: any) {
      alert(err.message || "Failed to generate token");
    }
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedLink(true);
    setTimeout(() => setCopiedLink(false), 2000);
  };

  const draftReminder = async () => {
    if (!selectedClient) return;
    setIsDrafting(true);
    try {
      const res = await apiFetch<any>(
        `/clients/${selectedClient.id}/missing-doc-reminder?vendor_name=Reliance%20Jio&period=July%202024`,
        { method: "POST" }
      );
      setReminderDraft(res);
    } catch (err: any) {
      alert(err.message || "Failed to draft reminder");
    } finally {
      setIsDrafting(false);
    }
  };

  const handleCreateClient = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiFetch("/clients", {
        method: "POST",
        body: JSON.stringify(newClientData),
      });
      setShowAddClient(false);
      loadClients();
    } catch (err: any) {
      alert(err.message || "Failed to add client");
    }
  };

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />

      <main className="flex-1 flex flex-col min-w-0">
        <Header
          title="Clients & Statutory Workflow"
          subtitle="Client portfolio management, compliance calendar and secure client document upload links"
          actions={
            isPartner && (
              <button
                onClick={() => setShowAddClient(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-[#1E3A8A] text-white rounded-lg hover:bg-blue-900 shadow-sm"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Onboard New Client</span>
              </button>
            )
          }
        />

        <div className="p-8 space-y-6 max-w-7xl mx-auto w-full">
          {/* Client Selection Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {clients.map((c) => {
              const isSelected = selectedClient?.id === c.id;
              return (
                <div
                  key={c.id}
                  onClick={() => {
                    setSelectedClient(c);
                    setPortalLink(null);
                    setReminderDraft(null);
                  }}
                  className={`p-5 rounded-xl border bg-white cursor-pointer transition-all ${
                    isSelected
                      ? "border-[#1E3A8A] ring-2 ring-blue-600/20 shadow-md"
                      : "border-slate-200 hover:border-slate-300 shadow-xs"
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-slate-100 text-slate-700">
                      {c.entity_type.replace(/_/g, " ")}
                    </span>
                    <span className="w-2 h-2 rounded-full bg-emerald-500" />
                  </div>
                  <h3 className="font-bold text-sm text-slate-900 leading-snug">{c.legal_name}</h3>
                  <p className="text-xs text-slate-500 mt-1 font-mono">
                    GSTIN: {c.gstin || "Unregistered"}
                  </p>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    State Code: {c.state_code} • Contact: {c.contact_person || "-"}
                  </p>
                </div>
              );
            })}
          </div>

          {/* Active Client Workflow Detail */}
          {selectedClient && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Compliance Calendar (2 cols) */}
              <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-5">
                <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                  <div>
                    <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                      <Calendar className="w-4 h-4 text-[#1E3A8A]" />
                      <span>Statutory Compliance Calendar — {selectedClient.legal_name}</span>
                    </h3>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Statutory GST, TDS, and Advance Tax deadlines under Indian Acts
                    </p>
                  </div>
                </div>

                <div className="divide-y divide-slate-100">
                  {deadlines.map((dl, idx) => (
                    <div key={idx} className="py-3 flex items-center justify-between">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-xs text-slate-900">{dl.title}</span>
                          <StatusBadge status={dl.status} size="sm" />
                        </div>
                        <p className="text-[11px] text-slate-500 mt-0.5">
                          Category: {dl.category} • Form/Challan: {dl.form} • Period: {dl.period}
                        </p>
                      </div>
                      <span className="text-xs font-mono font-bold text-slate-700">
                        {dl.due_date}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Secure Portal Link & Missing Document Reminders (1 col) */}
              <div className="space-y-4">
                {/* Secure Client Upload Link Box */}
                <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-3">
                  <div className="flex items-center gap-2 text-slate-900 font-semibold text-xs">
                    <LinkIcon className="w-4 h-4 text-[#1E3A8A]" />
                    <span>Secure Client Upload Portal</span>
                  </div>
                  <p className="text-[11px] text-slate-500 leading-relaxed">
                    Generate an expiring, token-authenticated link allowing {selectedClient.trade_name || selectedClient.legal_name} to drag & drop bills directly into Accuro without requiring credentials.
                  </p>

                  {portalLink ? (
                    <div className="space-y-2 bg-blue-50/60 p-3 rounded-lg border border-blue-100">
                      <span className="text-[10px] font-mono text-blue-900 block truncate">
                        {portalLink}
                      </span>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleCopy(portalLink)}
                          className="px-2.5 py-1 text-xs bg-white border border-blue-300 text-blue-900 rounded font-medium flex items-center gap-1 shadow-xs hover:bg-blue-50"
                        >
                          {copiedLink ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3" />}
                          <span>{copiedLink ? "Copied Link" : "Copy Link"}</span>
                        </button>
                        <a
                          href={portalLink}
                          target="_blank"
                          rel="noreferrer"
                          className="px-2.5 py-1 text-xs text-[#1E3A8A] font-medium hover:underline flex items-center gap-1"
                        >
                          <span>Open</span>
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      </div>
                    </div>
                  ) : (
                    <button
                      onClick={generatePortalLink}
                      className="w-full py-2 bg-slate-900 hover:bg-black text-white text-xs font-semibold rounded-lg shadow-sm transition-colors"
                    >
                      Generate Secure Upload Link (7 Days)
                    </button>
                  )}
                </div>

                {/* Missing Document Detection Box */}
                <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-3">
                  <div className="flex items-center gap-2 text-slate-900 font-semibold text-xs">
                    <FileQuestion className="w-4 h-4 text-amber-600" />
                    <span>Missing Invoices Detection</span>
                  </div>
                  <p className="text-[11px] text-slate-500 leading-relaxed">
                    Accuro detected that regular recurring vendor bills (e.g. Reliance Jio leased line for July 2024) are missing from client records.
                  </p>

                  {reminderDraft ? (
                    <div className="space-y-2 bg-slate-50 p-3 rounded-lg border border-slate-200 text-xs">
                      <p className="font-semibold text-slate-900">Auto-Drafted Client Reminder:</p>
                      <textarea
                        readOnly
                        rows={4}
                        value={reminderDraft.email_body}
                        className="w-full text-[11px] bg-white p-2 rounded border border-slate-200 font-mono text-slate-700"
                      />
                      <div className="flex items-center gap-2 pt-1">
                        <button
                          onClick={() => handleCopy(reminderDraft.email_body)}
                          className="px-2 py-1 bg-white border border-slate-300 text-slate-700 rounded text-[11px] hover:bg-slate-100 flex items-center gap-1"
                        >
                          <Copy className="w-3 h-3" />
                          <span>Copy Email</span>
                        </button>
                        <button
                          onClick={() => handleCopy(reminderDraft.whatsapp_message)}
                          className="px-2 py-1 bg-emerald-600 text-white rounded text-[11px] hover:bg-emerald-700 flex items-center gap-1"
                        >
                          <Send className="w-3 h-3" />
                          <span>Copy WhatsApp Text</span>
                        </button>
                      </div>
                    </div>
                  ) : (
                    <button
                      onClick={draftReminder}
                      disabled={isDrafting}
                      className="w-full py-2 bg-white border border-slate-300 text-slate-800 text-xs font-semibold rounded-lg hover:bg-slate-50 transition-colors"
                    >
                      {isDrafting ? "Drafting Reminder..." : "Auto-Draft Client Reminder"}
                    </button>
                  )}
                </div>
              </div>
            </div>
          )}

          <AiFooter />
        </div>
      </main>
    </div>
  );
}
