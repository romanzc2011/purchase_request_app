import React, { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
    TableRow,
    TableCell,
    TextField,
    Box,
    Button,
} from "@mui/material";
import Buttons from "../purchase_req/Buttons";
import { FormValues } from "../../types/formTypes";
import DownloadOutlinedIcon from "@mui/icons-material/DownloadOutlined";
import MoreDataButton from "./MoreDataButton";
import { convertBOC } from "../../utils/bocUtils";
import WarningIcon from '@mui/icons-material/WarningAmber';
import PendingIcon from '@mui/icons-material/Pending';
import SuccessIcon from '@mui/icons-material/CheckCircleOutline';
import { useUUIDStore } from "../../services/UUIDService";

const API_URL_ASSIGN = `${import.meta.env.VITE_API_URL}/api/assignIRQ1_ID`;
const API_URL_APPROVE_DENY = `${import.meta.env.VITE_API_URL}/api/approveDenyRequest`;

export default function ApprovalsTableRow({
    approval_data,
    expandButton,
}: {
    approval_data: FormValues;
    expandButton?: React.ReactNode;
}) {
    const queryClient = useQueryClient();

    // 1) per‑row state for the draft IRQ1_ID
    const [showIRQ1_ID, setIRQ1_ID] = useState<string>(
        approval_data.IRQ1_ID || ""
    );

    // Get UUID for the item
    const { getUUID } = useUUIDStore();

    // 2) mutation to assign ReqID
    const assignIRQ1Mutation = useMutation({
        mutationFn: async (newIRQ1ID: string) => {
            try {
                // Get the UUID from the store
                const UUID = await getUUID(approval_data.ID);
                console.log("UUID:", UUID);
                
                if (!UUID) {
                    console.error("UUID not found for request ID:", approval_data.ID);
                    throw new Error("UUID not found for this request");
                }
                
                // Log the data being sent for debugging
                console.log("Sending data to assignIRQ1_ID:", { 
                    ID: approval_data.ID, 
                    IRQ1_ID: newIRQ1ID, 
                    UUID: UUID 
                });
                
                const res = await fetch(API_URL_ASSIGN, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${localStorage.getItem("access_token")}`,
                    },
                    body: JSON.stringify({ 
                        ID: approval_data.ID, 
                        IRQ1_ID: newIRQ1ID, 
                        UUID: UUID 
                    }),
                });
                
                console.log("Response status:", res.status);
                
                if (!res.ok) {
                    const errorText = await res.text();
                    console.error("Error response:", errorText);
                    throw new Error(`HTTP error: ${res.status} - ${errorText}`);
                }
                
                const data = await res.json();
                console.log("Success response:", data);
                return data;
            } catch (error) {
                console.error("Error in assignReqIDMutation:", error);
                throw error;
            }
        },
        onSuccess: () => {
            console.log("Successfully assigned ReqID");
            queryClient.invalidateQueries({ queryKey: ["approval_data"] });
        },
        onError: (error) => {
            console.error("Mutation error:", error);
            // You could add a toast notification here
        }
    });

    // mutation to approve/deny
    const approveDenyMutation = useMutation({
        mutationFn: async (action: "approve" | "deny") => {
            console.log("Sending approve/deny request:", {
                ID: approval_data.ID,
                action
            });
            
            const res = await fetch(API_URL_APPROVE_DENY, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${localStorage.getItem("access_token")}`,
                },
                body: JSON.stringify({
                    ID: approval_data.ID,
                    action,
                }),
            });
            
            if (!res.ok) {
                const errorText = await res.text();
                console.error("Error response:", errorText);
                throw new Error(`HTTP error: ${res.status} - ${errorText}`);
            }
            
            return res.json();
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["approval_data"] });
        },
        onError: (error) => {
            console.error("Mutation error:", error);
            // You could add a toast notification here
        }
    });

    

    // stub download handler
    const handleDownload = () => {
        console.log("Download clicked for", approval_data.ID);
        // TODO: your download logic
    };

    return (
        <TableRow>
            {expandButton && (
                <TableCell>
                    {expandButton}
                </TableCell>
            )}
            {/* REQUISITION # */}
            <TableCell sx={{ color: "white" }}>

                <Box sx={{ display: "flex", gap: "5px" }}>
                    <Buttons
                        className="btn btn-maroon"
                        label={approval_data.IRQ1_ID ? "Assigned" : "Assign"}
                        onClick={() => assignIRQ1Mutation.mutate(showIRQ1_ID)}
                    />
                    <TextField
                        id="IRQ1_ID"
                        value={showIRQ1_ID}
                        className="form-control"
                        fullWidth
                        variant="outlined"
                        size="small"
                        onChange={(e) => setIRQ1_ID(e.target.value)}
                        sx={{
                            backgroundColor: approval_data.IRQ1_ID ? 'rgba(0, 128, 0, 0.1)' : 'white',
                            width: '100px',
                            '& .MuiOutlinedInput-root': {
                                '& fieldset': {
                                    borderColor: approval_data.IRQ1_ID ? 'green' : 'red',
                                    borderWidth: '2px',
                                },
                            },
                        }}
                    />
                </Box>
            </TableCell>

            {/* ID */}
            <TableCell sx={{ color: "white" }}>
                {approval_data.ID}
            </TableCell>

            {/* REQUESTER */}
            <TableCell sx={{ color: "white" }}>
                {approval_data.requester}
            </TableCell>

            {/* BUDGET OBJECT CODE */}
            <TableCell
                sx={{ color: "white", textAlign: "center" }}
            >
                {convertBOC(approval_data.budgetObjCode)}
            </TableCell>

            {/* FUND */}
            <TableCell sx={{ color: "white" }}>
                {approval_data.fund}
            </TableCell>

            {/* LOCATION */}
            <TableCell sx={{ color: "white" }}>
                {approval_data.location}
            </TableCell>

            {/* QUANTITY */}
            <TableCell
                sx={{ color: "white", textAlign: "center" }}
            >
                {approval_data.quantity}
            </TableCell>

            {/* PRICE EACH */}
            <TableCell
                sx={{ color: "white", textAlign: "center" }}
            >
                {typeof approval_data.priceEach === "number"
                    ? approval_data.priceEach.toFixed(2)
                    : "0.00"}
            </TableCell>

            {/* LINE TOTAL */}
            <TableCell
                sx={{ color: "white", textAlign: "center" }}
            >
                {typeof approval_data.totalPrice === "number"
                    ? approval_data.totalPrice.toFixed(2)
                    : "0.00"}
            </TableCell>

            {/* ITEM DESCRIPTION */}
            <TableCell
                sx={{ color: "white", textAlign: "center" }}
            >
                {approval_data.itemDescription}
            </TableCell>

            {/* JUSTIFICATION */}
            <TableCell
                sx={{ color: "white", textAlign: "center" }}
            >
                <MoreDataButton
                    name="Justification"
                    data={approval_data.justification}
                />
            </TableCell>

            {/* STATUS */}
            <TableCell
                sx={{ 
                    color: "black", 
                    textAlign: "center",
                    backgroundColor: 
                        approval_data.status === "NEW REQUEST" ? "#ff9800" : // Warning color (orange)
                        approval_data.status === "PENDING" ? "#2196f3" : // Info color (blue)
                        approval_data.status === "APPROVED" ? "#4caf50" : // Success color (green)
                        approval_data.status === "DENIED" ? "#f44336" : // Error color (red)
                        "#9e9e9e", // Default color (gray)
                    fontWeight: "bold"
                }}
            >
                {/* Status Icon and Text */}
                {/* WARNING */}
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1 }}>
                    {approval_data.status === "NEW REQUEST" && <WarningIcon />}
                    {approval_data.status === "PENDING" && <PendingIcon />}
                    {approval_data.status === "APPROVED" && <SuccessIcon />}
                    {approval_data.status}
                </Box>
            </TableCell>

            {/* ACTIONS */}
            <TableCell>
                <Box sx={{ display: "flex", gap: "10px" }}>
                    <Button
                        variant="contained"
                        color="success"
                        onClick={() =>
                            approveDenyMutation.mutate("approve")
                        }
                    >
                        Approve
                    </Button>
                    <Button
                        variant="contained"
                        color="error"
                        onClick={() =>
                            approveDenyMutation.mutate("deny")
                        }
                    >
                        Deny
                    </Button>
                    <Button
                        variant="contained"
                        color="primary"
                        onClick={handleDownload}
                    >
                        <DownloadOutlinedIcon />
                    </Button>
                </Box>
            </TableCell>
        </TableRow>
    );
}