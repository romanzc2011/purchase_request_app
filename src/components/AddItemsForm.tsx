import { FieldErrors, useForm, useFieldArray, Field } from "react-hook-form";
import { DevTool } from "@hookform/devtools";
import React, { useState } from "react";
import "./LearningDev";
import LearningDev from "./LearningDev";
import Buttons from "./Buttons";
import BudgetCodePicker from "./BudgetCodePicker";
import { useEffect } from "react";
import { FormValues } from "../types/formTypes";
import { Box } from "@mui/material";
import Grid from "@mui/material/Grid";
import LocationPicker from "./LocationPicker";
import FundPicker from "./FundPicker";
import PriceInput from "./PriceInput";
import QuantityInput from "./QuantityInput";

/*************************************************************************************** */
/* ADD ITEMS FORM */
/*************************************************************************************** */
export const AddItemsForm: React.FC<{
  dataBuffer: FormValues[];
  setDataBuffer: React.Dispatch<React.SetStateAction<FormValues[]>>;
}> = ({ dataBuffer, setDataBuffer }) => {
  /*************************************************************************************** */
  /* HANDLE ADD ITEM function */
  /*************************************************************************************** */
  const handleAddItem = (newItem: FormValues) => {
    const updatedItem = {
      ...newItem,
      id: generateRandomID(),
      price: Number(newItem.price) || 0,
      fund: newItem.fund || "",
      budgetObjCode: newItem.budgetObjCode || "",
    };

    setDataBuffer((prev) => [...prev, updatedItem]); // Add to buffer
    reset(); // Clear form
    console.log("Item Added: ", updatedItem);
  };

  /*************************************************************************************** */
  /* HANDLE ADD ITEM ERRORS function */
  /*************************************************************************************** */
  const onError = (errors: FieldErrors<FormValues>) => {
    console.log("Form errors", errors);
  };

  /* RANDOM ID GENERATOR 
  This will be for testing purposes only, in prod this will be
  replaced with a Requistion number or something more useful
  for finance */
  const generateRandomID = () => {
    const min = 1;
    const max = 5000;
    return Math.floor(Math.random() * (max - min + 1)) + min;
  };

  const form = useForm<FormValues>({
    defaultValues: {
      id: 0,
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
      budgetObjCode: "",
      fund: "",
      price: 0,
      location: "",
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

  /*************************************************************************************** */
  /* Form submission function */
  /*************************************************************************************** */

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
  /* File upload input element */
  /*************************************************************************************** */
  const { fields, append, remove } = useFieldArray({
    name: "fileAttachments",
    control,
  });

  return (
    <Grid>
      {/*************************************************************************************** */}
      {/* FORM SECTION -- Adding items only to buffer, actual submit will occur in table
          once user has finished adding items and reviewed everything */}
      {/*************************************************************************************** */}
      <form onSubmit={handleSubmit(handleAddItem, onError)} noValidate>
        {/** REQUESTER ****************************************************************** */}
        <Grid className="m-2 row">
          <label htmlFor="requester" className="col-sm-2 col-form-label">
            <strong>Requester</strong>
          </label>
          <Grid className="col-sm-5">
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
          </Grid>
        </Grid>

        {/** PHONE EXT ****************************************************************** */}
        <Grid className="m-2 row align-items-left">
          <label htmlFor="phoneext" className="col-sm-2 col-form-label">
            <strong>Phone Extension</strong>
          </label>
          <Grid className="col-sm-2">
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
          </Grid>
        </Grid>

        {/** DATE OF REQ ****************************************************************** */}
        <Grid className="m-2 row align-items-center">
          <label htmlFor="datereq" className="col-sm-2 col-form-label">
            <strong>Date of Request</strong>
          </label>
          <Grid className="col-sm-2">
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
          </Grid>
        </Grid>
        {/*************************************************************************************** */}

        {/** DATE ITEMS NEEDED ****************************************************************** */}
        <Grid className="m-2 row align-items-center">
          <label htmlFor="dateneed" className="col-sm-2 col-form-label">
            <strong>Date Item(s) Needed</strong>
          </label>
          <Grid className="col-sm-4">
            <Grid
              style={{ display: "flex", alignItems: "center", gap: "30px" }}
            >
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
              <Grid>
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
              </Grid>
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
            </Grid>
            <p className="error">{errors.dateneed?.message}</p>

            {/************************************************************************************ */}
          </Grid>
        </Grid>

        {/** ATTACHMENTS INCLUDED? ****************************************************************** */}
        <Grid className="m-3 align-items-center row">
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
          <Grid className="col-sm-6">
            {fields.map((field, index) => {
              const fileValue = watch(`fileAttachments.${index}.attachment`);

              return (
                <Grid className="mt-2 d-flex align-items-center" key={field.id}>
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
                </Grid>
              );
            })}

            <Grid className="d-flex align-items-center mt-3">
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
            </Grid>
          </Grid>
        </Grid>

        {/** ITEM DESCRIPTION ****************************************************************** */}
        <Grid className="m-3 align-items-center row">
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
          <Grid className="col-sm-4">
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
          </Grid>
        </Grid>

        {/** FOR LEARNING OR DEV? ****************************************************************** */}
        <Grid>
          <LearningDev register={register} errors={errors} />
        </Grid>

        <Box sx={{ my: 3 }}>
          <Box
            sx={{
              display: "flex",
              gap: 2,
              alignItems: "center",
              flexWrap: "nowrap",
            }}
          >
            {/************************************************************************************ */}
            {/* BUDGET OBJECT CODE */}
            <BudgetCodePicker
              onSelectBudgetCode={(budgetObjCode) => console.log(budgetObjCode)}
              register={register("budgetObjCode")}
              errors={errors}
            />

            {/************************************************************************************ */}
            {/* FUND SELECT */}
            <FundPicker
              onSelectFund={(fund: string) => console.log(fund)}
              register={register("fund")}
              errors={errors}
            />
          </Box>

          <Box sx={{ display: "flex", gap: 5, alignItems: "center", mt: 3 }}>
            {/************************************************************************************ */}
            {/* LOCATION */}
            <LocationPicker
              onSelectLocation={(location: string) => console.log(location)}
              register={register("location")}
              errors={errors}
            />

            {/************************************************************************************ */}
            {/* PRICE */}
            <PriceInput
              register={register("price", {
                required: "Price is required.",
                validate: (value) =>
                  value >= 0 || "Price cannot be less than $0.",
              })}
              errors={errors}
            />

            {/************************************************************************************ */}
            {/* QUANTITY */}
            <QuantityInput
              register={register("quantity", {
                required: "Quantity is required.",
                validate: (value) =>
                  value > 0 || "Quantity must be greater than 0.",
              })}
              errors={errors}
            />
          </Box>
        </Box>

        {/************************************************************************************ */}
        {/* BUTTONS: ADD ITEM, Clear */}
        {/************************************************************************************ */}
        <Box sx={{ display: "flex", justifyContent: "flex-start" }}>
          {/* Capture all data pertaining to the request temporarily to allow for addition of additional items
              SUBMIT button will handle gathering and sending the data to proper supervisors */}
          <Buttons
            className="me-3 btn btn-maroon"
            disabled={!isDirty || !isValid}
            label="Add Item"
            onClick={handleSubmit(handleAddItem)}
          />
          <Buttons
            label="Reset Form"
            className="btn btn-maroon"
            onClick={() => reset()}
          />
        </Box>
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
    </Grid>
  );
};

export default AddItemsForm;
