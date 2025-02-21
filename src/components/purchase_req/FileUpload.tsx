import { useState } from "react";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import CancelIcon from "@mui/icons-material/Cancel";
import FiberManualRecordIcon from "@mui/icons-material/FiberManualRecord";
import { Box, CircularProgress } from "@mui/material";
import UploadService from "../../services/FileUploadService";
import { IFile } from "../../types/File";

interface FileUploadProps {
  reqID: string;
  setFileInfos: React.Dispatch<React.SetStateAction<IFile[]>>;
}
const message = "";

const FileUpload: React.FC<FileUploadProps> = ({ reqID, setFileInfos }) => {
    const [currentFile, setCurrentFile] = useState<File>();

    const selectFile = (event: React.ChangeEvent<HTMLInputElement>) => {
        const { files } = event.target;

        if(files && files.length > 0) {
          const newFile: IFile = {
            file: files[0],
            name: files[0].name,
            status: "idle",
            progress: 0
          };

          setCurrentFile(files[0]);

          // Add selected files to list, start with red X before upload, check circle during, and green check on success
          setFileInfos((prev) => [...prev, newFile]);
        }
    }

    const upload = () => {
        if(!currentFile) return;

        // Update status for the file being uploaded
        setFileInfos((prev) =>
          prev.map((file) =>
            file.name === currentFile.name
              ? { ...file, status: "uploading" }
              : file
          )  
        );

        UploadService.upload(currentFile, reqID, (event: any) => {
            setProgress(Math.round((100 * event.loaded) / event.total));
        })
        /* Once uploaded get response status, if 200 then upload was successful, update the file status to 'success'  */
        .then((response) => {
          if (response.status === 200) {
              setFileInfos((prev) =>
                  prev.map((file) =>
                      file.name === currentFile.name
                          ? { ...file, status: "success" } // ✅ Update only the uploaded file
                          : file
                    )
                );
            } else {
                throw new Error("Upload failed");
            }
        })
        .catch(() => {
            setFileInfos((prev) =>
                prev.map((file) =>
                    file.name === currentFile.name
                      ? { ...file, status: "error" }
                      : file
                )
            );
        });
    };

    return (
      <Box className="col-sm-4">
          <Box className="row">
            <Box className="col-8">
              <label className="btn btn-default p-0">
                <input type="file" onChange={selectFile} />
                
              </label>
            </Box>
    
            <Box className="col-4">
              <button
                className="btn btn-maroon"
                disabled={!currentFile}
                onClick={upload}
              >
                Upload
              </button>
            </Box>
          </Box>
    
          {currentFile && (
            <Box className="progress my-3">
              <Box
                className="progress-bar progress-bar-info"
                role="progressbar"
                aria-valuenow={progress}
                aria-valuemin={0}
                aria-valuemax={100}
                style={{ width: progress + "%" }}
              >
                {progress}%
              </Box>
            </Box>
          )}
    
          {message && (
            <Box className="alert alert-secondary mt-3" role="alert">
              {message}
            </Box>
          )}
    
          <Box className="card mt-3">
            <Box className="card-header">List of Files</Box>
            <ul className="list-group list-group-flush">
              {fileInfos &&
                fileInfos.map((file, index) => (
                  <li className="list-group-item" key={index}>
                    {file.name}

                    {/* STATUS ICONS */}
                    {file.status === "idle" && <FiberManualRecordIcon sx={{ color: "gold", fontSize: 16, marginLeft: 1 }} />}
                    {file.status === "uploading" && <CircularProgress size={15} color="primary" thickness={5} />}
                    {file.status === "success" && <CheckCircleIcon sx={{ color: "green", fontSize: 16 }} />}
                    {file.status === "error" && <CancelIcon sx={{ color: "red", fontSize: 16 }} />}
                  </li>
                ))}
            </ul>
          </Box>
        </Box>
      );
    };

    export default FileUpload;