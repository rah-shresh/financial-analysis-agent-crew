
const dash = "\u2014";
 
export const isNum = (v) => typeof v === "number" && Number.isFinite(v);
 
// Mirrors backend/utils/currency.py, so a figure in the written summary and the same figure on the dashboard read alike.
const CURRENCY_SYMBOLS = {
  USD: "$", INR: "\u20b9", EUR: "\u20ac", GBP: "\u00a3", JPY: "\u00a5", CNY: "CN\u00a5", HKD: "HK$",
  CAD: "C$", AUD: "A$", SGD: "S$", KRW: "\u20a9", CHF: "CHF\u00a0",
};
const ZERO_DECIMAL = new Set(["JPY", "KRW"]);

/**
 * money(2470.1, "INR") -> "₹2,470.10" | money(247010, "INR", 0) -> "₹2,47,010" | money(12.5) -> "$12.50".
 * `currency` is the ISO code from report.overview.currency; London quotes in pence ("GBp"); an unknown
 * code is shown as the code itself rather than a guessed symbol.
 */
export function money(v, currency, digits) {
  if (!isNum(v)) return dash;
  let code = (currency ?? "").trim() || "USD";
  if (code === "GBX") code = "GBp";
  const d = digits ?? (ZERO_DECIMAL.has(code) ? 0 : 2);
  const number = Math.abs(v).toLocaleString(code === "INR" ? "en-IN" : "en-US", {
    minimumFractionDigits: d,
    maximumFractionDigits: d,
  });
  const sign = v < 0 && /[1-9]/.test(number) ? "-" : "";
  if (code === "GBp") return `${sign}${number}p`;
  return `${sign}${CURRENCY_SYMBOLS[code] ?? `${code}\u00a0`}${number}`;
}

/** Chart-axis label: no decimals for whole numbers ("₹2,500"), two otherwise ("$12.50"). */
export const moneyTick = (v, currency) => money(v, currency, Number.isInteger(v) || Math.abs(v) >= 100 ? 0 : 2);

/** The currency a report's prices are in. Every report the API returns carries one; USD is only a last resort. */
export const reportCurrency = (report) => report?.overview?.currency ?? "USD";
 
export const signedPct = (v, digits = 1) => (isNum(v) ? `${v > 0 ? "+" : ""}${v.toFixed(digits)}%` : dash);
 
export const pct = (v, digits = 1) => (isNum(v) ? `${v.toFixed(digits)}%` : dash);
 
/** yfinance gives ratios like ROE as fractions (0.0467 -> "4.7%"). */
export const fractionPct = (v, digits = 1) => (isNum(v) ? `${(v * 100).toFixed(digits)}%` : dash);
 
export const decimal = (v, digits = 2) => (isNum(v) ? v.toFixed(digits) : dash);
 
export const signed = (v, digits = 2) => (isNum(v) ? `${v > 0 ? "+" : ""}${v.toFixed(digits)}` : dash);
 
export function shortDate(iso) {
  const d = new Date(`${iso}T00:00:00`);
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}
 
export function longDate(iso) {
  const d = new Date(iso);
  return Number.isNaN(d.getTime())
    ? dash
    : d.toLocaleString("en-US", { year: "numeric", month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });
}
 
export function formatDuration(totalSeconds) {
  const s = Math.max(0, Math.floor(totalSeconds));
  const m = Math.floor(s / 60);
  return m > 0 ? `${m}m ${String(s % 60).padStart(2, "0")}s` : `${s}s`;
}
 
/** Headlines from Google News end with " - Source Name". */
export function splitHeadline(text) {
  const i = text.lastIndexOf(" - ");
  return i > 20 ? { title: text.slice(0, i), source: text.slice(i + 3) } : { title: text, source: null };
}
 
export function rsiZone(rsi) {
  if (!isNum(rsi)) return "";
  if (rsi >= 70) return "overbought territory";
  if (rsi <= 30) return "oversold territory";
  return "neutral range";
}
 
export const AGENT_LABELS = {
  preprocessor: "Data preprocessor",
  technical_analyst: "Technical analyst",
  sentiment: "Sentiment & news",
  forecasting: "Forecasting",
  risk: "Risk",
};
 
export const AGENT_WORKING_TEXT = {
  preprocessor: "Fetching and cleaning price data\u2026",
  technical_analyst: "Computing indicators and fundamentals\u2026",
  sentiment: "Reading recent headlines\u2026",
  forecasting: "Fitting ARIMA and training the LSTM \u2014 the slowest step\u2026",
  risk: "Running risk metrics and Monte Carlo simulation\u2026",
};
 
/** "above SMA (bullish bias)" -> "Above SMA" */
export function trendWord(trend) {
  if (!trend) return dash;
  return trend.toLowerCase().includes("above") ? "Above SMA" : "Below SMA";
}
 












