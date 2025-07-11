import { useEffect, useRef, useState } from "react";
import { toast, Id } from "react-toastify";

interface ProgressBarProps {
	isFinalSubmission: boolean;
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

export function ProgressBar({ isFinalSubmission }: ProgressBarProps) {
	const toastIdRef = useRef<Id | null>(null);

	useEffect(() => {
		if (!isFinalSubmission) return;

		const ws = new WebSocket("ws://localhost:5002/communicate");
		console.log("Connected to websocket")

		ws.onopen = () => {
			console.log("✅ WebSocket connected");
			toastIdRef.current = showProgressToast("Submitting request...", 0);
		};

		ws.onmessage = function (event) {
			try {
				const progressData = JSON.parse(event.data);
				console.log("Progress update received: ", progressData);

				const totalSteps = STEPS.length;
				const completedSteps = STEPS.filter(step => progressData[step]).length;
				const percent = Math.floor((completedSteps / totalSteps) * 100);

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
					console.log("Updated toast")
					ws.send("This works")
				}
			} catch (error) {
				console.error("Error parsing WebSocket message:", error);
			}
		};

		ws.onerror = (error) => {
			console.error("❌ WebSocket error:", error);
		};

		ws.onclose = (event) => {
			console.log("❌ WebSocket disconnected:", event.code, event.reason);
		};

		return () => ws.close();
	}, [isFinalSubmission]);
	return null;
}

export default showProgressToast; 