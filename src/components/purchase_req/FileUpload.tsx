import { useState, useRef, useEffect } from "react";
import { Box, CircularProgress, Typography } from "@mui/material";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import CancelIcon from "@mui/icons-material/Cancel";
import FiberManualRecordIcon from "@mui/icons-material/FiberManualRecord";
import UploadFile from "../../services/UploadHandler";
import { IFile } from "../../types/IFile";
import DeleteIcon from "@mui/icons-material/Delete";
import Button from "@mui/material/Button";

interface FileUploadProps {
    reqID: string;
    fileInfos: IFile[];
    isSubmitted: boolean;
    setFileInfos: React.Dispatch<React.SetStateAction<IFile[]>>;
}

/************************************************************************************ */
/* CONFIG API URL */
/************************************************************************************ */
const baseURL = import.meta.env.VITE_API_URL;
const API_CALL: string = "/api/getApprovalData";
const API_URL = `${baseURL}${API_CALL}`;
const accessToken = localStorage.getItem("access_token");

function FileUpload({ reqID, fileInfos, isSubmitted, setFileInfos }: FileUploadProps) {
    const [currentFile, setCurrentFile] = useState<File | undefined>();

    // Clear file list once form is submitted
    useEffect(() => {
        if(isSubmitted) {
            setFileInfos([]);
        }
    }, [isSubmitted, setFileInfos]);

    // For clearing the file select after delete/upload
    const fileInputRef = useRef<HTMLInputElement>(null);

    function selectFile(event: React.ChangeEvent<HTMLInputElement>): void {
        const files = event.target.files;
        if(files && files.length > 0) {
            const newFile: IFile = {
                file: files[0],
                name: files[0].name,
                status: "idle",
                progress: 0,
            };

            setCurrentFile(files[0]);
            setFileInfos((prev) => [...prev, newFile]);
        };
    }

    // Uploading file
    async function upload() {
        try {
            await Promise.all(
                // Upload idle files
                fileInfos.map(async (fileToUpload) => {
                    if (fileToUpload.status === "idle") {
                        await UploadFile({ file: fileToUpload, reqID, setFileInfos });
                        setCurrentFile(undefined);
                    }
                })
            );
        } catch (error) {
            // Update file to status error if caught error
            setFileInfos((prevFiles) =>
                prevFiles.map((file) => ({ ...file, status: "error" }))
            );
        }
    };

    

    // Delete file from backend
    async function apiDeleteFile(reqID: string, api_url: string, filename: string): Promise<number> {
        const response = await fetch(api_url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${accessToken}`,
            },
            body: JSON.stringify({"reqID": reqID, "filename": filename}),
        });
        
        if(!response.ok) {
          throw new Error(`HTTP error: ${response.status}`);
        } 

        return response.status;
    }
    

    /***************************************************************/
    /* DELETE FILE -- delete from backend if already submitted */
    /***************************************************************/
    function deleteFile({ file, index }: { file: any; index: any; }) {
        setFileInfos((prevFiles) => prevFiles.filter((_, i) => i !== index));
        const delete_api: string = `${API_URL}/api/deleteFile`;
        
        // Check if file has been uploaded, if so, delete it
        if (file.status === "success") {
            let filename: string = file.name;
            apiDeleteFile(reqID, delete_api, filename);
        }

        if (fileInputRef.current) {
            fileInputRef.current.value = "";
        }
    }

    return (
        <Box className="col-sm-4">
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
                <Box className="col-4">
                    <button
                        type="button"
                        className="btn btn-maroon"
                        disabled={!currentFile}
                        onClick={upload}
                    >
                        Upload
                    </button>
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
                    {fileInfos.map((file, index) => (
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
        </Box>
    );
};

export default FileUpload;
