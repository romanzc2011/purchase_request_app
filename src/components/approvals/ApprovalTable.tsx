import React from "react";
import { useQuery } from "@tanstack/react-query";
import {
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Paper,
    Box,
    Typography,
} from "@mui/material";
import ApprovalsTableRow from "./ApprovalsTableRow";
import { FormValues } from "../../types/formTypes";
import { fetchSearchData } from "./SearchBar";

interface ApprovalTableProps {
    onDelete: (ID: number) => void;
    resetTable: () => void;
    searchQuery: string;
}

const API_CALL1 = "/api/getApprovalData";
const API_URL1 = `${import.meta.env.VITE_API_URL}${API_CALL1}`;

async function fetchApprovalData() {
    const response = await fetch(API_URL1, {
        headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
    });
    if (!response.ok) throw new Error(`HTTP error: ${response.status}`);
    return response.json();
}

export default function ApprovalTable({
    searchQuery,
    onDelete,
    resetTable,
}: ApprovalTableProps) {
    const { data: searchData } = useQuery({
        queryKey: ["search_data", searchQuery],
        queryFn: () => fetchSearchData(searchQuery),
    });

    const { data: approvalData } = useQuery({
        queryKey: ["approval_data"],
        queryFn: fetchApprovalData,
    });

    const rows: FormValues[] = searchQuery
        ? searchData || []
        : approvalData || [];
    return (
        <Box sx={{ overflowX: "auto", height: "100vh", width: "100%" }}>
            <TableContainer
                component={Paper}
                sx={{
                    background: "#2c2c2c",
                    color: "white",
                    borderRadius: 2,
                    mt: 2,
                }}
            >
                <Table sx={{ minWidth: 800 }}>
                    <TableHead
                        sx={{
                            background:
                                "linear-gradient(to bottom, #2c2c2c, #800000)",
                        }}
                    >
                        <TableRow>
                            {[
                                "REQUISITION #",
                                "ID",
                                "REQUESTER",
                                "BUDGET OBJECT CODE",
                                "FUND",
                                "LOCATION",
                                "QUANTITY",
                                "PRICE EACH",
                                "LINE TOTAL",
                                "ITEM DESCRIPTION",
                                "JUSTIFICATION",
                                "STATUS",
                                "ACTIONS",
                            ].map((label) => (
                                <TableCell
                                    key={label}
                                    sx={{
                                        color: "white",
                                        fontWeight: "bold",
                                        textAlign: "center",
                                    }}
                                >
                                    {label}
                                </TableCell>
                            ))}
                        </TableRow>
                    </TableHead>

                    <TableBody sx={{ textAlign: "center" }}>
                        {rows.map((approval_data) => (
                            <ApprovalsTableRow
                                key={approval_data.ID}
                                approval_data={approval_data}
                            />
                        ))}
                    </TableBody>

                     <tfoot>
                        <TableRow>
                            <TableCell colSpan={7}>

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
                                {rows
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
