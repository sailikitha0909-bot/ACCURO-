"use client";

import React, { useState } from "react";
import { ZoomIn, ZoomOut, RotateCw, Eye } from "lucide-react";

interface BBox {
  page: number;
  box: [number, number, number, number]; // [ymin, xmin, ymax, xmax]
}

interface DocumentViewerProps {
  filename: string;
  fileType: string;
  extractionData?: any;
  activeFieldKey?: string | null;
  onSelectField?: (fieldKey: string) => void;
}

export const DocumentViewer: React.FC<DocumentViewerProps> = ({
  filename,
  fileType,
  extractionData,
  activeFieldKey,
  onSelectField,
}) => {
  const [zoom, setZoom] = useState(100);

  const fields = [
    { key: "supplier_name", label: "Supplier", data: extractionData?.supplier_name },
    { key: "supplier_gstin", label: "GSTIN", data: extractionData?.supplier_gstin },
    { key: "invoice_number", label: "Invoice No", data: extractionData?.invoice_number },
    { key: "invoice_date", label: "Date", data: extractionData?.invoice_date },
    { key: "taxable_value_paise", label: "Taxable Value", data: extractionData?.taxable_value_paise },
    { key: "total_amount_paise", label: "Total Amount", data: extractionData?.total_amount_paise },
  ];

  return (
    <div className="flex flex-col h-full bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-inner">
      {/* Top Viewer Controls */}
      <div className="flex items-center justify-between px-4 py-2 bg-slate-950 border-b border-slate-800 text-slate-300 text-xs">
        <div className="flex items-center gap-2">
          <Eye className="w-3.5 h-3.5 text-blue-400" />
          <span className="font-mono truncate max-w-xs">{filename}</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setZoom((z) => Math.max(70, z - 10))}
            className="p-1 hover:bg-slate-800 rounded text-slate-400 hover:text-white"
            title="Zoom out"
          >
            <ZoomOut className="w-3.5 h-3.5" />
          </button>
          <span className="font-mono text-[11px] w-10 text-center">{zoom}%</span>
          <button
            onClick={() => setZoom((z) => Math.min(150, z + 10))}
            className="p-1 hover:bg-slate-800 rounded text-slate-400 hover:text-white"
            title="Zoom in"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Document View Canvas */}
      <div className="flex-1 overflow-auto p-6 flex justify-center bg-slate-900/60">
        <div
          className="relative bg-white text-slate-900 shadow-2xl rounded p-8 transition-transform origin-top w-full max-w-[620px] min-h-[750px] border border-slate-300 font-sans text-xs select-none"
          style={{ transform: `scale(${zoom / 100})` }}
        >
          {/* Simulated Physical Tax Invoice */}
          <div className="border-b-2 border-slate-900 pb-4 mb-4 flex justify-between items-start">
            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Tax Invoice</span>
              <h2 className="text-base font-bold text-slate-900">
                {extractionData?.supplier_name?.value || "Vendor Corporation Pvt Ltd"}
              </h2>
              <p className="text-[11px] text-slate-600">
                GSTIN: <span className="font-mono font-semibold">{extractionData?.supplier_gstin?.value || "27AABCA1234F1Z5"}</span>
              </p>
              <p className="text-[10px] text-slate-500">Registered Office: Bandra Kurla Complex, Mumbai, MH</p>
            </div>
            <div className="text-right">
              <div className="bg-slate-100 p-2 rounded border border-slate-200">
                <p className="text-[10px] text-slate-500">Invoice Ref #</p>
                <p className="font-mono font-bold text-sm text-slate-900">
                  {extractionData?.invoice_number?.value || "INV-2024-88421"}
                </p>
                <p className="text-[10px] text-slate-500 mt-1">Date: {extractionData?.invoice_date?.value || "2024-07-05"}</p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 mb-6 bg-slate-50 p-3 rounded border border-slate-200 text-[11px]">
            <div>
              <p className="font-semibold text-slate-700">Billed To (Client):</p>
              <p className="font-medium text-slate-900">Apex Retailers Private Limited</p>
              <p className="text-slate-600 font-mono text-[10px]">GSTIN: 27AABCA1234F1Z5</p>
              <p className="text-slate-500">Place of Supply: 27 - Maharashtra</p>
            </div>
            <div>
              <p className="font-semibold text-slate-700">Dispatch Details:</p>
              <p className="text-slate-600">Terms: Immediate Settlement</p>
              <p className="text-slate-600">PO Ref: PO/2024/0991</p>
            </div>
          </div>

          {/* Line items schedule */}
          <table className="w-full text-left text-[11px] mb-6">
            <thead>
              <tr className="border-b border-slate-300 text-slate-600 font-semibold">
                <th className="py-1.5">Description</th>
                <th className="py-1.5 font-mono">HSN/SAC</th>
                <th className="py-1.5 text-right font-mono">Rate (%)</th>
                <th className="py-1.5 text-right font-mono">Amount (₹)</th>
              </tr>
            </thead>
            <tbody>
              {extractionData?.line_items?.map((item: any, i: number) => (
                <tr key={i} className="border-b border-slate-100">
                  <td className="py-2 text-slate-800 font-medium">{item.description}</td>
                  <td className="py-2 font-mono text-slate-500">{item.hsn_sac || "9983"}</td>
                  <td className="py-2 text-right font-mono text-slate-600">{item.gst_rate}%</td>
                  <td className="py-2 text-right font-mono font-medium text-slate-900">
                    ₹{(item.taxable_paise / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                  </td>
                </tr>
              )) || (
                <tr>
                  <td className="py-2">Cloud Computing Infrastructure Services</td>
                  <td className="py-2 font-mono">9983</td>
                  <td className="py-2 text-right font-mono">18%</td>
                  <td className="py-2 text-right font-mono">₹45,000.00</td>
                </tr>
              )}
            </tbody>
          </table>

          {/* Totals Section */}
          <div className="flex justify-end mt-4">
            <div className="w-64 space-y-1.5 text-right text-[11px]">
              <div className="flex justify-between text-slate-600">
                <span>Taxable Value:</span>
                <span className="font-mono">
                  ₹{((extractionData?.taxable_value_paise?.value || 4500000) / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                </span>
              </div>
              <div className="flex justify-between text-slate-600">
                <span>CGST (9%):</span>
                <span className="font-mono">
                  ₹{((extractionData?.cgst_paise?.value || 0) / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                </span>
              </div>
              <div className="flex justify-between text-slate-600">
                <span>SGST (9%):</span>
                <span className="font-mono">
                  ₹{((extractionData?.sgst_paise?.value || 0) / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                </span>
              </div>
              <div className="flex justify-between text-slate-600">
                <span>IGST (18%):</span>
                <span className="font-mono">
                  ₹{((extractionData?.igst_paise?.value || 810000) / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                </span>
              </div>
              <div className="flex justify-between font-bold text-sm text-slate-900 border-t border-slate-300 pt-2">
                <span>Total Amount:</span>
                <span className="font-mono text-[#1E3A8A]">
                  ₹{((extractionData?.total_amount_paise?.value || 5310000) / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                </span>
              </div>
            </div>
          </div>

          {/* Interactive Bounding Box Overlays */}
          {fields.map((f) => {
            const loc = f.data?.location?.box;
            if (!loc) return null;
            const isSelected = activeFieldKey === f.key;

            return (
              <div
                key={f.key}
                onClick={() => onSelectField && onSelectField(f.key)}
                className={`absolute cursor-pointer transition-all border-2 rounded ${
                  isSelected
                    ? "border-blue-600 bg-blue-500/20 ring-2 ring-blue-400 z-10"
                    : "border-amber-400/60 bg-amber-300/10 hover:border-amber-500 hover:bg-amber-300/25"
                }`}
                style={{
                  top: `${(loc[0] / 800) * 100}%`,
                  left: `${(loc[1] / 600) * 100}%`,
                  height: `${((loc[2] - loc[0]) / 800) * 100}%`,
                  width: `${((loc[3] - loc[1]) / 600) * 100}%`,
                }}
                title={`${f.label} (Confidence: ${Math.round((f.data.confidence || 0.9) * 100)}%)`}
              >
                <span className="absolute -top-4 left-0 text-[9px] font-mono px-1 rounded bg-[#1E3A8A] text-white whitespace-nowrap shadow-sm opacity-90">
                  {f.label} ({Math.round((f.data.confidence || 0.9) * 100)}%)
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
