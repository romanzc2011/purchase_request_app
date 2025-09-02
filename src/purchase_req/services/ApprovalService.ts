import { ApprovalData, DenialData } from "../types/approvalTypes";
import { computeAPIURL } from "../utils/misc_utils";

const API_URL_APPROVE_REQUEST = computeAPIURL("/api/approveRequest")
const API_URL_DENY_REQUEST = computeAPIURL("/api/denyRequest")

// ##############################################################
// Approve/Deny request
// ##############################################################
export async function approveDenyRequest(payload: ApprovalData | DenialData): Promise<any> {
    const token = localStorage.getItem("access_token");
    if (!token) {
        throw new Error("No token found");
    }   

    // Determine which endpoint to use based on action
    const isApproved = payload.action === "APPROVE" || payload.action === "approve";
    const url = isApproved ? API_URL_APPROVE_REQUEST : API_URL_DENY_REQUEST;
    
    // Format payload for the correct endpoint
    let formattedPayload;
    if (isApproved) {
        // For approve endpoint, use RequestPayload format
        formattedPayload = {
            ID: payload.ID,
            item_uuids: payload.item_uuids,
            item_funds: (payload as ApprovalData).item_funds ?? [],
            totalPrice: (payload as ApprovalData).totalPrice ?? [],
            target_status: payload.target_status,
            action: payload.action
        };
    } else {
        // For deny endpoint, use DenyPayload format
        formattedPayload = {
            ID: payload.ID,
            item_uuids: payload.item_uuids,
            target_status: payload.target_status, // Keep as array since backend now expects it
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