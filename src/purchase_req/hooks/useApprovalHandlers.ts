// hooks/useApprovalHandlers.ts
import { useState } from "react";
import { toast } from "react-toastify";
import { useQueryClient } from "@tanstack/react-query";
import { useAssignIRQ1 } from "./useAssignIRQ1";
import { useCommentModal } from "./useCommentModal";
import { useApprovalService } from "./useApprovalService";
import { GridRowId } from "@mui/x-data-grid";
import { DataRow } from "../types/approvalTypes";

// API URLs
const API_URL_STATEMENT_OF_NEED_FORM = `${import.meta.env.VITE_API_URL}/api/downloadStatementOfNeedForm`;
const API_URL_ASSIGN_CO = `${import.meta.env.VITE_API_URL}/api/assignCO`;
const API_URL_UPDATE_PRICES = `${import.meta.env.VITE_API_URL}/api/updatePrices`;

// #########################################################################################
// FETCH APPROVAL DATA
// #########################################################################################
async function fetchApprovalData(ID?: string) {
	const API_URL_APPROVAL_DATA = `${import.meta.env.VITE_API_URL}/api/getApprovalData`;

	if (ID) {
		const response = await fetch(`${API_URL_APPROVAL_DATA}?ID=${ID}`, {
		method: "GET",
		headers: {
			"Authorization": `Bearer ${localStorage.getItem("access_token")}`
		}
	});
		if (!response.ok) throw new Error(`HTTP ${response.status}`);
		const data = await response.json();
		return data;
	} else {
	const response = await fetch(API_URL_APPROVAL_DATA, {
	headers: {
		"Authorization": `Bearer ${localStorage.getItem("access_token")}`
	}
	});
		if (!response.ok) throw new Error(`HTTP ${response.status}`);
		const data = await response.json();
		return data;
	}
}

// #########################################################################################
// DOWNLOAD STATEMENT OF NEED FORM
// #########################################################################################
async function downloadStatementOfNeedForm(ID: string) {
try {
	// fetch approval data
	const approvalData = await fetchApprovalData(ID);

	// Ensure approvalData is an array
	const approvalDataArray = Array.isArray(approvalData) ? approvalData : [approvalData];

	// send approval data to backend
	const response = await fetch(API_URL_STATEMENT_OF_NEED_FORM, {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
			Authorization: `Bearer ${localStorage.getItem("access_token")}`
		},
		body: JSON.stringify({
			ID,
			approvalData: approvalDataArray
		})
	});
		if (!response.ok) throw new Error(`HTTP ${response.status}`);

		// Get the blob response
		const blob = await response.blob();

		// Create a URL for the blob
		const blobUrl = URL.createObjectURL(blob);

		// Create temporary link element
		const link = document.createElement("a");
		link.href = blobUrl;
		link.download = `statement_of_need-${ID}.pdf`;

		// Append to body
		document.body.appendChild(link);

		// Trigger download
		link.click();

		// Cleanup
		document.body.removeChild(link);
		URL.revokeObjectURL(blobUrl);
	} catch (error) {
		console.error("Error downloading statement of need form:", error);
		toast.error("Failed to download statement of need form. Please try again.");
	}
}

// #########################################################################################
// UPDATE PRICE EACH/ TOTAL PRICE
// #########################################################################################
async function updatePriceEachTotalPrice(
	purchase_request_id: string, 
	item_uuid: string, 
	newPriceEach: number, 
	newTotalPrice: number) {
	const response = await fetch(API_URL_UPDATE_PRICES, {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
			Authorization: `Bearer ${localStorage.getItem("access_token")}`
		},
		body: JSON.stringify({
			purchase_request_id,
			item_uuid,
			newPriceEach,
			newTotalPrice
		})
	});
	if (!response.ok) throw new Error(`HTTP ${response.status}`);
	
	return response.json();
}

// #########################################################################################
// APPROVAL HANDLERS HOOK
// #########################################################################################
export function useApprovalHandlers() {
	const queryClient = useQueryClient();
	const assignIRQ1Mutation = useAssignIRQ1();
	const {
		processPayload,
		setApprovalPayload,
		setDenialPayload
	} = useApprovalService();

	const {
		isOpen,
		openCommentModal,
		close,
		handleSubmit
	} = useCommentModal();

	const [expandedRows, setExpandedRows] = useState<Record<string, boolean>>({});
	const [openDesc, setOpenDesc] = useState(false);
	const [fullDesc, setFullDesc] = useState("");
	const [openJust, setOpenJust] = useState(false);
	const [fullJust, setFullJust] = useState("");
	const [rowSelectionModel, setRowSelectionModel] = useState<{ ids: Set<GridRowId>, type: 'include' | 'exclude' }>({
		ids: new Set(),
		type: 'include',
	});

	const toggleRow = (key: string) => setExpandedRows(prev => ({ ...prev, [key]: !prev[key] }));

	const handleOpenDesc = (desc: string) => {
		setFullDesc(desc);
		setOpenDesc(true);
	};
	const handleCloseDesc = () => {
		setOpenDesc(false);
		setFullDesc("");
	};

	const handleOpenJust = (just: string) => {
		setFullJust(just);
		setOpenJust(true);
	};
	const handleCloseJust = () => {
		setOpenJust(false);
		setFullJust("");
	};

	const handleDownload = (ID: string) => downloadStatementOfNeedForm(ID);

	//####################################################################
	// HANDLE EDIT PRICE EACH ROW
	//####################################################################
	const handleEditPriceEach = async (newRow: DataRow, oldRow: DataRow) => {
		console.log("Processing row update", { newRow, oldRow });
		const newPriceEach = newRow.priceEach;
		const quantity = newRow.quantity;
		const newTotalPrice = newPriceEach * quantity;

		return { ...newRow, priceEach: newPriceEach, totalPrice: newTotalPrice };
	};

	//####################################################################
	// HANDLE CONTRACTING OFFICER
	//####################################################################
	async function handleAssignCO(officerId: number, username: string) {
		console.log("Assigning CO to selected items", { officerId, username });

		try {
			const response = await fetch(API_URL_ASSIGN_CO, {
				method: "POST",
				headers: {
					"Authorization": `Bearer ${localStorage.getItem("access_token")}`,
					"Content-Type": "application/json"
				},
				body: JSON.stringify({
					request_ids: Array.from(rowSelectionModel.ids),
					contracting_officer_id: officerId,
					contracting_officer: username
				})
			});

			if (!response.ok) {
				throw new Error("Failed to assign CO");
			}

			toast.success("CO assigned successfully");
			queryClient.invalidateQueries({ queryKey: ["approvalData"] });
		} catch (error) {
			console.error("Failed to assign CO:", error);
			toast.error("Failed to assign CO");
		}
	}

	return {
		expandedRows,
		openDesc,
		fullDesc,
		openJust,
		fullJust,
		isOpen,
		toggleRow,
		handleOpenDesc,
		handleCloseDesc,
		handleOpenJust,
		handleCloseJust,
		handleDownload,
		handleEditPriceEach,
		assignIRQ1Mutation,
		processPayload,
		setApprovalPayload,
		setDenialPayload,
		openCommentModal,
		close,
		handleSubmit,
		rowSelectionModel,
		setRowSelectionModel,
		handleAssignCO,
		updatePriceEachTotalPrice,
	};
}
