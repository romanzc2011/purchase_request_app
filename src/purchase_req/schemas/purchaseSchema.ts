import { z } from "zod";

export const purchaseItemSchema = z
  .object({
    UUID:            z.string().optional(),
    ID:              z.string().optional(),
    IRQ1_ID:         z.string().optional(),
    requester:       z.string().min(1, "Requester is required"),
    phoneext:        z.string().min(1, "Phone extension is required"),
    datereq:         z.string().nonempty("Date requested is required"),
    dateneed:        z.union([z.string().min(1), z.null()]).optional(),
    orderType:       z.string().optional(),
    fileAttachments: z.array(z.object({
      attachment: z.any().optional(),
      name: z.string().optional(),
      type: z.string().optional(),
      size: z.number().optional()
    })).optional(),
    itemDescription: z.string().min(1, "Description is required"),
    justification:   z.string().min(1, "Justification is required"),
    trainNotAval: z.boolean().optional(),
    needsNotMeet: z.boolean().optional(),
    budgetObjCode:   z.string().min(1, "Budget code is required"),
    fund:            z.string().min(1, "Fund is required"),
    location:        z.string().min(1, "Location is required"),
    priceEach:       z.number().nonnegative("Price cannot be negative"),
    quantity:        z.number().min(1, "Quantity must be at least 1"),
    totalPrice:      z.number().optional(),
    status:          z.string().optional()
  })
  .superRefine((data, ctx) => {
    // If neither dateneed nor orderType is provided, add an error on dateneed
    if (!data.dateneed && !data.orderType) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "'Date Needed' OR an orderType is required.",
        path: ["dateneed"],
      });
    }
  });
export type PurchaseItem = z.infer<typeof purchaseItemSchema>;