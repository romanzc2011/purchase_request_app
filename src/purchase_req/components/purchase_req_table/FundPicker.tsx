import { UseFormRegister, FieldErrors, Controller } from "react-hook-form";
import { FormValues } from "../../types/formTypes";
import {
    Box,
    FormControl,
    InputLabel,
    MenuItem,
    Select,
    FormHelperText,
} from "@mui/material";

interface FundPickerProps {
    onSelectFund: (fund: string) => void;
    register: ReturnType<UseFormRegister<FormValues>>;
    errors: FieldErrors<FormValues>;
    control: any;
}

const FundPicker = ({
    onSelectFund,
    control,
}: FundPickerProps) => {
    return (
        <Box sx={{
            alignItems: "center",
            gap: 2,
            width: "300px", // reduced width
        }}>
            <Controller
                name="fund"
                control={control}
                render={({ field, fieldState }) => (
                    <FormControl
                        variant="outlined"
                        fullWidth
                        size="small"
                        error={!!fieldState.error}
                        sx={{ backgroundColor: "white" }}
                    >
                        <InputLabel
                            id="fund-label"
                            sx={{ fontWeight: "bold", color: "blue" }}
                        >
                            Fund
                        </InputLabel>
                        <Select
                            labelId="fund-label"
                            label="Fund"
                            {...field}
                            onChange={(e) => {
                                field.onChange(e);
                                onSelectFund(e.target.value as string);
                            }}
                            sx={{
                                "& .MuiSelect-select": {
                                    fontFamily: "Play",
                                    fontWeight: "bold",
                                }
                            }}
                        >
                            <MenuItem value={"51140X"} sx={{ fontFamily: "Play", fontWeight: "bold" }}>51140X</MenuItem>
                            <MenuItem value={"51140E"} sx={{ fontFamily: "Play", fontWeight: "bold" }}>51140E</MenuItem>
                            <MenuItem value={"092000"} sx={{ fontFamily: "Play", fontWeight: "bold" }}>092000</MenuItem>
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

export default FundPicker;
