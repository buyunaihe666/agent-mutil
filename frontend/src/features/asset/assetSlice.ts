import { createSlice } from "@reduxjs/toolkit";
import type { PayloadAction } from "@reduxjs/toolkit";

export interface AssetItem {
  id: string;
  filename: string;
  original_filename: string;
  file_size: number;
  mime_type?: string;
  preview_type: string;
  created_at: string;
}

interface AssetState {
  assets: AssetItem[];
  selectedAssetId: string | null;
  searchQuery: string;
  isLoading: boolean;
  error: string | null;
}

const initialState: AssetState = {
  assets: [],
  selectedAssetId: null,
  searchQuery: "",
  isLoading: false,
  error: null,
};

export const assetSlice = createSlice({
  name: "asset",
  initialState,
  reducers: {
    setAssets: (state, action: PayloadAction<AssetItem[]>) => {
      state.assets = action.payload;
    },
    addAsset: (state, action: PayloadAction<AssetItem>) => {
      state.assets.unshift(action.payload);
    },
    removeAsset: (state, action: PayloadAction<string>) => {
      state.assets = state.assets.filter((a) => a.id !== action.payload);
      if (state.selectedAssetId === action.payload) {
        state.selectedAssetId = null;
      }
    },
    setSelectedAsset: (state, action: PayloadAction<string | null>) => {
      state.selectedAssetId = action.payload;
    },
    setSearchQuery: (state, action: PayloadAction<string>) => {
      state.searchQuery = action.payload;
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
  setAssets,
  addAsset,
  removeAsset,
  setSelectedAsset,
  setSearchQuery,
  setLoading,
  setError,
} = assetSlice.actions;

export default assetSlice.reducer;
