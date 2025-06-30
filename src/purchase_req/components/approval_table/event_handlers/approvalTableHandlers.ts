import { useState } from "react";
import { toast } from "react-toastify";
import { useAssignIRQ1 } from "../../../hooks/useAssignIRQ1";
import { GridRowId } from "@mui/x-data-grid";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { DataRow } from "../../../types/approvalTypes";
import React from "react";



/***********************************************************************************/
// PROPS
/***********************************************************************************/
interface ApprovalTableProps {
	onDelete: (ID: string) => void;
	resetTable: () => void;
	searchQuery: string;
}

const queryClient = useQueryClient();
	const [expandedRows, setExpandedRows] = useState<Record<string, boolean>>({});
	const { data: searchData } = useQuery({ queryKey: ["search", searchQuery], queryFn: () => fetchSearchData(searchQuery) });
	const [groupCommentPayload, setGroupCommentPayload] = useState<GroupCommentPayload>({
		groupKey: "",
		comment: [],
		group_count: 0,
		item_uuids: [],
		item_desc: []
	});

	const {
		data: approvalData = [],
		isLoading,
		error,
	} = useQuery<DataRow[]>({
		queryKey: ["approvalData"],
		queryFn: () => fetchApprovalData(),
		staleTime: 0,
		gcTime: 5 * 60 * 1000,
		refetchOnWindowFocus: true,
		refetchOnMount: true,
	});

	// Build grouped map once per load
	const rowsWithUUID: DataRow[] = approvalData.map((r, i) =>
		r.UUID ? r : { ...r, UUID: `row-${i}` }
	);

	const grouped: Record<string, DataRow[]> = rowsWithUUID.reduce((acc, row) => {
		(acc[row.ID] ||= []).push(row);
		return acc;
	}, {} as Record<string, DataRow[]>);

	// Flattened rows
	const flatRows = React.useMemo<FlatRow[]>(() => {
		return Object.entries(grouped).flatMap(([groupKey, items]) => {
			// building header
			const header: FlatRow = {
				...items[0],
				isGroup: true,
				groupKey,
				rowCount: items.length,
				rowId: `header-${groupKey}`,
				UUID: `header-${groupKey}`,
			};

			// build ever child-with hidden flag
			const children: FlatRow[] = items.map(item => ({
				...item,
				isGroup: false,
				groupKey,
				rowCount: items.length,
				rowId: item.UUID,
				UUID: item.UUID,
				hidden: !expandedRows[groupKey]
			}));

			return [header, ...children];
		});
	}, [grouped, expandedRows]);

	// ITEM DESCRIPTION MODAL - for when length is too long
	const [openDesc, setOpenDesc] = useState<boolean>(false);
	const [fullDesc, setFullDesc] = useState<string>("");

	// JUSTIFICATION MODAL - for when length is too long
	const [openJust, setOpenJust] = useState<boolean>(false);
	const [fullJust, setFullJust] = useState<string>("");

	// SELECTED CONTRACTING OFFICER
	const [selectedCO, setSelectedCO] = useState<number | "">("");

	// track which groups are expanded
	const toggleRow = (key: string) => setExpandedRows(prev => ({ ...prev, [key]: !prev[key] }));

	// MUTATION TO ASSIGN IRQ1
	const assignIRQ1Mutation = useAssignIRQ1();

	// track which rows are selected
	const [rowSelectionModel, setRowSelectionModel] =
		useState<{ ids: Set<GridRowId>, type: 'include' | 'exclude' }>({
			ids: new Set(),
			type: 'include',
		});

	// Calculate total items in selected groups
	//  determine first if theres more than 1 UUID, then if there is i need to decide if its already flatten then 
	// flatten if not then count but theres 10 items altogether but this is count 1 if everything is collapsed
	const getTotalSelectedItems = () => {
		if (rowSelectionModel.type === 'exclude') {
			return flatRows.filter(row => !row.isGroup && !rowSelectionModel.ids.has(row.UUID)).length;
		}
		let total = 0;
		const selectedGroupKeys = new Set<string>();
		Array.from(rowSelectionModel.ids).forEach(uuid => {
			const row = flatRows.find(r => r.UUID === uuid);
			if (row && row.isGroup) {
				selectedGroupKeys.add(row.groupKey);
				total += row.rowCount;
			}
		});

		// count selected non-group rows that are NOT part of a selected group
		Array.from(rowSelectionModel.ids).forEach(uuid => {
			const row = flatRows.find(r => r.UUID === uuid);
			if (row && !row.isGroup && !selectedGroupKeys.has(row.groupKey)) {
				total += 1;
			}
		});
		return total;
	}

	


// Global variable to store group comment payload
let groupCommentPayload: GroupCommentPayload = {
	groupKey: "",
	comment: [],
	group_count: 0,
	item_uuids: [],
	item_desc: []
};

// Define a type for the DataGrid sx prop
type DataGridSxProps = {
	bgcolor: string;
	[key: string]: any;
};



/***********************************************************************************/
// FETCH CYBERSECURITY RELATED
/***********************************************************************************/
export async function fetchCyberSecRelated(UUID: string) {
	const response = await fetch(`${API_URL_CYBERSEC_RELATED}/${UUID}`, {
		method: "PUT",
		headers: {
			"Content-Type": "application/json",
			"Authorization": `Bearer ${localStorage.getItem("access_token")}`
		},
		body: JSON.stringify({
			isCyberSecRelated: true
		})
	});
	if (!response.ok) throw new Error(`HTTP ${response.status}`);
	const data = await response.json();
	return data;
}


//####################################################################
// HANDLE CYBERSECURITY RELATED
//####################################################################
export const handleDownload = (ID: string) => { downloadStatementOfNeedForm(ID) };

	// ####################################################################
	// Update assignedIRQ1s when approvalData changes
	const assignedIRQ1s = useMemo(() => {
		const map: Record<string, string> = {};
		approvalData.forEach(r => {
			if (r.IRQ1_ID) map[r.ID] = r.IRQ1_ID;
		});
		return map;
	}, [approvalData]);

	// User edit live in draftIRQ1
	const [draftIRQ1, setDraftIRQ1] = useState<Record<string, string>>(() => ({ ...assignedIRQ1s }));

	/***********************************************************************************/
	// MODALS
	/***********************************************************************************/
	/***********************************************************************************/
	// ITEM DESCRIPTION MODAL
	export const handleOpenDesc = (desc: string) => {
		setFullDesc(desc);
		setOpenDesc(true);
	};

	const handleCloseDesc = () => {
		setOpenDesc(false);
		setFullDesc("");
	};

	/***********************************************************************************/
	// JUSTIFICATION MODAL
	const handleOpenJust = (just: string) => {
		setFullJust(just);
		setOpenJust(true);
	};

	const handleCloseJust = () => {
		setOpenJust(false);
		setFullJust("");
	};

	const {
		processPayload,
		setApprovalPayload,
		setDenialPayload
	} = useApprovalService();

	const {
		isOpen,
		openCommentModal,
		close,
		handleSubmit,
	} = useCommentModal();