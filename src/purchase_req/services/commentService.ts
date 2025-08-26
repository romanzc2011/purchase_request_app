import { GroupCommentPayload } from "../types/approvalTypes";
import { computeAPIURL } from "../utils/misc_utils";

export async function addComments(payload: GroupCommentPayload): Promise<any> {
	const response = await fetch(computeAPIURL("/api/add_comments"), {
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
}

// #########################################################################################
// FILTER COMMENT PAYLOAD
// #########################################################################################
export function cleanPayload(payload: GroupCommentPayload) {
    // Zip the three arrays together
    const rows = payload.item_uuids.map((uuid, index) => ({
        uuid,
        desc: payload.item_desc[index],
        comment: payload.comment[index]
    }));

    // Filter out header rows
    const filteredRows = rows.filter(r => !r.uuid.startsWith("header-"));

    // unzip back into payload
    payload.item_uuids = filteredRows.map(r => r.uuid);
    payload.item_desc = filteredRows.map(r => r.desc);
    payload.comment = filteredRows.map(r => r.comment);
    payload.group_count = filteredRows.length;
}
