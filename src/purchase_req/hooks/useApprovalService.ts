import { useState } from "react";
import { ApprovalData } from "../types/approvalTypes";
import { approveDenyRequest } from "../services/ApprovalService";

export function useApprovalService() {
    const [approvalPayload, setApprovalPayload] = useState<ApprovalData | null>(null);
    const [isLoadingApproval, setIsLoadingApproval] = useState(false);
    const [errorInApprove, setErrorInApprove] = useState<string | null>(null);
    /* The approvalPayload is used to store the payload that will be sent to the server
    The approval payload will be coming in from ApprovalTable as approvalPayload. We will then 
    process the data the same way we did with comments, we want the same behavior */

    // PROCESS PAYLOAD
    // This function is called when the user clicks on the approve/deny button
    // It takes the payload as an argument and sends it to the server
    // processPayload --> approveDenyRequest (ApprovalService.ts)
    const processPayload = async (payload: ApprovalData) => {
        console.log("🔥 APPROVAL PAYLOAD", payload);
    }

    return {
        processPayload,
        approvalPayload,
        setApprovalPayload,
    }
}