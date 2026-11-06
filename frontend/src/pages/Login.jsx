import { useState } from "react";
import { Link } from "react-router-dom";
import AuthCard from "../components/AuthCard";
import { ErrorNote } from "../components/ui";
import { API_BASE, login } from "../services/api";
import { getErrorMessage } from "../services/errors";
import { useAuthStore } from "../store/authStore";
 
export default function Login() {
  const setSession = useAuthStore((s) => s.setSession);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);
 
  async function onSubmit(e) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      setSession(await login({ email, password })); // GuestRoute then redirects us onward
    } catch (err) {
      setError(getErrorMessage(err, API_BASE));
      setBusy(false);
    }
  }
 
  return (
    <AuthCard
      title="Log in"
      subtitle="Welcome back."
      footer={<>No account yet? <Link to="/register" className="font-medium text-stamp underline">Register</Link></>}
    >
      <form onSubmit={onSubmit} className="space-y-4" noValidate>
        <div>
          <label htmlFor="email" className="label">Email</label>
          <input id="email" type="email" autoComplete="email" required className="field mt-1"
                 value={email} onChange={(e) => setEmail(e.target.value)} />
        </div>
        <div>
          <label htmlFor="password" className="label">Password</label>
          <input id="password" type="password" autoComplete="current-password" required className="field mt-1"
                 value={password} onChange={(e) => setPassword(e.target.value)} />
        </div>
        {error && <ErrorNote>{error}</ErrorNote>}
        <button type="submit" className="btn-primary w-full" disabled={busy || !email || !password}>
          {busy ? "Logging in…" : "Log in"}
        </button>
      </form>
    </AuthCard>
  );
}
 