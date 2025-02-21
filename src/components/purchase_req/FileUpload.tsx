import { useState, useEffect } from "react";
import { Box } from "@mui/material";
import UploadService from "../../services/FileUploadService";
import IFile from "../../types/File";

interface FileUploadProps {
  reqID: string;
}

const FileUpload: React.FC<FileUploadProps> = ({ reqID }) => {
    const [currentFile, setCurrentFile] = useState<File>();
    const [progress, setProgress] = useState<number>(0);
    const [message, setMessage] = useState<string>("");
    const [fileInfos, setFileInfos] = useState<Array<IFile>>([]);

    const selectFile = (event: React.ChangeEvent<HTMLInputElement>) => {
        const { files } = event.target;
        const selectedFiles = files as FileList;
        setCurrentFile(selectedFiles?.[0]);
        setProgress(0);
    }

    const upload = () => {
        setProgress(0);
        if(!currentFile) return;

        UploadService.upload(currentFile, reqID, (event: any) => {
            setProgress(Math.round((100 * event.loaded) / event.total));
        })
            .then((files) => {
              if(Array.isArray(files.data)) {
                setFileInfos(files.data);
              } else {
                setFileInfos([]);
              }
            })
            .catch((err) => {
                setProgress(0);

                if(err.response && err.response.data && err.response.data.message) {
                    setMessage(err.response.data.message);
                } else {
                    setMessage("Could not upload the File!");
                }

                setCurrentFile(undefined);
            })
    }

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
                    <a href={file.url}>{file.name}</a>
                  </li>
                ))}
            </ul>
          </Box>
        </Box>
      );
    };

    export default FileUpload;