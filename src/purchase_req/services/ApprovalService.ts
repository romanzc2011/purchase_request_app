import { ApprovalData, DenialData } from "../types/approvalTypes";

const API_URL_APPROVE_REQUEST = `${import.meta.env.VITE_API_URL}/api/approveRequest`
const API_URL_DENY_REQUEST = `${import.meta.env.VITE_API_URL}/api/denyRequest`

// ##############################################################
// Approve/Deny request
// ##############################################################
export async function approveDenyRequest(payload: ApprovalData | DenialData): Promise<any> {
    const token = localStorage.getItem("access_token");
    if (!token) {
        throw new Error("No token found");
    }   

    // Determine which endpoint to use based on action
    const isDeny = payload.action === "DENY" || payload.action === "deny";
    const url = isDeny ? API_URL_DENY_REQUEST : API_URL_APPROVE_REQUEST;
    
    // Format payload for the correct endpoint
    let formattedPayload;
    if (isDeny) {
        // For deny endpoint, use DenyPayload format
        formattedPayload = {
            ID: payload.ID,
            item_uuids: payload.item_uuids,
            target_status: payload.target_status, // Keep as array since backend now expects it
            action: payload.action
        };
    } else {
        // For approve endpoint, use RequestPayload format
        formattedPayload = {
            ID: payload.ID,
            item_uuids: payload.item_uuids,
            item_funds: (payload as ApprovalData).item_funds,
            totalPrice: (payload as ApprovalData).totalPrice,
            target_status: payload.target_status,
            action: payload.action
        };
    }

    const response = await fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(formattedPayload),
    });
    if (!response.ok) {
        throw new Error("Failed to approve/deny request");
    }
    return response.json();
}