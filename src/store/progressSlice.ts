import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface ProgressState {
	status: 'idle' | 'in_progress' | 'done';
	percent: number;
}

const initialState: ProgressState = {
	status: 'idle',
	percent: 0,
};

const progressSlice = createSlice({
	name: 'progress',
	initialState,
	reducers: {
		startTest: (state) => {
			state.status = 'in_progress';
			console.log("startTest: ", state.status);
		},
		startProgress: (state) => {
			state.status = 'in_progress';
		},
		setPercent: (state, action: PayloadAction<number>) => {
			state.percent = action.payload;
		},
		completeProgress: (state) => {
			state.status = 'done';
		},
		resetProgress: (state) => {
			state.status = 'idle';
		},
	},
});

export const { startTest, startProgress, setPercent, completeProgress, resetProgress } = progressSlice.actions;
export default progressSlice.reducer;