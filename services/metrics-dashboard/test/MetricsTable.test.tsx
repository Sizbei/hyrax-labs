import { describe, it, expect } from "vitest";
import { render, screen, fireEvent, within } from "@testing-library/react";
import { MetricsTable } from "../src/components/MetricsTable";
import { generateAssets, snapshotAll } from "../src/data/generator";
import { METRICS } from "../src/data/metricsCatalog";

const assets = generateAssets(1337).slice(0, 20);
const snapshots = snapshotAll(assets, 1_700_000_000_000, 0);

function renderTable() {
  return render(
    <MetricsTable
      metrics={[...METRICS]}
      assets={assets}
      snapshots={snapshots}
      columnIds={["views", "likes", "ctr"]}
    />,
  );
}

describe("MetricsTable", () => {
  it("renders rows and column headers", () => {
    renderTable();
    expect(screen.getByText(/^Views/)).toBeInTheDocument();
    expect(screen.getByText(/^Likes/)).toBeInTheDocument();
    const body = screen.getByRole("table").querySelector("tbody")!;
    expect(within(body).getAllByRole("row").length).toBeGreaterThan(0);
  });

  it("filters rows by the search query", () => {
    renderTable();
    const body = screen.getByRole("table").querySelector("tbody")!;
    const before = within(body).getAllByRole("row").length;
    fireEvent.change(screen.getByLabelText("Filter assets"), {
      target: { value: "zzz-no-match-zzz" },
    });
    const after = within(body).queryAllByRole("row").length;
    expect(after).toBeLessThan(before);
    expect(after).toBe(0);
  });

  it("toggles sort direction when a header is clicked", () => {
    renderTable();
    // Likes is not the default sort column, so it starts unsorted.
    const header = screen.getByText(/^Likes/);
    fireEvent.click(header);
    expect(header.textContent).toContain("▼");
    fireEvent.click(header);
    expect(header.textContent).toContain("▲");
  });
});
