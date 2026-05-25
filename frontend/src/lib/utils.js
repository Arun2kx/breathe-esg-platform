export function cn(...classes) {
  return classes.filter(Boolean).join(" ");
}

export function formatDate(dateStr) {
  if (!dateStr) return "—";
  return new Date(dateStr).toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

export function formatNumber(val, decimals = 2) {
  if (val === null || val === undefined) return "—";
  return Number(val).toLocaleString("en-IN", {
    minimumFractionDigits: 0,
    maximumFractionDigits: decimals,
  });
}

export const SOURCE_LABELS = {
  sap: "SAP",
  utility: "Utility",
  travel: "Travel",
};

export const SCOPE_LABELS = {
  1: "Scope 1",
  2: "Scope 2",
  3: "Scope 3",
};
