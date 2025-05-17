import React, { useState, useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "react-toastify";
import 'react-toastify/dist/ReactToastify.css';
import { Box, Typography, Button, Modal, TextField } from "@mui/material";
import { DataGrid, DataGridProps, GridColDef, GridRowId, GridRowSelectionModel } from "@mui/x-data-grid";
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
import ScheduleIcon from "@mui/icons-material/Schedule";
import CommentModal from "../modals/CommentModal";
import "../../../styles/ApprovalTable.css"

import { STATUS_CONFIG, type DataRow, type FlatRow } from "../../../types/approvalTypes";
import { addComments, GroupCommentPayload, CommentEntry, cleanPayload } from "../../../services/CommentService";
import { cellRowStyles, headerStyles, footerStyles, paginationStyles } from "../../../styles/DataGridStyles";
import { ZodCatch } from "zod";
import { useUUIDStore } from "../../../services/UUIDService";

/***********************************************************************************/
// PROPS
/***********************************************************************************/
interface ApprovalTableProps {
    onDelete: (ID: string) => void;
    resetTable: () => void;
    searchQuery: string;
}

// Global variable to store group comment payload
let groupCommentPayload: GroupCommentPayload = {
    groupKey: "",
    comment: [],
    group_count: 0,
    item_uuids: [],
    item_desc: []
};

/* API URLs */
const API_URL_APPROVAL_DATA = `${import.meta.env.VITE_API_URL}/api/getApprovalData`;
const API_URL_CYBERSEC_RELATED = `${import.meta.env.VITE_API_URL}/api/cyberSecRelated`;
const API_URL_APPROVE_DENY = `${import.meta.env.VITE_API_URL}/api/approveDenyRequest`;
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
export default function ApprovalTableDG({ searchQuery }: ApprovalTableProps) {
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

    const [draftIRQ1, setDraftIRQ1] = useState<Record<string, string>>({});
    const [assignedIRQ1s, setAssignedIRQ1s] = useState<Record<string, string>>({});

    // ITEM DESCRIPTION MODAL - for when length is too long
    const [openDesc, setOpenDesc] = useState<boolean>(false);
    const [fullDesc, setFullDesc] = useState<string>("");

    // JUSTIFICATION MODAL - for when length is too long
    const [openJust, setOpenJust] = useState<boolean>(false);
    const [fullJust, setFullJust] = useState<string>("");

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

    const { getUUID } = useUUIDStore();

    // ####################################################################
    // ####################################################################
    // COMMAND TOOLBAR
    // Handle Approval/Deny/Download
    // ####################################################################
    // ####################################################################

    // ####################################################################
    // HANDLE DENY
    const handleDenyRow = (row: FlatRow) => {
        if (row && (!row.isGroup || (row.isGroup && row.rowCount === 1))) {
            approveDenyMutation.mutate({
                ID: row.ID,
                UUID: row.UUID,
                fund: row.fund,
                action: "deny"
            });
        }
    };

    //####################################################################
    // HANDLE CYBERSECURITY RELATED
    //####################################################################
    const handleDownload = (ID: string) => { downloadStatementOfNeedForm(ID) };
    const handleFollowUp = (ID: string) => { console.log("follow up", ID); };

    // ####################################################################
    // Update assignedIRQ1s when approvalData changes
    useEffect(() => {
        if (approvalData) {
            const newAssignedIRQ1s: Record<string, string> = {};
            const newDraftIRQ1: Record<string, string> = {};

            approvalData.forEach((row: DataRow) => {
                if (row.IRQ1_ID) {
                    newAssignedIRQ1s[row.ID] = row.IRQ1_ID;
                    newDraftIRQ1[row.ID] = row.IRQ1_ID;
                }
            });

            // Update both states once after processing all data
            setAssignedIRQ1s(newAssignedIRQ1s);
            setDraftIRQ1(prev => ({ ...prev, ...newDraftIRQ1 }));
        }
    }, [approvalData]);

    /***********************************************************************************/
    // HANDLE APPROVE/DENY
    /***********************************************************************************/
    const approveDenyMutation = useMutation({
        mutationFn: async ({
            ID,
            UUID,
            fund,
            action
        }: {
            ID: string,
            UUID: string,
            fund: string,
            action: "approve" | "deny"
        }) => {
            const res = await fetch(API_URL_APPROVE_DENY, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${localStorage.getItem("access_token")}`
                },
                body: JSON.stringify({
                    ID: ID,
                    UUID: UUID,
                    fund: fund,
                    action: action
                })
            });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return res.json();
        },
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ["approvalData"] }),
        onError: (error) => {
            console.error("Approval action failed:", error);
            toast.error("Approval action failed. Please try again.");
        }
    });

    /***********************************************************************************/
    // MODALS
    /***********************************************************************************/

    /***********************************************************************************/
    // ITEM DESCRIPTION MODAL
    const handleOpenDesc = (desc: string) => {
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
        isOpen,
        openCommentModal,
        close,
        handleSubmit,
    } = useCommentModal();

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

        // clean the payload
        //cleanPayload(payloadToSend);
        console.log("🔥 PAYLOAD TO SEND", payloadToSend);

        // Deselect all rows
        setRowSelectionModel({ ids: new Set(), type: 'include' });

        await addComments(payloadToSend);
        toast.success("Comments added successfully");
    };

    //####################################################################
    // HANDLE CYBERSECURITY RELATED
    //####################################################################
    async function handleCyberSecRow(row: DataRow) {
        const uuid = await getUUID(row.ID);
        if (!uuid) {
            toast.error("Failed to get UUID");
            console.error("Failed to get UUID");
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
    // HANDLE APPROVE/DENY
    //####################################################################

    // Per row approval
    async function handleApproveRow(row: DataRow) {
        const uuid = await getUUID(row.ID);
        if (!uuid) {
            toast.error("Failed to get UUID");
            console.error("Failed to get UUID");
            return;
        }
        approveDenyMutation.mutate({ ID: row.ID, UUID: uuid, fund: row.fund, action: "approve" });
    }
    // Bulk approve
    const handleBulkApprove = async () => {
        // collect DataRow objects to approve
        let toApprove: DataRow[] = [];

        for (const uuid of Array.from(rowSelectionModel.ids)) {
            // find the FlatRow you selected
            const flat = flatRows.find(r => r.UUID === uuid);
            if (!flat) continue;

            if (flat.isGroup && grouped[flat.groupKey]) {
                toApprove.push(...grouped[flat.groupKey]);
            } else {
                toApprove.push(flat as DataRow);
            }
        }

        // dedupe by UUID
        const uniqueRows = Array.from(
            new Map(toApprove.map(r => [r.UUID, r])).values()
        );

        // approve each row
        for (const row of uniqueRows) {
            await handleApproveRow(row);
        }
        // Deselect all rows
        setRowSelectionModel({ ids: new Set(), type: 'include' });
    }



    // the "toggle" column for group headers
    const toggleColumn: GridColDef = {
        field: "__groupToggle",
        headerName: "",
        width: 200,
        sortable: false,
        filterable: false,
        renderCell: params => {
            const row = params.row as FlatRow;
            if (!row.isGroup) return null;
            const isExpanded = expandedRows[row.groupKey];
            return (
                <Box
                    sx={{
                        display: "flex",
                        alignItems: "center",
                        cursor: "pointer",
                        width: "100%",
                        pl: row.rowCount === 1 ? 2 : 0
                    }}
                    onClick={() => toggleRow(row.groupKey)}
                >
                    {row.rowCount > 1 && (
                        expandedRows[row.groupKey]
                            ? <KeyboardArrowUpIcon fontSize="small" />
                            : <KeyboardArrowDownIcon fontSize="small" />
                    )}
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
            headerName: "IRQ1 #",
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
                                    onSuccess: (data) => {
                                        // Invalidate the query to refresh the data
                                        queryClient.invalidateQueries({ queryKey: ["approvalData"] });
                                        toast.success("IRQ1 assigned successfully");
                                    },
                                    onError: () => {
                                        toast.error("Failed to assign IRQ1");
                                    }
                                });
                            }}
                        />
                        <TextField
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
        // ID COLUMN
        /***********************************************************************************/
        {
            field: "ID",
            headerName: "ID",
            width: 130,
            sortable: true,
            renderCell: params => {
                if (params.row.isGroup && expandedRows[params.row.groupKey]) return null;
                return (
                    <Box sx={{ pl: params.row.rowCount === 1 ? 2 : 0 }}>
                        {params.value}
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
                    <Button startIcon={<DownloadOutlinedIcon />} variant="contained" color="primary" onClick={() => handleDownload(params.row.ID)}>
                        Download
                    </Button>
                </Box>
            )
        }
    ];

    // combine toggle + data columns
    const allColumns = [toggleColumn, ...dataColumns];

    return (
        <Box sx={{
            width: "100%",
            height: "100%",
            display: "flex",
            flexDirection: "column"
        }}>
            <Box sx={{ mb: 2 }}>
                COMMAND TOOLBAR
            </Box>
            {/* COMMAND TOOLBAR */}
            <Box sx={{ mb: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                {/* Approve Selected Button */}
                <Button
                    startIcon={<CheckIcon />}
                    variant="contained"
                    color="success"
                    onClick={handleBulkApprove}
                >
                    Approve Selected ({getTotalSelectedItems()})
                </Button>

                {/* Deny Selected Button */}
                <Button
                    startIcon={<CloseIcon />}
                    variant="contained"
                    color="error"
                //onClick={handleBulkDeny}
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

                {/* Follow Up Selected Button */}
                <Button
                    variant="outlined" startIcon={<ScheduleIcon />}
                //onClick={handleBulkFollowUp}
                >
                    Schedule Follow-Up
                </Button>
            </Box>

            <DataGrid
                rows={flatRows}
                getRowId={r => r.isGroup ? `header-${r.groupKey}` : r.UUID}
                columns={allColumns}
                getRowClassName={(params) => {
                    if (params.row.hidden) return 'hidden-row';
                    if (params.row.isGroup && expandedRows[params.row.groupKey]) return 'expanded-group-row';
                    return '';
                }}
                checkboxSelection
                rowSelectionModel={rowSelectionModel}
                onRowSelectionModelChange={(newModel) => {
                    const newSelection = new Set<GridRowId>();
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
                    setRowSelectionModel({ ids: newSelection, type: 'include' });

                    // Update comment payload based on selection
                    const selectedRows = Array.from(newSelection)
                        .map(uuid => flatRows.find(r => r.UUID === uuid))
                        .filter((r): r is FlatRow => !!r && !r.isGroup) as FlatRow[];

                    if (selectedRows.length === 0) return;

                    const payload: GroupCommentPayload = {
                        groupKey: selectedRows[0].groupKey,
                        group_count: selectedRows.length,
                        item_uuids: selectedRows.map(r => r.UUID),
                        item_desc: selectedRows.map(r => r.itemDescription),
                        comment: []
                    };

                    setGroupCommentPayload(payload);
                }}

                initialState={{ pagination: { paginationModel: { pageSize: 25 } } }}
                pageSizeOptions={[25, 50, 100]}
                disableRowSelectionOnClick
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
                    "& .MuiDataGrid-cellCheckbox": { color: "yellow" },

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