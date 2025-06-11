import WarningIcon from "@mui/icons-material/Warning";
import PendingIcon from "@mui/icons-material/Pending";
import SuccessIcon from "@mui/icons-material/CheckCircle";
import CloseIcon from "@mui/icons-material/Close";

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
    irq1_id         : string;
    id              : string;
    uuid            : string;       // Unique key for React/data-grid

    requester       : string;
    budget_obj_code : string;
    fund            : string;
    location        : string;
    quantity        : number;
    price_each      : number;
    total_price     : number;
    item_description: string;
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
    uuid: string;
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
    uuid: string;
    hidden?: boolean;
}

// #########################################################################################
// Approval data
// #########################################################################################  
export interface ApprovalData {
    id: string;
    item_count: number;
    item_uuids: string[];
    item_funds: string[];
    total_price: number[];
    target_status: ItemStatus[];
    action: string;
    co?: string;
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