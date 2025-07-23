import { configureStore } from "@reduxjs/toolkit";
import progressReducer from './progressSlice';

export const prasStore = configureStore({
	reducer: {
		progress: progressReducer
	}
});

export type RootState = ReturnType<typeof prasStore.getState>;
export type AppDispatch = typeof prasStore.dispatch;