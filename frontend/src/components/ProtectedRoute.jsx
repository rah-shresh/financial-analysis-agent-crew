import { Navigate, useLocation } from "react-router-dom";
import { useAuthStore } from "../store/authStore";
 
/** Wraps pages that need a login. Not logged in -> /login, and back here afterwards. */
export function ProtectedRoute({ children }) {
  const token = useAuthStore((s) => s.token);
  const location = useLocation();
  if (!token) return <Navigate to="/login" replace state={{ from: location }} />;
  return children;
}
 
/** Login/register pages: if you're already logged in, go where you were headed (or home). */
export function GuestRoute({ children }) {
  const token = useAuthStore((s) => s.token);
  const location = useLocation();
  if (token) return <Navigate to={location.state?.from?.pathname || "/"} replace />;
  return children;
}