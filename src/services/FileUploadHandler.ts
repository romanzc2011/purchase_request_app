import UploadService from "./FileUploadService";
import {IFile} from "../types/IFile";

export const uploadFile = (
    file: IFile,
    reqID: string,
    setFileInfos: React.Dispatch<React.SetStateAction<IFile[]>>
) => {
    if (!file) {
        console.warn('No file provided to uploadFile');
        return;
    }
    if (!file.file) {
        console.warn(`File object is missing for ${file.name}`);
        return;
    }
    setFileInfos((prev) =>
        prev.map((f) => (f.name === file.name ? { ...f, status: "uploading" } : f))
    );

    UploadService.upload(file.file, reqID, (event: ProgressEvent) => {
        const progress = Math.round((100 * event.loaded) / event.total);
        setFileInfos((prev) =>
            prev.map((f) => (f.name === file.name ? { ...f, progress } : f))
        );
    })
    .then((response) => {
        if(response.status === 200) {
            setFileInfos((prev) =>
                prev.map((f) => (f.name === file.name ? { ...f, status: "success" } : f))
            );
        } else {
            throw new Error("Upload failed");
        }
    })
    .catch((error: Error) => {
        console.error('File upload failed:', error);
        setFileInfos((prev) =>
            prev.map((f) => (f.name === file.name ? { ...f, status: "error" } : f))
        );
    });
};