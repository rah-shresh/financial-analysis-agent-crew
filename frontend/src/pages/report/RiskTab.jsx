import FanChart from "../../components/charts/FanChart";
import { SectionHead, Stat, StatGrid, Unavailable } from "../../components/ui";
import { decimal, money, pct, reportCurrency } from "../../services/format";
 
export default function RiskTab({ report }) {
  const r = report.risk;
  if (!r) return <Unavailable what="Risk analysis" reason={report.errors?.risk} />;
  const var95 = r.value_at_risk_95;
  const mc = r.monte_carlo;
  const cur = reportCurrency(report);
  const sharpeTone = r.sharpe_ratio >= 1 ? "gain" : r.sharpe_ratio < 0 ? "stamp" : "default";
 
  return (
    <div className="space-y-8">
      <section>
        <SectionHead number="01">Risk metrics</SectionHead>
        <StatGrid>
          <Stat label="Sharpe ratio" value={decimal(r.sharpe_ratio)} tone={sharpeTone} hint="return per unit of risk" />
          <Stat label="Volatility (yearly)" value={pct(r.annualized_volatility_pct)} hint={`${r.risk_label} risk`} />
          <Stat label="1-day VaR (95%)" value={pct(var95.daily_pct)} hint={`≈ ${money(Math.abs(var95.daily_dollar_per_share), cur)} per share`} />
          <Stat label="Risk level" value={r.risk_label} />
        </StatGrid>
        <p className="mt-3 max-w-3xl text-sm text-ink-soft">{var95.interpretation}</p>
      </section>
 
      {mc?.fan && (
        <section>
          <SectionHead number="02" aside={`${mc.simulations_run.toLocaleString("en-US")} simulations`}>
            Monte Carlo: where the price could go in {mc.horizon_days} days
          </SectionHead>
          <FanChart monteCarlo={mc} currency={cur} />
          <div className="mt-4">
            <StatGrid>
              <Stat label="Chance of a lower price" value={pct(mc.probability_of_loss_pct, 0)} />
              <Stat label="Median outcome" value={money(mc.median_final_price, cur)} />
              <Stat label="Bad case (5th pct)" value={money(mc.worst_case_5pct, cur)} tone="stamp" />
              <Stat label="Good case (95th pct)" value={money(mc.best_case_95pct, cur)} tone="gain" />
            </StatGrid>
          </div>
          <p className="mt-2 text-xs text-ink-soft">
            Simulated from this stock's own past average move and volatility. It shows the spread of outcomes the
            history implies, not a prediction.
          </p>
        </section>
      )}
    </div>
  );
}
 












