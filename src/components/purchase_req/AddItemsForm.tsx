import "bootstrap/dist/css/bootstrap.min.css";
import { FieldErrors, useForm } from "react-hook-form";
import { DevTool } from "@hookform/devtools";
import React from "react";
import "./LearningDev";
import LearningDev from "./LearningDev";
import Buttons from "./Buttons";
import BudgetCodePicker from "./BudgetCodePicker";
import { useEffect } from "react";
import { FormValues } from "../../types/formTypes";
import { Box } from "@mui/material";
import LocationPicker from "./LocationPicker";
import FileUpload from "./FileUpload";
import FundPicker from "./FundPicker";
import PriceInput from "./PriceInput";
import QuantityInput from "./QuantityInput";
import { IFile } from "../../types/IFile";
import { v4 as uuidv4 } from "uuid";

interface AddItemsProps {
  reqID: string;
  dataBuffer: FormValues[];
  fileInfos: IFile[];
  setDataBuffer: React.Dispatch<React.SetStateAction<FormValues[]>>;
  setFileInfos: React.Dispatch<React.SetStateAction<IFile[]>>;
  setIsSubmitted: React.Dispatch<React.SetStateAction<boolean>>;
  setReqID: React.Dispatch<React.SetStateAction<string>>;
}

/*************************************************************************************** */
/* ADD ITEMS FORM */
/*************************************************************************************** */
function AddItemsForm({
  reqID,
  dataBuffer,
  fileInfos,
  setDataBuffer,
  setFileInfos,
  setIsSubmitted,
  setReqID
}: AddItemsProps) {

  /*************************************************************************************** */
  /* HANDLE ADD ITEM function */
  /*************************************************************************************** */
  const handleAddItem = async (newItem: FormValues) => {
    /* Becausee a user could upload a file first, if user uploads a file first then it will create a uuid */
    const updatedItem = {
      ...newItem,
      reqID: reqID,
      price: Number(newItem.price) || 0,
      fund: newItem.fund || "",
      budgetObjCode: newItem.budgetObjCode || "",
    };

    setDataBuffer((prev) => [...prev, updatedItem]); // Add to buffer

    // Update submit/req states/values for re-rendering
    setIsSubmitted(true);
    setReqID(uuidv4());

    reset(); // Clear form
    console.log("Item Added: ", updatedItem);
  };

  /*************************************************************************************** */
  /* HANDLE ADD ITEM ERRORS function */
  /*************************************************************************************** */
  const onError = (errors: FieldErrors<FormValues>) => {
    console.log("Form errors", errors);
  };

  const form = useForm<FormValues>({
    defaultValues: {
      reqID: reqID,
      requester: "",
      phoneext: "",
      datereq: null,
      dateneed: null,
      orderType: "",
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
  const { errors, isDirty, isValid, isSubmitSuccessful } = formState;

  /*************************************************************************************** */
  /* Form submission function */
  /*************************************************************************************** */
  useEffect(() => {
    const subscription = watch((value) => {
      console.log(value);
    });
    return () => subscription.unsubscribe();
  }, [watch]);

  /* Reset form after successful submission */
  useEffect(() => {
    if (isSubmitSuccessful) {
      reset();
    }
  }, [isSubmitSuccessful, reset]);

  return (
    <Box>
      {/*************************************************************************************** */}
      {/* FORM SECTION -- Adding items only to buffer, actual submit will occur in table
          once user has finished adding items and reviewed everything */}
      {/*************************************************************************************** */}
      <form onSubmit={handleSubmit(handleAddItem, onError)}>
        {/** REQUESTER ****************************************************************** */}
        <Box className="m-2 row">
          <label htmlFor="requester" className="col-sm-1 col-form-label mt-4">
            <strong>Requester</strong>
          </label>
          <Box className="col-sm-3">
            <input
              id="requester"
              type="text"
              className="form-control mt-4"
              {...register("requester", {
                required: {
                  value: true,
                  message: "Name of requester is required",
                },
              })}
            />
            <p className="error">{errors.requester?.message}</p>
          </Box>
        </Box>

        {/** PHONE EXT ****************************************************************** */}
        <Box className="m-2 row">
          <label htmlFor="phoneext" className="col-sm-1 col-form-label">
            <strong>Phone Extension</strong>
          </label>
          <Box className="col-sm-2">
            <input
              id="phoneext"
              type="text"
              style={{ width: "150px" }}
              className="form-control"
              {...register("phoneext", {
                required: {
                  value: true,
                  message: "Phone extension is required",
                },
              })}
            ></input>
            <p className="error">{errors.phoneext?.message}</p>
          </Box>
        </Box>

        {/*************************************************************************************** */}
        {/** DATE OF REQ ************************************************************************ */}
        {/*************************************************************************************** */}
        <Box className="m-2 row align-items-center">
          <label htmlFor="datereq" className="col-sm-1 col-form-label">
            <strong>Date of Request</strong>
          </label>
          <Box className="col-sm-1">
            <input
              id="datereq"
              type="date"
              style={{ width: "150px" }}
              className="form-control"
              {...register("datereq", {
                required: {
                  value: true,
                  message: "Date requested is required.",
                },
              })}
            ></input>
            <p className="error">{errors.datereq?.message}</p>
          </Box>
        </Box>

        {/*************************************************************************************** */}
        {/** DATE ITEMS NEEDED ****************************************************************** */}
        {/*************************************************************************************** */}
        <Box className="m-2 row align-items-center">
          <label htmlFor="dateneed" className="col-sm-1 col-form-label">
            <strong>Date Item(s) Needed</strong>
          </label>
          <Box className="col-sm-2">
            <Box style={{ display: "flex", alignItems: "center", gap: "30px" }}>
              <input
                id="dateneed"
                type="date"
                style={{ width: "150px" }}
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
              <Box>
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
              </Box>
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
            </Box>
            <p className="error">{errors.dateneed?.message}</p>

            {/************************************************************************************ */}
          </Box>
        </Box>

        {/** ATTACHMENTS INCLUDED? ****************************************************************** */}
        <Box
          className="m-1 align-items-center row"
          sx={{ display: "flex", alignItems: "center", gap: 38 }}
        >
          <label
            htmlFor="fileAttachments"
            style={{
              fontSize: "0.9rem",
              maxWidth: "250px",
              whiteSpace: "nowrap",
            }}
          >
            <strong style={{ fontSize: "0.9rem" }}>
              Attachments included?
            </strong>
            (training information, pictures, web pages, screen shots, etc.)
          </label>

          <FileUpload
            reqID={reqID}
            fileInfos={fileInfos}
            setFileInfos={setFileInfos}
          />
        </Box>

        {/** ITEM DESCRIPTION ****************************************************************** */}
        <Box className="m-3 align-items-center row">
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
          <Box className="col-sm-4">
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
          </Box>
        </Box>

        {/** FOR LEARNING OR DEV? ****************************************************************** */}
        <Box>
          <LearningDev register={register} errors={errors} />
        </Box>

        <Box sx={{ my: 2 }}>
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

            {/************************************************************************************ */}
            {/* LOCATION */}
            <LocationPicker
              onSelectLocation={(location: string) => console.log(location)}
              register={register("location")}
              errors={errors}
            />
          </Box>

          <Box sx={{ display: "flex", gap: 5, alignItems: "center", mt: 5 }}>
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
    </Box>
  );
};

export default AddItemsForm;
