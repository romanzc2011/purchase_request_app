import { useEffect, useRef, useState } from "react";
import { toast, Id } from "react-toastify";
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '../../store/prasStore';
import { startTest, completeProgress, resetProgress } from '../../store/progressSlice';
import { isDownloadSig, socketSig, isSubmittedSig, messageSig, isRequestSubmitted } from "./PrasSignals";
import { effect } from "@preact/signals-react";
import { LinearProgress, Typography } from "@mui/material";
import { ProgressToast } from "../components/ProgressToast";

// #########################################################################################
// PROGRESS BAR COMPONENT
// #########################################################################################
export function ProgressBar() {
    const toastIdRef = useRef<Id | null>(null);
    const dispatch = useDispatch<AppDispatch>();
    const status = useSelector((s: RootState) => s.progress.status);
    const [currentPercent, setCurrentPercent] = useState(0);
    let socketSignal = socketSig.value;

    console.log("IS SUBMITTED SIG: ", isSubmittedSig.value);

    // Subscribe to the status to send reset message on complete
    useEffect(() => {
        if (status === 'done' && socketSignal) {
            socketSignal.send(JSON.stringify({ event: 'reset_data' }));
            dispatch(resetProgress());
            setCurrentPercent(0);

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
    });

    console.log("45: isRequestSubmitted: ", isRequestSubmitted.value);
    // Listen for WebSocket messages and update progress
    useEffect(() => {
        if (!socketSignal) return;

        const handleMessage = (event: MessageEvent) => {
            try {
                dispatch(startTest());

                const data = JSON.parse(event.data);
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
                console.log("Percent: ", percent);
                console.log("isRequestSubmitted: ", isRequestSubmitted.value);

                // PROGRESS_UPDATE (for downloading pdf)
                if (data.event === "PROGRESS_UPDATE" && (isDownloadSig.value || isRequestSubmitted.value) && percent != null) {
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
                    }

                    // optionally dispatch "done" after the bar finishes its transition
                    if (percent === 100) {
                        setTimeout(() => {
                            dispatch(completeProgress());
                            isDownloadSig.value = false; // Reset the signal when done
                            isSubmittedSig.value = false;
                            isRequestSubmitted.value = false;
                        }, 1000);
                    }
                }
            } catch (error) {
                console.error("Error parsing WebSocket message:", error);
            }
        };


        socketSignal.addEventListener('message', handleMessage);
        return () => socketSignal.removeEventListener('message', handleMessage);
    }, [socketSignal, dispatch]);

    return null;
}