import "@testing-library/jest-dom/vitest";
import { cloneElement } from "react";
import { vi } from "vitest";
 
// jsdom has no layout engine, so Recharts' ResponsiveContainer would measure 0x0 and draw nothing.
// Give charts a fixed size in tests so we can check what they actually render.
globalThis.ResizeObserver = class { observe() {} unobserve() {} disconnect() {} };
vi.mock("recharts", async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    ResponsiveContainer: ({ children }) => cloneElement(children, { width: 800, height: 320 }),
  };
});
 