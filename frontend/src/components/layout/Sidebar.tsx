"use client";

import React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard,
  Building2,
  FileText,
  BookOpen,
  ArrowLeftRight,
  AlertOctagon,
  FileSpreadsheet,
  ShieldCheck,
  Settings,
  LogOut,
  UserCheck,
} from "lucide-react";
import { Logo } from "../common/Logo";
import { getCurrentUser, clearAuthSession } from "@/lib/api";

const NAV_ITEMS = [
  { label: "Dashboard", href: "/", icon: LayoutDashboard },
  { label: "Exceptions", href: "/exceptions", icon: AlertOctagon, highlight: true },
  { label: "Clients", href: "/clients", icon: Building2 },
  { label: "Documents", href: "/documents", icon: FileText },
  { label: "Entries", href: "/entries", icon: BookOpen },
  { label: "GST Reconciliation", href: "/reconciliation", icon: ArrowLeftRight },
  { label: "Reports & Exports", href: "/reports", icon: FileSpreadsheet },
  { label: "Audit & DPDP", href: "/audit", icon: ShieldCheck },
  { label: "Settings & Rules", href: "/settings", icon: Settings },
];

export const Sidebar: React.FC = () => {
  const pathname = usePathname();
  const router = useRouter();
  const user = getCurrentUser();

  const handleLogout = () => {
    clearAuthSession();
    router.push("/login");
  };

  return (
    <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col flex-shrink-0 min-h-screen border-r border-slate-800">
      {/* Top Branding */}
      <div className="p-5 border-b border-slate-800/80">
        <Logo size="md" showTagline />
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                isActive
                  ? "bg-[#1E3A8A] text-white shadow-sm"
                  : "text-slate-400 hover:text-slate-100 hover:bg-slate-800/60"
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon className={`w-4 h-4 ${isActive ? "text-white" : "text-slate-400"}`} />
                <span>{item.label}</span>
              </div>
              {item.highlight && (
                <span className="w-2 h-2 rounded-full bg-amber-400" />
              )}
            </Link>
          );
        })}
      </nav>

      {/* User Info & Role Badge */}
      <div className="p-4 border-t border-slate-800 bg-slate-950/40">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-full bg-[#1E3A8A] flex items-center justify-center text-xs font-semibold text-white">
              {user?.full_name ? user.full_name[0] : "C"}
            </div>
            <div className="overflow-hidden">
              <p className="text-xs font-semibold text-slate-200 truncate">
                {user?.full_name || "CA Rajesh Mehta"}
              </p>
              <div className="flex items-center gap-1">
                <span className="text-[10px] font-mono uppercase px-1 py-0.2 rounded bg-slate-800 text-slate-300">
                  {user?.role === "partner" ? "Partner / CA" : "Article Staff"}
                </span>
              </div>
            </div>
          </div>
          <button
            onClick={handleLogout}
            title="Log out"
            className="text-slate-400 hover:text-rose-400 p-1 rounded transition-colors"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
        <p className="text-[10px] text-slate-500 font-mono text-center">
          Mehta & Associates • FRN: 105642W
        </p>
      </div>
    </aside>
  );
};
