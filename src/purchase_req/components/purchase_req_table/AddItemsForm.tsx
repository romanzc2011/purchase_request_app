import { FieldErrors, FormProvider } from "react-hook-form";
import { DevTool } from "@hookform/devtools";
import React, { useState } from "react";
import "./LearningDev";
import { Box, Snackbar, Alert } from "@mui/material";
import Buttons from "./Buttons";
import ContractingOfficerDropdown from "./ContractingOfficerDropdown";
import BudgetCodePicker from "./BudgetCodePicker";
import { useEffect } from "react";
import { TextField, Typography } from "@mui/material";
import Grid from "@mui/material/Grid2";
import LocationPicker from "./LocationPicker";
import { PurchaseItem, OrderType } from "../../schemas/purchaseSchema";
import FileUpload from "./FileUpload";
import FundPicker from "./FundPicker";
import PriceInput from "./PriceInput";
import QuantityInput from "./QuantityInput";
import { IFile } from "../../types/IFile";
import { defaultItemFields, FormValues } from "../../types/formTypes";
import InfoIcon from "@mui/icons-material/Info";
import Tooltip from "@mui/material/Tooltip";
import Justification from "./Justification";
import { v4 as uuidv4 } from "uuid";
import { useUUIDStore } from "../../services/UUIDService";
import RequesterAutocomplete from "../approval_table/ui/RequesterAutocomplete";
import { usePurchaseForm } from "../../hooks/usePurchaseForm";
import { toast } from "react-toastify";
import { isSubmittedSig } from "../../utils/PrasSignals";
import { signal } from "@preact/signals-react";

// Create a local test signal
const localTestSig = signal<boolean>(false);

/*************************************************************************************** */
/* INTERFACE PROPS */
/*************************************************************************************** */
interface AddItemsProps {
    ID?: string;
    fileInfo: IFile[];
    setDataBuffer: React.Dispatch<React.SetStateAction<FormValues[]>>;
    setID?: React.Dispatch<React.SetStateAction<string>>;
    setFileInfo: React.Dispatch<React.SetStateAction<IFile[]>>;
}

