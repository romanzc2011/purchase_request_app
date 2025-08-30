import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { ApprovalData, DataRow, DenialData } from "../types/approvalTypes";
import { approveDenyRequest } from "../services/ApprovalService";
import { toast } from "react-toastify";
import { useCommentModal } from "./useCommentModal";

export function useApprovalService() {
    const [approvalPayload, setApprovalPayload] = useState<ApprovalData | null>(null);
    const [denialPayload, setDenialPayload] = useState<DenialData | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const queryClient = useQueryClient();
	  // const assignIRQ1Mutation = useAssignIRQ1();
	const { openCommentModal, close, handleSubmit } = useCommentModal();
	
    /* The approvalPayload is used to store the payload that will be sent to the server
    The approval payload will be coming in from ApprovalTable as approvalPayload. We will then 
    process the data the same way we did with comments, we want the same behavior */

	//####################################################################
	// HANDLE UPDATE PROCESS ROW (PRICE EACH)
	//####################################################################
	const handleProcessRowUpdate = async (newRow: DataRow, oldRow: DataRow) => {
		console.log("Processing row update", { newRow, oldRow });

		try {
			// Update the approval data in the query cache
			queryClient.setQueryData(["approvalData"], (oldData: DataRow[] | undefined) => {
				if (!oldData) return oldData;
				return oldData.map(row => row.UUID === newRow.UUID ? newRow : row);
			});

			// Optionally, you can also call an API to persist the change
			// await updatePriceEachAPI(newRow.UUID, newRow.priceEach);

			toast.success("Price updated successfully");
		return newRow;
		} catch (error) {
			console.error("Failed to update price:", error);
			toast.error("Failed to update price");
			throw error; // This will revert the cell to the old value
		}
	};

    // PROCESS PAYLOAD
    // This function is called when the user clicks on the approve/deny button
    // It takes the payload as an argument and sends it to the server
    // processPayload --> approveDenyRequest (ApprovalService.ts)
    const processPayload = async (payload: ApprovalData | DenialData) => {
        setIsLoading(true);
        setError(null);
        try {
            const response = await approveDenyRequest(payload);
            console.log("🔥 APPROVE/DENY RESPONSE", response);
            return response;
        } catch (error) {
            setError("Failed to approve/deny request");
            console.error("Error approving/denying request:", error);
        } finally {
            setIsLoading(false);
        }
    }
    return { 
		isLoading, 
		error, 
		processPayload, 
		approvalPayload, 
		setApprovalPayload, 
		denialPayload, 
		setDenialPayload, 
		handleProcessRowUpdate, 
		openCommentModal, 
		close, 
		handleSubmit 
	};
}

