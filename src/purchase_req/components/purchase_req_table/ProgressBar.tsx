import { useEffect, useRef } from "react";
import { toast, Id } from "react-toastify";
import { useDispatch } from 'react-redux';
import { AppDispatch } from '../../../store/prasStore';
import { startTest, startProgress, setPercent, completeProgress } from '../../../store/progressSlice';
import { wrap } from "module";

interface ProgressBarProps {
	isFinalSubmission: boolean;
	socket: WebSocket;
}

const STEPS = [
	"id_generated",
	"pr_headers_inserted",
	"line_items_inserted",
	"generate_pdf",
	"send_approver_email",
	"send_requester_email"
];

const showProgressToast = (message: string, progress: number): Id => {
	return toast.loading(
		<div>
			<div>{message}</div>
			<div style={{ width: '100%', backgroundColor: '#ddd', borderRadius: '4px', marginTop: '8px' }}>
				<div
					style={{
						width: `${progress}%`,
						height: '4px',
						backgroundColor: '#4caf50',
						borderRadius: '4px',
						transition: 'width 0.3s ease'
					}}
				/>
			</div>
		</div>,
		{
			position: "top-center",
			autoClose: false
		}
	);
};
// #########################################################################################
// PROGRESS BAR COMPONENT
// #########################################################################################
export function ProgressBar({ isFinalSubmission, socket }: ProgressBarProps) {
	const toastIdRef = useRef<Id | null>(null);
	const dispatch = useDispatch<AppDispatch>();

	// Show initial toast when submission starts
	useEffect(() => {
		if (!isFinalSubmission) return;

		// Create initial toast
		toastIdRef.current = toast.loading(
			<div>
				<div>Submitting request... (0%)</div>
				<div style={{ width: '100%', backgroundColor: '#ddd', borderRadius: '4px', marginTop: '8px' }}>
					<div
						style={{
							width: `0%`,
							height: '4px',
							backgroundColor: '#4caf50',
							borderRadius: '4px',
							transition: 'width 0.3s ease'
						}}
					/>
				</div>
			</div>,
			{
				position: "top-center",
				autoClose: false
			}
		);
	}, [isFinalSubmission]);

	// Listen for WebSocket messages and update progress
	useEffect(() => {
		console.log("ProgressBar useEffect", { socket, isFinalSubmission });
		if (!socket) return;

		const handleMessage = (event: MessageEvent) => {
			try {
				console.log("🔔 WS message arrived:", event.data);
				dispatch(startTest());
				const progressData = JSON.parse(event.data);
				console.log("Progress update received: ", progressData);
				console.log("progressData datatype: ", typeof (progressData));
				console.log("event.data type", typeof (event.data))
				console.log("let me see just the event: ", event)
				console.log("Type of event: ", typeof (event));

				// Check if this is a progress update message
				console.log("Checking percent_complete:", progressData.percent_complete);
				if (progressData.percent_complete !== undefined) {
					const percent = Math.floor(progressData.percent_complete);
					console.log("Calculated percent:", percent);
					console.log("toastIdRef.current:", toastIdRef.current);

					if (toastIdRef.current) {
						toast.update(toastIdRef.current, {
							render: (
								<div>
									<div>Submitting request... ({percent}%)</div>
									<div style={{ width: '100%', backgroundColor: '#ddd', borderRadius: '4px', marginTop: '8px' }}>
										<div
											style={{
												width: `${percent}%`,
												height: '4px',
												backgroundColor: '#4caf50',
												borderRadius: '4px',
												transition: 'width 0.3s ease'
											}}
										/>
									</div>
								</div>
							),
							isLoading: percent < 100,
							autoClose: percent === 100 ? 3000 : false,
							type: percent === 100 ? "success" : undefined,
						});
					}
				}
			} catch (error) {
				console.error("Error parsing WebSocket message:", error);
			}
		};

		socket.addEventListener('message', handleMessage);
		return () => socket.removeEventListener('message', handleMessage);
	}, [socket, isFinalSubmission, dispatch]);

	return null;
}