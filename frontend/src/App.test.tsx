import { LayoutShell } from "@/components/layout/LayoutShell";
import { t } from "@/i18n";
import { store } from "@/store";
import { render, screen } from "@testing-library/react";
import { Provider } from "react-redux";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

describe("LayoutShell", () => {
  function renderLayout() {
    return render(
      <Provider store={store}>
        <MemoryRouter initialEntries={["/"]}>
          <LayoutShell />
        </MemoryRouter>
      </Provider>,
    );
  }

  it("renders without crashing", () => {
    renderLayout();
    expect(screen.getByText("NEXUS AI")).toBeInTheDocument();
  });

  it("renders status bar with version", () => {
    renderLayout();
    expect(screen.getByText(t("shell.version"))).toBeInTheDocument();
  });
});
