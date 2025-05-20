import { ApprovalData } from "../types/approvalTypes";

const API_URL_APPROVE_DENY_REQUEST = `${import.meta.env.VITE_API_URL}/api/approveDenyRequest`

//    const approveDenyMutation = useMutation({
//         mutationFn: async ({
//             ID,
//             UUID,
//             fund,
//             action
//         }: {
//             ID: string,
//             UUID: string,
//             fund: string,
//             action: "approve" | "deny"
//         }) => {
//             const res = await fetch(API_URL_APPROVE_DENY, {
//                 method: "POST",
//                 headers: {
//                     "Content-Type": "application/json",
//                     Authorization: `Bearer ${localStorage.getItem("access_token")}`
//                 },
//                 body: JSON.stringify({
//                     ID: ID,
//                     UUID: UUID,
//                     fund: fund,
//                     action: action
//                 })
//             });
//             if (!res.ok) throw new Error(`HTTP ${res.status}`);
//             return res.json();
//         },
//         onSuccess: () => queryClient.invalidateQueries({ queryKey: ["approvalData"] }),
//         onError: (error) => {
//             console.error("Approval action failed:", error);
//             toast.error("Approval action failed. Please try again.");
//         }
//     });

// ##############################################################
// Approve/Deny request
// ##############################################################
export async function approveDenyRequest(payload: ApprovalData) {
    const response = await fetch(API_URL_APPROVE_DENY_REQUEST, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });
    if (!response.ok) {
        throw new Error("Failed to approve/deny request");
    }
    console.log("🔥 APPROVE/DENY RESPONSE", response);
    return response.json();
}

function useMutation(arg0: {
    mutationFn: ({ ID, UUID, fund, action }: {
        ID: string;
        UUID: string;
        fund: string;
        action: "approve" | "deny";
    }) => Promise<any>; onSuccess: () => any; onError: (error: any) => void;
}) {
    throw new Error("Function not implemented.");
}
