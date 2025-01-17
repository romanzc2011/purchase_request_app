import { UseFormRegister, FieldErrors } from "react-hook-form";
import { FormValues } from "../../types/formTypes";
import { Box } from "@mui/material";

interface QuantityInputProps {
  register: ReturnType<UseFormRegister<FormValues>>;
  errors: FieldErrors<FormValues>;
}

const QuantityInput = ({ register, errors }: QuantityInputProps) => {
  return (
    <Box sx={{ display: "flex", alignItems: "center", gap: 2, width: "400px" }}>
      <label
        htmlFor="quantity"
        style={{ display: "block", width: "100px", whiteSpace: "nowrap" }}
      >
        <strong>Quantity:</strong>
      </label>
      <input
        id="quantity"
        type="number"
        className="form-control"
        placeholder="Enter quantity"
        {...register}
      />
      {errors.quantity && <p className="error">{errors.quantity.message}</p>}
    </Box>
  );
};

export default QuantityInput;