/*************************************************************************************** */
/* ADD ITEMS FORM */
/*************************************************************************************** */
function AddItemsForm({
    ID,
    setDataBuffer,
    fileInfo,
    setFileInfo,
}: AddItemsProps) {
    const { setUUID } = useUUIDStore();
    const form = usePurchaseForm();
    const {
        register,
        control,
        handleSubmit,
        formState,
        watch,
        reset,
        trigger,
        handleAssignCO,
    } = form;
    const { errors, isValid, isSubmitted } = formState;
    const [showSuccess, setShowSuccess] = useState(false);
    const [selectedCO, setSelectedCO] = useState<number | "">("");

    // #############################################################################
    // DEBUG
    // #############################################################################
    // Debug form state
    useEffect(() => {
        console.log('Form State:', {
            isValid,
            errors,
            values: watch(),
            formState: formState
        });
    }, [isValid, errors, watch, formState]);

    useEffect(() => {
        const subscription = watch((value, { name, type }) => {
            console.log("📋 Watched Change:", { name, type, value });
            console.log("🧪 Form State:", formState);
        });
        return () => subscription.unsubscribe();
    }, [watch, formState]);
    // #############################################################################
    // #############################################################################
    // #############################################################################

    // Debug success state
    useEffect(() => {
        console.log('Success state changed:', showSuccess);
    }, [showSuccess]);

    // Keep these header values between add items
    const [requester, phoneext, datereq, dateneed, orderType] = watch([
        "requester",
        "phoneext",
        "datereq",
        "dateneed",
        "orderType"
    ]);

    useEffect(() => {
        const subscription = watch((value, { name, type }) => {
            console.log("📋 Watched Change:", { name, type, value });
            console.log("🧪 Form State:", formState);
        });
        return () => subscription.unsubscribe()
    }, [watch, formState]);

    /*************************************************************************************** */
    /* HANDLE ADD ITEM function */
    /*************************************************************************************** */
    const handleAddItem = async (data: PurchaseItem) => {
        try {
            // Generate a new UUID for the item
            const uuid = uuidv4();

            // Create a new item with the UUID and ID, converting to FormValues
            const itemToAdd: FormValues = {
                ...data,
                UUID: uuid,
                ID: ID || "",
                IRQ1_ID: data.IRQ1_ID || "",
                orderType: data.orderType || "",
                priceEach: data.priceEach,
                status: "NEW REQUEST" as any,
                dateneed: data.dateneed === "" ? "" : (data.dateneed || ""),
                trainNotAval: data.trainNotAval || false,
                needsNotMeet: data.needsNotMeet || false,
                totalPrice: data.totalPrice || (data.priceEach * data.quantity),
                fileAttachments: data.fileAttachments?.map(f => ({
                    attachment: f.attachment || null,
                    name: f.name,
                    type: f.type,
                    size: f.size
                })) || []
            };

            // Store the UUID in the UUID store AFTER we have the ID
            if (ID) {
                setUUID(ID, uuid);
            }

            // Add the item to the data buffer
            setDataBuffer(prev => [...prev, itemToAdd]);

            // Show success message
            setShowSuccess(true);

            // Reset the form on AddItems, keep header data, but not item data
            // Only reset to keep header data if not final submitted

            if (!isSubmittedSig.value) {
                reset({
                    requester,
                    phoneext,
                    datereq,
                    dateneed,
                    orderType,
                    ...defaultItemFields
                }, {
                    keepErrors: false,
                    keepDirty: false,
                    keepTouched: false,
                    keepIsSubmitted: false,
                });
                // Re-run validation 
                await trigger();
            }

        } catch (error) {
            console.error("Error adding item:", error);
        }
    };

    /*************************************************************************************** */
    /* HANDLE ADD ITEM ERRORS function */
    /*************************************************************************************** */
    const onError = (errors: FieldErrors<PurchaseItem>) => {
        console.log("Form errors", errors);
    };

    // This is used to set the default value for the date requested field to today's date
    const today: Date = new Date();
    const isoString: string = today.toISOString();
    const formattedToday: string = isoString.split("T")[0];

    /* The form has successfully been submitted to the backend so we need to reset the form for everything */
    // Watch for isFinalSubmitted changes and reset form accordingly
    useEffect(() => {
        const shouldReset = isSubmittedSig.value;
        console.log("📋 useEffect running, isSubmittedSig.value:", shouldReset);

        if (shouldReset) {
            console.log("📋 Form submitted - resetting form");

            // Clear form state completely
            reset({
                requester: "",
                phoneext: "",
                datereq: formattedToday,
                dateneed: null,
                orderType: OrderType.STANDARD,
                ...defaultItemFields
            }, {
                keepErrors: false,
                keepDirty: false,
                keepIsSubmitted: false,
                keepTouched: false
            });

            // Define an async function inside useEffect for run trigger
            async function runValidation() {
                const result = await trigger(); // Re-validate whole form
                console.log("📋 Trigger result:", result);
                console.log("📋 Validation errors after trigger:", formState.errors);
            };

            // Call validation
            runValidation();

            // Reset the signal after the form is reset
            isSubmittedSig.value = false;
            console.log("📋 Signal reset to false");

        }
    }, [isSubmittedSig.value, reset, trigger, formattedToday]);

    /*************************************************************************************** */
    /* Form submission function */
    /*************************************************************************************** */
    useEffect(() => {
        const subscription = watch((value) => {
            console.log(value);
        });
        return () => subscription.unsubscribe();
    }, [watch]);

    // Trigger validation on mount to show initial errors
    useEffect(() => {
        // Small delay to ensure form is fully initialized
        const timer = setTimeout(() => {
            trigger();
        }, 100);
        return () => clearTimeout(timer);
    }, [trigger]);

    // When formstat isValid the reset zod

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
                                {...register("phoneext")}
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
                                {...register("datereq")}
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
                                {...register("dateneed")}
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
                                    value="QUARTERLY_ORDER"
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
                                    value="NO_RUSH"
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
                    {/* CONTRACTING OFFICER DROPDOWN */}
                    <ContractingOfficerDropdown
                        value={selectedCO}
                        requestID={ID}
                        onChange={setSelectedCO}
                        onClickOK={async (ID, officerId, username) => {
                            if (!ID) {
                                console.error("❌ No request ID available to assign CO");
                                toast.error("No request ID available to assign CO");
                                return;
                            }
                            try {
                                await handleAssignCO(ID, officerId, username);
                            } catch (error) {
                                console.error("❌ Error assigning CO:", error);
                                toast.error("Failed to assign CO");
                            }
                        }}
                    />
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
                                {...register("itemDescription")}
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
                                {/* ****************************************************** */}
                                {/* Fund Picker */}
                                {/* ****************************************************** */}
                                <FundPicker
                                    onSelectFund={(fund: string) =>
                                        console.log(fund)
                                    }
                                    control={control}
                                    register={register("fund")}
                                    errors={errors}
                                />
                            </Grid>

                            {/* ****************************************************** */}
                            {/* Budget Code Picker */}
                            {/* ****************************************************** */}
                            <Grid>
                                <BudgetCodePicker
                                    onSelectBudgetCode={(budgetObjCode, fund: string) =>
                                        console.log(budgetObjCode, fund)
                                    }
                                    control={control}
                                    register={register("budgetObjCode")}
                                    errors={errors}
                                    fund={watch("fund") || ""}
                                />
                            </Grid>
                            {/* ****************************************************** */}
                            {/* Location Picker */}
                            {/* ****************************************************** */}
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
                            {/* ****************************************************** */}
                            {/* Price Input */}
                            {/* ****************************************************** */}
                            <Grid>
                                <PriceInput
                                    register={register}
                                    errors={errors}
                                />
                            </Grid>

                            {/* ****************************************************** */}
                            {/* Quantity Input */}
                            {/* ****************************************************** */}
                            <Grid>
                                <QuantityInput
                                    register={register}
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
                            label="Add Item"
                            onClick={handleSubmit(handleAddItem, onError)}
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
            </FormProvider>
            <Snackbar
                open={showSuccess}
                autoHideDuration={3000}
                onClose={() => setShowSuccess(false)}
                anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
            >
                <Alert onClose={() => setShowSuccess(false)} severity="success" sx={{ width: '100%' }}>
                    Item successfully added!
                </Alert>
            </Snackbar>
            <DevTool control={control} />
        </Box>
    );
}

export default AddItemsForm;