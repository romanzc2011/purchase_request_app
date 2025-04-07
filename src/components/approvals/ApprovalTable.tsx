/* eslint-disable @typescript-eslint/no-unused-vars */
import { useQuery, useQueryClient } from '@tanstack/react-query';
import {
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Paper,
    Typography,
} from "@mui/material";
import { FormValues } from "../../types/formTypes";
import { Box, Button } from "@mui/material";
import { convertBOC } from "../../utils/bocUtils";
import DownloadOutlinedIcon from "@mui/icons-material/DownloadOutlined";
import MoreDataButton from "./MoreDataButton";
import { fetchSearchData } from "./SearchBar";

/************************************************************************************ */
/* CONFIG API URL- */
/************************************************************************************ */
const baseURL = import.meta.env.VITE_API_URL;
const API_CALL1: string = "/api/getApprovalData";
const API_CALL2: string = "/api/approveDenyRequest";
const API_URL2 = `${baseURL}${API_CALL2}`;
const API_URL1 = `${baseURL}${API_CALL1}`;

/* INTERFACE */
interface ApprovalTableProps {
    onDelete: (ID: number) => void;
    resetTable: () => void;
    searchQuery: string;
}

/************************************************************************************ */
/* FETCHING APPROVAL DATA FUNCTION for useQuery */
/************************************************************************************ */
const fetchApprovalData = async () => {
    const response = await fetch(API_URL1, {
        headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
    });

    if (!response.ok) {
        throw new Error(`HTTP error: ${response.status}`);
    }
    const jsonData = await response.json();
    console.log(jsonData);
    return jsonData;
}

/************************************************************************************ */
/* APPROVALS TABLE */
/************************************************************************************ */
function ApprovalsTable({ searchQuery }: ApprovalTableProps) {
    const queryClient = useQueryClient();
    const {
        data: searchData,
    } = useQuery({
        queryKey: ['search-data', searchQuery],
        queryFn: () => fetchSearchData(searchQuery),
        enabled: !!searchQuery,  // only run when searchQuery exists
    });

    const { data: approvalData } = useQuery({
        queryKey: ['approval_data'],
        queryFn: fetchApprovalData,
        enabled: !searchQuery,
    });

    // if searchQuery exists use searchData otherwise use approvalData
    let retval;
    if (searchQuery) {
        retval = searchData ? searchData : []
    } else {
        retval = approvalData ? approvalData : [];
    }

    // Check if the data is empty and display a message if it is
    /************************************************************************************ */
    /* APPROVE OR DENY */
    /************************************************************************************ */
    // Get the current state of newRequest, approved, and pendingApproval
    async function handleApproveDeny(id: string, status: string) {
        try {
            const response = await fetch(API_URL2, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                },
                body: JSON.stringify({
                    ID: id,
                    status: status,
                })
            });
            if (!response.ok) {
                throw new Error(`HTTP error: ${response.status}`);
            }
            const data = await response.json();

            // Invalidate the query to to trigger a refetch
            queryClient.invalidateQueries({ queryKey: ['approval_data'] });
            return data;
        }
        catch (error) {
            console.error("FetchService.ts", error);
            throw error;
        }
    }

    async function handleDownload() {
        // Handle download action here      
        console.log("Download clicked");
        // Add your logic to download the item
    }
    /************************************************************************************ */
    /* APPROVAL TABLE */

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
                            {/* ITEM DESCRIPTION */}
                            <TableCell
                                sx={{
                                    color: "white",
                                    fontWeight: "bold",
                                    textAlign: "center",
                                }}
                            >

                                ITEM DESCRIPTION
                            </TableCell>

                            {/**************************************************************************/}
                            {/* JUSTIFICATION */}
                            <TableCell
                                sx={{
                                    color: "white",
                                    fontWeight: "bold",
                                    textAlign: "center",
                                }}
                            >

                                JUSTIFICATION
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
                                {/* ITEM DESCRIPTION */}
                                <TableCell sx={{ color: "white", textAlign: "center" }}>
                                        {approval_data.itemDescription}
                                </TableCell>

                                {/**************************************************************************/}
                                {/* JUSTIFICATION */}
                                <TableCell sx={{ color: "white", textAlign: "center" }}>
                                    <MoreDataButton name="Justification" data={approval_data.justification} />
                                </TableCell>

                                {/**************************************************************************/}
                                {/* STATUS */}
                                <TableCell sx={{ color: "white", textAlign: "center" }}>
                                    {approval_data.status}
                                </TableCell>

                                {/**************************************************************************/}
                                {/* APPROVE/DENY BUTTONS */}
                                <TableCell>
                                    <Box sx={{ display: "flex", gap: "10px" }}>
                                        <Button
                                            variant="contained"
                                            color="success"
                                            onClick={() => handleApproveDeny(approval_data.ID, 'approve')}
                                        >
                                            Approve
                                        </Button>
                                        <Button
                                            variant="contained"
                                            color="error"
                                            onClick={() => handleApproveDeny(approval_data.ID, 'deny')}
                                        >
                                            Deny
                                        </Button>
                                        <Button
                                            variant="contained"
                                            color="primary"
                                            onClick={() => handleDownload}
                                        >
                                            <DownloadOutlinedIcon />
                                        </Button>
                                    </Box>
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                    <tfoot>
                        <TableRow>
                            <TableCell colSpan={6}>

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
