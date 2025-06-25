import { ApprovalData, DenialData } from "../types/approvalTypes";

const API_URL_APPROVE_DENY_REQUEST = `${import.meta.env.VITE_API_URL}/api/approveDenyRequest`

// ##############################################################
// Approve/Deny request
// ##############################################################
export async function approveDenyRequest(payload: ApprovalData | DenialData): Promise<any> {
    const token = localStorage.getItem("access_token");
    if (!token) {
        throw new Error("No token found");
    }   

    const response = await fetch(API_URL_APPROVE_DENY_REQUEST, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
    });
    if (!response.ok) {
        throw new Error("Failed to approve/deny request");
    }
    return response.json();
}