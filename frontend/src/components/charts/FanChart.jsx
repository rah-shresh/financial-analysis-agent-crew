import {
  Area, CartesianGrid, ComposedChart, Legend, Line, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { axisScale, fanRows } from "../../services/chartData";
import { money, moneyTick } from "../../services/format";
import ChartTooltip from "./ChartTooltip";
import { AXIS_STROKE, CHART_MARGIN, GRID_STROKE, Y_AXIS_WIDTH, axisTick } from "./theme";
 
const NAMES = { p95: "95th percentile", median: "Median", p5: "5th percentile" };
 
/**
 * Monte Carlo "fan": thousands of simulated price paths, summarised as the
 * 5th / median / 95th percentile for each future day. The shaded band is
 * where 90% of the simulated outcomes landed.
 */
export default function FanChart({ monteCarlo, currency }) {
  const rows = fanRows(monteCarlo);
  const { domain, ticks } = axisScale(rows.flatMap((r) => [r.p5, r.p95]));
 
  return (
    <div role="img" aria-label="Monte Carlo fan chart: range of simulated future prices" className="panel p-3">
      <ResponsiveContainer width="100%" height={320}>
        <ComposedChart data={rows} margin={CHART_MARGIN}>
          <CartesianGrid stroke={GRID_STROKE} strokeDasharray="2 4" vertical={false} />
          <XAxis dataKey="day" tickFormatter={(d) => `D${d}`} minTickGap={24} tick={axisTick} stroke={AXIS_STROKE} />
          <YAxis domain={domain} ticks={ticks} tick={axisTick} stroke={AXIS_STROKE} width={Y_AXIS_WIDTH} tickFormatter={(v) => moneyTick(v, currency)} />
          <Tooltip content={<ChartTooltip labelFormatter={(d) => `Day ${d}`} names={NAMES} format={(v) => money(v, currency)} />} />
          <Legend iconType="plainline" wrapperStyle={{ fontSize: 12 }} />
          <ReferenceLine y={monteCarlo.starting_price} stroke="#5E5B4D" strokeDasharray="3 3" />
          <Area dataKey="band" name="90% of simulations" stroke="none" fill="#1B2A4A" fillOpacity={0.12} isAnimationActive={false} legendType="square" />
          <Line dataKey="p95" name="95th percentile" stroke="#2F5D50" strokeWidth={1.2} strokeDasharray="4 3" dot={false} isAnimationActive={false} />
          <Line dataKey="median" name="Median" stroke="#26241D" strokeWidth={1.8} dot={false} isAnimationActive={false} />
          <Line dataKey="p5" name="5th percentile" stroke="#9C3B2C" strokeWidth={1.2} strokeDasharray="4 3" dot={false} isAnimationActive={false} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
 