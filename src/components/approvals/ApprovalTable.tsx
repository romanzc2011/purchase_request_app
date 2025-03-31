/* eslint-disable @typescript-eslint/no-unused-vars */
import { useEffect, useState } from "react";
import { QueryClient, useQuery, useQueryClient } from '@tanstack/react-query';
import {
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Paper,
    Button,
    Typography,
} from "@mui/material";
import { FormValues } from "../../types/formTypes";
import { Box } from "@mui/material";
import { convertBOC } from "../../utils/bocUtils";

/************************************************************************************ */
/* CONFIG API URL- */
/************************************************************************************ */
const baseURL = import.meta.env.VITE_API_URL;
const API_CALL: string = "/api/getApprovalData";
const API_URL = `${baseURL}${API_CALL}`;

/* INTERFACE */
interface ApprovalTableProps {
    onDelete: (ID: number) => void;
    resetTable: () => void;
    searchQuery: string;
}

/* FETCHING APPROVAL DATA FUNCTION for useQuery */
const fetchApprovalData = async () => {
    const response = await fetch(API_URL, {
        headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
    });
    
    if(!response.ok) {
        throw new Error(`HTTP error: ${response.status}`);
    }
    const jsonData = await response.json();
    console.log(jsonData);
    return jsonData;
}

