import { useEffect, useRef } from "react";
import { toast, Id } from "react-toastify";
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '../../../store/prasStore';
import { startTest, startProgress, setPercent, completeProgress, resetProgress } from '../../../store/progressSlice';

interface ProgressBarProps {
	isFinalSubmission: boolean;
	socket: WebSocket;
}

const STEPS = [
	"id_generated",
	"pr_headers_inserted",
	"pdf_generated",
	"line_items_inserted",
	"generate_pdf",
	"send_approver_email",
	"send_requester_email",
	"email_sent_requester",
	"email_sent_approver",
	"pending_approval_inserted"
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
	const status = useSelector((s: RootState) => s.progress.status);

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

	// Subscribe to the status to send reset message on complete
	useEffect(() => {
		if (status === 'done' && socket) {
			console.log("EVENT: DONE COMPLETE");
			socket.send(JSON.stringify({ event: 'reset_data' }));
			dispatch(resetProgress());
		}
	}, [status, socket, dispatch])

	// Listen for WebSocket messages and update progress
	useEffect(() => {
		console.log("ProgressBar useEffect", { socket, isFinalSubmission });
		if (!socket) return;


		const handleMessage = (event: MessageEvent) => {
			try {
				dispatch(startTest());
				const eventData = JSON.parse(event.data);
				console.log("🔔 WS message arrived: ", eventData);
				console.log("EVENT DATA: ", eventData.event);
				console.log("PERCENT_COMPLETE", eventData.percent_complete)

				if (eventData.percent_complete !== undefined) {
					let percent = eventData.percent_complete;
					console.log("Calculated percent:", percent);
					console.log("toastIdRef.current:", toastIdRef.current);

					// Send message back if done (100%)
					if (eventData.percent_complete == 100) {
						dispatch(completeProgress());
					}

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