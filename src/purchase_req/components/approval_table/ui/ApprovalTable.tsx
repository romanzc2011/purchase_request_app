import React, { useState, useEffect, useMemo, useCallback, useRef } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import 'react-toastify/dist/ReactToastify.css';
import { Box, Typography, Button, Modal, TextField } from "@mui/material";
import { DataGrid, GridColDef, GridRowId } from "@mui/x-data-grid";
import DownloadOutlinedIcon from "@mui/icons-material/DownloadOutlined";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import KeyboardArrowUpIcon from "@mui/icons-material/KeyboardArrowUp";
import { fetchSearchData } from "./SearchBar";
import Buttons from "../../purchase_req_table/Buttons";
import { convertBOC } from "../../../utils/bocUtils";
import { useAssignIRQ1 } from "../../../hooks/useAssignIRQ1";
import { useCommentModal } from "../../../hooks/useCommentModal";
import CommentIcon from '@mui/icons-material/Comment';
import CheckIcon from "@mui/icons-material/Check";
import MemoryIcon from '@mui/icons-material/Memory';
import CloseIcon from "@mui/icons-material/Close";
import SearchIcon from "@mui/icons-material/Search";
import CommentModal from "../modals/CommentModal";
import "../../../styles/ApprovalTable.css"

import { GroupCommentPayload, CommentEntry, STATUS_CONFIG, type DataRow, type FlatRow, ApprovalData, ItemStatus, DenialData } from "../../../types/approvalTypes";
import { addComments } from "../../../services/CommentService";
import { cellRowStyles, headerStyles, footerStyles, paginationStyles } from "../../../styles/DataGridStyles";
import { useApprovalService } from "../../../hooks/useApprovalService";
import { useApprovalHandlers } from "../../../hooks/useApprovalHandlers";
import { toast, Id } from "react-toastify";
import { isDownloadSig } from "../../../utils/PrasSignals";


/***********************************************************************************/
// PROPS
/***********************************************************************************/
interface ApprovalTableProps {
    onDelete: (ID: string) => void;
    resetTable: () => void;
    searchQuery: string;
    onClearSearch?: () => void;
}

/* API URLs */
const API_URL_APPROVAL_DATA = `${import.meta.env.VITE_API_URL}/api/getApprovalData`;
const API_URL_CYBERSEC_RELATED = `${import.meta.env.VITE_API_URL}/api/cyberSecRelated`;
const API_URL_ASSIGN_CO = `${import.meta.env.VITE_API_URL}/api/assignCO`;
const API_URL_STATEMENT_OF_NEED_FORM = `${import.meta.env.VITE_API_URL}/api/downloadStatementOfNeedForm`;

// Define a type for the DataGrid sx prop
type DataGridSxProps = {
    bgcolor: string;
    [key: string]: any;
};

