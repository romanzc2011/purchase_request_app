import { useState } from "react";
import { Box, CircularProgress } from "@mui/material";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import CancelIcon from "@mui/icons-material/Cancel";
import FiberManualRecordIcon from "@mui/icons-material/FiberManualRecord";
import { uploadFile } from "../../services/FileUploadHandler"; 
import { IFile } from "../../types/IFile";

interface FileUploadProps {
  reqID: string;
  fileInfos: IFile[];
  setFileInfos: React.Dispatch<React.SetStateAction<IFile[]>>;
}

const FileUpload: React.FC<FileUploadProps> = ({ reqID, fileInfos, setFileInfos }) => {
  const [currentFile, setCurrentFile] = useState<File | undefined>();

  const selectFile = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { files } = event.target;
    if (files && files.length > 0) {
      const newFile: IFile = {
        file: files[0],
        name: files[0].name,
        status: "idle",
        progress: 0,
      };

      setCurrentFile(files[0]);
      setFileInfos((prev) => [...prev, newFile]);
    }
  };

  const upload = async () => {
    if (!currentFile) return;

    const fileToUpload = fileInfos.find((file) => file.file === currentFile);
    if (!fileToUpload) return;

    // Call uploadFile and handle errors by updating status to "error"
    try {
        await uploadFile(fileToUpload, reqID, setFileInfos)

    } catch (error) {
      setFileInfos((prev) =>
        prev.map((file) => 
          file === fileToUpload ? { ...file, status: "error" } : file
        )
      );
    }
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
            type="button"
            className="btn btn-maroon"
            disabled={!currentFile}
            onClick={upload}
          >
            Upload
          </button>
        </Box>
      </Box>

      <Box className="mt-3">
        <Box className="card-header">List of Files</Box>
        <ul className="list-group list-group-flush">
          {fileInfos.map((file, index) => (
            <li className="list-group-item" key={index}>
              {file.name}
              {/* STATUS ICONS */}
              {file.status === "idle" && (
                <FiberManualRecordIcon sx={{ color: "gold", fontSize: 16, marginLeft: 1 }} />
              )}
              {file.status === "uploading" && (
                <CircularProgress size={15} color="primary" thickness={5} />
              )}
              {file.status === "success" && (
                <CheckCircleIcon sx={{ color: "green", fontSize: 16 }} />
              )}
              {file.status === "error" && (
                <CancelIcon sx={{ color: "red", fontSize: 16 }} />
              )}
            </li>
          ))}
        </ul>
      </Box>
    </Box>
  );
};

export default FileUpload;
