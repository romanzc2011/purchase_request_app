import { Typography } from "@mui/material";
import LinearProgress from "@mui/material/LinearProgress";

export function ProgressToast({ percent, message }: { percent: number, message: string }) {
    return (
        <div style={{ width: "100%" }}>
            <Typography variant="body2">
                {`${message}… (${percent}%)`}
            </Typography>
            <LinearProgress
                variant="determinate"
                value={percent}
                sx={{
                    color: "maroon",
                    height: 10,
                    borderRadius: 0,
                    marginTop: 1,

                    "& .MuiLinearProgress-bar": {
                        backgroundColor: "maroon",
                        transition: "width 1s ease"
                    },
                }}
            />
        </div>
    );
}