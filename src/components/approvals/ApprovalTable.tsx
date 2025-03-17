import { useEffect, useState } from "react";
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
/* CONFIG API URL */
/************************************************************************************ */
const baseURL = import.meta.env.VITE_API_URL;
const API_CALL: string = "/api/getApprovalData";
const API_URL = `${baseURL}${API_CALL}`;
/* INTERFACE */
interface ApprovalTableProps {
    onDelete: (reqID: number) => void;
    resetTable: () => void;
}

function ApprovalsTable({
}: ApprovalTableProps) {
    const [approvalData, setApprovalData] = useState<FormValues[]>([]);

    console.log("API: ", API_URL);
    /************************************************************************************ */
    /* Fetch data from backend to populate Approvals Table */
    /************************************************************************************ */
    useEffect(() => {
        fetch(API_URL)
            .then((res) => {
                if (!res.ok) {
                    throw new Error(`HTTP error: ${res.status}`);
                }

                return res.json();
            })
            .then((data) => {
                console.log("Fetched data:", data);
                // Extract approval_data array
                if (data.approval_data && Array.isArray(data.approval_data)) {
                    setApprovalData(data.approval_data);
                } else {
                    console.error("Unexpect data format:", data);
                }
            })
            .catch((err) => console.error("Error fetching data: ", err));
    }, []); // Empty dependency arr ensure this runs once

    const processedData = approvalData.map((item) => ({
        ...item,
    }));

    /************************************************************************************ */
    /* APPROVE OR DENY */
    /************************************************************************************ */
    const handleApprove = () => {};

    const handleDeny = () => {};

    return (
        <Box sx={{ overflowX: "auto", width: "100%" }}>
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
                            <TableCell
                                sx={{
                                    color: "white",
                                    fontWeight: "bold",
                                    textAlign: "center",
                                }}
                            >
                                REQUISITION ID
                            </TableCell>
                            <TableCell
                                sx={{
                                    color: "white",
                                    fontWeight: "bold",
                                    textAlign: "center",
                                }}
                            >
                                BUDGET OBJECT CODE
                            </TableCell>
                            <TableCell
                                sx={{
                                    color: "white",
                                    fontWeight: "bold",
                                    textAlign: "center",
                                }}
                            >
                                FUND
                            </TableCell>
                            <TableCell
                                sx={{
                                    color: "white",
                                    fontWeight: "bold",
                                    textAlign: "center",
                                }}
                            >
                                LOCATION
                            </TableCell>
                            <TableCell
                                sx={{
                                    color: "white",
                                    fontWeight: "bold",
                                    textAlign: "center",
                                }}
                            >
                                QUANTITY
                            </TableCell>
                            <TableCell
                                sx={{
                                    color: "white",
                                    fontWeight: "bold",
                                    textAlign: "center",
                                }}
                            >
                                PRICE EACH
                            </TableCell>
                            <TableCell
                                sx={{
                                    color: "white",
                                    fontWeight: "bold",
                                    textAlign: "center",
                                }}
                            >
                                ESTIMATED PRICE
                            </TableCell>
                            <TableCell
                                sx={{
                                    color: "white",
                                    fontWeight: "bold",
                                    textAlign: "center",
                                }}
                            >
                                STATUS
                            </TableCell>
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
                        {processedData.map((item) => (
                            <TableRow key={item.reqID}>
                                {/**************************************************************************/}
                                {/* REQUISITION ID */}
                                <TableCell sx={{ color: "white" }}>
                                    {item.reqID}
                                </TableCell>

                                {/**************************************************************************/}
                                {/* BUDGET OBJECT CODE */}
                                <TableCell sx={{ color: "white" }}>
                                    {convertBOC(item.budgetObjCode)}
                                </TableCell>

                                {/**************************************************************************/}
                                {/* FUND */}
                                <TableCell sx={{ color: "white" }}>
                                    {item.fund}
                                </TableCell>

                                {/**************************************************************************/}
                                {/* LOCATION */}
                                <TableCell sx={{ color: "white" }}>
                                    {item.location}
                                </TableCell>

                                {/**************************************************************************/}
                                {/* QUANTITY */}
                                <TableCell
                                    sx={{ color: "white", textAlign: "center" }}
                                >
                                    {item.quantity}
                                </TableCell>

                                {/**************************************************************************/}
                                {/* PRICE */}
                                <TableCell
                                    sx={{ color: "white", textAlign: "center" }}
                                >
                                    {typeof item.priceEach === "number"
                                        ? item.priceEach.toFixed(2)
                                        : "0.00"}
                                </TableCell>

                                {/**************************************************************************/}
                                {/* ESTIMATED PRICE */}
                                <TableCell
                                    sx={{ color: "white", textAlign: "center" }}
                                >
                                    {typeof item.totalPrice === "number"
                                        ? item.totalPrice.toFixed(2)
                                        : "0.00"}
                                </TableCell>
                                {/**************************************************************************/}
                                {/* STATUS */}
                                <TableCell sx={{ color: "white" }}>
                                    {item.status}
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
                                {processedData
                                    .reduce(
                                        (acc, item) =>
                                            acc +
                                            (Number(item.totalPrice) || 0),
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
