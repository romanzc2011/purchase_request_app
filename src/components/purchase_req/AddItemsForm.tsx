import { FieldErrors, useForm } from "react-hook-form";
import { DevTool } from "@hookform/devtools";
import React from "react";
import { useMutation } from "@tanstack/react-query";
import "./LearningDev";
import { Box } from "@mui/material";
import LearningDev from "./LearningDev";
import Buttons from "./Buttons";
import BudgetCodePicker from "./BudgetCodePicker";
import { useEffect } from "react";
import { FormValues } from "../../types/formTypes";
import { TextField, Typography } from "@mui/material";
import Grid from "@mui/material/Grid2";
import LocationPicker from "./LocationPicker";
import FileUpload from "./FileUpload";
import FundPicker from "./FundPicker";
import PriceInput from "./PriceInput";
import QuantityInput from "./QuantityInput";
import { IFile } from "../../types/IFile";
import { v4 as uuidv4 } from "uuid";
import InfoIcon from "@mui/icons-material/Info";
import Tooltip from "@mui/material/Tooltip";
import Justification from "./Justification";
import AddComments from "./AddComments";

/************************************************************************************ */
/* CONFIG API URL- */
/************************************************************************************ */
const baseURL = import.meta.env.VITE_API_URL;
const API_CALL: string = "/api/getReqID";
const API_URL = `${baseURL}${API_CALL}`;

/*************************************************************************************** */
/* INTERFACE PROPS */
/*************************************************************************************** */
interface AddItemsProps {
    ID: string;
    fileInfo: IFile[];
    setDataBuffer: React.Dispatch<React.SetStateAction<FormValues[]>>;
    setIsSubmitted: React.Dispatch<React.SetStateAction<boolean>>;
    setID: React.Dispatch<React.SetStateAction<string>>;
    setFileInfo: React.Dispatch<React.SetStateAction<IFile[]>>;
}

/*************************************************************************************** */
/* GENERATE REQUISITION ID */
/*************************************************************************************** */
async function generateReqID(requestData: FormValues): Promise<{ reqID: string }>  {
    const response = await fetch(API_URL, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify(requestData),
    });
    if (!response.ok) {
        throw new Error(`HTTP error: ${response.status}`);
    }
    return response.json();
}

