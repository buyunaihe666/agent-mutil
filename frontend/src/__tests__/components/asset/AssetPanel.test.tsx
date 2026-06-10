import { renderWithProviders } from "@/__tests__/test-utils";
import { AssetPanel } from "@/components/asset/AssetPanel";
import { t } from "@/i18n";
import { fireEvent, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

describe("AssetPanel compact variant", () => {
  it("renders the mock asset list with compact light styling", () => {
    const { container } = renderWithProviders(<AssetPanel variant="compact" />);

    expect(container.firstElementChild).toHaveClass("bg-white", "text-slate-900");
    expect(screen.getByText("sales_report.csv")).toBeInTheDocument();
    expect(screen.getByText("architecture.png")).toBeInTheDocument();
    expect(screen.getByText("readme.md")).toBeInTheDocument();
  });

  it("filters compact assets case-insensitively from the labelled search input", () => {
    renderWithProviders(<AssetPanel variant="compact" />);

    const searchInput = screen.getByRole("textbox", { name: t("common.search") });
    fireEvent.change(searchInput, { target: { value: "ARCHITECTURE" } });

    expect(screen.getByText("architecture.png")).toBeInTheDocument();
    expect(screen.queryByText("sales_report.csv")).not.toBeInTheDocument();
    expect(screen.queryByText("readme.md")).not.toBeInTheDocument();
  });

  it("shows translated image metadata and download action after clicking architecture.png", () => {
    renderWithProviders(<AssetPanel variant="compact" />);

    fireEvent.click(screen.getByText("architecture.png"));

    expect(screen.getByText(`${t("asset.type")}: image`)).toBeInTheDocument();
    expect(screen.getByText(`${t("asset.size")}: 1.0 MB`)).toBeInTheDocument();
    expect(screen.getByText(`${t("asset.mime")}: image/png`)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: new RegExp(t("action.download")) }),
    ).toBeInTheDocument();
  });

  it("marks the selected compact asset as pressed and clears it when clicked again", () => {
    renderWithProviders(<AssetPanel variant="compact" />);

    const assetButton = screen.getByRole("button", { name: /architecture\.png/ });
    expect(assetButton).toHaveAttribute("aria-pressed", "false");

    fireEvent.click(assetButton);
    expect(assetButton).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByText(`${t("asset.type")}: image`)).toBeInTheDocument();

    fireEvent.click(assetButton);

    expect(assetButton).toHaveAttribute("aria-pressed", "false");
    expect(screen.queryByText(`${t("asset.type")}: image`)).not.toBeInTheDocument();
  });

  it("shows the empty state when compact search has no matches", () => {
    renderWithProviders(<AssetPanel variant="compact" />);

    const searchInput = screen.getByRole("textbox", { name: t("common.search") });
    fireEvent.change(searchInput, { target: { value: "no_such_asset" } });

    expect(screen.getByText(t("status.empty"))).toBeInTheDocument();
  });

  it("renders Redux assets instead of mock assets when the store has uploaded assets", () => {
    renderWithProviders(<AssetPanel variant="compact" />, {
      preloadedState: {
        asset: {
          assets: [
            {
              id: "uploaded-1",
              filename: "uploaded.csv",
              original_filename: "uploaded.csv",
              file_size: 512,
              mime_type: "text/csv",
              preview_type: "table",
              created_at: "2026-06-10T00:00:00.000Z",
            },
          ],
          selectedAssetId: null,
          searchQuery: "",
          isLoading: false,
          error: null,
        },
      },
    });

    expect(screen.getByText("uploaded.csv")).toBeInTheDocument();
    expect(screen.queryByText("sales_report.csv")).not.toBeInTheDocument();
  });
});

describe("AssetPanel default/full variant", () => {
  it("renders asset list with dark sidebar-themed classes when variant is omitted (defaults to full)", () => {
    const { container } = renderWithProviders(<AssetPanel />);

    expect(container.firstElementChild).toHaveClass("bg-sidebar", "text-white");
    expect(screen.getByText("sales_report.csv")).toBeInTheDocument();
    expect(screen.getByText("architecture.png")).toBeInTheDocument();
    expect(screen.getByText("readme.md")).toBeInTheDocument();
  });
});
