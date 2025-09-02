import { GroupCommentPayload } from "../types/approvalTypes";
import { authFetch } from "../utils/authFetch";
import { computeHTTPURL } from "../utils/sio_client";

const API_URL_ADD_COMMENTS_BULK = `${computeHTTPURL("/api/add_comments")}`;

// #########################################################################################
// Add comments
// #########################################################################################
export async function addComments(payload: GroupCommentPayload) {
    const response = await authFetch(API_URL_ADD_COMMENTS_BULK, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });
    if (!response.ok) {
        throw new Error("Failed to add comments bulk");
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
