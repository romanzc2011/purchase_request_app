import { UseFormRegister, Controller, Control } from "react-hook-form";
import { PurchaseItem } from "../../schemas/purchaseSchema";
import Grid from "@mui/material/Grid2";
import { Typography, Checkbox, FormControlLabel } from "@mui/material";

interface LearningDevProps {
    control: Control<PurchaseItem>;
}

export default function LearningDev({ control }: LearningDevProps) {
    return (
        <Grid container spacing={2} mt={4}>
            {/* First Column */}
            <Grid size={{ xs: 12, sm: 5 }}>
                <Typography variant="body1" sx={{ fontWeight: "bold", fontSize: "0.9rem" }}>
                    If related to Learning &amp; Development:
                </Typography>
                <Typography variant="body2" sx={{ fontSize: "0.8rem", mt: 0.5 }}>
                    In accordance with the Guide, Volume12, §1125.10(c),
                    Requester certifies: OR the proposed training is not
                    available from the Federal Judicial Center (FJC) and/or AO
                    websites.
                </Typography>
                <Controller
                    name="learnAndDev.trainNotAval"
                    control={control}
                    defaultValue={false}
                    render={({ field }) => (
                        <FormControlLabel
                            control={
                                <Checkbox
                                    {...field}
                                    checked={field.value}
                                    size="small"
                                    sx={{ color: "white" }}
                                />
                            }
                            label="Not Available"
                            sx={{ mt: 1, ml: 1 }}
                        />
                    )}
                />
            </Grid>

            {/* OR */}
            <Grid
                size={{ xs: 12, sm: 1 }}
                sx={{ display: "flex", alignItems: "center", justifyContent: "center" }}
            >
                <Typography variant="body2" sx={{ fontWeight: "bold" }}>
                    OR
                </Typography>
            </Grid>

            {/* Second Column */}
            <Grid size={{ xs: 12, sm: 5 }}>
                <Typography variant="body1" sx={{ fontWeight: "bold", fontSize: "0.9rem" }}>
                    Training(s) offered do not meet employee(s)' needs:
                </Typography>
                <Typography variant="body2" sx={{ fontSize: "0.8rem", mt: 0.5 }}>
                    Justification is required or as an attachment.
                </Typography>
                <Controller
                    name="learnAndDev.needsNotMeet"
                    control={control}
                    defaultValue={false}
                    render={({ field }) => (
                        <FormControlLabel
                            control={
                                <Checkbox
                                    {...field}
                                    checked={field.value}
                                    size="small"
                                    sx={{ color: "white" }}
                                />
                            }
                            label="Doesn't Meet Needs"
                            sx={{ mt: 1, ml: 1 }}
                        />
                    )}
                />
            </Grid>
        </Grid>
    );
}