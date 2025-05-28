export interface IFile {
    file?: File;
    name: string;
    status: "idle" | "uploading" | "success" | "error" | "ready";
    progress?: number;
}