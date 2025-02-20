import http from "../http-common";

const upload = (file: File, requisitionID: string, onUploadProgress: any): Promise<any> => {
    let formData = new FormData();

    formData.append("file", file);
    formData.append("requistion_id", requisitionID);
    
    return http.post("/api/upload", formData, {
        headers: {
            "Content-Type": "multipart/form-data",
        },
        onUploadProgress,
    });
};

const getFiles = () : Promise<any> => {
    return http.get("/api/getfiles");
};

const FileUploadService = {
    upload,
    getFiles,
};

export default FileUploadService;