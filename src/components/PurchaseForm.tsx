import { FieldErrors, useForm, useFieldArray } from "react-hook-form";
import { DevTool } from "@hookform/devtools";
import "./learn_dev_radio/LearningDev";
import LearningDev from "./learn_dev_radio/LearningDev";
import Buttons from "./Buttons";
import BKSeal from "../assets/seal_no_border.png";
import { useEffect, useRef } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

/*************************************************************************************** */
/* Form Data Structure */
/*************************************************************************************** */
export type FormValues = {
  requester: string;
  phoneext: string;
  datereq: Date | null;
  dateneed: Date | null;
  orderType: string;
  fileAttachments: {
    attachment: File | null;
  }[];
  itemDescription: string;
  justification: string;
  addComments: string;
  learnAndDev: {
    trainNotAval: string;
    needsNotMeet: string;
  };
};

/*************************************************************************************** */
/* Default form values */
/*************************************************************************************** */
export const PurchaseForm: React.FC = () => {
  const form = useForm<FormValues>({
    defaultValues: {
      requester: "",
      phoneext: "",
      datereq: null,
      dateneed: null,
      orderType: "",
      fileAttachments: [{ attachment: null }],
      itemDescription: "",
      justification: "",
      addComments: "",
      learnAndDev: {
        trainNotAval: "",
        needsNotMeet: "",
      },
    },
    mode: "onSubmit",
  });

  const { register, control, handleSubmit, formState, watch, reset } = form;
  const {
    errors,
    isDirty,
    isValid,
    isSubmitting,
    isSubmitted,
    isSubmitSuccessful,
  } = formState;

  console.log({ isSubmitting, isSubmitted, isSubmitSuccessful });

  //console.log({ touchedFields, dirtyFields, isDirty, isValid });

  /*************************************************************************************** */
  /* File upload input element */
  /*************************************************************************************** */
  const { fields, append, remove } = useFieldArray({
    name: "fileAttachments",
    control,
  });

  /*************************************************************************************** */
  /* Form submission function */
  /*************************************************************************************** */
  const onSubmit = (data: FormValues) => {
    console.log("Form submitted", data);
  };

  useEffect(() => {
    const subscription = watch((value) => {
      console.log(value);
    });
    return () => subscription.unsubscribe();
  }, [watch]);

  /* Watch all values in Form */
  const watchForm = watch();

  /* Reset form after successful submission */
  useEffect(() => {
    if (isSubmitSuccessful) {
      reset();
    }
  }, [isSubmitSuccessful, reset]);

  /*************************************************************************************** */
  /* Form Errors Function */
  /*************************************************************************************** */
  const onError = (errors: FieldErrors<FormValues>) => {
    console.log("Form errors", errors);
  };

  function checkIfFileNull() {
    const myFile = useRef(null);
  }

  return (
    <div>
      {/*************************************************************************************** */}
      {/* Header Section */}
      {/*************************************************************************************** */}
      <div style={{ textAlign: "center", marginBottom: "30px" }}>
        <img src={BKSeal} style={{ marginBottom: "20px" }} alt="Seal" />
        <h3 style={{ fontWeight: "bold" }}>
          <div className="row">
            <div className="col text-center">
              UNITED STATES BANKRUPTCY COURT
            </div>
          </div>
          WESTERN DISTRICT OF LOUISIANA
          <br />
          <span style={{ fontSize: "1.2rem" }}>PURCHASE REQUEST FORM</span>
        </h3>
      </div>

      {/*************************************************************************************** */}
      {/* FORM SECTION */}
      {/*************************************************************************************** */}
      <form onSubmit={handleSubmit(onSubmit, onError)} noValidate>
        {/** REQUESTER ****************************************************************** */}
        <div className="m-2 row">
          <label htmlFor="requester" className="col-sm-2 col-form-label">
            <strong>Requester</strong>
          </label>
          <div className="col-sm-5">
            <input
              id="requester"
              type="text"
              className="form-control"
              {...register("requester", {
                required: {
                  value: true,
                  message: "Name of requester is required",
                },
              })}
            />
            <p className="error">{errors.requester?.message}</p>
          </div>
        </div>

        {/** PHONE EXT ****************************************************************** */}
        <div className="m-2 row align-items-left">
          <label htmlFor="phoneext" className="col-sm-2 col-form-label">
            <strong>Phone Extension</strong>
          </label>
          <div className="col-sm-2">
            <input
              id="phoneext"
              type="text"
              className="form-control"
              {...register("phoneext", {
                required: {
                  value: true,
                  message: "Phone extension is required",
                },
              })}
            ></input>
            <p className="error">{errors.phoneext?.message}</p>
          </div>
        </div>

        {/** DATE OF REQ ****************************************************************** */}
        <div className="m-2 row align-items-center">
          <label htmlFor="datereq" className="col-sm-2 col-form-label">
            <strong>Date of Request</strong>
          </label>
          <div className="col-sm-2">
            <input
              id="datereq"
              type="date"
              className="form-control"
              {...register("datereq", {
                required: {
                  value: true,
                  message: "Date requested is required.",
                },
              })}
            ></input>
            <p className="error">{errors.datereq?.message}</p>
          </div>
        </div>
        {/*************************************************************************************** */}

        {/** DATE ITEMS NEEDED ****************************************************************** */}
        <div className="m-2 row align-items-center">
          <label htmlFor="dateneed" className="col-sm-2 col-form-label">
            <strong>Date Item(s) Needed</strong>
          </label>
          <div className="col-sm-4">
            <div style={{ display: "flex", alignItems: "center", gap: "30px" }}>
              <input
                id="dateneed"
                type="date"
                className="form-control"
                {...register("dateneed", {
                  validate: (value, { orderType }) => {
                    if (!value && !orderType) {
                      return "'Date Item(s) Needed' OR an option must be selected.";
                    }
                    return true;
                  },
                })}
              />
              <strong>OR</strong>
              <div>
                <label
                  htmlFor="quarterlyOrder"
                  style={{ fontSize: "0.8rem", whiteSpace: "nowrap" }}
                >
                  <input
                    id="quarterlyOrder"
                    type="radio"
                    value="quarterlyOrder"
                    {...register("orderType")}
                    style={{ marginRight: "3px" }}
                  />
                  Inclusion w/quarterly office supply order
                </label>
              </div>
              <strong>OR</strong>
              <label
                htmlFor="noRush"
                style={{ fontSize: "0.8rem", whiteSpace: "nowrap" }}
              >
                <input
                  id="noRush"
                  type="radio"
                  value="noRush"
                  {...register("orderType")}
                  style={{ marginRight: "5px" }}
                />
                No Rush
              </label>
            </div>
            <p className="error">{errors.dateneed?.message}</p>

            {/************************************************************************************ */}
          </div>
        </div>

        {/** ATTACHMENTS INCLUDED? ****************************************************************** */}
        <div className="m-3 align-items-center row">
          <label
            style={{ fontSize: "0.8rem" }}
            htmlFor="fileAttachments"
            className="col-sm-3 col-form-label"
          >
            <strong style={{ fontSize: "0.9rem" }}>
              Attachments included?
            </strong>{" "}
            (training information, pictures, web pages, screen shots, etc.)
          </label>

          {/********************************************************************************************* */}
          {/** ATTACHMENTS FIELD ARRAY ****************************************************************** */}
          {/********************************************************************************************* */}
          <div className="col-sm-6">
            {fields.map((field, index) => {
              const fileValue = watch(`fileAttachments.${index}.attachment`);

              return (
                <div className="mt-2 d-flex align-items-center" key={field.id}>
                  <input
                    type="file"
                    className="form-control me-2"
                    style={{ width: "350px" }}
                    multiple
                    {...register(
                      `fileAttachments.${index}.attachment` as const,
                      {
                        validate: (value) =>
                          value instanceof File ||
                          value === null ||
                          "File is required",
                      }
                    )}
                  />
                  <p className="error">
                    {errors.fileAttachments?.[index]?.attachment?.message}
                  </p>

                  {/* Only show REMOVE button if more than 1 file/attachment */}
                  {index > 0 && (
                    <Buttons
                      className="btn btn-danger me-2"
                      onClick={() => remove(index)}
                      label="Remove"
                    />
                  )}
                </div>
              );
            })}

            <div className="d-flex align-items-center mt-3">
              {/* Conditionally render "Add File" button */}
              {fields.every(
                (field, index) => !!watch(`fileAttachments.${index}.attachment`) // Check if all fields have files uploaded
              ) && (
                <Buttons
                  className="btn btn-primary me-2"
                  onClick={() => append({ attachment: null })}
                  label="Add File"
                />
              )}
            </div>
          </div>
        </div>

        {/** ITEM DESCRIPTION ****************************************************************** */}
        <div className="m-3 align-items-center row">
          <label
            style={{ fontSize: "0.8rem" }}
            htmlFor="itemDescription"
            className="col-sm-4 col-form-label"
          >
            <strong style={{ fontSize: "0.9rem" }}>
              Description of Item/Project:
            </strong>{" "}
            (Include details such as qty, color, size, intended recipient, etc.)
            <br /> NOTE: If request is for office supplies needed before the
            next quarterly order, please state the justification.
          </label>
          <div className="col-sm-4">
            <textarea
              style={{ fontSize: "0.8rem" }}
              id="itemDescription"
              rows={6}
              className="form-control"
              {...register("itemDescription", {
                required: {
                  value: true,
                  message: "Item description required.",
                },
              })}
            />
            <p className="error">{errors.itemDescription?.message}</p>
          </div>
        </div>

        {/** FOR LEARNING OR DEV? ****************************************************************** */}
        <div>
          <LearningDev register={register} errors={errors} />
        </div>

        {/************************************************************************************ */}
        {/* BUTTONS: Submit Form, Print Form, Clear */}
        {/************************************************************************************ */}
        <div>
          <Buttons disabled={!isDirty || !isValid} label="Submit Form" />
          <Buttons label="Print Form" />
          <Buttons
            label="Reset Form"
            className="btn btn-warning"
            onClick={() => reset()}
          />
        </div>
        <hr
          style={{
            backgroundColor: "white",
            height: "2px",
            border: "none",
            margin: "20px 0",
          }}
        />
      </form>
      <DevTool control={control} />
    </div>
  );
};

export default PurchaseForm;
