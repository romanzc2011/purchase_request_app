import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "react-toastify";
import { useUUIDStore } from "../services/UUIDService";
import { FormValues } from "../types/formTypes";

const API_URL_ASSIGN_IRQ1 = `${import.meta.env.VITE_API_URL}/api/assignIRQ1_ID`;

/**
 * 
 * Args for the assignIRQ1 mutation
 * 
 * @param ID - The ID of the request
 * @param IRQ1_ID - The IRQ1 ID to assign
 * @param UUID - The UUID of the request
 */
interface AssignIRQ1Args {
    ID: string;
    newIRQ1ID: string;
}

/* Response from IRQ1 endpoint */
interface AssignIRQ1Response {
    IRQ1_ID_ASSIGNED: boolean;
    IRQ1_ID: string;
}

/** 
 * Custom hook to assign IRQ1 ID for specific row
 */
export function useAssignIRQ1() {
    const queryClient = useQueryClient();
    const { getUUID } = useUUIDStore();

    return useMutation<AssignIRQ1Response, Error, AssignIRQ1Args>({
        mutationFn: async ({ ID, newIRQ1ID }) => {
            const UUID = await getUUID(ID);
            if (!UUID) throw new Error("UUID not found for this request");

            const res = await fetch(API_URL_ASSIGN_IRQ1, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${localStorage.getItem("access_token")}`,
                },
                body: JSON.stringify({
                    ID,
                    IRQ1_ID: newIRQ1ID,
                    UUID,
                }),
            });
            if(!res.ok) {
                const errorText = await res.text();
                throw new Error(`HTTP error: ${res.status} - ${errorText}`);
            }
            return res.json();
        },
        onSuccess: (data, { ID }) => {
            queryClient.invalidateQueries({ queryKey: ["approvalData"] });
            toast.success("IRQ1 ID assigned successfully");
        }
    });
}
