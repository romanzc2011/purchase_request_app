import { useRef } from "react";
import { Box, CircularProgress, Typography } from "@mui/material";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import Grid from "@mui/material/Grid2";
import CancelIcon from "@mui/icons-material/Cancel";
import FiberManualRecordIcon from "@mui/icons-material/FiberManualRecord";
import { IFile } from "../../types/IFile";
import DeleteIcon from "@mui/icons-material/Delete";
import Button from "@mui/material/Button";

interface FileUploadProps {
    ID?: string;
    isSubmitted: boolean;
    fileInfo: IFile[];
    setFileInfo: React.Dispatch<React.SetStateAction<IFile[]>>;
}

/************************************************************************************ */
/* FILE UPLOAD */
/************************************************************************************ */
function FileUpload({ ID, fileInfo, setFileInfo }: FileUploadProps) {
    const fileInputRef = useRef<HTMLInputElement>(null);

    /************************************************************************************ */
    /* SELECT FILE */
    /************************************************************************************ */
    function selectFile(event: React.ChangeEvent<HTMLInputElement>): void {
        const files = event.target.files;
        if (files && files.length > 0) {
            const newFile: IFile = {
                file: files[0],
                name: files[0].name,
                status: "idle",
                progress: 0,
            };

            setFileInfo((prev) => [...prev, newFile]);
        }
    }

    // Delete file from backend
    async function apiDeleteFile(
        ID: string,
        filename: string
    ): Promise<number> {
        const API_URL = `${import.meta.env.VITE_API_URL}/api/deleteFile`;
        const accessToken = localStorage.getItem("access_token");
        const response = await fetch(API_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${accessToken}`,
            },
            body: JSON.stringify({ ID: ID, filename: filename }),
        });

        if (!response.ok) {
            throw new Error(`HTTP error: ${response.status}`);
        }
        return response.status;
    }

    /***************************************************************/
    /* DELETE FILE -- (only deletes files in frontend list) */
    /***************************************************************/
    function deleteFile({ file, index }: { file: IFile; index: number }) {
        setFileInfo((prevFiles) => prevFiles.filter((_, i) => i !== index));

        // Check if file has been uploaded, if so, delete it, this is if user changes their mind
        if (file.status === "success") {
            apiDeleteFile(ID || "", file.name).catch((error) =>
                console.error("Error deleting file: ", error)
            );
        }

        if (fileInputRef.current) {
            fileInputRef.current.value = "";
        }
    }

    return (
        <Grid>
            <Box className="row">
                <Box className="col-8">
                    <label className="btn btn-default p-0">
                        <input
                            type="file"
                            ref={fileInputRef}
                            onChange={selectFile}
                        />
                    </label>
                </Box>
            </Box>

            <Box
                className="card mt-3"
                sx={{
                    background: "linear-gradient(to bottom, #2c2c2c, #800000)",
                }}
            >
                <Box
                    className="card-header"
                    sx={{ color: "white", backgroundColor: "#242424" }}
                >
                    List of Files
                </Box>
                <ul className="list-group list-group-flush">
                    {fileInfo.map((file, index) => (
                        <li className="list-group-item" key={index}>
                            <Typography
                                noWrap
                                sx={{
                                    maxWidth: "150px",
                                    display: "inline-block",
                                    verticalAlign: "middle",
                                }}
                            >
                                {file.name}
                            </Typography>
                            {/* STATUS ICONS */}
                            {file.status === "idle" && (
                                <FiberManualRecordIcon
                                    sx={{
                                        color: "gold",
                                        fontSize: 16,
                                        marginLeft: 1,
                                    }}
                                />
                            )}
                            {file.status === "uploading" && (
                                <CircularProgress
                                    size={15}
                                    color="primary"
                                    thickness={5}
                                />
                            )}
                            {file.status === "success" && (
                                <CheckCircleIcon
                                    sx={{ color: "green", fontSize: 16 }}
                                />
                            )}
                            {file.status === "error" && (
                                <CancelIcon
                                    sx={{ color: "red", fontSize: 16 }}
                                />
                            )}
                            <Button
                                onClick={() => deleteFile({ file, index })}
                                size="small"
                                sx={{
                                    background: "maroon",
                                    marginLeft: "30px",
                                }}
                                variant="contained"
                                startIcon={<DeleteIcon />}
                            >
                                Delete
                            </Button>
                        </li>
                    ))}
                </ul>
            </Box>
        </Grid>
    );
}

export default FileUpload;
