import { effect, signal } from "@preact/signals-react";
import { Socket, io } from "socket.io-client";
import { Id, toast } from "react-toastify";
import { ProgressToast } from "../../components/ProgressToast";
import {
    isApprovalSig,
    isDownloadSig,
    isRequestSubmitted,
    isSubmittedSig,
    messageSig,
} from "../PrasSignals";

// Create and export a single socket instance you use everywhere
export const socketioInstance: Socket = io(window.location.origin, {
    path: "/progress_bar_bridge/communicate",
    transports: ["polling"],
    auth: (cb) => {
        const token = localStorage.getItem("access_token");
        cb({ token });
    },
    autoConnect: false, // Don't connect automatically
});

export const isIOConnectedSig = signal<boolean>(false);
export const transportSig = signal<string>("disconnected");

// Function to connect SocketIO after login
export function connectSocketIO() {
    console.log("🔌 Connecting SocketIO...");
    socketioInstance.connect();
}

// Call this ONCE at app startup
export function setupSocketProgressBridge() {
    // HMR guard (prevents duplicate listeners during dev hot reload)
    console.log("Setting up socket progress bridge");
    if (typeof window !== "undefined") {
        const w = window as any;
        if (w.__PRAS_BRIDGE_INIT__) return () => { };
        w.__PRAS_BRIDGE_INIT__ = true;
    }

    let toastId: Id | null = null;

    const handleReset = () => {
        isIOConnectedSig.value = socketioInstance.connected;
        // (your next line set it to true again; keep the one you intend)
        isDownloadSig.value = false;
        isSubmittedSig.value = false;
        isRequestSubmitted.value = false;
        isApprovalSig.value = false;
        if (toastId !== null) {
            toast.dismiss(toastId);
            toastId = null;
        }
    };

    // Config status message for toast messages
    const stopEffect = effect(() => {
        if (isDownloadSig.value) {
            messageSig.value = "Downloading PDF";
        } else if (isRequestSubmitted.value) {
            messageSig.value = "Submitting request";
        } else if (isApprovalSig.value) {
            messageSig.value = "Approval request processing";
        }
    });

    // --- CONNECTION LIFECYCLE ---
    const onConnect = () => {
        console.log("🔌 SocketIO connected successfully!");
        isIOConnectedSig.value = true;
        transportSig.value = socketioInstance.io.engine?.transport?.name || "connected";
    };

    const onUpgrade = (t: any) => {
        transportSig.value = t.name;
    };

    const onDisconnect = () => {
        isIOConnectedSig.value = false;
    };

    const onConnectError = (error: any) => {
        console.error("🔌 SocketIO connection error:", error);
        isIOConnectedSig.value = false;
    };

    // --- SERVER EVENTS ---
    // Starting Toast which is the progress bar to keep up with progress
    const onStartToast = (payload: { percent_complete: number }) => {
        toastId = toast.loading(
            <ProgressToast
                percent={payload.percent_complete ?? 0}
                message={messageSig.value}
            />,
            { position: "top-center", autoClose: false }
        );
    };

    /****************************************************************************************/
    /* PROGRESS BAR */
    /****************************************************************************************/
    const onProgressUpdate = (payload: { percent_complete: number }) => {
        const percent = payload.percent_complete ?? 0;

        if ((isDownloadSig.value || isRequestSubmitted.value || isApprovalSig.value) && percent != null) {
            if (toastId === null) {
                toastId = toast.loading(
                    <ProgressToast percent={percent} message={messageSig.value} />,
                    { position: "top-center", autoClose: false }
                );
            } else {
                toast.update(toastId, {
                    render: <ProgressToast percent={percent} message={messageSig.value} />,
                    type: percent === 100 ? "success" : "info",
                    isLoading: percent !== 100,
                    autoClose: percent === 100 ? 2000 : false,
                    position: "top-center",
                });
            }

            if (percent === 100) {
                handleReset();
            }
        }
    };

    /****************************************************************************************/
    /* CONNECTION TIMEOUT */
    /****************************************************************************************/
    const onConnectionTimeout = (payload: { message: string }) => {
        toast.error(payload.message);
    };

    const onNoUserFound = (payload: { message: string }) => {
        console.log("❌ NO_USER_FOUND event received:", payload);
        toast.error(payload.message);
    };

    const onMessageEvent = (payload: { message: string }) => {
        toast.success(payload.message);
    }

    const onUserFound = (payload: { message: string }) => {
        console.log("🎉 USER_FOUND event received:", payload);
        toast.success(payload.message);
    };

    const onSignalReset = (payload: { message: string }) => {
        toast.success(payload.message);
        handleReset();
    };

    const onError = (payload: { message: string }) => {
        console.log("🚨 ERROR received:", payload);
        toast.error(payload.message);
    };

    const onSendOriginalPrice = (payload: { message: number }) => {
        console.log("💰 ORIGINAL PRICE received:", payload);
        // This will be handled by the DataGrid's processRowUpdate error handling
        // The original price will be restored when the update fails
    };

    // ---- register listeners ONCE ----
    socketioInstance.on("connect", onConnect);
    socketioInstance.io.engine.on("upgrade", onUpgrade);
    socketioInstance.on("disconnect", onDisconnect);
    socketioInstance.on("connect_error", onConnectError);
    socketioInstance.on("START_TOAST", onStartToast);
    socketioInstance.on("PROGRESS_UPDATE", onProgressUpdate);
    socketioInstance.on("CONNECTION_TIMEOUT", onConnectionTimeout);
    socketioInstance.on("NO_USER_FOUND", onNoUserFound);
    socketioInstance.on("MESSAGE_EVENT", onMessageEvent);
    socketioInstance.on("USER_FOUND", onUserFound);
    socketioInstance.on("SIGNAL_RESET", onSignalReset);
    socketioInstance.on("ERROR_EVENT", onError);  // Fixed: Listen for ERROR_EVENT, not ERROR
    socketioInstance.on("SEND_ORGINAL_PRICE", onSendOriginalPrice);

    // Debug: Log all SocketIO events
    socketioInstance.onAny((eventName, ...args) => {
        console.log(`📡 SocketIO event received: ${eventName}`, args);
    });

    return () => {
        stopEffect();
        socketioInstance.off("connect", onConnect);
        socketioInstance.io.engine.off("upgrade", onUpgrade);
        socketioInstance.off("disconnect", onDisconnect);
        socketioInstance.off("connect_error", onConnectError);
        socketioInstance.off("START_TOAST", onStartToast);
        socketioInstance.off("PROGRESS_UPDATE", onProgressUpdate);
        socketioInstance.off("CONNECTION_TIMEOUT", onConnectionTimeout);
        socketioInstance.off("NO_USER_FOUND", onNoUserFound);
        socketioInstance.off("MESSAGE_EVENT", onMessageEvent);
        socketioInstance.off("USER_FOUND", onUserFound);
        socketioInstance.off("SIGNAL_RESET", onSignalReset);
        socketioInstance.off("ERROR_EVENT", onError);  // Fixed: Clean up ERROR_EVENT listener
        socketioInstance.off("SEND_ORGINAL_PRICE", onSendOriginalPrice);
    };
}
