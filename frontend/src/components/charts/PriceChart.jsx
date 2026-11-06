import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { axisScale, priceRows } from "../../services/chartData";
import { money, moneyTick, shortDate } from "../../services/format";
import ChartTooltip from "./ChartTooltip";
import { AXIS_STROKE, CHART_MARGIN, GRID_STROKE, Y_AXIS_WIDTH, axisTick } from "./theme";
 
const NAMES = { close: "Close", sma: "SMA 20", ema: "EMA 20" };
 
/** Closing price with its 20-day simple and exponential moving averages. */
export default function PriceChart({ series, currency }) {
  const rows = priceRows(series);
  const { domain, ticks } = axisScale(rows.flatMap((r) => [r.close, r.sma, r.ema]));
 
  return (
    <div role="img" aria-label="Line chart of closing price with 20-day moving averages" className="panel p-3">
      <ResponsiveContainer width="100%" height={320}>
        <LineChart data={rows} margin={CHART_MARGIN}>
          <CartesianGrid stroke={GRID_STROKE} strokeDasharray="2 4" vertical={false} />
          <XAxis dataKey="date" tickFormatter={shortDate} minTickGap={48} tick={axisTick} stroke={AXIS_STROKE} />
          <YAxis domain={domain} ticks={ticks} tick={axisTick} stroke={AXIS_STROKE} width={Y_AXIS_WIDTH} tickFormatter={(v) => moneyTick(v, currency)} />
          <Tooltip content={<ChartTooltip labelFormatter={shortDate} names={NAMES} format={(v) => money(v, currency)} />} />
          <Legend iconType="plainline" wrapperStyle={{ fontSize: 12 }} />
          <Line dataKey="close" name="Close" stroke="#26241D" strokeWidth={1.6} dot={false} isAnimationActive={false} />
          <Line dataKey="sma" name="SMA 20" stroke="#9C3B2C" strokeWidth={1.2} dot={false} isAnimationActive={false} />
          <Line dataKey="ema" name="EMA 20" stroke="#2F5D50" strokeWidth={1.2} dot={false} isAnimationActive={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
 