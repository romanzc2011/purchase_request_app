import { useForm }     from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { purchaseItemSchema, PurchaseItem } from "../schemas/purchaseSchema";

export const usePurchaseForm = () => {
  const today = new Date().toISOString().split("T")[0];

  return useForm<PurchaseItem>({
    resolver: zodResolver(purchaseItemSchema),
    defaultValues: {
      requester: "",
      phoneext: "",
      datereq: today,
      dateneed: null,
      order_type: "",
      item_description: "",
      justification: "",
      train_not_aval: false,
      needs_not_meet: false,
      budget_obj_code: "",
      fund: "",
      price_each: 0,
      location: "",
      quantity: 1,
      total_price: 0
    },
    mode: "onChange",
    reValidateMode: "onChange",
    shouldFocusError: true
  });
};
