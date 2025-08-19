import { useRef } from "react";
import { Box, CircularProgress, Typography } from "@mui/material";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import Grid from "@mui/material/Grid2";
import CancelIcon from "@mui/icons-material/Cancel";
import FiberManualRecordIcon from "@mui/icons-material/FiberManualRecord";
import { IFile } from "../../types/IFile";
import DeleteIcon from "@mui/icons-material/Delete";
import Button from "@mui/material/Button";
import { computeHTTPURL } from "../../utils/ws";

interface FileUploadProps {
    ID?: string;
    isSubmitted: boolean;
    fileInfo: IFile[];
    setFileInfo: React.Dispatch<React.SetStateAction<IFile[]>>;
}

/************************************************************************************ */
/* FILE UPLOAD
Getting file status from types/IFile.ts */
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

            console.log("File selected - Initial status:", newFile.status);
            setFileInfo((prev) => [...prev, newFile]);
            // Upload file immediately after selection
            uploadFile(newFile);
        }
    }

    /************************************************************************************ */
    /* UPLOAD FILE */
    /************************************************************************************ */
    async function uploadFile(file: IFile) {
        if (!ID) {
            console.error("No ID provided for file upload");
            return;
        }
        console.log("Starting upload - Current file status:", file.status);
        console.log("Current fileInfo state:", fileInfo);

        if (!file.file) {
            console.error("No file provided for upload");
            return;
        }

        // Update file status to uploading
        setFileInfo((prev) => {
            const updated = prev.map((f) =>
                f.name === file.name ? { ...f, status: "uploading" as const } : f
            );
            console.log("Status updated to uploading:", updated);
            return updated;
        });

        try {
            const formData = new FormData();
            formData.append("file", file.file);
            formData.append("ID", ID);

            // Update file status to ready
            setFileInfo((prev) => {
                const updated = prev.map((f) =>
                    f.name === file.name ? { ...f, status: "ready" as const } : f
                );
                console.log("Status updated to ready:", updated);
                return updated;
            });
        } catch (error) {
            console.error("Error uploading file:", error);
            // Update file status to error
            setFileInfo((prev) => {
                const updated = prev.map((f) =>
                    f.name === file.name ? { ...f, status: "error" as const } : f
                );
                console.log("Status updated to error:", updated);
                return updated;
            });
        }
    }

    // Delete file from backend
    async function apiDeleteFile(
        ID: string,
        filename: string
    ): Promise<number> {
        const API_URL = computeHTTPURL("/api/deleteFile");
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
        console.log("Deleting file - Current status:", file.status);
        setFileInfo((prevFiles) => {
            const updated = prevFiles.filter((_, i) => i !== index);
            console.log("File removed from list. Remaining files:", updated);
            return updated;
        });

        // Check if file has been uploaded, if so, delete it, this is if user changes their mind
        if (file.status === "ready") {
            console.log("File was ready, calling apiDeleteFile");
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
                            {file.status === "ready" && (
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
