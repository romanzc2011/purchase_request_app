import { useState } from "react";
import { Box, CircularProgress, Typography } from "@mui/material";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import CancelIcon from "@mui/icons-material/Cancel";
import FiberManualRecordIcon from "@mui/icons-material/FiberManualRecord";
import { uploadFile } from "../../services/FileUploadHandler";
import { IFile } from "../../types/IFile";
import DeleteIcon from "@mui/icons-material/Delete";
import Button from "@mui/material/Button";

interface FileUploadProps {
  reqID: string;
  fileInfos: IFile[];
  setFileInfos: React.Dispatch<React.SetStateAction<IFile[]>>;
}

const FileUpload: React.FC<FileUploadProps> = ({
  reqID,
  fileInfos,
  setFileInfos,
}) => {
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
    try {
      await Promise.all(
        // Upload idle files
        fileInfos.map(async (fileToUpload) => {
          if (fileToUpload.status === "idle") {
            await uploadFile(fileToUpload, reqID, setFileInfos);
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

  const deleteFile = async () => {};

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

      <Box
        className="card mt-3"
        sx={{ background: "linear-gradient(to bottom, #2c2c2c, #800000)" }}
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
              <Typography noWrap sx={{ maxwidth: "200px", display: "inline-block", verticalAlign: "middle"}}>
              {file.name}
              </Typography>
              {/* STATUS ICONS */}
              {file.status === "idle" && (
                <FiberManualRecordIcon
                  sx={{ color: "gold", fontSize: 16, marginLeft: 1 }}
                />
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
              <Button
                onClick={deleteFile}
                size="small"
                sx={{ background: "maroon", marginLeft: "30px"}}
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
