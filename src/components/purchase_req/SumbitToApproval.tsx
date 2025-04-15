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
import { v4 as uuidv4 } from 'uuid';
import { useQuery, useQueryClient } from "@tanstack/react-query";
const baseURL = import.meta.env.VITE_API_URL;
const API_CALL: string = "/api/sendToPurchaseReq";
const API_URL = `${baseURL}${API_CALL}`;

export const useUUIDStore = () => {
    const queryClient = useQueryClient();
    
    // Get UUIDs from the query cache
    const { data: uuids = {} } = useQuery<Record<string, string>>({
        queryKey: ['uuids'],
        queryFn: () => ({}),
        staleTime: Infinity,
    });
    
    // Set a UUID for a specific ID
    const setUUID = (id: string, uuid: string) => {
        console.log(`Setting UUID for ID ${id}: ${uuid}`);
        queryClient.setQueryData(['uuids'], (oldData: Record<string, string> = {}) => {
            const newData = {
                ...oldData,
                [id]: uuid
            };
            console.log("Updated UUID store:", newData);
            return newData;
        });
    };
    
    // Get a UUID for a specific ID
    const getUUID = (id: string) => {
        const uuid = uuids[id];
        console.log(`Getting UUID for ID ${id}: ${uuid || 'not found'}`);
        return uuid;
    };
    
    return { uuids, setUUID, getUUID };
};

/************************************************************************************ */
/* INTERFACE PROPS */
/************************************************************************************ */
interface SubmitApprovalTableProps {
    dataBuffer: FormValues[];
    onDelete: (ID: string) => void;
    ID?: string;
    fileInfo: IFile[];
    isSubmitted: boolean;
    setIsSubmitted: React.Dispatch<React.SetStateAction<boolean>>;
    setID?: React.Dispatch<React.SetStateAction<string>>;
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
    setFileInfo,
    setID
}: SubmitApprovalTableProps) {

    // Use our custom hook to manage UUIDs
    const { setUUID } = useUUIDStore();

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
        const price = Number(item.priceEach) || 0;
        const quantity = Number(item.quantity) || 1;
        return price * quantity;
    }

    // Preprocess data to calculate price
    const processedData = dataBuffer.map((item) => ({
        ...item,
        priceEach: Number(item.priceEach),
        calculatedPrice: calculatePrice(item)
    }));

    /************************************************************************************ */
    /* SUBMIT DATA --- send to backend to add to database */
    /************************************************************************************ */
    const handleSubmitData = async (processedData: FormValues[]) => {
        try {
            // Use a default ID if not provided
            const requestId = ID || `TEMP-${Date.now()}`;
            
            // Get the requester from the first item
            const requester = processedData[0]?.requester;
            if (!requester) {
                throw new Error("Requester is required");
            }
            
            // Process each item in the data buffer
            const processedItems = processedData.map(item => ({
                ...item,
                ID: requestId,
                UUID: item.UUID || uuidv4()
            }));
            
            // Create a single object with the requester and items
            const requestData = {
                requester: requester,
                items: processedItems
            };
            
            // Send the data to the backend
            const response = await fetch(API_URL, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${localStorage.getItem("access_token")}`,
                },
                body: JSON.stringify(requestData),
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            console.log("Submission result:", result);
            
            // Reset the form and data buffer
            setIsSubmitted(true);
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
            <Table sx={{ width: "100%", tableLayout: "auto" }}>
                <TableHead
                    sx={{
                        background:
                            "linear-gradient(to bottom, #2c2c2c, #800000)",
                    }}
                >
                    <TableRow>
                        <TableCell sx={{ color: "white", fontWeight: "bold" }}>
                            ID
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
                                {item.ID}
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
                                {typeof item.priceEach === "number"
                                    ? item.priceEach.toFixed(2)
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
