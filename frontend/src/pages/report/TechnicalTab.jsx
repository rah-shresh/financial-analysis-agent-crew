import PriceChart from "../../components/charts/PriceChart";
import { SectionHead, Stat, StatGrid, Unavailable } from "../../components/ui";
import { decimal, fractionPct, money, reportCurrency } from "../../services/format";
 
export default function TechnicalTab({ report }) {
  const t = report.technical;
  if (!t) return <Unavailable what="Technical analysis" reason={report.errors?.technical_analyst} />;
  const f = t.fundamentals;
  const currency = reportCurrency(report);
 
  return (
    <div className="space-y-8">
      <section>
        <SectionHead number="01" aside="past year, daily close">Price &amp; moving averages</SectionHead>
        <PriceChart series={report.price_series} currency={currency} />
      </section>
 
      <section>
        <SectionHead number="02">Indicators</SectionHead>
        <StatGrid>
          <Stat label="Last close" value={money(t.latest_close, currency)} />
          <Stat label="SMA 20" value={money(t.sma_20, currency)} hint="20-day simple average" />
          <Stat label="EMA 20" value={money(t.ema_20, currency)} hint="weights recent days more" />
          <Stat label="RSI 14" value={decimal(t.rsi_14, 1)} hint=">70 overbought · <30 oversold" />
        </StatGrid>
      </section>
 
      <section>
        <SectionHead number="03">Fundamentals</SectionHead>
        {f ? (
          <StatGrid columns={3}>
            <Stat label="P/E ratio" value={decimal(f.pe_ratio, 1)} hint="price vs. earnings" />
            <Stat label="Return on equity" value={fractionPct(f.roe)} />
            <Stat label="Profit margin" value={fractionPct(f.profit_margin)} />
          </StatGrid>
        ) : (
          <p className="text-sm text-ink-soft">Fundamentals weren't available for this ticker.</p>
        )}
        <p className="mt-2 text-xs text-ink-soft">A “—” means the data provider doesn't report that figure for this ticker (common for ETFs and indices).</p>
      </section>
    </div>
  );
}
 












