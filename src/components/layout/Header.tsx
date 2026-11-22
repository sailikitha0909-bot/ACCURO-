"use client";

import React, { useState, useEffect } from "react";
import { Building, Calendar, Plus, RefreshCw } from "lucide-react";
import { apiFetch } from "@/lib/api";

interface HeaderProps {
  title: string;
  subtitle?: string;
  selectedClientId?: string;
  onClientChange?: (clientId: string) => void;
  actions?: React.ReactNode;
}

export const Header: React.FC<HeaderProps> = ({
  title,
  subtitle,
  selectedClientId = "",
  onClientChange,
  actions,
}) => {
  const [clients, setClients] = useState<any[]>([]);

  useEffect(() => {
    apiFetch<any[]>("/clients")
      .then((data) => setClients(data || []))
      .catch(() => {});
  }, []);

  return (
    <header className="bg-white border-b border-slate-200 px-8 py-4 flex flex-col md:flex-row md:items-center justify-between gap-4 sticky top-0 z-20">
      <div>
        <h1 className="text-xl font-semibold text-slate-900 tracking-tight">{title}</h1>
        {subtitle && <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>}
      </div>

      <div className="flex items-center gap-3">
        {/* Client Selector Filter */}
        <div className="flex items-center gap-2 bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-lg text-xs">
          <Building className="w-3.5 h-3.5 text-slate-400" />
          <select
            value={selectedClientId}
            onChange={(e) => onClientChange && onClientChange(e.target.value)}
            className="bg-transparent text-slate-700 font-medium focus:outline-none cursor-pointer"
          >
            <option value="">All Clients (Firm-wide)</option>
            {clients.map((c) => (
              <option key={c.id} value={c.id}>
                {c.legal_name}
              </option>
            ))}
          </select>
        </div>

        {/* Financial Year Pill */}
        <div className="hidden sm:flex items-center gap-1.5 bg-blue-50 border border-blue-100 px-2.5 py-1.5 rounded-lg text-xs font-medium text-[#1E3A8A]">
          <Calendar className="w-3.5 h-3.5" />
          <span>FY 2024-25</span>
        </div>

        {/* Custom Page Actions */}
        {actions}
      </div>
    </header>
  );
};
