import UploadService from "./FileUploadService";
import {IFile} from "../types/File";

export const uploadFile = (
    file: IFile,
    reqID: string,
    setFileInfos: React.Dispatch<React.SetStateAction<IFile[]>>
) => {
    if(!file || !file.file) return;

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