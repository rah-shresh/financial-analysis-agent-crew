import { signed } from "../services/format";
 
/** A ruled scale from -1 (negative) to +1 (positive) with a marker at the score. */
export default function SentimentGauge({ score, label }) {
  const clamped = Math.max(-1, Math.min(1, score));
  const left = ((clamped + 1) / 2) * 100;
  const tone = label === "positive" ? "text-gain" : label === "negative" ? "text-stamp" : "text-ink";
 
  return (
    <div>
      <div className="flex items-baseline gap-3">
        <span className={`num text-3xl ${tone}`}>{signed(score, 2)}</span>
        <span className="text-sm uppercase tracking-wider text-ink-soft">{label}</span>
      </div>
      <div
        className="relative mt-4 h-2 border border-ink bg-card"
        role="meter"
        aria-valuemin={-1}
        aria-valuemax={1}
        aria-valuenow={clamped}
        aria-label="Sentiment score from -1 (negative) to +1 (positive)"
      >
        <div className="absolute inset-y-0 left-1/2 w-px bg-ink" />
        <div className="absolute -top-1.5 h-5 w-1 -translate-x-1/2 bg-stamp" style={{ left: `${left}%` }} />
      </div>
      <div className="mt-1 flex justify-between font-mono text-[11px] text-ink-soft">
        <span>-1 negative</span>
        <span>0</span>
        <span>positive +1</span>
      </div>
    </div>
  );
}
 