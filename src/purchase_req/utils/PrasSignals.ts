import { signal } from "@preact/signals-react";
import { Id } from "react-toastify";

export const isSubmittedSig 		= signal<boolean>(false);
export const isDownloadSig          = signal<boolean>(false);
export const isApprovalSig          = signal<boolean>(false);
export const messageSig             = signal<string>("");
export const isRequestSubmitted     = signal<boolean>(false);
export const userFoundSig           = signal<boolean>(false);
export const toastIdSignal = signal<Id | null>(null);
export const sioMessageSig = signal<string | null>(null);
export const sioErrorSig = signal<string | null>(null);
export const sioOriginalPriceSig = signal<number | null>(null);

export const reset_signals = () => {
	isSubmittedSig.value = false;
	isDownloadSig.value = false;
	isApprovalSig.value = false;
	messageSig.value = "";
	isRequestSubmitted.value = false;
	userFoundSig.value = false;
	toastIdSignal.value = null;
	sioMessageSig.value = null;
	sioErrorSig.value = null;
	sioOriginalPriceSig.value = null;
}