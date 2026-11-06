import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import { useAuthStore } from "../store/authStore";
 
const navClass = ({ isActive }) =>
  `pb-0.5 border-b-2 ${isActive ? "border-stamp text-ink" : "border-transparent text-ink-soft hover:text-ink"}`;
 
export default function AppShell() {
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  // A report page already ends with its own, fuller disclaimer; don't print a second one under it.
  const onReport = useLocation().pathname.startsWith("/reports/");
 
  return (
    <div className="mx-auto max-w-5xl px-5 pb-16">
      <header className="rule-double flex flex-wrap items-end justify-between gap-4 pb-4 pt-8">
        <div>
          <Link to="/" className="font-serif text-2xl font-semibold leading-none">
            Financial Analysis Crew
          </Link>
          <p className="mt-1.5 text-xs italic text-ink-soft">
            preprocessing · technicals · sentiment · forecast · risk
          </p>
        </div>
        <nav className="flex items-center gap-5 text-sm" aria-label="Main">
          <NavLink to="/" end className={navClass}>New analysis</NavLink>
          <NavLink to="/history" className={navClass}>History</NavLink>
          {user && <span className="hidden text-ink-soft sm:inline">{user.name}</span>}
          <button type="button" className="btn-ghost" onClick={logout}>Log out</button>
        </nav>
      </header>
 
      <main className="pt-8">
        <Outlet />
      </main>
 
      {!onReport && (
        <footer className="mt-14 border-t border-rule pt-3 text-xs italic text-ink-soft">
          For educational and informational purposes only — not investment advice.
        </footer>
      )}
    </div>
  );
}
 












