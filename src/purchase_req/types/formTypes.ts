/********************************************************/
/* FORM VALUES */

import { ItemStatus } from "./approvalTypes";

/********************************************************/
export type FormValues = {
  uuid?: string;
  id?: string;
  irq1_id?: string;
  requester: string;
  phoneext: string;
  datereq: Date | string;
  dateneed: Date | string;
  orderType: string;
  file_attachments: {
    attachment: File | null;
    name?: string;
    type?: string;
    size?: number;
  }[];
  itemDescription: string;
  justification: string;
  train_not_aval: boolean;
  needs_not_meet: boolean;
  quantity: number;
  price: number;
  price_each: number;
  total_price: number;
  fund: string;
  location: string;
  budget_obj_code: string;
  status: ItemStatus;
};

/********************************************************/
/* USER CREDENTIALS */
/********************************************************/
export type UserCredentials = {
  username: string;
  password: string;
}

/********************************************************/
/* Budget object code */
/********************************************************/
export const BOCMenuItems = [
  "3101",
  "3107",
  "3111",
  "3113",
  "3121",
  "3122",
  "3130"
];

/********************************************************/
/* LOCATIONS */
/********************************************************/
export const locations = [
  "ALEX/C",
  "ALEX/J",
  "LAFY/C",
  "LAFY/J",
  "LKCH/C",
  "LKCC/J",
  "MONR/C",
  "MONR/J",
  "SHVT/C",
  "SHVT/J"
];
