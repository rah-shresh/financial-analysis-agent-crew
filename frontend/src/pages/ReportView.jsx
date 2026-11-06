import { useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import Tabs from "../components/Tabs";
import { ErrorNote, Loading } from "../components/ui";
import { API_BASE, getReport } from "../services/api";
import { getErrorMessage } from "../services/errors";
import { longDate } from "../services/format";
import OverviewTab from "./report/OverviewTab";
import PredictionTab from "./report/PredictionTab";
import RiskTab from "./report/RiskTab";
import SentimentTab from "./report/SentimentTab";
import TechnicalTab from "./report/TechnicalTab";
 
const TABS = [
  { id: "overview", label: "Overview" },
  { id: "technical", label: "Technical" },
  { id: "sentiment", label: "Sentiment" },
  { id: "prediction", label: "Prediction" },
  { id: "risk", label: "Risk" },
];
const PANELS = { overview: OverviewTab, technical: TechnicalTab, sentiment: SentimentTab, prediction: PredictionTab, risk: RiskTab };
 
export default function ReportView() {
  const { reportId } = useParams();
  const [params, setParams] = useSearchParams();
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);
 
  useEffect(() => {
    let cancelled = false;
    setReport(null);
    setError(null);
    getReport(reportId)
      .then((r) => !cancelled && setReport(r))
      .catch((err) =>
        !cancelled && setError(err.response?.status === 404 ? "This report could not be found." : getErrorMessage(err, API_BASE))
      );
    return () => { cancelled = true; };
  }, [reportId]);
 
  // The active tab lives in the URL (?tab=risk) so a refresh or a shared link keeps it.
  const requested = params.get("tab");
  const tab = TABS.some((t) => t.id === requested) ? requested : "overview";
  const setTab = (id) => setParams(id === "overview" ? {} : { tab: id }, { replace: true });
 
  if (error) {
    return (
      <div className="space-y-4">
        <ErrorNote>{error}</ErrorNote>
        <Link to="/history" className="btn-ghost inline-block">Back to history</Link>
      </div>
    );
  }
  if (!report) return <Loading>Loading report…</Loading>;
 
  const Panel = PANELS[tab];
  return (
    <div>
      <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="label">Report · {longDate(report.created_at)}</p>
          <h1 className="text-3xl font-semibold">{report.ticker}</h1>
        </div>
        <Link to="/history" className="text-sm underline">← History</Link>
      </div>
 
      <Tabs tabs={TABS} active={tab} onChange={setTab} idPrefix="report" />
      <div role="tabpanel" id={`report-panel-${tab}`} aria-labelledby={`report-${tab}`}>
        <Panel report={report} />
      </div>
 
      <p className="mt-10 border-t border-rule pt-3 text-xs italic text-ink-soft">{report.disclaimer}</p>
    </div>
  );
}
 












