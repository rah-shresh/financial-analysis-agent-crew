/** Turn whatever went wrong into one readable sentence for the user. */
export function getErrorMessage(err, apiBase = "") {
  if (err?.response) {
    const { status, data } = err.response;
    const detail = data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail) && detail.length) {
      // FastAPI validation errors: [{ loc: ["body","password"], msg: "String should have at least 8 characters" }]
      return detail
        .map((d) => {
          const field = Array.isArray(d.loc) ? d.loc[d.loc.length - 1] : "";
          const msg = String(d.msg || "Invalid value").replace(/^Value error, /, "");
          return field && field !== "body" ? `${field}: ${msg}` : msg;
        })
        .join(" \u00b7 ");
    }
    if (status === 429) return "Too many requests. Please wait a moment and try again.";
    if (status >= 500) return "The server hit a problem. Please try again.";
    return `Request failed (${status}).`;
  }
  if (err?.request) {
    return `Can't reach the server${apiBase ? ` at ${apiBase}` : ""}. Is the backend running?`;
  }
  return err?.message || "Something went wrong.";
}
 