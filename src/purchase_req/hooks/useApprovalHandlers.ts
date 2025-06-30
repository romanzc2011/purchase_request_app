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

export function useApprovalHandlers() {
	

	const [expandedRows, setExpandedRows] = useState<Record<string, boolean>>({});
	const [openDesc, setOpenDesc] = useState(false);
	const [fullDesc, setFullDesc] = useState("");
	const [openJust, setOpenJust] = useState(false);
	const [fullJust, setFullJust] = useState("");
	const [isOpen, setIsOpen] = useState(false);
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
		assignIRQ1Mutation,
		processPayload,
		setApprovalPayload,
		setDenialPayload,
		openCommentModal,
		close,
		handleSubmit,
		rowSelectionModel,
		setRowSelectionModel,
		handleProcessRowUpdate,
		handleAssignCO,
	};
}
