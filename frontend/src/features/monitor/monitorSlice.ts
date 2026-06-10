import { createSlice } from "@reduxjs/toolkit";
import type { PayloadAction } from "@reduxjs/toolkit";

export interface HardwareStats {
  cpu_percent: number;
  memory_used_mb: number;
  memory_total_mb: number;
  gpu_name?: string;
  gpu_utilization_percent?: number;
}

export interface ContainerStats {
  container_id: string;
  name: string;
  cpu_percent: number;
  memory_usage_mb: number;
  memory_limit_mb: number;
  status: string;
}

export interface AgentActivity {
  agent_id: string;
  agent_name: string;
  agent_emoji?: string;
  status: "idle" | "working" | "blocked" | "error";
  message?: string;
}

export interface AuditEvent {
  id: string;
  action: string;
  user_id?: string;
  agent_id?: string;
  details?: string;
  timestamp: string;
}

export interface RateLimitInfo {
  api_requests_per_min: number;
  llm_requests_per_min: number;
}

interface MonitorState {
  activeTab: "performance" | "security";
  hardware: HardwareStats | null;
  containers: ContainerStats[];
  agentActivities: AgentActivity[];
  auditEvents: AuditEvent[];
  rateLimits: RateLimitInfo;
  isConnected: boolean;
  error: string | null;
}

const initialState: MonitorState = {
  activeTab: "performance",
  hardware: null,
  containers: [],
  agentActivities: [],
  auditEvents: [],
  rateLimits: {
    api_requests_per_min: 60,
    llm_requests_per_min: 10,
  },
  isConnected: false,
  error: null,
};

export const monitorSlice = createSlice({
  name: "monitor",
  initialState,
  reducers: {
    setActiveTab: (state, action: PayloadAction<"performance" | "security">) => {
      state.activeTab = action.payload;
    },
    setHardwareStats: (state, action: PayloadAction<HardwareStats>) => {
      state.hardware = action.payload;
    },
    setContainers: (state, action: PayloadAction<ContainerStats[]>) => {
      state.containers = action.payload;
    },
    setAgentActivities: (state, action: PayloadAction<AgentActivity[]>) => {
      state.agentActivities = action.payload;
    },
    updateAgentActivity: (state, action: PayloadAction<AgentActivity>) => {
      const idx = state.agentActivities.findIndex((a) => a.agent_id === action.payload.agent_id);
      if (idx !== -1) {
        state.agentActivities[idx] = action.payload;
      } else {
        state.agentActivities.push(action.payload);
      }
    },
    setAuditEvents: (state, action: PayloadAction<AuditEvent[]>) => {
      state.auditEvents = action.payload;
    },
    addAuditEvent: (state, action: PayloadAction<AuditEvent>) => {
      state.auditEvents.unshift(action.payload);
      // Keep max 100 events
      if (state.auditEvents.length > 100) {
        state.auditEvents = state.auditEvents.slice(0, 100);
      }
    },
    setRateLimits: (state, action: PayloadAction<RateLimitInfo>) => {
      state.rateLimits = action.payload;
    },
    setConnected: (state, action: PayloadAction<boolean>) => {
      state.isConnected = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
  },
});

export const {
  setActiveTab,
  setHardwareStats,
  setContainers,
  setAgentActivities,
  updateAgentActivity,
  setAuditEvents,
  addAuditEvent,
  setRateLimits,
  setConnected,
  setError,
} = monitorSlice.actions;

export default monitorSlice.reducer;
