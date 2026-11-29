/**
 * Standard Indian numbering system (Lakhs and Crores) and date utilities.
 */

export function formatIndianCurrency(paise: number | null | undefined): string {
  if (paise === null || paise === undefined || isNaN(paise)) return "₹0.00";
  const rupees = paise / 100.0;
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(rupees);
}

export function formatCompactRupees(paise: number): string {
  const rupees = paise / 100.0;
  if (rupees >= 10000000) {
    return `₹${(rupees / 10000000).toFixed(2)} Cr`;
  }
  if (rupees >= 100000) {
    return `₹${(rupees / 100000).toFixed(2)} L`;
  }
  if (rupees >= 1000) {
    return `₹${(rupees / 1000).toFixed(1)}k`;
  }
  return formatIndianCurrency(paise);
}

export function formatDate(isoStr: string | null | undefined): string {
  if (!isoStr) return "-";
  try {
    const d = new Date(isoStr);
    return new Intl.DateTimeFormat("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    }).format(d);
  } catch {
    return isoStr;
  }
}

export function formatDateTime(isoStr: string | null | undefined): string {
  if (!isoStr) return "-";
  try {
    const d = new Date(isoStr);
    return new Intl.DateTimeFormat("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      hour12: true,
    }).format(d);
  } catch {
    return isoStr;
  }
}
