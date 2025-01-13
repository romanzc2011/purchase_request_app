import React from "react";
import Justification from "./Justification";
import AddComments from "./AddComments";
import { UseFormRegister, FieldErrors } from "react-hook-form";
import { FormValues } from "../../../types/formTypes";

interface LearningDevProps {
  register: UseFormRegister<FormValues>;
  errors: FieldErrors<FormValues>;
}

const LearningDev: React.FC<LearningDevProps> = ({ register, errors }) => {
  return (
    <div className="row">
      <div className="col-sm-5">
        {/* Checkbox for train/dev is not available via Federal Judiciary Center */}
        <label
          htmlFor="trainNotAval"
          style={{
            fontSize: "0.8rem",
            marginLeft: "20px",
            whiteSpace: "normal",
          }}
        >
          <strong style={{ fontSize: "0.9rem" }}>If related to Learning & Development:</strong> In accordance
          with the Guide, Volume12, §1125.10(c), Requester certifies: OR the
          proposed training is not available from the Federal Judicial Center
          (FJC) and/or AO websites.
          <input
            id="notAval"
            style={{ marginRight: "5px", marginLeft: "10px" }}
            type="checkbox"
            value="trainNotAval"
            {...register("learnAndDev.trainNotAval")}
          />
        </label>
      </div>

      <div className="col-sm-1">
        <strong>OR</strong>
      </div>

      {/* Checkbox for not meeting employees needs */}
      <div className="col-sm-5">
        <label
          htmlFor="needsNotMeet"
          style={{
            fontSize: "0.8rem",
            marginLeft: "20px",
            whiteSpace: "normal",
          }}
        >
          Training(s) that are offered from the FJC and/or websites do not meet
          the employee(s) needs. Justification is required below or as an
          attachment.
          <input
            id="needsNotMeet"
            style={{ marginRight: "5px", marginLeft: "10px" }}
            type="checkbox"
            value="needsNotMeet"
            {...register("learnAndDev.needsNotMeet")}
          />
        </label>
      </div>

      {/* JUSTIFICATION */}
      <div>
        <Justification register={register} errors={errors} />
      </div>

      {/* ADDITIONAL COMMENTS */}
      <div>
        <AddComments register={register} errors={errors} />
      </div>
    </div>
  );
};

export default LearningDev;