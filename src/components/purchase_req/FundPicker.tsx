import { UseFormRegister, FieldErrors } from "react-hook-form";
import { FormValues } from "../../types/formTypes";
import { Box } from "@mui/material";

interface FundPickerProps {
  onSelectFund: (fund: string) => void;
  register: ReturnType<UseFormRegister<FormValues>>;
  errors: FieldErrors<FormValues>;
}

const FundPicker = ({ onSelectFund, register, errors }: FundPickerProps) => {
  return (
    <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
      <label
        htmlFor="fund"
        style={{
          display: "block",
          width: "100px",
          whiteSpace: "nowrap",
          textAlign: "right",
          marginRight: "5px",
        }}
      >
        <strong>Fund:</strong>
      </label>
      <select
        className="form-select"
        {...register}
        onChange={(e) => onSelectFund(e.target.value)}
      >
        <option value={"092000"}>092000</option>
        <option value={"51140E"}>51140E</option>
        <option value={"51140X"}>51140X</option>
      </select>
      {errors.fund && <p className="error">{errors.fund.message}</p>}
    </Box>
  );
};

export default FundPicker;
