import { useForm } from "react-hook-form";
import { FormValues } from "../types/formTypes";

export const usePurchaseForm = () => {
    // This is used to set the default value for the date requested field to today's date
    const today: Date = new Date();
    const isoString: string = today.toISOString();
    const formattedToday: string = isoString.split("T")[0];

    const form = useForm<FormValues>({
        defaultValues: {
            UUID: "",
            ID: "",
            IRQ1_ID: "",
            requester: "",
            phoneext: "",
            datereq: formattedToday,
            dateneed: null,
            orderType: "",
            itemDescription: "",
            justification: "",
            addComments: "",
            learnAndDev: {
                trainNotAval: false,
                needsNotMeet: false
            },
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

    return form;
}; 