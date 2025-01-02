import { UseFormRegister, FieldErrors } from "react-hook-form";
import { FormValues } from "../types/formTypes";

interface PriceInputProps {
  register: ReturnType<UseFormRegister<FormValues>>;
  errors: FieldErrors<FormValues>;
}

const PriceInput = ({ register, errors }: PriceInputProps) => {
  return (
    <>
      <label
        htmlFor="price"
        style={{ display: "block", width: "100px", whiteSpace: "nowrap" }}
      >
        <strong>Price</strong>
      </label>
      <input
        id="price"
        type="number"
        className="form-control"
        placeholder="Enter price"
        {...register}
      />
      {errors.price && <p className="error">{errors.price.message}</p>}
    </>
  );
};

export default PriceInput;
