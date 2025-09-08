import { UseFormRegister, FieldErrors, Controller } from "react-hook-form";
import { FormValues } from "../../types/formTypes";
import { getBOCOptions } from "../../utils/bocUtils";
import {
    Box,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    ListSubheader,
    FormHelperText,
    Typography,
} from "@mui/material";

interface BudgetPickerProps {
    onSelectBudgetCode: (budgetObjCode: string, fund: string) => void;
    register: ReturnType<UseFormRegister<FormValues>>;
    errors: FieldErrors<FormValues>;
    control: any; // Consider typing this as Control<FormValues> if desired
    fund: string;
}

const BudgetCodePicker = ({
    onSelectBudgetCode,
    control,
    fund,
}: BudgetPickerProps) => {
    return (
        <Box
            sx={{
                alignItems: "center",
                gap: 2,
                width: "300px", // reduced width
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
                        sx={{
                            backgroundColor: "white",
                            fontWeight: "bold",
                            color: "blue",
                            "&.Mui-focused": {
                                color: "blue",
                            },
                            "&.MuiInputLabel-shrink": {
                                color: "blue",
                                fontWeight: "bold",
                            },
                        }}
                    >
                        <InputLabel
                            id="budgetObjCode-label"
                            sx={{
                                fontWeight: "bold",
                                color: "blue",
                                "&.Mui-focused": {
                                    color: "blue",
                                },
                                "&.MuiInputLabel-shrink": {
                                    color: "blue",
                                    fontWeight: "bold",
                                },
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
                                onSelectBudgetCode(e.target.value as string, fund);
                            }}
                        >
                            {getBOCOptions(fund)?.map((option) => {
                                if (option.disabled) {
                                    return (
                                        <ListSubheader
                                            key={option.value}
                                            disableSticky
                                            sx={{
                                                fontFamily: "Tahoma",
                                                fontWeight: "bold", color: "blue"
                                            }}
                                        >
                                            {option.label}
                                        </ListSubheader>
                                    );
                                }
                                const [code, ...rest] = option.label.split(" - ");
                                const description = rest.join(" - ");
                                return (
                                    <MenuItem key={option.value} value={option.value}>
                                        <Typography component="span" fontWeight="bold">
                                            {code}
                                        </Typography>
                                        {description && (
                                            <Typography component="span">
                                                {" - "}
                                                {description}
                                            </Typography>
                                        )}
                                    </MenuItem>
                                );
                            }) || []}
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
