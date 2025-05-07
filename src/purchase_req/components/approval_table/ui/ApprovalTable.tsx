import React, { useState, useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "react-toastify";
import { Box, Typography, Button, Modal, TextField } from "@mui/material";
import { DataGrid, GridColDef } from "@mui/x-data-grid";
import DownloadOutlinedIcon from "@mui/icons-material/DownloadOutlined";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import KeyboardArrowUpIcon from "@mui/icons-material/KeyboardArrowUp";
import { FormValues } from "../../../types/formTypes";
import { fetchSearchData } from "./SearchBar";
import Buttons from "../../purchase_req_table/Buttons";
import { convertBOC } from "../../../utils/bocUtils";
import { useCommentMutation } from "../../../api/comments";
import WarningIcon from "@mui/icons-material/Warning";
import PendingIcon from "@mui/icons-material/Pending";
import SuccessIcon from "@mui/icons-material/CheckCircle";
import { useAssignIRQ1 } from "../../../hooks/useAssignIRQ1";
import { useCommentModal } from "../../../hooks/useCommentModal";
import CommentModal from "../modals/CommentModal";
import "../../../styles/ApprovalTable.css"
import { cellRowStyles, headerStyles, footerStyles, paginationStyles } from "../../../styles/DataGridStyles";

/***********************************************************************************/
// PROPS
/***********************************************************************************/
interface ApprovalTableProps {
    onDelete: (ID: string) => void;
    resetTable: () => void;
    searchQuery: string;
}

/* API URLs */
const API_URL_APPROVAL_DATA = `${import.meta.env.VITE_API_URL}/api/getApprovalData`;
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
        return response.json();
    } else {
        const response = await fetch(API_URL_APPROVAL_DATA, {
            headers: {
                "Authorization": `Bearer ${localStorage.getItem("access_token")}`
            }
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
    }
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
    const { data: searchData } = useQuery({ queryKey: ["search", searchQuery], queryFn: () => fetchSearchData(searchQuery) });
    const { data: approvalData = [] } = useQuery<FormValues[]>({
        queryKey: ["approvalData"],
        queryFn: () => fetchApprovalData()
    });
    const [draftIRQ1, setDraftIRQ1] = useState<Record<string, string>>({});
    const [assignedIRQ1s, setAssignedIRQ1s] = useState<Record<string, string>>({});

    // ITEM DESCRIPTION MODAL - for when length is too long
    const [openDesc, setOpenDesc] = useState<boolean>(false);
    const [fullDesc, setFullDesc] = useState<string>("");

    // JUSTIFICATION MODAL - for when length is too long
    const [openJust, setOpenJust] = useState<boolean>(false);
    const [fullJust, setFullJust] = useState<string>("");

    // track which groups are expanded
    const [expandedRows, setExpandedRows] = useState<Record<string, boolean>>({});
    const toggleRowExpanded = (key: string) =>
        setExpandedRows(prev => ({ ...prev, [key]: !prev[key] }));

    const assignIRQ1Mutation = useAssignIRQ1();

    // Update assignedIRQ1s when approvalData changes
    useEffect(() => {
        if (approvalData) {
            const newAssignedIRQ1s: Record<string, string> = {};
            approvalData.forEach((row: FormValues) => {
                if (row.IRQ1_ID) {
                    newAssignedIRQ1s[row.ID] = row.IRQ1_ID;
                    // Also update the draftIRQ1 state with the assigned value
                    setDraftIRQ1(prev => ({ ...prev, [row.ID]: row.IRQ1_ID }));
                }
            });
            setAssignedIRQ1s(newAssignedIRQ1s);
        }
    }, [approvalData]);

    /***********************************************************************************/
    // HANDLE APPROVE/DENY
    /***********************************************************************************/
    const approveDenyMutation = useMutation({
        mutationFn: async ({ ID, action }: { ID: string, action: "approve" | "deny" }) => {
            const res = await fetch(API_URL_APPROVE_DENY, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${localStorage.getItem("access_token")}`
                },
                body: JSON.stringify({ ID, action })
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
    // Handle Approval/Deny/Download
    const handleApprove = (ID: string) => approveDenyMutation.mutate({ ID, action: "approve" });
    const handleDeny = (ID: string) => approveDenyMutation.mutate({ ID, action: "deny" });
    const handleDownload = (ID: string) => { downloadStatementOfNeedForm(ID); console.log("download", ID); };

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

    // base rows
    const baseRows = (searchQuery ? searchData : approvalData) || [];

    // ensure each has a UUID
    const rowsWithIds = baseRows.map((row: FormValues, i: number) =>
        row.UUID ? row : { ...row, UUID: `row-${i}` }
    );

    // group by ID
    const grouped = rowsWithIds.reduce((acc: Record<string, FormValues[]>, row: FormValues) => {
        const key = String(row.ID);
        (acc[key] ||= []).push(row);
        return acc;
    }, {});

    /***********************************************************************************/
    // COMMENT MODAL
    /***********************************************************************************/
    const commentMutation = useCommentMutation();

    const {
        isOpen,
        commentText,
        setCommentText,
        open: openCommentModal,
        close: closeCommentModal,
        handleSubmit: handleSubmitComment,
    } = useCommentModal();

    // FlatRow type
    type FlatRow =
        | { id: string; isGroup: true; groupKey: string; rowCount: number }
        | (FormValues & { id: string; isGroup?: false });

    // build flatRows array
    const flatRows: FlatRow[] = (Object.entries(grouped) as [string, FormValues[]][])
        .flatMap(([key, items]) => {
            const header: FlatRow = {
                ...items[0],           // <-- copy all data fields from the 1st item
                id: `group-${key}`,
                isGroup: true,
                groupKey: key,
                rowCount: items.length
            };

            if (!expandedRows[key]) {
                return [header];
            }

            // build detail rows
            const detailRows: FlatRow[] = items.slice(1).map(item => ({
                ...item,
                id: item.UUID!,
                isGroup: false
            }));
            return [header, ...detailRows];
        });

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
            return (
                <Box
                    sx={{ display: "flex", alignItems: "center", cursor: "pointer" }}
                    onClick={() => toggleRowExpanded(row.groupKey)}
                >
                    {expandedRows[row.groupKey]
                        ? <KeyboardArrowUpIcon fontSize="small" />
                        : <KeyboardArrowDownIcon fontSize="small" />}
                    <Box component="span" sx={{ ml: 1, fontWeight: "bold" }}>
                        {row.groupKey} ({row.rowCount})
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
        },

        /***********************************************************************************/
        // REQUESTER COLUMN
        /***********************************************************************************/
        {
            field: "requester",
            headerName: "Requester",
            width: 130,
            sortable: true,
        },

        /***********************************************************************************/
        // BUDGET OBJECT CODE COLUMN
        /***********************************************************************************/
        {
            field: "budgetObjCode",
            headerName: "Budget Object Code",
            width: 150,
            renderCell: params => convertBOC(params.value)
        },

        /***********************************************************************************/
        // FUND COLUMN
        /***********************************************************************************/
        {
            field: "fund",
            headerName: "Fund",
            width: 130,
            sortable: true,
        },

        /***********************************************************************************/
        // LOCATION COLUMN
        /***********************************************************************************/
        {
            field: "location",
            headerName: "Location",
            width: 130,
            sortable: true,
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
            renderCell: params =>
                typeof params.value === "number" ? params.value.toFixed(2) : "0.00"
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
            renderCell: params =>
                typeof params.value === "number" ? params.value.toFixed(2) : "0.00"
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
            renderCell: params => (
                <Box
                    sx={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        gap: 1,
                        color: "black",
                        backgroundColor:
                            params.value === "NEW REQUEST"
                                ? "#ff9800"
                                : params.value === "PENDING"
                                    ? "#2196f3"
                                    : params.value === "APPROVED"
                                        ? "#4caf50"
                                        : params.value === "DENIED"
                                            ? "#f44336"
                                            : "#9e9e9e",
                        fontWeight: "bold",
                        width: "100%",
                        height: "100%"
                    }}
                >
                    {params.value === "NEW REQUEST" && <WarningIcon htmlColor="black" />}
                    {params.value === "PENDING" && <PendingIcon htmlColor="black" />}
                    {params.value === "APPROVED" && <SuccessIcon htmlColor="black" />}
                    {params.value}
                </Box>
            )
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

                    {/* Add Comment Button */}
                    <Button
                        sx={{ backgroundColor: "#800000", "&:hover": { backgroundColor: "#600000" } }}
                        variant="contained"
                        onClick={() => openCommentModal(params.row.ID)}
                    >
                        Add Comment
                    </Button>

                    {/* Approve Button */}
                    <Button
                        variant="contained"
                        color="success"
                        onClick={() => handleApprove(params.row.ID)}
                        disabled={params.row.status === "APPROVED"}
                        sx={{ minWidth: "100px" }}
                    >
                        Approve
                    </Button>

                    {/* Deny Button */}
                    <Button
                        variant="contained"
                        color="error"
                        onClick={() => handleDeny(params.row.ID)}
                        disabled={params.row.status === "DENIED"}
                    >
                        Deny
                    </Button>

                    {/* Download Button */}
                    <Button variant="contained" color="primary" onClick={() => handleDownload(params.row.ID)}>
                        <DownloadOutlinedIcon />
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
            <DataGrid
                rows={flatRows}
                columns={allColumns}
                getRowId={(row: any) => row.id}
                getRowClassName={({ row }: { row: any }) =>
                    (row as FlatRow).isGroup ? "group-header-row" : ""
                }
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
                } as DataGridSxProps}
            />
            <style>{`
        .group-header-row .MuiDataGrid-cell {
          background-color: #3c3c3c !important;
          font-weight: bold;
          font-size: 1.05rem !important; /* Increased font size for group headers */
        }
      `}</style>

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
                commentText={commentText}
                onClose={closeCommentModal}
                onSubmit={(comment) => {
                    console.log("CommentModal onSubmit called with:", comment);
                    setCommentText(comment);
                    console.log("After setCommentText, calling handleSubmitComment");
                    handleSubmitComment();
                }}
            />
        </Box>
    );
}
