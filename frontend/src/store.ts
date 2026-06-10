import { configureStore } from "@reduxjs/toolkit";
import agentReducer from "./features/agent/agentSlice";
import assetReducer from "./features/asset/assetSlice";
import conversationReducer from "./features/conversation/conversationSlice";
import monitorReducer from "./features/monitor/monitorSlice";
import themeReducer from "./features/theme/themeSlice";

export const store = configureStore({
  reducer: {
    theme: themeReducer,
    conversation: conversationReducer,
    agent: agentReducer,
    asset: assetReducer,
    monitor: monitorReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
