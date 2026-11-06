import { useEffect, useState } from "react";
import { getRun } from "../services/api";
import { getErrorMessage } from "../services/errors";
 
const ACTIVE = ["queued", "running"];
export const isActive = (status) => ACTIVE.includes(status);
 
/**
 * Polls GET /api/analysis/{id} until the run finishes.
 * (The backend saves progress after every agent, so polling shows live progress.)
 * Stops on: finished run, 404, or 5 failures in a row. Cleans up on unmount.
 */
export function useRunPolling(runId, intervalMs = 2000) {
  const [run, setRun] = useState(null);
  const [error, setError] = useState(null);
 
  useEffect(() => {
    let cancelled = false;
    let timer;
    let failures = 0;
    setRun(null);
    setError(null);
 
    const tick = async () => {
      try {
        const data = await getRun(runId);
        if (cancelled) return;
        failures = 0;
        setRun(data);
        setError(null);
        if (isActive(data.status)) timer = setTimeout(tick, intervalMs);
      } catch (err) {
        if (cancelled) return;
        if (err.response?.status === 404) {
          setError("This analysis could not be found.");
          return;
        }
        failures += 1;
        if (failures >= 5) {
          setError(getErrorMessage(err));
          return;
        }
        timer = setTimeout(tick, intervalMs * 2);
      }
    };
 
    tick();
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [runId, intervalMs]);
 
  return { run, error };
}
 












