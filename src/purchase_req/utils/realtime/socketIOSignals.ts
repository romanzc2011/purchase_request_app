import { signal } from "@preact/signals-react";
import { isApprovalSig, isDownloadSig, isRequestSubmitted, isSubmittedSig } from "../PrasSignals";
import { toast } from "react-toastify";
import { toastIdSignal } from "../PrasSignals";
import { Socket, io } from "socket.io-client";

const socket = io({ path: "/realtime/communicate" });

export const isIOConnectedSig   = signal<boolean>(false);
export const transportSig = signal<string>(socket.io.engine.transport.name);
export const socketSig = signal<Socket | null>(socket);

export function socketEmit(event: string, data: any) {
    socket.emit(event, data);
}

const handleOpen = () => {
    console.log("✅ WebSocket connected");
    isIOConnectedSig.value = true;
    // Reset signals when reconnecting
    isDownloadSig.value = false;
    isSubmittedSig.value = false;
    isRequestSubmitted.value = false;
    isApprovalSig.value = false
    if (toastIdSignal.value !== null) {
        toast.dismiss(toastIdSignal.value);
    }
};
// ----------------------------------------------------------
// SOCKET EVENTS
// ----------------------------------------------------------

// CONNECT
socket.on("connect", () => {
    console.log("🔌 connected with id: ", socket.id);
    console.log("🔌 connected: ", socket.connected);
    console.log("🔌 transport: ", socket.io.engine.transport.name);
});

// CONNECT ERROR
socket.on("connect_error", (error) => {
    console.log("🔌 connect error: ", error);
    handleOpen();
});

socket.on("reset_data", () => {
    
})

// DISCONNECT
socket.on("disconnect", () => {
    console.log("🔌 disconnected");
});

// ERROR
socket.on("error", (error) => {
    console.log("🔌 error: ", error);
});