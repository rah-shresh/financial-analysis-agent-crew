import { Link, useParams } from "react-router-dom";
import AgentLogsPanel from "../components/AgentLogsPanel";
import { ErrorNote, Loading, Pill } from "../components/ui";
import { useElapsed } from "../hooks/useElapsed";
import { isActive, useRunPolling } from "../hooks/useRunPolling";
import { formatDuration } from "../services/format";
 
const TONE = { queued: "default", running: "stamp", completed: "gain", failed: "stamp" };
 
export default function LiveProgress() {
  const { runId } = useParams();
  const { run, error } = useRunPolling(runId);
  const elapsed = useElapsed(run);
 
  if (error) {
    return (
      <div className="space-y-4">
        <ErrorNote>{error}</ErrorNote>
        <Link to="/" className="btn-ghost inline-block">Back to new analysis</Link>
      </div>
    );
  }
  if (!run) return <Loading>Loading analysis…</Loading>;
 
  return (
    <div>
      <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="label">Analysis</p>
          <h1 className="text-3xl font-semibold">{run.ticker}</h1>
        </div>
        <div className="flex items-center gap-3">
          <span className="num text-sm text-ink-soft" aria-label="Elapsed time">{formatDuration(elapsed ?? 0)}</span>
          <Pill tone={TONE[run.status]}>{run.status}</Pill>
        </div>
      </div>
 
      <AgentLogsPanel agents={run.agents} />
 
      {isActive(run.status) && (
        <p className="mt-4 text-sm text-ink-soft" role="status">
          This usually takes 1–2 minutes. You can leave this page — the analysis keeps running and will be waiting in your history.
        </p>
      )}
 
      {run.status === "completed" && run.report_id && (
        <div className="mt-6 flex items-center gap-4">
          <Link to={`/reports/${run.report_id}`} className="btn-primary">View report →</Link>
          <Link to="/" className="text-sm underline">Run another</Link>
        </div>
      )}
 
      {run.status === "failed" && (
        <div className="mt-6 space-y-4">
          <ErrorNote>{run.error || "This analysis failed."}</ErrorNote>
          <Link to="/" className="btn-ghost inline-block">Try another ticker</Link>
        </div>
      )}
    </div>
  );
}
 












