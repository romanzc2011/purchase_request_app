import { signal } from "@preact/signals-react";

export const isSubmittedSig 		= signal<boolean>(false);
export const isDownloadSig			= signal<boolean>(false);
export const socketSig				= signal<WebSocket | undefined>(undefined);