import { UseFormRegister, FieldErrors } from "react-hook-form";
import { FormValues } from "../types/formTypes";

interface FundPickerProps {
  onSelectFund: (fund: string) => void;
  register: ReturnType<UseFormRegister<FormValues>>;
  errors: FieldErrors<FormValues>;
}

const FundPicker = ({ onSelectFund, register, errors }: FundPickerProps) => {
  return (
    <>
      <label
        htmlFor="fund"
        style={{ display: "block", width: "100px", whiteSpace: "nowrap" }}
      >
        <strong>Fund</strong>
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
    </>
  );
};

export default FundPicker;
