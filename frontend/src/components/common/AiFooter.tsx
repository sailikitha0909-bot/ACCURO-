import React from "react";

interface AiFooterProps {
  className?: string;
}

export const AiFooter: React.FC<AiFooterProps> = ({ className = "" }) => {
  return (
    <div
      className={`flex items-center justify-between text-[11px] text-slate-500 border-t border-slate-200/80 pt-2.5 mt-4 ${className}`}
    >
      <div className="flex items-center gap-1.5">
        <span className="w-1.5 h-1.5 rounded-full bg-blue-600 animate-pulse" />
        <span className="font-medium text-slate-600">
          AI-prepared draft by Accuro. Requires CA review.
        </span>
      </div>
      <span className="font-mono text-[10px] text-slate-400">
        Deterministic Verification Engine Active
      </span>
    </div>
  );
};
