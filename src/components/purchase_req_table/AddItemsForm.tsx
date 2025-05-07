import { FieldErrors, useForm, FormProvider } from "react-hook-form";
import { DevTool } from "@hookform/devtools";
import React from "react";
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
import InfoIcon from "@mui/icons-material/Info";
import Tooltip from "@mui/material/Tooltip";
import Justification from "./Justification";
import AddComments from "./AddComments";
import { v4 as uuidv4 } from "uuid";
import { useUUIDStore } from "../../services/UUIDService";
import RequesterAutocomplete from "../approval_table/ui/RequesterAutocomplete";
import { usePurchaseForm } from "../../hooks/usePurchaseForm";

/*************************************************************************************** */
/* INTERFACE PROPS */
/*************************************************************************************** */
interface AddItemsProps {
    ID?: string;
    fileInfo: IFile[];
    setDataBuffer: React.Dispatch<React.SetStateAction<FormValues[]>>;
    setIsSubmitted: React.Dispatch<React.SetStateAction<boolean>>;
    setID?: React.Dispatch<React.SetStateAction<string>>;
    setFileInfo: React.Dispatch<React.SetStateAction<IFile[]>>;
}

/*************************************************************************************** */
/* ADD ITEMS FORM */
/*************************************************************************************** */
function AddItemsForm({
    ID,
    setDataBuffer,
    setIsSubmitted,
    setID,
    fileInfo,
    setFileInfo,
}: AddItemsProps) {
    const { setUUID } = useUUIDStore();
    const form = usePurchaseForm();
    const { register, control, handleSubmit, formState, watch, reset, trigger } = form;
    const { errors, isValid, isSubmitted } = formState;

    /*************************************************************************************** */
    /* CREATE NEW ID -- get from backend */
    /*************************************************************************************** */
    async function createNewID() {
        const response = await fetch(
            `${import.meta.env.VITE_API_URL}/api/createNewID`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${localStorage.getItem("access_token")}`,
                },
            }
        );
        if (!response.ok) throw new Error(`HTTP error: ${response.status}`);
        console.log("New ID response", response);
        return response.json();
    }

    /*************************************************************************************** */
    /* HANDLE ADD ITEM function */
    /*************************************************************************************** */
    const handleAddItem = async (data: FormValues) => {
        try {
            // Generate a new UUID for the item
            const uuid = uuidv4();

            // Get a new ID from the backend
            const response = await createNewID();
            const newId = response.ID; // Extract the ID from the response object
            console.log("New ID handleAddItem", newId);

            // If dateneed is null and orderType is set, use today's date
            const dateneed = data.dateneed ? new Date(data.dateneed) : (data.orderType ? new Date(formattedToday) : null);

            // Create a new item with the UUID and ID
            const itemToAdd: FormValues = {
                ...data,
                UUID: uuid,
                priceEach: data.priceEach, // Keep as string to match FormValues type
                ID: newId, // Use the extracted ID
                status: "NEW REQUEST",
                dateneed: dateneed // Use the processed date
            };

            // Store the UUID in the UUID store AFTER we have the ID
            setUUID(newId, uuid);

            console.log("Item to add:", itemToAdd);

            // Add the item to the data buffer
            setDataBuffer(prev => [...prev, itemToAdd]);

            // Reset the form with default values
            reset({
                UUID: "",
                ID: "",
                IRQ1_ID: "",
                requester: "",
                phoneext: "",
                datereq: formattedToday,
                dateneed: null,
                orderType: "",
                itemDescription: "",
                justification: "",
                addComments: "",
                learnAndDev: {
                    trainNotAval: false,
                    needsNotMeet: false
                },
                budgetObjCode: "",
                fund: "",
                priceEach: 0,
                location: "",
                quantity: 0,
            });
        } catch (error) {
            console.error("Error adding item:", error);
        }
    };

    /*************************************************************************************** */
    /* HANDLE ADD ITEM ERRORS function */
    /*************************************************************************************** */
    const onError = (errors: FieldErrors<FormValues>) => {
        console.log("Form errors", errors);
    };

    // This is used to set the default value for the date requested field to today's date
    const today: Date = new Date();
    const isoString: string = today.toISOString();
    const formattedToday: string = isoString.split("T")[0];

    // Trigger validation on mount
    useEffect(() => {
        trigger();
    }, [trigger]);

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
        <Box sx={{
            display: 'flex',
            flexDirection: 'column',
            width: '100%',
            height: '100%',
            overflow: 'auto'
        }}>
            <FormProvider {...form}>
                <form
                    onSubmit={handleSubmit(handleAddItem, onError)}
                    style={{
                        width: '100%',
                        height: '100%',
                        overflow: 'auto'
                    }}
                >
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
                            <RequesterAutocomplete
                                name="requester"
                                label=""
                                freeSolo
                                rules={{ required: "Name of requester is required" }}
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
                                error={!!errors.phoneext}
                                helperText={errors.phoneext?.message}
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
                                disabled={true}
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
                                    validate: (value) => {
                                        const orderType = watch("orderType");
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
                                    {...register("orderType", {
                                        onChange: () => {
                                            trigger("dateneed");
                                        }
                                    })}
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
                                    {...register("orderType", {
                                        onChange: () => {
                                            trigger("dateneed");
                                        }
                                    })}
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
                        <LearningDev control={control} />
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
                                    register={register("budgetObjCode", {
                                        required: "Budget code is required.",
                                    })}
                                    errors={errors}

                                />
                            </Grid>
                            <Grid>
                                <FundPicker
                                    onSelectFund={(fund: string) =>
                                        console.log(fund)
                                    }
                                    control={control}
                                    register={register("fund", {
                                        required: "Fund is required.",
                                    })}
                                    errors={errors}
                                />
                            </Grid>
                            <Grid>
                                <LocationPicker
                                    onSelectLocation={(location: string) =>
                                        console.log(location)
                                    }
                                    control={control}
                                    register={register("location", {
                                        required: "Location is required.",
                                    })}
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
                                    register={register("priceEach", {
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
            </FormProvider>
        </Box>
    );
}

export default AddItemsForm;