/** Test utility: render component wrapped with Redux Provider and MemoryRouter. */

import agentReducer from "@/features/agent/agentSlice";
import assetReducer from "@/features/asset/assetSlice";
import conversationReducer from "@/features/conversation/conversationSlice";
import monitorReducer from "@/features/monitor/monitorSlice";
import themeReducer from "@/features/theme/themeSlice";
import type { RootState } from "@/store";
import { configureStore } from "@reduxjs/toolkit";
import { type RenderOptions, render } from "@testing-library/react";
import type { ReactElement } from "react";
import { Provider } from "react-redux";
import { MemoryRouter } from "react-router-dom";

/** Create a fully configured store with all reducers for testing. */
export function createMockStore(overrides?: Partial<RootState>) {
  return configureStore({
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    reducer: {
      theme: themeReducer,
      conversation: conversationReducer,
      agent: agentReducer,
      asset: assetReducer,
      monitor: monitorReducer,
      // biome-ignore lint/suspicious/noExplicitAny: test utility cast
    } as any,
    preloadedState: overrides,
  });
}

interface RenderWithProvidersOptions extends Omit<RenderOptions, "wrapper"> {
  initialRoute?: string;
  preloadedState?: Partial<RootState>;
}

export function renderWithProviders(ui: ReactElement, options: RenderWithProvidersOptions = {}) {
  const { initialRoute = "/", preloadedState, ...renderOptions } = options;
  const store = createMockStore(preloadedState);

  function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <Provider store={store}>
        <MemoryRouter initialEntries={[initialRoute]}>{children}</MemoryRouter>
      </Provider>
    );
  }

  return { store, ...render(ui, { wrapper: Wrapper, ...renderOptions }) };
}
