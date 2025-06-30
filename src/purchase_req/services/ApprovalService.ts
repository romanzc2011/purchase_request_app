import { ApprovalData, DenialData } from "../types/approvalTypes";

const API_URL_APPROVE_REQUEST = `${import.meta.env.VITE_API_URL}/api/approveRequest`
const API_URL_DENY_REQUEST = `${import.meta.env.VITE_API_URL}/api/denyRequest`
const API_URL_APPROVAL_DATA = `${import.meta.env.VITE_API_URL}/api/getApprovalData`;
const API_URL_CYBERSEC_RELATED = `${import.meta.env.VITE_API_URL}/api/cyberSecRelated`;
const API_URL_ASSIGN_CO = `${import.meta.env.VITE_API_URL}/api/assignCO`;
const API_URL_STATEMENT_OF_NEED_FORM = `${import.meta.env.VITE_API_URL}/api/downloadStatementOfNeedForm`;

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

/***********************************************************************************/
// FETCH/DOWNLOAD STATEMENT OF NEED FORM - also send approval data to backend - download form
/***********************************************************************************/
export async function downloadStatementOfNeedForm(ID: string) {
	try {
		// fetch approval data
		const approvalData = await fetchApprovalData(ID);

		// Ensure approvalData is an array
		const approvalDataArray = Array.isArray(approvalData) ? approvalData : [approvalData];

		// send approval data to backend
		const response = await fetch(API_URL_STATEMENT_OF_NEED_FORM, {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
				Authorization: `Bearer ${localStorage.getItem("access_token")}`
			},
			body: JSON.stringify({
				ID,
				approvalData: approvalDataArray
			})
		});
		if (!response.ok) throw new Error(`HTTP ${response.status}`);

		// Get the blob response
		const blob = await response.blob();

		// Create a URL for the blob
		const blobUrl = URL.createObjectURL(blob);

		// Create temporary link element
		const link = document.createElement("a");
		link.href = blobUrl;
		link.download = `statement_of_need-${ID}.pdf`;

		// Append to body
		document.body.appendChild(link);

		// Trigger download
		link.click();

		// Cleanup
		document.body.removeChild(link);
		URL.revokeObjectURL(blobUrl);
	} catch (error) {
		console.error("Error downloading statement of need form:", error);
		toast.error("Failed to download statement of need form. Please try again.");
	}
}

/***********************************************************************************/
// FETCH APPROVAL DATA
/***********************************************************************************/
export async function fetchApprovalData(ID?: string) {
	if (ID) {
		const response = await fetch(`${API_URL_APPROVAL_DATA}?ID=${ID}`, {
			method: "GET",
			headers: {
				"Authorization": `Bearer ${localStorage.getItem("access_token")}`
			}
		});
		if (!response.ok) throw new Error(`HTTP ${response.status}`);
		const data = await response.json();

		return data;
	} else {
		const response = await fetch(API_URL_APPROVAL_DATA, {
			headers: {
				"Authorization": `Bearer ${localStorage.getItem("access_token")}`
			}
		});
		if (!response.ok) throw new Error(`HTTP ${response.status}`);
		const data = await response.json();

		return data;
	}
}