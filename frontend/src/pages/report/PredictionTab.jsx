import ForecastChart from "../../components/charts/ForecastChart";
import { SectionHead, Stat, StatGrid, Unavailable } from "../../components/ui";
import { money, reportCurrency, signedPct } from "../../services/format";
 
const tone = (v) => (v > 0 ? "gain" : v < 0 ? "stamp" : "default");
 
export default function PredictionTab({ report }) {
  const f = report.forecast;
  if (!f) return <Unavailable what="The forecast" reason={report.errors?.forecasting} />;
  const ci = f.confidence_interval_95;
  const lstm = f.lstm;
  const cur = reportCurrency(report);
 
  return (
    <div className="space-y-8">
      <section>
        <SectionHead number="01" aside={`next ${f.forecast_days} trading days`}>Forecast</SectionHead>
        {f.path ? (
          <ForecastChart report={report} />
        ) : (
          <p className="text-sm text-ink-soft">The day-by-day forecast path isn't stored for this report.</p>
        )}
        <p className="mt-2 text-xs text-ink-soft">
          The shaded band is ARIMA's 95% range — wide on purpose: it's the honest uncertainty, not a flaw. Dates are
          weekdays; exchange holidays aren't modeled.
        </p>
      </section>
 
      <section>
        <SectionHead number="02">The two models</SectionHead>
        <StatGrid columns={lstm ? 4 : 2}>
          <Stat label="ARIMA · end price" value={money(f.forecast_final_price, cur)} hint={`from ${money(f.last_actual_price, cur)}`} />
          <Stat label="ARIMA · change" value={signedPct(f.forecast_change_pct)} tone={tone(f.forecast_change_pct)}
                hint={`95% range ${money(ci.lower, cur)} – ${money(ci.upper, cur)}`} />
          {lstm && <Stat label="LSTM · end price" value={money(lstm.forecast_final_price, cur)} />}
          {lstm && <Stat label="LSTM · change" value={signedPct(lstm.forecast_change_pct)} tone={tone(lstm.forecast_change_pct)} />}
        </StatGrid>
        <p className="mt-3 max-w-3xl text-sm text-ink-soft">
          ARIMA is a classical statistical model; the LSTM is a small neural network trained on about a year of
          prices (plus the news sentiment score). They are independent opinions — when they disagree, that's
          information: the outlook is genuinely uncertain.
        </p>
      </section>
    </div>
  );
}
 












