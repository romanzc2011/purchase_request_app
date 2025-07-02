import { DataRow, FlatRow } from "../../types/approvalTypes";
import { toast } from "react-toastify";
import { GridRowId } from "@mui/x-data-grid";

interface HandleCommandsProps {
    rowSelectionModel: { ids: Set<GridRowId>, type: 'include' | 'exclude' };
    flatRows: FlatRow[];
    grouped: Record<string, DataRow[]>;
    setRowSelectionModel: (model: { ids: Set<GridRowId>, type: 'include' | 'exclude' }) => void;
    getUUID: (id: string) => Promise<string | null>;
    openCommentModal: (id: string) => void;
    approveDenyMutation: any; // Replace with proper type
    fetchCyberSecRelated: (uuid: string) => Promise<any>;
}

export const createHandleCommands = ({
    rowSelectionModel,
    flatRows,
    grouped,
    setRowSelectionModel,
    getUUID,
    openCommentModal,
    approveDenyMutation,
    fetchCyberSecRelated
}: HandleCommandsProps) => {
    // Handle Approve
    async function handleApproveRow(row: DataRow) {
        const uuid = await getUUID(row.ID);
        if (!uuid) {
            toast.error("Failed to get UUID");
            console.error("Failed to get UUID");
            return;
        }
        approveDenyMutation.mutate({ ID: row.ID, UUID: uuid, fund: row.fund, action: "approve" });
    }

	/*************************************************************************************** */
	/* APPROVE -- approve the request */
	/*************************************************************************************** */
    const handleBulkApprove = async () => {
        let toApprove: DataRow[] = [];

        for (const uuid of Array.from(rowSelectionModel.ids)) {
            const flat = flatRows.find(r => r.UUID === uuid);
            if (!flat) continue;

            if (flat.isGroup && grouped[flat.groupKey]) {
                toApprove.push(...grouped[flat.groupKey]);
            } else {
                toApprove.push(flat as DataRow);
            }
        }

        const uniqueRows = Array.from(
            new Map(toApprove.map(r => [r.UUID, r])).values()
        );

        for (const row of uniqueRows) {
            await handleApproveRow(row);
        }
        setRowSelectionModel({ ids: new Set(), type: 'include' });
    };

    // Handle Deny
    const handleDenyRow = (row: DataRow) => {
        approveDenyMutation.mutate({
            ID: row.ID,
            UUID: row.UUID,
            fund: row.fund,
            action: "deny"
        });
    };

	/*************************************************************************************** */
	/* DENY -- deny the request */
	/*************************************************************************************** */
    const handleBulkDeny = () => {
        Array.from(rowSelectionModel.ids).forEach(uuid => {
            const row = flatRows.find(r => r.UUID === uuid);
            if (row && !row.isGroup) {
                handleDenyRow(row);
            }
        });
        setRowSelectionModel({ ids: new Set(), type: 'include' });
    };

    // Handle Comment
    async function handleCommentRow(row: DataRow) {
        const uuid = await getUUID(row.ID);
        if (!uuid) {
            toast.error("Failed to get UUID");
            console.error("Failed to get UUID");
            return;
        }
        openCommentModal(row.ID);
    }
	
	/*************************************************************************************** */
	/* COMMENT -- open the comment modal */
	/*************************************************************************************** */
    const handleBulkComment = async () => {
        let commentRows: DataRow[] = [];

        for (const uuid of Array.from(rowSelectionModel.ids)) {
            const flat = flatRows.find(r => r.UUID === uuid);
            if (!flat) continue;

            if (flat.isGroup && grouped[flat.groupKey]) {
                commentRows.push(...grouped[flat.groupKey]);
            } else {
                commentRows.push(flat as DataRow);
            }
        }

        const uniqueRows = Array.from(
            new Map(commentRows.map(r => [r.UUID, r])).values()
        );

        if (uniqueRows.length > 0) {
            await handleCommentRow(uniqueRows[0]);
        }

        setRowSelectionModel({ ids: new Set(), type: 'include' });
    };

	/*************************************************************************************** */
	/* CYBERSECURITY RELATED -- update the cybersecurity related field */
	/*************************************************************************************** */
    // Handle CyberSec
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

        // Dedupe the rows
        const uniqueRows = Array.from(
            new Map(cyberSecRows.map(r => [r.UUID, r])).values()
        );

        for (const row of uniqueRows) {
            await handleCyberSecRow(row);
        }

        setRowSelectionModel({ ids: new Set(), type: 'include' });
    };

    return {
        handleBulkApprove,
        handleBulkDeny,
        handleBulkComment,
        handleBulkCyberSec
    };
}; 