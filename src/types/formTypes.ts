export type FormValues = {
    req_id: number;
    requester: string;
    phoneext: string;
    datereq: Date | null;
    dateneed: Date | null;
    orderType: string;
    fileAttachments: {
      attachment: File | null;
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
    fund: string;
    location: string;
    budgetObjCode: string;
  };