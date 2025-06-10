import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "react-toastify";
import { useUUIDStore } from "../services/UUIDService";

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
    id: string;
    new_irq1_id: string;
}

/* Response from IRQ1 endpoint */
interface AssignIRQ1Response {
    irq1_id_assigned: boolean;
    irq1_id: string;
}

/** 
 * Custom hook to assign IRQ1 ID for specific row
 */
export function useAssignIRQ1() {
    const queryClient = useQueryClient();
    const { getUUID } = useUUIDStore();

    return useMutation<AssignIRQ1Response, Error, AssignIRQ1Args>({
        mutationFn: async ({ id, new_irq1_id }) => {
            const UUID = await getUUID(id);
            if (!UUID) throw new Error("UUID not found for this request");

            const res = await fetch(API_URL_ASSIGN_IRQ1, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${localStorage.getItem("access_token")}`,
                },
                body: JSON.stringify({
                    id,
                    irq1_id: new_irq1_id,
                    UUID,
                }),
            });
            if(!res.ok) {
                const errorText = await res.text();
                throw new Error(`HTTP error: ${res.status} - ${errorText}`);
            }
            return res.json();
        },
        onSuccess: (data, { id }) => {
            queryClient.invalidateQueries({ queryKey: ["approvalData"] });
            queryClient.invalidateQueries({ queryKey: ["search"] });
            toast.success("IRQ1 ID assigned successfully");
        }
    });
}
