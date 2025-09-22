import { Controller } from "react-hook-form";
import { UseFormRegister, FieldErrors } from "react-hook-form";
import { FormValues, locations } from "../../types/formTypes";
import { Box, MenuItem, FormControl, InputLabel, Select, FormHelperText } from "@mui/material";
import { GridRenderCellParams } from "@mui/x-data-grid";

interface LocationProps {
    onSelectLocation: (location: string) => void;
    register: ReturnType<UseFormRegister<FormValues>>;
    errors: FieldErrors<FormValues>;
    control: any;
}

interface LocationEditProps {
    onSelectLocation: (location: string) => void;
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

export const LocationEditCell = (params: GridRenderCellParams) => {
    return (
        <Select
            value={params.value}
            onChange={(e) => params.api.setEditCellValue({
                id: params.id,
                field: params.field,
                value: e.target.value
            })}
            size="small"
            variant="standard"
            sx={{ width: "100%" }}
        >
            {locations.map((location, index) => (
                <MenuItem key={index} value={location} sx={{ fontFamily: "Tahoma", fontWeight: "bold" }}>
                    {location}
                </MenuItem>
            ))}
        </Select>
    )
}

export default LocationFilter;
