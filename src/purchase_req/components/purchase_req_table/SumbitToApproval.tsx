import Buttons from "./Buttons";
import {
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Paper,
    Button,
    Box,
    IconButton,
    Collapse,
    Typography,
} from "@mui/material";
import { tableHeaderStyles } from "../../styles/DataGridStyles";
import { FormValues } from "../../types/formTypes";
import { IFile } from "../../types/IFile";
import React, { useState, useMemo, useCallback, useEffect } from "react";
import { v4 as uuidv4 } from 'uuid';
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import KeyboardArrowUpIcon from "@mui/icons-material/KeyboardArrowUp";
import { toast } from "react-toastify";
import { ItemStatus } from "../../types/approvalTypes";
import { OrderType } from "../../schemas/purchaseSchema";
import { isRequestSubmitted, isSubmittedSig } from "../../utils/PrasSignals";

const API_URL = "/api/sendToPurchaseReq";

/************************************************************************************ */
/* INTERFACE PROPS */
/************************************************************************************ */
interface SubmitApprovalTableProps {
    dataBuffer: FormValues[];
    onDelete: (ID: string) => void;
    ID?: string;
    fileInfo: IFile[];
    setID?: React.Dispatch<React.SetStateAction<string>>;
    setDataBuffer: React.Dispatch<React.SetStateAction<FormValues[]>>;
    setFileInfo: React.Dispatch<React.SetStateAction<IFile[]>>;
}

