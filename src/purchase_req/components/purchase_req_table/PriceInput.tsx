import { UseFormRegister, FieldErrors } from "react-hook-form";
import { FormValues } from "../../types/formTypes";
import { TextField, Typography } from "@mui/material";
import Grid from "@mui/material/Grid2";

interface PriceInputProps {
    register: ReturnType<UseFormRegister<FormValues>>;
    errors: FieldErrors<FormValues>;
}

const PriceInput = ({ register, errors }: PriceInputProps) => {
    return (
        <Grid container spacing={1} alignItems="center">
            <Grid size={{ xs: 2 }}>
                <Typography
                    variant="button"
                    component="label"
                    htmlFor="price"
                    sx={{ mr: 8, fontWeight: "bold" }}
                >
                    Price:
                </Typography>
            </Grid>
            <Grid size={{ xs: 6, sm: 3 }}>
                <TextField
                    id="price"
                    className="form-control"
                    size="small"
                    type="number"
                    variant="outlined"
                    placeholder="Enter Price"
                    error={!!errors.price}
                    helperText={errors.price?.message}
                    sx={{ backgroundColor: "white" }}
                    {...register}
                />
            </Grid>
        </Grid>
    );
};

export default PriceInput;
