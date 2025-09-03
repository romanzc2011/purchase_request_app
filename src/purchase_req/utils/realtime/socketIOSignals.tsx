import { effect, signal } from "@preact/signals-react";
import { Socket, io } from "socket.io-client";
import { isApprovalSig, isDownloadSig, isRequestSubmitted, isSubmittedSig, messageSig } from "../PrasSignals";
import { Id, toast } from "react-toastify";
import { ProgressToast } from "../../components/ProgressToast";
import { useRef } from "react";

/* Using SocketIO to have full duplex comms b/w frontend and backend
    start the progress tracking via event START_TOAST
*/

export const socketioInstance: Socket = io("", { path: "/realtime/communicate" });

export const isIOConnectedSig = signal<boolean>(false);
export const transportSig = signal<string>(socketioInstance.io.engine.transport.name);
const toastIdRef = useRef<Id | null>(null);


const handleReset = () => {
    isIOConnectedSig.value = socketioInstance.connected;
    isIOConnectedSig.value = true;
    isDownloadSig.value = false;
    isSubmittedSig.value = false;
    isRequestSubmitted.value = false;
    isApprovalSig.value = false;
    if (toastIdRef.current !== null) {
        toast.dismiss(toastIdRef.current);
    }
};

// Config status message for toast messages
effect(() => {
    if (isDownloadSig.value) {
        messageSig.value = "Downloading PDF";

    } else if (isRequestSubmitted.value) {
        messageSig.value = "Submitting request";

    } else if (isApprovalSig.value) {
        messageSig.value = "Approval request processing";
    }
})

// --- CONNECTION LIFECYCLE --- //
// -----------------------------------------------------------------------
// CONNECT
// -----------------------------------------------------------------------
socketioInstance.on("connect", () => {
    isIOConnectedSig.value = true;
    transportSig.value = socketioInstance.io.engine.transport.name;
});

// -----------------------------------------------------------------------
// UPGRADE
// -----------------------------------------------------------------------
socketioInstance.io.engine.on("upgrade", (t: any) => {
    transportSig.value = t.name;
});

// -----------------------------------------------------------------------
// DISCONNECT
// -----------------------------------------------------------------------
socketioInstance.on("disconnect", () => {
    isIOConnectedSig.value = false;
});

// -----------------------------------------------------------------------
// CONNECT ERROR
// -----------------------------------------------------------------------
socketioInstance.on("connect_error", () => {
    isIOConnectedSig.value = false;
});

// -----------------------------------------------------------------------
// SERVER EVENTS
// -----------------------------------------------------------------------
socketioInstance.on("START_TOAST", (payload: { percent_complete: number }) => {
    toastIdRef.current = toast.loading(
        <ProgressToast percent={payload.percent_complete} message={messageSig.value} />,
        { position: "top-center", autoClose: false }
    );
});

// -----------------------------------------------------------------------
// PROGRESS UPDATE
// -----------------------------------------------------------------------
socketioInstance.on("PROGRESS_UPDATE", (payload: { percent_complete: number }) => {
    const percent = payload.percent_complete ?? 0;

    if ((isDownloadSig.value || isRequestSubmitted.value || isApprovalSig.value) && percent != null) {
        console.log("PROGRESS UPDATE SECTION");

        // Update progress bar
        if (toastIdRef.current === null) {
            toastIdRef.current = toast.loading(
                <ProgressToast percent={payload.percent_complete} message={messageSig.value} />,
                { position: "top-center", autoClose: false }
            );
        } else {
            toast.update(toastIdRef.current, {
                render: <ProgressToast percent={payload.percent_complete} message={messageSig.value} />,
                type: percent === 100 ? "success" : "info",
                isLoading: percent !== 100,
                autoClose: percent === 100 ? 1000 : false,
                position: "top-center",
            });
        }

        // Reset signals after completion
        if (percent === 100) {
            handleReset();
        }
    }
});

// -----------------------------------------------------------------------
// NO USER FOUND
// -----------------------------------------------------------------------
socketioInstance.on("NO_USER_FOUND", (payload: { message: string }) => {
    toast.error(payload.message);
});

// -----------------------------------------------------------------------
// USER FOUND
// -----------------------------------------------------------------------
socketioInstance.on("USER_FOUND", (payload: { message: string }) => {
    toast.success(payload.message);
});

// -----------------------------------------------------------------------
// SIGNAL RESET
// -----------------------------------------------------------------------
socketioInstance.on("SIGNAL_RESET", (payload: { message: string }) => {
    toast.success(payload.message);
    handleReset();
});