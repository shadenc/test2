import { render, screen, waitFor } from "@testing-library/react";
import App from "./App";

beforeEach(() => {
  global.fetch = jest.fn((url) => {
    const u = String(url);
    if (u.includes("/foreign_ownership_data.json") || u.endsWith(".json")) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve([]),
        text: () => Promise.resolve(""),
      });
    }
    if (u.includes("retained_earnings_flow") || u.includes("/api/")) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ status: "idle" }),
        text: () => Promise.resolve(""),
      });
    }
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve([]),
      text: () => Promise.resolve(""),
    });
  });
});

test("renders dashboard grid after load", async () => {
  render(<App />);
  await waitFor(() => {
    expect(screen.getByRole("grid")).toBeInTheDocument();
  });
});
