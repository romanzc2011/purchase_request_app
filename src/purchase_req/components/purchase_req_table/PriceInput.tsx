import { UseFormRegister, FieldErrors } from "react-hook-form";
import { PurchaseItem } from "../../schemas/purchaseSchema";
import { TextField, Typography } from "@mui/material";
import Grid from "@mui/material/Grid2";

interface PriceInputProps {
    register: UseFormRegister<PurchaseItem>;
    errors: FieldErrors<PurchaseItem>;
}

const PriceInput = ({ register, errors }: PriceInputProps) => {
    return (
        <Grid container spacing={1} alignItems="center">
            <Grid size={{ xs: 2 }}>
                <Typography
                    variant="button"
                    component="label"
                    htmlFor="price"
                    sx={{ mr: 8, fontWeight: "bold", fontFamily: "Play" }}
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
                    error={!!errors.priceEach}
                    helperText={errors.priceEach?.message}
                    sx={{ backgroundColor: "white", fontFamily: "Play" }}
                    inputProps={{ min: 0, step: "0.01" }}
                    {...register("priceEach", { valueAsNumber: true })}
                />
            </Grid>
        </Grid>
    );
};

export default PriceInput;
