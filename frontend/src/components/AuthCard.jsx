import { Link } from "react-router-dom";
 
/** Shared frame for the login / register pages. */
export default function AuthCard({ title, subtitle, children, footer }) {
  return (
    <div className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-5 py-10">
      <div className="rule-double pb-3">
        <Link to="/" className="font-serif text-2xl font-semibold">Financial Analysis Crew</Link>
        <p className="mt-1 text-xs italic text-ink-soft">preprocessing · technicals · sentiment · forecast · risk</p>
      </div>
      <div className="panel mt-6 p-6">
        <h1 className="text-xl font-semibold">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-ink-soft">{subtitle}</p>}
        <div className="mt-5">{children}</div>
      </div>
      <p className="mt-4 text-center text-sm text-ink-soft">{footer}</p>
    </div>
  );
}