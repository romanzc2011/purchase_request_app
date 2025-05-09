import React from "react";
import { UseFormRegister, FieldErrors } from "react-hook-form";
import { PurchaseItem } from "../../schemas/purchaseSchema";
import Grid from "@mui/material/Grid2";
import { TextField, Typography } from "@mui/material";

interface JustificationProps {
    register: UseFormRegister<PurchaseItem>;
    errors: FieldErrors<PurchaseItem>;
}

const Justification: React.FC<JustificationProps> = ({ register, errors }) => {
    return (
        <Grid container spacing={1} mt={4}>
            <Grid size={{ xs: 3 }}>
                <Typography
                    variant="button"
                    component="label"
                    htmlFor="justification"
                >
                    <strong style={{ fontSize: "0.9rem" }}>
                        Purchase Justification:
                    </strong>{" "}
                </Typography>
            </Grid>
            <Grid size={{ xs: 4 }}>
                <TextField
                    id="justification"
                    multiline
                    rows={4}
                    fullWidth
                    className="form-control"
                    variant="outlined"
                    size="small"
                    {...register("justification")}
                    error={!!errors.justification}
                    helperText={errors.justification?.message}
                    sx={{
                        ml: 2,
                        fontSize: "0.8rem",
                    }}
                />
            </Grid>
        </Grid>
    );
};

export default Justification;
