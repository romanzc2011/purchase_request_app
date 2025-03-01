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
import React, { useEffect, useState } from "react";
import UploadFile from "../../services/UploadHandler";

const baseURL = import.meta.env.VITE_API_URL;
const API_CALL: string = "/api/sendToPurchaseReq";
const API_URL = `${baseURL}${API_CALL}`;

/************************************************************************************ */
/* INTERFACE PROPS */
/************************************************************************************ */
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
    isSubmitted,
    setFileInfos,
    setIsSubmitted,
    setDataBuffer,
}: SubmitApprovalTableProps) {
    const [isUploading, setIsUploading] = useState(false);

    /* Check if table has been submitted */
    useEffect(() => {
        if (isSubmitted) {
            setDataBuffer([]);

            console.log("In the if isSubmitted: dataBuffer==", dataBuffer);
            setIsSubmitted(false);
        }
    }, [isSubmitted, setDataBuffer, setIsSubmitted]);

    // Check if any file is not uploaded, user may have already uploaded
    const filesPendingUpload = fileInfos.some(
        (file) => file.status !== "success"
    );

    /************************************************************************************ */
    /* CALCULATE PRICE -- helper function to convert price/quantity to number and do
         calculations */
    /************************************************************************************ */
    function calculatePrice(item: FormValues): number {
        const price = Number(item.price) || 0;
        const quantity = Number(item.quantity) || 1;
        return price * quantity;
    }

    // Preprocess data to calculate price
    const processedData = dataBuffer.map((item) => ({
        ...item, // Spread operator, takes all properties from item object and puts them in new object being created with .map() callback
        calculatedPrice: calculatePrice(item),
    }));

    /************************************************************************************ */
    /* SUBMIT DATA --- send to backend to add to database */
    /************************************************************************************ */
    const handleSubmitData = async (processedData: FormValues[]) => {
        // Find all files not uploaded
        const filesToUpload = fileInfos.filter(
            (file) => file.status !== "success"
        );

        if (filesToUpload.length > 0) {
            console.log("Uploading remaining files");
            setIsUploading(true);

            // Upload all pending files
            for (const file of filesToUpload) {
                console.log("Uploading file");
                UploadFile({ file, reqID, setFileInfos });
            }

            setIsUploading(false); // Uploading done
            return;
        }

        // Retrieve access to from local storage
        const accessToken = localStorage.getItem("access_token");
        console.log("TOKEN: ", accessToken);

        // Loop over provessedData and send element separately
        for (const item of processedData) {
            try {
                const response = await fetch(API_URL, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${accessToken}`,
                    },
                    body: JSON.stringify(item),
                });

                if (!response.ok) {
                    throw new Error(`HTTP error: ${response.status}`);
                }

                const data = await response.json();
                console.log("Response from POST request:", data);
            } catch (error) {
                console.error("Error sending data for item", reqID, error);
            }
        }
        setIsSubmitted(true);
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
                                {typeof item.price === "number"
                                    ? item.price.toFixed(2)
                                    : "0.00"}
                            </TableCell>
                            <TableCell sx={{ color: "white" }}>
                                {typeof item.calculatedPrice === "number"
                                    ? item.calculatedPrice.toFixed(2)
                                    : "0.00"}
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
                                    handleSubmitData(processedData);
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