function SubmitApprovalTable({
    dataBuffer,
    onDelete,
    fileInfo,
    setDataBuffer,
    setFileInfo,
    setID
}: SubmitApprovalTableProps) {

    // State for expanded rows
    const [expandedRows, setExpandedRows] = useState<Record<string, boolean>>({});

    // Optimize expensive calculations with useMemo
    const calculatePrice = useCallback((item: FormValues): number => {
        const price = Number(item.priceEach) || 0;
        const quantity = Number(item.quantity) || 1;
        return price * quantity;
    }, []);

    // Preprocess data to calculate price - memoized
    const processedData = useMemo(() => dataBuffer.map((item) => ({
        ...item,
        priceEach: Number(item.priceEach),
        calculatedPrice: calculatePrice(item)
    })), [dataBuffer, calculatePrice]);

    /* Check if data buffer is multiple items */
    const itemCount = dataBuffer.length;

    // Group items by ID - memoized
    const groupedItems = useMemo(() =>
        processedData.reduce<Record<string, FormValues[]>>((acc, item) => {
            (acc[item.ID] = acc[item.ID] || []).push(item);
            return acc;
        }, {}), [processedData]);

    // Optimize toggle function
    const toggleRowExpanded = useCallback((id: string) =>
        setExpandedRows((prev) => ({
            ...prev,
            [id]: !prev[id],
        })), []);

    useEffect(() => {
        if (isSubmittedSig.value) {
            setDataBuffer([]);
            // Don't reset immediately - let the progress bar handle it
            // isSubmittedSig.value = false;
        }
    }, [isSubmittedSig.value, setDataBuffer]);

    /************************************************************************************ */
    /* SUBMIT DATA --- send to backend to add to database */
    /************************************************************************************ */
    const handleSubmitData = async (processedData: FormValues[]) => {

        try {
            // Get a proper ID from the backend
            const idRequest = await fetch(`/api/createNewID`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${localStorage.getItem("access_token")}`,
                },
            });

            if (!idRequest.ok) {
                toast.error("Failed to get ID");
                throw new Error(`Failed to get ID: ${idRequest.status}`);
            }

            const idData = await idRequest.json();
            const requestId = idData.ID;

            // Get the requester from the first item
            const requester = processedData[0]?.requester;
            if (!requester) {
                throw new Error("Requester is required");
            }

            // Process each item in the data buffer
            const processedItems = processedData.map(item => ({
                ID: requestId,
                UUID: item.UUID || uuidv4(),
                IRQ1_ID: item.IRQ1_ID || null,
                requester: item.requester,
                phoneext: String(item.phoneext),
                datereq: item.datereq instanceof Date
                    ? item.datereq.toISOString().split('T')[0]
                    : item.datereq || null,
                dateneed: item.dateneed instanceof Date
                    ? item.dateneed.toISOString().split('T')[0]
                    : item.dateneed || null,
                orderType: item.orderType || OrderType.STANDARD,
                itemDescription: item.itemDescription,
                justification: item.justification,
                trainNotAval: Boolean(item.trainNotAval),
                needsNotMeet: Boolean(item.needsNotMeet),
                quantity: Number(item.quantity),
                priceEach: Number(item.priceEach),
                totalPrice: Number(item.totalPrice) || (Number(item.priceEach) * Number(item.quantity)),
                fund: item.fund,
                location: item.location,
                budgetObjCode: String(item.budgetObjCode).padStart(4, '0'),
                status: ItemStatus.NEW_REQUEST,
                fileAttachments: fileInfo.map(file => ({
                    name: file.name,
                    file: file.file,
                    type: file.file?.type || '',
                    size: file.file?.size || 0
                }))
            }));

            // Create a single object with the requester and items
            const requestData = {
                requester: requester,
                items: processedItems,
                itemCount: itemCount
            };

            const formData = new FormData();
            formData.append("payload_json", JSON.stringify(requestData));

            // Attach files from fileInfo
            fileInfo.forEach(file => {
                if (file.file && file.status === "ready") {
                    formData.append("files", file.file);
                }
            });

            // Send the data to the backend
            const response = await fetch(API_URL, {
                method: "POST",
                headers: {
                    Authorization: `Bearer ${localStorage.getItem("access_token")}`,
                },
                body: formData,
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            // Reset the form and data buffer
            isSubmittedSig.value = true;
            console.log("IS SUBMITTED SIG: ", isSubmittedSig.value);
            setDataBuffer([]);

            // Update the ID if setID is provided
            if (setID) {
                setID(requestId);
            }

        } catch (error) {
            console.error("Error submitting data:", error);
        }
    };

    return (
        <TableContainer
            component={Paper}
            sx={{
                background: " #2c2c2c",
                color: "white", // Ensure text contrast
                borderRadius: "10px",
                overflow: "hidden", // Ensure rounded corners
                width: "100%",
            }}
        >
            <Table sx={{
                width: "100%",
                tableLayout: "auto",
                fontFamily: "'Play', sans-serif !important",
            }}>
                <TableHead
                    sx={{
                        ...tableHeaderStyles,
                        fontFamily: "'Play', sans-serif !important"
                    }}
                >
                    <TableRow sx={{ fontFamily: "'Play', sans-serif !important", fontSize: "1.1rem" }}>
                        <TableCell sx={{ width: 40 }} /> {/* expand/collapse */}
                        <TableCell>ID</TableCell>
                        <TableCell>Budget Object Code</TableCell>
                        <TableCell>Fund</TableCell>
                        <TableCell>Location</TableCell>
                        <TableCell sx={{ fontSize: "1.1rem" }}>Quantity</TableCell>
                        <TableCell>Price Each</TableCell>
                        <TableCell>Line Total</TableCell>
                        <TableCell>Actions</TableCell>
                    </TableRow>
                </TableHead>
                <TableBody>
                    {Object.entries(groupedItems).map(([id, items]) => (
                        <React.Fragment key={id}>
                            {/* Main row with expand/collapse button */}
                            <TableRow><TableCell>
                                {items.length > 1 && (
                                    <IconButton
                                        size="small"
                                        onClick={() => toggleRowExpanded(id)}
                                        sx={{ color: "white" }}
                                    >
                                        {expandedRows[id] ? (
                                            <KeyboardArrowUpIcon />
                                        ) : (
                                            <KeyboardArrowDownIcon />
                                        )}
                                    </IconButton>
                                )}
                            </TableCell>
                                <TableCell sx={{
                                    color: "white",
                                    fontFamily: "'Play', sans-serif !important",
                                    fontSize: "1rem"
                                }}>
                                    {items[0].ID}
                                </TableCell>
                                <TableCell sx={{
                                    color: "white",
                                    fontFamily: "'Play', sans-serif !important",
                                    fontSize: "1rem"
                                }}>
                                    {items[0].budgetObjCode}
                                </TableCell>
                                <TableCell sx={{
                                    color: "white",
                                    fontFamily: "'Play', sans-serif !important",
                                    fontSize: "1rem"
                                }}>
                                    {items[0].fund}
                                </TableCell>
                                <TableCell sx={{
                                    color: "white",
                                    fontFamily: "'Play', sans-serif !important",
                                    fontSize: "1rem"
                                }}>
                                    {items[0].location}
                                </TableCell>
                                <TableCell sx={{
                                    color: "white",
                                    fontFamily: "'Play', sans-serif !important",
                                    fontSize: "1rem"
                                }}>
                                    {items[0].quantity}
                                </TableCell>
                                <TableCell sx={{
                                    color: "white",
                                    fontFamily: "'Play', sans-serif !important",
                                    fontSize: "1rem"
                                }}>
                                    {typeof items[0].priceEach === "number"
                                        ? items[0].priceEach.toFixed(2)
                                        : "0.00"}
                                </TableCell>
                                <TableCell sx={{
                                    color: "white",
                                    fontFamily: "'Play', sans-serif !important",
                                    fontSize: "1rem"
                                }}>
                                    {calculatePrice(items[0]).toFixed(2)}
                                </TableCell>
                                <TableCell>
                                    <Button
                                        variant="contained"
                                        color="error"
                                        onClick={() => {
                                            onDelete(items[0].ID);
                                        }}
                                    >
                                        Delete
                                    </Button>
                                </TableCell></TableRow>

                            {/* Collapsible rows for additional items */}
                            {items.length > 1 && (
                                <TableRow><TableCell
                                    colSpan={9}
                                    sx={{ p: 0, background: "#3c3c3c" }}
                                >
                                    <Collapse
                                        in={expandedRows[id]}
                                        timeout="auto"
                                        unmountOnExit
                                    >
                                        <Box sx={{ m: 2 }}>
                                            <Typography
                                                variant="h6"
                                                gutterBottom
                                                component="div"
                                                sx={{ color: "white" }}
                                            >
                                                Additional Items
                                            </Typography>
                                            <Table size="small" aria-label="additional items">
                                                <TableHead>
                                                    <TableRow>{[
                                                        "ID",
                                                        "Budget Object Code",
                                                        "Fund",
                                                        "Location",
                                                        "Quantity",
                                                        "Price Each",
                                                        "Line Total",
                                                    ].map((label) => (
                                                        <TableCell
                                                            key={label}
                                                            sx={{
                                                                color: "white",
                                                                fontWeight: "bold",
                                                            }}
                                                        >
                                                            {label}
                                                        </TableCell>
                                                    ))}</TableRow>
                                                </TableHead>
                                                <TableBody>
                                                    {items.slice(1).map((item, idx) => (
                                                        <TableRow key={idx}>
                                                            <TableCell sx={{
                                                                color: "white",
                                                                fontFamily: "'Play', sans-serif !important",
                                                                fontSize: "1rem"
                                                            }}>
                                                                {item.ID}
                                                            </TableCell>
                                                            <TableCell sx={{
                                                                color: "white",
                                                                fontFamily: "'Play', sans-serif !important",
                                                                fontSize: "1rem"
                                                            }}>
                                                                {item.budgetObjCode}
                                                            </TableCell>
                                                            <TableCell sx={{
                                                                color: "white",
                                                                fontFamily: "'Play', sans-serif !important",
                                                                fontSize: "1rem"
                                                            }}>
                                                                {item.fund}
                                                            </TableCell>
                                                            <TableCell sx={{
                                                                color: "white",
                                                                fontFamily: "'Play', sans-serif !important",
                                                                fontSize: "1rem"
                                                            }}>
                                                                {item.location}
                                                            </TableCell>
                                                            <TableCell sx={{
                                                                color: "white",
                                                                fontFamily: "'Play', sans-serif !important",
                                                                fontSize: "1rem"
                                                            }}>
                                                                {item.quantity}
                                                            </TableCell>
                                                            <TableCell sx={{
                                                                color: "white",
                                                                fontFamily: "'Play', sans-serif !important",
                                                                fontSize: "1rem"
                                                            }}>
                                                                {typeof item.priceEach === "number"
                                                                    ? item.priceEach.toFixed(2)
                                                                    : "0.00"}
                                                            </TableCell>
                                                            <TableCell sx={{
                                                                color: "white",
                                                                fontFamily: "'Play', sans-serif !important",
                                                                fontSize: "1rem"
                                                            }}>
                                                                {calculatePrice(item).toFixed(2)}
                                                            </TableCell></TableRow>
                                                    ))}
                                                </TableBody>
                                            </Table>
                                        </Box>
                                    </Collapse>
                                </TableCell>
                                </TableRow>
                            )}
                        </React.Fragment>
                    ))}
                </TableBody>

                {/* FOOTER WITH FILE UPLOAD & SUBMIT BUTTON */}
                <TableBody>
                    <TableRow>
                        <TableCell colSpan={6}>
                            {/* Display current files */}
                            {fileInfo.length > 0 && (
                                <Box sx={{ mb: 2 }}>
                                    <Typography variant="subtitle2" sx={{ color: "white" }}>
                                        Attached Files:
                                    </Typography>
                                    <ul style={{ color: "white", listStyle: "none", padding: 0 }}>
                                        {fileInfo.map((file, index) => (
                                            <li key={index}>
                                                {file.name} - {file.status}
                                            </li>
                                        ))}
                                    </ul>
                                </Box>
                            )}

                            {/************************************************************************************ */}
                            {/* BUTTONS: SUBMIT */}
                            {/************************************************************************************ */}
                            {/* Submit data to proper destination, email to supervisor or notify sup that there's a request for them to approve */}
                            <Buttons
                                label="Submit Form"
                                className="me-3 btn btn-maroon"
                                disabled={dataBuffer.length === 0}
                                onClick={() => {
                                    isRequestSubmitted.value = true;
                                    handleSubmitData(processedData);
                                    isSubmittedSig.value = true;
                                    setFileInfo([]);
                                }}
                            />

                        </TableCell>

                        <TableCell
                            colSpan={2}
                            sx={{ color: "white", textAlign: "right" }}
                        ></TableCell>
                        <TableCell
                            colSpan={3}
                            sx={{
                                border: 1,
                                color: "#16fdda",
                                textAlign: "left",
                                fontSize: "1.15rem",
                                fontFamily: "'Play', sans-serif !important"
                            }}
                        >
                            Total: $
                            {processedData
                                .reduce(
                                    (acc, item) =>
                                        acc +
                                        (Number(item.calculatedPrice) || 0),
                                    0
                                )
                                .toFixed(2)}
                        </TableCell>
                    </TableRow>
                </TableBody>
            </Table>
        </TableContainer>
    );
}

export default SubmitApprovalTable;