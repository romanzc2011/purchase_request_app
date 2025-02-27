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
} from "@mui/material";
import ReportProblemIcon from "@mui/icons-material/ReportProblem";
import { FormValues } from "../../types/formTypes";
import { convertBOC } from "../../utils/bocUtils";
import { IFile } from "../../types/IFile";
import React, { useState } from "react";
import { uploadFile } from "../../services/FileUploadHandler";

let API_URL: string = `https://${window.location.hostname}:5002/api/sendToPurchaseReq`;

/* INTERFACE */
interface SubmitApprovalTableProps {
    dataBuffer: FormValues[];
    onDelete: (reqID: string) => void;
    fileInfos: IFile[];
    reqID: string;
    isSubmitted: boolean;
    setFileInfos: React.Dispatch<React.SetStateAction<IFile[]>>;
    setIsSubmitted: React.Dispatch<React.SetStateAction<boolean>>;
    setReqID: React.Dispatch<React.SetStateAction<string>>;
    setDataBuffer: React.Dispatch<React.SetStateAction<FormValues[]>>;
}

function SubmitApprovalTable({
    dataBuffer,
    onDelete,
    reqID,
    fileInfos,
    setFileInfos,
    setIsSubmitted,
}: SubmitApprovalTableProps) {
    const [isUploading, setIsUploading] = useState(false);

    // Check if any file is not uploaded, user may have already uploaded
    const filesPendingUpload = fileInfos.some(
        (file) => file.status !== "success"
    );

    // Preprocess data to calculate price
    const processedData = dataBuffer.map((item) => ({
        ...item,
        calculatedPrice: (item.price || 0) * (item.quantity || 1), // Calculating based on quantity
    }));

    /************************************************************************************ */
    /* SUBMIT DATA --- send to backend to add to database */
    /************************************************************************************ */
    const handleSubmitData = (dataBuffer: FormValues[]) => {
        // Find all files not uploaded
        const filesToUpload = fileInfos.filter(
            (file) => file.status !== "success"
        );

        if (filesToUpload.length > 0) {
            console.log("Uploading remaining files");
            setIsUploading(true);

            // Upload all pending files
            for (const file of filesToUpload) {
                uploadFile(file, reqID, setFileInfos);
            }

            setIsUploading(false); // Uploading done
            return;
        }

        // Retrieve access to from local storage
        const accessToken = localStorage.getItem("access_token");
        console.log("TOKEN: ", accessToken);
        fetch(API_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${accessToken}`,
            },

            body: JSON.stringify({ dataBuffer }),
        })
            .then((res) => {
                if (!res.ok) {
                    throw new Error(`HTTP error: ${res.status}`);
                }
                return res.json();
            })
            .then((data) => {
                console.log("Response from POST request: ", data);

            })
            .catch((err) => console.error("Error sending data:", err));
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
            <Table sx={{ width: "100%", tableLayout: "auto" }}>
                <TableHead
                    sx={{
                        background:
                            "linear-gradient(to bottom, #2c2c2c, #800000)",
                    }}
                >
                    <TableRow>
                        <TableCell sx={{ color: "white", fontWeight: "bold" }}>
                            Requisition ID
                        </TableCell>
                        <TableCell sx={{ color: "white", fontWeight: "bold" }}>
                            Budget Object Code
                        </TableCell>
                        <TableCell sx={{ color: "white", fontWeight: "bold" }}>
                            Fund
                        </TableCell>
                        <TableCell sx={{ color: "white", fontWeight: "bold" }}>
                            Location
                        </TableCell>
                        <TableCell sx={{ color: "white", fontWeight: "bold" }}>
                            Quantity
                        </TableCell>
                        <TableCell sx={{ color: "white", fontWeight: "bold" }}>
                            Price Each
                        </TableCell>
                        <TableCell sx={{ color: "white", fontWeight: "bold" }}>
                            Estimated Price
                        </TableCell>
                        <TableCell sx={{ color: "white", fontWeight: "bold" }}>
                            Actions
                        </TableCell>
                    </TableRow>
                </TableHead>
                <TableBody>
                    {processedData.map((item) => (
                        <TableRow key={item.reqID}>
                            <TableCell sx={{ color: "white" }}>
                                {item.reqID}
                            </TableCell>
                            <TableCell sx={{ color: "white" }}>
                                {convertBOC(item.budgetObjCode)}
                            </TableCell>
                            <TableCell sx={{ color: "white" }}>
                                {item.fund}
                            </TableCell>
                            <TableCell sx={{ color: "white" }}>
                                {item.location}
                            </TableCell>
                            <TableCell sx={{ color: "white" }}>
                                {item.quantity}
                            </TableCell>
                            <TableCell sx={{ color: "white" }}>
                                {Number(item.price).toFixed(2)}
                            </TableCell>
                            <TableCell sx={{ color: "white" }}>
                                {item.calculatedPrice.toFixed(2)}
                            </TableCell>
                            <TableCell>
                                <Button
                                    variant="contained"
                                    color="error"
                                    onClick={() => {
                                        onDelete(item.reqID);
                                    }}
                                >
                                    Delete
                                </Button>
                            </TableCell>
                        </TableRow>
                    ))}
                </TableBody>

                {/* FOOTER WITH FILE UPLOAD & SUBMIT BUTTON */}
                <tfoot>
                    <TableRow>
                        <TableCell colSpan={4}>
                            {/* Show a warning if files are pending upload */}
                            {filesPendingUpload && (
                                <Box
                                    sx={{
                                        display: "flex",
                                        alignItems: "center",
                                        mb: 2,
                                    }}
                                >
                                    <ReportProblemIcon
                                        sx={{ color: "gold", fontSize: 16 }}
                                    />
                                    <Box
                                        component="span"
                                        sx={{
                                            color: "red",
                                            fontWeight: "bold",
                                            marginLeft: 1,
                                        }}
                                    >
                                        Some files are not uploaded yet. Upload
                                        them before submitting.
                                    </Box>
                                </Box>
                            )}

                            {/************************************************************************************ */}
                            {/* BUTTONS: SUBMIT/PRINT */}
                            {/************************************************************************************ */}
                            {/* Submit data to proper destination, email to supervisor or notify sup that there's a request for them to approve */}
                            <Buttons
                                label="Submit Form"
                                className=" me-3 btn btn-maroon"
                                disabled={
                                    dataBuffer.length === 0 ||
                                    filesPendingUpload ||
                                    isUploading
                                }
                                onClick={() => {
                                    handleSubmitData(dataBuffer);
                                    setIsSubmitted(true);
                                }}
                            />

                            {/* This button will print out item Request */}
                            <Buttons
                                label="Print Form"
                                className="btn btn-maroon"
                            />
                        </TableCell>

                        <TableCell
                            colSpan={2}
                            sx={{ color: "white", textAlign: "right" }}
                        ></TableCell>
                        <TableCell
                            colSpan={2}
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
                                        (Number(item.calculatedPrice) || 0),
                                    0
                                )
                                .toFixed(2)}
                        </TableCell>
                    </TableRow>
                </tfoot>
            </Table>
        </TableContainer>
    );
}

export default SubmitApprovalTable;