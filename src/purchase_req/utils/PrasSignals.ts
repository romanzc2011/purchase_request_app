import { signal } from "@preact/signals-react";

export const isSubmittedSig 		= signal<boolean>(false);
export const isDownloadSig			= signal<boolean>(false);
export const socketSig				= signal<WebSocket | undefined>(undefined);
export const messageSig             = signal<string>("");
export const isRequestSubmitted     = signal<boolean>(false);
export const userFoundSig           = signal<boolean>(false);