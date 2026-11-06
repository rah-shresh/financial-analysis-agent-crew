/** Tests for the two pages the other suites don't touch: New analysis (the form) and History. */
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
 
import reportsList from "./fixtures/reports_list.json";
 
vi.mock("../services/api", () => ({
  API_BASE: "http://test",
  listReports: vi.fn(),
  startRun: vi.fn(),
}));
 
import History from "../pages/History";
import NewAnalysis from "../pages/NewAnalysis";
import * as api from "../services/api";
 
beforeEach(() => {
  api.listReports.mockReset();
  api.startRun.mockReset();
});
 
function renderAt(path, ui) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path={path} element={ui} />
        <Route path="/analysis/:runId" element={<p>live progress page</p>} />
        <Route path="/reports/:id" element={<p>report page</p>} />
      </Routes>
    </MemoryRouter>
  );
}
 
describe("NewAnalysis", () => {
  it("rejects a malformed ticker on the spot, without calling the API", async () => {
    api.listReports.mockResolvedValue([]);
    renderAt("/", <NewAnalysis />);
    await userEvent.type(screen.getByLabelText(/ticker symbol/i), "TSLA; DROP TABLE");
    await userEvent.click(screen.getByRole("button", { name: /run analysis/i }));
    expect(screen.getByRole("alert")).toHaveTextContent(/letters, digits/i);
    expect(api.startRun).not.toHaveBeenCalled();
  });
 
  it("starts the run with the trimmed ticker and moves to the live progress page", async () => {
    api.listReports.mockResolvedValue([]);
    api.startRun.mockResolvedValue({ id: "run123" });
    renderAt("/", <NewAnalysis />);
    await userEvent.type(screen.getByLabelText(/ticker symbol/i), "  tsla ");
    await userEvent.click(screen.getByRole("button", { name: /run analysis/i }));
    expect(api.startRun).toHaveBeenCalledWith("tsla");
    expect(await screen.findByText("live progress page")).toBeInTheDocument();
  });
 
  it("shows the server's reason when a run can't start (e.g. one is already in progress)", async () => {
    api.listReports.mockResolvedValue([]);
    api.startRun.mockRejectedValue({ response: { status: 429, data: { detail: "You already have an analysis in progress." } } });
    renderAt("/", <NewAnalysis />);
    await userEvent.type(screen.getByLabelText(/ticker symbol/i), "AAPL");
    await userEvent.click(screen.getByRole("button", { name: /run analysis/i }));
    expect(await screen.findByRole("alert")).toHaveTextContent("You already have an analysis in progress.");
    expect(screen.getByRole("button", { name: /run analysis/i })).toBeEnabled(); // can try again
  });
 
  it("keeps the button disabled while the box is empty, and example chips fill it in", async () => {
    api.listReports.mockResolvedValue([]);
    renderAt("/", <NewAnalysis />);
    expect(screen.getByRole("button", { name: /run analysis/i })).toBeDisabled();
    await userEvent.click(screen.getByRole("button", { name: "NVDA" }));
    expect(screen.getByLabelText(/ticker symbol/i)).toHaveValue("NVDA");
    expect(screen.getByRole("button", { name: /run analysis/i })).toBeEnabled();
  });
 
  it("lists recent analyses, and the page still works if that list fails to load", async () => {
    api.listReports.mockResolvedValue(reportsList);
    const { unmount } = renderAt("/", <NewAnalysis />);
    expect(await screen.findByRole("link", { name: new RegExp(reportsList[0].ticker) })).toBeInTheDocument();
    unmount();
 
    api.listReports.mockRejectedValue(new Error("boom"));
    renderAt("/", <NewAnalysis />);
    expect(screen.getByLabelText(/ticker symbol/i)).toBeInTheDocument();
    expect(screen.queryByText(/recent analyses/i)).not.toBeInTheDocument();
  });
});
 
describe("History", () => {
  it("shows each saved report with its headline numbers, linking to the full report", async () => {
    api.listReports.mockResolvedValue(reportsList);
    renderAt("/history", <History />);
    const link = await screen.findByRole("link", { name: reportsList[0].ticker });
    expect(link).toHaveAttribute("href", `/reports/${reportsList[0].id}`);
    expect(screen.getByRole("columnheader", { name: /30-day arima/i })).toBeInTheDocument();
    expect(api.listReports).toHaveBeenCalledWith({ limit: 20, skip: 0 });
  });
 
  it("invites you to run a first analysis when there's nothing yet", async () => {
    api.listReports.mockResolvedValue([]);
    renderAt("/history", <History />);
    expect(await screen.findByText(/no analyses yet/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /run your first analysis/i })).toHaveAttribute("href", "/");
  });
 
  it("offers 'Load more' only after a full page, and appends the next page", async () => {
    const fullPage = Array.from({ length: 20 }, (_, i) => ({ ...reportsList[0], id: `r${i}`, ticker: `T${i}` }));
    api.listReports.mockResolvedValueOnce(fullPage).mockResolvedValueOnce([{ ...reportsList[0], id: "last", ticker: "LAST" }]);
    renderAt("/history", <History />);
    await screen.findByRole("link", { name: "T0" });
    await userEvent.click(screen.getByRole("button", { name: /load more/i }));
    expect(api.listReports).toHaveBeenLastCalledWith({ limit: 20, skip: 20 });
    expect(await screen.findByRole("link", { name: "LAST" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "T0" })).toBeInTheDocument();           // earlier rows are kept
    expect(screen.queryByRole("button", { name: /load more/i })).not.toBeInTheDocument(); // short page = the end
  });
 
  it("shows a readable error instead of a blank page when loading fails", async () => {
    api.listReports.mockRejectedValue({ request: {} }); // no response = server unreachable
    renderAt("/history", <History />);
    expect(await screen.findByRole("alert")).toHaveTextContent(/can't reach the server at http:\/\/test/i);
  });
});
 












