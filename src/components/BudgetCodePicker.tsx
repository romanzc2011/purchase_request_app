import React from "react";
import { UseFormRegister, FieldErrors } from "react-hook-form";
import { FormValues } from "../types/formTypes";

interface BudgetPickerProps {
  onSelectBudgetCode: (budgetObjCode: string) => void;
  register: ReturnType<UseFormRegister<FormValues>>;
  errors: FieldErrors<FormValues>;
}

const BudgetCodePicker = ({
  onSelectBudgetCode,
  register,
  errors,
}: BudgetPickerProps) => {
  return (
    <>
      <label
        htmlFor="budgetObjCode"
        style={{
          display: "block",
          minWidth: "200px",
          whiteSpace: "nowrap",
          textAlign: "right",
          marginRight: "8px",
        }}
      >
        <strong>Budget Object Code (BOC):</strong>
      </label>

      <select
        className="form-select"
        {...register}
        onChange={(e) => onSelectBudgetCode(e.target.value)}
      >
        <option id={"generalOfficeEq"} value={"generalOfficeEq"}>
          3101 - General Office Equipment
        </option>
        <option id={"audioRecording"} value={"audioRecordingEq"}>
          3107 - Audio Recording Equipment
        </option>
        <option id={"furnitureFix"} value={"furnitureFix"}>
          3111 - Furniture and Fixtures
        </option>
        <option id={"mailingEq"} value={"mailingEq"}>
          3113 - Mailing Equipment
        </option>
        <option id={"newPrintDigi"} value={"newPrintDigi"}>
          3121 - Legal Resources - New Print and Digital Purchases
        </option>
        <option id={"printDigiCont"} value={"printDigiCont"}>
          3122 - Legal Resources - Print and Digital Continuations
        </option>
        <option id={"lawEnforceEq"} value={"lawEnforceEq"}>
          3130 - Law Enforcement Equipment
        </option>
      </select>
      {errors.budgetObjCode && <p className="error">{errors.budgetObjCode.message}</p>}
    </>
  );
};

export default BudgetCodePicker;
