import { Suspense, lazy } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import AppShell from "./components/AppShell";
import { Loading } from "./components/ui";
import { GuestRoute, ProtectedRoute } from "./components/ProtectedRoute";
import History from "./pages/History";
import LiveProgress from "./pages/LiveProgress";
import Login from "./pages/Login";
import NewAnalysis from "./pages/NewAnalysis";
import NotFound from "./pages/NotFound";
import Register from "./pages/Register";
 
// The report page pulls in the charting library (the heaviest dependency), so it loads on demand.
const ReportView = lazy(() => import("./pages/ReportView"));
 
export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<GuestRoute><Login /></GuestRoute>} />
        <Route path="/register" element={<GuestRoute><Register /></GuestRoute>} />
        <Route element={<ProtectedRoute><AppShell /></ProtectedRoute>}>
          <Route index element={<NewAnalysis />} />
          <Route path="analysis/:runId" element={<LiveProgress />} />
          <Route path="reports/:reportId" element={<Suspense fallback={<Loading>Loading report…</Loading>}><ReportView /></Suspense>} />
          <Route path="history" element={<History />} />
        </Route>
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  );
}
 