import { useEffect, useRef, useState } from "react";
import { toast, Id } from "react-toastify";
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '../../store/prasStore';
import { startTest, completeProgress, resetProgress } from '../../store/progressSlice';
import { isDownloadSig, socketSig, isSubmittedSig, messageSig, isRequestSubmitted, userFoundSig, isApprovalSig, reset_signals } from "./PrasSignals";
import { effect } from "@preact/signals-react";
import { ProgressToast } from "../components/ProgressToast";

// #########################################################################################
// PROGRESS BAR COMPONENT
// #########################################################################################
export function ProgressBar() {
    const toastIdRef = useRef<Id | null>(null);
    const dispatch = useDispatch<AppDispatch>();
    const status = useSelector((s: RootState) => (s as any).progress.status);
    const [lastHeartbeat, setLastHeartbeat] = useState<number>(Date.now());
    const [isConnected, setIsConnected] = useState(false);
    let socketSignal = socketSig.value;

    console.log("IS SUBMITTED SIG: ", isSubmittedSig.value);

    // Subscribe to the status to send reset message on complete
    useEffect(() => {
        if (status === 'done' && socketSignal) {
            socketSignal.send(JSON.stringify({ event: 'reset_data' }));
            dispatch(resetProgress());

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

        if (isRequestSubmitted.value) {
            messageSig.value = "Submitting request";
        }

        if (isApprovalSig.value) {
            messageSig.value = "Approval request processing";
        }
    });

    // Handle connection status changes
    useEffect(() => {
        if (socketSignal) {
            console.log("✅ WebSocket connected in ProgressBar");
            setIsConnected(true);
            // Reset signals when reconnecting
            isDownloadSig.value = false;
            isSubmittedSig.value = false;
            isRequestSubmitted.value = false;
            isApprovalSig.value = false;
            if (toastIdRef.current !== null) {
                toast.dismiss(toastIdRef.current);
            }
        }
    }, [socketSignal]);

    console.log("45: isRequestSubmitted: ", isRequestSubmitted.value);
    // Listen for WebSocket messages and update progress
    useEffect(() => {
        if (!socketSignal) return;

        // Create a custom event listener that will be triggered by App.tsx
        const handleProgressMessage = (event: CustomEvent) => {
            try {
                const data = event.detail;

                // Handle heartbeat
                if (data.event === "heartbeat") {
                    setLastHeartbeat(Date.now());
                    return;
                }

                dispatch(startTest());

                const percent = data.percent_complete;
                console.log("PERCENT: ", percent);

                // START TOAST
                if (data.event === "START_TOAST") {
                    toastIdRef.current = toast.loading(
                        <ProgressToast percent={0} message={messageSig.value} />,
                        { position: "top-center", autoClose: false }
                    );
                    return;
                }

                console.log("DATE.EVENT: ", data.event);
                console.log("Download sig: ", isDownloadSig.value);
                console.log("Submitted Sig: ", isSubmittedSig.value);
                console.log("Approval request: ", isApprovalSig.value);
                console.log("Percent: ", percent);
                console.log("isRequestSubmitted: ", isRequestSubmitted.value);

                // PROGRESS_UPDATE (for downloading pdf)
                if (data.event === "PROGRESS_UPDATE" && (isDownloadSig.value || isRequestSubmitted.value || isApprovalSig.value) && percent != null) {
                    // create toast if needed
                    console.log("PROGRESS UPDATE SECTION");
                    if (toastIdRef.current === null) {
                        toastIdRef.current = toast.loading(
                            <ProgressToast percent={percent} message={messageSig.value} />,
                            { position: "top-center", autoClose: false }
                        );
                    } else {
                        toast.update(toastIdRef.current, {
                            render: <ProgressToast percent={percent} message={messageSig.value} />,
                            isLoading: percent < 100,
                            autoClose: percent === 100 ? 1000 : false,
                            position: "top-center",
                            type: percent === 100 ? "success" : undefined,
                        });
                        console.log("TOAST.UPDATE ", percent);
                    }

                    // optionally dispatch "done" after the bar finishes its transition
                    if (percent === 100) {
                        setTimeout(() => {
                            dispatch(completeProgress());
                            isDownloadSig.value = false; // Reset the signal when done
                            isSubmittedSig.value = false;
                            isRequestSubmitted.value = false;
                            isApprovalSig.value = false;
                        }, 1000);
                    }
                } else if (data.event === "NO_USER_FOUND") {
                    toast.error(data.message);
                    userFoundSig.value = false;

                } else if (data.event === "USER_FOUND") {
                    userFoundSig.value = true;

                } else if (data.event == "SIGNAL_RESET") {
                    console.log(data.event);
                    console.log("SIGNAL RESET");
                    reset_signals();
                    //dispatch(resetProgress());

                    if (toastIdRef.current !== null) {
                        toast.dismiss(toastIdRef.current);
                    }

                }
            } catch (error) {
                console.error("Error parsing WebSocket message:", error);
            }
        };

        // Listen for custom progress events
        window.addEventListener('progress-message', handleProgressMessage as EventListener);
        return () => window.removeEventListener('progress-message', handleProgressMessage as EventListener);
    }, [socketSignal, dispatch]);

    // Check for stale connection (no heartbeat for 2 minutes)
    useEffect(() => {
        const checkConnection = () => {
            const now = Date.now();
            if (now - lastHeartbeat > 120000 && isConnected) { // 2 minutes
                console.log("⚠️ No heartbeat received for 2 minutes, connection may be stale");
            }
        };

        const interval = setInterval(checkConnection, 30000); // Check every 30 seconds
        return () => clearInterval(interval);
    }, [lastHeartbeat, isConnected]);

    return null;
}