import { useState } from "react";
import { Link } from "react-router-dom";
import AuthCard from "../components/AuthCard";
import { ErrorNote } from "../components/ui";
import { API_BASE, register } from "../services/api";
import { getErrorMessage } from "../services/errors";
import { useAuthStore } from "../store/authStore";
 
export default function Register() {
  const setSession = useAuthStore((s) => s.setSession);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);
 
  async function onSubmit(e) {
    e.preventDefault();
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      setSession(await register({ name, email, password }));
    } catch (err) {
      setError(getErrorMessage(err, API_BASE));
      setBusy(false);
    }
  }
 
  return (
    <AuthCard
      title="Create an account"
      subtitle="Your analyses are saved to your history."
      footer={<>Already registered? <Link to="/login" className="font-medium text-stamp underline">Log in</Link></>}
    >
      <form onSubmit={onSubmit} className="space-y-4" noValidate>
        <div>
          <label htmlFor="name" className="label">Name</label>
          <input id="name" type="text" autoComplete="name" required className="field mt-1"
                 value={name} onChange={(e) => setName(e.target.value)} />
        </div>
        <div>
          <label htmlFor="email" className="label">Email</label>
          <input id="email" type="email" autoComplete="email" required className="field mt-1"
                 value={email} onChange={(e) => setEmail(e.target.value)} />
        </div>
        <div>
          <label htmlFor="password" className="label">Password</label>
          <input id="password" type="password" autoComplete="new-password" required className="field mt-1"
                 value={password} onChange={(e) => setPassword(e.target.value)} aria-describedby="pw-hint" />
          <p id="pw-hint" className="mt-1 text-xs text-ink-soft">At least 8 characters.</p>
        </div>
        {error && <ErrorNote>{error}</ErrorNote>}
        <button type="submit" className="btn-primary w-full" disabled={busy || !name || !email || !password}>
          {busy ? "Creating account…" : "Create account"}
        </button>
      </form>
    </AuthCard>
  );
}
 












