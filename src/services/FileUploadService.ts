import axios, { AxiosProgressEvent } from "axios";

const PROD_URL = `https://${window.location.hostname}:5002`;
const DEV_URL = `http://${window.location.hostname}:5004`;

// Choose which URL to use
const baseURL = DEV_URL;

const api = axios.create({
  baseURL,
  headers: {
    "Content-Type": "application/json",
  },
});

const upload = (
  file: File,
  reqID: string,
  onUploadProgress: (progressEvent: AxiosProgressEvent) => void
): Promise<any> => {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("reqID", reqID);
  console.log("reqID: ", reqID);

  return api.post("/api/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress,
  });
};

const getFiles = (): Promise<any> => {
  return api.get("/api/getfiles");
};

const FileUploadService = {
    upload,
    getFiles,
};

export default FileUploadService;
