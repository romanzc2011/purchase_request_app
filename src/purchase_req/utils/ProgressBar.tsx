import { useEffect, useRef, useState } from "react";
import { toast, Id } from "react-toastify";
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '../../store/prasStore';
import { startTest, completeProgress, resetProgress } from '../../store/progressSlice';
import { isDownloadSig, socketSig, isSubmittedSig, messageSig } from "./PrasSignals";
import { effect } from "@preact/signals-react";
import { LinearProgress, Typography } from "@mui/material";

// #########################################################################################
// PROGRESS BAR COMPONENT
// #########################################################################################
export function ProgressBar() {
	const toastIdRef = useRef<Id | null>(null);
	const dispatch = useDispatch<AppDispatch>();
	const status = useSelector((s: RootState) => s.progress.status);
	const [currentPercent, setCurrentPercent] = useState(0);
	let socketSignal = socketSig.value;

	// Subscribe to the status to send reset message on complete
	useEffect(() => {
		if (status === 'done' && socketSignal) {
			socketSignal.send(JSON.stringify({ event: 'reset_data' }));
			dispatch(resetProgress());
			setCurrentPercent(0);

			if (toastIdRef.current !== null) {
				toast.dismiss(toastIdRef.current);
			}
		}
	}, [status, socketSignal, dispatch])

	// Capture signal trigger and change
	effect(() => {
		if (isDownloadSig.value) {
			messageSig.value = "Downloading PDF";
		}

		if (isSubmittedSig.value) {
			messageSig.value = "Submitting request";
		}
	})

	// Listen for WebSocket messages and update progress
	useEffect(() => {
		if (!socketSignal) return;

		const handleMessage = (event: MessageEvent) => {
			try {
				dispatch(startTest());

				const eventData = JSON.parse(event.data);

				if (eventData.event === "PROGRESS_UPDATE") {
					console.log(eventData);
					let percent = eventData.percent_complete;
					setCurrentPercent(percent);
				}

				// Handle START_TOAST message
				if (eventData.event === "START_TOAST") {
					console.log(eventData);
					toastIdRef.current = toast.loading(
						<div style={{ width: "100%" }}>
							<Typography variant="body2">
								{`${messageSig.value}... (0%)`}
							</Typography>
							<LinearProgress
								variant="determinate"
								value={0}
								sx={{ height: 4, borderRadius: 2, marginTop: 1 }}
							/>
						</div>,
						{
							position: "top-center",
							autoClose: false
						}

					);
					return;
				}

				// Handle progress updates
				if (eventData.percent_complete !== undefined) {
					let percent = eventData.percent_complete;

					// Send message back if done (100%)
					if (eventData.percent_complete == 100) {
						dispatch(completeProgress());
					}

					setCurrentPercent(percent);
					if (toastIdRef.current) {
						for (let i = currentPercent; i <= percent; i++) {
							toast.update(toastIdRef.current, {
								render: (
									<div style={{ width: "100%" }}>
										<Typography variant="body2">
											{`${messageSig.value}... (${i}%)`}
										</Typography>
										<LinearProgress
											variant="determinate"
											value={i}
											sx={{ height: 4, borderRadius: 2, marginTop: 1 }}
										/>
									</div>
								),
								isLoading: percent < 100,
								autoClose: percent === 100 ? 1000 : false,
								type: percent === 100 ? "success" : undefined,
							});
						}

					}
				}
			} catch (error) {
				console.error("Error parsing WebSocket message:", error);
			}
		};

		socketSignal.addEventListener('message', handleMessage);
		return () => socketSignal.removeEventListener('message', handleMessage);
	}, [socketSignal, dispatch]);

	return null;
}