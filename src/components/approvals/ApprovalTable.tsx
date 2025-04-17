import React, { useState } from "react";
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
    Collapse,
    IconButton,
    TextField,
    Button,
} from "@mui/material";
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';
import DownloadOutlinedIcon from '@mui/icons-material/DownloadOutlined';
import WarningIcon from '@mui/icons-material/WarningAmber';
import PendingIcon from '@mui/icons-material/Pending';
import SuccessIcon from '@mui/icons-material/CheckCircleOutline';
import ErrorIcon from '@mui/icons-material/Error';
import ApprovalsTableRow from "./ApprovalsTableRow";
import Buttons from "../purchase_req/Buttons";
import MoreDataButton from "./MoreDataButton";
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

    // Group rows by ID to handle multiple items per request
    const groupedRows = rows.reduce((acc, row) => {
        const id = row.ID;
        if (!acc[id]) {
            acc[id] = [];
        }
        acc[id].push(row);
        return acc;
    }, {} as Record<string, FormValues[]>);

    // State to track which rows are expanded
    const [expandedRows, setExpandedRows] = useState<Record<string, boolean>>({});

    // Toggle expanded state for a row
    const toggleRowExpanded = (id: string) => {
        setExpandedRows(prev => ({
            ...prev,
            [id]: !prev[id]
        }));
    };

    return (
        <Box sx={{ overflowX: "auto", height: "100vh", width: "100%" }}>
            <TableContainer component={Paper} sx={{ background: "#2c2c2c", color: "white", borderRadius: 2, mt: 2, width: "100%" }}>
                <Table sx={{ minWidth: 800, width: "100%" }}>
                    <TableHead sx={{ background: "linear-gradient(to bottom, #2c2c2c, #800000)" }}>
                        <TableRow>
                            <TableCell sx={{ width: "50px" }} /> {/* Expand/collapse icon column */}
                            {[
                                "REQUISITION #", "ID", "REQUESTER", "BUDGET OBJECT CODE",
                                "FUND", "LOCATION", "QUANTITY", "PRICE EACH",
                                "LINE TOTAL", "ITEM DESCRIPTION", "JUSTIFICATION",
                                "STATUS", "ACTIONS"
                            ].map(label => (
                                <TableCell key={label} sx={{ color: "white", fontWeight: "bold", textAlign: "center", padding: "8px 16px" }}>
                                    {label}
                                </TableCell>
                            ))}
                        </TableRow>
                    </TableHead>

                    <TableBody sx={{ textAlign: "center" }}>
                        {Object.entries(groupedRows).map(([id, items]) => (
                            <React.Fragment key={id}>
                                {/* Main row with expand/collapse icon */}
                                <TableRow>
                                    <TableCell sx={{ color: "white" }}>
                                        <IconButton
                                            size="small"
                                            onClick={() => toggleRowExpanded(id)}
                                            sx={{ color: "white" }}
                                        >
                                            {expandedRows[id] ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
                                        </IconButton>
                                    </TableCell>
                                    <TableCell sx={{ color: "white" }}>
                                        <Box sx={{ display: "flex", gap: "5px" }}>
                                            <Buttons
                                                className="btn btn-maroon"
                                                disabled={!items[0].reqID || Boolean(items[0].reqID)}
                                                label={items[0].reqID ? "Assigned" : "Assign"}
                                                onClick={() => { }}
                                            />
                                            <TextField
                                                id="reqID"
                                                value={items[0].reqID || ""}
                                                className="form-control"
                                                fullWidth
                                                variant="outlined"
                                                size="small"
                                                inputProps={{
                                                    readOnly: Boolean(items[0].reqID),
                                                    style: {
                                                        width: '50px',
                                                        color: items[0].reqID ? 'green' : 'inherit'
                                                    }
                                                }}
                                                sx={{
                                                    backgroundColor: items[0].reqID ? 'rgba(0, 128, 0, 0.1)' : 'white',
                                                    '& .MuiOutlinedInput-root': {
                                                        '& fieldset': {
                                                            borderColor: items[0].reqID ? 'green' : 'red',
                                                            borderWidth: '2px',
                                                        },
                                                    },
                                                }}
                                            />
                                        </Box>
                                    </TableCell>
                                    <TableCell sx={{ color: "white" }}>{items[0].ID}</TableCell>
                                    <TableCell sx={{ color: "white" }}>{items[0].requester}</TableCell>
                                    <TableCell sx={{ color: "white" }}>{items[0].budgetObjCode}</TableCell>
                                    <TableCell sx={{ color: "white" }}>{items[0].fund}</TableCell>
                                    <TableCell sx={{ color: "white" }}>{items[0].location}</TableCell>
                                    <TableCell sx={{ color: "white" }}>{items[0].quantity}</TableCell>
                                    <TableCell sx={{ color: "white" }}>{items[0].priceEach}</TableCell>
                                    <TableCell sx={{ color: "white" }}>{items[0].totalPrice}</TableCell>
                                    <TableCell sx={{ color: "white" }}>{items[0].itemDescription}</TableCell>
                                    <TableCell sx={{ color: "white" }}>
                                        <MoreDataButton name="Justification" data={items[0].justification} />
                                    </TableCell>

                                    <TableCell sx={{
                                        color: "black",
                                        textAlign: "center",
                                        backgroundColor:
                                            items[0].status === "NEW REQUEST" ? "#ff9800" : // Warning color (orange)
                                            items[0].status === "PENDING" ? "#2196f3" : // Info color (blue)
                                            items[0].status === "APPROVED" ? "#4caf50" : // Success color (green)
                                            items[0].status === "DENIED" ? "#f44336" : // Error color (red)
                                                            "#9e9e9e", // Default color (gray)
                                        fontWeight: "bold"
                                    }}>
                                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1 }}>
                                            {items[0].status === "NEW REQUEST" && <WarningIcon />}
                                            {items[0].status === "PENDING" && <PendingIcon />}
                                            {items[0].status === "APPROVED" && <SuccessIcon />}
                                            {items[0].status === "DENIED" && <ErrorIcon />}
                                            {items[0].status}
                                        </Box>
                                    </TableCell>
                                    <TableCell sx={{ color: "white" }}>
                                        <Box sx={{ display: "flex", gap: "10px" }}>
                                            <Button
                                                variant="contained"
                                                color="success"
                                                onClick={() => { }}
                                            >
                                                Approve
                                            </Button>
                                            <Button
                                                variant="contained"
                                                color="error"
                                                onClick={() => { }}
                                            >
                                                Deny
                                            </Button>
                                            <Button
                                                variant="contained"
                                                color="primary"
                                                onClick={() => { }}
                                            >
                                                <DownloadOutlinedIcon />
                                            </Button>
                                        </Box>
                                    </TableCell>
                                </TableRow>

                                {/* Collapsible content for additional items */}
                                <TableRow>
                                    <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={14}>
                                        <Collapse in={expandedRows[id]} timeout="auto" unmountOnExit>
                                            <Box sx={{ margin: 1, background: "#3c3c3c", borderRadius: 1, p: 2 }}>
                                                <Typography variant="h6" gutterBottom component="div" sx={{ color: "white" }}>
                                                    Additional Items
                                                </Typography>
                                                <Table size="small" aria-label="additional items">
                                                    <TableHead>
                                                        <TableRow>
                                                            {[
                                                                "ID", "BUDGET OBJECT CODE", "FUND", "LOCATION",
                                                                "QUANTITY", "PRICE EACH", "LINE TOTAL",
                                                                "ITEM DESCRIPTION", "JUSTIFICATION"
                                                            ].map(label => (
                                                                <TableCell key={label} sx={{ color: "white", fontWeight: "bold" }}>
                                                                    {label}
                                                                </TableCell>
                                                            ))}
                                                        </TableRow>
                                                    </TableHead>
                                                    <TableBody>
                                                        {items.slice(1).map((item, index) => (
                                                            <TableRow key={index}>
                                                                <TableCell sx={{ color: "white" }}>{item.ID}</TableCell>
                                                                <TableCell sx={{ color: "white" }}>{item.budgetObjCode}</TableCell>
                                                                <TableCell sx={{ color: "white" }}>{item.fund}</TableCell>
                                                                <TableCell sx={{ color: "white" }}>{item.location}</TableCell>
                                                                <TableCell sx={{ color: "white" }}>{item.quantity}</TableCell>
                                                                <TableCell sx={{ color: "white" }}>{item.priceEach}</TableCell>
                                                                <TableCell sx={{ color: "white" }}>{item.totalPrice}</TableCell>
                                                                <TableCell sx={{ color: "white" }}>{item.itemDescription}</TableCell>
                                                                <TableCell sx={{ color: "white" }}>
                                                                    <MoreDataButton name="Justification" data={item.justification} />
                                                                </TableCell>
                                                            </TableRow>
                                                        ))}
                                                    </TableBody>
                                                </Table>
                                            </Box>
                                        </Collapse>
                                    </TableCell>
                                </TableRow>
                            </React.Fragment>
                        ))}
                    </TableBody>

                    <tfoot>
                        <TableRow>
                            <TableCell colSpan={7}></TableCell>
                            <TableCell colSpan={2} sx={{ color: "white", textAlign: "right" }}>
                                <Typography variant="h6" component="div" sx={{ fontWeight: "bold", textAlign: "right" }}></Typography>
                            </TableCell>
                            <TableCell colSpan={4} sx={{ color: "white", fontWeight: "bold", textAlign: "right" }}>
                                Total: ${rows.reduce((acc: number, approval_data: FormValues) => acc + (Number(approval_data.totalPrice) || 0), 0).toFixed(2)}
                            </TableCell>
                        </TableRow>
                    </tfoot>
                </Table>
            </TableContainer>
        </Box>
    );
}