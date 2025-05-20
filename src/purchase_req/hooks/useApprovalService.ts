import { useState } from "react";
import { ApprovalData } from "../types/approvalTypes";
import { approveDenyRequest } from "../services/ApprovalService";

export function useApprovalService() {
    const [approvalPayload, setApprovalPayload] = useState<ApprovalData | null>(null);
    const [isLoadingApproval, setIsLoadingApproval] = useState(false);
    const [errorInApprove, setErrorInApprove] = useState<string | null>(null);

    // TODO: Remove all approval functions from the ApprovalTable and move them to this hook
    /* The approvalPayload is used to store the payload that will be sent to the server
    The approval payload will be coming in from ApprovalTable as approvalPayload. We will then 
    process the data the same way we did with comments, we want the same behavior */

    // PROCESS PAYLOAD
    // This function is called when the user clicks on the approve/deny button
    // It takes the payload as an argument and sends it to the server
    // processPayload --> approveDenyRequest (ApprovalService.ts)
    const processPayload = async (payload: ApprovalData) => {
        console.log("🔥 processPayload fired with:", payload);
        process.exit(0); // TEST
        // Storing the payload before sending to the server
        // try {
        //     setIsLoadingApproval(true);
        //     const response = await approveDenyRequest(payload);
        //     console.log("🔥 APPROVE/PAYLOAD RESPONSE", response);
        //     return response;
        // } catch (error) {
        //     console.error("🔥 APPROVE/DENY ERROR", error);
        //     setErrorInApprove(error instanceof Error ? error.message : "An unknown error occurred");
        //     throw error;
        // } finally {
        //     setIsLoadingApproval(false);
        // }
    }

    return {
        processPayload,
        approvalPayload,
        isLoadingApproval,
        setIsLoadingApproval,
        errorInApprove,
        setApprovalPayload,
        setErrorInApprove,

    }
}