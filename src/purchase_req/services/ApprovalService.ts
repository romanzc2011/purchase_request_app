import { ApprovalData } from "../types/approvalTypes";
import { useApprovalService } from "../hooks/useApprovalService";

const API_URL_APPROVE_DENY_REQUEST = `${import.meta.env.VITE_API_URL}/api/approveDenyRequest`

// ##############################################################
// Approve/Deny request
// ##############################################################
export async function approveDenyRequest(payload: ApprovalData) {
    const response = await fetch(API_URL_APPROVE_DENY_REQUEST, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });
    if (!response.ok) {
        throw new Error("Failed to approve/deny request");
    }
    console.log("🔥 APPROVE/DENY RESPONSE", response);
    return response.json();
}