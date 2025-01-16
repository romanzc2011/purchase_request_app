import { UseFormRegister, FieldErrors } from "react-hook-form";
import { FormValues } from "../../types/formTypes";
import { Box } from "@mui/material";

interface PriceInputProps {
  register: ReturnType<UseFormRegister<FormValues>>;
  errors: FieldErrors<FormValues>;
}

const PriceInput = ({ register, errors }: PriceInputProps) => {
  return (
    <Box sx={{ display: "flex", alignItems: "center", gap: 1, width: "358px" }}>
      <label
        htmlFor="price"
        style={{ display: "block", width: "100px", whiteSpace: "nowrap" }}
      >
        <strong>Price:</strong>
      </label>
      <input
        id="price"
        type="number"
        className="form-control"
        placeholder="Enter Price"
        {...register}
      />
      {errors.price && <p className="error">{errors.price.message}</p>}
    </Box>
  );
};

export default PriceInput;