function ApprovalsTable({ searchQuery }: ApprovalTableProps) {
    const {isPending, isError, data, error} = useQuery({
        queryKey: ['approval_data', searchQuery],
        queryFn: fetchApprovalData,
    });
    console.log("Fetch data:", data);
    const queryClient = useQueryClient();
    const cachedSearchData = searchQuery && queryClient.getQueryData<FormValues[]>(['search-str', searchQuery]);

    // If searchQuery exists and cachedData found, display that
    const retval = searchQuery ? cachedSearchData || [] : data || [];

    /************************************************************************************ */
    /* APPROVE OR DENY */
    /************************************************************************************ */
    const handleApprove = () => {};

    const handleDeny = () => {};

    return (
        <Box sx={{ overflowX: "auto", height: '100vh', width: "100%" }}>
            <TableContainer
                component={Paper}
                sx={{
                    background: " #2c2c2c",
                    color: "white", // Ensure text contrast
                    borderRadius: "10px",
                    width: "100%",
                    marginTop: "20px",
                }}
            >
                <Table sx={{ minWidth: 800, tableLayout: "auto" }}>
                    <TableHead
                        sx={{
                            background:
                                "linear-gradient(to bottom, #2c2c2c, #800000)",
                        }}
                    >
                        <TableRow>
                            {/**************************************************************************/}
                                {/* REQUISITION ID */}
                            <TableCell
                                sx={{
                                    color: "white",
                                    fontWeight: "bold",
                                    textAlign: "center",
                                }}
                            >
                                REQUISITION ID
                            </TableCell>
                            {/**************************************************************************/}
                                {/* RECIPIENT */}
                            <TableCell
                                sx={{
                                    color: "white",
                                    fontWeight: "bold",
                                    textAlign: "center",
                                }}
                            >
                                
                                RECIPIENT
                            </TableCell>
                            {/**************************************************************************/}
                                {/* BUDGET OBJECT CODE */}
                            <TableCell
                                sx={{
                                    color: "white",
                                    fontWeight: "bold",
                                    textAlign: "center",
                                }}
                            >
                                
                                BUDGET OBJECT CODE
                            </TableCell>
                            {/**************************************************************************/}
                                {/* FUND */}
                            <TableCell
                                sx={{
                                    color: "white",
                                    fontWeight: "bold",
                                    textAlign: "center",
                                }}
                            >
                                
                                FUND
                            </TableCell>
                            {/**************************************************************************/}
                                {/* LOCATION */}
                            <TableCell
                                sx={{
                                    color: "white",
                                    fontWeight: "bold",
                                    textAlign: "center",
                                }}
                            >
                                
                                LOCATION
                            </TableCell>
                            {/**************************************************************************/}
                                {/* QUANTITY */}
                            <TableCell
                                sx={{
                                    color: "white",
                                    fontWeight: "bold",
                                    textAlign: "center",
                                }}
                            >
                                
                                QUANTITY
                            </TableCell>
                            {/**************************************************************************/}
                                {/* PRICE EACH */}
                            <TableCell
                                sx={{
                                    color: "white",
                                    fontWeight: "bold",
                                    textAlign: "center",
                                }}
                            >
                                
                                PRICE EACH
                            </TableCell>
                            {/**************************************************************************/}
                                {/* ESTIMATED PRICE */}
                            <TableCell
                                sx={{
                                    color: "white",
                                    fontWeight: "bold",
                                    textAlign: "center",
                                }}
                            >
                                
                                LINE TOTAL
                            </TableCell>
                            {/**************************************************************************/}
                                {/* STATUS */}
                            <TableCell
                                sx={{
                                    color: "white",
                                    fontWeight: "bold",
                                    textAlign: "center",
                                }}
                            >
                                
                                STATUS
                            </TableCell>
                            {/**************************************************************************/}
                                {/* ACTIONS */}
                            <TableCell
                                sx={{
                                    color: "white",
                                    fontWeight: "bold",
                                    textAlign: "center",
                                }}
                            >
                                
                                ACTIONS
                            </TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody sx={{ textAlign: "center" }}>
                        {retval.map((approval_data: FormValues) => (
                            <TableRow key={approval_data.ID}>
                                {/**************************************************************************/}
                                {/* REQUISITION ID */}
                                <TableCell sx={{ color: "white" }}>
                                    {approval_data.reqID}
                                </TableCell>

                                {/**************************************************************************/}
                                {/* RECIPIENT */}
                                <TableCell sx={{ color: "white" }}>
                                    {approval_data.recipient}
                                </TableCell>

                                {/**************************************************************************/}
                                {/* BUDGET OBJECT CODE */}
                                <TableCell sx={{ color: "white" }}>
                                    {convertBOC(approval_data.budgetObjCode)}
                                </TableCell>

                                {/**************************************************************************/}
                                {/* FUND */}
                                <TableCell sx={{ color: "white" }}>
                                    {approval_data.fund}
                                </TableCell>

                                {/**************************************************************************/}
                                {/* LOCATION */}
                                <TableCell sx={{ color: "white" }}>
                                    {approval_data.location}
                                </TableCell>

                                {/**************************************************************************/}
                                {/* QUANTITY */}
                                <TableCell
                                    sx={{ color: "white", textAlign: "center" }}
                                >
                                    {approval_data.quantity}
                                </TableCell>

                                {/**************************************************************************/}
                                {/* PRICE */}
                                <TableCell
                                    sx={{ color: "white", textAlign: "center" }}
                                >
                                    {typeof approval_data.priceEach === "number"
                                        ? approval_data.priceEach.toFixed(2)
                                        : "0.00"}
                                </TableCell>

                                {/**************************************************************************/}
                                {/* ESTIMATED PRICE */}
                                <TableCell
                                    sx={{ color: "white", textAlign: "center" }}
                                >
                                    {typeof approval_data.totalPrice === "number"
                                        ? approval_data.totalPrice.toFixed(2)
                                        : "0.00"}
                                </TableCell>
                                {/**************************************************************************/}
                                {/* STATUS */}
                                <TableCell sx={{ color: "white" }}>
                                    {approval_data.status}
                                </TableCell>

                                {/**************************************************************************/}
                                {/* APPROVE/DENY BUTTONS */}
                                <TableCell>
                                    <Box sx={{ display: "flex", gap: "10px" }}>
                                        <Button
                                            variant="contained"
                                            color="success"
                                            onClick={handleApprove}
                                        >
                                            Approve
                                        </Button>
                                        <Button
                                            variant="contained"
                                            color="error"
                                            onClick={handleDeny}
                                        >
                                            Deny
                                        </Button>
                                    </Box>
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                    <tfoot>
                        <TableRow>
                            <TableCell colSpan={4}>
                           
                            </TableCell>

                            <TableCell
                                colSpan={2}
                                sx={{ color: "white", textAlign: "right" }}
                            >
                                <Typography
                                    variant="h6"
                                    component="div"
                                    sx={{
                                        fontWeight: "bold",
                                        textAlign: "right",
                                    }}
                                ></Typography>
                            </TableCell>
                            <TableCell
                                colSpan={4}
                                sx={{
                                    color: "white",
                                    fontWeight: "bold",
                                    textAlign: "right",
                                }}
                            >
                                Total: $
                                {retval
                                    .reduce(
                                        (acc: number, approval_data: FormValues) =>
                                            acc +
                                            (Number(approval_data.totalPrice) || 0),
                                        0
                                    )
                                    .toFixed(2)}
                            </TableCell>
                        </TableRow>
                    </tfoot>
                </Table>
            </TableContainer>
            </Box>
    );
}

export default ApprovalsTable;
