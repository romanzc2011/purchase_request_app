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
    needsNotMeet: string;
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