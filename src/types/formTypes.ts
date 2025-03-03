/********************************************************/
/* FORM VALUES */
/********************************************************/
export type FormValues = {
  reqID: string;
  requester: string;
  phoneext: string;
  datereq: Date | null;
  dateneed: Date | null;
  orderType: string;
  fileAttachments: {
    attachment: File | null;
    name?: string;
    type?: string;
    size?: number;
  }[];
  itemDescription: string;
  justification: string;
  addComments: string;
  learnAndDev: {
    trainNotAval: string;
    needsNotMeet: string
  };
  quantity: number;
  price: number;
  priceEach: number;
  totalPrice: number;
  fund: string;
  location: string;
  budgetObjCode: string;
  status: string;
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
  "3101 - General Office Equipment",
  "3107 - Audio Recording Equipment",
  "3111 - Furniture and Fixtures",
  "3113 - Mailing Equipment",
  "3121 - Legal Resources - New Print and Digital Purchases",
  "3122 - Legal Resources - Print and Digital Continuations",
  "3130 - Law Enforcement Equipment"
];

/********************************************************/
/* LOCATIONS */
/********************************************************/
export const locations = [
  "51140X",
  "51140E",
  "092000",
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

