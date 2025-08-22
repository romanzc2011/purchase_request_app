import { useEffect, useRef, useState } from "react";
import { toast, Id } from "react-toastify";
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '../../store/prasStore';
import { startTest, completeProgress, resetProgress } from '../../store/progressSlice';
import { isDownloadSig, socketSig, isSubmittedSig, messageSig, isRequestSubmitted, userFoundSig, isApprovalSig, reset_signals } from "./PrasSignals";
import { effect } from "@preact/signals-react";
import { ProgressToast } from "../components/ProgressToast";
import { webSocketService } from "../services/WebSocketService";
import { computeWSURL } from "./ws";

// #########################################################################################
// PROGRESS BAR COMPONENT
// #########################################################################################

const handleMessage = (event: MessageEvent, dispatch: AppDispatch, toastIdRef: React.MutableRefObject<Id | null>) => {
    try {
        const data = JSON.parse(event.data);
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
export function ProgressBar() {
    const toastIdRef = useRef<Id | null>(null);
    const dispatch = useDispatch<AppDispatch>();
    const status = useSelector((s: RootState) => (s as any).progress.status);
    const [lastHeartbeat, setLastHeartbeat] = useState<number>(Date.now());
    const [isConnected, setIsConnected] = useState(false);
    let socketSignal = socketSig.value;

    console.log("IS SUBMITTED SIG: ", isSubmittedSig.value);

    // Create WebSocket connection and assign to signal
    useEffect(() => {
        // Create the WebSocket connection));
        webSocketService.connect();
        webSocketService.send("hello from client");

        // // Fires when connection to websocket server is established
        // socket.onopen = (event) => {
        //     console.log("✅ WebSocket connected:", event);
        //     socket.send("Hello from client");
        // };

        // // Fires when a message is received from the websocket server
        // socket.onmessage = (event) => {
        //     console.log(`Received message: ${event.data}`);
        // };

        // // Fires when connection to server is closed
        // socket.onclose = (event) => {
        //     if (event.wasClean) {
        //         console.log(`Connection closed cleanly: code=${event.code}, reason=${event.reason}`);
        //     } else {
        //         console.error(`CONNECTION DIED UNEXPECTEDLY: code=${event.code}, reason=${event.reason}`);
        //     }
        //     // Clear the signal when connection closes
        //     socketSig.value = undefined;
        // };

        // // Fires when there's an error
        // socket.onerror = (error) => {
        //     console.error("WEBSOCKET ERROR: ", error);
        // }

        // // Cleanup function
        // return () => {
        //     if (socket.readyState === WebSocket.OPEN) {
        //         socket.close();
        //     }
        //     socketSig.value = undefined;
        // };
    }, []); // Empty dependency array - only run once on mount

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
    // useEffect(() => {
    //     if (socketSignal) {
    //         const handleOpen = () => {
    //             console.log("✅ WebSocket connected");
    //             setIsConnected(true);
    //             // Reset signals when reconnecting
    //             isDownloadSig.value = false;
    //             isSubmittedSig.value = false;
    //             isRequestSubmitted.value = false;
    //             isApprovalSig.value = false
    //             if (toastIdRef.current !== null) {
    //                 toast.dismiss(toastIdRef.current);
    //             }
    //         };

    //         const handleClose = () => {
    //             console.log("❌ WebSocket disconnected");
    //             setIsConnected(false);
    //             // Clear any existing toasts when disconnected
    //             if (toastIdRef.current !== null) {
    //                 toast.dismiss(toastIdRef.current);
    //             }
    //         };

    //         return () => {
    //             socketSignal.removeEventListener('open', handleOpen);
    //             socketSignal.removeEventListener('close', handleClose);
    //         };
    //     }
    // }, [socketSignal]);

    console.log("45: isRequestSubmitted: ", isRequestSubmitted.value);
    // Listen for WebSocket messages and update progress
    useEffect(() => {
        if (!socketSignal) return;



    }, [socketSignal, dispatch]);

    return null;
}