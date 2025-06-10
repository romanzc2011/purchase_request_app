import UploadService from "./UploadService";
import { IFile } from "../types/IFile";

interface UploadFileProps {
    file: File;
    id: string;
    setFileInfo: React.Dispatch<React.SetStateAction<IFile[]>>;
}

async function UploadFile({ file, id, setFileInfo }: UploadFileProps) {
    if (!file) {
        console.error(
            "No file provided or file object is missing for",
            id,
        );
        return;
    }

    // Set status to uploading
    setFileInfo((prev) =>
        prev.map((f) =>
            f.name === file.name ? { ...f, status: "uploading" } : f
        )
    );

    try {
        console.log("UploadHandler.ts");
        const response = await UploadService.upload({
            file: file,
            ID: id,
            dataBuffer: [],
            api_call: "/api/upload",
        });

        if (response && response.status === 200) {
            setFileInfo((prev) =>
                prev.map((f) =>
                    f.name === file.name ? { ...f, status: "success" } : f
                )
            )
        
        } else {
            throw new Error("Upload failed");
        }
    } catch (error) {
        console.error("File upload failed:", error);
        setFileInfo((prev) =>
            prev.map((f) =>
                f.name === file.name ? { ...f, status: "error" } : f
            )
        );
    }
}

export default UploadFile;