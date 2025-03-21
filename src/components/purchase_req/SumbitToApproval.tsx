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
} from "@mui/material";
import { FormValues } from "../../types/formTypes";
import { convertBOC } from "../../utils/bocUtils";
import { IFile } from "../../types/IFile";
import React, { useEffect } from "react";
import UploadFile from "../../services/UploadHandler";

const baseURL = import.meta.env.VITE_API_URL;
const API_CALL: string = "/api/sendToPurchaseReq";
const API_URL = `${baseURL}${API_CALL}`;

/************************************************************************************ */
/* INTERFACE PROPS */
/************************************************************************************ */
interface SubmitApprovalTableProps {
    dataBuffer: FormValues[];
    onDelete: (ID: string) => void;
    ID: string;
    fileInfo: IFile[];
    isSubmitted: boolean;
    setIsSubmitted: React.Dispatch<React.SetStateAction<boolean>>;
    setID: React.Dispatch<React.SetStateAction<string>>;
    setDataBuffer: React.Dispatch<React.SetStateAction<FormValues[]>>;
    setFileInfo: React.Dispatch<React.SetStateAction<IFile[]>>;
}

function SubmitApprovalTable({
    dataBuffer,
    onDelete,
    ID,
    fileInfo,
    isSubmitted,
    setIsSubmitted,
    setDataBuffer,
    setFileInfo
}: SubmitApprovalTableProps) {

    /* Check if table has been submitted */
    useEffect(() => {
        if (isSubmitted) {
            setDataBuffer([]);

            console.log("In the if isSubmitted: dataBuffer==", dataBuffer);
            setIsSubmitted(false);
        }
    }, [isSubmitted, setDataBuffer, setIsSubmitted]);

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

        /* UploadFile is function in UploadHandler that is making the call to the service to
            handle the upload */
        // Find all files not uploaded
        const filesToUpload = fileInfo.filter(file => file.status !== "success");

        if(filesToUpload.length > 0) {
            for(const file of filesToUpload) {
                await UploadFile({ file, ID, setFileInfo });
            }
        }

        // Retrieve access to from local storage
        const accessToken = localStorage.getItem("access_token");
        console.log("TOKEN: ", accessToken);

        // Loop over provessedData and send each request separately
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
                console.error("Error sending data for item", ID, error);
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
                            Line Total
                        </TableCell>
                        <TableCell sx={{ color: "white", fontWeight: "bold" }}>
                            Actions
                        </TableCell>
                    </TableRow>
                </TableHead>
                <TableBody>
                    {processedData.map((item) => (
                        <TableRow key={item.ID}>
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
                                        onDelete(item.ID);
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
                            {/************************************************************************************ */}
                            {/* BUTTONS: SUBMIT/PRINT */}
                            {/************************************************************************************ */}
                            {/* Submit data to proper destination, email to supervisor or notify sup that there's a request for them to approve */}
                            <Buttons
                                label="Submit Form"
                                className=" me-3 btn btn-maroon"
                                disabled={dataBuffer.length === 0}
                                onClick={() => {
                                    handleSubmitData(processedData);
                                    setIsSubmitted(true);
                                    setFileInfo([]);
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
