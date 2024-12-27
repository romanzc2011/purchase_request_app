import React from 'react';
import { UseFormRegister, FieldErrors } from 'react-hook-form';
import { FormValues } from '../PurchaseForm';

interface JustificationProps {
  register: UseFormRegister<FormValues>;
  errors: FieldErrors<FormValues>;
}

const Justification: React.FC<JustificationProps> = ({ register, errors }) => {
  return (
    <div className='m-3 row align-items-center'>
      {/** JUSTIFICATION ****************************************************************** */}
      <div className="m-1 row">
        <label htmlFor="justification" className="col-sm-3 col-form-label">
          <strong>Justification/Business Purpose</strong>
        </label>
        <div className="col-sm-5">
          <textarea
            style={{ fontSize: "0.8rem" }}
            id="justification"
            rows={7}
            className="form-control"
            {...register("justification", {
              required: {
                value: true,
                message: "Justification for item required"
              }
            })}
          />
          <p className='error'>{errors.justification?.message}</p>
        </div>
      </div>
    </div>
  )
}

export default Justification;