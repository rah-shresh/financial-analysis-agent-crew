import {
  Area, CartesianGrid, ComposedChart, Legend, Line, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { axisScale, forecastRows } from "../../services/chartData";
import { money, moneyTick, reportCurrency, shortDate } from "../../services/format";
import ChartTooltip from "./ChartTooltip";
import { AXIS_STROKE, CHART_MARGIN, GRID_STROKE, Y_AXIS_WIDTH, axisTick } from "./theme";
 
const NAMES = { close: "Actual", arima: "ARIMA", lstm: "LSTM" };
 
/** Last 90 days of price, then the 30-day forecast: ARIMA (with its 95% range, shaded) and LSTM. */
export default function ForecastChart({ report }) {
  const rows = forecastRows(report);
  const currency = reportCurrency(report);
  const hasLstm = Boolean(report.forecast?.lstm?.path);
  const today = report.price_series.dates[report.price_series.dates.length - 1];
  const { domain, ticks } = axisScale(rows.flatMap((r) => [r.close, r.arima, r.lstm, ...(r.band ?? [])]));
 
  return (
    <div role="img" aria-label="Chart of recent price and the 30-day ARIMA and LSTM forecasts" className="panel p-3">
      <ResponsiveContainer width="100%" height={340}>
        <ComposedChart data={rows} margin={CHART_MARGIN}>
          <CartesianGrid stroke={GRID_STROKE} strokeDasharray="2 4" vertical={false} />
          <XAxis dataKey="date" tickFormatter={shortDate} minTickGap={48} tick={axisTick} stroke={AXIS_STROKE} />
          <YAxis domain={domain} ticks={ticks} tick={axisTick} stroke={AXIS_STROKE} width={Y_AXIS_WIDTH} tickFormatter={(v) => moneyTick(v, currency)} />
          <Tooltip content={<ChartTooltip labelFormatter={shortDate} names={NAMES} format={(v) => money(v, currency)} />} />
          <Legend iconType="plainline" wrapperStyle={{ fontSize: 12 }} />
          <ReferenceLine x={today} stroke="#5E5B4D" strokeDasharray="3 3" label={{ value: "today", fontSize: 11, fill: "#5E5B4D", position: "insideTopLeft" }} />
          <Area dataKey="band" name="ARIMA 95% range" stroke="none" fill="#9C3B2C" fillOpacity={0.13} isAnimationActive={false} legendType="square" />
          <Line dataKey="close" name="Actual" stroke="#26241D" strokeWidth={1.6} dot={false} isAnimationActive={false} />
          <Line dataKey="arima" name="ARIMA" stroke="#9C3B2C" strokeWidth={1.8} strokeDasharray="5 4" dot={false} isAnimationActive={false} />
          {hasLstm && (
            <Line dataKey="lstm" name="LSTM" stroke="#1B2A4A" strokeWidth={1.8} strokeDasharray="2 3" dot={false} isAnimationActive={false} />
          )}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
 












