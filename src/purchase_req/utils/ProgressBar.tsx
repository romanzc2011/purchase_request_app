import { useEffect, useRef, useState } from "react";
import { toast, Id } from "react-toastify";
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '../../store/prasStore';
import { startTest, completeProgress, resetProgress } from '../../store/progressSlice';
import { isDownloadSig, isSubmittedSig, messageSig, isRequestSubmitted, userFoundSig, isApprovalSig, reset_signals } from "./PrasSignals";
import { effect } from "@preact/signals-react";
import { ProgressToast } from "../components/ProgressToast";
import { computeAPIURL } from "./misc_utils";

// #########################################################################################
// PROGRESS BAR COMPONENT
// #########################################################################################
export function ProgressBar() {
    const toastIdRef = useRef<Id | null>(null);
    const dispatch = useDispatch<AppDispatch>();
    const status = useSelector((s: RootState) => (s as any).progress.status);
    const [lastHeartbeat, setLastHeartbeat] = useState<number>(Date.now());
    const [isConnected, setIsConnected] = useState(false);
    //let socketSignal = socketSig.value;
    const eventSource = new EventSource(computeAPIURL("/sse"), {
        withCredentials: true
    });

    eventSource.onopen = () => {
        console.log("✅ SSE OPENED");
    }

    eventSource.onmessage = (event) => {
        console.log("SERVER EVENT: ", event);
        console.log("EVENT.DATA: ", event.data)
    }

    eventSource.onerror = (event) => {
        console.log("❌ SSE ERROR: ", event);
        // event is of type Event, which does not have readyState.
        // Use eventSource.readyState instead.
        if (eventSource.readyState === EventSource.CLOSED) {
            console.log("SSE connection closed.");
            setIsConnected(false);
            if (toastIdRef.current !== null) {
                toast.dismiss(toastIdRef.current);
            }
        }
    }

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
        //if (socketSignal) {
        console.log(eventSource.readyState);

        if (eventSource.readyState === EventSource.OPEN) {
            console.log("READY TO RECEIVE MESSAGES");
        }
        const handleOpen = () => {
            console.log("✅ SSE RECEIVED");
            setIsConnected(true);
            // Reset signals when reconnecting
            isDownloadSig.value = false;
            isSubmittedSig.value = false;
            isRequestSubmitted.value = false;
            isApprovalSig.value = false
            if (toastIdRef.current !== null) {
                toast.dismiss(toastIdRef.current);
            }
        };

        const handleClose = () => {
            console.log("❌ WebSocket disconnected");
            setIsConnected(false);
            // Clear any existing toasts when disconnected
            if (toastIdRef.current !== null) {
                toast.dismiss(toastIdRef.current);
            }
        };

    }, []);

    console.log("45: isRequestSubmitted: ", isRequestSubmitted.value);
    // Listen for WebSocket messages and update progress
    useEffect(() => {
        //if (!socketSignal) return;

        const handleMessage = (event: MessageEvent) => {
            try {
                const data = JSON.parse(event.data);

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
                if (data.event === "PROGRESS_UPDATE" && (isDownloadSig.value || isRequestSubmitted.value || isRequestSubmitted.value || isApprovalSig) && percent != null) {
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

        // socketSignal.addEventListener('message', handleMessage);
        // return () => socketSignal.removeEventListener('message', handleMessage);
    }, []);

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