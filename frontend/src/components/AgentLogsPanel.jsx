import { AGENT_LABELS, AGENT_WORKING_TEXT } from "../services/format";
 
const STATUS = {
  queued: { text: "queued", cls: "border-rule text-ink-soft" },
  running: { text: "running", cls: "border-stamp text-stamp pulse-stamp" },
  done: { text: "done", cls: "border-gain text-gain" },
  skipped: { text: "skipped", cls: "border-rule text-ink-soft" },
  failed: { text: "failed", cls: "border-stamp text-stamp" },
};
 
/**
 * The live "agent log": one ruled row per agent, in pipeline order, with its
 * status, its own log lines, and -- while it's working -- what it's doing.
 * This is the part of the UI that shows it's a multi-agent system.
 * `agents` is the API's list of { name, status, message, log }.
 */
export default function AgentLogsPanel({ agents }) {
  return (
    <ol className="panel divide-y divide-rule-soft" aria-label="Agent progress">
      {agents.map((agent, i) => {
        const s = STATUS[agent.status] ?? STATUS.queued;
        const label = AGENT_LABELS[agent.name] ?? agent.name;
        // A failure's reason is usually already in the agent's own log line; don't print it twice.
        const showMessage = agent.message && (agent.status === "failed" || agent.status === "skipped")
          && !agent.log?.some((line) => line.includes(agent.message));
        return (
          <li key={agent.name} className="px-4 py-3" aria-label={`${label}: ${agent.status}`}>
            <div className="flex items-center gap-3">
              <span className="num w-5 text-sm text-ink-soft">{i + 1}</span>
              <span className="flex-1 font-medium">{label}</span>
              <span className={`border px-2 py-0.5 font-mono text-[11px] ${s.cls}`}>{s.text}</span>
            </div>
 
            {agent.status === "running" && (
              <p className="pulse-stamp ml-8 mt-1.5 text-sm text-stamp">{AGENT_WORKING_TEXT[agent.name]}</p>
            )}
 
            {agent.log?.length > 0 && (
              <ul className="ml-8 mt-1.5 space-y-0.5">
                {agent.log.map((line, j) => (
                  <li key={j} className="font-mono text-xs text-ink-soft">{line}</li>
                ))}
              </ul>
            )}
 
            {showMessage && (
              <p className={`ml-8 mt-1.5 text-sm italic ${agent.status === "failed" ? "text-stamp" : "text-ink-soft"}`}>
                {agent.message}
              </p>
            )}
          </li>
        );
      })}
    </ol>
  );
}
 