/*************************************************************************************** */
/* ADD ITEMS FORM */
/*************************************************************************************** */
function AddItemsForm({
    ID,
    setDataBuffer,
    setID,
    fileInfo,
    setFileInfo,
}: AddItemsProps) {
    const { mutate: generateReqIDMutation } = useMutation<{ reqID: string }, Error, FormValues>({
        mutationFn: generateReqID,
    });

    /*************************************************************************************** */
    /* HANDLE ADD ITEM function */
    /*************************************************************************************** */
    const handleAddItem = async (newItem: FormValues) => {
        /* Becausee a user could upload a file first, if user uploads a file first then it will create a uuid */
        const newID = uuidv4();
        //const newReqID = "send to create reqid service";
        const updatedItem = {
            ...newItem,
            ID: newID,
            price: Number(newItem.price) || 0,
            fund: newItem.fund || "",
            budgetObjCode: newItem.budgetObjCode || "",
        };

        // Trigger the mutation to generate a reqID
        generateReqIDMutation(updatedItem, {
            onSuccess: (data: { reqID: string }) => {
                // Update the item with the generated reqID
                updatedItem.reqID = data.reqID;
                console.log("Received reqID: ", data.reqID);
                // Now update the buffer and state
                setDataBuffer((prev) => [...prev, updatedItem]);
                setID(newID);
                reset();
                console.log("Item Added: ", updatedItem);
            },
            onError: (err) => {
                console.error("Error generating reqID", err);
            },
        });
    };

    /*************************************************************************************** */
    /* HANDLE ADD ITEM ERRORS function */
    /*************************************************************************************** */
    const onError = (errors: FieldErrors<FormValues>) => {
        console.log("Form errors", errors);
    };

    const form = useForm<FormValues>({
        defaultValues: {
            ID: ID,
            reqID: "reqID",
            requester: "",
            recipient: "",
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
            quantity: 0,
        },
        mode: "onChange",
    });

    const { register, control, handleSubmit, formState, watch, reset } = form;
    const { errors, isValid, isSubmitted } = formState;

    /*************************************************************************************** */
    /* Form submission function */
    /*************************************************************************************** */
    useEffect(() => {
        const subscription = watch((value) => {
            console.log(value);
        });
        return () => subscription.unsubscribe();
    }, [watch]);

    return (
        <Box sx={{ display: 'flex' }}>
            {/*************************************************************************************** */}
            {/* FORM SECTION -- Adding items only to buffer, actual submit will occur in table
              once user has finished adding items and reviewed everything */}
            {/*************************************************************************************** */}
            <form onSubmit={handleSubmit(handleAddItem, onError)}>
                {/******************************************************************************************* */}
                {/** REQUESTER ****************************************************************************** */}
                {/******************************************************************************************* */}
                <Grid container spacing={1} alignItems="center" sx={{ mt: 4 }}>
                    <Grid size={{ xs: 2 }}>
                        <Typography
                            variant="button"
                            component="label"
                            htmlFor="requester"
                        >
                            <strong>Requester</strong>
                        </Typography>
                    </Grid>
                    <Grid size={{ xs: 6, sm: 3 }}>
                        <TextField
                            id="requester"
                            className="form-control"
                            fullWidth
                            variant="outlined"
                            size="small"
                            {...register("requester", {
                                required: "Name of requester is required",
                            })}
                            error={!!errors.requester}
                            helperText={errors.requester?.message}
                        />
                    </Grid>
                </Grid>
                {/******************************************************************************************* */}
                {/** RECIPIENT ****************************************************************************** */}
                {/******************************************************************************************* */}
                <Grid container spacing={1} alignItems="center" sx={{ mt: 4 }}>
                    <Grid size={{ xs: 2 }}>
                        <Typography
                            variant="button"
                            component="label"
                            htmlFor="recipient"
                        >
                            <strong>Recipient</strong>
                        </Typography>
                    </Grid>
                    <Grid size={{ xs: 6, sm: 3 }}>
                        <TextField
                            id="recipient"
                            className="form-control"
                            fullWidth
                            variant="outlined"
                            size="small"
                            {...register("recipient", {
                                required: "Name of recipient is required",
                            })}
                            error={!!errors.recipient}
                            helperText={errors.recipient?.message}
                        />
                    </Grid>
                </Grid>

                {/******************************************************************************************* */}
                {/** PHONE EXT ****************************************************************************** */}
                {/******************************************************************************************* */}
                <Grid container spacing={1} alignItems="center" sx={{ mt: 4 }}>
                    <Grid size={{ xs: 2 }}>
                        <Typography
                            variant="button"
                            component="label"
                            htmlFor="phoneext"
                        >
                            <strong>Phone Extension</strong>
                        </Typography>
                    </Grid>
                    <Grid size={{ xs: 6, sm: 3 }}>
                        <TextField
                            id="phoneext"
                            className="form-control"
                            fullWidth
                            variant="outlined"
                            size="small"
                            {...register("phoneext", {
                                required: "Phone extention is required",
                            })}
                            error={!!errors.requester}
                            helperText={errors.requester?.message}
                        />
                    </Grid>
                </Grid>

                {/*************************************************************************************** */}
                {/** DATE OF REQ ************************************************************************ */}
                {/*************************************************************************************** */}
                <Grid container spacing={1} sx={{ mt: 4 }}>
                    <Grid size={{ xs: 2 }}>
                        <Typography
                            variant="button"
                            component="label"
                            htmlFor="datereq"
                            sx={{ whiteSpace: "nowrap" }}
                        >
                            <strong>Date of Request</strong>
                        </Typography>
                    </Grid>
                    <Grid size={{ xs: 6, sm: 3 }}>
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
                    </Grid>
                </Grid>

                {/*************************************************************************************** */}
                {/** DATE ITEMS NEEDED ****************************************************************** */}
                {/*************************************************************************************** */}
                <Grid container spacing={1} className="row" sx={{ mt: 2 }}>
                    {/* Label: Date Items Needed */}
                    <Grid size={{ xs: 2 }}>
                        <Typography
                            variant="button"
                            component="label"
                            htmlFor="dateneed"
                            sx={{ whiteSpace: "nowrap" }}
                        >
                            <strong>Date Item(s) Needed</strong>
                        </Typography>
                    </Grid>

                    {/* Date Picker Input */}
                    <Grid size={{ xs: "auto" }} mr={4}>
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
                    </Grid>

                    {/* OR Label */}
                    <Grid size={{ xs: "auto" }}>
                        <strong>OR</strong>
                    </Grid>

                    {/* Quarterly Order Option */}
                    <Grid size={{ xs: "auto" }} mr={4}>
                        <label
                            htmlFor="quarterlyOrder"
                            style={{ fontSize: "0.8rem", whiteSpace: "nowrap" }}
                        >
                            <input
                                id="quarterlyOrder"
                                type="radio"
                                value="quarterlyOrder"
                                {...register("orderType")}
                                style={{ marginRight: "5px" }}
                            />
                            Inclusion w/quarterly office supply order
                        </label>
                    </Grid>

                    {/* OR Label */}
                    <Grid size={{ xs: "auto" }}>
                        <strong>OR</strong>
                    </Grid>

                    {/* No Rush Option */}
                    <Grid size={{ xs: 3 }}>
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
                </Grid>

                {/* Error message for Date Needed validation */}
                <Grid size={{ xs: 12 }}>
                    <p className="error">{errors.dateneed?.message}</p>
                </Grid>
                <hr />

                {/******************************************************************************************* */}
                {/** FILE ATTACHMENTS *********************************************************************** */}
                {/******************************************************************************************* */}
                <Grid container sx={{ mt: 4 }}>
                    {/* Left Side - Label and Description */}
                    <Grid size={{ xs: 3 }}>
                        <Typography
                            variant="button"
                            component="label"
                            htmlFor="fileAttachments"
                        >
                            <strong>Attachments included?</strong>
                        </Typography>
                        <Typography
                            variant="button"
                            component="label"
                            htmlFor="fileAttachments"
                            sx={{ fontSize: "12px", mt: 0.5 }}
                        ></Typography>

                        <Tooltip
                            title="Training information, pictures, web pages, screen shots, etc."
                            arrow
                        >
                            <InfoIcon
                                sx={{
                                    fontSize: "16px",
                                    ml: 1,
                                    verticalAlign: "middle",
                                }}
                            />
                        </Tooltip>
                    </Grid>

                    {/* Right Side - File Upload Component */}
                    <Grid size={{ xs: "auto" }} sx={{ ml: 2 }}>
                        <FileUpload
                            ID={ID}
                            isSubmitted={isSubmitted}
                            fileInfo={fileInfo}
                            setFileInfo={setFileInfo}
                        />
                    </Grid>
                </Grid>

                {/******************************************************************************************* */}
                {/** ITEM DESCRIPTION *********************************************************************** */}
                {/******************************************************************************************* */}
                <Grid container spacing={1} mt={4}>
                    <Grid size={{ xs: 3 }}>
                        <Typography
                            variant="button"
                            component="label"
                            htmlFor="itemDescription"
                        >
                            <strong style={{ fontSize: "0.9rem" }}>
                                Description of Item/Project:
                            </strong>{" "}
                            <Tooltip
                                title="Include details such as qty, color, size, intended recipient, etc. NOTE: If request is for office supplies needed before the next quarterly order, please state the justification."
                                arrow
                            >
                                <InfoIcon
                                    sx={{
                                        fontSize: "16px",
                                        ml: 1,
                                        verticalAlign: "middle",
                                    }}
                                />
                            </Tooltip>
                        </Typography>
                    </Grid>
                    <Grid size={{ xs: 4 }}>
                        <TextField
                            id="itemDescription"
                            multiline
                            rows={4}
                            fullWidth
                            className="form-control"
                            variant="outlined"
                            size="small"
                            {...register("itemDescription", {
                                required: {
                                    value: true,
                                    message: "Item description required.",
                                },
                            })}
                            error={!!errors.itemDescription}
                            helperText={errors.itemDescription?.message}
                            sx={{
                                ml: 2,
                                fontSize: "0.8rem",
                            }}
                        />
                    </Grid>
                </Grid>

                {/******************************************************************************************* */}
                {/** JUSTIFICATION/ADD COMMENTS ************************************************************* */}
                {/******************************************************************************************* */}
                <Justification register={register} errors={errors} />
                <AddComments register={register} errors={errors} />

                {/** FOR LEARNING OR DEV? ****************************************************************** */}
                <Grid container>
                    <LearningDev register={register} />
                </Grid>

                <hr />
                <Grid container spacing={2}>
                    {/* Column for the Select Pickers */}
                    <Grid
                        size={{ xs: 12, sm: 6 }}
                        container
                        direction="column"
                        spacing={2}
                    >
                        <Grid>
                            <BudgetCodePicker
                                onSelectBudgetCode={(budgetObjCode) =>
                                    console.log(budgetObjCode)
                                }
                                control={control}
                                register={register("budgetObjCode")}
                                errors={errors}
                            />
                        </Grid>
                        <Grid>
                            <FundPicker
                                onSelectFund={(fund: string) =>
                                    console.log(fund)
                                }
                                control={control}
                                register={register("fund")}
                                errors={errors}
                            />
                        </Grid>
                        <Grid>
                            <LocationPicker
                                onSelectLocation={(location: string) =>
                                    console.log(location)
                                }
                                control={control}
                                register={register("location")}
                                errors={errors}
                            />
                        </Grid>
                    </Grid>

                    {/* Column for Price and Quantity */}
                    <Grid
                        size={{ xs: 12, sm: 6 }}
                        container
                        direction="column"
                        spacing={2}
                    >
                        <Grid>
                            <PriceInput
                                register={register("price", {
                                    required: "Price is required.",
                                    validate: (value) =>
                                        value >= 0 ||
                                        "Price cannot be less than $0.",
                                })}
                                errors={errors}
                            />
                        </Grid>
                        <Grid>
                            <QuantityInput
                                register={register("quantity", {
                                    required: "Quantity is required.",
                                    validate: (value) =>
                                        value > 0 ||
                                        "Quantity must be greater than 0.",
                                })}
                                errors={errors}
                            />
                        </Grid>
                    </Grid>
                </Grid>

                {/************************************************************************************ */}
                {/* BUTTONS: ADD ITEM, Clear */}
                {/************************************************************************************ */}
                <Grid
                    sx={{
                        display: "flex",
                        justifyContent: "flex-start",
                        mt: 4,
                    }}
                >
                    {/* Capture all data pertaining to the request temporarily to allow for addition of additional items
                      SUBMIT button will handle gathering and sending the data to proper supervisors */}
                    <Buttons
                        className="me-3 btn btn-maroon"
                        disabled={!isValid}
                        label="Add Item"
                        onClick={handleSubmit(handleAddItem)}
                    />
                    <Buttons
                        label="Reset Form"
                        className="btn btn-maroon"
                        onClick={() => reset()}
                    />
                </Grid>
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
}

export default AddItemsForm;