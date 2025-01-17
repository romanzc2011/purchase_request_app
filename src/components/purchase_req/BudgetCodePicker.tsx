import { UseFormRegister, FieldErrors } from "react-hook-form";
import { FormValues } from "../../types/formTypes";
import { Box } from "@mui/material";

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
    <Box sx={{ display: "flex", alignItems: "center", gap: 2, width: "700px" }}>
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
        <option id={"generalOfficeEq"} value={"3101 - General Office Equipment"}>
          3101 - General Office Equipment
        </option>
        <option id={"audioRecording"} value={"3107 - Audio Recording Equipment"}>
          3107 - Audio Recording Equipment
        </option>
        <option id={"furnitureFix"} value={"3111 - Furniture and Fixtures"}>
          3111 - Furniture and Fixtures
        </option>
        <option id={"mailingEq"} value={"3113 - Mailing Equipment"}>
          3113 - Mailing Equipment
        </option>
        <option id={"newPrintDigi"} value={"3121 - Legal Resources - New Print and Digital Purchases"}>
          3121 - Legal Resources - New Print and Digital Purchases
        </option>
        <option id={"printDigiCont"} value={"3122 - Legal Resources - Print and Digital Continuations"}>
          3122 - Legal Resources - Print and Digital Continuations
        </option>
        <option id={"lawEnforceEq"} value={"3130 - Law Enforcement Equipment"}>
          3130 - Law Enforcement Equipment
        </option>
      </select>
      {errors.budgetObjCode && <p className="error">{errors.budgetObjCode.message}</p>}
      </Box>
  );
};

export default BudgetCodePicker;
