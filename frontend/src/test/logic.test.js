import { describe, expect, it } from "vitest";
import report from "./fixtures/report.json";
import { axisScale, fanRows, forecastRows, paddedDomain, priceRows } from "../services/chartData";
import { getErrorMessage } from "../services/errors";
import {
  formatDuration, fractionPct, money, moneyTick, reportCurrency, shortDate, signedPct, splitHeadline, trendWord,
} from "../services/format";
 
describe("getErrorMessage", () => {
  it("uses a plain string detail from the API", () => {
    expect(getErrorMessage({ response: { status: 401, data: { detail: "Invalid email or password" } } })).toBe(
      "Invalid email or password"
    );
  });
 
  it("flattens FastAPI validation errors into one readable line", () => {
    const err = {
      response: {
        status: 422,
        data: {
          detail: [
            { loc: ["body", "password"], msg: "String should have at least 8 characters" },
            { loc: ["body", "email"], msg: "Value error, Enter a valid email address" },
          ],
        },
      },
    };
    expect(getErrorMessage(err)).toBe(
      "password: String should have at least 8 characters \u00b7 email: Enter a valid email address"
    );
  });
 
  it("explains a network failure instead of showing 'Network Error'", () => {
    expect(getErrorMessage({ request: {}, message: "Network Error" }, "http://127.0.0.1:8000")).toContain(
      "Can't reach the server at http://127.0.0.1:8000"
    );
  });
 
  it("has sensible fallbacks", () => {
    expect(getErrorMessage({ response: { status: 500, data: {} } })).toMatch(/server hit a problem/i);
    expect(getErrorMessage({ response: { status: 429, data: {} } })).toMatch(/too many requests/i);
    expect(getErrorMessage(new Error("boom"))).toBe("boom");
  });
});
 
describe("formatters", () => {
  it("formats money, signed percentages and ratios", () => {
    expect(money(1234.5)).toBe("$1,234.50");
    expect(signedPct(2.345)).toBe("+2.3%");
    expect(signedPct(-0.09)).toBe("-0.1%");
    expect(fractionPct(0.0467)).toBe("4.7%");
  });
 
  it("formats money in the stock's own currency: dollars, rupees (lakh grouping), euros, pence", () => {
    expect(money(1234.5, "USD")).toBe("$1,234.50");
    expect(money(2470.1, "INR")).toBe("\u20b92,470.10");
    expect(money(24701000.5, "INR")).toBe("\u20b92,47,01,000.50");
    expect(money(-12.5, "EUR")).toBe("-\u20ac12.50");
    expect(money(5000, "JPY")).toBe("\u00a55,000");            // yen has no decimals
    expect(money(300.456, "GBp")).toBe("300.46p");              // London quotes in pence
    expect(money(12.5, "XYZ")).toBe("XYZ\u00a012.50");          // unknown code: shown, not guessed
    expect(money(1234.5, "USD", 0)).toBe("$1,235");
    expect(money(12.5)).toBe("$12.50");                         // no currency given: dollars
    expect(money(-0.001, "USD")).toBe("$0.00");                 // never "-$0.00"
  });
  it("labels chart axes without clutter, and reads the currency off a report", () => {
    expect(moneyTick(2500, "INR")).toBe("\u20b92,500");
    expect(moneyTick(12.5, "USD")).toBe("$12.50");
    expect(reportCurrency({ overview: { currency: "INR" } })).toBe("INR");
    expect(reportCurrency({ overview: {} })).toBe("USD");
    expect(trendWord("above SMA (bullish bias)")).toBe("Above SMA");
    expect(trendWord("below SMA (bearish bias)")).toBe("Below SMA");
  });
  it("shows a dash, never 'NaN' or 'null', for missing numbers", () => {
    for (const fn of [money, signedPct, fractionPct]) {
      expect(fn(null)).toBe("\u2014");
      expect(fn(undefined)).toBe("\u2014");
      expect(fn(NaN)).toBe("\u2014");
    }
  });
 
  it("formats durations and dates", () => {
    expect(formatDuration(7)).toBe("7s");
    expect(formatDuration(75)).toBe("1m 15s");
    expect(shortDate("2026-10-14")).toBe("Oct 14");
  });
 
  it("splits the news source off a headline", () => {
    expect(splitHeadline("Tesla stock jumps 5% on better-than-expected deliveries - CNBC")).toEqual({
      title: "Tesla stock jumps 5% on better-than-expected deliveries",
      source: "CNBC",
    });
    expect(splitHeadline("Short - one")).toEqual({ title: "Short - one", source: null });
  });
});
 
