import React from "react";
import { UseFormRegister, FieldErrors } from "react-hook-form";
import { FormValues } from "../../types/formTypes";
import Grid from "@mui/material/Grid2";
import { TextField, Typography } from "@mui/material";

interface AddCommentsProps {
    register: UseFormRegister<FormValues>;
    errors: FieldErrors<FormValues>;
}

const Justification: React.FC<AddCommentsProps> = ({ register, errors }) => {
    return (
        <Grid container spacing={1} mt={4}>
            <Grid size={{ xs: 3 }}>
                <Typography
                    variant="button"
                    component="label"
                    htmlFor="addComments"
                >
                    <strong style={{ fontSize: "0.9rem" }}>
                        Addition Comments/Instructions:
                    </strong>{" "}
                  
                </Typography>
            </Grid>
            <Grid size={{ xs: 4 }}>
                <TextField
                    id="addComments"
                    multiline
                    rows={4}
                    fullWidth
                    className="form-control"
                    variant="outlined"
                    size="small"
                    {...register("addComments")}
                    error={!!errors.addComments}
                    helperText={errors.addComments?.message}
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
