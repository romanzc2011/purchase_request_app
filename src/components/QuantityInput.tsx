import { UseFormRegister, FieldErrors } from "react-hook-form";
import { FormValues } from "../types/formTypes";

interface QuantityInputProps {
  register: ReturnType<UseFormRegister<FormValues>>;
  errors: FieldErrors<FormValues>;
}

const QuantityInput = ({ register, errors }: QuantityInputProps) => {
  return (
    <>
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
    </>
  );
};

export default QuantityInput;
