import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "react-toastify";
import { computeAPIURL } from "../utils/misc_utils";

export function useAssignIRQ1() {
	const queryClient = useQueryClient();

	return useMutation({
		mutationFn: async ({ ID, newIRQ1ID }: { ID: string; newIRQ1ID: string }) => {
			const response = await fetch(computeAPIURL("/api/assignIRQ1_ID"), {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
					Authorization: `Bearer ${localStorage.getItem("access_token")}`
				},
				body: JSON.stringify({
					ID,
					newIRQ1ID
				})
			});

			if (!response.ok) {
				throw new Error("Failed to assign IRQ1");
			}

			return response.json();
		},
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: ["approvalData"] });
		},
		onError: (error) => {
			console.error("Error assigning IRQ1:", error);
			toast.error("Failed to assign IRQ1");
		}
	});
}
