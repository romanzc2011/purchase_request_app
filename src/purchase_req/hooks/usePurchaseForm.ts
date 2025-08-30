import { useForm }     from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { purchaseItemSchema, PurchaseItem, OrderType } from "../schemas/purchaseSchema";
import { toast } from "react-toastify";
import { useCallback } from "react";
import { computeAPIURL } from "../utils/misc_utils";

export const usePurchaseForm = () => {
	const today = new Date().toISOString().split("T")[0];

	const form = useForm<PurchaseItem>({
	resolver: zodResolver(purchaseItemSchema),
	defaultValues: {
		requester: "",
		phoneext: "",
		datereq: today,
		dateneed: null,
		orderType: OrderType.STANDARD,
		itemDescription: "",
		justification: "",
		trainNotAval: false,
		needsNotMeet: false,
		budgetObjCode: "",
		fund: "",
		priceEach: 0,
		location: "",
		quantity: 0,
	},
	mode: "onChange",
	reValidateMode: "onChange",
	shouldFocusError: true,
	});

	const API_URL_ASSIGN_CO = `${import.meta.env.VITE_API_URL}/api/assignCO`;

	/*************************************************************************************** */
	/* ASSIGN CO -- assign CO to request */
	/*************************************************************************************** */
	const handleAssignCO = useCallback(async (requestId: string, officerId: number, username: string) => {
		const payload = {
			request_id: requestId,
			contracting_officer_id: officerId,
			contracting_officer: username,
		};
		try {
			const response = await fetch(API_URL_ASSIGN_CO, {
				method: "POST",
				headers: {
					"Authorization": `Bearer ${localStorage.getItem("access_token")}`,
					"Content-Type": "application/json",
				},
				body: JSON.stringify(payload),
			});
			if (!response.ok) {
				throw new Error("Failed to assign CO");
			}
			const data = await response.json();
			console.log("🔥 CO assigned successfully:", data);
			toast.success("CO assigned successfully");
		} catch (error) {
			console.error("❌ Error assigning CO:", error);
			toast.error("Failed to assign CO");
		}
	}, []);

	/*************************************************************************************** */
	/* CREATE NEW ID -- create new ID for request */
	/*************************************************************************************** */
	const createNewID = useCallback(async () => {
		const response = await fetch(
			computeAPIURL("/api/createNewID"),
			{
				method: "POST",
				headers: {
					"Content-Type": "application/json",
					Authorization: `Bearer ${localStorage.getItem("access_token")}`,
				},
			}
		);
		if (!response.ok) throw new Error(`HTTP error: ${response.status}`);
		console.log("New ID response", response);
		return response.json();
	}, []);

	return {
		...form,
		handleAssignCO,
		createNewID,
	}
};
