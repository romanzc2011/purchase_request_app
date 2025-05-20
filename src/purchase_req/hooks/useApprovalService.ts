import { useState } from "react";
import { ApprovalData } from "../types/approvalTypes";
import { approveDenyRequest } from "../services/ApprovalService";

export function useApprovalService() {
    const [approvalPayload, setApprovalPayload] = useState<ApprovalData | null>(null);

    const approveDeny = async (payload: ApprovalData) => {
        try {
            const response = await approveDenyRequest(payload);
            console.log("🔥 APPROVE/DENY RESPONSE", response);
        } catch (error) {
            console.error("🔥 APPROVE/DENY ERROR", error);
        }
    }

    return {
        approveDeny
    }
}