/***********************************************************************************/
// FETCH APPROVAL DATA
/***********************************************************************************/
async function fetchApprovalData(ID?: string) {
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

/***********************************************************************************/
// FETCH CYBERSECURITY RELATED
/***********************************************************************************/
async function fetchCyberSecRelated(UUID: string) {
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
/***********************************************************************************/
// FETCH/DOWNLOAD STATEMENT OF NEED FORM - also send approval data to backend - download form
/***********************************************************************************/
async function downloadStatementOfNeedForm(ID: string) {
    try {
        // fetch approval data
        console.log("FETCHING APPROVAL DATA");
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
/***********************************************************************************/
// APPROVAL TABLE
/***********************************************************************************/
export default function ApprovalTableDG({ searchQuery, onClearSearch }: ApprovalTableProps) {
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

    // ADD THIS: rowSelectionModel state
    const [rowSelectionModel, setRowSelectionModel] = useState<{ ids: Set<GridRowId>, type: 'include' | 'exclude' }>({
        ids: new Set(),
        type: 'include',
    });

    // ADD THIS: Modal state for description and justification
    const [openDesc, setOpenDesc] = useState(false);
    const [fullDesc, setFullDesc] = useState("");
    const [openJust, setOpenJust] = useState(false);
    const [fullJust, setFullJust] = useState("");

    // ADD THIS: toggleRow function for group expand/collapse
    const toggleRow = useCallback((groupKey: string) => {
        setExpandedRows(prev => ({ ...prev, [groupKey]: !prev[groupKey] }));
    }, []);

    // assignIRQ1Mutation from useAssignIRQ1
    const assignIRQ1Mutation = useAssignIRQ1();

    // ref for IRQ1 input field
    const irq1InputRef = useRef<Record<string, HTMLInputElement | null>>({});

    const [selectedCO, setSelectedCO] = useState<number | "">(1); // Change 1 to default CO's ID

    // Get handleEditPriceEach from useApprovalHandlers
    const { handleEditPriceEach } = useApprovalHandlers(rowSelectionModel);

    const {
        data: approvalData = [],
    } = useQuery<DataRow[]>({
        queryKey: ["approvalData"],
        queryFn: () => fetchApprovalData(),
        staleTime: 0,
        gcTime: 5 * 60 * 1000,
        refetchOnWindowFocus: true,
        refetchOnMount: true,
    });

    // Filter approval data based on search results - EXCLUSIVE SEARCH
    const filteredApprovalData = useMemo(() => {

        // If no search query, show all data
        if (!searchQuery || !searchData || searchData.length === 0) {
            return approvalData;
        }

        // Extract IDs from search results - check different possible field names
        const searchResultIds = new Set();
        searchData.forEach((item: any) => {
            if (item.ID) searchResultIds.add(item.ID);
            if (item.id) searchResultIds.add(item.id);
            if (item.purchase_request_id) searchResultIds.add(item.purchase_request_id);
        });

        // EXCLUSIVE FILTERING: Only show items that match search results
        const filtered = approvalData.filter(item => searchResultIds.has(item.ID));

        return filtered;
    }, [approvalData, searchData, searchQuery]);

    // Optimize expensive calculations with useMemo
    const rowsWithUUID = useMemo(() =>
        filteredApprovalData.map((r, i) =>
            r.UUID ? r : { ...r, UUID: `row-${i}` }
        ), [filteredApprovalData]);

    const grouped = useMemo(() => {
        return rowsWithUUID.reduce((acc, row) => {
            (acc[row.ID] ||= []).push(row);
            return acc;
        }, {} as Record<string, DataRow[]>);
    }, [rowsWithUUID]);

    /* Flatten the rows so the data can be displayed as a list for
    for expand/collapsed functionality */
    const flatRows = React.useMemo<FlatRow[]>(() => {
        return Object.entries(grouped).flatMap(([groupKey, items]) => {
            // If there's only one item, emit it as a normal row (no header)
            if (items.length === 1) {
                const item = items[0];
                return [{
                    ...item,
                    isGroup: false,
                    groupKey,
                    rowCount: 1,
                    rowId: item.UUID,
                    UUID: item.UUID,
                    hidden: false
                }];
            }

            // For real groups (2+ items) emit a synthetic header + its children
            const header: FlatRow = {
                ...items[0],
                isGroup: true,
                groupKey,
                rowCount: items.length,
                rowId: `header-${groupKey}`,
                UUID: `header-${groupKey}`
            };

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

    // Optimize event handlers with useCallback
    const getTotalSelectedItems = useCallback(() => {
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
    }, [flatRows, rowSelectionModel]);

    // ####################################################################
    // ####################################################################
    // COMMAND TOOLBAR
    // Handle Approval/Deny/Download/Comment
    // ####################################################################
    // ####################################################################

    const handleDownload = useCallback(async (ID: string) => {
        try {
            isDownloadSig.value = true;
            console.log("IS DOWNLOADING: ", isDownloadSig);
            await downloadStatementOfNeedForm(ID);
        } catch (err) {
            console.error("Error: ", err);
        }
    }, []);

    // ####################################################################
    // Update assignedIRQ1s when approvalData changes
    const assignedIRQ1s = useMemo(() => {
        const map: Record<string, string> = {};
        filteredApprovalData.forEach(r => {
            if (r.IRQ1_ID) map[r.ID] = r.IRQ1_ID;
        });

        return map;
    }, [filteredApprovalData]);

    // User edit live in draftIRQ1 - update when assignedIRQ1s changes
    const [draftIRQ1, setDraftIRQ1] = useState<Record<string, string>>({});

    // Update draftIRQ1 when assignedIRQ1s changes
    useEffect(() => {
        setDraftIRQ1(prev => ({ ...prev, ...assignedIRQ1s }));
    }, [assignedIRQ1s]);

    /***********************************************************************************/
    // MODALS
    /***********************************************************************************/
    /***********************************************************************************/
    // ITEM DESCRIPTION MODAL
    const handleOpenDesc = useCallback((desc: string) => {
        setFullDesc(desc);
        setOpenDesc(true);
    }, []);

    const handleCloseDesc = useCallback(() => {
        setOpenDesc(false);
        setFullDesc("");
    }, []);

    /***********************************************************************************/
    // JUSTIFICATION MODAL
    const handleOpenJust = useCallback((just: string) => {
        setFullJust(just);
        setOpenJust(true);
    }, []);

    const handleCloseJust = useCallback(() => {
        setOpenJust(false);
        setFullJust("");
    }, []);

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

    /***********************************************************************************/
    // HANDLE APPROVE
    /***********************************************************************************/

    // HANDLE APPROVE CLICK
    async function handleApproveClick(): Promise<void> {
        // Filter out header rows
        const selectedItemUuids = Array.from(rowSelectionModel.ids).filter(
            id => !String(id).startsWith("header-")
        );

        if (selectedItemUuids.length === 0) {
            toast.error("No items selected");
            return;
        }

        // From main data source of filteredApprovalData, find DataRow objects with UUIDs that
        // are a NEW REQUEST or PENDING
        const itemsToProcessForApproval = filteredApprovalData.filter(item =>
            selectedItemUuids.includes(item.UUID) &&
            (item.status === ItemStatus.NEW_REQUEST || item.status === ItemStatus.PENDING_APPROVAL)
        );

        if (itemsToProcessForApproval.length === 0) {
            toast.error("No items selected for approval");
            return;
        }

        // Reconstruct the payload for API call
        // This will tell the backend what action to take
        const apiPayload: ApprovalData = {
            ID: itemsToProcessForApproval[0].ID,
            item_uuids: itemsToProcessForApproval.map(item => item.UUID),
            item_funds: itemsToProcessForApproval.map(item => item.fund),
            totalPrice: itemsToProcessForApproval.map(item => item.totalPrice),
            target_status: itemsToProcessForApproval.map(item => ItemStatus.PENDING_APPROVAL), // Change to this if conditions met in backend
            action: "APPROVE"
        }

        // Calling the processPayload function to send the payload to the backend
        try {
            await processPayload(apiPayload);
            toast.success("Batch approval successful");

            // Invalidate the query to refresh the data, updates local
            // state and re-renders the table
            queryClient.invalidateQueries({ queryKey: ["approvalData"] });
        } catch (error) {
            console.error("Batch approval failed:", error);
            toast.error("Batch approval failed");
        }
        // Deselect all rows
        setRowSelectionModel({ ids: new Set(), type: 'include' });
    }

    /***********************************************************************************/
    // HANDLE COMMENT
    /***********************************************************************************/
    const handleCommentClick = async () => {
        if (!groupCommentPayload) return;

        const { groupKey, item_uuids, item_desc, group_count } = groupCommentPayload;
        const entries: CommentEntry[] = [];

        // Loop through this and get the comment for each item
        for (let i = 0; i < group_count; i++) {
            const uuid = item_uuids[i];
            const desc = item_desc[i];

            // Skip if this is a group header
            if (uuid.startsWith('header-')) continue;

            const singlePayLoad: GroupCommentPayload = {
                groupKey,
                item_uuids: [uuid],
                item_desc: [desc],
                group_count: 1,
                comment: []
            }

            const userComment = await openCommentModal(singlePayLoad);
            entries.push({ uuid, comment: userComment });
        }

        const payloadToSend = {
            ...groupCommentPayload,
            comment: entries
        }

        // Deselect all rows
        setRowSelectionModel({ ids: new Set(), type: 'include' });

        await addComments(payloadToSend);
        toast.success("Comments added successfully");
    };

    // ------------------------------------------------------------------
    // HANDLE DENY
    // ------------------------------------------------------------------
    async function handleDenyClick(): Promise<void> {
        const selectedItemUuids = Array.from(rowSelectionModel.ids).filter(
            id => !String(id).startsWith("header-")
        );

        if (selectedItemUuids.length === 0) {
            toast.error("No items selected");
            console.error("No items selected");
            return;
        }

        const itemsToProcessForDenial = filteredApprovalData.filter(item =>
            selectedItemUuids.includes(item.UUID) &&
            (item.status === ItemStatus.NEW_REQUEST || item.status === ItemStatus.PENDING_APPROVAL)
        );

        if (itemsToProcessForDenial.length === 0) {
            toast.error("No items selected for denial");
        }

        // Construct small payload of uuids to deny
        const apiDenyPayload: DenialData = {
            ID: itemsToProcessForDenial[0].ID,
            item_uuids: itemsToProcessForDenial.map(item => item.UUID),
            target_status: itemsToProcessForDenial.map(item => ItemStatus.DENIED),
            action: "DENY"
        }

        // Calling the processPayload function to send the payload to the backend
        try {
            await processPayload(apiDenyPayload);
            toast.success("Batch denial successful");

            // Invalidate the query to refresh the data, updates local
            // state and re-renders the table
            queryClient.invalidateQueries({ queryKey: ["approvalData"] });
        } catch (error) {
            console.error("Batch denial failed: ", error);
            toast.error("Batch denial failed");
        }
        // Deselect all rows
        setRowSelectionModel({ ids: new Set(), type: 'include' });
    }

    //####################################################################
    // HANDLE CYBERSECURITY RELATED
    //####################################################################
    async function handleCyberSecRow(row: DataRow) {
        // Use the UUID that's already in the row data instead of fetching it
        const uuid = row.UUID;
        if (!uuid) {
            toast.error("No UUID found for this row");
            console.error("No UUID found for this row");
            return;
        }
        try {
            await fetchCyberSecRelated(uuid);
            toast.success("Cybersecurity related updated");
        } catch (error) {
            console.error("Failed to update cybersecurity related:", error);
            toast.error("Failed to update cybersecurity related");
        }
    }

    const handleBulkCyberSec = async () => {
        let cyberSecRows: DataRow[] = [];

        for (const uuid of Array.from(rowSelectionModel.ids)) {
            const flat = flatRows.find(r => r.UUID === uuid);
            if (!flat) continue;

            if (flat.isGroup && grouped[flat.groupKey]) {
                cyberSecRows.push(...grouped[flat.groupKey]);
            } else {
                cyberSecRows.push(flat as DataRow);
            }
        }

        // dedupe by UUID
        const uniqueRows = Array.from(
            new Map(cyberSecRows.map(r => [r.UUID, r])).values()
        );

        for (const row of uniqueRows) {
            await handleCyberSecRow(row);
        }

        // Deselect all rows
        setRowSelectionModel({ ids: new Set(), type: 'include' });
    }

    //####################################################################
    // HANDLE CONTRACTING OFFICER
    //####################################################################
    async function handleAssignCO(officerId: number, username: string) {

        // Get selected Rows
        const selectedItemUUIDs = Array.from(rowSelectionModel.ids)
            .filter(id => !String(id).startsWith("header-"));

        if (selectedItemUUIDs.length === 0) {
            toast.error("No items selected");
            return;
        }

        const requestIDs = [
            ...new Set(filteredApprovalData
                .filter(item => selectedItemUUIDs.includes(item.UUID))
                .map(item => item.ID)
            )
        ];

        try {
            const response = await fetch(API_URL_ASSIGN_CO, {
                method: "POST",
                headers: {
                    "Authorization": `Bearer ${localStorage.getItem("access_token")}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    request_ids: requestIDs,
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

    // the "toggle" column for group headers
    const toggleColumn: GridColDef = {
        field: "__groupToggle",
        headerName: "ID",
        width: 200,
        sortable: false,
        filterable: false,
        renderCell: params => {
            const row = params.row as FlatRow;
            if (!row.isGroup) {
                // Render an empty icon placeholder for alignment
                return (
                    <Box sx={{ display: "flex", alignItems: "center", width: "100%" }}>
                        <Box sx={{ width: 24 /* or whatever your icon's width is */ }} />
                        <Box component="span" sx={{ ml: 1, fontWeight: "bold", color: "#FFFFFF" }}>
                            {`${row.groupKey} (${row.rowCount} items)`}
                        </Box>
                    </Box>
                );
            }
            const isExpanded = expandedRows[row.groupKey];
            return (
                <Box
                    sx={{
                        display: "flex",
                        alignItems: "center",
                        cursor: "pointer",
                        width: "100%",
                    }}
                    onClick={() => toggleRow(row.groupKey)}
                >
                    <Box sx={{ width: 24, display: "flex", alignItems: "center", justifyContent: "center" }}>
                        {row.rowCount > 1 && (
                            isExpanded
                                ? <KeyboardArrowUpIcon fontSize="small" />
                                : <KeyboardArrowDownIcon fontSize="small" />
                        )}
                    </Box>
                    <Box component="span" sx={{ ml: 1, fontWeight: "bold", color: "#FFFFFF" }}>
                        {`${row.groupKey} (${row.rowCount} items)`}
                    </Box>
                </Box>
            );
        }
    };

    /***********************************************************************************/
    // IRQ1 COLUMN
    /***********************************************************************************/
    const dataColumns: GridColDef[] = [
        {
            field: "IRQ1_ID",
            headerName: "RQ1 #",
            width: 220,
            sortable: true,
            renderCell: params => {
                if (params.row.isGroup && expandedRows[params.row.groupKey]) return null;
                const id = params.row.ID;
                const existingIRQ1 = assignedIRQ1s[id] || "";
                const currentDraftIRQ1 = draftIRQ1[id] || "";

                return (
                    <Box sx={{ display: "flex", gap: 1 }}>
                        <Buttons
                            className="btn btn-maroon assign-button"
                            disabled={!!assignedIRQ1s[id]}
                            label={assignedIRQ1s[id] ? "Assigned" : "Assign"}
                            onClick={() => {
                                assignIRQ1Mutation.mutate({
                                    ID: id,
                                    newIRQ1ID: currentDraftIRQ1
                                }, {
                                    onSuccess: () => {
                                        // Invalidate the query to refresh the data
                                        queryClient.invalidateQueries({ queryKey: ["approvalData"] });
                                        toast.success("IRQ1 assigned successfully");
                                    },
                                    onError: () => {
                                        toast.error("Failed to assign IRQ1");

                                        const ref = irq1InputRef.current[id];
                                        if (ref) {
                                            ref.value = "";
                                        }
                                        // Also clear the draft state
                                        setDraftIRQ1(prev => ({ ...prev, [id]: "" }));
                                    }
                                });
                            }}
                        />
                        <TextField
                            inputRef={(el) => irq1InputRef.current[id] = el}
                            value={currentDraftIRQ1}
                            disabled={!!existingIRQ1}
                            size="small"
                            onChange={e => setDraftIRQ1(prev => ({ ...prev, [id]: e.target.value }))}
                            sx={{
                                backgroundColor: existingIRQ1 ? 'rgba(0, 128, 0, 0.2)' : 'white',
                                width: '100px',
                                '& .MuiOutlinedInput-root': {
                                    '& fieldset': {
                                        borderColor: existingIRQ1 ? 'green' : 'red',
                                        borderWidth: '2px',
                                    },
                                    '&.Mui-disabled': {
                                        backgroundColor: 'rgba(0, 128, 0, 0.2)',
                                        '& .MuiOutlinedInput-input': {
                                            color: '#00ff00',
                                            WebkitTextFillColor: '#00ff00',
                                        },
                                    },
                                },
                            }}
                        />
                    </Box>
                );
            }
        },

        /***********************************************************************************/
        // REQUESTER COLUMN
        /***********************************************************************************/
        {
            field: "requester",
            headerName: "Requester",
            width: 130,
            sortable: true,
            renderCell: params => {
                if (params.row.isGroup && expandedRows[params.row.groupKey]) return null;
                return params.value;
            }
        },

        /***********************************************************************************/
        // BUDGET OBJECT CODE COLUMN
        /***********************************************************************************/
        {
            field: "budgetObjCode",
            headerName: "Budget Object Code",
            width: 150,
            renderCell: params => {
                if (params.row.isGroup && expandedRows[params.row.groupKey]) return null;
                return convertBOC(params.value);
            }
        },

        /***********************************************************************************/
        // FUND COLUMN
        /***********************************************************************************/
        {
            field: "fund",
            headerName: "Fund",
            width: 130,
            sortable: true,
            renderCell: params => {
                if (params.row.isGroup && expandedRows[params.row.groupKey]) return null;
                return params.value;
            }
        },

        /***********************************************************************************/
        // LOCATION COLUMN
        /***********************************************************************************/
        {
            field: "location",
            headerName: "Location",
            width: 130,
            sortable: true,
            renderCell: params => {
                if (params.row.isGroup && expandedRows[params.row.groupKey]) return null;
                return params.value;
            }
        },

        /***********************************************************************************/
        // QUANTITY COLUMN
        /***********************************************************************************/
        {
            field: "quantity",
            headerName: "Quantity",
            type: "number",
            align: "center",
            width: 100,
            sortable: true,
            renderCell: params => {
                if (params.row.isGroup && expandedRows[params.row.groupKey]) return null;
                return params.value;
            }
        },

        /***********************************************************************************/
        // PRICE EACH COLUMN
        /***********************************************************************************/
        {
            field: "priceEach",
            headerName: "Price Each",
            type: "number",
            align: "center",
            sortable: true,
            width: 120,
            editable: true,
            renderCell: params => {
                if (params.row.isGroup && expandedRows[params.row.groupKey]) { return null; }
                return typeof params.value === "number" ? params.value.toFixed(2) : "0.00";
            }
        },

        /***********************************************************************************/
        // LINE TOTAL COLUMN
        /***********************************************************************************/
        {
            field: "totalPrice",
            headerName: "Line Total",
            type: "number",
            align: "center",
            width: 120,
            sortable: true,
            renderCell: params => {
                if (params.row.isGroup && expandedRows[params.row.groupKey]) { return null; }
                return typeof params.value === "number" ? params.value.toFixed(2) : "0.00";
            }
        },

        /***********************************************************************************/
        // ITEM DESCRIPTION COLUMN
        /***********************************************************************************/
        {
            field: "itemDescription",
            headerName: "Item Description",
            align: "center",
            width: 200,
            sortable: false,
            renderCell: (params) => {
                if (params.row.isGroup && expandedRows[params.row.groupKey]) return null;
                const desc: string = params.value || "";
                const truncatedDesc = desc.length > 20
                    ? desc.slice(0, 20) + "..."
                    : desc;

                return (
                    <Button
                        onClick={() => handleOpenDesc(desc)}
                        variant="text"
                        sx={{
                            padding: 0,
                            minWidth: 0,
                            color: "inherit"
                        }}
                    >
                        <Typography variant="body2" sx={{
                            color: "inherit",
                            whiteSpace: "nowrap",
                            overflow: "hidden",
                            textOverflow: "ellipsis"
                        }}>
                            {truncatedDesc}
                        </Typography>
                    </Button>
                );
            }
        },

        /***********************************************************************************/
        // JUSTIFICATION COLUMN
        /***********************************************************************************/
        {
            field: "justification",
            headerName: "Justification",
            align: "center",
            width: 200,
            sortable: false,
            renderCell: (params) => {
                if (params.row.isGroup && expandedRows[params.row.groupKey]) return null;
                const just: string = params.value || "";
                const truncatedJust = just.length > 20
                    ? just.slice(0, 20) + "..."
                    : just;

                return (
                    <Button
                        onClick={() => handleOpenJust(just)}
                        variant="text"
                        sx={{
                            padding: 0,
                            minWidth: 0,
                            color: "inherit"
                        }}
                    >
                        <Typography variant="body2" sx={{
                            color: "inherit",
                            whiteSpace: "nowrap",
                            overflow: "hidden",
                            textOverflow: "ellipsis"
                        }}>
                            {truncatedJust}
                        </Typography>
                    </Button>
                );
            }
        },

        /***********************************************************************************/
        // STATUS COLUMN
        /***********************************************************************************/
        {
            field: "status",
            headerName: "Status",
            align: "center",
            width: 200,
            sortable: true,
            renderCell: params => {
                if (params.row.isGroup && expandedRows[params.row.groupKey]) return null;
                const status = params.value as DataRow["status"];
                const { bg, Icon } = STATUS_CONFIG[status] || { bg: "#9e9e9e", Icon: React.Fragment };
                return (
                    <Box
                        sx={{
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            gap: 1,
                            backgroundColor: bg,
                            color: "black",
                            fontWeight: "bold",
                            width: "100%",
                            height: "100%",
                        }}
                    >
                        {/* Render the mapped icon */}
                        <Icon htmlColor="black" />
                        {status}
                    </Box>
                );
            }
        },

        /***********************************************************************************/
        // ACTIONS COLUMN
        /***********************************************************************************/
        {
            field: "actions",
            headerName: "Actions",
            width: 400,
            sortable: false,
            renderCell: params => (
                <Box sx={{ display: "flex", gap: 1, alignItems: "center", justifyContent: "center", width: "100%", height: "100%" }}>

                    {/* Download Button */}
                    <Button startIcon={<DownloadOutlinedIcon />} variant="contained" color="primary" onClick={() => {

                        handleDownload(params.row.ID);
                    }}>
                        Download
                    </Button>
                </Box>
            )
        }
    ];

    // combine toggle + data columns
    const allColumns = [toggleColumn, ...dataColumns];

    //#####################################################################
    // COMMAND TOOLBAR BUTTONS
    //#####################################################################
    return (
        <Box sx={{
            width: "100%",
            height: "100%",
            display: "flex",
            flexDirection: "column",

        }}>
            <Box sx={{ mb: 2, fontSize: '1.2rem', fontWeight: 'bold', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>COMMAND TOOLBAR</span>
                {searchQuery && (
                    <Box sx={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 1,
                        backgroundColor: '#1976d2',
                        color: 'white',
                        padding: '4px 12px',
                        borderRadius: '16px',
                        fontSize: '0.9rem'
                    }}>
                        <SearchIcon sx={{ fontSize: '1rem' }} />
                        <span>Search Active: "{searchQuery}" - {filteredApprovalData.length} items</span>
                        <Button
                            size="small"
                            variant="outlined"
                            sx={{
                                color: 'white',
                                borderColor: 'white',
                                ml: 1,
                                '&:hover': {
                                    borderColor: 'white',
                                    backgroundColor: 'rgba(255,255,255,0.1)'
                                }
                            }}
                            onClick={() => {
                                // Clear the search
                                if (onClearSearch) {
                                    onClearSearch();
                                }
                            }}
                        >
                            Clear
                        </Button>
                    </Box>
                )}
            </Box>



            {/* COMMAND TOOLBAR */}
            <Box sx={{ mb: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                {/* Approve Selected Button */}
                <Button
                    startIcon={<CheckIcon />}
                    variant="contained"
                    color="success"
                    onClick={handleApproveClick}
                >
                    Approve Selected ({getTotalSelectedItems()})
                </Button>

                {/* Deny Selected Button */}
                <Button
                    startIcon={<CloseIcon />}
                    variant="contained"
                    color="error"
                    onClick={handleDenyClick}
                >
                    Deny Selected ({getTotalSelectedItems()})
                </Button>

                {/* Comment Selected Button */}
                {/* Add Comment Button */}
                <Button
                    startIcon={<CommentIcon />} // Make icon smaller
                    sx={{
                        backgroundColor: "#800000",
                        "&:hover": { backgroundColor: "#600000" },
                    }}
                    variant="contained"
                    onClick={handleCommentClick}
                >
                    Add Comment ({getTotalSelectedItems()})
                </Button>

                {/* CyberSec Related Button */}
                <Button
                    variant="contained"
                    startIcon={<MemoryIcon sx={{ color: "white" }} />}
                    onClick={handleBulkCyberSec}
                    sx={{
                        backgroundColor: "black",
                        color: "white",
                        "&:hover": {
                            backgroundColor: "#222", // slightly lighter on hover
                        }
                    }}
                >
                    CyberSec Related ({getTotalSelectedItems()})
                </Button>
            </Box>

            {/* DATA GRID */}
            <div style={{ height: '70vh', overflowX: 'auto', overflowY: 'auto' }}>
                <DataGrid
                    rows={flatRows}
                    disableVirtualization={false}
                    getRowId={r => {
                        const row = r as FlatRow;
                        return row.isGroup ? `header-${row.groupKey}` : row.UUID;
                    }}
                    getRowClassName={(params) => {
                        const row = params.row as FlatRow;
                        if (row.hidden) return 'hidden-row';
                        if (row.isGroup && expandedRows[row.groupKey]) return 'expanded-group-row';
                        return '';
                    }}

                    checkboxSelection
                    columns={allColumns}
                    processRowUpdate={handleEditPriceEach}
                    rowSelectionModel={rowSelectionModel}
                    isCellEditable={(params) => {
                        // Only allow editing priceEach field
                        if (params.field !== 'priceEach') return false;

                        // Don't allow editing group headers
                        if (params.row.isGroup) return false;

                        // Don't allow editing if status is APPROVED, DENIED, COMPLETED, or CANCELLED
                        const status = params.row.status;
                        if (status === ItemStatus.APPROVED || status === ItemStatus.DENIED) {
                            return false;
                        }
                        return true;
                    }}

                    onRowSelectionModelChange={(newModel) => {
                        const newSelection = new Set<GridRowId>();
                        const prev = rowSelectionModel.ids;
                        // Process each selected UUID
                        Array.from(newModel.ids).forEach(uuid => {
                            const row = flatRows.find(r => r.UUID === uuid);
                            if (row) {
                                if (row.isGroup) {
                                    // If it's a group, add all items in that group
                                    const groupItems = flatRows.filter(r => r.groupKey === row.groupKey);
                                    groupItems.forEach(item => newSelection.add(item.UUID));
                                } else {
                                    // If it's an individual item, add it directly
                                    newSelection.add(uuid);
                                }
                            }
                        });

                        // Update the selection model
                        const removed = Array.from(prev).filter(id => !newSelection.has(id));
                        const updated = new Set(newSelection);
                        removed.forEach(uuid => {
                            const row = flatRows.find(r => r.UUID === uuid);
                            if (row?.isGroup) {
                                flatRows.filter(r => r.groupKey === row.groupKey && !r.isGroup).forEach(r => updated.delete(r.UUID));
                            }
                        });

                        setRowSelectionModel({ ids: updated, type: 'include' });

                        // Update comment payload based on selection
                        const selectedRows = Array.from(newSelection)
                            .map(uuid => flatRows.find(r => r.UUID === uuid))
                            .filter((r): r is FlatRow => !!r && !r.isGroup) as FlatRow[];

                        if (selectedRows.length === 0) return;

                        /* At this point we are unsure which button user will press so we need to prepare data
                        for all the functions, comments or approvals/deny */

                        // Prepare the payload for comments
                        const payload: GroupCommentPayload = {
                            groupKey: selectedRows[0].groupKey,
                            group_count: selectedRows.length,
                            item_uuids: selectedRows.map(r => r.UUID),
                            item_desc: selectedRows.map(r => r.itemDescription),
                            comment: []
                        };

                        // Set the group comment payload
                        setGroupCommentPayload(payload);

                        // Now prepare the payload for approvals/deny
                        const approvalPayload: ApprovalData = {
                            ID: selectedRows[0].ID,
                            item_uuids: selectedRows.map(r => r.UUID),
                            item_funds: selectedRows.map(r => r.fund),
                            totalPrice: selectedRows.map(r => r.totalPrice),
                            target_status: selectedRows.map(r => r.status),
                            action: "APPROVE" // Default to APPROVE, will be overridden by specific button clicks
                        };

                        // Process the approval payload in hook
                        setApprovalPayload(approvalPayload)

                        // Prepare Denial data
                        const denyPayload: DenialData = {
                            ID: selectedRows[0].ID,
                            item_uuids: selectedRows.map(r => r.UUID),
                            target_status: selectedRows.map(r => r.status),
                            action: "DENY"
                        }

                        // Process the denial payload in hook
                        setDenialPayload(denyPayload)
                    }}

                    initialState={{ pagination: { paginationModel: { pageSize: 25 } } }}
                    pageSizeOptions={[25, 50, 100]}
                    rowHeight={60}
                    sx={{
                        flex: 1,
                        bgcolor: "#2c2c2c",
                        border: 'none',
                        height: '100%',
                        '& .MuiDataGrid-main': {
                            overflow: 'auto'
                        },
                        '& .MuiDataGrid-virtualScroller': {
                            overflow: 'auto !important'
                        },
                        // Cells & rows
                        ...cellRowStyles,

                        // Column headers
                        ...headerStyles,

                        // Footer container
                        ...footerStyles,

                        // Pagination labels
                        ...paginationStyles,

                        // any one-off tweaks

                        '& .expanded-group-row': {
                            background: 'linear-gradient(180deg, #800000 0%, #600000 100%) !important',
                            '&:hover': {
                                background: 'linear-gradient(180deg, #600000 0%, #400000 100%) !important',
                            },
                            '& .MuiDataGrid-cell': {
                                background: 'linear-gradient(180deg, #800000 0%, #600000 100%) !important',
                                borderBottom: '2px solid #FFFFFF',
                                color: '#FFFFFF',
                                fontWeight: 'bold',
                            }
                        },
                        '& .hidden-row': {
                            display: 'none',
                        }
                    } as DataGridSxProps}
                />
            </div>

            {/* Item Description Modal */}
            <Modal
                open={openDesc}
                onClose={handleCloseDesc}
                aria-labelledby="item-description-modal"
                aria-describedby="full-item-description"
            >
                <Box sx={{
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                    width: 700,
                    bgcolor: '#2c2c2c',
                    border: '2px solid #800000',
                    boxShadow: 24,
                    p: 4,
                    color: 'white',
                    borderRadius: 1
                }}>
                    <Typography variant="h6" component="h2" sx={{ mb: 2 }}>
                        Item Description
                    </Typography>
                    <Typography id="full-item-description" sx={{ mt: 2, whiteSpace: 'pre-wrap' }}>
                        {fullDesc}
                    </Typography>
                    <Button
                        onClick={handleCloseDesc}
                        variant="contained"
                        sx={{ mt: 3, bgcolor: '#800000', '&:hover': { bgcolor: '#600000' } }}
                    >
                        Close
                    </Button>
                </Box>
            </Modal>

            {/* Justification Modal */}
            <Modal
                open={openJust}
                onClose={handleCloseJust}
                aria-labelledby="justification-modal"
                aria-describedby="full-justification"
            >
                <Box sx={{
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                    width: 700,
                    bgcolor: '#2c2c2c',
                    border: '2px solid #800000',
                    boxShadow: 24,
                    p: 4,
                    color: 'white',
                    borderRadius: 1
                }}>
                    <Typography variant="h6" component="h2" sx={{ mb: 2 }}>
                        Justification
                    </Typography>
                    <Typography id="full-justification" sx={{ mt: 2, whiteSpace: 'pre-wrap' }}>
                        {fullJust}
                    </Typography>
                    <Button
                        onClick={handleCloseJust}
                        variant="contained"
                        sx={{ mt: 3, bgcolor: '#800000', '&:hover': { bgcolor: '#600000' } }}
                    >
                        Close
                    </Button>
                </Box>
            </Modal>

            {/* Comment Modal */}
            <CommentModal
                open={isOpen}
                onClose={close}
                onSubmit={handleSubmit}
            />
        </Box>
    );
}