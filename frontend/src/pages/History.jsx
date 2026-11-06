import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ErrorNote, Loading, Pill, SectionHead } from "../components/ui";
import { API_BASE, listReports } from "../services/api";
import { getErrorMessage } from "../services/errors";
import { longDate, signedPct, trendWord } from "../services/format";
 
const PAGE = 20;
const RISK_TONE = { low: "gain", moderate: "default", high: "stamp" };
 
export default function History() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [hasMore, setHasMore] = useState(false);
  const [error, setError] = useState(null);
 
  const load = useCallback(async (skip) => {
    setLoading(true);
    setError(null);
    try {
      const page = await listReports({ limit: PAGE, skip });
      setRows((prev) => (skip === 0 ? page : [...prev, ...page]));
      setHasMore(page.length === PAGE);
    } catch (err) {
      setError(getErrorMessage(err, API_BASE));
    } finally {
      setLoading(false);
    }
  }, []);
 
  useEffect(() => { load(0); }, [load]);
 
  return (
    <div>
      <SectionHead number="01">History</SectionHead>
 
      {error && <ErrorNote>{error}</ErrorNote>}
      {loading && rows.length === 0 && <Loading />}
 
      {!loading && !error && rows.length === 0 && (
        <div className="panel px-5 py-8 text-center">
          <p className="font-medium">No analyses yet.</p>
          <Link to="/" className="btn-primary mt-4 inline-block">Run your first analysis</Link>
        </div>
      )}
 
      {rows.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[34rem] text-left text-sm">
            <thead>
              <tr className="border-b border-ink">
                {["Ticker", "Date", "Trend", "30-day ARIMA", "Risk"].map((h) => (
                  <th key={h} scope="col" className="label py-2 pr-4 font-normal">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => {
                const o = r.overview ?? {};
                return (
                  <tr key={r.id} className="border-b border-rule-soft hover:bg-card">
                    <td className="py-2.5 pr-4">
                      <Link to={`/reports/${r.id}`} className="num font-medium underline decoration-rule underline-offset-2">
                        {r.ticker}
                      </Link>
                    </td>
                    <td className="py-2.5 pr-4 text-ink-soft">{longDate(r.created_at)}</td>
                    <td className="py-2.5 pr-4">{trendWord(o.trend)}</td>
                    <td className="num py-2.5 pr-4">{signedPct(o.forecast_arima_pct)}</td>
                    <td className="py-2.5">{o.risk_label ? <Pill tone={RISK_TONE[o.risk_label]}>{o.risk_label}</Pill> : "—"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
 
      {hasMore && (
        <button type="button" className="btn-ghost mt-5" disabled={loading} onClick={() => load(rows.length)}>
          {loading ? "Loading…" : "Load more"}
        </button>
      )}
    </div>
  );
}
 












