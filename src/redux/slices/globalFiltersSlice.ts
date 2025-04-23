import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { RootState } from '../store';

interface DateRange {
  start: Date | null;
  end: Date | null;
}

interface GlobalFiltersState {
  selectedTickers: string[];
  dateRange: DateRange;
  sentiment: string;
}

const initialState: GlobalFiltersState = {
  selectedTickers: [],
  dateRange: { start: null, end: null },
  sentiment: 'All',
};

export const globalFiltersSlice = createSlice({
  name: 'globalFilters',
  initialState,
  reducers: {
    setSelectedTickers: (state, action: PayloadAction<string[]>) => {
      state.selectedTickers = action.payload;
    },
    setDateRange: (state, action: PayloadAction<DateRange>) => {
      state.dateRange = action.payload;
    },
    setSentiment: (state, action: PayloadAction<string>) => {
      state.sentiment = action.payload;
    },
  },
});

export const { setSelectedTickers, setDateRange, setSentiment } = globalFiltersSlice.actions;

export const selectGlobalFilters = (state: RootState) => state.globalFilters;

export default globalFiltersSlice.reducer; 