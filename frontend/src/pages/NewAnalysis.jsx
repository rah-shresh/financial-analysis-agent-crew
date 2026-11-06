import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ErrorNote, SectionHead } from "../components/ui";
import { API_BASE, listReports, startRun } from "../services/api";
import { getErrorMessage } from "../services/errors";
import { longDate, signedPct } from "../services/format";
 
const TICKER_RE = /^[A-Za-z0-9.\-^=]{1,15}$/;
const EXAMPLES = ["TSLA", "AAPL", "MSFT", "NVDA", "RELIANCE.NS"];
 
export default function NewAnalysis() {
  const navigate = useNavigate();
  const [ticker, setTicker] = useState("");
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);
  const [recent, setRecent] = useState([]);
 
  useEffect(() => {
    let cancelled = false;
    listReports({ limit: 5 })
      .then((rows) => !cancelled && setRecent(rows))
      .catch(() => {}); // the list is a nicety; the form works without it
    return () => { cancelled = true; };
  }, []);
 
  async function onSubmit(e) {
    e.preventDefault();
    const value = ticker.trim();
    if (!TICKER_RE.test(value)) {
      setError("Enter a ticker like TSLA, BRK-B or RELIANCE.NS (letters, digits and . - ^ = only).");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const run = await startRun(value);
      navigate(`/analysis/${run.id}`);
    } catch (err) {
      setError(getErrorMessage(err, API_BASE));
      setBusy(false);
    }
  }
 
  return (
    <div>
      <SectionHead number="01">New analysis</SectionHead>
      <p className="mb-5 max-w-xl text-sm text-ink-soft">
        Five agents clean the data, read the technicals, score the news, forecast 30 days ahead and measure risk.
        It takes about a minute or two.
      </p>
 
      <form onSubmit={onSubmit} className="flex flex-wrap items-end gap-3" noValidate>
        <div className="min-w-[14rem] flex-1">
          <label htmlFor="ticker" className="label">Ticker symbol</label>
          <input id="ticker" className="field mt-1 uppercase" placeholder="TSLA" autoComplete="off" spellCheck="false"
                 value={ticker} onChange={(e) => setTicker(e.target.value)} />
        </div>
        <button type="submit" className="btn-primary" disabled={busy || !ticker.trim()}>
          {busy ? "Starting…" : "Run analysis"}
        </button>
      </form>
 
      <div className="mt-3 flex flex-wrap items-center gap-2 text-sm">
        <span className="text-ink-soft">Try:</span>
        {EXAMPLES.map((t) => (
          <button key={t} type="button" onClick={() => setTicker(t)}
                  className="border border-rule px-2 py-0.5 font-mono text-xs hover:border-ink">
            {t}
          </button>
        ))}
      </div>
 
      <p className="mt-2 text-xs text-ink-soft">Indian stocks need a suffix: .NS for NSE or .BO for BSE (for example TCS.NS).</p>
      {error && <div className="mt-4 max-w-xl"><ErrorNote>{error}</ErrorNote></div>}
 
      {recent.length > 0 && (
        <section className="mt-12">
          <SectionHead number="02" aside={<Link to="/history" className="underline">All history</Link>}>
            Recent analyses
          </SectionHead>
          <ul className="divide-y divide-rule-soft border-y border-rule-soft">
            {recent.map((r) => (
              <li key={r.id}>
                <Link to={`/reports/${r.id}`} className="flex items-center gap-4 px-1 py-2.5 hover:bg-card">
                  <span className="num min-w-[9rem] shrink-0 font-medium">{r.ticker}</span>
                  <span className="flex-1 text-xs text-ink-soft">{longDate(r.created_at)}</span>
                  <span className="num text-sm">{signedPct(r.overview?.forecast_arima_pct)}</span>
                </Link>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
 












