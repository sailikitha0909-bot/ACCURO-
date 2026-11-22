import React from "react";

interface StatusBadgeProps {
  status: string;
  size?: "sm" | "md";
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = "md", className = "" }) => {
  const norm = (status || "").toLowerCase().trim();

  let colorClasses = "bg-slate-100 text-slate-700 border-slate-200";

  // Severity Badges
  if (norm === "high") {
    colorClasses = "bg-red-50 text-red-700 border-red-200 dark:bg-red-950/30 dark:text-red-400 dark:border-red-900";
  } else if (norm === "medium") {
    colorClasses = "bg-amber-50 text-amber-800 border-amber-200 dark:bg-amber-950/30 dark:text-amber-400 dark:border-amber-900";
  } else if (norm === "low") {
    colorClasses = "bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/30 dark:text-blue-400 dark:border-blue-900";
  }
  // Voucher Status Badges
  else if (norm === "final" || norm === "approved" || norm === "resolved" || norm === "done" || norm === "matched") {
    colorClasses = "bg-emerald-50 text-emerald-800 border-emerald-200 dark:bg-emerald-950/30 dark:text-emerald-400 dark:border-emerald-900";
  } else if (norm === "draft" || norm === "open" || norm === "in_review" || norm === "queued") {
    colorClasses = "bg-sky-50 text-sky-800 border-sky-200 dark:bg-sky-950/30 dark:text-sky-400 dark:border-sky-900";
  } else if (norm === "needs_attention" || norm === "partially_matched") {
    colorClasses = "bg-amber-50 text-amber-800 border-amber-200 dark:bg-amber-950/30 dark:text-amber-400 dark:border-amber-900";
  } else if (norm === "rejected" || norm === "failed" || norm === "overdue" || norm === "books_only") {
    colorClasses = "bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-950/30 dark:text-rose-400 dark:border-rose-900";
  }

  const label = norm.replace(/_/g, " ").toUpperCase();
  const px = size === "sm" ? "px-1.5 py-0.5 text-[10px]" : "px-2 py-0.5 text-xs";

  return (
    <span
      className={`inline-flex items-center font-medium rounded border tracking-wide uppercase ${px} ${colorClasses} ${className}`}
    >
      {label}
    </span>
  );
};
