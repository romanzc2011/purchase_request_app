import WarningIcon from "@mui/icons-material/Warning";
import PendingIcon from "@mui/icons-material/Pending";
import SuccessIcon from "@mui/icons-material/CheckCircle";
import CloseIcon from "@mui/icons-material/Close";


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
    status          : "NEW REQUEST" | "PENDING" | "APPROVED" | "DENIED";
}

// #########################################################################################
// Flattened rows
// #########################################################################################    
export type FlatRow = 
| (DataRow & {  isGroup: true; groupKey: string; rowCount: number })
| (DataRow & {  isGroup: false; groupKey: string; rowId: string });


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
    "PENDING": { 
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
    }
}