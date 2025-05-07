import { useState, useEffect, useCallback } from "react";
import { FormValues } from "../../../types/formTypes";
import ApprovalTable from "../ui/ApprovalTable";
import SearchBar from "../ui/SearchBar";
import CommentModal from "../modals/CommentModal";
import { Box } from "@mui/material";

/* INTERFACE */
interface ApprovalTableProps {
    onDelete: (ID: string) => void;
    resetTable: () => void;
}

/* API URLs */
const API_URL_POST_COMMENTS = `${import.meta.env.VITE_API_URL}/api/postComments`;

/* POST comments: the approver (Ted/Edmund) will review a SON, if there are multiple items, they may approve
    they may approve the entire SON, or if they have questions on a line item, and they dont want to completely
    reject that request, they add a comment to that line item, that comment is then sent back to the requester
    and the requester will need to approve a new SON.
*/

async function postComments(comments: string[], ID: string) {
    try {
        const response = await fetch(API_URL_POST_COMMENTS, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${localStorage.getItem("access_token")}`,
            },
            body: JSON.stringify({
                comments: comments,
                ID: ID,
            }),
        });
        if (!response.ok) throw new Error(`HTTP error: ${response.status}`);
        return response.json();
    } catch (error) {
        console.error("Error posting comments:", error);
    }
}

export default function ApprovalPageMain({ onDelete, resetTable }: ApprovalTableProps) {
    const [dataBuffer, setDataBuffer] = useState<FormValues[]>([]);
    const [searchQuery, setSearchQuery] = useState("");

    return (
        <Box sx={{
            display: 'flex',
            flexDirection: 'column',
            height: '100%'
        }}>
            <Box sx={{ mb: 2 }}>
                <SearchBar setSearchQuery={setSearchQuery} />
            </Box>
            <Box sx={{ flex: 1 }}>
                <ApprovalTable

                    onDelete={(ID: string) =>
                        setDataBuffer(
                            dataBuffer.filter(
                                (item) => item.ID !== ID
                            )
                        )
                    }
                    resetTable={resetTable}
                    searchQuery={searchQuery}
                />
            </Box>
        </Box>
    )
}
