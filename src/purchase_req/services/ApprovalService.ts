import { computeAPIURL } from "../utils/misc_utils";

export function useApprovalService() {
	const processPayload = async (payload: any) => {
		const url = payload.action === "APPROVE" 
			? computeAPIURL("/api/approveRequest")
			: computeAPIURL("/api/denyRequest");

		const response = await fetch(url, {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
				Authorization: `Bearer ${localStorage.getItem("access_token")}`
			},
			body: JSON.stringify(payload)
		});

		if (!response.ok) {
			throw new Error(`HTTP error! status: ${response.status}`);
		}

		return response.json();
	};

	const setApprovalPayload = (payload: any) => {
		// This function can be used to set approval payload if needed
		console.log("Approval payload set:", payload);
	};

	const setDenialPayload = (payload: any) => {
		// This function can be used to set denial payload if needed
		console.log("Denial payload set:", payload);
	};

	return {
		processPayload,
		setApprovalPayload,
		setDenialPayload
	};
}