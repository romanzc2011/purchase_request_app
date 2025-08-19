import { z } from "zod";
import { ItemStatus } from "../types/approvalTypes";

export enum OrderType {
	STANDARD = "STANDARD",
	QUARTERLY_ORDER = "QUARTERLY_ORDER",
	NO_RUSH = "NO_RUSH",
}

export const purchaseItemSchema = z
  .object({
    UUID:            z.string().optional(),
    ID:              z.string().optional(),
    IRQ1_ID:         z.string().optional(),

    requester:       z.string().min(1, "Requester is required"),
    phoneext:        z.string().min(1, "Phone extension is required"),
	
    datereq:         z.string().nonempty("Date requested is required"),
    dateneed: z
        .string()
        .transform(val => val === "" ? null : val)
        .nullable()
        .optional(),
		
    orderType:	z.nativeEnum(OrderType).optional(),

    fileAttachments: z
      .array(
        z.object({
          attachment: z.instanceof(File).optional(),
          name:       z.string().optional(),
          type:       z.string().optional(),
          size:       z.number().optional(),
        })
      )
      .optional(),

    itemDescription: z.string().min(1, "Description is required"),
    justification:   z.string().min(1, "Justification is required"),

    trainNotAval: z.boolean().optional(),
    needsNotMeet: z.boolean().optional(),

    budgetObjCode: z
		.string()
		.min(1, "Budget code is required")
		.transform((s) => s.padStart(4, "0")),

    fund:            z.string().min(1, "Fund is required"),
    location:        z.string().min(1, "Location is required"),

    priceEach:       z.number().nonnegative("Price cannot be negative"),
    quantity:        z.number().int("Quantity must be a whole number").min(1, "Quantity must be at least 1"),
	
	totalPrice: z
		.number()
		.optional()
		.transform((tp) => {
			// 1) If the user explicitly supplied a positive number, keep it.
			if (typeof tp === "number" && tp > 0) {
				return tp;
			}

			// 2) Otherwise, we'll compute this in the superRefine
			return tp;
		}),

    status: z.nativeEnum(ItemStatus).optional(),
  })
  .superRefine((data, ctx) => {
    console.log("superRefine check:", data.dateneed, data.orderType);
    if (!data.dateneed && !data.orderType) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "'Date Needed' OR an orderType is required.",
        path: ["dateneed"],
      });
    }
    
    // Calculate totalPrice if not provided
    if (!data.totalPrice || data.totalPrice <= 0) {
      data.totalPrice = data.priceEach * data.quantity;
    }
  });

export type PurchaseItem = z.infer<typeof purchaseItemSchema>;