describe("chart data, built from a REAL backend report", () => {
  it("price rows keep the 19 leading null moving-average values (gaps, not zeros)", () => {
    const rows = priceRows(report.price_series);
    expect(rows).toHaveLength(report.price_series.dates.length);
    expect(rows.slice(0, 19).every((r) => r.sma === null)).toBe(true);
    expect(rows[19].sma).not.toBeNull();
  });
 
  it("forecast rows continue the line from the last real close", () => {
    const rows = forecastRows(report, 90);
    const horizon = report.forecast.path.dates.length;
    expect(rows).toHaveLength(90 + horizon);
 
    const lastClose = report.price_series.close.at(-1);
    const join = rows[89];
    expect(join.close).toBe(lastClose);
    expect(join.arima).toBe(lastClose);
    expect(join.lstm).toBe(lastClose);
    expect(join.band).toEqual([lastClose, lastClose]);
 
    const future = rows.slice(90);
    expect(future.every((r) => r.close === undefined && typeof r.arima === "number")).toBe(true);
    expect(future.every((r) => r.band[0] <= r.arima && r.arima <= r.band[1])).toBe(true);
    expect(future[0].date > join.date).toBe(true);      // dates keep moving forward
  });
 
  it("omits LSTM cleanly when it didn't run", () => {
    const noLstm = { ...report, forecast: { ...report.forecast, lstm: null } };
    expect(forecastRows(noLstm).every((r) => r.lstm === undefined)).toBe(true);
  });
 
  it("returns nothing (not a crash) for reports saved without a forecast path", () => {
    expect(forecastRows({ ...report, forecast: { ...report.forecast, path: undefined } })).toEqual([]);
  });
 
  it("fan rows start at today's price and widen, ending at the headline worst/best cases", () => {
    const mc = report.risk.monte_carlo;
    const rows = fanRows(mc);
    expect(rows).toHaveLength(mc.horizon_days + 1);
    expect(rows[0]).toMatchObject({ day: 0, p5: mc.starting_price, p95: mc.starting_price });
    expect(rows.every((r) => r.p5 <= r.median && r.median <= r.p95)).toBe(true);
    expect(rows.at(-1).p5).toBe(mc.worst_case_5pct);
    expect(rows.at(-1).p95).toBe(mc.best_case_95pct);
  });
 
  it("y-axis ticks land on round numbers, whatever the price level", () => {
    expect(axisScale([2441.3, 2588.7])).toEqual({ domain: [2400, 2600], ticks: [2400, 2450, 2500, 2550, 2600] });
    expect(axisScale([281.4, 452.9, 360]).ticks).toEqual([250, 300, 350, 400, 450, 500]);
    expect(axisScale([0.52, 0.61]).ticks).toEqual([0.5, 0.52, 0.54, 0.56, 0.58, 0.6, 0.62]);
    const { domain, ticks } = axisScale([281.4, 452.9]);
    expect(domain[0]).toBeLessThanOrEqual(281.4);              // every data point stays inside the axis
    expect(domain[1]).toBeGreaterThanOrEqual(452.9);
    expect(ticks[0]).toBe(domain[0]);
    expect(ticks.at(-1)).toBe(domain[1]);
    expect(axisScale([])).toEqual({ domain: ["auto", "auto"], ticks: undefined });
    // a price that spans ~1,950 to ~3,200 gets a tight axis, not one padded out to 1,500-3,500
    expect(axisScale([1950, 3200])).toEqual({ domain: [1750, 3500], ticks: [1750, 2000, 2250, 2500, 2750, 3000, 3250, 3500] });
  });
  it("pads the y-axis and ignores nulls", () => {
    // 5% padding, rounded outward to a round step: range 10 -> [99.5, 110.5] -> steps of 2 -> [98, 112]
    expect(paddedDomain([null, 100, 110, undefined])).toEqual([98, 112]);
    // ...and the step scales with the range: [195, 305] -> steps of 20 -> [180, 320]
    expect(paddedDomain([200, 300])).toEqual([180, 320]);
    expect(paddedDomain([null])).toEqual(["auto", "auto"]);
  });
});
 












