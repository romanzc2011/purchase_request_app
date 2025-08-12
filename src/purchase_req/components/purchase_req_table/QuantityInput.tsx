import { UseFormRegister, FieldErrors } from "react-hook-form";
import { PurchaseItem } from "../../schemas/purchaseSchema";
import { TextField, Typography } from "@mui/material";
import Grid from "@mui/material/Grid2";

interface QuantityInputProps {
    register: UseFormRegister<PurchaseItem>;
    errors: FieldErrors<PurchaseItem>;
}

const QuantityInput = ({ register, errors }: QuantityInputProps) => {
    return (
        <Grid container spacing={1} alignItems="center">
            <Grid size={{ xs: 2 }}>
                <Typography
                    variant="button"
                    component="label"
                    htmlFor="quantity"
                    sx={{ mr: 4, fontWeight: "bold", fontFamily: "Play" }}
                >
                    quantity:
                </Typography>
            </Grid>
            <Grid size={{ xs: 6, sm: 3 }}>
                <TextField
                    id="quantity"
                    size="small"
                    type="number"
                    className="form-control"
                    variant="outlined"
                    placeholder="Enter quantity"
                    error={!!errors.quantity}
                    helperText={errors.quantity?.message}
                    sx={{ backgroundColor: "white", fontFamily: "Play" }}
                    inputProps={{ min: 1 }}
                    {...register("quantity", { valueAsNumber: true })}
                />
            </Grid>
        </Grid>
    );
};

export default QuantityInput;
