import { useEffect, useState } from "react";
import { isActive } from "./useRunPolling";
 
/** Seconds a run has been going (ticks every second), or its total once it has finished. */
export function useElapsed(run) {
  const [now, setNow] = useState(() => Date.now());
  const active = Boolean(run) && isActive(run.status);
 
  useEffect(() => {
    if (!active) return undefined;
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, [active]);
 
  if (!run) return null;
  const start = new Date(run.started_at ?? run.created_at).getTime();
  const end = run.finished_at ? new Date(run.finished_at).getTime() : now;
  return Math.max(0, (end - start) / 1000);
}