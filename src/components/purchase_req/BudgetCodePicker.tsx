import React from "react";
import { UseFormRegister, FieldErrors, Controller } from "react-hook-form";
import { FormValues } from "../../types/formTypes";
import {
    Box,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    FormHelperText,
} from "@mui/material";

interface BudgetPickerProps {
    onSelectBudgetCode: (budgetObjCode: string) => void;
    register: ReturnType<UseFormRegister<FormValues>>;
    errors: FieldErrors<FormValues>;
    control: any; // Consider typing this as Control<FormValues> if desired
}

const BudgetCodePicker = ({
    onSelectBudgetCode,
    register,
    errors,
    control,
}: BudgetPickerProps) => {
    return (
        <Box
            sx={{
                display: "flex",
                alignItems: "center",
                gap: 2,
                width: "400px", // reduced width
            }}
        >
            <Controller
                name="budgetObjCode"
                control={control}
                defaultValue="3101 - General Office Equipment"
                render={({ field, fieldState }) => (
                    <FormControl
                        fullWidth
                        variant="outlined"
                        size="small"
                        error={!!fieldState.error}
                        sx={{ backgroundColor: "white" }}
                    >
                        <InputLabel
                            id="budgetObjCode-label"
                            sx={{ 
                              fontWeight: "bold", 
                              color: "maroon",
                              "&.Mui-focused": {
                                color: "maroon",
                              },
                              "&.MuiInputLabel-shrink" : {
                                color: "maroon",
                                fontWeight: "bold",
                              }
                            }}
                        >
                            Budget Object Code (BOC)
                        </InputLabel>
                        <Select
                            labelId="budgetObjCode-label"
                            label="Budget Object Code (BOC)"
                            {...field}
                            onChange={(e) => {
                                field.onChange(e);
                                onSelectBudgetCode(e.target.value as string);
                            }}
                        >
                            <MenuItem value={"3101 - General Office Equipment"}>
                                3101 - General Office Equipment
                            </MenuItem>
                            <MenuItem
                                value={"3107 - Audio Recording Equipment"}
                            >
                                3107 - Audio Recording Equipment
                            </MenuItem>
                            <MenuItem value={"3111 - Furniture and Fixtures"}>
                                3111 - Furniture and Fixtures
                            </MenuItem>
                            <MenuItem value={"3113 - Mailing Equipment"}>
                                3113 - Mailing Equipment
                            </MenuItem>
                            <MenuItem
                                value={
                                    "3121 - Legal Resources - New Print and Digital Purchases"
                                }
                            >
                                3121 - Legal Resources - New Print and Digital
                                Purchases
                            </MenuItem>
                            <MenuItem
                                value={
                                    "3122 - Legal Resources - Print and Digital Continuations"
                                }
                            >
                                3122 - Legal Resources - Print and Digital
                                Continuations
                            </MenuItem>
                            <MenuItem
                                value={"3130 - Law Enforcement Equipment"}
                            >
                                3130 - Law Enforcement Equipment
                            </MenuItem>
                        </Select>
                        {fieldState.error && (
                            <FormHelperText>
                                {fieldState.error.message}
                            </FormHelperText>
                        )}
                    </FormControl>
                )}
            />
        </Box>
    );
};

export default BudgetCodePicker;
