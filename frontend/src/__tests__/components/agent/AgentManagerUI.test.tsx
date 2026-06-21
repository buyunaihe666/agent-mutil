import { renderWithProviders } from "@/__tests__/test-utils";
import { AgentManagerUI } from "@/components/agent/AgentManagerUI";
import { fireEvent, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

describe("AgentManagerUI", () => {
  it("renders preset agents and new agent action in compact mode", () => {
    const { container } = renderWithProviders(<AgentManagerUI variant="compact" />);

    expect(container.firstElementChild).toHaveClass("bg-white", "text-gray-900");
    expect(screen.getByText("数字主管")).toBeInTheDocument();
    expect(screen.getByText("风控顾问")).toBeInTheDocument();
    expect(screen.getByText("数据专家")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "+ New Agent" })).toBeInTheDocument();
  });

  it("opens the template library when clicking Templates tab", () => {
    renderWithProviders(<AgentManagerUI variant="compact" />);

    fireEvent.click(screen.getByRole("tab", { name: "模板" }));

    expect(screen.getByText("市场分析")).toBeInTheDocument();
    expect(screen.getByText("代码审查")).toBeInTheDocument();
    expect(screen.getByText("文档撰写")).toBeInTheDocument();
    expect(screen.getByText("数据分析")).toBeInTheDocument();
  });

  it("renders agent cards for preset agents", () => {
    renderWithProviders(<AgentManagerUI />, {
      preloadedState: {
        agent: {
          agents: [],
          templates: [],
          editingAgentId: null,
          editingTemplateId: null,
          activeTab: "agents",
          selectedAgentId: null,
          searchQuery: "",
          templateSearchQuery: "",
          statusFilter: "all",
          versionHistory: {},
          isLoading: false,
          error: null,
        },
      } as never,
    });
    expect(screen.getByText("数字主管")).toBeInTheDocument();
    expect(screen.getByText("风控顾问")).toBeInTheDocument();
    expect(screen.getByText("数据专家")).toBeInTheDocument();
  });

  it("shows preset badge on preset agents", () => {
    renderWithProviders(<AgentManagerUI />);
    const presetBadges = screen.getAllByText("Preset");
    expect(presetBadges.length).toBe(3);
  });

  it("shows agent descriptions", () => {
    renderWithProviders(<AgentManagerUI />);
    expect(screen.getByText("任务拆解与分配协调者")).toBeInTheDocument();
    expect(screen.getByText("安全审计与合规检查")).toBeInTheDocument();
    expect(screen.getByText("数据处理与分析")).toBeInTheDocument();
  });

  it("preset agents have no delete button", () => {
    renderWithProviders(<AgentManagerUI />);
    const deleteButtons = screen.queryAllByRole("button", { name: /^删除 / });
    expect(deleteButtons.length).toBe(0);
  });

  it("shows tool tags for agents", () => {
    renderWithProviders(<AgentManagerUI />);
    const fileReadTags = screen.getAllByText("file_read");
    expect(fileReadTags.length).toBeGreaterThanOrEqual(1);
    const dbQueryTags = screen.getAllByText("database_query");
    expect(dbQueryTags.length).toBeGreaterThanOrEqual(1);
    const codeExecTags = screen.getAllByText("code_execution");
    expect(codeExecTags.length).toBeGreaterThanOrEqual(1);
  });

  it("shows model, permission level, and version info", () => {
    renderWithProviders(<AgentManagerUI />);
    expect(screen.getAllByText(/Model: deepseek-chat/).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/Level: L4/)).toBeInTheDocument();
    expect(screen.getByText(/Level: L3/)).toBeInTheDocument();
    expect(screen.getByText(/Level: L2/)).toBeInTheDocument();
  });

  it("search filters agents by name", () => {
    renderWithProviders(<AgentManagerUI />);
    const searchInput = screen.getByPlaceholderText("搜索...");
    fireEvent.change(searchInput, { target: { value: "风控" } });
    expect(screen.getByText("风控顾问")).toBeInTheDocument();
    expect(screen.queryByText("数字主管")).not.toBeInTheDocument();
    expect(screen.queryByText("数据专家")).not.toBeInTheDocument();
  });

  it("search filters agents by description", () => {
    renderWithProviders(<AgentManagerUI />);
    const searchInput = screen.getByPlaceholderText("搜索...");
    fireEvent.change(searchInput, { target: { value: "安全审计" } });
    expect(screen.getByText("风控顾问")).toBeInTheDocument();
    expect(screen.queryByText("数字主管")).not.toBeInTheDocument();
  });

  it("status filter shows only active agents", () => {
    renderWithProviders(<AgentManagerUI />);
    const filterSelect = screen.getByRole("combobox");
    fireEvent.change(filterSelect, { target: { value: "active" } });
    expect(screen.getByText("数字主管")).toBeInTheDocument();
    expect(screen.getByText("风控顾问")).toBeInTheDocument();
    expect(screen.getByText("数据专家")).toBeInTheDocument();
  });

  it("status filter shows only inactive agents", () => {
    renderWithProviders(<AgentManagerUI />);
    const filterSelect = screen.getByRole("combobox");
    fireEvent.change(filterSelect, { target: { value: "inactive" } });
    expect(screen.queryByText("数字主管")).not.toBeInTheDocument();
  });

  it("'New Agent' button opens editor", () => {
    renderWithProviders(<AgentManagerUI />);
    fireEvent.click(screen.getByText("+ New Agent"));
    expect(screen.getByText("New Agent")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Agent name")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Brief description")).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText("Define agent persona, behavior, and output format..."),
    ).toBeInTheDocument();
  });

  it("cancel button hides editor", () => {
    renderWithProviders(<AgentManagerUI />);
    fireEvent.click(screen.getByText("+ New Agent"));
    expect(screen.getByText("New Agent")).toBeInTheDocument();
    fireEvent.click(screen.getByText("取消"));
    expect(screen.queryByText("New Agent")).not.toBeInTheDocument();
  });

  it("template tab shows templates with edit, delete, and use buttons", () => {
    renderWithProviders(<AgentManagerUI />);
    fireEvent.click(screen.getByRole("tab", { name: "模板" }));

    expect(screen.getByText("市场分析")).toBeInTheDocument();
    expect(screen.getByText("代码审查")).toBeInTheDocument();
    expect(screen.getByText("文档撰写")).toBeInTheDocument();
    expect(screen.getByText("数据分析")).toBeInTheDocument();
    expect(screen.getByText("安全审计")).toBeInTheDocument();

    // Each template card should have a Use button
    const useButtons = screen.getAllByText("Use");
    expect(useButtons.length).toBe(5);
  });

  it("clicking Use on a template creates a new agent and switches to agents tab", () => {
    renderWithProviders(<AgentManagerUI />);
    fireEvent.click(screen.getByRole("tab", { name: "模板" }));
    fireEvent.click(screen.getAllByText("Use")[0]);

    // Should have switched back to agents tab and show the new agent
    expect(screen.queryByText("Template Library")).not.toBeInTheDocument();
    expect(screen.getByText("市场分析")).toBeInTheDocument(); // new agent in list
    expect(screen.getByText("数字主管")).toBeInTheDocument();
    expect(screen.getByText("风控顾问")).toBeInTheDocument();
    expect(screen.getByText("数据专家")).toBeInTheDocument();
  });

  it("version history toggle", () => {
    renderWithProviders(<AgentManagerUI />);
    const showButtons = screen.getAllByText("Show Version History");
    fireEvent.click(showButtons[0]);
    expect(screen.getByText("Hide Version History")).toBeInTheDocument();
    expect(screen.getAllByText("v1").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Initial version")).toBeInTheDocument();
  });

  it("version history hides on second click", () => {
    renderWithProviders(<AgentManagerUI />);
    const showButtons = screen.getAllByText("Show Version History");
    fireEvent.click(showButtons[0]);
    fireEvent.click(screen.getByText("Hide Version History"));
    const showButtonsAfter = screen.getAllByText("Show Version History");
    expect(showButtonsAfter.length).toBe(3);
  });

  it("renders Redux version history for an agent instead of synthetic fallback entries", () => {
    renderWithProviders(<AgentManagerUI />, {
      preloadedState: {
        agent: {
          agents: [],
          templates: [],
          editingAgentId: null,
          editingTemplateId: null,
          activeTab: "agents",
          selectedAgentId: null,
          searchQuery: "",
          templateSearchQuery: "",
          statusFilter: "all",
          versionHistory: {
            "1": [
              {
                version_number: 7,
                change_description: "Unique store-backed history entry",
                created_at: "2026-06-10T00:00:00.000Z",
              },
            ],
          },
          isLoading: false,
          error: null,
        },
      } as never,
    });

    fireEvent.click(screen.getAllByText("Show Version History")[0]);

    expect(screen.getByText("Unique store-backed history entry")).toBeInTheDocument();
    expect(screen.queryByText("Initial version")).not.toBeInTheDocument();
  });

  it("edit button opens editor with prefilled data", () => {
    renderWithProviders(<AgentManagerUI />);
    const editButton = screen.getByRole("button", { name: "编辑 数字主管" });
    fireEvent.click(editButton);
    const nameInput = screen.getByPlaceholderText("Agent name") as HTMLInputElement;
    expect(nameInput.value).toBe("数字主管");
    expect(screen.getByText("编辑 Agent")).toBeInTheDocument();
  });

  it("edit button has accessible name for preset agent", () => {
    renderWithProviders(<AgentManagerUI />);
    expect(screen.getByRole("button", { name: "编辑 数字主管" })).toBeInTheDocument();
  });

  it("saving edits to a fallback preset keeps the updated agent visible", () => {
    renderWithProviders(<AgentManagerUI />);
    fireEvent.click(screen.getByRole("button", { name: "编辑 数字主管" }));
    const nameInput = screen.getByPlaceholderText("Agent name") as HTMLInputElement;
    fireEvent.change(nameInput, { target: { value: "Updated Name" } });
    fireEvent.click(screen.getByRole("button", { name: "保存" }));

    expect(screen.queryByText("保存")).not.toBeInTheDocument();
    expect(screen.getByText("Updated Name")).toBeInTheDocument();
  });

  it("Templates tab has + New Template button that opens template editor", () => {
    renderWithProviders(<AgentManagerUI />);
    fireEvent.click(screen.getByRole("tab", { name: "模板" }));

    const newTemplateButton = screen.getByText("+ New Template");
    fireEvent.click(newTemplateButton);

    expect(screen.getByText("New Template")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Template name")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Brief description")).toBeInTheDocument();
  });

  it("template editor cancel hides the editor", () => {
    renderWithProviders(<AgentManagerUI />);
    fireEvent.click(screen.getByRole("tab", { name: "模板" }));
    fireEvent.click(screen.getByText("+ New Template"));
    expect(screen.getByText("New Template")).toBeInTheDocument();

    fireEvent.click(screen.getByText("取消"));
    expect(screen.queryByText("New Template")).not.toBeInTheDocument();
  });

  it("template cards have edit and delete buttons", () => {
    renderWithProviders(<AgentManagerUI />);
    fireEvent.click(screen.getByRole("tab", { name: "模板" }));

    // Each template should have edit and delete buttons
    const editButtons = screen.getAllByRole("button", { name: /^编辑 / });
    expect(editButtons.length).toBe(5);
    const deleteButtons = screen.getAllByRole("button", { name: /^删除 / });
    expect(deleteButtons.length).toBe(5);
  });

  it("template edit button opens editor with prefilled data", () => {
    renderWithProviders(<AgentManagerUI />);
    fireEvent.click(screen.getByRole("tab", { name: "模板" }));

    const editButton = screen.getByRole("button", { name: "编辑 市场分析" });
    fireEvent.click(editButton);

    expect(screen.getByText("编辑 Template")).toBeInTheDocument();
    const nameInput = screen.getByPlaceholderText("Template name") as HTMLInputElement;
    expect(nameInput.value).toBe("市场分析");
  });
});
