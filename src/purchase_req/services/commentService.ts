import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "react-toastify";

const API_URL_ADD_COMMENTS_BULK = `${import.meta.env.VITE_API_URL}/api/add_comments`

export interface GroupCommentPayload {
    groupKey: string;   // Group key is the ID in the table, ie LAWB000x
    comment: CommentEntry[];
    group_count: number;
    item_uuids: string[];
    item_desc: string[];
}

export interface CommentEntry { uuid: string; comment: string }

// #########################################################################################
// Add comments
// #########################################################################################
export async function addComments(payload: GroupCommentPayload) {
    const response = await fetch(API_URL_ADD_COMMENTS_BULK, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });
    if (!response.ok) {
        throw new Error("Failed to add comments bulk");
    }
    return response.json();
}
