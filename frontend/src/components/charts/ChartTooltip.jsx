import { isNum, money } from "../../services/format";
 
/** Tooltip styled like the rest of the ledger. Ignores the invisible "band" series. */
export default function ChartTooltip({ active, payload, label, labelFormatter, names = {}, format = money }) {
  if (!active || !payload?.length) return null;
  const items = payload.filter((p) => p.dataKey !== "band" && isNum(p.value));
  if (!items.length) return null;
  return (
    <div className="panel px-3 py-2 text-xs">
      <div className="mb-1 font-mono text-ink-soft">{labelFormatter ? labelFormatter(label) : label}</div>
      {items.map((p) => (
        <div key={p.dataKey} className="flex justify-between gap-5">
          <span style={{ color: p.color }}>{names[p.dataKey] ?? p.name}</span>
          <span className="num">{format(p.value)}</span>
        </div>
      ))}
    </div>
  );
}
 