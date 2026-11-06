import { Pill, SectionHead } from "../../components/ui";
import { AGENT_LABELS, decimal, money, pct, rsiZone, signed, signedPct } from "../../services/format";
 
const tone = (v) => (v > 0 ? "text-gain" : v < 0 ? "text-stamp" : "");
 
function Row({ label, children }) {
  return (
    <div className="flex items-baseline justify-between gap-6 border-b border-rule-soft py-2.5">
      <dt className="text-sm text-ink-soft">{label}</dt>
      <dd className="num text-right">{children}</dd>
    </div>
  );
}
 
export default function OverviewTab({ report }) {
  const o = report.overview;
  const failed = Object.entries(report.errors ?? {});
 
  return (
    <div className="space-y-8">
      <section>
        <SectionHead number="01">At a glance</SectionHead>
        <dl className="max-w-2xl border-t border-ink">
          <Row label="Last close">{money(o.latest_close, o.currency)}</Row>
          <Row label="Trend"><span className="font-sans">{o.trend ?? "—"}</span></Row>
          <Row label="RSI (14)">
            {o.rsi_14 != null ? <>{decimal(o.rsi_14, 1)} <span className="font-sans text-xs text-ink-soft">· {rsiZone(o.rsi_14)}</span></> : "—"}
          </Row>
          <Row label="News sentiment">
            {o.sentiment_label ? <><span className="font-sans">{o.sentiment_label}</span> ({signed(o.sentiment_score, 2)})</> : "—"}
          </Row>
          <Row label="30-day outlook · ARIMA">
            <span className={tone(o.forecast_arima_pct)}>{signedPct(o.forecast_arima_pct)}</span>
          </Row>
          {o.forecast_lstm_pct != null && (
            <Row label="30-day outlook · LSTM">
              <span className={tone(o.forecast_lstm_pct)}>{signedPct(o.forecast_lstm_pct)}</span>{" "}
              {/* null = one model sees almost no move, which is neither agreement nor disagreement */}
              <Pill tone={o.forecast_models_agree == null ? "default" : o.forecast_models_agree ? "gain" : "stamp"}>
                {o.forecast_models_agree == null ? "one model sees no move" : o.forecast_models_agree ? "models agree" : "models disagree"}
              </Pill>
            </Row>
          )}
          <Row label="Risk level">
            {o.risk_label ? <><span className="font-sans">{o.risk_label}</span> · Sharpe {decimal(o.sharpe_ratio)}</> : "—"}
          </Row>
          <Row label="Worst typical day (95% VaR)">{pct(o.var_95_daily_pct)}</Row>
          <Row label="Chance of a lower price in 30 days">{pct(o.probability_of_loss_30d_pct, 0)}</Row>
        </dl>
      </section>
 
      <section>
        <SectionHead number="02">Analyst note</SectionHead>
        <p className="panel max-w-3xl border-l-4 border-l-stamp px-5 py-4 font-serif leading-relaxed">{report.summary}</p>
      </section>
 
      {failed.length > 0 && (
        <section>
          <SectionHead number="03">Not available in this report</SectionHead>
          <ul className="max-w-3xl space-y-1 text-sm">
            {failed.map(([agent, message]) => (
              <li key={agent}>
                <span className="font-medium">{AGENT_LABELS[agent] ?? agent}:</span>{" "}
                <span className="text-ink-soft">{message}</span>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
 












