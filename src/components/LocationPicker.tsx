import { UseFormRegister, FieldErrors } from "react-hook-form";
import { FormValues } from "../types/formTypes";

interface LocationProps {
  onSelectLocation: (location: string) => void;
  register: ReturnType<UseFormRegister<FormValues>>;
  errors: FieldErrors<FormValues>;
}

const LocationFilter = ({
  onSelectLocation,
  register,
  errors,
}: LocationProps) => {
  return (
    <>
      <label
        htmlFor="location"
        style={{ minWidth: "50px", whiteSpace: "nowrap" }}
      >
        <strong>Location</strong>
      </label>
      <select
        className="form-select"
        {...register}
        onChange={(e) => onSelectLocation(e.target.value)}
      >
        <option id={"ALEX/C"} value={"ALEX/C"}>
          ALEX/C
        </option>
        <option id={"ALEX/J"} value={"ALEX/J"}>
          ALEX/J
        </option>
        <option id={"LAFY/C"} value={"LAFY/C"}>
          LAFY/C
        </option>
        <option id={"LAFY/J"} value={"LAFY/J"}>
          LAFY/J
        </option>
        <option id={"LKCH/C"} value={"LKCH/C"}>
          LKCH/C
        </option>
        <option id={"LKCC/JA"} value={"LKCC/J"}>
          LKCC/J
        </option>
        <option id={"MONR/C"} value={"MONR/C"}>
          MONR/C
        </option>
        <option id={"MONR/J"} value={"MONR/J"}>
          MONR/J
        </option>
        <option id={"SHVT/C"} value={"SHVT/C"}>
          SHVT/C
        </option>
        <option id={"SHVT/J"} value={"SHVT/J"}>
          SHVT/J
        </option>
      </select>
      {errors.location && <p className="error">{errors.location.message}</p>}
    </>
  );
};

export default LocationFilter;
