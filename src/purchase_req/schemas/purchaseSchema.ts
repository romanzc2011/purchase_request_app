import { z } from "zod";

export const purchaseItemSchema = z
  .object({
    uuid:            z.string().optional(),
    id:              z.string().optional(),
    request_id:      z.string().optional(),
    irq1_id:         z.string().optional(),
    requester:       z.string().min(1, "Requester is required"),
    phoneext:        z.string().min(1, "Phone extension is required"),
    datereq:         z.string().nonempty("Date requested is required"),
    dateneed: z
        .string()
        .transform(val => val === "" ? null : val)
        .nullable()
        .optional(),
    order_type:       z.string().optional(),
    file_attachments: z.array(z.object({
      attachment: z.any().optional(),
      name: z.string().optional(),
      type: z.string().optional(),
      size: z.number().optional()
    })).optional(),
    item_description: z.string().min(1, "Description is required"),
    justification:   z.string().min(1, "Justification is required"),
    train_not_aval: z.boolean().default(false),
    needs_not_meet: z.boolean().default(false),
    budget_obj_code:   z.string().min(1, "Budget code is required"),
    fund:            z.string().min(1, "Fund is required"),
    location:        z.string().min(1, "Location is required"),
    price_each:       z.coerce.number().min(0, "Price cannot be negative"),
    quantity:        z.coerce.number().min(1, "Quantity must be at least 1"),
    total_price:      z.number().optional(),
    status:          z.string().optional()
  })
  .transform(data => ({
    ...data,
    total_price: (data.price_each as number) * (data.quantity as number)
  }))
  .superRefine((data, ctx) => {
    console.log("superRefine check:", data.dateneed, data.order_type);
    if (!data.dateneed && !data.order_type) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "'Date Needed' OR an orderType is required.",
        path: ["dateneed", "order_type"],
      });
    }
  });

export type PurchaseItem = z.infer<typeof purchaseItemSchema>;
