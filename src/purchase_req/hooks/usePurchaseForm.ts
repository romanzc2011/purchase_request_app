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
      orderType: "",
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
};
