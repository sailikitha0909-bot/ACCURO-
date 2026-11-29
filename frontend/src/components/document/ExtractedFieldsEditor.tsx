"use client";

import React, { useState, useEffect } from "react";
import { CheckCircle2, AlertTriangle, ShieldCheck, Save, Sparkles } from "lucide-react";
import { formatIndianCurrency } from "@/lib/formatters";
import { StatusBadge } from "../common/StatusBadge";
import { AiFooter } from "../common/AiFooter";
import { apiFetch, getCurrentUser } from "@/lib/api";

interface ExtractedFieldsEditorProps {
  documentId: string;
  entryData: any;
  exceptions?: any[];
  onSaved?: () => void;
  onFocusField?: (fieldKey: string) => void;
}

export const ExtractedFieldsEditor: React.FC<ExtractedFieldsEditorProps> = ({
  documentId,
  entryData,
  exceptions = [],
  onSaved,
  onFocusField,
}) => {
  const user = getCurrentUser();
  const isPartner = user?.role === "partner";

  const [formData, setFormData] = useState<any>({
    invoice_number: entryData?.invoice_number || "",
    invoice_date: entryData?.invoice_date ? entryData.invoice_date.slice(0, 10) : "",
    party_name: entryData?.party_name || "",
    party_gstin: entryData?.party_gstin || "",
    place_of_supply: entryData?.place_of_supply || "27",
    taxable_value_paise: entryData?.taxable_value_paise || 0,
    cgst_paise: entryData?.cgst_paise || 0,
    sgst_paise: entryData?.sgst_paise || 0,
    igst_paise: entryData?.igst_paise || 0,
    total_amount_paise: entryData?.total_amount_paise || 0,
    debit_account_id: entryData?.debit_account_id || "",
    is_itc_eligible: entryData?.is_itc_eligible ?? true,
  });

  const [accounts, setAccounts] = useState<any[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");
  const [errorMsg, setErrorMsg] = useState("");

  useEffect(() => {
    if (entryData?.client_id) {
      apiFetch<any[]>(`/clients/${entryData.client_id}/chart-of-accounts`)
        .then((data) => setAccounts(data || []))
        .catch(() => {});
    }
  }, [entryData?.client_id]);

  const handleChange = (field: string, val: any) => {
    setFormData((prev: any) => ({ ...prev, [field]: val }));
  };

  const handleSave = async () => {
    if (!entryData?.id) return;
    setIsSubmitting(true);
    setErrorMsg("");
    setSuccessMsg("");
    try {
      await apiFetch(`/entries/${entryData.id}`, {
        method: "PUT",
        body: JSON.stringify(formData),
      });
      setSuccessMsg("Changes saved successfully. Learned rules updated.");
      if (onSaved) onSaved();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to save entry");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleApprove = async () => {
    if (!entryData?.id) return;
    setIsSubmitting(true);
    setErrorMsg("");
    try {
      await apiFetch(`/entries/${entryData.id}/approve`, {
        method: "POST",
      });
      setSuccessMsg("Voucher approved to FINAL by Partner/CA!");
      if (onSaved) onSaved();
    } catch (err: any) {
      setErrorMsg(err.message || "Approval failed");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold text-slate-900">Extracted Voucher Details</h3>
            <StatusBadge status={entryData?.status || "draft"} size="sm" />
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Review AI draft and approve accounting ledger mapping
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleSave}
            disabled={isSubmitting}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors shadow-sm"
          >
            <Save className="w-3.5 h-3.5" />
            <span>Save Draft</span>
          </button>

          {isPartner ? (
            <button
              onClick={handleApprove}
              disabled={isSubmitting || entryData?.status === "final"}
              className={`flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold rounded-lg text-white shadow-sm transition-all ${
                entryData?.status === "final"
                  ? "bg-emerald-600 cursor-default opacity-90"
                  : "bg-[#1E3A8A] hover:bg-blue-900 active:scale-95"
              }`}
            >
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>{entryData?.status === "final" ? "Approved Final" : "Approve Voucher (CA)"}</span>
            </button>
          ) : (
            <span
              className="text-[11px] font-mono text-slate-400 bg-slate-100 px-2 py-1 rounded border border-slate-200"
              title="Article Staff cannot finalize vouchers. Only Partner/CA role can approve."
            >
              CA Approval Required
            </span>
          )}
        </div>
      </div>

      {/* Messages */}
      {successMsg && (
        <div className="px-6 py-2 bg-emerald-50 border-b border-emerald-200 text-emerald-800 text-xs flex items-center gap-1.5">
          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          <span>{successMsg}</span>
        </div>
      )}
      {errorMsg && (
        <div className="px-6 py-2 bg-rose-50 border-b border-rose-200 text-rose-800 text-xs flex items-center gap-1.5">
          <AlertTriangle className="w-4 h-4 text-rose-600" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Form Content */}
      <div className="flex-1 overflow-y-auto p-6 space-y-5">
        {/* Exceptions Warning Box */}
        {exceptions.length > 0 && (
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 space-y-2">
            <div className="flex items-center gap-2 text-amber-900 font-semibold text-xs">
              <AlertTriangle className="w-4 h-4 text-amber-600" />
              <span>{exceptions.length} Compliance Exception(s) Require CA Decision</span>
            </div>
            {exceptions.map((exc, i) => (
              <div key={i} className="text-xs text-amber-800 bg-white/70 p-2.5 rounded border border-amber-200/80">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-semibold text-slate-900">{exc.title}</span>
                  <StatusBadge status={exc.severity} size="sm" />
                </div>
                <p className="text-slate-600 mb-1.5 leading-relaxed">{exc.description}</p>
                {exc.suggested_fix && (
                  <p className="text-blue-900 font-medium bg-blue-50/80 px-2 py-1 rounded text-[11px]">
                    💡 Suggested Fix: {exc.suggested_fix}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Basic Fields Grid */}
        <div className="grid grid-cols-2 gap-4 text-xs">
          <div>
            <label className="block font-medium text-slate-700 mb-1">Supplier / Party Name</label>
            <input
              type="text"
              value={formData.party_name}
              onFocus={() => onFocusField && onFocusField("supplier_name")}
              onChange={(e) => handleChange("party_name", e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block font-medium text-slate-700 mb-1">Supplier GSTIN</label>
            <input
              type="text"
              value={formData.party_gstin}
              onFocus={() => onFocusField && onFocusField("supplier_gstin")}
              onChange={(e) => handleChange("party_gstin", e.target.value.toUpperCase())}
              className="w-full px-3 py-2 font-mono border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none uppercase"
            />
          </div>

          <div>
            <label className="block font-medium text-slate-700 mb-1">Invoice Number</label>
            <input
              type="text"
              value={formData.invoice_number}
              onFocus={() => onFocusField && onFocusField("invoice_number")}
              onChange={(e) => handleChange("invoice_number", e.target.value)}
              className="w-full px-3 py-2 font-mono border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block font-medium text-slate-700 mb-1">Invoice Date</label>
            <input
              type="date"
              value={formData.invoice_date}
              onFocus={() => onFocusField && onFocusField("invoice_date")}
              onChange={(e) => handleChange("invoice_date", e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>
        </div>

        {/* Categorisation Ledger Picker */}
        <div className="bg-slate-50 p-4 rounded-lg border border-slate-200">
          <div className="flex items-center justify-between mb-2">
            <label className="block font-semibold text-xs text-slate-900">
              Assigned Ledger Account (Debit)
            </label>
            <span className="text-[10px] text-blue-700 font-medium flex items-center gap-1">
              <Sparkles className="w-3 h-3 text-blue-600" />
              Rule resolution active
            </span>
          </div>
          <select
            value={formData.debit_account_id}
            onChange={(e) => handleChange("debit_account_id", e.target.value)}
            className="w-full px-3 py-2 text-xs bg-white border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none font-medium"
          >
            <option value="">-- Select Chart of Accounts Ledger --</option>
            {accounts.map((acc) => (
              <option key={acc.id} value={acc.id}>
                {acc.account_code} - {acc.account_name} ({acc.parent_group})
              </option>
            ))}
          </select>
          <p className="text-[11px] text-slate-500 mt-1.5">
            Changing this account automatically trains Accuro&apos;s categorisation engine for future invoices from this supplier.
          </p>
        </div>

        {/* Monetary & Tax Breakdown */}
        <div className="border border-slate-200 rounded-lg overflow-hidden text-xs">
          <div className="bg-slate-100 px-4 py-2 font-semibold text-slate-700 border-b border-slate-200">
            Tax & Amount Schedule (INR)
          </div>
          <div className="p-4 grid grid-cols-2 sm:grid-cols-3 gap-3">
            <div>
              <span className="text-slate-500 text-[11px]">Taxable Value (₹)</span>
              <p className="font-mono font-medium text-slate-900 mt-0.5">
                {formatIndianCurrency(formData.taxable_value_paise)}
              </p>
            </div>
            <div>
              <span className="text-slate-500 text-[11px]">CGST (₹)</span>
              <p className="font-mono text-slate-800 mt-0.5">{formatIndianCurrency(formData.cgst_paise)}</p>
            </div>
            <div>
              <span className="text-slate-500 text-[11px]">SGST (₹)</span>
              <p className="font-mono text-slate-800 mt-0.5">{formatIndianCurrency(formData.sgst_paise)}</p>
            </div>
            <div>
              <span className="text-slate-500 text-[11px]">IGST (₹)</span>
              <p className="font-mono text-slate-800 mt-0.5">{formatIndianCurrency(formData.igst_paise)}</p>
            </div>
            <div>
              <span className="text-slate-500 text-[11px]">Place of Supply</span>
              <p className="font-mono text-slate-800 mt-0.5">{formData.place_of_supply}</p>
            </div>
            <div className="bg-blue-50/50 p-2 rounded border border-blue-100">
              <span className="text-[#1E3A8A] font-semibold text-[11px]">Total Voucher Value</span>
              <p className="font-mono font-bold text-sm text-[#1E3A8A] mt-0.5">
                {formatIndianCurrency(formData.total_amount_paise)}
              </p>
            </div>
          </div>
        </div>

        {/* ITC Eligibility Toggle */}
        <div className="flex items-center justify-between p-3 rounded-lg border border-slate-200 text-xs">
          <div>
            <p className="font-medium text-slate-900">Input Tax Credit (ITC) Availment</p>
            <p className="text-[11px] text-slate-500">
              Uncheck if credit is blocked under Section 17(5) or personal consumption.
            </p>
          </div>
          <input
            type="checkbox"
            checked={formData.is_itc_eligible}
            onChange={(e) => handleChange("is_itc_eligible", e.target.checked)}
            className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500 cursor-pointer"
          />
        </div>

        <AiFooter />
      </div>
    </div>
  );
};
