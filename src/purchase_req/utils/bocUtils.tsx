const BOC_MAPPING: Record<string, string> = {
  generalOfficeEq: "3101 - General Office Equipment",
  audioRecordingEq: "3102 - Audio Recording Equipment",
  furnitureFix: "3103 - Furniture and Fixtures",
  mailingEq: "3104 - Mailing Equipment",
  newPrintDigi: "3105 - New Print and Digital Equipment",
  printDigiCont: "3106 - Printing and Digital Content",
  lawEnforceEq: "3107 - Law Enforcement Equipment",
};

export const convertBOC = (boc: string): string => {
    return BOC_MAPPING[boc] || boc; // Return original if no match
}
