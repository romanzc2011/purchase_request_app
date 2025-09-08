import { Controller } from "react-hook-form";
import { UseFormRegister, FieldErrors } from "react-hook-form";
import { FormValues, locations } from "../../types/formTypes";
import { Box, MenuItem, FormControl, InputLabel, Select, FormHelperText } from "@mui/material";

interface LocationProps {
    onSelectLocation: (location: string) => void;
    register: ReturnType<UseFormRegister<FormValues>>;
    errors: FieldErrors<FormValues>;
    control: any;
}

const LocationFilter = ({
    onSelectLocation,
    control,
}: LocationProps) => {
    return (
        <Box
            sx={{
                alignItems: "center",
                gap: 2,
                width: "300px", // reduced width
            }}
        >
            <Controller
                name="location"
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
                            id="location-label"
                            sx={{ fontWeight: "bold", color: "blue" }}
                        >
                            Location
                        </InputLabel>
                        <Select
                            labelId="location-label"
                            label="Location"
                            {...field}
                            onChange={(e) => {
                                field.onChange(e);
                                onSelectLocation(e.target.value as string);
                            }}
                            sx={{
                                "& .MuiSelect-select": {
                                    fontFamily: "Tahoma",
                                    fontWeight: "bold",
                                }
                            }}
                        >
                            {locations.map((option, index) => (
                                <MenuItem key={index} value={option} sx={{ fontFamily: "Tahoma", fontWeight: "bold" }}>
                                    {option}
                                </MenuItem>
                            ))}
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

export default LocationFilter;
