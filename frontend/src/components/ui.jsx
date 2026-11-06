/** Small shared building blocks. */
 
export function SectionHead({ number, children, aside }) {
  return (
    <div className="mb-3 flex items-baseline justify-between gap-3 border-b border-rule pb-1.5">
      <h2 className="flex items-baseline gap-2.5 text-lg font-semibold">
        {number && <span className="num text-xs font-normal text-ink-soft">{number}</span>}
        {children}
      </h2>
      {aside && <span className="text-xs text-ink-soft">{aside}</span>}
    </div>
  );
}
 
const TONE = { gain: "text-gain", stamp: "text-stamp", default: "text-ink" };
 
/** A ledger figure: small caption over a big mono number. */
export function Stat({ label, value, hint, tone = "default" }) {
  return (
    <div className="border-r border-rule-soft px-4 py-3 last:border-r-0">
      <div className="label">{label}</div>
      <div className={`num mt-1 text-xl ${TONE[tone]}`}>{value}</div>
      {hint && <div className="mt-0.5 text-xs text-ink-soft">{hint}</div>}
    </div>
  );
}
 
export function StatGrid({ children, columns = 4 }) {
  const cols = { 2: "sm:grid-cols-2", 3: "sm:grid-cols-3", 4: "sm:grid-cols-4" }[columns];
  return <div className={`grid grid-cols-2 border-y border-ink ${cols}`}>{children}</div>;
}
 
export function Pill({ tone = "default", children }) {
  const styles = {
    default: "border-rule text-ink-soft",
    gain: "border-gain text-gain",
    stamp: "border-stamp text-stamp",
  };
  return <span className={`inline-block border px-2 py-0.5 font-mono text-[11px] ${styles[tone]}`}>{children}</span>;
}
 
/** Shown when a report section couldn't be produced -- says why, never fakes data. */
export function Unavailable({ what, reason }) {
  return (
    <div className="panel border-l-4 border-l-stamp px-4 py-3 text-sm" role="note">
      <p className="font-medium">{what} isn't available for this run.</p>
      {reason && <p className="mt-1 text-ink-soft">{reason}</p>}
    </div>
  );
}
 
export function ErrorNote({ children }) {
  return (
    <div className="border border-stamp bg-card px-4 py-3 text-sm text-stamp" role="alert">
      {children}
    </div>
  );
}
 
export function Loading({ children = "Loading…" }) {
  return (
    <p className="pulse-stamp py-10 text-center text-sm text-ink-soft" role="status">
      {children}
    </p>
  );
}
 












