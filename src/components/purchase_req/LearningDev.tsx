import { UseFormRegister } from "react-hook-form";
import { FormValues } from "../../types/formTypes";
import Grid from "@mui/material/Grid2";
import { Typography, Checkbox, FormControlLabel } from "@mui/material";

interface LearningDevProps {
    register: UseFormRegister<FormValues>;
}

function LearningDev({ register }: LearningDevProps) {
    return (
        <Grid container spacing={2} mt={4}>
            {/* First Column: Learning & Development Option */}
            <Grid size={{ xs: 12, sm: 5 }}>
                <Typography
                    variant="body1"
                    sx={{ fontWeight: "bold", fontSize: "0.9rem" }}
                >
                    If related to Learning &amp; Development:
                </Typography>
                <Typography
                    variant="body2"
                    sx={{ fontSize: "0.8rem", mt: 0.5 }}
                >
                    In accordance with the Guide, Volume12, §1125.10(c),
                    Requester certifies: OR the proposed training is not
                    available from the Federal Judicial Center (FJC) and/or AO
                    websites.
                </Typography>
                <FormControlLabel
                    control={
                        <Checkbox
                        sx={{ color: "white" }}
                            {...register("learnAndDev.trainNotAval")}
                            size="small"
                        />
                    }
                    label="Not Available"
                    sx={{ mt: 1, ml: 1 }}
                />
            </Grid>

            {/* Middle Column: OR */}
            <Grid
                size={{ xs: 12, sm: 1 }}
                sx={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                }}
            >
                <Typography variant="body2" sx={{ fontWeight: "bold" }}>
                    OR
                </Typography>
            </Grid>

            {/* Second Column: Training Needs Option */}
            <Grid size={{ xs: 12, sm: 5 }}>
                <Typography
                    variant="body1"
                    sx={{ fontWeight: "bold", fontSize: "0.9rem" }}
                >
                    Training(s) offered do not meet employee(s)' needs:
                </Typography>
                <Typography
                    variant="body2"
                    sx={{ fontSize: "0.8rem", mt: 0.5 }}
                >
                    Justification is required below or as an attachment.
                </Typography>
                <FormControlLabel
                    control={
                        <Checkbox
                            sx={{ color: "white" }}
                            {...register("learnAndDev.needsNotMeet")}
                            size="small"
                        />
                    }
                    label="Doesn't Meet Needs"
                    sx={{ mt: 1, ml: 1 }}
                />
            </Grid>
        </Grid>
    );
}

export default LearningDev;
