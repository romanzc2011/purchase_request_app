export interface IFile {
    file?: File;
    name: string;
    status: "idle" | "uploading" | "success" | "error";
    progress?: number;
}