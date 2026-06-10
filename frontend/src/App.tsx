import { BrowserRouter, Route, Routes } from "react-router-dom";
import { AgentManagerUI } from "./components/agent/AgentManagerUI";
import { AssetPanel } from "./components/asset/AssetPanel";
import { ConversationUI } from "./components/conversation/ConversationUI";
import { LayoutShell } from "./components/layout/LayoutShell";
import { MonitorPanel } from "./components/monitor/MonitorPanel";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/*" element={<LayoutShell />}>
          <Route index element={<ConversationUI />} />
          <Route path="conversations" element={<ConversationUI />} />
          <Route path="assets" element={<AssetPanel />} />
          <Route path="agents" element={<AgentManagerUI />} />
          <Route path="monitor" element={<MonitorPanel />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
