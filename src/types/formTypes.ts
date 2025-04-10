/********************************************************/
/* FORM VALUES */
/********************************************************/


export type FormValues = {
  ID: string;
  reqID: string;
  requester: string;
  recipient: string;
  phoneext: string;
  datereq: string;
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

