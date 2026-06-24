import { createSlice } from "@reduxjs/toolkit";
import type { PayloadAction } from "@reduxjs/toolkit";

export interface AgentData {
  id: string;
  name: string;
  description?: string;
  system_prompt?: string;
  avatar_emoji?: string;
  permission_level: number;
  is_preset: boolean;
  is_active: boolean;
  is_meta?: boolean;
  tools?: string[];
  default_model: string;
  temperature: number;
  version_count: number;
  updated_at: string;
}

export interface AgentTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  avatar_emoji: string;
  system_prompt: string;
  tools: string[];
}

export interface AgentVersion {
  version_number: number;
  change_description?: string;
  created_at: string;
}

interface AgentState {
  agents: AgentData[];
  templates: AgentTemplate[];
  editingAgentId: string | null;
  editingTemplateId: string | null;
  activeTab: "agents" | "templates";
  selectedAgentId: string | null;
  searchQuery: string;
  templateSearchQuery: string;
  statusFilter: "all" | "active" | "inactive";
  versionHistory: Record<string, AgentVersion[]>; // agentId -> versions
  isLoading: boolean;
  error: string | null;
}

const initialState: AgentState = {
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
};

export const agentSlice = createSlice({
  name: "agent",
  initialState,
  reducers: {
    setAgents: (state, action: PayloadAction<AgentData[]>) => {
      state.agents = action.payload;
    },
    addAgent: (state, action: PayloadAction<AgentData>) => {
      state.agents.push(action.payload);
    },
    updateAgent: (state, action: PayloadAction<Partial<AgentData> & { id: string }>) => {
      const idx = state.agents.findIndex((a) => a.id === action.payload.id);
      if (idx !== -1) {
        state.agents[idx] = {
          ...state.agents[idx],
          ...action.payload,
          version_count: state.agents[idx].version_count + 1,
          updated_at: new Date().toISOString(),
        };
      }
    },
    removeAgent: (state, action: PayloadAction<string>) => {
      state.agents = state.agents.filter((a) => a.id !== action.payload);
    },
    setEditingAgent: (state, action: PayloadAction<string | null>) => {
      state.editingAgentId = action.payload;
    },
    setActiveTab: (state, action: PayloadAction<"agents" | "templates">) => {
      state.activeTab = action.payload;
    },
    setEditingTemplate: (state, action: PayloadAction<string | null>) => {
      state.editingTemplateId = action.payload;
    },
    setTemplateSearchQuery: (state, action: PayloadAction<string>) => {
      state.templateSearchQuery = action.payload;
    },
    addTemplate: (state, action: PayloadAction<AgentTemplate>) => {
      state.templates.push(action.payload);
    },
    updateTemplate: (state, action: PayloadAction<Partial<AgentTemplate> & { id: string }>) => {
      const idx = state.templates.findIndex((t) => t.id === action.payload.id);
      if (idx !== -1) {
        state.templates[idx] = { ...state.templates[idx], ...action.payload };
      }
    },
    removeTemplate: (state, action: PayloadAction<string>) => {
      state.templates = state.templates.filter((t) => t.id !== action.payload);
    },
    setSelectedAgent: (state, action: PayloadAction<string | null>) => {
      state.selectedAgentId = action.payload;
    },
    setSearchQuery: (state, action: PayloadAction<string>) => {
      state.searchQuery = action.payload;
    },
    setStatusFilter: (state, action: PayloadAction<"all" | "active" | "inactive">) => {
      state.statusFilter = action.payload;
    },
    setTemplates: (state, action: PayloadAction<AgentTemplate[]>) => {
      state.templates = action.payload;
    },
    setVersionHistory: (
      state,
      action: PayloadAction<{ agentId: string; versions: AgentVersion[] }>,
    ) => {
      state.versionHistory[action.payload.agentId] = action.payload.versions;
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
  },
});

export const {
  setAgents,
  addAgent,
  updateAgent,
  removeAgent,
  setEditingAgent,
  setActiveTab,
  setEditingTemplate,
  setTemplateSearchQuery,
  addTemplate,
  updateTemplate,
  removeTemplate,
  setSelectedAgent,
  setSearchQuery,
  setStatusFilter,
  setTemplates,
  setVersionHistory,
  setLoading,
  setError,
} = agentSlice.actions;

export default agentSlice.reducer;
