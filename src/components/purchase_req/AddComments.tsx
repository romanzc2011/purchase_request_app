import React from 'react';
import { UseFormRegister, FieldErrors } from 'react-hook-form';
import { FormValues } from "../../../types/formTypes";

interface AddCommentsProps {
  register: UseFormRegister<FormValues>;
  errors: FieldErrors<FormValues>;
}

const AddComments: React.FC<AddCommentsProps> = ({ register, errors }) => {
  return (
    <div className='m-3 row align-items-center'>
      {/** ADDITIONAL COMMENTS ****************************************************************** */}
      <div className="m-1 row">
        <label htmlFor="addComments" className="col-sm-2 col-form-label" style={{ fontSize: "1rem" }}>
          <strong>Additional Comments/Special Instructions</strong>
        </label>
        <div className="col-sm-5">
          <textarea
            style={{ fontSize: "0.8rem" }}
            id="addComments"
            rows={7}
            className="form-control"
            {...register("addComments")}
          />
          <p>{errors.addComments?.message}</p>
        </div>
      </div>
    </div>
  )
}

export default AddComments