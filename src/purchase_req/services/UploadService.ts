import axios from "axios";
import { FormValues } from "../types/formTypes";

interface FileInfo {
    name: string;
}

interface UploadParamsProps {
    file: File;
    ID: string;
    dataBuffer: FormValues[];
    api_call: string;
}

const baseURL = import.meta.env.VITE_API_URL;

const api = axios.create({
    baseURL,
    headers: {
        "Content-Type": "application/json",
    },
});


function upload({ file, ID, dataBuffer, api_call }: UploadParamsProps) {
    const formData = new FormData();

    formData.append("file", file);
    formData.append("ID", ID);

    if(api_call == "/api/upload") {
        return api.post("/api/upload", formData, {
            headers: { 
                "Content-Type": "multipart/form-data",
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
            },
        });
    }

    if(api_call == "/api/sendToPurchaseReq") {
        return api.post(api_call, dataBuffer, {
            headers: { "Content-Type": "multipart/form-data" },
        });
    }
    
};

const getFiles = (): Promise<FileInfo[]> => {
    return api.get("/api/getfiles");
};

const UploadService = {
    upload,
    getFiles,
};

export default UploadService;
