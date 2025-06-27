import WarningIcon from "@mui/icons-material/Warning";
import PendingIcon from "@mui/icons-material/Pending";
import SuccessIcon from "@mui/icons-material/CheckCircle";
import CloseIcon from "@mui/icons-material/Close";
import { Optional } from "@tanstack/react-query";

// #########################################################################################
// Item status
// #########################################################################################  
export enum ItemStatus {
    NEW_REQUEST = "NEW REQUEST",
    PENDING_APPROVAL = "PENDING APPROVAL",
    APPROVED = "APPROVED",
    DENIED = "DENIED",
    ON_HOLD = "ON HOLD",
    COMPLETED = "COMPLETED",
    CANCELLED = "CANCELLED"
}

// #########################################################################################
// DataRow
// #########################################################################################    
export interface DataRow {
    IRQ1_ID         : string;
    ID              : string;
    UUID            : string;       // Unique key for React/data-grid
    requester       : string;
    budgetObjCode   : string;
    fund            : string;
    location        : string;
    quantity        : number;
    priceEach       : number;
    totalPrice      : number;
    itemDescription : string;
    justification   : string;
    status          : ItemStatus;
}

// #########################################################################################
// Flattened rows
// #########################################################################################    
export interface FlatRow extends DataRow {
    isGroup: boolean;
    groupKey: string;
    rowCount: number;
    rowId: string;
    UUID: string;
    hidden?: boolean;
}

// #########################################################################################
// Flattened rows
// #########################################################################################  
export interface FlatRow extends DataRow {
    isGroup: boolean;
    groupKey: string;
    rowCount: number;
    rowId: string;
    UUID: string;
    hidden?: boolean;
}

// #########################################################################################
// Approval data
// #########################################################################################  
export interface ApprovalData {
    ID: string;
    item_uuids: string[];
    item_funds: string[];
    totalPrice: number[];
    target_status: ItemStatus[];
    action: string;
    co?: string;
}

// #########################################################################################
// Deny data
// #########################################################################################
export interface DenialData {
	ID: string;
	item_uuids: string[];
	target_status: ItemStatus[];
	action: "DENY"
}

// #########################################################################################
// Group comment payload
// #########################################################################################      
export interface GroupCommentPayload {
    groupKey: string;   // Group key is the ID in the table, ie LAWB000x
    comment: CommentEntry[];
    group_count: number;
    item_uuids: string[];
    item_desc: string[];
}

export interface CommentEntry { uuid: string; comment: string }

export interface ContractingOfficer {
	id?: number;
	username: string;
	email?: string;
}

// #########################################################################################
// Status for rows
// #########################################################################################    
export const STATUS_CONFIG: Record<DataRow["status"], {
    bg: string;
    Icon: React.FC<{htmlColor?: string}>;
    canApprove: boolean;
    canDeny: boolean;
    canComment: boolean;
    canFollowUp: boolean;
}> = {
    "NEW REQUEST": { 
        bg: "#ff9800", 
        Icon: WarningIcon,
        canApprove: true,
        canDeny: true,
        canComment: true,
        canFollowUp: false
    },
    "PENDING APPROVAL": { 
        bg: "#2196f3", 
        Icon: PendingIcon,
        canApprove: true,
        canDeny: true,
        canComment: true,
        canFollowUp: true
    },
    "APPROVED": { 
        bg: "#4caf50", 
        Icon: SuccessIcon,
        canApprove: false,
        canDeny: false,
        canComment: true,
        canFollowUp: false
    },
    "DENIED": { 
        bg: "#f44336", 
        Icon: CloseIcon,
        canApprove: false,
        canDeny: false,
        canComment: false,
        canFollowUp: false
    },
    "ON HOLD": { 
        bg: "#ff9800", 
        Icon: WarningIcon,
        canApprove: false,
        canDeny: false,
        canComment: true,
        canFollowUp: false
    },
    "COMPLETED": { 
        bg: "#4caf50", 
        Icon: SuccessIcon,
        canApprove: false,
        canDeny: false,
        canComment: false,
        canFollowUp: false
    },
    "CANCELLED": { 
        bg: "#f44336", 
        Icon: CloseIcon,
        canApprove: false,
        canDeny: false,
        canComment: false,
        canFollowUp: false
    }
}