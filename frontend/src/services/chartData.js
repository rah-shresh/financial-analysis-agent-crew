/** Pure functions: backend report JSON -> arrays Recharts can plot. No React in here, so they're easy to test. */
import { isNum } from "./format";
 
/**
 * Smallest "round" step (1, 2 or 5 times a power of ten -- or 2.5 once steps are 25 or more, so
 * "₹1,750 / ₹2,000 / ₹2,250" is possible) that is at least `rawStep`.
 */
function niceStep(rawStep) {
  const pow = 10 ** Math.floor(Math.log10(rawStep));
  const f = rawStep / pow;
  return (f <= 1 ? 1 : f <= 2 ? 2 : f <= 2.5 && pow >= 10 ? 2.5 : f <= 5 ? 5 : 10) * pow;
}

/**
 * Y-axis for a price chart: the data's range plus a little padding (so lines don't hug the edges),
 * rounded outward to round numbers, with a tick at every step -- "₹2,400 / ₹2,450 / ₹2,500"
 * instead of whatever odd values the padded min and max happen to be.
 */
export function axisScale(values, pad = 0.05) {
  const nums = values.filter(isNum);
  if (!nums.length) return { domain: ["auto", "auto"], ticks: undefined };
  const lo = Math.min(...nums);
  const hi = Math.max(...nums);
  const margin = (hi - lo || Math.abs(hi) || 1) * pad;
  const step = niceStep((hi - lo + 2 * margin) / 6);
  const start = Math.floor((lo - margin) / step) * step;
  const end = Math.ceil((hi + margin) / step) * step;
  const ticks = [];
  for (let t = start; t <= end + step / 2; t += step) ticks.push(Number(t.toPrecision(12)));
  return { domain: [Number(start.toPrecision(12)), Number(end.toPrecision(12))], ticks };
}

/** Just the [min, max] of axisScale. */
export const paddedDomain = (values, pad) => axisScale(values, pad).domain;
 
export function priceRows(series) {
  if (!series?.dates) return [];
  return series.dates.map((date, i) => ({
    date,
    close: series.close[i],
    sma: series.sma_20[i], // null for the first 19 days: Recharts leaves a gap, which is honest
    ema: series.ema_20[i],
  }));
}
 
/**
 * History (last `historyDays`) + the forecast on one time axis.
 * The last real day is also seeded into the forecast series so the lines
 * visibly continue from where the price actually ended.
 */
export function forecastRows(report, historyDays = 90) {
  const series = report?.price_series;
  const path = report?.forecast?.path;
  if (!series?.dates || !path?.dates) return [];
 
  const lstmPath = report.forecast.lstm?.path;
  const n = series.dates.length;
  const rows = [];
  for (let i = Math.max(0, n - historyDays); i < n; i++) rows.push({ date: series.dates[i], close: series.close[i] });
 
  const lastClose = series.close[n - 1];
  const last = rows[rows.length - 1];
  last.arima = lastClose;
  last.band = [lastClose, lastClose];
  if (lstmPath) last.lstm = lastClose;
 
  path.dates.forEach((date, i) => {
    const row = { date, arima: path.arima[i], band: [path.ci_lower[i], path.ci_upper[i]] };
    if (lstmPath) row.lstm = lstmPath[i];
    rows.push(row);
  });
  return rows;
}
 
/** Monte Carlo: day 0 is today's price, then the 5th / median / 95th percentile of every simulated day. */
export function fanRows(monteCarlo) {
  const fan = monteCarlo?.fan;
  if (!fan) return [];
  const start = monteCarlo.starting_price;
  const rows = [{ day: 0, p5: start, median: start, p95: start, band: [start, start] }];
  fan.median.forEach((median, i) =>
    rows.push({ day: i + 1, p5: fan.p5[i], median, p95: fan.p95[i], band: [fan.p5[i], fan.p95[i]] })
  );
  return rows;
}
 












