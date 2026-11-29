import React from "react";

interface LogoProps {
  className?: string;
  showTagline?: boolean;
  size?: "sm" | "md" | "lg";
}

export const Logo: React.FC<LogoProps> = ({
  className = "",
  showTagline = false,
  size = "md",
}) => {
  const iconSize = size === "sm" ? 20 : size === "lg" ? 32 : 26;
  const textSize = size === "sm" ? "text-lg" : size === "lg" ? "text-2xl" : "text-xl";

  return (
    <div className={`flex flex-col ${className}`}>
      <div className="flex items-center gap-2">
        {/* Ledger line icon with checkmark */}
        <div
          className="flex items-center justify-center rounded bg-[#1E3A8A] text-white shadow-sm flex-shrink-0"
          style={{ width: iconSize, height: iconSize }}
        >
          <svg
            className="w-4 h-4"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            {/* Top ledger line */}
            <line x1="3" y1="5" x2="21" y2="5" opacity="0.4" />
            {/* Checkmark resting on middle ledger line */}
            <line x1="3" y1="12" x2="8" y2="12" />
            <polyline points="7 11 11 15 17 8" />
            <line x1="16" y1="12" x2="21" y2="12" />
            {/* Bottom ledger line */}
            <line x1="3" y1="19" x2="21" y2="19" opacity="0.4" />
          </svg>
        </div>
        <div className="flex items-baseline gap-1.5">
          <span className={`font-semibold tracking-tight text-slate-900 dark:text-white ${textSize}`}>
            Accuro
          </span>
          <span className="text-[10px] font-mono uppercase tracking-widest text-[#1E3A8A] bg-blue-50 dark:bg-blue-950/40 px-1 py-0.5 rounded border border-blue-100 dark:border-blue-900">
            CA
          </span>
        </div>
      </div>
      {showTagline && (
        <span className="text-xs text-slate-500 dark:text-slate-400 mt-1 font-normal">
          Accurate accounts. You review, Accuro does the rest.
        </span>
      )}
    </div>
  );
};
