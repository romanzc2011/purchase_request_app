import { useEffect, useRef, useState } from "react";
import { toast, Id } from "react-toastify";
import { useDispatch, useSelector } from "react-redux";
import { AppDispatch, RootState } from "../../store/prasStore";
import { completeProgress, resetProgress } from "../../store/progressSlice";
import { isDownloadSig, isSubmittedSig, messageSig, isRequestSubmitted, userFoundSig, isApprovalSig, reset_signals } from "./PrasSignals";
import { effect as signalsEffect } from "@preact/signals-react";
import { ProgressToast } from "../components/ProgressToast";
import { webSocketService } from "../services/WebSocketService";

export function ProgressBar() {
    const toastIdRef = useRef<Id | null>(null);
    const dispatch = useDispatch<AppDispatch>();
    const status = useSelector((s: RootState) => (s as any).progress.status);

    const [isConnected, setIsConnected] = useState(false);
    const [lastHeartbeat, setLastHeartbeat] = useState<number>(Date.now());

    // One-time connect + subscriptions
    useEffect(() => {
        webSocketService.connect();

        // connection state
        const unsubOpen = webSocketService.subscribe("open", () => {
            setIsConnected(true);
            // optional reset when reconnecting
            isDownloadSig.value = false;
            isSubmittedSig.value = false;
            isRequestSubmitted.value = false;
            isApprovalSig.value = false;
            if (toastIdRef.current) toast.dismiss(toastIdRef.current);
        });
        const unsubClose = webSocketService.subscribe("close", () => setIsConnected(false));

        // keep last heartbeat fresh (use any server “heartbeat” or “connection_status” event)
        const unsubHeartbeat = webSocketService.subscribe("heartbeat", () => setLastHeartbeat(Date.now()));
        const unsubConnStatus = webSocketService.subscribe("connection_status", () => setLastHeartbeat(Date.now()));

        // toast progress
        const unsubProgress = webSocketService.subscribe("PROGRESS_UPDATE", (data) => {
            const percent = data?.percent_complete;
            if (percent == null) return;

            if (toastIdRef.current == null) {
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
            }

            if (percent === 100) {
                setTimeout(() => {
                    dispatch(completeProgress());
                    isDownloadSig.value = false;
                    isSubmittedSig.value = false;
                    isRequestSubmitted.value = false;
                    isApprovalSig.value = false;
                }, 1000);
            }
        });

        // other events
        const unsubStartToast = webSocketService.subscribe("START_TOAST", () => {
            toastIdRef.current = toast.loading(<ProgressToast percent={0} message={messageSig.value} />, {
                position: "top-center",
                autoClose: false,
            });
        });

        const unsubNoUser = webSocketService.subscribe("NO_USER_FOUND", (d) => {
            toast.error(d.message);
            userFoundSig.value = false;
        });
        const unsubUser = webSocketService.subscribe("USER_FOUND", () => {
            userFoundSig.value = true;
        });
        const unsubReset = webSocketService.subscribe("SIGNAL_RESET", () => {
            reset_signals();
            if (toastIdRef.current) toast.dismiss(toastIdRef.current);
        });

        // optional client ping if your server isn’t sending WS pings
        const pingId = setInterval(() => webSocketService.send({ event: "ping" }), 25000);
        // initial “are we good?”
        webSocketService.send({ event: "check_connection" });

        return () => {
            clearInterval(pingId);
            unsubOpen(); unsubClose();
            unsubHeartbeat(); unsubConnStatus();
            unsubProgress(); unsubStartToast();
            unsubNoUser(); unsubUser(); unsubReset();
            webSocketService.disconnect(); // if ProgressBar is global, this is fine
        };
    }, [dispatch]);

    // Tie signals to the message text (create once, dispose on unmount)
    useEffect(() => {
        const disposeOrEffect = signalsEffect(() => {
            if (isDownloadSig.value) messageSig.value = "Downloading PDF";
            if (isRequestSubmitted.value) messageSig.value = "Submitting request";
            if (isApprovalSig.value) messageSig.value = "Approval request processing";
        });
        // Some versions return a disposer function, others an object with .dispose()
        return () => {
            if (typeof disposeOrEffect === "function") disposeOrEffect();
            else (disposeOrEffect as any)?.dispose?.();
        };
    }, []);

    // When Redux says “done”, tell server to reset & clear toast
    useEffect(() => {
        if (status === "done" && isConnected) {
            webSocketService.send({ event: "reset_data" });
            dispatch(resetProgress());
            if (toastIdRef.current) toast.dismiss(toastIdRef.current);
        }
    }, [status, isConnected, dispatch]);

    // Stale-connection watcher (if you care)
    useEffect(() => {
        const id = setInterval(() => {
            if (isConnected && Date.now() - lastHeartbeat > 120_000) {
                console.warn("⚠️ No heartbeat for 2 minutes; connection may be stale");
            }
        }, 30_000);
        return () => clearInterval(id);
    }, [isConnected, lastHeartbeat]);

    return null;
}
