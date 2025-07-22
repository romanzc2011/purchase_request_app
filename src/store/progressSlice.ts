import { createSlice } from '@reduxjs/toolkit';

interface ProgressState {
	status: 'idle' | 'in_progress' | 'done' | 'reset_data';
}

const initialState: ProgressState = {
	status: 'idle',
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
		completeProgress: (state) => {
			state.status = 'done';
			console.log("complete: ", state.status);
		},
		resetProgress: (state) => {
			state.status = 'reset_data';
		},
	},
});

export const { startTest, startProgress, completeProgress, resetProgress } = progressSlice.actions;
export default progressSlice.reducer;